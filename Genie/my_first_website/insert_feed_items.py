import sys
import json
import pg8000
import ssl
import urllib.parse
from datetime import date

env_path = "/Users/popular/Desktop/Genie/my_first_website/.env"

# Production owner of all admin-authored content (see migrations/002_backfill_owner.sql
# and sync_reports_to_supabase.py) — feed items are published to every user the same
# way research reports are, so they're written under the same owner id.
PROD_OWNER_ID = "c2de9b2d-1916-4970-86a9-35999d4778d2"


def load_items(path):
    with open(path, "r", encoding="utf-8") as f:
        items = json.load(f)
    if not isinstance(items, list):
        raise ValueError("Expected a JSON list of items")
    return items


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 insert_feed_items.py <items.json>")
        sys.exit(1)

    items = load_items(sys.argv[1])
    print(f"Loaded {len(items)} item(s) from {sys.argv[1]}")

    db_url = None
    with open(env_path, "r") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                db_url = line.split("DATABASE_URL=", 1)[1].strip()
    if not db_url:
        print("❌ Error: DATABASE_URL not found in .env!")
        sys.exit(1)

    url = urllib.parse.urlparse(db_url)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    conn = pg8000.connect(
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port or 5432,
        database=url.path[1:],
        ssl_context=ssl_context
    )
    print("✅ Connected to Supabase.")

    # digest_date is the day this run happened — the feed files every item
    # from one run under this single date, regardless of each item's own
    # (possibly older) item_date. A per-item "digest_date" override is
    # honored for backfilling past runs, but defaults to today.
    run_date = date.today().isoformat()

    query = """
        INSERT INTO feed_items (user_id, item_date, digest_date, item_type, tickers, summary, th_summary, source_name, source_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    try:
        cursor = conn.cursor()
        for item in items:
            tickers = item.get("tickers", "")
            if isinstance(tickers, list):
                tickers = ",".join(t.strip().upper() for t in tickers if t.strip())
            cursor.execute(query, (
                PROD_OWNER_ID,
                item["item_date"],
                item.get("digest_date", run_date),
                item.get("item_type", "news"),
                tickers,
                item["summary"],
                item.get("th_summary"),
                item.get("source_name"),
                item.get("source_url"),
            ))
            print(f" - Inserted [{item.get('item_type', 'news')}] {item['item_date']}: {item['summary'][:70]}")
        conn.commit()
        print(f"🎉 {len(items)} feed item(s) published to Supabase!")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during insert: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
