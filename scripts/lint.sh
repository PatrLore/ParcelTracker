#!/usr/bin/env bash
# Run linters and formatters check for both backend and frontend.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"

echo "== backend: ruff check =="
"$root/backend/.venv/bin/ruff" check "$root/backend/app" "$root/backend/tests"

echo "== backend: ruff format --check =="
"$root/backend/.venv/bin/ruff" format --check "$root/backend/app" "$root/backend/tests"

echo "== frontend: oxlint =="
(cd "$root/frontend" && npm run lint)

echo "== frontend: tsc =="
(cd "$root/frontend" && npx tsc -b)
