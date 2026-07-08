"""Diagnostics tests for Concierge."""

from __future__ import annotations

from collections.abc import Mapping

from homeassistant.core import HomeAssistant

from custom_components.concierge.diagnostics import async_get_config_entry_diagnostics
from custom_components.concierge.models import ContextState, Interaction
from custom_components.concierge.storage import ConciergeStorage


def _contains_key(payload: object, forbidden_key: str) -> bool:
    if isinstance(payload, Mapping):
        if forbidden_key in payload:
            return True
        return any(_contains_key(value, forbidden_key) for value in payload.values())
    if isinstance(payload, list):
        return any(_contains_key(value, forbidden_key) for value in payload)
    return False


async def test_diagnostics_include_state_summary(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Diagnostics should expose only allowlisted operational summaries."""
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

    assert set(diagnostics) == {
        "storage_health",
        "session_health",
        "manifest_health",
        "cleanup_health",
        "reconciliation_health",
        "repairs_health",
        "provider_availability",
        "retention_policy",
    }
    assert diagnostics["session_health"]["total_session_count"] == 0
    assert diagnostics["cleanup_health"]["cleanup_attempt_count"] == 0
    assert diagnostics["manifest_health"]["manifest_schema_version"] == 1
    assert diagnostics["retention_policy"]["retention_mode"] == "zero_retention_default"
    assert "state" not in diagnostics
    assert "entry" not in diagnostics
    assert "coordinator_data" not in diagnostics
    for forbidden_key in {
        "recording_path",
        "speaker_embedding_id",
        "provider_device_id",
        "person_ref",
        "sample_items",
        "state",
        "entry",
        "coordinator_data",
    }:
        assert _contains_key(diagnostics, forbidden_key) is False