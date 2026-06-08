# 00 — Overview & Executive Summary

## Your setup

- **Role:** US‑based e‑commerce shop owner selling on **Walmart Marketplace** (third‑party seller).
- **ERP today:** **DianXiaoMi (店小秘)** — a free Chinese cross‑border ERP that already connects to your Walmart shop (as an approved Solution Provider) and handles order sync, inventory, listing, label/logistics printing, and procurement.
- **Goal:** automate the operational workflow and connect **your own AI agent** to the Walmart shop — without replacing DianXiaoMi and without risking the seller account.
- **Stance chosen:** **runtime‑agnostic.** These docs describe the Walmart side + a generic MCP/tool layer that any agent runtime (a Claude/MCP agent, a custom Python/TS orchestrator, or an n8n/Make flow) can consume.

## The big picture

```
                 ┌─────────────────────────── Walmart Marketplace ───────────────────────────┐
                 │  Push Notifications (webhooks)            REST API (poll + writes)          │
                 │      PO created, returns, OOS, Buy Box …  items/inventory/price/orders/...  │
                 └───────────▲───────────────────────────────────▲───────────────────────────┘
                             │ events                             │ reads/writes (your OWN keys)
            ┌────────────────┴─────────────────┐                 │
            │   Agent middleware (you build)    │   ┌─────────────┴──────────────┐
            │   • webhook receiver + dedup       │   │  Walmart MCP / tool layer  │
            │   • event ledger + entity map      │──▶│  READ tools  (always on)   │
            │   • reconciliation sweeps          │   │  WRITE tools (dry-run +    │
            │   • decision + audit store         │   │   human approval gate)     │
            └────────────────┬───────────────────┘   └────────────────────────────┘
                             │ proposes / alerts
                             ▼
                    AI agent (any runtime)

   DianXiaoMi (unchanged) ── owns inventory push, fulfillment, procurement ── runs ALONGSIDE
```

The agent uses **your own first‑party API keys**, sits **alongside** DianXiaoMi (not replacing it), is **read‑mostly**, and writes to Walmart only through narrow, idempotent, human‑gated paths (or Walmart's own native Repricer).

## Executive summary of findings

1. **Access is easy for your own shop.** A single seller automating their own account just generates a personal Client ID/Secret in Seller Center and calls the Marketplace API with the OAuth2 `client_credentials` grant. **No partnership, contract, or "Connected App" approval is required.** (Details: `01`.)

2. **"Connected Apps" is a different thing** — it's the list of third‑party Solution‑Provider apps (like DianXiaoMi) you've OAuth‑authorized to act on your behalf. Becoming a Connected App is only necessary if you want to *distribute* your agent to other sellers. (Details: `01`.)

3. **DianXiaoMi exposes no open API.** It is an API *consumer*, not a provider — you cannot push to it or pull from it programmatically in any supported way. So the agent must integrate at the **Walmart layer** (the same API DXM uses underneath), not "through" DXM. (Details: `06`.)

4. **The Walmart Marketplace API is broad and capable** — full CRUD over Items/Catalog, Inventory, Price/Promotions, Orders, Returns, WFS fulfillment, plus Reports/Insights/Settlement and a native server‑side Repricer. Most bulk writes are **async feeds** (submit → poll → per‑item results). (Details: `02`.)

5. **Walmart has push webhooks** ("Notifications") — PO created, returns, inventory OOS, Buy Box change, offer published/unpublished, report ready, and more. This corrects the common belief that Walmart is poll‑only. Best design is a **webhook receiver + reconciliation‑sweep hybrid**. (Details: `02`, `04`.)

6. **There is no official Walmart MCP server**, and community ones target the *consumer shopping* side, not the seller API. One proprietary paid seller‑API MCP exists (Vinkius, **not** Walmart‑affiliated). Walmart **does** publish OpenAPI specs (per section). Practical path: **build a thin MCP/tool layer around your own keys.** (Details: `01`, `04`.)

7. **The account is protected by automated enforcement.** Pricing that's too high *or too low* gets **auto‑suppressed/unpublished**; a **performance scorecard** (on‑time delivery, valid tracking, cancellation, etc.) governs account health; repeated violations escalate to suspension. Any autonomous agent must hard‑enforce guardrails. (Details: `05`.)

8. ⚠️ **Time‑sensitive:** legacy **Delegated Access** keys are being retired (no new keys after **2026‑07‑30**; all dead **2026‑10‑01**). Everything moves to OAuth 2.0 via the App Store. Your own first‑party keys are unaffected — but verify nothing critical still rides Delegated Access. (Details: `01`.)

## Headline corrections to common misconceptions

| Common belief | Reality |
|---|---|
| "Walmart is poll‑only; no webhooks." | ❌ Walmart has push **Notifications/webhooks** for orders, returns, OOS, Buy Box, etc. |
| "I must become a partner / Connected App to use the API." | ❌ For your own shop, just use your own keys. No approval. |
| "DianXiaoMi has an open API I can call." | ❌ It does not. AI‑written SEO pages claiming otherwise are hallucinations. |
| "There's an official Walmart MCP server." | ❌ None official; community ones are consumer‑shopping, not seller API. |
| "Repricing means hammering the price API." | ❌ The price write limits are tight (100/hr single, 10/hr bulk). Prefer Walmart's **native Repricer** or webhook‑triggered selective updates. |

## What to build (summary; full plan in `04`)

A small **middleware** + **MCP/tool layer** in front of the Walmart Marketplace API, rolled out in phases:

- **Phase 0** — foundation: own keys, token cache, webhook receiver, event ledger, entity map, READ‑only tools.
- **Phase 1** — read‑only analytics & recommendations (zero writes; writes exist only as `dry_run` diffs).
- **Phase 2** — human‑in‑the‑loop writes behind approval tokens.
- **Phase 3** — supervised autonomy for low‑risk, well‑bounded actions (e.g. repricing within a pre‑approved band).

Your four priority automations — **order→ERP fulfillment sync**, **repricing & Buy Box**, **listing creation & optimization**, **inventory sync & health** — map onto these phases (`03`, `04`).
