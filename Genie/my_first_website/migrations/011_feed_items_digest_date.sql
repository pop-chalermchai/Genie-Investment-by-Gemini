-- Migration 011 — Digest run date for feed items.
-- Run AFTER 010. Additive only; safe on a live database.
--
-- feed_items.item_date is the news's own date (see migration 010's freshness
-- policy — items span up to 7 days back). The research feed's date-grouped
-- view used to scatter one digest run's items across all of those dates,
-- which read as noise once a run started spanning a week. digest_date is
-- the day the /daily-digest run actually happened — the feed now files all
-- of a run's items as ONE row under digest_date, and item_date is used only
-- to order items *within* that row when it's opened.

ALTER TABLE feed_items ADD COLUMN IF NOT EXISTS digest_date DATE;

-- Backfill: every row published so far came from the single 2026-07-20 run.
UPDATE feed_items SET digest_date = '2026-07-20' WHERE digest_date IS NULL;
