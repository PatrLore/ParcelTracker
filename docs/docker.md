# Docker

`docker-compose.yml` at the repository root runs the full stack: backend,
frontend, and a PostgreSQL database. Redis is included but disabled by
default (it's optional per the project spec).

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

Then:

```bash
docker compose up --build
```

- Backend: `http://localhost:8000` (docs at `/docs`).
- Frontend: `http://localhost:5173`.
- The backend container runs `alembic upgrade head` on every start before
  launching Uvicorn (see `backend/entrypoint.sh`), so migrations are always
  applied automatically.

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
docker compose build --no-cache backend   # after editing backend/pyproject.toml
docker compose build --no-cache frontend  # after editing frontend/package.json
```

## Logs and data persistence

- Postgres data: named volume `db-data`.
- Backend logs: named volume `backend-logs`, mounted at `/app/logs` (see
  `logging.directory` in `config.yaml`).
