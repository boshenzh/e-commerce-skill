---
name: walmart-buybox-pricing
description: "Win the Walmart Buy Box and reprice SAFELY without getting suppressed. Use when: 'win the Buy Box', 'reprice on Walmart', 'set up a repricer', 'I lost the Buy Box', 'is this price safe to set', 'competitive pricing on Walmart', '沃尔玛黄金购物车', '调价/改价'. This is the highest-risk skill — every price write must pass the guardrails."
author: "boshenzh"
license: "Apache-2.0"
version: "0.1.0"
allowed-tools: "Read Bash"
---

# Walmart Buy Box & Repricing — win the box without tripping suppression

A **spoke** of the `walmart-seller` hub. Read the hub first for auth, the API map, and the global safety rules: [`../walmart-seller/SKILL.md`](../walmart-seller/SKILL.md). This is the **riskiest** workflow on the platform — a runaway repricer can suppress your SKUs or suspend the account. Be prescriptive; never skip the guardrail check.

## When to use / when not

- **Use** to win/recover the Buy Box, stand up a repricing strategy, or decide whether a specific price is safe to set.
- **Not** for listing content/SEO (`walmart-listings`, `walmart-seo`), inventory & fulfillment (`walmart-fulfillment-ops`), or ad bidding (`walmart-advertising`).
- **Single source of truth:** the agent is the system of record for Walmart price writes and owns them end-to-end. (If you ever add another tool that also writes to Walmart, partition fields per system to avoid oversell / double-write / price-flapping.)

## How the Buy Box is actually won

Winner-take-all, but **lowest price does not always win.** Walmart ranks the **landed price** (item + shipping) *plus* delivery speed/method (WFS / fast-free-shipping boost), in-stock status, and seller performance (scorecard). A slightly higher price with WFS + fast delivery can take the box from a cheaper offer. So: be competitive on landed price, but don't free-fall — fix fulfillment signals instead of dropping below your floor.

## Preferred approach (DEFAULT): Walmart's native Repricer

Delegate to the native Repricer instead of hammering `PUT /v3/price` against the tight 100/hr limit.

- Create a strategy: `POST /v3/repricer/strategy` (create ~20/hr; then assign / unassign / pause). Rule types: **Buy Box / External / Competitive** — Competitive is Walmart-recommended. Optional AI strategy.
- **MANDATORY per-SKU `minimumSellerAllowedPrice` + `maximumSellerAllowedPrice`.** The Repricer never prices outside them — these are your hard floor/ceiling. Cadence is 15 min–4 hr.
- This is safer *and* avoids the write limits — the engine reprices for you within `[min, max]`.

Alternative (self-driven, only if the Repricer can't express the rule): read the Buy Box signal, compute a target, and write `PUT /v3/price` yourself — but it must go through the same write sequence below.

## Mandatory write sequence (plan → validate → execute)

Never deviate. Every price write — Repricer min/max OR direct `PUT /v3/price` — runs all five steps:

1. **Read the Buy Box signal.** Request the on-request **BUYBOX** report (`POST /v3/reports/reportRequests?reportType=BUYBOX` → poll → download). Note `isSellerBuyBoxWinner`, **BuyBox Item Price**, **BuyBox Ship Price** (landed = item + ship).
2. **Compute a target** within `[min, max]`. If there is **no competitive target → hold the last submitted price** (do NOT drop to min).
3. **Run the guardrail check and proceed ONLY on ALLOW (exit 0):**
   ```bash
   python3 ../walmart-seller/scripts/guardrail_check.py --sku ABC --proposed <target> \
       --cost <cost> --map <MAP> --min <min> --max <max> --last <last> \
       --max-change-pct 15 --reference <reference_price>
   ```
   DENY (exit 2) → stop. Below-floor or large moves need **human approval**, not a retry.
4. **Execute — prefer Repricer assign** (set/adjust the SKU's min/max + strategy). Else direct write:
   ```bash
   python3 ../walmart-seller/scripts/wm_request.py PUT /v3/price --body @price.json
   ```
5. **Read back after ~5 min** (price writes take ~5 min to reflect). Confirm the new price stuck. If it didn't reflect (phantom success), don't re-write blindly — re-read, then surface to a human if it keeps reverting.

## Hard rules (full text: [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md))

- Never below `max(cost + min_margin, MAP)`. Never above the **reference price** (the de-facto ceiling). Clamp to `[min, max]`.
- **Too-LOW prices get suppressed too** — reason "Pricing Error" — not just too-high. A downward runaway is the dangerous one.
- Per-cycle change cap (~15%); cooldowns per SKU; honor `429`. One strategy/owner per SKU. SKU allowlist; everything else read-only.
- **No competitive target → hold last price.** Never chase a competitor below your floor — hold at `min` and accept the Buy Box loss.
- **Kill-switch on anomaly** (unpublish spike, 429 storm, data gaps) — freeze all writes.

For exact endpoints, fields, and rate limits, read [`../walmart-seller/references/api-reference.md`](../walmart-seller/references/api-reference.md). Before ANY price write, read [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md) and run `guardrail_check.py`.

## Working example (verified offline)

```bash
# ALLOW — within [17.99, 29.99], above floor, below reference 24.99, within 15% of 21.99
python3 ../walmart-seller/scripts/guardrail_check.py --sku ABC --proposed 19.99 \
    --cost 12 --map 17.99 --min 17.99 --max 29.99 --last 21.99 \
    --max-change-pct 15 --reference 24.99
# → ALLOW, exit 0

# DENY — 10.00 is below the floor max(cost+margin, MAP)=17.99
python3 ../walmart-seller/scripts/guardrail_check.py --sku ABC --proposed 10 \
    --cost 12 --map 17.99 --min 17.99 --max 29.99 --last 21.99 \
    --max-change-pct 15 --reference 24.99
# → DENY (R2 below min + R1 below floor), exit 2
```

## Gotchas

- **A runaway DOWNWARD repricer trips "Pricing Error" suppression.** Too-low is dangerous, not only too-high. Always set a real `min`; never let the strategy chase to zero.
- **Write limits are tight** — single `PUT /v3/price` 100/hr, bulk `PRICE_AND_PROMOTION` feed 10/hr. Prefer the native Repricer so you stop spending writes.
- **`PUT /v3/price` takes ~5 min to reflect.** Don't re-write or assume failure before reading back; you'll burn the rate budget and may double-move the price.
- **Never chase below your floor.** When the competitive floor < your `min`, hold at `min` and accept the Buy Box loss — a lost box is recoverable; a suppressed SKU or suspended account is not.
- **Repricer create-body field names are unverified** (the portal is a JS SPA) — confirm exact `minimumSellerAllowedPrice`/`maximumSellerAllowedPrice` spellings against a live sandbox call before coding.
