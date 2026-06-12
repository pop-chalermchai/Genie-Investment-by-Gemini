import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'portfolio.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE research_reports RENAME COLUMN en_content TO en_overview")
    cursor.execute("ALTER TABLE research_reports RENAME COLUMN th_content TO th_overview")
    cursor.execute("ALTER TABLE research_reports ADD COLUMN en_dcf TEXT")
    cursor.execute("ALTER TABLE research_reports ADD COLUMN th_dcf TEXT")
    print("Database altered successfully.")
except Exception as e:
    print(f"Error altering database: {e}")

conn.commit()
conn.close()
