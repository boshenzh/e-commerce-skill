---
name: walmart-fulfillment-ops
description: "Run seller-fulfilled Walmart order operations within SLA — acknowledge, ship with tracking, handle returns, and protect the scorecard. Use when: 'process my Walmart orders', 'ship a Walmart order', 'why did my order auto-cancel', 'handle a return/refund', 'I'm missing my ship-by SLA', 'monitor order fulfillment', '沃尔玛订单处理', '发货/履约'."
author: "boshenzh"
license: "Apache-2.0"
version: "0.1.0"
allowed-tools: "Read Bash"
---

# Walmart Fulfillment Ops — monitor seller-fulfilled order SLAs, handle exceptions

Spoke of the **walmart-seller** hub ([`../walmart-seller/SKILL.md`](../walmart-seller/SKILL.md)). Read the hub first for auth, env vars (`WALMART_CLIENT_ID` / `WALMART_CLIENT_SECRET` / `WALMART_ENV`), and the global safety rules. All calls go through the hub's authenticated helper.

## The one rule that defines this skill

**DianXiaoMi (DXM) OWNS order acknowledge + ship.** This skill's job is to **MONITOR SLAs and handle exceptions** — it does **not** routinely acknowledge or ship orders. Doing so from the agent **double-fulfills** (duplicate tracking, oversell). Default posture = read-only watcher. Any agent-initiated ack/ship/cancel/refund is a deliberate, **human-approved exception** because it competes with DXM.

## When to use / when not

- **Use** to: watch the released-order queue, confirm DXM is acknowledging + shipping on time, alert on lines approaching their ship-by deadline, and execute a one-off ack/ship/cancel/refund/return when a human explicitly approves it.
- **Not** for: routine bulk fulfillment (DXM does that), inventory pushes (DXM owns inventory — see hub), WFS fulfillment (`walmart-wfs`), or pricing/Buy Box (`walmart-buybox-pricing`).

## Order lifecycle (tracked PER LINE, not per order)

`Created (released)` → `Acknowledged` → `Shipped` → `Delivered`, with `Cancelled` / `Refund` branches. Each line of a PO can be in a different state.

## The SLAs this skill exists to protect

- **Acknowledge within 4 HOURS** of release.
- **Ship by the Expected Ship Date (ESD)** with valid tracking.
- **Walmart AUTO-CANCELS** any line not shipped-with-tracking by **ESD + 4 calendar days.** Auto-cancels hammer the Cancellation Rate.
- Scorecard at stake (full table in [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md)): **On-Time Delivery ≥ 90%**, **Valid Tracking Rate ≥ 99%**, **Cancellation Rate ≤ 2%**.

## Workflow — default is MONITOR

1. **Poll the work queue** of unacknowledged/released orders and (better) subscribe to **PO-created** push events. Newest first.
2. **Confirm DXM is keeping up:** each line acknowledged within 4 h and shipping before its ESD. If DXM is doing its job, do nothing.
3. **Escalate / alert** any line approaching its ESD (or ESD+4d auto-cancel) still without tracking. Surface PO id, line, ESD, and time remaining — let a human decide.
4. **Only then, as a human-approved exception**, ack / ship / cancel / refund from here (steps below). Never as a routine batch.

## Endpoints (exact paths in [`../walmart-seller/references/api-reference.md`](../walmart-seller/references/api-reference.md))

Make every call via the hub helper:

```bash
python3 ../walmart-seller/scripts/wm_request.py GET '/v3/orders/released?createdStartDate=2026-06-01'
```

- **Work queue:** `GET /v3/orders/released?createdStartDate=…` — **60/min** (this is the bottleneck).
- **All orders:** `GET /v3/orders` — cursor-paged, **5000/min**. **One order:** `GET /v3/orders/{poId}`.
- **Ship (exception only):** `POST /v3/orders/{poId}/shipping` with `trackingInfo` — `shipDateTime` (epoch-ms), `carrierName` as `{"carrier":"UPS"}` or `{"otherCarrier":"…"}`, `methodCode`, `trackingNumber`. The **same endpoint edits** a shipment, but only within a **~4 hr window** after shipping.
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

- **DXM owns fulfillment — don't ack/ship routinely from the agent.** It double-fulfills (duplicate tracking, oversell). Monitor by default; write only on human approval.
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
