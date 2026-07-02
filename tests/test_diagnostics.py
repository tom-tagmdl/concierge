"""Diagnostics tests for Concierge."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.concierge.diagnostics import async_get_config_entry_diagnostics
from custom_components.concierge.models import ContextState, Interaction
from custom_components.concierge.storage import ConciergeStorage


async def test_diagnostics_include_state_summary(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Diagnostics should expose persisted state and summary counts."""
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(
        area_id="great_room",
        aliases={"movie time": "scene.movie_mode"},
        global_overlays={"weather": True},
    )
    await storage.async_upsert_interaction(
        Interaction(
            interaction_id="interaction-1",
            area_id="great_room",
            message="Laundry complete",
            level="attention",
            state="active",
            priority=80,
        )
    )
    await storage.async_upsert_context(
        ContextState(
            context_type="weather",
            available=True,
            summary="Warm and sunny",
            detail="High of 92",
            speakable="It is warm and sunny.",
        )
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, setup_integration)

    assert diagnostics["state_summary"]["room_count"] == 1
    assert diagnostics["state_summary"]["interaction_count"] == 1
    assert diagnostics["state_summary"]["context_count"] == 1
    assert diagnostics["state_summary"]["person_profile_count"] == 0
    assert diagnostics["state_summary"]["voice_profile_count"] == 0
    assert "great_room" in diagnostics["state"]["rooms"]