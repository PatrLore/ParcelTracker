# Docker

`docker-compose.yml` at the repository root runs the full stack: backend,
import worker, tracking worker, frontend, and a PostgreSQL database. Redis
is included but disabled by default (it's optional per the project spec).

The backend image's build context is the repository root, not `backend/`,
because the backend depends on the sibling `importer` and `tracking`
packages (see `docs/architecture.md`). `backend`, `worker`, and
`tracking-worker` all use the same image (`backend/Dockerfile`) - `worker`
and `tracking-worker` just override the entrypoint to run `app.worker`
(mail-account polling, Phase 2) or `app.tracking_worker` (shipment status
refresh, Phase 3) instead of Uvicorn.

## First run

```bash
cp .env.example .env                                   # Postgres credentials
cp backend/config.docker.example.yaml backend/config.yaml
```

Edit `backend/config.yaml`:

- `database.password` must match `POSTGRES_PASSWORD` in `.env`.
- `security.jwt_secret_key` - generate a real secret before anything but
  local experimentation:
  `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`.
- `tracking_provider.name` / `tracking_provider.api_key` - set these to
  enable automatic tracking-status refresh (Phase 3). Leave `name: "none"`
  to skip it; the `tracking-worker` container idles harmlessly in that case.

Then:

```bash
docker compose up --build
```

- Backend: `http://localhost:8000` (docs at `/docs`).
- Frontend: `http://localhost:5173`.
- Both the `backend` and `worker` containers run `alembic upgrade head` on
  every start (see `backend/entrypoint.sh` / `backend/worker-entrypoint.sh`),
  so migrations are always applied automatically, whichever starts first.
- Add a mail account via `POST /api/v1/mail-accounts` (or the frontend, once
  that UI lands) and the `worker` container polls it automatically once its
  `poll_interval_seconds` has elapsed.
- With a `tracking_provider` configured, the `tracking-worker` container
  refreshes every non-terminal shipment's status on
  `tracking_provider.poll_interval_seconds`. You can also trigger a refresh
  for one shipment on demand via `POST /shipments/{id}/refresh-tracking`.

## Why Postgres in Docker but SQLite by default outside it?

`config.example.yaml` (bare-metal/dev) defaults to SQLite because it needs
no extra services. `docker-compose.yml` provisions a `db` (Postgres)
container because a multi-container deployment is the point at which a
real database service pays for itself - concurrent access from more than
one process, backups, etc. Switching `backend/config.yaml`'s
`database.driver` back to `sqlite` inside Docker works too; the `db`
service would then simply go unused (drop `depends_on: db` from the
`backend` service if you do this).

## Optional Redis

```bash
docker compose --profile redis up --build
```

Also set `redis.enabled: true` in `backend/config.yaml` (host `redis`,
port `6379`) once a feature that uses it (e.g. background job queues in a
later phase) needs it.

## Rebuilding after dependency changes

```bash
docker compose build --no-cache backend worker tracking-worker  # after editing
                                                                  # backend/pyproject.toml,
                                                                  # importer/pyproject.toml, or
                                                                  # tracking/pyproject.toml
docker compose build --no-cache frontend                         # after editing frontend/package.json
```

## Logs and data persistence

- Postgres data: named volume `db-data`.
- Backend/worker/tracking-worker logs: named volume `backend-logs`, mounted
  at `/app/backend/logs` (see `logging.directory` in `config.yaml`).
