# refurbi.

Premium refurbished smartphones - online storefront, retail-counter POS and device-level inventory in one platform.

- Why and how: [docs/CTO_DECISIONS.md](docs/CTO_DECISIONS.md)
- What's being built, in order: [ROADMAP.md](ROADMAP.md)
- What's done so far: [PROGRESS.md](PROGRESS.md)
- Rules for the autonomous build agent: [CLAUDE.md](CLAUDE.md)

Stack: Next.js 15 (store + admin + partner POS in one app) - FastAPI - PostgreSQL 16 - Alembic - Docker.

## Run locally

Prerequisites: Node 22+, Python 3.12, [uv](https://docs.astral.sh/uv/), Docker.

```bash
# Postgres 16 (and optionally the API container)
docker compose up -d db

# API  -> http://localhost:8000/health
cd services/api && cp .env.example .env
uv sync && uv run uvicorn app.main:app --reload
uv run ruff check . && uv run pytest

# Web  -> http://localhost:3000
cd apps/web && cp .env.example .env.local
npm install && npm run dev
npm run lint && npx tsc --noEmit && npm run build
```

Layout: `apps/web` (Next.js 15 storefront/admin/partner), `services/api` (FastAPI modular monolith), `docs/` (decisions).
