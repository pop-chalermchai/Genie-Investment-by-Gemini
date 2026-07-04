#!/usr/bin/env python3
"""One-time insert of KFAFIXSSF into Supabase thai_funds."""

import os, sys, ssl, urllib.parse
import pg8000

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")

def get_db_url():
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    return line.split("DATABASE_URL=", 1)[1].strip()
    return os.environ.get("DATABASE_URL")

def connect(db_url):
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
    pg = connect(get_db_url())
    cur = pg.cursor()
    cur.execute("""
        INSERT INTO thai_funds (proj_id, proj_abbr_name, proj_name_th, proj_name_en, fund_status, amc_name_en, unique_id, last_synced)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (proj_id) DO UPDATE SET
            proj_abbr_name = EXCLUDED.proj_abbr_name,
            proj_name_th   = EXCLUDED.proj_name_th,
            proj_name_en   = EXCLUDED.proj_name_en,
            amc_name_en    = EXCLUDED.amc_name_en,
            last_synced    = NOW()
    """, (
        'F00001514W',
        'KFAFIXSSF',
        'กองทุนเปิดกรุงศรีแอคทีฟตราสารหนี้-เพื่อการออม',
        'Krungsri Active Fixed Income Fund-SSF',
        'RG',
        'KRUNGSRI ASSET MANAGEMENT COMPANY LIMITED',
        'C0000000709',
    ))
    pg.commit()

    cur.execute("SELECT proj_id, proj_abbr_name, proj_name_th FROM thai_funds WHERE proj_abbr_name = 'KFAFIXSSF'")
    print("✅ Inserted:", cur.fetchone())
    pg.close()

if __name__ == "__main__":
    main()
