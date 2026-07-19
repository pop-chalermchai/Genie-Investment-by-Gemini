# Migrations

Numbered SQL migrations for the Genie Investment Postgres (Supabase) database.
Run them **in order**, once, against the Supabase SQL editor (or `psql`).
This replaces the old `migrate_db()` startup hack (see Product Roadmap step 3).

## Order & purpose

| File | What it does | When |
|------|--------------|------|
| `001_multiuser_schema.sql` | Adds `user_id` columns + indexes; makes report_key / category name unique **per user** | First |
| `002_backfill_owner.sql` | Assigns all existing rows to the owner's UUID, then sets `NOT NULL` | After creating the owner's auth user |
| `003_rls.sql` | Enables Row-Level Security policies (defense-in-depth) | After 002 |
| `004_profiles.sql` | Per-user profile table (display name, avatar, currency/theme/language preferences) + RLS | After 003 |
| `005_manual_price.sql` | Adds nullable `assets.manual_price` — user-entered market-price override for assets that can't be priced automatically | Applied 2026-07-07 |
| `006_research_date.sql` | Adds `research_reports.research_date` for the date-sorted research feed; backfills existing rows to the migration date | Applied 2026-07-08 |
| `007_user_roles.sql` | Adds `profiles.role` (admin/user) — research authoring + thai_funds sync become admin-only; owner backfilled as admin | Applied 2026-07-09 |
| `008_sectors.sql` | Adds per-user `sectors` master-data table (ingest combobox + dashboard filter) + RLS; seeds defaults + every sector already on an existing asset | Applied 2026-07-10 |
| `009_feed_items.sql` | Adds `feed_items` table for admin-authored macro/news bulletins shown in the research feed's date groups, alongside full reports + RLS | Applied 2026-07-19 |

## Step-by-step (multi-user go-live)

1. **Back up first** — Supabase point-in-time restore, or `python3 sync_portfolio_to_supabase.py --pull`.
2. **Create the owner user** — Supabase Dashboard → Authentication → Users → invite `chanruthaikul@gmail.com`. Copy the generated **UUID**.
3. Run `001_multiuser_schema.sql`.
4. Edit `002_backfill_owner.sql`: replace every `<OWNER_UUID>` with the UUID from step 2. Run it. Confirm the three orphan-count checks all return 0.
5. Run `003_rls.sql`.
6. No JWT secret needed — this project signs tokens with **ES256** (asymmetric).
   The backend verifies them via the project JWKS endpoint automatically
   (`SUPABASE_URL` defaults to the project URL; override with an env var only if
   the project changes). Auth is enforced in production because `DATABASE_URL` is set.
7. Deploy the code and verify login works end-to-end.

## Notes

- The Flask backend connects as the DB owner role (BYPASSRLS), so **application-layer
  `user_id` scoping in `api/index.py` is the primary guard** — RLS here is a backstop.
  See `../ARCHITECTURE_MULTIUSER.md` §0.
- These migrations are Postgres-only. Local SQLite dev uses `init_db.py` (its schema
  should be kept roughly in sync, but local dev runs single-user).
- If your Supabase project uses **asymmetric** JWT signing keys (newer projects) rather
  than the legacy HS256 secret, the backend's `jwt.decode(..., algorithms=['HS256'])`
  must be switched to verify via the project JWKS. Flag this before go-live.
