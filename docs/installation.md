# Installation

Two supported paths: Docker Compose (recommended for running the server) and
a bare-metal setup (recommended for development). See
[`docker.md`](docker.md) for the Docker path and [`development.md`](development.md)
for day-to-day development workflow.

## Requirements

- Docker path: Docker Engine 24+ and the Docker Compose plugin.
- Bare-metal path: Python 3.13, Node.js 22+, and (optionally) PostgreSQL or
  MariaDB if you don't want SQLite.

## Bare-metal quick start

### Backend

```bash
cd backend
python3.13 -m venv .venv
.venv/bin/pip install -e "../tracking[dev]" -e "../importer[dev]" \
  -e "../notification[dev]" -e "../mqtt[dev]" -e ".[dev]"
cp config.example.yaml config.yaml   # review/edit before continuing
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload
```

Or simply `scripts/dev-backend.sh`, which does all of the above.

The API is now at `http://localhost:8000`, with interactive docs at
`/docs` (Swagger UI) and `/redoc` (ReDoc).

Create your first user - either via the frontend's `/register` page once
it's running (see below), or directly against the API:

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "change-me-please"}'
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dev server proxies `/api` to `http://localhost:8000` (see
`frontend/vite.config.ts`), so both must be running for the login page to
work.

### Import worker (Phase 2, optional)

To have shipping-confirmation emails picked up automatically, connect a
mailbox from the frontend's `/mailboxes` page (or `POST /api/v1/mail-accounts`
directly) - see [`mailboxes.md`](mailboxes.md) for provider-specific setup,
including the extra one-time step Outlook.com/Hotmail/Live needs. Then run
the worker:

```bash
scripts/dev-worker.sh
```

It polls every active mail account (respecting each account's own
`poll_interval_seconds`) and turns recognized confirmations into orders and
shipments. Without it running, mail accounts can still be synced manually via
`POST /api/v1/mail-accounts/{id}/sync`.

### Tracking worker (Phase 3, optional)

Set `tracking_provider.name`/`tracking_provider.api_key` in `config.yaml`
to one of `seventeentrack`, `aftership`, `trackingmore`, or `ship24`, then
run:

```bash
scripts/dev-tracking-worker.sh
```

It refreshes every non-terminal shipment's status on
`tracking_provider.poll_interval_seconds`. Without it running (or with
`tracking_provider.name: "none"`), shipments can still be refreshed
manually via `POST /api/v1/shipments/{id}/refresh-tracking`.

The same worker process also republishes MQTT sensor state (see below) on
its own interval - no separate process needed for that.

### Notifications and MQTT (Phase 4, optional)

Enable any of `notification.webhook` / `.discord` / `.telegram` / `.email`
/ `.signal` in `config.yaml` to get notified when a new shipping
confirmation is detected or a shipment becomes delivered/delayed - all are
off by default. Set `mqtt.enabled: true` (and `mqtt.host`, pointing at any
MQTT broker, e.g. Home Assistant's own Mosquitto add-on) to have the
tracking worker publish `parcel.total` / `.in_transit` /
`.delivered_today` / `.next_delivery` / `.delayed` as Home Assistant MQTT
Discovery sensors.

## Configuration

All runtime configuration lives in `backend/config.yaml`, copied from
`backend/config.example.yaml`. Nothing is read from hardcoded values or
scattered environment variables - the only environment variable the backend
looks at is `PARCEL_SERVER_CONFIG`, which lets you point at a different
config file entirely (used by the Docker image).

At minimum, change these before exposing the server beyond your own
machine:

- `security.jwt_secret_key` - generate with
  `python -c "import secrets; print(secrets.token_urlsafe(64))"`.
- `security.mail_encryption_key` - encrypts mailbox passwords at rest;
  generate with
  `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
- `database.*` - if not using SQLite.
- `server.cors_origins` - the origin(s) your frontend is served from.
- `tracking_provider.*` - if you want automatic shipment status refresh
  (Phase 3); see [Tracking worker](#tracking-worker-phase-3-optional) above.
