# Build context is the repository root (see docker-compose.yml) because the
# backend depends on the sibling `importer` and `tracking` packages.
FROM python:3.13-slim AS base

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PARCEL_SERVER_CONFIG=/app/backend/config.yaml

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY tracking ./tracking
COPY importer ./importer
COPY backend/pyproject.toml ./backend/pyproject.toml
COPY backend/app ./backend/app
COPY backend/alembic ./backend/alembic
COPY backend/alembic.ini ./backend/alembic.ini

RUN pip install --no-cache-dir ./tracking ./importer ./backend

COPY backend/entrypoint.sh /entrypoint.sh
COPY backend/worker-entrypoint.sh /worker-entrypoint.sh
RUN chmod +x /entrypoint.sh /worker-entrypoint.sh

WORKDIR /app/backend
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
