"""
Local SQLite migration — bring portfolio.db up to the multi-user schema.

This is the local-dev counterpart to migrations/001_multiuser_schema.sql (which
targets Supabase/Postgres). It adds the user_id columns the app now expects and
assigns all existing local rows to the local dev user, so `python3 api/index.py`
keeps working single-user against SQLite.

Idempotent and additive — safe to run more than once; never drops data.

    python3 migrate_local_sqlite.py
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portfolio.db")
DEV_USER_ID = os.environ.get("DEV_USER_ID", "local-dev-user")


def _columns(cur, table):
    cur.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}


def _table_exists(cur, table):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"No local DB at {DB_PATH} — nothing to migrate.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    changes = []
    for table in ("portfolios", "categories", "research_reports"):
        if not _table_exists(cur, table):
            continue
        cols = _columns(cur, table)
        if "user_id" not in cols:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN user_id TEXT")
            changes.append(f"{table}: added user_id")
        # backfill any NULL user_id to the local dev user
        cur.execute(f"UPDATE {table} SET user_id=? WHERE user_id IS NULL", (DEV_USER_ID,))
        if cur.rowcount:
            changes.append(f"{table}: backfilled {cur.rowcount} row(s) -> {DEV_USER_ID}")

    # portfolios.sort_order is referenced by the reorder endpoint
    if _table_exists(cur, "portfolios") and "sort_order" not in _columns(cur, "portfolios"):
        cur.execute("ALTER TABLE portfolios ADD COLUMN sort_order INTEGER")
        changes.append("portfolios: added sort_order")

    # profiles — local counterpart of migrations/004_profiles.sql (user_id is TEXT
    # here; no auth.users to reference in SQLite)
    if not _table_exists(cur, "profiles"):
        cur.execute(
            """
            CREATE TABLE profiles (
                user_id            TEXT PRIMARY KEY,
                display_name       TEXT,
                avatar_emoji       TEXT NOT NULL DEFAULT '🧞',
                preferred_currency TEXT NOT NULL DEFAULT 'USD',
                preferred_theme    TEXT NOT NULL DEFAULT 'light',
                preferred_language TEXT NOT NULL DEFAULT 'en',
                updated_at         DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        changes.append("profiles: created table")

    conn.commit()
    conn.close()

    if changes:
        print("✅ Local SQLite migrated:")
        for c in changes:
            print("   -", c)
    else:
        print("✅ Local SQLite already up to date.")


if __name__ == "__main__":
    migrate()
