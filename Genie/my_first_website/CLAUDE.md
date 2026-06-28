# Genie Investment — Project Guide for AI Agents

## Repository structure
- Git root: `~/Desktop/` (one level above this file)
- Web app lives in: `~/Desktop/Genie/my_first_website/`
- Obsidian research vault: `~/Desktop/Genie/research/`

## Deploy workflow — ALWAYS follow this order

### 1. Commit & push to GitHub
```bash
cd ~/Desktop
git add <files>
git commit -m "..."
git push origin main
```

### 2. Sync portfolio DB → Supabase
```bash
cd ~/Desktop/Genie/my_first_website
python3 sync_portfolio_to_supabase.py
```

### 3. Deploy → Vercel
**Must run from git root (`~/Desktop`), NOT from `my_first_website/`**
```bash
cd ~/Desktop
npx vercel --prod
```
Or use the convenience script (handles both steps 2 and 3):
```bash
cd ~/Desktop/Genie/my_first_website
./deploy.sh
```

## Vercel project
- **Project name:** `genie-investment-by-gemini`
- **Team:** `popular-s-projects1`
- **Production URL:** https://genie-investment-by-gemini.vercel.app
- **Root directory (in Vercel settings):** `Genie/my_first_website`
- `.vercel/project.json` is committed — DO NOT delete it
- Always verify with `npx vercel project ls` before deploying if unsure

## Supabase sync
- Script: `my_first_website/sync_portfolio_to_supabase.py`
- Push local → Supabase: `python3 sync_portfolio_to_supabase.py`
- Pull Supabase → local: `python3 sync_portfolio_to_supabase.py --pull`
- Connection string loaded from `my_first_website/.env` (not committed)

## Common mistakes to avoid
- Do NOT run `vercel --prod` from inside `my_first_website/` — it will path-resolve incorrectly
- Do NOT run `vercel --prod` without `.vercel/project.json` present — it will create a new project
- Do NOT commit `.env` or `portfolio.db` (both in `.gitignore`)
