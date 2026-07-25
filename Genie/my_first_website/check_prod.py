#!/usr/bin/env python3
"""Smoke-test the live production Genie Investment app (with login).

Logs in as a dedicated smoke-test user and exercises the key API endpoints
end-to-end, including that unauthenticated requests are properly rejected.

Credentials come from my_first_website/.env (gitignored):
    CHECK_PROD_EMAIL=<smoke-test user email>
    CHECK_PROD_PASSWORD=<smoke-test user password>

Create the user once in Supabase Dashboard -> Authentication -> Users
(signup is invite-only). A fresh user with no holdings is fine — every check
validates status + response shape, not row counts.

Usage:  python3 check_prod.py
Exit code 0 = all checks passed.
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = "https://genieports.com"
SUPABASE_URL = "https://jkndlurskolcmifmsctm.supabase.co"
# Public anon key — same value that ships in auth.js; safe to commit.
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImprbmRsdXJza29sY21pZm1zY3RtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEyNzEyNjUsImV4cCI6MjA5Njg0NzI2NX0."
    "lfgMZNRAIFpy4Bn0LEOOO8O1BWUGu1hwEtJL2FDg8Ik"
)

results = []


def load_env():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v.strip().strip('"').strip("'"))


def http(url, headers=None, body=None):
    """Returns (status_code, parsed_json_or_None)."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {})
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read().decode() or "null")
        except Exception:
            payload = None
        return e.code, payload
    except Exception as e:
        return 0, {"error": str(e)}


def check(name, ok, detail=""):
    ok = bool(ok)
    results.append(ok)
    print(f"{'✅ PASS' if ok else '❌ FAIL'}  {name}" + (f" — {detail}" if detail else ""))


def login(email, password):
    status, data = http(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": SUPABASE_ANON_KEY},
        body={"email": email, "password": password},
    )
    if status == 200 and data and data.get("access_token"):
        return data["access_token"]
    print(f"❌ FAIL  Login as {email} — HTTP {status}: {data}")
    results.append(False)
    return None


def main():
    load_env()
    email = os.environ.get("CHECK_PROD_EMAIL")
    password = os.environ.get("CHECK_PROD_PASSWORD")
    if not email or not password:
        print("Missing CHECK_PROD_EMAIL / CHECK_PROD_PASSWORD in .env — see header of this script.")
        sys.exit(2)

    # 1. Auth config says login is enforced
    status, data = http(f"{BASE}/api/auth-config")
    check("auth-config reachable", status == 200 and (data or {}).get("authRequired") is True,
          f"HTTP {status}, authRequired={(data or {}).get('authRequired')}")

    # 2. Unauthenticated request is rejected (security check)
    status, _ = http(f"{BASE}/api/init-data")
    check("unauthenticated /api/init-data rejected", status == 401, f"HTTP {status}")

    # 3. Login with the smoke-test user
    token = login(email, password)
    if not token:
        sys.exit(1)
    check("login (Supabase password grant)", True, email)
    auth = {"Authorization": f"Bearer {token}"}

    # 4. init-data returns the expected shape
    status, data = http(f"{BASE}/api/init-data", headers=auth)
    ok = status == 200 and isinstance(data, dict) and \
        isinstance(data.get("holdings"), list) and isinstance(data.get("portfolios"), list)
    check("/api/init-data", ok,
          f"HTTP {status}, holdings={len(data.get('holdings', []))}, portfolios={len(data.get('portfolios', []))}"
          if ok else f"HTTP {status}")

    # 5. holdings query runs (validates schema incl. manualPrice column)
    status, data = http(f"{BASE}/api/holdings", headers=auth)
    ok = status == 200 and isinstance(data, list)
    shape = "empty (new user ok)" if ok and not data else \
        ("manualPrice present" if ok and "manualPrice" in data[0] else "manualPrice MISSING")
    check("/api/holdings", ok and (not data or "manualPrice" in data[0]), f"HTTP {status}, {shape}")

    # 6. Thai fund NAV lookup (SEC API path)
    status, data = http(f"{BASE}/api/thai-fund?code=ABFTH", headers=auth)
    ok = status == 200 and isinstance(data, dict) and data.get("nav") is not None
    check("/api/thai-fund?code=ABFTH", ok,
          f"HTTP {status}, nav={(data or {}).get('nav')}")

    # 7. Live stock price proxy (Yahoo path, also used for FX rates)
    status, data = http(f"{BASE}/api/stock?ticker=EURUSD=X", headers=auth)
    ok = status == 200 and isinstance(data, dict) and data.get("price")
    check("/api/stock?ticker=EURUSD=X", ok, f"HTTP {status}, price={(data or {}).get('price')}")

    print("-" * 60)
    passed, total = sum(results), len(results)
    print(f"{passed}/{total} checks passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
