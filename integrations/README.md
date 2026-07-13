# integrations

Deeper platform integrations beyond generic notifications:

- **`home_assistant/`** (done) - a native Home Assistant custom integration
  (`custom_components/parcel_server/`): sensors (active parcels, next
  delivery, last delivery, top merchant, top carrier) and services
  (`refresh_tracking`, `archive_parcel`, `send_notification`). See
  `home_assistant/README.md`. Complements, rather than replaces, the
  generic MQTT Discovery sensors already published by the `mqtt/` package.
- Additional authentication providers: OAuth, LDAP, Home Assistant auth -
  not yet done, see `docs/roadmap.md`.
