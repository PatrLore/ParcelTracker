"""Tests for the factories that turn config.yaml settings into notification
channels / an MQTT publisher / a tracking provider."""

from __future__ import annotations

from notification.channels.webhook import WebhookChannel

from app.config import Settings
from app.services.mqtt_publisher_factory import get_configured_mqtt_publisher
from app.services.notification_dispatch_factory import get_configured_notification_dispatcher


def test_dispatcher_has_no_channels_by_default(monkeypatch):
    monkeypatch.setattr(
        "app.services.notification_dispatch_factory.get_settings", lambda: Settings()
    )

    dispatcher = get_configured_notification_dispatcher()

    assert dispatcher.channels == ()


def test_dispatcher_includes_enabled_webhook_channel(monkeypatch):
    settings = Settings()
    settings.notification.webhook.enabled = True
    settings.notification.webhook.url = "https://example.com/hook"
    monkeypatch.setattr("app.services.notification_dispatch_factory.get_settings", lambda: settings)

    dispatcher = get_configured_notification_dispatcher()

    assert len(dispatcher.channels) == 1
    assert isinstance(dispatcher.channels[0], WebhookChannel)


def test_dispatcher_can_include_multiple_enabled_channels(monkeypatch):
    settings = Settings()
    settings.notification.webhook.enabled = True
    settings.notification.webhook.url = "https://example.com/hook"
    settings.notification.discord.enabled = True
    settings.notification.discord.webhook_url = "https://discord.com/api/webhooks/x/y"
    monkeypatch.setattr("app.services.notification_dispatch_factory.get_settings", lambda: settings)

    dispatcher = get_configured_notification_dispatcher()

    assert len(dispatcher.channels) == 2


def test_mqtt_publisher_is_none_when_disabled(monkeypatch):
    monkeypatch.setattr("app.services.mqtt_publisher_factory.get_settings", lambda: Settings())

    assert get_configured_mqtt_publisher() is None


def test_mqtt_publisher_is_built_when_enabled(monkeypatch):
    settings = Settings()
    settings.mqtt.enabled = True
    settings.mqtt.host = "broker.local"
    monkeypatch.setattr("app.services.mqtt_publisher_factory.get_settings", lambda: settings)

    publisher = get_configured_mqtt_publisher()

    assert publisher is not None
