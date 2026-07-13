# Architecture

## Overview

Parcel Server is split into two independently deployable applications:

- **`backend/`** — a FastAPI service exposing a versioned REST API
  (`/api/v1`), backed by SQLAlchemy models and Alembic migrations.
- **`frontend/`** — a React + TypeScript single-page app (Vite, MUI) that
  consumes the REST API.

Everything else at the repository root (`importer/`, `tracking/`,
`notification/`, `mqtt/`, `integrations/`) is a future-phase package that
will plug into the backend through an explicit interface, never by reaching
into its internals.

## Backend layering

The backend follows a strict layered architecture; each layer only depends
on the layer directly below it:

```
app/api/            HTTP concerns only: request/response schemas, status
                     codes, routing. No business logic.
        v1/router.py   aggregates all versioned routers
        v1/endpoints/  one module per resource
        deps.py        shared FastAPI dependencies (DB session, current user)

app/services/        Business logic. Raises domain exceptions
                      (app/services/exceptions.py); knows nothing about
                      HTTP or FastAPI.

app/repositories/     Data access. The only layer that writes SQLAlchemy
                      queries. BaseRepository[T] provides generic CRUD;
                      resource-specific repositories add targeted queries.

app/models/           SQLAlchemy ORM models (the schema). Import them
                      through app/models/__init__.py so Alembic's
                      autogenerate sees the full metadata.

app/schemas/          Pydantic request/response models (the API contract).
                      Distinct from ORM models so the wire format can evolve
                      independently of the storage format.

app/core/             Cross-cutting infrastructure: password hashing, JWT,
                      logging setup. No dependency on any other app/* layer.

app/config.py         Single source of truth for all runtime settings,
                      loaded from config.yaml. Nothing is hardcoded.
```

Routes depend on services via FastAPI's `Depends`; services depend on
repositories; repositories depend on the SQLAlchemy `Session`. This keeps
business rules testable without spinning up the HTTP layer (see
`backend/tests/unit/`) and keeps API tests focused on request/response
behavior (see `backend/tests/api/`).

## Data model (Phase 1)

- **User** — an account that owns orders.
- **Order** — a purchase from a merchant; belongs to a user; has zero or
  more shipments.
- **Shipment** — a parcel with a tracking number, optionally linked to an
  order and a carrier; has a tracking-event history.
- **TrackingEvent** — one status update in a shipment's history (status,
  description, location, timestamp).
- **Carrier** — reference data for a shipping carrier (DHL, UPS, ...).
- **Email** — a raw ingested shipping-confirmation email (Phase 2); can be
  linked back to the order it was matched against.

## Database portability

`app/config.py`'s `DatabaseSettings.sqlalchemy_url` is the only place that
builds a connection string. Switching between SQLite, PostgreSQL, and
MariaDB is a one-line change in `config.yaml` (`database.driver`) - no code
changes, because every query goes through SQLAlchemy Core/ORM rather than
driver-specific SQL.

## Forward-looking interfaces

Two abstractions are deliberately introduced ahead of their implementation,
because the top-level project structure depends on them not being an
afterthought:

- **`tracking.TrackingProvider`** (Phase 3) — `register()` / `update()` /
  `remove()`. Concrete providers (17TRACK, AfterShip, TrackingMore, Ship24,
  carrier APIs) implement this interface; the backend only ever depends on
  it, so the active provider is a configuration choice.
- Merchant email parsers and carrier tracking-number detectors (Phase 2/3)
  will be plugin-registered, so adding support for a new merchant or
  carrier never requires touching the core import/tracking loop.

## Authentication

JWT access + refresh tokens (`app/core/security.py`). Passwords are hashed
with Argon2 (bcrypt as fallback) via passlib. OAuth, LDAP, and Home
Assistant authentication are planned for later phases as additional
`app/core/security.py` strategies behind the same `get_current_user`
dependency.
