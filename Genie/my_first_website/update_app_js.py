import os

app_js_path = os.path.join(os.path.dirname(__file__), 'app.js')

with open(app_js_path, 'r', encoding='utf-8') as f:
    code = f.read()

start_str = "const researchReports = {"
end_str = "};\n\n// ==========================================================================\n// CORE WORKSPACE INITIALIZATION"

s = code.find(start_str)
e = code.find(end_str)

if s != -1 and e != -1:
    before = code[:s]
    after = code[e + len("};\n\n"):]
    
    # We replace with `let researchReports = {};\n\n`
    new_code = before + "let researchReports = {};\n\n" + after
    
    # Now we need to update DOMContentLoaded
    dom_content_loaded = """document.addEventListener("DOMContentLoaded", () => {
    fetch('/api/holdings')
        .then(response => response.json())
        .then(data => {
            // Our DB API currently doesn't return 'currentPrice'. 
            // The fetchLivePrices function handles fetching the live price and recalculating.
            // For now, default currentPrice to avgCost so it doesn't break math before live fetch completes.
            holdings = data.map(h => ({...h, currentPrice: h.avgCost}));
            updateDashboard();
            renderReport();
            fetchLivePrices(); // Automatically fetch live prices on startup
        })
        .catch(err => console.error("Error fetching holdings:", err));
});"""
    
    new_dom_content_loaded = """document.addEventListener("DOMContentLoaded", () => {
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
        fetchLivePrices();
    })
    .catch(err => console.error("Error fetching data:", err));
});"""

    new_code = new_code.replace(dom_content_loaded, new_dom_content_loaded)
    
    # Add renderReportList function before renderReport
    render_report_list_func = """
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
"""
    
    # Insert renderReportList just before renderReport() definition
    render_report_idx = new_code.find("function renderReport() {")
    if render_report_idx != -1:
        new_code = new_code[:render_report_idx] + render_report_list_func + "\n" + new_code[render_report_idx:]
    
    # Update selectReport to also re-render the list so active class updates
    select_report_old = """function selectReport(reportKey) {
    activeReport = reportKey;
    
    // Update active class in sidebar
    document.querySelectorAll(".report-list-item").forEach(btn => {
        btn.classList.remove("active");
    });
    const activeBtn = document.getElementById(`report-item-${reportKey}`);
    if (activeBtn) activeBtn.classList.add("active");

    renderReport();
}"""
    
    select_report_new = """function selectReport(reportKey) {
    activeReport = reportKey;
    renderReportList(); // update active classes dynamically
    renderReport();
}"""
    
    new_code = new_code.replace(select_report_old, select_report_new)
    
    with open(app_js_path, 'w', encoding='utf-8') as f:
        f.write(new_code)
    print("Updated app.js successfully")
else:
    print("Could not find start/end markers in app.js")
