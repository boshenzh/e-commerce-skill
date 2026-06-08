# Access & Auth (condensed)

Full version: `../../../docs/01-access-paths-and-connected-apps.md`.

## The seven access paths (pick A for your own shop)

| # | Path | Approval | Verdict |
|---|---|---|---|
| **A** | **Your own first‑party API keys** (`client_credentials`) | none | ✅ use this |
| B | Solution‑Provider OAuth app ("Connected App") | Walmart contract + ~3–5 wk | only to sell software to other sellers |
| C | Legacy Delegated Access keys | provider contract | ❌ retiring (no new after 2026‑07‑30; dead 2026‑10‑01) |
| D | Through an existing third‑party connected app | — | ❌ dead end if it has no open API |
| E | Browser/UI automation | — | ⚠️ last resort, ToS‑sensitive |
| F | 3rd‑party MCP/platform (Vinkius, CedCommerce…) | vendor | convenience layer only |
| G | Walmart Connect ads API | WCPN partner | separate (`walmart-advertising`) |

**Connected Apps** (`seller.walmart.com/apps/connected-apps`) = third‑party Solution‑Provider apps you OAuth‑authorized. You do **not** need to be one to automate your own shop.

## Generate your own keys

Seller Center → Settings → **API Key Management** → "Visit Developer Portal" → copy the **lock‑icon** personal key pair (`Client ID` + `Client Secret`). No application, contract, or review. These have full, unrestricted access to **your** account.

Seller keys vs Solution‑Provider keys: seller keys = full access; provider keys = no access until you grant per‑service scopes.

## Token flow

```
POST https://marketplace.walmartapis.com/v3/token
Authorization: Basic base64(<clientId>:<clientSecret>)
Content-Type: application/x-www-form-urlencoded
WM_SVC.NAME: Walmart Marketplace
WM_QOS.CORRELATION_ID: <uuid>

grant_type=client_credentials
→ { "access_token": "...", "token_type": "Bearer", "expires_in": 900 }   # 15 min
```

- Cache the token; **refresh at ~80% TTL (~12 min)**; single‑flight the refresh.
- Sandbox host: `https://sandbox.walmartapis.com` (add header `WM_SANDBOX: v2`). `WALMART_ENV=sandbox` selects it in the scripts.
- Legacy digital‑signature auth (`WM_SEC.AUTH_SIGNATURE`) is **deprecated** — use OAuth.

## Required headers on every call

`WM_SEC.ACCESS_TOKEN`, `WM_QOS.CORRELATION_ID` (fresh GUID), `WM_SVC.NAME: Walmart Marketplace`, `Accept`/`Content-Type: application/json`, optional `WM_CONSUMER.CHANNEL.TYPE`. `scripts/wm_request.py` sets these for you.

## ⚠️ Delegated Access retirement (2026)

No new Delegated‑Access keys after **2026‑07‑30**; all stop **2026‑10‑01**. Your own first‑party keys are **unaffected**. Audit `seller.walmart.com/apps/connected-apps` and re‑authorize (via OAuth Connect) anything still on Delegated Access before the cutoff.
