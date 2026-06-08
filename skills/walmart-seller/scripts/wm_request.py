#!/usr/bin/env python3
"""Make an authenticated Walmart Marketplace API request.

Handles the boring-but-critical parts so skills don't re-implement them:
  - token caching to a temp file (refresh at ~80% of the 15-min TTL)
  - the required headers (WM_SEC.ACCESS_TOKEN, WM_QOS.CORRELATION_ID, WM_SVC.NAME, Accept)
  - 429 backoff honoring x-next-replenish-time / X-Next-Replenishment-Time
Stdlib only (urllib). Imports get_token from the sibling get_token.py.

Usage:
  python3 wm_request.py GET  /v3/orders/released --query createdStartDate=2026-06-01
  python3 wm_request.py GET  /v3/items --query 'limit=20&nextCursor=*'
  python3 wm_request.py PUT  /v3/price --body @price.json
  python3 wm_request.py POST '/v3/feeds?feedType=MP_ITEM' --body @item_feed.json --content-type application/json

As a library:
  from wm_request import wm_request
  status, headers, body = wm_request("GET", "/v3/items", query={"limit": "20"})
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from get_token import get_token, host_for  # noqa: E402

_CACHE = os.path.join(
    os.environ.get("TMPDIR", "/tmp"),
    f"wm_token_{os.environ.get('WALMART_ENV', 'production')}.json",
)
_MAX_429_RETRIES = 5


def _cached_token() -> str:
    """Return a valid token, minting + caching a fresh one if needed."""
    try:
        with open(_CACHE) as f:
            c = json.load(f)
        if c.get("expires_at", 0) - time.time() > 60:  # >60s headroom
            return c["access_token"]
    except (OSError, ValueError, KeyError):
        pass
    token, expires_in = get_token()
    # refresh at ~80% TTL: store an effective expiry at 80% of the real one
    effective = time.time() + int(expires_in * 0.8)
    try:
        with open(_CACHE, "w") as f:
            json.dump({"access_token": token, "expires_at": effective}, f)
        os.chmod(_CACHE, 0o600)
    except OSError:
        pass
    return token


def wm_request(method, path, query=None, body=None, content_type="application/json"):
    """Return (status_code, response_headers_dict, response_text)."""
    env = os.environ.get("WALMART_ENV", "production")
    host = host_for(env)
    url = host + path
    if query:
        qs = query if isinstance(query, str) else urllib.parse.urlencode(query)
        url += ("&" if "?" in url else "?") + qs

    data = None
    if body is not None:
        data = body.encode() if isinstance(body, str) else json.dumps(body).encode()

    for attempt in range(_MAX_429_RETRIES + 1):
        headers = {
            "WM_SEC.ACCESS_TOKEN": _cached_token(),
            "WM_QOS.CORRELATION_ID": str(uuid.uuid4()),
            "WM_SVC.NAME": "Walmart Marketplace",
            "Accept": "application/json",
        }
        if env.lower() == "sandbox":
            headers["WM_SANDBOX"] = "v2"
        if data is not None:
            headers["Content-Type"] = content_type
        req = urllib.request.Request(url, data=data, method=method.upper(), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.status, dict(resp.headers), resp.read().decode(errors="replace")
        except urllib.error.HTTPError as e:
            hdrs = dict(e.headers or {})
            text = e.read().decode(errors="replace")
            if e.code == 429 and attempt < _MAX_429_RETRIES:
                wait = _replenish_wait(hdrs, attempt)
                print(f"# 429 throttled; backing off {wait:.1f}s "
                      f"(attempt {attempt + 1}/{_MAX_429_RETRIES})", file=sys.stderr)
                time.sleep(wait)
                continue
            if e.code == 401 and attempt == 0:
                # token may be stale despite cache headroom — drop cache and retry once
                try:
                    os.remove(_CACHE)
                except OSError:
                    pass
                continue
            return e.code, hdrs, text
        except urllib.error.URLError as e:
            if attempt < _MAX_429_RETRIES:
                time.sleep(2 ** attempt)
                continue
            sys.exit(f"ERROR: could not reach {host}: {e.reason}")
    return 429, {}, "rate limited: retries exhausted"


def _replenish_wait(headers, attempt):
    """Seconds to wait based on Walmart's replenish header (casing varies), with backoff floor."""
    lower = {k.lower(): v for k, v in headers.items()}
    raw = lower.get("x-next-replenish-time") or lower.get("x-next-replenishment-time")
    if raw:
        try:
            # value may be ms-since-epoch or seconds-until; handle both heuristically
            v = float(raw)
            if v > 1e12:  # epoch ms
                return max(1.0, v / 1000.0 - time.time())
            if v > 1e9:   # epoch s
                return max(1.0, v - time.time())
            return max(1.0, v)  # seconds-until
        except ValueError:
            pass
    return min(60.0, 2 ** attempt + 1)  # exponential fallback


def main():
    ap = argparse.ArgumentParser(description="Authenticated Walmart Marketplace request.")
    ap.add_argument("method", help="GET|POST|PUT|DELETE")
    ap.add_argument("path", help="e.g. /v3/items  (may include ?query=...)")
    ap.add_argument("--query", help="extra querystring, e.g. 'limit=20&nextCursor=*'")
    ap.add_argument("--body", help="request body as a string, or @file to read from a file")
    ap.add_argument("--content-type", default="application/json")
    args = ap.parse_args()

    body = args.body
    if body and body.startswith("@"):
        with open(body[1:]) as f:
            body = f.read()

    status, headers, text = wm_request(
        args.method, args.path, query=args.query, body=body, content_type=args.content_type
    )
    print(f"# HTTP {status}", file=sys.stderr)
    tc = {k.lower(): v for k, v in headers.items()}.get("x-current-token-count")
    if tc is not None:
        print(f"# x-current-token-count: {tc}", file=sys.stderr)
    print(text)
    sys.exit(0 if 200 <= status < 300 else 1)


if __name__ == "__main__":
    main()
