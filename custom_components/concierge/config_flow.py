"""Config flow for Concierge."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_ENABLE_NOTIFICATIONS,
    CONF_NIGHT_MODE_ENABLED,
    CONF_UPDATE_INTERVAL_SECONDS,
    COORDINATOR_MAX_UPDATE_SECONDS,
    COORDINATOR_MIN_UPDATE_SECONDS,
    DEFAULT_ENABLE_NOTIFICATIONS,
    DEFAULT_NAME,
    DEFAULT_NIGHT_MODE_ENABLED,
    DEFAULT_UPDATE_INTERVAL_SECONDS,
    DOMAIN,
)


class ConciergeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Concierge."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        """Handle the initial step."""
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input["name"], data=user_input)

        schema = vol.Schema(
            {
                vol.Required("name", default=DEFAULT_NAME): str,
                vol.Required(CONF_ENABLE_NOTIFICATIONS, default=DEFAULT_ENABLE_NOTIFICATIONS): bool,
                vol.Required(
                    CONF_UPDATE_INTERVAL_SECONDS,
                    default=DEFAULT_UPDATE_INTERVAL_SECONDS,
                ): vol.All(vol.Coerce(int), vol.Range(min=COORDINATOR_MIN_UPDATE_SECONDS, max=COORDINATOR_MAX_UPDATE_SECONDS)),
                vol.Required(CONF_NIGHT_MODE_ENABLED, default=DEFAULT_NIGHT_MODE_ENABLED): bool,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return options flow."""
        return ConciergeOptionsFlow(config_entry)


class ConciergeOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Concierge."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_ENABLE_NOTIFICATIONS,
                    default=self.config_entry.options.get(
                        CONF_ENABLE_NOTIFICATIONS,
                        self.config_entry.data.get(CONF_ENABLE_NOTIFICATIONS, DEFAULT_ENABLE_NOTIFICATIONS),
                    ),
                ): bool,
                vol.Required(
                    CONF_UPDATE_INTERVAL_SECONDS,
                    default=self.config_entry.options.get(
                        CONF_UPDATE_INTERVAL_SECONDS,
                        self.config_entry.data.get(CONF_UPDATE_INTERVAL_SECONDS, DEFAULT_UPDATE_INTERVAL_SECONDS),
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=COORDINATOR_MIN_UPDATE_SECONDS, max=COORDINATOR_MAX_UPDATE_SECONDS)),
                vol.Required(
                    CONF_NIGHT_MODE_ENABLED,
                    default=self.config_entry.options.get(
                        CONF_NIGHT_MODE_ENABLED,
                        self.config_entry.data.get(CONF_NIGHT_MODE_ENABLED, DEFAULT_NIGHT_MODE_ENABLED),
                    ),
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
