// ==========================================================================
// CLIENT-SIDE PORTFOLIO DATABASE & STATE MANAGEMENT
// ==========================================================================
let holdings = [];

let activeTab = "dashboard";
let activeReport = "mu";
let activeLanguage = "en";
let activeReportTab = "overview";
let allocationChart = null;
let displayCurrency = "USD";
let exchangeRateUSDTHB = 32.505;
let currentSort = { column: null, direction: 'asc' };

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
    }
};

// ==========================================================================
// RESEARCH REPORTS DATABASE (ENGLISH & THAI)
// ==========================================================================
let researchReports = {};

// === DELETE PORTFOLIO LOGIC ===
function deletePortfolio(pName) {
    if (confirm(`Are you sure you want to delete the portfolio "${pName}"? This will also delete all assets and transactions inside it.`)) {
        fetch('/api/portfolio?name=' + encodeURIComponent(pName), {
            method: 'DELETE'
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                // Remove from dropdowns
                const filter = document.getElementById("portfolio-filter");
                const option1 = [...filter.options].find(o => o.value === pName);
                if (option1) option1.remove();
                
                const ingestFilter = document.getElementById("ingest-portfolio");
                const option2 = [...ingestFilter.options].find(o => o.value === pName);
                if (option2) option2.remove();

                // Re-fetch holdings
                fetch('/api/holdings')
                    .then(r => r.json())
                    .then(hData => {
                        holdings = hData.map(h => ({...h, currentPrice: h.avgCost}));
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
        fetch('/api/reports').then(res => res.json())
    ])
    .then(([holdingsData, reportsData]) => {
        holdings = holdingsData.map(h => ({...h, currentPrice: h.avgCost}));
        researchReports = reportsData;
        
        updateDashboard();
        renderReportList();
        
        // Auto-select first report if any
        const reportKeys = Object.keys(researchReports);
        if (reportKeys.length > 0 && !activeReport) {
            activeReport = reportKeys[0];
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
        
        fetchLivePrices();
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
                case 'return': valA = getMarketValue(a) - getCostBasis(a); valB = getMarketValue(b) - getCostBasis(b); break;
                default: valA = a.ticker; valB = b.ticker;
            }
            
            if (valA < valB) return currentSort.direction === 'asc' ? -1 : 1;
            if (valA > valB) return currentSort.direction === 'asc' ? 1 : -1;
            return 0;
        });
    }

    const portfoliosData = {};
    holdings.forEach(pos => {
        if (!portfoliosData[pos.portfolio]) {
            portfoliosData[pos.portfolio] = { value: 0, cost: 0 };
        }
    });
    
    const tableBody = document.getElementById("positions-table-body");
    tableBody.innerHTML = ""; // Clear table

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

        // Accumulate sub-portfolio totals
        const pData = portfoliosData[pos.portfolio];
        if (pData) {
            pData.value += marketValue;
            pData.cost += costBasis;
        }

        const symbol = displayCurrency === "USD" ? "$" : "฿";

        // Generate HTML row
        const row = document.createElement("tr");
        row.style.cursor = "pointer";
        row.title = "Click to view detailed chart & stats";
        row.onclick = () => openStockDetail(pos.ticker);
        row.innerHTML = `
            <td><span class="ticker-badge">${pos.ticker}</span></td>
            <td><strong>${pos.companyName}</strong><br><span style="font-size: 0.72rem; color: var(--text-secondary);">${pos.sector}</span></td>
            <td><span class="portfolio-badge badge-${pos.portfolio.toLowerCase().replace(/ /g, '-')}">${pos.portfolio}</span></td>
            <td class="text-right table-shares">${formatNumber(pos.shares, 1)}</td>
            <td class="text-right table-currency">${symbol}${avgCost.toFixed(2)}</td>
            <td class="text-right table-currency">${symbol}${currentPrice.toFixed(2)}</td>
            <td class="text-right table-currency" style="font-weight: 500;">${symbol}${formatNumber(marketValue, 2)}</td>
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

    // Update Sub-Portfolios Summaries Cards dynamically
    const gridEl = document.getElementById("sub-portfolios-grid");
    if (gridEl) {
        gridEl.innerHTML = ""; // clear current cards
        const colors = ["#00F0FF", "#D4AF37", "#8B5CF6", "#10B981", "#FF5C5C", "#FFA500"];
        let colorIdx = 0;
        
        Object.keys(portfoliosData).forEach(pName => {
            const data = portfoliosData[pName];
            const pGainLoss = data.value - data.cost;
            const pGainLossPct = data.cost > 0 ? (pGainLoss / data.cost) * 100 : 0;
            const isPos = pGainLoss >= 0;
            
            const color = colors[colorIdx % colors.length];
            colorIdx++;
            
            const card = document.createElement("div");
            card.className = "metric-card glass-panel";
            card.style.padding = "15px";
            card.style.borderLeft = `3px solid ${color}`;
            card.style.display = "flex";
            card.style.flexDirection = "column";
            card.style.position = "relative";
            
            card.innerHTML = `
                <button onclick="deletePortfolio('${pName}')" title="Delete Portfolio" style="position: absolute; top: 10px; right: 10px; background: none; border: none; color: var(--color-negative); cursor: pointer; font-size: 1.2rem; padding: 0; line-height: 1; opacity: 0.7; transition: opacity 0.2s;" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.7">&times;</button>
                <span style="font-size: 0.75rem; color: var(--text-secondary); font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;">${pName}</span>
                <div style="font-size: 1.25rem; font-weight: 700; color: var(--text-primary); margin: 5px 0;">${symbol}${formatNumber(data.value, 2)}</div>
                <span class="${isPos ? 'positive' : 'negative'}" style="font-size: 0.8rem; font-weight: 500; color: ${isPos ? 'var(--color-positive)' : 'var(--color-negative)'}">
                    ${isPos ? '+' : ''}${pGainLossPct.toFixed(1)}% (${symbol}${formatNumber(pGainLoss, 0)})
                </span>
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
                    "rgba(0, 240, 255, 0.65)", // Neon cyan
                    "rgba(212, 175, 55, 0.65)",  // Gold
                    "rgba(139, 92, 246, 0.65)",  // Violet
                    "rgba(16, 185, 129, 0.65)"  // Emerald
                ],
                borderColor: [
                    "#00F0FF",
                    "#D4AF37",
                    "#8B5CF6",
                    "#10B981"
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
function selectReport(reportId) {
    activeReport = reportId;

    // Toggle active list item classes
    Object.keys(researchReports).forEach(r => {
        const item = document.getElementById(`report-item-${r}`);
        if (item) {
            if (r === reportId) {
                item.classList.add("active");
            } else {
                item.classList.remove("active");
            }
        }
    });

    renderReport();
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
function renderReportList() {
    const container = document.getElementById("report-list-container");
    if (!container) return;
    
    container.innerHTML = "";
    Object.keys(researchReports).forEach(key => {
        const report = researchReports[key];
        const btn = document.createElement("button");
        btn.className = "report-list-item " + (activeReport === key ? "active" : "");
        btn.id = "report-item-" + key;
        btn.onclick = () => selectReport(key);
        
        btn.innerHTML = `
            <div class="report-status-badge verified">AUDITED</div>
            <span class="report-ticker">${report.ticker}</span>
            <span class="report-name">${report.companyName}</span>
        `;
        container.appendChild(btn);
    });
}

function renderReport() {
    const reportData = researchReports[activeReport];
    if (!reportData) return;

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

// ==========================================================================
// PORTFOLIO MANAGEMENT
// ==========================================================================
function openAddPortfolioModal() {
    document.getElementById("add-portfolio-modal").classList.add("active");
}

function closeAddPortfolioModal() {
    document.getElementById("add-portfolio-modal").classList.remove("active");
}

function handleAddPortfolio(event) {
    event.preventDefault();
    const name = document.getElementById("new-port-name").value;
    const category = document.getElementById("new-port-category").value;
    
    fetch('/api/portfolios', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, category })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeAddPortfolioModal();
            document.getElementById("add-portfolio-form").reset();
            
            // Add to dropdown filters immediately so they can ingest
            const filter = document.getElementById("portfolio-filter");
            if (![...filter.options].find(o => o.value === name)) {
                const option = document.createElement("option");
                option.value = name; option.text = name;
                filter.appendChild(option);
            }
            
            const ingestFilter = document.getElementById("ingest-portfolio");
            if (![...ingestFilter.options].find(o => o.value === name)) {
                const option = document.createElement("option");
                option.value = name; option.text = name;
                ingestFilter.appendChild(option);
            }
            
            alert("Portfolio created successfully! You can now add positions to it using the Quick Ingest panel.");
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

function loadTransactions() {
    const tbody = document.getElementById("transactions-table-body");
    tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="color: var(--text-secondary); text-align: center; padding: 20px;">🔄 Loading transaction history...</td></tr>`;

    fetch('/api/transactions')
        .then(res => res.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            transactionsList = data;
            renderTransactions();
        })
        .catch(err => {
            console.error("Error loading transactions:", err);
            tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="color: #EF4444; text-align: center; padding: 20px;">❌ Failed to load transactions: ${err.message}</td></tr>`;
        });
}

function renderTransactions() {
    const tbody = document.getElementById("transactions-table-body");
    tbody.innerHTML = "";
    
    const filterText = document.getElementById("tx-search-input").value.toUpperCase();
    
    const filtered = transactionsList.filter(t => {
        return !filterText || t.ticker.toUpperCase().includes(filterText) || t.companyName.toUpperCase().includes(filterText);
    });
    
    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="color: var(--text-secondary); text-align: center; padding: 20px;">No transactions found.</td></tr>`;
        return;
    }
    
    filtered.forEach(t => {
        const tr = document.createElement("tr");
        
        let dateStr = t.transactionDate || "";
        if (dateStr.includes("T")) {
            dateStr = dateStr.replace("T", " ").substring(0, 16);
        } else if (dateStr.includes(" ")) {
            dateStr = dateStr.substring(0, 16);
        }
        
        const typeBadge = t.type === "BUY" 
            ? `<span class="badge badge-success" style="background: rgba(16, 185, 129, 0.1); color: #10B981; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem;">BUY</span>`
            : `<span class="badge badge-danger" style="background: rgba(239, 68, 68, 0.1); color: #EF4444; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 0.75rem;">SELL</span>`;
            
        let price = parseFloat(t.price);
        let shares = parseFloat(t.shares);
        
        let displayPrice = price;
        let displayCurrencySym = t.currency === "THB" ? "฿" : "$";
        
        if (displayCurrency === "THB" && t.currency === "USD") {
            displayPrice = price * exchangeRateUSDTHB;
            displayCurrencySym = "฿";
        } else if (displayCurrency === "USD" && t.currency === "THB") {
            displayPrice = price / exchangeRateUSDTHB;
            displayCurrencySym = "$";
        }
        
        const formattedPrice = displayCurrencySym + displayPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        const formattedQty = Math.abs(shares).toLocaleString(undefined, { maximumFractionDigits: 4 });
        
        tr.innerHTML = `
            <td style="color: var(--text-secondary); font-family: var(--font-mono); font-size: 0.85rem;">${dateStr}</td>
            <td style="font-weight: 700; color: var(--accent-neon);">${t.ticker}</td>
            <td style="color: var(--text-primary);">${t.companyName}</td>
            <td>${typeBadge}</td>
            <td class="text-right" style="font-family: var(--font-mono); font-weight: 500; color: var(--text-primary); text-align: right;">${formattedQty}</td>
            <td class="text-right" style="font-family: var(--font-mono); color: var(--text-secondary); text-align: right;">${formattedPrice}</td>
            <td style="color: var(--text-secondary); font-size: 0.85rem;">${t.currency}</td>
            <td><span style="font-size: 0.8rem; background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 3px; color: var(--text-secondary);">${t.portfolio}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function filterTransactions() {
    renderTransactions();
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
