import sqlite3
import os

import re

def clean_markdown(text):
    if not text:
        return ""
    # Remove frontmatter (YAML block at the top)
    if text.strip().startswith('---'):
        text = re.sub(r'^---\s*\n.*?\n---\s*\n', '', text, flags=re.DOTALL)
    # Remove links block at the bottom
    text = re.sub(r'\n*---\s*\n\*\*Links:\*\*.*$', '', text, flags=re.DOTALL)
    return text.strip()


db_path = "/Users/popular/Desktop/Genie/my_first_website/portfolio.db"

# Read localized files from research/FLY
with open("/Users/popular/Desktop/Genie/research/FLY/01_Valerie_FLY_Analysis.md", "r", encoding="utf-8") as f:
    en_overview = clean_markdown(f.read())

with open("/Users/popular/Desktop/Genie/research/FLY/02_Christian_FLY_Audit.md", "r", encoding="utf-8") as f:
    en_dcf = clean_markdown(f.read())

with open("/Users/popular/Desktop/Genie/research/FLY/01_Valerie_FLY_Analysis_TH.md", "r", encoding="utf-8") as f:
    th_overview = clean_markdown(f.read())

with open("/Users/popular/Desktop/Genie/research/FLY/02_Christian_FLY_Audit_TH.md", "r", encoding="utf-8") as f:
    th_dcf = clean_markdown(f.read())

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute('''
        INSERT OR REPLACE INTO research_reports (
            report_key, ticker, company_name, subtitle, prepared_by, audited_by, rating, is_positive, en_overview, th_overview, en_dcf, th_dcf, sector
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'fly', 'FLY', 'Firefly Aerospace, Inc.', 'Northrop Partnership & High-Hurdle Growth Scaling',
        'Valerie', 'Christian', 'SPECULATIVE BUY', True, en_overview, th_overview, en_dcf, th_dcf, 'Aerospace'
    ))
    conn.commit()
    print("Successfully inserted FLY reports into the database!")
except Exception as e:
    print(f"Error inserting to DB: {e}")
finally:
    conn.close()