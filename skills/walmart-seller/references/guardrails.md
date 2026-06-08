# Guardrails — account‑safety rules every write must respect

Full version: `../../../docs/05-guardrails-and-policy.md`. Walmart enforces pricing/content rules via **automated suppression** and governs account health via a **scorecard**. Violations suppress SKUs or suspend the account. Encode the invariants below in the write path; validate prices with `../scripts/guardrail_check.py`.

## Scorecard thresholds (monitor; alert before breach)

| Metric | Threshold |
|---|---|
| On‑Time Delivery | **≥ 90%** (not 95% — that's stale) |
| Late Shipment Rate | ≤ 5% |
| Valid Tracking Rate | **≥ 99%** |
| Cancellation Rate (seller) | **≤ 2%** |
| Return/Refund Rate | ≤ 6% |
| Item Not Received | ≤ 2% |
| Negative Feedback | ≤ 2% |
| Seller Response Rate | ≥ 95% within 48 h |

"Order Defect Rate / 90‑day" is **legacy** terminology — superseded by the above. No single auto‑suspend cutoff; failing any standard "may result in suppression, suspension or termination," usually after ≥1 warning.

## Pricing Rule (the big hazard)

Walmart computes an internal **reference price** (competitors + Walmart.com + historical + Buy Box) and:
- **Too HIGH (egregious)** → unpublish, reason **"Reasonable Price Not Satisfied."**
- **Too HIGH (substantial)** → Add‑to‑Cart removed + price hidden = **Buy Box loss without delisting.**
- **Too LOW (erroneous)** → unpublish, reason **"Pricing Error."** ← a runaway downward repricer trips this.
- **Shipping is in scope** ("Egregious Shipping Cost"); 10 shipping‑template edits/day → 24‑h lockout.
- Re‑aligns → auto‑republish ~48 h. Repeated/egregious violations → **account suspension.**
- Walmart publishes **no numeric markup thresholds** — treat the reference price (shown on the Unpublished‑Items / Pricing‑Insights dashboard) as the **ceiling**.

## Hard agent invariants (enforce in code)

1. **Mandatory per‑SKU `min` + `max`.** Reject any SKU lacking both. `min = max(cost + min_margin, MAP)`, `max ≤ reference_price`.
2. **Clamp every price to `[min, max]`.** Never below floor. If competitive floor < min → hold at min, accept Buy Box loss; never chase a loss.
3. **Reference price = ceiling.** Keep landed price (item + shipping) at/below it.
4. **Per‑cycle change cap** (e.g. ≤15%); larger swings → human approval.
5. **Cooldowns + rate budgeting.** Honor 100/hr·10/hr·60/min and the 10 template‑edits/day lockout; back off on 429. ~4‑hr cadence is normal — don't thrash.
6. **Human‑approval gate** for large moves and any price below cost/MAP.
7. **Global kill‑switch** (freeze writes on unpublish spike / 429 storm / data gaps) + per‑SKU circuit breakers.
8. **SKU allowlist** — everything else read‑only. One owner/strategy per SKU.
9. **No competitive target → hold last submitted price** (don't free‑fall to min).
10. **Content validation before any listing write** (§ below).
11. **Audit every change** + the data behind it (for Plan‑of‑Action appeals).
12. **Single source of truth** — the agent is the system of record for Walmart writes (listings, price, inventory, orders, returns, WFS). *(Optional: if you ever add another tool that also writes to Walmart, partition fields per system to avoid oversell / double‑write / price‑flapping.)*

> **Owning inventory + fulfillment (standalone).** Because the agent owns these end‑to‑end, it needs (a) a real source of inventory truth — your own warehouse/3PL stock — to push to Walmart, and (b) a way to produce shipping labels + tracking (Walmart's carrier/label APIs or a 3PL) when acknowledging/shipping orders.

## Content rules (for listing writes)

- Titles ~50–75 chars; **no symbols (™/®/*/½/hearts), no marketing claims ("Free Shipping","Best Seller","#1"), no retailer info.**
- English‑only; no conflicting info across images/attributes; "Made in USA" consistent.
- Must **own** the item + brand/IP rights; not a prohibited category.

## Automation conduct

API automation is allowed (Walmart sells its own Repricer), but: respect rate limits; no review/rating manipulation; no raising price after an order completes; no ad‑hoc customer price negotiation (No‑Haggling); browser‑scraping public Walmart pages without written consent violates ToS.

## Appeals

Per‑SKU pricing flag → submit a comparable‑item URL ("Submit an external price match"), validated ~48 h. Suspension → Seller Center Help → written **Business Plan of Action** (root cause → corrective → preventative + docs); reinstatement not guaranteed.

## guardrail_check.py contract

`guardrail_check.py` returns **ALLOW** only if the proposed price: is within `[min, max]`; ≥ `max(cost+min_margin, MAP)`; ≤ `reference_price`; and within `max_change_pct` of `last_price`. Otherwise **DENY** with the failing rule. Exit code `0`=allow, `2`=deny. Always run it before a price write.
