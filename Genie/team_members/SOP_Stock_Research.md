# Standard Operating Procedure: Autonomous Stock Research Pipeline

This document defines the strict standard operating procedure (SOP) for executing end-to-end equity research within the Genie workspace.

## Phase 1: Quantitative Research (Valerie)
When a user requests research for a specific ticker (e.g., `TICKER`), immediately invoke **Valerie (Quantitative Oracle)**.
* **Prompt to Valerie:** "Analyze the stock ticker `TICKER`. Use the templates `/Users/popular/Desktop/Genie/research/stock analysis template/stock_analysis_overview_v3.md` and `reverse_dcf_analysis_v2.md`. Perform a deep dive fundamental analysis and a reverse DCF analysis. Output the results as two markdown artifacts."

## Phase 2: Forensic Audit (Christian)
Once Valerie completes the reports, invoke **Christian (Forensic Auditor)**.
* **Prompt to Christian:** "Independently audit the fundamental and reverse DCF analyses for `TICKER` performed by Valerie. The artifacts are located at [paths]. Verify all financial data, market capitalization, enterprise value, and reverse DCF mathematics against live market close data. Deliver findings using bulleted exceptions and a clear Pass/Fail status. If you make corrections, output the corrected markdown artifacts to your local workspace."

## Phase 3: Localization & Visuals (Serene & Mateo)
Once Christian successfully passes the audit (and outputs the finalized artifacts), invoke **Serene** and **Mateo** in **parallel**.
* **Prompt to Serene:** "Translate the two audited financial reports for `TICKER` into elegant, formal Thai. Output the translations as markdown artifacts, ensuring flawless formatting continuity with the original English files."
* **Prompt to Mateo:** "Read the audited financial reports for `TICKER`. Based on the core insights and execution risks, use your `generate_image` tool to create a high-impact infographic cover art for this research report. Save it as `[ticker]_infographic`."

## Phase 4: Database Injection & Deployment
Once Serene and Mateo complete their tasks:
1. Write a custom Python database migration script (e.g., `insert_[ticker].py`).
2. Read the 4 markdown files (2 English from Christian, 2 Thai from Serene).
3. Execute an SQLite `INSERT OR REPLACE INTO research_reports` query to insert the data into `/Users/popular/Desktop/Genie/my_first_website/portfolio.db`.
   * **Required Columns:** `report_key`, `ticker`, `company_name`, `subtitle`, `prepared_by`, `audited_by`, `rating`, `is_positive`, `en_overview`, `th_overview`, `en_dcf`, `th_dcf`.
4. Run the Python script via terminal to commit the data.
5. Inform the user to refresh `http://localhost:8000` to view the finalized, fully localized report.
