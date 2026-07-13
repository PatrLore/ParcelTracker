#!/usr/bin/env bash
# Run the frontend dev server with hot reload.
set -euo pipefail

cd "$(dirname "$0")/../frontend"

if [ ! -d node_modules ]; then
  npm install
fi

exec npm run dev
