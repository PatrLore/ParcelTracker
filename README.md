# Parcel Server

A self-hosted parcel-tracking server. It reads shipping confirmations out of
your inbox, extracts tracking numbers, identifies the carrier, and keeps
track of every parcel's status - all running locally under your control.

All five planned phases are done (see [`docs/roadmap.md`](docs/roadmap.md)
for what's genuinely finished vs. still best-effort within each): the
foundation (backend, frontend, database, Docker, authentication,
dashboard), automatic email import (IMAP mailboxes, pluggable merchant
parsers, carrier detection), tracking-provider integration (17TRACK,
AfterShip, TrackingMore, Ship24), notifications (webhook, Discord,
Telegram, Email, Signal) plus MQTT/Home Assistant Discovery sensors, a
statistics dashboard, and a dedicated Home Assistant custom integration
(native sensors and services, see `custom_components/parcel_server/` and
`integrations/home_assistant/README.md`). Additional auth providers
(OAuth, LDAP) remain open - see the roadmap.

## Stack

- **Backend:** Python 3.13, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic,
  Uvicorn.
- **Frontend:** React, TypeScript, Vite, Material UI (dark/light mode).
- **Database:** SQLite by default; PostgreSQL or MariaDB as drop-in
  alternatives (one config field, no code changes).
- **Auth:** JWT (OAuth, LDAP, and Home Assistant auth planned for later
  phases).
- **Home Assistant:** MQTT Discovery sensors (below) plus a dedicated
  custom integration (`custom_components/parcel_server/`, installable via
  HACS as a custom repository - docs at `integrations/home_assistant/`)
  with a config flow, five native sensors, and three services (refresh
  tracking, archive parcel, send notification), and a matching Lovelace
  dashboard card (`dist/parcel-server-card.js`, installable via HACS as a
  separate Plugin-category entry).
- **Email import:** IMAP polling (Gmail, Outlook/Exchange, GMX, WEB.DE,
  Yahoo, ...) with auto-discovered merchant parsers (Amazon, eBay, Otto,
  MediaMarkt, Saturn, IKEA, Temu, Kaufland, AliExpress, Decathlon, Zalando,
  Alternate) and carrier tracking-number detection (DHL, UPS, DPD, GLS,
  Hermes, FedEx, USPS, Cainiao, YunExpress, Amazon Logistics, Royal Mail,
  PostNL, ...).
- **Tracking providers:** pluggable `TrackingProvider` interface with
  17TRACK, AfterShip, TrackingMore, and Ship24 implementations - swap the
  active one in `config.yaml`, no code changes.
- **Notifications:** webhook, Discord, Telegram, Email (SMTP), and Signal
  (via signal-cli-rest-api) - independently enabled, fan out to all of them
  on new confirmations and delivered/delayed shipments.
- **MQTT:** Home Assistant MQTT Discovery sensors (`parcel.total`,
  `.in_transit`, `.delivered_today`, `.next_delivery`, `.delayed`).
- **Statistics:** parcels per month, average delivery time, top
  merchant/carrier, delayed rate, success rate.
- **Docker:** full Compose stack - backend, import worker, tracking worker,
  frontend, database, optional Redis, optional MQTT broker.

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
scripts/dev-backend.sh          # FastAPI with auto-reload on :8000
scripts/dev-frontend.sh         # Vite dev server on :5173
scripts/dev-worker.sh           # mail-account import polling loop (optional)
scripts/dev-tracking-worker.sh  # shipment tracking refresh loop (optional)
```

See [`docs/installation.md`](docs/installation.md) and
[`docs/development.md`](docs/development.md).

## Project structure

```
backend/         FastAPI app + import/tracking workers: API, services,
                 repositories, models, Alembic
frontend/        React + TypeScript + MUI single-page app
database/        Data-model docs, seed data (migrations live in backend/)
importer/        IMAP client + pluggable merchant email parsers (Phase 2,
                 standalone package - see docs/architecture.md)
tracking/        Carrier tracking-number detection (Phase 2) + provider-
                 agnostic TrackingProvider interface and implementations
                 (Phase 3) - standalone package
notification/    Notification channel plugins: webhook, Discord, Telegram,
                 Email, Signal (Phase 4) - standalone package
mqtt/            MQTT publisher + Home Assistant Discovery (Phase 4) -
                 standalone package
custom_components/  Home Assistant custom integration (parcel_server/,
                 done) - lives at the repo root because HACS requires it
                 there; its docs/tests live at integrations/home_assistant/
dist/            Lovelace dashboard card (parcel-server-card.js, done) -
                 also at the repo root, HACS's "plugin" category has the
                 same root-level requirement as custom_components/ above
integrations/    Home Assistant integration + dashboard card docs/tests
                 (home_assistant/, see custom_components/ and dist/ above)
                 plus additional auth providers (Phase 4+, not yet implemented)
docs/            Architecture, installation, Docker, development, roadmap
tests/           (backend/importer/tracking/notification/mqtt/
                 integrations-home_assistant tests live alongside their own
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
