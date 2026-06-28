---
type: stock-analysis
ticker: FLY
sector: Aerospace
tags: [aerospace, fly]
---

# Reverse DCF Analysis: Firefly Aerospace, Inc. (FLY)

## Mandatory Assumption Disclosure
This analysis uses:
* Single-stage Gordon Growth Model (to solve for steady-state revenue)
* Multi-stage Discounted Cash Flow model (to solve for 10-year implied FCF growth rate)
* Steady-state economics
* Long-term margin assumptions
* Current capital structure
* No speculative optionality valuation unless disclosed

**Business Profile:** Space Infrastructure & Launch Services (Defense / Commercial Spaceflight)
Firefly Aerospace operates in the space infrastructure sector, specializing in small-to-medium lift orbital launch vehicles (Alpha, Eclipse), spacecraft propulsion (Miranda engines), and lunar logistics (Blue Ghost lander program).

---

## Section 1 — Reverse DCF Summary
**What must this company become over the next 5–10 years?**
* **Revenue scale:** Must scale from its current $184.88M TTM revenue to $2.53B in steady-state annual revenue under base-case assumptions.
* **Market position:** Must establish itself as the leading commercial provider of medium-lift launch services (Eclipse) alongside Rocket Lab and SpaceX, and the primary commercial lunar lander supplier.
* **Geographic scale:** Requires fully operational, high-throughput launch complexes at Cape Canaveral (SLC-20) and Vandenberg (SLC-2W), alongside scaled manufacturing facilities in Briggs, TX.
* **Margin profile:** Must achieve and sustain long-term Free Cash Flow margins of 20%, reflecting highly optimized manufacturing and high-margin engine supply contracts.
* **Competitive position:** Needs to maintain its strategic partnership with Northrop Grumman to secure consistent defense-related launch and engine supply backlogs.

---

## Section 2 — Implied Revenue
Implied Revenue = EV × (CoE − g) ÷ FCF Margin
*(Assuming Current EV = $4,600.56 Million)*

| Scenario | EV | CoE | g | Margin | Implied Revenue |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Conservative | $4,600.56M | 16% | 3% | 15% | $3,987.15M |
| Base | $4,600.56M | 14% | 3% | 20% | $2,530.31M |
| Aggressive | $4,600.56M | 12% | 3% | 25% | $1,656.20M |

**Explanation:** Under the Base scenario, to justify its current EV of $4.60B, Firefly must eventually generate $2.53B in steady-state annual revenue at a 20% FCF margin.

---

## Section 2b — 10-Year Implied FCF Growth Solver (Multi-Stage DCF)
To address the user's specific request, we solve for the implied 10-year annual FCF growth rate ($g_{implied}$) required to justify the current valuation. 

We model three starting FCF scenarios ($FCF_0$) under a 14.0% WACC (CoE) and a 3.0% terminal growth rate ($g_{terminal}$):
1. **Conservative:** $25.0 Million FCF base (assuming initial positive FCF inflection)
2. **Base:** $50.0 Million FCF base (representing mid-cycle FCF conversion)
3. **Optimistic:** $75.0 Million FCF base (assuming rapid FCF inflection)

Since FLY holds a significant Net Cash position ($498.64 Million), we calculate the growth rates required to justify both the Enterprise Value ($4,600.56 Million) and the Market Capitalization ($5,099.20 Million):

### Target 1: Enterprise Value = $4,600.56 Million
* **Scenario 1 ($FCF_0 = $25.0M):** $g_{implied}$ = **48.16%**
* **Scenario 2 ($FCF_0 = $50.0M):** $g_{implied}$ = **37.29%**
* **Scenario 3 ($FCF_0 = $75.0M):** $g_{implied}$ = **31.13%**

### Target 2: Market Capitalization = $5,099.20 Million
* **Scenario 1 ($FCF_0 = $25.0M):** $g_{implied}$ = **49.82%**
* **Scenario 2 ($FCF_0 = $50.0M):** $g_{implied}$ = **38.87%**
* **Scenario 3 ($FCF_0 = $75.0M):** $g_{implied}$ = **32.68%**

**Analysis:** Even under the optimistic $75.0M starting FCF base, Firefly must grow its FCF by **31.13% to 32.68%** annually for the next 10 years to support the current valuation. Under the base scenario ($50.0M $FCF_0$), the implied growth requirement is **37.29% to 38.87%**, highlighting a demanding growth profile.

---

## Section 3 — Risk Adjusted Revenue
Risk Adjusted Revenue = Implied Revenue ÷ Probability

| Scenario | Implied Revenue | Probability | Risk Adjusted Revenue |
| :--- | :--- | :--- | :--- |
| Conservative | $3,987.15M | 50% | $7,974.30M |
| Base | $2,530.31M | 70% | $3,614.73M |
| Aggressive | $1,656.20M | 100% | $1,656.20M |

**Explanation:** Operational execution risk is high in aerospace. Factoring in a 70% probability of successfully scaling to a steady-state business model in the Base scenario, the market is effectively pricing in a risk-adjusted revenue requirement of $3.61B.

---

## Section 4 — KPI Translation
To achieve the Base scenario implied revenue of $2,530.31 Million, Firefly’s operational output at steady state must scale to the following:

* **Launch Services (Alpha):** 15 launches per year at $15M ASP = **$225.0 Million**
* **Launch Services (Eclipse):** 20 launches per year at $55M ASP = **$1,100.0 Million**
* **Spacecraft Solutions (Blue Ghost):** 4 lunar missions per year at $150M ASP = **$600.0 Million**
* **Propulsion Supply (Miranda):** 12 engine sets per year supplied to Northrop Grumman at $10M ASP = **$120.0 Million**
* **Defense & Spacecraft Programs (Forge / Golden Dome):** Backlog billing of **$485.31 Million**
* **Total Steady-State Revenue:** **$2,530.31 Million**

*If these assumptions fail, what must compensate?*
If the Eclipse medium-lift vehicle experiences developmental delays or launch failures, Firefly must either scale its small-lift Alpha launch cadence to over 100 flights per year, or increase Blue Ghost lunar mission pricing to over $400 Million per mission to meet the base revenue target. Neither alternative is operationally or commercially feasible.

---

## Section 5 — TAM Reality Check
Required Market Share = Implied Revenue ÷ TAM

| TAM | Required Revenue | Required Market Share |
| :--- | :--- | :--- |
| $40,000M | $2,530.31M | 6.33% |

*TAM Estimate represents the projected global commercial launch and lunar logistics market by FY2035.*

Classify: **Reasonable (5–15%)**

**Discuss:**
* **TAM quality:** Moderate. Highly dependent on government agency budgets (NASA CLPS, U.S. Space Force) and the roll-out of commercial satellite constellations.
* **TAM inflation risk:** High. Space sector TAMs are frequently over-optimistic regarding the pace of commercial lunar and orbital habitat development.
* **Competition intensity:** Extreme. The launch market is dominated by SpaceX (Falcon 9/Starship), with Rocket Lab (Neutron) competing directly in the medium-lift class.

---

## Section 6 — Revenue Per Employee Check
Revenue per Employee = $2,530.31 Million ÷ 1,500 (projected steady-state headcount) = **$1.69 Million**

Compare with:
* Elite SaaS: \~$1.0M
* Semiconductor Leaders: \~$2.0M
* Infrastructure/Space Leaders (Rocket Lab / Northrop Grumman): \~$400k – $500k

Assess: **Aggressive**
* Space manufacturing is highly labor-intensive (requiring assembly technicians, quality assurance, and launch crew). Achieving $1.69M per employee would require unprecedented automation in rocket manufacturing, far exceeding current industry standards (\~$400k for Rocket Lab).

---

## Section 7 — Rule of 40 Assessment
Rule of 40 = Revenue Growth + FCF Margin
* Implied Growth (Base Case 10-Yr FCF growth): **37.29%**
* FCF Margin: **20.0%**
* Total Score: **57.29**

| Score | Interpretation |
| :--- | :--- |
| >50 | **Exceptional** |

**Discuss sustainability:** Highly unsustainable. Growing at 37% CAGR while maintaining a 20% FCF margin is virtually impossible in a capital-intensive aerospace business, as high growth requires continuous, heavy CapEx reinvestment.

---

## Section 8 — Dilution & SBC Analysis
* **SBC % Revenue:** \~8.0% (Estimated)
* **Dilution Rate:** \~6.0% (Reflecting recent May 2026 equity offering to fund Eclipse development)

Classify: **Moderate** to **High**

**Discuss:** Ongoing dilution is a persistent headwind for space stocks. While the company's net cash position ($498.64 Million) provides a cushion, any major delay in the Eclipse program will necessitate further capital raises, diluting existing shareholders.

---

## Section 9 — Capital Intensity
* Capex requirements: Very High (launch pads, engine test stands, composite autoclaves)
* Manufacturing investment: High
* Data center investment: Low
* Inventory requirements: High

Classify: **Capital-intensive**

**Discuss impact on long-term margins:** Tremendous upfront CapEx is required before achieving launch cadence scale. This structurally depresses ROIC and early-stage FCF margins, meaning positive FCF generation is deferred until the late 2020s.

---

## Section 10 — Customer Concentration
* Largest customers: Northrop Grumman, NASA, U.S. Space Force
* Revenue concentration: **High (>25%)** (These three clients represent >50% of the company's current backlog)

**Discuss vulnerability:** High vulnerability. A policy shift at NASA regarding lunar exploration, or a change in Northrop Grumman's Antares 330 launcher roadmap, would severely impact Firefly's revenue backlog.

---

## Section 11 — Competitive Moat
* Network effects: None
* Switching costs: Moderate (defense payload integrations require long certification processes)
* Brand: Weak (early-stage public entity)
* Scale advantage: Moderate (strategic backing from Northrop Grumman provides co-development funding)
* Cost advantage: Moderate (proprietary carbon-composite structures lower vehicle mass and cost)
* Proprietary technology: Moderate (Miranda engine, carbon-composite fabrication)

Classify moat: **Moderate**

**Explain:** Firefly does not possess a wide moat, but its strategic alignment with Northrop Grumman and active flight heritage with Alpha provide a defensible niche that protects it from pre-revenue launch startups.

---

## Section 12 — Sanity Check
Assess whether implied outcomes are: **Difficult** to **Very Difficult**

Identify primary bottlenecks:
* Execution (medium-lift vehicle development and engine qualification)
* Competition (SpaceX pricing pressure and Rocket Lab's Neutron)
* Capital (managing cash burn before Eclipse generates positive cash flow)

---

## Section 13 — Market Expectations
**Which scenario is currently priced in?**
**Base to Bull (Aggressive)**

**Support with evidence:** The current market cap of $5.10 Billion and EV of $4.60 Billion requires Firefly to scale to $2.53 Billion in revenue at a 20% FCF margin, or achieve an annual FCF growth rate of 37% to 39% over the next decade from a $50M base. The market is pricing in flawless execution of the Eclipse vehicle and repeated success in the lunar division, leaving no margin for technical anomalies.

---

## Section 14 — Analyst View
Choose: **Speculative Buy**

**Justify using:** The valuation is demanding (11.7x Forward P/S) and execution difficulty is high. However, the strategic partnership with Northrop Grumman and the established Spacecraft Solutions segment (Blue Ghost) provide a real path to commercial scaling that differentiates FLY from other speculative space companies. It is a Speculative Buy for investors with high risk tolerance.

---

## Section 15 — Milestones

**Leading Indicators:**
1. Alpha Block II flight success and payload validation.
2. Completion of Miranda engine hot-fire qualification tests.
3. Integration of Miranda engines with Northrop Grumman's Antares 330 first stage.
4. Net new commercial contract signings for Eclipse.
5. Successful launch of Blue Ghost Mission 2 (BGM2).

**Lagging Indicators:**
1. TTM Revenue growth.
2. Path to positive operating cash flow (burn rate reduction).
3. GAAP Gross Margin expansion.
4. Completion of capital expenditure cycles (launch pad construction).
5. Earnings per share (inflection to positive in FY2027).

---

## Section 16 — Top Risks
| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Launch Failure / Anomaly** | Severe | Fleet grounding, customer churn; mitigated by automated quality control and testing |
| **Eclipse Development Delays** | High | Prolonged cash burn, market share loss; mitigated by co-funding and engineering support from Northrop Grumman |
| **NASA CLPS Budget Cuts** | High | Revenue drop in Spacecraft Solutions; mitigated by commercial payload sales and U.S. Space Force contracts |
| **Equity Dilution** | Moderate | Value dilution for existing shareholders; mitigated by achieving cash flow neutrality in 18-24 months |

---

## Section 17 — Execution Difficulty Score
Score: **8** (Difficult)

| Score | Difficulty |
| :--- | :--- |
| 7–8 | **Difficult** |

---

## Section 18 — Judgment Call
Investment Attractiveness Score: **6**

Based on:
* Valuation
* KPI realism
* TAM
* Moat
* Execution risk

Choice: **Speculative Position**

**Explanation:** The partnership with Northrop Grumman and the spacecraft division provide real commercial substance, but the implied growth rates (31% to 37% FCF growth over 10 years) and steady-state revenue requirements ($2.53B) are highly challenging. It is attractive only as a speculative position in a diversified growth portfolio.

---

## Final Output Style
Hedge Fund Memo / Investment Committee Note

---

## Final Section
**One-Line Insight**
*The corporate partnership de-risks the technology, but the market is already pricing in a commercial scale-up that has yet to be proven.*

---

## Golden Rule
The stock is attractive only if the implied business outcomes (achieving a 37% FCF growth rate and scaling to a $2.53B revenue base) are realistically achievable through the flawless execution of the Eclipse and Blue Ghost programs.

---
**Links:** [[00_FLY_Hub|⬅️ Back to FLY Stock Hub]]
