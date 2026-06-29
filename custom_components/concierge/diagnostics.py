"""Diagnostics support for Concierge."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .storage import ConciergeStorage

TO_REDACT = {"token", "api_key", "access_token"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data.get(DOMAIN, {}).get(config_entry.entry_id)
    coordinator_data = coordinator.data if coordinator else {}
    state = await ConciergeStorage(hass).async_load_state()
    state_snapshot = state.as_dict()
    state_summary = {
        "room_count": len(state.rooms),
        "interaction_count": len(state.interactions),
        "signal_count": len(state.signals),
        "context_count": len(state.contexts),
        "execution_preference_count": len(state.execution_preferences),
        "global_context_usage_count": len(state.global_context_usage),
    }

    return {
        "entry": async_redact_data(config_entry.as_dict(), TO_REDACT),
        "coordinator_data": async_redact_data(coordinator_data, TO_REDACT),
        "state_summary": async_redact_data(state_summary, TO_REDACT),
        "state": async_redact_data(state_snapshot, TO_REDACT),
    }
