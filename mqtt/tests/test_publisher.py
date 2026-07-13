"""Tests for MqttPublisher, using a fake MQTT client (no real broker)."""

from __future__ import annotations

import json

from mqtt.publisher import MqttConfig, MqttPublisher
from mqtt.sensors import SENSORS


class FakeMqttClient:
    def __init__(self, client_id: str | None = None) -> None:
        self.client_id = client_id
        self.credentials: tuple[str, str] | None = None
        self.connected_to: tuple[str, int] | None = None
        self.published: list[tuple[str, str, bool]] = []
        self.disconnected = False

    def username_pw_set(self, username: str, password: str) -> None:
        self.credentials = (username, password)

    def connect(self, host: str, port: int) -> None:
        self.connected_to = (host, port)

    def loop_start(self) -> None:
        pass

    def loop_stop(self) -> None:
        pass

    def disconnect(self) -> None:
        self.disconnected = True

    def publish(self, topic: str, payload: str, retain: bool = False) -> None:
        self.published.append((topic, payload, retain))


def test_connect_uses_configured_credentials():
    client = FakeMqttClient()
    config = MqttConfig(host="broker.local", port=1883, username="user", password="pass")
    publisher = MqttPublisher(config, client=client)

    publisher.connect()

    assert client.credentials == ("user", "pass")
    assert client.connected_to == ("broker.local", 1883)


def test_publish_discovery_announces_every_sensor_retained():
    client = FakeMqttClient()
    publisher = MqttPublisher(MqttConfig(host="broker.local"), client=client)

    publisher.publish_discovery()

    assert len(client.published) == len(SENSORS)
    for topic, payload, retain in client.published:
        assert topic.startswith("homeassistant/sensor/parcel_server_")
        assert retain is True
        body = json.loads(payload)
        assert "unique_id" in body
        assert "state_topic" in body


def test_publish_state_sends_only_known_sensor_values():
    client = FakeMqttClient()
    publisher = MqttPublisher(MqttConfig(host="broker.local"), client=client)

    publisher.publish_state({"total": 5, "in_transit": 2, "unknown_key": 99})

    published_topics = {topic for topic, _, _ in client.published}
    assert "parcel_server/total/state" in published_topics
    assert "parcel_server/in_transit/state" in published_topics
    assert not any("unknown_key" in topic for topic in published_topics)
    assert all(retain for _, _, retain in client.published)


def test_disconnect_calls_client_disconnect():
    client = FakeMqttClient()
    publisher = MqttPublisher(MqttConfig(host="broker.local"), client=client)

    publisher.disconnect()

    assert client.disconnected is True
