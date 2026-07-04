-- Migration 001 — Multi-user schema (Supabase / Postgres)
-- Adds user ownership columns. Run BEFORE 002_backfill and 003_rls.
-- Safe to re-run: uses IF NOT EXISTS.
--
-- Ownership model (see ARCHITECTURE_MULTIUSER.md):
--   portfolios / research_reports / categories  -> own user_id column
--   assets / transactions                       -> inherit via foreign keys (NO user_id)
--   thai_funds                                  -> shared reference data (NO user_id)

ALTER TABLE portfolios       ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);
ALTER TABLE research_reports ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);
ALTER TABLE categories       ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

CREATE INDEX IF NOT EXISTS idx_portfolios_user ON portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_user    ON research_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_categories_user ON categories(user_id);

-- research_reports.report_key is currently globally UNIQUE. With per-user reports,
-- two users may legitimately use the same key. Make uniqueness per-user instead.
ALTER TABLE research_reports DROP CONSTRAINT IF EXISTS research_reports_report_key_key;
CREATE UNIQUE INDEX IF NOT EXISTS uq_reports_user_key ON research_reports(user_id, report_key);

-- categories.name is currently globally UNIQUE. Same reasoning — scope per user.
ALTER TABLE categories DROP CONSTRAINT IF EXISTS categories_name_key;
CREATE UNIQUE INDEX IF NOT EXISTS uq_categories_user_name ON categories(user_id, name);
