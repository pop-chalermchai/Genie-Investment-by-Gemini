import sqlite3
import os
import re

db_path = os.path.join(os.path.dirname(__file__), 'portfolio.db')
app_js_path = os.path.join(os.path.dirname(__file__), 'app.js')

def migrate_reports():
    with open(app_js_path, 'r', encoding='utf-8') as f:
        code = f.read()
        
    start_str = "const researchReports = {"
    end_str = "};\n\n// ==========================================================================\n// CORE WORKSPACE INITIALIZATION"
    
    s = code.find(start_str)
    e = code.find(end_str)
    if s == -1 or e == -1:
        # Fallback end search
        e = code.find("};\n\n//")
    
    if s == -1 or e == -1:
        print("Could not find researchReports in app.js")
        return
        
    reports_block = code[s + len(start_str):e]
    
    # Split by top-level keys. This is a bit hacky but works for the known format.
    # The format is like:
    #     mu: {
    #         ticker: "MU",
    # ...
    #         th: `...`
    #     },
    #     hynix: {
    
    # We will use regex to find the blocks
    pattern = re.compile(r'^\s+([a-z]+):\s*\{\s*\n(.*?)\n\s+\}(?:,|\n$)', re.MULTILINE | re.DOTALL)
    matches = pattern.findall(reports_block + '\n}')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
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
            en_content TEXT,
            th_content TEXT
        )
    ''')
    
    for key, content in matches:
        # Extract fields using regex
        ticker = re.search(r'ticker:\s*"([^"]+)"', content).group(1)
        company_name = re.search(r'companyName:\s*"([^"]+)"', content).group(1)
        subtitle = re.search(r'subtitle:\s*"([^"]+)"', content).group(1)
        prepared_by = re.search(r'preparedBy:\s*"([^"]+)"', content).group(1)
        audited_by = re.search(r'auditedBy:\s*"([^"]+)"', content).group(1)
        rating = re.search(r'rating:\s*"([^"]+)"', content).group(1)
        is_positive = 'true' in re.search(r'isPositive:\s*(true|false)', content).group(1)
        
        en_content = re.search(r'en:\s*`(.*?)`', content, re.DOTALL).group(1)
        th_content = re.search(r'th:\s*`(.*?)`', content, re.DOTALL).group(1)
        
        cursor.execute('''
            INSERT OR REPLACE INTO research_reports 
            (report_key, ticker, company_name, subtitle, prepared_by, audited_by, rating, is_positive, en_content, th_content)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (key, ticker, company_name, subtitle, prepared_by, audited_by, rating, is_positive, en_content, th_content))
        
        print(f"Migrated report: {key}")
        
    conn.commit()
    conn.close()
    print("Migration of reports complete!")

if __name__ == '__main__':
    migrate_reports()
