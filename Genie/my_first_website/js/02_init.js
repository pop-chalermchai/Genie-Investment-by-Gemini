function fetchInitData(onComplete = null) {
    return Promise.all([
        fetch('/api/init-data?t=' + Date.now()).then(res => res.json()),
        fetch('/api/categories?t=' + Date.now()).then(res => res.json()),
        fetch('/api/sectors?t=' + Date.now()).then(res => res.json())
    ])
    .then(([initData, catsData, sectorsData]) => {
        holdings = initData.holdings.map(h => ({...h, currentPrice: h.manualPrice || h.avgCost}));
        researchReports = initData.reports;
        feedItems = Array.isArray(initData.feedItems) ? initData.feedItems : [];
        portfoliosList = initData.portfolios;
        categoriesList = catsData;
        sectorsList = Array.isArray(sectorsData) ? sectorsData : [];

        populateDropdowns();
        updateDashboard();
        renderReportList();
        
        if (activeParentPortfolio) {
            renderPortfolioPage();
        }
        
        if (onComplete) onComplete();
    })
    .catch(err => console.error("Error fetching init data:", err));
}

document.addEventListener("DOMContentLoaded", async () => {
    let isAllowed = true;
    if (window.GenieAuth) {
        // Allow public access to initialization, only force auth check on protected routes/actions
        isAllowed = window.GenieAuth.hasSession();
        if (window.location.hash.includes("type=recovery")) {
            await GenieAuth.ensureAllowed();
        }
    }
    loadUserProfile(); // fire-and-forget: applies name/avatar/preferences when it lands
    fetchInitData(() => {
        // Apply cached prices from localStorage for instant first render
        try {
            const cached = JSON.parse(localStorage.getItem('genie-price-cache') || '{}');
            const CACHE_TTL = 24 * 60 * 60 * 1000; // 24 hours
            if (cached.__ts__ && (Date.now() - cached.__ts__) < CACHE_TTL) {
                if (cached.__rate__) exchangeRateUSDTHB = cached.__rate__;
                if (cached.__rateEURUSD__) exchangeRateEURUSD = cached.__rateEURUSD__;
                // Manual price overrides win over cached live prices
                holdings.forEach(h => { if (cached[h.ticker] && !h.manualPrice) h.currentPrice = cached[h.ticker]; });
            }
        } catch (e) { /* ignore corrupt cache */ }

        updateDashboard();

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
            if (!isAllowed && path !== "research") {
                switchTab("research", false);
                if (window.GenieAuth) window.GenieAuth.showLogin();
            } else {
                switchTab(path, false);
            }
        } else {
            switchTab(isAllowed ? "dashboard" : "research", false);
        }

        fetchLivePrices(); // runs in background, silently updates prices
        setupDragAndDrop();
    });
});

// TAB SWITCHER
function switchTab(tabName, pushState = true) {
    if (window.GenieAuth && !window.GenieAuth.hasSession() && tabName !== "research") {
        window.GenieAuth.showLogin();
        if (!activeTab) tabName = "research";
        else return;
    }

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

// WORKSPACE SUB-TAB SWITCHER (Holdings vs Allocation & Add Position)
function switchWorkspaceView(viewName) {
    const views = ["holdings", "visuals"];
    views.forEach(v => {
        const tabEl = document.getElementById(`wtab-${v}`);
        const contentEl = document.getElementById(`workspace-view-${v}`);

        if (v === viewName) {
            tabEl.classList.add("active");
            contentEl.classList.add("active-content");
        } else {
            tabEl.classList.remove("active");
            contentEl.classList.remove("active-content");
        }
    });

    // Resize chart to prevent visual glitches when its container becomes visible
    if (viewName === "visuals" && allocationChart) {
        allocationChart.resize();
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
