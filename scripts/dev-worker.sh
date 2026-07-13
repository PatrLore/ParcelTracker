#!/usr/bin/env bash
# Run the mail-account import worker locally (Phase 2).
set -euo pipefail

cd "$(dirname "$0")/../backend"

if [ ! -d .venv ]; then
  echo "Run scripts/dev-backend.sh first to set up the virtualenv." >&2
  exit 1
fi

if [ ! -f config.yaml ]; then
  cp config.example.yaml config.yaml
  echo "Created backend/config.yaml from config.example.yaml - review it before continuing."
fi

.venv/bin/alembic upgrade head
exec .venv/bin/python -m app.worker
