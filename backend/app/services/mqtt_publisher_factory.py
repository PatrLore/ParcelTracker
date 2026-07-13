"""Builds the MQTT publisher configured in ``config.yaml``."""

from __future__ import annotations

from mqtt import MqttConfig, MqttPublisher

from app.config import get_settings


def get_configured_mqtt_publisher() -> MqttPublisher | None:
    """Returns the configured publisher, or ``None`` if MQTT is disabled."""
    settings = get_settings().mqtt
    if not settings.enabled:
        return None
    return MqttPublisher(
        MqttConfig(
            host=settings.host,
            port=settings.port,
            username=settings.username,
            password=settings.password,
        )
    )
