-- Migration 009 — Daily feed items (macro/news bulletins for the research feed).
-- Run AFTER 003 (RLS pattern) and 007 (admin role, gates writes). Additive
-- only; safe on a live database.
--
-- These are short, admin-authored bulletins (macro news, per-ticker news)
-- shown in the Equity Research feed's date groups alongside full reports —
-- same "admin-authored, published to every user" model as research_reports
-- (see _load_reports()'s profiles.role='admin' check in api/index.py).
-- Manually curated and inserted via the daily-digest skill, not synced from
-- an external feed.

CREATE TABLE IF NOT EXISTS feed_items (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id),
    item_date   DATE NOT NULL,
    item_type   TEXT NOT NULL DEFAULT 'news', -- 'news' | 'macro'
    tickers     TEXT,                          -- comma-separated; nullable (pure macro items may tag none)
    summary     TEXT NOT NULL,
    source_name TEXT,
    source_url  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feed_items_date ON feed_items(item_date);
CREATE INDEX IF NOT EXISTS idx_feed_items_user ON feed_items(user_id);

-- RLS backstop, same rationale as 003/004/008: the app's user_id scoping
-- (application layer) is the primary guard; this protects direct
-- anon/authenticated access. Writes are additionally gated by
-- @require_admin at the API layer.
ALTER TABLE feed_items ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS feed_items_owner ON feed_items;
CREATE POLICY feed_items_owner ON feed_items
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
