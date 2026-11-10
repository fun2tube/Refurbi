# Refurbi - Build Progress

## Status
- Tasks done: 4 / 36 (11%)
- Current milestone: 0 - Foundation
- Next task: T06
- Blockers: T02 (push lacks `workflow` scope)

## Founder inputs needed (not blocking yet)
- Set real JWT_SECRET, SUPER_ADMIN_EMAIL/PASSWORD in the deploy env, then run `python -m app.seed` (T05)
- GSTIN, legal name, registered address (T16 invoices)
- CA sign-off on GST margin scheme (Rule 32(5)) and ITC policy
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
