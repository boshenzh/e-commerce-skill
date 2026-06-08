---
name: walmart-pro-seller
description: "Understand and qualify for the Walmart Pro Seller Badge (Rising/Advanced/Pro tiers). Use when: 'how do I get the Pro Seller badge', 'Pro Seller requirements', 'what tier am I', 'qualify for Pro Seller', 'Pro Seller rewards', '沃尔玛Pro Seller', '专业卖家徽章'."
author: "boshenzh"
license: "Apache-2.0"
version: "0.1.0"
allowed-tools: "Read Bash"
---

# Walmart Pro Seller — earn the badge by hitting your scorecard

The **Pro Seller Badge** is a trust signal Walmart stamps on your listings when your operational performance is consistently excellent. It is **earned by performance, not applied for** — there is no form, no fee, no human reviewer. You qualify (or fall out) automatically based on the same metrics that keep your account healthy. This skill explains the tiers, the criteria, the rewards, and gives you an action plan. It's advisory; for the actual write/fulfillment work it routes you to the operational spokes.

Read the hub first: [`../walmart-seller/SKILL.md`](../walmart-seller/SKILL.md).

## When to use / when not to

- **Use** to explain the badge, diagnose why a seller hasn't earned it, plan how to qualify, or read the seller's current Pro Seller status via the API.
- **Not** for the actual repricing/listing/fulfillment work — this skill only diagnoses and plans. It dispatches to `walmart-fulfillment-ops`, `walmart-wfs`, `walmart-seo`, and `walmart-buybox-pricing`.
- **Not** an application workflow — there is nothing to submit. Don't promise a seller you can "apply" them in.

## The three tiers

A 3-tier progression, all earned the same way (rising performance unlocks the next):

| Tier | What it means |
|---|---|
| **Rising** | Entry recognition — early consistent performance after the tenure minimum. |
| **Advanced** | Sustained strong performance + higher volume. |
| **Pro Seller** | Top tier — the badge buyers see on listings; the full reward set. |

## Qualification criteria (directional — VERIFY current numbers in Seller Center)

Walmart adjusts these thresholds periodically, so treat the numbers below as directional and **confirm the live values in Seller Center → Performance** before telling a seller they qualify:

- **On-time delivery — higher than the scorecard's ≥90% floor** (historically ~95%+); verify current Pro Seller criteria in Seller Center.
- **Low seller-responsible cancellation rate** (very low — tighter than the ≤2% scorecard floor; cited around < 1%, but verify current criteria).
- **High Listing Quality** on trending/relevant items (drive via `walmart-seo`).
- **Account tenure** — roughly **90+ days** selling.
- **Minimum order / sales volume** over the measurement window.
- **No recent policy violations** (pricing suppressions, content flags, etc.).

Note the pattern: these are the **scorecard metrics from [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md), just at a higher bar.** The same work that protects the account from suspension also earns the badge.

## Rewards (Pro Seller tier)

- The **Pro Seller badge** displayed on your listings (buyer trust → conversion lift).
- **Search/visibility boost** in Walmart search.
- **Faster payouts.**
- **Referral-fee discounts** (cited up to **~10%**).
- **SEM / Walmart Connect ad credits.**

## Status: reading it via the API

- Status **refreshes only on the 5th and the 20th of each month** — a fix made on the 6th won't show until the 20th. Set expectations accordingly.
- A **Pro Seller status endpoint** exists under the Insights APIs — look it up in `../walmart-seller/references/api-reference.md` (listed under Insights) and **confirm the exact path on live before calling**. The **legacy Pro Seller API v1 was retired mid-2025** — use the current one.
- Read it through the hub's authenticated helper (no token plumbing needed):

```bash
# look up <pro-seller-status-endpoint> under Insights in references/api-reference.md
# and confirm the exact path on live first, then:
python3 ../walmart-seller/scripts/wm_request.py GET <pro-seller-status-endpoint>
```

If that path 404s or 410s, you're on the deprecated route — re-check the Insights section of `../walmart-seller/references/api-reference.md` for the current spelling (the developer portal is a JS SPA and field/path spellings drift).

## Action plan — how to actually qualify

This is a fulfillment-and-quality problem, not a paperwork problem. Work the metrics, in order of leverage:

1. **Tighten fulfillment well above the ≥90% on-time floor (historically ~95%+) + valid tracking.** Route seller-fulfilled orders through `walmart-fulfillment-ops` (acknowledge within the 4-hr SLA, ship before Expected Ship Date, upload tracking). Where possible move SKUs to WFS via `walmart-wfs` — WFS orders are on-time by construction and stabilize the on-time metric fastest.
2. **Drive Listing Quality** with `walmart-seo` (content completeness, images, attributes, ratings) on your trending/high-traffic items.
3. **Keep cancellations < 1%** by keeping inventory accurate so you never cancel for OOS. This is mostly a DXM-side inventory job — don't write inventory from the agent (hub rule 12 (Don't fight DXM)).
4. **Sustain order volume** above the minimum across the window; don't let it dip right before a 5th/20th refresh.
5. **Stay clean** — no pricing suppressions or content flags. Before ANY price write, read [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md) and run `../walmart-seller/scripts/guardrail_check.py`. A "Pricing Error" suppression both hurts the account and disqualifies the badge.

## Working example — diagnose a seller against the bar

```bash
# 1) Pull current performance (scorecard metrics underpin the badge)
#    use the <pro-seller-status-endpoint> from references/api-reference.md (Insights), verified on live:
python3 ../walmart-seller/scripts/wm_request.py GET <pro-seller-status-endpoint>

# 2) Compare each metric to the bar, e.g.:
#    on-time 93%  -> above the >=90% floor but short of the badge bar (~95%+) -> action: move top SKUs to WFS (walmart-wfs)
#    cancel  1.4% -> above the badge bar (very low / ~<1%) -> action: fix inventory accuracy (DXM side)
#    tenure  120d -> PASS
#    LQ      low  -> action: walmart-seo
# 3) Tell the seller the gap + that status only re-rates on the 5th/20th.
```

## Gotchas

- **It's earned, not applied for.** Never tell a seller to "submit an application" — there is no form. The only lever is performance.
- **Badge bar > scorecard floor.** ≥90% on-time (not 95%) keeps you alive; the badge bar sits higher (historically ~95%+). ≤2% cancellation keeps you alive; the badge wants a very low rate (around <1%). Verify the current Pro Seller criteria in Seller Center — don't conflate "account-safe" with "badge-qualified."
- **Thresholds shift — don't hardcode.** Always verify the current numbers in Seller Center → Performance. The values here are directional.
- **Status updates only twice a month (5th/20th).** A seller who fixes a metric on the 6th will not see the badge appear until the 20th, even if the underlying metric already cleared. Manage expectations.
- **Use the current status endpoint** — the legacy Pro Seller API v1 was retired mid-2025; a 410/404 means you're on the dead route.

## Load deeper

- Tiers/criteria are scorecard-derived → [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md).
- Exact endpoint paths + rate limits + the Insights APIs → [`../walmart-seller/references/api-reference.md`](../walmart-seller/references/api-reference.md).
- Auth/token flow + env vars (`WALMART_CLIENT_ID/SECRET/ENV`) + routing → [`../walmart-seller/SKILL.md`](../walmart-seller/SKILL.md).
