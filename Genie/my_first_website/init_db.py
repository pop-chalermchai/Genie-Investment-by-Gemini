import sqlite3
import os

# กำหนดที่เก็บไฟล์ฐานข้อมูล portfolio.db ให้อยู่ในโฟลเดอร์เดียวกันกับสคริปต์
db_path = os.path.join(os.path.dirname(__file__), 'portfolio.db')

def init_db():
    # สร้างหรือเชื่อมต่อกับฐานข้อมูล
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. ตาราง categories (ประเภทสินทรัพย์)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            user_id TEXT
        )
    ''')

    # 1b. ตาราง sectors (master data สำหรับ dropdown/autocomplete — ไม่ใช่ FK)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sectors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_id TEXT NOT NULL
        )
    ''')

    # 2. ตาราง portfolios (แฟ้มจัดเก็บพอร์ต)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_id INTEGER,
            parent_id INTEGER,
            sort_order INTEGER,
            user_id TEXT,
            FOREIGN KEY (category_id) REFERENCES categories (id),
            FOREIGN KEY (parent_id) REFERENCES portfolios (id)
        )
    ''')

    # 3. ตาราง assets (หลักทรัพย์/สินทรัพย์)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            company_name TEXT,
            sector TEXT,
            portfolio_id INTEGER,
            manual_price REAL,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
        )
    ''')

    # 4. ตาราง transactions (ประวัติการซื้อขาย)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER,
            type TEXT NOT NULL, -- 'BUY' หรือ 'SELL'
            shares REAL NOT NULL,
            price REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (asset_id) REFERENCES assets (id)
        )
    ''')

    # เพิ่มหมวดหมู่ตั้งต้นให้เลย (ถ้ายังไม่มี)
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO categories (name, description) VALUES ('Stocks', 'หุ้นและ ETF ทั่วไป')")
        cursor.execute("INSERT INTO categories (name, description) VALUES ('Provident Fund', 'กองทุนสำรองเลี้ยงชีพ')")
        cursor.execute("INSERT INTO categories (name, description) VALUES ('Crypto', 'สินทรัพย์ดิจิทัล')")
        conn.commit()

    # 5. ตาราง thai_funds (cache รายชื่อกองทุนไทยจาก SEC API)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS thai_funds (
            proj_id TEXT PRIMARY KEY,
            proj_abbr_name TEXT NOT NULL,
            proj_name_th TEXT,
            proj_name_en TEXT,
            fund_status TEXT,
            amc_name_en TEXT,
            unique_id TEXT,
            last_synced DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_thai_funds_abbr ON thai_funds (proj_abbr_name)')

    # 6. ตาราง profiles (ข้อมูลผู้ใช้ + preferences — local counterpart ของ migrations/004_profiles.sql)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            user_id            TEXT PRIMARY KEY,
            display_name       TEXT,
            avatar_emoji       TEXT NOT NULL DEFAULT '🧞',
            preferred_currency TEXT NOT NULL DEFAULT 'USD',
            preferred_theme    TEXT NOT NULL DEFAULT 'light',
            preferred_language TEXT NOT NULL DEFAULT 'en',
            updated_at         DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ สร้างฐานข้อมูลและ 6 ตารางสำเร็จแล้ว! ไฟล์ถูกเก็บไว้ที่: {db_path}")

if __name__ == '__main__':
    init_db()
