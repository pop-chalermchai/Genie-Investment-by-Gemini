import http.server
import urllib.request
import json
import urllib.parse
import os
import sqlite3

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Initialize SimpleHTTPRequestHandler to serve from DIRECTORY
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == '/api/holdings':
            db_path = os.path.join(DIRECTORY, 'portfolio.db')
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Fetch holdings joined across tables with parent portfolio info
                query = '''
                    SELECT 
                        a.ticker, a.company_name as companyName, a.sector, a.domain,
                        p.name as portfolio, p.id as portfolioId, p.parent_id as parentId,
                        (SELECT name FROM portfolios WHERE id = p.parent_id) as parentPortfolio,
                        t.currency, SUM(t.shares) as shares, 
                        SUM(CASE WHEN t.type IN ('BUY', 'TRANSFER_IN') THEN t.shares * t.price ELSE 0 END) / 
                        NULLIF(SUM(CASE WHEN t.type IN ('BUY', 'TRANSFER_IN') THEN t.shares ELSE 0 END), 0) as avgCost
                    FROM assets a
                    JOIN portfolios p ON a.portfolio_id = p.id
                    JOIN transactions t ON t.asset_id = a.id
                    GROUP BY a.id, p.id
                    HAVING SUM(t.shares) > 0
                '''
                cursor.execute(query)
                rows = cursor.fetchall()
                
                holdings = []
                for r in rows:
                    holdings.append(dict(r))
                    
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(holdings).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        elif parsed_url.path == '/api/init-data':
            db_path = os.path.join(DIRECTORY, 'portfolio.db')
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 1. Holdings
                holdings_query = '''
                    SELECT 
                        a.ticker, a.company_name as companyName, a.sector, a.domain,
                        p.name as portfolio, p.id as portfolioId, p.parent_id as parentId,
                        (SELECT name FROM portfolios WHERE id = p.parent_id) as parentPortfolio,
                        t.currency, SUM(t.shares) as shares, 
                        SUM(CASE WHEN t.type IN ('BUY', 'TRANSFER_IN') THEN t.shares * t.price ELSE 0 END) / 
                        NULLIF(SUM(CASE WHEN t.type IN ('BUY', 'TRANSFER_IN') THEN t.shares ELSE 0 END), 0) as avgCost
                    FROM assets a
                    JOIN portfolios p ON a.portfolio_id = p.id
                    JOIN transactions t ON t.asset_id = a.id
                    GROUP BY a.id, p.id
                    HAVING SUM(t.shares) > 0
                '''
                cursor.execute(holdings_query)
                holdings = [dict(r) for r in cursor.fetchall()]
                
                # 2. Reports
                cursor.execute('SELECT * FROM research_reports')
                reports_rows = cursor.fetchall()
                reports = {}
                for r in reports_rows:
                    reports[r['report_key']] = {
                        "ticker": r['ticker'],
                        "companyName": r['company_name'],
                        "subtitle": r['subtitle'],
                        "preparedBy": r['prepared_by'],
                        "auditedBy": r['audited_by'],
                        "rating": r['rating'],
                        "isPositive": bool(r['is_positive']),
                        "priceTarget": r['price_target'],
                        "analysisPrice": r['analysis_price'],
                        "en_overview": r['en_overview'],
                        "th_overview": r['th_overview'],
                        "en_dcf": r['en_dcf'],
                        "th_dcf": r['th_dcf'],
                        "sector": r['sector'] if 'sector' in r.keys() else 'Other Sectors'
                    }
                    
                # 3. Portfolios
                portfolios_query = """
                    SELECT 
                        p.id, p.name, p.category_id as categoryId, c.name as category, p.parent_id as parentId,
                        (SELECT name FROM portfolios WHERE id = p.parent_id) as parentName
                    FROM portfolios p
                    LEFT JOIN categories c ON p.category_id = c.id
                """
                cursor.execute(portfolios_query)
                ports = [dict(r) for r in cursor.fetchall()]
                
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "holdings": holdings,
                    "reports": reports,
                    "portfolios": ports
                }).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        elif parsed_url.path == '/api/transactions':
            db_path = os.path.join(DIRECTORY, 'portfolio.db')
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT 
                        t.id, t.type, t.shares, t.price, t.currency, t.transaction_date as transactionDate,
                        a.ticker, a.company_name as companyName, p.name as portfolio, p.parent_id as parentId,
                        (SELECT name FROM portfolios WHERE id = p.parent_id) as parentPortfolio
                    FROM transactions t
                    JOIN assets a ON t.asset_id = a.id
                    JOIN portfolios p ON a.portfolio_id = p.id
                    ORDER BY t.transaction_date DESC
                '''
                cursor.execute(query)
                rows = cursor.fetchall()
                txs = [dict(r) for r in rows]
                conn.close()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(txs).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        elif parsed_url.path == '/api/stock/chart':
            query_params = urllib.parse.parse_qs(parsed_url.query)
            ticker = query_params.get('ticker', [None])[0]
            chart_range = query_params.get('range', ['1mo'])[0]
            
            if not ticker:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing ticker parameter"}).encode())
                return
                
            ticker = ticker.upper()
            interval = '1d'
            if chart_range == '1d':
                interval = '5m'
                
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
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(chart_data).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        elif parsed_url.path == '/api/reports':
            db_path = os.path.join(DIRECTORY, 'portfolio.db')
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
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
                        "priceTarget": r['price_target'],
                        "analysisPrice": r['analysis_price'],
                        "en_overview": r['en_overview'],
                        "th_overview": r['th_overview'],
                        "en_dcf": r['en_dcf'],
                        "th_dcf": r['th_dcf'],
                        "sector": r['sector']
                    }
                conn.close()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(reports).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        elif parsed_url.path == '/api/portfolios':
            db_path = os.path.join(DIRECTORY, 'portfolio.db')
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # Fetch all portfolios, left joining categories and sub-querying parent portfolio names
                query = '''
                    SELECT 
                        MIN(p.id) as id, p.name, p.category_id as categoryId, c.name as category, p.parent_id as parentId,
                        (SELECT name FROM portfolios WHERE id = p.parent_id) as parentName
                    FROM portfolios p
                    LEFT JOIN categories c ON p.category_id = c.id
                    GROUP BY p.name, p.category_id, c.name, p.parent_id
                '''
                cursor.execute(query)
                rows = cursor.fetchall()
                ports = [dict(r) for r in rows]
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(ports).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        elif parsed_url.path == '/api/stock':
            # Handle API stock request
            query_params = urllib.parse.parse_qs(parsed_url.query)
            ticker = query_params.get('ticker', [None])[0]
            
            if not ticker:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing ticker parameter"}).encode())
                return

            # Fetch data from Yahoo Finance
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
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(stock_info).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            # For Path Routing support:
            # If the path is one of our frontend routes, serve index.html
            clean_path = parsed_url.path.strip('/')
            if clean_path in ('', 'dashboard', 'team', 'research', 'transactions'):
                self.path = '/index.html'
            # Delegate to SimpleHTTPRequestHandler to serve static files
            super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == '/api/portfolios':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                portfolio_name = data.get('name')
                category_name = data.get('category', 'Stocks')
                parent_id = data.get('parentId')
                if parent_id == '': parent_id = None
                
                if not portfolio_name:
                    raise ValueError("Portfolio name is required")
                
                db_path = os.path.join(DIRECTORY, 'portfolio.db')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get category id
                cursor.execute("SELECT id FROM categories WHERE name=?", (category_name,))
                cat_row = cursor.fetchone()
                if cat_row:
                    cat_id = cat_row[0]
                else:
                    cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
                    cat_id = cursor.lastrowid
                
                cursor.execute("SELECT id FROM portfolios WHERE name=?", (portfolio_name,))
                if cursor.fetchone():
                    raise ValueError(f"Portfolio name '{portfolio_name}' already exists. Please choose a different name.")
                
                cursor.execute("INSERT INTO portfolios (name, category_id, parent_id) VALUES (?, ?, ?)", (portfolio_name, cat_id, parent_id))
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif parsed_url.path == '/api/transfer':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                source_portfolio_id = data.get('sourcePortfolioId')
                dest_portfolio_id = data.get('destPortfolioId')
                ticker = data.get('ticker').upper().strip()
                shares = float(data.get('shares', 0))
                price = float(data.get('price', 0))
                date = data.get('date')
                
                if not all([source_portfolio_id, dest_portfolio_id, ticker, shares > 0, price >= 0]):
                    raise ValueError("Missing required fields or invalid amounts")
                
                if int(source_portfolio_id) == int(dest_portfolio_id):
                    raise ValueError("Source and destination portfolios must be different")
                    
                db_path = os.path.join(DIRECTORY, 'portfolio.db')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check source and destination portfolios
                cursor.execute("SELECT id FROM portfolios WHERE id=?", (source_portfolio_id,))
                if not cursor.fetchone():
                    raise ValueError(f"Source portfolio ID {source_portfolio_id} does not exist")
                    
                cursor.execute("SELECT id FROM portfolios WHERE id=?", (dest_portfolio_id,))
                if not cursor.fetchone():
                    raise ValueError(f"Destination portfolio ID {dest_portfolio_id} does not exist")
                
                # Check if asset exists in source portfolio
                cursor.execute("SELECT id, company_name, sector FROM assets WHERE ticker=? AND portfolio_id=?", (ticker, source_portfolio_id))
                src_asset_row = cursor.fetchone()
                if not src_asset_row:
                    raise ValueError(f"Ticker {ticker} not found in source portfolio")
                src_asset_id, company_name, sector = src_asset_row
                
                # Calculate available shares in source
                cursor.execute("SELECT SUM(shares) FROM transactions WHERE asset_id=?", (src_asset_id,))
                avail_shares_row = cursor.fetchone()
                avail_shares = avail_shares_row[0] if (avail_shares_row and avail_shares_row[0] is not None) else 0
                
                # Use a small tolerance for floating point comparison (e.g., 1e-8)
                if avail_shares < shares - 1e-8:
                    raise ValueError(f"Insufficient shares of {ticker} in source portfolio. Available: {avail_shares}, requested: {shares}")
                
                # Get or create destination asset
                cursor.execute("SELECT id FROM assets WHERE ticker=? AND portfolio_id=?", (ticker, dest_portfolio_id))
                dest_asset_row = cursor.fetchone()
                if dest_asset_row:
                    dest_asset_id = dest_asset_row[0]
                else:
                    cursor.execute("INSERT INTO assets (ticker, company_name, sector, portfolio_id) VALUES (?, ?, ?, ?)",
                                   (ticker, company_name, sector, dest_portfolio_id))
                    dest_asset_id = cursor.lastrowid
                
                # Get currency from source asset
                cursor.execute("SELECT currency FROM transactions WHERE asset_id=? LIMIT 1", (src_asset_id,))
                currency_row = cursor.fetchone()
                currency = currency_row[0] if currency_row else 'USD'
                
                # Perform the transfer transactions inside SQLite transaction
                if date:
                    cursor.execute("INSERT INTO transactions (asset_id, type, shares, price, currency, transaction_date) VALUES (?, 'TRANSFER_OUT', ?, ?, ?, ?)",
                                   (src_asset_id, -shares, price, currency, date))
                    cursor.execute("INSERT INTO transactions (asset_id, type, shares, price, currency, transaction_date) VALUES (?, 'TRANSFER_IN', ?, ?, ?, ?)",
                                   (dest_asset_id, shares, price, currency, date))
                else:
                    cursor.execute("INSERT INTO transactions (asset_id, type, shares, price, currency) VALUES (?, 'TRANSFER_OUT', ?, ?, ?)",
                                   (src_asset_id, -shares, price, currency))
                    cursor.execute("INSERT INTO transactions (asset_id, type, shares, price, currency) VALUES (?, 'TRANSFER_IN', ?, ?, ?)",
                                   (dest_asset_id, shares, price, currency))
                
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif parsed_url.path == '/api/ingest':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                type = data.get('type', 'BUY').upper()
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
                    
                if type == 'SELL':
                    shares = -abs(shares)
                
                db_path = os.path.join(DIRECTORY, 'portfolio.db')
                conn = sqlite3.connect(db_path)
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
                
                if tx_date:
                    cursor.execute("INSERT INTO transactions (asset_id, type, shares, price, currency, transaction_date) VALUES (?, ?, ?, ?, ?, ?)",
                                   (asset_id, type, shares, price, currency, tx_date))
                else:
                    cursor.execute("INSERT INTO transactions (asset_id, type, shares, price, currency) VALUES (?, ?, ?, ?, ?)",
                                   (asset_id, type, shares, price, currency))
                
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif parsed_url.path == '/api/bulk-ingest':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                tx_list = data.get('transactions', [])
                if not tx_list:
                    raise ValueError("No transactions provided")
                
                db_path = os.path.join(DIRECTORY, 'portfolio.db')
                conn = sqlite3.connect(db_path)
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
                    
                    if tx_date:
                        cursor.execute("INSERT INTO transactions (asset_id, type, shares, price, currency, transaction_date) VALUES (?, ?, ?, ?, ?, ?)",
                                       (asset_id, tx_type, shares, price, currency, tx_date))
                    else:
                        cursor.execute("INSERT INTO transactions (asset_id, type, shares, price, currency) VALUES (?, ?, ?, ?, ?)",
                                       (asset_id, tx_type, shares, price, currency))
                
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "count": len(tx_list)}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif parsed_url.path == '/api/research-report':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                report_key = data.get('report_key', '').strip()
                ticker = data.get('ticker', '').strip().upper()
                company_name = data.get('company_name', '').strip()
                subtitle = data.get('subtitle', '')
                prepared_by = data.get('prepared_by', '')
                audited_by = data.get('audited_by', '')
                rating = data.get('rating', '')
                is_positive = 1 if data.get('is_positive') else 0
                price_target = data.get('price_target') or None
                analysis_price = data.get('analysis_price') or None
                sector = data.get('sector', 'Other Sectors')
                en_overview = data.get('en_overview', '')
                th_overview = data.get('th_overview', '')
                en_dcf = data.get('en_dcf', '')
                th_dcf = data.get('th_dcf', '')
                if not report_key or not ticker or not company_name:
                    raise ValueError("report_key, ticker, and company_name are required")
                db_path = os.path.join(DIRECTORY, 'portfolio.db')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT INTO research_reports (report_key, ticker, company_name, subtitle, prepared_by, audited_by, rating, is_positive, price_target, analysis_price, sector, en_overview, th_overview, en_dcf, th_dcf)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (report_key, ticker, company_name, subtitle, prepared_by, audited_by, rating, is_positive, price_target, analysis_price, sector, en_overview, th_overview, en_dcf, th_dcf)
                )
                conn.commit()
                conn.close()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_PUT(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == '/api/transaction':
            query = urllib.parse.parse_qs(parsed_url.query)
            tx_id = query.get('id', [None])[0]
            if not tx_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Transaction id required"}).encode())
                return
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                data = json.loads(body)

                tx_type = data.get('type')
                shares = float(data.get('shares', 0))
                price = float(data.get('price', 0))
                currency = data.get('currency', 'USD')
                tx_date = data.get('transactionDate')

                if not tx_type or shares == 0 or price <= 0:
                    raise ValueError("Missing required fields")

                # Negative shares for SELL/TRANSFER_OUT
                if tx_type in ('SELL', 'TRANSFER_OUT'):
                    shares = -abs(shares)
                else:
                    shares = abs(shares)

                db_path = os.path.join(DIRECTORY, 'portfolio.db')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                if tx_date:
                    cursor.execute(
                        "UPDATE transactions SET type=?, shares=?, price=?, currency=?, transaction_date=? WHERE id=?",
                        (tx_type, shares, price, currency, tx_date, tx_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE transactions SET type=?, shares=?, price=?, currency=? WHERE id=?",
                        (tx_type, shares, price, currency, tx_id)
                    )
                conn.commit()
                conn.close()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif parsed_url.path == '/api/research-report':
            query = urllib.parse.parse_qs(parsed_url.query)
            report_key = query.get('key', [None])[0]
            if not report_key:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "report_key required"}).encode())
                return
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length)
                data = json.loads(body)
                ticker = data.get('ticker', '').strip().upper()
                company_name = data.get('company_name', '').strip()
                subtitle = data.get('subtitle', '')
                prepared_by = data.get('prepared_by', '')
                audited_by = data.get('audited_by', '')
                rating = data.get('rating', '')
                is_positive = 1 if data.get('is_positive') else 0
                price_target = data.get('price_target') or None
                analysis_price = data.get('analysis_price') or None
                sector = data.get('sector', 'Other Sectors')
                en_overview = data.get('en_overview', '')
                th_overview = data.get('th_overview', '')
                en_dcf = data.get('en_dcf', '')
                th_dcf = data.get('th_dcf', '')
                db_path = os.path.join(DIRECTORY, 'portfolio.db')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(
                    '''UPDATE research_reports SET ticker=?, company_name=?, subtitle=?, prepared_by=?, audited_by=?, rating=?, is_positive=?, price_target=?, analysis_price=?, sector=?, en_overview=?, th_overview=?, en_dcf=?, th_dcf=?
                       WHERE report_key=?''',
                    (ticker, company_name, subtitle, prepared_by, audited_by, rating, is_positive, price_target, analysis_price, sector, en_overview, th_overview, en_dcf, th_dcf, report_key)
                )
                conn.commit()
                conn.close()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        parsed_url = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        if parsed_url.path == '/api/portfolio':
            try:
                data = json.loads(post_data.decode('utf-8'))
                old_name = data.get('oldName')
                new_name = data.get('newName')
                parent_name = data.get('parentName')
                if not old_name or not new_name:
                    raise ValueError("oldName and newName required")
                
                db_path = os.path.join(DIRECTORY, 'portfolio.db')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                if parent_name:
                    cursor.execute("SELECT id FROM portfolios WHERE name=? AND parent_id IS NULL", (parent_name,))
                    p_row = cursor.fetchone()
                    if p_row:
                        p_id = p_row[0]
                        cursor.execute("UPDATE portfolios SET name=? WHERE name=? AND parent_id=?", (new_name, old_name, p_id))
                    else:
                        cursor.execute("UPDATE portfolios SET name=? WHERE name=?", (new_name, old_name))
                else:
                    cursor.execute("UPDATE portfolios SET name=? WHERE name=?", (new_name, old_name))
                    
                conn.commit()
                conn.close()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
            
        elif parsed_url.path == '/api/asset-adjustment':
            try:
                data = json.loads(post_data.decode('utf-8'))
                ticker = data.get('ticker')
                portfolio_name = data.get('portfolio')
                new_shares = float(data.get('shares', 0))
                new_price = float(data.get('price', 0))
                currency = data.get('currency', 'USD')
                
                db_path = os.path.join(DIRECTORY, 'portfolio.db')
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT id FROM portfolios WHERE name=?", (portfolio_name,))
                p_row = cursor.fetchone()
                if not p_row:
                    raise ValueError("Portfolio not found")
                p_id = p_row['id']
                
                cursor.execute("SELECT id FROM assets WHERE ticker=? AND portfolio_id=?", (ticker, p_id))
                a_row = cursor.fetchone()
                if not a_row:
                    raise ValueError("Asset not found")
                asset_id = a_row['id']
                
                cursor.execute("DELETE FROM transactions WHERE asset_id=?", (asset_id,))
                if new_shares > 0:
                    cursor.execute("INSERT INTO transactions (asset_id, type, shares, price, currency) VALUES (?, 'BUY', ?, ?, ?)", (asset_id, new_shares, new_price, currency))
                
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == '/api/transaction':
            query = urllib.parse.parse_qs(parsed_url.query)
            tx_id = query.get('id', [None])[0]
            if not tx_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Transaction id required"}).encode())
                return
            try:
                db_path = os.path.join(DIRECTORY, 'portfolio.db')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM transactions WHERE id=?", (tx_id,))
                conn.commit()
                conn.close()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif parsed_url.path == '/api/portfolio':
            query = urllib.parse.parse_qs(parsed_url.query)
            p_name = query.get('name', [None])[0]
            
            if not p_name:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Portfolio name required"}).encode())
                return
                
            try:
                db_path = os.path.join(DIRECTORY, 'portfolio.db')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Find portfolio ID
                cursor.execute("SELECT id FROM portfolios WHERE name=?", (p_name,))
                p_row = cursor.fetchone()
                if not p_row:
                    raise ValueError(f"Portfolio '{p_name}' not found")
                p_id = p_row[0]
                
                # If it's a parent portfolio, we need to gather all sub-portfolios under it
                cursor.execute("SELECT id FROM portfolios WHERE parent_id=?", (p_id,))
                sub_ids = [row[0] for row in cursor.fetchall()]
                
                # Combine parent ID and sub portfolio IDs
                all_ids = [p_id] + sub_ids
                
                # Delete transactions related to assets in these portfolios
                for curr_id in all_ids:
                    cursor.execute("DELETE FROM transactions WHERE asset_id IN (SELECT id FROM assets WHERE portfolio_id=?)", (curr_id,))
                    cursor.execute("DELETE FROM assets WHERE portfolio_id=?", (curr_id,))
                    cursor.execute("DELETE FROM portfolios WHERE id=?", (curr_id,))
                
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif parsed_url.path == '/api/research-report':
            query = urllib.parse.parse_qs(parsed_url.query)
            report_key = query.get('key', [None])[0]
            if not report_key:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "report_key required"}).encode())
                return
            try:
                db_path = os.path.join(DIRECTORY, 'portfolio.db')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM research_reports WHERE report_key=?", (report_key,))
                conn.commit()
                conn.close()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == '__main__':
    print(f"Starting server on http://127.0.0.1:{PORT} serving {DIRECTORY}...")
    server = http.server.HTTPServer(('127.0.0.1', PORT), MyHandler)
    server.serve_forever()
