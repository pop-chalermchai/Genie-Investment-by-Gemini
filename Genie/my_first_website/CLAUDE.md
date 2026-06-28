# Genie Investment — Project Guide for AI Agents

## Repository structure
- Git root: `~/Desktop/` (one level above this file)
- Web app lives in: `~/Desktop/Genie/my_first_website/`
- Obsidian research vault: `~/Desktop/Genie/research/`

## Deploy workflow

### Deploying code changes only (most common case)
```bash
cd ~/Desktop/Genie/my_first_website
./deploy.sh
```
This deploys code to Vercel ONLY. It does NOT touch Supabase data.

### Deploying code + syncing local DB to Supabase
```bash
cd ~/Desktop/Genie/my_first_website
./deploy.sh --sync
```
⚠️ Only use `--sync` when you intentionally want to overwrite Supabase with local SQLite data (e.g. after making data changes locally). Running `--sync` when users have made changes on the live site will DELETE their data.

### Manual steps (if needed)
```bash
# 1. Push code to GitHub
cd ~/Desktop && git push origin main

# 2. Deploy to Vercel (from git root)
cd ~/Desktop && npx vercel --prod

# 3. Sync DB (only when needed)
cd ~/Desktop/Genie/my_first_website && python3 sync_portfolio_to_supabase.py
```

## Vercel project
- **Project name:** `genie-investment-by-gemini`
- **Team:** `popular-s-projects1`
- **Production URL:** https://genie-investment-by-gemini.vercel.app
- **Root directory (in Vercel settings):** `Genie/my_first_website`
- `.vercel/project.json` is committed — DO NOT delete it
- Must run `npx vercel --prod` from git root (`~/Desktop`), NOT from `my_first_website/`

## Supabase sync
- Script: `my_first_website/sync_portfolio_to_supabase.py`
- Push local → Supabase: `python3 sync_portfolio_to_supabase.py`
- Pull Supabase → local: `python3 sync_portfolio_to_supabase.py --pull`
- Connection string loaded from `my_first_website/.env` (not committed)
- **Production DB is Supabase** — users add data there directly via the web app
- **Local DB is SQLite** — only for local development and testing

## Common mistakes to avoid
- Do NOT run `./deploy.sh` with `--sync` for routine code deployments — it overwrites live user data
- Do NOT run `vercel --prod` from inside `my_first_website/` — it will path-resolve incorrectly
- Do NOT run `vercel --prod` without `.vercel/project.json` present — it will create a new project
- Do NOT commit `.env` or `portfolio.db` (both in `.gitignore`)
