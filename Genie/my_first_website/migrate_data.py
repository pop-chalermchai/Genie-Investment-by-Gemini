import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'portfolio.db')

holdings = [
    {"ticker": "JBL", "companyName": "Jabil Inc.", "sector": "Technology", "shares": 50, "avgCost": 285.15, "currency": "USD", "portfolio": "Dime"},
    {"ticker": "VOO", "companyName": "Vanguard S&P 500 ETF", "sector": "Financial Services", "shares": 40, "avgCost": 480.00, "currency": "USD", "portfolio": "Tax Saving Fund"},
    {"ticker": "VOO", "companyName": "Vanguard S&P 500 ETF", "sector": "Financial Services", "shares": 0.20306, "avgCost": 630.31, "currency": "USD", "portfolio": "WeBull"},
    {"ticker": "QQQ", "companyName": "Invesco QQQ Trust", "sector": "Financial Services", "shares": 0.04719, "avgCost": 720.70, "currency": "USD", "portfolio": "WeBull"},
    {"ticker": "CBRS", "companyName": "Cerebras Systems Inc", "sector": "Technology", "shares": 0.35793, "avgCost": 279.66, "currency": "USD", "portfolio": "WeBull"},
    {"ticker": "EOSE", "companyName": "Eos Energy Enterprises Inc", "sector": "Industrials", "shares": 100, "avgCost": 9.50, "currency": "USD", "portfolio": "WeBull"},
    {"ticker": "INVZ", "companyName": "Innoviz Technologies Ltd", "sector": "Technology", "shares": 100, "avgCost": 0.70, "currency": "USD", "portfolio": "WeBull"},
    {"ticker": "CRML", "companyName": "Critical Metals Corp", "sector": "Basic Materials", "shares": 100, "avgCost": 15.00, "currency": "USD", "portfolio": "WeBull"},
    {"ticker": "ONDS", "companyName": "Ondas Holdings Inc", "sector": "Technology", "shares": 100, "avgCost": 13.00, "currency": "USD", "portfolio": "WeBull"},
    {"ticker": "GLD", "companyName": "SPDR Gold Shares", "sector": "Financial Services", "shares": 0.247, "avgCost": 0.00, "currency": "USD", "portfolio": "WeBull"},
    {"ticker": "BMNR", "companyName": "Bitmine Immersion Techs Inc", "sector": "Technology", "shares": 15, "avgCost": 39.51, "currency": "USD", "portfolio": "WeBull"},
    {"ticker": "IREN", "companyName": "Iren Limited", "sector": "Technology", "shares": 14, "avgCost": 58.42, "currency": "USD", "portfolio": "WeBull"},
    {"ticker": "KAsset PVD", "companyName": "KAsset Provident Fund (Siam Piwat)", "sector": "Diversified", "shares": 1.0, "avgCost": 333913.34, "currency": "THB", "portfolio": "Provident Fund"}
]

def migrate_data():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get category IDs
    cursor.execute("SELECT id FROM categories WHERE name='Stocks'")
    stock_cat_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM categories WHERE name='Provident Fund'")
    pvd_cat_id = cursor.fetchone()[0]

    # Insert Portfolios
    portfolios_data = {
        "Dime": stock_cat_id,
        "Tax Saving Fund": stock_cat_id,
        "WeBull": stock_cat_id,
        "Provident Fund": pvd_cat_id
    }
    
    portfolio_ids = {}
    for p_name, cat_id in portfolios_data.items():
        cursor.execute("INSERT INTO portfolios (name, category_id) VALUES (?, ?)", (p_name, cat_id))
        portfolio_ids[p_name] = cursor.lastrowid

    # Insert Assets and Transactions
    for h in holdings:
        p_id = portfolio_ids[h["portfolio"]]
        # Check if asset exists in this portfolio
        cursor.execute("SELECT id FROM assets WHERE ticker=? AND portfolio_id=?", (h["ticker"], p_id))
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO assets (ticker, company_name, sector, portfolio_id) VALUES (?, ?, ?, ?)", 
                          (h["ticker"], h["companyName"], h["sector"], p_id))
            asset_id = cursor.lastrowid
        else:
            asset_id = row[0]
        
        # Insert a single 'BUY' transaction to represent the current average cost and shares
        cursor.execute("INSERT INTO transactions (asset_id, type, shares, price, currency) VALUES (?, 'BUY', ?, ?, ?)",
                      (asset_id, h["shares"], h["avgCost"], h["currency"]))

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == '__main__':
    migrate_data()
