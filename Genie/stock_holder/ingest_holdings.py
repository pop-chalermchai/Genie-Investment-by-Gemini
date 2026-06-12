#!/usr/bin/env python3
"""
Automated Stock Holdings Ingest Script
Christian, Forensic Auditor
"""

import os
import csv
import json
import sqlite3
from datetime import datetime

DB_NAME = "stock_holdings.db"
DEFAULT_PORTFOLIO_ID = 1

def log_message(msg):
    print(f"[*] {msg}")

def normalize_headers(headers):
    """Normalize headers to standard lowercase names for flexible mapping."""
    mapping = {
        'ticker': ['ticker', 'symbol', 'stock', 'code', 'asset'],
        'company_name': ['company_name', 'name', 'company', 'description'],
        'transaction_type': ['transaction_type', 'type', 'action', 'buy_sell', 'tx_type'],
        'quantity': ['quantity', 'shares', 'qty', 'units', 'volume'],
        'price_per_share': ['price_per_share', 'price', 'avg_cost', 'cost', 'cost_basis', 'buy_price', 'price/share'],
        'fees': ['fees', 'commission', 'fee', 'tx_fees'],
        'notes': ['notes', 'comment', 'notes/memo', 'memo'],
        'current_price': ['current_price', 'last_price', 'quote', 'market_price'],
        'sector': ['sector', 'category'],
        'industry': ['industry', 'subsector']
    }
    
    normalized = {}
    for h in headers:
        clean = h.strip().lower().replace(' ', '_').replace('/', '_')
        matched = False
        for std_key, alt_names in mapping.items():
            if clean in alt_names or clean.replace('_', '') in alt_names:
                normalized[h] = std_key
                matched = True
                break
        if not matched:
            normalized[h] = clean
    return normalized

def parse_csv(filepath):
    """Parse CSV file and return list of dictionaries with normalized keys."""
    results = []
    with open(filepath, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            return []
            
        norm_map = normalize_headers(headers)
        
        for row in reader:
            if not row or all(x.strip() == '' for x in row):
                continue
            entry = {}
            for idx, val in enumerate(row):
                if idx < len(headers):
                    orig_h = headers[idx]
                    std_h = norm_map[orig_h]
                    entry[std_h] = val.strip()
            results.append(entry)
    return results

def parse_json(filepath):
    """Parse JSON file and normalize keys."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle list of items or nested dictionary
    if isinstance(data, dict):
        if 'holdings' in data:
            items = data['holdings']
        elif 'transactions' in data:
            items = data['transactions']
        else:
            items = [data]
    elif isinstance(data, list):
        items = data
    else:
        return []
        
    results = []
    for item in items:
        # Normalize keys in dict
        norm_map = normalize_headers(item.keys())
        norm_item = {norm_map[k]: v for k, v in item.items()}
        results.append(norm_item)
    return results

def ingest_data(conn, parsed_data):
    """Ingest normalized transaction or holding data into SQLite."""
    cursor = conn.cursor()
    
    inserted_assets = 0
    inserted_txs = 0
    updated_quotes = 0
    
    for row in parsed_data:
        ticker = row.get('ticker')
        if not ticker:
            continue
        ticker = ticker.upper()
        
        # 1. Upsert Asset details
        company_name = row.get('company_name', f"Asset {ticker}")
        sector = row.get('sector', 'Unknown')
        industry = row.get('industry', 'Unknown')
        
        cursor.execute("""
            INSERT INTO assets (ticker, company_name, sector, industry)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(ticker) DO UPDATE SET
                company_name=coalesce(excluded.company_name, assets.company_name),
                sector=coalesce(excluded.sector, assets.sector),
                industry=coalesce(excluded.industry, assets.industry)
        """, (ticker, company_name, sector, industry))
        inserted_assets += 1
        
        # 2. Handle transaction details
        tx_type = row.get('transaction_type', 'BUY').upper()
        if tx_type not in ('BUY', 'SELL'):
            tx_type = 'BUY'
            
        quantity_str = row.get('quantity', '0').replace(',', '')
        price_str = row.get('price_per_share', '0').replace('$', '').replace(',', '')
        fees_str = row.get('fees', '0').replace('$', '').replace(',', '')
        
        try:
            quantity = float(quantity_str)
            price = float(price_str)
            fees = float(fees_str)
        except ValueError:
            log_message(f"Warning: Skipping row for {ticker} due to numerical format errors.")
            continue
            
        if quantity <= 0:
            continue
            
        notes = row.get('notes', 'Auto-imported position holding')
        
        # Check if we should insert as transaction
        cursor.execute("""
            INSERT INTO transactions (portfolio_id, ticker, transaction_type, quantity, price_per_share, fees, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (DEFAULT_PORTFOLIO_ID, ticker, tx_type, quantity, price, fees, notes))
        inserted_txs += 1
        
        # 3. Handle live quotes if provided
        current_price_str = row.get('current_price')
        if current_price_str:
            try:
                current_price = float(current_price_str.replace('$', '').replace(',', ''))
                cursor.execute("""
                    INSERT INTO quotes (ticker, current_price, last_updated)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(ticker) DO UPDATE SET
                        current_price=excluded.current_price,
                        last_updated=CURRENT_TIMESTAMP
                """, (ticker, current_price))
                updated_quotes += 1
            except ValueError:
                pass
                
    conn.commit()
    return inserted_assets, inserted_txs, updated_quotes

def scan_and_ingest():
    # Setup connection
    if not os.path.exists(DB_NAME):
        log_message("Error: Database not found. Please run init_db.py first.")
        return
        
    conn = sqlite3.connect(DB_NAME)
    
    # Supported extensions
    extensions = ['.csv', '.json']
    script_files = ['init_db.py', 'ingest_holdings.py']
    
    files_to_process = []
    for f in os.listdir('.'):
        name, ext = os.path.splitext(f)
        if ext.lower() in extensions and f not in script_files:
            # Avoid processing schema file
            if f != 'schema.sql':
                files_to_process.append(f)
                
    if not files_to_process:
        log_message("No new holdings sheet (.csv or .json) detected in folder to import.")
        conn.close()
        return

    log_message(f"Detected {len(files_to_process)} file(s) for ingestion.")
    
    for f in files_to_process:
        log_message(f"Processing file: {f}")
        _, ext = os.path.splitext(f)
        
        if ext.lower() == '.csv':
            data = parse_csv(f)
        else:
            data = parse_json(f)
            
        if not data:
            log_message(f"Warning: File {f} was empty or failed to parse.")
            continue
            
        assets, txs, quotes = ingest_data(conn, data)
        log_message(f"Imported successfully from {f}: {assets} Assets, {txs} Transactions, {quotes} Quotes.")
        
        # Archive file to avoid repeated imports
        archive_dir = "archive"
        os.makedirs(archive_dir, exist_ok=True)
        archive_path = os.path.join(archive_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{f}")
        os.rename(f, archive_path)
        log_message(f"Archived file to: {archive_path}")
        
    # Re-run valuation summary
    print("\n" + "=" * 60)
    print("POP'S ALPHA FUND — UPDATED PORTFOLIO VALUATION")
    print("=" * 60)
    
    cursor = conn.cursor()
    query = """
        SELECT 
            t.ticker,
            SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity ELSE -t.quantity END) as total_shares,
            SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity * t.price_per_share + t.fees ELSE -t.quantity * t.price_per_share + t.fees END) / 
                SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity ELSE -t.quantity END) as avg_cost,
            coalesce(q.current_price, 0.0) as current_price,
            SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity ELSE -t.quantity END) * coalesce(q.current_price, 0.0) as market_value
        FROM transactions t
        LEFT JOIN quotes q ON t.ticker = q.ticker
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
    scan_and_ingest()
