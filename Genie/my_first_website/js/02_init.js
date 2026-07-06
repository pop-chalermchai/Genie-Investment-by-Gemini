function fetchInitData(onComplete = null) {
    return Promise.all([
        fetch('/api/init-data?t=' + Date.now()).then(res => res.json()),
        fetch('/api/categories?t=' + Date.now()).then(res => res.json())
    ])
    .then(([initData, catsData]) => {
        holdings = initData.holdings.map(h => ({...h, currentPrice: h.avgCost}));
        researchReports = initData.reports;
        portfoliosList = initData.portfolios;
        categoriesList = catsData;
        
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
    // Gate the app on auth. The backend tells us whether a login is required
    // (see /api/auth-config); if so and there's no session, show login and stop.
    if (window.GenieAuth) {
        const allowed = await GenieAuth.ensureAllowed();
        if (!allowed) return;
    }
    loadUserProfile(); // fire-and-forget: applies name/avatar/preferences when it lands
    fetchInitData(() => {
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
    });
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
