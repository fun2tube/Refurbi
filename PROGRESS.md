# Refurbi - Build Progress

## Status
- Tasks done: 1 / 36 (3%)
- Current milestone: 0 - Foundation
- Next task: T03
- Blockers: T02 (push lacks `workflow` scope)

## Founder inputs needed (not blocking yet)
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
