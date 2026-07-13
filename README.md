# Parcel Server

A self-hosted parcel-tracking server. It reads shipping confirmations out of
your inbox, extracts tracking numbers, identifies the carrier, and keeps
track of every parcel's status - all running locally under your control.

Phases 1 and 2 of a five-phase build are done (see
[`docs/roadmap.md`](docs/roadmap.md)): the foundation (backend, frontend,
database, Docker, authentication, dashboard) and automatic email import
(IMAP mailboxes, pluggable merchant parsers, carrier detection). Real
tracking-provider integration, notifications, and statistics land in later
phases.

## Stack

- **Backend:** Python 3.13, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic,
  Uvicorn.
- **Frontend:** React, TypeScript, Vite, Material UI (dark/light mode).
- **Database:** SQLite by default; PostgreSQL or MariaDB as drop-in
  alternatives (one config field, no code changes).
- **Auth:** JWT (OAuth, LDAP, and Home Assistant auth planned for later
  phases).
- **Email import:** IMAP polling (Gmail, Outlook/Exchange, GMX, WEB.DE,
  Yahoo, ...) with auto-discovered merchant parsers (Amazon, eBay, Otto,
  MediaMarkt, Saturn, IKEA, Temu, Kaufland, AliExpress, Decathlon, Zalando,
  Alternate) and carrier tracking-number detection (DHL, UPS, DPD, GLS,
  Hermes, FedEx, USPS, Cainiao, YunExpress, Amazon Logistics, Royal Mail,
  PostNL, ...).
- **Docker:** full Compose stack - backend, import worker, frontend,
  database, optional Redis.

## Quick start

### Docker (recommended for running the server)

```bash
cp .env.example .env
cp backend/config.docker.example.yaml backend/config.yaml
# edit backend/config.yaml: set a real security.jwt_secret_key and
# security.mail_encryption_key, and match database.password to
# POSTGRES_PASSWORD in .env
docker compose up --build
```

Backend: http://localhost:8000/docs · Frontend: http://localhost:5173

See [`docs/docker.md`](docs/docker.md) for details.

### Local development

```bash
scripts/dev-backend.sh    # FastAPI with auto-reload on :8000
scripts/dev-frontend.sh   # Vite dev server on :5173
scripts/dev-worker.sh     # mail-account import polling loop (optional)
```

See [`docs/installation.md`](docs/installation.md) and
[`docs/development.md`](docs/development.md).

## Project structure

```
backend/         FastAPI app + import worker: API, services, repositories,
                 models, Alembic
frontend/        React + TypeScript + MUI single-page app
database/        Data-model docs, seed data (migrations live in backend/)
importer/        IMAP client + pluggable merchant email parsers (Phase 2,
                 standalone package - see docs/architecture.md)
tracking/        Carrier tracking-number detection (Phase 2, implemented)
                 + provider-agnostic tracking interface (Phase 3, not yet
                 implemented) - standalone package
notification/    Notification channel plugins (Phase 4)
mqtt/            MQTT / Home Assistant Discovery (Phase 4)
integrations/    Home Assistant integration, additional auth (Phase 4+)
docs/            Architecture, installation, Docker, development, roadmap
tests/           (backend/importer/tracking tests live alongside their own
                 code; see docs/development.md)
docker/          Supplementary Docker assets (compose file is at the repo root)
scripts/         Dev/lint/test/migrate helper scripts
```

## Documentation

- [Architecture](docs/architecture.md)
- [Installation](docs/installation.md)
- [Docker](docs/docker.md)
- [Development](docs/development.md)
- [Roadmap](docs/roadmap.md)

API documentation is generated automatically by FastAPI: Swagger UI at
`/docs`, ReDoc at `/redoc`, OpenAPI schema at `/openapi.json`.

## Principles

Maintainability and extensibility come first: layered architecture
(API → services → repositories → models), dependency injection via FastAPI,
a repository pattern isolating SQL from business logic, full type hints,
and no business logic in API routes. Merchant parsers, carrier detectors,
tracking providers, and notification channels are plugins added by dropping
in one new file - never by editing the core loop that discovers them.
