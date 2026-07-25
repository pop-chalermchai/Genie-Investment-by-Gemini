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
        
        const sym = currencySymbol(data.currency);
        
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

function editSubPortfolio(subName) {
    if (!activeParentPortfolio) {
        alert("Cannot edit sub-portfolio: active parent portfolio is not set.");
        return;
    }
    const parentPort = portfoliosList.find(p => p.name && p.name.trim().toLowerCase() === activeParentPortfolio.trim().toLowerCase() && p.parentId === null);
    if (!parentPort) {
        alert(`Cannot edit sub-portfolio: parent portfolio "${activeParentPortfolio}" could not be found.`);
        return;
    }
    const subPortObj = portfoliosList.find(p => p.name === subName && p.parentId === parentPort.id);
    const currentCategory = subPortObj ? subPortObj.category : "Stocks";

    document.getElementById("edit-subport-old-name").value = subName;
    document.getElementById("edit-subport-name").value = subName;
    document.getElementById("edit-subport-category").value = currentCategory || "Stocks";
    document.getElementById("edit-subportfolio-modal").classList.add("active");
}

function closeEditSubPortfolioModal() {
    document.getElementById("edit-subportfolio-modal").classList.remove("active");
}

function editParentPortfolio(pName) {
    const portObj = portfoliosList.find(p => p.name === pName && p.parentId === null);
    const currentCategory = portObj ? portObj.category : "Stocks";

    document.getElementById("edit-port-old-name").value = pName;
    document.getElementById("edit-port-name").value = pName;
    document.getElementById("edit-port-category").value = currentCategory || "Stocks";
    document.getElementById("edit-portfolio-modal").classList.add("active");
}

function closeEditPortfolioModal() {
    document.getElementById("edit-portfolio-modal").classList.remove("active");
}

function handleEditPortfolioSubmit(e) {
    e.preventDefault();
    const oldName = document.getElementById("edit-port-old-name").value;
    const newName = document.getElementById("edit-port-name").value.trim();
    const newCategory = document.getElementById("edit-port-category").value;

    if (!newName) {
        alert("Portfolio name is required.");
        return;
    }

    fetch('/api/portfolio', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            oldName: oldName,
            newName: newName,
            newCategory: newCategory
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            closeEditPortfolioModal();
            if (activeParentPortfolio === oldName) {
                activeParentPortfolio = newName;
            }
            fetchInitData();
        } else {
            alert("Failed to update portfolio: " + data.error);
        }
    })
    .catch(err => {
        console.error("Error updating portfolio:", err);
        alert("Failed to update portfolio.");
    });
}

function handleEditSubPortfolioSubmit(e) {
    e.preventDefault();
    const oldName = document.getElementById("edit-subport-old-name").value;
    const newName = document.getElementById("edit-subport-name").value.trim();
    const newCategory = document.getElementById("edit-subport-category").value;

    if (!newName) {
        alert("Sub-portfolio name is required.");
        return;
    }

    fetch('/api/portfolio', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            oldName: oldName,
            newName: newName,
            parentName: activeParentPortfolio,
            newCategory: newCategory
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            closeEditSubPortfolioModal();
            if (activeSubPortfolio === oldName) {
                activeSubPortfolio = newName;
            }
            fetchInitData();
        } else {
            alert("Failed to rename sub-portfolio: " + data.error);
        }
    });
}

function deleteSubPortfolio(subName) {
    if (confirm(`Delete sub-portfolio "${subName}" and all its assets/transactions?`)) {
        fetch('/api/portfolio?name=' + encodeURIComponent(subName), { method: 'DELETE' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                activeSubPortfolio = null;
                fetchInitData();
            } else {
                alert("Failed to delete sub-portfolio: " + data.error);
            }
        });
    }
}

// ---------------------------------------------
// ADD SUB-PORTFOLIO MODAL
// ---------------------------------------------
function openAddSubPortfolioModal() {
    if (!activeParentPortfolio) {
        console.error("openAddSubPortfolioModal error: activeParentPortfolio is not set");
        alert("Cannot add sub-portfolio: active parent portfolio is not set.");
        return;
    }
    const pInfo = portfoliosList.find(p => p.name && p.name.trim().toLowerCase() === activeParentPortfolio.trim().toLowerCase() && p.parentId === null);
    if (pInfo) {
        document.getElementById("new-subport-parent-id").value = pInfo.id;
        document.getElementById("add-subportfolio-modal").classList.add("active");
    } else {
        console.error("openAddSubPortfolioModal error: parent portfolio not found in portfoliosList", activeParentPortfolio, portfoliosList);
        alert(`Cannot add sub-portfolio: parent portfolio "${activeParentPortfolio}" could not be found.`);
    }
}

function closeAddSubPortfolioModal() {
    document.getElementById("add-subportfolio-modal").classList.remove("active");
}

function handleAddSubPortfolio(e) {
    e.preventDefault();
    const name = document.getElementById("new-subport-name").value.trim();
    const category = document.getElementById("new-subport-category").value;
    const parentIdVal = document.getElementById("new-subport-parent-id").value;
    const parentId = parentIdVal === "" ? null : parseInt(parentIdVal);

    fetch('/api/portfolios', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, category, parentId })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            closeAddSubPortfolioModal();
            document.getElementById("add-subportfolio-form").reset();
            fetchInitData();
        } else {
            alert("Error: " + data.error);
        }
    });
}

// ---------------------------------------------
// EDIT ASSET MODAL
// ---------------------------------------------
function openEditAssetModal(ticker, portfolio, currency, shares, avgCost, portfolioId, manualPrice) {
    document.getElementById("edit-asset-ticker").value = ticker;
    document.getElementById("edit-asset-portfolio").value = portfolio;
    document.getElementById("edit-asset-portfolio-id").value = portfolioId || '';
    document.getElementById("edit-asset-currency").value = currency;
    document.getElementById("edit-asset-display").innerText = `${ticker} (in ${portfolio})`;
    document.getElementById("edit-asset-shares").value = shares;
    document.getElementById("edit-asset-price").value = avgCost;
    document.getElementById("edit-asset-market-price").value = manualPrice || '';
    document.getElementById("edit-asset-modal").classList.add("active");
}

function closeEditAssetModal() {
    document.getElementById("edit-asset-modal").classList.remove("active");
}

function handleEditAsset(e) {
    e.preventDefault();
    const ticker = document.getElementById("edit-asset-ticker").value;
    const portfolio = document.getElementById("edit-asset-portfolio").value;
    const portfolioId = document.getElementById("edit-asset-portfolio-id").value;
    const currency = document.getElementById("edit-asset-currency").value;
    const shares = parseFloat(document.getElementById("edit-asset-shares").value);
    const price = parseFloat(document.getElementById("edit-asset-price").value);
    const manualPriceRaw = document.getElementById("edit-asset-market-price").value;
    const manualPrice = manualPriceRaw !== "" ? parseFloat(manualPriceRaw) : null; // null clears the override

    fetch('/api/asset-adjustment', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, portfolio, portfolioId: portfolioId ? parseInt(portfolioId) : null, currency, shares, price, manualPrice })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            closeEditAssetModal();
            fetchInitData();
        } else {
            alert("Failed to adjust asset: " + data.error);
        }
    });
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

// ==========================================================================
// USER PROFILE (display name, avatar, preferences synced via /api/profile)
// ==========================================================================
let userProfile = null;
const PROFILE_AVATARS = ["🧞", "🧞‍♂️", "🧞‍♀️", "🦁", "🐯", "🦊", "🐼", "🦅", "🚀", "💎", "📈", "🪙"];

function loadUserProfile() {
    return fetch('/api/profile?t=' + Date.now())
        .then(r => r.json())
        .then(p => { if (p && !p.error) applyProfile(p); })
        .catch(err => console.error("Error loading profile:", err));
}

function applyProfile(profile) {
    userProfile = profile;

    // Header chip
    const avatarEl = document.getElementById("profile-header-avatar");
    const nameEl = document.getElementById("profile-header-name");
    if (avatarEl) avatarEl.innerText = profile.avatar_emoji || "🧞";
    if (nameEl) nameEl.innerText = profile.display_name || "Profile";

    // Workspace label — belongs to whoever is signed in, never a hardcoded name
    const workspaceEl = document.getElementById("portfolio-title");
    if (workspaceEl) {
        workspaceEl.innerText = profile.display_name
            ? profile.display_name + "'s Portfolios"
            : "My Portfolios";
    }

    // Role-gated UI: research authoring is admin-only (backend enforces too)
    const isAdmin = profile.role === "admin";
    const newReportBtn = document.getElementById("btn-new-report");
    if (newReportBtn) newReportBtn.style.display = isAdmin ? "" : "none";
    const readerActions = document.getElementById("reader-admin-actions");
    if (readerActions) readerActions.style.display = isAdmin ? "flex" : "none";

    // Preferences
    if (profile.preferred_theme) setTheme(profile.preferred_theme);
    if (profile.preferred_currency && profile.preferred_currency !== displayCurrency) {
        toggleCurrency(profile.preferred_currency);
    }
    if (profile.preferred_language && profile.preferred_language !== activeLanguage) {
        activeLanguage = profile.preferred_language;
        const langBtn = document.getElementById("lang-" + profile.preferred_language);
        if (langBtn) {
            document.getElementById("lang-en").classList.remove("active");
            document.getElementById("lang-th").classList.remove("active");
            langBtn.classList.add("active");
        }
        // Re-render report only once data is loaded (boot-time race guard)
        if (Object.keys(researchReports).length > 0) renderReport();
    }
}

function renderAvatarChoices(selected) {
    const wrap = document.getElementById("profile-avatar-choices");
    wrap.innerHTML = "";
    PROFILE_AVATARS.forEach(emoji => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.innerText = emoji;
        btn.dataset.emoji = emoji;
        btn.style.cssText = "font-size:1.3rem;padding:6px 8px;border-radius:6px;cursor:pointer;background:rgba(0,0,0,0.3);border:1px solid " +
            (emoji === selected ? "var(--accent-neon)" : "rgba(255,255,255,0.1)") + ";";
        btn.onclick = () => renderAvatarChoices(emoji);
        wrap.appendChild(btn);
    });
    wrap.dataset.selected = selected;
}

function openProfileModal() {
    const fill = () => {
        document.getElementById("profile-email").innerText = (userProfile && userProfile.email) || "";
        document.getElementById("profile-display-name").value = (userProfile && userProfile.display_name) || "";
        renderAvatarChoices((userProfile && userProfile.avatar_emoji) || "🧞");
        document.getElementById("profile-currency").value = (userProfile && userProfile.preferred_currency) || "USD";
        document.getElementById("profile-theme").value = (userProfile && userProfile.preferred_theme) || "light";
        document.getElementById("profile-language").value = (userProfile && userProfile.preferred_language) || "en";
        document.getElementById("profile-modal").classList.add("active");
    };
    if (userProfile) { fill(); } else { loadUserProfile().then(fill); }
}

function closeProfileModal() {
    document.getElementById("profile-modal").classList.remove("active");
}

function handleProfileSubmit(e) {
    e.preventDefault();
    const payload = {
        display_name: document.getElementById("profile-display-name").value.trim(),
        avatar_emoji: document.getElementById("profile-avatar-choices").dataset.selected || "🧞",
        preferred_currency: document.getElementById("profile-currency").value,
        preferred_theme: document.getElementById("profile-theme").value,
        preferred_language: document.getElementById("profile-language").value,
    };
    fetch('/api/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(r => r.json().then(data => ({ ok: r.ok, data })))
    .then(({ ok, data }) => {
        if (!ok || data.error) {
            alert("Error saving profile: " + (data.error || "unknown"));
            return;
        }
        applyProfile(data);
        closeProfileModal();
    })
    .catch(err => {
        console.error("Error saving profile:", err);
        alert("Failed to save profile.");
    });
}

// === Profile dropdown menu (avatar button in the nav) ===
function toggleProfileMenu(e) {
    e.stopPropagation();
    const dd = document.getElementById("profile-dropdown");
    const opening = dd.style.display !== "block";
    dd.style.display = opening ? "block" : "none";
    if (opening) {
        // Anchored right of the button by default; flip when that runs off-screen
        // (mobile: the nav collapses to a grid and the button sits near the left edge)
        dd.style.right = "0";
        dd.style.left = "auto";
        if (dd.getBoundingClientRect().left < 8) {
            dd.style.right = "auto";
            dd.style.left = "0";
        }
    }
}

function closeProfileMenu() {
    document.getElementById("profile-dropdown").style.display = "none";
}

document.addEventListener("click", (e) => {
    const wrap = document.getElementById("profile-menu-wrap");
    if (wrap && !wrap.contains(e.target)) closeProfileMenu();
});

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeProfileMenu();
});
