# Project Rules

- **Terminology:** When the user mentions "research", they are referring to the "Equity Research" page/section of the application.

- **Running the web app locally:**
  ```bash
  cd /Users/popular/Desktop/Genie/my_first_website
  python3 api/index.py
  ```
  - Reads `DATABASE_URL` from `.env` → connects directly to **Supabase** (same DB as production)
  - Falls back to local SQLite `portfolio.db` if `.env` has no `DATABASE_URL`
  - Do NOT use `server.py` — it is legacy and SQLite-only
  - App runs at `http://127.0.0.1:8000`

- **Deploying the web app:**
  ```bash
  cd /Users/popular/Desktop/Genie/my_first_website
  ./deploy.sh          # deploy code to Vercel only (safe — does NOT touch DB)
  ./deploy.sh --sync   # deploy code AND overwrite Supabase with local SQLite
  ```
  ⚠️ Never use `--sync` unless intentionally seeding/resetting production data. It will DELETE any data users have added on the live site.
  - Production URL: https://genie-investment-by-gemini.vercel.app
  - Vercel project: `genie-investment-by-gemini` (team: `popular-s-projects1`)
  - Must run from git root (`~/Desktop`) if running `npx vercel --prod` manually

- **Standard Equity Research Ingestion Workflow:** When creating, updating, or inserting equity research reports, the agent MUST follow these steps to prevent database duplicates and parsing errors:
  1. Save the reports as clean Markdown files inside the `research/{TICKER}/` directory using the standard filenames:
     - `01_Valerie_{TICKER}_Overview.md` (English Overview)
     - `02_Valerie_{TICKER}_ReverseDCF.md` (English Reverse DCF)
     - `04_Serene_{TICKER}_Overview_TH.md` (Thai Overview)
     - `04_Serene_{TICKER}_ReverseDCF_TH.md` (Thai Reverse DCF)
  2. Add the uppercase `{TICKER}` string into the `tickers` array inside [insert_all.py](file:///Users/popular/Desktop/Genie/my_first_website/insert_all.py).
  3. Run `python3 insert_all.py` inside `my_first_website/` to clean and load them into the local SQLite `portfolio.db` database.
  4. Run `python3 sync_reports_to_supabase.py` to synchronize changes to the live production database.
  5. Do NOT use manual SQL INSERT queries or obsolete deployment tools (like `deploy_report.py` which formats keys with `_2026` suffixes), as this creates duplicates on the dashboard.

