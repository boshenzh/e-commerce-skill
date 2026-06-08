# 03 — Agent Automation Playbook

Each automation is written as an **agent loop**: *trigger → read → decide → write (gated) → verify*. Your four priority workflows lead; six more are catalogued after. Each names the APIs (`02`), the decision points, and the human‑approval guardrails (`05`).

**Cross‑cutting rules that apply to every loop:**
- **Phantom success:** a `200`/`202` does **not** mean the change is live. After any write, **wait ~60 s, read back, confirm**, then mark the intent `CONFIRMED`.
- **Idempotency:** every write carries a deterministic key `hash(sku + field + target + intentId)`; persist `intent → feedId` so retries never double‑submit.
- **Single source of truth:** the agent is the system of record for Walmart writes — listings, price, inventory, orders, returns, and WFS — and owns them end‑to‑end. *(Optional: if you ever add another tool that also writes to Walmart, partition fields per system to avoid oversell / double‑write / price‑flapping.)*
- **Rate budgeting:** writes are scarce (`PUT /v3/price` 100/hr; bulk feeds 10/hr; order actions 60/min). Batch, schedule, prioritize.

---

## ⭐ Priority 1 — Order fulfillment

**Goal:** never miss the 4‑hour acknowledge SLA or the Expected‑Ship‑Date auto‑cancel; keep tracking flowing; surface exceptions. **The agent owns fulfillment end‑to‑end** — it acknowledges, ships, cancels, and refunds against Walmart directly.

```
Trigger:  PO-created webhook  (+ GET /v3/orders/released poll every 5–15 min as reconciliation safety net)
Read:     GET /v3/orders/{poId}  → line items, expectedShipDate, shipNodeType
Decide:   • Acknowledge each released order within the 4-hr SLA.
          • Any line approaching ExpectedShipDate?  → ship with label + tracking before ESD.
          • Any cancel/refund/return events?  → action + log.
Write:    POST …/acknowledge  → POST …/shipping (carrier + tracking) before ESD.
          POST …/cancel (true OOS), POST …/refund — large/exceptional cases human-gated.
Verify:   GET /v3/orders/{poId} status transitions; alert on stalls.
```

- **Read tools:** `get_orders`, `get_order`, `get_returns`, `list_notifications`.
- **Decision points:** SLA risk (ack <4 hr; ship by ESD; auto‑cancel at ESD+4 days), tracking gaps, which cancels/refunds are routine vs need approval.
- **Fulfillment plumbing:** a standalone agent must produce shipping labels + tracking to ship — use Walmart's carrier/label APIs or your 3PL — and feed real tracking numbers back on the ship call.
- **Guardrails:** agent acknowledges/ships routinely; large or exceptional cancels/refunds stay human‑gated.
- **Value:** protects On‑Time Shipping / Valid Tracking Rate scorecard metrics; turns silent SLA misses into proactive action.

---

## ⭐ Priority 2 — Repricing & Buy Box defense

**Goal:** win/hold the Buy Box at the best margin without tripping suppression. **Prefer Walmart's native Repricer** (server‑side, dodges the tight write limits); use self‑repricing only for cases the native engine can't express.

```
Trigger:  Buy Box change webhook  (+ nightly BUYBOX on-request report for full-catalog truth)
Read:     BUYBOX report → isSellerBuyBoxWinner, BuyBox Item Price, BuyBox Ship Price, your price
Decide:   target = clamp(competitive_target, [min, max])
          where min = max(unit_cost + min_margin, MAP), max ≤ reference_price
          • If competitive floor < min → DO NOT chase; hold at min, accept Buy Box loss
          • If no competitive target → hold last submitted price
Write:    Preferred: POST /v3/repricer/strategy (Competitive) + assign SKUs with min/max  (≈20/hr)
          Fallback:  PUT /v3/price (100/hr) or PRICE_AND_PROMOTION feed (10/hr) within [min,max]
Verify:   read-back price after ~5 min; confirm it stuck at the submitted value.
```

- **Read tools:** `get_buybox_status`, `get_item`, `get_price`, unpublished‑item reasons.
- **Decision points:** clamp to `[min,max]`; never below floor; per‑cycle %‑change cap; cooldown per SKU; SKU allowlist.
- **Guardrails (hard):** mandatory per‑SKU min/max; never below cost/MAP; large moves → human approval; read‑back tripwire if the submitted price doesn't stick (suspend agent writes on that SKU and alert). See `05`.
- **Why native Repricer first:** real‑time per‑SKU repricing across a big catalog is impossible under 100/hr·10/hr write limits; the native engine reprices within your bounds server‑side at 15 min–4 hr cadence.

---

## ⭐ Priority 3 — Listing creation & optimization

**Goal:** create well‑formed listings, fix unpublished items, and lift Listing Quality. Content writes are validated against policy **before** submit.

```
Trigger:  new-product request | unpublished-item event | low Listing Quality score
Read:     GET /v3/items/walmart/search → match? (MP_ITEM_MATCH) : full setup (MP_ITEM)
          POST /v3/items/spec → required/highly-recommended attributes
          Insights: listingQuality/score (content/offer/discoverability), unpublished reasons
Decide:   • Build schema-valid feed; LLM drafts title/desc/attributes within policy
          • For unpublished: map reason code → fix (e.g. Pricing Error → raise price;
            Reasonable Price Not Satisfied → lower toward reference)
Write:    POST /v3/feeds?feedType=MP_ITEM | MP_ITEM_MATCH | MP_MAINTENANCE  → feedId   (10/hr)
Verify:   poll GET /v3/feeds/{feedId}?includeDetails=true (per-item ingestionStatus);
          then GET /v3/items/{sku} until publishedStatus = PUBLISHED  (feed PROCESSED ≠ published)
```

- **Read tools:** `get_item`, `get_listing_quality`, `get_unpublished_items`, `get_spec`, `walmart_search`.
- **Decision points:** match vs full setup; which attributes to enrich for ranking; image/content compliance.
- **Content guardrails:** titles ~50–75 chars, **no special symbols (™/®/*/hearts), no marketing claims ("Free Shipping","Best Seller"), no retailer info**; English‑only; no conflicting info; IP/brand owned; not a prohibited category. Validate before submit (`05`).
- **Value:** higher Listing Quality → better discoverability + Buy Box eligibility; fewer unpublished SKUs silently losing sales.

---

## ⭐ Priority 4 — Inventory sync & health

**Goal:** keep Walmart inventory accurate (the agent is the writer), catch drift, react to OOS, and monitor account health + finances.

```
Trigger:  Inventory-OOS webhook | nightly full sweep | settlement-ready
Read:     GET /v3/inventories (all SKUs/nodes) | GET /v3/fulfillment/inventory (WFS ATS)
          Seller Performance summaries; recon report (availableReconFiles → reconFileJson)
Decide:   • Drift: does live Walmart qty match the source-of-truth stock? → correct
          • OOS on a SKU that should have stock? → push the correct qty
          • Scorecard nearing a threshold? → alert with root cause
          • Settlement vs expected (fees/refunds/payout)? → reconciliation report
Write:    PUT /v3/inventory (per SKU) | MP_INVENTORY feed (bulk) — push corrected quantities.
          Large/exceptional corrections human-gated.
Verify:   re-read after any write; reconcile ledger.
```

- **Read tools:** `get_inventory`, `get_wfs_inventory`, `get_seller_performance`, `get_reconciliation`.
- **Decision points:** drift threshold, which OOS is real vs lag, scorecard early‑warning, settlement variance.
- **Inventory source of truth:** a standalone agent needs a real stock feed to push from — your own warehouse/3PL on‑hand quantities — reconciled against Walmart on every sweep; the agent owns the push to Walmart end‑to‑end.
- **Guardrails:** all per‑SKU min/max, per‑cycle change caps, and read‑back verification still apply; large/exceptional corrections are explicit, logged, human‑approved.
- **Value:** prevents oversell/undersell, protects Cancellation Rate (a scorecard metric), and catches fee/refund leakage in settlements.

---

## Additional automations (catalogue)

| # | Automation | Trigger | Key APIs | Notes / guardrail |
|---|---|---|---|---|
| 5 | **Returns/refunds handling** | Return webhook | `GET /v3/returns`, `POST /v3/returns/{id}/refund` | Seller‑fulfilled only (WFS view‑only); refund within 48 hr; refunds human‑gated in early phases |
| 6 | **Customer Q&A / review monitoring** | new question/review | Reviews via Brand Portal / Seller Center (limited API) | Draft responses for human approval; respond within response‑rate SLA (≥95%/48h) |
| 7 | **Listing‑quality / content‑discoverability** | weekly | Insights listingQuality, content score | Prioritize SKUs with biggest score gaps; content compliance gate |
| 8 | **Performance/scorecard monitoring + alerting** | daily | Seller Performance API | Early‑warning before thresholds; assemble Plan‑of‑Action evidence automatically |
| 9 | **Ad campaign management** | — | Walmart Connect (WCPN‑gated) | Out of scope unless you join WCPN (`01` Path G) |
| 10 | **Catalog enrichment & dedup** | weekly | `GET /v3/items`, `Get Spec`, `isDuplicate` | Fill highly‑recommended attributes; flag duplicate items |
| 11 | **Financial reconciliation** | each settlement | recon/payment reports | Per‑settlement journal entry; flag `Excess Refund Adjustment`, fee anomalies |
| 12 | **Assortment growth** | monthly | `/v3/growth/assortment/recommendations` | Surface "Customer Favorites" to add; human decides what to source |
| 13 | **WFS replenishment** | low‑ATS | `POST /v3/fulfillment/inbound-shipments` | Recommend inbound qty from sell‑through; shipment creation human‑gated |

## Read‑only vs write actions (quick map)

| Always read‑only (safe) | Gated writes (approval) |
|---|---|
| get orders / order / returns | acknowledge / ship (agent owns) |
| get item / inventory / price / buybox | update price / submit price feed |
| listing quality / unpublished reasons | submit item / maintenance feed |
| reports / insights / settlement | cancel / refund order lines |
| list notifications | issue return refund |
| reconciliation drift | inventory push / correction (agent owns) |

The MCP/tool layer enforces this split structurally (`04`).
