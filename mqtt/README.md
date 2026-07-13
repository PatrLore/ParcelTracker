# mqtt

MQTT integration with Home Assistant MQTT Discovery. A standalone,
database-free Python package - see `docs/architecture.md`.

## Sensors

- `parcel.total`
- `parcel.in_transit`
- `parcel.delivered_today`
- `parcel.next_delivery`
- `parcel.delayed`

`publisher.MqttPublisher.publish_discovery()` announces all five under
Home Assistant's Discovery topic convention
(`homeassistant/sensor/parcel_server_<key>/config`, retained);
`publish_state(values)` pushes current values to
`parcel_server/<key>/state` (also retained, so a restarting broker/Home
Assistant sees the last known values immediately).

## Tests

```bash
cd mqtt && ../backend/.venv/bin/pytest
```

## Out of scope for this repository

A dedicated Home Assistant *custom integration* (its own
`custom_components/parcel_server/` with native sensors and services, as
opposed to generic MQTT Discovery) is a separate deliverable - it would
live in its own repository following Home Assistant's integration
structure, not here. MQTT Discovery gets the same sensors into Home
Assistant today without that extra project.
