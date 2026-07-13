"""The Parcel Server integration: native Home Assistant sensors and services
for a self-hosted Parcel Server backend, talking to its REST API
(``/api/v1``) rather than the generic MQTT Discovery sensors the ``mqtt``
package already publishes (see ``mqtt/README.md``) - this integration adds
config-flow setup and the services the MQTT sensors can't provide
(refresh_tracking, archive_parcel, send_notification)."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ParcelServerApiClient, ParcelServerError
from .const import (
    ATTR_ARCHIVED,
    ATTR_EVENT,
    ATTR_MESSAGE,
    ATTR_ORDER_ID,
    ATTR_SHIPMENT_ID,
    ATTR_TITLE,
    CONF_BASE_URL,
    CONF_VERIFY_SSL,
    DOMAIN,
    SERVICE_ARCHIVE_PARCEL,
    SERVICE_REFRESH_TRACKING,
    SERVICE_SEND_NOTIFICATION,
)
from .coordinator import ParcelServerDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

REFRESH_TRACKING_SCHEMA = vol.Schema({vol.Required(ATTR_SHIPMENT_ID): cv.positive_int})
ARCHIVE_PARCEL_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ORDER_ID): cv.positive_int,
        vol.Optional(ATTR_ARCHIVED, default=True): cv.boolean,
    }
)
SEND_NOTIFICATION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TITLE): cv.string,
        vol.Required(ATTR_MESSAGE): cv.string,
        vol.Optional(ATTR_EVENT, default="manual"): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass, verify_ssl=entry.data.get(CONF_VERIFY_SSL, True))
    client = ParcelServerApiClient(
        session,
        entry.data[CONF_BASE_URL],
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
        verify_ssl=entry.data.get(CONF_VERIFY_SSL, True),
    )

    coordinator = ParcelServerDataUpdateCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    _register_services(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            for service in (
                SERVICE_REFRESH_TRACKING,
                SERVICE_ARCHIVE_PARCEL,
                SERVICE_SEND_NOTIFICATION,
            ):
                hass.services.async_remove(DOMAIN, service)
    return unloaded


def _register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_REFRESH_TRACKING):
        return  # Already registered by a previously-set-up entry.

    def _any_client() -> ParcelServerApiClient:
        # Services are registered once per domain, not per config entry, so
        # with more than one Parcel Server account configured this always
        # targets the first one set up. Fine for the common single-account
        # setup; multi-account service targeting would need its own field.
        coordinator: ParcelServerDataUpdateCoordinator = next(iter(hass.data[DOMAIN].values()))
        return coordinator.client

    async def _handle_refresh_tracking(call: ServiceCall) -> None:
        try:
            await _any_client().async_refresh_tracking(call.data[ATTR_SHIPMENT_ID])
        except ParcelServerError as exc:
            raise HomeAssistantError(str(exc)) from exc

    async def _handle_archive_parcel(call: ServiceCall) -> None:
        try:
            await _any_client().async_archive_order(
                call.data[ATTR_ORDER_ID], call.data[ATTR_ARCHIVED]
            )
        except ParcelServerError as exc:
            raise HomeAssistantError(str(exc)) from exc

    async def _handle_send_notification(call: ServiceCall) -> None:
        try:
            await _any_client().async_send_notification(
                call.data[ATTR_TITLE], call.data[ATTR_MESSAGE], call.data[ATTR_EVENT]
            )
        except ParcelServerError as exc:
            raise HomeAssistantError(str(exc)) from exc

    hass.services.async_register(
        DOMAIN, SERVICE_REFRESH_TRACKING, _handle_refresh_tracking, schema=REFRESH_TRACKING_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_ARCHIVE_PARCEL, _handle_archive_parcel, schema=ARCHIVE_PARCEL_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_NOTIFICATION,
        _handle_send_notification,
        schema=SEND_NOTIFICATION_SCHEMA,
    )
