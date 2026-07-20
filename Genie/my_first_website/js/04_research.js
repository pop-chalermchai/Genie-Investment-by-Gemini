let collapsedSectors = {}; // Remember collapsed states client-side
let collapsedDates = {};   // Same, keyed by research date (feed grouping)

function selectReport(reportId) {
    activeReport = reportId;
    localStorage.setItem('genie-last-report', reportId);
    openResearchReader();
}

// ── Full-page reader navigation ────────────────────────────────────
function openResearchReader() {
    document.getElementById("research-feed-view").style.display = "none";
    document.getElementById("research-reader-view").style.display = "";
    renderReport();
    window.scrollTo({ top: 0 });
}

function closeResearchReader() {
    document.getElementById("research-reader-view").style.display = "none";
    document.getElementById("research-feed-view").style.display = "";
    renderReportList();
}

function scrollToReaderSection(section) {
    document.getElementById("reader-sec-" + section)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function formatResearchDate(iso) {
    if (!iso) return "—";
    const d = new Date(iso + "T00:00:00");
    if (isNaN(d)) return iso;
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

// Full date header for a feed group — e.g. "19 กรกฎาคม 2026" (TH) / "July 19, 2026" (EN)
function formatGroupDateHeader(iso) {
    if (!iso || iso === "undated") return activeLanguage === "th" ? "ไม่ระบุวันที่" : "Undated";
    const d = new Date(iso + "T00:00:00");
    if (isNaN(d)) return iso;
    // Force the Gregorian calendar for th-TH — it defaults to the Buddhist Era
    // (year + 543) otherwise, which doesn't match the rest of the app's dates.
    return activeLanguage === "th"
        ? d.toLocaleDateString("th-TH-u-ca-gregory", { day: "numeric", month: "long", year: "numeric" })
        : d.toLocaleDateString("en-US", { day: "numeric", month: "long", year: "numeric" });
}

function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
}

// Pull the recommendation strip (the first blockquote of the overview —
// "RECOMMENDATION: … | TARGET PRICE: …" / "คำแนะนำ: …") for the feed row.
function getReportSummaryLine(report) {
    const raw = report[activeLanguage + "_overview"] || report.en_overview || "";
    const m = raw.match(/^>\s?\S.*(?:\n>\s?.*)*/m); // first blockquote block
    if (!m) return "";
    return m[0]
        .replace(/^>\s?/gm, "")
        .replace(/\*\*|__|`|\*/g, "")
        .replace(/\s*\n\s*/g, " · ")
        .replace(/[ \t]{2,}/g, " ")
        .trim();
}

function setLanguage(lang) {
    activeLanguage = lang;
    document.getElementById("lang-en").classList.remove("active");
    document.getElementById("lang-th").classList.remove("active");
    document.getElementById("lang-" + lang).classList.add("active");
    renderReport();
    renderReportList(); // feed summary lines are localized too
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
    } else if (researchSortBy === 'sector') {
        reports.sort((a, b) => (a.sector || 'Other').localeCompare(b.sector || 'Other') || a.ticker.localeCompare(b.ticker));
    } else {
        // Default: research date, newest first (undated last)
        reports.sort((a, b) => (b.researchDate || '').localeCompare(a.researchDate || '') || a.ticker.localeCompare(b.ticker));
    }
    return { reports, query };
}

function makeReportRow(report) {
    const recColor = report.isPositive ? 'var(--color-positive)' : 'var(--color-negative)';
    const recBg    = report.isPositive ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)';
    const recLabel = (report.rating || 'N/A').split(' ')[0].replace(/[^A-Z/]/gi, '') || 'N/A';

    const upside = getUpsidePct(report);
    const rightMeta = report.priceTarget
        ? `<span style="font-family:var(--font-mono);font-size:0.78rem;color:var(--text-primary);white-space:nowrap;">PT $${parseFloat(report.priceTarget).toFixed(2)}</span>` +
          (upside !== null
            ? `<span style="font-family:var(--font-mono);font-size:0.78rem;font-weight:700;white-space:nowrap;color:${upside >= 0 ? 'var(--color-positive)' : 'var(--color-negative)'};">${upside >= 0 ? '+' : ''}${upside.toFixed(1)}%</span>`
            : '')
        : `<span style="font-size:0.75rem;color:var(--text-secondary);white-space:nowrap;">${report.sector || ''}</span>`;

    const rowEl = document.createElement("div");
    rowEl.className = "research-feed-row";
    rowEl.id = "report-item-" + report.key;
    rowEl.onclick = () => selectReport(report.key);
    const summary = getReportSummaryLine(report);
    rowEl.innerHTML = `
        <span class="feed-date">${formatResearchDate(report.researchDate)}</span>
        <span class="feed-rating" style="background:${recBg};color:${recColor};">${recLabel}</span>
        <span class="feed-main">
            <span class="feed-title">
                <span class="report-ticker">${report.ticker}</span>
                <span class="feed-company">${report.companyName}</span>
            </span>
            ${summary ? `<span class="feed-summary">${escapeHtml(summary)}</span>` : ''}
        </span>
        <span class="feed-right">${rightMeta}<span class="feed-chevron">›</span></span>
    `;
    return rowEl;
}

// Compact one-liner for a daily-digest feed item (macro/news bulletin) —
// ticker chip(s) + summary + source link, no reader/click-through.
function makeFeedItemRow(item) {
    const tickerChips = (item.tickers || []).map(t =>
        `<span class="feed-rating" style="background:rgba(0,136,255,0.12);color:var(--accent-neon);margin-right:4px;">$${escapeHtml(t)}</span>`
    ).join('');
    const tag = item.itemType === 'macro'
        ? `<span class="feed-rating" style="background:rgba(147,161,161,0.18);color:var(--text-secondary);">${activeLanguage === 'th' ? 'มหภาค' : 'MACRO'}</span>`
        : tickerChips;
    const sourceHtml = item.sourceUrl
        ? `<a href="${escapeHtml(item.sourceUrl)}" target="_blank" rel="noopener" onclick="event.stopPropagation();" style="font-size:0.72rem;color:var(--text-secondary);text-decoration:none;white-space:nowrap;">${escapeHtml(item.sourceName || (activeLanguage === 'th' ? 'แหล่งข่าว' : 'Source'))}</a>`
        : (item.sourceName ? `<span style="font-size:0.72rem;color:var(--text-secondary);white-space:nowrap;">${escapeHtml(item.sourceName)}</span>` : '');

    const rowEl = document.createElement("div");
    rowEl.className = "research-feed-row feed-item-row";
    rowEl.style.cursor = "default";
    rowEl.innerHTML = `
        <span style="display:flex;flex-wrap:wrap;gap:4px;flex-shrink:0;max-width:180px;">${tag}</span>
        <span class="feed-main">
            <span class="feed-summary" style="color:var(--text-primary);-webkit-line-clamp:3;">${escapeHtml((activeLanguage === 'th' && item.th_summary) ? item.th_summary : item.summary)}</span>
        </span>
        <span class="feed-right">${sourceHtml}</span>
    `;
    return rowEl;
}

function renderReportList() {
    const container = document.getElementById("report-list-container");
    if (!container) return;
    container.innerHTML = "";
    const { reports, query } = getFilteredSortedReports();

    const countEl = document.getElementById("research-feed-count");
    if (countEl) countEl.textContent = `${reports.length} report${reports.length === 1 ? '' : 's'}`;

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
    } else if (researchSortBy === 'date' && !query) {
        // Grouped by date (diary/timeline view) — reports arrive already
        // newest-first from getFilteredSortedReports(). Daily-digest feed
        // items (macro/news bulletins) are merged in under the same date
        // key — a date may have items but no report, or vice versa.
        const groups = {};
        const getGroup = d => { if (!groups[d]) groups[d] = { reports: [], items: [] }; return groups[d]; };
        reports.forEach(r => getGroup(r.researchDate || "undated").reports.push(r));
        feedItems.forEach(it => getGroup(it.itemDate || "undated").items.push(it));
        const dateKeys = Object.keys(groups).sort((a, b) => {
            if (a === "undated") return 1;
            if (b === "undated") return -1;
            return b.localeCompare(a);
        });
        dateKeys.forEach(dateKey => {
            const isCollapsed = collapsedDates[dateKey] === true;
            const { reports: dayReports, items: dayItems } = groups[dateKey];
            const total = dayReports.length + dayItems.length;
            const groupHeader = document.createElement("div");
            groupHeader.className = "report-date-header";
            groupHeader.style.cssText = "display:flex;justify-content:space-between;align-items:center;padding:10px 14px;background:var(--bg-card-solid);border:1px solid var(--border-dim);border-radius:6px;margin-top:10px;cursor:pointer;font-size:0.78rem;font-weight:700;color:var(--text-primary);user-select:none;transition:var(--transition);";
            groupHeader.onmouseover = () => { groupHeader.style.background = "rgba(147,161,161,0.15)"; };
            groupHeader.onmouseout  = () => { groupHeader.style.background = "var(--bg-card-solid)"; };
            groupHeader.onclick = () => { collapsedDates[dateKey] = !isCollapsed; renderReportList(); };
            const label = activeLanguage === "th" ? "รายการ" : (total === 1 ? "item" : "items");
            groupHeader.innerHTML = `<span>${formatGroupDateHeader(dateKey)} · ${total} ${label}</span><span style="font-size:0.65rem;display:inline-block;transform:${isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)'};">▼</span>`;
            container.appendChild(groupHeader);
            const wrapper = document.createElement("div");
            wrapper.style.cssText = "display:flex;flex-direction:column;gap:6px;margin-top:6px;padding-left:8px;";
            if (isCollapsed) wrapper.style.display = "none";
            dayReports.forEach(r => wrapper.appendChild(makeReportRow(r)));
            dayItems.forEach(it => wrapper.appendChild(makeFeedItemRow(it)));
            container.appendChild(wrapper);
        });
    } else {
        // Flat sorted list
        const wrapper = document.createElement("div");
        wrapper.style.cssText = "display:flex;flex-direction:column;gap:8px;margin-top:14px;";
        if (reports.length === 0) {
            wrapper.innerHTML = Object.keys(researchReports).length === 0
                ? `<div style="color:var(--text-secondary);font-size:0.85rem;text-align:center;padding:40px 0;">No research reports yet — hit <strong>+ New</strong> to write your first one.</div>`
                : `<div style="color:var(--text-secondary);font-size:0.82rem;text-align:center;padding:24px 0;">No reports match the current filter.</div>`;
        }
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
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:var(--text-secondary);padding:30px 0;">No reports match the current filter.</td></tr>`;
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
        tr.onclick = () => selectReport(r.key);
        tr.innerHTML = `
            <td style="font-family:var(--font-mono);font-size:0.8rem;color:var(--text-secondary);white-space:nowrap;">${formatResearchDate(r.researchDate)}</td>
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
    const [reportsData, itemsData] = await Promise.all([
        fetch('/api/reports').then(r => r.json()),
        fetch('/api/feed-items').then(r => r.ok ? r.json() : [])
    ]);
    researchReports = reportsData;
    feedItems = Array.isArray(itemsData) ? itemsData : [];
    renderReportList();
}

let reportModalMode = 'add'; // 'add' | 'edit'
let reportModalEditKey = null;

function openAddReportModal() {
    reportModalMode = 'add';
    reportModalEditKey = null;
    document.getElementById('report-modal-title').textContent = 'New Research Report';
    document.getElementById('report-form').reset();
    document.getElementById('rform-date').value = new Date().toISOString().slice(0, 10);
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
    document.getElementById('rform-date').value = r.researchDate || '';
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
        research_date: document.getElementById('rform-date').value || null,
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
        // If the deleted report was open in the reader, return to the feed
        const readerEl = document.getElementById("research-reader-view");
        if (readerEl && readerEl.style.display !== "none") {
            closeResearchReader();
        }
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
                <p style="color:var(--text-secondary);font-size:0.88rem;margin:0;">Select a report from the research feed to begin reading.</p>
            </div>`;
        return;
    }

    // Research date (reader top bar + meta ribbon)
    const dateStr = formatResearchDate(reportData.researchDate);
    const readerDateEl = document.getElementById("reader-date");
    if (readerDateEl) readerDateEl.textContent = reportData.researchDate ? `Research date: ${dateStr}` : "";
    const metaDateEl = document.getElementById("meta-val-date");
    if (metaDateEl) metaDateEl.textContent = dateStr;

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

    // Load localized body content — Overview and Reverse DCF render as one
    // continuous page with anchor sections for the jump chips.
    const reportContainer = document.getElementById("report-article-content");
    const overviewRaw = reportData[activeLanguage + "_overview"];
    const dcfRaw = reportData[activeLanguage + "_dcf"];

    let html = "";
    if (overviewRaw) {
        html += `<div id="reader-sec-overview">${marked.parse(overviewRaw)}</div>`;
    }
    if (dcfRaw) {
        html += `<hr style="border:none;border-top:1px solid var(--border-dim);margin:36px 0;">`;
        html += `<div id="reader-sec-dcf">${marked.parse(dcfRaw)}</div>`;
    }
    if (!html) {
        html = "<em>Content not available for this report.</em>";
    }
    // Report bodies are freeform markdown rendered to HTML — sanitize to
    // strip any embedded scripts/handlers before injecting.
    reportContainer.innerHTML = window.DOMPurify ? DOMPurify.sanitize(html) : html;

    // Hide the DCF jump chip when the report has no DCF section
    const dcfChip = document.getElementById("jump-chip-dcf");
    if (dcfChip) dcfChip.style.display = dcfRaw ? "" : "none";

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

    // 1. Fetch live exchange rates from Yahoo Finance (USD/THB and EUR/USD)
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
    const eurRatePromise = (async () => {
        try {
            const response = await fetch(`/api/stock?ticker=EURUSD=X`);
            if (response.ok) {
                const data = await response.json();
                if (data.price) {
                    exchangeRateEURUSD = data.price;
                    console.log("Updated EUR/USD exchange rate to:", exchangeRateEURUSD);
                }
            }
        } catch (err) {
            console.warn("Failed to fetch live EUR/USD rate:", err);
        }
    })();

    // 2. Fetch prices for all holdings
    const promises = holdings.map(async (pos) => {
        if (pos.manualPrice) return; // User-entered market price overrides live fetch
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
    await Promise.all([...promises, ratePromise, eurRatePromise]);

    // Save prices to localStorage cache for instant render on next page load
    const priceCache = { __ts__: Date.now(), __rate__: exchangeRateUSDTHB, __rateEURUSD__: exchangeRateEURUSD };
    holdings.forEach(h => { if (!h.manualPrice) priceCache[h.ticker] = h.currentPrice; });
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
