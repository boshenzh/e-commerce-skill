# Walmart Marketplace × AI Agent — Research & Build Library

This folder is a self‑contained reference for running a **US Walmart Marketplace seller account** with a **standalone AI agent** as the sole system of record. It answers three questions end‑to‑end: *how do I (or an agent) get access?*, *what can the Walmart APIs do?*, and *how do I automate safely without risking the account?*

> Compiled June 2026 from a 25‑agent web‑research pass over `developer.walmart.com`, `marketplacelearn.walmart.com`, `seller.walmart.com`, and the `highsidelabs/walmart-api-php` + `api-evangelist` OpenAPI mirrors. Load‑bearing facts (auth, webhooks, rate limits, scorecard, MCP availability) were independently fact‑checked. The Walmart developer portal is a JavaScript SPA, so a handful of exact field spellings / rate numbers are flagged "verify against a live sandbox call." See `99-sources.md`.

## How to read this

| Start here if you want to… | Read |
|---|---|
| Understand the whole picture in one page | `00-overview.md` |
| Know **how an agent can access** your shop (Connected Apps, your own keys, etc.) | `01-access-paths-and-connected-apps.md` |
| Look up **what each Walmart API does** (endpoints, params, limits) | `02-walmart-api-reference.md` |
| See **the actual automations** mapped to APIs | `03-agent-automation-playbook.md` |
| Design the **system + roll it out in phases** | `04-architecture-and-build-plan.md` |
| Know the **rules that keep the account alive** | `05-guardrails-and-policy.md` |
| Understand **how the standalone agent owns the store + data flow** | `06-standalone-operation.md` |
| Find the **source URL** for any claim | `99-sources.md` |

## The 60‑second answer

- **To automate your own shop, use your OWN first‑party API keys** (Seller Center → API Key Management → personal Client ID/Secret). **No Walmart approval needed.** You do *not* need to become a "Connected App."
- **Connected Apps** = third‑party Solution‑Provider apps you OAuth‑authorized. That program is for software distributed to *many* sellers — you don't need it to run your own shop.
- **The agent is standalone** — it owns the whole Walmart store directly through the Marketplace API with your own keys; no ERP or middleman is required.
- **Walmart has push webhooks** (PO created, returns, Buy Box, OOS, …) — not poll‑only. Design a webhook + reconciliation hybrid.
- **The account is protected by automated suppression** (pricing rules) and a **performance scorecard**. Every write the agent makes must respect hard guardrails (per‑SKU min/max price, never below cost/MAP, change caps, kill‑switch). See `05`.
- ⚠️ **Legacy Delegated Access keys are retiring** — none after **2026‑07‑30**, all dead **2026‑10‑01**. Your own first‑party keys are unaffected.

## Glossary

| Term | Meaning |
|---|---|
| **Seller Center** | Walmart's web console for sellers (`seller.walmart.com`). |
| **Developer Portal** | `developer.walmart.com` — API docs, references, Postman, key management entry. |
| **Marketplace API** | The seller‑facing REST API (`marketplace.walmartapis.com/v3/...`) for items, inventory, price, orders, returns, WFS, reports. |
| **Solution Provider** | A Walmart‑approved third‑party software vendor (ERP/listing/ads tool). |
| **Connected App** | A Solution‑Provider app a seller has OAuth‑authorized to act on their account. |
| **Delegated Access** | Legacy per‑provider scoped keys. **Being retired in 2026.** |
| **WFS** | Walmart Fulfillment Services — Walmart's "FBA": you ship stock to Walmart, they fulfill. |
| **MCS** | Multichannel Solutions — WFS fulfilling orders from *other* channels (Amazon/eBay/Temu…). |
| **Buy Box** | The default "Add to Cart" offer on a product page; effectively winner‑take‑all, price‑led. |
| **Feed** | An async bulk job (items/inventory/price). Submit → `feedId` → poll status → per‑item results. |
| **Ship node** | A fulfillment center / warehouse location for seller‑fulfilled inventory. |
| **ATS** | Available‑To‑Sell quantity. |
| **ODR / Scorecard** | Seller performance metrics (on‑time delivery, valid tracking, cancellation, etc.). |
| **MCP** | Model Context Protocol — a standard way to expose tools to an AI agent. |
