"""Test Concierge services."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.concierge.const import DOMAIN
from custom_components.concierge.services import EVENT_CONCIERGE_REQUEST, SERVICE_REQUEST_ACTION


async def test_request_action_service_fires_event(hass: HomeAssistant, setup_integration) -> None:
    """Test service call emits concierge event."""
    events: list = []

    def _listener(event):
        events.append(event)

    remove_listener = hass.bus.async_listen(EVENT_CONCIERGE_REQUEST, _listener)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_REQUEST_ACTION,
        {
            "intent": "summarize_room",
            "room": "living_room",
            "target_asset": "grand_piano",
        },
        blocking=True,
    )

    assert len(events) == 1
    assert events[0].data["intent"] == "summarize_room"
    remove_listener()
