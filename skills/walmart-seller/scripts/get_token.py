#!/usr/bin/env python3
"""Mint a Walmart Marketplace OAuth2 access token (client_credentials).

Uses the SELLER's own first-party API keys — no Walmart approval needed.
Stdlib only (urllib); no pip install required.

Env:
  WALMART_CLIENT_ID      your Client ID      (Seller Center -> API Key Management)
  WALMART_CLIENT_SECRET  your Client Secret
  WALMART_ENV            "production" (default) | "sandbox"

Usage:
  python3 get_token.py                 # prints the full token JSON
  python3 get_token.py --quiet         # prints just the access_token
  python3 get_token.py --env sandbox   # override WALMART_ENV

As a library:
  from get_token import get_token
  token, expires_in = get_token()
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

HOSTS = {
    "production": "https://marketplace.walmartapis.com",
    "sandbox": "https://sandbox.walmartapis.com",
}


def host_for(env: str) -> str:
    env = (env or "production").lower()
    if env not in HOSTS:
        sys.exit(f"ERROR: WALMART_ENV must be 'production' or 'sandbox', got '{env}'")
    return HOSTS[env]


def get_token(env: str | None = None):
    """Return (access_token, expires_in_seconds). Raises SystemExit on misconfig."""
    client_id = os.environ.get("WALMART_CLIENT_ID")
    client_secret = os.environ.get("WALMART_CLIENT_SECRET")
    if not client_id or not client_secret:
        sys.exit(
            "ERROR: set WALMART_CLIENT_ID and WALMART_CLIENT_SECRET (your own "
            "first-party keys from Seller Center -> API Key Management)."
        )
    env = env or os.environ.get("WALMART_ENV", "production")
    host = host_for(env)

    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request(
        f"{host}/v3/token",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "WM_SVC.NAME": "Walmart Marketplace",
            "WM_QOS.CORRELATION_ID": str(uuid.uuid4()),
        },
    )
    sandbox = env.lower() == "sandbox"
    if sandbox:
        req.add_header("WM_SANDBOX", "v2")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:500]
        sys.exit(f"ERROR: token request failed ({e.code}). Check creds/env.\n{detail}")
    except urllib.error.URLError as e:
        sys.exit(f"ERROR: could not reach {host}: {e.reason}")

    token = data.get("access_token")
    if not token:
        sys.exit(f"ERROR: no access_token in response: {json.dumps(data)[:300]}")
    return token, int(data.get("expires_in", 900))


def main():
    ap = argparse.ArgumentParser(description="Mint a Walmart Marketplace access token.")
    ap.add_argument("--env", help="production|sandbox (overrides WALMART_ENV)")
    ap.add_argument("--quiet", action="store_true", help="print only the access_token")
    args = ap.parse_args()
    token, expires_in = get_token(args.env)
    if args.quiet:
        print(token)
    else:
        print(json.dumps({"access_token": token, "expires_in": expires_in}, indent=2))
        print(f"# token valid ~{expires_in}s ({expires_in // 60} min) — cache it; "
              "refresh at ~80% TTL", file=sys.stderr)


if __name__ == "__main__":
    main()
