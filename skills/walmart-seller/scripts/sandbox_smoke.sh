#!/usr/bin/env bash
# Read-only sandbox smoke test for the walmart-seller hub scripts.
# Verifies auth + a few GETs end-to-end against the Walmart sandbox.
# SAFE: makes no writes. Requires WALMART_CLIENT_ID / WALMART_CLIENT_SECRET set.
#
# Usage:
#   export WALMART_CLIENT_ID=... WALMART_CLIENT_SECRET=...
#   ./sandbox_smoke.sh
set -u
cd "$(dirname "$0")"
export WALMART_ENV="sandbox"

if [ -z "${WALMART_CLIENT_ID:-}" ] || [ -z "${WALMART_CLIENT_SECRET:-}" ]; then
  echo "FAIL: set WALMART_CLIENT_ID and WALMART_CLIENT_SECRET (sandbox keys) first." >&2
  exit 1
fi

pass=0; fail=0
check () { # name  expected_csv  method  path
  local name="$1" expected="$2" method="$3" path="$4"
  local out code
  out=$(python3 wm_request.py "$method" "$path" 2>&1)
  code=$(echo "$out" | sed -n 's/^# HTTP \([0-9]*\).*/\1/p' | head -1)
  if echo ",$expected," | grep -q ",$code,"; then
    echo "PASS  $name  -> HTTP $code"; pass=$((pass+1))
  else
    echo "FAIL  $name  -> HTTP ${code:-???} (expected one of: $expected)"; fail=$((fail+1))
    echo "$out" | grep -v '^#' | head -c 200 | sed 's/^/      /'; echo
  fi
}

echo "== minting sandbox token =="
if python3 get_token.py --env sandbox --quiet >/dev/null 2>&1; then
  echo "PASS  token mint"; pass=$((pass+1))
else
  echo "FAIL  token mint"; fail=$((fail+1)); python3 get_token.py --env sandbox 2>&1 | head -3
fi

echo "== read-only GETs =="
check "items"            "200"     GET "/v3/items?limit=1"
check "orders-released"  "200"     GET "/v3/orders/released?createdStartDate=2026-06-01"
check "inventory(404 ok)" "200,404" GET "/v3/inventory?sku=SAMPLE-SKU"
# NOTE: GET /v3/feeds intermittently returns 520 on Walmart's sandbox (their bug); not asserted.

echo "== summary: $pass passed, $fail failed =="
[ "$fail" -eq 0 ] || exit 2
