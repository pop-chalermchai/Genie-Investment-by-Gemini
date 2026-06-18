import sqlite3
import os
import urllib.parse
import ssl
import pg8000
import sys

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'portfolio.db')

print("====================================================")
print("     SQLite to Supabase (PostgreSQL) Migrator       ")
print("====================================================")

# 1. Check local SQLite DB
if not os.path.exists(DB_PATH):
    print(f"❌ Error: Local SQLite database not found at {DB_PATH}")
    print("Please make sure you run this script inside the 'my_first_website' directory.")
    sys.exit(1)

# 2. Get Supabase Connection String
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("\nPlease enter your Supabase Connection String.")
    print("Format: postgresql://postgres:[password]@db.[project-id].supabase.co:5432/postgres")
    db_url = input("\nSupabase URL: ").strip()

if not db_url:
    print("❌ Error: Connection string cannot be empty.")
    sys.exit(1)

# Modify protocol if necessary
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# 3. Connect to Databases
try:
    print("\nConnecting to local SQLite...")
    conn_sqlite = sqlite3.connect(DB_PATH)
    cursor_sqlite = conn_sqlite.cursor()
    print("✅ Connected to SQLite.")
except Exception as e:
    print(f"❌ Failed to connect to SQLite: {e}")
    sys.exit(1)

try:
    print("Connecting to Supabase (PostgreSQL)...")
    url = urllib.parse.urlparse(db_url)
    username = url.username
    password = url.password
    database = url.path[1:]
    hostname = url.hostname
    port = url.port or 5432
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
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
except Exception as e:
    print(f"❌ Failed to connect to Supabase: {e}")
    print("\nDouble check your credentials, password, and network connection.")
    conn_sqlite.close()
    sys.exit(1)

# 4. Create Tables on Postgres
print("\nCreating tables on Supabase if they don't exist...")

tables_schemas = {
    "categories": """
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            description TEXT
        );
    """,
    "portfolios": """
        CREATE TABLE IF NOT EXISTS portfolios (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            category_id INTEGER REFERENCES categories (id)
        );
    """,
    "assets": """
        CREATE TABLE IF NOT EXISTS assets (
            id SERIAL PRIMARY KEY,
            ticker VARCHAR(50) NOT NULL,
            company_name VARCHAR(255),
            sector VARCHAR(255),
            portfolio_id INTEGER REFERENCES portfolios (id)
        );
    """,
    "transactions": """
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            asset_id INTEGER REFERENCES assets (id),
            type VARCHAR(50) NOT NULL,
            shares DOUBLE PRECISION NOT NULL,
            price DOUBLE PRECISION NOT NULL,
            currency VARCHAR(10) DEFAULT 'USD',
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "research_reports": """
        CREATE TABLE IF NOT EXISTS research_reports (
            id SERIAL PRIMARY KEY,
            report_key VARCHAR(255) UNIQUE NOT NULL,
            ticker VARCHAR(50),
            company_name VARCHAR(255),
            subtitle VARCHAR(255),
            prepared_by VARCHAR(255),
            audited_by VARCHAR(255),
            rating VARCHAR(50),
            is_positive BOOLEAN,
            en_overview TEXT,
            th_overview TEXT,
            en_dcf TEXT,
            th_dcf TEXT,
            sector VARCHAR(255)
        );
    """
}

try:
    for table_name, schema in tables_schemas.items():
        print(f" - Table '{table_name}'...")
        cursor_pg.execute(schema)
    conn_pg.commit()
    print("✅ Schema created successfully.")
except Exception as e:
    print(f"❌ Error creating schema on Supabase: {e}")
    conn_sqlite.close()
    conn_pg.close()
    sys.exit(1)

# 5. Migrate Data
print("\nMigrating data table by table...")

def migrate_table(table_name, columns, pg_placeholders):
    print(f"Migrating table '{table_name}'...")
    
    # Check if table already has data
    cursor_pg.execute(f"SELECT COUNT(*) FROM {table_name}")
    count_pg = cursor_pg.fetchone()[0]
    if count_pg > 0:
        overwrite = input(f" ⚠️ Table '{table_name}' already has {count_pg} rows on Supabase. Overwrite? (y/n): ").strip().lower()
        if overwrite != 'y':
            print(f" Skipping table '{table_name}'.")
            return
        # Truncate table CASCADE
        print(f" Truncating table '{table_name}'...")
        cursor_pg.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
        conn_pg.commit()

    # Get data from SQLite
    cols_str = ", ".join(columns)
    cursor_sqlite.execute(f"SELECT {cols_str} FROM {table_name}")
    rows = cursor_sqlite.fetchall()
    
    if not rows:
        print(f" - No rows to migrate for '{table_name}'.")
        return

    # Insert into Postgres
    insert_query = f"INSERT INTO {table_name} ({cols_str}) VALUES ({pg_placeholders})"
    inserted_count = 0
    for row in rows:
        cursor_pg.execute(insert_query, row)
        inserted_count += 1
        
    conn_pg.commit()
    print(f" ✅ Successfully migrated {inserted_count} rows to '{table_name}'.")

try:
    # Migrate in order of dependencies (FKs)
    migrate_table(
        "categories", 
        ["id", "name", "description"], 
        "%s, %s, %s"
    )
    migrate_table(
        "portfolios", 
        ["id", "name", "category_id"], 
        "%s, %s, %s"
    )
    migrate_table(
        "assets", 
        ["id", "ticker", "company_name", "sector", "portfolio_id"], 
        "%s, %s, %s, %s, %s"
    )
    migrate_table(
        "transactions", 
        ["id", "asset_id", "type", "shares", "price", "currency", "transaction_date"], 
        "%s, %s, %s, %s, %s, %s, %s"
    )
    migrate_table(
        "research_reports", 
        ["id", "report_key", "ticker", "company_name", "subtitle", "prepared_by", "audited_by", "rating", "is_positive", "en_overview", "th_overview", "en_dcf", "th_dcf", "sector"], 
        "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
    )

    # 6. Reset Sequences for Auto-Increment
    print("\nSyncing auto-increment sequences in Supabase...")
    for table in tables_schemas.keys():
        seq_query = f"SELECT setval('{table}_id_seq', COALESCE((SELECT MAX(id) FROM {table}), 1), true);"
        cursor_pg.execute(seq_query)
    conn_pg.commit()
    print("✅ Sequences synced successfully.")

    print("\n🎉 MIGRATION COMPLETED SUCCESSFULLY! 🎉")
    print("Your Supabase database is now fully synced with your local portfolio database.")

except Exception as e:
    print(f"❌ Error during migration: {e}")
    conn_pg.rollback()
finally:
    conn_sqlite.close()
    conn_pg.close()
