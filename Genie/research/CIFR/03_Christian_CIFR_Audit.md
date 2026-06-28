# CIFR Forensic Audit Report
### Auditor: Christian (The Forensic Auditor) | Date: June 20, 2026
### Subject: Valerie's Equity Research Reports — Cipher Digital Inc. (NASDAQ: CIFR)
### Files Audited:
- `01_Valerie_CIFR_Overview.md`
- `02_Valerie_CIFR_ReverseDCF.md`

---

## AUDIT METHODOLOGY

Independent verification conducted against the following primary sources:
- Cipher Digital Inc. Form 10-Q (Q1 FY2026, March 31, 2026) — SEC EDGAR
- Cipher Mining Q1 2026 Earnings Call Transcript (The Motley Fool, May 5, 2026)
- Cipher Digital Q1 2026 8-K Earnings Press Release (SEC.gov, May 5, 2026)
- StockAnalysis.com — CIFR consensus data, June 20, 2026
- GlobeNewswire / investors.ciphermining.com — official press releases
- BitcoinTreasuries.net / SEC filing confirmations
- CoinDesk BTC price feed, June 20, 2026
- VanEck research report, June 2026

All arithmetic has been independently recalculated where figures are verifiable.

---

## SECTION 1: OVERVIEW REPORT — Key Financial Figures

**Verdict: CONDITIONAL PASS**

### Items Verified — PASS

| Claim | Verified Value | Status |
| :--- | :--- | :--- |
| Stock Price: $29.18 | $29.18 (June 18/20, 2026 close) | PASS |
| BTC Price: ~$63,700 | $63,675.74 as of June 20, 2026 (CoinDesk) | PASS |
| Q1 2026 Revenue: $34.8M | $34.84M (10-Q confirmed) | PASS |
| Q4 2025 Revenue: $59.7M | ~$60M (earnings call); minor rounding | PASS |
| GAAP Net Loss Q1: -$114.3M (-$0.28/share) | $114.32M loss, -$0.28 EPS (10-Q) | PASS |
| Adj. EBITDA Q1: -$48M | Confirmed -$48M (8-K press release) | PASS |
| Operating Cash Flow Q1: +$91.5M | $91.5M (10-Q confirmed) | PASS |
| Q1 CapEx: $554M | $554.0M (10-Q confirmed) | PASS |
| Unrestricted Cash: $715M | $715.2M (10-Q confirmed) | PASS |
| Total Debt (Principal): $5.2B | $5.21B (10-Q confirmed) | PASS |
| Total Cash (Restricted + Unrestricted): ~$4.25B | $4,246.3M (10-Q confirmed) | PASS |
| Total Contracted Revenue: $11.4B | Confirmed (Q1 earnings slides) | PASS |
| AWS / Black Pearl TCV: ~$5.5B | Confirmed — 15-year, 300 MW (SEC 8-K, press releases) | PASS |
| AWS / Black Pearl: 15-year, 300 MW | Confirmed | PASS |
| Stingray: 70 MW, AWS-backed | Confirmed — 70 MW critical IT load (8-K June 2026) | PASS |
| Stingray: $810M notes at 6.0% | Confirmed — Stingray Compute LLC, 6.000% notes due 2031 | PASS |
| Odessa Hashrate: 11.6 EH/s | Confirmed (Q1 2026 10-Q, earnings call) | PASS |
| Hashrate efficiency: 17.2 J/TH | Confirmed (Q1 2026 earnings call) | PASS |
| Power cost: $0.028/kWh | Confirmed — fixed-price Odessa PPA | PASS |
| BTC Mined Q1: 346 BTC | Confirmed (10-Q, earnings call) | PASS |
| Operating Capacity (Mining): 207 MW | Confirmed — Odessa only | PASS |
| NOI Average (2026–2036): $787M/yr | Confirmed (Q1 2026 earnings slides) | PASS |
| NOI 2027E: $646M | Confirmed (Q1 2026 earnings slides) | PASS |
| NOI 2035E: $892M | Confirmed (Q1 2026 earnings slides) | PASS |
| 4.2 GW total grid-approved pipeline | Confirmed — 907 MW contracted + 3.3 GW pipeline | PASS |
| Colchis JV: 1 GW, West Texas | Confirmed — joint entity announced Q3 2025 | PASS |
| FY2024 Revenue: $151.3M | Confirmed | PASS |
| FY2025 Revenue: $223.9M | Confirmed | PASS |
| 52-Week Range: $3.29 – $30.01 | Confirmed — $3.29 low (June 23, 2025); $30.01 high (June 3, 2026) | PASS |
| YoY Stock Return: +759.7% | Confirmed (StockAnalysis, CompaniesMarketCap) | PASS |
| Market Cap: ~$11.94B | Confirmed at $29.18 × 409.05M shares | PASS |
| Analyst Consensus: Strong Buy | Confirmed — 16 analysts, Strong Buy (StockAnalysis S&P Global) | PASS |
| Consensus Mean PT: $32.00 | Confirmed — $32.00 mean (StockAnalysis, June 2026) | PASS |
| VanEck $50B Funding Gap Warning (June 2026) | Confirmed — CoinDesk, June 16, 2026 | PASS |
| $200M Revolving Credit Facility (May 2026) | Confirmed — first corporate revolver | PASS |
| $1.7B notes at 7.125%, due 2030 | Confirmed (10-Q debt schedule) | PASS |
| $2.0B notes at 6.125%, due 2031 | Confirmed (10-Q debt schedule) | PASS |

---

### Items with EXCEPTIONS — FAIL

---

**EXCEPTION 1 — CRITICAL: Bitcoin Holdings Materially Overstated (Both Reports)**

- **Valerie Claim:** "Bitcoin Treasury: 1,807.60 BTC as of March 31, 2026 (~$115M at $63,700/BTC)"
- **Verified Fact (SEC 10-Q, March 31, 2026):** 1,116 BTC with a fair value of $76.2 million.
- **Impact:** The 1,807.60 BTC figure appears to have been sourced from BitcoinTreasuries.net, which may reflect a different date, a combined BTC+ETH treasury figure, or stale data. The authoritative source — the 10-Q filed directly with the SEC — states 1,116 BTC.
- **Dollar Value Error:** The report states ~$115M, calculated as 1,807.60 × $63,700 = $115.1M. The correct value is 1,116 × $63,700 = $71.1M, consistent with the SEC-reported fair value of $76.2M (slight BTC price variation at reporting date).
- **Magnitude of Error:** BTC holdings overstated by 691.6 BTC (+62%). USD value overstated by ~$39–44M.
- **VERDICT: FAIL — Material misstatement in both reports.**
- **Correction:** BTC Treasury = 1,116 BTC ≈ $76.2M (SEC 10-Q). All references to "1,807.60 BTC" and "~$115M" must be corrected.

---

**EXCEPTION 2 — MATERIAL: Barber Lake / Fluidstack TCV Overstated**

- **Valerie Claim (Overview, Section 3):** "Fluidstack-Google / Barber Lake (Texas): 10-year, 300 MW lease. ~$5.9B contracted revenue."
- **Valerie Claim (Overview, Section 1 table note):** Total contracted revenue $11.4B (implied $5.9B for Barber Lake given $5.5B for AWS).
- **Verified Fact:** The Barber Lake/Fluidstack contracts (two tranches):
  - Initial agreement (Sept 2025): ~$3.0B over 10-year base term (168 MW critical IT load)
  - Expansion agreement (Nov 2025): ~$830M over 10-year base term (additional 39 MW critical IT load)
  - **Combined base-term TCV: ~$3.83B** (not $5.9B)
  - Extension options would bring total to ~$9.0B — but extensions are not contracted.
- **How the $11.4B Total is Reached:** $5.5B (Black Pearl) + $3.83B (Barber Lake) + $2.0B (Stingray base) = $11.33B ≈ $11.4B. This reconciles only if Barber Lake is ~$3.83B, not $5.9B.
- **Root Cause:** $5.9B appears to conflate base-term revenue with extension option scenarios. The $9.0B figure (with full extensions) from the November 2025 announcement may have been incorrectly attributed as the base-term TCV for Barber Lake alone.
- **VERDICT: FAIL — The $5.9B Barber Lake TCV is unsupported by public filings. Correct figure is ~$3.83B base term.**
- **Correction:** "Fluidstack-Google / Barber Lake (Texas): 10-year, 300 MW lease. ~$3.83B contracted revenue (base term); up to ~$9.0B including extension options."

---

**EXCEPTION 3 — MATERIAL: Morgan Stanley Price Target Stale/Incorrect**

- **Valerie Claim:** "Morgan Stanley PT (Apr 2026): $40.50 (OW)" listed in both the header table and the analyst consensus table.
- **Verified Fact:** Morgan Stanley raised its PT on CIFR from $40.50 to $42.50 on May 19, 2026 (post-Q1 earnings), then further lowered it to $48.50 on June 3/4, 2026. As of June 20, 2026 (report date), the current Morgan Stanley PT is $48.50, not $40.50.
  - Source: GuruFocus, Benzinga analyst ratings (June 2026); StockAnalysis consensus page shows $49 from Morgan Stanley as of report date.
- **VERDICT: FAIL — The $40.50 MS target is two revisions stale. Current figure as of report date: $48.50 (most recently $49 per some aggregators).**
- **Correction:** "Morgan Stanley PT (Jun 2026): $48.50 (Overweight)" — updated to most recent available figure.

---

**EXCEPTION 4 — MATERIAL: Analyst Price Target Range Incorrect (High and Low)**

- **Valerie Claim:** "High Price Target: $53.00" and "Low Price Target: $18.00"
- **Verified Fact (StockAnalysis, S&P Global consensus, June 2026):**
  - High Target: $69
  - Low Target: $23
- **VERDICT: FAIL — Both the high and low targets are incorrect and meaningfully understated/understated the range.**
- **Correction:** High Target: $69. Low Target: $23.

---

**EXCEPTION 5 — MINOR: Shares Outstanding Discrepancy**

- **Valerie Claim:** "409.05 Million shares outstanding"
- **Verified Fact (10-Q, March 31, 2026):** 405,266,365 shares (405.27 million).
- **Context:** The 409.05M figure likely reflects shares as of a later date (possibly the earnings call date or a data feed snapshot post-period), and the difference (3.78M shares, ~0.9%) is likely due to SBC issuances or ATM activity between March 31 and the report date. The discrepancy is minor but should be noted.
- **VERDICT: MINOR FLAG — Not a material misstatement, but the 10-Q balance sheet figure differs from the reported shares outstanding. Clarification of the measurement date is required.**
- **Correction:** Note that 405.27M shares as of March 31, 2026 (10-Q); approximately 409.05M shares as of June 2026 (data feed).

---

**EXCEPTION 6 — MINOR: Debt Structure Table — Stingray Notes Timing**

- **Valerie Claim (Overview, Section 2 Debt Structure):** Lists "$810M Senior Secured Notes (Stingray data center, AWS-backed) at 6.0% — June 2026" as part of the Q1 2026 balance sheet.
- **Verified Fact:** The Stingray notes were announced June 8, 2026 — AFTER the Q1 2026 balance sheet date of March 31, 2026. These notes do not appear on the March 31 balance sheet. Total debt as of March 31, 2026 was $5.21B (pre-Stingray). The Stingray facility adds $0.81B post-quarter.
- **Impact:** The debt table conflates Q1 balance sheet figures with subsequent post-quarter financing activity, potentially creating the impression that $5.2B in debt included the Stingray notes at Q1 end — which it did not.
- **VERDICT: MINOR FLAG — Disclosure needed that the Stingray $810M notes were issued post-Q1 (June 2026) and are not included in the Q1 balance sheet total debt of $5.21B. Pro-forma debt post-Stingray: ~$6.02B.**

---

## SECTION 2: REVERSE DCF REPORT — Mathematics & Assumptions

**Verdict: CONDITIONAL PASS (core DCF math correct; power cost calculations contain material errors)**

### Items Verified — PASS

| Claim | Verified Calculation | Status |
| :--- | :--- | :--- |
| EV = ~$12.77B (MCap + Debt - Total Cash) | $11.94B + $5.21B - $4.25B = $12.90B (close; variance from rounding/BTC) | PASS |
| DCF Base: NOI = EV × (CoE - g) = $12.77B × (14% - 3%) = $1.40B | Verified: $12.77B × 0.11 = $1.405B | PASS |
| DCF Base: Revenue = $1.40B / 70% margin = $2.00B | Verified: $1.405B / 0.70 = $2.007B | PASS |
| DCF Conservative: NOI = $12.77B × (16% - 3%) = $1.66B | Verified: $12.77B × 0.13 = $1.660B | PASS |
| DCF Conservative: Revenue = $1.66B / 65% margin = $2.55B | Verified: $1.660B / 0.65 = $2.554B | PASS |
| DCF Aggressive: NOI = $12.77B × (12% - 3%) = $1.15B | Verified: $12.77B × 0.09 = $1.149B; report states $1.12B | MINOR — see below |
| EV/2027E NOI = $12.77B / $646M = 19.8x | Verified: $12.77B / $0.646B = 19.77x ≈ 19.8x | PASS |
| Interest coverage 2027: $646M NOI - $338M interest = $308M | Verified at stated inputs | PASS |
| NOI/MW = $787M / 907 MW ≈ $867K/MW | Verified: $787M / 907 = $867K/MW | PASS |
| BTC Mining Revenue Q1: 346 BTC × $63,700 = ~$22M | Verified: 346 × $63,700 = $22.04M | PASS |

---

### Items with EXCEPTIONS — FAIL

---

**EXCEPTION 7 — CRITICAL: Power Cost Calculation in Section 4 Narrative Is Wrong**

- **Valerie Claim (DCF Section 4, Sub-Model A footnote):** "207 MW × 8,760 hours × $0.028/kWh ÷ 346 BTC (approx.) = ~$146M power cost ÷ 346 BTC ≈ ~$42,200/BTC in power cost alone."
- **Correct Calculation:**
  - Annual kWh = 207,000 kW × 8,760 hours = 1,813,320,000 kWh
  - Annual power cost = 1,813,320,000 × $0.028 = **$50,773,000 ≈ $50.8M annually**
  - Quarterly power cost = $50.8M / 4 = **$12.7M per quarter**
  - Power cost per BTC = $12.7M / 346 BTC = **~$36,700/BTC**
- **Report Error:** States "$146M power cost" annually. This is 2.88× too high. The $146M figure is arithmetically unsupported — its origin is unknown. Annual power cost at 207 MW and $0.028/kWh is $50.8M, not $146M.
- **Downstream Error:** Because the narrative power cost is wrong, the stated power cost per BTC of "$42,200" is also wrong. Correct power-only cost to mine is approximately **$36,700/BTC**, and the stated all-in cost range of "$35,000–$45,000/BTC" happens to bracket the correct power-only figure but was derived from an erroneous calculation, not a correct one.
- **VERDICT: FAIL — Material arithmetic error. The "$146M power cost" figure is incorrect by a factor of ~2.88x. The correct annual electricity cost at 207 MW / $0.028/kWh is approximately $50.8M.**

---

**EXCEPTION 8 — CRITICAL: Power Cost in BTC Production Scenario Summary Table Is Wrong**

- **Valerie Claim (DCF, BTC Production Economics Scenario Summary table):** "Power Cost/Qtr: ~$5.1M" (footnoted as "207 MW × 8,760 hrs/year ÷ 4 quarters × $0.028/kWh")
- **Correct Calculation:**
  - Quarterly hours = 8,760 / 4 = 2,190 hours
  - Quarterly kWh = 207,000 kW × 2,190 hours = 453,330,000 kWh
  - Quarterly power cost = 453,330,000 × $0.028 = **$12,693,240 ≈ $12.7M per quarter**
- **Report Error:** States $5.1M/quarter. This is understated by **$7.6M (approximately 2.5× too low)**.
- **Root Cause:** The formula appears to have divided by 4 twice or used a different MW figure. The stated footnote math: 207 MW × (8,760 ÷ 4) × $0.028 = 207,000 × 2,190 × $0.028 = $12.7M. The report shows $5.1M, suggesting an error in the computation (possibly 207 MW was used as 207 — i.e., not converted to kW — or some other calculation flaw).
- **Downstream Impact:** This error causes the Gross Profit figures in the scenario table to be materially overstated. Correct quarterly gross profit figures:
  - Bear ($40K BTC): $14.0M revenue - $12.7M power = $1.3M (3.9% margin, not 64%)
  - Base ($63.7K BTC): $22.3M revenue - $12.7M power = $9.6M (43% margin, not 77%)
  - Bull ($100K BTC): $35.0M revenue - $12.7M power = $22.3M (64% margin, not 85%)
  - Peak Bull ($150K BTC): $52.5M revenue - $12.7M power = $39.8M (76% margin, not 90%)
- **Note:** These are electricity-only gross margins. Adding overhead, SG&A, and depreciation ($8–10M/quarter per Valerie's own estimate) reduces these further. The all-in "pure electricity" gross margin is far thinner than represented in the scenario table.
- **VERDICT: FAIL — The scenario table power cost is understated by ~2.5×, causing gross profit margins to be materially overstated across all scenarios.**

---

**EXCEPTION 9 — MINOR: DCF Aggressive Scenario NOI Rounding**

- **Valerie Claim:** Aggressive scenario: Implied NOI = $1.12B
- **Correct Calculation:** $12.77B × (12% - 3%) = $12.77B × 0.09 = **$1.149B**
- **Report states $1.12B** — a $29M understatement (2.5%). This appears to be a rounding error.
- **VERDICT: MINOR — Immaterial rounding error. Correct figure: $1.15B.**

---

**EXCEPTION 10 — MINOR: EV Figure Inconsistency Between Reports**

- **Overview Report (Section 1):** "EV ~$16.9 Billion" (calculated using only unrestricted cash as the cash offset)
- **DCF Report (Key Input Data):** "EV ~$12.77 Billion" (calculated using total cash including restricted)
- **Assessment:** Both methodologies are disclosed in the DCF report's EV Note, and neither is arithmetically incorrect given their stated assumptions. However, the Overview Report presents $16.9B as the primary EV without disclosing the methodology, while the DCF report uses a different figure without cross-referencing the overview. This creates reader confusion and inconsistency across the two documents.
- **Standard Practice:** Enterprise Value in investment banking convention uses total cash (restricted + unrestricted) unless the restriction is permanent and legally impairs access. Construction escrow cash is time-restricted but ultimately accessible — the debate is legitimate. The DCF's $12.77B EV is more technically defensible; the Overview's $16.9B represents a more conservative (higher EV) view.
- **Recommended Resolution:** Both reports should use the same primary EV figure with explicit methodology disclosure, and cross-reference each other.
- **VERDICT: MINOR — No arithmetic error, but inconsistency across documents requires disclosure alignment.**

---

**EXCEPTION 11 — MINOR: BTC Holdings Error Propagated to DCF Report**

- **DCF Report (Key Input Data table):** "BTC Holdings (1,807.60 BTC @ $63,700) = ~$115 Million"
- **Correct (SEC 10-Q):** 1,116 BTC at fair value $76.2M
- **Same error as Exception 1, propagated into DCF report.**
- **VERDICT: FAIL (same as Exception 1) — applies to DCF report as well.**

---

## SECTION 3: INPUT DATA FRESHNESS CHECK

**Verdict: CONDITIONAL PASS**

| Data Point | Report Date Claimed | Freshness Status |
| :--- | :--- | :--- |
| Stock Price ($29.18) | June 20, 2026 | CURRENT |
| BTC Price (~$63,700) | June 20, 2026 | CURRENT (confirmed $63,675) |
| Q1 2026 Financial Data | May 5, 2026 (10-Q) | CURRENT |
| Analyst Consensus ($32 mean) | June 2026 | CURRENT |
| Morgan Stanley PT ($40.50) | April 27, 2026 | STALE — superseded by $48.50 (June 2026) |
| High/Low PT Range ($18–$53) | 2026 | STALE — range is $23–$69 per June 2026 data |
| BTC Holdings (1,807.60 BTC) | March 31, 2026 | INCORRECT — 10-Q says 1,116 BTC |
| VanEck Report | June 16, 2026 | CURRENT |

---

## SUMMARY OF ALL EXCEPTIONS

| # | Severity | Location | Finding |
| :--- | :--- | :--- | :--- |
| 1 | CRITICAL | Both Reports | BTC Holdings: 1,807.60 BTC stated; 10-Q confirms 1,116 BTC. USD value overstated ~$39-44M. |
| 2 | MATERIAL | Overview, Sections 3 & 10 | Barber Lake TCV: $5.9B stated; base-term TCV is ~$3.83B per press releases. Extension-scenario value of $9B may have been conflated. |
| 3 | MATERIAL | Overview, Sections 1 & 8 | Morgan Stanley PT: $40.50 stated (April 2026 figure); current MS PT is $48.50 (June 2026). Two revisions stale. |
| 4 | MATERIAL | Overview, Sections 1 & 8 | Analyst PT range: $18–$53 stated; correct range is $23–$69. Both bounds are wrong. |
| 5 | MINOR | Overview, Section 1 | Shares: 409.05M stated vs. 405.27M in 10-Q (March 31, 2026). Likely reflects later-date data feed. |
| 6 | MINOR | Overview, Section 2 | Stingray $810M notes listed in Q1 balance sheet; these were issued post-quarter (June 8, 2026). Timing disclosure needed. |
| 7 | CRITICAL | DCF, Section 4 | Power cost narrative: "$146M annual" is wrong — correct is $50.8M. Cost per BTC understated to ~$42,200 when correct electricity cost per BTC is ~$36,700 (the final stated range of $35K–$45K brackets the right answer but is derived from a wrong intermediate calculation). |
| 8 | CRITICAL | DCF, BTC Scenario Table | Quarterly power cost: $5.1M stated; correct is $12.7M. Gross margins overstated across all BTC price scenarios. |
| 9 | MINOR | DCF, Section 2 | Aggressive scenario NOI: $1.12B stated; correct is $1.15B. Minor rounding error. |
| 10 | MINOR | Both Reports | EV inconsistency: Overview uses ~$16.9B; DCF uses ~$12.77B without cross-disclosure. Both are methodologically defensible but need alignment. |
| 11 | CRITICAL | DCF, Key Inputs | BTC Holdings: Same error as Exception 1 — propagated to DCF report. |

---

## VERIFIED ITEMS SUMMARY (NOTABLE PASSES)

The following high-stakes claims are independently confirmed and require no correction:

- Total contracted revenue: $11.4B — **CONFIRMED**
- AWS Black Pearl: $5.5B, 15-year, 300 MW — **CONFIRMED**
- Average annualized NOI $787M (2026–2036) — **CONFIRMED**
- 2027E NOI: $646M — **CONFIRMED**
- Hashrate 11.6 EH/s, 17.2 J/TH, BTC mined 346 in Q1 — **CONFIRMED**
- Odessa PPA: $0.028/kWh — **CONFIRMED**
- Total debt $5.2B; $1.7B at 7.125%, $2.0B at 6.125% — **CONFIRMED**
- Unrestricted cash $715M; restricted cash ~$3.53B; total cash $4.25B — **CONFIRMED**
- Q1 revenue $34.8M; operating CF $91.5M; CapEx $554M — **CONFIRMED**
- 52-week range $3.29–$30.01 — **CONFIRMED**
- BTC price ~$63,700 — **CONFIRMED**
- Analyst consensus: Strong Buy, $32 mean, 16 analysts — **CONFIRMED**
- Core reverse DCF math (Sections 1–3, 5–13) — **CONFIRMED**
- VanEck $50B funding gap warning, June 2026 — **CONFIRMED**

---

## OVERALL VERDICT

**FAIL**

The reports contain three critical errors that materially misstate financial figures visible to an investment decision-maker:

1. **Bitcoin holdings overstated by 62%** (1,807 BTC vs. 1,116 BTC per SEC 10-Q) — affects balance sheet integrity.
2. **Barber Lake TCV overstated by ~54%** ($5.9B vs. ~$3.83B base-term) — affects contracted revenue per-asset analysis and the tenant concentration table.
3. **Power cost calculation errors** in the DCF are structurally wrong: the narrative claims $146M in annual power costs (correct: $50.8M), and the BTC scenario table uses $5.1M/quarter in power costs (correct: $12.7M), causing mining gross margins across all scenarios to be materially overstated.

The remaining errors (stale analyst price targets, minor share count variance, EV disclosure inconsistency) are correctable without altering the core investment thesis.

The structural logic, NOI projections, contract terms, debt structure, and overall investment conclusion (SPECULATIVE BUY at $29.18 with $32 target) are directionally sound and supported by primary sources. However, no report containing critical arithmetic errors in mining economics and a material overstatement of a primary contracted asset value may be issued without correction.

**Corrected files have been issued as:**
- `03_Valerie_CIFR_Overview_AUDITED.md`
- `03_Valerie_CIFR_ReverseDCF_AUDITED.md`

---

*Audit conducted by Christian (The Forensic Auditor) — Genie Research Platform | June 20, 2026*
*All figures verified against SEC EDGAR filings, official press releases, and market data providers.*
*Every figure in this report is wrong until independently verified — and in several cases, it was.*

---
**Links:** [[00_CIFR_Hub|⬅️ Back to CIFR Stock Hub]]
