# Build context is the repository root (see docker-compose.yml) because the
# backend depends on the sibling `importer`, `tracking`, `notification`, and
# `mqtt` packages.
FROM python:3.13-slim AS base

# Set via `docker compose build --build-arg` / the GIT_COMMIT env var (see
# docker-compose.yml) so the running container can report which commit
# it was built from - see app/core/version.py. Defaults to "unknown" if
# not passed, which the update-check endpoint treats as "can't tell".
ARG GIT_COMMIT=unknown

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PARCEL_SERVER_CONFIG=/app/backend/config.yaml \
    PARCEL_SERVER_COMMIT=$GIT_COMMIT

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY tracking ./tracking
COPY importer ./importer
COPY notification ./notification
COPY mqtt ./mqtt
COPY backend/pyproject.toml ./backend/pyproject.toml
COPY backend/app ./backend/app
COPY backend/alembic ./backend/alembic
COPY backend/alembic.ini ./backend/alembic.ini

RUN pip install --no-cache-dir ./tracking ./importer ./notification ./mqtt ./backend

COPY backend/entrypoint.sh /entrypoint.sh
COPY backend/worker-entrypoint.sh /worker-entrypoint.sh
COPY backend/tracking-worker-entrypoint.sh /tracking-worker-entrypoint.sh
RUN chmod +x /entrypoint.sh /worker-entrypoint.sh /tracking-worker-entrypoint.sh

WORKDIR /app/backend
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
