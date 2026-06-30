#!/usr/bin/env python3
"""
Sync thai_funds from local SQLite → Supabase in batches.
Usage: python3 sync_thai_funds_to_supabase.py
"""

import sqlite3
import os
import sys
import ssl
import urllib.parse
import pg8000

SQLITE_PATH = os.path.join(os.path.dirname(__file__), "portfolio.db")
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
BATCH_SIZE = 1000


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


def main():
    db_url = get_db_url()
    print("Connecting to Supabase...")
    pg = connect_supabase(db_url)
    print("✅ Connected")

    cur_pg = pg.cursor()

    # Ensure table exists
    cur_pg.execute("""
        CREATE TABLE IF NOT EXISTS thai_funds (
            proj_id TEXT PRIMARY KEY,
            proj_abbr_name TEXT,
            proj_name_th TEXT,
            proj_name_en TEXT,
            fund_status TEXT,
            amc_name_en TEXT,
            unique_id TEXT,
            last_synced TIMESTAMP
        )
    """)
    pg.commit()

    # Check current Supabase count
    cur_pg.execute("SELECT COUNT(*) FROM thai_funds")
    before_count = cur_pg.fetchone()[0]
    print(f"Supabase before: {before_count} funds")

    # Load from local SQLite
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    cur_sq = sqlite_conn.cursor()
    cur_sq.execute("SELECT proj_id, proj_abbr_name, proj_name_th, proj_name_en, fund_status, amc_name_en, unique_id FROM thai_funds")
    rows = cur_sq.fetchall()
    print(f"Local SQLite: {len(rows)} funds → pushing to Supabase...")

    upserted = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        # Build single multi-row INSERT — 1 round trip per batch instead of 1 per row
        placeholders = ", ".join(
            ["(%s, %s, %s, %s, %s, %s, %s, NOW())"] * len(batch)
        )
        values = []
        for row in batch:
            values.extend([row["proj_id"], row["proj_abbr_name"], row["proj_name_th"],
                           row["proj_name_en"], row["fund_status"], row["amc_name_en"], row["unique_id"]])
        cur_pg.execute(f"""
            INSERT INTO thai_funds (proj_id, proj_abbr_name, proj_name_th, proj_name_en, fund_status, amc_name_en, unique_id, last_synced)
            VALUES {placeholders}
            ON CONFLICT (proj_id) DO UPDATE SET
                proj_abbr_name = EXCLUDED.proj_abbr_name,
                proj_name_th = EXCLUDED.proj_name_th,
                proj_name_en = EXCLUDED.proj_name_en,
                fund_status = EXCLUDED.fund_status,
                amc_name_en = EXCLUDED.amc_name_en,
                unique_id = EXCLUDED.unique_id,
                last_synced = NOW()
        """, values)
        pg.commit()
        upserted += len(batch)
        print(f"  {upserted}/{len(rows)} done...")

    cur_pg.execute("SELECT COUNT(*) FROM thai_funds")
    after_count = cur_pg.fetchone()[0]
    print(f"\n✅ Done. Supabase after: {after_count} funds (was {before_count})")

    sqlite_conn.close()
    pg.close()


if __name__ == "__main__":
    main()
