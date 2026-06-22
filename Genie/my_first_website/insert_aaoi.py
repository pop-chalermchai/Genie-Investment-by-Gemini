import sqlite3
import os
import pg8000
import ssl
import urllib.parse
import shutil

import re

def clean_markdown(text):
    if not text:
        return ""
    # Remove frontmatter (YAML block at the top)
    if text.strip().startswith('---'):
        text = re.sub(r'^---\s*\n.*?\n---\s*\n', '', text, flags=re.DOTALL)
    # Remove links block at the bottom
    text = re.sub(r'\n*---\s*\n\*\*Links:\*\*.*$', '', text, flags=re.DOTALL)
    return text.strip()


# 0. Copy generated cover art to target path
source_art = "/Users/popular/.gemini/antigravity-cli/brain/8c5d788d-bc40-41ce-9e3c-678a3b1d647f/aaoi_cover_art_1781762657491.jpg"
dest_art = "/Users/popular/Desktop/Genie/research/AAOI/aaoi_report_cover_art.png"

try:
    if os.path.exists(source_art):
        os.makedirs(os.path.dirname(dest_art), exist_ok=True)
        shutil.copy(source_art, dest_art)
        print("✅ Successfully copied cover art to research/AAOI/aaoi_report_cover_art.png!")
    else:
        print("⚠️ Source cover art image not found!")
except Exception as e:
    print(f"❌ Error copying cover art: {e}")

# 1. Read files
with open("/Users/popular/Desktop/Genie/research/AAOI/01_Valerie_AAOI_Analysis.md", "r", encoding="utf-8") as f:
    en_overview = clean_markdown(f.read())

with open("/Users/popular/Desktop/Genie/research/AAOI/02_Christian_AAOI_Audit.md", "r", encoding="utf-8") as f:
    en_dcf = clean_markdown(f.read())

with open("/Users/popular/Desktop/Genie/research/AAOI/01_Valerie_AAOI_Analysis_TH.md", "r", encoding="utf-8") as f:
    th_overview = clean_markdown(f.read())

with open("/Users/popular/Desktop/Genie/research/AAOI/02_Christian_AAOI_Audit_TH.md", "r", encoding="utf-8") as f:
    th_dcf = clean_markdown(f.read())

db_path = "/Users/popular/Desktop/Genie/my_first_website/portfolio.db"

# 2. Insert to SQLite
conn_sqlite = sqlite3.connect(db_path)
cursor_sqlite = conn_sqlite.cursor()

try:
    cursor_sqlite.execute('''
        INSERT OR REPLACE INTO research_reports (
            report_key, ticker, company_name, subtitle, prepared_by, audited_by, rating, is_positive, en_overview, th_overview, en_dcf, th_dcf, sector
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'aaoi', 'AAOI', 'Applied Optoelectronics, Inc.', 'High-Speed Optical Transceivers, Active Optical Cables & AI Data Center Networking',
        'Valerie', 'Christian', 'HOLD', False, en_overview, th_overview, en_dcf, th_dcf, 'Technology'
    ))
    conn_sqlite.commit()
    print("✅ Successfully inserted AAOI reports into local SQLite!")
except Exception as e:
    print(f"❌ Error inserting to SQLite: {e}")
finally:
    conn_sqlite.close()

# 3. Read .env file for Supabase URL
env_path = "/Users/popular/Desktop/Genie/my_first_website/.env"
db_url = None
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                db_url = line.split("DATABASE_URL=", 1)[1].strip()

if db_url:
    print("Connecting to Supabase...")
    url = urllib.parse.urlparse(db_url)
    username = url.username
    password = url.password
    database = url.path[1:]
    hostname = url.hostname
    port = url.port or 5432

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        conn_pg = pg8000.connect(
            user=username,
            password=password,
            host=hostname,
            port=port,
            database=database,
            ssl_context=ssl_context
        )
        cursor_pg = conn_pg.cursor()
        print("✅ Connected to Supabase.")

        query = """
            INSERT INTO research_reports (
                report_key, ticker, company_name, subtitle, prepared_by, audited_by, rating, is_positive, en_overview, th_overview, en_dcf, th_dcf, sector
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (report_key) DO UPDATE SET
                ticker = EXCLUDED.ticker,
                company_name = EXCLUDED.company_name,
                subtitle = EXCLUDED.subtitle,
                prepared_by = EXCLUDED.prepared_by,
                audited_by = EXCLUDED.audited_by,
                rating = EXCLUDED.rating,
                is_positive = EXCLUDED.is_positive,
                en_overview = EXCLUDED.en_overview,
                th_overview = EXCLUDED.th_overview,
                en_dcf = EXCLUDED.en_dcf,
                th_dcf = EXCLUDED.th_dcf,
                sector = EXCLUDED.sector
        """

        cursor_pg.execute(query, (
            'aaoi', 'AAOI', 'Applied Optoelectronics, Inc.', 'High-Speed Optical Transceivers, Active Optical Cables & AI Data Center Networking',
            'Valerie', 'Christian', 'HOLD', False, en_overview, th_overview, en_dcf, th_dcf, 'Technology'
        ))
        conn_pg.commit()
        print("✅ Successfully inserted AAOI reports into Supabase!")
    except Exception as e:
        print(f"❌ Error inserting to Supabase: {e}")
    finally:
        conn_pg.close()
else:
    print("⚠️ DATABASE_URL not found in .env. Skipping Supabase migration.")