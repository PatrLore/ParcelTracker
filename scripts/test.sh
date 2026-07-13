#!/usr/bin/env bash
# Run the backend test suite with coverage.
set -euo pipefail

cd "$(dirname "$0")/../backend"
.venv/bin/pytest --cov=app --cov-report=term-missing
