# Architecture

## Overview

Parcel Server is split into independently deployable/installable units:

- **`backend/`** — a FastAPI service exposing a versioned REST API
  (`/api/v1`), backed by SQLAlchemy models and Alembic migrations. Also runs
  as a separate **import worker** process (`app/worker.py`) that polls mail
  accounts (Phase 2).
- **`frontend/`** — a React + TypeScript single-page app (Vite, MUI) that
  consumes the REST API.
- **`importer/`** — a standalone, database-free Python package: an IMAP
  client (`imap_client.py`) and pluggable merchant-confirmation parsers
  (`parsers/`). Implemented Phase 2.
- **`tracking/`** — a standalone, database-free Python package: the
  `TrackingProvider` interface (Phase 3, not yet implemented) and carrier
  tracking-number detection (`carriers.py`, implemented, used by `importer`
  since Phase 2).
- **`notification/`, `mqtt/`, `integrations/`** — future-phase packages
  (Phase 4+), currently placeholders.

`importer` and `tracking` have zero dependency on `backend`, FastAPI, or
SQLAlchemy - they're plain Python libraries installed into the backend's
virtualenv (`pip install -e ../importer -e ../tracking`, see
`scripts/dev-backend.sh` and `backend/Dockerfile`). The backend is the only
thing that depends on them, through
`app/services/email_ingestion_service.py` - never the other way around, and
never by reaching into their internals beyond the documented interface each
exposes.

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

## Data model

- **User** — an account that owns orders and mail accounts.
- **Order** — a purchase from a merchant; belongs to a user; has zero or
  more shipments.
- **Shipment** — a parcel with a tracking number, optionally linked to an
  order and a carrier; has a tracking-event history.
- **TrackingEvent** — one status update in a shipment's history (status,
  description, location, timestamp).
- **Carrier** — reference data for a shipping carrier (DHL, UPS, ...);
  created on demand when a parser first detects it.
- **Email** — a raw ingested shipping-confirmation email; linked back to
  the order it was matched against, or `order_id = NULL` if no parser
  recognized the sender.
- **MailAccount** (Phase 2) — an IMAP mailbox a user connected for import.
  The password is never stored in plain text - see
  [Mailbox credential encryption](#mailbox-credential-encryption) below.

## Email import pipeline (Phase 2)

```
app/worker.py (separate process/container)
  -> for each due MailAccount:
       app/services/email_ingestion_service.py
         -> importer.imap_client.ImapMailbox.fetch_since(last_seen_uid)
         -> importer.parsers.detect(raw_email)   # sender/regex-based
         -> persists Email, and (if matched) Order + Shipment rows
```

- `importer.imap_client.ImapMailbox` wraps `imapclient`, exposing
  `fetch_since(uid)` (polling) and `idle_check(...)` (IMAP IDLE). The worker
  currently only polls, on a per-account interval
  (`MailAccount.poll_interval_seconds`); IDLE is available in the client but
  not yet wired into a runner - a future phase can add one without changing
  the polling path.
- `importer.parsers.registry` auto-discovers every
  `MerchantParser` subclass in `importer/parsers/` via `pkgutil` - adding a
  merchant is one new file, no registration step.
  `importer.parsers._regex_parser.RegexMerchantParser` covers the common
  case (match by sender domain, extract via regex); a parser with unusual
  formatting can subclass `MerchantParser` directly instead.
- `EmailIngestionService` is the only place this data becomes database rows:
  it's injected an `ImapMailbox`-shaped factory (default: the real one),
  so tests exercise the full fetch -> parse -> persist path against a fake
  in-memory mailbox with no network access
  (`backend/tests/unit/test_email_ingestion_service.py`).
- Every `Email.message_id` is unique - re-fetching an already-seen message
  (e.g. a mailbox that doesn't advance UIDs monotonically) is a no-op.

### Mailbox credential encryption

`MailAccount.encrypted_password` is a Fernet token
(`app/core/crypto.py`), keyed by `security.mail_encryption_key` in
`config.yaml` - never the user's plaintext IMAP password. The API
(`MailAccountRead`) never includes the password or its encrypted form in
any response.

## Database portability

`app/config.py`'s `DatabaseSettings.sqlalchemy_url` is the only place that
builds a connection string. Switching between SQLite, PostgreSQL, and
MariaDB is a one-line change in `config.yaml` (`database.driver`) - no code
changes, because every query goes through SQLAlchemy Core/ORM rather than
driver-specific SQL.

## Forward-looking interfaces

**`tracking.TrackingProvider`** (Phase 3, interface defined, no
implementation yet) — `register()` / `update()` / `remove()`. Concrete
providers (17TRACK, AfterShip, TrackingMore, Ship24, carrier APIs) will
implement this interface; the backend will only ever depend on it, so the
active provider is a configuration choice, not a code change.

## Authentication

JWT access + refresh tokens (`app/core/security.py`). Passwords are hashed
with Argon2 (bcrypt as fallback) via passlib. OAuth, LDAP, and Home
Assistant authentication are planned for later phases as additional
`app/core/security.py` strategies behind the same `get_current_user`
dependency.
