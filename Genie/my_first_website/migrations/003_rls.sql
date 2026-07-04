-- Migration 003 — Row-Level Security (defense-in-depth backstop).
-- Run AFTER 002 (data must be backfilled, or rows vanish from every query).
--
-- IMPORTANT: The Flask backend connects as the DB owner role, which has BYPASSRLS.
-- So these policies do NOT protect requests coming through the app — the app's own
-- user_id scoping (see api/index.py) is the PRIMARY guard. RLS here protects against
-- direct access via the anon/authenticated Supabase roles (e.g. supabase-js, the
-- REST API, future clients) and catches app queries that forget to scope.

ALTER TABLE portfolios       ENABLE ROW LEVEL SECURITY;
ALTER TABLE assets           ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions     ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories       ENABLE ROW LEVEL SECURITY;
ALTER TABLE thai_funds       ENABLE ROW LEVEL SECURITY;

-- Direct-owner tables
DROP POLICY IF EXISTS portfolios_owner ON portfolios;
CREATE POLICY portfolios_owner ON portfolios
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS reports_owner ON research_reports;
CREATE POLICY reports_owner ON research_reports
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS categories_owner ON categories;
CREATE POLICY categories_owner ON categories
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- Inherited ownership via foreign keys
DROP POLICY IF EXISTS assets_owner ON assets;
CREATE POLICY assets_owner ON assets
    USING (portfolio_id IN (SELECT id FROM portfolios WHERE user_id = auth.uid()))
    WITH CHECK (portfolio_id IN (SELECT id FROM portfolios WHERE user_id = auth.uid()));

DROP POLICY IF EXISTS transactions_owner ON transactions;
CREATE POLICY transactions_owner ON transactions
    USING (asset_id IN (
        SELECT a.id FROM assets a JOIN portfolios p ON a.portfolio_id = p.id
        WHERE p.user_id = auth.uid()))
    WITH CHECK (asset_id IN (
        SELECT a.id FROM assets a JOIN portfolios p ON a.portfolio_id = p.id
        WHERE p.user_id = auth.uid()));

-- Shared reference data: any authenticated user may read; writes only via service_role
-- (service_role bypasses RLS, so the sync endpoint keeps working; no write policy = no
-- writes for anon/authenticated).
DROP POLICY IF EXISTS thai_funds_read ON thai_funds;
CREATE POLICY thai_funds_read ON thai_funds FOR SELECT USING (auth.role() = 'authenticated');
