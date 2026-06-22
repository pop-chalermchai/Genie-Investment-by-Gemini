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

with open("/Users/popular/Desktop/Genie/research/BMNR/01_BMNR_Fundamental_Analysis.md", "r") as f:
    fundamental = clean_markdown(f.read())

with open("/Users/popular/Desktop/Genie/research/BMNR/02_BMNR_Reverse_DCF.md", "r") as f:
    dcf = clean_markdown(f.read())

en_content = fundamental + "\n\n---\n\n" + dcf
th_content = """# บทวิเคราะห์: BitMine Immersion Technologies, Inc. (BMNR)

## ภาพรวมและการประเมินมูลค่า
BMNR เปลี่ยนจุดโฟกัสมาเป็นคนเก็บเหรียญ (Ethereum Treasury) โดยมีเป้าหมายทะเยอทะยานคือถือเหรียญ 5% ของทั้งหมดในระบบ (Alchemy of 5%) และนำไปฝากกินดอกเบี้ย (Staking) ทำให้การประเมินมูลค่าปัจจุบันเก็งกำไรสูงและผูกกับราคา ETH โดยตรง

## ประเมินมูลค่าแบบ Reverse DCF (โดย Valerie)
ที่มูลค่าบริษัท (EV) $8.5 พันล้านเหรียญ ตลาดกำลังคาดหวังให้ BMNR สร้างรายได้ที่มั่นคงระดับ $4.6 - $6.6 พันล้านเหรียญต่อปีในอนาคต (เติบโตขึ้น 15-20 เท่าจากปัจจุบัน) ซึ่งเป็นเป้าที่ยากมากถึงมากที่สุด (Execution Difficulty Score = 9/10) ในมุมมองของนักลงทุนสถาบัน

## ความเสี่ยงหลัก (Key Risks)
- **Dilution Risk:** การจะซื้อเหรียญให้ได้ตามเป้า บริษัทใช้วิธีเพิ่มทุนและออกหุ้นใหม่อย่างต่อเนื่อง ซึ่งจะทำให้นักลงทุนเจอสภาวะถูกลดสัดส่วน (Dilute) ตลอดเวลา

## สรุป (Judgment Call)
**เก็งกำไรเท่านั้น (Speculative Only)**: ความเสี่ยงสูงมาก ราคาปัจจุบันซื้อความคาดหวังแบบไร้ที่ติ (Priced for perfection) ไว้หมดแล้ว หากเครือข่ายมีปัญหาหรือเกิด Crypto Winter จะอันตรายต่อการถือยาวอย่างยิ่ง
"""

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if columns en_content and th_content exist, just in case
try:
    cursor.execute('''
        INSERT OR REPLACE INTO research_reports (
            report_key, ticker, company_name, subtitle, prepared_by, audited_by, rating, is_positive, en_content, th_content, sector
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'bmnr', 'BMNR', 'BitMine Immersion Technologies', 'Crypto Infrastructure & ETH Treasury',
        'Mateo & Valerie', 'Christian (Forensic)', 'HOLD / Speculative', False, en_content, th_content, 'Digital Assets & Infrastructure'
    ))
except Exception as e:
    print("Error:", e)

conn.commit()
conn.close()
print("BMNR report inserted successfully!")