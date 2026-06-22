import os
import re
import sqlite3

tickers = ["AAOI", "AAPL", "AMKR", "AMSC", "BMNR", "EOSE", "FLY", "FPS", "Hynix", "JBL", "LITE", "MU", "NVDA"]

def clean_markdown(text):
    if not text:
        return ""
    # Remove frontmatter (YAML block at the top)
    if text.strip().startswith('---'):
        text = re.sub(r'^---\s*\n.*?\n---\s*\n', '', text, flags=re.DOTALL)
    # Remove links block at the bottom
    text = re.sub(r'\n*---\s*\n\*\*Links:\*\*.*$', '', text, flags=re.DOTALL)
    return text.strip()

def extract_info(ticker):
    path = f"/Users/popular/Desktop/Genie/research/{ticker}/01_Valerie_{ticker}_Overview.md"
    # Fallback to older file naming format if needed
    if not os.path.exists(path):
        # Scan folder for a file that contains "Overview" and ends in .md
        folder = f"/Users/popular/Desktop/Genie/research/{ticker}"
        if os.path.exists(folder):
            for f in os.listdir(folder):
                if "overview" in f.lower() and f.endswith(".md") and not "audited" in f.lower() and not "_th" in f.lower():
                    path = os.path.join(folder, f)
                    break
                    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Skipping {ticker} (Overview not found at {path})")
        return None
    
    company = ticker
    sector = "Technology"
    rating = "BUY"
    pt = 0.0
    price = 0.0
    
    m = re.search(r'\*\*Sector(?:[^\*]*)\*\*\s*[:\|]?\s*([^\n\|]+)', content, re.IGNORECASE)
    if m: sector = m.group(1).strip()
    
    m = re.search(r'\*\*(?:Rating|Recommendation|Recommendation / Rating)(?:[^\*]*)\*\*\s*[:\|]?\s*([A-Za-z ]+)', content, re.IGNORECASE)
    if m: rating = m.group(1).strip().upper()
        
    m = re.search(r'\*\*Price Target[^\*]*\*\*\s*[:\|]?\s*\$?([\d\.]+)', content, re.IGNORECASE)
    if not m: m = re.search(r'Target(?: Price)?.*?\$([\d\.]+)', content, re.IGNORECASE)
    if m: pt = float(m.group(1).strip().replace(',', ''))
        
    m = re.search(r'\*\*(?:Current Price|Analysis Price|Price)[^\*]*\*\*\s*[:\|]?\s*\$?([\d\.]+)', content, re.IGNORECASE)
    if not m: m = re.search(r'Current Price.*?\$([\d\.]+)', content, re.IGNORECASE)
    if m: price = float(m.group(1).strip().replace(',', ''))
        
    m = re.search(r'^#\s*(.*?)\s*\(', content, re.MULTILINE)
    if not m: m = re.search(r'^#\s*(.*?)\n', content, re.MULTILINE)
    if m: company = m.group(1).strip()
        
    is_positive = 0 if any(w in rating for w in ["AVOID", "SELL", "UNDERPERFORM", "HOLD", "WAIT"]) else 1
    if "SPECULATIVE BUY" in rating: is_positive = 1
    
    # Files
    dcf_path = f"/Users/popular/Desktop/Genie/research/{ticker}/03_Valerie_{ticker}_ReverseDCF_AUDITED.md"
    if not os.path.exists(dcf_path):
        # Fallback
        dcf_path = f"/Users/popular/Desktop/Genie/research/{ticker}/02_Valerie_{ticker}_ReverseDCF.md"
        
    th_ov_path = f"/Users/popular/Desktop/Genie/research/{ticker}/04_Serene_{ticker}_Overview_TH.md"
    th_dcf_path = f"/Users/popular/Desktop/Genie/research/{ticker}/04_Serene_{ticker}_ReverseDCF_TH.md"
    
    def read_f(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return clean_markdown(f.read())
        except:
            return ""
            
    en_overview = clean_markdown(content)
    th_overview = read_f(th_ov_path)
    en_dcf = read_f(dcf_path)
    th_dcf = read_f(th_dcf_path)
    
    return (
        f"{ticker.lower()}",
        ticker,
        company,
        "Institutional Equity Research | " + rating,
        "Valerie (The Quantitative Oracle)",
        "Christian (The Forensic Auditor)",
        rating,
        is_positive,
        pt,
        price,
        sector,
        en_overview,
        th_overview,
        en_dcf,
        th_dcf
    )

def main():
    db_path = os.path.join(os.path.dirname(__file__), 'portfolio.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS research_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_key TEXT UNIQUE NOT NULL,
            ticker TEXT,
            company_name TEXT,
            subtitle TEXT,
            prepared_by TEXT,
            audited_by TEXT,
            rating TEXT,
            is_positive BOOLEAN,
            price_target REAL,
            analysis_price REAL,
            sector TEXT,
            en_overview TEXT,
            th_overview TEXT,
            en_dcf TEXT,
            th_dcf TEXT
        )
    ''')
    
    for t in tickers:
        data = extract_info(t)
        if data:
            print(f"Ingesting {t}...")
            try:
                c.execute('''
                    INSERT INTO research_reports (
                        report_key, ticker, company_name, subtitle, prepared_by, audited_by, rating, 
                        is_positive, price_target, analysis_price, sector, 
                        en_overview, th_overview, en_dcf, th_dcf
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', data)
            except sqlite3.IntegrityError:
                print(f"Updating {t}...")
                c.execute('''
                    UPDATE research_reports SET
                        ticker=?, company_name=?, subtitle=?, prepared_by=?, audited_by=?, rating=?, 
                        is_positive=?, price_target=?, analysis_price=?, sector=?, 
                        en_overview=?, th_overview=?, en_dcf=?, th_dcf=?
                    WHERE report_key=?
                ''', data[1:] + (data[0],))
    conn.commit()
    conn.close()
    print("Done inserting all clean research reports to SQLite!")

if __name__ == '__main__':
    main()
