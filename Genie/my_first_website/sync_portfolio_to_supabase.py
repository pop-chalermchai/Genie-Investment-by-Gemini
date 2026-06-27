#!/usr/bin/env python3
"""
Sync local SQLite portfolio data to Supabase (push) or restore from Supabase (pull).

Usage:
  python3 sync_portfolio_to_supabase.py          # push local → Supabase
  python3 sync_portfolio_to_supabase.py --pull   # pull Supabase → local (restore)
"""

import sqlite3
import os
import sys
import ssl
import urllib.parse
import pg8000

SQLITE_PATH = os.path.join(os.path.dirname(__file__), "portfolio.db")
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")

TABLES = ["categories", "portfolios", "assets", "transactions"]


def get_db_url():
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    return line.split("DATABASE_URL=", 1)[1].strip()
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    print("❌ DATABASE_URL not found in .env or environment")
    sys.exit(1)


def connect_supabase(db_url):
    parsed = urllib.parse.urlparse(db_url)
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    return pg8000.connect(
        user=parsed.username,
        password=parsed.password,
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path[1:],
        ssl_context=ssl_ctx,
    )


def ensure_supabase_tables(pg):
    cur = pg.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            category_id INTEGER REFERENCES categories(id),
            parent_id INTEGER REFERENCES portfolios(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id SERIAL PRIMARY KEY,
            ticker TEXT NOT NULL,
            company_name TEXT,
            sector TEXT,
            domain TEXT,
            portfolio_id INTEGER REFERENCES portfolios(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            asset_id INTEGER REFERENCES assets(id),
            type TEXT NOT NULL,
            shares REAL NOT NULL,
            price REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            transaction_date TIMESTAMP DEFAULT NOW()
        )
    """)
    pg.commit()
    print("✅ Supabase tables ready")


def push(sqlite_conn, pg):
    cur_sq = sqlite_conn.cursor()
    cur_pg = pg.cursor()

    # Delete in reverse order to respect foreign key constraints
    for table in reversed(TABLES):
        cur_pg.execute(f"DELETE FROM {table}")
    pg.commit()

    # Insert in forward order (parents before children)
    for table in TABLES:
        if table == "portfolios":
            # Self-referential FK: insert parent rows (parent_id IS NULL) before children
            cur_sq.execute("SELECT * FROM portfolios ORDER BY parent_id NULLS FIRST, id")
        else:
            cur_sq.execute(f"SELECT * FROM {table}")
        rows = cur_sq.fetchall()
        col_names = [d[0] for d in cur_sq.description]

        if not rows:
            print(f"   {table}: 0 rows — skipped")
            continue

        placeholders = ", ".join(["%s"] * len(col_names))
        cols = ", ".join(col_names)
        for row in rows:
            cur_pg.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", list(row))

        # Reset serial sequence to max id
        if "id" in col_names:
            cur_pg.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), MAX(id)) FROM {table}")

        pg.commit()
        print(f"   {table}: {len(rows)} rows pushed ✅")


def pull(pg, sqlite_conn):
    cur_pg = pg.cursor()
    cur_sq = sqlite_conn.cursor()

    for table in TABLES:
        cur_pg.execute(f"SELECT * FROM {table}")
        rows = cur_pg.fetchall()
        col_names = [d[0] for d in cur_pg.description]

        if not rows:
            print(f"   {table}: 0 rows in Supabase — skipped")
            continue

        cur_sq.execute(f"DELETE FROM {table}")
        placeholders = ", ".join(["?"] * len(col_names))
        cols = ", ".join(col_names)
        cur_sq.executemany(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", rows)
        sqlite_conn.commit()
        print(f"   {table}: {len(rows)} rows restored ✅")


def main():
    mode = "pull" if "--pull" in sys.argv else "push"
    db_url = get_db_url()

    print(f"Connecting to Supabase...")
    pg = connect_supabase(db_url)
    print("✅ Connected")

    ensure_supabase_tables(pg)

    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row

    if mode == "push":
        print("\nPushing local SQLite → Supabase:")
        push(sqlite_conn, pg)
        print("\n✅ Push complete")
    else:
        print("\nPulling Supabase → local SQLite:")
        pull(pg, sqlite_conn)
        print("\n✅ Pull complete — local DB restored")

    sqlite_conn.close()
    pg.close()


if __name__ == "__main__":
    main()
