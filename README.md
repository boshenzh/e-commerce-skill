# e-commerce-skill

A collection of **OpenClaw skills** for running marketplace seller stores. v0.1 is a **Walmart Marketplace (US)** suite, built on the bundled research library in [`docs/`](docs/README.md). It is a **standalone Walmart seller agent** that owns the whole Walmart store: it is the **system of record for all Walmart writes** — listings, price, inventory, orders (acknowledge / ship / cancel / refund), returns, and WFS — adding a Walmart‑native intelligence + guarded‑write layer on top.

## Design: hub‑and‑spoke

One operational **hub** owns the shared machinery so every other skill inherits it and nothing re‑derives auth or safety:

- **`walmart-seller`** (hub) — access/auth (your own first‑party API keys), a condensed API map, the **account‑safety guardrails**, and runnable Python helpers (`get_token`, `wm_request`, `guardrail_check`).

Around it, focused **spokes** — one per job‑to‑be‑done:

| Skill | Use it to… | Type |
|---|---|---|
| `walmart-onboarding` | apply to & get approved on Walmart Marketplace, then set up API keys | advisory |
| `walmart-listings` | create & optimize product listings (the `MP_ITEM` feed flow) | operational |
| `walmart-seo` | rank in Walmart search — title/attribute/Listing‑Quality tactics | advisory + API |
| `walmart-wfs` | set up & run Walmart Fulfillment Services (inbound, inventory health) | operational |
| `walmart-advertising` | plan Walmart Connect ads (Sponsored Products/Brands/Display) + get API access | advisory |
| `walmart-buybox-pricing` | win the Buy Box & reprice safely (native Repricer + guardrails) | operational |
| `walmart-pro-seller` | qualify for the Pro Seller Badge tiers | advisory |
| `walmart-customer-targeting` | gain visibility to Walmart+ / high‑value customers | advisory |
| `walmart-fulfillment-ops` | run seller‑fulfilled order ops within SLA (ack/ship/track/returns) | operational |
| `walmart-product-research` | find winning products (爆款) via demand signals | operational |

**Start at `walmart-seller`** — it routes you to the right spoke and holds the credentials + guardrails everything else depends on.

Because the agent owns inventory and fulfillment end‑to‑end, a standalone deployment needs two things of its own: (a) a real source of inventory truth — your own warehouse/3PL stock — to push to Walmart, and (b) a way to produce shipping labels + tracking (Walmart's carrier/label APIs or a 3PL).

## Install (OpenClaw)

The collection is self‑contained (skills + `docs/` + scripts, no external deps beyond `python3`). OpenClaw discovers `SKILL.md` files under the workspace skills directory (workspace > managed > bundled).

**On another server, via GitHub (recommended):**

```bash
# on the target server, in the OpenClaw workspace
git clone https://github.com/boshenzh/e-commerce-skill.git
ln -s "$PWD/e-commerce-skill/skills"/* <openclaw-workspace>/skills/   # or cp -R
# update later with:  git -C e-commerce-skill pull
```

If your OpenClaw build installs skills from a Git source (tracked in `skills-lock.json`, as in the `shen-ai` workspace), point it at `boshenzh/e-commerce-skill` so the lock file records the source + hash for reproducible installs.

**Local copy (same machine):**

```bash
cp -R skills/* <openclaw-workspace>/skills/
```

Then set credentials (your own first‑party Walmart keys — see `walmart-onboarding` / `walmart-seller`) as **environment variables on the server** (never commit them):

```bash
export WALMART_CLIENT_ID="…"
export WALMART_CLIENT_SECRET="…"
export WALMART_ENV="production"   # or: sandbox
```

Smoke‑test auth: `python3 skills/walmart-seller/scripts/get_token.py` (or the full read‑only check: `skills/walmart-seller/scripts/sandbox_smoke.sh`).

## Conventions

- Format: `SKILL.md` + YAML frontmatter (`name` = folder, `description` with inline triggers, `version`), `references/` for deep docs, `scripts/` (Python stdlib — no pip installs).
- Tone: imperative, second‑person, with explicit **Gotchas**.
- Safety‑first: any price/inventory/cancel write must pass the hub's guardrails (`walmart-seller/references/guardrails.md` + `scripts/guardrail_check.py`).
- Single source of truth — the agent is the system of record for Walmart writes. (Optional: if you ever add another tool that also writes to Walmart, partition fields per system to avoid oversell / double‑write / price‑flapping.)

## Relationship to `docs/`

The bundled [`docs/`](docs/) is the **research library** (full API reference, access analysis, policy detail, sources). These skills are the **actionable layer** distilled from it. When a skill needs deep detail it links back to the hub, which bridges to `docs/`. If Walmart changes something, update `docs/` first, then the affected skill.

## Roadmap

v0.1 = Walmart. The structure is marketplace‑agnostic; future siblings (`amazon-*`, `tiktok-shop-*`) can drop in alongside `walmart-*`.
