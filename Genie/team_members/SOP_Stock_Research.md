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

## Phase 4: Database Injection & Deployment (Genie)
Once Serene and Mateo complete their tasks, **Genie** handles deployment directly — no Python script required, no manual copy-paste.

1. Read the 4 finalized markdown files (2 English from Christian, 2 Thai from Serene).
2. Call `POST http://127.0.0.1:8000/api/research-report` via curl with a JSON payload containing all required fields.
3. Confirm `{"success": true}` response.
4. Inform Pop to refresh `http://localhost:8000` to view the report live.

**Required fields in the JSON payload:**

| Field | Description |
|---|---|
| `report_key` | Unique ID e.g. `NVDA_2026` |
| `ticker` | Stock ticker e.g. `NVDA` |
| `company_name` | Full company name |
| `subtitle` | Report tagline |
| `sector` | Sector e.g. `Technology` |
| `prepared_by` | e.g. `Valerie (Quantitative Oracle)` |
| `audited_by` | e.g. `Christian (Forensic Auditor)` |
| `rating` | e.g. `BUY`, `ACCUMULATE`, `AVOID` |
| `is_positive` | `true` / `false` |
| `price_target` | Target price (number) |
| `analysis_price` | Price at time of analysis (number) |
| `en_overview` | English overview markdown (full text) |
| `th_overview` | Thai overview markdown (full text) |
| `en_dcf` | English DCF markdown (full text) |
| `th_dcf` | Thai DCF markdown (full text) |

> **Note:** The web modal (`+ New` button on the Equity Research page) is available for quick edits or minor updates to existing reports. For full report injection after the pipeline, always use the API method above.
