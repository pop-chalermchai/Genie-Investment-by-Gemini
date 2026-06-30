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
- **Production URL:** https://genie-investment-by-gemini.vercel.app
- **Root directory (in Vercel settings):** `Genie/my_first_website`
- `.vercel/project.json` is committed — DO NOT delete it
- Must run `npx vercel --prod` from git root (`~/Desktop`), NOT from `my_first_website/`

## Database
- **Production:** Supabase (Postgres) — `DATABASE_URL` in `.env`
- **Local fallback:** SQLite `portfolio.db` (gitignored)
- Sync script: `python3 sync_portfolio_to_supabase.py [--pull]`
- Do NOT sync routinely — production data belongs to users

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
