# Standard Operating Procedure: Autonomous Stock Research Pipeline

## Pipeline Architecture

Each ticker runs its own **independent lane** — no global phase blocking. Valerie, Christian, and Genie's correction step pipeline per ticker; Serene batches all tickers in a single session at the end.

```
[Valerie RKLB]──→[Christian RKLB]──→[Genie: apply RKLB corrections]─┐
[Valerie CIFR]──→[Christian CIFR]──→[Genie: apply CIFR corrections]─┤──→[Serene: batch all]
[Valerie OKLO]──→[Christian OKLO]──→[Genie: apply OKLO corrections]─┘   [Mateo ×N parallel]
                                                                               │
                                                                         [deploy_report.py ×N]
```

**Sequencing rules:**
1. Spawn ALL Valerie agents in parallel (background)
2. As EACH Valerie finishes → immediately spawn Christian for that ticker (don't wait for other tickers)
3. As EACH Christian finishes → Genie applies corrections immediately (see Phase 2 → Genie step)
4. Once ALL tickers have AUDITED files → spawn ONE Serene session for all tickers (batched, sequentially)
5. In parallel with Serene → spawn Mateo for all tickers (background)
6. Once Serene and Mateo finish → run `deploy_report.py` for each ticker

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

## Phase 3: Localization (Serene — batched) & Visuals (Mateo — parallel)

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

### Mateo — parallel (background), one spawn per ticker

**Prompt to Mateo:**
> "Read the audited financial report for `{TICKER}` at `research/{TICKER}/03_Valerie_{TICKER}_Overview_AUDITED.md`. Based on the company's sector, business model, and key insights, use your `generate_image` tool to create a high-impact institutional cover art image. Save it as `research/{TICKER}/{ticker_lowercase}_cover_art.png`."

---

## Phase 4: Database Injection (deploy_report.py)

Once Serene and Mateo complete, Genie runs the deploy script for each ticker. **Do NOT read markdown files into context** — the script handles file I/O directly.

```bash
cd /Users/popular/Desktop/Genie/my_first_website

python3 deploy_report.py \
  --ticker {TICKER} \
  --company "{COMPANY_NAME}" \
  --sector "{SECTOR}" \
  --rating "{RATING}" \
  --positive \
  --pt {PRICE_TARGET} \
  --price {ANALYSIS_PRICE}
```

Use `--negative` instead of `--positive` for AVOID/SELL ratings.
Use `--mode update` to overwrite an existing report (e.g. re-deploying with corrections).
Use `--key {TICKER}_{YEAR}` to override the default report key.

Confirm `✓ SUCCESS` output for each ticker before reporting completion.

> **Server must be running:** `python server.py` on port 8000.
> If server is not running, instruct Pop to start it before deploy.

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
| Phase 3 | `{ticker}_cover_art.png` | Mateo |

---

## Session Limit Guidelines

- If a Valerie or Christian agent hits a session limit: re-spawn for the affected ticker only
- If Serene hits a limit mid-batch: re-spawn with remaining tickers only (skip completed ones)
- Parallel spawns maximum: 3 Valerie + 3 Mateo (background). Never more than 3 heavy agents simultaneously
- If repeated limit hits occur: stagger spawns by 2–3 minutes instead of launching all at once

---

## Web Modal (Quick Updates)

The `+ New` button on the Equity Research page is available for minor edits to existing reports. For full pipeline injection, always use `deploy_report.py`.
