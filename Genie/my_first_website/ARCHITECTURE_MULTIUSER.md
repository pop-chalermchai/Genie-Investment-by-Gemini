# Architecture Spec — Multi-User (Supabase Auth + RLS)

> ร่างโดย Fable 5 — 2026-07-04 (วันที่ 1) · Auth provider ที่เลือก: **Supabase Auth**
> เอกสารนี้คือพิมพ์เขียวสำหรับงานวันที่ 2 (Auth+RLS) และเป็นตัวอ้างอิงให้โมเดลรุ่นถัดไปทำต่อ
> อ่านคู่กับ `SECURITY_FINDINGS.md` (ข้อ 1 CRITICAL คือที่มาของ spec นี้)

---

## 0. หัวใจที่ต้องเข้าใจก่อน (อ่านให้จบก่อนลงมือ)

**RLS เพียงอย่างเดียว "ไม่" ปกป้องแอปนี้** เพราะ backend (Flask + pg8000) ตอนนี้ต่อ Postgres ด้วย `DATABASE_URL` ในฐานะ role เจ้าของฐานข้อมูล (`postgres`) ซึ่งมีสิทธิ์ **BYPASSRLS** — RLS policy จะถูกข้ามทั้งหมด

พูดง่ายๆ: ต่อให้เราเขียน RLS policy สวยแค่ไหน ถ้า Flask ยังต่อด้วย connection เดิม ทุก query จะเห็นข้อมูลทุก user อยู่ดี **นี่คือกับดักที่พังเงียบที่สุด** — policy ดูเหมือนทำงาน แต่จริงๆ ไม่ทำอะไรเลย

ดังนั้นสถาปัตยกรรมนี้ต้องมี **สองชั้น**:
1. **Application-layer ownership (ชั้นหลัก)** — ทุก query scope ด้วย `user_id` ของผู้ใช้ที่ล็อกอิน โดยดึง `user_id` จาก Supabase JWT ที่ verify แล้ว
2. **RLS (ชั้นกันพลาด/defense-in-depth)** — เปิดไว้ทุกตาราง เผื่อวันหน้ามี query ที่ลืม scope หรือมีการต่อผ่าน role อื่น

> ⚠️ **จุดตัดสินใจ #1 (รอ Sensei เลือก):** จะเอาชั้นไหนเป็นหลัก? ดูหัวข้อ 6 — ผมแนะนำ "App-layer เป็นหลัก + RLS เป็น backstop" เพราะ backend เป็น Flask custom ไม่ได้ใช้ supabase-js

---

## 1. โมเดลความเป็นเจ้าของข้อมูล (ownership model)

ตารางปัจจุบัน 6 ตาราง แบ่งเป็น 3 กลุ่ม:

| ตาราง | เจ้าของ | วิธีผูก user | หมายเหตุ |
|-------|---------|--------------|----------|
| `portfolios` | ผู้ใช้ | เพิ่มคอลัมน์ `user_id` ตรงๆ | ราก (root) ของความเป็นเจ้าของ |
| `assets` | ผู้ใช้ (ทางอ้อม) | ผ่าน `portfolio_id → portfolios.user_id` | ไม่ต้องมี user_id เอง (ดู decision #2) |
| `transactions` | ผู้ใช้ (ทางอ้อม) | ผ่าน `asset_id → assets → portfolios.user_id` | ลึก 2 ชั้น |
| `research_reports` | ผู้ใช้ | เพิ่มคอลัมน์ `user_id` ตรงๆ | report เป็นของแต่ละคน |
| `categories` | ผู้ใช้ (แนะนำ) | เพิ่มคอลัมน์ `user_id` | ดู decision #3 — global หรือ per-user |
| `thai_funds` | **ส่วนกลาง (shared)** | ไม่มี user_id | reference data จาก SEC ทุกคนอ่านร่วมกัน เขียนได้เฉพาะ sync |

**หลักการ:** `portfolios` และ `research_reports` คือจุดที่ผูก `user_id` โดยตรง ส่วน `assets`/`transactions` สืบทอดความเป็นเจ้าของผ่าน foreign key — ทำให้ไม่มีข้อมูลกำพร้าและ query ตรงไปตรงมา

---

## 2. Schema changes (SQL)

```sql
-- 2.1 เพิ่ม user_id (อ้างอิง auth.users ของ Supabase)
ALTER TABLE portfolios       ADD COLUMN user_id UUID REFERENCES auth.users(id);
ALTER TABLE research_reports ADD COLUMN user_id UUID REFERENCES auth.users(id);
ALTER TABLE categories       ADD COLUMN user_id UUID REFERENCES auth.users(id);  -- ถ้าเลือก per-user

-- 2.2 index สำหรับ query ที่ scope ด้วย user_id (สำคัญต่อ performance)
CREATE INDEX idx_portfolios_user  ON portfolios(user_id);
CREATE INDEX idx_reports_user     ON research_reports(user_id);
CREATE INDEX idx_categories_user  ON categories(user_id);

-- 2.3 backfill: ยกข้อมูลเดิมทั้งหมดให้เจ้าของคนแรก (ดูหัวข้อ 4)
-- 2.4 หลัง backfill แล้วค่อยบังคับ NOT NULL:
-- ALTER TABLE portfolios ALTER COLUMN user_id SET NOT NULL;  -- ทำหลัง backfill เท่านั้น
```

`assets` และ `transactions` **ไม่ต้อง** เพิ่ม `user_id` (สืบทอดผ่าน FK) — เว้นแต่จะเลือก decision #2 แบบ denormalize เพื่อความเร็ว

---

## 3. RLS policies (ชั้นกันพลาด)

```sql
-- เปิด RLS ทุกตารางที่เป็นข้อมูลผู้ใช้
ALTER TABLE portfolios       ENABLE ROW LEVEL SECURITY;
ALTER TABLE assets           ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions     ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories       ENABLE ROW LEVEL SECURITY;

-- portfolios: เห็น/แก้ได้เฉพาะของตัวเอง
CREATE POLICY portfolios_owner ON portfolios
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- research_reports + categories: เหมือนกัน
CREATE POLICY reports_owner ON research_reports
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE POLICY categories_owner ON categories
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- assets: สืบทอดผ่าน portfolio
CREATE POLICY assets_owner ON assets
    USING (portfolio_id IN (SELECT id FROM portfolios WHERE user_id = auth.uid()))
    WITH CHECK (portfolio_id IN (SELECT id FROM portfolios WHERE user_id = auth.uid()));

-- transactions: สืบทอดลึก 2 ชั้น
CREATE POLICY transactions_owner ON transactions
    USING (asset_id IN (
        SELECT a.id FROM assets a JOIN portfolios p ON a.portfolio_id = p.id
        WHERE p.user_id = auth.uid()))
    WITH CHECK (asset_id IN (
        SELECT a.id FROM assets a JOIN portfolios p ON a.portfolio_id = p.id
        WHERE p.user_id = auth.uid()));

-- thai_funds: reference data — อ่านได้ทุกคนที่ล็อกอิน, เขียนเฉพาะ service role
ALTER TABLE thai_funds ENABLE ROW LEVEL SECURITY;
CREATE POLICY thai_funds_read ON thai_funds FOR SELECT USING (auth.role() = 'authenticated');
-- ไม่มี policy INSERT/UPDATE → เขียนได้เฉพาะ service_role (ซึ่ง bypass RLS)
```

**หมายเหตุสำคัญ:** policy เหล่านี้จะ "มีผลจริง" ก็ต่อเมื่อ query รันในฐานะ role ที่เคารพ RLS + มี JWT ที่ทำให้ `auth.uid()` คืนค่าถูก (ดูหัวข้อ 6)

---

## 4. Migration path จาก single-user → multi-user

ข้อมูลเดิมทั้งหมดเป็นของ Sensei (chanruthaikul@gmail.com) ต้องยกให้เจ้าของก่อนบังคับ NOT NULL:

1. สร้าง auth user แรกผ่าน Supabase Auth (สมัครด้วยอีเมล chanruthaikul@gmail.com) → ได้ `auth.users.id` (UUID)
2. Backfill:
   ```sql
   UPDATE portfolios       SET user_id = '<OWNER_UUID>' WHERE user_id IS NULL;
   UPDATE research_reports SET user_id = '<OWNER_UUID>' WHERE user_id IS NULL;
   UPDATE categories       SET user_id = '<OWNER_UUID>' WHERE user_id IS NULL;
   ```
3. ตรวจว่าไม่มี row ไหน user_id เป็น NULL แล้วค่อย `SET NOT NULL`
4. เปิด RLS (หัวข้อ 3) **หลัง** backfill เสร็จ — ถ้าเปิดก่อน ข้อมูลเดิมจะหายจากสายตาทันที

> ⚠️ ทำบน branch/preview + backup ก่อน (Supabase point-in-time หรือ `sync_portfolio_to_supabase.py --pull`) เพราะ migration นี้ย้อนยาก

---

## 5. Backend changes (Flask `api/index.py`)

งานหลักฝั่ง backend คือ "รู้ว่าใครกำลังเรียก" แล้ว scope ทุก query:

1. **Verify JWT** — ทุก request อ่าน `Authorization: Bearer <token>` แล้ว verify กับ Supabase JWT secret (env var `SUPABASE_JWT_SECRET`) ดึง `sub` (= user_id) ออกมา ทำเป็น decorator `@require_auth` ครอบทุก route ที่แตะข้อมูลผู้ใช้
2. **Scope ทุก query** — เพิ่มเงื่อนไข `user_id` เข้าไปในทุก SELECT/INSERT/UPDATE/DELETE:
   - `portfolios` / `research_reports` / `categories`: `WHERE user_id = %s`
   - `assets`: join กลับไป portfolios ของ user
   - `transactions`: join 2 ชั้น
   - ตอน INSERT portfolio/report/category ต้องเซ็ต `user_id` ของผู้เรียกเสมอ
3. **จุดที่ต้องระวังเป็นพิเศษ** (จาก audit วันนี้):
   - `DELETE /api/portfolio` (บรรทัด ~558) — ต้องเช็คว่า portfolio เป็นของ user ก่อนลบเป็นทอดๆ
   - `PUT /api/asset-adjustment` (บรรทัด ~516) — รับ `portfolioId` ตรงจาก client → **ต้อง** verify ว่า portfolio นั้นเป็นของ user (ตอนนี้เชื่อ client ทันที = IDOR)
   - `POST /api/transfer` — เช็คว่าทั้ง source และ dest เป็นของ user เดียวกัน
   - `PUT/DELETE /api/transaction?id=` — เช็คว่า transaction สืบไปถึง user นี้จริง
4. Endpoint สาธารณะที่ **ไม่ต้อง** auth: `/api/stock`, `/api/stock/chart` (ข้อมูลตลาดจาก Yahoo, ไม่มีข้อมูลผู้ใช้) — แต่ควรใส่ rate limit

---

## 6. จุดตัดสินใจที่รอ Sensei เลือก (ก่อนเริ่มวันที่ 2)

**Decision #1 — ชั้นบังคับสิทธิ์หลัก**
- **(แนะนำ) App-layer เป็นหลัก + RLS เป็น backstop** — verify JWT ใน Flask แล้ว scope ทุก query ด้วย user_id, เปิด RLS ไว้กันพลาด · ข้อดี: ควบคุมชัด แก้ทีละ endpoint ได้, ไม่ต้องรื้อ connection layer · ข้อเสีย: ต้องแก้ query เยอะ (~30 endpoint) และวินัยในการ scope สำคัญมาก → นี่คือเหตุผลที่ต้องมี test suite (วันที่ 3)
- **ทางเลือก: RLS เป็นหลัก** — เปลี่ยน backend ให้ต่อ Postgres ด้วย role ที่เคารพ RLS แล้ว `SET LOCAL request.jwt.claims` ต่อ request · ข้อดี: policy เดียวคุมหมด · ข้อเสีย: ต้องรื้อ `get_db_connection()` และจัดการ role/claims เอง เสี่ยงพลาดถ้าตั้งไม่ครบ

**Decision #2 — `assets`/`transactions` เก็บ `user_id` ซ้ำไหม**
- ไม่เก็บ (แนะนำ) — สืบผ่าน FK, schema สะอาด, query ซับซ้อนขึ้นนิด
- เก็บซ้ำ (denormalize) — query เร็ว/ง่ายขึ้น แต่ต้อง sync ให้ตรงเสมอ

**Decision #3 — `categories` แบบไหน**
- Per-user (แนะนำ) — แต่ละคนมีหมวดหมู่ของตัวเอง, seed default (Stocks/Provident Fund/Crypto) ให้ user ใหม่
- Global — หมวดหมู่ใช้ร่วมกันทุกคน (ง่ายกว่า แต่ผู้ใช้แก้ของกันได้)

**Decision #4 — การสมัครสมาชิก**
- เปิดสมัครเสรี (email/password หรือ OAuth Google) หรือ invite-only ช่วงแรก?

---

## 7. ลำดับงานวันที่ 2 (เมื่อ decision ครบ)

1. ตั้ง Supabase Auth (เปิด provider, ตั้ง redirect URL)
2. รัน schema changes (หัวข้อ 2) บน preview/branch DB ก่อน
3. Backfill + migration (หัวข้อ 4)
4. เพิ่ม `@require_auth` + JWT verify ใน Flask
5. Scope ทุก query (หัวข้อ 5) — ไล่ทีละ endpoint
6. เปิด RLS (หัวข้อ 3)
7. เพิ่มหน้า login/signup ฝั่ง frontend (`app.js` + Supabase JS client)
8. **Test:** พิสูจน์ว่า user A มองไม่เห็น/แก้ไม่ได้ข้อมูล user B (ตัวชี้วัดความสำเร็จของทั้งงาน)
