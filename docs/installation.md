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
.venv/bin/pip install -e ".[dev]"
cp config.example.yaml config.yaml   # review/edit before continuing
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload
```

The API is now at `http://localhost:8000`, with interactive docs at
`/docs` (Swagger UI) and `/redoc` (ReDoc).

Create your first user:

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
- `database.*` - if not using SQLite.
- `server.cors_origins` - the origin(s) your frontend is served from.
