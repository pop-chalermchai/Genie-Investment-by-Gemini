-- SQLite Database Schema for Stock Holdings Database
-- Created on 2026-06-02

-- 1. Portfolios Table
CREATE TABLE IF NOT EXISTS portfolios (
    portfolio_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tickers/Assets Table
CREATE TABLE IF NOT EXISTS assets (
    ticker TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    sector TEXT,
    industry TEXT,
    currency TEXT DEFAULT 'USD'
);

-- 3. Transactions Table (Logs all buy/sell events)
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    transaction_type TEXT CHECK(transaction_type IN ('BUY', 'SELL')) NOT NULL,
    quantity REAL NOT NULL,
    price_per_share REAL NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fees REAL DEFAULT 0.0,
    notes TEXT,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id),
    FOREIGN KEY (ticker) REFERENCES assets(ticker)
);

-- 4. Current Quotes Table (Cached current prices for valuation)
CREATE TABLE IF NOT EXISTS quotes (
    ticker TEXT PRIMARY KEY,
    current_price REAL NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker) REFERENCES assets(ticker)
);
