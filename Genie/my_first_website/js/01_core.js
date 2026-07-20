// ==========================================================================
// CLIENT-SIDE PORTFOLIO DATABASE & STATE MANAGEMENT
// ==========================================================================
let holdings = [];
let portfoliosList = [];
let categoriesList = [];
let sectorsList = []; // per-user sector master data — [{id, name}]
let cachedParentTotals = {};
let activeParentPortfolio = null;
let activeSubPortfolio = null;

let activeTab = "dashboard";
let activeReport = "mu";
let activeLanguage = "en";
let allocationChart = null;
let displayCurrency = "USD";
let exchangeRateUSDTHB = 32.505;
let exchangeRateEURUSD = 1.08;

// Central currency conversion — all portfolio math goes through here.
// Rates are expressed as USD per 1 unit of each currency; converting A→B
// pivots through USD so adding a new currency is a one-line change.
function convertCurrency(amount, from, to) {
    if (!from || !to || from === to) return amount;
    const usdPerUnit = { USD: 1, THB: 1 / exchangeRateUSDTHB, EUR: exchangeRateEURUSD };
    const f = usdPerUnit[from] ?? 1;
    const t = usdPerUnit[to] ?? 1;
    return amount * (f / t);
}

function currencySymbol(code) {
    return { USD: "$", THB: "฿", EUR: "€" }[code] || "$";
}
let currentSort = { column: null, direction: 'asc' };
let portfolioSort = { column: null, direction: 'asc' };
let isManageMode = false;

// ==========================================================================
// THEME STATE MANAGEMENT (Solarized Light / Dark Switcher)
// ==========================================================================
let activeTheme = localStorage.getItem("genie-portfolio-theme") || "light";

function getBadgeStyle(name) {
    return `style="background:var(--bg-card-solid);color:var(--text-primary);border:1px solid var(--border-color);font-weight:600;"`;
}

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

function sortPortfolioTable(column) {
    if (portfolioSort.column === column) {
        portfolioSort.direction = portfolioSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        portfolioSort.column = column;
        portfolioSort.direction = 'asc';
    }
    renderPortfolioPage();
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
let feedItems = [];              // Daily digest items (macro/news bulletins) — see js/04_research.js
let activeDigestDate = null;     // Digest currently open in the digest reader (see openDigestReader)
let researchFilterMode = 'all'; // 'all' | 'positive' | 'negative'
let researchSortBy = 'date';    // 'date' | 'sector' | 'ticker' | 'upside'
let researchViewMode = 'list';  // 'list' | 'table'

// === PORTFOLIO DRILL-DOWN NAVIGATION ===
function navigateToPortfolio(parentName, callback) {
    activeParentPortfolio = parentName;
    activeSubPortfolio = null;
    document.getElementById("dashboard-main-view").style.display = "none";
    document.getElementById("portfolio-detail-view").style.display = "block";
    renderPortfolioPage();
    if (callback) callback();
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

    // Build sub-portfolio chips (or manage list in manage mode)
    if (isManageMode) {
        renderManageSubportList();
    }
    const chipsEl = document.getElementById("subport-chips");
    chipsEl.innerHTML = "";
    if (isManageMode) chipsEl.style.display = "none";

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

    // Apply sorting (mirrors the main dashboard table)
    if (portfolioSort.column) {
        const getMarketValue = (h) => h.shares * convertCurrency(h.currentPrice, h.currency, displayCurrency);
        const getCostBasis = (h) => h.shares * convertCurrency(h.avgCost, h.currency, displayCurrency);

        filteredHoldings.sort((a, b) => {
            let valA, valB;
            switch (portfolioSort.column) {
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

            if (valA < valB) return portfolioSort.direction === 'asc' ? -1 : 1;
            if (valA > valB) return portfolioSort.direction === 'asc' ? 1 : -1;
            return 0;
        });
    }

    if (filteredHoldings.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;color:var(--text-secondary);padding:24px;">No holdings in this portfolio.</td></tr>`;
        return;
    }

    // Pre-pass: total market value of the current view (parent or selected sub-port),
    // so weights sum to 100% within this view
    let viewTotalMarketValue = 0;
    filteredHoldings.forEach(pos => {
        viewTotalMarketValue += pos.shares * convertCurrency(pos.currentPrice, pos.currency, displayCurrency);
    });

    filteredHoldings.forEach(pos => {
        const avgCost = convertCurrency(pos.avgCost, pos.currency, displayCurrency);
        const currentPrice = convertCurrency(pos.currentPrice, pos.currency, displayCurrency);
        const costBasis = pos.shares * avgCost;
        const marketValue = pos.shares * currentPrice;

        const gainLoss = marketValue - costBasis;
        const gainLossPct = costBasis > 0 ? (gainLoss / costBasis) * 100 : 0;
        const weightPct = viewTotalMarketValue > 0 ? (marketValue / viewTotalMarketValue) * 100 : 0;

        const row = document.createElement("tr");
        row.style.cursor = "pointer";
        row.title = "Click to view detailed chart & stats";
        row.onclick = () => openStockDetail(pos.ticker);
        row.innerHTML = `
            <td><span class="ticker-badge">${pos.ticker}</span></td>
            <td><strong>${pos.companyName}</strong><br><span style="font-size:0.72rem;color:var(--text-secondary);">${pos.sector || ''}</span></td>
            <td><span class="portfolio-badge" ${getBadgeStyle(pos.portfolio)}>${pos.portfolio}</span></td>
            <td class="text-right table-shares">${formatShares(pos.shares)}</td>
            <td class="text-right table-currency">${symbol}${avgCost.toFixed(2)}</td>
            <td class="text-right table-currency">${symbol}${currentPrice.toFixed(2)}</td>
            <td class="text-right table-currency" style="font-weight:500;">${symbol}${formatNumber(marketValue, 2)}</td>
            <td class="text-right" style="font-family:var(--font-mono);font-size:0.85rem;">
                <div style="display:flex;align-items:center;justify-content:flex-end;gap:6px;">
                    <div style="width:40px;height:4px;background:var(--border-dim);border-radius:2px;overflow:hidden;flex-shrink:0;">
                        <div style="width:${Math.min(weightPct,100)}%;height:100%;background:var(--accent-neon);border-radius:2px;"></div>
                    </div>
                    <span style="color:var(--text-secondary);min-width:36px;text-align:right;">${weightPct.toFixed(1)}%</span>
                </div>
            </td>
            <td class="text-right ${gainLoss >= 0 ? 'cell-positive' : 'cell-negative'}">
                <div style="display:flex;justify-content:flex-end;align-items:center;gap:10px;">
                    <span>${symbol}${formatNumber(gainLoss, 2)} (${gainLossPct >= 0 ? '+' : ''}${gainLossPct.toFixed(1)}%)</span>
                    <button onclick="event.stopPropagation(); openEditAssetModal('${pos.ticker}', '${pos.portfolio}', '${pos.currency}', ${pos.shares}, ${pos.avgCost}, ${pos.portfolioId}, ${pos.manualPrice ?? null})" title="Edit Asset" style="background:none;border:none;color:var(--text-secondary);cursor:pointer;font-size:1rem;padding:0;">✎</button>
                </div>
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
                    fetch('/api/holdings?t=' + Date.now()).then(res => res.json()),
                    fetch('/api/portfolios?t=' + Date.now()).then(res => res.json())
                ])
                .then(([hData, pData]) => {
                    holdings = hData.map(h => ({...h, currentPrice: h.manualPrice || h.avgCost}));
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
