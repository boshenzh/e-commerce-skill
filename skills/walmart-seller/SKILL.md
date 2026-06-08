---
name: walmart-seller
description: "Hub skill for operating a Walmart Marketplace (US) seller store as an agent. Owns the shared machinery every other walmart-* skill depends on: ACCESS & AUTH (use the seller's OWN first-party API keys — no Walmart approval needed; OAuth2 client_credentials → 15-min token), a condensed API map (items/inventory/price/orders/returns/WFS/reports/notifications), the ACCOUNT-SAFETY GUARDRAILS (scorecard thresholds + pricing-suppression rules + hard write invariants), and runnable Python helpers (get_token, wm_request, guardrail_check). Routes to the right spoke skill for a task. Use FIRST whenever the user wants to do anything on Walmart Marketplace: 'connect my Walmart shop', 'get a Walmart API token', 'call the Walmart marketplace API', 'reprice on Walmart', 'is this price safe', 'manage my Walmart store', '沃尔玛卖家', '连接沃尔玛店铺'. Sits ALONGSIDE an ERP like DianXiaoMi (which owns inventory push + fulfillment) — do not duplicate its writes."
author: "boshenzh"
license: "Apache-2.0"
version: "0.1.0"
allowed-tools: "Read Bash WebFetch"
metadata:
  openclaw:
    requires:
      bins:
        - python3
    env:
      - WALMART_CLIENT_ID
      - WALMART_CLIENT_SECRET
      - WALMART_ENV
---

# Walmart Seller — hub (auth, API map, guardrails, routing)

This is the entry point for everything on Walmart Marketplace (US). Read this first, then jump to the spoke skill for the specific job. The deep research lives in the bundled [`docs/`](../../docs/README.md); the condensed, action‑ready versions live in this skill's `references/`.

## When to use / when not to

- **Use** for any Walmart seller operation: authenticating, calling the API, repricing, listing, fulfilling, researching products, checking account safety.
- **Not** for Walmart **advertising** programmatically beyond planning — the ads API is partner‑gated (`walmart-advertising`). Not for **consumer** Walmart shopping (this is the seller side).
- **Coexistence:** the user runs **DianXiaoMi (DXM)**, which owns inventory push + order fulfillment. This agent layer is **read‑mostly** and writes to Walmart only through narrow, guarded paths (price/listing/Buy Box) or Walmart's native Repricer. Never routinely acknowledge/ship orders or push inventory from here — that double‑fulfills/oversells. See `../../docs/06-dianxiaomi-and-data-flow.md`.

## Access model (do this once)

Automating **your own** shop needs **your own first‑party API keys** — **no Walmart approval, no "Connected App", no partnership.**

1. Seller Center → **Settings → API Key Management** → "Visit Developer Portal" (auto‑signs you in).
2. Copy the **personal key pair** (the row with the **lock icon**): `Client ID` + `Client Secret`.
3. Export them (never hard‑code; never put them in a prompt):
   ```bash
   export WALMART_CLIENT_ID="…"
   export WALMART_CLIENT_SECRET="…"
   export WALMART_ENV="production"   # or sandbox
   ```

Full detail + the seven access paths + the Delegated‑Access 2026 retirement: `references/access-and-auth.md` and `../../docs/01-access-paths-and-connected-apps.md`. New to the platform? Start with `walmart-onboarding`.

## Authentication (every call)

- Token: `POST https://marketplace.walmartapis.com/v3/token`, HTTP Basic `base64(clientId:clientSecret)`, body `grant_type=client_credentials`. Returns `access_token` with **`expires_in: 900` (15 min)**.
- **Cache the token; refresh at ~80% TTL (~12 min).** Don't mint a token per call.
- Every API call carries: `WM_SEC.ACCESS_TOKEN`, `WM_QOS.CORRELATION_ID` (a fresh GUID), `WM_SVC.NAME: Walmart Marketplace`, `Accept`/`Content-Type: application/json`.

Use the scripts instead of re‑implementing this:

```bash
# 1) mint + print a token (validates your creds)
python3 scripts/get_token.py                # --env sandbox supported

# 2) make any authenticated call (auto token caching + 429 backoff)
python3 scripts/wm_request.py GET  /v3/orders/released --query createdStartDate=2026-06-01
python3 scripts/wm_request.py GET  /v3/items --query 'limit=20&nextCursor=*'
python3 scripts/wm_request.py PUT  /v3/price --body @price.json

# 3) BEFORE any price write, validate it against the guardrails
python3 scripts/guardrail_check.py --sku ABC --proposed 19.99 \
    --cost 12.00 --map 17.99 --min 17.99 --max 29.99 --last 21.99 \
    --max-change-pct 15 --reference 24.99
```

## Capability map — route to the right spoke

| Goal | Skill |
|---|---|
| Apply / get approved / set up the account | `walmart-onboarding` |
| Create or optimize a listing | `walmart-listings` |
| Rank higher in Walmart search | `walmart-seo` |
| Set up / run WFS fulfillment | `walmart-wfs` |
| Plan ads / get ads API access | `walmart-advertising` |
| Win the Buy Box / reprice | `walmart-buybox-pricing` |
| Qualify for the Pro Seller badge | `walmart-pro-seller` |
| Reach Walmart+ / high‑value buyers | `walmart-customer-targeting` |
| Process seller‑fulfilled orders | `walmart-fulfillment-ops` |
| Find winning products (爆款) | `walmart-product-research` |

API endpoint quick‑reference for any of these: `references/api-reference.md`.

## Global safety rules (non‑negotiable — full text in `references/guardrails.md`)

Any **write** the agent makes must respect these, or it risks SKU suppression or account suspension:

1. **Price has hard bounds.** Never below `max(cost + min_margin, MAP)`; never above the Walmart **reference price** (the de‑facto ceiling). Clamp to `[min, max]`. Run `scripts/guardrail_check.py` first.
2. **Too‑low prices get suppressed too** (reason "Pricing Error"), not just too‑high ("Reasonable Price Not Satisfied"). A runaway downward repricer is dangerous.
3. **Cap per‑cycle change** (e.g. ≤15%); larger moves need human approval. **Cooldowns** per SKU. Walmart's own engine runs ~4‑hr cadence — don't thrash.
4. **Respect rate limits** (price single 100/hr, bulk feeds 10/hr, order actions 60/min); on `429` back off using `x-next-replenish-time` (handled by `wm_request.py`).
5. **Don't fight DXM.** Don't write fields DXM owns (inventory, order ack/ship). Prefer propose‑to‑human for anything DXM also syncs.
6. **Content compliance** before any listing write (no marketing claims/symbols in titles, English‑only, IP‑owned, not a prohibited category).
7. **Kill‑switch + audit.** Freeze all writes on anomaly (unpublish spike, 429 storm); log every write + the data behind it for Plan‑of‑Action appeals.
8. **Feed writes are async + can lie:** `feedStatus=PROCESSED` ≠ item live, and a `200` may not have applied. Always **poll per‑item status, then read back** ~60 s later.

## Gotchas

- **"Connected Apps" ≠ how you build this.** Connected Apps are third‑party OAuth tools (DXM is one). Your in‑house agent uses your own keys directly — no App Store listing. (`references/access-and-auth.md`.)
- **DianXiaoMi has no open API** — you cannot drive it programmatically. Integrate at the Walmart layer. (`../../docs/06`.)
- **Token TTL is 15 minutes.** Stale‑token 401s are the #1 integration bug — cache + proactively refresh.
- **Scripts use Python stdlib only** (`urllib`), so they run anywhere with `python3`; no `pip install` needed.
- **developer.walmart.com is a JS SPA** — exact field spellings/limits can drift; confirm against a live sandbox call (`references/api-reference.md` flags the uncertain ones).
