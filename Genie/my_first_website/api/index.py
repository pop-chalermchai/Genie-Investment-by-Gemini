from flask import Flask, jsonify, request, send_from_directory
from datetime import datetime, timedelta
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

# Load .env for local development (Vercel injects env vars automatically)
_env_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip())

DATABASE_URL = os.environ.get('DATABASE_URL')
SEC_FACTSHEET_KEY = os.environ.get('SEC_FACTSHEET_KEY', 'eb52da4e4d2c4587a293bbbf6c4f00cb')
SEC_DAILY_INFO_KEY = os.environ.get('SEC_DAILY_INFO_KEY', '38a6644d289443f4803ceb41132c1c60')

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
                a.ticker, a.company_name as "companyName", p.name as portfolio, p.parent_id as "parentId",
                (SELECT name FROM portfolios WHERE id = p.parent_id) as "parentPortfolio"
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

@app.route('/api/init-data', methods=['GET'])
def get_init_data():
    try:
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Holdings
        holdings_query = '''
            SELECT 
                a.ticker, a.company_name as "companyName", a.sector, a.domain,
                p.name as portfolio, p.id as "portfolioId", p.parent_id as "parentId",
                (SELECT name FROM portfolios WHERE id = p.parent_id) as "parentPortfolio",
                t.currency, SUM(t.shares) as shares, 
                SUM(CASE WHEN t.type IN ('BUY', 'TRANSFER_IN') THEN t.shares * t.price ELSE 0 END) / 
                NULLIF(SUM(CASE WHEN t.type IN ('BUY', 'TRANSFER_IN') THEN t.shares ELSE 0 END), 0) as "avgCost"
            FROM assets a
            JOIN portfolios p ON a.portfolio_id = p.id
            JOIN transactions t ON t.asset_id = a.id
            GROUP BY a.id, p.id, t.currency
            HAVING SUM(t.shares) > 0
        '''
        execute_sql(cursor, is_postgres, holdings_query)
        holdings = fetch_all_as_dict(cursor, is_postgres)
        
        # 2. Reports
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
                "priceTarget": r.get('price_target'),
                "analysisPrice": r.get('analysis_price'),
                "en_overview": r['en_overview'],
                "th_overview": r['th_overview'],
                "en_dcf": r['en_dcf'],
                "th_dcf": r['th_dcf'],
                "sector": r.get('sector')
            }
            
        # 3. Portfolios
        portfolios_query = """
            SELECT 
                p.id, p.name, p.category_id as "categoryId", c.name as category, p.parent_id as "parentId",
                (SELECT name FROM portfolios WHERE id = p.parent_id) as "parentName"
            FROM portfolios p
            LEFT JOIN categories c ON p.category_id = c.id
        """
        execute_sql(cursor, is_postgres, portfolios_query)
        ports = fetch_all_as_dict(cursor, is_postgres)
        
        conn.close()
        return jsonify({
            "holdings": holdings,
            "reports": reports,
            "portfolios": ports
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/holdings', methods=['GET'])
def get_holdings():
    try:
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        query = '''
            SELECT 
                a.ticker, a.company_name as "companyName", a.sector, a.domain,
                p.name as portfolio, p.id as "portfolioId", p.parent_id as "parentId",
                (SELECT name FROM portfolios WHERE id = p.parent_id) as "parentPortfolio",
                t.currency, SUM(t.shares) as shares, 
                SUM(CASE WHEN t.type IN ('BUY', 'TRANSFER_IN') THEN t.shares * t.price ELSE 0 END) / 
                NULLIF(SUM(CASE WHEN t.type IN ('BUY', 'TRANSFER_IN') THEN t.shares ELSE 0 END), 0) as "avgCost"
            FROM assets a
            JOIN portfolios p ON a.portfolio_id = p.id
            JOIN transactions t ON t.asset_id = a.id
            GROUP BY a.id, p.id, t.currency
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
                "priceTarget": r.get('price_target'),
                "analysisPrice": r.get('analysis_price'),
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
        parent_id = data.get('parentId')
        if parent_id == '' or parent_id == 'null':
            parent_id = None

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
                execute_sql(cursor, is_postgres, "SELECT MAX(id) FROM categories")
                cat_id = cursor.fetchone()[0]
            else:
                cat_id = cursor.lastrowid

        # Check for duplicates
        execute_sql(cursor, is_postgres, "SELECT id FROM portfolios WHERE name=?", (portfolio_name,))
        if fetch_all_as_dict(cursor, is_postgres):
            raise ValueError(f"Portfolio name '{portfolio_name}' already exists. Please choose a different name.")

        execute_sql(cursor, is_postgres, "INSERT INTO portfolios (name, category_id, parent_id) VALUES (?, ?, ?)", (portfolio_name, cat_id, parent_id))

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

@app.route('/api/portfolio', methods=['PUT'])
def edit_portfolio():
    try:
        data = request.get_json(force=True)
        old_name = data.get('oldName')
        new_name = data.get('newName')
        parent_name = data.get('parentName')
        new_category = data.get('newCategory')
        if not old_name or not new_name:
            raise ValueError("oldName and newName are required")
            
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        
        # Get category id if newCategory is provided
        cat_id = None
        if new_category:
            execute_sql(cursor, is_postgres, "SELECT id FROM categories WHERE name=?", (new_category,))
            cat_rows = fetch_all_as_dict(cursor, is_postgres)
            if cat_rows:
                cat_id = cat_rows[0]['id']
            else:
                execute_sql(cursor, is_postgres, "INSERT INTO categories (name) VALUES (?)", (new_category,))
                if is_postgres:
                    execute_sql(cursor, is_postgres, "SELECT MAX(id) FROM categories")
                    cat_id = cursor.fetchone()[0]
                else:
                    cat_id = cursor.lastrowid
        
        if parent_name:
            # Find parent portfolio ID
            execute_sql(cursor, is_postgres, "SELECT id FROM portfolios WHERE name=? AND parent_id IS NULL", (parent_name,))
            rows = fetch_all_as_dict(cursor, is_postgres)
            if rows:
                p_id = rows[0]['id']
                if cat_id is not None:
                    execute_sql(cursor, is_postgres, "UPDATE portfolios SET name=?, category_id=? WHERE name=? AND parent_id=?", (new_name, cat_id, old_name, p_id))
                else:
                    execute_sql(cursor, is_postgres, "UPDATE portfolios SET name=? WHERE name=? AND parent_id=?", (new_name, old_name, p_id))
            else:
                raise ValueError("Parent portfolio not found")
        else:
            if cat_id is not None:
                execute_sql(cursor, is_postgres, "UPDATE portfolios SET name=?, category_id=? WHERE name=? AND parent_id IS NULL", (new_name, cat_id, old_name))
            else:
                execute_sql(cursor, is_postgres, "UPDATE portfolios SET name=? WHERE name=? AND parent_id IS NULL", (new_name, old_name))
                
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/asset-adjustment', methods=['PUT'])
def adjust_asset():
    try:
        data = request.get_json(force=True)
        ticker = data.get('ticker')
        portfolio_name = data.get('portfolio')
        new_shares = float(data.get('shares', 0))
        new_price = float(data.get('price', 0))
        currency = data.get('currency', 'USD')
        
        if not all([ticker, portfolio_name, new_shares >= 0, new_price >= 0]):
            raise ValueError("Missing or invalid fields")
            
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        
        execute_sql(cursor, is_postgres, "SELECT id FROM portfolios WHERE name=?", (portfolio_name,))
        p_rows = fetch_all_as_dict(cursor, is_postgres)
        if not p_rows:
            raise ValueError("Portfolio not found")
        p_id = p_rows[0]['id']
        
        execute_sql(cursor, is_postgres, "SELECT id FROM assets WHERE ticker=? AND portfolio_id=?", (ticker, p_id))
        a_rows = fetch_all_as_dict(cursor, is_postgres)
        if not a_rows:
            raise ValueError("Asset not found")
        asset_id = a_rows[0]['id']
        
        execute_sql(cursor, is_postgres, "DELETE FROM transactions WHERE asset_id=?", (asset_id,))
        if new_shares > 0:
            execute_sql(cursor, is_postgres, "INSERT INTO transactions (asset_id, type, shares, price, currency) VALUES (?, 'BUY', ?, ?, ?)", (asset_id, new_shares, new_price, currency))
            
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
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()

        # Find portfolio ID
        execute_sql(cursor, is_postgres, "SELECT id FROM portfolios WHERE name=?", (p_name,))
        p_rows = fetch_all_as_dict(cursor, is_postgres)
        if not p_rows:
            raise ValueError(f"Portfolio '{p_name}' not found")
        p_id = p_rows[0]['id']

        # Find all sub-portfolios under this parent
        execute_sql(cursor, is_postgres, "SELECT id FROM portfolios WHERE parent_id=?", (p_id,))
        sub_rows = fetch_all_as_dict(cursor, is_postgres)
        sub_ids = [r['id'] for r in sub_rows]

        # Delete children first, then parent (Postgres FK constraint requires this order)
        all_ids = sub_ids + [p_id]
        for curr_id in all_ids:
            execute_sql(cursor, is_postgres, "DELETE FROM transactions WHERE asset_id IN (SELECT id FROM assets WHERE portfolio_id=?)", (curr_id,))
            execute_sql(cursor, is_postgres, "DELETE FROM assets WHERE portfolio_id=?", (curr_id,))
            execute_sql(cursor, is_postgres, "DELETE FROM portfolios WHERE id=?", (curr_id,))

        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/research-report', methods=['POST'])
def add_research_report():
    try:
        data = request.get_json(force=True)
        report_key = data.get('report_key', '').strip()
        ticker = data.get('ticker', '').strip().upper()
        company_name = data.get('company_name', '').strip()
        subtitle = data.get('subtitle', '')
        prepared_by = data.get('prepared_by', '')
        audited_by = data.get('audited_by', '')
        rating = data.get('rating', '')
        is_positive = bool(data.get('is_positive'))
        price_target = data.get('price_target')
        analysis_price = data.get('analysis_price')
        sector = data.get('sector', 'Other Sectors')
        en_overview = data.get('en_overview', '')
        th_overview = data.get('th_overview', '')
        en_dcf = data.get('en_dcf', '')
        th_dcf = data.get('th_dcf', '')
        
        if not report_key or not ticker or not company_name:
            raise ValueError("report_key, ticker, and company_name are required")
            
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            INSERT INTO research_reports (
                report_key, ticker, company_name, subtitle, prepared_by, audited_by, 
                rating, is_positive, price_target, analysis_price, sector, 
                en_overview, th_overview, en_dcf, th_dcf
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        execute_sql(cursor, is_postgres, query, (
            report_key, ticker, company_name, subtitle, prepared_by, audited_by, 
            rating, 1 if is_positive else 0, price_target, analysis_price, sector, 
            en_overview, th_overview, en_dcf, th_dcf
        ))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/research-report', methods=['PUT'])
def edit_research_report():
    report_key = request.args.get('key')
    if not report_key:
        return jsonify({"error": "report_key required"}), 400
        
    try:
        data = request.get_json(force=True)
        ticker = data.get('ticker', '').strip().upper()
        company_name = data.get('company_name', '').strip()
        subtitle = data.get('subtitle', '')
        prepared_by = data.get('prepared_by', '')
        audited_by = data.get('audited_by', '')
        rating = data.get('rating', '')
        is_positive = bool(data.get('is_positive'))
        price_target = data.get('price_target')
        analysis_price = data.get('analysis_price')
        sector = data.get('sector', 'Other Sectors')
        en_overview = data.get('en_overview', '')
        th_overview = data.get('th_overview', '')
        en_dcf = data.get('en_dcf', '')
        th_dcf = data.get('th_dcf', '')
        
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            UPDATE research_reports 
            SET ticker=?, company_name=?, subtitle=?, prepared_by=?, audited_by=?, 
                rating=?, is_positive=?, price_target=?, analysis_price=?, sector=?, 
                en_overview=?, th_overview=?, en_dcf=?, th_dcf=?
            WHERE report_key=?
        '''
        execute_sql(cursor, is_postgres, query, (
            ticker, company_name, subtitle, prepared_by, audited_by, 
            rating, 1 if is_positive else 0, price_target, analysis_price, sector, 
            en_overview, th_overview, en_dcf, th_dcf, report_key
        ))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/research-report', methods=['DELETE'])
def delete_research_report():
    report_key = request.args.get('key')
    if not report_key:
        return jsonify({"error": "report_key required"}), 400
        
    try:
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        
        query = "DELETE FROM research_reports WHERE report_key=?"
        execute_sql(cursor, is_postgres, query, (report_key,))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/portfolios', methods=['GET'])
def get_portfolios():
    try:
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        query = """
            SELECT 
                MIN(p.id) as id, p.name, p.category_id as "categoryId", c.name as category, p.parent_id as "parentId",
                (SELECT name FROM portfolios WHERE id = p.parent_id) as "parentName"
            FROM portfolios p
            LEFT JOIN categories c ON p.category_id = c.id
            GROUP BY p.name, p.category_id, c.name, p.parent_id
        """
        execute_sql(cursor, is_postgres, query)
        ports = fetch_all_as_dict(cursor, is_postgres)
        conn.close()
        return jsonify(ports)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/transfer', methods=['POST'])
def transfer_stock():
    try:
        data = request.get_json(force=True)
        source_portfolio_id = data.get('sourcePortfolioId')
        dest_portfolio_id = data.get('destPortfolioId')
        ticker = data.get('ticker', '').upper().strip()
        shares = float(data.get('shares', 0))
        price = float(data.get('price', 0))
        date = data.get('date')
        
        if not all([source_portfolio_id, dest_portfolio_id, ticker, shares > 0, price >= 0]):
            raise ValueError("Missing required fields or invalid amounts")
            
        if int(source_portfolio_id) == int(dest_portfolio_id):
            raise ValueError("Source and destination portfolios must be different")
            
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        
        # Check source and destination portfolios
        execute_sql(cursor, is_postgres, "SELECT id FROM portfolios WHERE id=?", (source_portfolio_id,))
        if not fetch_all_as_dict(cursor, is_postgres):
            raise ValueError(f"Source portfolio ID {source_portfolio_id} does not exist")
            
        execute_sql(cursor, is_postgres, "SELECT id FROM portfolios WHERE id=?", (dest_portfolio_id,))
        if not fetch_all_as_dict(cursor, is_postgres):
            raise ValueError(f"Destination portfolio ID {dest_portfolio_id} does not exist")
            
        # Check if asset exists in source
        execute_sql(cursor, is_postgres, "SELECT id, company_name, sector FROM assets WHERE ticker=? AND portfolio_id=?", (ticker, source_portfolio_id))
        src_rows = fetch_all_as_dict(cursor, is_postgres)
        if not src_rows:
            raise ValueError(f"Ticker {ticker} not found in source portfolio")
        src_asset_id = src_rows[0]['id']
        company_name = src_rows[0]['company_name']
        sector = src_rows[0]['sector']
        
        # Calculate available shares
        execute_sql(cursor, is_postgres, "SELECT SUM(shares) as total FROM transactions WHERE asset_id=?", (src_asset_id,))
        avail_row = fetch_all_as_dict(cursor, is_postgres)
        avail_shares = float(avail_row[0]['total'] or 0) if avail_row else 0
        
        if avail_shares < shares - 1e-8:
            raise ValueError(f"Insufficient shares of {ticker} in source portfolio. Available: {avail_shares}, requested: {shares}")
            
        # Get or create dest asset
        execute_sql(cursor, is_postgres, "SELECT id FROM assets WHERE ticker=? AND portfolio_id=?", (ticker, dest_portfolio_id))
        dest_rows = fetch_all_as_dict(cursor, is_postgres)
        if dest_rows:
            dest_asset_id = dest_rows[0]['id']
        else:
            execute_sql(cursor, is_postgres, "INSERT INTO assets (ticker, company_name, sector, portfolio_id) VALUES (?, ?, ?, ?)", (ticker, company_name, sector, dest_portfolio_id))
            if is_postgres:
                execute_sql(cursor, is_postgres, "SELECT MAX(id) as id FROM assets")
                dest_asset_id = fetch_all_as_dict(cursor, is_postgres)[0]['id']
            else:
                dest_asset_id = cursor.lastrowid
                
        # Get currency
        execute_sql(cursor, is_postgres, "SELECT currency FROM transactions WHERE asset_id=? LIMIT 1", (src_asset_id,))
        curr_row = fetch_all_as_dict(cursor, is_postgres)
        currency = curr_row[0]['currency'] if curr_row else 'USD'
        
        # Insert transactions
        if date:
            execute_sql(cursor, is_postgres, "INSERT INTO transactions (asset_id, type, shares, price, currency, transaction_date) VALUES (?, 'TRANSFER_OUT', ?, ?, ?, ?)", (src_asset_id, -shares, price, currency, date))
            execute_sql(cursor, is_postgres, "INSERT INTO transactions (asset_id, type, shares, price, currency, transaction_date) VALUES (?, 'TRANSFER_IN', ?, ?, ?, ?)", (dest_asset_id, shares, price, currency, date))
        else:
            execute_sql(cursor, is_postgres, "INSERT INTO transactions (asset_id, type, shares, price, currency) VALUES (?, 'TRANSFER_OUT', ?, ?, ?)", (src_asset_id, -shares, price, currency))
            execute_sql(cursor, is_postgres, "INSERT INTO transactions (asset_id, type, shares, price, currency) VALUES (?, 'TRANSFER_IN', ?, ?, ?)", (dest_asset_id, shares, price, currency))
            
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/transaction', methods=['PUT'])
def edit_transaction():
    tx_id = request.args.get('id')
    if not tx_id:
        return jsonify({"error": "Transaction id required"}), 400
        
    try:
        data = request.get_json(force=True)
        tx_type = data.get('type')
        shares = float(data.get('shares', 0))
        price = float(data.get('price', 0))
        currency = data.get('currency', 'USD')
        tx_date = data.get('transactionDate')
        
        if not tx_type or shares == 0 or price <= 0:
            raise ValueError("Missing required fields")
            
        if tx_type in ('SELL', 'TRANSFER_OUT'):
            shares = -abs(shares)
        else:
            shares = abs(shares)
            
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        
        if tx_date:
            execute_sql(cursor, is_postgres, "UPDATE transactions SET type=?, shares=?, price=?, currency=?, transaction_date=? WHERE id=?", (tx_type, shares, price, currency, tx_date, tx_id))
        else:
            execute_sql(cursor, is_postgres, "UPDATE transactions SET type=?, shares=?, price=?, currency=? WHERE id=?", (tx_type, shares, price, currency, tx_id))
            
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/transaction', methods=['DELETE'])
def delete_transaction():
    tx_id = request.args.get('id')
    if not tx_id:
        return jsonify({"error": "Transaction id required"}), 400
        
    try:
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        execute_sql(cursor, is_postgres, "DELETE FROM transactions WHERE id=?", (tx_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        execute_sql(cursor, is_postgres, "SELECT id, name, description FROM categories ORDER BY name")
        rows = fetch_all_as_dict(cursor, is_postgres)
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/categories', methods=['POST'])
def add_category():
    try:
        data = request.get_json(force=True)
        cat_name = data.get('name')
        description = data.get('description', '')
        if not cat_name:
            raise ValueError("Category name is required")
            
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        
        # Check duplicate
        execute_sql(cursor, is_postgres, "SELECT id FROM categories WHERE name=?", (cat_name,))
        if fetch_all_as_dict(cursor, is_postgres):
            raise ValueError(f"Category '{cat_name}' already exists.")
            
        execute_sql(cursor, is_postgres, "INSERT INTO categories (name, description) VALUES (?, ?)", (cat_name, description))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/categories', methods=['PUT'])
def edit_category():
    try:
        data = request.get_json(force=True)
        cat_id = data.get('id')
        new_name = data.get('name')
        description = data.get('description', '')
        if not cat_id or not new_name:
            raise ValueError("id and name required")
            
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        execute_sql(cursor, is_postgres, "UPDATE categories SET name = ?, description = ? WHERE id = ?", (new_name, description, cat_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/categories', methods=['DELETE'])
def delete_category():
    try:
        cat_id = request.args.get('id')
        if not cat_id:
            raise ValueError("Category id required")

        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()

        # Update referencing portfolios
        execute_sql(cursor, is_postgres, "UPDATE portfolios SET category_id = NULL WHERE category_id = ?", (cat_id,))
        # Delete category
        execute_sql(cursor, is_postgres, "DELETE FROM categories WHERE id = ?", (cat_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/portfolios/reorder', methods=['POST'])
def reorder_portfolios():
    try:
        items = request.get_json()
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        for item in items:
            execute_sql(cursor, is_postgres, "UPDATE portfolios SET sort_order = ? WHERE id = ?", (item['sortOrder'], item['id']))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/thai-fund', methods=['GET'])
def get_thai_fund():
    code = request.args.get('code', '').upper().strip()
    if not code:
        return jsonify({"error": "Missing code parameter"}), 400
    try:
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        execute_sql(cursor, is_postgres, "SELECT * FROM thai_funds WHERE UPPER(proj_abbr_name) = ?", (code,))
        rows = fetch_all_as_dict(cursor, is_postgres)
        conn.close()
        if not rows:
            return jsonify({"error": f"Fund '{code}' not found. Try syncing fund list first via POST /api/thai-fund/sync"}), 404
        fund = rows[0]
        proj_id = fund['proj_id']
        nav = None
        nav_date = None
        for i in range(1, 8):
            date_str = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            try:
                nav_url = f'https://api.sec.or.th/FundDailyInfo/{proj_id}/dailynav/{date_str}'
                req = urllib.request.Request(nav_url, headers={'Ocp-Apim-Subscription-Key': SEC_DAILY_INFO_KEY})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode())
                        if data and len(data) > 0:
                            nav = data[0]['last_val']
                            nav_date = date_str
                            break
            except Exception:
                continue
        return jsonify({
            'proj_abbr_name': fund['proj_abbr_name'],
            'proj_name_th': fund.get('proj_name_th'),
            'proj_name_en': fund.get('proj_name_en'),
            'amc_name_en': fund.get('amc_name_en'),
            'nav': nav,
            'nav_date': nav_date,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/thai-fund/sync', methods=['POST'])
def sync_thai_funds():
    try:
        conn, is_postgres = get_db_connection()
        cursor = conn.cursor()
        # Ensure thai_funds table exists
        if is_postgres:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS thai_funds (
                    proj_id TEXT PRIMARY KEY,
                    proj_abbr_name TEXT,
                    proj_name_th TEXT,
                    proj_name_en TEXT,
                    fund_status TEXT,
                    amc_name_en TEXT,
                    unique_id TEXT,
                    last_synced TIMESTAMP
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS thai_funds (
                    proj_id TEXT PRIMARY KEY,
                    proj_abbr_name TEXT,
                    proj_name_th TEXT,
                    proj_name_en TEXT,
                    fund_status TEXT,
                    amc_name_en TEXT,
                    unique_id TEXT,
                    last_synced TIMESTAMP
                )
            """)
        conn.commit()

        amc_req = urllib.request.Request(
            'https://api.sec.or.th/FundFactsheet/fund/amc',
            headers={'Ocp-Apim-Subscription-Key': SEC_FACTSHEET_KEY}
        )
        with urllib.request.urlopen(amc_req, timeout=10) as resp:
            amcs = json.loads(resp.read().decode())

        total = 0
        for amc in amcs:
            unique_id = amc['unique_id']
            amc_name = amc.get('name_en', '')
            try:
                fund_req = urllib.request.Request(
                    f'https://api.sec.or.th/FundFactsheet/fund/amc/{unique_id}',
                    headers={'Ocp-Apim-Subscription-Key': SEC_FACTSHEET_KEY}
                )
                with urllib.request.urlopen(fund_req, timeout=10) as resp:
                    funds = json.loads(resp.read().decode())
                for f in funds:
                    execute_sql(cursor, is_postgres, """
                        INSERT INTO thai_funds (proj_id, proj_abbr_name, proj_name_th, proj_name_en, fund_status, amc_name_en, unique_id, last_synced)
                        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(proj_id) DO UPDATE SET
                            proj_abbr_name=EXCLUDED.proj_abbr_name,
                            proj_name_th=EXCLUDED.proj_name_th,
                            proj_name_en=EXCLUDED.proj_name_en,
                            fund_status=EXCLUDED.fund_status,
                            amc_name_en=EXCLUDED.amc_name_en,
                            last_synced=CURRENT_TIMESTAMP
                    """, (f.get('proj_id'), f.get('proj_abbr_name'), f.get('proj_name_th'),
                          f.get('proj_name_en'), f.get('fund_status'), amc_name, unique_id))
                    total += 1
            except Exception:
                continue
        conn.commit()
        conn.close()
        return jsonify({"synced": total, "amcs": len(amcs)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Static file serving (local dev only) ──────────────────────────────────────
@app.route('/')
@app.route('/dashboard')
@app.route('/team')
@app.route('/research')
@app.route('/transactions')
def serve_index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(BASE_DIR, filename)


if __name__ == '__main__':
    print(f"Starting Flask dev server on http://127.0.0.1:8000")
    print(f"DB: {'Supabase' if DATABASE_URL else 'Local SQLite'}")
    app.run(host='127.0.0.1', port=8000, debug=True)
