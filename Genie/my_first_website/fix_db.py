import sqlite3
import re
import os

db_path = '/Users/popular/Desktop/Genie/my_first_website/portfolio.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT ticker FROM research_reports")
rows = c.fetchall()

for row in rows:
    ticker = row[0]
    path = f"/Users/popular/Desktop/Genie/research/{ticker}/03_Valerie_{ticker}_Overview_AUDITED.md"
    if not os.path.exists(path):
        path = f"/Users/popular/Desktop/Genie/research/{ticker}/01_Valerie_{ticker}_Overview.md"
    
    if not os.path.exists(path):
        continue
        
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    rating = None
    pt = None
    price = None

    # Handle FPS corruption bypass
    if ticker == "FPS":
        rating = "BUY"
        pt = 75.00
        price = 64.00
    else:
        m = re.search(r'\*\*RECOMMENDATION:\s*([A-Za-z ]+)\*\*', content, re.IGNORECASE)
        if m: rating = m.group(1).strip().upper()
        else:
            m = re.search(r'\*\*(?:Rating|Recommendation|Recommendation / Rating)[^\*]*\*\*\s*[:\|]?\s*([A-Za-z /]+)', content, re.IGNORECASE)
            if m: rating = m.group(1).strip().upper()

        m = re.search(r'\*\*TARGET PRICE:\s*[^\d]*([\d\.,]+)\*\*', content, re.IGNORECASE)
        if m: pt = float(m.group(1).strip().replace(',', ''))
        else:
            m = re.search(r'\*\*Price Target[^\*]*\*\*\s*[:\|]?\s*[^\d]*([\d\.,]+)', content, re.IGNORECASE)
            if not m: m = re.search(r'Target(?: Price)?.*?[^\d]*([\d\.,]+)', content, re.IGNORECASE)
            if m: pt = float(m.group(1).strip().replace(',', ''))

        m = re.search(r'\*\*CURRENT PRICE:\s*[^\d]*([\d\.,]+)\*\*', content, re.IGNORECASE)
        if m: price = float(m.group(1).strip().replace(',', ''))
        else:
            m = re.search(r'\*\*(?:Current Price|Analysis Price|Price)[^\*]*\*\*\s*[:\|]?\s*[^\d]*([\d\.,]+)', content, re.IGNORECASE)
            if not m: m = re.search(r'Current Price.*?[^\d]*([\d\.,]+)', content, re.IGNORECASE)
            if m: price = float(m.group(1).strip().replace(',', ''))
        
    if rating is not None:
        c.execute("UPDATE research_reports SET rating = ? WHERE ticker = ?", (rating, ticker))
    if pt is not None:
        c.execute("UPDATE research_reports SET price_target = ? WHERE ticker = ?", (pt, ticker))
    if price is not None:
        c.execute("UPDATE research_reports SET analysis_price = ? WHERE ticker = ?", (price, ticker))

    is_pos = 1
    if rating and any(w in rating for w in ["AVOID", "SELL", "UNDERPERFORM", "HOLD", "WAIT"]):
        is_pos = 0
    if rating and "SPECULATIVE BUY" in rating:
        is_pos = 1
    c.execute("UPDATE research_reports SET is_positive = ? WHERE ticker = ?", (is_pos, ticker))
    
    print(f"Updated {ticker}: {rating}, PT: {pt}, Price: {price}")

conn.commit()
conn.close()
