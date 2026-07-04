let parsedExcelTransactions = [];

function copyTemplateAsCSV() {
    const csvContent = 
`Date,Ticker,Company Name,Sector,Sub-Portfolio,Type,Shares,Price,Currency
2026-06-14 10:00:00,AAPL,Apple Inc.,Technology,Dime,BUY,10,180.5,USD
2026-06-14 14:30:00,TSLA,Tesla Inc.,Consumer Cyclical,WeBull,SELL,5,175.0,USD
2026-06-14 16:00:00,7-11,CP All,Consumer Defensive,Tax Saving Fund,BUY,100,58.25,THB`;

    navigator.clipboard.writeText(csvContent).then(() => {
        alert("Standard CSV template copied to clipboard!\nYou can paste it into Excel or any text editor, then save it as an Excel (.xlsx) or CSV file.");
    }).catch(err => {
        console.error("Failed to copy template: ", err);
        // Fallback using prompt
        window.prompt("Could not copy automatically. Please copy the CSV text below manually:", csvContent);
    });
}

function setupDragAndDrop() {
    const dropZone = document.getElementById("upload-drop-zone");
    if (!dropZone) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('drop-zone--over'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('drop-zone--over'), false);
    });

    dropZone.addEventListener('drop', handleDrop, false);

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            const input = document.getElementById("excel-file-input");
            if (input) {
                input.files = files;
                handleExcelUpload({ target: input });
            }
        }
    }
}

function handleExcelUpload(event) {
    if (typeof XLSX === 'undefined') {
        alert("Error: SheetJS library (XLSX) is not loaded.\nPlease check your internet connection or check the browser console for network errors.");
        return;
    }
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, { type: 'array' });
            
            const sheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[sheetName];
            
            const rows = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
            if (rows.length <= 1) {
                alert("The Excel file is empty or missing data rows.");
                cancelExcelUpload();
                return;
            }
            
            const headers = rows[0].map(h => String(h).trim().toLowerCase());
            
            const colIndices = {
                date: headers.indexOf("date"),
                ticker: headers.indexOf("ticker"),
                companyName: headers.indexOf("company name"),
                sector: headers.indexOf("sector"),
                portfolio: headers.indexOf("sub-portfolio"),
                type: headers.indexOf("type"),
                shares: headers.indexOf("shares"),
                price: headers.indexOf("price"),
                currency: headers.indexOf("currency")
            };
            
            const requiredCols = ["ticker", "portfolio", "type", "shares", "price"];
            for (const col of requiredCols) {
                if (colIndices[col] === -1) {
                    alert(`Missing required column in Excel: "${col}"`);
                    cancelExcelUpload();
                    return;
                }
            }
            
            parsedExcelTransactions = [];
            let errorCount = 0;
            let errorMsg = "";
            
            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                if (!row || row.length === 0 || row.every(cell => cell === null || cell === undefined || cell === "")) {
                    continue;
                }
                
                const getCell = (colKey) => {
                    const idx = colIndices[colKey];
                    return idx !== -1 && row[idx] !== undefined && row[idx] !== null ? String(row[idx]).trim() : "";
                };
                
                const ticker = getCell("ticker").toUpperCase();
                const portfolio = getCell("portfolio");
                const type = getCell("type").toUpperCase();
                const sharesVal = parseFloat(getCell("shares"));
                const priceVal = parseFloat(getCell("price"));
                
                let date = getCell("date");
                let companyName = getCell("companyName");
                let sector = getCell("sector");
                let currency = getCell("currency").toUpperCase();
                
                if (!ticker) {
                    errorCount++;
                    errorMsg += `Row ${i+1}: Ticker is empty\n`;
                    continue;
                }
                if (!portfolio) {
                    errorCount++;
                    errorMsg += `Row ${i+1} (${ticker}): Sub-Portfolio is empty\n`;
                    continue;
                }
                
                const validPortfolios = ["Dime", "WeBull", "Tax Saving Fund", "Provident Fund"];
                const matchingPortfolio = validPortfolios.find(p => p.toLowerCase() === portfolio.toLowerCase());
                if (!matchingPortfolio) {
                    errorCount++;
                    errorMsg += `Row ${i+1} (${ticker}): Portfolio must be one of [Dime, WeBull, Tax Saving Fund, Provident Fund]\n`;
                    continue;
                }
                
                if (type !== "BUY" && type !== "SELL") {
                    errorCount++;
                    errorMsg += `Row ${i+1} (${ticker}): Type must be BUY or SELL\n`;
                    continue;
                }
                
                if (isNaN(sharesVal) || sharesVal <= 0) {
                    errorCount++;
                    errorMsg += `Row ${i+1} (${ticker}): Shares must be a positive number\n`;
                    continue;
                }
                
                if (isNaN(priceVal) || priceVal <= 0) {
                    errorCount++;
                    errorMsg += `Row ${i+1} (${ticker}): Price must be a positive number\n`;
                    continue;
                }
                
                if (!companyName) companyName = ticker;
                if (!sector) sector = "Technology";
                if (!currency) currency = "USD";
                if (currency !== "USD" && currency !== "THB") currency = "USD";
                
                if (date) {
                    if (!isNaN(date) && parseFloat(date) > 20000 && parseFloat(date) < 60000) {
                        const serial = parseFloat(date);
                        const utc_days  = Math.floor(serial - 25569);
                        const utc_value = utc_days * 86400;                                        
                        const date_info = new Date(utc_value * 1000);
                        const fractional_day = serial - Math.floor(serial) + 0.0000001;
                        let total_seconds = Math.floor(86400 * fractional_day);
                        const seconds = total_seconds % 60;
                        total_seconds -= seconds;
                        const minutes = Math.floor(total_seconds / 60) % 60;
                        const hours = Math.floor(total_seconds / 3600);
                        date_info.setHours(hours, minutes, seconds);
                        
                        const pad = (n) => String(n).padStart(2, '0');
                        date = `${date_info.getFullYear()}-${pad(date_info.getMonth()+1)}-${pad(date_info.getDate())} ${pad(date_info.getHours())}:${pad(date_info.getMinutes())}:${pad(date_info.getSeconds())}`;
                    } else {
                        const parsedDate = new Date(date);
                        if (!isNaN(parsedDate.getTime())) {
                            const pad = (n) => String(n).padStart(2, '0');
                            date = `${parsedDate.getFullYear()}-${pad(parsedDate.getMonth()+1)}-${pad(parsedDate.getDate())} ${pad(parsedDate.getHours())}:${pad(parsedDate.getMinutes())}:${pad(parsedDate.getSeconds())}`;
                        } else {
                            date = "";
                        }
                    }
                }
                
                parsedExcelTransactions.push({
                    date,
                    ticker,
                    companyName,
                    sector,
                    portfolio: matchingPortfolio,
                    type,
                    shares: sharesVal,
                    avgCost: priceVal,
                    currency
                });
            }
            
            if (errorCount > 0) {
                alert(`Found ${errorCount} formatting errors:\n\n${errorMsg.substring(0, 500)}${errorMsg.length > 500 ? '...' : ''}\nPlease fix the Excel file and try again.`);
                cancelExcelUpload();
                return;
            }
            
            if (parsedExcelTransactions.length === 0) {
                alert("No valid transaction rows found in the sheet.");
                cancelExcelUpload();
                return;
            }
            
            renderExcelPreview();
            
        } catch (err) {
            console.error("Error reading excel file:", err);
            alert("Error reading Excel file. Please ensure it is a valid .xlsx or .xls file.");
            cancelExcelUpload();
        }
    };
    reader.readAsArrayBuffer(file);
}

function renderExcelPreview() {
    const previewContainer = document.getElementById("excel-preview-container");
    const previewCount = document.getElementById("preview-count");
    const previewBody = document.getElementById("excel-preview-body");
    
    if (!previewContainer || !previewCount || !previewBody) return;
    
    previewCount.innerText = parsedExcelTransactions.length;
    previewBody.innerHTML = "";
    
    parsedExcelTransactions.forEach(tx => {
        const row = document.createElement("tr");
        
        const typeStyle = tx.type === "BUY" ? "color: #10B981; font-weight: 600;" : "color: #EF4444; font-weight: 600;";
        const currencySymbol = tx.currency === "USD" ? "$" : "฿";
        
        row.innerHTML = `
            <td style="color: var(--text-secondary);">${tx.date || "<i>(Now)</i>"}</td>
            <td style="font-weight: 700; color: var(--text-primary);">${tx.ticker}</td>
            <td>${tx.companyName}</td>
            <td style="${typeStyle}">${tx.type}</td>
            <td class="text-right">${tx.shares.toLocaleString()}</td>
            <td class="text-right">${currencySymbol}${tx.avgCost.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 4})}</td>
            <td>${tx.currency}</td>
            <td><span class="badge" style="background: rgba(255,255,255,0.05); color: var(--text-primary); padding: 2px 6px; border-radius: 4px; font-size: 0.75rem;">${tx.portfolio}</span></td>
        `;
        previewBody.appendChild(row);
    });
    
    previewContainer.style.display = "block";
}

function cancelExcelUpload() {
    const input = document.getElementById("excel-file-input");
    if (input) input.value = "";
    
    const previewContainer = document.getElementById("excel-preview-container");
    if (previewContainer) previewContainer.style.display = "none";
    
    parsedExcelTransactions = [];
}

function confirmExcelUpload() {
    if (parsedExcelTransactions.length === 0) return;
    
    const btn = document.getElementById("btn-confirm-upload");
    const originalText = btn.innerText;
    btn.disabled = true;
    btn.innerText = "⏳ Ingesting...";
    
    fetch('/api/bulk-ingest', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            transactions: parsedExcelTransactions
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Successfully imported ${data.count} transactions!`);
            cancelExcelUpload();
            
            // Re-fetch transactions & holdings
            loadTransactions();
            
            fetch('/api/holdings')
                .then(r => r.json())
                .then(hData => {
                    holdings = hData.map(h => ({...h, currentPrice: h.avgCost}));
                    updateDashboard();
                    fetchLivePrices(); // Update to live price
                });
        } else {
            alert("Import error: " + data.error);
        }
    })
    .catch(err => {
        console.error("Error confirm upload:", err);
        alert("Failed to import transactions.");
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerText = originalText;
    });
}

// ==========================================================================
// FEATURE: STOCK TRANSFERS BETWEEN SUB-PORTFOLIOS
// ==========================================================================
function openTransferStockModal() {
    const modal = document.getElementById("transfer-stock-modal");
    if (!modal) return;
    
    // Clear fields
    document.getElementById("transfer-stock-form").reset();
    document.getElementById("transfer-source-available").innerText = "";
    
    // Populate Ticker select dropdown with tickers from holdings
    const tickerSelect = document.getElementById("transfer-ticker");
    tickerSelect.innerHTML = '<option value="" disabled selected>Select Ticker...</option>';
    
    // Get unique tickers that currently have active shares > 0
    const uniqueTickers = [...new Set(holdings.map(h => h.ticker))].sort();
    
    uniqueTickers.forEach(ticker => {
        const option = document.createElement("option");
        option.value = ticker;
        option.text = ticker;
        tickerSelect.appendChild(option);
    });
    
    modal.classList.add("active");
}

function closeTransferStockModal() {
    const modal = document.getElementById("transfer-stock-modal");
    if (modal) modal.classList.remove("active");
}

function onTransferTickerChange() {
    const ticker = document.getElementById("transfer-ticker").value;
    const sourceSelect = document.getElementById("transfer-source");
    sourceSelect.innerHTML = '<option value="" disabled selected>Select Source...</option>';
    
    // Find all portfolios that hold this ticker
    const holdingPorts = holdings.filter(h => h.ticker === ticker);
    
    holdingPorts.forEach(hp => {
        // Find portfolio ID for the portfolio name
        const portObj = portfoliosList.find(p => p.name === hp.portfolio && p.parentId !== null);
        if (portObj) {
            const option = document.createElement("option");
            option.value = portObj.id;
            option.text = `${hp.parentPortfolio || hp.portfolio} - ${hp.portfolio}`;
            // Store shares and average cost in attributes for easy access
            option.setAttribute("data-shares", hp.shares);
            option.setAttribute("data-cost", hp.avgCost);
            sourceSelect.appendChild(option);
        }
    });
    
    document.getElementById("transfer-source-available").innerText = "";
    document.getElementById("transfer-dest").innerHTML = '<option value="" disabled selected>Select Destination...</option>';
}

function onTransferSourceChange() {
    const sourceSelect = document.getElementById("transfer-source");
    const selectedOption = sourceSelect.options[sourceSelect.selectedIndex];
    
    if (!selectedOption) return;
    
    const shares = parseFloat(selectedOption.getAttribute("data-shares"));
    const cost = parseFloat(selectedOption.getAttribute("data-cost"));
    
    document.getElementById("transfer-source-available").innerText = `Available: ${formatShares(shares)} shares (Avg Cost: $${cost.toFixed(2)})`;
    
    // Pre-fill fields
    document.getElementById("transfer-shares").value = shares;
    document.getElementById("transfer-price").value = cost.toFixed(2);
    
    // Populate Destination dropdown with sub-portfolios EXCEPT the source portfolio
    const sourceId = parseInt(sourceSelect.value);
    const destSelect = document.getElementById("transfer-dest");
    destSelect.innerHTML = '<option value="" disabled selected>Select Destination...</option>';
    
    const subPorts = portfoliosList.filter(p => p.parentId !== null && p.id !== sourceId);
    subPorts.forEach(p => {
        const option = document.createElement("option");
        option.value = p.id;
        option.text = `${p.parentName} - ${p.name}`;
        destSelect.appendChild(option);
    });
}

function handleTransferStock(event) {
    event.preventDefault();
    
    const ticker = document.getElementById("transfer-ticker").value;
    const sourcePortfolioId = parseInt(document.getElementById("transfer-source").value);
    const destPortfolioId = parseInt(document.getElementById("transfer-dest").value);
    const shares = parseFloat(document.getElementById("transfer-shares").value);
    const price = parseFloat(document.getElementById("transfer-price").value);
    
    if (sourcePortfolioId === destPortfolioId) {
        alert("Source and Destination portfolios must be different!");
        return;
    }
    
    fetch('/api/transfer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            sourcePortfolioId,
            destPortfolioId,
            ticker,
            shares,
            price
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            alert("Stock transferred successfully!");
            closeTransferStockModal();
            
            // Re-fetch holdings
            fetch('/api/holdings')
                .then(r => r.json())
                .then(hData => {
                    holdings = hData.map(h => ({...h, currentPrice: h.avgCost}));
                    updateDashboard();
                    fetchLivePrices(); // update with real prices
                });
        } else {
            alert("Error transferring stock: " + data.error);
        }
    })
    .catch(err => {
        console.error("Error during transfer:", err);
        alert("Failed to transfer stock.");
    });
}

// ---------------------------------------------
// CATEGORY MANAGEMENT MODAL & OPERATIONS
// ---------------------------------------------
function openManageCategoriesModal() {
    renderCategoriesList();
    document.getElementById("manage-categories-modal").classList.add("active");
}

function closeManageCategoriesModal() {
    document.getElementById("manage-categories-modal").classList.remove("active");
}

function renderCategoriesList() {
    const container = document.getElementById("categories-list-container");
    if (!container) return;
    
    container.innerHTML = "";
    
    if (categoriesList.length === 0) {
        container.innerHTML = `<div style="color:var(--text-secondary); text-align:center; padding: 20px; font-style:italic;">No categories found. Add one below.</div>`;
        return;
    }
    
    categoriesList.forEach(cat => {
        const row = document.createElement("div");
        row.style.cssText = "display:flex; justify-content:space-between; align-items:center; padding: 10px 8px; border-bottom: 1px solid rgba(255,255,255,0.05); gap: 10px;";
        row.innerHTML = `
            <span id="cat-display-${cat.id}" style="color:#fff; font-weight:600; font-size:0.9rem;">${cat.name}</span>
            <div style="display:flex; gap: 8px;">
                <button type="button" onclick="editCategoryInline(${cat.id}, '${cat.name.replace(/'/g, "\\'")}')" class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.72rem; border-radius: 4px; border: 1px solid var(--border-dim); background: var(--bg-card-solid); color: var(--text-primary); cursor: pointer;">Edit</button>
                <button type="button" onclick="deleteCategoryInline(${cat.id}, '${cat.name.replace(/'/g, "\\'")}')" class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.72rem; border-radius: 4px; border: 1px solid var(--border-dim); background: rgba(239, 68, 68, 0.1); color: var(--color-negative); cursor: pointer;">Delete</button>
            </div>
        `;
        container.appendChild(row);
    });
}

function handleAddCategorySubmit(e) {
    e.preventDefault();
    const name = document.getElementById("new-cat-name").value.trim();
    if (!name) return;
    
    fetch('/api/categories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            document.getElementById("add-category-form").reset();
            // Re-fetch category list and refresh
            fetch('/api/categories')
            .then(res => res.json())
            .then(cats => {
                categoriesList = cats;
                renderCategoriesList();
                populateDropdowns();
            });
        } else {
            alert("Error adding category: " + data.error);
        }
    })
    .catch(err => {
        console.error("Error adding category:", err);
        alert("Failed to add category.");
    });
}

function editCategoryInline(catId, currentName) {
    const newName = prompt(`Rename category "${currentName}" to:`, currentName);
    if (!newName || newName.trim() === "" || newName.trim() === currentName) return;
    
    fetch('/api/categories', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: catId, name: newName.trim() })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            // Re-fetch category list and refresh
            fetch('/api/categories')
            .then(res => res.json())
            .then(cats => {
                categoriesList = cats;
                renderCategoriesList();
                populateDropdowns();
                fetchInitData(); // Fetch whole init data to refresh any name mapping
            });
        } else {
            alert("Error renaming category: " + data.error);
        }
    })
    .catch(err => {
        console.error("Error renaming category:", err);
        alert("Failed to rename category.");
    });
}

function deleteCategoryInline(catId, catName) {
    if (confirm(`Are you sure you want to delete category "${catName}"?\nAny portfolios referencing this category will have their category cleared.`)) {
        fetch('/api/categories?id=' + catId, {
            method: 'DELETE'
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                // Re-fetch category list and refresh
                fetch('/api/categories')
                .then(res => res.json())
                .then(cats => {
                    categoriesList = cats;
                    renderCategoriesList();
                    populateDropdowns();
                    fetchInitData(); // Fetch whole init data to refresh database state
                });
            } else {
                alert("Error deleting category: " + data.error);
            }
        })
        .catch(err => {
            console.error("Error deleting category:", err);
            alert("Failed to delete category.");
        });
    }
}
