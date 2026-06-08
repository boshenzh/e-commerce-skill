---
name: walmart-product-research
description: "Find winning/high-demand products (爆款) to sell on Walmart using Walmart's own demand signals. Use when: 'find products to sell on Walmart', 'what's selling well on Walmart', 'find a 爆款', 'product research / opportunity analysis', 'what should I add to my catalog', 'Walmart best sellers', '选品', '找爆款'."
author: "boshenzh"
license: "Apache-2.0"
version: "0.1.0"
allowed-tools: "Read Bash"
---

# Walmart Product Research — find 爆款 from Walmart's own demand signals

Spoke of the `walmart-seller` hub. There is **no public Walmart "best sellers / BSR" API**. You triangulate demand from three sanctioned sources: Walmart's **assortment recommendations** (the primary signal), **catalog search** (competition + price band), and **your own Item Performance** report (what already converts). Read the hub first: [`../walmart-seller/SKILL.md`](../walmart-seller/SKILL.md). All calls go through the authenticated helper — `WALMART_CLIENT_ID/SECRET/ENV` must be exported (see hub Access model).

## When to use / when not to

- **Use** to source new SKUs, validate a product idea against real demand, or find adjacent winners to your current catalog.
- **Not** for listing/creating the chosen item — hand the shortlist to `walmart-listings`. Not for repricing an existing SKU — that's `walmart-buybox-pricing`.
- **Read-mostly skill.** This skill makes **no writes** except `Reject`-ing an irrelevant assortment recommendation. No price/inventory writes — so the pricing guardrails don't gate normal use here.

## The four sanctioned signals (which endpoint gives what)

| Signal | Endpoint | Tells you |
|---|---|---|
| **Demand to add** (primary) | `GET /v3/growth/assortment/recommendations` | "Customer Favorites" / in-demand items to add, preferred variants, demand & price trends, grouped by **BRAND** or **CATEGORY**. `Reject` irrelevant ones. |
| **Competition + price band** | `GET /v3/items/walmart/search` (`query`/`UPC`/`GTIN`) | how many sellers/offers exist on a candidate → demand vs. saturation. |
| **Category map** | `GET /v3/utilities/taxonomy` + `productType`/`shelf` fields | where a product lives; which categories you can pull recs for. |
| **What already converts (yours)** | `ITEM_PERFORMANCE` report | GMV, units, conversion rate, total product visits per SKU → double down on winners + adjacencies. |
| **How contested a SKU is** | `BUYBOX` report | competitor count + winning price on a SKU. |

Exact request/response shapes and throttles: [`../walmart-seller/references/api-reference.md`](../walmart-seller/references/api-reference.md) (§ Items/Catalog, § Reports/Insights).

## Workflow

1. **Pull assortment recommendations** for your categories — start here, it IS Walmart's demand signal:
   `python3 ../walmart-seller/scripts/wm_request.py GET '/v3/growth/assortment/recommendations'`
   Group by CATEGORY or BRAND; note demand/price trend on each. `Reject` ones irrelevant to your store so the feed sharpens.
2. **Scout each candidate** with catalog search to gauge competition + the live price band:
   `python3 ../walmart-seller/scripts/wm_request.py GET '/v3/items/walmart/search?query=<keyword>'`
   Many existing offers = proven demand but thin margin; few/none = whitespace (or no demand — cross-check step 3).
3. **Cross-check your own performance.** Request an `ITEM_PERFORMANCE` report (`POST /v3/reports/reportRequests?reportType=ITEM_PERFORMANCE` → poll → `GET /v3/reports/downloadReport`). Find your high-conversion SKUs and source **adjacent** products in the same `shelf`/`productType`.
4. **Read price + taxonomy off your own catalog** to anchor margin math — `GET /v3/items?limit=1` returns `productType`, `shelf`, and `price:{currency,amount}` per item (verified working example below).
5. **Shortlist** items scoring **high demand × low competition × healthy margin** (price band from step 2 minus your landed cost). Record the evidence per pick (rec trend, offer count, your conversion data).
6. **Hand off to `walmart-listings`** to create the listing. Do not create it here.

## Working example (sandbox-verified)

`GET /v3/items?limit=1` is live-tested on the Walmart sandbox; use it as the canonical taxonomy/price scout:

```bash
python3 ../walmart-seller/scripts/wm_request.py GET '/v3/items?limit=1'
# → HTTP 200
# {"ItemResponse":[{"sku":"…","wpid":"…","upc":"…","gtin":"…",
#   "productName":"…","productType":"…","shelf":"…",
#   "price":{"currency":"USD","amount":…},
#   "publishedStatus":"…","unpublishedReasons":…}]}
```

Other sandbox-verified calls you can lean on: `GET /v3/orders/released?createdStartDate=2026-06-01` → 200 (`{"list":{"meta":{...},"elements":{"order":[...]}}}`); `GET /v3/inventory?sku=SAMPLE-SKU` → clean 404 `CONTENT_NOT_FOUND.GMP_INVENTORY_API` when the SKU is absent (use to confirm a SKU exists before deeper scouting).

## Gotchas

- **There is NO public best-sellers / BSR API.** Anyone expecting one is wrong — synthesize demand from assortment recs + search + your own Item Performance. Don't claim a ranking the API doesn't give.
- **Assortment recommendations are THE sanctioned demand signal — start there**, not with search. Search alone shows *supply* (offers), not *demand*.
- **Do NOT scrape walmart.com** for best-sellers/category rankings. Browser-scraping public Walmart pages without written consent **violates Walmart's Terms of Use** (hub guardrail). Stay on the API.
- **Assortment recs and insights endpoints may be limited on sandbox.** `GET /v3/items?limit=1` is confirmed; treat `/v3/growth/assortment/recommendations`, `ITEM_PERFORMANCE`, and `BUYBOX` as **"verify on production"** — don't claim a sandbox result for them.
- **Reports are async on-request**, not instant: `POST` to request → poll the request status → `GET /v3/reports/downloadReport`. Don't expect inline data.
- **Demand ≠ profit.** A hot rec with 40 existing offers may have no margin left. Always pair the demand signal with the search price band and your landed cost before shortlisting.

## Load deeper

- Endpoints/limits/response shapes: [`../walmart-seller/references/api-reference.md`](../walmart-seller/references/api-reference.md).
- If a candidate flows into a price write later, that's `walmart-buybox-pricing` — and **before any price write** read [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md) and run `../walmart-seller/scripts/guardrail_check.py`.
