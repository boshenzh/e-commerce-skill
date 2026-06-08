# Glossary

| Term | Meaning |
|---|---|
| **Seller Center** | Walmart's seller console (`seller.walmart.com`). |
| **Developer Portal** | `developer.walmart.com` — API docs/reference + key‑management entry. |
| **Marketplace API** | Seller REST API (`marketplace.walmartapis.com/v3/...`). |
| **Solution Provider** | Walmart‑approved third‑party software vendor (DianXiaoMi is one). |
| **Connected App** | A Solution‑Provider app a seller OAuth‑authorized to act on their account. |
| **Delegated Access** | Legacy per‑provider scoped keys. Retiring 2026‑10‑01. |
| **client_credentials** | OAuth2 grant for a seller's own keys → 15‑min access token. |
| **Feed** | Async bulk job (items/inventory/price): submit → `feedId` → poll → per‑item results. |
| **MP_ITEM / MP_ITEM_MATCH** | Full new‑item feed vs offer‑only‑against‑existing‑catalog feed. |
| **Item Spec 5.0** | Current per‑category attribute schema (download via Get Spec). |
| **Buy Box** | Default "Add to Cart" offer; effectively winner‑take‑all, price‑led. |
| **Reference price** | Walmart's internal computed fair price; the de‑facto ceiling for the Pricing Rule. |
| **Repricer** | Walmart's native server‑side repricing engine (`/v3/repricer/strategy`). |
| **WFS** | Walmart Fulfillment Services — Walmart's "FBA": ship stock in, Walmart fulfills. |
| **MCS** | Multichannel Solutions — WFS fulfilling orders from other channels. |
| **Ship node** | A fulfillment center / warehouse for seller‑fulfilled inventory. |
| **ATS** | Available‑To‑Sell quantity. |
| **Lag time** | Order‑to‑ship days (0–1 typical; ≥2 needs category approval). |
| **Expected Ship Date (ESD)** | Date an order must ship by; auto‑cancel at ESD + 4 days. |
| **Listing Quality** | Walmart's 0–100 content/offer/discoverability/ratings score. |
| **Pro Seller Badge** | Performance tier (Rising/Advanced/Pro) with visibility/payout perks. |
| **Walmart+** | Walmart's membership program (free fast shipping); a high‑value audience. |
| **Walmart Connect / WCPN** | Walmart's ad business / its partner network gating the ads API. |
| **Scorecard** | Seller performance metrics (OTD/VTR/cancellation/etc.). |
| **DXM** | DianXiaoMi (店小秘) — the user's ERP; an API consumer with no open API. |
| **MAP** | Minimum Advertised Price — a floor the agent must never price below. |
| **爆款** | "Hot/winning product" — a high‑demand best‑seller (product‑research target). |
