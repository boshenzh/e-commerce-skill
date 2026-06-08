# 04 — Architecture & Phased Build Plan

How the agent and an MCP/tool layer fit together — and a step‑by‑step rollout from read‑only analytics to supervised autonomy. The agent is the **system of record** for the Walmart store and owns all writes.

## Reference architecture

```
Walmart Notifications (webhooks) ─┐         ┌─ Walmart Marketplace REST API (poll + writes)
   PO created, returns, OOS,       ▼         ▼   (Path A: YOUR own keys, client_credentials)
   Buy Box, report ready …  ┌──────────────────────────────┐
                            │   Agent middleware (you build) │◀────────────────────────────────┐
                            │  • webhook receiver + dedup    │                                   │
                            │  • event ledger                │     ┌──────────────────────────┐  │
                            │  • canonical entity map        │     │  Walmart MCP / tool layer │  │
                            │  • reconciliation sweeps       │────▶│  READ tools  (always on)  │──┘
                            │  • decision + audit store      │     │  WRITE tools (dry-run +   │
                            └───────────────┬────────────────┘     │   approval token)         │
                                            │ proposes / acts       └──────────────────────────┘
                                            ▼
                                   AI agent (any runtime)
```

The agent uses **Path A keys**, is the **system of record** for the Walmart store, and writes to Walmart through narrow, idempotent, guardrailed tools (gated by approval in early phases; a policy engine for bounded actions later).

## 1. System‑of‑record (the agent owns everything)

The agent is the authoritative writer for the Walmart store and owns every domain end‑to‑end:

| Domain | Owner (system of record) | Notes |
|---|---|---|
| **Inventory (ATS)** | **Agent** → pushes to Walmart | the agent owns this end‑to‑end; it pushes available‑to‑sell from your own stock truth (see note below) |
| **Price baseline / floor** | **Agent** | high blast radius; gated + bounded |
| **Repricing deltas / Buy Box** | **Agent** within bounds | where the agent adds value |
| **Listings / catalog content** | **Agent** | the agent owns listing setup, audits, and enrichment |
| **Order state (fulfillment)** | **Agent** | the agent owns this end‑to‑end: acknowledge, ship (tracking), cancel, refund, returns, WFS |
| **Walmart event truth / analytics / reconciliation / decisions** | **Agent** | observability + decisions |

**The agent owns all writes — listings, price, inventory, orders, returns, WFS — and is the single system of record for the Walmart store.**

> **Inventory & fulfillment for a standalone agent:** because the agent owns these, it needs (a) a real **source of inventory truth** — your own warehouse/3PL stock counts — to push available‑to‑sell to Walmart, and (b) a way to produce **shipping labels + tracking** (Walmart's carrier/label APIs or a 3PL) to fulfill and ship orders.

## 2. Event ingestion — webhook + reconciliation hybrid

Walmart webhooks are at‑least‑once, unordered, best‑effort — so pair them with polling.

**Webhook receiver requirements:**
- **Verify signatures**; reject anything unverified or for a seller you don't manage.
- **Persist the raw payload first, return 2xx only after a durable write**, process async. (Walmart retries on non‑2xx → a slow handler causes duplicates.)
- **Dedupe on `eventId`** (unique constraint; redelivery = no‑op).
- **Assume no ordering** — never apply a Buy Box/inventory event blindly; reconcile against current Walmart state first.

**Polling cadences (respect limits):**
- **Orders** (`GET /v3/orders` ~5000/min): adaptive 30 s–5 min delta poll — the agent ingests POs and drives order state (acknowledge / ship / cancel / refund), with polling also serving reconciliation.
- **Inventory/price**: read‑back after each write + a periodic full sweep (nightly/few‑hours) diffing live vs expected → emit `drift` events.
- **Reconciliation sweep** is the safety net for missed/duplicated webhooks: enumerate active offers, diff vs the event ledger, backfill gaps.

**Phantom‑success rule:** Walmart can return 200 yet not apply a change for minutes. Write → wait ~60 s → read back → confirm before marking `CONFIRMED`.

## 3. Async feed handling

```
submit feed → capture feedId → poll GET /v3/feeds/{feedId}?includeDetails=true
   feedStatus: INPROGRESS → PROCESSED | ERROR
   walk itemDetails.itemIngestionStatus[]  (a PROCESSED feed can still have failed items!)
```
- **Error classes:** `DATA_ERROR` (bad payload → fix + resubmit), `SYSTEM_ERROR` / `TIMEOUT_ERROR` (retryable).
- **Poll backoff:** 15 min, 1 hr, 2 hr, then every 4 hr. Don't hot‑loop.
- **Idempotency:** deterministic key per intent; persist `intent → feedId`; a retry looks up the existing `feedId` instead of double‑submitting. Keep the same correlation ID across retries.
- **Retry/backoff/dead‑letter:** transient → exponential backoff + jitter (honor `x-current-token-count` / `X-Next-Replenishment-Time` on 429); permanent (`DATA_ERROR` after fixes) → **dead‑letter queue** with full per‑item context for human review. Never silently drop.
- **Batch to respect ~10 feeds/hour/type:** a token‑bucket submission scheduler that coalesces pending intents into the next window and prioritizes Buy‑Box‑critical reprices when the budget is tight.

## 4. MCP / tool layer (the privilege boundary)

Treat the agent as a credentialed machine principal that will fire hundreds of tool calls. The tool layer — not the prompt — is where safety is enforced.

- **Separate READ vs WRITE tools.** Production default = **read‑only**; write tools enabled per role/phase. (Read: `get_orders`, `get_returns`, `get_item`, `get_inventory`, `get_price`, `get_buybox_status`, `get_feed_status`, `list_notifications`, `get_reconciliation_drift`. Write: `update_price`, `update_inventory`, `submit_feed`, `acknowledge_order`, `ship_order`, `cancel_order`, `refund_order`, `manage_return`.)
- **Dry‑run / preview:** every write tool accepts `dry_run: true` and returns a **diff** (current vs proposed price/qty, affected SKUs, projected Buy Box/margin impact) with no submit. This is the agent's default.
- **Human‑approval gates:** price/inventory/cancel are gated in Phases 1–2. The write tool returns a `pending_approval` object + one‑time **approval token**; the mutation only fires when a human (later a policy engine) returns that token.
- **Idempotency at the tool layer:** every write tool **requires** a client idempotency key; duplicate key → original result, never a second feed.
- **Audit logging:** structured logs w/ correlation IDs for every tool call — tool, args (secrets/PII redacted), dry‑run vs live, approval token + approver, latency, success/failure, `feedId`, per‑item outcome. Answer "which agent, on whose authority, changed what, and was it approved." Retain through return/dispute windows.
- **Least privilege:** give the agent **your own first‑party API keys** (no Connected App or partnership needed) and scope the tool layer to exactly the writes it should own per phase. Enable higher‑blast‑radius tools (cancel, bulk inventory, new listings) only as the rollout advances.

## 5. Secrets / token management

- **Access token TTL 15 min; refresh token ~1 year.** Cache the access token (Redis/Secrets Manager) keyed by client+seller; **refresh proactively at ~80% TTL**; single‑flight the refresh.
- Store `client_id`/`secret`/refresh tokens in a **dedicated secrets manager** — never env files or the agent's prompt/context. The MCP server reads them; the agent never sees raw credentials.
- **Rotation:** rotate on schedule + on suspected compromise; support overlapping old+new validity so in‑flight refreshes don't fail.

## 6. Single source of truth

**The agent is the system of record for Walmart writes.** (Optional: if you ever add another tool that also writes to Walmart, partition fields per system to avoid oversell / double‑write / price‑flapping.)

Still apply the write‑safety basics regardless: **read‑before‑write + verification read‑back** (the phantom‑success pattern) and **per‑SKU cooldowns** so a write cycle can't contend with itself.

## 7. Phased rollout

| Phase | What ships | Writes? |
|---|---|---|
| **0 — Foundation** | OAuth client (scoped), token cache + proactive refresh, webhook receiver (verify + dedup + durable write), event ledger, canonical entity map, reconciliation sweep, MCP server **READ tools only** | none |
| **1 — Read‑only analytics** | Buy‑Box‑loss diagnosis, OOS/return trends, pricing/margin recommendations, scorecard + reconciliation reports. Write tools exist only in `dry_run` (diffs a human reviews) | none (dry‑run only) |
| **2 — Human‑in‑the‑loop writes** | Enable write tools behind **approval tokens** (price‑delta, targeted inventory correction, feed submit, listing fixes, order state). Full audit on. Agent proposes → human approves → submit → read‑back confirms | gated |
| **3 — Supervised autonomy** | For **low‑blast‑radius** actions (reprice within a pre‑approved margin/price band + SKU allowlist), a **policy engine** auto‑issues the approval token when hard guardrails pass. Cancels, large inventory changes, new listings stay **human‑gated indefinitely**. Global kill‑switch + per‑SKU circuit breakers revert to Phase 2 on anomaly | bounded auto |

**Mapping to your 4 workflows:** order/inventory monitoring + analytics land in **Phase 1**; repricing and listing fixes graduate to **Phase 2**; bounded repricing within a band reaches **Phase 3**. Order‑state and inventory writes are owned by the agent and gated through Phase 2, with only low‑blast‑radius actions auto‑issued in Phase 3.

## 8. Suggested component checklist (Phase 0–1)

- [ ] Secret manager holding Client ID/Secret; token service with proactive refresh + single‑flight.
- [ ] Walmart API client (typed) with 429 handling (read replenish headers) + retry/backoff.
- [ ] Webhook receiver (HTTPS, signature verify, `eventId` dedup, durable write, 2xx‑after‑persist) — validate with **Test Notification API**.
- [ ] Event ledger (append‑only) + canonical entity map `(walmart_sku, gtin/upc, walmart_item_id, internal_offer_id)` bootstrapped from `GET /v3/items`.
- [ ] Reconciliation sweep job (nightly diff live vs expected → drift events).
- [ ] MCP/tool server exposing READ tools; WRITE tools present but `dry_run`‑only with approval scaffolding.
- [ ] Audit log store with correlation IDs.
- [ ] Dashboards/alerts for SLA risk, scorecard thresholds, drift, dead‑letter.

See `05` for the guardrails these tools must enforce.
