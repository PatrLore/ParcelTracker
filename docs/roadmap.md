# Roadmap

## Phase 1 - Foundation (done)

- Project scaffold, layered backend architecture, Docker Compose.
- SQLAlchemy models + Alembic migrations (User, Order, Shipment,
  TrackingEvent, Carrier, Email).
- FastAPI REST API with JWT auth, rate limiting, security headers.
- React + TypeScript + MUI frontend: login, dashboard, dark/light mode.
- Unit + API test suites.

## Phase 2 - Email import

- IMAP importer (`importer/`): IDLE + polling, multiple mailboxes/users,
  folder watching.
- Pluggable merchant parsers (Amazon, eBay, Otto, MediaMarkt, Saturn, IKEA,
  Temu, Kaufland, AliExpress, Decathlon, Zalando, Alternate, ...).
- Orders created/updated from parsed confirmations.

## Phase 3 - Tracking

- `tracking.TrackingProvider` implementations (17TRACK, AfterShip,
  TrackingMore, Ship24, direct carrier APIs).
- Modular carrier tracking-number detection (DHL, DHL Express, Deutsche
  Post, UPS, DPD, GLS, Hermes, FedEx, USPS, Cainiao, YunExpress, Amazon
  Logistics, Royal Mail, PostNL, ...).
- Scheduled status refresh, full tracking-history persistence.

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
