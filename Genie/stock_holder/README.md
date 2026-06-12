# 📂 Stock Holdings Database System

Welcome to the **Stock Holdings Database System** for Pop's high-conviction portfolios. This system uses a lightweight, self-contained **SQLite** database (`stock_holdings.db`) to record asset definitions, transaction logs, and live price feeds to automatically track cost bases, valuations, and unrealized gains.

---

## 🏛️ Database Architecture & Schema

The database consists of four highly optimized relational tables designed for financial precision:

```mermaid
erDiagram
    PORTFOLIOS ||--o{ TRANSACTIONS : contains
    ASSETS ||--o{ TRANSACTIONS : logs
    ASSETS ||--|| QUOTES : has
    
    PORTFOLIOS {
        INTEGER portfolio_id PK
        TEXT name UNIQUE
        TEXT description
        TIMESTAMP created_at
    }
    
    ASSETS {
        TEXT ticker PK
        TEXT company_name
        TEXT sector
        TEXT industry
        TEXT currency
    }
    
    TRANSACTIONS {
        INTEGER transaction_id PK
        INTEGER portfolio_id FK
        TEXT ticker FK
        TEXT transaction_type
        REAL quantity
        REAL price_per_share
        TIMESTAMP transaction_date
        REAL fees
        TEXT notes
    }
    
    QUOTES {
        TEXT ticker PK
        REAL current_price
        TIMESTAMP last_updated
    }
```

---

## 🚀 How to Initialize and Seed

We have included a Python initialization script that automatically creates the database, applies the schema, seeds it with our Jabil and Forgent investment metrics, and outputs a portfolio valuation summary.

### 1. Run the Python Initialization Script
Run the script directly from your terminal:
```bash
./init_db.py
```

This will generate:
- 🗄️ `stock_holdings.db` (SQLite binary database)
- 📊 A terminal dashboard of current holdings, cost bases, market values, and unrealized gains.

---

## 📥 Automated Position Ingestion

To make it incredibly easy to load your external stock holding sheets, we have included an automated ingestion script: **`ingest_holdings.py`**.

### 1. Supported File Formats
You can save any holdings sheet as a **CSV** (comma-separated) or **JSON** file in this folder. The ingestion engine is extremely flexible and case-insensitive. It automatically maps and standardizes columns like:
*   **Asset Identifier:** `ticker`, `symbol`, `stock`, `code`
*   **Asset Details:** `company_name`, `sector`, `industry`
*   **Transaction:** `shares`, `quantity`, `qty`
*   **Pricing:** `avg_cost`, `price`, `cost_basis`, `price_per_share`
*   **Current Feed (Optional):** `current_price`, `market_price`, `quote`

#### Example `holdings.csv` format:
```csv
ticker,company_name,shares,avg_cost,current_price,sector
AAPL,Apple Inc.,100,175.50,190.50,Technology
GOOGL,Alphabet Inc.,50,165.00,175.20,Technology
```

### 2. Run the Ingestion Script
Save your file (e.g. `holdings.csv`) directly in the `/Users/popular/Desktop/Genie/stock_holder/` folder, then run:
```bash
./ingest_holdings.py
```

The script will:
1.  Scan the folder for new CSV/JSON files.
2.  Import all asset definitions, transaction positions, and cached quotes.
3.  Archive the imported spreadsheet into the `archive/` subfolder (with a timestamp) to prevent double imports.
4.  Re-run the portfolio valuation query to display your updated holdings, total cost bases, and returns in real-time.

---

## 🔍 Key SQL Queries

You can connect to `stock_holdings.db` using any SQLite client (e.g., DBeaver, TablePlus, or the `sqlite3` CLI) to run standard queries:

### A. Insert a New Asset / Ticker
```sql
INSERT INTO assets (ticker, company_name, sector, industry)
VALUES ('AAPL', 'Apple Inc.', 'Technology', 'Consumer Electronics');
```

### B. Record a Purchase (BUY)
```sql
INSERT INTO transactions (portfolio_id, ticker, transaction_type, quantity, price_per_share, fees, notes)
VALUES (1, 'FPS', 'BUY', 500.0, 56.35, 10.0, 'Accumulated on momentum break');
```

### C. Update Active Market Prices (Quotes)
```sql
INSERT OR REPLACE INTO quotes (ticker, current_price, last_updated)
VALUES ('FPS', 58.20, CURRENT_TIMESTAMP);
```

### D. Generate Full Portfolio Valuation & Gain/Loss Report
```sql
SELECT 
    t.ticker,
    SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity ELSE -t.quantity END) as total_shares,
    SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity * t.price_per_share + t.fees ELSE -t.quantity * t.price_per_share + t.fees END) / 
        SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity ELSE -t.quantity END) as weighted_avg_cost,
    q.current_price,
    SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity ELSE -t.quantity END) * q.current_price as market_value,
    (SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity ELSE -t.quantity END) * q.current_price) - 
        SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity * t.price_per_share + t.fees ELSE -t.quantity * t.price_per_share + t.fees END) as unrealized_gain_loss
FROM transactions t
JOIN quotes q ON t.ticker = q.ticker
GROUP BY t.ticker;
```

---

## 🗂️ Files Reference:
*   [schema.sql](file:///Users/popular/Desktop/Genie/stock_holder/schema.sql) - *DDL table definitions*
*   [init_db.py](file:///Users/popular/Desktop/Genie/stock_holder/init_db.py) - *Python database setup & demo query runner*
*   [ingest_holdings.py](file:///Users/popular/Desktop/Genie/stock_holder/ingest_holdings.py) - *Automated position loader and archiver*
*   [README.md](file:///Users/popular/Desktop/Genie/stock_holder/README.md) - *This documentation*
