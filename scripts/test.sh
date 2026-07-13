#!/usr/bin/env bash
# Run the backend, importer, and tracking test suites.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
python="$root/backend/.venv/bin/python"

echo "== backend =="
(cd "$root/backend" && "$python" -m pytest --cov=app --cov-report=term-missing)

echo "== importer =="
(cd "$root/importer" && "$python" -m pytest)

echo "== tracking =="
(cd "$root/tracking" && "$python" -m pytest)
