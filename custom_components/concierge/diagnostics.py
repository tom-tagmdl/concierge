"""Diagnostics support for Concierge."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {"token", "api_key", "access_token"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data.get(DOMAIN, {}).get(config_entry.entry_id)
    data = coordinator.data if coordinator else {}

    return {
        "entry": async_redact_data(config_entry.as_dict(), TO_REDACT),
        "coordinator_data": async_redact_data(data, TO_REDACT),
    }
