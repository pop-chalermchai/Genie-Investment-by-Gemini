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
    
    // Initialize parentTotals with all parent and sub-portfolios from portfoliosList
    // Sort by sortOrder so Object.keys(parentTotals) reflects the user-defined order
    if (typeof portfoliosList !== 'undefined' && portfoliosList) {
        const sortedList = [...portfoliosList].sort((a, b) => (a.sortOrder ?? a.id) - (b.sortOrder ?? b.id));
        sortedList.forEach(p => {
            if (p.parentId === null) {
                if (!parentTotals[p.name]) {
                    parentTotals[p.name] = { value: 0, cost: 0, subPorts: {}, isEmpty: true };
                }
            }
        });
        sortedList.forEach(p => {
            if (p.parentId !== null) {
                const parentName = p.parentName;
                if (parentTotals[parentName]) {
                    if (!parentTotals[parentName].subPorts[p.name]) {
                        parentTotals[parentName].subPorts[p.name] = { value: 0, cost: 0 };
                    }
                }
            }
        });
    }
    
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
        parentTotals[parentName].isEmpty = false;
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
            <td><span class="portfolio-badge" ${getBadgeStyle(subName)}>${subName}</span></td>
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

    // Empty parent portfolios are already pre-populated from portfoliosList in parentTotals

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
            const isEmpty = data.isEmpty === true;

            const lowerName = parentName.toLowerCase();
            const color = parentColors[lowerName] || colors[colorIdx % colors.length];
            colorIdx++;

            const card = document.createElement("div");
            card.className = "metric-card glass-panel parent-portfolio-card";
            card.style.cssText = `padding:15px; border-left:3px solid ${color}; display:flex; flex-direction:column; cursor:pointer; position:relative; transition:var(--transition);${isEmpty ? 'opacity:0.7;' : ''}`;
            card.onclick = (e) => {
                if (e.target.tagName === "BUTTON") return;
                navigateToPortfolio(parentName);
            };
            card.onmouseover = () => { card.style.transform = "translateY(-2px)"; card.style.boxShadow = `0 4px 20px ${color}33`; };
            card.onmouseout = () => { card.style.transform = ""; card.style.boxShadow = ""; };

            const bottomRow = isEmpty
                ? `<span style="font-size:0.75rem;color:var(--text-secondary);font-style:italic;">No holdings yet — add a transaction to start</span>`
                : `<span style="font-size:0.78rem;font-weight:600;color:${isPos ? 'var(--color-positive)' : 'var(--color-negative)'};">${isPos ? '+' : ''}${pGainLossPct.toFixed(1)}% (${symbol}${formatNumber(Math.abs(pGainLoss), 0)})</span>
                   <span style="font-size:0.72rem;color:var(--text-secondary);">${subPortCount} sub-port${subPortCount > 1 ? 's' : ''} →</span>`;

            card.innerHTML = `
                <div style="font-size:1.2rem;font-weight:700;color:var(--text-emphasis);margin:0 0 2px 0;">${parentName}</div>
                <span style="font-size:1.1rem;font-weight:700;color:var(--text-primary);">${symbol}${formatNumber(data.value, 2)}</span>
                <div style="display:flex;justify-content:center;align-items:center;gap:14px;margin-top:6px;">${bottomRow}</div>
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

    const txType = document.getElementById("ingest-tx-type").value;
    const assetType = document.getElementById("ingest-asset-type").value;
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
            type: txType, assetType, ticker, companyName, sector, portfolio, shares, avgCost, currency
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById("ingest-form").reset();
            document.getElementById("ingest-asset-type").value = "STOCK";
            document.getElementById("ingest-tx-type").value = "BUY";
            toggleAssetType();
            toggleTxType();
            
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

function toggleAssetType() {
    const assetType = document.getElementById("ingest-asset-type").value;
    const labelCost = document.getElementById("label-avg-cost");
    const labelTicker = document.getElementById("label-ticker");
    const sharesLabel = document.querySelector("label[for='ingest-shares']");
    const currencySelect = document.getElementById("ingest-currency");
    const sectorSelect = document.getElementById("ingest-sector");
    const tickerInput = document.getElementById("ingest-ticker");
    const txType = document.getElementById("ingest-tx-type").value;
    const isSell = txType === "SELL";

    if (assetType === "THAI_FUND") {
        labelCost.innerText = isSell ? "Selling NAV (THB)" : "NAV per Unit (THB)";
        labelTicker.innerText = "Fund Code";
        if (sharesLabel) sharesLabel.innerText = "Units";
        tickerInput.placeholder = "e.g., KFGROWTH or K-GROWTH";
        if (currencySelect) currencySelect.value = "THB";
        if (sectorSelect) sectorSelect.value = "Thai Mutual Fund";
    } else if (assetType === "CRYPTO") {
        labelCost.innerText = isSell ? "Selling Price ($)" : "Avg Cost ($)";
        labelTicker.innerText = "Ticker";
        if (sharesLabel) sharesLabel.innerText = "Coins";
        tickerInput.placeholder = "e.g., BTC or ETH";
        if (currencySelect) currencySelect.value = "USD";
        if (sectorSelect && sectorSelect.value === "Thai Mutual Fund") sectorSelect.value = "Cryptocurrency";
    } else {
        labelCost.innerText = isSell ? "Selling Price ($)" : "Avg Cost ($)";
        labelTicker.innerText = "Ticker";
        if (sharesLabel) sharesLabel.innerText = "Shares (Qty)";
        tickerInput.placeholder = "e.g., TSLA or AAPL";
        if (currencySelect) currencySelect.value = "USD";
        if (sectorSelect && sectorSelect.value === "Thai Mutual Fund") sectorSelect.value = "Technology";
    }
}

function toggleTxType() {
    const txSelect = document.getElementById("ingest-tx-type");
    txSelect.classList.remove("type-buy", "type-sell");
    txSelect.classList.add(txSelect.value === "SELL" ? "type-sell" : "type-buy");
    // Update cost label to reflect sell vs buy
    toggleAssetType();
}

// ========== MANAGE MODE ==========

function toggleManageMode() {
    isManageMode = !isManageMode;
    const btn = document.getElementById("btn-manage-portfolios");
    const grid = document.getElementById("sub-portfolios-grid");
    const treePanel = document.getElementById("manage-tree-panel");

    if (btn) {
        btn.textContent = isManageMode ? "✓ Done" : "⚙ Manage";
        btn.classList.toggle("active", isManageMode);
    }

    if (isManageMode) {
        if (grid) grid.style.display = "none";
        if (treePanel) treePanel.style.display = "block";
        renderManageTree();
        // Also update sub-port view if we're in a portfolio detail
        if (activeParentPortfolio) renderManageSubportList();
    } else {
        if (treePanel) treePanel.style.display = "none";
        if (grid) grid.style.display = "";   // un-hide the card grid
        const chipsEl = document.getElementById("subport-chips");
        const manageList = document.getElementById("manage-subport-list");
        if (chipsEl) chipsEl.style.display = "";
        if (manageList) manageList.style.display = "none";
        updateDashboard();
        if (activeParentPortfolio) renderPortfolioPage();
    }
}

function renderManageTree() {
    const panel = document.getElementById("manage-tree-panel");
    if (!panel) return;
    panel.innerHTML = "";

    const parents = portfoliosList
        .filter(p => p.parentId === null)
        .sort((a, b) => (a.sortOrder ?? a.id) - (b.sortOrder ?? b.id));

    if (parents.length === 0) {
        panel.innerHTML = '<div style="padding:16px;color:var(--text-secondary);text-align:center;font-size:0.85rem;">No portfolios yet.</div>';
        return;
    }

    parents.forEach((parent, pIdx) => {
        if (pIdx > 0) {
            const div = document.createElement("div");
            div.className = "manage-tree-divider";
            panel.appendChild(div);
        }

        // Parent row
        const row = createManageRow(parent.name, parent.id, false, null, pIdx, parents.length);
        panel.appendChild(row);

        // Children
        const children = portfoliosList
            .filter(p => p.parentId === parent.id)
            .sort((a, b) => (a.sortOrder ?? a.id) - (b.sortOrder ?? b.id));

        children.forEach((child, cIdx) => {
            const childRow = createManageRow(child.name, child.id, true, parent.id, cIdx, children.length);
            panel.appendChild(childRow);
        });

        // Add sub-port button
        const addRow = document.createElement("div");
        addRow.style.cssText = "padding:6px 16px 6px 16px;";
        const addBtn = document.createElement("button");
        addBtn.className = "manage-tree-btn btn-add";
        addBtn.textContent = "+ Add Sub-Portfolio";
        addBtn.onclick = () => {
            isManageMode = false;
            toggleManageMode();
            navigateToPortfolio(parent.name, () => openAddSubPortfolioModal());
        };
        addRow.appendChild(addBtn);
        panel.appendChild(addRow);
    });
}

function createManageRow(name, id, isChild, parentId, idx, total) {
    const level = isChild ? "child" : "parent";
    const row = document.createElement("div");
    row.className = "manage-tree-row" + (isChild ? " is-child" : "");

    const upBtn = document.createElement("button");
    upBtn.className = "manage-tree-btn manage-order-btn";
    upBtn.textContent = "▲";
    upBtn.title = "Move up";
    upBtn.disabled = (idx === 0);
    upBtn.onclick = () => movePortfolio(id, level, parentId, -1);

    const downBtn = document.createElement("button");
    downBtn.className = "manage-tree-btn manage-order-btn";
    downBtn.textContent = "▼";
    downBtn.title = "Move down";
    downBtn.disabled = (idx === total - 1);
    downBtn.onclick = () => movePortfolio(id, level, parentId, 1);

    const nameEl = document.createElement("span");
    nameEl.className = "manage-tree-name";
    nameEl.textContent = name;

    const editBtn = document.createElement("button");
    editBtn.className = "manage-tree-btn";
    editBtn.textContent = "Edit";
    editBtn.onclick = () => {
        if (isChild) {
            const parent = portfoliosList.find(p => p.id === parentId);
            if (parent) activeParentPortfolio = parent.name;
            editSubPortfolio(name);
        } else {
            editParentPortfolio(name);
        }
    };

    const delBtn = document.createElement("button");
    delBtn.className = "manage-tree-btn btn-delete";
    delBtn.textContent = "Delete";
    delBtn.onclick = () => {
        if (isChild) {
            const parent = portfoliosList.find(p => p.id === parentId);
            if (parent) activeParentPortfolio = parent.name;
            deleteSubPortfolio(name);
        } else {
            deleteParentPortfolio(name);
        }
    };

    row.appendChild(upBtn);
    row.appendChild(downBtn);
    row.appendChild(nameEl);
    row.appendChild(editBtn);
    row.appendChild(delBtn);
    return row;
}

function renderManageSubportList() {
    const chipsEl = document.getElementById("subport-chips");
    const manageList = document.getElementById("manage-subport-list");
    if (!manageList) return;

    if (!isManageMode) {
        if (chipsEl) chipsEl.style.display = "";
        manageList.style.display = "none";
        return;
    }

    if (chipsEl) chipsEl.style.display = "none";
    manageList.style.display = "block";
    manageList.innerHTML = "";

    if (!activeParentPortfolio) return;
    const parentPort = portfoliosList.find(p => p.name === activeParentPortfolio && p.parentId === null);
    if (!parentPort) return;

    const children = portfoliosList
        .filter(p => p.parentId === parentPort.id)
        .sort((a, b) => (a.sortOrder ?? a.id) - (b.sortOrder ?? b.id));

    const wrapper = document.createElement("div");
    wrapper.style.cssText = "background:var(--bg-card);border:1px solid var(--border-dim);border-radius:10px;padding:6px 0;margin:8px 0;";

    children.forEach((child, cIdx) => {
        const row = createManageRow(child.name, child.id, true, parentPort.id, cIdx, children.length);
        wrapper.appendChild(row);
    });

    if (children.length === 0) {
        const empty = document.createElement("div");
        empty.className = "manage-tree-empty";
        empty.textContent = "No sub-portfolios yet.";
        wrapper.appendChild(empty);
    }

    manageList.appendChild(wrapper);
}

function movePortfolio(id, level, parentId, direction) {
    const group = level === "parent"
        ? portfoliosList.filter(p => p.parentId === null).sort((a, b) => (a.sortOrder ?? a.id) - (b.sortOrder ?? b.id))
        : portfoliosList.filter(p => p.parentId === parentId).sort((a, b) => (a.sortOrder ?? a.id) - (b.sortOrder ?? b.id));

    const idx = group.findIndex(p => p.id === id);
    const swapIdx = idx + direction;
    if (idx === -1 || swapIdx < 0 || swapIdx >= group.length) return;

    // Swap
    [group[idx], group[swapIdx]] = [group[swapIdx], group[idx]];

    // Update sortOrder on the live portfoliosList objects
    group.forEach((p, i) => { p.sortOrder = i * 10; });

    persistPortfolioOrder(group);

    // Always re-render the tree (shows both parents and sub-ports)
    // Also re-render sub-port detail list if currently in portfolio detail view
    renderManageTree();
    renderManageSubportList();
}

function persistPortfolioOrder(group) {
    const payload = group.map((p, i) => ({ id: p.id, sortOrder: i * 10 }));
    fetch('/api/portfolios/reorder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    }).catch(err => console.warn("Failed to persist portfolio order:", err));
}

// AUTO-FILL THAI MUTUAL FUND FROM SEC API
async function autoFillThaiFund() {
    const tickerInput = document.getElementById("ingest-ticker");
    const nameInput = document.getElementById("ingest-name");
    const costInput = document.getElementById("ingest-avg-cost");
    const code = tickerInput.value.trim().toUpperCase();

    if (!code || nameInput.value.trim() !== "") return;

    // Reset previous values before new lookup
    nameInput.value = "";
    costInput.value = "";
    nameInput.placeholder = "กำลังค้นหากองทุน...";
    try {
        let response = await fetch(`/api/thai-fund?code=${encodeURIComponent(code)}`);
        if (response.status === 404) {
            // Auto-sync fund list and retry once
            nameInput.placeholder = "กำลัง Sync ข้อมูลกองทุน (ครั้งแรก)...";
            await fetch('/api/thai-fund/sync', { method: 'POST' });
            response = await fetch(`/api/thai-fund?code=${encodeURIComponent(code)}`);
        }
        if (!response.ok) {
            nameInput.placeholder = "ไม่พบกองทุน — ตรวจสอบรหัสกองทุน";
            return;
        }
        const data = await response.json();
        nameInput.value = data.proj_name_th || data.proj_name_en || code;
        if (data.nav) {
            costInput.value = data.nav.toFixed(4);
        }
    } catch (err) {
        console.warn("Thai fund auto-fill failed:", err);
        nameInput.placeholder = "e.g., กองทุนเปิดกรุงศรีโกรทอิควิตี้";
    }
}

// AUTO-FILL COMPANY NAME FROM YAHOO FINANCE
async function autoFillCompanyName() {
    const assetType = document.getElementById("ingest-asset-type").value;
    if (assetType === "THAI_FUND") {
        return autoFillThaiFund();
    }

    const tickerInput = document.getElementById("ingest-ticker");
    const nameInput = document.getElementById("ingest-name");
    let ticker = tickerInput.value.trim().toUpperCase();
    
    // Auto-append -USD for popular crypto if not present
    const cryptoList = ['BTC', 'ETH', 'SOL', 'ADA', 'XRP', 'DOGE', 'BNB', 'DOT', 'LTC', 'LINK'];
    if (cryptoList.includes(ticker)) {
        ticker = ticker + '-USD';
        tickerInput.value = ticker; // Update the UI
    }
    
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
        
        // Auto-select Cryptocurrency sector if applicable
        const sectorInput = document.getElementById("ingest-sector");
        if (ticker.endsWith("-USD") && sectorInput) {
            sectorInput.value = "Cryptocurrency";
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
