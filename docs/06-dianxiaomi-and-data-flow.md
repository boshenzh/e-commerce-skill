# 06 — DianXiaoMi (店小秘) & Data Flow

## What DianXiaoMi is

DianXiaoMi (店小秘) is a **free Chinese cross‑border e‑commerce ERP/SaaS** that aggregates **60+ marketplaces** (Amazon, eBay, Shopify, AliExpress, Wish, Shopee, Lazada, Coupang, Ozon, Temu, WooCommerce, **Walmart**, etc.). For a Walmart seller it typically handles:

- **Order processing** — pulls Walmart POs, batches, prints shipping labels and logistics docs.
- **Inventory & stock sync** — tracks stock across channels and pushes available quantities out.
- **Listing / publishing** — create/maintain listings, promotions, ads.
- **Procurement / purchasing** — 1688/supplier sourcing, purchase orders.
- **Warehouse / overseas‑warehouse / FBA‑style management**, profit reports.

It is a **confirmed approved Walmart Solution Provider** ([marketplace.walmart.com/solution-providers/dianxiaomi](https://marketplace.walmart.com/solution-providers/dianxiaomi/)) across categories: Advertising, Full Service, Inventory Management, Item Setup, Order Management, Pricing, Research & Analytics, Returns, Shipping & Fulfillment. So in your `seller.walmart.com/apps/connected-apps`, DXM appears as one of your OAuth‑authorized **Connected Apps**.

## The critical constraint: DXM has NO open API

After checking DXM's help center, platform‑authorization articles, and third‑party docs, there is **no public developer API / 开放平台**:

- No developer portal, no API reference, no app registration/ISV onboarding, **no DXM‑issued AppKey/AppSecret** for outbound access.
- DXM is an **API consumer, not a provider.** Integration always flows **into** DXM: you paste **another platform's** credentials (e.g. Walmart, Shopify, Coupang Access/Secret keys) into DXM, and DXM pulls/pushes on your behalf.

⚠️ **Common confusion:** articles saying "obtain the API key and secret to connect to DianXiaoMi," or "set API usage to 开放API/Open API," **always refer to the EXTERNAL platform's** open API (Coupang's Access Key, a Shopify app key) — **not** a DXM‑exposed API. AI‑generated SEO/Q&A pages (AMZ123, PingCode) that claim DXM "provides rich open API interfaces (order/product/inventory/member) and a developer key page" are **hallucinated boilerplate**, uncorroborated by any primary DXM source. **Treat them as false.**

### What this means for your agent

There is **no official, documented way to programmatically call DianXiaoMi.** Your only options to "reach DXM" are:

1. **Integrate at the Walmart layer** that DXM also reads from — **the recommended approach.** Your agent talks to the same Walmart Marketplace API DXM uses underneath.
2. **DXM's own UI** (manual, or brittle browser/computer‑use automation — `01` Path E).
3. **Contact DXM business/technical support** to ask about any private/partner integration (no public terms exist).

→ The agent **cannot write back into DXM**, which is exactly why the architecture is **"augment, don't replace; propose, don't clobber"** (`04`).

## Data‑flow model

```
                    ┌──────────── Walmart Marketplace (system of record for live state) ───────────┐
                    │                                                                                │
   DianXiaoMi ──────┤ pushes inventory, ships orders, writes tracking, manages listings (OWNS these) │
   (no inbound API) │                                                                                │
                    │   ▲ reads (events + REST)                          writes (gated, narrow)  ▲    │
                    └───┼─────────────────────────────────────────────────────────────────────┼────┘
                        │                                                                        │
                 ┌──────┴───────────────────────────────────────────────────────────────┐      │
                 │  Agent middleware  — reads Walmart truth, reasons, proposes/alerts     │──────┘
                 │  • cannot push to DXM      • writes to Walmart only in domains DXM      │
                 │  • bootstraps entity map     leaves alone, or via native Repricer       │
                 └────────────────────────────────────────────────────────────────────────┘
```

- **DXM and the agent are two writers to Walmart.** To avoid flapping/oversell, partition fields: DXM owns inventory + order‑state + listings; the agent owns (Phase 2+) only price deltas / Buy Box within bounds. Enforce with a **conflict tripwire** (if the agent writes price Y and DXM pushes X back, alert + suspend agent writes on that SKU) — see `04` §6.

## The canonical entity map

Because you can't query DXM, build the join in your middleware and key it on **Walmart‑side identifiers**:

```
entity_map: (walmart_sku, gtin/upc, walmart_item_id (wpid), dxm_sku, internal_offer_id)
```

- **Bootstrap from Walmart**, not DXM: enumerate `GET /v3/items` (cursor) to get `sku`, `wpid`, identifiers, `publishedStatus`.
- Map `dxm_sku` either by convention (if DXM uses the same SKU you set on Walmart) or via a periodic **export from the DXM UI** matched on SKU/GTIN.
- Treat the Walmart identifiers as the keys the agent reasons on.

## Practical recommendation

**Skip DXM for automation; talk to Walmart directly with your own keys.** DXM keeps doing what it's good at (order ingestion, label/logistics, inventory push, procurement). The agent adds the **Walmart‑native intelligence layer** DXM doesn't provide: event‑driven monitoring, Buy‑Box/pricing analytics, reconciliation, scorecard early‑warning, and a narrow set of guarded price/listing writes. If you ever need the agent and DXM to coordinate tighter, the only lever is DXM's support team — there is no API to build on.

Sources: `99-sources.md` → "DianXiaoMi."
