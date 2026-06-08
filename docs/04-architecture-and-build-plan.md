# 04 — Architecture & Phased Build Plan

How the agent, an MCP/tool layer, and DianXiaoMi fit together — and a step‑by‑step rollout from read‑only analytics to supervised autonomy.

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
                                            │ proposes / alerts     └──────────────────────────┘
                                            ▼
                                   AI agent (any runtime)

   DianXiaoMi (unchanged) ── owns inventory push, fulfillment, procurement ── runs ALONGSIDE
```

The agent uses **Path A keys**, sits **alongside** DXM, is **read‑mostly**, and writes to Walmart only through narrow, idempotent, human‑gated tools (or the native Repricer).

## 1. System‑of‑record (who owns what)

DXM has **no inbound API**, so you can't make it the agent's downstream. Let ownership follow what each system can authoritatively write:

| Domain | Owner (system of record) | Why |
|---|---|---|
| **Inventory (ATS)** | **DianXiaoMi** → pushes to Walmart | DXM knows true cross‑channel stock; two writers = oversell |
| **Price baseline / floor** | **DianXiaoMi** | high blast radius; agent proposes deltas |
| **Repricing deltas / Buy Box** | **Agent** (Phase 2+) within bounds | where the agent adds value |
| **Listings / catalog content** | **DianXiaoMi** (agent audits/enriches) | DXM does listing setup |
| **Order state (fulfillment)** | **DianXiaoMi** | DXM ingests POs, ships, writes tracking |
| **Walmart event truth / analytics / reconciliation / decisions** | **NEW agent layer** | the gap DXM doesn't fill |

**The agent owns observability + decisions, not operational writes.** Replacing DXM would mean rebuilding warehouse/procurement/label/logistics — not worth it.

## 2. Event ingestion — webhook + reconciliation hybrid

Walmart webhooks are at‑least‑once, unordered, best‑effort — so pair them with polling.

**Webhook receiver requirements:**
- **Verify signatures**; reject anything unverified or for a seller you don't manage.
- **Persist the raw payload first, return 2xx only after a durable write**, process async. (Walmart retries on non‑2xx → a slow handler causes duplicates.)
- **Dedupe on `eventId`** (unique constraint; redelivery = no‑op).
- **Assume no ordering** — never apply a Buy Box/inventory event blindly; reconcile against current Walmart state first.

**Polling cadences (respect limits):**
- **Orders** (`GET /v3/orders` ~5000/min): adaptive 30 s–5 min delta poll — but for **reconciliation only** (DXM acts on orders).
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

- **Separate READ vs WRITE tools.** Production default = **read‑only**; write tools enabled per role/phase. (Read: `get_orders`, `get_returns`, `get_item`, `get_inventory`, `get_price`, `get_buybox_status`, `get_feed_status`, `list_notifications`, `get_reconciliation_drift`. Write: `propose_price_update`, `propose_inventory_update`, `submit_feed`, `request_cancel`.)
- **Dry‑run / preview:** every write tool accepts `dry_run: true` and returns a **diff** (current vs proposed price/qty, affected SKUs, projected Buy Box/margin impact) with no submit. This is the agent's default.
- **Human‑approval gates:** price/inventory/cancel are gated in Phases 1–2. The write tool returns a `pending_approval` object + one‑time **approval token**; the mutation only fires when a human (later a policy engine) returns that token.
- **Idempotency at the tool layer:** every write tool **requires** a client idempotency key; duplicate key → original result, never a second feed.
- **Audit logging:** structured logs w/ correlation IDs for every tool call — tool, args (secrets/PII redacted), dry‑run vs live, approval token + approver, latency, success/failure, `feedId`, per‑item outcome. Answer "which agent, on whose authority, changed what, and was it approved." Retain through return/dispute windows.
- **Least privilege:** give the agent a **scoped Solution‑Provider credential** (or, for your own shop, your own keys but with the agent's tool layer *excluding* order acknowledge/ship/cancel so it structurally cannot collide with DXM's fulfillment).

## 5. Secrets / token management

- **Access token TTL 15 min; refresh token ~1 year.** Cache the access token (Redis/Secrets Manager) keyed by client+seller; **refresh proactively at ~80% TTL**; single‑flight the refresh.
- Store `client_id`/`secret`/refresh tokens in a **dedicated secrets manager** — never env files or the agent's prompt/context. The MCP server reads them; the agent never sees raw credentials.
- **Rotation:** rotate on schedule + on suspected compromise; support overlapping old+new validity so in‑flight refreshes don't fail.

## 6. Avoiding double‑writes / conflicts with DXM

1. **Field‑level ownership partition (no overlap):** DXM owns inventory + order‑state writes; the agent owns only price‑delta/Buy‑Box writes (Phase 2+). Never both on the same field.
2. **Credential/tool scope as the hard wall:** make the agent's tools *incapable* of writing DXM‑owned fields. Policy in the prompt is advisory; a missing tool/scope is a wall.
3. **Conflict tripwire:** subscribe to Buy Box / Offer / price‑change events; if the agent writes price Y and then sees DXM push X back within minutes, raise a **conflict alert** and suspend agent writes on that SKU until a human decides.
4. **Read‑before‑write + verification read‑back** (the phantom‑success pattern).
5. **Per‑SKU cooldowns** so the agent can't contend with DXM's sync cycle.
6. Because DXM can't be told what the agent did, prefer **propose‑to‑human** for any field DXM actively syncs; reserve direct agent writes for domains DXM leaves alone (e.g. promotional price within an agreed band) or the native Repricer.

## 7. Phased rollout

| Phase | What ships | Writes? |
|---|---|---|
| **0 — Foundation** | OAuth client (scoped), token cache + proactive refresh, webhook receiver (verify + dedup + durable write), event ledger, canonical entity map, reconciliation sweep, MCP server **READ tools only** | none |
| **1 — Read‑only analytics** | Buy‑Box‑loss diagnosis, OOS/return trends, pricing/margin recommendations, scorecard + reconciliation reports. Write tools exist only in `dry_run` (diffs a human reviews) | none (dry‑run only) |
| **2 — Human‑in‑the‑loop writes** | Enable write tools behind **approval tokens** (price‑delta, targeted inventory correction, feed submit, listing fixes). Conflict tripwires + full audit on. Agent proposes → human approves → submit → read‑back confirms | gated |
| **3 — Supervised autonomy** | For **low‑blast‑radius** actions (reprice within a pre‑approved margin/price band + SKU allowlist), a **policy engine** auto‑issues the approval token when hard guardrails pass. Cancels, large inventory changes, new listings stay **human‑gated indefinitely**. Global kill‑switch + per‑SKU circuit breakers revert to Phase 2 on anomaly | bounded auto |

**Mapping to your 4 workflows:** order/inventory monitoring + analytics land in **Phase 1**; repricing‑via‑native‑Repricer and listing fixes graduate to **Phase 2**; bounded repricing within a band reaches **Phase 3**. Inventory writes stay with DXM throughout.

## 8. Suggested component checklist (Phase 0–1)

- [ ] Secret manager holding Client ID/Secret; token service with proactive refresh + single‑flight.
- [ ] Walmart API client (typed) with 429 handling (read replenish headers) + retry/backoff.
- [ ] Webhook receiver (HTTPS, signature verify, `eventId` dedup, durable write, 2xx‑after‑persist) — validate with **Test Notification API**.
- [ ] Event ledger (append‑only) + canonical entity map `(walmart_sku, gtin/upc, walmart_item_id, dxm_sku, internal_offer_id)` bootstrapped from `GET /v3/items`.
- [ ] Reconciliation sweep job (nightly diff live vs expected → drift events).
- [ ] MCP/tool server exposing READ tools; WRITE tools present but `dry_run`‑only with approval scaffolding.
- [ ] Audit log store with correlation IDs.
- [ ] Dashboards/alerts for SLA risk, scorecard thresholds, drift, dead‑letter, conflicts.

See `05` for the guardrails these tools must enforce, and `06` for the DXM entity‑map bootstrap.
