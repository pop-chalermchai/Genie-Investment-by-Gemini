from flask import Flask, jsonify, request
import sqlite3
import os
import urllib.request
import urllib.parse
import json
import ssl
import pg8000

app = Flask(__name__)

# Config
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'portfolio.db')
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    """
    Returns (conn, is_postgres)
    """
    if DATABASE_URL:
        # Connect to Supabase / Postgres
        db_url = DATABASE_URL
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        url = urllib.parse.urlparse(db_url)
        username = url.username
        password = url.password
        database = url.path[1:]
        hostname = url.hostname
        port = url.port or 5432
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        conn = pg8000.connect(
            user=username,
            password=password,
            host=hostname,
            port=port,
            database=database,
            ssl_context=ssl_context
        )
        return conn, True
    else:
        # Fallback to local SQLite
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn, False

def execute_sql(cursor, is_postgres, query, params=None):
    if params is None:
        params = ()
    if is_postgres:
        # Convert SQLite ? to Postgres %s placeholders
        query = query.replace('?', '%s')
    cursor.execute(query, params)

def fetch_all_as_dict(cursor, is_postgres):
    if is_postgres:
        if not cursor.description:
            return []
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    else:
        return [dict(r) for r in cursor.fetchall()]

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    try:
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        query = '''
            SELECT 
                t.id, t.type, t.shares, t.price, t.currency, t.transaction_date as "transactionDate",
                a.ticker, a.company_name as "companyName", p.name as portfolio
            FROM transactions t
            JOIN assets a ON t.asset_id = a.id
            JOIN portfolios p ON a.portfolio_id = p.id
            ORDER BY t.transaction_date DESC
        '''
        execute_sql(cursor, is_postgres, query)
        transactions = fetch_all_as_dict(cursor, is_postgres)
        conn.close()
        return jsonify(transactions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stock/chart', methods=['GET'])
def get_stock_chart():
    ticker = request.args.get('ticker')
    chart_range = request.args.get('range', '1mo')
    interval = '1d'
    if chart_range == '1d':
        interval = '5m'
    
    if not ticker:
        return jsonify({"error": "Missing ticker parameter"}), 400
        
    ticker = ticker.upper()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={chart_range}&interval={interval}"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if not data.get('chart', {}).get('result'):
                raise ValueError("No stock chart data found in Yahoo Finance response")
            
            result = data['chart']['result'][0]
            timestamps = result.get('timestamp', [])
            quote = result.get('indicators', {}).get('quote', [{}])[0]
            
            chart_data = {
                "ticker": ticker,
                "timestamps": timestamps,
                "close": quote.get('close', []),
                "open": quote.get('open', []),
                "high": quote.get('high', []),
                "low": quote.get('low', []),
                "volume": quote.get('volume', [])
            }
            return jsonify(chart_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/holdings', methods=['GET'])
def get_holdings():
    try:
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        # Cleaned up GROUP BY to satisfy Postgres strict requirements
        query = '''
            SELECT 
                a.ticker, a.company_name as "companyName", a.sector, 
                p.name as portfolio, 
                t.currency, SUM(t.shares) as shares, 
                SUM(CASE WHEN t.type = 'BUY' THEN t.shares * t.price ELSE 0 END) / NULLIF(SUM(CASE WHEN t.type = 'BUY' THEN t.shares ELSE 0 END), 0) as "avgCost"
            FROM assets a
            JOIN portfolios p ON a.portfolio_id = p.id
            JOIN transactions t ON t.asset_id = a.id
            GROUP BY a.ticker, a.company_name, a.sector, p.name, t.currency
            HAVING SUM(t.shares) > 0
        '''
        execute_sql(cursor, is_postgres, query)
        holdings = fetch_all_as_dict(cursor, is_postgres)
        conn.close()
        return jsonify(holdings)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports', methods=['GET'])
def get_reports():
    try:
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        execute_sql(cursor, is_postgres, 'SELECT * FROM research_reports')
        rows = fetch_all_as_dict(cursor, is_postgres)
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
                "th_dcf": r['th_dcf'],
                "sector": r.get('sector')
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
        
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        
        # Get category id
        execute_sql(cursor, is_postgres, "SELECT id FROM categories WHERE name=?", (category_name,))
        cat_rows = fetch_all_as_dict(cursor, is_postgres)
        
        if cat_rows:
            cat_id = cat_rows[0]['id']
        else:
            execute_sql(cursor, is_postgres, "INSERT INTO categories (name) VALUES (?)", (category_name,))
            if is_postgres:
                # In pg8000, we retrieve last inserted ID differently if needed,
                # but standard returning or querying max ID can be done, or we can use cursor.lastrowid fallback.
                # Actually, pg8000 doesn't populate cursor.lastrowid by default.
                # So we can use INSERT INTO ... RETURNING id
                execute_sql(cursor, is_postgres, "SELECT MAX(id) FROM categories")
                cat_id = cursor.fetchone()[0]
            else:
                cat_id = cursor.lastrowid
        
        execute_sql(cursor, is_postgres, "INSERT INTO portfolios (name, category_id) VALUES (?, ?)", (portfolio_name, cat_id))
        
        if is_postgres:
            conn.commit()
        else:
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
        tx_date = data.get('date')
        
        if not all([ticker, company_name, portfolio_name, shares > 0, price > 0]):
            raise ValueError("Missing required fields or invalid amounts")
            
        if tx_type == 'SELL':
            shares = -abs(shares)
        
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        
        execute_sql(cursor, is_postgres, "SELECT id FROM portfolios WHERE name=?", (portfolio_name,))
        p_rows = fetch_all_as_dict(cursor, is_postgres)
        if not p_rows:
            raise ValueError(f"Portfolio '{portfolio_name}' does not exist")
        p_id = p_rows[0]['id']
        
        execute_sql(cursor, is_postgres, "SELECT id FROM assets WHERE ticker=? AND portfolio_id=?", (ticker, p_id))
        a_rows = fetch_all_as_dict(cursor, is_postgres)
        
        if a_rows:
            asset_id = a_rows[0]['id']
        else:
            execute_sql(cursor, is_postgres, "INSERT INTO assets (ticker, company_name, sector, portfolio_id) VALUES (?, ?, ?, ?)",
                           (ticker, company_name, sector, p_id))
            if is_postgres:
                execute_sql(cursor, is_postgres, "SELECT MAX(id) FROM assets")
                asset_id = cursor.fetchone()[0]
            else:
                asset_id = cursor.lastrowid
        
        if tx_date:
            execute_sql(cursor, is_postgres, "INSERT INTO transactions (asset_id, type, shares, price, currency, transaction_date) VALUES (?, ?, ?, ?, ?, ?)",
                           (asset_id, tx_type, shares, price, currency, tx_date))
        else:
            execute_sql(cursor, is_postgres, "INSERT INTO transactions (asset_id, type, shares, price, currency) VALUES (?, ?, ?, ?, ?)",
                           (asset_id, tx_type, shares, price, currency))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/bulk-ingest', methods=['POST'])
def bulk_ingest():
    try:
        data = request.get_json(force=True)
        tx_list = data.get('transactions', [])
        if not tx_list:
            raise ValueError("No transactions provided")
            
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        
        for tx in tx_list:
            tx_type = tx.get('type', 'BUY').upper()
            ticker = tx.get('ticker')
            company_name = tx.get('companyName')
            sector = tx.get('sector', 'Technology')
            portfolio_name = tx.get('portfolio')
            shares = float(tx.get('shares', 0))
            price = float(tx.get('avgCost', 0))
            currency = tx.get('currency', 'USD')
            tx_date = tx.get('date')
            
            if not all([ticker, company_name, portfolio_name, shares > 0, price > 0]):
                raise ValueError(f"Missing required fields or invalid amounts for ticker {ticker}")
                
            if tx_type == 'SELL':
                shares = -abs(shares)
                
            execute_sql(cursor, is_postgres, "SELECT id FROM portfolios WHERE name=?", (portfolio_name,))
            p_rows = fetch_all_as_dict(cursor, is_postgres)
            if not p_rows:
                raise ValueError(f"Portfolio '{portfolio_name}' does not exist")
            p_id = p_rows[0]['id']
            
            execute_sql(cursor, is_postgres, "SELECT id FROM assets WHERE ticker=? AND portfolio_id=?", (ticker, p_id))
            a_rows = fetch_all_as_dict(cursor, is_postgres)
            
            if a_rows:
                asset_id = a_rows[0]['id']
            else:
                execute_sql(cursor, is_postgres, "INSERT INTO assets (ticker, company_name, sector, portfolio_id) VALUES (?, ?, ?, ?)",
                               (ticker, company_name, sector, p_id))
                if is_postgres:
                    execute_sql(cursor, is_postgres, "SELECT MAX(id) FROM assets")
                    asset_id = cursor.fetchone()[0]
                else:
                    asset_id = cursor.lastrowid
            
            if tx_date:
                execute_sql(cursor, is_postgres, "INSERT INTO transactions (asset_id, type, shares, price, currency, transaction_date) VALUES (?, ?, ?, ?, ?, ?)",
                               (asset_id, tx_type, shares, price, currency, tx_date))
            else:
                execute_sql(cursor, is_postgres, "INSERT INTO transactions (asset_id, type, shares, price, currency) VALUES (?, ?, ?, ?, ?)",
                               (asset_id, tx_type, shares, price, currency))
                               
        conn.commit()
        conn.close()
        return jsonify({"success": True, "count": len(tx_list)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio', methods=['DELETE'])
def delete_portfolio():
    p_name = request.args.get('name')
    if not p_name:
        return jsonify({"error": "Portfolio name required"}), 400
        
    try:
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        
        # Find portfolio ID
        execute_sql(cursor, is_postgres, "SELECT id FROM portfolios WHERE name=?", (p_name,))
        p_rows = fetch_all_as_dict(cursor, is_postgres)
        if not p_rows:
            raise ValueError(f"Portfolio '{p_name}' not found")
        p_id = p_rows[0]['id']
        
        # Delete transactions related to assets in this portfolio
        execute_sql(cursor, is_postgres, "DELETE FROM transactions WHERE asset_id IN (SELECT id FROM assets WHERE portfolio_id=?)", (p_id,))
        
        # Delete assets in this portfolio
        execute_sql(cursor, is_postgres, "DELETE FROM assets WHERE portfolio_id=?", (p_id,))
        
        # Delete portfolio
        execute_sql(cursor, is_postgres, "DELETE FROM portfolios WHERE id=?", (p_id,))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
