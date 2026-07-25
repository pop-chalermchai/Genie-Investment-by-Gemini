---
name: check-prod
description: Verify production Genie Investment app is healthy — logs in with the smoke-test user and tests key API endpoints end-to-end.
---

# Check Production

Smoke-test the live production app at https://genieports.com

The app enforces Supabase Auth on every `/api/*` route, so the check logs in
as a dedicated smoke-test user first.

## Run

```bash
cd ~/Desktop/Genie/my_first_website && python3 check_prod.py
```

## What it checks

1. `/api/auth-config` reachable and reports `authRequired: true`
2. Unauthenticated `/api/init-data` is rejected with 401 (auth enforced)
3. Login via Supabase password grant succeeds
4. `/api/init-data` returns holdings + portfolios lists
5. `/api/holdings` runs and rows include `manualPrice` (schema check)
6. `/api/thai-fund?code=ABFTH` returns a NAV (SEC API path)
7. `/api/stock?ticker=EURUSD=X` returns a price (Yahoo proxy / FX path)

Exit code 0 and `7/7 checks passed` = healthy.

## Setup (one-time)

The script reads credentials from `my_first_website/.env` (gitignored):

```
CHECK_PROD_EMAIL=<smoke-test user email>
CHECK_PROD_PASSWORD=<smoke-test user password>
```

Create the user in Supabase Dashboard → Authentication → Users → Add user
(signup is invite-only). A fresh user with no data is fine — checks validate
status and response shape, not row counts. Do NOT use a real account.

## If unhealthy

- Exit code 2 = credentials missing from `.env` (setup above)
- Login failure = check the smoke-test user exists / password in `.env`
- Check Vercel deployment logs: `npx vercel logs <url>`
- Check if latest deploy succeeded: `cd ~/Desktop && npx vercel ls`
