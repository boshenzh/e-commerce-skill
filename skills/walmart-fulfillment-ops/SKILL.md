---
name: walmart-fulfillment-ops
description: "Run seller-fulfilled Walmart order operations end-to-end within SLA — acknowledge, ship with tracking, handle returns/refunds, and protect the scorecard. Use when: 'process my Walmart orders', 'ship a Walmart order', 'why did my order auto-cancel', 'handle a return/refund', 'I'm missing my ship-by SLA', 'fulfill my Walmart orders', '沃尔玛订单处理', '发货/履约'."
author: "boshenzh"
license: "Apache-2.0"
version: "0.1.0"
allowed-tools: "Read Bash"
---

# Walmart Fulfillment Ops — run seller-fulfilled order fulfillment end-to-end within SLA

Spoke of the **walmart-seller** hub ([`../walmart-seller/SKILL.md`](../walmart-seller/SKILL.md)). Read the hub first for auth, env vars (`WALMART_CLIENT_ID` / `WALMART_CLIENT_SECRET` / `WALMART_ENV`), and the global safety rules. All calls go through the hub's authenticated helper.

## The one rule that defines this skill

**The agent owns order fulfillment end-to-end** — it is the system of record for Walmart order writes: **acknowledge within 4 h, ship with valid tracking before the Expected Ship Date, and handle cancels / refunds / returns.** Everything is driven by the SLAs and scorecard below.

> **Single source of truth** — the agent is the system of record for Walmart writes. (If you ever add another tool that also writes to Walmart, partition fields per system to avoid oversell / double-write / price-flapping.) Optional, only matters if a second writer exists.

To run fulfillment standalone you need two things outside the order APIs: (a) a real **source of inventory truth** — your own warehouse/3PL stock — to keep Walmart quantities accurate, and (b) a way to produce **shipping labels + tracking** (Walmart's carrier/label APIs or a 3PL) so every shipped line carries valid tracking.

## When to use / when not

- **Use** to: poll the released-order queue, acknowledge orders, ship lines with valid tracking before their ESD, cancel/refund, and process returns/refunds.
- **Not** for: WFS fulfillment (`walmart-wfs`) or pricing/Buy Box (`walmart-buybox-pricing`).

## Order lifecycle (tracked PER LINE, not per order)

`Created (released)` → `Acknowledged` → `Shipped` → `Delivered`, with `Cancelled` / `Refund` branches. Each line of a PO can be in a different state.

## The SLAs this skill exists to protect

- **Acknowledge within 4 HOURS** of release.
- **Ship by the Expected Ship Date (ESD)** with valid tracking.
- **Walmart AUTO-CANCELS** any line not shipped-with-tracking by **ESD + 4 calendar days.** Auto-cancels hammer the Cancellation Rate.
- Scorecard at stake (full table in [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md)): **On-Time Delivery ≥ 90%**, **Valid Tracking Rate ≥ 99%**, **Cancellation Rate ≤ 2%**.

## Workflow — fulfill end-to-end

1. **Poll the work queue** of unacknowledged/released orders and (better) subscribe to **PO-created** push events. Newest first.
2. **Acknowledge** each line within 4 h of release.
3. **Ship** each line with valid tracking before its ESD (label + tracking from your carrier/label API or 3PL). Prioritize any line approaching its ESD (or ESD+4d auto-cancel) still without tracking — surface PO id, line, ESD, and time remaining.
4. **Cancel / refund / process returns** as needed (steps below), keeping every change within the safety guardrails.

## Endpoints (exact paths in [`../walmart-seller/references/api-reference.md`](../walmart-seller/references/api-reference.md))

Make every call via the hub helper:

```bash
python3 ../walmart-seller/scripts/wm_request.py GET '/v3/orders/released?createdStartDate=2026-06-01'
```

- **Work queue:** `GET /v3/orders/released?createdStartDate=…` — **60/min** (this is the bottleneck).
- **All orders:** `GET /v3/orders` — cursor-paged, **5000/min**. **One order:** `GET /v3/orders/{poId}`.
- **Ship:** `POST /v3/orders/{poId}/shipping` with `trackingInfo` — `shipDateTime` (epoch-ms), `carrierName` as `{"carrier":"UPS"}` or `{"otherCarrier":"…"}`, `methodCode`, `trackingNumber`. The **same endpoint edits** a shipment, but only within a **~4 hr window** after shipping.
- **Cancel:** `POST /v3/orders/{poId}/cancel` with `cancellationReason`. **Refund:** `POST /v3/orders/{poId}/refund` with **NEGATIVE** amounts.
- **Returns:** `GET /v3/returns`; refund a return with `POST /v3/returns/{returnOrderId}/refund` — **Shipped lines only**, negative amounts. **WFS returns are VIEW-ONLY** (Walmart refunds them; you cannot).

## Working example — poll the released queue (sandbox-verified 200)

```bash
python3 ../walmart-seller/scripts/wm_request.py GET '/v3/orders/released?createdStartDate=2026-06-01'
```

Returns (verified live on sandbox):

```json
{ "list": { "meta": { "totalCount": 0, "limit": 10, "nextCursor": null },
            "elements": { "order": [] } } }
```

Walk `list.elements.order[]`; page with `list.meta.nextCursor`. (Also verified on sandbox: `GET /v3/items?limit=1` → 200 `ItemResponse[]`; a missing-SKU `GET /v3/inventory?sku=…` → clean 404 `CONTENT_NOT_FOUND.GMP_INVENTORY_API`.) The order **write/feed endpoints are limited on the sandbox** — **verify ship/cancel/refund shapes on production** before relying on them.

## Gotchas

- **The two SLAs that wreck the scorecard:** the **4-hr ack** and the **ESD + 4 calendar-day auto-cancel**. Auto-cancels count against Cancellation Rate (≤ 2%); missed tracking hits Valid Tracking Rate (≥ 99%).
- **Refund amounts must be NEGATIVE** — both `/refund` and `/returns/{id}/refund`. A positive amount is wrong.
- **WFS returns are view-only.** Don't try to refund them; Walmart handles those.
- **Tracking edits expire fast** — the ship endpoint only edits a shipment for **~4 hr** after it was first submitted. After that the tracking is locked.
- **State is per LINE.** A PO can be part-shipped; check/act on the line, not the whole order.
- **`60/min` on order actions is the throttle** (vs 5000/min for `GET /v3/orders`). On `429`, `wm_request.py` backs off via `x-next-replenish-time` — don't hand-roll retries.

## Load deeper

- Exact endpoints, limits, payload fields: [`../walmart-seller/references/api-reference.md`](../walmart-seller/references/api-reference.md).
- Scorecard thresholds + account-safety invariants: [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md).
- Auth, token caching, env vars, routing: [`../walmart-seller/SKILL.md`](../walmart-seller/SKILL.md).
