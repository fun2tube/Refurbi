#!/bin/sh
# Container entrypoint: migrate, seed (idempotent; adds demo data when APP_ENV=preview), serve.
# Migrations run here (not as a pre-deploy command) because Render's free plan has none.
set -e
alembic upgrade head
python -m app.seed
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
