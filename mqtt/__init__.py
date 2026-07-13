"""MQTT publisher and Home Assistant MQTT Discovery.

Publishes ``parcel.total``, ``parcel.in_transit``, ``parcel.delivered_today``,
``parcel.next_delivery``, and ``parcel.delayed`` as Home Assistant MQTT
Discovery sensors (see :mod:`mqtt.sensors`), retained so a restarting broker
or Home Assistant instance sees the last known values immediately.
"""

from mqtt.publisher import MqttConfig, MqttPublisher
from mqtt.sensors import SENSORS, Sensor

__all__ = ["MqttConfig", "MqttPublisher", "SENSORS", "Sensor"]
