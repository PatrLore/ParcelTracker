# Development

## Backend

```bash
cd backend
.venv/bin/pytest                 # unit + API tests
.venv/bin/ruff check app tests   # lint
.venv/bin/ruff format app tests  # format
```

Or from the repo root: `scripts/test.sh`, `scripts/lint.sh`.

## importer, tracking, notification, and mqtt

These are separate, installable packages at the repo root (see
`docs/architecture.md`) - they have no database or FastAPI dependency, so
their own test suites run standalone:

```bash
cd importer && ../backend/.venv/bin/pytest
cd tracking && ../backend/.venv/bin/pytest
cd notification && ../backend/.venv/bin/pytest
cd mqtt && ../backend/.venv/bin/pytest
```

`scripts/dev-backend.sh` installs all four (`pip install -e ../tracking
-e ../importer -e ../notification -e ../mqtt`) into `backend/.venv`
alongside the backend itself, so backend code can `import importer` /
`import tracking` / `import notification` / `import mqtt` directly.

### Adding a merchant parser

Add a new module to `importer/parsers/` subclassing
`importer.parsers._regex_parser.RegexMerchantParser` (or
`importer.parsers.base.MerchantParser` directly for non-regex cases) -
`importer.parsers.registry` discovers it automatically via `pkgutil`. No
other file needs to change. See any existing parser (e.g.
`importer/parsers/amazon.py`) for the shape, and
`importer/tests/test_parsers.py` for how to test one with a crafted
`RawEmail` fixture.

### Adding a carrier

Add one entry to `CARRIER_PATTERNS` (and `_DETECTION_ORDER`, for
disambiguation against overlapping digit-length formats) in
`tracking/carriers.py`.

### Adding a tracking provider

Add a new module to `tracking/providers/` implementing
`tracking.provider.TrackingProvider` (`register()` / `update()` /
`remove()`), then register it in `tracking/providers/factory.py`'s
`_PROVIDERS` dict and `app/config.py`'s `TrackingProviderSettings.name`
literal. See any existing provider (e.g. `tracking/providers/aftership.py`)
for the shape, and `tracking/tests/test_providers.py` for how to test one
against `httpx.MockTransport` - no real API credentials or network access
needed.

### Adding a notification channel

Add a new module to `notification/channels/` implementing
`notification.channel.NotificationChannel` (`send(message)`), then wire it
into `app/services/notification_dispatch_factory.py`'s
`get_configured_notification_dispatcher()` and give it a settings block in
`app/config.py`'s `NotificationSettings`. See any existing channel (e.g.
`notification/channels/discord.py`) for the shape, and
`notification/tests/test_channels_http.py` /
`test_email_smtp.py` for how to test one without real network/SMTP access.

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
