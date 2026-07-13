#!/usr/bin/env bash
# Run linters and formatters check for backend, importer, tracking,
# notification, mqtt, and frontend.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
ruff="$root/backend/.venv/bin/ruff"

echo "== backend: ruff check =="
"$ruff" check "$root/backend/app" "$root/backend/tests"

echo "== backend: ruff format --check =="
"$ruff" format --check "$root/backend/app" "$root/backend/tests"

echo "== importer: ruff check =="
"$ruff" check "$root/importer"

echo "== tracking: ruff check =="
"$ruff" check "$root/tracking"

echo "== notification: ruff check =="
"$ruff" check "$root/notification"

echo "== mqtt: ruff check =="
"$ruff" check "$root/mqtt"

echo "== frontend: oxlint =="
(cd "$root/frontend" && npm run lint)

echo "== frontend: tsc =="
(cd "$root/frontend" && npx tsc -b)
