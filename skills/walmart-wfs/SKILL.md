---
name: walmart-wfs
description: "Set up and operate Walmart Fulfillment Services (WFS) — Walmart's FBA equivalent: send inventory in, Walmart fulfills. Use when: 'set up WFS', 'is WFS worth it', 'send inventory to Walmart', 'create an inbound shipment', 'WFS benefits/fees', 'convert my items to WFS', 'check my WFS inventory', '沃尔玛官方仓', 'WFS入仓'."
author: "boshenzh"
license: "Apache-2.0"
version: "0.1.0"
allowed-tools: "Read Bash"
---

# Walmart WFS — managed fulfillment (inbound, inventory, multichannel)

Spoke skill. The hub [`../walmart-seller/SKILL.md`](../walmart-seller/SKILL.md) owns auth, the env vars (`WALMART_CLIENT_ID`/`WALMART_CLIENT_SECRET`/`WALMART_ENV`), the global safety rules, and the runnable helpers. Read it first if you haven't. WFS is Walmart's FBA equivalent: you send inventory to Walmart fulfillment centers (FCs); Walmart stores it, picks/packs/ships, and handles customer service + returns.

## When to use / when not to

- **Use** to enroll in WFS, convert items to WFS, create/track an inbound shipment, print box labels, read WFS inventory, or set up multichannel fulfillment (WFS shipping non-Walmart orders).
- **Not** for seller-fulfilled orders (that's `walmart-fulfillment-ops`) or pushing inventory quantities — **WFS inventory is Walmart-controlled and read-only here** (see Gotchas).
- **Worth-it decision is advisory:** WFS adds the "TwoDay" fast/free badge, boosts Buy Box win rate, is a Pro Seller eligibility path, and offloads CS + returns — but costs a **per-unit fulfillment fee + monthly storage fee** that erodes margin on slow movers. Recommend WFS for fast-moving, well-ranked SKUs; keep slow/heavy/low-margin SKUs seller-fulfilled. Lay out the tradeoff; let the human decide.

## Workflow

1. **Enroll** — opt into WFS in Seller Center (Fulfillment → WFS). One-time account-level setup; no API call.
2. **Convert / create items as WFS-eligible** — feeds (10/hr, async):
   - Convert *existing* items: `POST /v3/feeds?feedType=OMNI_WFS`.
   - Stand up *new* WFS items: `POST /v3/feeds?feedType=MP_WFS_ITEM`.
   - Poll `GET /v3/feeds/{feedId}?includeDetails=true` and confirm per-item `ingestionStatus` — **`PROCESSED` ≠ live**; read back the item.
3. **Create the inbound shipment** (payload below — confirm exact shape on live) — `POST /v3/fulfillment/inbound-shipments`.
4. **Check for errors, then print labels** — `GET /v3/fulfillment/inbound-shipment-errors`, then `POST /v3/fulfillment/shipment-label`. Box up, ship to the FC Walmart assigns.
5. **Monitor inventory health** — `GET /v3/fulfillment/inventory` (ATS) + `GET /v3/report/wfs/getInventoryHealthReport`. Watch for low/aging stock; replenish via a new inbound shipment.
6. **Orders fulfill automatically** — Walmart picks/packs/ships and runs CS/returns. Do **not** acknowledge/ship WFS orders from the agent.

## Working example — create an inbound shipment

```bash
cat > /tmp/wfs_inbound.json <<'JSON'
{
  "inboundOrderId": "INB-2026-0608-001",
  "returnAddress": {
    "name": "Acme Returns", "address1": "123 Warehouse Rd",
    "city": "Bentonville", "state": "AR", "postalCode": "72712", "country": "US"
  },
  "orderItems": [
    { "productId": "00012345678905", "productType": "GTIN",
      "sku": "ACME-WIDGET-BLK", "itemQty": { "unit": "EACH", "amount": 200 } }
  ]
}
JSON

python3 ../walmart-seller/scripts/wm_request.py POST \
  /v3/fulfillment/inbound-shipments --body @/tmp/wfs_inbound.json

# then check errors and print labels
python3 ../walmart-seller/scripts/wm_request.py GET  /v3/fulfillment/inbound-shipment-errors
# inbound-shipment-items must be scoped to a shipment/order (e.g. ?shipmentId=...) — confirm the param on live
python3 ../walmart-seller/scripts/wm_request.py GET  '/v3/fulfillment/inbound-shipment-items?shipmentId=...'
# shipment-label takes a request body built per the live spec (shipment/box identifiers) — construct it then pass --body @file
python3 ../walmart-seller/scripts/wm_request.py POST /v3/fulfillment/shipment-label --body @/tmp/label_req.json
```

Cancel a shipment before it ships: `DELETE /v3/fulfillment/inbound-shipments/{inboundOrderId}`.

## Multichannel (MCS) — WFS fulfills your other channels

WFS can ship orders from Amazon/eBay/Temu/etc. out of the same WFS stock:
`POST /v3/fulfillment/orders-fulfillments`. Useful to consolidate inventory in one FC pool.

## Gotchas

- **WFS inventory is READ-ONLY via API.** Never `PUT /v3/inventory` (or `MP_INVENTORY`/`inventory` feeds) for a WFS SKU — Walmart controls those quantities; the only way to add stock is an inbound shipment. Quantity pushes are for **seller-fulfilled** SKUs only. Don't let the DXM inventory sync touch WFS SKUs either.
- **Fees eat margin on slow movers.** Per-unit fulfillment fee + monthly storage. Long-resident inventory bleeds storage fees — use the inventory health report to flush aging stock before converting more SKUs.
- **The new Preferred-Carrier booking API supersedes the legacy carrier-rate-quote calls.** Don't build against the old rate-quote endpoints; verify the current Preferred-Carrier paths against a live call.
- **Sandbox is thin for fulfillment.** Several `/v3/fulfillment/*` endpoints are limited or stubbed on sandbox — verify behavior on production (with a tiny test shipment) before trusting responses.
- **Item conversion is a feed, not instant.** `OMNI_WFS`/`MP_WFS_ITEM` go through the async feed pipeline (10/hr, poll status); a `PROCESSED` feed doesn't mean the SKU is WFS-live — read the item back.

## Load deeper

- Exact endpoints, rate limits, and the WFS section: [`../walmart-seller/references/api-reference.md`](../walmart-seller/references/api-reference.md).
- Account-safety invariants (scorecard, write rules): [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md). Before ANY price write on a WFS SKU, read it and run `../walmart-seller/scripts/guardrail_check.py`.
- Authenticated calls: `../walmart-seller/scripts/wm_request.py` (auto token caching + 429 backoff).
