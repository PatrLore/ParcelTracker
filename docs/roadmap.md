# Roadmap

## Phase 1 - Foundation (done)

- Project scaffold, layered backend architecture, Docker Compose.
- SQLAlchemy models + Alembic migrations (User, Order, Shipment,
  TrackingEvent, Carrier, Email).
- FastAPI REST API with JWT auth, rate limiting, security headers.
- React + TypeScript + MUI frontend: login, dashboard, dark/light mode.
- Unit + API test suites.

## Phase 2 - Email import (done)

- IMAP importer (`importer/`): polling implemented (per-mailbox interval);
  IMAP IDLE supported at the client level, not yet wired into a background
  runner. Multiple mailboxes/users via the `MailAccount` model.
- Pluggable merchant parsers, auto-discovered (Amazon, eBay, Otto,
  MediaMarkt, Saturn, IKEA, Temu, Kaufland, AliExpress, Decathlon, Zalando,
  Alternate).
- Modular carrier tracking-number detection (`tracking/carriers.py`): DHL,
  DHL Express, Deutsche Post, UPS, DPD, GLS, Hermes, FedEx, USPS, Cainiao,
  YunExpress, Amazon Logistics, Royal Mail, PostNL.
- Orders and shipments created/updated from parsed confirmations
  (`EmailIngestionService`), via a standalone worker process/container.
- Mailbox passwords encrypted at rest (Fernet).
- Not yet done: real-world tuning of the parser regexes against actual
  provider emails (current patterns are best-effort, based on documented/
  typical formats - see `docs/development.md` on adding/refining a parser),
  and folder-watching beyond a single configured `folder` per mailbox.

## Phase 3 - Tracking (done)

- `tracking.TrackingProvider` implementations: 17TRACK, AfterShip,
  TrackingMore, Ship24 (`tracking/providers/`), each behind the shared
  interface via `tracking.providers.factory.create_provider`.
- Scheduled status refresh: a standalone tracking worker
  (`app/tracking_worker.py`) polls every non-terminal shipment on the
  interval configured in `tracking_provider.poll_interval_seconds`; a
  manual `POST /shipments/{id}/refresh-tracking` endpoint is also available.
- Full tracking-history persistence: every new provider event becomes a
  `TrackingEvent` row, deduplicated by `(status, occurred_at)`.
- Not yet done: direct carrier APIs (DHL, UPS, ... as tracking providers in
  their own right, rather than only as detected-from-tracking-number
  metadata) - the roadmap's original "direct carrier APIs" item. Also not
  done: the four providers' response-parsing has not been validated against
  their live APIs (see each provider module's docstring) - only against
  fabricated responses matching their published schemas.

## Phase 4 - Notifications & integrations (partially done)

- `notification/` plugin channels (done): generic webhook, Discord,
  Telegram, Email (SMTP), and Signal (via a self-hosted
  signal-cli-rest-api sidecar - Signal has no official bot API of its
  own). Each is independently enabled in `config.yaml`; a
  `NotificationDispatcher` fans a message out to every enabled channel,
  isolating one channel's failure from the rest. A manual trigger
  (`POST /notifications/send`) fans an ad-hoc message out the same way -
  added for the Home Assistant integration's `send_notification` service,
  useful standalone too.
- `mqtt/` MQTT Discovery sensors (done): `parcel.total`, `parcel.in_transit`,
  `parcel.delivered_today`, `parcel.next_delivery`, `parcel.delayed`,
  published (retained) via Home Assistant's MQTT Discovery convention.
- Wired into the backend (done): a new order/shipment confirmation, and a
  shipment transitioning to delivered/delayed, both dispatch a
  notification; the tracking worker also republishes MQTT sensor state on
  its own configurable interval.
- `integrations/home_assistant/` - Home Assistant *custom integration*
  (done): native sensors (active parcels, next/last delivery, top
  merchant/carrier) and services (`refresh_tracking`, `archive_parcel`,
  `send_notification`), talking to the REST API via a config flow rather
  than MQTT Discovery - see `integrations/home_assistant/README.md`. Its
  `archive_parcel` service is backed by a new `Order.archived` flag
  (`POST /orders/{id}/archive`) that also excludes archived orders'
  shipments from the dashboard summary (statistics stay lifetime-inclusive
  - see `app/services/dashboard_service.py`). Not yet done: end-to-end
  validation against a live Home Assistant instance (only the REST client,
  `api.py`, has an automated test suite - the config flow/coordinator/
  sensor platform require the `homeassistant` package itself to exercise,
  which isn't installed in this repo).
- `dist/parcel-server-card.js` - a matching Lovelace dashboard card (done):
  a dependency-free vanilla Web Component reading the integration's five
  sensors, distributed as a separate HACS *plugin*-category entry from the
  integration above (same repo, two independent HACS "custom repository"
  entries - see `integrations/home_assistant/README.md`). Not yet done:
  the same live-validation gap as the integration - only checked with
  Node's `--check` (syntax), never rendered inside an actual Home
  Assistant dashboard.
- Additional auth providers (OAuth, LDAP, Home Assistant auth) - not done.
- Not yet done: the four HTTP-based channels' request/response handling has
  not been validated against the live APIs (see each channel module's
  docstring) - only against fabricated responses/fakes.

## Phase 5 - Statistics & polish (done)

- Statistics endpoint (`GET /api/v1/statistics/summary`) and a frontend
  page: parcels per month (bar chart), average delivery time, top
  merchant, top carrier, delayed rate, success rate - all scoped to the
  authenticated user, computed portably across SQLite/PostgreSQL/MariaDB
  (monthly bucketing done in Python rather than a DB-specific date-trunc
  function).
- Performance: added indexes that were missing for the query patterns
  already in the codebase - `Order.user_id`, `MailAccount.user_id` (every
  query on both tables filters by it; FK columns aren't auto-indexed by
  Postgres/MariaDB), and `Shipment.tracking_status` (filtered/grouped by
  in the dashboard, tracking worker, and statistics).
- Logging: every HTTP request is now logged through the app's own logger
  (method, path, status, duration), so it flows through the rotating file
  handler; Uvicorn's own access log is disabled in the Docker entrypoint
  to avoid a second, non-rotating log stream with a different format.
- Not yet done: pagination/rate-limit tuning under real load (no load
  testing has been done against this codebase), and pushing the parcels-
  per-month chart's month count into user-configurable UI (currently a
  `months` query param, default 12, not yet exposed as a control).
