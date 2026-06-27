"""Service handlers for Concierge."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN

SERVICE_REQUEST_ACTION = "request_action"
EVENT_CONCIERGE_REQUEST = "concierge_request"

SERVICE_REQUEST_ACTION_SCHEMA = vol.Schema(
    {
        vol.Required("intent"): str,
        vol.Optional("room"): str,
        vol.Optional("target_asset"): str,
        vol.Optional("context"): dict,
    }
)


async def _async_handle_request_action(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle concierge request action service call."""
    payload: dict[str, Any] = {
        "intent": call.data["intent"],
        "room": call.data.get("room"),
        "target_asset": call.data.get("target_asset"),
        "context": call.data.get("context", {}),
    }
    hass.bus.async_fire(EVENT_CONCIERGE_REQUEST, payload)


async def async_register_services(hass: HomeAssistant) -> None:
    """Register Concierge services."""
    if hass.services.has_service(DOMAIN, SERVICE_REQUEST_ACTION):
        return

    async def _handler(call: ServiceCall) -> None:
        await _async_handle_request_action(hass, call)

    hass.services.async_register(
        DOMAIN,
        SERVICE_REQUEST_ACTION,
        _handler,
        schema=SERVICE_REQUEST_ACTION_SCHEMA,
    )


async def async_unregister_services(hass: HomeAssistant) -> None:
    """Unregister Concierge services."""
    if hass.services.has_service(DOMAIN, SERVICE_REQUEST_ACTION):
        hass.services.async_remove(DOMAIN, SERVICE_REQUEST_ACTION)
