# Security & Code Review — Genie Investment

> ตรวจโดย Fable 5 — 2026-07-04 (วันที่ 1 ของแผน 4 วัน)
> สโคป: `api/index.py`, `app.js`, `deploy.sh`, `vercel.json`, การตั้งค่า Supabase/Vercel
> สถานะโปรเจกต์ตอนตรวจ: single-user, ยังไม่มี auth, กำลังจะเปิดให้ผู้ใช้ภายนอก

---

## สรุปผู้บริหาร (อ่านแค่นี้ก่อนก็ได้)

แอปตอนนี้ **ยังปลอดภัยพอสำหรับใช้คนเดียว แต่ยังเปิดสาธารณะไม่ได้เด็ดขาด** จนกว่าจะแก้ 3 เรื่องแรกด้านล่าง จุดที่อันตรายที่สุดไม่ใช่บั๊กในโค้ด แต่คือ **ทุก API endpoint เปิดโล่งไม่มีการล็อกอิน** — ใครก็ตามที่รู้ URL สามารถอ่าน/แก้/ลบพอร์ตทั้งหมดได้ นี่คือเหตุผลว่าทำไมงานวันที่ 2 (Auth + RLS) ถึงเป็นหัวใจของแผนนี้

| # | ระดับ | ประเด็น | สถานะ |
|---|-------|---------|-------|
| 1 | 🔴 CRITICAL | ไม่มี authentication — API เปิดโล่งทั้งหมด | ✅ แก้แล้ว (Auth ES256 + user_id scoping ทุก endpoint; รอ cutover deploy) |
| 2 | 🟠 HIGH | Source code (.py) ถูกเสิร์ฟเป็น static บน production | ✅ แก้แล้ว (`.vercelignore` — รอ preview-deploy ยืนยัน) |
| 3 | 🟠 HIGH | SEC API keys ฝังใน source แล้วหลุดออกทาง #2 | ⚠️ เอา default ออกจาก source แล้ว — **รอ Pop rotate key ที่ SEC portal** |
| 4 | 🟡 MEDIUM | Stored XSS ผ่าน `innerHTML` + `marked.parse` ไม่ sanitize | ✅ แก้แล้ว (DOMPurify ครอบ `marked.parse`) + isolation ลดความเสี่ยง cross-user |
| 5 | 🟡 MEDIUM | ปิดการตรวจ SSL certificate ตอนต่อ Postgres | ✅ รองรับ verify-ca ผ่าน `SUPABASE_CA_CERT` (default เดิมกัน prod พัง) |
| 6 | 🟢 LOW | Error `str(e)` ส่งกลับ client ตรงๆ (leak internals) | ✅ แก้แล้ว (`_err()` — ValueError→400 ข้อความจริง, อื่นๆ→500 generic + log) |
| 7 | 🟢 LOW | ไม่มี rate limiting / CSRF / security headers | ⬜ ยังไม่ทำ (หลัง Auth) |

---

## 🔴 1. ไม่มี Authentication — API เปิดโล่งทั้งหมด (CRITICAL)

**หลักฐาน:** `api/index.py` ทุก route ตั้งแต่บรรทัด 84 ถึง 1059 ไม่มีการตรวจ identity ใดๆ เลย ไม่มี token, ไม่มี session, ไม่มี API key ฝั่ง client

**ผลกระทบ:** ถ้าเปิดให้ผู้ใช้ภายนอก ใครก็ได้ที่ยิง request มาที่ `https://…/api/…` จะสามารถ:
- `GET /api/init-data` → ดูพอร์ต/หุ้น/ต้นทุนทั้งหมดของทุกคน
- `POST /api/ingest`, `PUT /api/asset-adjustment` → แก้ข้อมูลของใครก็ได้
- `DELETE /api/portfolio?name=…` → ลบพอร์ตทิ้งได้ (บรรทัด 558–591 ลบ transactions+assets+portfolio เป็นทอดๆ)

**ทำไมต้องรอวันที่ 2:** นี่ไม่ใช่บั๊กที่แก้ด้วยการเติมโค้ดไม่กี่บรรทัด — ต้องออกแบบทั้งระบบ (auth provider, ผูก `user_id` เข้าทุกตาราง, RLS policy) จึงจัดเป็นงานหลักของวันที่ 2 พร้อม spec ที่จะร่างในวันที่ 1

**ข้อบรรเทาชั่วคราว (ถ้าจะเปิดก่อน auth เสร็จ):** ตั้ง Vercel password protection หรือ Vercel Firewall จำกัด IP ไว้ก่อน

---

## 🟠 2. Source code ถูกเสิร์ฟเป็น static file บน production (HIGH)

**หลักฐาน (ยืนยันจริงบน production):**
```
GET /server.py                       → HTTP 200, 65,939 bytes (โค้ดเต็ม)
GET /sync_portfolio_to_supabase.py   → HTTP 200
GET /init_db.py                      → HTTP 200
GET /deploy_report.py                → HTTP 200
```
Vercel เสิร์ฟทุกไฟล์ใน root directory (`Genie/my_first_website`) เป็น static asset โดยอัตโนมัติ ตอนนี้มีไฟล์ `.py` ที่ commit เข้า git ถึง **24 ไฟล์** ที่หลุดออกไปแบบนี้

**ผลกระทบ:** ผู้โจมตีอ่าน logic ทั้งหมด รู้โครงสร้าง DB, รู้ชื่อ endpoint ภายใน, และได้ SEC API keys (ดูข้อ 3) ไปฟรีๆ

**วิธีแก้ (ทำได้วันนี้):** สร้าง `.vercelignore` กันไฟล์ที่ไม่ควร deploy ออกไป — เหลือแค่ `index.html`, `app.js`, asset ที่ frontend ใช้, และ `api/`
```
# .vercelignore
*.py
!api/*.py
*.db
notes/
research/
```
> ⚠️ ต้องยืนยันว่า serverless function ยังทำงาน — `api/index.py` ต้องไม่ถูก ignore ตัวอย่างข้างบนใช้ `!api/*.py` กันไว้แล้ว ต้องทดสอบ deploy บน preview ก่อน promote

---

## 🟠 3. SEC API keys ฝังใน source เป็น fallback (HIGH)

**หลักฐาน:** `api/index.py:28-29` และ `server.py:12-13`
```python
SEC_FACTSHEET_KEY  = os.environ.get('SEC_FACTSHEET_KEY',  'eb52da4e…<redacted>')
SEC_DAILY_INFO_KEY = os.environ.get('SEC_DAILY_INFO_KEY', '38a6644d…<redacted>')
```
keys เหล่านี้ commit อยู่ใน git และหลุดออกทางข้อ 2 ด้วย

**วิธีแก้:**
1. เปลี่ยน (rotate) keys ทั้งสองที่พอร์ทัล SEC — ของเดิมถือว่ารั่วแล้ว
2. เอาค่า default ออก ให้ raise error ถ้าไม่มี env var แทน
3. ตั้ง env var จริงบน Vercel (`SEC_FACTSHEET_KEY`, `SEC_DAILY_INFO_KEY`)

---

## 🟡 4. Stored XSS ผ่าน innerHTML + marked.parse (MEDIUM)

**หลักฐาน:** `app.js` ใช้ `innerHTML` กับข้อมูลจาก DB โดยไม่ escape หลายจุด เช่น ชื่อบริษัท/พอร์ต (บรรทัด 215, 260, 557) และที่หนักสุดคือเนื้อ research report:
```js
// app.js:1529
reportContainer.innerHTML = marked.parse(rawText);   // ไม่มี DOMPurify
```
`marked` เวอร์ชันปัจจุบันไม่ sanitize ให้อัตโนมัติ ถ้า `rawText` มี `<img src=x onerror=…>` จะรันได้

**ทำไมถึงเป็นความเสี่ยงจริง:** พอเปิด multi-user (ข้อ 1) ผู้ใช้ B ใส่ report ที่ฝัง script → ผู้ใช้ A เปิดอ่าน → script รันในเซสชันของ A

**วิธีแก้ (วันที่ 3):** เพิ่ม DOMPurify ครอบ output ของ `marked.parse` และเปลี่ยนจุดที่ interpolate ข้อมูล user เข้า template string ให้ใช้ `textContent` หรือ escape ก่อน

---

## 🟡 5. ปิดการตรวจ SSL certificate ตอนต่อ Postgres (MEDIUM)

**หลักฐาน:** `api/index.py:48-50`
```python
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
```
เปิดช่องให้ MITM ดักการเชื่อมต่อระหว่างแอปกับ Supabase ได้

**วิธีแก้ (วันที่ 3):** ใช้ CA bundle ของ Supabase แล้วเปิด verify กลับ ถ้า pg8000 มีปัญหาเรื่อง cert ให้โหลด root cert ของ Supabase มาชี้แทนการปิดทั้งหมด

---

## 🟢 6. Error message leak (LOW)

ทุก endpoint ทำ `return jsonify({"error": str(e)}), 500` — ส่ง exception ดิบกลับไป client เผยโครงสร้างภายใน/ข้อความ DB **แก้:** log ฝั่ง server, ส่ง generic message กลับ client

## 🟢 7. ไม่มี rate limiting / CSRF / security headers (LOW)

ยังไม่มี rate limit (เสี่ยง abuse endpoint ที่ยิง Yahoo/SEC), ไม่มี security headers (CSP, HSTS ฯลฯ) **แก้:** ทำหลัง Auth เพราะบางส่วนผูกกับ session

---

## สิ่งที่ "ดีอยู่แล้ว" (ไม่ต้องแก้)

- ✅ SQL ใช้ parameterized query (`?` / `%s`) ทุกจุด — **ไม่พบช่องโหว่ SQL injection**
- ✅ `.env`, `.env.local`, `portfolio.db` อยู่ใน `.gitignore` และยืนยันแล้วว่า **ไม่หลุด** บน production (ทุกตัวได้ HTTP 404)
- ✅ Input validation พื้นฐานมี (เช็ค required fields, แปลง type) ครบพอสมควร

---

## ลำดับการแก้ที่แนะนำ

1. **วันนี้เลย (เร็ว, ได้ผลสูง):** ข้อ 2 + ข้อ 3 — สร้าง `.vercelignore`, rotate keys, เอา default ออก
2. **วันที่ 2:** ข้อ 1 — Auth + RLS (งานใหญ่ ตาม spec)
3. **วันที่ 3:** ข้อ 4, 5, 6 — XSS, SSL, error handling พร้อมกับ test suite
4. **หลัง Auth:** ข้อ 7 — rate limit + headers
