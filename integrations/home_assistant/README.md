# Home Assistant custom integration

A native Home Assistant `custom_components/parcel_server/` integration -
distinct from the generic MQTT Discovery sensors the `mqtt/` package already
publishes (see `mqtt/README.md`). This one talks to the backend's REST API
(`/api/v1`) directly, so it needs a config flow (base URL + account login)
and can offer services the MQTT sensors can't: triggering a tracking
refresh, archiving a parcel, and sending an ad-hoc notification.

The integration's code lives at `/custom_components/parcel_server/` (the
repository root), not under this directory - HACS requires
`custom_components/<domain>/` to be at the repository root, so it can't
live alongside this README/its tests/its dev tooling, which stay here.

## Installation

### Via HACS (recommended)

1. In Home Assistant, go to HACS → the three-dot menu (top right) →
   **Custom repositories**.
2. Add `https://github.com/PatrLore/ParcelTracker`, type **Integration**.
3. Find "Parcel Server" in HACS and install it.
4. Restart Home Assistant.
5. Settings → Devices & Services → Add Integration → "Parcel Server".
6. Enter the backend's base URL (e.g. `http://parcel-server.local:8000`)
   and the email/password of a Parcel Server account. The config flow logs
   in immediately to verify the credentials before creating the entry.

### Manual

1. Copy `/custom_components/parcel_server/` (repo root, not this directory)
   into your Home Assistant config directory, e.g.
   `<config>/custom_components/parcel_server/`.
2. Restart Home Assistant and continue from step 5 above.

Alternatively, `.github/workflows/release-ha-integration.yml` can build a
versioned `parcel_server.zip` (Actions tab → "Release Home Assistant
integration" → Run workflow) if you'd rather download one release asset
than copy a folder - not required for HACS, just a manual-install
convenience.

## Sensors

One "Parcel Server" device with five sensors, refreshed every 60 seconds:

- **Active parcels** - count of shipments in transit, delayed, or newly
  confirmed (mirrors `GET /dashboard/summary`, and is archived-order-aware:
  see `docs/roadmap.md`); attributes break out each status plus the
  lifetime `total_shipments` from `GET /statistics/summary`.
- **Next delivery** - the soonest `estimated_delivery_date` among
  non-terminal shipments (a `date` sensor); attributes: merchant, carrier,
  tracking number, order ID, shipment ID.
- **Last delivery** - the most recent `delivery_date` among delivered
  shipments, same attributes as above.
- **Top merchant** / **Top carrier** - from the lifetime statistics
  summary.

Next/last delivery are computed client-side from `GET /orders` (which
nests each order's shipments) since the backend has no single endpoint for
"the next delivery date across one user's shipments" - see
`coordinator.py`.

## Services

- `parcel_server.refresh_tracking` - `shipment_id` (required). Calls
  `POST /shipments/{id}/refresh-tracking`.
- `parcel_server.archive_parcel` - `order_id` (required), `archived`
  (optional, default `true`). Calls `POST /orders/{id}/archive`.
- `parcel_server.send_notification` - `title`, `message` (both required),
  `event` (optional, default `manual`). Calls `POST /notifications/send`,
  fanning the message out through every notification channel configured
  on the backend.

All three are registered once per Home Assistant instance (not per config
entry) and target the first configured Parcel Server account - see the
comment in `__init__.py` if you run more than one account.

## Development

`api.py` (the REST client) has no `homeassistant.*` imports, so it's unit
tested standalone against a real in-process aiohttp server (no live
network, no Home Assistant runtime required):

```bash
cd integrations/home_assistant
python3 -m venv .venv && .venv/bin/pip install -r requirements_test.txt
.venv/bin/pytest
cd ../..   # back to the repo root - custom_components/ lives there
backend/.venv/bin/ruff check custom_components integrations/home_assistant/tests
```

The rest of the integration (`__init__.py`, `config_flow.py`,
`coordinator.py`, `sensor.py`) follows Home Assistant's standard
integration structure and requires a real Home Assistant instance (or the
`pytest-homeassistant-custom-component` test harness, not set up here) to
exercise end-to-end - it has not been validated against a live Home
Assistant instance, matching this project's documented stance on
not-yet-live-validated integrations (see `docs/roadmap.md`).
