import sqlite3
import os
import pg8000
import ssl
import urllib.parse

db_path = "/Users/popular/Desktop/Genie/my_first_website/portfolio.db"
env_path = "/Users/popular/Desktop/Genie/my_first_website/.env"

# Production owner of all research reports (see migrations/002_backfill_owner.sql).
# Local SQLite tags reports with the placeholder "local-dev-user", which is not a
# valid Supabase auth UUID, so we always write this real owner id instead.
PROD_OWNER_ID = "c2de9b2d-1916-4970-86a9-35999d4778d2"

# 1. Read all reports from SQLite
print("Reading reports from local SQLite...")
conn_sqlite = sqlite3.connect(db_path)
conn_sqlite.row_factory = sqlite3.Row
cursor_sqlite = conn_sqlite.cursor()
cursor_sqlite.execute("SELECT * FROM research_reports")
rows = cursor_sqlite.fetchall()
conn_sqlite.close()

# 2. Get Supabase Connection String
db_url = None
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                db_url = line.split("DATABASE_URL=", 1)[1].strip()

if not db_url:
    print("❌ Error: DATABASE_URL not found in .env!")
    exit(1)

# 3. Connect to Supabase
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

    # 4. Upsert all reports into Supabase
    query = """
        INSERT INTO research_reports (
            report_key, ticker, company_name, subtitle, prepared_by, audited_by, rating, is_positive, price_target, analysis_price, en_overview, th_overview, en_dcf, th_dcf, sector, user_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id, report_key) DO UPDATE SET
            ticker = EXCLUDED.ticker,
            company_name = EXCLUDED.company_name,
            subtitle = EXCLUDED.subtitle,
            prepared_by = EXCLUDED.prepared_by,
            audited_by = EXCLUDED.audited_by,
            rating = EXCLUDED.rating,
            is_positive = EXCLUDED.is_positive,
            price_target = EXCLUDED.price_target,
            analysis_price = EXCLUDED.analysis_price,
            en_overview = EXCLUDED.en_overview,
            th_overview = EXCLUDED.th_overview,
            en_dcf = EXCLUDED.en_dcf,
            th_dcf = EXCLUDED.th_dcf,
            sector = EXCLUDED.sector
    """

    for r in rows:
        cursor_pg.execute(query, (
            r['report_key'], r['ticker'], r['company_name'], r['subtitle'],
            r['prepared_by'], r['audited_by'], r['rating'], bool(r['is_positive']),
            r['price_target'], r['analysis_price'],
            r['en_overview'], r['th_overview'], r['en_dcf'], r['th_dcf'], r['sector'], PROD_OWNER_ID
        ))
        print(f" - Upserted report: {r['report_key']}")
        
    conn_pg.commit()
    print("🎉 All reports successfully synced to Supabase!")

except Exception as e:
    print(f"❌ Error during sync: {e}")
finally:
    conn_pg.close()
