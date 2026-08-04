"""
User-isolation tests — the success metric for the multi-user work.

These prove, at the application layer, that user A cannot see, modify, or delete
user B's data, and that unauthenticated requests are rejected once auth is on.
They run with JWT verification enabled (the `multiuser` fixture).
"""


def _hdr(make_token, uid):
    return {"Authorization": f"Bearer {make_token(uid)}"}


# ── Authentication gate ───────────────────────────────────────────────────────

def test_no_token_is_unauthorized(multiuser):
    client, _ = multiuser
    # init-data is intentionally public — it powers the logged-out research
    # view — but must not leak any user-scoped data to an anonymous caller.
    r = client.get("/api/init-data")
    assert r.status_code == 200
    body = r.get_json()
    assert body["holdings"] == []
    assert body["portfolios"] == []
    assert client.get("/api/holdings").status_code == 401


def test_garbage_token_is_unauthorized(multiuser):
    client, _ = multiuser
    r = client.get("/api/holdings", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 401


def test_token_signed_with_wrong_secret_rejected(multiuser):
    client, make_token = multiuser
    bad = make_token("alice", secret="attacker-secret")
    r = client.get("/api/holdings", headers={"Authorization": f"Bearer {bad}"})
    assert r.status_code == 401


# ── ES256 (the algorithm this project actually uses in production) ─────────────

def test_es256_token_accepted(es256):
    client, sign = es256
    r = client.get("/api/holdings", headers={"Authorization": f"Bearer {sign('alice')}"})
    assert r.status_code == 200


def test_es256_token_signed_with_wrong_key_rejected(es256):
    client, sign = es256
    # A token signed by a different EC key must fail verification against the
    # injected public key.
    from cryptography.hazmat.primitives.asymmetric import ec
    import jwt as _jwt, time as _time
    other = ec.generate_private_key(ec.SECP256R1())
    now = int(_time.time())
    forged = _jwt.encode({"sub": "mallory", "aud": "authenticated", "iat": now, "exp": now + 3600},
                         other, algorithm="ES256")
    r = client.get("/api/holdings", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401


# ── Read isolation ────────────────────────────────────────────────────────────

def test_users_do_not_see_each_others_portfolios(multiuser):
    client, make_token = multiuser
    # Alice creates a portfolio and a holding
    client.post("/api/portfolios", json={"name": "Alice Fund", "category": "Stocks"}, headers=_hdr(make_token, "alice"))
    client.post("/api/ingest", json={
        "type": "BUY", "ticker": "AAPL", "companyName": "Apple",
        "portfolio": "Alice Fund", "shares": 5, "avgCost": 150,
    }, headers=_hdr(make_token, "alice"))

    # Bob sees nothing of Alice's
    bob_ports = client.get("/api/portfolios", headers=_hdr(make_token, "bob")).get_json()
    assert all(p["name"] != "Alice Fund" for p in bob_ports)
    bob_holdings = client.get("/api/holdings", headers=_hdr(make_token, "bob")).get_json()
    assert all(h["ticker"] != "AAPL" for h in bob_holdings)

    # Alice still sees her own
    alice_holdings = client.get("/api/holdings", headers=_hdr(make_token, "alice")).get_json()
    assert any(h["ticker"] == "AAPL" for h in alice_holdings)


def test_categories_are_per_user(multiuser):
    client, make_token = multiuser
    # First load seeds each user's own default categories
    client.get("/api/init-data", headers=_hdr(make_token, "alice"))
    client.get("/api/init-data", headers=_hdr(make_token, "bob"))
    client.post("/api/categories", json={"name": "Alice Only"}, headers=_hdr(make_token, "alice"))

    bob_cats = [c["name"] for c in client.get("/api/categories", headers=_hdr(make_token, "bob")).get_json()]
    assert "Alice Only" not in bob_cats
    assert "Stocks" in bob_cats  # seeded default


# ── Write / delete isolation ──────────────────────────────────────────────────

def test_bob_cannot_delete_alice_portfolio(multiuser):
    client, make_token = multiuser
    client.post("/api/portfolios", json={"name": "Alice Fund", "category": "Stocks"}, headers=_hdr(make_token, "alice"))

    # Bob attempts to delete a portfolio he doesn't own — must not succeed in removing it
    client.delete("/api/portfolio?name=Alice Fund", headers=_hdr(make_token, "bob"))

    alice_ports = [p["name"] for p in client.get("/api/portfolios", headers=_hdr(make_token, "alice")).get_json()]
    assert "Alice Fund" in alice_ports  # still there


def test_bob_cannot_adjust_alice_asset_via_forged_portfolio_id(multiuser):
    client, make_token = multiuser
    # Alice creates a portfolio + holding
    client.post("/api/portfolios", json={"name": "Alice Fund", "category": "Stocks"}, headers=_hdr(make_token, "alice"))
    client.post("/api/ingest", json={
        "type": "BUY", "ticker": "AAPL", "companyName": "Apple",
        "portfolio": "Alice Fund", "shares": 5, "avgCost": 150,
    }, headers=_hdr(make_token, "alice"))
    alice_ports = client.get("/api/portfolios", headers=_hdr(make_token, "alice")).get_json()
    alice_pid = next(p["id"] for p in alice_ports if p["name"] == "Alice Fund")

    # Bob forges Alice's portfolioId in an adjustment — the IDOR guard must reject it
    r = client.put("/api/asset-adjustment", json={
        "ticker": "AAPL", "portfolio": "whatever", "portfolioId": alice_pid,
        "shares": 999, "price": 1,
    }, headers=_hdr(make_token, "bob"))
    assert r.status_code == 400  # "Portfolio not found" for Bob (validation error)

    # Alice's holding is unchanged
    alice_holdings = client.get("/api/holdings", headers=_hdr(make_token, "alice")).get_json()
    aapl = next(h for h in alice_holdings if h["ticker"] == "AAPL")
    assert aapl["shares"] == 5


def test_bob_cannot_delete_alice_transaction(multiuser):
    client, make_token = multiuser
    client.post("/api/portfolios", json={"name": "Alice Fund", "category": "Stocks"}, headers=_hdr(make_token, "alice"))
    client.post("/api/ingest", json={
        "type": "BUY", "ticker": "AAPL", "companyName": "Apple",
        "portfolio": "Alice Fund", "shares": 5, "avgCost": 150,
    }, headers=_hdr(make_token, "alice"))
    tx = client.get("/api/transactions", headers=_hdr(make_token, "alice")).get_json()
    tx_id = tx[0]["id"]

    client.delete(f"/api/transaction?id={tx_id}", headers=_hdr(make_token, "bob"))

    # Alice's transaction survives
    still = client.get("/api/transactions", headers=_hdr(make_token, "alice")).get_json()
    assert any(t["id"] == tx_id for t in still)


# ── Profile ───────────────────────────────────────────────────────────────────

def test_profile_requires_auth(multiuser):
    client, _ = multiuser
    assert client.get("/api/profile").status_code == 401
    assert client.put("/api/profile", json={"display_name": "x"}).status_code == 401


def test_profile_created_with_defaults_on_first_get(multiuser):
    client, make_token = multiuser
    p = client.get("/api/profile", headers=_hdr(make_token, "alice")).get_json()
    assert p["display_name"] is None
    assert p["avatar_emoji"] == "🧞"
    assert p["preferred_currency"] == "USD"
    assert p["preferred_theme"] == "light"
    assert p["preferred_language"] == "en"
    assert "user_id" not in p  # internal id never leaves the API


def test_profiles_are_per_user(multiuser):
    client, make_token = multiuser
    r = client.put("/api/profile", json={
        "display_name": "Alice", "preferred_currency": "THB", "preferred_theme": "dark",
    }, headers=_hdr(make_token, "alice"))
    assert r.status_code == 200

    # Bob still sees pristine defaults, not Alice's values
    bob = client.get("/api/profile", headers=_hdr(make_token, "bob")).get_json()
    assert bob["display_name"] is None
    assert bob["preferred_currency"] == "USD"

    # Alice's values persisted
    alice = client.get("/api/profile", headers=_hdr(make_token, "alice")).get_json()
    assert alice["display_name"] == "Alice"
    assert alice["preferred_currency"] == "THB"
    assert alice["preferred_theme"] == "dark"


def test_profile_rejects_invalid_values(multiuser):
    client, make_token = multiuser
    hdr = _hdr(make_token, "alice")
    assert client.put("/api/profile", json={"preferred_currency": "EUR"}, headers=hdr).status_code == 400
    assert client.put("/api/profile", json={"preferred_theme": "neon"}, headers=hdr).status_code == 400
    assert client.put("/api/profile", json={"preferred_language": "jp"}, headers=hdr).status_code == 400
    assert client.put("/api/profile", json={"display_name": "x" * 61}, headers=hdr).status_code == 400
    assert client.put("/api/profile", json={}, headers=hdr).status_code == 400
    # unknown fields alone are rejected, not silently written
    assert client.put("/api/profile", json={"user_id": "evil"}, headers=hdr).status_code == 400


def test_profile_empty_display_name_clears_it(multiuser):
    client, make_token = multiuser
    hdr = _hdr(make_token, "alice")
    client.put("/api/profile", json={"display_name": "Alice"}, headers=hdr)
    r = client.put("/api/profile", json={"display_name": "  "}, headers=hdr)
    assert r.status_code == 200
    assert r.get_json()["display_name"] is None
