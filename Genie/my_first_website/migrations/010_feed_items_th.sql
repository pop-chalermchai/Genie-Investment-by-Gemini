-- Migration 010 — Thai translation for feed items.
-- Run AFTER 009. Additive only; safe on a live database.
--
-- Mirrors research_reports' en_overview/th_overview pairing: feed_items keeps
-- one English `summary` (NOT NULL, unchanged) plus an optional `th_summary`
-- for the Thai translation. Nullable because older rows and macro items the
-- author skips translating simply fall back to English in the UI (same
-- fallback rule already used for report overviews).

ALTER TABLE feed_items ADD COLUMN IF NOT EXISTS th_summary TEXT;
