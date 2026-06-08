# 00 — Overview & Executive Summary

## Your setup

- **Role:** US‑based e‑commerce shop owner selling on **Walmart Marketplace** (third‑party seller).
- **System of record:** **your own AI agent** is the system of record for the Walmart store and owns all writes end‑to‑end — listings, price, inventory, orders (acknowledge / ship / cancel / refund), returns, and WFS.
- **Goal:** automate the operational workflow with a standalone AI agent that runs the Walmart shop — without risking the seller account.
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
            │   • reconciliation sweeps          │   │  WRITE tools (idempotent + │
            │   • decision + audit store         │   │   guardrailed, agent owns) │
            └────────────────┬───────────────────┘   └────────────────────────────┘
                             │ decides / acts
                             ▼
                    AI agent (any runtime)
                    system of record — owns all Walmart writes
```

The agent uses **your own first‑party API keys** and is the **system of record** for the Walmart store: it owns all writes — listings, price, inventory, orders, returns, WFS — through narrow, idempotent, guardrailed paths (or Walmart's own native Repricer).

## Executive summary of findings

1. **Access is easy for your own shop.** A single seller automating their own account just generates a personal Client ID/Secret in Seller Center and calls the Marketplace API with the OAuth2 `client_credentials` grant. **No partnership, contract, or "Connected App" approval is required.** (Details: `01`.)

2. **"Connected Apps" is a different thing** — it's the list of third‑party Solution‑Provider apps you've OAuth‑authorized to act on your behalf. Becoming a Connected App is only necessary if you want to *distribute* your agent to other sellers. (Details: `01`.)

3. **The Walmart Marketplace API is broad and capable** — full CRUD over Items/Catalog, Inventory, Price/Promotions, Orders, Returns, WFS fulfillment, plus Reports/Insights/Settlement and a native server‑side Repricer. Most bulk writes are **async feeds** (submit → poll → per‑item results). (Details: `02`.)

4. **Walmart has push webhooks** ("Notifications") — PO created, returns, inventory OOS, Buy Box change, offer published/unpublished, report ready, and more. This corrects the common belief that Walmart is poll‑only. Best design is a **webhook receiver + reconciliation‑sweep hybrid**. (Details: `02`, `04`.)

5. **There is no official Walmart MCP server**, and community ones target the *consumer shopping* side, not the seller API. One proprietary paid seller‑API MCP exists (Vinkius, **not** Walmart‑affiliated). Walmart **does** publish OpenAPI specs (per section). Practical path: **build a thin MCP/tool layer around your own keys.** (Details: `01`, `04`.)

6. **The account is protected by automated enforcement.** Pricing that's too high *or too low* gets **auto‑suppressed/unpublished**; a **performance scorecard** (on‑time delivery, valid tracking, cancellation, etc.) governs account health; repeated violations escalate to suspension. Any autonomous agent must hard‑enforce guardrails. (Details: `05`.)

7. ⚠️ **Time‑sensitive:** legacy **Delegated Access** keys are being retired (no new keys after **2026‑07‑30**; all dead **2026‑10‑01**). Everything moves to OAuth 2.0 via the App Store. Your own first‑party keys are unaffected — but verify nothing critical still rides Delegated Access. (Details: `01`.)

## Headline corrections to common misconceptions

| Common belief | Reality |
|---|---|
| "Walmart is poll‑only; no webhooks." | ❌ Walmart has push **Notifications/webhooks** for orders, returns, OOS, Buy Box, etc. |
| "I must become a partner / Connected App to use the API." | ❌ For your own shop, just use your own keys. No approval. |
| "There's an official Walmart MCP server." | ❌ None official; community ones are consumer‑shopping, not seller API. |
| "Repricing means hammering the price API." | ❌ The price write limits are tight (100/hr single, 10/hr bulk). Prefer Walmart's **native Repricer** or webhook‑triggered selective updates. |

## What to build (summary; full plan in `04`)

A small **middleware** + **MCP/tool layer** in front of the Walmart Marketplace API, rolled out in phases:

- **Phase 0** — foundation: own keys, token cache, webhook receiver, event ledger, entity map, READ‑only tools.
- **Phase 1** — read‑only analytics & recommendations (writes exist only as `dry_run` diffs while you build confidence).
- **Phase 2** — enable guardrailed writes (the `write → wait → read‑back` pattern, per‑cycle change caps, etc.).
- **Phase 3** — full autonomy: the agent owns all writes for the store within its hard guardrails (e.g. repricing within a pre‑approved band).

Your four priority automations — **order fulfillment (acknowledge / ship / cancel / refund)**, **repricing & Buy Box**, **listing creation & optimization**, **inventory sync & health** — map onto these phases (`03`, `04`).

> **Inventory & fulfillment need a source of truth.** Because the agent owns inventory and fulfillment end‑to‑end, a standalone agent needs (a) a real source of inventory truth — your own warehouse/3PL stock — to push to Walmart, and (b) a way to produce shipping labels + tracking (Walmart's carrier/label APIs or a 3PL). WFS orders are fulfilled by Walmart, but seller‑fulfilled orders are yours to ship.

> **Single source of truth** — the agent is the system of record for Walmart writes. (If you ever add another tool that also writes to Walmart, partition fields per system to avoid oversell / double‑write / price‑flapping.) *(Optional.)*
