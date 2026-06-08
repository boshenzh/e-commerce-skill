# Walmart Marketplace API — condensed endpoint map

Full version with payloads: `../../../docs/02-walmart-api-reference.md`. Base host `https://marketplace.walmartapis.com` (sandbox `https://sandbox.walmartapis.com` + `WM_SANDBOX: v2`). All paths `/v3/...`. Throttle = per‑API token bucket → `429` + headers `x-current-token-count` / `x-next-replenish-time`.

## Auth
- `POST /v3/token` — `grant_type=client_credentials`, Basic auth, token TTL 900s.

## Items / Catalog (feed‑based, async)
- `GET /v3/items/walmart/search` — find a catalog match (`query`/`UPC`/`GTIN`/`ASIN`, `responseFormat=SPEC`). → match ⇒ `MP_ITEM_MATCH`, else `MP_ITEM`.
- `POST /v3/items/spec` — get per‑product‑type JSON Schema (Item Spec **5.0**). `GET /v3/utilities/taxonomy` — categories.
- `POST /v3/feeds?feedType=MP_ITEM|MP_ITEM_MATCH|MP_MAINTENANCE|MP_WFS_ITEM|OMNI_WFS` — submit; returns `feedId`. **10/hr, ≤25 MB.**
- `GET /v3/feeds/{feedId}?includeDetails=true` — poll; `RECEIVED→INPROGRESS→PROCESSED|ERROR`; walk per‑item `ingestionStatus`.
- `GET /v3/items` (paginate with `nextCursor=*`, or `limit`+`offset`; `limit=1` works for a quick probe) / `GET /v3/items/{id}` / `DELETE /v3/items/{sku}` (retire). **Feed PROCESSED ≠ item PUBLISHED** — verify `publishedStatus`. Response: `ItemResponse[]` with `sku`, `wpid`, `upc/gtin`, `productName`, `productType`, `price`, `publishedStatus`, `unpublishedReasons`.

## Inventory (DXM owns this — read‑mostly here)
- `PUT /v3/inventory?sku=` `{quantity:{unit:"EACH",amount}}` (~200/min) · `GET /v3/inventory`.
- Multi‑node: `GET|PUT /v3/inventories/{sku}` · `GET /v3/inventories`.
- Bulk feeds: `feedType=inventory` (single node, 10/hr) · `MP_INVENTORY` (multi, ~50/hr).
- WFS inventory **read‑only**: `GET /v3/fulfillment/inventory` (ATS).
- Lag time: feed `lagtime` · `GET /v3/lagtime`.

## Price / Promotions / Repricer
- `PUT /v3/price` (single, **100/hr**) — `pricing[]` w/ `currentPrice`, `currentPriceType` (BASE/REDUCED/CLEARANCE), `comparisonPrice`, `priceDisplayCodes`, `effective/expirationDate`, `processMode`.
- `POST /v3/feeds?feedType=PRICE_AND_PROMOTION` (**10/hr**, ≤10k items) — bulk; replaced legacy `price`/`promo`.
- Native **Repricer** `/v3/repricer/strategy` (create ~20/hr; assign/unassign/pause) — rule types Buy Box / External / **Competitive (Walmart‑recommended)**, plus an optional eligibility‑gated AI strategy; **per‑item `minimumSellerAllowedPrice` + `maximumSellerAllowedPrice` mandatory**; 15 min–4 hr cadence. (`PUT /v3/price` may take ~5 min to reflect.)
- Promo prices: `GET /v3/promo/sku/{sku}`.

## Orders (DXM owns fulfillment — monitor here)
- `GET /v3/orders/released?createdStartDate=YYYY-MM-DD` (work queue, `createdStartDate` required, 60/min) · `GET /v3/orders` (all, cursor, 5000/min) · `GET /v3/orders/{poId}`. Response: `list.meta.{totalCount,limit,nextCursor}` + `list.elements.order[]`.
- Actions (60/min each): `POST …/acknowledge` (SLA **4 hr**), `POST …/shipping` (tracking: `shipDateTime` epoch‑ms, **`carrierName` is an object** `{"carrier":"UPS"}` or `{"otherCarrier":"…"}`, `methodCode`, `trackingNumber`; same call edits), `POST …/cancel`, `POST …/refund` (negative amounts).
- Auto‑cancel if not shipped by Expected Ship Date + 4 days.

## Returns
- `GET /v3/returns` (`isWFSEnabled=Y`) · `POST /v3/returns/{returnOrderId}/refund` (Shipped lines only, negative; **WFS = view‑only**).
- Overrides: `feedType=RETURNS_OVERRIDES`. Reship = `orderType=REPLACEMENT` order.

## WFS / Fulfillment / MCS
- Inbound: `POST /v3/fulfillment/inbound-shipments` (body `{inboundOrderId, returnAddress, orderItems[]{productId, productType, sku, itemQty:{unit:"EACH", amount}}}` — confirm exact shape on live), `…/inbound-shipment-errors`, `…/inbound-shipment-items` (scope by shipment/order id), `DELETE …/{inboundOrderId}`, label `POST /v3/fulfillment/shipment-label`. **Quantity unit is `EACH`** (same convention as inventory/orders).
- WFS inventory: `GET /v3/fulfillment/inventory`, `GET /v3/report/wfs/getInventoryHealthReport`.
- Multichannel: `POST /v3/fulfillment/orders-fulfillments` (WFS fulfills Amazon/eBay/Temu…).
- Settings (seller‑fulfilled): `/v3/settings/shipping/{shipnodes,templates,carriers}`.

## Reports / Insights / Settlement
- On‑request: `POST /v3/reports/reportRequests?reportType=ITEM|INVENTORY|ITEM_PERFORMANCE|BUYBOX|CANCELLATION|PROMO` → poll → `GET /v3/reports/downloadReport`.
- Insights: `GET /v3/insights/items/listingQuality/score` (score is **0–100**: `overAllQuality` + content/offer/discoverability/ratings sub‑scores — confirm exact JSON keys on live); unpublished‑item reasons; `/v3/growth/assortment/recommendations` (read: Customer‑Favorites/in‑demand items, variants, trends, categorization by BRAND/CATEGORY, + a Reject action); Pro Seller status (legacy v1 retired mid‑2025 — use the current API; confirm the exact path on live); Seller Performance summaries.
- Settlement: `GET /v3/report/reconreport/{availableReconFiles,reconFileJson}` (bi‑weekly payout).

## Notifications / Webhooks (push)
- `Get Event Types` · `Create/Update/Delete Subscription` · `Test Notification`.
- Events: **PO created**, PO line auto‑canceled, **Returns**, Order intent to cancel, Order management, **Inventory OOS**, **Buy Box**, Offer published/unpublished, **Report status**, Assortment recs, Driver status; + Performance webhooks.
- Ack **2xx after durable write** or Walmart retries 3× (+5/+15/+45 min). Dedupe on `eventId`; no ordering guarantee.

## Walmart Connect ads (separate, partner‑gated)
- `developer.api.walmart.com/api-proxy/service/WPA/Api/v1/` — WCPN partners only; marketplace keys don't unlock it.

## Uncertain / verify against live sandbox
Repricer create‑body field names; exact recon CSV columns; new WFS Preferred‑Carrier paths; Get Spec throttle (3 vs 10/min). Always confirm exact request/response shapes before coding (the portal is JS‑rendered).
