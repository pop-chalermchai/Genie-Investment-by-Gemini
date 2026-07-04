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
        // Report bodies are freeform markdown rendered to HTML — sanitize to
        // strip any embedded scripts/handlers before injecting.
        const html = marked.parse(rawText);
        reportContainer.innerHTML = window.DOMPurify ? DOMPurify.sanitize(html) : html;
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

    // 2. Fetch prices for all holdings
    const promises = holdings.map(async (pos) => {
        if (pos.ticker.includes(" ") || pos.ticker.startsWith("KAsset")) return; // Skip custom/private tickers

        // Thai mutual funds — fetch NAV from SEC API instead of Yahoo Finance
        if (pos.currency === "THB" || pos.sector === "Thai Mutual Fund") {
            try {
                const response = await fetch(`/api/thai-fund?code=${encodeURIComponent(pos.ticker)}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.nav) pos.currentPrice = data.nav;
                    if (data.proj_name_th) pos.companyName = data.proj_name_th;
                }
            } catch (err) {
                console.warn(`Failed to fetch NAV for ${pos.ticker}:`, err);
            }
            return;
        }

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
