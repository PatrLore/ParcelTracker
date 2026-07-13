#!/usr/bin/env bash
# Apply database migrations. Usage: scripts/migrate.sh [alembic-args...]
# Defaults to "upgrade head" when no arguments are given.
set -euo pipefail

cd "$(dirname "$0")/../backend"

if [ "$#" -eq 0 ]; then
  .venv/bin/alembic upgrade head
else
  .venv/bin/alembic "$@"
fi
