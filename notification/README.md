# notification

Plugin-based notification dispatch. A standalone, database-free Python
package - see `docs/architecture.md`.

## Channels

- `channels/webhook.py` - generic outgoing webhook (JSON POST).
- `channels/discord.py` - Discord incoming webhook.
- `channels/telegram.py` - Telegram Bot API.
- `channels/email_smtp.py` - SMTP email.
- `channels/signal.py` - Signal, via a self-hosted
  [signal-cli-rest-api](https://github.com/bbernhard/signal-cli-rest-api)
  sidecar (Signal has no official bot/webhook API of its own).

Each implements `channel.NotificationChannel` (`send(message)`).
`dispatcher.NotificationDispatcher` fans a `NotificationMessage` out to a
list of channels, isolating one channel's failure from the rest - unlike
the email importer's merchant parsers, channels are not auto-discovered:
each needs distinct credentials, so which ones are active is an explicit,
config-driven list (see `app/services/notification_dispatch_factory.py`
on the backend side).

(MQTT / Home Assistant Discovery is the separate `mqtt` package - it
publishes ongoing sensor state rather than one-off messages.)

## Adding a channel

Add a new module to `channels/` implementing `NotificationChannel`, then
wire it into `app/services/notification_dispatch_factory.py` and give it a
settings block in `app/config.py`'s `NotificationSettings`. See any existing
channel for the shape, and `tests/test_channels_http.py` /
`tests/test_email_smtp.py` for how to test one without real network/SMTP
access.

## Tests

```bash
cd notification && ../backend/.venv/bin/pytest
```
