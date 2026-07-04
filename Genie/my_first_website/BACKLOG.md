# BACKLOG — Genie Investment

> เอกสารส่งไม้ต่อจาก 4-day sprint (Fable 5, ก.ค. 2026) — งานที่เหลือแตกเป็น task ย่อย
> เรียงตามลำดับความสำคัญ แต่ละข้อออกแบบให้หยิบไปทำได้จบในตัว (self-contained)
>
> **กติกาก่อนแตะโค้ด (ทุก task):**
> 1. อ่าน `CLAUDE.md` + `ARCHITECTURE_MULTIUSER.md` ก่อน
> 2. รันเทสต์ก่อนและหลังแก้: `DATABASE_URL="" SEC_FACTSHEET_KEY="" python3 -m pytest tests/ -q` (ต้องผ่านครบ)
> 3. endpoint ใหม่ที่แตะข้อมูลผู้ใช้ ต้อง `@require_auth` + scope ด้วย `g.user_id` + เขียน isolation test เพิ่ม
> 4. ห้าม deploy `--sync`, ห้าม commit `.env`/`portfolio.db`/`backups/`

---

## P0 — รอเจ้าของทำ (Pop เท่านั้น)

### T1. ~~Rotate SEC API keys~~ ✅ เสร็จ (2026-07-04)
Rotate key สำเร็จ + subscribe API product ใหม่ชื่อ "Fund API" บน secopendata.sec.or.th (คนละ subscription จากของเดิม)

### T1-b. ~~Migrate ไป Thai SEC Open API v2~~ ✅ เสร็จ (2026-07-04) — NAV lookup ใช้งานได้แล้ว

**สรุปสิ่งที่เกิดขึ้น:** `api.sec.or.th` เวอร์ชันเก่าถูก ก.ล.ต. ปิดให้บริการทั้งระบบ (คืน HTTP 503 พร้อมข้อความ deprecation ชี้ไป `secopendata.sec.or.th` ซึ่งเป็นแค่**หน้าเอกสาร** ไม่ใช่ API endpoint จริง) ต้อง subscribe API product ใหม่ (คนละตัวจาก subscription เดิม แม้ host เดียวกัน) แล้วใช้ endpoint ใหม่

**Endpoint + parameter ที่ยืนยันแล้วด้วยการยิงจริง:**
```
GET https://api.sec.or.th/v2/fund/daily-info/nav
    ?proj_id=<proj_id>
    &start_nav_date=YYYY-MM-DD
    &end_nav_date=YYYY-MM-DD
Header: Ocp-Apim-Subscription-Key: <key>
```
⚠️ เอกสารบนเว็บมี 2 จุดขัดแย้งกันเอง — กล่อง NOTE บอกชื่อ param ว่า `nav_date_start`/`nav_date_end` (ผิด) ส่วนตาราง "Query parameters" จริงบอกว่า `start_nav_date`/`end_nav_date` (ถูก — ยืนยันด้วย curl จริงแล้ว) **ถ้าจะดู endpoint อื่นในเอกสารชุดนี้ เชื่อตาราง parameter ไม่ใช่กล่อง NOTE**

**Response shape:** `{"message","page_size","next_cursor","items":[{proj_id, unique_id, fund_class_name, nav_date, net_asset, last_val, sell_price, buy_price, sell_swap_price, buy_swap_price, last_upd_date}]}` — field `last_val` ชื่อเดิมเป๊ะ (parsing เดิมใช้ต่อได้)

**ข้อควรรู้:** proj_id เดียวอาจมีหลาย `fund_class_name` (share class) พร้อม NAV ต่างกัน (เช่น `ONE-UGERMF-A` vs `-P`) — endpoint ไม่รองรับกรองด้วยวันเดียว (ไม่มี `nav_date` เดี่ยวๆ ใช้ได้) ต้องขอเป็นช่วงวันที่แล้วเลือกวันล่าสุดเอง

**แก้แล้วใน `api/index.py` (`get_thai_fund()`):** เปลี่ยนจาก loop 7 วันยิงทีละวัน → ยิงครั้งเดียวขอช่วง 10 วันย้อนหลัง แล้วเลือก item ที่ `nav_date` ล่าสุดด้วย `max(items, key=lambda it: it['nav_date'])` — เทสต์ 24 ตัวผ่านหมด, ทดสอบยิงจริงกับ Pop's key แล้วได้ NAV ปัจจุบันถูกต้อง (deploy แล้ว)

**Diagnostic logging ที่เพิ่มไว้ (เก็บไว้ถาวร):** `get_thai_fund()` มี `app.logger.warning(...)` log HTTP status/body จาก SEC API เวลา lookup fail (ไม่ log ตัวคีย์) — ใช้ `npx vercel logs <deployment-url> --json --level warning` ดูได้เวลา debug ต่อ

### T1-c. `sync_thai_funds()` ยังใช้ endpoint เก่า (`/FundFactsheet/fund/amc...`) — ยังไม่แก้ (priority ต่ำกว่า)
ยังไม่ได้ migrate เพราะข้อมูล `thai_funds` ในเครื่องมีอยู่แล้ว (sync ไว้ก่อนหน้านี้) ใช้หาชื่อกองทุนได้ปกติ — sync ใหม่จะได้กองทุนที่เพิ่งเปิดใหม่/ข้อมูลล่าสุด แต่ไม่ block การใช้งานตอนนี้

**Mapping ที่รู้แล้ว (จากหน้า Fund API Mapping):**
| เก่า | ใหม่ |
|---|---|
| `/FundFactsheet/fund/amc` (รายชื่อ บลจ.) | `/v2/fund/general-info/amcs` |
| `/FundFactsheet/fund/amc/{unique_id}` (กองทุนใต้ บลจ.) | `/v2/fund/general-info/profiles` |

**งานที่ต้องทำ:** หา query parameter ที่ endpoint ใหม่ทั้งสองต้องการ (ใช้วิธีเดียวกับ T1-b — เปิด endpoint docs ในหน้า secopendata.sec.or.th ดูตาราง "Query parameters" ตรงๆ อย่าเชื่อกล่อง NOTE) แล้วแก้ `sync_thai_funds()` ให้เรียก v2 + ปรับ parsing ตาม response schema ใหม่
**เสร็จเมื่อ:** `POST /api/thai-fund/sync` คืนจำนวนกองทุนที่ sync ได้จริงจาก v2 (ไม่ใช่ error 503)

---

## P1 — ความทนทาน (โมเดลไหนก็ทำได้ ถ้าทำตามกติกา)

### T2. Scheduled backup อัตโนมัติ (roadmap ข้อ 4 — ข้อเดียวที่ยังไม่เสร็จ)
ตอนนี้มี backup manual (`backups/prod_backup_*.json` — สร้างโดย script ตอน cutover)
- ทางเลือก ก: Supabase Pro มี daily backup ในตัว (จ่ายเงิน ไม่ต้องเขียนโค้ด)
- ทางเลือก ข: เขียน `backup_prod.py` (ลอก logic dump จาก cutover ได้) + ตั้ง cron/Vercel cron ยิงรายวัน เก็บ 7 ชุดล่าสุด
**เสร็จเมื่อ:** มี backup ใหม่เกิดขึ้นเองอย่างน้อยวันละครั้ง

### T3. Connection cleanup ใน error path
ทุก endpoint เปิด `conn` แล้วถ้า exception ก่อน `conn.close()` จะรั่ว (serverless อายุสั้นเลยยังไม่เจ็บ)
แก้เป็น pattern เดียว: `try/finally` หรือ context manager ครอบ `get_db_connection()`
**เสร็จเมื่อ:** ไม่มี endpoint ไหนที่ conn ไม่ถูกปิดใน error path + เทสต์เดิมผ่านครบ

### T4. `SELECT MAX(id)` → `RETURNING id`
จุด INSERT บน Postgres ใช้ `SELECT MAX(id)` หา id ล่าสุด — race ได้ถ้าสอง request ชนกัน
แก้เป็น `INSERT … RETURNING id` (Postgres) / คง `lastrowid` (SQLite) ใน helper เดียว
**เสร็จเมื่อ:** ไม่มี `SELECT MAX(id)` เหลือใน `api/index.py`

### T5. Frontend แสดง error 401/429 ให้เป็นมิตร
ตอนนี้ 429 (rate limit) กับ 401 กลางเซสชัน แสดงเป็น error ดิบใน alert/console
เพิ่มการจัดการใน `app.js`: 429 → toast "ลองใหม่ในอีกสักครู่", 401 → auth.js จัดการแล้ว (แค่เช็คว่าไม่มี alert ซ้อน)
**เสร็จเมื่อ:** ยิงเกิน rate limit แล้วเห็นข้อความอ่านรู้เรื่อง ไม่ใช่ JSON ดิบ

---

## P2 — โครงสร้าง (ควรใช้โมเดลกลางขึ้นไป เช่น Sonnet)

### T6. แตก `app.js` (~3,100 บรรทัด) เป็นโมดูล
วิธีปลอดภัย (ไม่มี bundler — ใช้ classic scripts เรียงลำดับ):
1. แตกเป็นไฟล์ต่อเนื่องตามลำดับเดิมเป๊ะ (sequential split) — ห้ามย้ายลำดับโค้ด: `js/01_state.js` (ตัวแปร global + helpers), `js/02_dashboard.js`, `js/03_reports.js`, `js/04_transactions.js`, `js/05_ingest.js`, `js/06_modals.js`, `js/07_main.js` (DOMContentLoaded ท้ายไฟล์)
2. แทน `<script src="app.js?v=16">` ด้วย script tags เรียงลำดับ 01→07
3. ตรวจ: `node --check` ทุกไฟล์ + `cat js/*.js | diff - app.js` ต้องตรงกัน (พิสูจน์ว่าแค่แบ่ง ไม่ได้แก้) + เปิดเว็บคลิกครบทุก tab
**เสร็จเมื่อ:** ทุกหน้า (dashboard/transactions/research/team) ทำงานเหมือนเดิม + ไฟล์ใหญ่สุดไม่เกิน ~700 บรรทัด

### T7. ลด innerHTML ที่ interpolate ข้อมูล user
`app.js` มี ~40 จุดที่ต่อ string ข้อมูล DB เข้า innerHTML (XSS จุดใหญ่สุดคือ report — แก้ด้วย DOMPurify แล้ว)
ไล่แก้จุดที่เหลือ: ชื่อพอร์ต/บริษัท/หมวด ให้ escape ก่อน หรือใช้ `textContent`
ทำหลัง T6 จะง่ายกว่า (ไฟล์เล็กลง) **เสร็จเมื่อ:** ตั้งชื่อพอร์ตเป็น `<img src=x onerror=alert(1)>` แล้วไม่มี alert

### T8. เปิด SSL verify-ca กับ Supabase
โหลด CA cert: Supabase Dashboard → Project Settings → Database → SSL → Download certificate
ตั้งเนื้อ PEM เป็น env `SUPABASE_CA_CERT` บน Vercel (โค้ดรองรับแล้ว — ดู `get_db_connection()`)
**เสร็จเมื่อ:** prod ต่อ DB ได้ปกติโดย `verify_mode=CERT_REQUIRED`

### T9-b. Security headers บน static assets + บทเรียน incident 2026-07-04
**Incident จริง (วินิจฉัยครั้งแรกผิด):** API ล่ม 2 รอบในวัน ship ไม่ใช่เพราะ `headers` block —
สาเหตุจริงคือ **Vercel GitHub integration: build ที่ trigger จาก `git push` ไม่มี Python lambda เลย**
(พิสูจน์ด้วย `vercel inspect`: git-triggered deployments ไม่มี λ, CLI deployments มี `λ api/index`)
ทุกครั้งที่ push → git build แย่ง production alias → `/api/*` ทั้งหมด 404
**แก้ถาวรแล้ว:** `vercel.json` มี `"git": {"deploymentEnabled": false}` — โปรเจกต์นี้ **deploy ทาง CLI เท่านั้น** (`deploy.sh`)
⚠️ ห้ามลบบรรทัดนี้ / ถ้าอยากกลับมาใช้ git deploy ต้องแก้เรื่อง function หายใน git build ให้ได้ก่อน (ทดสอบบน preview)
**งานที่เหลือของ task นี้:** เพิ่ม security headers ให้ static assets — `headers` block ใน vercel.json น่าจะบริสุทธิ์ (ยังไม่ยืนยัน 100%) ให้ลองใหม่บน **preview deploy** แล้วเช็ค `/api/auth-config` ก่อน promote เสมอ
**เสร็จเมื่อ:** `curl -sI /` เห็น nosniff/HSTS โดย `/api/*` ยังทำงาน

### T9. Vercel WAF rate limiting (ทดแทน in-memory limiter)
Limiter ปัจจุบัน per-instance (serverless ไม่แชร์ state) — ตั้ง WAF rule บน Vercel dashboard:
rate limit `/api/*` ต่อ IP แล้วลด/ถอด in-memory limiter ออกได้
**เสร็จเมื่อ:** มี WAF rule ทำงานจริง (ทดสอบด้วย curl ยิงรัว)

---

## P3 — ฟีเจอร์ multi-user เพิ่มเติม (หลังมีผู้ใช้จริง)

### T10. หน้า invite/จัดการผู้ใช้ — ตอนนี้เชิญได้ทาง Supabase dashboard เท่านั้น (พอสำหรับ invite-only ช่วงแรก)
### T11. Password reset flow — GoTrue มี `/recover` endpoint; ต้องทำหน้า UI + email template
### T12. แยก `thai_funds` sync ออกจาก request path — ตอนนี้ sync ยิงจาก endpoint (ช้า/timeout ได้) → ย้ายเป็น Vercel cron
### T13. Audit log — ตาราง `audit_log` เก็บ user_id + action + timestamp สำหรับ write operations

---

## บริบทที่ต้องรู้ (สำหรับโมเดลที่มาทำต่อ)

- **สถาปัตยกรรม auth:** app-layer scoping เป็นเกราะหลัก (Flask ต่อ DB เป็น owner ที่ BYPASSRLS) — RLS เป็น backstop เท่านั้น อย่าเข้าใจผิดว่า RLS คุ้มครองอยู่แล้วเลยไม่ scope query
- **Token เป็น ES256** verify ผ่าน JWKS อัตโนมัติ — ไม่มี secret ฝั่งเรา / HS256 path มีไว้ให้เทสต์
- **เทสต์คือสัญญา:** `test_auth_isolation.py` คือตัวพิสูจน์ว่า user แยกกันจริง ถ้าแก้แล้วแดง = หยุดทันที
- **Deploy:** `cd ~/Desktop && npx vercel --prod` (จาก git root เท่านั้น) — "ship it" = commit + deploy + push
- ประวัติเต็มของ sprint อยู่ใน memory ของ Claude (`project_fable_sprint.md`) + `SECURITY_FINDINGS.md`
