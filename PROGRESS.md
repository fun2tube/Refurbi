# Refurbi - Build Progress

## Status
- Tasks done: 7 / 37 (19%) (incl. TP1 preview task)
- Current milestone: 1 - Inventory core
- Next task: T08
- Preview URL: (not yet recorded - founder: add a line `Preview URL: ...` after following docs/PREVIEW_SETUP.md)
- Blockers: T02 (push lacks `workflow` scope)

## Founder inputs needed (not blocking yet)
- **ACTION (3 min): follow docs/PREVIEW_SETUP.md to get your preview link**
- Set real JWT_SECRET, SUPER_ADMIN_EMAIL/PASSWORD in the deploy env, then run `python -m app.seed` (T05)
- GSTIN, legal name, registered address (T16 invoices)
- CA sign-off on GST margin scheme (Rule 32(5)) and ITC policy
- Product photos/descriptions/spec text for the catalogue (T06 seeds only model names, years, 5G flag, RAM/storage configs - please verify; no prices/images invented)
- Grade definitions A/B/C and warranty months per grade
- Counter list: names, addresses, owners, commission terms
- Later: domain, hosting, Razorpay, WhatsApp Business, SMS DLT, Google Maps accounts

## Log

### 2026-11-09 - Planning
- Done: market research, CTO decisions, 36-task roadmap, agent instructions.
- Next: T01

### 2026-11-09T00:00Z - T01 Monorepo skeleton (T02 CI blocked)
- Done: apps/web (Next.js 15.5, TS, Tailwind 4, App Router, ESLint); services/api (FastAPI, uv, ruff, pytest, /health); docker-compose.yml (Postgres 16 + api); .env.example files; .gitignore; README run instructions; CI workflow drafted at ci/ci.yml (api ruff+pytest with Postgres 16 service; web lint+tsc+build).
- Tests: API 1 passed; ruff clean; web lint, tsc, build pass locally. 
- Decisions made: pushed directly to main (accepted). Used system Python 3.12 via UV_PYTHON locally (uv download of 3.12 is slow in sandbox). Web uses npm (package-lock committed). Docker daemon not run in sandbox; compose file only syntax-checked.
- Blockers / founder inputs needed: T02 BLOCKED [!]: push of .github/workflows/* was rejected ("OAuth App ... without `workflow` scope"). Workflow parked at ci/ci.yml. Founder: grant the workflow scope / GitHub App `workflows` permission, or manually `git mv ci/ci.yml .github/workflows/ci.yml`.
- Next: T03

### 2026-11-10T02:45Z - T03 API core
- Done: app/core (settings via pydantic-settings, SQLAlchemy 2 engine/session dependency + naming-convention Base, error envelope `{"error":{code,message,details?,request_id?}}` with AppError/NotFound/Conflict/Unauthorized/Forbidden + handlers for HTTP/validation/unhandled (no internals leaked), pagination helper (PageDep, paginate, Page envelope, page_size capped), JSON structured logging with x-request-id middleware); Alembic configured (migrations/env.py reads DATABASE_URL, empty 0001 baseline); app/models.py registry for autogenerate; /health kept.
- Tests: API 8 passed; ruff check + format clean. `alembic upgrade head` / `alembic check` verified against a real local Postgres 16 (not docker). Web untouched.
- Decisions made: Pagination is page/page_size (default 20, max 100). Core tests use in-memory SQLite for the helper; Postgres-specific behaviour will be tested once CI (T02) provides a service. Ignored ruff UP046/UP047 (TypeVar style kept). Sandbox default python is 3.11, ran with UV_PYTHON=/usr/bin/python3.12.
- Blockers / founder inputs needed: T02 still blocked (workflow scope).
- Next: T04

### 2026-11-10T02:50Z - T04 Design system in web
- Done: tokens (Midnight/Porcelain/Silver/Refurbi Green) in globals.css + Tailwind theme; Inter + Manrope via next/font; components/ui: Button, Input, Select, Card, GradeBadge, Price (tabular, paise -> Indian-grouped rupees via lib/money.ts); StoreShell/AdminShell/PartnerShell with route-group layouts (app/(store), app/admin, app/partner); placeholder demo home (real homepage is T21); removed create-next-app boilerplate assets. Added vitest + `npm test`, wired into ci/ci.yml.
- Tests: web 3 passed (money formatting); lint, tsc, build pass. API 8 passed.
- Decisions made: vitest pinned to ^3 (v5 conflicts with @types/node 20). Grade A/B/C labels are placeholders pending founder grade definitions. Demo price on the placeholder home is dummy data.
- Blockers / founder inputs needed: T02 still blocked (workflow scope); grade definitions still needed.
- Next: T05

### 2026-11-10T06:45Z - T05 Auth
- Done: app/auth: models (users, roles, permissions, role_permissions, user_roles with nullable counter_id, refresh_tokens), Argon2id hashing, JWT access tokens (15 min, typ-checked), rotating refresh tokens (HttpOnly, SameSite=Strict, Secure outside dev, path /auth; only SHA-256 hash stored; reuse of a rotated token revokes the whole family), /auth/login, /auth/refresh, /auth/logout, /auth/me; `require_permission(code, counter_param=None)` dependency; default roles super_admin/admin/qc_technician/counter_partner in rbac.py; idempotent `python -m app.seed` (RBAC + super admin from SUPER_ADMIN_EMAIL/PASSWORD env); migration 0002.
- Tests: API 22 passed (14 new incl. counter isolation, refresh rotation/replay, expiry, forged tokens, deactivated user); ruff check + format clean. Alembic upgrade/downgrade/check verified on local Postgres 16. Web: lint, tsc, 3 tests, build pass.
- Decisions made: counter-scoped role grants permission only for that counter and never for counter-less actions; global role (counter_id NULL) applies everywhere. counter_id has no FK until counters table exists (T14 should add it). Customer phone-OTP auth (D8) deferred to T24 reserve flow. Ignored ruff B008 (FastAPI Depends). Login failures return one uniform message and equalise timing for unknown emails. No rate limiting yet (T34).
- Blockers / founder inputs needed: T02 still blocked (workflow scope).
- Next: T06

### 2026-11-10T10:45Z - T06 Catalogue schema + API
- Done: app/catalog: brands, product_models, product_variants (sku unique, storage/RAM CHECKs), specifications (unique per model+key), product_images; migration 0003; public read endpoints `/catalog/brands`, `/catalog/models` (brand filter, paginated), `/catalog/models/{slug}` (active variants, specs, images; whitelist schemas, no internal ids); admin CRUD under `/admin/catalog` (brands, models, variants, replace-all specs, images add/delete) gated by catalog.read/catalog.write; deactivation hides items publicly; idempotent demo seed of 15 models (iPhone 11-15, Galaxy S21-S23 + A34/A52s/A53/A54 5G, OnePlus 9/10 Pro/11) wired into `python -m app.seed`.
- Tests: API 29 passed (7 new incl. public endpoint no-sensitive-fields checks, auth/permission 401/403, CRUD, conflicts, visibility); ruff clean; alembic upgrade/downgrade/check verified on local Postgres 16. Web untouched.
- Decisions made: specs are per model (not per variant); image URLs only accepted if https:// or relative (blocks javascript:); seed lists RAM/storage configs from public knowledge and is labelled demo - founder to verify; slugs omit duplicate brand prefix (iphone-13, oneplus-11, samsung-galaxy-s22). A52s was added to reach 15 models.
- Blockers / founder inputs needed: T02 still blocked (workflow scope); catalogue content (photos, specs) and grade definitions.
- Next: T07

### 2026-11-10T11:15Z - T07 Device schema
- Done: app/inventory: devices (imei_encrypted, imei_hash UNIQUE, imei_last4, grade, battery_health, cost_paise, price_paise, status, location_kind + counter_id), device_tests (JSONB checklist, partial unique index = one current test per device), device_photos, stock_movements (append-only ledger), audit_log; CHECK constraints for status (D7's 14 states), grade, location, battery 0-100, non-negative money, counter_id iff COUNTER; migration 0004. IMEI helpers (Luhn validation, Fernet MultiFernet encryption with key rotation, HMAC-SHA256 keyed hash); settings IMEI_ENCRYPTION_KEYS / IMEI_HASH_KEY (dev placeholders, documented in .env.example). Added `cryptography` dependency.
- Tests: API 44 passed (15 new: D7 enum, IMEI validation, encrypt/rotate/hash, unique IMEI, 8 CHECK violations, partial unique test index); ruff clean; alembic upgrade/downgrade/check verified on Postgres 16 (partial index confirmed in pg_indexes).
- Decisions made: Schema only - no write paths yet; status changes arrive with the lifecycle service (T08). The D2 "one active reservation/sale per device" partial indexes need reservation/sale tables, so they land with T24/T17 (noted); the partial index here is on current QC test. counter_id has no FK until T14. Grades A/B/C remain placeholders.
- Blockers / founder inputs needed: T02 still blocked (workflow scope). Before production: generate real IMEI_ENCRYPTION_KEYS (Fernet) and IMEI_HASH_KEY and store them securely; losing the encryption key makes stored IMEIs unreadable.
- Next: T08

### 2026-11-10T14:30Z - TP1 One-click preview deployment on Render
- Done: root `render.yaml` Blueprint (free Postgres `refurbi-db`; Docker API `refurbi-api` with DATABASE_URL via fromDatabase, JWT_SECRET / IMEI_ENCRYPTION_KEYS / IMEI_HASH_KEY / SUPER_ADMIN_PASSWORD via generateValue, APP_ENV=preview, healthCheckPath /health, CORS_ORIGINS wired from the web service's RENDER_EXTERNAL_URL; Node web `refurbi-web` with NEXT_PUBLIC_API_URL wired from the API's RENDER_EXTERNAL_URL). API: services/api/Dockerfile + scripts/start.sh (alembic upgrade head, idempotent seed incl. demo data, uvicorn on $PORT); settings normalise postgres:// to postgresql+psycopg://, CORS_ORIGINS (bare hosts treated as https) + CORSMiddleware; IMEI keys that are not valid Fernet keys are derived by SHA-256 (so generated strings work); minimal `counters` table (migration 0005, T14 will extend); `app/preview_seed.py` (3 demo counters, 30 demo devices across grades A/B/C, warehouse + counters, synthetic Luhn IMEIs 99000000..., dummy paise prices; runs only when APP_ENV=preview). Web: DemoBanner on every page when APP_ENV/NEXT_PUBLIC_APP_ENV=preview, preview start page at `/` (links to /catalogue, /admin, /partner, "coming soon" for the rest), /catalogue (live from public API), /admin/login (demo admin sign-in against the API), lib/config.ts (normalises API URL scheme; localhost fallback only in development). docs/PREVIEW_SETUP.md.
- Tests: API 57 passed (13 new: seed idempotency/grades/counters, demo admin login with a +/= password, DB URL + CORS normalisation, CORS headers, Fernet derivation, public catalogue leak check); ruff clean. Web: lint, tsc, 9 tests, build pass. Verified against real local Postgres 16: alembic upgrade + check, seed twice, API login, and a headless browser flow (catalogue lists 15 models; login from the web origin works via CORS).
- Decisions made: (1) Render free plan has no pre-deploy command, so migrations + seed run in the container start script. (2) Public URLs wired with `fromService ... envVarKey: RENDER_EXTERNAL_URL` (gives a full https URL; `host` is private-network only); apps also normalise a missing scheme. (3) Demo devices are inserted directly in their initial state because the lifecycle service (T08) does not exist yet. (4) Access token kept in sessionStorage in the preview login page (refresh cookie is SameSite=Strict and web/API are different sites on Render; real auth UI comes later). (5) `/` is the preview start page until T21 replaces it.
- Blockers / founder inputs needed: render.com and docs.render.com were NOT reachable from the build sandbox, so render.yaml was checked against the spec only via search-result excerpts and memory, NOT by Render's validator. Residual risks to check on first Apply: (a) web<->api `fromService` references form a cycle (Render may reject it; fallback: drop CORS_ORIGINS wiring and use a Next rewrite proxy); (b) `RENDER_EXTERNAL_URL` via fromService envVarKey; (c) Docker `dockerfilePath`/`dockerContext` are repo-root relative. If Apply errors, copy the error to the next run. Founder: ACTION (3 min) follow docs/PREVIEW_SETUP.md, then record `Preview URL: ...` here.
- Next: T08
