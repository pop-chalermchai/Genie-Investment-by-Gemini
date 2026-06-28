# FORENSIC AUDIT REPORT — OKLO Inc. (NYSE: OKLO)

> **Auditor:** Christian (The Forensic Auditor)
> **Subject:** Equity Research Reports by Valerie (The Quantitative Oracle)
> **Files Audited:**
> - `01_Valerie_OKLO_Overview.md`
> - `02_Valerie_OKLO_ReverseDCF.md`
> **Audit Date:** June 20, 2026
> **Methodology:** Independent verification against SEC filings (10-K FY2025, 10-Q Q1 2026), press releases, and cross-referenced market data aggregators (StockAnalysis, StockTitan, Macrotrends, FinanceCharts)

---

## EXECUTIVE SUMMARY

The two Oklo reports are **substantially accurate** in their current financial data (Q1 2026 balance sheet, income statement, guidance, pipeline agreements, regulatory milestones), market metrics, and reverse DCF methodology. However, **three material errors** and **two minor errors** require correction. The most significant errors are: (1) a materially wrong FY2024 year-end cash figure in the historical financial table, and (2) an incorrect reactor capacity designation for Aurora-INL in the reverse DCF scenario tables, which cascades into incorrect revenue projections for 2027.

**Corrected files have been produced** as `03_Valerie_OKLO_Overview_AUDITED.md` and `03_Valerie_OKLO_ReverseDCF_AUDITED.md`.

---

## SECTION 1 — KEY FINANCIAL FIGURES

**VERDICT: CONDITIONAL PASS**

### Current Market Data (as of June 17–20, 2026)

| Claimed Figure | Verified Figure | Source | Status |
| :--- | :--- | :--- | :--- |
| Market Cap ~$10.6B | $10.53–$10.64B (range across sources) | Multiple market data aggregators | PASS |
| Shares Outstanding ~174M | 173,867,839 shares per Q1 2026 10-Q | SEC EDGAR, oklo-20260331 | PASS |
| EV ~$8.06B | ~$8.0–8.1B (confirmed calculation) | Derived from market cap minus $2.54B cash | PASS |
| Stock Price ~$61 | $58.82–$61.14 (range June 17–20) | Market data; volatility across sources | PASS |
| 52-Week Range $35.69–$193.84 | $35.69–$193.84 (older pull) / $44.88–$193.84 (updated pull) | Macrotrends; minor data-pull timing difference | CONDITIONAL PASS — see note |
| ATH $193.84 | $193.84 confirmed | Macrotrends | PASS |

*Note on 52-week range: The $35.69 low reflects a range pulled slightly before the audit date; the updated range from some sources shows $44.88. This is a data-pull timing artifact, not an analytical error. No correction required.*

### Q1 2026 Financial Results (Period ended March 31, 2026)

| Claimed Figure | Verified Figure | Source | Status |
| :--- | :--- | :--- | :--- |
| Cash & Marketable Securities $2.54B | $2,536,898K ($2.537B) | Q1 2026 10-Q, oklo-20260331 | PASS |
| Total Debt $0 | $0 confirmed | Q1 2026 10-Q | PASS |
| Net Loss -$33.1M | -$33,065K confirmed | Q1 2026 10-Q | PASS |
| Operating Loss -$51.2M | -$51,249K confirmed | Q1 2026 10-Q | PASS |
| EPS -$0.19 | -$0.19 per basic/diluted share | Q1 2026 10-Q | PASS |
| Non-Op Income $21.3M | $21,339K confirmed | Q1 2026 10-Q | PASS |
| R&D Expense $27.0M | $27,049K confirmed | Q1 2026 10-Q | PASS |
| G&A Expense $24.2M | $24,200K confirmed | Q1 2026 10-Q | PASS |
| SBC Q1 2026 $15.6M | $15,586K confirmed; SBC annualized ~$62.3M | Q1 2026 10-Q | PASS |
| Operating Cash Burn Q1 $17.9M | $17,867K confirmed | Q1 2026 10-Q cash flow statement | PASS |
| Q1 2026 Capex $32.8M | $32,810K confirmed | Q1 2026 10-Q cash flow statement | PASS |
| Total Q1 investing outflows $359M | $359,034K confirmed | Q1 2026 10-Q | PASS |
| ATM raise Q1 2026: $1.18B / 12.4M shares | $1,181,897K; 12,376,352 shares at avg $96.95 net | Q1 2026 10-Q | PASS |
| FY2026 Operating Burn Guidance $80–100M | $80–100M confirmed | Q1 2026 earnings call | PASS |
| FY2026 Capex Guidance $350–450M | $350–450M confirmed | Q1 2026 earnings call | PASS |

### Historical Annual Financials

| Claimed Figure | Verified Figure | Source | Status |
| :--- | :--- | :--- | :--- |
| FY2025 Operating Loss -$139.3M | -$139.29M confirmed | Q1 2026 10-Q comparative; 10-K FY2025 | PASS |
| FY2025 Net Loss -$105.7M | -$105.66M confirmed | StockTitan, multiple aggregators | PASS |
| FY2025 EPS -$0.72 | -$0.72 confirmed | StockAnalysis, StockTitan | PASS |
| FY2025 Cash (Dec 31, 2025) ~$1.23B | $788.45M (cash) + $439.53M (mkt sec) = $1.228B | StockAnalysis balance sheet; consistent with Q4 earnings call stating "~$1.4B" at year-end before remaining ATM draws | PASS |
| FY2024 Operating Loss -$52.8M | -$52.8M confirmed | StockAnalysis, multiple aggregators | PASS |
| FY2024 Net Loss -$73.6M | -$73.62M confirmed | StockAnalysis | PASS |
| FY2024 EPS -$0.74 | -$0.74 confirmed | StockAnalysis | PASS |
| **FY2024 Cash (Dec 31, 2024) "~$780M"** | **$275.3M confirmed** | **10-K FY2024; multiple sources** | **FAIL — MATERIAL ERROR** |

**EXCEPTION — MATERIAL ERROR (FY2024 Cash):**
The Overview historical table states cash was "~$780M" at December 31, 2024. This is factually incorrect. Per Oklo's FY2024 10-K (filed March 2025), total cash, cash equivalents, and marketable securities were **$275.3M** at December 31, 2024. The correct sequence is: Dec 2024 = $275.3M → Dec 2025 = $1.23B (following the December 2025 ATM raise that generated $300M gross by year-end plus prior cash) → March 2026 = $2.54B (following $1.18B Q1 2026 ATM draw). The $780M figure does not correspond to any known Oklo cash balance at any quarter end.

**Correction:** Historical table FY2024 cash restated to "$275.3M" from "~$780M."

### Dilution & Share Count

| Claimed Figure | Verified Figure | Source | Status |
| :--- | :--- | :--- | :--- |
| Shares Dec 2025 "~157M" | 160,514,103 shares per Q1 2026 10-Q comparison column | SEC EDGAR, oklo-20260331 balance sheet | FAIL — MINOR ERROR |
| Shares June 2026 ~174M | 173,867,839 per Q1 10-Q; ~174M confirmed | Q1 2026 10-Q | PASS |
| 6-Month Dilution "+10.8%" | (173.87M – 160.51M) / 160.51M = **+8.3%** | Derived from 10-Q verified share counts | FAIL — MINOR ERROR |
| SBC Annualized ~$62M | $15.586M × 4 = $62.3M | Q1 2026 10-Q | PASS |

**EXCEPTION — MINOR ERROR (Share Count Dec 2025):**
The report states "~157 million" shares at December 31, 2025. Per the comparative balance sheet in the Q1 2026 10-Q (which discloses Dec 31, 2025 shares as 160,514,103), the correct figure is approximately **160.5M** shares. This also invalidates the stated 6-month dilution of +10.8%; the correct figure is +8.3% over this window.

---

## SECTION 2 — PIPELINE FIGURES

**VERDICT: PASS**

| Claimed Figure | Verified Figure | Source | Status |
| :--- | :--- | :--- | :--- |
| 14 GW total announced pipeline | Confirmed as stated pipeline aggregate | Multiple sources including Utility Dive, DCD | PASS |
| Switch: 12 GW non-binding MPA | Confirmed 12 GW non-binding master power agreement | Utility Dive, Oklo newsroom | PASS |
| Meta: 1.2 GW Ohio campus, January 2026, prepayment | Confirmed January 9, 2026 announcement, 1.2 GW, prepayment mechanism, Pike County Ohio | Oklo newsroom, Yahoo Finance | PASS |
| Equinix: 500 MW LOI | Confirmed 500 MW agreement, non-binding | Multiple sources | PASS |
| Pipeline concentration: Switch = 85.7% | 12,000 / 14,000 = 85.7% — confirmed | Arithmetic verification | PASS |
| Centrus LOI June 2026, HALEU for up to 5 Aurora powerhouses | Confirmed June 18, 2026 announcement; up to 5 Aurora powerhouses for Ohio campus; Piketon, Ohio HALEU supply starting 2029 | PRNewswire, Oklo newsroom | PASS |

---

## SECTION 3 — REVERSE DCF MATHEMATICS

**VERDICT: CONDITIONAL PASS**

### Formula and Implied Revenue Calculations

The Reverse DCF uses `Implied Revenue = EV × (CoE – g) / FCF Margin`. This is the Gordon Growth Model inverted, applied to steady-state FCF. The formula is appropriate and correctly applied.

| Scenario | Claimed Revenue | Verified Revenue | Status |
| :--- | :--- | :--- | :--- |
| Bear (16% CoE, 3% g, 15% margin) | $6.98B | $8.06B × 0.13 / 0.15 = **$6.985B** | PASS (rounding) |
| Base (14% CoE, 3% g, 20% margin) | $4.43B | $8.06B × 0.11 / 0.20 = **$4.433B** | PASS (rounding) |
| Bull (12% CoE, 3% g, 25% margin) | $2.90B | $8.06B × 0.09 / 0.25 = **$2.902B** | PASS (rounding) |

### Revenue Per Reactor Calculation

**Claimed:** 75 MWe × 8,760 hrs/yr × 90% × $120/MWh = **$70.9M**
**Verified:** 75 × 8,760 × 0.90 × 120 = 75 × 946,080 = **$70,956,000 = $70.96M** → rounds to $70.9M

**STATUS: PASS**

### Reactor Count Calculations — MATERIAL DISCREPANCY

The report applies $70.9M/reactor to divide into implied revenues, but the stated reactor counts and GW figures do not match the arithmetic:

| Scenario | Implied Revenue | Reactor Count Stated | Reactor Count Correct | GW Stated | GW Correct | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Bear $6.98B | $6,985M / $70.9M | "85+ reactors" | **98.5 reactors ≈ 98–99** | "~6.4 GW" | **~7.4 GW** | FAIL |
| Base $4.43B | $4,433M / $70.9M | "~54 reactors" | **62.5 reactors ≈ 62–63** | "~4 GW" | **~4.7 GW** | FAIL |
| Bull $2.90B | $2,902M / $70.9M | "~35 reactors" | **40.9 reactors ≈ 41** | "~2.6 GW" | **~3.1 GW** | FAIL |

**EXCEPTION — MATERIAL ERROR (Reactor Counts in Section 2):**
The implied reactor counts and GW figures in Section 2 of the Reverse DCF are all materially understated. The error appears systematic — reactor counts understate by approximately 12–16 per scenario relative to the arithmetic. This is significant because it understates the execution difficulty of each scenario. The text descriptions following the table correctly characterize these as demanding outcomes, but the numerical anchors are wrong and should be corrected.

### Aurora-INL Reactor Size in Scenario Tables — MATERIAL ERROR

**VERDICT: FAIL**

The Bull and Base scenario revenue ramp tables in Reverse DCF Section 4 describe Aurora-INL operations as generating revenue from a "15 MWe (Aurora-INL pilot)" unit in 2027. This is factually incorrect.

**Verified fact:** The Aurora powerhouse under construction at INL (groundbreaking September 22, 2025) is a **75 MWe** sodium-cooled fast reactor. Per ANS Nuclear Newswire (September 2025), World Nuclear News, and Oklo's own press releases, the first Aurora powerhouse is rated at 75 MWe. The "15 MWe" scale belonged to an earlier, abandoned design configuration prior to Oklo's scaling announcement in 2024.

**Impact on Revenue Projections:**
- Bull 2027 revenue shown as "~$15–18M" at "15 MWe" — if Aurora-INL is 75 MWe and operates at 90% CF under a $140/MWh PPA, the correct 2027 revenue (for a partial year, say Q4 2027 only) should be approximately $70.9M × 1/4 quarter ≈ $18–21M for partial-year, or the full year at 75 MWe × 90% × $140/MWh × 8,760 hrs = **$82.7M annually**.
- Base 2029 revenue shown as "~$13M" for "15 MWe Aurora-INL FCO" — at 75 MWe × 85% CF × $115/MWh, the correct annual figure would be **~$62.5M**.
- Bear 2031 revenue shown as "~$10M" for "15 MWe" — at 75 MWe × 80% CF × $95/MWh, the correct figure would be **~$50.1M**.

The operational capacity row labels need correction from "15 MWe" to "75 MWe" and revenue estimates updated accordingly throughout all three scenario tables.

---

## SECTION 4 — REGULATORY TIMELINE CLAIMS

**VERDICT: PASS**

| Claimed Fact | Verified Status | Source | Status |
| :--- | :--- | :--- | :--- |
| NRC PDC Topical Report approved; 15-day acceptance vs 30-60 days | Confirmed. NRC approved May 6, 2026. 15-day acceptance vs typical 30-60 days explicitly confirmed | BusinessWire, May 6, 2026 | PASS |
| Aurora-INL groundbreaking September 2025 | Confirmed September 22, 2025 | ANS Nuclear Newswire, Oklo newsroom | PASS |
| Aurora-INL targets late 2027 / early 2028 operation | Confirmed late 2027 / early 2028 window. One source notes DOE "fast-track" designation may accelerate further | World Nuclear News, Fox Business, multiple | PASS |
| DOE authorization path (not NRC) for Aurora-INL | Confirmed. Aurora-INL progresses via DOE Reactor Pilot Program authorization, not standard NRC COLA | ANS, Oklo newsroom DOE NSDA approvals | PASS |
| NRC denied first Aurora application January 2022 | Confirmed | SEC filings, public record | PASS |
| COLA Phase 1 submission planned for 2026 | Confirmed. NRC COLA submission for commercial Aurora fleet is a 2026 planned milestone per Q1 2026 earnings call | Q1 2026 earnings call transcript | PASS |
| Atomic Alchemy NRC materials license granted March 2026 | Confirmed March 17, 2026 | BusinessWire, Oklo newsroom | PASS |
| Groves criticality targeted July 2026 | Confirmed "by 4 July" per Nuclear Engineering International | NEI Magazine, Oklo NSDA approval press release | PASS |
| Groves: DOE NSDA approval obtained | Confirmed | Oklo newsroom | PASS |
| Kiewit as construction contractor | Confirmed; referenced in Centrus LOI press release | PRNewswire Centrus LOI announcement | PASS |
| Part 57 regulatory framework under development | Confirmed — in development at NRC, not yet codified | NRC regulatory activities | PASS |
| Sam Altman stepped down as chairman April 2025 | Confirmed April 22, 2025 | Bloomberg, CNBC, multiple | PASS |

---

## SECTION 5 — INPUT DATA FRESHNESS

**VERDICT: PASS**

All primary financial data is sourced from:
- Q1 2026 10-Q (period ended March 31, 2026, filed May 12, 2026) — **current**
- FY2025 10-K (period ended December 31, 2025, filed March 17, 2026) — **current**
- Press releases from January–June 2026 — **current**
- Market data accessed June 17–20, 2026 — **current as of report date**

The analyst consensus data (23 analysts, mean $88.63, median $84.00) is consistent with data from S&P Global as of June 2026, though slight variations exist across aggregators ($88.89 mean from one source vs. $88.63 stated). These are within normal aggregator variance. The consensus rating of "Buy" is confirmed.

Data freshness: **No stale data identified** beyond the single FY2024 historical cash error noted in Section 1.

---

## CONSOLIDATED EXCEPTION LIST

### Material Errors (Require Correction)

**E-01 — FY2024 Year-End Cash (Overview, Section 2 Historical Table)**
- Claimed: "~$780M" at December 31, 2024
- Verified: **$275.3M** per FY2024 10-K
- Correction: Update historical table cash figure to $275.3M for FY2024
- Impact: Historical financial table, cash runway narrative
- Severity: MATERIAL — misrepresents FY2024 liquidity by approximately $505M

**E-02 — Aurora-INL Reactor Capacity in Scenario Tables (Reverse DCF, Section 4)**
- Claimed: "15 MWe (Aurora-INL pilot)" in Bull (2027), Base (2029), Bear (2031) revenue tables
- Verified: Aurora-INL first powerhouse is **75 MWe** per ANS, World Nuclear News, Oklo newsroom; September 2025 groundbreaking was for 75 MWe unit; the 15 MWe was a prior abandoned design configuration
- Correction: Update all scenario table references from "15 MWe" to "75 MWe" and recalculate associated revenue estimates
- Impact: Revenue projections for the key FCO year in each scenario are incorrect:
  - Bull 2027: $15–18M → should be ~$82.7M at full year (or ~$21M for Q4-only partial year)
  - Base 2029: $13M → should be ~$62.5M
  - Bear 2031: $10M → should be ~$50.1M
- Severity: MATERIAL — the FCO year revenue is a critical model input; understating by 4–5x understates FCO economics

**E-03 — Implied Reactor Count and GW Calculations (Reverse DCF, Section 2)**
- Claimed reactor counts (Bear: 85+, Base: ~54, Bull: ~35) and GW (6.4 GW, 4 GW, 2.6 GW) are understated relative to the stated implied revenues divided by $70.9M/reactor
- Verified correct figures:
  - Bear: ~98–99 reactors (~7.4 GW)
  - Base: ~62–63 reactors (~4.7 GW)
  - Bull: ~41 reactors (~3.1 GW)
- Severity: MATERIAL — the stated counts frame the magnitude of required execution; understating by ~15% to ~18% understates execution complexity

### Minor Errors (Noted, Corrected in Audited Files)

**E-04 — Shares Outstanding at December 31, 2025 (Overview Section 7 / Reverse DCF Section 8)**
- Claimed: "~157M" at December 31, 2025
- Verified: **160,514,103 shares** (~160.5M) per Q1 2026 10-Q comparative balance sheet
- Correction: Update to ~160.5M

**E-05 — 6-Month Dilution Percentage (Reverse DCF Section 8)**
- Claimed: "+10.8%" dilution Dec 2025 to June 2026
- Verified: (173.87M – 160.51M) / 160.51M = **+8.3%**
- Correction: Update to +8.3%

---

## SECTION-BY-SECTION VERDICTS

| Report Section | Verdict | Key Finding |
| :--- | :--- | :--- |
| Overview §1 — Quick Snapshot & Valuation Metrics | PASS | All current market metrics verified |
| Overview §2 — Latest Earnings & Financial Health | CONDITIONAL PASS | Q1 2026 financials fully verified; FY2024 year-end cash is incorrect (E-01); FY2025 year-end cash is correct |
| Overview §3 — Business Model & Economic Moat | PASS | No quantitative claims requiring correction; qualitative analysis is sound |
| Overview §4 — TAM/SAM/SOM | PASS | Market projections and SOM estimates are within range of cited sources |
| Overview §5 — Forward Guidance & Catalysts | PASS | All guidance figures and milestone dates verified |
| Overview §6 — Earnings Forecast Table | PASS | Historical figures correct (except E-01 reflected in cash column of §2); forward estimates appropriately disclosed as speculative |
| Overview §7 — Investment Risks | PASS | All risk characterizations verified and balanced |
| Overview §8 — Analyst Consensus | PASS | 23 analysts, Buy consensus, mean $88.63 corroborated by S&P Global data (~$88.89 minor variance) |
| Overview §9 — References | PASS | Source citations are specific, verifiable, and consistent with content |
| Reverse DCF — Capital Structure Data | PASS | All figures verified against Q1 2026 10-Q |
| Reverse DCF §1 — Implied Revenue Summary | PASS | Revenue ranges correct; narrative description accurate |
| Reverse DCF §2 — Implied Revenue Table | CONDITIONAL PASS | Formula and revenue figures correct; reactor count/GW figures understated (E-03) |
| Reverse DCF §3 — Risk-Adjusted Revenue | PASS | Probability assignments and arithmetic verified; conclusions coherent |
| Reverse DCF §4 — Three Scenarios | CONDITIONAL PASS | Scenario structure sound; Aurora-INL capacity wrong in all three tables (E-02); revenue for FCO year cascades incorrect |
| Reverse DCF §5 — TAM Reality Check | PASS | TAM figures and market share math verified |
| Reverse DCF §6 — Revenue Per Employee | PASS | Benchmarks and classification are reasonable |
| Reverse DCF §7–11 | PASS | Qualitative/framework sections; no quantitative errors found |
| Reverse DCF §8 — Dilution & SBC Analysis | CONDITIONAL PASS | SBC and total dilution verified; base Dec 2025 share count and 6-month dilution % incorrect (E-04, E-05) |
| Reverse DCF §12–18 | PASS | Conclusions, milestones, risk table, and judgment call are coherent and supported |

---

## OVERALL VERDICT

**CONDITIONAL PASS — CORRECTIONS REQUIRED**

The two Valerie OKLO reports are materially reliable on current data (Q1 2026 balance sheet, operating metrics, pipeline, regulatory milestones, and reverse DCF framework). Three material errors and two minor errors have been identified and corrected in the audited files. The analytical framework — reverse DCF methodology, risk-adjusted revenue, scenario structure, and investment judgment — is sound and internally consistent once the underlying data errors are resolved.

**The reports may not be published in unedited form.** Corrected versions (`03_Valerie_OKLO_Overview_AUDITED.md`, `03_Valerie_OKLO_ReverseDCF_AUDITED.md`) supersede the originals.

---

*Christian — The Forensic Auditor | June 20, 2026*
*Primary verification sources: SEC EDGAR (oklo-20260331.htm, oklo-20251231.htm, oklo-20241231.htm); Oklo.com newsroom; ANS Nuclear Newswire; World Nuclear News; StockAnalysis.com; StockTitan.net; PRNewswire (Centrus LOI, June 18, 2026); BusinessWire (NRC PDC approval, May 6, 2026; Atomic Alchemy NRC license, March 17, 2026).*

**One-line overall verdict: CONDITIONAL PASS — three material errors corrected (FY2024 cash overstated by ~$505M, Aurora-INL capacity misidentified as 15 MWe vs. actual 75 MWe, reactor count calculations systematically understated) and two minor dilution-figure errors corrected; all current financial metrics, pipeline claims, regulatory milestones, and reverse DCF mathematics are independently verified.**

---
**Links:** [[00_OKLO_Hub|⬅️ Back to OKLO Stock Hub]]
