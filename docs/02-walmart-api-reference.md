# 02 — Walmart Marketplace API Reference (US)

Complete seller‑facing API surface, grouped by function. **Base host:** `https://marketplace.walmartapis.com` (sandbox `https://sandbox.walmartapis.com`, send header `WM_SANDBOX: v2`). All paths are under `/v3`.

> The developer portal renders client‑side, so a few exact field spellings / numbers below were corroborated from Walmart's Postman collection and the `highsidelabs/walmart-api-php` + `api-evangelist` OpenAPI mirrors and are flagged. Always confirm exact request/response schemas against a live sandbox call before coding.

## Common request headers (every call)

| Header | Required | Value |
|---|---|---|
| `WM_SEC.ACCESS_TOKEN` | ✅ | OAuth2 access token from `POST /v3/token` |
| `WM_QOS.CORRELATION_ID` | ✅ | A unique GUID per request (for tracing) |
| `WM_SVC.NAME` | ✅ | `Walmart Marketplace` |
| `WM_CONSUMER.CHANNEL.TYPE` | optional | channel identifier |
| `Accept` / `Content-Type` | ✅ | `application/json` (XML accepted on some legacy feeds) |

## Throttling model (applies to all groups)

- **Per‑API token bucket.** Each endpoint has its own bucket; limits are **per‑seller** (direct integrations and Solution Providers get separate allotments). Published numbers are defaults and can vary per account.
- **429 Too Many Requests** when a bucket is empty; **413 Payload Too Large** for oversized feeds.
- Every response carries **`x-current-token-count`** (tokens remaining) and **`x-next-replenish-time`** / **`X-Next-Replenishment-Time`** (casing is inconsistent across Walmart's own pages — match case‑insensitively). On 429: stop calling that API, sleep until replenishment, resume with **exponential backoff + jitter**; ideally run a client‑side token bucket to stay under proactively.

---

## A. Authentication / Token API

| Operation | Method / Path | Notes |
|---|---|---|
| Get access token | `POST /v3/token` | `grant_type=client_credentials` (direct seller) or `authorization_code`/`refresh_token` (delegated/OAuth app) |

- **Auth:** HTTP **Basic** `base64(clientId:clientSecret)` in `Authorization`.
- **Body (seller):** `grant_type=client_credentials` (form‑encoded).
- **Response:** `{ access_token, token_type: "Bearer", expires_in: 900 }` → **15‑minute** TTL. Refresh tokens (OAuth app flow) last ~1 year.
- **Best practice:** cache the token (shared store), **refresh proactively at ~80% TTL (~12 min)**, single‑flight the refresh so concurrent workers don't stampede the token endpoint. No published RPM cap — TTL caching *is* the rate management.
- **Legacy:** the old digital‑signature auth (`WM_SEC.AUTH_SIGNATURE`, `WM_SEC.TIMESTAMP`, `WM_CONSUMER.ID`) is **deprecated**. Use OAuth.

---

## B. Items / Catalog (Item Management)

Listing creation is **feed‑based and asynchronous** — even a single item goes through the feed pipeline. There is **no synchronous create/update**; reads, retire, and search are synchronous.

### Listing creation flow

```
1. Search the global catalog → decide match vs full setup
     GET /v3/items/walmart/search?query=… | UPC=… | GTIN=… | ASIN=…&responseFormat=SPEC
2. Download the spec for your product type(s)
     POST /v3/items/spec   body: { feedType, version, productTypes:[…≤20…] }   → JSON Schema
3. Submit the feed
     POST /v3/feeds?feedType=MP_ITEM (or MP_ITEM_MATCH)   → { feedId }
4. Poll feed status
     GET /v3/feeds/{feedId}?includeDetails=true   RECEIVED → INPROGRESS → PROCESSED|ERROR
5. Inspect per-item ingestionStatus (DATA_SUCCESS/SUCCESS vs ERROR)
6. Confirm publish separately (feed PROCESSED ≠ item PUBLISHED)
     GET /v3/items/{sku}   → publishedStatus
```

> A bulk create/update can take **up to ~4 hours**. Recommended polling: 15 min, 1 hr, 2 hr, then every 4 hr. Always verify publish status separately.

### Feed types (items)

| `feedType` | Purpose |
|---|---|
| `MP_ITEM` | Full new item setup (product content + your offer) |
| `MP_ITEM_MATCH` | Offer‑only setup against an existing Walmart catalog product |
| `MP_MAINTENANCE` | Update/maintain existing items |
| `MP_WFS_ITEM` | Items fulfilled by WFS |
| `OMNI_WFS` | Convert an existing seller‑fulfilled item to WFS |
| `RETURNS_OVERRIDES` | Bulk returns settings/overrides |
| `lagtime` | Fulfillment lag time |
| `price` / `promo` | **Legacy** (replaced by `PRICE_AND_PROMOTION`) |

### Endpoints

| Operation | Method / Path | Rate limit | Notes |
|---|---|---|---|
| Bulk item setup | `POST /v3/feeds?feedType=MP_ITEM` | **10/hr**, ≤25 MB (docs also say ≤10 MB for speed), ≤10,000 items | returns `feedId` |
| Get an item | `GET /v3/items/{id}` | 900/min (60/min w/ query params) | `productIdType=SKU\|GTIN\|UPC\|EAN\|ISBN\|ITEM_ID` |
| Get all items | `GET /v3/items` | 300/min (60/min w/ params) | pagination: `nextCursor=*` first call, then echo returned cursor; or `offset`+`limit` |
| Item count | `GET /v3/items/count` | — | by status |
| Retire an item | `DELETE /v3/items/{sku}` | 900/min | URL‑encode the SKU; takes up to 48 hr to remove |
| Bulk item retire | (bulk delete API) | — | batch retirement |
| Global catalog search | `GET /v3/items/walmart/search` | — | `query`/`UPC`/`GTIN`/`ASIN`, `responseFormat=SPEC\|DEFAULT` |
| Own‑catalog search | `POST /v3/items/catalog/search` | — | filter your own listings; cursor expires in 2 min |
| Get spec | `POST /v3/items/spec` | ~3–10/min (sources conflict) | returns per‑product‑type JSON Schema |
| Taxonomy | `GET /v3/utilities/taxonomy?feedType=…&version=…` | — | valid categories for a spec version |
| Feed statuses (all) | `GET /v3/feeds` | 5000/min | `feedId`, `offset`, `limit` |
| Feed item status | `GET /v3/feeds/{feedId}?includeDetails=true` | 5000/min | per‑item `ingestionStatus` + errors |

### MP_ITEM payload shape (Item Spec 5.0)

- `MPItemFeedHeader` — once per feed: `locale: "en"`, `version` (exact spec string, e.g. `5.0.20260205-…-api`), `businessUnit: "WALMART_US"`.
- `MPItem[]` — each item has:
  - **`Orderable`** — offer/identity: `sku`, `productIdentifiers` (`productId`+`productIdType`), `productName`, `brand`, price fields, `ShippingWeight` + dimensions, `condition`, conditional flags (`isChemical`/`isAerosol`/`releaseDate`).
  - **`Visible`** — product‑type‑specific content: `shortDescription`, `material`, `mainImageUrl`, `productSecondaryImageURL`, warranty/netContent, Prop‑65 flags, etc.

### Item Spec 5.0 notes

- Current version is **5.0** (4.0 sunset 2024‑10‑31). Three attribute tiers: **required** (publish blocks if missing), **highly recommended** (affects ranking/Buy Box), **optional**. Country‑of‑Origin became mandatory from `5.0.20250612‑…`. Always call **Get Spec** for the live version string.
- **Maintenance gotchas:** Country of Origin **cannot be updated** via `MP_MAINTENANCE` once set (delete + wait 48 hr + recreate). Some attributes can't be edited in maintenance.

### Images / rich media

- **Standard images = public URLs in the feed** (`mainImageUrl`, `productSecondaryImageURL`, `swatchImage`). URL must point to a loadable image file (`.jpg`/`.png`), not an HTML page.
- **Requirements:** JPEG/PNG/BMP (no GIF), 1:1 square, recommended 2200×2200 (min 1500×1500 for zoom), ≤5 MB, pure‑white main‑image background; ≥4 images recommended.
- **Enhanced rich media** (video, 360° spin, A+‑style below‑the‑fold) is **not** in the feed — via Seller Center or approved providers (Salsify, Syndigo, SellCord).

---

## C. Inventory

Single‑item and per‑node updates are synchronous PUTs; large catalogs use async feeds. **WFS inventory is read‑only** (Walmart controls it). SKUs must exist (via Item API) before setting inventory.

| Operation | Method / Path | Rate limit | Notes |
|---|---|---|---|
| Update inventory (single) | `PUT /v3/inventory?sku={sku}[&shipNode=…]` | ~200/min | body `{ sku, quantity:{unit:"EACH", amount}, inventoryAvailableDate? }` |
| Get inventory (single) | `GET /v3/inventory?sku={sku}[&shipNode=…]` | ~200/min | returns qty + lag time |
| Get multi‑node (one SKU) | `GET /v3/inventories/{sku}[?shipNode=…]` | ~200/min | `nodes[]` per‑node ATS |
| Get all SKUs/all nodes | `GET /v3/inventories` | ~200/min | `limit` (max 50) + `nextCursor` |
| Update multi‑node (one SKU) | `PUT /v3/inventories/{sku}` | ~200/min | body `{ inventories:{ nodes:[{ shipNode, inputQty:{unit,amount} }] } }` |
| Bulk inventory (single node) | `POST /v3/feeds?feedType=inventory` | ~10/hr, ≤10 MB | spec 1.4; XML/JSON; `shipNode` param |
| Bulk inventory (multi‑node) | `POST /v3/feeds?feedType=MP_INVENTORY` | ~50/hr, ~1 MB | spec 1.5; JSON only |
| WFS inventory (read) | `GET /v3/fulfillment/inventory` | ~100/min | `sku`, `from/toModifiedDate`, `limit` (max 300), `offset`; fields `availToSellQty`, `onHandQty`, `shipNodeType`, `modifiedDate` |

**Lag time** (order‑to‑ship days; most items 0–1, ≥2 needs category approval): bulk feed `POST /v3/feeds?feedType=lagtime` (~6/day), validate via `GET /v3/lagtime`; can also be carried in the `inventory` feed alongside quantity.

---

## D. Price, Promotions & Repricer

Three layers: direct price update (sync single + async bulk), promotional pricing, and Walmart's **native server‑side Repricer**.

### Single & bulk price

| Operation | Method / Path | Rate limit | Notes |
|---|---|---|---|
| Update price (single) | `PUT /v3/price` | **100/hr** | `promo` (bool, default true), `replaceAll` |
| Bulk price + promotion | `POST /v3/feeds?feedType=PRICE_AND_PROMOTION` | **10/hr** (shared), ≤10k items, ≤10 MB | current path; replaced legacy `price`/`promo` |
| Get promo prices (SKU) | `GET /v3/promo/sku/{sku}` | ~1000/min | current promotional prices |

**`PUT /v3/price` body** — `sku`, optional `offerId`/`replaceAll`, and `pricing[]` of:
- `currentPrice {currency, amount}`, `currentPriceType` (`BASE`|`REDUCED`|`CLEARANCE`)
- `comparisonPrice {…}` + `comparisonPriceType` (strikethrough "comp at")
- `priceDisplayCodes` (`CART` = MAP/hide‑until‑cart, or `CHECKOUT`)
- `effectiveDate` / `expirationDate` (ISO‑8601 UTC, for promos)
- `processMode` (`UPSERT` | `DELETE`)

Response 200: *"It may take up to five minutes to reflect on the site."*

**Promotion business rules:** ≤10 promos/SKU; start ≥30 min in the future (UTC); end after start; ≤180‑day duration; no overlapping ranges for a SKU; `Reduced` promos require ≥14‑day duration; delete requires exact start/end match.

### Native Repricer — `/v3/repricer/strategy`

Walmart adjusts your live price server‑side against competitive signals (15 min–4 hr cadence; doesn't change shipping). Accept the Repricer terms in Seller Center first.

| Operation | Method / Path | Rate limit |
|---|---|---|
| Create strategy | `POST /v3/repricer/strategy` | ~20/hr |
| List strategies | `GET /v3/repricer/strategy` | list ~50/hr; details ~10/min |
| Update strategy | `PUT /v3/repricer/strategy/{strategyCollectionId}` | ~10/hr |
| Delete strategy | `DELETE /v3/repricer/strategy` | ~10/hr |
| Assign / unassign / pause items | `POST /v3/repricer/strategy/assign \| /unassign \| /pause` | — |

- **Rule types:** **Buy Box** (meet/beat the winning Buy Box price), **External Price** (meet/beat lowest external‑site price), **Competitive Price** (Walmart‑recommended; the current UI labels it "Walmart Buy Box and external retailers" — beat whichever is lower). Walmart also offers an optional **AI‑powered strategy** (eligibility‑gated) that auto‑optimizes within your min/max.
- **Strategy fields:** `adjustmentValue` (≥0), `adjustmentType` (`UNIT`|`PERCENTAGE`), `enabled`, `enableRepricerForPromotion`, `restoreSellerPriceWithoutTarget` (hold last price when no competitor — default false), `enableBuyboxMeetExternal`, `compareWith3pOfferOnly`, `repricerStrategy` (name string).
- **Mandatory per‑item bounds:** `minimumSellerAllowedPrice` + `maximumSellerAllowedPrice` — the Repricer never prices outside them. Can also be set at item setup via the `automate_pricing` block.

> ⚠️ The exact create‑body field names (e.g. whether the rule field is `ruleType`/`strategyType` with enums) couldn't be fully confirmed from the JS‑rendered reference — verify against the live Postman collection / `/reference/createstrategy` before coding.

### Competitive signals for a self‑driven repricer

- **BUYBOX on‑request report** (see Reports): columns `SKU`, `Seller Item Price`, `Seller Ship Price`, **`isSellerBuyBoxWinner`**, **`BuyBox Item Price`**, **`BuyBox Ship Price`**. Near‑real‑time, whole catalog.
- **Buy Box change webhook** (Notifications): fires when the Buy Box owner changes — react without polling.
- **Caveat:** the API exposes only the current Buy Box holder + partial offer metadata, **not** the full competitor stack; some tools supplement with scraped/competitive‑match data.

---

## E. Orders

Synchronous JSON with cursor pagination. Order actions are direct POSTs (no feed). Status is tracked **per order line**: Created → Acknowledged → Shipped → Delivered, plus Cancelled / Refund.

| Operation | Method / Path | Rate limit | Notes |
|---|---|---|---|
| Get released orders | `GET /v3/orders/released` | 60/min | Created‑status work queue; `createdStartDate` required; WFS orders auto‑advance and are excluded |
| Get all orders | `GET /v3/orders` | 5000/min | filters: `status`, `sku`, `customerOrderId`, `purchaseOrderId`, dates; cursor — subsequent calls use **only** `nextCursor` |
| Get an order | `GET /v3/orders/{purchaseOrderId}` | 5000/min | full detail incl. per‑line `orderLineStatuses` + tracking |
| Acknowledge | `POST /v3/orders/{poId}/acknowledge` | 60/min | body usually empty; **SLA: ack within 4 hr** |
| Ship | `POST /v3/orders/{poId}/shipping` | 60/min | upload tracking (see below); same call edits a shipment |
| Cancel | `POST /v3/orders/{poId}/cancel` | 60/min | `cancellationReason` per line; can't cancel Shipped lines |
| Refund | `POST /v3/orders/{poId}/refund` | 60/min | `refunds[]` with **negative** `chargeAmount`; `chargeType` PRODUCT/SHIPPING |

**Shipping update — required per line** (`orderShipment` → `orderLines.orderLine[]`):
- `status: "Shipped"`, `statusQuantity {unitOfMeasurement:"EACH", amount}`
- `trackingInfo`: `shipDateTime` (**epoch ms UTC**), `carrierName {carrier:"UPS"}` or `{otherCarrier:"…"}`, `methodCode` (Value/Standard/Express(TwoDay)/OneDay/Freight/WhiteGlove), `trackingNumber`, `trackingURL` (required for `otherCarrier`).

**SLAs / auto‑cancel:** ship by Expected Ship Date (driven by lag time, ~2 operational days); Walmart **auto‑cancels** orders not shipped‑with‑tracking by **Expected Ship Date + 4 calendar days** (no reimbursement for late ones). Tracking edits allowed only ~4 hr after marking shipped (disabled after first carrier scan). The **60/min action limit** is the practical bottleneck for high volume — batch lines within one PO call.

---

## F. Returns & post‑order servicing

Two surfaces: Marketplace Returns (`/v3/returns/*`, seller‑fulfilled) and WFS/MCS Fulfillment Returns (`/v3/fulfillment/return-orders`). **For WFS, returns/refunds are view‑only (Walmart drives them).**

| Operation | Method / Path | Notes |
|---|---|---|
| Get returns | `GET /v3/returns` | filters `returnOrderId`, `customerOrderId`, `status` (INITIATED/DELIVERED/COMPLETED), `returnType` (REPLACEMENT/REFUND), dates, `limit` (max 200); `isWFSEnabled=Y` to include WFS |
| Issue refund (return) | `POST /v3/returns/{returnOrderId}/refund` | only **Shipped** lines; **negative** amount; can't exceed original charge; **not** for WFS |
| Returns overrides (bulk) | `POST /v3/feeds?feedType=RETURNS_OVERRIDES` | async; Keep‑It / Partial Keep‑It, Return Restricted, Return Center |
| Create return (WFS/MCS) | `POST /v3/fulfillment/return-orders` | for Walmart‑fulfilled orders; `sellerReturnOrderId` for idempotency |
| WFS return status | `GET /v3/fulfillment/return-orders` | `limit`, `offset`, `from/toOrderDate` |

- **No public seller‑fulfilled "create return"** — those are created by the customer/Customer Care and surface via `getReturns`.
- **Reship** = the **replacement order** flow (`orderType=REPLACEMENT` with `replacementInfo.originalCustomerOrderID`); fulfill it like a normal order.
- **Policy:** ≥30‑day window starting 7 days after ship; refund on first carrier scan of the return; sellers can't charge return shipping (Walmart's RSS default); refund within **48 hr** of receipt; disputes via Seller Center (~72 hr hold, one appeal within 30 days). Non‑standard/partial refunds via the **Adjustments dashboard** (can't refund until all lines shipped/completed).

---

## G. WFS / Fulfillment / Multichannel (MCS)

WFS = Walmart's FBA: send stock to Walmart FCs; Walmart picks/packs/ships + handles customer service & returns.

**Item setup:** `POST /v3/feeds?feedType=MP_WFS_ITEM` (new WFS items), `feedType=OMNI_WFS` (convert existing).

**Inbound shipments:**
| Operation | Method / Path |
|---|---|
| Create inbound shipment | `POST /v3/fulfillment/inbound-shipments` |
| Inbound errors | `GET /v3/fulfillment/inbound-shipment-errors` |
| Get inbound shipments | `GET /v3/fulfillment/inbound-shipments` |
| Get inbound items | `GET /v3/fulfillment/inbound-shipment-items` |
| Update shipment qty | `PUT /v3/fulfillment/shipment-quantities` |
| Cancel inbound | `DELETE /v3/fulfillment/inbound-shipments/{inboundOrderId}` |
| Inbound preview | `POST /v3/fulfillment/inbound-preview` |
| Shipment label (v2) | `POST /v3/fulfillment/shipment-label` |
| Update parcel tracking | `POST /v3/fulfillment/shipment-tracking` |

> Walmart shipped a **new WFS Preferred‑Carrier API** (parcel + LTL: Create/Get/Cancel Booking, Generate/Download Label, Bill of Lading, Pickup Schedule) superseding the legacy `carrier-rate-quotes` calls. Exact new `/v3/...` paths aren't cleanly exposed on the JS portal — verify against the live OpenAPI/Postman.

**WFS inventory:** `GET /v3/fulfillment/inventory` (ATS), `GET /v3/report/wfs/getInventoryHealthReport`, `GET /v3/fulfillment/inventory-log`. ATS = available to sell; buckets: Unavailable, Reserved, Inbound.

**Multichannel (MCS)** — WFS fulfills Amazon/eBay/Temu/etc.:
| Operation | Method / Path |
|---|---|
| Create customer (fulfillment) order | `POST /v3/fulfillment/orders-fulfillments` |
| Get fulfillment order status | `GET /v3/fulfillment/orders-fulfillments/status` |
| Fetch delivery promise | `POST /v3/fulfillment/orders-fulfillments/fetchOrderPromiseOptions` |
| Cancel customer order | `POST /v3/fulfillment/orders-fulfillments/cancel` |

**Settings (ship nodes & shipping templates, seller‑fulfilled):** `…/v3/settings/shipping/shipnodes` (CRUD + coverage), `…/3plshipnodes`, `…/3plproviders`, `…/templates` (CRUD), `…/carriers`, `…/shippingprofile`.

Indicative WFS rate limits: Create inbound shipment 500/min; Create customer order 600/min; Get shipments 32/min; Create carrier rate quote 8/min.

---

## H. Reports, Insights & Settlement

### On‑request Reports (async job)

```
POST /v3/reports/reportRequests?reportType={TYPE}&reportVersion={VER}   → { requestId }
GET  /v3/reports/reportRequests/{requestId}    RECEIVED → INPROGRESS → READY|ERROR
GET  /v3/reports/downloadReport?requestId={requestId}   → file (CSV)
```
- Optional POST body: `rowFilters`, `excludeColumns`, `dataStartTime`/`dataEndTime`. Generation ~15–45 min; requests retained 30 days. A **Reports Scheduler** supports recurring generation.
- **Report types:** `ITEM` (v4, incl. `BuyBoxEligible`), `INVENTORY`, `ITEM_PERFORMANCE` (GMV, units, conversion, visits), **`BUYBOX`** (competitive Buy Box data), `CANCELLATION` (poNum, cancelReason, dates), `PROMO`, `RETURN_ITEM_OVERRIDES`, plus `DELIVERY_DEFECT`, `LAG_TIME`, `SHIPPING_CONFIGURATION`, WFS reports.

### Insights / Growth (synchronous JSON)

| Operation | Path | Returns |
|---|---|---|
| Listing Quality score | `GET /v3/insights/items/listingQuality/score` | `overAllQuality` (0–100), `offerScore`, `contentScore`, `ratingReviewScore`, `defectRatio` |
| Unpublished item count | (insights) | count per reason code + cost |
| Unpublished items | (insights) | item details by reason (e.g. Pricing Error, Reasonable Price Not Satisfied) → republish/fix |
| Assortment recommendations | `/v3/growth/assortment/recommendations` | Customer‑Favorites to add, variants, trends, categorization; `Reject` to suppress |
| Pro Seller status | (pro‑seller API) | tier (Rising/Advanced/Pro) + rewards; refreshes 5th & 20th |
| Seller Performance | (seller‑performance API) | OTD/OTS, VTR, cancellations, returns, item‑not‑received, negative feedback (summary JSON + `.xlsx` report; 14/30/60/90‑day windows) |

### Settlement / reconciliation (date‑driven, synchronous)

| Operation | Path | Format |
|---|---|---|
| Available recon dates | `GET /v3/report/reconreport/availableReconFiles[?reportVersion=v1]` | — |
| Recon report (CSV) | `GET /v3/report/reconreport/reconFile[?reportVersion=v1]` | CSV stream |
| Recon report (JSON) | `GET /v3/report/reconreport/reconFileJson` | JSON (`reportData[]`, `nextOffset`) |
| Payment statement | `GET /v3/report/payment/statement` | — |
| Payment performance | `GET /v3/report/payment/performance` | — |

- Fields: gross sales/shipping, commission/referral fees, payment‑processing fees, **WFS fees**, tax, refunds/adjustments, `Excess Refund Adjustment`, net payout; per record `Transaction Type`, `Purchase Order #`, `Partner Item Id` (SKU), `Fulfillment Type` (Seller/WFS).
- **Cadence:** **bi‑weekly (14‑day)** settlement; period closes 11:59 PM PT, recon generated ~day 8, payout follows. Established/Pro sellers can get ~7‑day cycles. (A2X/Sellercloud post one summarized journal entry per settlement for accounting reconciliation.)

---

## I. Notifications / Webhooks (push)

Walmart **does** push events ("Notifications, also known as webhooks") — layer on top of poll APIs to cut polling.

| Operation | Purpose |
|---|---|
| Get Event Types | list available events + resource names (ITEM, INVENTORY, ORDER, RETURN, REPORTS…) |
| Create Subscription | register callback URL for selected events |
| Update / Delete Subscription | manage subscriptions |
| Test Notification | send a sample payload to validate your endpoint |

- **Event types:** **PO created**, PO line auto‑canceled, **Returns**, Order intent to cancel, Order management, **Inventory OOS**, **Buy Box**, Offer published/unpublished, **Report status** (`resourceName=REPORTS`, `eventType=REPORT_STATUS`), Assortment recommendations, Driver status; plus **Performance webhooks** (warnings/reports).
- **Delivery:** Walmart POSTs the payload; your endpoint must **ack 2xx after a durable write**, else Walmart **retries 3×** at +5 / +15 / +45 min. Dedupe on the delivery `eventId`. **No ordering guarantee** — reconcile against live state before acting. Verify request signatures.

---

## J. Walmart Connect (Advertising) — separate program

- Sponsored Search/Products, Sponsored Brands, Display Ads APIs (campaigns, ad groups, keywords/bids, reporting).
- **Partner‑gated** (WCPN) — not self‑serve; your Marketplace keys don't unlock it.
- Production base: `https://developer.api.walmart.com/api-proxy/service/WPA/Api/v1/`.

---

## Deprecations to watch

- **Delegated Access** keys: gone after 2026‑10‑01 (migrate to OAuth 2.0). (See `01`.)
- Legacy `feedType=price` / `feedType=promo` → use `PRICE_AND_PROMOTION`.
- Legacy WFS `GET /v3/fulfillment/label/{shipmentId}` + legacy carrier‑rate‑quote calls → use `POST /v3/fulfillment/shipment-label` + the new Preferred‑Carrier booking flow.
- Item Spec 4.x → 5.0.
- Pro Seller API v1 deprecated 2025‑07‑31 → new Pro Seller API.

Full source URLs per group: see `99-sources.md`.
