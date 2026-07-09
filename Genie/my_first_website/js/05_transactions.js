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
const DEFAULT_SECTORS = ["Technology", "Industrial Goods", "Consumer Cyclical", "Financial Services", "Cryptocurrency", "Thai Mutual Fund"];

function populateSectorOptions() {
    // Union of defaults + every sector already used by holdings, sorted
    const sectors = new Set(DEFAULT_SECTORS);
    holdings.forEach(h => { if (h.sector) sectors.add(h.sector); });
    const sorted = [...sectors].sort((a, b) => a.localeCompare(b));

    // Quick Ingest combobox suggestions (free text still allowed)
    const datalist = document.getElementById("sector-options");
    if (datalist) {
        datalist.innerHTML = "";
        sorted.forEach(s => {
            const opt = document.createElement("option");
            opt.value = s;
            datalist.appendChild(opt);
        });
    }

    // Dashboard sector filter — keep the current selection if it still exists
    const sectorFilter = document.getElementById("sector-filter");
    if (sectorFilter) {
        const current = sectorFilter.value;
        sectorFilter.innerHTML = '<option value="ALL">All Sectors</option>';
        sorted.forEach(s => {
            const opt = document.createElement("option");
            opt.value = s;
            opt.text = s;
            sectorFilter.appendChild(opt);
        });
        if ([...sectorFilter.options].some(o => o.value === current)) sectorFilter.value = current;
    }
}

function populateDropdowns() {
    populateSectorOptions();

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
    
    // Populate category dropdowns dynamically
    const categorySelects = ["new-port-category", "new-subport-category", "edit-subport-category", "edit-port-category"];
    categorySelects.forEach(selectId => {
        const selectEl = document.getElementById(selectId);
        if (selectEl) {
            selectEl.innerHTML = '';
            categoriesList.forEach(cat => {
                const option = document.createElement("option");
                option.value = cat.name;
                option.text = cat.name;
                selectEl.appendChild(option);
            });
        }
    });
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
    const parentEl = document.getElementById("new-port-parent");
    const parentIdVal = parentEl ? parentEl.value : "";
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

        const displayPrice = convertCurrency(parseFloat(t.price), t.currency, displayCurrency);
        const sym = displayCurrency === "THB" ? "฿" : "$";

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
