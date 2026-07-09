-- Migration 008 — Sector master data (per-user).
-- Run AFTER 003 (RLS pattern) and 007 (role backfill, unrelated but keeps
-- the sequence honest). Additive only; safe on a live database.
--
-- The `sector` column on `assets` stays a free-text field (unchanged) — this
-- table is a per-user suggestion/master list for the ingest combobox and
-- dashboard filter, not a foreign key. Deleting a sector here never touches
-- existing assets.

CREATE TABLE IF NOT EXISTS sectors (
    id      BIGSERIAL PRIMARY KEY,
    name    TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_sectors_user_name ON sectors(user_id, name);
CREATE INDEX IF NOT EXISTS idx_sectors_user ON sectors(user_id);

-- RLS backstop, same rationale as 003/004: the app's user_id scoping is the
-- primary guard; this protects direct anon/authenticated access.
ALTER TABLE sectors ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS sectors_owner ON sectors;
CREATE POLICY sectors_owner ON sectors
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- Seed every existing portfolio owner with the historical default sector list...
INSERT INTO sectors (name, user_id)
SELECT DISTINCT d.name, p.user_id
FROM portfolios p
CROSS JOIN (VALUES
    ('Technology'), ('Industrial Goods'), ('Consumer Cyclical'),
    ('Financial Services'), ('Cryptocurrency'), ('Thai Mutual Fund')
) AS d(name)
WHERE p.user_id IS NOT NULL
ON CONFLICT (user_id, name) DO NOTHING;

-- ...plus every sector already in use by that user's own assets, so nothing
-- already on a holding is missing from the dropdown post-migration.
INSERT INTO sectors (name, user_id)
SELECT DISTINCT a.sector, p.user_id
FROM assets a
JOIN portfolios p ON a.portfolio_id = p.id
WHERE a.sector IS NOT NULL AND a.sector <> '' AND p.user_id IS NOT NULL
ON CONFLICT (user_id, name) DO NOTHING;
