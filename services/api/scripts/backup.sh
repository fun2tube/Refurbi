#!/bin/sh
# Free backup: logical dump of the Neon database. Usage: DATABASE_URL=... sh scripts/backup.sh [outdir]
# Use the DIRECT (non-pooler) Neon URL, plain postgresql:// form (not postgresql+psycopg://).
# Restore: pg_restore --no-owner --clean --if-exists -d "$TARGET_URL" file.dump
set -e
: "${DATABASE_URL:?set DATABASE_URL to the Neon connection string}"
out="${1:-.}/refurbi-$(date -u +%Y%m%dT%H%M%SZ).dump"
pg_dump --format=custom --no-owner --file "$out" "$DATABASE_URL"
echo "wrote $out"
