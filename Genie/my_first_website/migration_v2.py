import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'portfolio.db')

def migrate():
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}. Please initialize it first.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Add parent_id column if it doesn't exist
    cursor.execute("PRAGMA table_info(portfolios)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'parent_id' not in columns:
        print("Adding parent_id column to portfolios table...")
        try:
            cursor.execute("ALTER TABLE portfolios ADD COLUMN parent_id INTEGER REFERENCES portfolios(id)")
            conn.commit()
            print("✅ Column parent_id added successfully.")
        except Exception as e:
            print(f"❌ Error adding column: {e}")
            conn.close()
            return
    else:
        print("parent_id column already exists in portfolios table.")

    # 2. Get category IDs
    cursor.execute("SELECT id, name FROM categories")
    categories = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Ensure standard categories exist
    if 'Stocks' not in categories:
        cursor.execute("INSERT INTO categories (name, description) VALUES ('Stocks', 'หุ้นและ ETF ทั่วไป')")
        categories['Stocks'] = cursor.lastrowid
    if 'Provident Fund' not in categories:
        cursor.execute("INSERT INTO categories (name, description) VALUES ('Provident Fund', 'กองทุนสำรองเลี้ยงชีพ')")
        categories['Provident Fund'] = cursor.lastrowid
        
    stocks_cat_id = categories['Stocks']
    pvd_cat_id = categories['Provident Fund']

    # 3. Migrate 'US Stock' parent and its sub-portfolios (Dime, WeBull)
    # Check if 'US Stock' parent exists (name='US Stock' and parent_id IS NULL)
    cursor.execute("SELECT id FROM portfolios WHERE name='US Stock' AND parent_id IS NULL")
    us_stock_parent = cursor.fetchone()
    if not us_stock_parent:
        cursor.execute("INSERT INTO portfolios (name, category_id, parent_id) VALUES ('US Stock', ?, NULL)", (stocks_cat_id,))
        us_stock_parent_id = cursor.lastrowid
        print(f"✅ Created parent portfolio 'US Stock' (ID: {us_stock_parent_id})")
    else:
        us_stock_parent_id = us_stock_parent[0]
        print(f"Parent portfolio 'US Stock' already exists (ID: {us_stock_parent_id})")

    # Link Dime
    cursor.execute("SELECT id, parent_id FROM portfolios WHERE name='Dime'")
    dime_row = cursor.fetchone()
    if dime_row:
        dime_id, dime_parent = dime_row
        if dime_parent != us_stock_parent_id:
            cursor.execute("UPDATE portfolios SET parent_id=? WHERE id=?", (us_stock_parent_id, dime_id))
            print(f"✅ Linked portfolio 'Dime' to 'US Stock' parent")
        else:
            print("Portfolio 'Dime' is already linked to 'US Stock'")

    # Link WeBull
    cursor.execute("SELECT id, parent_id FROM portfolios WHERE name='WeBull'")
    webull_row = cursor.fetchone()
    if webull_row:
        webull_id, webull_parent = webull_row
        if webull_parent != us_stock_parent_id:
            cursor.execute("UPDATE portfolios SET parent_id=? WHERE id=?", (us_stock_parent_id, webull_id))
            print(f"✅ Linked portfolio 'WeBull' to 'US Stock' parent")
        else:
            print("Portfolio 'WeBull' is already linked to 'US Stock'")

    # 4. Migrate 'Tax Saving Fund' parent and sub-portfolio
    # Check if there is already a sub-portfolio of Tax Saving Fund (name='Tax Saving Fund' and parent_id IS NOT NULL)
    cursor.execute("SELECT id FROM portfolios WHERE name='Tax Saving Fund' AND parent_id IS NOT NULL")
    tsf_sub_row = cursor.fetchone()
    
    if not tsf_sub_row:
        # We need to find the original portfolio named 'Tax Saving Fund' (which has parent_id IS NULL)
        cursor.execute("SELECT id FROM portfolios WHERE name='Tax Saving Fund' AND parent_id IS NULL")
        tsf_original_rows = cursor.fetchall()
        
        if len(tsf_original_rows) == 1:
            # We have exactly one. This is the original one with assets.
            original_id = tsf_original_rows[0][0]
            
            # Create a new parent portfolio named 'Tax Saving Fund'
            cursor.execute("INSERT INTO portfolios (name, category_id, parent_id) VALUES ('Tax Saving Fund', ?, NULL)", (stocks_cat_id,))
            parent_id = cursor.lastrowid
            
            # Set the original portfolio's parent_id to the new parent
            cursor.execute("UPDATE portfolios SET parent_id=? WHERE id=?", (parent_id, original_id))
            print(f"✅ Created parent 'Tax Saving Fund' and linked original sub-portfolio (ID: {original_id}) to it.")
        elif len(tsf_original_rows) > 1:
            # This shouldn't happen unless we are in an intermediate state. Let's link the first one to the second one.
            original_id = tsf_original_rows[0][0]
            parent_id = tsf_original_rows[1][0]
            cursor.execute("UPDATE portfolios SET parent_id=? WHERE id=?", (parent_id, original_id))
            print(f"✅ Linked existing portfolio ID {original_id} to parent ID {parent_id}")
        else:
            # Tax Saving Fund doesn't exist at all. Let's create both.
            cursor.execute("INSERT INTO portfolios (name, category_id, parent_id) VALUES ('Tax Saving Fund', ?, NULL)", (stocks_cat_id,))
            parent_id = cursor.lastrowid
            cursor.execute("INSERT INTO portfolios (name, category_id, parent_id) VALUES ('Tax Saving Fund', ?, ?)", (stocks_cat_id, parent_id))
            print(f"✅ Created new parent and sub-portfolio 'Tax Saving Fund'.")
    else:
        print("Tax Saving Fund parent-child hierarchy is already set up.")

    # 5. Migrate 'Provident Fund' parent and sub-portfolio
    # Check if there is already a sub-portfolio of Provident Fund (name='Provident Fund' and parent_id IS NOT NULL)
    cursor.execute("SELECT id FROM portfolios WHERE name='Provident Fund' AND parent_id IS NOT NULL")
    pvd_sub_row = cursor.fetchone()
    
    if not pvd_sub_row:
        # Find original
        cursor.execute("SELECT id FROM portfolios WHERE name='Provident Fund' AND parent_id IS NULL")
        pvd_original_rows = cursor.fetchall()
        
        if len(pvd_original_rows) == 1:
            original_id = pvd_original_rows[0][0]
            
            # Create a new parent
            cursor.execute("INSERT INTO portfolios (name, category_id, parent_id) VALUES ('Provident Fund', ?, NULL)", (pvd_cat_id,))
            parent_id = cursor.lastrowid
            
            # Link original
            cursor.execute("UPDATE portfolios SET parent_id=? WHERE id=?", (parent_id, original_id))
            print(f"✅ Created parent 'Provident Fund' and linked original sub-portfolio (ID: {original_id}) to it.")
        elif len(pvd_original_rows) > 1:
            original_id = pvd_original_rows[0][0]
            parent_id = pvd_original_rows[1][0]
            cursor.execute("UPDATE portfolios SET parent_id=? WHERE id=?", (parent_id, original_id))
            print(f"✅ Linked existing portfolio ID {original_id} to parent ID {parent_id}")
        else:
            # Create both
            cursor.execute("INSERT INTO portfolios (name, category_id, parent_id) VALUES ('Provident Fund', ?, NULL)", (pvd_cat_id,))
            parent_id = cursor.lastrowid
            cursor.execute("INSERT INTO portfolios (name, category_id, parent_id) VALUES ('Provident Fund', ?, ?)", (pvd_cat_id, parent_id))
            print(f"✅ Created new parent and sub-portfolio 'Provident Fund'.")
    else:
        print("Provident Fund parent-child hierarchy is already set up.")

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == '__main__':
    migrate()
