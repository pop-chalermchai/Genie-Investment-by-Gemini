import sqlite3
import os
import pg8000
import ssl
import urllib.parse

# 1. Read files
with open("/Users/popular/Desktop/Genie/research/NVDA/01_Valerie_NVDA_Analysis.md", "r", encoding="utf-8") as f:
    en_overview = f.read()

with open("/Users/popular/Desktop/Genie/research/NVDA/02_Christian_NVDA_Audit.md", "r", encoding="utf-8") as f:
    en_dcf = f.read()

with open("/Users/popular/Desktop/Genie/research/NVDA/01_Valerie_NVDA_Analysis_TH.md", "r", encoding="utf-8") as f:
    th_overview = f.read()

with open("/Users/popular/Desktop/Genie/research/NVDA/02_Christian_NVDA_Audit_TH.md", "r", encoding="utf-8") as f:
    th_dcf = f.read()

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
        'nvda', 'NVDA', 'NVIDIA Corporation', 'CUDA Lock-In, Blackwell Scaling & Valuation Audits',
        'Valerie', 'Christian', 'BUY (ON PULLBACKS)', True, en_overview, th_overview, en_dcf, th_dcf, 'Semiconductors'
    ))
    conn_sqlite.commit()
    print("✅ Successfully inserted NVDA reports into local SQLite!")
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
            'nvda', 'NVDA', 'NVIDIA Corporation', 'CUDA Lock-In, Blackwell Scaling & Valuation Audits',
            'Valerie', 'Christian', 'BUY (ON PULLBACKS)', True, en_overview, th_overview, en_dcf, th_dcf, 'Semiconductors'
        ))
        conn_pg.commit()
        print("✅ Successfully inserted NVDA reports into Supabase!")
    except Exception as e:
        print(f"❌ Error inserting to Supabase: {e}")
    finally:
        conn_pg.close()
else:
    print("⚠️ DATABASE_URL not found in .env. Skipping Supabase migration.")
