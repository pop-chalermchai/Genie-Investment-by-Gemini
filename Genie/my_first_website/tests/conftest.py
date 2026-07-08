"""
Shared pytest fixtures for the Genie Investment API.

These tests run the Flask app against a FRESH, TEMPORARY SQLite database so they
never touch portfolio.db or the production Supabase data. The app is imported by
file path (api/index.py is not an importable package name) and its module-level
globals (DB_PATH / DATABASE_URL / SUPABASE_JWT_SECRET) are overridden per test.

Auth in tests:
  - Requests with no Authorization header run as the local dev user
    (DEV_USER_ID = 'local-dev-user'), matching local single-user mode.
  - `make_token(user_id)` mints a Supabase-style HS256 JWT signed with the test
    secret, so isolation tests can act as distinct users.
"""
import os
import sqlite3
import importlib.util
import tempfile
import time

import jwt
import pytest

API_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api", "index.py")
TEST_JWT_SECRET = "test-secret-for-local-suite-only"
DEV_USER_ID = "local-dev-user"


def _build_schema(db_path):
    """Create the 6 tables the app expects (with user_id), plus seed data for the dev user."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executescript(
        """
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            user_id TEXT
        );
        CREATE TABLE portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_id INTEGER,
            parent_id INTEGER,
            sort_order INTEGER,
            user_id TEXT
        );
        CREATE TABLE assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            company_name TEXT,
            sector TEXT,
            domain TEXT,
            portfolio_id INTEGER,
            manual_price REAL
        );
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER,
            type TEXT NOT NULL,
            shares REAL NOT NULL,
            price REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE research_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_key TEXT NOT NULL,
            ticker TEXT, company_name TEXT, subtitle TEXT,
            prepared_by TEXT, audited_by TEXT, rating TEXT,
            is_positive BOOLEAN, price_target REAL, analysis_price REAL, sector TEXT,
            en_overview TEXT, th_overview TEXT, en_dcf TEXT, th_dcf TEXT,
            user_id TEXT, research_date DATE
        );
        CREATE TABLE profiles (
            user_id            TEXT PRIMARY KEY,
            display_name       TEXT,
            avatar_emoji       TEXT NOT NULL DEFAULT '🧞',
            preferred_currency TEXT NOT NULL DEFAULT 'USD',
            preferred_theme    TEXT NOT NULL DEFAULT 'light',
            preferred_language TEXT NOT NULL DEFAULT 'en',
            updated_at         DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE thai_funds (
            proj_id TEXT PRIMARY KEY, proj_abbr_name TEXT, proj_name_th TEXT,
            proj_name_en TEXT, fund_status TEXT, amc_name_en TEXT,
            unique_id TEXT, last_synced DATETIME
        );

        INSERT INTO categories (name, description, user_id) VALUES ('Stocks', 'general', 'local-dev-user');
        INSERT INTO portfolios (id, name, category_id, parent_id, user_id) VALUES (1, 'US Stock', 1, NULL, 'local-dev-user');
        INSERT INTO assets (id, ticker, company_name, sector, portfolio_id)
            VALUES (1, 'NVDA', 'NVIDIA Corp', 'Technology', 1);
        INSERT INTO transactions (asset_id, type, shares, price, currency)
            VALUES (1, 'BUY', 10, 100.0, 'USD');
        """
    )
    conn.commit()
    conn.close()


def _load_app(tmp_db, jwt_secret=None):
    spec = importlib.util.spec_from_file_location("genie_api", API_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.DATABASE_URL = None      # force local SQLite, never Postgres
    mod.DB_PATH = tmp_db
    mod.SUPABASE_JWT_SECRET = jwt_secret
    mod.SUPABASE_JWKS_URL = None  # no network in tests unless a test opts in
    mod._jwks_client = None
    mod.app.config["TESTING"] = True
    return mod


def make_token(user_id, secret=TEST_JWT_SECRET):
    """Mint a Supabase-style access token for `user_id`."""
    now = int(time.time())
    payload = {"sub": user_id, "aud": "authenticated", "role": "authenticated",
               "iat": now, "exp": now + 3600}
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture()
def client():
    """Test client in local single-user mode (no JWT secret; no token required)."""
    fd, tmp_db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    _build_schema(tmp_db)
    mod = _load_app(tmp_db, jwt_secret=None)
    with mod.app.test_client() as c:
        yield c
    os.remove(tmp_db)


@pytest.fixture()
def multiuser():
    """
    Test client with JWT verification enabled (multi-user mode).
    Returns (client, make_token). No portfolios are pre-seeded to any real user,
    so isolation tests build their own data via the API.
    """
    fd, tmp_db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    _build_schema(tmp_db)
    mod = _load_app(tmp_db, jwt_secret=TEST_JWT_SECRET)
    with mod.app.test_client() as c:
        yield c, make_token
    os.remove(tmp_db)


def auth_headers(user_id):
    return {"Authorization": f"Bearer {make_token(user_id)}"}


@pytest.fixture()
def es256():
    """
    Test client that verifies ES256 tokens via JWKS — the algorithm this Supabase
    project actually uses in production. A local EC keypair stands in for Supabase's
    signing key, injected through a stub JWKS client so no network is touched.
    Returns (client, sign) where sign(user_id) -> an ES256 access token.
    """
    from cryptography.hazmat.primitives.asymmetric import ec

    fd, tmp_db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    _build_schema(tmp_db)
    mod = _load_app(tmp_db, jwt_secret=None)

    priv = ec.generate_private_key(ec.SECP256R1())
    pub = priv.public_key()

    class _StubKey:
        key = pub

    class _StubJWKS:
        def get_signing_key_from_jwt(self, token):
            return _StubKey()

    # Enable the asymmetric path and force auth on.
    mod.SUPABASE_JWKS_URL = "https://stub/jwks"
    mod._jwks_client = _StubJWKS()
    mod.SUPABASE_JWT_SECRET = "enable-auth"  # makes _auth_enforced() true

    def sign(user_id):
        now = int(time.time())
        return jwt.encode(
            {"sub": user_id, "aud": "authenticated", "role": "authenticated",
             "iat": now, "exp": now + 3600},
            priv, algorithm="ES256",
        )

    with mod.app.test_client() as c:
        yield c, sign
    os.remove(tmp_db)
