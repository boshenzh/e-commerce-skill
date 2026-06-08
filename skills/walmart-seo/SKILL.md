---
name: walmart-seo
description: "Improve organic search ranking on Walmart — ranking factors, title/attribute optimization, and Listing Quality. Use when: 'rank higher on Walmart', 'Walmart search SEO', 'why isn't my product showing in search', 'improve my Listing Quality score', 'optimize keywords/title for Walmart', '沃尔玛搜索排名', '提高曝光'. This is ORGANIC search; for paid placement see walmart-advertising."
author: "boshenzh"
license: "Apache-2.0"
version: "0.1.0"
allowed-tools: "Read Bash"
---

# Walmart SEO — rank higher in organic search (Listing Quality, titles, attributes)

Advisory skill with API hooks. This covers **organic** ranking on Walmart.com search. Paid placement (Sponsored Products) is a different lever — see `../walmart-advertising/SKILL.md`. Start at the hub `../walmart-seller/SKILL.md` for auth and the global write guardrails.

## When to use / when not to

- **Use** to diagnose why a SKU ranks low or isn't surfacing, to optimize titles/attributes/keywords, and to raise the **Listing Quality** score.
- **Not** for paid ads (`../walmart-advertising`), for creating a listing from scratch (`../walmart-listings`), or for winning the Buy Box / repricing (`../walmart-buybox-pricing`). SEO touches all of these — route, don't duplicate.

## The five organic ranking signals (and how to act on each)

1. **Relevance** — does the title, attributes, and category match the customer's query? This is the lever you control most directly via content.
2. **Performance** — sales velocity, conversion rate, and **in-stock rate**. Keep popular SKUs in stock; an out-of-stock SKU loses ranking momentum that's slow to rebuild.
3. **Content / Listing Quality** — measurable via the API (below). The single best lever because it's the one you can read a number for.
4. **Price / Buy Box** — a competitive landed price wins the Buy Box and lifts ranking. **An over-priced item gets SUPPRESSED and disappears from search entirely** — no amount of content fixes that. See `../walmart-buybox-pricing/SKILL.md` and `../walmart-seller/references/guardrails.md`.
5. **Reviews/ratings + fulfillment speed** — more/better reviews lift ranking; a **TwoDay** tag (WFS or qualified seller-fulfilled) lifts it further. See `../walmart-wfs/SKILL.md`.

## Workflow

1. **Measure first.** Pull the Listing Quality score and find the weakest dimension:
   ```bash
   python3 ../walmart-seller/scripts/wm_request.py GET /v3/insights/items/listingQuality/score
   ```
   It returns `overAllQuality` plus sub-scores: **content**, **offer**, **discoverability**, **ratings**. **Fix the lowest sub-score first** — don't polish a dimension that's already strong.
2. **Content gap** → enrich the **title**, attributes, and images. Structure titles as **Brand + Key Feature + Product Type + Attributes** (e.g. `Acme 12-Cup Stainless Steel Drip Coffee Maker, Programmable, Black`). Respect content rules (next step's gotcha + `../walmart-seller/references/guardrails.md`).
3. **Offer gap** → check price and Buy Box status. If suppressed for price, that's the real problem; hand off to `../walmart-buybox-pricing`. Before ANY price write, read `../walmart-seller/references/guardrails.md` and run `../walmart-seller/scripts/guardrail_check.py`.
4. **Discoverability gap** → fill **highly-recommended attributes** (they feed both ranking AND the left-rail filters buyers use) and weave researched keywords into the title/attributes. Keyword research: type the product into Walmart search and harvest the **autocomplete** suggestions, then scan the **top competitor titles** on the results page for shared terms.
5. **Re-measure.** Content writes are async feeds — `PROCESSED` ≠ live (hub rule 8). Re-pull the score ~24-48 h later (Listing Quality and ranking update on a lag, not instantly).

## Working example — find the weakest dimension, then fix it

```bash
# 1) read the score for the whole catalog (or a single item)
python3 ../walmart-seller/scripts/wm_request.py GET /v3/insights/items/listingQuality/score
# → e.g. { "overAllQuality": 62, "content": 81, "offer": 55,
#          "discoverability": 40, "ratings": 70 }   # scores are 0–100
```
Field names above are illustrative — confirm the exact JSON keys against **production** (the response shape isn't pinned in the docs). Here `discoverability` (40) is weakest → the fix is **attributes + keywords**, not rewriting the title. Pull the product-type spec to see which highly-recommended attributes are empty:
```bash
python3 ../walmart-seller/scripts/wm_request.py POST /v3/items/spec --body @spec_request.json
```
Fill the gaps via an `MP_MAINTENANCE` feed (see `../walmart-listings/SKILL.md`), then re-measure tomorrow.

## Calibration

This is **advisory and flexible**: describe *what* to improve and *why*, then let the seller (or you) choose specific copy within the content rules. The one prescriptive boundary is **content compliance** — a title that breaks policy gets the listing rejected, undoing all SEO work.

## Gotchas

- **SEO ≠ ads.** Organic ranking and Sponsored Products placement are separate systems. A paid campaign doesn't raise your organic rank, and a great organic rank doesn't earn ad slots. Don't conflate them.
- **Keyword-stuffing and marketing-claim titles VIOLATE content policy** and get the listing rejected. No `™/®/*`, no "Free Shipping / Best Seller / #1", no repeated keywords. Titles ~50-75 chars, English-only. (`../walmart-seller/references/guardrails.md`.)
- **A price-suppressed item ranks NOWHERE** no matter how good the content. Always check offer/Buy Box status before spending effort on content — fix suppression first.
- **Listing Quality is the single best lever** and the only ranking signal with a real number behind it. Drive decisions off the sub-scores, not guesswork.
- **Highly-recommended attributes are double-duty** — they feed ranking *and* power the filter facets buyers click. Empty ones cost you on both.
- **Insights may be limited on sandbox.** Verify the listingQuality score against **production** (`WALMART_ENV=production`); a thin/empty sandbox response isn't a content problem.

## Load deeper

- Exact endpoints, throttles, and the insights family: `../walmart-seller/references/api-reference.md`.
- Pricing-suppression rules + content rules + scorecard: `../walmart-seller/references/guardrails.md`.
- Authenticated calls: `../walmart-seller/scripts/wm_request.py`. Price-write safety: `../walmart-seller/scripts/guardrail_check.py`.
