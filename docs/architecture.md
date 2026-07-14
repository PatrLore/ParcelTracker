# Architecture

## Overview

Parcel Server is split into independently deployable/installable units:

- **`backend/`** — a FastAPI service exposing a versioned REST API
  (`/api/v1`), backed by SQLAlchemy models and Alembic migrations. Also runs
  as two separate worker processes: an **import worker**
  (`app/worker.py`, Phase 2) that polls mail accounts, and a **tracking
  worker** (`app/tracking_worker.py`, Phase 3/4) that refreshes shipment
  status via the configured tracking provider and republishes MQTT sensor
  state.
- **`frontend/`** — a React + TypeScript single-page app (Vite, MUI) that
  consumes the REST API.
- **`importer/`** — a standalone, database-free Python package: an IMAP
  client (`imap_client.py`) and pluggable merchant-confirmation parsers
  (`parsers/`). Implemented Phase 2.
- **`tracking/`** — a standalone, database-free Python package: carrier
  tracking-number detection (`carriers.py`, Phase 2, used by `importer`) and
  the `TrackingProvider` interface plus four concrete implementations
  (`providers/` - 17TRACK, AfterShip, TrackingMore, Ship24; Phase 3).
- **`notification/`** — a standalone, database-free Python package: the
  `NotificationChannel` interface plus five implementations (webhook,
  Discord, Telegram, Email, Signal) and a fan-out `NotificationDispatcher`.
  Phase 4.
- **`mqtt/`** — a standalone, database-free Python package: an MQTT
  publisher with Home Assistant MQTT Discovery for the five `parcel.*`
  sensors. Phase 4.
- **`custom_components/parcel_server/`** (repository root) — a native Home
  Assistant custom integration talking to the REST API directly: a config
  flow, five sensors, and three services (`refresh_tracking`,
  `archive_parcel`, `send_notification`). Lives at the repository root,
  not under `integrations/`, because HACS requires `custom_components/`
  there; its docs, tests, and dev tooling live at
  `integrations/home_assistant/` instead (see
  `integrations/home_assistant/README.md`). Unlike
  `importer`/`tracking`/`notification`/`mqtt`, it isn't pip-installed into
  the backend's virtualenv - it's installed into Home Assistant itself,
  via HACS or by copying the folder into Home Assistant's config directory.
- **`dist/parcel-server-card.js`** (repository root) — a Lovelace
  dashboard card, HACS's separate "plugin" category from the
  `custom_components/parcel_server/` "integration" category (same repo,
  two independent HACS entries). A dependency-free vanilla Web Component
  reading the integration's five sensors - no `lit`/build step. At the
  repository root (inside `dist/`) rather than under `integrations/` for
  the same HACS root-level file-discovery reason as `custom_components/`.
- **`integrations/`** — deeper platform integrations beyond generic
  notifications: `home_assistant/` (Phase 4+, done) holds the Home
  Assistant integration's and dashboard card's docs/tests (their code is
  at `custom_components/parcel_server/` and `dist/`, see above). Additional
  auth
  providers (OAuth, LDAP) remain a placeholder.

`importer`, `tracking`, `notification`, and `mqtt` all have zero dependency
on `backend`, FastAPI, or SQLAlchemy - they're plain Python libraries
installed into the backend's virtualenv (`pip install -e ../importer
-e ../tracking -e ../notification -e ../mqtt`, see `scripts/dev-backend.sh`
and `backend/Dockerfile`). The backend is the only thing that depends on
them, through one dedicated service module per package
(`email_ingestion_service.py`, `tracking_sync_service.py`,
`notification_dispatch_factory.py`, `mqtt_publish_service.py`) - never the
other way around, and never by reaching into their internals beyond the
documented interface each exposes.

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
- **Shipment.tracking_registered** (Phase 3) — whether `register()` has
  already been called against the configured `TrackingProvider` for this
  shipment, so the sync loop doesn't re-register on every pass.

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

## Tracking provider integration (Phase 3)

```
app/tracking_worker.py (separate process/container)
  -> tracking_provider.name != "none":
       app/services/tracking_sync_service.py
         -> for each non-terminal Shipment:
              provider.register(tracking_number)   # once per shipment
              provider.update(tracking_number)      # -> TrackingProviderEvent[]
              -> new events become TrackingEvent rows; Shipment.tracking_status
                 and .delivery_date update from the latest event
```

- `tracking.providers.factory.create_provider(name, api_key)` builds the
  provider named in `config.yaml`'s `tracking_provider.name` (`none` /
  `seventeentrack` / `aftership` / `trackingmore` / `ship24`).
  `app/services/tracking_provider_factory.py` is the one place backend code
  calls it - `TrackingSyncService` and the `POST
  /shipments/{id}/refresh-tracking` endpoint both go through it, so there's
  a single source of truth for which provider is active.
- Each provider implementation (`tracking/providers/*.py`) talks to one
  external REST API via `httpx`. Response field names follow each
  provider's public documentation as of this writing; if a provider changes
  its schema, only that one file needs updating. Tests
  (`tracking/tests/test_providers.py`) exercise the request/response
  handling against `httpx.MockTransport`, not the live APIs.
- `TrackingSyncService` deduplicates events by `(status, occurred_at)`,
  normalized to naive UTC - `DateTime(timezone=True)` columns round-trip as
  naive on SQLite but stay timezone-aware on Postgres/MariaDB, so comparing
  raw values would behave differently per backend.
- A shipment already `DELIVERED` or `RETURNED` is excluded from
  `sync_due_shipments()` - there's nothing left to poll for.
- One shipment's provider request failing doesn't stop the rest of that
  sync pass (`TrackingSyncService.sync_due_shipments` catches per-shipment,
  the worker also wraps the whole pass defensively).

## Notifications and MQTT (Phase 4)

```
new order/shipment confirmation  --> app/services/email_ingestion_service.py
shipment -> DELIVERED / DELAYED  --> app/services/tracking_sync_service.py
                                          |
                                          v
                          app/services/notification_dispatch_factory.py
                                          |
                                          v
                       notification.NotificationDispatcher.dispatch(...)
                          -> every enabled channel, independently
```

- Each channel (`notification/channels/*.py`) is independently enabled in
  `config.yaml`'s `notification.*` section - nothing is sent anywhere by
  default. `get_configured_notification_dispatcher()` is the one place
  backend code builds the enabled-channel list; `EmailIngestionService` and
  `TrackingSyncService` both take an optional `NotificationDispatcher` and
  fire a message on the two events the spec calls for: a new order
  confirmation, and a shipment becoming delivered or delayed.
- `NotificationDispatcher.dispatch()` sends to every channel and swallows
  per-channel exceptions (logged, not raised) - one broken webhook
  shouldn't silence Telegram, email, and the rest.
- MQTT works differently: instead of one-off messages, `mqtt.MqttPublisher`
  publishes *retained* Home Assistant MQTT Discovery config once and
  current sensor values (`parcel.total`, `.in_transit`, `.delivered_today`,
  `.next_delivery`, `.delayed`) repeatedly, computed globally across every
  user (`app/services/mqtt_publish_service.py`) - matching a single
  Home-Assistant-per-household deployment rather than per-user sensors.
- The tracking worker (`app/tracking_worker.py`) runs both the tracking
  sync and the MQTT publish as two independently-scheduled jobs on one
  30-second tick, each on its own configured interval
  (`tracking_provider.poll_interval_seconds`, `mqtt.publish_interval_seconds`)
  - the same pattern the mail worker uses for per-account polling.

## Statistics (Phase 5)

`GET /api/v1/statistics/summary` (`app/services/statistics_service.py`)
computes, scoped to the current user: parcels per month (last N, default
12), average delivery time, top merchant, top carrier, delayed rate, and
success rate. Two things worth knowing:

- **Monthly bucketing is done in Python**, not with a SQL date-trunc
  function (`OrderRepository.monthly_counts_for_user`) - `date_trunc` is
  Postgres-specific and SQLite/MariaDB each have their own equivalent, so
  computing it in Python keeps the query portable across all three
  supported backends at the cost of fetching one column's worth of rows.
- **Delayed rate counts history, not just current status** - a shipment
  that was once `DELAYED` and later delivered still counts, via a `UNION`
  of "currently delayed" and "has a DELAYED `TrackingEvent`"
  (`ShipmentRepository.delayed_shipment_count_for_user`).

The frontend's `StatisticsPage` renders this as a KPI row (reusing the
dashboard's `StatCard`), a single-series bar chart for parcels/month, and
two rate meters (success/delayed) - see `docs/development.md` for the
frontend layout.

## Performance and logging (Phase 5)

- Indexes were added for query patterns that already existed in the
  codebase, not speculatively: `Order.user_id` and `MailAccount.user_id`
  (every query on both tables filters by it, and unlike SQLite,
  Postgres/MariaDB don't auto-index FK columns), and
  `Shipment.tracking_status` (filtered/grouped by in the dashboard,
  tracking worker, and statistics).
- Every HTTP request is logged through `app.main`'s own logger (method,
  path, status, duration) via a middleware, so it flows through the
  rotating file handler configured in `app/core/logging.py`. Uvicorn's own
  access log is a separate logger with its own handler/format and
  **doesn't rotate** by default, so it's disabled in the Docker entrypoint
  (`--no-access-log`) to avoid a second, inconsistent log stream.

## Database portability

`app/config.py`'s `DatabaseSettings.sqlalchemy_url` is the only place that
builds a connection string. Switching between SQLite, PostgreSQL, and
MariaDB is a one-line change in `config.yaml` (`database.driver`) - no code
changes, because every query goes through SQLAlchemy Core/ORM rather than
driver-specific SQL.

## Authentication

JWT access + refresh tokens (`app/core/security.py`). Passwords are hashed
with Argon2 (bcrypt as fallback) via passlib. OAuth, LDAP, and Home
Assistant authentication are planned for later phases as additional
`app/core/security.py` strategies behind the same `get_current_user`
dependency.
