-- Migration 004 — per-user profile (display name, avatar, app preferences).
-- Run AFTER 003. Additive only; safe on a live database.
--
-- email / last_sign_in_at / created_at live in auth.users — do not duplicate here.
-- Preferences move cross-device state out of localStorage so a user gets the
-- same currency/theme/language on every machine.

CREATE TABLE IF NOT EXISTS profiles (
    user_id            UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name       TEXT,
    avatar_emoji       TEXT NOT NULL DEFAULT '🧞',
    preferred_currency TEXT NOT NULL DEFAULT 'USD' CHECK (preferred_currency IN ('USD', 'THB')),
    preferred_theme    TEXT NOT NULL DEFAULT 'light' CHECK (preferred_theme IN ('light', 'dark')),
    preferred_language TEXT NOT NULL DEFAULT 'en' CHECK (preferred_language IN ('en', 'th')),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- RLS backstop, same rationale as 003: the app's user_id scoping is the primary
-- guard; this protects direct anon/authenticated access.
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS profiles_owner ON profiles;
CREATE POLICY profiles_owner ON profiles
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
