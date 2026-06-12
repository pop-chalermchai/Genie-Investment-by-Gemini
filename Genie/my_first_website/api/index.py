from flask import Flask, jsonify, request
import sqlite3
import os
import urllib.request
import urllib.parse
import json

app = Flask(__name__)

# Resolve path to portfolio.db (at the root of my_first_website)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'portfolio.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/holdings', methods=['GET'])
def get_holdings():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = '''
            SELECT 
                a.ticker, a.company_name as companyName, a.sector, 
                p.name as portfolio, 
                t.currency, SUM(t.shares) as shares, 
                SUM(CASE WHEN t.type = 'BUY' THEN t.shares * t.price ELSE 0 END) / NULLIF(SUM(CASE WHEN t.type = 'BUY' THEN t.shares ELSE 0 END), 0) as avgCost
            FROM assets a
            JOIN portfolios p ON a.portfolio_id = p.id
            JOIN transactions t ON t.asset_id = a.id
            GROUP BY a.id, p.id
            HAVING SUM(t.shares) > 0
        '''
        cursor.execute(query)
        rows = cursor.fetchall()
        holdings = [dict(r) for r in rows]
        conn.close()
        return jsonify(holdings)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports', methods=['GET'])
def get_reports():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM research_reports')
        rows = cursor.fetchall()
        reports = {}
        for r in rows:
            reports[r['report_key']] = {
                "ticker": r['ticker'],
                "companyName": r['company_name'],
                "subtitle": r['subtitle'],
                "preparedBy": r['prepared_by'],
                "auditedBy": r['audited_by'],
                "rating": r['rating'],
                "isPositive": bool(r['is_positive']),
                "en_overview": r['en_overview'],
                "th_overview": r['th_overview'],
                "en_dcf": r['en_dcf'],
                "th_dcf": r['th_dcf']
            }
        conn.close()
        return jsonify(reports)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stock', methods=['GET'])
def get_stock():
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({"error": "Missing ticker parameter"}), 400
    
    ticker = ticker.upper()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if not data.get('chart', {}).get('result'):
                raise ValueError("No stock data found in Yahoo Finance response")
            
            meta = data['chart']['result'][0]['meta']
            stock_info = {
                "ticker": ticker,
                "price": meta.get("regularMarketPrice"),
                "previousClose": meta.get("previousClose") or meta.get("chartPreviousClose"),
                "currency": meta.get("currency"),
                "fiftyTwoWeekHigh": meta.get("fiftyTwoWeekHigh"),
                "fiftyTwoWeekLow": meta.get("fiftyTwoWeekLow"),
                "longName": meta.get("longName") or meta.get("shortName") or ticker,
                "volume": meta.get("regularMarketVolume"),
                "dayHigh": meta.get("regularMarketDayHigh"),
                "dayLow": meta.get("regularMarketDayLow")
            }
            return jsonify(stock_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolios', methods=['POST'])
def add_portfolio():
    try:
        data = request.get_json(force=True)
        portfolio_name = data.get('name')
        category_name = data.get('category', 'Stocks')
        
        if not portfolio_name:
            raise ValueError("Portfolio name is required")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get category id
        cursor.execute("SELECT id FROM categories WHERE name=?", (category_name,))
        cat_row = cursor.fetchone()
        if cat_row:
            cat_id = cat_row[0]
        else:
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
            cat_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO portfolios (name, category_id) VALUES (?, ?)", (portfolio_name, cat_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ingest', methods=['POST'])
def ingest_transaction():
    try:
        data = request.get_json(force=True)
        tx_type = data.get('type', 'BUY').upper()
        ticker = data.get('ticker')
        company_name = data.get('companyName')
        sector = data.get('sector')
        portfolio_name = data.get('portfolio')
        shares = float(data.get('shares', 0))
        price = float(data.get('avgCost', 0))
        currency = data.get('currency', 'USD')
        
        if not all([ticker, company_name, portfolio_name, shares > 0, price > 0]):
            raise ValueError("Missing required fields or invalid amounts")
            
        if tx_type == 'SELL':
            shares = -abs(shares)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM portfolios WHERE name=?", (portfolio_name,))
        p_row = cursor.fetchone()
        if not p_row:
            raise ValueError(f"Portfolio '{portfolio_name}' does not exist")
        p_id = p_row[0]
        
        cursor.execute("SELECT id FROM assets WHERE ticker=? AND portfolio_id=?", (ticker, p_id))
        a_row = cursor.fetchone()
        
        if a_row:
            asset_id = a_row[0]
        else:
            cursor.execute("INSERT INTO assets (ticker, company_name, sector, portfolio_id) VALUES (?, ?, ?, ?)",
                           (ticker, company_name, sector, p_id))
            asset_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO transactions (asset_id, type, shares, price, currency) VALUES (?, ?, ?, ?, ?)",
                       (asset_id, tx_type, shares, price, currency))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio', methods=['DELETE'])
def delete_portfolio():
    p_name = request.args.get('name')
    if not p_name:
        return jsonify({"error": "Portfolio name required"}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Find portfolio ID
        cursor.execute("SELECT id FROM portfolios WHERE name=?", (p_name,))
        p_row = cursor.fetchone()
        if not p_row:
            raise ValueError(f"Portfolio '{p_name}' not found")
        p_id = p_row[0]
        
        # Delete transactions related to assets in this portfolio
        cursor.execute("DELETE FROM transactions WHERE asset_id IN (SELECT id FROM assets WHERE portfolio_id=?)", (p_id,))
        
        # Delete assets in this portfolio
        cursor.execute("DELETE FROM assets WHERE portfolio_id=?", (p_id,))
        
        # Delete portfolio
        cursor.execute("DELETE FROM portfolios WHERE id=?", (p_id,))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
