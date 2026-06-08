---
name: walmart-customer-targeting
description: "Increase visibility to Walmart+ members and high-value customers. Use when: 'reach Walmart+ customers', 'get the TwoDay/Walmart+ tag', 'increase my product visibility', 'how do I show up for Walmart+ members', 'Walmart deals/events', '触达Walmart+用户', '提升店铺可见度'."
author: "boshenzh"
license: "Apache-2.0"
version: "0.1.0"
allowed-tools: "Read"
---

# Walmart Customer Targeting — earn visibility to Walmart+ & high-value buyers

Advisory skill. There is **no API to "target Walmart+ members."** You don't buy your way in front of them — you **earn** it by being the offer Walmart's surfaces (search, Buy Box, "fast delivery" filters) prefer. This skill explains the levers and routes you to the operational skill that pulls each one. Hub: [`../walmart-seller/SKILL.md`](../walmart-seller/SKILL.md).

## What Walmart+ actually is

Walmart's **paid membership** (free fast shipping with **no order minimum**, plus fuel and other perks). These are **high-intent, high-frequency** buyers who filter for fast/free delivery and convert well. Winning them is a **fulfillment + pricing + content outcome**, not a targeting setting.

## When to use / when not to

- **Use** to understand *why* you're (not) visible to Walmart+ / high-value buyers and *which* lever to move first.
- **Not** for the actual API writes — those live in the spokes below. This skill is read-only by design (`allowed-tools: Read`).
- **Not** for paid placement — that's `walmart-advertising` (partner-gated; marketplace keys don't unlock it).

## The levers (ranked, with where to act)

Visibility compounds: **speed + price + content → Buy Box + higher search rank → more impressions to Walmart+ and everyone else.** Move them in this order.

1. **Fast/free shipping tag — usually the fastest single win.** Walmart+ shoppers filter hard on delivery speed and a TwoDay/free badge. Either enroll SKUs in **WFS** (Walmart fulfills; auto-earns the fast tag) or set a **TwoDay shipping template** on seller-fulfilled SKUs (`/v3/settings/shipping/templates`). → `walmart-wfs`.
2. **Accurate, low lag time.** A truthful, short `lagtime` lets Walmart promise (and keep) a faster delivery date — over-promising tanks On-Time Delivery. Set via feed `lagtime` or `GET /v3/lagtime`. → `walmart-wfs`.
3. **Competitive landed price to win the Buy Box.** Item **+ shipping** must beat the reference price; the Buy Box winner is what shoppers actually see and buy. → `walmart-buybox-pricing`.
4. **High in-stock rate.** Out-of-stock = invisible. Watch the **Inventory OOS** webhook event; the agent owns the inventory push end-to-end (`GET|PUT /v3/inventories/{sku}`). → hub `../walmart-seller/SKILL.md`.
5. **Strong Listing Quality + reviews.** Higher LQ score and ratings lift search rank and conversion. Check `GET /v3/insights/items/listingQuality/score`. → `walmart-seo`.
6. **Participate in Walmart Deals / savings events.** Featured-deal placement is extra exposure — but requires **enrollment in Seller Center** (no self-serve "join event" marketplace endpoint). → `walmart-buybox-pricing` for the deal/promo price mechanics.
7. **Geo-relevant fulfillment.** Ship nodes near demand → faster *promised* delivery → more "fast delivery" impressions. Configure `/v3/settings/shipping/shipnodes` (multi-node inventory via `GET|PUT /v3/inventories/{sku}`). → `walmart-wfs`.

## Working example — diagnose which lever to pull first

No live calls here; this skill reasons over data the spokes/hub fetch. The decision rule:

```
IF sku has no fast/free tag        → fix shipping first (WFS or TwoDay template)   [walmart-wfs]
ELIF not winning Buy Box           → fix landed price                              [walmart-buybox-pricing]
ELIF Listing Quality < good        → fix content/reviews                          [walmart-seo]
ELIF in-stock rate low / OOS       → fix inventory (agent owns the push)           [hub]
ELSE                               → enroll in Walmart Deals / add ship nodes
```

The inputs come from the hub's helper (run by the hub/operational spoke, not this advisory skill), e.g. Listing Quality:

```bash
# (run by the hub/operational spoke, e.g. walmart-seo / walmart-wfs — this Read-only skill only reasons over the result)
python3 ../walmart-seller/scripts/wm_request.py GET /v3/insights/items/listingQuality/score
```

## Gotchas

- **There is NO "target Walmart+ members" API.** Visibility is *earned* via fulfillment speed + Buy Box + content, never *bought*. Don't go hunting for a targeting endpoint — there isn't one.
- **Fastest single win is almost always the shipping tag** (WFS enrollment or a TwoDay template), not a price cut. Try that lever before repricing.
- **Walmart Deals / events require Seller Center enrollment** — there is no self-serve marketplace endpoint to "join an event." Don't promise programmatic enrollment.
- **A faster promised date you can't keep backfires.** Lag time must be honest: missing it breaks On-Time Delivery (**≥ 90%**) and Late Shipment (**≤ 5%**) on the scorecard, which *lowers* visibility. See [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md).
- **This skill is advisory only.** It picks the lever; the **API work happens in the spokes** (`walmart-wfs`, `walmart-buybox-pricing`, `walmart-seo`). Route there — don't duplicate their writes here. **Single source of truth — the agent is the system of record for Walmart writes.** (If you ever add another tool that also writes to Walmart, partition fields per system to avoid oversell / double-write / price-flapping.)
- **Any price move to "win Buy Box" is a guarded write.** Before *any* price write, the spoke must read [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md) and run `../walmart-seller/scripts/guardrail_check.py` (too-low prices get suppressed too).

## Load deeper

- Hub (auth, routing, global safety): [`../walmart-seller/SKILL.md`](../walmart-seller/SKILL.md)
- Exact endpoints, rate limits, shipping-template & lag-time paths: [`../walmart-seller/references/api-reference.md`](../walmart-seller/references/api-reference.md)
- Scorecard thresholds + pricing/suppression invariants: [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md)
- Operational spokes: `walmart-wfs` · `walmart-buybox-pricing` · `walmart-seo`
