# tests

Backend unit and API tests live in `backend/tests/` (co-located with the
`backend/pyproject.toml` that configures pytest). This top-level directory
is reserved for cross-cutting end-to-end tests once the frontend and
backend are exercised together (e.g. Playwright flows) in a later phase.
