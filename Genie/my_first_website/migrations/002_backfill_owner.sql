-- Migration 002 — Backfill existing single-user data to the first owner.
-- Run AFTER 001, and AFTER creating the owner's auth user in Supabase Auth.
--
-- HOW TO GET c2de9b2d-1916-4970-86a9-35999d4778d2:
--   1. Sign up / invite chanruthaikul@gmail.com via Supabase Auth (Dashboard > Authentication).
--   2. Copy the user's UUID from the Users table.
--   3. Replace every c2de9b2d-1916-4970-86a9-35999d4778d2 below with it (keep the quotes).
--
-- BACK UP FIRST (Supabase point-in-time or sync_portfolio_to_supabase.py --pull).
-- This is hard to reverse.

UPDATE portfolios       SET user_id = 'c2de9b2d-1916-4970-86a9-35999d4778d2' WHERE user_id IS NULL;
UPDATE research_reports SET user_id = 'c2de9b2d-1916-4970-86a9-35999d4778d2' WHERE user_id IS NULL;
UPDATE categories       SET user_id = 'c2de9b2d-1916-4970-86a9-35999d4778d2' WHERE user_id IS NULL;

-- Verify no orphans remain (each should return 0):
--   SELECT count(*) FROM portfolios       WHERE user_id IS NULL;
--   SELECT count(*) FROM research_reports WHERE user_id IS NULL;
--   SELECT count(*) FROM categories       WHERE user_id IS NULL;

-- Only after the counts above are all 0, enforce NOT NULL:
ALTER TABLE portfolios       ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE research_reports ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE categories       ALTER COLUMN user_id SET NOT NULL;
