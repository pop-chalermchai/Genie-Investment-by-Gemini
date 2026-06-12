#!/usr/bin/env python3
"""
Stock Holdings Database Initialization & Seeding Script
Christian, Forensic Auditor & Quantitative Analyst Team
"""

import os
import sqlite3
from datetime import datetime

DB_NAME = "stock_holdings.db"
SCHEMA_FILE = "schema.sql"

def main():
    print("=" * 60)
    print("INITIALIZING STOCK HOLDINGS DATABASE")
    print("=" * 60)

    # 1. Connect to SQLite database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    print(f"Connected to database: {DB_NAME}")

    # 2. Read and execute Schema SQL
    if os.path.exists(SCHEMA_FILE):
        with open(SCHEMA_FILE, "r") as f:
            schema_sql = f.read()
        cursor.executescript(schema_sql)
        print("Schema successfully executed and tables created.")
    else:
        print(f"Error: {SCHEMA_FILE} not found. DB not initialized.")
        return

    # 3. Seed Assets
    assets_data = [
        ("FPS", "Forgent Power Solutions, Inc.", "Industrial Goods", "Electrical Powertrains & eHouses", "USD"),
        ("JBL", "Jabil Inc.", "Technology", "Electronics Manufacturing Services", "USD"),
        ("MSFT", "Microsoft Corporation", "Technology", "Software & Cloud Infrastructure", "USD"),
        ("AAPL", "Apple Inc.", "Technology", "Consumer Electronics", "USD")
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO assets (ticker, company_name, sector, industry, currency)
        VALUES (?, ?, ?, ?, ?)
    """, assets_data)
    print("Seeded asset master definitions.")

    # 4. Seed Portfolio
    cursor.execute("""
        INSERT OR REPLACE INTO portfolios (portfolio_id, name, description)
        VALUES (1, "Pop's Alpha Fund", "Strategic high-conviction asymmetric investment portfolio")
    """)
    print("Seeded master portfolio: 'Pop's Alpha Fund'.")

    # 5. Seed Transactions (Buy events at our target entry levels)
    transactions_data = [
        (1, "JBL", "BUY", 1000.0, 285.00, 150.0, "Acquired at maximum Buy-In entry limit limit"),
        (1, "FPS", "BUY", 5000.0, 47.00, 250.0, "Allocated at primary Class A offering price"),
        (1, "MSFT", "BUY", 500.0, 415.00, 50.0, "Hyperscaler structural cloud play")
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO transactions (portfolio_id, ticker, transaction_type, quantity, price_per_share, fees, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, transactions_data)
    print("Seeded historic purchase transactions.")

    # 6. Seed Current Quotes (Active market prices as of June 2, 2026)
    quotes_data = [
        ("FPS", 56.35),
        ("JBL", 365.00),
        ("MSFT", 430.00),
        ("AAPL", 190.50)
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO quotes (ticker, current_price, last_updated)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """, quotes_data)
    print("Seeded active market quotes.")

    conn.commit()
    print("Transaction committed successfully.")

    # 7. Perform Portfolio Valuation Query
    print("\n" + "=" * 60)
    print("POP'S ALPHA FUND — CURRENT PORTFOLIO VALUATION")
    print("=" * 60)

    query = """
        SELECT 
            t.ticker,
            SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity ELSE -t.quantity END) as total_shares,
            SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity * t.price_per_share + t.fees ELSE -t.quantity * t.price_per_share + t.fees END) / 
                SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity ELSE -t.quantity END) as avg_cost,
            q.current_price,
            SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity ELSE -t.quantity END) * q.current_price as market_value
        FROM transactions t
        JOIN quotes q ON t.ticker = q.ticker
        GROUP BY t.ticker
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    print(f"{'Ticker':<8} | {'Shares':<10} | {'Avg Cost':<12} | {'Current Price':<15} | {'Market Value':<15} | {'Gain/Loss':<12}")
    print("-" * 80)
    
    total_cost_basis = 0.0
    total_market_value = 0.0

    for row in rows:
        ticker, shares, avg_cost, current_price, market_value = row
        cost_basis = shares * avg_cost
        gain_loss = market_value - cost_basis
        gain_loss_pct = (gain_loss / cost_basis) * 100 if cost_basis > 0 else 0
        
        total_cost_basis += cost_basis
        total_market_value += market_value
        
        print(f"{ticker:<8} | {shares:<10,.1f} | ${avg_cost:<11,.2f} | ${current_price:<14,.2f} | ${market_value:<14,.2f} | ${gain_loss:<10,.2f} ({gain_loss_pct:+.1f}%)")

    portfolio_gain = total_market_value - total_cost_basis
    portfolio_gain_pct = (portfolio_gain / total_cost_basis) * 100 if total_cost_basis > 0 else 0

    print("-" * 80)
    print(f"{'TOTALS':<8} | {'':<10} | ${total_cost_basis:<11,.2f} | {'':<14} | ${total_market_value:<14,.2f} | ${portfolio_gain:<10,.2f} ({portfolio_gain_pct:+.1f}%)")
    print("=" * 80)

    conn.close()

if __name__ == "__main__":
    main()
