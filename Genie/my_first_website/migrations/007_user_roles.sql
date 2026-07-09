-- 007_user_roles.sql
-- Adds a role to profiles for admin/user permission separation.
--   admin : full access (research authoring, thai_funds sync)
--   user  : full control of their OWN portfolio data; research is read-only
--           (admin-authored reports are served to every user by the backend)
-- The owner's account is backfilled to admin (identified as the only user
-- who owns portfolios at migration time).
-- App-layer checks in api/index.py are the primary guard, consistent with
-- the existing architecture (backend connects as DB owner / BYPASSRLS).

ALTER TABLE profiles ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user';

-- Backfill: every user who owns data today (= the owner) becomes admin.
INSERT INTO profiles (user_id, role)
SELECT DISTINCT user_id, 'admin' FROM portfolios
ON CONFLICT (user_id) DO UPDATE SET role = 'admin';
