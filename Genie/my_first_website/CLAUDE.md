# Genie Investment — Project Guide for AI Agents

## Repository structure
- Git root: `~/Desktop/` (one level above this file)
- Web app lives in: `~/Desktop/Genie/my_first_website/`
- Obsidian research vault: `~/Desktop/Genie/research/`

## Running locally

```bash
cd ~/Desktop/Genie/my_first_website
python3 api/index.py
```

- Reads `DATABASE_URL` from `.env` → connects to **Supabase** automatically
- If `.env` has no `DATABASE_URL` → falls back to local SQLite (`portfolio.db`)
- Do NOT use `server.py` for new development (legacy, SQLite-only)

## Deploy workflow

### Deploying code changes (most common)
```bash
cd ~/Desktop/Genie/my_first_website
./deploy.sh
```
Deploys code to Vercel ONLY. Does NOT touch Supabase data.

### Deploying code + syncing local DB → Supabase
```bash
./deploy.sh --sync
```
⚠️ Only use when intentionally overwriting Supabase with local data (e.g. initial seed). Will DELETE any data users have added on production since last sync.

### Manual Vercel deploy (from git root)
```bash
cd ~/Desktop && npx vercel --prod
```

## Vercel project
- **Project name:** `genie-investment-by-gemini`
- **Team:** `popular-s-projects1`
- **Production URL:** https://genieports.com (custom domain, registered via Vercel)
- **Fallback URL:** https://genie-investment-by-gemini.vercel.app (still serves the same deployment)
- **Root directory (in Vercel settings):** `Genie/my_first_website`
- `.vercel/project.json` is committed — DO NOT delete it
- Must run `npx vercel --prod` from git root (`~/Desktop`), NOT from `my_first_website/`

## Database
- **Production:** Supabase (Postgres) — `DATABASE_URL` in `.env`
- **Local fallback:** SQLite `portfolio.db` (gitignored)
- Sync script: `python3 sync_portfolio_to_supabase.py [--pull]`
- Do NOT sync routinely — production data belongs to users
- **Schema migrations:** numbered SQL in `migrations/` — run in order (see `migrations/README.md`). Replaces the old `migrate_db()` startup hack.
- **Local SQLite schema:** after pulling multi-user changes, run `python3 migrate_local_sqlite.py` once to add `user_id`/`sort_order` columns to an existing `portfolio.db` and backfill to the dev user.
- **Auth mode is backend-driven:** `GET /api/auth-config` returns `{authRequired}`. It's true when `DATABASE_URL` or `SUPABASE_JWT_SECRET` is set (prod, or local-against-Supabase), false only in pure local SQLite dev. The frontend reads this to decide whether to show the login screen.

## Auth & multi-user (in progress — see ARCHITECTURE_MULTIUSER.md)
- Auth provider: **Supabase Auth** (HS256 JWT). Signup is **invite-only** at launch.
- Every `/api/*` route is `@require_auth`. Data is scoped by `user_id` at the
  **application layer** (primary guard); RLS in `migrations/003_rls.sql` is a backstop
  because the backend connects as the DB owner (BYPASSRLS).
- Tokens are **ES256** (asymmetric). The backend verifies them via the project
  JWKS endpoint (`SUPABASE_URL` → `/auth/v1/.well-known/jwks.json`). HS256 + a
  `SUPABASE_JWT_SECRET` is also supported (tests / legacy) but not used in prod.
- Env vars:
  - `SUPABASE_URL` — defaults to the project URL; used to build the JWKS URL. No secret required for auth.
  - `SEC_FACTSHEET_KEY`, `SEC_DAILY_INFO_KEY` — required for Thai-fund endpoints (no hardcoded fallback).
  - `DEV_USER_ID` — local single-user id (default `local-dev-user`). The no-token dev
    fallback works ONLY when running local SQLite with `DATABASE_URL` and `SUPABASE_JWT_SECRET` both unset.
- When adding/altering any endpoint that touches user data, scope every query by
  `user_id` and add an isolation test. This is the invariant that keeps users separate.

## Tests
```bash
cd ~/Desktop/Genie/my_first_website
DATABASE_URL="" SEC_FACTSHEET_KEY="" python3 -m pytest tests/ -q
```
- `tests/test_api_baseline.py` — characterization of core flows (single-user).
- `tests/test_auth_isolation.py` — proves user A cannot see/modify/delete user B's data.
- Run before committing any change to `api/index.py`.

## Ship it convention

When the user says **"ship it"**, execute these three steps in order without asking:

1. **Commit** — stage changed files and commit with a descriptive message
2. **Deploy** — `cd ~/Desktop && npx vercel --prod`
3. **Push** — `git -C ~/Desktop/Genie push`

Do not ask for confirmation. Do not stop between steps unless one of them fails.

---

## Common mistakes to avoid
- Do NOT run `./deploy.sh --sync` for routine code deployments — overwrites live user data
- Do NOT run `vercel --prod` from inside `my_first_website/` — path-resolves incorrectly
- Do NOT run `vercel --prod` without `.vercel/project.json` — creates a duplicate project
- Do NOT commit `.env` or `portfolio.db` (both in `.gitignore`)

---

## Product Roadmap (future development)

### Phase: Multi-user support
When opening the app to external users, these must be implemented in order:

1. **Authentication** — Add login system
   - Recommended: Supabase Auth (built-in, free tier)
   - Alternative: Clerk (better UX, paid)
   - Each user gets their own session and identity

2. **Row-Level Security (RLS)** — Supabase Postgres policy
   - Users can only read/write their own portfolios, assets, transactions
   - Prevents data leakage between users
   - Must be enabled BEFORE opening to public

3. **Schema migrations** — Replace `migrate_db()` startup hack
   - Use proper migration scripts (e.g. numbered SQL files)
   - Run migrations manually, not on every server start
   - Prevents accidental schema changes in production

4. **Backup strategy** — Supabase has built-in daily backups (Pro plan)
   - `sync_portfolio_to_supabase.py --pull` can serve as manual backup
   - Do NOT rely on local SQLite as backup for production data
