# 05 — Guardrails & Policy (keeping the account alive)

Walmart enforces pricing and content rules largely through **automated suppression**, not warnings, and governs account health through a **performance scorecard**. An autonomous agent that ignores these can get SKUs unpublished or the account suspended. This chapter is the rulebook the agent's write path **must** hard‑enforce.

The agent is the **system of record** for this Walmart store and owns **all writes** end‑to‑end: listings, price, inventory, orders (acknowledge / ship / cancel / refund), returns, and WFS. Because it owns inventory, it needs a **real source of inventory truth** — your own warehouse/3PL stock — to push to Walmart (otherwise availability and the too‑low/oversell hazards can't be controlled).

## 1. Seller performance scorecard (thresholds)

Current official "Seller performance standards" (Marketplace Learn, fetched June 2026):

| Metric | Threshold | Window |
|---|---|---|
| **On‑Time Delivery (OTD)** | **≥ 90%** | rolling ~30–60 day |
| **Late Shipment Rate** | ≤ 5% | ~30–60 day |
| **Valid Tracking Rate (VTR)** | **≥ 99%** | ~30–60 day |
| **Cancellation Rate** (seller‑initiated) | **≤ 2%** | ~30–60 day |
| **Return/Refund Rate** | ≤ 6% | 60 day |
| **Item Not Received Rate** | ≤ 2% | 60 day |
| **Negative Feedback Rate** | ≤ 2% | 60 day (enforced from early 2026) |
| **Seller Response Rate** | ≥ 95% within 48 h | — |

> Notes: "Order Defect Rate (ODR) < 2% over 90 days" is **legacy** terminology — the current page no longer lists ODR or a 90‑day window; it's been replaced by the granular metrics above. Some third‑party blogs still cite an older **OTD > 95%** — the live official figure is **90%**. There's **no single auto‑suspend cutoff**: failing any standard "may result in suppression, suspension or termination," usually after ≥1 warning, with appeals via a corrective plan.

**Agent implication:** continuously monitor these via the Seller Performance API and **alert before** a metric approaches its threshold. The agent owns order sync end‑to‑end (acknowledge / ship / cancel / refund; see `03` Priority 1) largely to protect OTD/VTR/Cancellation. Because the agent owns fulfillment, it needs a reliable way to produce **shipping labels + tracking** — Walmart's carrier/label APIs or a 3PL — so every shipment posts valid tracking inside the OTD/VTR window.

## 2. Pricing Rule (automated suppression) — the big hazard

Walmart computes an internal **reference price** from competitor sites, Walmart.com, historical, and Buy Box data, and:

- **Too high (egregiously):** offer is **unpublished** — reason code **"Reasonable Price Not Satisfied"** ("currently not buyable," removed from search).
- **Too high (substantially, but not egregious):** **Add‑to‑Cart button removed + price/shipping hidden** from the item page (effectively **Buy Box loss without delisting**; still buyable via "More Seller Options").
- **Too LOW (priced erroneously):** also **unpublished** — reason code **"Pricing Error"** — to protect sellers from unintended losses. **A runaway downward repricer can get suppressed for going too low.**
- **Shipping counts:** listing price **and** shipping are evaluated together; "Egregious Shipping Cost" is its own unpublish reason. (Plus a platform limit: **10 shipping‑template edits/day** before a 24‑hour lockout.)
- **Republish:** once price re‑aligns (you lower it, or competitors move), Walmart auto‑republishes, **typically within 48 hours**.
- **Escalation:** most violations are per‑SKU, but **repeated or egregious violations → account suspension** ("non‑compliance with the Retailer Agreement").

Walmart does **not** publish numeric markup thresholds — the language is qualitative ("egregiously/substantially higher," "price gouging"). **Treat the reference price (visible on the Unpublished Items / Pricing Insights dashboard) as the de‑facto ceiling.**

## 3. Buy Box mechanics (price‑led, effectively single‑winner)

The Buy Box goes to the "best overall value": lowest **landed** price (item + shipping), plus delivery speed/method (WFS/fast‑free‑shipping boost), in‑stock availability, seller performance, content quality, and customer geo. Lowest price doesn't *always* win, but price discipline within `[min, max]` is the lever the agent controls. Win/hold it by keeping landed price at/below the reference and the competitive floor — without violating the too‑low rule.

## 4. Content & prohibited‑content policy (for listing writes)

- **Prohibited Products Policy** (extensive): alcohol, drugs/paraphernalia, weapons, recalled items, PFAS, offensive/discriminatory content, IP‑infringing/counterfeit, reselling from competitors, etc. Violations → removal + possible suspension/termination.
- **IP/trademark:** you must **own** the items and have rights to sell branded products; content must not infringe third‑party IP.
- **Content standards:** English‑only, no conflicting info across images/packaging/attributes; "Made in USA" must be consistent.
- **Title hygiene (best practice):** ~50–75 chars; **no special symbols (™/®/*/½/^/hearts), no marketing claims ("Free Shipping","Best Seller","#1 rated","high quality"), no retailer‑specific info**; structure Brand + Key Features + Product Type + Attributes.

**Agent implication:** validate every generated title/description/image against these rules **before** submitting a feed; block any SKU in a prohibited category or lacking proven brand/IP rights.

## 5. Automation / bot rules

- **No blanket ban on legitimate API automation** (Walmart even sells its own Repricer), but:
  - Writes are **token‑bucket rate‑limited** (price single 100/hr, bulk feeds 10/hr, order actions 60/min); 429 on overflow, 413 on oversized payloads.
  - The **Seller Code of Conduct** forbids: uncompetitive/unfair shipping costs, raising retail price after an order completes, manipulating reviews/ratings, and attempts to override a Marketplace policy/decision.
  - **No Haggling Policy:** ad‑hoc customer price negotiation is prohibited (use pre‑set Partial Keep‑It rules) — relevant if an agent ever generates customer‑facing offers.
- **UI/browser automation** (not API) of public Walmart pages is prohibited without written consent (Terms of Use ban on robots/scraping). Driving *your own* Seller Center is lower‑risk but still ToS‑sensitive (see `01` Path E).

## 6. Hard agent invariants (engineering rules)

Encode these as non‑negotiable checks in the repricing/listing write path. The first two mirror Walmart's own Repricer (which refuses to run an item without them):

1. **Mandatory per‑SKU `min` and `max` price.** Reject any SKU lacking both. Set `min = max(unit_cost + min_margin, MAP_floor)` and `max ≤ reference_price`.
2. **Clamp every computed price to `[min, max]`.** Never below floor (margin **and** the too‑low suppression). If the competitive floor < min, **hold at min**, accept Buy Box loss — never sell at a loss or get suppressed.
3. **Reference price = ceiling.** Pull it from the Unpublished Items / Pricing Insights surface; keep landed price (item + shipping) at/below it.
4. **Per‑cycle change cap.** Limit any single adjustment to ≤ X% per cycle; larger swings require human approval.
5. **Cooldowns + rate budgeting.** Respect 100/hr·10/hr·60/min; honor the 10 shipping‑template‑edits/day lockout; back off on 429 via `X-Next-Replenishment-Time`. Walmart's own engine runs ~4‑hr cadence — don't thrash.
6. **Human‑approval gate** for large moves and any price below cost/MAP — hard stops, never auto‑override.
7. **Global kill‑switch** freezing all writes on anomaly (spike in unpublished SKUs, 429 storm, reference‑price data gaps) + **per‑SKU circuit breakers**.
8. **SKU allowlist** — everything else read‑only by default. One strategy/owner per SKU (no conflicting writes).
   - **Single source of truth** — the agent is the system of record for Walmart writes. (Optional: if you ever add another tool that also writes to Walmart, partition fields per system to avoid oversell / double‑write / price‑flapping.)
9. **"No competitive target" → hold last submitted price** (don't free‑fall to min).
10. **Content‑write validation** (§4) before any item feed.
11. **Audit + corrective‑action logging** on every change + the reference data behind it, so a Plan of Action can be assembled fast.

## 7. Appeals / corrective action (when a flag fires)

- **Pricing‑flag dispute (per‑SKU, fastest):** submit the **URL of a comparable item** via the Pricing Insights / Listing Quality dashboard ("Submit an external price match"); Walmart validates ~48 h.
- **Account‑suspension appeal:** Seller Center → **Help** → submit a written **Business Plan of Action** (root‑cause acknowledgment → corrective actions already taken → preventative controls), with supporting docs (warehouse photos, supplier invoices <2 months old, IP docs). Handled in order received; reinstatement not guaranteed; keep following the plan or risk a second suspension/termination.

Sources: `99-sources.md` → "Policy, scorecard & pricing rules."
