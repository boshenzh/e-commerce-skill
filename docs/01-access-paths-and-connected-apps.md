# 01 — Access Paths & Connected Apps

> This chapter answers, in full: *"My shop is managed through a Connected App — can I operate through one? How are connected apps used? What are the different ways to access the shop through agents (connected apps, APIs, etc.)?"*

## 1. The short answer

There are **seven** ways an agent/software can touch a Walmart seller account. They split on one axis: **are you automating your *own* shop, or distributing software to *many* sellers?**

| # | Path | Auth mechanism | Approval needed | What it can do | Verdict for you |
|---|---|---|---|---|---|
| **A** | **Your own first‑party API keys** | OAuth2 `client_credentials` (your Client ID/Secret), 15‑min token | **None** beyond being a seller | Full, unrestricted access to **your** account's API | ✅ **Recommended** |
| B | Approved **Solution Provider** OAuth app (a "Connected App") | OAuth2 `authorization_code` + 1‑yr refresh, scoped | Walmart contract + ~3–5 wk review | Operate **many** sellers who authorize you | Only if you later sell the agent |
| C | Legacy **Delegated Access** keys | per‑provider Client ID/Secret, granular scopes | provider must already be contracted | Like A but delegated to a 3rd party | ❌ **Retiring** (see §6) |
| D | *Through* an existing connected app (e.g. DianXiaoMi) | n/a | n/a | Nothing — **DXM has no open API** | ❌ Dead end |
| E | **Browser / UI automation** of Seller Center or DXM | logged‑in session cookies | none (but ToS‑sensitive) | Anything visible in the UI | ⚠️ Last resort |
| F | **3rd‑party hosted MCP / platform** (Vinkius, CedCommerce, ChannelEngine, Linnworks) | the vendor's auth | the vendor's onboarding | Wraps the same API + multichannel | Convenience layer only |
| G | **Walmart Connect ads** API (Sponsored Search/Display) | partner‑gated | WCPN partner approval | Ad campaigns/reporting — separate from Marketplace | Separate track |

**Bottom line:** automate your own shop with **Path A** (your own keys). Becoming a Connected App (Path B) is for distribution to other sellers. DXM (Path D) can't be driven programmatically.

## 2. What "Connected Apps" actually is

In Seller Center, under the **Apps** left‑nav heading, there are two related surfaces:

- **App Store / App Listings** — a directory of Walmart‑approved Solution Providers (ERPs, listing/order/inventory/ads tools) you can connect to your account.
- **Connected Apps** (`seller.walmart.com/apps/connected-apps`) — the list of providers you have **already authorized**, with **Renew** and **Revoke** controls.

**DianXiaoMi is a confirmed approved Walmart Solution Provider** ([listing](https://marketplace.walmart.com/solution-providers/dianxiaomi/)) — categories include Advertising, Full Service, Inventory Management, Item Setup, Order Management, Pricing, Returns, Shipping & Fulfillment. So when you "manage your shop through DianXiaoMi," DXM appears here as one of your OAuth‑authorized Connected Apps.

### Lifecycle of a connected app

1. **Browse** the App Store → pick a provider.
2. **Connect** → you're redirected to the provider's site to sign in.
3. **Authorize** → check the box accepting the provider's privacy policy, then you're sent to Walmart's auth server (`login.account.wal-mart.com/authorize`), review the requested scope, and click **Authorize**.
4. The app now acts on your behalf using **revocable tokens** — **you never share your password or your own API secret**.
5. **Annual renewal** — OAuth authorizations expire yearly; go to **Connected Apps → Renew** (extends one year). Walmart notifies you when a provider migrates to OAuth 2.0.
6. **Revoke** — **Connected Apps → Revoke** instantly cuts that app's access to your data.

Only approved providers who have implemented OAuth 2.0 are connectable; not every provider supports it yet.

## 3. How a connected app works technically (OAuth 2.0 authorization‑code)

```
Seller clicks "Connect"
   → GET https://login.account.wal-mart.com/authorize
        ?responseType=code&clientId=<provider>&redirectUri=<provider>&clientType=...&nonce=...&state=...
   → seller authorizes; Walmart redirects an auth CODE to provider's redirectUri
   → provider POST https://marketplace.walmartapis.com/v3/token
        Authorization: Basic base64(<provider clientId>:<provider secret>)
        body: grant_type=authorization_code & code=<code> & redirectUri=...
   → returns { access_token (Bearer, ~15 min), refresh_token (~1 year), expires_in }
```

- **Scopes are per service** (item setup, orders, inventory, pricing, content, …) — the seller controls what the app may touch.
- The **1‑year refresh‑token lifetime** is exactly why Walmart requires **annual re‑authorization**.

## 4. How to generate YOUR OWN keys (Path A) — the recommended route

You do **not** go through the App Store for this. Per Walmart's official "Get started as a seller" docs:

1. In **Seller Center**, open **Settings → API Key Management** (entry point also linked as `seller.walmart.com/api-key`).
2. Click **"Visit Developer Portal"** — you're auto‑signed‑in with your Seller Center credentials (choose login type **Marketplace (US, Mexico, Canada & Chile)**).
3. Your **personal key pair** is already there — the row marked with a **lock icon**.
4. **Copy your Client ID and Client Secret.**

There is **no application, no contract, no human review, no App Store listing**. These keys have **full, unrestricted access to your own account's entire Marketplace API surface**.

Then your agent/middleware authenticates:

```
POST https://marketplace.walmartapis.com/v3/token
Authorization: Basic base64(<clientId>:<clientSecret>)
Content-Type: application/x-www-form-urlencoded
WM_SVC.NAME: Walmart Marketplace
WM_QOS.CORRELATION_ID: <uuid>

grant_type=client_credentials
→ { access_token, token_type: "Bearer", expires_in: 900 }   # 15 minutes
```

…and sends `WM_SEC.ACCESS_TOKEN: <access_token>` on every subsequent call. (See `02` for the full header set.)

## 5. Seller keys vs Solution‑Provider keys (why the distinction matters)

| | **Seller (self) keys** | **Solution‑Provider keys** |
|---|---|---|
| Who creates | You, in Seller Center | You mint a *separate* pair for a named, Walmart‑approved provider |
| Default access | **Full / unrestricted** (lock icon) | **None** until you grant per‑object scopes (Items, Orders, Inventory, Prices…) |
| Use case | Your own in‑house automation | Letting a third party act on your behalf |
| Revocation | Rotate in the portal | Revoke just that provider without touching your own keys |

For your agent, **use your own seller keys** and keep them on your own infrastructure (secret manager). If you ever build a multi‑tenant product, you'd mint Solution‑Provider/OAuth credentials per seller instead.

## 6. ⚠️ Delegated Access is being retired (act before the cutoff)

There are three generations of third‑party access; only the newest rolls forward:

- **Gen 1 — Digital signature** (Consumer ID + Private Key, `WM_SEC.AUTH_SIGNATURE`): long deprecated (~2019). Ignore.
- **Gen 2 — Delegated Access** (separate per‑provider Client ID/Secret with granular scopes): **now deprecated** — **no new keys after 2026‑07‑30**, and **all delegated keys stop working 2026‑10‑01** (one Walmart FAQ says "until September 2026" — treat **Oct 1 2026** as the hard stop). The Delegated Keys section is being removed from the portal.
- **Gen 3 — OAuth 2.0 via the Seller Center App Store** (current standard for ERPs/partners): the seller authorizes an approved app; Walmart issues it tokens.

**What this means for you:**
- **Path A (your own first‑party keys) is unaffected** — keep building on it.
- If DianXiaoMi (or any other connected app) still rides Delegated Access, it must be re‑authorized via **Connect** in the App Store (OAuth 2.0) before the cutoff. **Audit `seller.walmart.com/apps/connected-apps`** and re‑connect anything flagged for migration.

## 7. Why you can't go "through" DianXiaoMi (Path D)

DianXiaoMi talks to Walmart via Walmart's official APIs under the hood, but **exposes no open/public API to its own users** — no developer portal, no API reference, no app registration, no outbound webhook. (Confirmed against its help center; AI‑generated SEO pages claiming a DXM "open API with order/product/inventory interfaces" are hallucinated boilerplate — see `06`.)

Consequence: "operating through DXM programmatically" collapses into **UI automation of DXM's web app** (Path E) — strictly worse than just calling the Walmart API directly, since you'd be screen‑driving a tool that is itself only calling that API. **Talk to Walmart directly.**

## 8. UI / browser automation (Path E) — when and the caveats

Use only for the rare operations that genuinely have no API endpoint. It drives a logged‑in browser (computer‑use / Playwright / Claude‑in‑Chrome) by simulating clicks.

- **Brittle** (breaks on any layout change), slow, hard to make transactional.
- **ToS‑sensitive:** Walmart's Terms of Use prohibit using "any robot, spider… to retrieve, index, scrape, data mine, or otherwise gather any Walmart Materials" without prior written consent; Walmart detects automation (CAPTCHA/MFA/blocks). Lower‑risk on *your own* seller account than scraping public pages, but still against ToS and a possible account flag.
- **Never** use it for things the API already covers (it covers nearly everything you'd want).

## 9. Third‑party MCP / platforms (Path F)

- **Hosted MCP gateways** (e.g. **Vinkius** "Walmart Marketplace MCP," ~8 agent tools like `wm_update_inventory`, `wm_set_price`, `wm_list_items`): one‑command connect, server‑side credential injection. **But Vinkius is explicitly *not* affiliated with or authorized by Walmart**, it's a paid subscription, and it ultimately drives *your* keys on *their* infrastructure — an extra third party in your trust path. Prefer building a **thin MCP wrapper around your own keys on your own host**.
- **Integration platforms** (CedCommerce, ChannelEngine, Linnworks, Zentail): full multichannel SaaS that connect to Walmart and expose *their own* APIs an agent could orchestrate. Worth it only if you genuinely need multichannel (Walmart + Amazon + Shopify) in one place; otherwise an unnecessary layer over Path A.

## 10. Walmart Connect ads (Path G) — separate, partner‑gated

The Walmart Connect advertising APIs (Sponsored Search/Products, Sponsored Brands, Display) are **publicly documented but not self‑serve** — access is gated to **Walmart Connect Partner Network (WCPN)** partners (tiers: Full‑Service, Campaign Management, Reporting Only, Creative Only). Your Marketplace seller keys do **not** unlock ads. Pursue separately (via an approved partner like Pacvue/Skai, or by applying to WCPN) only if/when you want to manage ads programmatically. Production base for Sponsored Products: `https://developer.api.walmart.com/api-proxy/service/WPA/Api/v1/`.

## 11. Decision matrix

| Your goal | Do this |
|---|---|
| **Automate your OWN single shop (your case)** | **Path A** — your own seller keys + a thin self‑hosted MCP/tool layer |
| Want agent ergonomics fast, OK adding a 3rd party | Path F1 (hosted MCP) as a convenience layer over your own keys |
| Need Walmart **plus** other channels in one system | Path F2 (ChannelEngine/CedCommerce/Linnworks) |
| A few UI‑only actions with no API | Path E (browser automation), sparingly, own account only |
| **Later: sell the agent to MANY sellers** | **Path B** — become an approved Solution Provider, ship an OAuth Connected App |
| Manage Walmart **ads** programmatically | Path G — apply to WCPN separately |
| Anything currently on Delegated Access | Migrate to OAuth 2.0 before **2026‑10‑01** |

Sources for this chapter: see `99-sources.md` → "Access, auth & Connected Apps."
