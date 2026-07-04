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

### T1. ~~Rotate SEC API keys~~ ✅ เสร็จ (2026-07-04) — แต่เจอปัญหาใหญ่กว่า ดู T1-b
Rotate key สำเร็จแล้ว (`SEC_FACTSHEET_KEY`, `SEC_DAILY_INFO_KEY` ตั้งบน Vercel production ใหม่) แต่ NAV ยังไม่ขึ้น

### T1-b. 🔴 CRITICAL: Migrate ไป Thai SEC Open API ใหม่ (`api.sec.or.th` ถูกปิดแล้ว)
**สาเหตุที่แท้จริง (เจอผ่าน Vercel logs หลัง rotate key):** `api.sec.or.th` (host เดิมที่ endpoint `FundDailyInfo`/`FundFactsheet` ใช้อยู่) **ถูก ก.ล.ต. ปิดให้บริการทั้งระบบแล้ว** — ไม่เกี่ยวกับคีย์ผิดหรือหมดอายุ ทุก request คืน:
```
HTTP 503: ยุติการให้บริการ API เดิม โดยขอให้ผู้ใช้งานดำเนินการเปลี่ยนไปใช้งาน
API เวอร์ชันใหม่ได้ที่ https://secopendata.sec.or.th
```
ชื่อกองทุนที่ยังขึ้นในแอปได้เพราะอ่านจากตาราง `thai_funds` ที่เคย sync เก็บไว้ก่อนหน้านี้ (ข้อมูลเก่า) — **NAV สดใช้ไม่ได้เลยจนกว่าจะ migrate**

**ที่ลองแล้ว:** เข้า `https://secopendata.sec.or.th` ทั้งผ่าน WebFetch และ curl — **โดน WAF บล็อกจาก server-side/automated request** เข้าได้เฉพาะ browser จริง ต้องให้คนเปิดดูเอง

**Mapping ที่ยืนยันแล้ว (จากหน้า "Fund API Mapping (Old vs New)" บน secopendata.sec.or.th + ทดสอบ endpoint จริง):**

| เก่า (`api.sec.or.th`) | ใหม่ (`api.sec.or.th`) | หมายเหตุ |
|---|---|---|
| `/FundDailyInfo/{proj_id}/dailynav/{nav_date}` | `/v2/fund/daily-info/nav` | ยืนยันด้วย curl จริง — ตอบ 401 (มีอยู่จริง ไม่ใช่ 503) query param รูปแบบใหม่ (ไม่ใช่ path param) แต่ยังไม่รู้ชื่อ param แน่ชัด |
| `/FundDailyInfo/{proj_id}/dividend` | `/v2/fund/daily-info/dividend-history` | |
| `/FundFactsheet/fund/amc` | `/v2/fund/general-info/amcs` | ใช้แทนใน `sync_thai_funds()` |
| `/FundFactsheet/fund/amc/{unique_id}` | `/v2/fund/general-info/profiles` | ใช้แทนใน `sync_thai_funds()` |

**สิ่งที่ "ไม่ต้องเปลี่ยน":**
- **Host เดิม** `api.sec.or.th` — แค่เติม `/v2/` prefix ไม่ใช่ domain ใหม่ (`secopendata.sec.or.th` เป็นแค่หน้า "เอกสาร" ไม่ใช่ API endpoint จริง — endpoint จริงยังอยู่ที่ `api.sec.or.th`)
- **Auth header เดิม** `Ocp-Apim-Subscription-Key` — ยืนยันแล้ว (ตอบ error message ต่างกันระหว่าง "missing" กับ "invalid" key ซึ่งพิสูจน์ว่า header ถูกต้อง)

**ที่ยังไม่รู้ (ต้องหาต่อ):**
1. ชื่อ query parameter ที่ `/v2/fund/daily-info/nav` ต้องการ (proj_id? nav_date? ชื่ออื่น?) — Azure APIM เช็ค subscription key ก่อนเช็ค param เสมอ เดาไม่ได้ถ้าไม่มีคีย์จริง ต้องดู endpoint docs หรือ "ลองยิงจริง" (Try it out) ในหน้า secopendata
2. คีย์ที่ rotate ไปแล้ว (`SEC_FACTSHEET_KEY`/`SEC_DAILY_INFO_KEY` บน Vercel) ใช้กับ v2 ได้เลยไหม หรือต้อง subscribe API product ใหม่แยกต่างหากในหน้า "เริ่มต้นใช้งาน" ของ secopendata — **ทดสอบเองได้โดยไม่ต้องเปิดเผยคีย์:**
   ```
   curl -s "https://api.sec.or.th/v2/fund/daily-info/nav" -H "Ocp-Apim-Subscription-Key: <คีย์จริง>"
   ```
   ถ้าตอบอย่างอื่นที่ไม่ใช่ "invalid subscription key" แปลว่าคีย์ใช้ได้แล้ว
3. โครงสร้าง response ใหม่ (โค้ดเดิมคาดหวัง field เช่น `last_val`, `proj_abbr_name` ฯลฯ — ต้องดู response จริงจาก v2 ถึงจะรู้ชื่อ field ใหม่)

**งานที่ต้องทำ (เมื่อรู้ param/response ครบ):**
1. แก้ `api/index.py`: เปลี่ยน URL จาก `/FundDailyInfo/...` → `/v2/fund/daily-info/nav`, จาก `/FundFactsheet/fund/amc...` → `/v2/fund/general-info/amcs` + `/profiles`, ปรับ query param และ parsing response ตาม schema ใหม่
2. Sync ข้อมูลกองทุนใหม่เข้า `thai_funds` ตาราง (ผ่าน `/api/thai-fund/sync` ที่แก้แล้ว)
**เสร็จเมื่อ:** `/api/thai-fund?code=…` คืน NAV จริงบน prod (ไม่ null)

**Diagnostic logging ที่เพิ่มไว้ (เก็บไว้ถาวร ไม่ต้องลบ):** `get_thai_fund()` มี `app.logger.warning(...)` log HTTP status/body จาก SEC API เวลา NAV lookup fail (ไม่ log ตัวคีย์) — ใช้ `npx vercel logs <deployment-url> --json --level warning` ดูได้เวลา debug ต่อ

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
