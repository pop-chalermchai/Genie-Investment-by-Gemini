"""
Baseline characterization tests for the Genie Investment API.

Purpose: lock in the CURRENT behavior of the API before the multi-user / auth
refactor (see ARCHITECTURE_MULTIUSER.md). If a change during that work alters a
response shape or breaks a flow, these tests should turn red.

NOTE: These assert single-user behavior. After auth lands, endpoints will require
a token and become user-scoped — update these tests as part of that work.
"""


# ── Read endpoints: shape + status ────────────────────────────────────────────

def test_init_data_shape(client):
    r = client.get("/api/init-data")
    assert r.status_code == 200
    data = r.get_json()
    assert set(["holdings", "reports", "portfolios"]).issubset(data.keys())


def test_portfolios_list(client):
    r = client.get("/api/portfolios")
    assert r.status_code == 200
    ports = r.get_json()
    assert any(p["name"] == "US Stock" for p in ports)


def test_holdings_aggregates_shares(client):
    r = client.get("/api/holdings")
    assert r.status_code == 200
    holdings = r.get_json()
    nvda = next(h for h in holdings if h["ticker"] == "NVDA")
    assert nvda["shares"] == 10
    assert nvda["avgCost"] == 100.0


def test_transactions_list(client):
    r = client.get("/api/transactions")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_categories_list(client):
    r = client.get("/api/categories")
    assert r.status_code == 200
    assert any(c["name"] == "Stocks" for c in r.get_json())


# ── Write flow: create → ingest → reflect → delete ────────────────────────────

def test_add_portfolio_then_ingest_updates_holdings(client):
    # create a new sub-portfolio
    r = client.post("/api/portfolios", json={"name": "Crypto Bag", "category": "Stocks"})
    assert r.status_code == 200 and r.get_json().get("success")

    # ingest a buy into it
    r = client.post("/api/ingest", json={
        "type": "BUY", "ticker": "BTC", "companyName": "Bitcoin",
        "portfolio": "Crypto Bag", "shares": 2, "avgCost": 50000, "currency": "USD",
    })
    assert r.status_code == 200 and r.get_json().get("success")

    # holdings should now include BTC with 2 shares
    holdings = client.get("/api/holdings").get_json()
    btc = next(h for h in holdings if h["ticker"] == "BTC")
    assert btc["shares"] == 2
    assert btc["avgCost"] == 50000


def test_duplicate_portfolio_name_rejected(client):
    client.post("/api/portfolios", json={"name": "Dup", "category": "Stocks"})
    r = client.post("/api/portfolios", json={"name": "Dup", "category": "Stocks"})
    assert r.status_code == 400
    assert "already exists" in r.get_json()["error"]


def test_delete_portfolio_removes_holdings(client):
    client.post("/api/portfolios", json={"name": "Temp", "category": "Stocks"})
    client.post("/api/ingest", json={
        "type": "BUY", "ticker": "TSLA", "companyName": "Tesla",
        "portfolio": "Temp", "shares": 1, "avgCost": 200, "currency": "USD",
    })
    r = client.delete("/api/portfolio?name=Temp")
    assert r.status_code == 200 and r.get_json().get("success")
    holdings = client.get("/api/holdings").get_json()
    assert not any(h["ticker"] == "TSLA" for h in holdings)


# ── Validation guards ─────────────────────────────────────────────────────────

def test_ingest_missing_fields_rejected(client):
    r = client.post("/api/ingest", json={"ticker": "X"})
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_ingest_into_missing_portfolio_rejected(client):
    r = client.post("/api/ingest", json={
        "type": "BUY", "ticker": "AAA", "companyName": "AAA Inc",
        "portfolio": "Nope", "shares": 1, "avgCost": 1,
    })
    assert r.status_code == 400
    assert "does not exist" in r.get_json()["error"]


def test_stock_endpoint_requires_ticker(client):
    r = client.get("/api/stock")
    assert r.status_code == 400


def test_thai_fund_sync_without_key_returns_503(client):
    # SEC_FACTSHEET_KEY is unset in the test env → guard should return 503
    r = client.post("/api/thai-fund/sync")
    assert r.status_code == 503


# ── Security headers & rate limiting ─────────────────────────────────────────

def test_security_headers_on_api_responses(client):
    r = client.get("/api/holdings")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_rate_limit_kicks_in_on_proxy_endpoint(client):
    # /api/thai-fund is @rate_limited (RATE_LIMIT_MAX=30/min). Hammer it and
    # expect 429s once the budget is spent. (Uses a fund code that doesn't
    # exist — a 404 still consumes budget, no external call is made because
    # the DB lookup fails first.)
    statuses = [client.get("/api/thai-fund?code=NOPE").status_code for _ in range(35)]
    assert 429 in statuses
    assert statuses[0] != 429          # first requests pass
    assert statuses[-1] == 429         # budget exhausted at the end
