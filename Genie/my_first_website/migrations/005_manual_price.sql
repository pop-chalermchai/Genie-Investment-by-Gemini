-- 005_manual_price.sql
-- Adds an optional user-entered market price on assets.
-- Used as a price override for assets whose market price cannot be fetched
-- automatically (Yahoo Finance / SEC API). NULL = use automatic live price.
-- Additive only — no existing data is modified.

ALTER TABLE assets ADD COLUMN IF NOT EXISTS manual_price DOUBLE PRECISION;
