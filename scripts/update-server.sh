#!/usr/bin/env bash
# Update a running Docker Compose deployment: pull the latest code and
# rebuild/restart the stack with it. Run this on the server hosting Parcel
# Server (not from a dev machine) - see docs/docker.md "Checking for
# updates" for why this isn't done automatically from inside the app.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: $root is not a git repository." >&2
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "error: uncommitted local changes in $root - commit or stash them first, then re-run." >&2
  git status --short
  exit 1
fi

branch="$(git rev-parse --abbrev-ref HEAD)"
echo "== Updating Parcel Server ($root, branch: $branch) =="

echo "-- git pull --"
git pull

commit="$(git rev-parse HEAD)"
echo "-- Now at commit ${commit:0:7} --"

echo "-- docker compose up --build -d --"
GIT_COMMIT="$commit" docker compose up --build -d

echo "-- Container status --"
docker compose ps

echo "== Update complete (commit ${commit:0:7}) =="
