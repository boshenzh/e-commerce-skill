---
name: walmart-onboarding
description: "Walmart Marketplace application, approval, and account setup — the pre-API steps to become an approved US seller, then how to turn on API access. Use when the user is NOT yet selling on Walmart or is setting up the account: 'apply to Walmart Marketplace', 'get approved to sell on Walmart', 'Walmart seller application', 'set up my Walmart store', 'onboarding to Walmart', '入驻沃尔玛', '沃尔玛开店申请'. Not for API calls once approved (use walmart-seller)."
author: "boshenzh"
license: "Apache-2.0"
version: "0.1.0"
allowed-tools: "Read"
---

# Walmart Onboarding — get approved to sell, then turn on API access

The pre-API journey: application → review → onboarding checklist → go live → self-serve API keys. This is **advisory** (no live API). Once the seller has keys, hand off to the hub [`../walmart-seller/SKILL.md`](../walmart-seller/SKILL.md) for everything programmatic.

## When to use / when not to

- **Use** when the user is not yet an approved Walmart seller, or is mid-setup: applying, waiting on review, completing the partner profile, configuring payments/shipping/tax, or flipping on API access for the first time.
- **Not** for API calls once approved (auth, items, price, orders) → that's the hub and its spokes. Not for consumer Walmart shopping.
- **Key mental model:** getting **approved to sell** (a Walmart review, can be rejected) is a *different gate* from getting **API keys** (instant, self-serve, after approval). See gotcha #1.

## Eligibility — what Walmart expects before you apply

US sellers generally need:
- A **US business entity** with an **EIN / US Tax ID** and a completed **W-9**.
- A **US business address**.
- A **catalog of compliant products** (own the items + brand/IP; not a prohibited category — same content rules the hub enforces).
- A demonstrable **e-commerce / marketplace track record** (existing sales history, GMV, fulfillment quality). Approval is **reviewed and NOT guaranteed**.

There is an **international-seller path**, but it is **stricter** (more documentation, longer review). Default to the US-entity path if one exists.

## Workflow

1. **Apply.** Go to `marketplace.walmart.com` → "Request to sell" / sign up. Provide business info, **W-9 tax** details, the **product categories** you'll sell, and a **fulfillment plan** (seller-fulfilled vs **WFS** — Walmart Fulfillment Services).
2. **Wait for review.** Walmart reviews the application; expect **days to weeks**. Strengthen the application with a strong catalog + a credible fulfillment story (see gotcha #3). It can be rejected.
3. **Onboarding checklist (after approval).** Work top-to-bottom:
   - Complete the **partner / company profile** (logo, business display name, contact, policies).
   - Set up **payments**: connect the payout partner (**Payoneer / Hyperwallet** — verify current details in Seller Center) so Walmart can pay you.
   - Configure **shipping templates** + a **return policy**.
   - Complete **tax setup** (nexus, collection settings).
   - Create **test items** and **test orders**, verify they flow correctly.
   - **Request to go live.**
4. **Turn on API access (self-serve, instant).** Seller Center → **Settings → API Key Management** → copy **your own first-party `Client ID` / `Client Secret`** (the personal key pair). No further Walmart approval needed.
5. **Hand off to the hub.** Set the env vars and switch to [`../walmart-seller/SKILL.md`](../walmart-seller/SKILL.md):
   ```bash
   export WALMART_CLIENT_ID="…"
   export WALMART_CLIENT_SECRET="…"
   export WALMART_ENV="production"   # or sandbox
   ```
   Validate the creds immediately: `python3 ../walmart-seller/scripts/get_token.py`.
6. **(Optional) Connect a solution provider** (e.g. **DianXiaoMi**) by browsing **Seller Center → Apps → App Store → Connect** via **OAuth** — you authorize them, you do **not** paste your secret to them. Manage/renew/revoke them afterward under **Connected Apps** (`seller.walmart.com/apps/connected-apps`). See gotcha #4.

## Working example — validate keys the moment you have them

After step 4, confirm the new first-party keys mint a token before doing anything else:

```bash
export WALMART_CLIENT_ID="abc123…"
export WALMART_CLIENT_SECRET="xyz789…"
export WALMART_ENV="production"
python3 ../walmart-seller/scripts/get_token.py
# expect: an access_token with expires_in: 900 (15-minute TTL)
```

If this returns a token, onboarding-to-API is done — everything else (items, price, orders) lives in the hub and its spokes.

## Gotchas

1. **API KEYS ≠ APPROVAL TO SELL.** Generating keys is instant and self-serve; getting *approved to sell* is a Walmart review that can be **rejected**. Don't tell the user "you're in" just because the developer portal showed a key pair — that step only exists *after* approval.
2. **You generally need a real US entity + Tax ID** (EIN, W-9, US address). The international path exists but is stricter; don't promise approval without it.
3. **Approval favors a strong catalog + fulfillment story.** A thin catalog or vague fulfillment plan is the common rejection cause. Lead with proven e-commerce track record and a clear seller-fulfilled-or-WFS plan.
4. **Never share your `Client Secret` with a provider.** Authorize DianXiaoMi (or any ERP) by browsing **Seller Center → Apps → App Store → Connect** via **OAuth**, which grants scoped access without exposing your first-party secret; manage/renew/revoke them under **Connected Apps** (`seller.walmart.com/apps/connected-apps`). Your own keys stay yours.
5. **2026 access change:** legacy **Delegated Access** keys retire **2026-10-01** (no *new* delegated keys after **2026-07-30**). Your **own first-party keys are unaffected** — this is the path to use. Detail: [`../walmart-seller/references/access-and-auth.md`](../walmart-seller/references/access-and-auth.md).

## Load deeper

- **Keys + auth flow + the seven access paths:** [`../walmart-seller/SKILL.md`](../walmart-seller/SKILL.md) and [`../walmart-seller/references/access-and-auth.md`](../walmart-seller/references/access-and-auth.md).
- **Exact endpoints + rate limits** (once you start calling the API): [`../walmart-seller/references/api-reference.md`](../walmart-seller/references/api-reference.md).
- **Account-safety scorecard + pricing/content invariants** (read before any write, and configure shipping/returns/tax to match): [`../walmart-seller/references/guardrails.md`](../walmart-seller/references/guardrails.md).
- **Routing to the right spoke** for listing/pricing/WFS/orders work: the hub's capability map.
