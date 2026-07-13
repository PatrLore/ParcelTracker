"""Config flow: collect the backend URL and account credentials, verify
them with a real login call before the entry is created."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ParcelServerApiClient, ParcelServerAuthError, ParcelServerError
from .const import CONF_BASE_URL, CONF_VERIFY_SSL, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BASE_URL): str,
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_VERIFY_SSL, default=True): bool,
    }
)


async def _validate_login(hass: HomeAssistant, data: dict[str, Any]) -> None:
    session = async_get_clientsession(hass, verify_ssl=data[CONF_VERIFY_SSL])
    client = ParcelServerApiClient(
        session,
        data[CONF_BASE_URL],
        data[CONF_EMAIL],
        data[CONF_PASSWORD],
        verify_ssl=data[CONF_VERIFY_SSL],
    )
    await client.async_login()


class ParcelServerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handles a config flow for Parcel Server."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_BASE_URL] = user_input[CONF_BASE_URL].rstrip("/")
            await self.async_set_unique_id(f"{user_input[CONF_BASE_URL]}:{user_input[CONF_EMAIL]}")
            self._abort_if_unique_id_configured()

            try:
                await _validate_login(self.hass, user_input)
            except ParcelServerAuthError:
                errors["base"] = "invalid_auth"
            except ParcelServerError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=user_input[CONF_EMAIL], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
