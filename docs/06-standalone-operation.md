# 06 — Standalone Operation & Data Flow

The agent is the **standalone system of record** for the Walmart store. It owns every write — listings, price, inventory, orders (acknowledge/ship/cancel/refund), returns, WFS — directly through the Walmart Marketplace API with the seller's own first‑party keys. There is no other system in the loop by default.

## Data‑flow model

```
                 ┌──────────────── Walmart Marketplace (the live store) ─────────────────┐
                 │  Push Notifications (webhooks)         REST API (reads + ALL writes)    │
                 │  PO created, returns, OOS, Buy Box …   items/inventory/price/orders/... │
                 └───────────▲───────────────────────────────────▲───────────────────────┘
                             │ events                             │ reads + writes (own keys)
            ┌────────────────┴─────────────────────────────────────┴────────────────┐
            │  The agent (sole owner)                                                 │
            │  • webhook receiver + dedup        • listings / price / inventory writes │
            │  • event ledger + reconciliation   • order fulfillment + returns         │
            │  • decision + audit store          • guarded by the safety invariants    │
            └─────────────────────────────────────────────────────────────────────────┘
                             ▲                                   ▲
                    inventory truth                       labels + tracking
              (your warehouse / 3PL stock)        (Walmart carrier/label APIs or a 3PL)
```

## What a standalone agent must supply itself

The Walmart API is the **data plane** — it does not know your real stock and does not produce shipping labels. A standalone agent therefore needs two real‑world inputs:

1. **A source of inventory truth.** Walmart stores whatever quantity you push (`PUT /v3/inventory` / inventory feed); it has no idea what's actually on your shelves. Maintain one authoritative stock number (your warehouse system, a 3PL feed, or a spreadsheet/DB the agent reads) and sync it to Walmart. **One source of truth, one writer.**
2. **A way to fulfill.** For seller‑fulfilled orders the agent must produce a shipping label + tracking number to ship by the Expected Ship Date. Options: Walmart's carrier/label APIs, a 3PL that returns tracking, or **WFS** (let Walmart fulfill — see `../skills/walmart-wfs/SKILL.md`, which removes the label/inventory burden entirely).

## Ownership (single source of truth)

| Domain | Owner |
|---|---|
| Listings / catalog content | the agent |
| Price / promotions / Buy Box | the agent (within the hard guardrails) |
| Inventory (available‑to‑sell) | the agent (synced from your stock source) |
| Order state (ack / ship / cancel / refund) | the agent |
| Returns | the agent (WFS returns are Walmart‑driven, view‑only) |
| Walmart events / analytics / reconciliation / audit | the agent |

**If you ever add another tool that also writes to Walmart** (a second app, a manual operator, a channel manager), partition writes **per field per system** so the two never write the same field — otherwise you get oversell, double‑fulfillment, or price‑flapping. With a single standalone agent this is a non‑issue: it is the only writer.

## Guardrails still apply

Being standalone does not relax safety. Every write still passes the account‑safety invariants (per‑SKU min/max, never below cost/MAP, change caps, the too‑high/too‑low suppression rules, content rules, kill‑switch, rate‑limit backoff, and the phantom‑success "write → wait → read‑back" check). See `05-guardrails-and-policy.md` and `../skills/walmart-seller/references/guardrails.md`.
