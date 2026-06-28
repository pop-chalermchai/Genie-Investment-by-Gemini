---
type: stock-analysis
ticker: FPS
sector: Energy
tags: [energy, fps]
---

# Reverse DCF Analyst v2 — Institutional Grade

## Role
You are a professional institutional equity analyst specializing in Reverse DCF. 
Your responsibility is not to predict future stock prices. Your responsibility is to determine: What level of business performance is already implied by today’s valuation? 

* Think like a portfolio manager.
* Think probabilistically.
* Think in terms of business outcomes, not stock prices.
* Numbers lead the narrative.

## Core Principle
Reverse DCF is not asking: "Will the company grow?"
Reverse DCF is asking: "How much growth is already embedded in today’s stock price?"

## Primary Objective
When the user provides only Ticker and Company Name, you must independently gather relevant information and perform a complete Reverse DCF analysis.

## Data Collection (Mandatory)
### Market Data
* Share Price: $64.00
* Market Capitalization: $17.0 Billion
* Cash: $450 Million
* Debt: $950 Million
* Net Debt: $500 Million
* Enterprise Value (EV): $17.5 Billion

### Financial Data
* Revenue FY (FY26E): $1.37 Billion
* Revenue Growth: ~30%
* Gross Margin: 38%
* Operating Margin: 22%
* Free Cash Flow Margin: ~17% (Targeting 20% steady-state)
* Net Income Margin: ~15%

### Capital Structure
* Shares Outstanding: ~265 Million
* SBC Expense: ~3% of Revenue
* Dilution Rate: Low (1-2% annually)

### Business Profile
* Sector: Hardware / Infrastructure (Electrical Equipment)
Forgent Power Solutions (FPS) designs and manufactures electrical distribution equipment, including automatic transfer switches, transformers, and power distribution units, highly exposed to the data center and AI infrastructure build-out.

## Mandatory Assumption Disclosure
This analysis uses:
* Single-stage Gordon Growth Model
* Steady-state economics
* Long-term margin assumptions
* Current capital structure
* No speculative optionality valuation unless disclosed

## Reverse DCF Assumptions

| Scenario | Cost of Equity | Terminal Growth | FCF Margin | Probability |
| :--- | :--- | :--- | :--- | :--- |
| Conservative | 16% | 3% | 15% | 50% |
| Base | 14% | 3% | 20% | 70% |
| Aggressive | 12% | 3% | 25% | 100% |

## Section 1 — Reverse DCF Summary
What must this company become over the next 5–10 years?
* Revenue scale: FPS must grow from $1.37B to nearly $10B in revenue to justify its base-case valuation.
* Market position: It must capture a dominant double-digit share of the global high-density data center power equipment market.
* Margin profile: Must expand and sustain FCF margins of 20%, requiring significant operating leverage and premium pricing power.
* Competitive position: Must defend against entrenched electrical giants (Eaton, Schneider Electric) without succumbing to price wars.

## Section 2 — Implied Revenue
Implied Revenue = EV * (CoE - g) / FCF Margin

| Scenario | EV | CoE | g | Margin | Implied Revenue |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Conservative | $17.5B | 16% | 3% | 15% | **$15.17 Billion** |
| Base | $17.5B | 14% | 3% | 20% | **$9.63 Billion** |
| Aggressive | $17.5B | 12% | 3% | 25% | **$6.30 Billion** |

*Interpretation*: The current EV of $17.5B demands that FPS reaches nearly $10B in annual revenue at a 20% FCF margin in a steady state (Base Scenario). This represents roughly a 7x increase from current FY26 expectations.

## Section 3 — Risk Adjusted Revenue
Risk Adjusted Revenue = Implied Revenue / Probability

| Scenario | Implied Revenue | Probability | Risk Adjusted Revenue |
| :--- | :--- | :--- | :--- |
| Conservative | $15.17B | 50% | **$30.34 Billion** |
| Base | $9.63B | 70% | **$13.75 Billion** |
| Aggressive | $6.30B | 100% | **$6.30 Billion** |

*Interpretation*: To account for the 30% execution risk of reaching steady-state in the base scenario, the target "Risk-Adjusted" revenue hurdle is $13.75B. The market expects near-perfect execution over the next decade.

## Section 4 — KPI Translation
Industry: Hardware / Infrastructure
* Hardware KPIs: Data Center Deployments, MW (Megawatts) of Power Equipment Shipped, Average Selling Price (ASP).
If we assume an ASP of $5M per large-scale data center deployment:
* Base Implied Revenue ($9.63B) requires ~1,926 large-scale deployments annually.
If hyperscaler deployment slows down, FPS must compensate with massive pricing power or expansion into lower-margin broad industrial markets.

## Section 5 — TAM Reality Check
Required Market Share = Implied Revenue / TAM
Assuming a Data Center Power Distribution TAM of $40 Billion:

| TAM | Required Revenue | Required Market Share |
| :--- | :--- | :--- |
| $40 Billion | $9.63 Billion | **24.1%** |

*Classification*: **Difficult (15–30%)**
*Discussion*: Reaching a 24% market share is difficult against incumbents like Schneider and Eaton. TAM inflation is a real risk here; if the AI build-out cycle normalizes, the actual SAM may be lower, making the required market share nearly impossible to achieve without consolidation.

## Section 6 — Revenue Per Employee Check
Current Revenue: $1.37B / Employees (Est. 5,000) = ~$274,000 per employee.
Required Revenue ($9.63B) with double the headcount (10,000) = $963,000 per employee.
*Assessment*: **Aggressive**. While hardware/manufacturing can scale, nearing $1M per employee in a capital-heavy manufacturing sector is extremely rare and typically reserved for elite software or fabless semiconductors.

## Section 7 — Rule of 40 Assessment
Rule of 40 = Revenue Growth (30%) + FCF Margin (17%) = 47.
*Classification*: **Strong**.
*Discussion*: FPS is currently operating at a strong Rule of 40 profile, driven by hyper-growth in revenue. However, sustaining 30% growth on a multi-billion base while expanding margins is highly unlikely in hardware over a 5-10 year horizon.

## Section 8 — Dilution & SBC Analysis
* SBC % Revenue: ~3%
* Dilution Rate: ~1-2%
*Classification*: **Low**
*Discussion*: Minimal shareholder impact. Unlike SaaS, FPS does not rely heavily on stock-based compensation, which protects the purity of the FCF metrics.

## Section 9 — Capital Intensity
* Capex requirements: Building new manufacturing facilities (e.g., Mexico plant) requires substantial upfront capital.
* Inventory requirements: High, dependent on raw materials (copper, steel).
*Classification*: **Capital-intensive**
*Discussion*: Capital intensity will be a drag on FCF margins. Achieving the aggressive 25% FCF margin assumes massive factory automation and perfect supply chain execution.

## Section 10 — Customer Concentration
* Largest customers: Top 3 Hyperscalers (AWS, Microsoft, Google) likely make up a large portion of data center demand.
* Revenue concentration: Estimated 25-40%.

| Concentration | Risk |
| :--- | :--- |
| >25% | **High** |

*Discussion*: FPS is highly vulnerable to the CAPEX cycles of a few mega-cap tech companies. A 10% cut in hyperscaler CAPEX could lead to a 30% cut in FPS forward estimates.

## Section 11 — Competitive Moat
* Evaluated: Switching costs, Mission-critical brand reputation.
* Moat Classification: **Moderate**
*Explanation*: Data centers cannot afford power failures, making them sticky once equipment is installed. However, the technology itself is not an impenetrable monopoly, and incumbents have deep pockets to compete.

## Section 12 — Sanity Check
* Outcomes: **Difficult**.
* Bottlenecks: Competition, Execution, Capital.
To grow from $1.3B to nearly $10B requires a flawless decade of capacity expansion and sustained AI datacenter demand. The market is pricing FPS like a software monopoly, not an electrical equipment manufacturer.

## Section 13 — Market Expectations
Which scenario is currently priced in?
* Choice: **Bull (Aggressive to Base)**
*Evidence*: The $17.5B EV demands $6B-$9B in steady-state revenue. The market is completely ignoring the cyclicality of hardware and pricing in a perpetual upcycle.

## Section 14 — Analyst View
* Choice: **Hold / Avoid for new money**
* Justification: While the business is fundamentally strong and the AI tailwind is real, the valuation leaves zero margin of safety. Execution difficulty is high, and the required market share (24%) in a competitive hardware TAM is aggressive. 

## Section 15 — Milestones
* **Leading Indicators:**
    1. Hyperscaler CAPEX announcements
    2. Copper and raw material pricing trends
    3. Backlog growth rate QoQ
    4. Facility utilization rates (Mexico plant ramp)
    5. Data center vacancy rates
* **Lagging Indicators:**
    1. Gross margin expansion
    2. Revenue conversion from backlog
    3. FCF yield
    4. Market share percentage updates
    5. Debt paydown pace

## Section 16 — Top Risks
| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| Hyperscaler CAPEX cut | High | Diversification into utility grid modernization |
| Copper price spike | Moderate | Long-term contracts and pricing power |
| Incumbent price war | High | Focus on premium, high-density custom solutions |

## Section 17 — Execution Difficulty Score
* Score: **7.5**
* Interpretation: **Difficult**

## Section 18 — Judgment Call
* Investment Attractiveness Score: **4/10**
* Choice: **Wait**
* Explanation: The company is a great business trading at a perfect price. Wait for a cyclical pullback in AI infrastructure enthusiasm or a temporary earnings miss to build a position at a lower EV.

## Final Output Style
The narrative is right, but the valuation is already pricing in flawless execution.

---
**Links:** [[00_FPS_Hub|⬅️ Back to FPS Stock Hub]]
