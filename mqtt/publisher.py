"""MQTT publisher with Home Assistant MQTT Discovery.

Publishes the sensors in :mod:`mqtt.sensors` under Home Assistant's
Discovery topic convention (``homeassistant/sensor/<id>/config``), so
Home Assistant - or any other MQTT-Discovery-aware consumer - picks them
up automatically; no manual entity configuration needed on the consuming
side.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import paho.mqtt.client as mqtt

from mqtt.sensors import SENSORS, Sensor

_DISCOVERY_PREFIX = "homeassistant"
_DEVICE_ID = "parcel_server"


@dataclass(frozen=True)
class MqttConfig:
    host: str
    port: int = 1883
    username: str = ""
    password: str = ""
    client_id: str = "parcel-server"


class MqttPublisher:
    def __init__(self, config: MqttConfig, client: mqtt.Client | None = None) -> None:
        self._config = config
        self._client = client or mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=config.client_id
        )
        if config.username:
            self._client.username_pw_set(config.username, config.password)

    def connect(self) -> None:
        """Connect and start the background network loop.

        A short-lived publisher (connect - publish a few messages -
        disconnect, as used by the tracking worker's periodic tick) needs
        the loop running for ``publish()`` calls to actually reach the
        broker - paho-mqtt queues messages internally otherwise.
        """
        self._client.connect(self._config.host, self._config.port)
        self._client.loop_start()

    def disconnect(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    def publish_discovery(self) -> None:
        """Publish (retained) HA MQTT Discovery config for every sensor."""
        for sensor in SENSORS:
            self._client.publish(
                _discovery_topic(sensor), json.dumps(_discovery_payload(sensor)), retain=True
            )

    def publish_state(self, values: dict[str, str | int]) -> None:
        """Publish current sensor values, keyed by :attr:`Sensor.key`."""
        for sensor in SENSORS:
            if sensor.key in values:
                self._client.publish(_state_topic(sensor), str(values[sensor.key]), retain=True)


def _state_topic(sensor: Sensor) -> str:
    return f"{_DEVICE_ID}/{sensor.key}/state"


def _discovery_topic(sensor: Sensor) -> str:
    return f"{_DISCOVERY_PREFIX}/sensor/{_DEVICE_ID}_{sensor.key}/config"


def _discovery_payload(sensor: Sensor) -> dict:
    payload = {
        "name": sensor.name,
        "unique_id": f"{_DEVICE_ID}_{sensor.key}",
        "state_topic": _state_topic(sensor),
        "icon": sensor.icon,
        "device": {
            "identifiers": [_DEVICE_ID],
            "name": "Parcel Server",
            "manufacturer": "Parcel Server",
        },
    }
    if sensor.unit:
        payload["unit_of_measurement"] = sensor.unit
    return payload
