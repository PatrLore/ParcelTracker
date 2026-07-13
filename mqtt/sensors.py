"""The Home Assistant MQTT Discovery sensors this package publishes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Sensor:
    key: str
    name: str
    icon: str
    unit: str | None = None


SENSORS: tuple[Sensor, ...] = (
    Sensor(key="total", name="Parcels total", icon="mdi:package-variant-closed", unit="parcels"),
    Sensor(key="in_transit", name="Parcels in transit", icon="mdi:truck-delivery", unit="parcels"),
    Sensor(
        key="delivered_today",
        name="Parcels delivered today",
        icon="mdi:package-check",
        unit="parcels",
    ),
    Sensor(key="next_delivery", name="Next delivery", icon="mdi:calendar-clock"),
    Sensor(key="delayed", name="Parcels delayed", icon="mdi:alert-circle", unit="parcels"),
)
