---
name: walmart-listings
description: "Create and optimize Walmart product listings via the feed-based item flow, and fix unpublished items. Use when: 'create a Walmart listing', 'list a product on Walmart', 'set up items on Walmart', 'fix my unpublished items', 'optimize my listing content', 'bulk upload products', '上架沃尔玛商品', '商品发布'. For pure search ranking tactics see walmart-seo; for price see walmart-buybox-pricing."
author: "boshenzh"
license: "Apache-2.0"
version: "0.1.0"
allowed-tools: "Read Bash"
---

# Walmart Listings — feed-based item setup, publish verification, and unpublished-item repair

Create or repair listings on Walmart Marketplace (US). Listings are **feed-based and async**: you submit a feed, it processes, items ingest individually, and publish status is a *separate* fact you must read back. This is a spoke of [`../walmart-seller/SKILL.md`](../walmart-seller/SKILL.md) — auth, env vars (`WALMART_CLIENT_ID/SECRET/ENV`), token caching, and rate-limit backoff all live there and are handled by `../walmart-seller/scripts/wm_request.py`.

## When to use / when not to

- **Use** to create a listing (new or offer-only match), optimize title/attribute content, bulk-upload, or diagnose why items are unpublished.
- **Not** for price or inventory — those have their **own feeds** and route to `walmart-buybox-pricing` and DXM respectively. Not for pure search-rank tactics (`walmart-seo`).
- **Read first** for exact endpoints/limits: [`../walmart-seller/references/api-reference.md`](../walmart-seller/references/api-reference.md). For content/IP/pricing-suppression rules: [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md).

## Workflow (PRESCRIPTIVE — follow the sequence; the async parts bite if you skip a step)

1. **Decide the path.** `GET /v3/items/walmart/search` with `query`/`UPC`/`GTIN`/`ASIN` and `responseFormat=SPEC`.
   - Catalog **match found** ⇒ `feedType=MP_ITEM_MATCH` (offer-only: you attach an offer to an existing item; minimal attributes).
   - **No match** ⇒ `feedType=MP_ITEM` (full content setup).
2. **Get the spec.** `POST /v3/items/spec` returns the per-product-type JSON Schema (Item Spec **5.0**) — required + highly-recommended attributes. Resolve the product type / category via `GET /v3/utilities/taxonomy`.
3. **Build a schema-valid feed.** Standard images are **URLs inside the feed** (`mainImageUrl`, `productSecondaryImageURL`): JPEG/PNG, 1:1 square, white background, **≥1500px** (verify current requirements). Enhanced/rich media (video, 360°) is **NOT** in the feed — handle it separately after the item exists.
4. **Gate content BEFORE submit** (see Content compliance below). Then submit: `POST /v3/feeds?feedType=MP_ITEM` → returns `feedId`. Limits: **10 feeds/hr, ≤25 MB.**
5. **Poll the feed.** `GET /v3/feeds/{feedId}?includeDetails=true`. Status walks `RECEIVED → INPROGRESS → PROCESSED | ERROR`. **Walk per-item `ingestionStatus`** — a `PROCESSED` feed can still contain individually failed items.
6. **Verify publish separately.** `GET /v3/items/{sku}` → check `publishedStatus`. **`feedStatus=PROCESSED` ≠ item `PUBLISHED`.** Do not report success off the feed status alone.

## Fixing unpublished items

1. Read the reasons: `GET /v3/items` (or `/v3/items/{sku}`) exposes `publishedStatus` + `unpublishedReasons`.
2. Map reason → fix:
   - **"Pricing Error"** (price too low) → raise the price toward the floor.
   - **"Reasonable Price Not Satisfied"** (too high vs Walmart's reference price) → lower toward the reference.
   - Content/attribute reasons → resubmit a corrected `MP_ITEM`/`MP_MAINTENANCE` feed.
3. **Price fixes do NOT go through item maintenance.** Route any price change to `walmart-buybox-pricing`, and before any price write read [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md) and run `../walmart-seller/scripts/guardrail_check.py`. After re-alignment Walmart auto-republishes in ~48 h.

## Content compliance (gate this BEFORE submitting any listing feed)

Freedom on copywriting *within* these rules — optimize for search relevance and Buy Box eligibility, but never violate:
- **Title ~50–75 chars.** No symbols (™ / ® / * / ½ / hearts). No marketing claims ("Free Shipping", "Best Seller", "#1"). No retailer info.
- **English-only**; no conflicting info across images vs attributes.
- You must **own** the item + brand/IP rights; not a prohibited category.

Full rules: [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md).

## Working example — inspect the catalog and read unpublished reasons

Use the hub's authenticated helper (handles token caching + 429 backoff). This GET is sandbox-verified (HTTP 200):

```bash
python3 ../walmart-seller/scripts/wm_request.py GET '/v3/items?limit=1'
```

Returns:

```json
{"ItemResponse":[{"sku":"...","wpid":"...","upc":"...","gtin":"...",
  "productName":"...","productType":"...","shelf":"...",
  "price":{"currency":"USD","amount":0.0},
  "publishedStatus":"UNPUBLISHED",
  "unpublishedReasons":["..."]}]}
```

`unpublishedReasons` is your repair worklist — page the full catalog with `nextCursor=*`, then apply the reason→fix mapping above.

## Gotchas (the mistakes you WILL make)

- **`PROCESSED` ≠ `PUBLISHED`.** Always re-read `GET /v3/items/{sku}` `publishedStatus`; never call a listing live off feed status.
- **A `PROCESSED` feed can hide failed items.** Walk every per-item `ingestionStatus` before declaring success — don't trust the top-level feed status.
- **Country of Origin is sticky.** Once set, it **cannot** be changed via `MP_MAINTENANCE` — you must `DELETE /v3/items/{sku}`, **wait 48 h**, then recreate (verify current requirements). Get it right the first time.
- **Price and inventory have their OWN feeds**, not item maintenance: price → `PRICE_AND_PROMOTION` / `walmart-buybox-pricing`; inventory → DXM. Don't try to fix a "Pricing Error" with an `MP_ITEM` feed.
- **`MP_ITEM` and `PRICE_AND_PROMOTION` share the ~10/hr feed budget** — bulk item submits and bulk price submits draw from the same throttle, so sequence them.
- **Rich media isn't in the feed.** A clean `MP_ITEM` feed gets you the standard listing only; video/360° is a separate post-create step.

## Load deeper

- Exact endpoints, feed types, and rate limits → [`../walmart-seller/references/api-reference.md`](../walmart-seller/references/api-reference.md).
- Content rules, the reference-price ceiling, suppression reasons, appeals → [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md).
- Auth, env vars, routing to other spokes → [`../walmart-seller/SKILL.md`](../walmart-seller/SKILL.md).

> **Sandbox note:** the `GET /v3/items` example above is sandbox-verified. Feed submit/poll (`POST /v3/feeds`, `GET /v3/feeds/{feedId}`), `POST /v3/items/spec`, and insights endpoints are **limited on the Walmart sandbox — verify on production.**
