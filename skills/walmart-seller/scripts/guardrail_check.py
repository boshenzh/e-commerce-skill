#!/usr/bin/env python3
"""Validate a proposed Walmart price against the account-safety guardrails.

Run this BEFORE any price write (PUT /v3/price or a PRICE_AND_PROMOTION feed).
Encodes the hard invariants from references/guardrails.md. Stdlib only.

Rules (ALL must hold to ALLOW):
  R1 floor    proposed >= max(cost + min_margin, MAP)        # never sell at a loss / below MAP
  R2 min      proposed >= min                                 # respect per-SKU floor
  R3 max      proposed <= max                                 # respect per-SKU ceiling
  R4 ceiling  proposed <= reference (if given)                # avoid too-HIGH suppression
  R5 change   |proposed - last| / last <= max_change_pct%     # don't thrash (if last given)
Also: R2/R3 require BOTH min and max to be present (Walmart's Repricer mandates them).

Exit codes: 0 = ALLOW, 2 = DENY, 1 = bad input.

Usage:
  python3 guardrail_check.py --sku ABC --proposed 19.99 \
      --cost 12.00 --map 17.99 --min 17.99 --max 29.99 \
      --last 21.99 --max-change-pct 15 --reference 24.99
  python3 guardrail_check.py --json '{"sku":"ABC","proposed":19.99,"cost":12,"map":17.99,
      "min":17.99,"max":29.99,"last":21.99,"max_change_pct":15,"reference":24.99}'

As a library:
  from guardrail_check import check
  verdict = check(proposed=19.99, cost=12, map=17.99, min=17.99, max=29.99, ...)
  verdict["allow"]  # bool ; verdict["reasons"]  # list[str]
"""
import argparse
import json
import sys


def check(proposed, cost=None, map_price=None, min_price=None, max_price=None, last=None,
          min_margin=0.0, max_change_pct=None, reference=None, sku=None):
    reasons = []

    if proposed is None or proposed <= 0:
        return {"sku": sku, "allow": False, "reasons": ["proposed price must be > 0"]}

    # R2/R3 — per-SKU bounds are mandatory
    if min_price is None or max_price is None:
        reasons.append("DENY R2/R3: per-SKU min AND max are required before any price write")
    else:
        if proposed < min_price:
            reasons.append(f"DENY R2: proposed {proposed} < min {min_price}")
        if proposed > max_price:
            reasons.append(f"DENY R3: proposed {proposed} > max {max_price}")
        if min_price > max_price:
            reasons.append(f"DENY config: min {min_price} > max {max_price}")

    # R1 — hard floor = max(cost + margin, MAP)
    floor_parts = []
    if cost is not None:
        floor_parts.append(cost + (min_margin or 0.0))
    if map_price is not None:
        floor_parts.append(map_price)
    if floor_parts:
        floor = max(floor_parts)
        if proposed < floor:
            reasons.append(
                f"DENY R1: proposed {proposed} below floor {round(floor, 4)} "
                f"(max of cost+margin / MAP) — risks loss AND 'Pricing Error' suppression"
            )

    # R4 — reference price is the ceiling (too-HIGH suppression)
    if reference is not None and proposed > reference:
        reasons.append(
            f"DENY R4: proposed {proposed} > reference {reference} "
            f"— risks 'Reasonable Price Not Satisfied' unpublish / Buy Box loss"
        )

    # R5 — per-cycle change cap
    if last is not None and last > 0 and max_change_pct is not None:
        change = abs(proposed - last) / last * 100.0
        if change > max_change_pct:
            reasons.append(
                f"DENY R5: change {round(change, 2)}% > cap {max_change_pct}% "
                f"(last {last} -> {proposed}); needs human approval"
            )

    allow = len(reasons) == 0
    if allow:
        reasons.append("ALLOW: within [min,max], at/above floor, at/below reference, within change cap")
    return {"sku": sku, "proposed": proposed, "allow": allow, "reasons": reasons}


def main():
    ap = argparse.ArgumentParser(description="Validate a proposed price against guardrails.")
    ap.add_argument("--json", help="all inputs as a JSON object (overrides individual flags)")
    ap.add_argument("--sku")
    ap.add_argument("--proposed", type=float)
    ap.add_argument("--cost", type=float)
    ap.add_argument("--map", type=float)
    ap.add_argument("--min", type=float)
    ap.add_argument("--max", type=float)
    ap.add_argument("--last", type=float)
    ap.add_argument("--min-margin", type=float, default=0.0)
    ap.add_argument("--max-change-pct", type=float)
    ap.add_argument("--reference", type=float)
    args = ap.parse_args()

    if args.json:
        try:
            d = json.loads(args.json)
        except ValueError as e:
            sys.exit(f"ERROR: bad --json: {e}")
        verdict = check(
            proposed=d.get("proposed"), cost=d.get("cost"), map_price=d.get("map"),
            min_price=d.get("min"), max_price=d.get("max"), last=d.get("last"),
            min_margin=d.get("min_margin", 0.0), max_change_pct=d.get("max_change_pct"),
            reference=d.get("reference"), sku=d.get("sku"),
        )
    else:
        if args.proposed is None:
            sys.exit("ERROR: --proposed is required (or pass --json)")
        verdict = check(
            proposed=args.proposed, cost=args.cost, map_price=args.map, min_price=args.min,
            max_price=args.max, last=args.last, min_margin=args.min_margin,
            max_change_pct=args.max_change_pct, reference=args.reference, sku=args.sku,
        )

    print(json.dumps(verdict, indent=2))
    sys.exit(0 if verdict["allow"] else 2)


if __name__ == "__main__":
    main()
