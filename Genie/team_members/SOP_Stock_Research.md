# Standard Operating Procedure: Autonomous Stock Research Pipeline

## Pipeline Architecture

Each ticker runs its own **independent lane** — no global phase blocking. Valerie, Christian, and Genie's correction step pipeline per ticker; Serene batches all tickers in a single session at the end.

```
[Valerie RKLB]──→[Christian RKLB]──→[Genie: apply RKLB corrections]─┐
[Valerie CIFR]──→[Christian CIFR]──→[Genie: apply CIFR corrections]─┤──→[Serene: batch all]
[Valerie OKLO]──→[Christian OKLO]──→[Genie: apply OKLO corrections]─┘
```

**Sequencing rules:**
1. Spawn ALL Valerie agents in parallel (background)
2. As EACH Valerie finishes → immediately spawn Christian for that ticker (don't wait for other tickers)
3. As EACH Christian finishes → Genie applies corrections immediately (see Phase 2 → Genie step)
4. Once ALL tickers have AUDITED files → spawn ONE Serene session for all tickers (batched, sequentially)
5. Once ALL tickers have Thai translations → run Phase 4 (Database Deploy) for all tickers

> Pipeline currently ends after Phase 4 (database deploy). Cover art (Mateo) is still on hold until re-added to this SOP.

---

## Phase 1: Quantitative Research (Valerie × N — all parallel)

Spawn one Valerie agent per ticker simultaneously (all background).

**Prompt to Valerie:**
> "Analyze the stock ticker `{TICKER}`. Use the templates at:
> - `/Users/popular/Desktop/Genie/research/stock analysis template/stock_analysis_overview_v3.md`
> - `/Users/popular/Desktop/Genie/research/stock analysis template/reverse_dcf_analysis_v2.md`
>
> Perform a deep-dive fundamental analysis and a Reverse DCF analysis. Save the two reports as:
> - `research/{TICKER}/01_Valerie_{TICKER}_Overview.md`
> - `research/{TICKER}/02_Valerie_{TICKER}_ReverseDCF.md`"

---

## Phase 2: Forensic Audit — Diff-Only Format (Christian × N — pipelined)

Spawn Christian **as soon as each ticker's Valerie files land** — do not wait for all tickers.

**Prompt to Christian:**
> "Independently audit the fundamental and Reverse DCF analyses for `{TICKER}` performed by Valerie. Files are at:
> - `research/{TICKER}/01_Valerie_{TICKER}_Overview.md`
> - `research/{TICKER}/02_Valerie_{TICKER}_ReverseDCF.md`
>
> Verify all financial data against live SEC filings and market data. Then output a **correction-only report** (NOT a full rewritten file) saved to:
> - `research/{TICKER}/03_Christian_{TICKER}_Corrections.md`
>
> Use the Correction Table Format specified in this SOP. If there are no errors, still output the table (empty) with status PASS."

**Christian's output format** (`03_Christian_{TICKER}_Corrections.md`):

```markdown
# Christian Audit — {TICKER}
**Status:** PASS / PASS WITH CORRECTIONS / FAIL
**Audit Date:** {date}
**Source:** 01_Valerie_{TICKER}_Overview.md + 02_Valerie_{TICKER}_ReverseDCF.md

## Correction Table

| Error ID | File | Section | Old Text (exact) | Corrected Text | Source |
|---|---|---|---|---|---|
| E-01 | Overview | Section 2, Row "Cash" | `~$780M` | `$275.3M` | 10-K FY2024, p.45 |
| E-02 | DCF | Section 4, Bull table 2027 row | `15 MWe / ~$15–18M` | `75 MWe / ~$82.7M` | 10-K FY2025 |

_If no errors: leave table body empty. Status = PASS._
```

> **FAIL status** = critical data integrity failure. Do not proceed to Phase 3. Notify Genie immediately.

---

## Genie: Apply Corrections (between Phase 2 and Phase 3)

After each Christian agent completes, Genie applies corrections and creates AUDITED files:

1. **Read** `03_Christian_{TICKER}_Corrections.md`
2. **Copy** Valerie's originals:
   - Read `01_Valerie_{TICKER}_Overview.md` → Write as `03_Valerie_{TICKER}_Overview_AUDITED.md`
   - Read `02_Valerie_{TICKER}_ReverseDCF.md` → Write as `03_Valerie_{TICKER}_ReverseDCF_AUDITED.md`
3. **Apply** each row in the Correction Table using Edit tool (old_string → new_string) on the AUDITED files
4. If status = PASS (no corrections): skip step 3, the copy itself is the AUDITED file
5. **Confirm** AUDITED files exist before proceeding

> Note: "Old Text (exact)" in Christian's table must be unique enough to match with Edit tool. If ambiguous, Christian should include a longer surrounding string.

---

## Phase 3: Localization (Serene — batched)

Trigger only after ALL tickers have both AUDITED files ready.

### Serene — ONE session, all tickers sequentially

**Prompt to Serene:**
> "Translate the following audited financial reports into elegant, formal Thai. Process each ticker sequentially in this session.
>
> **Tickers to translate: {TICKER_1}, {TICKER_2}, {TICKER_3}**
>
> For each ticker, translate:
> - `research/{TICKER}/03_Valerie_{TICKER}_Overview_AUDITED.md` → save as `research/{TICKER}/04_Serene_{TICKER}_Overview_TH.md`
> - `research/{TICKER}/03_Valerie_{TICKER}_ReverseDCF_AUDITED.md` → save as `research/{TICKER}/04_Serene_{TICKER}_ReverseDCF_TH.md`
>
> Maintain flawless formatting continuity with the English originals. Preserve all tables, headers, and markdown structure."

Cover art (Mateo) is paused — do not run it until this SOP is updated to bring it back. Once all tickers have Thai translations, proceed to Phase 4 below to load the reports into the database.

---

## Phase 4: Database Deploy

After a ticker (or batch of tickers) has both AUDITED files and both Thai translation files, load the data into the database:

1. Add the uppercase `{TICKER}` string into the `tickers` array inside [insert_all.py](file:///Users/popular/Desktop/Genie/my_first_website/insert_all.py).
2. Run `python3 insert_all.py` inside `my_first_website/` to clean and load the reports into the local SQLite `portfolio.db`.
   - `insert_all.py` reads the **AUDITED** overview (`03_Valerie_{TICKER}_Overview_AUDITED.md`) and **AUDITED** DCF (`03_Valerie_{TICKER}_ReverseDCF_AUDITED.md`) files, falling back to the raw `01_`/`02_` drafts only if no AUDITED file exists yet.
3. Run `python3 sync_reports_to_supabase.py` to synchronize the changes to the live production database.
4. **Do NOT** use `deploy_report.py` — it is obsolete, formats keys with `_2026` suffixes, and will create duplicate entries on the dashboard.

---

## File Naming Convention Summary

| Step | File | Who creates |
|---|---|---|
| Phase 1 | `01_Valerie_{TICKER}_Overview.md` | Valerie |
| Phase 1 | `02_Valerie_{TICKER}_ReverseDCF.md` | Valerie |
| Phase 2 | `03_Christian_{TICKER}_Corrections.md` | Christian |
| Genie apply | `03_Valerie_{TICKER}_Overview_AUDITED.md` | Genie (copy + edit) |
| Genie apply | `03_Valerie_{TICKER}_ReverseDCF_AUDITED.md` | Genie (copy + edit) |
| Phase 3 | `04_Serene_{TICKER}_Overview_TH.md` | Serene |
| Phase 3 | `04_Serene_{TICKER}_ReverseDCF_TH.md` | Serene |

---

## Session Limit Guidelines

- If a Valerie or Christian agent hits a session limit: re-spawn for the affected ticker only
- If Serene hits a limit mid-batch: re-spawn with remaining tickers only (skip completed ones)
- Parallel spawns maximum: 3 Valerie (background). Never more than 3 heavy agents simultaneously
- If repeated limit hits occur: stagger spawns by 2–3 minutes instead of launching all at once

---

## Web Modal (Quick Updates)

The `+ New` button on the Equity Research page is available for minor edits to existing reports. For full pipeline injection, use Phase 4 (Database Deploy) above — do not use `deploy_report.py`, which is obsolete.
