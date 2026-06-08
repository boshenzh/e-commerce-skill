---
name: walmart-advertising
description: "Plan and (where possible) access Walmart Connect advertising — Sponsored Products (search/browse; formerly Sponsored Search / Performance Ads), Sponsored Brands, and Display. Use when: 'advertise on Walmart', 'Walmart Sponsored Products', 'set up Walmart ads', 'Walmart Connect API', 'lower my ACoS', 'Walmart PPC', '沃尔玛广告', '沃尔玛推广'. Heads-up: the ads API is partner-gated, not self-serve."
author: "boshenzh"
license: "Apache-2.0"
version: "0.1.0"
allowed-tools: "Read"
---

# Walmart Advertising — plan campaigns and find the real access path

Advisory spoke of the `walmart-seller` hub. Walmart Connect is Walmart's retail-media
business: ads that appear in search, browse, and across the site. It is a **separate
program from the Marketplace API** you use for everything else in this collection — different
base host, different access gate. Your job here is **strategy + getting the user onto the
right access path**, not pretending to call an ads API you can't reach. Hub: [`../walmart-seller/SKILL.md`](../walmart-seller/SKILL.md).

## When to use / when not to

- **Use** to plan Walmart Connect campaigns (Sponsored Products, Sponsored Brands,
  Display), set ACoS/ROAS targets, structure auto→manual keyword harvesting, or figure out
  *how the user can actually run/automate ads*.
- **Not** for Marketplace catalog/price/order work — that's the hub and its other spokes.
  Not for self-serve API calls: see the access reality below.
- **Calibration:** advisory. Give the strategy and the access path. Do **not** claim you can
  drive the ads API with the seller's Marketplace keys — you can't.

## Access reality (read this first — it's the #1 thing the agent gets wrong)

The **Walmart Connect Ads API is gated** to the **Walmart Connect Partner Network (WCPN)**.
It is **NOT self-serve**: there is no "request my own ads key in Seller Center" path the way
there is for the Marketplace API. Your **Marketplace seller keys do NOT unlock ads** —
they're a different program.

- **Different base host:** `developer.api.walmart.com/api-proxy/service/WPA/Api/v1/`
  (not `marketplace.walmartapis.com`). Same fact noted in the hub's
  [`../walmart-seller/references/api-reference.md`](../walmart-seller/references/api-reference.md) under "Walmart Connect ads".
- **WCPN partner tiers** (you apply to one): **Full-Service**, **Campaign Management**,
  **Reporting Only**, **Creative Only**. The tier scopes which API capabilities you get.

### Three ways to actually run ads (pick one)

1. **Default — Walmart Ad Center UI (self-serve).** For a single seller this is the realistic
   entry point. Create and manage Sponsored Products campaigns by hand in the Ad
   Center dashboard. No API approval needed. Recommend this first.
2. **Apply to WCPN** to get direct Ads API access — only worth it at scale (many SKUs /
   programmatic bid management). Expect an application + tier assignment.
3. **Use an approved partner platform** (e.g. **Pacvue**, **Skai**) that already holds WCPN
   API access — fastest way to get automation without becoming a partner yourself.

## Workflow (campaign strategy)

1. **Pick the program.** Start with **Sponsored Products** (the search program — keyword +
   auto campaigns placed in search/browse; formerly called Sponsored Search / Performance
   Ads) — highest intent, lowest effort. Add **Sponsored Brands** (banner + brand logo +
   multi-product) once you have winning items; **Display** for awareness/retargeting later.
2. **Run an auto campaign first** to harvest the search terms Walmart actually matches you on.
3. **Graduate winners to manual.** Move converting terms into a manual keyword campaign with
   tighter bids; add poor performers as negatives in the auto campaign.
4. **Defend your branded terms** with a dedicated manual campaign so competitors don't poach
   buyers searching your brand.
5. **Set an ACoS / ROAS target up front** (ad spend ÷ ad sales = ACoS). Bid toward it; cut or
   lower bids on anything chronically above target.
6. **Control spend** with **dayparting** (run during high-converting hours) and **daily +
   campaign budget caps**. Pause campaigns that exhaust budget by noon — that's an
   under-bidding/over-broad signal.
7. **Track via reporting** (campaign / keyword / item performance). If you only hold the
   Reporting-Only WCPN tier, this is the part the API exposes.

## Working example — an Ad Center starting structure

```
Campaign: "Auto-Harvest — Widgets"      type: Sponsored Products, targeting: AUTO
  daily budget: $30   |   default bid: $0.45   |   ACoS target: 20%
  → after 2 weeks: export the search-term report, pull terms with ≥2 orders

Campaign: "Manual — Widgets (Exact)"    type: Sponsored Products, targeting: MANUAL
  harvested keyword "stainless widget"  bid: $0.65  (raise on winners, toward 20% ACoS)
  negatives added back into Auto-Harvest: "cheap widget", "widget repair"

Campaign: "Brand Defense — MyBrand"     type: Sponsored Products, targeting: MANUAL
  keyword "mybrand widget"  bid: $0.55   (protect branded search)
```

You build the above **in the Ad Center UI** (or via a WCPN partner). There is no
collection script for it — this skill makes **no live API calls** (allowed-tools: `Read`).

## Gotchas

- **The ads API is partner-gated, not self-serve.** Do **not** try the seller's Marketplace
  keys against the WPA host — they won't authenticate; it's a separate program.
- **Different base host + program** from everything else here. `marketplace.walmartapis.com`
  is Marketplace; ads live at `developer.api.walmart.com/api-proxy/service/WPA/Api/v1/`.
- **For a single seller, the Ad Center UI is the realistic entry point** — don't send a small
  seller down the WCPN application path when the dashboard does the job.
- **Ads ≠ Buy Box.** Winning ad placement does not win the organic Buy Box, and a Sponsored
  Product still won't surface if the listing is **unpublished for a pricing violation** — so
  fix pricing/listing health first (hub guardrails) before spending on ads.
- **Walmart publishes no fixed ACoS benchmark** — set your own target from margin, don't
  copy an Amazon number.

## Load deeper

- Hub (auth model, routing, env vars, global safety): [`../walmart-seller/SKILL.md`](../walmart-seller/SKILL.md).
- The one-line ads note + full Marketplace endpoint map: [`../walmart-seller/references/api-reference.md`](../walmart-seller/references/api-reference.md).
- Listing/pricing health that gates whether ads even show (and before any price write, run
  `../walmart-seller/scripts/guardrail_check.py`): [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md).
- Authenticated **Marketplace** (not ads) calls go through `../walmart-seller/scripts/wm_request.py`.
