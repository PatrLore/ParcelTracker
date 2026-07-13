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

## Relationship to the dedicated Home Assistant integration

A dedicated Home Assistant *custom integration* (its own
`custom_components/parcel_server/` with native sensors and services, as
opposed to generic MQTT Discovery) now lives at
`integrations/home_assistant/` - see its README. It complements this
package rather than replacing it: MQTT Discovery still gets sensors into
Home Assistant with zero extra setup (just an MQTT broker), while the
custom integration adds a config flow and the three services
(`refresh_tracking`, `archive_parcel`, `send_notification`) MQTT alone
can't express.
