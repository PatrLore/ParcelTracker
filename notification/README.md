# notification

Phase 4. Plugin-based notification dispatch.

Planned channels: MQTT, Home Assistant, Telegram, Signal, Discord, Email,
and generic webhooks. Each channel implements a shared `NotificationChannel`
interface (mirroring `tracking.TrackingProvider`) so new channels can be
added without touching the dispatch core.
