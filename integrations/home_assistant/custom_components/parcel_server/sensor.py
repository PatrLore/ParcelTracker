"""The five sensors this integration exposes: active parcel count, next
delivery, last delivery, top merchant, top carrier."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CARRIER,
    ATTR_MERCHANT,
    ATTR_ORDER_ID,
    ATTR_SHIPMENT_ID,
    ATTR_TRACKING_NUMBER,
    DOMAIN,
)
from .coordinator import NextOrLastDelivery, ParcelServerDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: ParcelServerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            ParcelServerActiveParcelsSensor(coordinator, entry),
            ParcelServerNextDeliverySensor(coordinator, entry),
            ParcelServerLastDeliverySensor(coordinator, entry),
            ParcelServerTopMerchantSensor(coordinator, entry),
            ParcelServerTopCarrierSensor(coordinator, entry),
        ]
    )


class ParcelServerSensorBase(CoordinatorEntity[ParcelServerDataUpdateCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: ParcelServerDataUpdateCoordinator, entry: ConfigEntry, key: str
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Parcel Server",
            manufacturer="Parcel Server",
            configuration_url=entry.data.get("base_url"),
        )


class ParcelServerActiveParcelsSensor(ParcelServerSensorBase):
    _attr_translation_key = "active_parcels"
    _attr_native_unit_of_measurement = "parcels"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:package-variant-closed"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "active_parcels")

    @property
    def native_value(self) -> int:
        dashboard = self.coordinator.data["dashboard"]
        return dashboard["in_transit"] + dashboard["delayed"] + dashboard["new_confirmations"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        dashboard = self.coordinator.data["dashboard"]
        statistics = self.coordinator.data["statistics"]
        return {
            "in_transit": dashboard["in_transit"],
            "delayed": dashboard["delayed"],
            "new_confirmations": dashboard["new_confirmations"],
            "expected_tomorrow": dashboard["expected_tomorrow"],
            "delivered_today": dashboard["delivered_today"],
            "total_shipments_lifetime": statistics["total_shipments"],
        }


class _DeliverySensorBase(ParcelServerSensorBase):
    _attr_device_class = SensorDeviceClass.DATE

    def _delivery(self) -> NextOrLastDelivery:
        raise NotImplementedError

    @property
    def native_value(self):
        return self._delivery().date

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        delivery = self._delivery()
        return {
            ATTR_MERCHANT: delivery.merchant,
            ATTR_CARRIER: delivery.carrier,
            ATTR_TRACKING_NUMBER: delivery.tracking_number,
            ATTR_ORDER_ID: delivery.order_id,
            ATTR_SHIPMENT_ID: delivery.shipment_id,
        }


class ParcelServerNextDeliverySensor(_DeliverySensorBase):
    _attr_translation_key = "next_delivery"
    _attr_icon = "mdi:truck-delivery-outline"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "next_delivery")

    def _delivery(self) -> NextOrLastDelivery:
        return self.coordinator.data["next_delivery"]


class ParcelServerLastDeliverySensor(_DeliverySensorBase):
    _attr_translation_key = "last_delivery"
    _attr_icon = "mdi:package-variant"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "last_delivery")

    def _delivery(self) -> NextOrLastDelivery:
        return self.coordinator.data["last_delivery"]


class ParcelServerTopMerchantSensor(ParcelServerSensorBase):
    _attr_translation_key = "top_merchant"
    _attr_icon = "mdi:storefront-outline"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "top_merchant")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data["statistics"]["top_merchant"]


class ParcelServerTopCarrierSensor(ParcelServerSensorBase):
    _attr_translation_key = "top_carrier"
    _attr_icon = "mdi:truck-outline"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "top_carrier")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data["statistics"]["top_carrier"]
