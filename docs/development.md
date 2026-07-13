# Development

## Backend

```bash
cd backend
.venv/bin/pytest                 # unit + API tests
.venv/bin/ruff check app tests   # lint
.venv/bin/ruff format app tests  # format
```

Or from the repo root: `scripts/test.sh`, `scripts/lint.sh`.

### Adding a migration

After changing a model under `app/models/`:

```bash
cd backend
.venv/bin/alembic revision --autogenerate -m "describe the change"
.venv/bin/alembic upgrade head
```

Always review the generated migration - autogenerate does not detect every
kind of change (renames, some constraint changes).

### Adding an endpoint

1. Add/extend the Pydantic schema in `app/schemas/`.
2. Add the business logic to a service in `app/services/` (raise
   `app/services/exceptions.py` errors for not-found/conflict cases - do not
   raise `HTTPException` there).
3. Add the repository query (if new) to `app/repositories/`.
4. Add the route in `app/api/v1/endpoints/`, translating service exceptions
   to HTTP status codes.
5. Add unit tests for the service and API tests for the route.

## Frontend

```bash
cd frontend
npm run dev     # dev server with hot reload, proxies /api to :8000
npm run build   # type-checks (tsc -b) then builds
npm run lint    # oxlint
```

### Project layout

```
src/api/         axios client + token storage
src/contexts/    AuthContext (session), ThemeModeContext (light/dark)
src/components/  shared UI building blocks
src/pages/       route-level components
src/types/       API response types, hand-kept in sync with backend schemas
```

## Tests

- `backend/tests/unit/` - service-layer tests against an in-memory SQLite
  database (no HTTP).
- `backend/tests/api/` - FastAPI `TestClient` tests exercising full request
  handling, including auth.

## Code style

- Python: Ruff (lint + format), full type hints, module/class-level
  docstrings explaining intent; inline comments only where the *why* isn't
  obvious from the code.
- TypeScript: strict mode (see `tsconfig.app.json`), function components,
  no default exports for shared modules.
