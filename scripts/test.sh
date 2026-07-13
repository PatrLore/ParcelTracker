#!/usr/bin/env bash
# Run the backend, importer, tracking, notification, and mqtt test suites.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
python="$root/backend/.venv/bin/python"

echo "== backend =="
(cd "$root/backend" && "$python" -m pytest --cov=app --cov-report=term-missing)

echo "== importer =="
(cd "$root/importer" && "$python" -m pytest)

echo "== tracking =="
(cd "$root/tracking" && "$python" -m pytest)

echo "== notification =="
(cd "$root/notification" && "$python" -m pytest)

echo "== mqtt =="
(cd "$root/mqtt" && "$python" -m pytest)
