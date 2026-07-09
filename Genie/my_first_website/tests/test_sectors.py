"""Sector master data: CRUD, per-user isolation, optional-field ingest, and
the auto-upsert that promotes a freehand-typed sector into the master list."""
from conftest import auth_headers

ALICE = "sector-alice"
BOB = "sector-bob"


def test_sectors_list_seeded_from_conftest(client):
    # conftest's `client` fixture is single-user local dev — no sectors table
    # rows are pre-seeded, so this just proves the endpoint doesn't error.
    r = client.get('/api/sectors')
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_add_and_delete_sector(client):
    r = client.post('/api/sectors', json={"name": "Healthcare"})
    assert r.status_code == 200

    names = [s['name'] for s in client.get('/api/sectors').get_json()]
    assert "Healthcare" in names

    sector_id = next(s['id'] for s in client.get('/api/sectors').get_json() if s['name'] == "Healthcare")
    r = client.delete(f'/api/sectors?id={sector_id}')
    assert r.status_code == 200
    names = [s['name'] for s in client.get('/api/sectors').get_json()]
    assert "Healthcare" not in names


def test_add_sector_case_insensitive_dedupe(client):
    assert client.post('/api/sectors', json={"name": "Energy"}).status_code == 200
    r = client.post('/api/sectors', json={"name": "energy"})
    assert r.status_code == 400


def test_add_sector_requires_name(client):
    r = client.post('/api/sectors', json={"name": "  "})
    assert r.status_code == 400


def test_ingest_without_sector_succeeds_and_stores_null(client):
    client.post('/api/portfolios', json={"name": "Parent", "category": "Stocks"})
    client.post('/api/portfolios', json={"name": "Sub", "category": "Stocks", "parentId": 1})
    r = client.post('/api/ingest', json={
        "type": "BUY", "ticker": "NOSEC", "companyName": "No Sector Co",
        "portfolio": "Sub", "shares": 1, "avgCost": 10, "currency": "USD", "sector": "",
    })
    assert r.status_code == 200, r.get_json()

    holdings = client.get('/api/holdings').get_json()
    row = next(h for h in holdings if h['ticker'] == 'NOSEC')
    assert row['sector'] is None


def test_ingest_with_new_sector_auto_adds_to_master_list(client):
    client.post('/api/portfolios', json={"name": "Parent", "category": "Stocks"})
    client.post('/api/portfolios', json={"name": "Sub", "category": "Stocks", "parentId": 1})
    client.post('/api/ingest', json={
        "type": "BUY", "ticker": "FREE", "companyName": "Freehand Sector Co",
        "portfolio": "Sub", "shares": 1, "avgCost": 10, "currency": "USD",
        "sector": "My Brand New Sector",
    })
    names = [s['name'] for s in client.get('/api/sectors').get_json()]
    assert "My Brand New Sector" in names


def test_sectors_are_isolated_per_user(multiuser):
    c, _ = multiuser
    c.post('/api/sectors', json={"name": "Alice Only"}, headers=auth_headers(ALICE))
    c.post('/api/sectors', json={"name": "Bob Only"}, headers=auth_headers(BOB))

    alice_names = [s['name'] for s in c.get('/api/sectors', headers=auth_headers(ALICE)).get_json()]
    bob_names = [s['name'] for s in c.get('/api/sectors', headers=auth_headers(BOB)).get_json()]
    assert "Alice Only" in alice_names and "Bob Only" not in alice_names
    assert "Bob Only" in bob_names and "Alice Only" not in bob_names


def test_bob_cannot_delete_alices_sector(multiuser):
    c, _ = multiuser
    c.post('/api/sectors', json={"name": "Alice Sector"}, headers=auth_headers(ALICE))
    sector_id = next(s['id'] for s in c.get('/api/sectors', headers=auth_headers(ALICE)).get_json())

    # Bob's delete targets Alice's id but is scoped by his own user_id — no-op, no error.
    r = c.delete(f'/api/sectors?id={sector_id}', headers=auth_headers(BOB))
    assert r.status_code == 200
    alice_names = [s['name'] for s in c.get('/api/sectors', headers=auth_headers(ALICE)).get_json()]
    assert "Alice Sector" in alice_names
