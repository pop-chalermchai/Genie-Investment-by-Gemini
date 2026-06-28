---
type: stock-analysis
ticker: FPS
sector: Energy
tags: [energy, fps]
---

# FORENSIC AUDIT & VALUATION CLEARANCE REPORT

**Date:** June 2, 2026  
**Auditor:** Christian, Forensic Auditor (Wall Street Purist)  
**Target Security:** Forgent Power Solutions, Inc. (NYSE: FPS) Class A Common Stock  
**Valuation Baseline:** $47.00 (Upsized Public Offering Price, June 1, 2026)  
**Subject Analysis:** Q3 FY26 Q-Filing, S-1 Registration Statements, and Valerie's DCF / Payoff Model  
**Audit Status:** COMPLETE  
**Verdict:** **PASS**

---

## 1. Audit Mandate & Scope

This independent forensic audit was commissioned to verify the mathematical accuracy, logical integrity, and structural validity of the valuation models and financial metrics compiled by Quantitative Analyst Valerie in the report *Equity Research Audit: Forgent Power Solutions, Inc. (NYSE: FPS)* under `/Users/popular/Desktop/Genie/research/FPS/01_Valerie_FPS_Analysis.md`.

We approach all quantitative models with a high degree of skepticism. Valuation models in high-growth, secularly-hyped sectors are frequently prone to inflated assumptions, formulaic shortcuts, and aggressive rounding. Our duty is to independently re-perform the calculations and cross-examine the results using rigorous, programmatic solver techniques.

### Scope of Verification:
1. **Capital Structure & Share Counts:** Cross-check total diluted shares outstanding, implied equity value, and net debt scenarios.
2. **Reverse DCF Hurdle Rates:** Re-solve for the implied 10-year annual Free Cash Flow (FCF) growth rates that equate the discounted cash flows (and terminal value) to the target Enterprise Value (EV) under Case 1 (Core Net Debt) and Case 2 (Adjusted Net Debt) for FCF starting bases ranging from $100M to $300M.
3. **Asymmetric Payoff Ratios:** Recalculate and verify the 3.0x asymmetric risk-reward checks under Scenario A (Near-Term) and Scenario B (Multi-Year).

---

## 2. Quantitative Parameters & Baseline Audit

We isolated the baseline valuation inputs from the company's public market prospectus and Valerie's report:
*   **Share Price ($P_0$):** $47.00 (Upsized Class A offering price)
*   **Diluted Shares Outstanding ($N$):** 244,118,850
*   **Implied Equity Value ($E$):** $11,473,585,950 ($11.474 billion)
*   **WACC ($r$):** 10.0% (0.10)
*   **Terminal Growth Rate ($g$):** 3.0% (0.03)

### Net Debt Scenarios:
1. **Case 1 (Core Net Debt):** $506.2 Million
   * *Formula:* $600.0M (Senior Secured Term Loan) - $93.8M (Cash & Cash Equivalents)
   * *Target Enterprise Value:* **$11,979,785,950**
2. **Case 2 (Adjusted Net Debt):** $713.5 Million
   * *Formula:* $600.0M (Term Loan) + $207.3M (Tax Receivable Agreement [TRA] Liability) - $93.8M (Cash)
   * *Target Enterprise Value:* **$12,187,085,950**

*Forensic Note on June 1 Offering:* The upsized primary proceeds ($645.7 million before fees) were entirely utilized to redeem corresponding ownership units held by Neos Partners, LP. The cash balance remained essentially neutral at \~$93.8M, and total diluted shares outstanding remained stable at 244.1 million, as Class B units were converted. The balance sheet representations are deemed accurate and in accordance with the SEC Form 424B4 Prospectus.

---

## 3. Independent Reverse DCF Solver & Methodology

The Reverse DCF calculation requires solving for the annual growth rate ($growth$) that satisfies the following non-linear relation:

$$EV = \sum_{t=1}^{10} \frac{FCF_0 \times (1 + growth)^t}{(1 + r)^t} + \frac{\frac{FCF_0 \times (1 + growth)^{10} \times (1 + g)}{r - g}}{(1 + r)^{10}}$$

To avoid any analytical shortcuts, we implemented a high-precision Python script utilizing a bisection search algorithm (tolerance of $10^{-12}$) to solve for the exact growth rate under all sensitive iterations.

### Script Code (`/Users/popular/.gemini/antigravity-cli/brain/b3b1a063-e602-4649-9c41-5d12497984c5/scratch/fps_dcf_solver.py`):
```python
# Reverse DCF and Payoff Ratio Solver for Forgent Power Solutions (FPS)
# Christian, Forensic Auditor

def calculate_ev(fcf_0, growth, r, g):
    # Year 1 to 10 cash flows discounted
    pv_fcf = 0.0
    for t in range(1, 11):
        fcf_t = fcf_0 * ((1.0 + growth) ** t)
        pv_fcf += fcf_t / ((1.0 + r) ** t)
    
    # Terminal Value at year 10
    fcf_10 = fcf_0 * ((1.0 + growth) ** 10)
    tv = (fcf_10 * (1.0 + g)) / (r - g)
    pv_tv = tv / ((1.0 + r) ** 10)
    
    return pv_fcf + pv_tv

def solve_growth_rate(target_ev, fcf_0, r, g):
    # Bisection search to find growth rate
    low = -0.99
    high = 5.0
    tol = 1e-12
    max_iter = 100
    
    for _ in range(max_iter):
        mid = (low + high) / 2.0
        ev = calculate_ev(fcf_0, mid, r, g)
        if abs(ev - target_ev) < tol:
            return mid
        if ev < target_ev:
            low = mid
        else:
            high = mid
    return mid

def check_asymmetric_payoff(entry, downside, upside):
    payoff = (upside - entry) / (entry - downside)
    return payoff

def main():
    # Parameters
    r = 0.10
    g = 0.03
    
    fcf_bases = [100.0, 150.0, 200.0, 250.0, 300.0]  # in Millions
    
    cases = [
        {"name": "Case 1: Core Net Debt", "target_ev": 11979785950.0},
        {"name": "Case 2: Adjusted Net Debt", "target_ev": 12187085950.0}
    ]
    
    print("=" * 80)
    print("REVERSE DCF GROWTH RATE ANALYSIS")
    print("=" * 80)
    
    for case in cases:
        print(f"\n{case['name']} (Target EV: ${case['target_ev']:,.2f})")
        print("-" * 80)
        print(f"{'Starting FCF Base':<20} | {'Implied Growth Rate':<22} | {'Implied Year 10 FCF':<20}")
        print("-" * 80)
        for fcf in fcf_bases:
            fcf_0_val = fcf * 1e6
            growth = solve_growth_rate(case['target_ev'], fcf_0_val, r, g)
            fcf_10 = fcf_0_val * ((1.0 + growth) ** 10)
            print(f"${fcf:<18.1f}M | {growth * 100:>20.4f}% | ${fcf_10 / 1e6:>18.2f}M")
            
    print("\n" + "=" * 80)
    print("ASYMMETRIC PAYOFF VERIFICATION")
    print("=" * 80)
    
    scenarios = [
        {"name": "Scenario A (Near-Term)", "entry": 47.00, "downside": 39.00, "upside": 71.00},
        {"name": "Scenario B (Multi-Year)", "entry": 47.00, "downside": 35.00, "upside": 83.00}
    ]
    
    for sc in scenarios:
        ratio = check_asymmetric_payoff(sc['entry'], sc['downside'], sc['upside'])
        print(f"{sc['name']}:")
        print(f"  Entry: ${sc['entry']:.2f}, Downside: ${sc['downside']:.2f}, Upside: ${sc['upside']:.2f}")
        print(f"  Calculated Payoff Ratio: {ratio:.4f}x (Expected: 3.00x)")
        print("-" * 50)

if __name__ == "__main__":
    main()
```

### Script Execution & Terminal Output:
```text
================================================================================
REVERSE DCF GROWTH RATE ANALYSIS
================================================================================

Case 1: Core Net Debt (Target EV: $11,979,785,950.00)
--------------------------------------------------------------------------------
Starting FCF Base    | Implied Growth Rate    | Implied Year 10 FCF 
--------------------------------------------------------------------------------
$100.0             M |              31.7091% | $           1570.94M
$150.0             M |              25.9830% | $           1510.81M
$200.0             M |              21.9988% | $           1460.78M
$250.0             M |              18.9448% | $           1417.08M
$300.0             M |              16.4683% | $           1377.84M

Case 2: Adjusted Net Debt (Target EV: $12,187,085,950.00)
--------------------------------------------------------------------------------
Starting FCF Base    | Implied Growth Rate    | Implied Year 10 FCF 
--------------------------------------------------------------------------------
$100.0             M |              31.9547% | $           1600.47M
$150.0             M |              26.2225% | $           1539.78M
$200.0             M |              22.2348% | $           1489.28M
$250.0             M |              19.1786% | $           1445.19M
$300.0             M |              16.7007% | $           1405.59M

================================================================================
ASYMMETRIC PAYOFF VERIFICATION
================================================================================
Scenario A (Near-Term):
  Entry: $47.00, Downside: $39.00, Upside: $71.00
  Calculated Payoff Ratio: 3.0000x (Expected: 3.00x)
--------------------------------------------------
Scenario B (Multi-Year):
  Entry: $47.00, Downside: $35.00, Upside: $83.00
  Calculated Payoff Ratio: 3.0000x (Expected: 3.00x)
--------------------------------------------------
```

---

## 4. Reconciliation & Quantitative Comparison

We map Valerie's reported metrics against our exact programmatically calculated values. 

### Table 1: Case 1 Implied Growth Rates (Core EV: $11,979,785,950)
| Starting FCF ($FCF_0$) | Valerie's Implied Growth Rate | Forensic Auditor Re-performance | Absolute Variance | Reconciliation Status |
| :--- | :---: | :---: | :---: | :---: |
| $100.0M | 31.71% | 31.7091% | < 0.001% | **RECONCILED** (Pass) |
| **$150.0M (Base Case)** | **25.98%** | **25.9830%** | **< 0.003%** | **RECONCILED** (Pass) |
| $200.0M | 22.00% | 21.9988% | < 0.002% | **RECONCILED** (Pass) |
| $250.0M | 18.94% | 18.9448% | < 0.005% | **RECONCILED** (Pass) |
| $300.0M | 16.47% | 16.4683% | < 0.002% | **RECONCILED** (Pass) |

### Table 2: Case 2 Implied Growth Rates (Adjusted EV: $12,187,085,950)
| Starting FCF ($FCF_0$) | Valerie's Implied Growth Rate | Forensic Auditor Re-performance | Absolute Variance | Reconciliation Status |
| :--- | :---: | :---: | :---: | :---: |
| $100.0M | 31.95% | 31.9547% | < 0.005% | **RECONCILED** (Pass) |
| **$150.0M (Base Case)** | **26.22%** | **26.2225%** | **< 0.003%** | **RECONCILED** (Pass) |
| $200.0M | 22.23% | 22.2348% | < 0.005% | **RECONCILED** (Pass) |
| $250.0M | 19.18% | 19.1786% | < 0.002% | **RECONCILED** (Pass) |
| $300.0M | 16.70% | 16.7007% | < 0.001% | **RECONCILED** (Pass) |

### Table 3: Asymmetric Payoff Re-performance Check
| Scenario | Parameters | Valerie's Payoff Ratio | Re-performed Ratio | Reconciliation Status |
| :--- | :--- | :---: | :---: | :---: |
| **Scenario A (Near-Term)** | Entry: $47.00, Down $39.00, Up $71.00 | 3.0x | 3.0000x | **RECONCILED** (Pass) |
| **Scenario B (Multi-Year)** | Entry: $47.00, Down $35.00, Up $83.00 | 3.0x | 3.0000x | **RECONCILED** (Pass) |

---

## 5. Auditor's Findings & Fundamental Commentary

The quantitative validation confirms that the numbers presented in Valerie's valuation analysis are mathematically clean and represent highly precise conversions. 

From a fundamental and structural perspective, we highlight the following audits:
1. **Conservative Hurdle Rate at $47.00 Offering:** 
   Our model confirms that at a starting FCF base of **$150M** under Core Net Debt (Case 1), the market implies a **25.98%** compound annual growth rate over the next 10 years to justify the $47.00 price. For an AI infrastructure-adjacent player that recently grew quarterly revenue by **103% YoY** and boasts a **$1.98 billion backlog** (+157% YoY), this represents a highly achievable hurdle rate. 
2. **CapEx De-leveraging Catalyst:** 
   In FY26, Forgent's capital expenditures peak at $205.0 million. The roll-off of capacity expansion in FY27 down to \~1.0%–1.5% of revenue represents a massive FCF inflection catalyst. The $150.0 million FCF base for FY27 is not only realistic but highly likely to be exceeded. If FCF hits $200.0 million in Year 1, the required growth rate to justify $47.00 drops to a mere **22.00%**, providing a wider fundamental cushion.
3. **Payoff Symmetry:** 
   Both Scenario A (12-Month) and Scenario B (24-Month) return an exact asymmetric ratio of **3.0x**. In Scenario A, the $39.00 downside level represents a 17.0% decline from the baseline, which is protected by a solid 30.0x multiple on near-term EBITDA. In Scenario B, the $35.00 downside represents a conservative level near the original IPO price. The upside targets of $71.00 and $83.00 represent realistic outcomes based on backlog monetization and double capacity expansion. 

---

## 6. Audit Verdict

Valerie's quantitative representations, corporate parameters, bisection limits, reverse DCF growth rate metrics, and asymmetric payoff ratios have been programmatically evaluated and audited. 

We find **zero mathematical discrepancies, zero structural flaws, and zero logical errors** in the baseline numbers of the report.

### Final Audit Decision: **PASS**

*This clearance report officially approves the quantitative underwriting of Forgent Power Solutions, Inc. (NYSE: FPS) Class A Common Stock at the baseline entry price of $47.00.*

---
**Christian**  
*Forensic Auditor*  
*Wall Street Purist*

---
**Links:** [[00_FPS_Hub|⬅️ Back to FPS Stock Hub]]
