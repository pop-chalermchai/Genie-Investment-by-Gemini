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
                
                # Fetch holdings joined across tables
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
        elif parsed_url.path == '/api/transactions':
            db_path = os.path.join(DIRECTORY, 'portfolio.db')
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT 
                        t.id, t.type, t.shares, t.price, t.currency, t.transaction_date as transactionDate,
                        a.ticker, a.company_name as companyName, p.name as portfolio
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
                        "en_overview": r['en_overview'],
                        "th_overview": r['th_overview'],
                        "en_dcf": r['en_dcf'],
                        "th_dcf": r['th_dcf']
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
                
                cursor.execute("INSERT INTO portfolios (name, category_id) VALUES (?, ?)", (portfolio_name, cat_id))
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
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == '/api/portfolio':
            query = parse_qs(parsed_url.query)
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
                
                # Delete transactions related to assets in this portfolio
                cursor.execute("DELETE FROM transactions WHERE asset_id IN (SELECT id FROM assets WHERE portfolio_id=?)", (p_id,))
                
                # Delete assets in this portfolio
                cursor.execute("DELETE FROM assets WHERE portfolio_id=?", (p_id,))
                
                # Delete portfolio
                cursor.execute("DELETE FROM portfolios WHERE id=?", (p_id,))
                
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
    print(f"Starting server on http://localhost:{PORT} serving {DIRECTORY}...")
    server = http.server.HTTPServer(('localhost', PORT), MyHandler)
    server.serve_forever()
