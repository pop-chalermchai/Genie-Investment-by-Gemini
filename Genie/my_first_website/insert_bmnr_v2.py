import sqlite3
import os

db_path = "/Users/popular/Desktop/Genie/my_first_website/portfolio.db"

# English from Christian
with open("/Users/popular/.gemini/antigravity-cli/brain/3a79accf-5157-4124-b90b-eb3aaf52ddec/bmnr_stock_analysis_overview.md", "r") as f:
    en_overview = f.read()

with open("/Users/popular/.gemini/antigravity-cli/brain/3a79accf-5157-4124-b90b-eb3aaf52ddec/bmnr_reverse_dcf_analysis.md", "r") as f:
    en_dcf = f.read()

# Thai from Serene
with open("/Users/popular/.gemini/antigravity-cli/brain/775c2c54-8f8f-4769-97e4-60cf9a3a261b/bmnr_stock_analysis_overview_th.md", "r") as f:
    th_overview = f.read()

with open("/Users/popular/.gemini/antigravity-cli/brain/775c2c54-8f8f-4769-97e4-60cf9a3a261b/bmnr_reverse_dcf_analysis_th.md", "r") as f:
    th_dcf = f.read()

# Add the image to the top of the English overview
# (Removed infographic embedding based on user feedback)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute('''
        INSERT OR REPLACE INTO research_reports (
            report_key, ticker, company_name, subtitle, prepared_by, audited_by, rating, is_positive, en_overview, th_overview, en_dcf, th_dcf, sector
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'bmnr', 'BMNR', 'BitMine Immersion Technologies', 'Ethereum Proxy Vault & Asymmetric Risk',
        'Valerie', 'Christian', 'AVOID / Speculative', False, en_overview, th_overview, en_dcf, th_dcf, 'Technology & Semiconductors'
    ))
    conn.commit()
    print("Successfully inserted BMNR reports into the new database schema!")
except Exception as e:
    print(f"Error inserting to DB: {e}")
finally:
    conn.close()
