// ==========================================================================
// CLIENT-SIDE PORTFOLIO DATABASE & STATE MANAGEMENT
// ==========================================================================
let holdings = [];
let portfoliosList = [];
let cachedParentTotals = {};
let activeParentPortfolio = null;
let activeSubPortfolio = null;

let activeTab = "dashboard";
let activeReport = "mu";
let activeLanguage = "en";
let activeReportTab = "overview";
let allocationChart = null;
let displayCurrency = "USD";
let exchangeRateUSDTHB = 32.505;
let currentSort = { column: null, direction: 'asc' };

// ==========================================================================
// THEME STATE MANAGEMENT (Solarized Light / Dark Switcher)
// ==========================================================================
let activeTheme = localStorage.getItem("genie-portfolio-theme") || "light";

function setTheme(theme) {
    activeTheme = theme;
    localStorage.setItem("genie-portfolio-theme", theme);
    
    const body = document.body;
    const btnLight = document.getElementById("theme-btn-light");
    const btnDark = document.getElementById("theme-btn-dark");
    
    if (theme === "dark") {
        body.classList.add("dark-theme");
        if (btnDark) btnDark.classList.add("active");
        if (btnLight) btnLight.classList.remove("active");
    } else {
        body.classList.remove("dark-theme");
        if (btnLight) btnLight.classList.add("active");
        if (btnDark) btnDark.classList.remove("active");
    }
}

// Initialize theme immediately on script load
setTheme(activeTheme);

function sortTable(column) {
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.column = column;
        currentSort.direction = 'asc';
    }
    updateDashboard();
}

// ==========================================================================
// SUB-AGENT TEAM PROFILE DATABASE
// ==========================================================================
const teamProfiles = {
    genie: {
        name: "Genie",
        avatar: "🧞‍♂️",
        role: "Orchestration Mastermind",
        skills: ["Intent Parsing", "Task Deconstruction", "Quality Synthesis", "Context Decoding"],
        quote: "Rub the lamp of curiosity, Pop, and watch your technical queries manifest into multi-agent symphonies!",
        intro: "Directs the symphony. Translates messy user intentions into optimized micro-workflows and delegates with CEO-style precision.",
        guardrails: [
            "Never do heavy grunt work; coordinate and delegate.",
            "Maintain high-energy, witty, and playfully theatrical persona.",
            "Enforce Valerie's and Christian's strict verification protocols.",
            "Designate graphic designs, visual layouts, and C-suite decks to Mateo."
        ]
    },
    valerie: {
        name: "Valerie",
        avatar: "📊",
        role: "Quantitative Oracle",
        skills: ["Reverse DCF", "Asymmetric Return Model", "Fundamental Auditing", "CapEx Tracking"],
        quote: "In God we trust; all others must bring audited balance sheets, validated cash flows, and mathematical proofs.",
        intro: "The numbers beast. Conducts deep-dive balance sheet audits, constructs valuations, and screens for growth anomalies.",
        guardrails: [
            "Solve for market growth rates via Reverse DCF model first.",
            "Require a minimum 3-to-1 Upside-to-Downside Payoff Ratio for buy ratings.",
            "Identify and evaluate competitor CapEx and advanced packaging yield risk.",
            "Report data directly to Christian for independent calculation verification."
        ]
    },
    serene: {
        name: "Serene",
        avatar: "🌎",
        role: "Financial Localization Expert",
        skills: ["Bilingual Translation", "Linguistic Nuance", "Term Standardization", "Cross-Border Adaptations"],
        quote: "Translating words is simple; translating the risk profile, financial spirit, and analytical context is an art.",
        intro: "The bridging voice. Translates dense English equity audits into rich, readable Thai while preserving extreme technical accuracy.",
        guardrails: [
            "Translate all core financial ratios into standardized Thai industry equivalents.",
            "Ensure definitions of DCF assumptions remain perfectly aligned with international standards.",
            "Highlight English vocabularies and structures to support Pop's language growth."
        ]
    },
    mateo: {
        name: "Mateo",
        avatar: "🎨",
        role: "The Creative Alchemist",
        skills: ["Executive Slide Decks", "Cover Art Production", "Interactive HTML UI", "Visual Aesthetics"],
        quote: "Data is the skeleton, Pop. Design is the muscle, the flesh, and the electrical impulse that brings it to life.",
        intro: "Design lead. Responsible for visual layouts, interactive aesthetics, and ensuring everything looks premium and jaw-dropping.",
        guardrails: [
            "Use deep space obsidian backdrops, gold highlights, and cyan glow trails.",
            "Never use default generic colors or unstyled browser placeholders.",
            "Design custom UI elements with micro-animations and smooth transition flows."
        ]
    },
    christian: {
        name: "Christian",
        avatar: "🔍",
        role: "The Forensic Auditor",
        skills: ["Formula Audit", "Independent Review", "Discrepancy Check", "Regulatory Alignment"],
        quote: "Trust, but verify. The math is either 100% correct, or it is completely wrong. There is no gray area in forensics.",
        intro: "The internal gatekeeper. Verifies mathematical models and enforces audit independence to verify reports are 100% correct.",
        guardrails: [
            "Maintain absolute audit independence; do not participate in thesis generation.",
            "Re-compute every DCF growth percentage, WACC formula, and margin calculation.",
            "Flag all model inconsistencies or unmitigated risk overlaps immediately."
        ]
    },
    lex: {
        name: "Lex",
        avatar: "🛡️",
        role: "The Code Sentinel",
        skills: ["Security Audit", "Bug Detection", "Performance Review", "SOP Compliance"],
        quote: "Every line of code is guilty of a vulnerability until proven otherwise. Ship clean, or don't ship.",
        intro: "The code gatekeeper. Audits all web platform changes for security holes, logic bugs, and SOP violations before any git commit.",
        guardrails: [
            "Never approve a commit containing a CRITICAL security or logic finding.",
            "Classify all findings as 🔴 CRITICAL / 🟡 WARNING / 🟢 SUGGESTION with file:line references.",
            "Scope reviews strictly to changed files only — do not rewrite legacy code.",
            "Conclude every review with a clear ✅ APPROVED or 🚫 REJECTED verdict."
        ]
    }
};

// ==========================================================================
// RESEARCH REPORTS DATABASE (ENGLISH & THAI)
// ==========================================================================
let researchReports = {};
let researchFilterMode = 'all'; // 'all' | 'positive' | 'negative'
let researchSortBy = 'sector';  // 'sector' | 'ticker' | 'upside'
let researchViewMode = 'list';  // 'list' | 'table'

// === PORTFOLIO DRILL-DOWN NAVIGATION ===
function navigateToPortfolio(parentName) {
    activeParentPortfolio = parentName;
    activeSubPortfolio = null;
    document.getElementById("dashboard-main-view").style.display = "none";
    document.getElementById("portfolio-detail-view").style.display = "block";
    renderPortfolioPage();
}

function navigateBack() {
    activeParentPortfolio = null;
    activeSubPortfolio = null;
    document.getElementById("dashboard-main-view").style.display = "";
    document.getElementById("portfolio-detail-view").style.display = "none";
}

function selectSubPortfolio(subName) {
    activeSubPortfolio = activeSubPortfolio === subName ? null : subName;
    renderPortfolioPage();
}

function renderPortfolioPage() {
    const data = cachedParentTotals[activeParentPortfolio];
    if (!data) return;

    const symbol = displayCurrency === "USD" ? "$" : "฿";
    const pGainLoss = data.value - data.cost;
    const pGainLossPct = data.cost > 0 ? (pGainLoss / data.cost) * 100 : 0;

    // Update header
    document.getElementById("port-detail-name").innerText = activeParentPortfolio;
    document.getElementById("port-detail-value").innerText = `${symbol}${formatNumber(data.value, 2)}`;
    const plEl = document.getElementById("port-detail-pl");
    plEl.innerText = `${pGainLoss >= 0 ? '+' : ''}${pGainLossPct.toFixed(1)}% (${symbol}${formatNumber(Math.abs(pGainLoss), 0)})`;
    plEl.style.color = pGainLoss >= 0 ? 'var(--color-positive)' : 'var(--color-negative)';

    // Build sub-portfolio chips
    const chipsEl = document.getElementById("subport-chips");
    chipsEl.innerHTML = "";

    const allChip = document.createElement("button");
    allChip.className = "subport-chip" + (activeSubPortfolio === null ? " active" : "");
    allChip.innerHTML = `<span class="chip-name">All</span><span class="chip-value">${symbol}${formatNumber(data.value, 0)}</span>`;
    allChip.onclick = () => { activeSubPortfolio = null; renderPortfolioPage(); };
    chipsEl.appendChild(allChip);

    Object.keys(data.subPorts).forEach(subName => {
        const subData = data.subPorts[subName];
        const subGainLoss = subData.value - subData.cost;
        const subGainLossPct = subData.cost > 0 ? (subGainLoss / subData.cost) * 100 : 0;
        const chip = document.createElement("button");
        chip.className = "subport-chip" + (activeSubPortfolio === subName ? " active" : "");
        chip.innerHTML = `<span class="chip-name">${subName}</span><span class="chip-value">${symbol}${formatNumber(subData.value, 0)}</span><span class="chip-pl" style="color:${subGainLoss >= 0 ? 'var(--color-positive)' : 'var(--color-negative)'}">${subGainLoss >= 0 ? '+' : ''}${subGainLossPct.toFixed(1)}%</span>`;
        chip.onclick = () => selectSubPortfolio(subName);
        chipsEl.appendChild(chip);
    });

    // Build filtered holdings table
    const tbody = document.getElementById("portfolio-table-body");
    tbody.innerHTML = "";

    const filteredHoldings = holdings.filter(pos => {
        const parentMatch = (pos.parentPortfolio || pos.portfolio) === activeParentPortfolio;
        const subMatch = activeSubPortfolio === null || pos.portfolio === activeSubPortfolio;
        return parentMatch && subMatch;
    });

    if (filteredHoldings.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:var(--text-secondary);padding:24px;">No holdings in this portfolio.</td></tr>`;
        return;
    }

    filteredHoldings.forEach(pos => {
        let avgCost = pos.avgCost;
        let currentPrice = pos.currentPrice;
        let costBasis = pos.shares * avgCost;
        let marketValue = pos.shares * currentPrice;

        if (displayCurrency === "USD" && pos.currency === "THB") {
            avgCost = pos.avgCost / exchangeRateUSDTHB;
            currentPrice = pos.currentPrice / exchangeRateUSDTHB;
            costBasis = (pos.shares * pos.avgCost) / exchangeRateUSDTHB;
            marketValue = (pos.shares * pos.currentPrice) / exchangeRateUSDTHB;
        } else if (displayCurrency === "THB" && pos.currency === "USD") {
            avgCost = pos.avgCost * exchangeRateUSDTHB;
            currentPrice = pos.currentPrice * exchangeRateUSDTHB;
            costBasis = (pos.shares * pos.avgCost) * exchangeRateUSDTHB;
            marketValue = (pos.shares * pos.currentPrice) * exchangeRateUSDTHB;
        }

        const gainLoss = marketValue - costBasis;
        const gainLossPct = costBasis > 0 ? (gainLoss / costBasis) * 100 : 0;

        const row = document.createElement("tr");
        row.style.cursor = "pointer";
        row.title = "Click to view detailed chart & stats";
        row.onclick = () => openStockDetail(pos.ticker);
        row.innerHTML = `
            <td><span class="ticker-badge">${pos.ticker}</span></td>
            <td><strong>${pos.companyName}</strong><br><span style="font-size:0.72rem;color:var(--text-secondary);">${pos.sector}</span></td>
            <td><span class="portfolio-badge">${pos.portfolio}</span></td>
            <td class="text-right table-shares">${formatShares(pos.shares)}</td>
            <td class="text-right table-currency">${symbol}${avgCost.toFixed(2)}</td>
            <td class="text-right table-currency">${symbol}${currentPrice.toFixed(2)}</td>
            <td class="text-right table-currency" style="font-weight:500;">${symbol}${formatNumber(marketValue, 2)}</td>
            <td class="text-right ${gainLoss >= 0 ? 'cell-positive' : 'cell-negative'}">
                ${symbol}${formatNumber(gainLoss, 2)} (${gainLossPct >= 0 ? '+' : ''}${gainLossPct.toFixed(1)}%)
            </td>
        `;
        tbody.appendChild(row);
    });
}

function deleteParentPortfolio(pName) {
    if (confirm(`Are you sure you want to delete the portfolio "${pName}"? This will also delete all sub-portfolios, assets, and transactions inside it.`)) {
        fetch('/api/portfolio?name=' + encodeURIComponent(pName), {
            method: 'DELETE'
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                // Re-fetch holdings and portfolios
                Promise.all([
                    fetch('/api/holdings').then(res => res.json()),
                    fetch('/api/portfolios').then(res => res.json())
                ])
                .then(([hData, pData]) => {
                    holdings = hData.map(h => ({...h, currentPrice: h.avgCost}));
                    portfoliosList = pData;
                    populateDropdowns();
                    updateDashboard();
                    fetchLivePrices(); // Update with real prices
                });
            } else {
                alert("Error deleting portfolio: " + data.error);
            }
        })
        .catch(err => {
            console.error("Error deleting portfolio:", err);
            alert("Failed to delete portfolio.");
        });
    }
}

// ==========================================================================
// CORE WORKSPACE INITIALIZATION & LOGIC FLOW
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
    Promise.all([
        fetch('/api/holdings').then(res => res.json()),
        fetch('/api/reports').then(res => res.json()),
        fetch('/api/portfolios').then(res => res.json())
    ])
    .then(([holdingsData, reportsData, portfoliosData]) => {
        holdings = holdingsData.map(h => ({...h, currentPrice: h.avgCost}));
        researchReports = reportsData;
        portfoliosList = portfoliosData;
        
        populateDropdowns();

        // Apply cached prices from localStorage for instant first render
        try {
            const cached = JSON.parse(localStorage.getItem('genie-price-cache') || '{}');
            const CACHE_TTL = 24 * 60 * 60 * 1000; // 24 hours
            if (cached.__ts__ && (Date.now() - cached.__ts__) < CACHE_TTL) {
                if (cached.__rate__) exchangeRateUSDTHB = cached.__rate__;
                holdings.forEach(h => { if (cached[h.ticker]) h.currentPrice = cached[h.ticker]; });
            }
        } catch (e) { /* ignore corrupt cache */ }

        updateDashboard();
        renderReportList();

        // Restore last viewed report from localStorage
        const lastReport = localStorage.getItem('genie-last-report');
        if (lastReport && researchReports[lastReport]) {
            activeReport = lastReport;
        }

        renderReport();

        // Detect initial tab from URL path
        const path = window.location.pathname.substring(1);
        const validTabs = ["dashboard", "team", "research", "transactions"];
        if (validTabs.includes(path)) {
            switchTab(path, false);
        } else {
            switchTab("dashboard", false);
        }

        fetchLivePrices(); // runs in background, silently updates prices
        setupDragAndDrop();
    })
    .catch(err => console.error("Error fetching data:", err));
});

// TAB SWITCHER
function switchTab(tabName, pushState = true) {
    activeTab = tabName;
    
    // Toggle navigation classes
    const tabs = ["dashboard", "team", "research", "transactions"];
    tabs.forEach(t => {
        const tabEl = document.getElementById(`tab-${t}`);
        const contentEl = document.getElementById(`section-${t}`);
        
        if (t === tabName) {
            tabEl.classList.add("active");
            contentEl.classList.add("active-content");
        } else {
            tabEl.classList.remove("active");
            contentEl.classList.remove("active-content");
        }
    });

    // Update URL without page reload
    if (pushState) {
        const path = tabName === "dashboard" ? "/" : "/" + tabName;
        history.pushState({ tab: tabName }, "", path);
    }

    // Resize chart to prevent visual glitches when switching tabs
    if (tabName === "dashboard" && allocationChart) {
        allocationChart.resize();
    }

    if (tabName === "transactions") {
        loadTransactions();
    }
}

// Handle browser back/forward buttons
window.addEventListener("popstate", (event) => {
    const tabName = (event.state && event.state.tab) || "dashboard";
    switchTab(tabName, false);
});

// ==========================================================================
// DASHBOARD VIEW LOGIC & MATH ENGINE
// ==========================================================================
function updateDashboard() {
    let totalCostBasis = 0;
    let totalMarketValue = 0;

    // Apply sorting
    if (currentSort.column) {
        holdings.sort((a, b) => {
            const getMarketValue = (h) => {
                let p = h.currentPrice;
                if (displayCurrency === "USD" && h.currency === "THB") p /= exchangeRateUSDTHB;
                else if (displayCurrency === "THB" && h.currency === "USD") p *= exchangeRateUSDTHB;
                return h.shares * p;
            };
            const getCostBasis = (h) => {
                let c = h.avgCost;
                if (displayCurrency === "USD" && h.currency === "THB") c /= exchangeRateUSDTHB;
                else if (displayCurrency === "THB" && h.currency === "USD") c *= exchangeRateUSDTHB;
                return h.shares * c;
            };
            
            let valA, valB;
            switch (currentSort.column) {
                case 'ticker': valA = a.ticker; valB = b.ticker; break;
                case 'companyName': valA = a.companyName; valB = b.companyName; break;
                case 'portfolio': valA = a.portfolio; valB = b.portfolio; break;
                case 'shares': valA = a.shares; valB = b.shares; break;
                case 'avgCost': valA = getCostBasis(a)/a.shares; valB = getCostBasis(b)/b.shares; break;
                case 'marketPrice': valA = getMarketValue(a)/a.shares; valB = getMarketValue(b)/b.shares; break;
                case 'marketValue': valA = getMarketValue(a); valB = getMarketValue(b); break;
                case 'weight': valA = getMarketValue(a); valB = getMarketValue(b); break;
                case 'return': valA = getMarketValue(a) - getCostBasis(a); valB = getMarketValue(b) - getCostBasis(b); break;
                default: valA = a.ticker; valB = b.ticker;
            }
            
            if (valA < valB) return currentSort.direction === 'asc' ? -1 : 1;
            if (valA > valB) return currentSort.direction === 'asc' ? 1 : -1;
            return 0;
        });
    }

    // Group totals by parent portfolio and nested sub-portfolio
    const parentTotals = {}; // { "US Stock": { value: 0, cost: 0, subPorts: { "Dime": { value: 0, cost: 0 }, "WeBull": { value: 0, cost: 0 } } } }
    
    const tableBody = document.getElementById("positions-table-body");
    tableBody.innerHTML = ""; // Clear table

    // Pre-pass: calculate total market value for weight % computation
    let preTotalMarketValue = 0;
    holdings.forEach(pos => {
        let mv = pos.shares * pos.currentPrice;
        if (displayCurrency === "USD" && pos.currency === "THB") mv /= exchangeRateUSDTHB;
        else if (displayCurrency === "THB" && pos.currency === "USD") mv *= exchangeRateUSDTHB;
        preTotalMarketValue += mv;
    });

    holdings.forEach((pos, index) => {
        let avgCost = pos.avgCost;
        let currentPrice = pos.currentPrice;
        let costBasis = pos.shares * avgCost;
        let marketValue = pos.shares * currentPrice;

        // Perform currency conversion to the display currency on the fly
        if (displayCurrency === "USD" && pos.currency === "THB") {
            avgCost = pos.avgCost / exchangeRateUSDTHB;
            currentPrice = pos.currentPrice / exchangeRateUSDTHB;
            costBasis = (pos.shares * pos.avgCost) / exchangeRateUSDTHB;
            marketValue = (pos.shares * pos.currentPrice) / exchangeRateUSDTHB;
        } else if (displayCurrency === "THB" && pos.currency === "USD") {
            avgCost = pos.avgCost * exchangeRateUSDTHB;
            currentPrice = pos.currentPrice * exchangeRateUSDTHB;
            costBasis = (pos.shares * pos.avgCost) * exchangeRateUSDTHB;
            marketValue = (pos.shares * pos.currentPrice) * exchangeRateUSDTHB;
        }

        const gainLoss = marketValue - costBasis;
        const gainLossPct = costBasis > 0 ? (gainLoss / costBasis) * 100 : 0;
        
        totalCostBasis += costBasis;
        totalMarketValue += marketValue;

        // Accumulate parent and sub-portfolio totals
        const parentName = pos.parentPortfolio || pos.portfolio;
        const subName = pos.portfolio;
        
        if (!parentTotals[parentName]) {
            parentTotals[parentName] = { value: 0, cost: 0, subPorts: {} };
        }
        parentTotals[parentName].value += marketValue;
        parentTotals[parentName].cost += costBasis;

        if (!parentTotals[parentName].subPorts[subName]) {
            parentTotals[parentName].subPorts[subName] = { value: 0, cost: 0 };
        }
        parentTotals[parentName].subPorts[subName].value += marketValue;
        parentTotals[parentName].subPorts[subName].cost += costBasis;

        const symbol = displayCurrency === "USD" ? "$" : "฿";
        const weightPct = preTotalMarketValue > 0 ? (marketValue / preTotalMarketValue) * 100 : 0;

        // Check if this ticker has a research report
        const reportKey = Object.keys(researchReports).find(k => researchReports[k].ticker === pos.ticker);
        const researchLink = reportKey
            ? `<span onclick="event.stopPropagation();openResearchFromHolding('${reportKey}')" style="display:block;font-size:0.62rem;color:var(--accent-gold);opacity:0.7;cursor:pointer;letter-spacing:0.4px;margin-top:3px;transition:opacity 0.15s;" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.7">research ↗</span>`
            : '';

        // Badge class derived from sub-portfolio name
        const badgeName = subName.toLowerCase().replace(/ /g, '-');

        // Generate HTML row
        const row = document.createElement("tr");
        row.style.cursor = "pointer";
        row.title = "Click to view detailed chart & stats";
        row.onclick = () => openStockDetail(pos.ticker);
        const logoHtml = pos.domain
            ? `<img src="https://icon.horse/icon/${pos.domain}" width="24" height="24" loading="lazy" style="border-radius:5px;object-fit:contain;display:block;margin:0 auto 4px;" onerror="this.style.display='none'">`
            : '';

        row.innerHTML = `
            <td style="text-align:center;">${logoHtml}<span style="font-family:var(--font-mono);font-weight:700;font-size:0.82rem;color:var(--accent-neon);letter-spacing:0.5px;">${pos.ticker}</span>${researchLink}</td>
            <td><strong>${pos.companyName}</strong><br><span style="font-size: 0.72rem; color: var(--text-secondary);">${pos.sector}</span></td>
            <td><span class="portfolio-badge badge-${badgeName}">${subName}</span></td>
            <td class="text-right table-shares">${formatShares(pos.shares)}</td>
            <td class="text-right table-currency">${symbol}${avgCost.toFixed(2)}</td>
            <td class="text-right table-currency">${symbol}${currentPrice.toFixed(2)}</td>
            <td class="text-right table-currency" style="font-weight: 500;">${symbol}${formatNumber(marketValue, 2)}</td>
            <td class="text-right" style="font-family:var(--font-mono);font-size:0.85rem;">
                <div style="display:flex;align-items:center;justify-content:flex-end;gap:6px;">
                    <div style="width:40px;height:4px;background:var(--border-dim);border-radius:2px;overflow:hidden;flex-shrink:0;">
                        <div style="width:${Math.min(weightPct,100)}%;height:100%;background:var(--accent-neon);border-radius:2px;"></div>
                    </div>
                    <span style="color:var(--text-secondary);min-width:36px;text-align:right;">${weightPct.toFixed(1)}%</span>
                </div>
            </td>
            <td class="text-right ${gainLoss >= 0 ? 'cell-positive' : 'cell-negative'}">
                ${symbol}${formatNumber(gainLoss, 2)} (${gainLossPct >= 0 ? '+' : ''}${gainLossPct.toFixed(1)}%)
            </td>
        `;
        tableBody.appendChild(row);
    });

    const netGainLoss = totalMarketValue - totalCostBasis;
    const netGainLossPct = totalCostBasis > 0 ? (netGainLoss / totalCostBasis) * 100 : 0;

    const symbol = displayCurrency === "USD" ? "$" : "฿";

    // Update Dashboard metric texts
    document.getElementById("val-portfolio-value").innerText = `${symbol}${formatNumber(totalMarketValue, 2)}`;
    document.getElementById("val-total-cost").innerText = `${symbol}${formatNumber(totalCostBasis, 2)}`;
    
    const plEl = document.getElementById("val-unrealized-pl");
    const plPctEl = document.getElementById("val-unrealized-pct");
    const valPortPct = document.getElementById("val-portfolio-pct");
    
    plEl.innerText = `${symbol}${formatNumber(netGainLoss, 2)}`;
    plPctEl.innerText = `${netGainLossPct >= 0 ? '+' : ''}${netGainLossPct.toFixed(1)}%`;
    valPortPct.innerText = `${netGainLossPct >= 0 ? '+' : ''}${netGainLossPct.toFixed(1)}% Return`;

    // Adjust metric colors dynamically
    if (netGainLoss >= 0) {
        plEl.style.color = "var(--color-positive)";
        plPctEl.className = "metric-change positive";
        valPortPct.className = "metric-change positive";
    } else {
        plEl.style.color = "var(--color-negative)";
        plPctEl.className = "metric-change negative";
        valPortPct.className = "metric-change negative";
    }

    // Cache parentTotals for portfolio drill-down page
    cachedParentTotals = parentTotals;

    // If user is on portfolio detail page, re-render it with fresh prices
    if (activeParentPortfolio) {
        renderPortfolioPage();
    }

    // Update Parent Portfolio Summary Cards (compact, always fixed height)
    const gridEl = document.getElementById("sub-portfolios-grid");
    if (gridEl) {
        gridEl.innerHTML = "";
        const parentColors = {
            "us stock": "#CA8A04",
            "tax saving fund": "#8B5CF6",
            "provident fund": "#10B981"
        };
        const colors = ["#8B5CF6", "#CA8A04", "#EF4444", "#22C55E", "#FFA500", "#FF5C5C"];
        let colorIdx = 0;

        Object.keys(parentTotals).forEach(parentName => {
            const data = parentTotals[parentName];
            const pGainLoss = data.value - data.cost;
            const pGainLossPct = data.cost > 0 ? (pGainLoss / data.cost) * 100 : 0;
            const isPos = pGainLoss >= 0;
            const subPortCount = Object.keys(data.subPorts).length;

            const lowerName = parentName.toLowerCase();
            const color = parentColors[lowerName] || colors[colorIdx % colors.length];
            colorIdx++;

            const card = document.createElement("div");
            card.className = "metric-card glass-panel parent-portfolio-card";
            card.style.cssText = `padding:15px; border-left:3px solid ${color}; display:flex; flex-direction:column; cursor:pointer; position:relative; transition:var(--transition);`;
            card.onclick = (e) => {
                if (e.target.tagName === "BUTTON") return;
                navigateToPortfolio(parentName);
            };
            card.onmouseover = () => { card.style.transform = "translateY(-2px)"; card.style.boxShadow = `0 4px 20px ${color}33`; };
            card.onmouseout = () => { card.style.transform = ""; card.style.boxShadow = ""; };

            card.innerHTML = `
                <button onclick="deleteParentPortfolio('${parentName}')" title="Delete Portfolio" style="position:absolute;top:10px;right:10px;background:none;border:none;color:var(--color-negative);cursor:pointer;font-size:1.2rem;padding:0;line-height:1;opacity:0.5;transition:opacity 0.2s;" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.5">&times;</button>
                <div style="font-size:1.2rem;font-weight:700;color:var(--text-emphasis);margin:0 0 2px 0;">${parentName}</div>
                <span style="font-size:1.1rem;font-weight:700;color:var(--text-primary);">${symbol}${formatNumber(data.value, 2)}</span>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;">
                    <span style="font-size:0.78rem;font-weight:600;color:${isPos ? 'var(--color-positive)' : 'var(--color-negative)'};">${isPos ? '+' : ''}${pGainLossPct.toFixed(1)}% (${symbol}${formatNumber(Math.abs(pGainLoss), 0)})</span>
                    <span style="font-size:0.72rem;color:var(--text-secondary);">${subPortCount} sub-port${subPortCount > 1 ? 's' : ''} →</span>
                </div>
            `;
            gridEl.appendChild(card);
        });
    }

    // Refresh allocation charts
    renderChart();
}

// CHART ENGINE (Chart.js implementation)
function renderChart() {
    const ctx = document.getElementById("allocationChart").getContext("2d");
    
    // Destroy previous instance to re-draw correctly
    if (allocationChart) {
        allocationChart.destroy();
    }

    const labels = holdings.map(h => h.ticker);
    const data = holdings.map(h => {
        let price = h.currentPrice;
        // Convert price to display currency
        if (displayCurrency === "USD" && h.currency === "THB") {
            price = h.currentPrice / exchangeRateUSDTHB;
        } else if (displayCurrency === "THB" && h.currency === "USD") {
            price = h.currentPrice * exchangeRateUSDTHB;
        }
        return h.shares * price;
    });
    
    allocationChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    "rgba(202, 138, 4, 0.65)",  // Quest Gold
                    "rgba(245, 208, 97, 0.65)",  // Lighter Gold Accent
                    "rgba(139, 92, 246, 0.65)",  // Royal Purple
                    "rgba(34, 197, 94, 0.65)"   // Jade Green
                ],
                borderColor: [
                    "#CA8A04",
                    "#F5D061",
                    "#8B5CF6",
                    "#22C55E"
                ],
                borderWidth: 1.5,
                hoverOffset: 12
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        color: "#94A3B8",
                        font: {
                            family: "Inter",
                            size: 11
                        },
                        boxWidth: 12,
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: "#0A0F1A",
                    titleColor: "#FFFFFF",
                    bodyColor: "#94A3B8",
                    borderColor: "rgba(148, 163, 184, 0.15)",
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            const val = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = ((val / total) * 100).toFixed(1);
                            const symbol = displayCurrency === "USD" ? "$" : "฿";
                            return `Allocation: ${symbol}${formatNumber(val, 2)} (${pct}%)`;
                        }
                    }
                }
            },
            cutout: "70%"
        }
    });
}

// INGEST POSITION TRANSACTION
function handleIngest(event) {
    event.preventDefault();

    const type = document.getElementById("ingest-type").value;
    const ticker = document.getElementById("ingest-ticker").value.toUpperCase().trim();
    const companyName = document.getElementById("ingest-name").value.trim();
    const sector = document.getElementById("ingest-sector").value;
    const portfolio = document.getElementById("ingest-portfolio").value;
    const shares = parseFloat(document.getElementById("ingest-shares").value);
    const avgCost = parseFloat(document.getElementById("ingest-avg-cost").value);
    const currency = document.getElementById("ingest-currency").value;

    fetch('/api/ingest', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            type, ticker, companyName, sector, portfolio, shares, avgCost, currency
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById("ingest-form").reset();
            toggleIngestType(); // reset to default styles
            
            // Re-fetch holdings from DB
            fetch('/api/holdings')
                .then(r => r.json())
                .then(hData => {
                    holdings = hData.map(h => ({...h, currentPrice: h.avgCost}));
                    updateDashboard();
                    fetchLivePrices(); // Re-trigger live price fetch for the new asset
                });
        } else {
            alert("Error: " + data.error);
        }
    })
    .catch(err => {
        console.error("Error ingesting position:", err);
        alert("Failed to ingest position.");
    });
}

function toggleIngestType() {
    const select = document.getElementById("ingest-type");
    const label = document.getElementById("label-avg-cost");
    
    if (select.value === "SELL") {
        select.classList.remove("type-buy");
        select.classList.add("type-sell");
        label.innerText = "Selling Price ($)";
    } else {
        select.classList.remove("type-sell");
        select.classList.add("type-buy");
        label.innerText = "Avg Cost ($)";
    }
}

// AUTO-FILL COMPANY NAME FROM YAHOO FINANCE
async function autoFillCompanyName() {
    const tickerInput = document.getElementById("ingest-ticker");
    const nameInput = document.getElementById("ingest-name");
    const ticker = tickerInput.value.trim().toUpperCase();
    
    if (!ticker || nameInput.value.trim() !== "") return;
    
    nameInput.placeholder = "Auto-fetching name...";
    try {
        const response = await fetch(`/api/stock?ticker=${ticker}`);
        if (!response.ok) throw new Error("API error");
        const data = await response.json();
        
        if (data.longName) {
            nameInput.value = data.longName;
        } else if (data.shortName) {
            nameInput.value = data.shortName;
        } else {
            nameInput.placeholder = "e.g., Tesla, Inc.";
        }
        
        // Auto-fill price as a hint to avg cost if it's empty
        const costInput = document.getElementById("ingest-avg-cost");
        if (data.price && !costInput.value) {
            costInput.value = data.price.toFixed(2);
        }
    } catch (err) {
        console.warn("Failed to auto-fill name for", ticker, err);
        nameInput.placeholder = "e.g., Tesla, Inc.";
    }
}

// LIVE FILTERING SEARCHBAR
function filterPositions() {
    const query = document.getElementById("search-input").value.toUpperCase().trim();
    const sector = document.getElementById("sector-filter").value;
    const portfolio = document.getElementById("portfolio-filter").value;
    
    const rows = document.getElementById("positions-table-body").getElementsByTagName("tr");
    
    holdings.forEach((pos, idx) => {
        const matchesQuery = pos.ticker.includes(query) || pos.companyName.toUpperCase().includes(query);
        const matchesSector = sector === "ALL" || pos.sector === sector;
        const matchesPortfolio = portfolio === "ALL" || pos.portfolio === portfolio;
        
        if (matchesQuery && matchesSector && matchesPortfolio) {
            rows[idx].style.display = "";
        } else {
            rows[idx].style.display = "none";
        }
    });
}

// ==========================================================================
// SUB-AGENT TEAM PROFILE INTERACTION
// ==========================================================================
function toggleCardFlip(cardEl) {
    cardEl.classList.toggle("flipped");
}


// ==========================================================================
// RESEARCH VIEW LOCALIZATION ENGINE
// ==========================================================================
let collapsedSectors = {}; // Remember collapsed states client-side

function selectReport(reportId) {
    activeReport = reportId;
    localStorage.setItem('genie-last-report', reportId);
    renderReport();
    renderReportList();
}

function setLanguage(lang) {
    activeLanguage = lang;
    document.getElementById("lang-en").classList.remove("active");
    document.getElementById("lang-th").classList.remove("active");
    document.getElementById("lang-" + lang).classList.add("active");
    renderReport();
}

function setReportTab(tab) {
    activeReportTab = tab;
    document.getElementById("tab-overview").classList.remove("active");
    document.getElementById("tab-dcf").classList.remove("active");
    document.getElementById("tab-" + tab).classList.add("active");
    renderReport();
}

function getUpsidePct(report) {
    if (!report.priceTarget || !report.analysisPrice || report.analysisPrice === 0) return null;
    return ((report.priceTarget - report.analysisPrice) / report.analysisPrice) * 100;
}

function getFilteredSortedReports() {
    const query = (document.getElementById("report-search-input")?.value || '').toLowerCase().trim();
    let reports = Object.keys(researchReports).map(key => ({ key, ...researchReports[key] }));
    if (query) reports = reports.filter(r => r.ticker.toLowerCase().includes(query) || r.companyName.toLowerCase().includes(query));
    if (researchFilterMode === 'positive') reports = reports.filter(r => r.isPositive);
    if (researchFilterMode === 'negative') reports = reports.filter(r => !r.isPositive);
    if (researchSortBy === 'ticker') {
        reports.sort((a, b) => a.ticker.localeCompare(b.ticker));
    } else if (researchSortBy === 'upside') {
        reports.sort((a, b) => (getUpsidePct(b) ?? -Infinity) - (getUpsidePct(a) ?? -Infinity));
    } else {
        reports.sort((a, b) => (a.sector || 'Other').localeCompare(b.sector || 'Other') || a.ticker.localeCompare(b.ticker));
    }
    return { reports, query };
}

function makeReportRow(report) {
    const recColor = report.isPositive ? 'var(--color-positive)' : 'var(--color-negative)';
    const recBg    = report.isPositive ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)';
    const recLabel = (report.rating || 'N/A').split(' ')[0].replace(/[^A-Z/]/gi, '') || 'N/A';
    const ptLine   = report.priceTarget
        ? `<span style="font-size:0.68rem;color:var(--text-secondary);font-family:var(--font-mono);">PT: $${parseFloat(report.priceTarget).toFixed(2)}</span>`
        : '';
    const btn = document.createElement("button");
    btn.className = "report-list-item " + (activeReport === report.key ? "active" : "");
    btn.id = "report-item-" + report.key;
    btn.style.flex = "1";
    btn.onclick = () => selectReport(report.key);
    btn.innerHTML = `
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:2px;">
            <span style="font-size:0.68rem;font-weight:700;padding:1px 5px;border-radius:3px;background:${recBg};color:${recColor};white-space:nowrap;">${recLabel}</span>
            <span class="report-ticker">${report.ticker}</span>
            ${ptLine}
        </div>
        <span class="report-name" style="font-size:0.78rem;">${report.companyName}</span>
    `;
    const actions = document.createElement("div");
    actions.className = "report-row-actions";
    const editBtn = document.createElement("button");
    editBtn.title = "Edit"; editBtn.innerHTML = "✏️";
    editBtn.onclick = (e) => { e.stopPropagation(); openEditReportModal(report.key); };
    editBtn.style.cssText = "padding:2px 6px;border:1px solid var(--border-dim);background:var(--bg-card-solid);border-radius:4px;cursor:pointer;font-size:0.75rem;line-height:1;";
    const delBtn = document.createElement("button");
    delBtn.title = "Delete"; delBtn.innerHTML = "🗑";
    delBtn.onclick = (e) => { e.stopPropagation(); deleteReport(report.key); };
    delBtn.style.cssText = "padding:2px 6px;border:1px solid var(--border-dim);background:var(--bg-card-solid);border-radius:4px;cursor:pointer;font-size:0.75rem;line-height:1;";
    actions.appendChild(editBtn); actions.appendChild(delBtn);
    const rowEl = document.createElement("div");
    rowEl.className = "report-row";
    rowEl.appendChild(btn); rowEl.appendChild(actions);
    return rowEl;
}

function renderReportList() {
    const container = document.getElementById("report-list-container");
    if (!container) return;
    container.innerHTML = "";
    const { reports, query } = getFilteredSortedReports();

    if (researchSortBy === 'sector' && !query) {
        // Grouped by sector
        const groups = {};
        reports.forEach(r => { const s = r.sector || "Other Sectors"; if (!groups[s]) groups[s] = []; groups[s].push(r); });
        Object.keys(groups).forEach(sector => {
            const isCollapsed = collapsedSectors[sector] === true;
            const groupHeader = document.createElement("div");
            groupHeader.className = "report-sector-header";
            groupHeader.style.cssText = "display:flex;justify-content:space-between;align-items:center;padding:10px 14px;background:var(--bg-card-solid);border:1px solid var(--border-dim);border-radius:6px;margin-top:10px;cursor:pointer;font-size:0.78rem;font-weight:700;color:var(--text-primary);user-select:none;transition:var(--transition);";
            groupHeader.onmouseover = () => { groupHeader.style.background = "rgba(147,161,161,0.15)"; };
            groupHeader.onmouseout  = () => { groupHeader.style.background = "var(--bg-card-solid)"; };
            groupHeader.onclick = () => { collapsedSectors[sector] = !isCollapsed; renderReportList(); };
            groupHeader.innerHTML = `<span>📁 ${sector} (${groups[sector].length})</span><span style="font-size:0.65rem;display:inline-block;transform:${isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)'};">▼</span>`;
            container.appendChild(groupHeader);
            const wrapper = document.createElement("div");
            wrapper.style.cssText = "display:flex;flex-direction:column;gap:6px;margin-top:6px;padding-left:8px;";
            if (isCollapsed) wrapper.style.display = "none";
            groups[sector].forEach(r => wrapper.appendChild(makeReportRow(r)));
            container.appendChild(wrapper);
        });
    } else {
        // Flat sorted list
        const wrapper = document.createElement("div");
        wrapper.style.cssText = "display:flex;flex-direction:column;gap:6px;margin-top:6px;";
        if (reports.length === 0) wrapper.innerHTML = `<div style="color:var(--text-secondary);font-size:0.82rem;text-align:center;padding:20px 0;">No reports match.</div>`;
        reports.forEach(r => wrapper.appendChild(makeReportRow(r)));
        container.appendChild(wrapper);
    }
}

function filterReports() {
    renderReportList();
    if (researchViewMode === 'table') renderResearchTable();
}

function setResearchFilter(mode) {
    researchFilterMode = mode;
    ['all', 'pos', 'neg'].forEach(id => document.getElementById('rf-' + id)?.classList.remove('rf-active'));
    const map = { all: 'rf-all', positive: 'rf-pos', negative: 'rf-neg' };
    document.getElementById(map[mode])?.classList.add('rf-active');
    renderReportList();
    if (researchViewMode === 'table') renderResearchTable();
}

function setResearchSort(by) {
    researchSortBy = by;
    renderReportList();
    if (researchViewMode === 'table') renderResearchTable();
}

function setResearchViewMode(mode) {
    researchViewMode = mode;
    document.getElementById('research-list-mode').style.display  = mode === 'list'  ? '' : 'none';
    document.getElementById('research-table-mode').style.display = mode === 'table' ? '' : 'none';
    document.getElementById('rv-btn-list').classList.toggle('rv-active',  mode === 'list');
    document.getElementById('rv-btn-table').classList.toggle('rv-active', mode === 'table');
    if (mode === 'table') renderResearchTable();
}

function renderResearchTable() {
    const tbody = document.getElementById('research-table-body');
    if (!tbody) return;
    const { reports } = getFilteredSortedReports();
    tbody.innerHTML = '';
    if (reports.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--text-secondary);padding:30px 0;">No reports match the current filter.</td></tr>`;
        return;
    }
    reports.forEach(r => {
        const upside = getUpsidePct(r);
        const upsideStr   = upside !== null ? `${upside >= 0 ? '+' : ''}${upside.toFixed(1)}%` : '—';
        const upsideColor = upside === null ? 'var(--text-secondary)' : upside >= 0 ? 'var(--color-positive)' : 'var(--color-negative)';
        const recColor    = r.isPositive ? 'var(--color-positive)' : 'var(--color-negative)';
        const recBg       = r.isPositive ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)';
        const recLabel    = (r.rating || 'N/A').split(' ')[0].replace(/[^A-Z/]/gi, '') || 'N/A';
        const tr = document.createElement('tr');
        tr.style.cursor = 'pointer';
        tr.onclick = () => { setResearchViewMode('list'); selectReport(r.key); };
        tr.innerHTML = `
            <td style="font-family:var(--font-mono);font-weight:700;color:var(--accent-neon);">${r.ticker}</td>
            <td style="color:var(--text-primary);font-size:0.85rem;">${r.companyName}</td>
            <td style="color:var(--text-secondary);font-size:0.82rem;">${r.sector || '—'}</td>
            <td><span style="font-size:0.72rem;font-weight:700;padding:2px 7px;border-radius:3px;background:${recBg};color:${recColor};white-space:nowrap;">${recLabel}</span></td>
            <td style="text-align:right;font-family:var(--font-mono);color:var(--text-secondary);">${r.analysisPrice ? '$' + parseFloat(r.analysisPrice).toFixed(2) : '—'}</td>
            <td style="text-align:right;font-family:var(--font-mono);color:var(--text-primary);">${r.priceTarget ? '$' + parseFloat(r.priceTarget).toFixed(2) : '—'}</td>
            <td style="text-align:right;font-family:var(--font-mono);font-weight:700;color:${upsideColor};">${upsideStr}</td>
        `;
        tbody.appendChild(tr);
    });
}

// ── Research Report Modal ──────────────────────────────────────────

async function loadResearchReports() {
    const data = await fetch('/api/reports').then(r => r.json());
    researchReports = data;
    renderReportList();
}

let reportModalMode = 'add'; // 'add' | 'edit'
let reportModalEditKey = null;

function openAddReportModal() {
    reportModalMode = 'add';
    reportModalEditKey = null;
    document.getElementById('report-modal-title').textContent = 'New Research Report';
    document.getElementById('report-form').reset();
    document.getElementById('rform-edit-key').value = '';
    document.getElementById('rform-key').readOnly = false;
    document.getElementById('rform-key').style.opacity = '1';
    document.getElementById('rform-error').style.display = 'none';
    setReportFormTab('info');
    document.getElementById('report-modal').classList.add('active');
}

function openEditReportModal(key) {
    const r = researchReports[key];
    if (!r) return;
    reportModalMode = 'edit';
    reportModalEditKey = key;
    document.getElementById('report-modal-title').textContent = `Edit Report — ${key}`;
    document.getElementById('rform-edit-key').value = key;
    document.getElementById('rform-key').value = key;
    document.getElementById('rform-key').readOnly = true;
    document.getElementById('rform-key').style.opacity = '0.5';
    document.getElementById('rform-ticker').value = r.ticker || '';
    document.getElementById('rform-company').value = r.companyName || '';
    document.getElementById('rform-subtitle').value = r.subtitle || '';
    document.getElementById('rform-sector').value = r.sector || '';
    document.getElementById('rform-rating').value = r.rating || '';
    document.getElementById('rform-prepared-by').value = r.preparedBy || '';
    document.getElementById('rform-audited-by').value = r.auditedBy || '';
    document.getElementById('rform-price-target').value = r.priceTarget || '';
    document.getElementById('rform-analysis-price').value = r.analysisPrice || '';
    document.getElementById('rform-is-positive').checked = !!r.isPositive;
    document.getElementById('rform-en-overview').value = r.en_overview || '';
    document.getElementById('rform-th-overview').value = r.th_overview || '';
    document.getElementById('rform-en-dcf').value = r.en_dcf || '';
    document.getElementById('rform-th-dcf').value = r.th_dcf || '';
    document.getElementById('rform-error').style.display = 'none';
    setReportFormTab('info');
    document.getElementById('report-modal').classList.add('active');
}

function closeReportModal() {
    document.getElementById('report-modal').classList.remove('active');
}

function setReportFormTab(tab) {
    const panels = { info: 'rform-panel-info', content: 'rform-panel-content' };
    const tabBtns = { info: 'rform-tab-info', content: 'rform-tab-content' };
    Object.keys(panels).forEach(t => {
        document.getElementById(panels[t]).style.display = t === tab ? '' : 'none';
        const btn = document.getElementById(tabBtns[t]);
        if (t === tab) {
            btn.style.color = 'var(--accent-neon)';
            btn.style.borderBottomColor = 'var(--accent-neon)';
        } else {
            btn.style.color = 'var(--text-secondary)';
            btn.style.borderBottomColor = 'transparent';
        }
    });
}

async function saveReport(event) {
    event.preventDefault();
    const errEl = document.getElementById('rform-error');
    errEl.style.display = 'none';

    const payload = {
        report_key: document.getElementById('rform-key').value.trim(),
        ticker: document.getElementById('rform-ticker').value.trim().toUpperCase(),
        company_name: document.getElementById('rform-company').value.trim(),
        subtitle: document.getElementById('rform-subtitle').value.trim(),
        sector: document.getElementById('rform-sector').value.trim() || 'Other Sectors',
        rating: document.getElementById('rform-rating').value.trim(),
        prepared_by: document.getElementById('rform-prepared-by').value.trim(),
        audited_by: document.getElementById('rform-audited-by').value.trim(),
        price_target: parseFloat(document.getElementById('rform-price-target').value) || null,
        analysis_price: parseFloat(document.getElementById('rform-analysis-price').value) || null,
        is_positive: document.getElementById('rform-is-positive').checked,
        en_overview: document.getElementById('rform-en-overview').value,
        th_overview: document.getElementById('rform-th-overview').value,
        en_dcf: document.getElementById('rform-en-dcf').value,
        th_dcf: document.getElementById('rform-th-dcf').value,
    };

    if (!payload.report_key || !payload.ticker || !payload.company_name) {
        errEl.textContent = 'Report Key, Ticker, and Company Name are required.';
        errEl.style.display = 'block';
        return;
    }

    try {
        let res;
        if (reportModalMode === 'add') {
            res = await fetch('/api/research-report', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        } else {
            res = await fetch(`/api/research-report?key=${encodeURIComponent(reportModalEditKey)}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        }
        const data = await res.json();
        if (!res.ok || data.error) throw new Error(data.error || 'Server error');
        closeReportModal();
        await loadResearchReports();
        if (reportModalMode === 'add') {
            selectReport(payload.report_key);
        } else {
            renderReport();
        }
    } catch (err) {
        errEl.textContent = err.message;
        errEl.style.display = 'block';
    }
}

async function deleteReport(key) {
    if (!confirm(`Delete research report "${key}"? This cannot be undone.`)) return;
    try {
        const res = await fetch(`/api/research-report?key=${encodeURIComponent(key)}`, { method: 'DELETE' });
        const data = await res.json();
        if (!res.ok || data.error) throw new Error(data.error || 'Server error');
        if (activeReport === key) {
            const remaining = Object.keys(researchReports).filter(k => k !== key);
            activeReport = remaining.length > 0 ? remaining[0] : null;
        }
        await loadResearchReports();
        renderReport();
    } catch (err) {
        alert('Delete failed: ' + err.message);
    }
}

function renderReport() {
    const reportData = researchReports[activeReport];
    if (!reportData) {
        document.getElementById("report-article-content").innerHTML =
            `<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:80px 20px;gap:12px;opacity:0.5;">
                <svg viewBox="0 0 24 24" style="width:40px;height:40px;fill:var(--text-secondary);"><path d="M12 3L1 9l4 2.18v6L12 21l7-3.82v-6l2-1.09L12 3zm6.8 9.18L12 15.9l-6.8-3.72V10.1l6.8 3.71 6.8-3.71v2.08zM12 11.9L5.2 8.18 12 4.45l6.8 3.73L12 11.9z"/></svg>
                <p style="color:var(--text-secondary);font-size:0.88rem;margin:0;">Select a report from the sidebar to begin reading.</p>
            </div>`;
        return;
    }

    // Update Ribbon values
    document.getElementById("viewer-main-title").innerText = `${reportData.companyName} (${reportData.ticker})`;
    document.getElementById("viewer-subtitle").innerText = reportData.subtitle;
    document.getElementById("viewer-rating").innerText = reportData.rating;

    const ratingBadge = document.getElementById("viewer-rating");
    if (reportData.isPositive) {
        ratingBadge.className = "meta-item-val rating-badge positive";
    } else {
        ratingBadge.className = "meta-item-val rating-badge negative";
    }

    const langLabel = activeLanguage === "en" ? "Serene (English Feed)" : "Serene (Localized Thai)";
    document.getElementById("meta-val-lang").innerText = langLabel;

    // Load actual localized HTML body content
    const reportContainer = document.getElementById("report-article-content");
    const contentKey = activeLanguage + "_" + activeReportTab;
    const rawText = reportData[contentKey];
    if (rawText) {
        reportContainer.innerHTML = marked.parse(rawText);
    } else {
        reportContainer.innerHTML = "<em>Content not available for this tab.</em>";
    }

    // Fetch and update the live stock price in report ribbon
    updateReportLivePrice(reportData.ticker);
}

// ==========================================================================
// REAL-TIME API FETCH ENGINE (YAHOO FINANCE VIA PYTHON PROXY)
// ==========================================================================
async function fetchLivePrices() {
    const btnText = document.getElementById("btn-refresh-text");
    const btnIcon = document.getElementById("btn-refresh-icon");
    if (btnText) btnText.innerText = "Refreshing...";
    if (btnIcon) btnIcon.style.animation = "spin 1s linear infinite";

    // 1. Fetch live USD/THB exchange rate from Yahoo Finance
    const ratePromise = (async () => {
        try {
            const response = await fetch(`/api/stock?ticker=USDTHB=X`);
            if (response.ok) {
                const data = await response.json();
                if (data.price) {
                    exchangeRateUSDTHB = data.price;
                    console.log("Updated USD/THB exchange rate to:", exchangeRateUSDTHB);
                }
            }
        } catch (err) {
            console.warn("Failed to fetch live USD/THB rate:", err);
        }
    })();

    // 2. Fetch prices for public stock holdings
    const promises = holdings.map(async (pos) => {
        if (pos.ticker.includes(" ") || pos.ticker.startsWith("KAsset")) return; // Skip custom/private tickers
        try {
            const response = await fetch(`/api/stock?ticker=${pos.ticker}`);
            if (!response.ok) throw new Error("API error");
            const data = await response.json();
            if (data.price) {
                pos.currentPrice = data.price;
                // Keep longName if available (except for fake FPS ticker)
                if (data.longName && pos.ticker !== "FPS") {
                    pos.companyName = data.longName;
                }
            }
        } catch (err) {
            console.warn(`Failed to fetch live price for ${pos.ticker}:`, err);
        }
    });

    // Wait for all to complete
    await Promise.all([...promises, ratePromise]);

    // Save prices to localStorage cache for instant render on next page load
    const priceCache = { __ts__: Date.now(), __rate__: exchangeRateUSDTHB };
    holdings.forEach(h => { priceCache[h.ticker] = h.currentPrice; });
    localStorage.setItem('genie-price-cache', JSON.stringify(priceCache));

    // Update the UI
    updateDashboard();

    // Reset button state
    if (btnText) btnText.innerText = "Refresh Prices";
    if (btnIcon) btnIcon.style.animation = "none";
}

function toggleCurrency(curr) {
    displayCurrency = curr;
    
    // Toggle active state on UI buttons
    const usdBtn = document.getElementById("cur-usd");
    const thbBtn = document.getElementById("cur-thb");
    if (usdBtn && thbBtn) {
        usdBtn.classList.toggle("active", curr === "USD");
        thbBtn.classList.toggle("active", curr === "THB");
    }
    
    // Re-render UI
    updateDashboard();
}

async function updateReportLivePrice(ticker) {
    const livePriceEl = document.getElementById("meta-val-live-price");
    if (!livePriceEl) return;
    livePriceEl.innerText = "Loading...";

    try {
        const response = await fetch(`/api/stock?ticker=${ticker}`);
        if (!response.ok) throw new Error("API error");
        const data = await response.json();
        if (data.price) {
            livePriceEl.innerText = `$${data.price.toFixed(2)} USD`;
        } else {
            livePriceEl.innerText = "N/A";
        }
    } catch (err) {
        console.warn(`Failed to fetch live report price for ${ticker}:`, err);
        livePriceEl.innerText = "Error";
    }
}

// ==========================================================================
// HELPER SYSTEM UTILITIES
// ==========================================================================
function formatNumber(number, decimals = 0) {
    return number.toLocaleString("en-US", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

function formatShares(shares) {
    return shares.toLocaleString("en-US", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 8
    });
}

// ==========================================================================
// PORTFOLIO MANAGEMENT
// ==========================================================================
function populateDropdowns() {
    // Populate portfolio filter
    const portfolioFilter = document.getElementById("portfolio-filter");
    if (portfolioFilter) {
        portfolioFilter.innerHTML = '<option value="ALL">All</option>';
        // Show only sub-portfolios (those with a parent)
        portfoliosList.filter(p => p.parentId !== null).forEach(p => {
            const option = document.createElement("option");
            option.value = p.name;
            option.text = p.name;
            portfolioFilter.appendChild(option);
        });
    }

    // Populate ingest sub-portfolio dropdown (only sub-portfolios!)
    const ingestPortfolio = document.getElementById("ingest-portfolio");
    if (ingestPortfolio) {
        ingestPortfolio.innerHTML = '<option value="" disabled selected>Select Sub-Portfolio...</option>';
        // Sub-portfolios have parentId !== null
        const subPorts = portfoliosList.filter(p => p.parentId !== null);
        subPorts.forEach(p => {
            const option = document.createElement("option");
            option.value = p.name;
            option.text = `${p.parentName} - ${p.name}`;
            ingestPortfolio.appendChild(option);
        });
    }
    
    // Populate Add Portfolio parent dropdown
    const newPortParent = document.getElementById("new-port-parent");
    if (newPortParent) {
        newPortParent.innerHTML = '<option value="">None (Create as Parent Portfolio)</option>';
        // Parent portfolios have parentId === null
        const parentPorts = portfoliosList.filter(p => p.parentId === null);
        parentPorts.forEach(p => {
            const option = document.createElement("option");
            option.value = p.id;
            option.text = p.name;
            newPortParent.appendChild(option);
        });
    }
}

function openAddPortfolioModal() {
    document.getElementById("add-portfolio-modal").classList.add("active");
}

function closeAddPortfolioModal() {
    document.getElementById("add-portfolio-modal").classList.remove("active");
}

function handleAddPortfolio(event) {
    event.preventDefault();
    const name = document.getElementById("new-port-name").value.trim();
    const category = document.getElementById("new-port-category").value;
    const parentIdVal = document.getElementById("new-port-parent").value;
    const parentId = parentIdVal === "" ? null : parseInt(parentIdVal);
    
    fetch('/api/portfolios', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, category, parentId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeAddPortfolioModal();
            document.getElementById("add-portfolio-form").reset();
            
            // Re-fetch all portfolios and re-populate
            fetch('/api/portfolios')
                .then(r => r.json())
                .then(pData => {
                    portfoliosList = pData;
                    populateDropdowns();
                    updateDashboard();
                });
            
            alert("Portfolio created successfully!");
        } else {
            alert("Error adding portfolio: " + data.error);
        }
    })
    .catch(err => {
        console.error("Error:", err);
        alert("Failed to add portfolio");
    });
}

// ==========================================================================
// FEATURE 1: TRANSACTIONS (ACTIVITY LOG)
// ==========================================================================
let transactionsList = [];
let txCurrentPage = 1;
let txRowsPerPage = 25;
let txDatePreset = 'all';
let txTypeFilter = 'all';

function setTxPreset(preset) {
    txDatePreset = preset;
    txCurrentPage = 1;

    // Update active button state
    ['all', 'this_year', 'last_3m', 'this_month', 'custom'].forEach(p => {
        const btn = document.getElementById(`tx-preset-${p}`);
        if (btn) btn.classList.toggle('active', p === preset);
    });

    renderTransactions();
}

function setTxPage(page) {
    txCurrentPage = page;
    renderTransactions();
}

function setTxRowsPerPage(val) {
    txRowsPerPage = val === 'all' ? 'all' : parseInt(val);
    txCurrentPage = 1;
    renderTransactions();
}

function setTxTypeFilter(type) {
    txTypeFilter = type;
    txCurrentPage = 1;
    ['all', 'BUY', 'SELL', 'TRANSFER_IN', 'TRANSFER_OUT', 'DIVIDEND'].forEach(t => {
        const btn = document.getElementById(`tx-type-${t}`);
        if (btn) btn.classList.toggle('active', t === type);
    });
    renderTransactions();
}

function loadTransactions() {
    const tbody = document.getElementById("transactions-table-body");
    tbody.innerHTML = `<tr><td colspan="9" class="text-center" style="color: var(--text-secondary); text-align: center; padding: 20px;">🔄 Loading transaction history...</td></tr>`;

    fetch('/api/transactions')
        .then(res => res.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            transactionsList = data;
            renderTransactions();
        })
        .catch(err => {
            console.error("Error loading transactions:", err);
            tbody.innerHTML = `<tr><td colspan="9" class="text-center" style="color: #EF4444; text-align: center; padding: 20px;">❌ Failed to load transactions: ${err.message}</td></tr>`;
        });
}

function renderTransactions() {
    const tbody = document.getElementById("transactions-table-body");
    tbody.innerHTML = "";

    // 1. Search filter
    const filterText = (document.getElementById("tx-search-input")?.value || "").toUpperCase();

    // 2. Date range filter
    const now = new Date();
    let dateFrom = null;
    let dateTo = null;

    if (txDatePreset === 'this_month') {
        dateFrom = new Date(now.getFullYear(), now.getMonth(), 1);
    } else if (txDatePreset === 'last_3m') {
        dateFrom = new Date(now.getFullYear(), now.getMonth() - 3, now.getDate());
    } else if (txDatePreset === 'this_year') {
        dateFrom = new Date(now.getFullYear(), 0, 1);
    } else if (txDatePreset === 'custom') {
        const fromVal = document.getElementById("tx-date-from")?.value;
        const toVal = document.getElementById("tx-date-to")?.value;
        if (fromVal) dateFrom = new Date(fromVal);
        if (toVal) { dateTo = new Date(toVal); dateTo.setHours(23, 59, 59); }
    }

    const filtered = transactionsList.filter(t => {
        if (filterText && !t.ticker.toUpperCase().includes(filterText) && !t.companyName.toUpperCase().includes(filterText)) return false;
        if (txTypeFilter !== 'all' && t.type !== txTypeFilter) return false;
        if (dateFrom || dateTo) {
            const txDate = new Date(t.transactionDate);
            if (dateFrom && txDate < dateFrom) return false;
            if (dateTo && txDate > dateTo) return false;
        }
        return true;
    });

    // 3. Pagination
    const total = filtered.length;
    const rpp = txRowsPerPage === 'all' ? total : txRowsPerPage;
    const totalPages = rpp > 0 ? Math.max(1, Math.ceil(total / rpp)) : 1;
    txCurrentPage = Math.min(Math.max(1, txCurrentPage), totalPages);
    const start = (txCurrentPage - 1) * rpp;
    const paginated = txRowsPerPage === 'all' ? filtered : filtered.slice(start, start + rpp);

    // Update pagination UI
    const pageInfo = document.getElementById("tx-page-info");
    const countLabel = document.getElementById("tx-count-label");
    const prevBtn = document.getElementById("tx-btn-prev");
    const nextBtn = document.getElementById("tx-btn-next");
    if (pageInfo) pageInfo.innerText = total > 0 ? `Page ${txCurrentPage} of ${totalPages}` : "";
    if (countLabel) countLabel.innerText = `of ${total} entries`;
    if (prevBtn) prevBtn.disabled = txCurrentPage <= 1;
    if (nextBtn) nextBtn.disabled = txCurrentPage >= totalPages;

    if (paginated.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" style="color: var(--text-secondary); text-align: center; padding: 24px;">No transactions found.</td></tr>`;
        return;
    }

    const typeMeta = {
        BUY:          { label: "BUY",      bg: "rgba(16,185,129,0.1)",  color: "#10B981" },
        SELL:         { label: "SELL",     bg: "rgba(239,68,68,0.1)",   color: "#EF4444" },
        TRANSFER_IN:  { label: "TRSF IN",  bg: "rgba(59,130,246,0.1)",  color: "#3B82F6" },
        TRANSFER_OUT: { label: "TRSF OUT", bg: "rgba(245,158,11,0.1)",  color: "#F59E0B" },
        DIVIDEND:     { label: "DIV",      bg: "rgba(168,85,247,0.1)",  color: "#A855F7" },
    };

    paginated.forEach(t => {
        let dateStr = (t.transactionDate || "").replace("T", " ").substring(0, 16);

        const meta = typeMeta[t.type] || { label: t.type, bg: "rgba(100,100,100,0.1)", color: "var(--text-secondary)" };
        const typeBadge = `<span style="background:${meta.bg};color:${meta.color};padding:4px 8px;border-radius:4px;font-weight:600;font-size:0.75rem;">${meta.label}</span>`;

        let price = parseFloat(t.price);
        let displayPrice = price;
        let sym = t.currency === "THB" ? "฿" : "$";
        if (displayCurrency === "THB" && t.currency === "USD") { displayPrice = price * exchangeRateUSDTHB; sym = "฿"; }
        else if (displayCurrency === "USD" && t.currency === "THB") { displayPrice = price / exchangeRateUSDTHB; sym = "$"; }

        const formattedPrice = sym + displayPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        const formattedQty = formatShares(Math.abs(parseFloat(t.shares)));

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td style="color:var(--text-secondary);font-family:var(--font-mono);font-size:0.85rem;">${dateStr}</td>
            <td style="font-weight:700;color:var(--accent-neon);">${t.ticker}</td>
            <td style="color:var(--text-primary);">${t.companyName}</td>
            <td>${typeBadge}</td>
            <td class="text-right" style="font-family:var(--font-mono);font-weight:500;color:var(--text-primary);">${formattedQty}</td>
            <td class="text-right" style="font-family:var(--font-mono);color:var(--text-secondary);">${formattedPrice}</td>
            <td style="color:var(--text-secondary);font-size:0.85rem;">${t.currency}</td>
            <td><span style="font-size:0.78rem;background:var(--bg-card-solid);border:1px solid var(--border-dim);padding:2px 7px;border-radius:4px;color:var(--text-primary);font-weight:500;">${t.portfolio}</span></td>
            <td style="white-space:nowrap;">
                <button onclick="openEditTransactionModal(${t.id})" class="tx-action-btn" title="Edit"><svg viewBox="0 0 24 24" style="width:14px;height:14px;fill:currentColor;"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg></button>
                <button onclick="deleteTransaction(${t.id})" class="tx-action-btn tx-action-delete" title="Delete"><svg viewBox="0 0 24 24" style="width:14px;height:14px;fill:currentColor;"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg></button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function openResearchFromHolding(reportKey) {
    switchTab('research');
    setTimeout(() => {
        selectReport(reportKey);
    }, 100);
}

function filterTransactions() {
    txCurrentPage = 1;
    renderTransactions();
}

function openEditTransactionModal(txId) {
    const tx = transactionsList.find(t => t.id === txId);
    if (!tx) return;

    document.getElementById('edit-tx-id').value = tx.id;
    document.getElementById('edit-tx-type').value = tx.type;
    document.getElementById('edit-tx-currency').value = tx.currency;
    document.getElementById('edit-tx-shares').value = Math.abs(parseFloat(tx.shares));
    document.getElementById('edit-tx-price').value = parseFloat(tx.price);
    document.getElementById('edit-tx-date').value = (tx.transactionDate || '').substring(0, 10);
    document.getElementById('edit-tx-meta').textContent = `${tx.ticker} · ${tx.companyName} · ${tx.portfolio}`;
    document.getElementById('edit-tx-error').style.display = 'none';

    document.getElementById('edit-transaction-modal').classList.add('active');
}

function closeEditTransactionModal() {
    document.getElementById('edit-transaction-modal').classList.remove('active');
}

async function saveEditTransaction(event) {
    event.preventDefault();
    const errEl = document.getElementById('edit-tx-error');
    errEl.style.display = 'none';

    const id = document.getElementById('edit-tx-id').value;
    const payload = {
        type: document.getElementById('edit-tx-type').value,
        shares: parseFloat(document.getElementById('edit-tx-shares').value),
        price: parseFloat(document.getElementById('edit-tx-price').value),
        currency: document.getElementById('edit-tx-currency').value,
        transactionDate: document.getElementById('edit-tx-date').value,
    };

    try {
        const res = await fetch(`/api/transaction?id=${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok || data.error) throw new Error(data.error || 'Failed to save');
        closeEditTransactionModal();
        loadTransactions();
        updateDashboard();
    } catch (err) {
        errEl.textContent = err.message;
        errEl.style.display = 'block';
    }
}

async function deleteTransaction(txId) {
    const tx = transactionsList.find(t => t.id === txId);
    const label = tx ? `${tx.ticker} ${tx.type} ${Math.abs(parseFloat(tx.shares))} shares` : `#${txId}`;
    if (!confirm(`Delete transaction: ${label}?\n\nThis cannot be undone.`)) return;

    try {
        const res = await fetch(`/api/transaction?id=${txId}`, { method: 'DELETE' });
        const data = await res.json();
        if (!res.ok || data.error) throw new Error(data.error || 'Delete failed');
        loadTransactions();
        updateDashboard();
    } catch (err) {
        alert(`Error: ${err.message}`);
    }
}

function exportTransactionsCSV() {
    // Build same filtered set as current view (all pages, not just current page)
    const filterText = (document.getElementById("tx-search-input")?.value || "").toUpperCase();
    const now = new Date();
    let dateFrom = null, dateTo = null;

    if (txDatePreset === 'this_month') {
        dateFrom = new Date(now.getFullYear(), now.getMonth(), 1);
    } else if (txDatePreset === 'last_3m') {
        dateFrom = new Date(now.getFullYear(), now.getMonth() - 3, now.getDate());
    } else if (txDatePreset === 'this_year') {
        dateFrom = new Date(now.getFullYear(), 0, 1);
    } else if (txDatePreset === 'custom') {
        const fromVal = document.getElementById("tx-date-from")?.value;
        const toVal = document.getElementById("tx-date-to")?.value;
        if (fromVal) dateFrom = new Date(fromVal);
        if (toVal) { dateTo = new Date(toVal); dateTo.setHours(23, 59, 59); }
    }

    const rows = transactionsList.filter(t => {
        if (filterText && !t.ticker.toUpperCase().includes(filterText) && !t.companyName.toUpperCase().includes(filterText)) return false;
        if (txTypeFilter !== 'all' && t.type !== txTypeFilter) return false;
        if (dateFrom || dateTo) {
            const txDate = new Date(t.transactionDate);
            if (dateFrom && txDate < dateFrom) return false;
            if (dateTo && txDate > dateTo) return false;
        }
        return true;
    });

    const headers = ['Date', 'Ticker', 'Company Name', 'Type', 'Shares', 'Price', 'Currency', 'Portfolio'];
    const lines = [headers.join(',')];
    rows.forEach(t => {
        const date = (t.transactionDate || '').substring(0, 10);
        const shares = Math.abs(parseFloat(t.shares));
        const price = parseFloat(t.price);
        const companyEsc = `"${(t.companyName || '').replace(/"/g, '""')}"`;
        const portEsc = `"${(t.portfolio || '').replace(/"/g, '""')}"`;
        lines.push([date, t.ticker, companyEsc, t.type, shares, price, t.currency, portEsc].join(','));
    });

    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transactions_${new Date().toISOString().substring(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ==========================================================================
// FEATURE 4: DETAILED SINGLE-STOCK VIEW
// ==========================================================================
let activeChartTicker = null;
let activeChartRange = "1mo";
let stockDetailChartInstance = null;

async function openStockDetail(ticker) {
    activeChartTicker = ticker;
    activeChartRange = "1mo";
    
    // Show modal
    const modal = document.getElementById("stock-detail-modal");
    modal.classList.add("active");
    
    // Clear old chart
    if (stockDetailChartInstance) {
        stockDetailChartInstance.destroy();
        stockDetailChartInstance = null;
    }
    
    // Load metadata stats
    document.getElementById("modal-stock-ticker").innerText = ticker;
    document.getElementById("modal-stock-name").innerText = "Loading...";
    document.getElementById("modal-stock-sector").innerText = "";
    document.getElementById("modal-stock-price").innerText = "$0.00";
    document.getElementById("modal-stock-prev-close").innerText = "$0.00";
    document.getElementById("modal-stock-52w").innerText = "$0.00 - $0.00";
    document.getElementById("modal-stock-day").innerText = "$0.00 - $0.00";
    
    updateRangeButtonStyles();

    try {
        const response = await fetch(`/api/stock?ticker=${ticker}`);
        if (!response.ok) throw new Error("Failed to load stock data");
        const data = await response.json();
        
        const sym = data.currency === "THB" ? "฿" : "$";
        
        document.getElementById("modal-stock-name").innerText = data.longName || data.ticker;
        
        // Find sector from existing holdings if not returned
        const existing = holdings.find(h => h.ticker === ticker);
        document.getElementById("modal-stock-sector").innerText = existing ? existing.sector : "Technology";
        
        document.getElementById("modal-stock-price").innerText = sym + (data.price ? data.price.toFixed(2) : "0.00");
        document.getElementById("modal-stock-prev-close").innerText = sym + (data.previousClose ? data.previousClose.toFixed(2) : "0.00");
        
        if (data.fiftyTwoWeekLow && data.fiftyTwoWeekHigh) {
            document.getElementById("modal-stock-52w").innerText = `${sym}${data.fiftyTwoWeekLow.toFixed(2)} - ${sym}${data.fiftyTwoWeekHigh.toFixed(2)}`;
        } else {
            document.getElementById("modal-stock-52w").innerText = "N/A";
        }
        
        if (data.dayLow && data.dayHigh) {
            document.getElementById("modal-stock-day").innerText = `${sym}${data.dayLow.toFixed(2)} - ${sym}${data.dayHigh.toFixed(2)}`;
        } else {
            document.getElementById("modal-stock-day").innerText = "N/A";
        }
    } catch (err) {
        console.error("Error fetching stock metadata:", err);
    }
    
    // Load chart data
    fetchStockChartData();
}

function closeStockDetailModal() {
    document.getElementById("stock-detail-modal").classList.remove("active");
    if (stockDetailChartInstance) {
        stockDetailChartInstance.destroy();
        stockDetailChartInstance = null;
    }
}

async function fetchStockChartData() {
    const canvas = document.getElementById("stockDetailChart");
    if (!canvas) return;
    
    const ctx = canvas.getContext("2d");
    
    try {
        const response = await fetch(`/api/stock/chart?ticker=${activeChartTicker}&range=${activeChartRange}`);
        if (!response.ok) throw new Error("Chart API error");
        const data = await response.json();
        
        if (stockDetailChartInstance) {
            stockDetailChartInstance.destroy();
        }
        
        // Prepare chart labels (dates)
        const labels = data.timestamps.map(ts => {
            const date = new Date(ts * 1000);
            if (activeChartRange === "1d") {
                return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
            }
            return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
        });
        
        // Filter out null values from prices
        const prices = data.close.map((p, i) => p !== null ? p : (data.close[i-1] || data.close[i+1] || 0));
        
        // Decide glowing chart line color based on performance
        const firstPrice = prices[0] || 0;
        const lastPrice = prices[prices.length - 1] || 0;
        const isUp = lastPrice >= firstPrice;
        
        const strokeColor = isUp ? "#10B981" : "#EF4444"; // Green vs Red
        const glowColor = isUp ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)";
        
        const gradient = ctx.createLinearGradient(0, 0, 0, 250);
        gradient.addColorStop(0, glowColor);
        gradient.addColorStop(1, "rgba(3, 7, 18, 0)");
        
        stockDetailChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: activeChartTicker,
                    data: prices,
                    borderColor: strokeColor,
                    borderWidth: 2,
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.2,
                    pointRadius: prices.length > 50 ? 0 : 2,
                    pointHoverRadius: 5,
                    pointBackgroundColor: strokeColor,
                    pointBorderColor: "#fff",
                    shadowColor: strokeColor,
                    shadowBlur: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                legend: { display: false },
                scales: {
                    xAxes: [{
                        gridLines: { color: "rgba(255, 255, 255, 0.03)" },
                        ticks: { fontColor: "rgba(255, 255, 255, 0.4)", fontSize: 10, maxTicksLimit: 8 }
                    }],
                    yAxes: [{
                        gridLines: { color: "rgba(255, 255, 255, 0.03)" },
                        ticks: { 
                            fontColor: "rgba(255, 255, 255, 0.4)", 
                            fontSize: 10,
                            callback: function(value) {
                                return value.toLocaleString();
                            }
                        }
                    }]
                },
                tooltips: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: "rgba(3, 7, 18, 0.9)",
                    titleFontColor: strokeColor,
                    bodyFontColor: "#fff",
                    borderColor: "rgba(255, 255, 255, 0.1)",
                    borderWidth: 1,
                    displayColors: false,
                    callbacks: {
                        label: function(tooltipItem) {
                            return `Price: ` + parseFloat(tooltipItem.yLabel).toFixed(2);
                        }
                    }
                }
            }
        });
    } catch (err) {
        console.error("Error loading stock chart:", err);
    }
}

function changeStockChartRange(range) {
    activeChartRange = range;
    updateRangeButtonStyles();
    fetchStockChartData();
}

function updateRangeButtonStyles() {
    const ranges = ['1d', '1mo', '3mo', '1y'];
    ranges.forEach(r => {
        const btn = document.getElementById(`btn-range-${r}`);
        if (!btn) return;
        if (r === activeChartRange) {
            btn.style.border = "1px solid var(--accent-neon)";
            btn.style.background = "rgba(0, 240, 255, 0.05)";
            btn.style.color = "var(--accent-neon)";
        } else {
            btn.style.border = "1px solid rgba(255, 255, 255, 0.1)";
            btn.style.background = "transparent";
            btn.style.color = "var(--text-secondary)";
        }
    });
}

// ==========================================================================
// EXCEL TRANSACTION IMPORT & TEMPLATE DOWNLOAD
// ==========================================================================
let parsedExcelTransactions = [];

function copyTemplateAsCSV() {
    const csvContent = 
`Date,Ticker,Company Name,Sector,Sub-Portfolio,Type,Shares,Price,Currency
2026-06-14 10:00:00,AAPL,Apple Inc.,Technology,Dime,BUY,10,180.5,USD
2026-06-14 14:30:00,TSLA,Tesla Inc.,Consumer Cyclical,WeBull,SELL,5,175.0,USD
2026-06-14 16:00:00,7-11,CP All,Consumer Defensive,Tax Saving Fund,BUY,100,58.25,THB`;

    navigator.clipboard.writeText(csvContent).then(() => {
        alert("Standard CSV template copied to clipboard!\nYou can paste it into Excel or any text editor, then save it as an Excel (.xlsx) or CSV file.");
    }).catch(err => {
        console.error("Failed to copy template: ", err);
        // Fallback using prompt
        window.prompt("Could not copy automatically. Please copy the CSV text below manually:", csvContent);
    });
}

function setupDragAndDrop() {
    const dropZone = document.getElementById("upload-drop-zone");
    if (!dropZone) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('drop-zone--over'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('drop-zone--over'), false);
    });

    dropZone.addEventListener('drop', handleDrop, false);

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            const input = document.getElementById("excel-file-input");
            if (input) {
                input.files = files;
                handleExcelUpload({ target: input });
            }
        }
    }
}

function handleExcelUpload(event) {
    if (typeof XLSX === 'undefined') {
        alert("Error: SheetJS library (XLSX) is not loaded.\nPlease check your internet connection or check the browser console for network errors.");
        return;
    }
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, { type: 'array' });
            
            const sheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[sheetName];
            
            const rows = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
            if (rows.length <= 1) {
                alert("The Excel file is empty or missing data rows.");
                cancelExcelUpload();
                return;
            }
            
            const headers = rows[0].map(h => String(h).trim().toLowerCase());
            
            const colIndices = {
                date: headers.indexOf("date"),
                ticker: headers.indexOf("ticker"),
                companyName: headers.indexOf("company name"),
                sector: headers.indexOf("sector"),
                portfolio: headers.indexOf("sub-portfolio"),
                type: headers.indexOf("type"),
                shares: headers.indexOf("shares"),
                price: headers.indexOf("price"),
                currency: headers.indexOf("currency")
            };
            
            const requiredCols = ["ticker", "portfolio", "type", "shares", "price"];
            for (const col of requiredCols) {
                if (colIndices[col] === -1) {
                    alert(`Missing required column in Excel: "${col}"`);
                    cancelExcelUpload();
                    return;
                }
            }
            
            parsedExcelTransactions = [];
            let errorCount = 0;
            let errorMsg = "";
            
            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                if (!row || row.length === 0 || row.every(cell => cell === null || cell === undefined || cell === "")) {
                    continue;
                }
                
                const getCell = (colKey) => {
                    const idx = colIndices[colKey];
                    return idx !== -1 && row[idx] !== undefined && row[idx] !== null ? String(row[idx]).trim() : "";
                };
                
                const ticker = getCell("ticker").toUpperCase();
                const portfolio = getCell("portfolio");
                const type = getCell("type").toUpperCase();
                const sharesVal = parseFloat(getCell("shares"));
                const priceVal = parseFloat(getCell("price"));
                
                let date = getCell("date");
                let companyName = getCell("companyName");
                let sector = getCell("sector");
                let currency = getCell("currency").toUpperCase();
                
                if (!ticker) {
                    errorCount++;
                    errorMsg += `Row ${i+1}: Ticker is empty\n`;
                    continue;
                }
                if (!portfolio) {
                    errorCount++;
                    errorMsg += `Row ${i+1} (${ticker}): Sub-Portfolio is empty\n`;
                    continue;
                }
                
                const validPortfolios = ["Dime", "WeBull", "Tax Saving Fund", "Provident Fund"];
                const matchingPortfolio = validPortfolios.find(p => p.toLowerCase() === portfolio.toLowerCase());
                if (!matchingPortfolio) {
                    errorCount++;
                    errorMsg += `Row ${i+1} (${ticker}): Portfolio must be one of [Dime, WeBull, Tax Saving Fund, Provident Fund]\n`;
                    continue;
                }
                
                if (type !== "BUY" && type !== "SELL") {
                    errorCount++;
                    errorMsg += `Row ${i+1} (${ticker}): Type must be BUY or SELL\n`;
                    continue;
                }
                
                if (isNaN(sharesVal) || sharesVal <= 0) {
                    errorCount++;
                    errorMsg += `Row ${i+1} (${ticker}): Shares must be a positive number\n`;
                    continue;
                }
                
                if (isNaN(priceVal) || priceVal <= 0) {
                    errorCount++;
                    errorMsg += `Row ${i+1} (${ticker}): Price must be a positive number\n`;
                    continue;
                }
                
                if (!companyName) companyName = ticker;
                if (!sector) sector = "Technology";
                if (!currency) currency = "USD";
                if (currency !== "USD" && currency !== "THB") currency = "USD";
                
                if (date) {
                    if (!isNaN(date) && parseFloat(date) > 20000 && parseFloat(date) < 60000) {
                        const serial = parseFloat(date);
                        const utc_days  = Math.floor(serial - 25569);
                        const utc_value = utc_days * 86400;                                        
                        const date_info = new Date(utc_value * 1000);
                        const fractional_day = serial - Math.floor(serial) + 0.0000001;
                        let total_seconds = Math.floor(86400 * fractional_day);
                        const seconds = total_seconds % 60;
                        total_seconds -= seconds;
                        const minutes = Math.floor(total_seconds / 60) % 60;
                        const hours = Math.floor(total_seconds / 3600);
                        date_info.setHours(hours, minutes, seconds);
                        
                        const pad = (n) => String(n).padStart(2, '0');
                        date = `${date_info.getFullYear()}-${pad(date_info.getMonth()+1)}-${pad(date_info.getDate())} ${pad(date_info.getHours())}:${pad(date_info.getMinutes())}:${pad(date_info.getSeconds())}`;
                    } else {
                        const parsedDate = new Date(date);
                        if (!isNaN(parsedDate.getTime())) {
                            const pad = (n) => String(n).padStart(2, '0');
                            date = `${parsedDate.getFullYear()}-${pad(parsedDate.getMonth()+1)}-${pad(parsedDate.getDate())} ${pad(parsedDate.getHours())}:${pad(parsedDate.getMinutes())}:${pad(parsedDate.getSeconds())}`;
                        } else {
                            date = "";
                        }
                    }
                }
                
                parsedExcelTransactions.push({
                    date,
                    ticker,
                    companyName,
                    sector,
                    portfolio: matchingPortfolio,
                    type,
                    shares: sharesVal,
                    avgCost: priceVal,
                    currency
                });
            }
            
            if (errorCount > 0) {
                alert(`Found ${errorCount} formatting errors:\n\n${errorMsg.substring(0, 500)}${errorMsg.length > 500 ? '...' : ''}\nPlease fix the Excel file and try again.`);
                cancelExcelUpload();
                return;
            }
            
            if (parsedExcelTransactions.length === 0) {
                alert("No valid transaction rows found in the sheet.");
                cancelExcelUpload();
                return;
            }
            
            renderExcelPreview();
            
        } catch (err) {
            console.error("Error reading excel file:", err);
            alert("Error reading Excel file. Please ensure it is a valid .xlsx or .xls file.");
            cancelExcelUpload();
        }
    };
    reader.readAsArrayBuffer(file);
}

function renderExcelPreview() {
    const previewContainer = document.getElementById("excel-preview-container");
    const previewCount = document.getElementById("preview-count");
    const previewBody = document.getElementById("excel-preview-body");
    
    if (!previewContainer || !previewCount || !previewBody) return;
    
    previewCount.innerText = parsedExcelTransactions.length;
    previewBody.innerHTML = "";
    
    parsedExcelTransactions.forEach(tx => {
        const row = document.createElement("tr");
        
        const typeStyle = tx.type === "BUY" ? "color: #10B981; font-weight: 600;" : "color: #EF4444; font-weight: 600;";
        const currencySymbol = tx.currency === "USD" ? "$" : "฿";
        
        row.innerHTML = `
            <td style="color: var(--text-secondary);">${tx.date || "<i>(Now)</i>"}</td>
            <td style="font-weight: 700; color: var(--text-primary);">${tx.ticker}</td>
            <td>${tx.companyName}</td>
            <td style="${typeStyle}">${tx.type}</td>
            <td class="text-right">${tx.shares.toLocaleString()}</td>
            <td class="text-right">${currencySymbol}${tx.avgCost.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 4})}</td>
            <td>${tx.currency}</td>
            <td><span class="badge" style="background: rgba(255,255,255,0.05); color: var(--text-primary); padding: 2px 6px; border-radius: 4px; font-size: 0.75rem;">${tx.portfolio}</span></td>
        `;
        previewBody.appendChild(row);
    });
    
    previewContainer.style.display = "block";
}

function cancelExcelUpload() {
    const input = document.getElementById("excel-file-input");
    if (input) input.value = "";
    
    const previewContainer = document.getElementById("excel-preview-container");
    if (previewContainer) previewContainer.style.display = "none";
    
    parsedExcelTransactions = [];
}

function confirmExcelUpload() {
    if (parsedExcelTransactions.length === 0) return;
    
    const btn = document.getElementById("btn-confirm-upload");
    const originalText = btn.innerText;
    btn.disabled = true;
    btn.innerText = "⏳ Ingesting...";
    
    fetch('/api/bulk-ingest', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            transactions: parsedExcelTransactions
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Successfully imported ${data.count} transactions!`);
            cancelExcelUpload();
            
            // Re-fetch transactions & holdings
            loadTransactions();
            
            fetch('/api/holdings')
                .then(r => r.json())
                .then(hData => {
                    holdings = hData.map(h => ({...h, currentPrice: h.avgCost}));
                    updateDashboard();
                    fetchLivePrices(); // Update to live price
                });
        } else {
            alert("Import error: " + data.error);
        }
    })
    .catch(err => {
        console.error("Error confirm upload:", err);
        alert("Failed to import transactions.");
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerText = originalText;
    });
}

// ==========================================================================
// FEATURE: STOCK TRANSFERS BETWEEN SUB-PORTFOLIOS
// ==========================================================================
function openTransferStockModal() {
    const modal = document.getElementById("transfer-stock-modal");
    if (!modal) return;
    
    // Clear fields
    document.getElementById("transfer-stock-form").reset();
    document.getElementById("transfer-source-available").innerText = "";
    
    // Populate Ticker select dropdown with tickers from holdings
    const tickerSelect = document.getElementById("transfer-ticker");
    tickerSelect.innerHTML = '<option value="" disabled selected>Select Ticker...</option>';
    
    // Get unique tickers that currently have active shares > 0
    const uniqueTickers = [...new Set(holdings.map(h => h.ticker))].sort();
    
    uniqueTickers.forEach(ticker => {
        const option = document.createElement("option");
        option.value = ticker;
        option.text = ticker;
        tickerSelect.appendChild(option);
    });
    
    modal.classList.add("active");
}

function closeTransferStockModal() {
    const modal = document.getElementById("transfer-stock-modal");
    if (modal) modal.classList.remove("active");
}

function onTransferTickerChange() {
    const ticker = document.getElementById("transfer-ticker").value;
    const sourceSelect = document.getElementById("transfer-source");
    sourceSelect.innerHTML = '<option value="" disabled selected>Select Source...</option>';
    
    // Find all portfolios that hold this ticker
    const holdingPorts = holdings.filter(h => h.ticker === ticker);
    
    holdingPorts.forEach(hp => {
        // Find portfolio ID for the portfolio name
        const portObj = portfoliosList.find(p => p.name === hp.portfolio && p.parentId !== null);
        if (portObj) {
            const option = document.createElement("option");
            option.value = portObj.id;
            option.text = `${hp.parentPortfolio || hp.portfolio} - ${hp.portfolio}`;
            // Store shares and average cost in attributes for easy access
            option.setAttribute("data-shares", hp.shares);
            option.setAttribute("data-cost", hp.avgCost);
            sourceSelect.appendChild(option);
        }
    });
    
    document.getElementById("transfer-source-available").innerText = "";
    document.getElementById("transfer-dest").innerHTML = '<option value="" disabled selected>Select Destination...</option>';
}

function onTransferSourceChange() {
    const sourceSelect = document.getElementById("transfer-source");
    const selectedOption = sourceSelect.options[sourceSelect.selectedIndex];
    
    if (!selectedOption) return;
    
    const shares = parseFloat(selectedOption.getAttribute("data-shares"));
    const cost = parseFloat(selectedOption.getAttribute("data-cost"));
    
    document.getElementById("transfer-source-available").innerText = `Available: ${formatShares(shares)} shares (Avg Cost: $${cost.toFixed(2)})`;
    
    // Pre-fill fields
    document.getElementById("transfer-shares").value = shares;
    document.getElementById("transfer-price").value = cost.toFixed(2);
    
    // Populate Destination dropdown with sub-portfolios EXCEPT the source portfolio
    const sourceId = parseInt(sourceSelect.value);
    const destSelect = document.getElementById("transfer-dest");
    destSelect.innerHTML = '<option value="" disabled selected>Select Destination...</option>';
    
    const subPorts = portfoliosList.filter(p => p.parentId !== null && p.id !== sourceId);
    subPorts.forEach(p => {
        const option = document.createElement("option");
        option.value = p.id;
        option.text = `${p.parentName} - ${p.name}`;
        destSelect.appendChild(option);
    });
}

function handleTransferStock(event) {
    event.preventDefault();
    
    const ticker = document.getElementById("transfer-ticker").value;
    const sourcePortfolioId = parseInt(document.getElementById("transfer-source").value);
    const destPortfolioId = parseInt(document.getElementById("transfer-dest").value);
    const shares = parseFloat(document.getElementById("transfer-shares").value);
    const price = parseFloat(document.getElementById("transfer-price").value);
    
    if (sourcePortfolioId === destPortfolioId) {
        alert("Source and Destination portfolios must be different!");
        return;
    }
    
    fetch('/api/transfer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            sourcePortfolioId,
            destPortfolioId,
            ticker,
            shares,
            price
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            alert("Stock transferred successfully!");
            closeTransferStockModal();
            
            // Re-fetch holdings
            fetch('/api/holdings')
                .then(r => r.json())
                .then(hData => {
                    holdings = hData.map(h => ({...h, currentPrice: h.avgCost}));
                    updateDashboard();
                    fetchLivePrices(); // update with real prices
                });
        } else {
            alert("Error transferring stock: " + data.error);
        }
    })
    .catch(err => {
        console.error("Error during transfer:", err);
        alert("Failed to transfer stock.");
    });
}
