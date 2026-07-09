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
        "enrollment_activity_summary",
        "completion_activity_summary",
        "cleanup_activity_summary",
        "reconciliation_activity_summary",
        "capture_provider_activity_summary",
        "retention_policy",
    }
    assert diagnostics["session_health"]["total_session_count"] == 0
    assert diagnostics["cleanup_health"]["cleanup_attempt_count"] == 0
    assert diagnostics["manifest_health"]["manifest_schema_version"] == 1
    assert diagnostics["retention_policy"]["retention_mode"] == "zero_retention_default"
    assert diagnostics["provider_availability"]["provider_type"] == "browser_microphone"
    assert diagnostics["provider_availability"]["provider_available"] is True
    assert diagnostics["provider_availability"]["provider_supported"] is True
    assert diagnostics["provider_availability"]["capture_supported"] is True
    assert diagnostics["provider_availability"]["selection_supported"] is True
    assert diagnostics["provider_availability"]["reason_code"] == "ready"
    assert diagnostics["provider_availability"]["satellite_capture_supported"] is False
    assert diagnostics["provider_availability"]["satellite_status_code"] == "provider_not_selected"
    assert diagnostics["enrollment_activity_summary"]["active_enrollments"] == 0
    assert diagnostics["completion_activity_summary"]["completion_attempts"] == 0
    assert diagnostics["cleanup_activity_summary"]["cleanup_executions"] == 0
    assert diagnostics["reconciliation_activity_summary"]["orphan_sessions_detected"] >= 0
    assert diagnostics["capture_provider_activity_summary"]["captured_sample_count"] == 0
    assert diagnostics["capture_provider_activity_summary"]["provider_type"] == "browser_microphone"
    assert "state" not in diagnostics
    assert "entry" not in diagnostics
    assert "coordinator_data" not in diagnostics
    for forbidden_key in {
        "recording_path",
        "recording_mime_type",
        "recording_size_bytes",
        "recording_duration_ms",
        "speech_text",
        "phrase_text",
        "sample_id",
        "speaker_embedding_id",
        "embeddings",
        "profile_vectors",
        "provider_device_id",
        "person_ref",
        "person_id",
        "sample_items",
        "state",
        "entry",
        "coordinator_data",
    }:
        assert _contains_key(diagnostics, forbidden_key) is False