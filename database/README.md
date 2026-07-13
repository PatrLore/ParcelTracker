# database

Schema migrations live with the application code that owns them, in
`backend/alembic/`. This directory is for database-adjacent assets that are
*not* migrations: entity-relationship documentation, seed/fixture data for
local development, and (later) driver-specific tuning notes for the optional
PostgreSQL/MariaDB backends.

See [`docs/architecture.md`](../docs/architecture.md) for the current data
model.
