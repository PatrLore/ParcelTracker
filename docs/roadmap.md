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

## Phase 4 - Notifications & integrations

- `notification/` plugin channels: MQTT, Home Assistant, Telegram, Signal,
  Discord, Email, webhooks.
- `mqtt/` MQTT Discovery sensors (`parcel.total`, `parcel.in_transit`,
  `parcel.delivered_today`, `parcel.next_delivery`, `parcel.delayed`).
- `integrations/` Home Assistant custom integration (sensors + services),
  additional auth providers (OAuth, LDAP, Home Assistant auth).

## Phase 5 - Statistics & polish

- Dashboard analytics: parcels per month, average delivery time, top
  merchant/carrier, delay rate, success rate.
- Performance passes, structured-logging refinements, log rotation
  hardening.
