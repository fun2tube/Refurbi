#!/usr/bin/env bash
# One-command E2E: API (preview seed, fake adapters) + web + Playwright. Demo credentials only.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
export DATABASE_URL="${E2E_DATABASE_URL:-postgresql+psycopg://refurbi:refurbi_dev_password@localhost:5432/refurbi_e2e}"
export APP_ENV=preview JWT_SECRET=e2e-secret-not-real-0123456789abcdef
export SUPER_ADMIN_EMAIL=admin@example.com SUPER_ADMIN_PASSWORD=e2e-password CORS_ORIGINS=http://localhost:3000
cd "$ROOT/services/api"
# fresh state every run (scratch DB only!) so stock/sales from earlier runs never leak in
psql "${DATABASE_URL/+psycopg/}" -q -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
uv run alembic upgrade head && uv run python -m app.seed
uv run uvicorn app.main:app --port 8000 >/tmp/refurbi-e2e-api.log 2>&1 & API_PID=$!
cd "$ROOT/apps/web"
NEXT_PUBLIC_API_URL=http://localhost:8000 npx next build >/tmp/refurbi-e2e-build.log 2>&1
NEXT_PUBLIC_API_URL=http://localhost:8000 npx next start -p 3000 >/tmp/refurbi-e2e-web.log 2>&1 & WEB_PID=$!
trap 'kill $API_PID $WEB_PID 2>/dev/null || true' EXIT
npx --yes wait-on@8 -t 90000 http-get://localhost:8000/health http-get://localhost:3000
npx playwright test --trace off "$@"
