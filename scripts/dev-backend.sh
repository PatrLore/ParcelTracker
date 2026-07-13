#!/usr/bin/env bash
# Run the backend API locally with auto-reload for development.
set -euo pipefail

cd "$(dirname "$0")/../backend"

if [ ! -d .venv ]; then
  python3.13 -m venv .venv
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -e "../tracking[dev]" -e "../importer[dev]" -e ".[dev]"
fi

if [ ! -f config.yaml ]; then
  cp config.example.yaml config.yaml
  echo "Created backend/config.yaml from config.example.yaml - review it before continuing."
fi

.venv/bin/alembic upgrade head
exec .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
