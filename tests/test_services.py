"""Tests for Concierge contract-first services."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from homeassistant.core import Event, SupportsResponse
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import floor_registry as fr
from homeassistant.core import HomeAssistant

from custom_components.concierge import services as services_module
from custom_components.concierge.archive_runtime import (
    CONF_AUDIT_ARCHIVE_DESTINATION_URI,
    CONF_AUDIT_ARCHIVE_ENABLED,
)
from custom_components.concierge.const import CONF_VOICE_IDENTITY_LINKED
from custom_components.concierge.const import DOMAIN, EVENT_EXECUTION
from custom_components.concierge.models import (
    ActivityEvent,
    ContinuityConfidenceBand,
    ExperienceSnapshot,
    LearningOwnershipScope,
    LearningPolicyEvaluationRequest,
    LearningWriteRequest,
    PersonProfile,
    PreferenceIdentityState,
    PreferenceResolutionRequest,
    UsualState,
    UsualStateBasis,
)
from custom_components.concierge.storage import ConciergeStorage


@pytest.fixture
def enable_custom_integrations() -> None:
    """Satisfy the shared test conftest autouse dependency for targeted standalone runs."""
    return None


def _register_voice_identity_runtime_services(
    hass: HomeAssistant,
    *,
    attribution_payload: dict[str, object] | None = None,
    identity_context_payload: dict[str, object] | None = None,
) -> None:
    """Register test Voice Identity runtime services with deterministic payloads."""
    if hass.services.has_service("voice_identity", "attribute_speaker"):
        hass.services.async_remove("voice_identity", "attribute_speaker")
    if hass.services.has_service("voice_identity", "get_identity_context"):
        hass.services.async_remove("voice_identity", "get_identity_context")

    async def _handle_attribute_speaker(call):
        _ = call
        payload = attribution_payload or {
            "success": True,
            "status": "attribution_unavailable",
            "identity_confidence_level": "unknown",
            "confidence": 0.0,
            "confidence_band": "unavailable",
            "reason_code": "attribution_unavailable",
            "attribution_method": "none",
            "is_confident": False,
            "is_ambiguous": False,
            "is_abstained": True,
            "diagnostic_summary": {
                "diagnostic_available": False,
                "diagnostic_reason_code": "diagnostics_unavailable",
                "repair_available": False,
                "health_status": "unavailable",
                "attribution_readiness": "unavailable",
                "compatibility_readiness": "unavailable",
            },
            "repair_hint_code": "review_component_health",
            "suggested_next_action_code": "reload_voice_identity",
            "health_status": "unavailable",
            "readiness_status": "unavailable",
        }
        return {"success": True, "reason_code": "ready", "entry_id": "entry", "attribution": payload}

    async def _handle_get_identity_context(call):
        _ = call
        payload = identity_context_payload or {
            "state": "unavailable",
            "reason_code": "attribution_unavailable",
            "source": "voice_identity",
        }
        return {"success": True, "reason_code": "ready", "entry_id": "entry", "identity_context": payload}

    hass.services.async_register(
        "voice_identity",
        "attribute_speaker",
        _handle_attribute_speaker,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        "voice_identity",
        "get_identity_context",
        _handle_get_identity_context,
        supports_response=SupportsResponse.ONLY,
    )


def _enable_music_assistant_provider(hass: HomeAssistant, monkeypatch) -> None:
    """Enable Music Assistant as the configured Concierge media provider for tests."""
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    entry.options["media_provider"] = "music_assistant"

    original_async_entries = hass.config_entries.async_entries

    def _patched_async_entries(domain=None):
        if domain == "music_assistant":
            return [SimpleNamespace(domain="music_assistant")]
        return original_async_entries(domain)

    monkeypatch.setattr(hass.config_entries, "async_entries", _patched_async_entries)


def _register_music_assistant_play_media(hass: HomeAssistant, calls: list[dict[str, object]]) -> None:
    """Register a deterministic Music Assistant play_media test handler."""
    if hass.services.has_service("music_assistant", "play_media"):
        hass.services.async_remove("music_assistant", "play_media")

    async def _play_media(call) -> None:
        calls.append(dict(call.data))

    hass.services.async_register("music_assistant", "play_media", _play_media)


async def _seed_room_media_context(
    storage: ConciergeStorage,
    *,
    area_id: str,
    provider_source: str = "music_assistant",
    source_room_id: str | None = None,
    provider_media_id: str | None = None,
    media_type: str | None = None,
    track_title: str | None = None,
    artist_name: str | None = None,
    album_name: str | None = None,
    genre: str | None = None,
    media_query: str | None = None,
    manual_stop: bool = False,
    manual_stop_cooldown_until: str | None = None,
    manual_stop_cooldown_seconds: int | None = None,
) -> None:
    """Seed a room-scoped last-media record for continuation tests."""
    state = await storage.async_load_state()
    selected_room_id = source_room_id or area_id
    now_iso = datetime.now(timezone.utc).isoformat()
    state.usual_states[services_module._room_media_state_id(area_id=selected_room_id)] = UsualState(
        state_id=services_module._room_media_state_id(area_id=selected_room_id),
        scope="room",
        scope_ref=selected_room_id,
        basis=UsualStateBasis.LEARNED,
        updated_at=now_iso,
        values={
            "room_id": selected_room_id,
            "source_room_id": selected_room_id,
            "source_room_selection_reason": "test_seeded_context",
            "provider_source": provider_source,
            "provider_media_id": provider_media_id,
            "media_type": media_type,
            "media_query": media_query or provider_media_id or track_title or genre,
            "last_song": track_title,
            "last_genre": genre,
            "last_album": album_name,
            "last_artist": artist_name,
            "last_media": {
                "provider_source": provider_source,
                "provider_media_id": provider_media_id,
                "media_type": media_type,
                "track_title": track_title,
                "artist_name": artist_name,
                "album_name": album_name,
                "genre": genre,
                "media_query": media_query or provider_media_id or track_title or genre,
                "captured_at": now_iso,
            },
            "manual_stop": manual_stop,
            "manual_stop_cooldown_until": manual_stop_cooldown_until,
            "manual_stop_cooldown_seconds": manual_stop_cooldown_seconds,
            "captured_at": now_iso,
        },
        metadata={
            "policy_name": "experience_continuity_room_media_context_ec_e_03",
            "source_room_selection_reason": "test_seeded_context",
            "captured_at": now_iso,
        },
    )
    await storage.async_save_state(state)


async def test_room_media_context_capture_persists_and_overwrites_room_scoped_state(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Room media capture should persist and overwrite room-scoped continuity state without crossing room boundaries."""
    area = ar.async_get(hass).async_create(name="Kitchen")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "media_player_entity_ids": ["media_player.kitchen_main"],
        },
        blocking=True,
    )

    storage = ConciergeStorage(hass)
    initial_state = await storage.async_load_state()
    captured_state = await services_module._async_capture_room_media_context(
        hass,
        storage=storage,
        state=initial_state,
        area_id=area.id,
        source_room_id=area.id,
        provider_source="music_assistant",
        media_type="track",
        media_query="Song A",
        music_assistant_request={
            "media_type": "track",
            "media_id": "track-001",
            "radio_mode": False,
        },
        room_media_context={
            "source_room_selection_reason": "test_seeded_context",
            "source_room_candidates": [area.id],
            "room_media_context": {
                "provider_source": "music_assistant",
                "provider_media_id": "track-001",
                "media_type": "track",
                "track_title": "Song A",
                "artist_name": "Artist A",
                "album_name": "Album A",
                "genre": "Jazz",
                "media_query": "Song A",
            },
        },
    )

    state_id = services_module._room_media_state_id(area_id=area.id)
    assert captured_state["state_id"] == state_id
    assert captured_state["scope"] == "room"
    assert captured_state["values"]["last_song"] == "Song A"
    assert captured_state["values"]["last_genre"] == "Jazz"
    assert captured_state["values"]["provider_media_id"] == "track-001"

    refreshed = await storage.async_load_state()
    assert state_id in refreshed.usual_states
    stored = refreshed.usual_states[state_id]
    first_updated_at = stored.updated_at
    assert stored.values["room_id"] == area.id
    assert stored.values["source_room_id"] == area.id
    assert stored.values["provider_source"] == "music_assistant"
    assert stored.values["provider_media_id"] == "track-001"
    assert stored.values["media_type"] == "track"
    assert stored.values["media_query"] == "Song A"
    assert stored.values["last_song"] == "Song A"
    assert stored.values["last_genre"] == "Jazz"

    overwrite_state = await storage.async_load_state()
    await services_module._async_capture_room_media_context(
        hass,
        storage=storage,
        state=overwrite_state,
        area_id=area.id,
        source_room_id=area.id,
        provider_source="music_assistant",
        media_type="track",
        media_query="Song B",
        music_assistant_request={
            "media_type": "track",
            "media_id": "track-002",
            "radio_mode": False,
        },
        room_media_context={
            "source_room_selection_reason": "test_seeded_context",
            "source_room_candidates": [area.id],
            "room_media_context": {
                "provider_source": "music_assistant",
                "provider_media_id": "track-002",
                "media_type": "track",
                "track_title": "Song B",
                "artist_name": "Artist B",
                "album_name": "Album B",
                "genre": "Classical",
                "media_query": "Song B",
            },
        },
    )

    refreshed_again = await storage.async_load_state()
    overwritten = refreshed_again.usual_states[state_id]
    assert overwritten.updated_at != first_updated_at
    assert overwritten.values["provider_media_id"] == "track-002"
    assert overwritten.values["last_song"] == "Song B"
    assert overwritten.values["last_genre"] == "Classical"


async def test_capability_resolution_uses_entry_scoped_voice_identity_discovery(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Capability evaluation should succeed using entry-scoped Voice Identity discovery runtime."""
    capabilities = await services_module._async_resolve_integration_capabilities(hass)

    assert capabilities["cap_voice_enrollment"] is True
    assert capabilities["voice_enrollment_reason_code"] == "ready"
    assert capabilities["input_snapshot"]["voice_identity_linked"] is True


async def test_capability_resolution_reports_linkage_disabled(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Capability evaluation should fail closed when Voice Identity linkage is disabled."""
    hass.config_entries.async_update_entry(
        setup_integration,
        options={
            **dict(setup_integration.options),
            CONF_VOICE_IDENTITY_LINKED: False,
            CONF_AUDIT_ARCHIVE_ENABLED: True,
            CONF_AUDIT_ARCHIVE_DESTINATION_URI: "/media/concierge-tests",
        },
    )

    capabilities = await services_module._async_resolve_integration_capabilities(hass)

    assert capabilities["cap_voice_enrollment"] is False
    assert capabilities["voice_enrollment_reason_code"] == "voice_identity_linkage_disabled"


async def test_interaction_services_round_trip(hass: HomeAssistant, setup_integration) -> None:
    """Interaction service endpoints should support update/get/clear flows."""
    await hass.services.async_call(
        DOMAIN,
        "update_interaction",
        {
            "interaction_id": "int-1",
            "area_id": "living_room",
            "message": "Laundry is done",
            "level": "attention",
            "state": "active",
            "priority": 90,
        },
        blocking=True,
    )

    result = await hass.services.async_call(
        DOMAIN,
        "get_interactions",
        {"area_id": "living_room"},
        blocking=True,
        return_response=True,
    )
    assert len(result["interactions"]) == 1
    assert result["interactions"][0]["interaction_id"] == "int-1"

    await hass.services.async_call(
        DOMAIN,
        "clear_interaction",
        {"interaction_id": "int-1"},
        blocking=True,
    )

    cleared = await hass.services.async_call(
        DOMAIN,
        "get_interactions",
        {"area_id": "living_room"},
        blocking=True,
        return_response=True,
    )
    assert cleared["interactions"] == []


async def test_context_and_summary_services(hass: HomeAssistant, setup_integration) -> None:
    """Context updates should be retrievable and included in summary output."""
    area = ar.async_get(hass).async_create(name="Living Room")

    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "global_overlays": {"weather": False, "news": True},
        },
        blocking=True,
    )

    await hass.services.async_call(
        DOMAIN,
        "update_global_context",
        {
            "context_type": "weather",
            "enabled": True,
            "summary": "Partly cloudy, 85 degrees",
            "detail": "High of 92, low of 75",
            "speakable": "It is currently partly cloudy and 85 degrees.",
        },
        blocking=True,
    )

    await hass.services.async_call(
        DOMAIN,
        "update_global_context",
        {
            "context_type": "news",
            "enabled": True,
            "summary": "3 headlines available",
            "detail": "Morning digest ready",
            "speakable": "Here are today\'s top headlines.",
        },
        blocking=True,
    )

    context = await hass.services.async_call(
        DOMAIN,
        "get_context",
        {"context_type": "weather"},
        blocking=True,
        return_response=True,
    )
    assert context["context"] is not None
    assert context["context"]["summary"] == "Partly cloudy, 85 degrees"

    summary = await hass.services.async_call(
        DOMAIN,
        "get_summary",
        {"area_id": area.id, "include_context": True, "include_signals": False},
        blocking=True,
        return_response=True,
    )
    assert "Partly cloudy, 85 degrees" not in summary["summary"]
    assert "3 headlines available" in summary["summary"]
    assert summary["context_area_id"] == area.id
    assert summary["resolved_composite_id"] is None
    assert summary["context_source_count"] == 1
    assert summary["signal_count"] == 0
    assert summary["fallback_context_applied"] is False
    assert summary["fallback_reason"] is None
    discovery = summary["capability_discovery"]
    assert discovery["applicable"] is True
    assert discovery["deterministic_discovery"] is True
    assert discovery["capability_authority_external"] is True
    assert discovery["deferred_release_2_owners"]["capability_diagnostics_explainability"] == "#318"
    ids = [item["capability_id"] for item in discovery["discovered_capabilities"]]
    assert ids == [
        "ai_actions",
        "tts",
        "persona",
        "asset_handoff_consumption",
        "voice_enrollment",
        "extended_history",
    ]
    continuity = summary["continuity_governance_boundary"]
    assert continuity["applicable"] is True
    assert continuity["continuity_path"] == "governed_continuity_boundary"
    assert continuity["deterministic_boundary"] is True
    assert continuity["continuity_authority_external"] is True
    assert continuity["continuity_owns_identity"] is False
    assert continuity["continuity_owns_occupancy"] is False
    assert continuity["continuity_owns_memory"] is False
    assert continuity["privacy_boundary_preserved"] is True
    assert continuity["orchestration_constraints"]["route_scope"] == "room"
    assert continuity["orchestration_constraints"]["affinity_behavior_enabled"] is True
    assert continuity["orchestration_constraints"]["diagnostics_behavior_enabled"] is True
    assert continuity["deferred_release_3_owners"]["person_room_affinity_boundary"] == "#326"
    assert continuity["deferred_release_3_owners"]["continuity_affinity_diagnostics_explainability"] == "#328"
    affinity = summary["person_room_affinity_boundary"]
    assert affinity["applicable"] is True
    assert affinity["affinity_path"] == "governed_person_room_affinity_boundary"
    assert affinity["deterministic_boundary"] is True
    assert affinity["affinity_authority_external"] is True
    assert affinity["affinity_owns_identity"] is False
    assert affinity["affinity_owns_room_truth"] is False
    assert affinity["affinity_owns_occupancy"] is False
    assert affinity["affinity_owns_memory"] is False
    assert affinity["guest_safe_boundary_preserved"] is True
    assert affinity["privacy_boundary_preserved"] is True
    assert affinity["orchestration_constraints"]["route_scope"] == "room"
    assert affinity["orchestration_constraints"]["affinity_learning_enabled"] is False
    assert affinity["orchestration_constraints"]["diagnostics_behavior_enabled"] is True
    assert affinity["deferred_release_3_owners"]["privacy_household_memory_boundary"] == "#327"
    assert affinity["deferred_release_3_owners"]["continuity_affinity_diagnostics_explainability"] == "#328"
    memory = summary["privacy_household_memory_boundary"]
    assert memory["applicable"] is True
    assert memory["boundary_path"] == "governed_privacy_household_memory_boundary"
    assert memory["deterministic_boundary"] is True
    assert memory["privacy_authority_external"] is True
    assert memory["household_memory_authority_external"] is True
    assert memory["memory_owns_identity"] is False
    assert memory["memory_owns_retention_policy"] is False
    assert memory["memory_owns_storage"] is False
    assert memory["memory_owns_provenance"] is False
    assert memory["guest_safe_boundary_preserved"] is True
    assert memory["orchestration_constraints"]["route_scope"] == "room"
    assert memory["orchestration_constraints"]["household_memory_diagnostics_enabled"] is False
    assert memory["deferred_release_3_owners"]["continuity_affinity_diagnostics_explainability"] == "#328"
    messaging = summary["messaging_governance_boundary"]
    assert messaging["applicable"] is True
    assert messaging["boundary_path"] == "governed_messaging_boundary"
    assert messaging["messaging_authority_external"] is True
    assert messaging["message_authority_external"] is True
    assert messaging["provenance_authority_external"] is True
    assert messaging["household_memory_authority_external"] is True
    assert messaging["authority_protection"]["messaging_owns_truth"] is False
    assert messaging["authority_protection"]["messaging_owns_provenance"] is False
    assert messaging["authority_protection"]["messaging_owns_memory"] is False
    assert messaging["authority_protection"]["messaging_owns_identity"] is False
    assert messaging["governance_controls"]["message_boundary_only"] is True
    assert messaging["governance_controls"]["truth_determination_enabled"] is False
    assert messaging["governance_controls"]["source_of_record_enabled"] is False
    assert messaging["deferred_release_4_owners"]["messaging_provenance"] == "#340"
    assert messaging["deferred_release_4_owners"]["notification_and_delivery_boundary"] == "#341"
    assert messaging["deferred_release_4_owners"]["recipient_consent_privacy_visibility_boundary"] == "#342"
    productivity_boundary = summary["productivity_source_of_record_boundary"]
    assert productivity_boundary["applicable"] is True
    assert productivity_boundary["boundary_path"] == "governed_productivity_source_of_record_boundary"
    assert productivity_boundary["deterministic_boundary"] is True
    assert productivity_boundary["concierge_role"] == "bounded_consumer_orchestrator"
    assert productivity_boundary["representation_kinds"] == [
        "configuration_reference",
        "consumed_projection",
        "generated_explanation",
        "coordination_context",
    ]
    assert productivity_boundary["configured_source_reference_count"] == 0
    assert productivity_boundary["domain_boundaries"]["calendar"]["source_of_record_external"] is True
    assert productivity_boundary["domain_boundaries"]["calendar"]["configured_reference_present"] is False
    assert productivity_boundary["domain_boundaries"]["calendar"]["concierge_canonical_state_owned"] is False
    assert productivity_boundary["domain_boundaries"]["briefing"]["derived_context_only"] is True
    assert productivity_boundary["provenance_requirements"]["provenance_reference_required"] is True
    assert productivity_boundary["diagnostics_visibility"]["safe_source_metadata_only"] is True
    assert productivity_boundary["non_authority_assertions"]["creates_source_of_record"] is False
    assert productivity_boundary["non_authority_assertions"]["stores_duplicate_canonical_records"] is False
    occupancy = summary["occupancy_governance_boundary"]
    assert occupancy["applicable"] is True
    assert occupancy["occupancy_path"] == "governed_occupancy_boundary"
    assert occupancy["deterministic_boundary"] is True
    assert occupancy["occupancy_authority_external"] is True
    assert occupancy["occupancy_policy_authority_external"] is True
    assert occupancy["occupancy_truth_authority_external"] is True
    assert occupancy["occupancy_owns_room_truth"] is False
    assert occupancy["occupancy_owns_identity"] is False
    assert occupancy["occupancy_owns_household_memory"] is False
    assert occupancy["occupancy_owns_restoration"] is False
    assert occupancy["guest_safe_boundary_preserved"] is True
    assert occupancy["privacy_boundary_preserved"] is True
    assert occupancy["orchestration_constraints"]["route_scope"] == "room"
    assert occupancy["orchestration_constraints"]["occupancy_boundary_only"] is True
    assert occupancy["orchestration_constraints"]["occupancy_decision_behavior_enabled"] is False
    assert occupancy["orchestration_constraints"]["occupancy_execution_enabled"] is False
    assert occupancy["orchestration_constraints"]["occupancy_inference_enabled"] is False
    assert occupancy["orchestration_constraints"]["occupancy_diagnostics_behavior_enabled"] is False
    assert occupancy["deferred_release_3_owners"]["presence_governance_boundary"] == "#334"
    assert occupancy["deferred_release_3_owners"]["occupancy_presence_diagnostics_explainability"] == "#337"
    presence = summary["presence_governance_boundary"]
    assert presence["applicable"] is True
    assert presence["presence_path"] == "governed_presence_boundary"
    assert presence["deterministic_boundary"] is True
    assert presence["presence_authority_external"] is True
    assert presence["presence_policy_authority_external"] is True
    assert presence["presence_truth_authority_external"] is True
    assert presence["presence_owns_occupancy"] is False
    assert presence["presence_owns_room_truth"] is False
    assert presence["presence_owns_identity"] is False
    assert presence["presence_owns_household_memory"] is False
    assert presence["presence_owns_restoration"] is False
    assert presence["guest_safe_boundary_preserved"] is True
    assert presence["privacy_boundary_preserved"] is True
    assert presence["consumes_occupancy_governance_visibility"] is True
    assert presence["orchestration_constraints"]["route_scope"] == "room"
    assert presence["orchestration_constraints"]["presence_boundary_only"] is True
    assert presence["orchestration_constraints"]["presence_detection_enabled"] is False
    assert presence["orchestration_constraints"]["presence_inference_enabled"] is False
    assert presence["orchestration_constraints"]["presence_attribution_enabled"] is False
    assert presence["orchestration_constraints"]["presence_behavior_enabled"] is False
    assert presence["orchestration_constraints"]["presence_diagnostics_behavior_enabled"] is False
    assert presence["deferred_release_3_owners"]["guest_unknown_occupant_behavior"] == "#335"
    assert presence["deferred_release_3_owners"]["occupancy_presence_diagnostics_explainability"] == "#337"
    guest_unknown = envelope["guest_unknown_occupant_behavior"]
    assert guest_unknown["applicable"] is False
    assert guest_unknown["behavior_path"] == "not_applicable_direct_execution"
    assert guest_unknown["occupant_state"] == "unknown_occupant"
    assert guest_unknown["conservative_behavior_required"] is True
    assert guest_unknown["restoration_eligibility_allowed"] is False
    assert guest_unknown["governance_controls"]["behavior_enabled"] is False
    guest_unknown = envelope["guest_unknown_occupant_behavior"]
    assert guest_unknown["applicable"] is True
    assert guest_unknown["behavior_path"] == "governed_guest_unknown_occupant_behavior"
    assert guest_unknown["occupant_state"] == "unknown_occupant"
    assert guest_unknown["conservative_behavior_required"] is True
    assert guest_unknown["private_personalization_blocked"] is True
    assert guest_unknown["private_memory_inheritance_blocked"] is True
    assert guest_unknown["restoration_eligibility_allowed"] is False
    assert guest_unknown["identity_attribution_enabled"] is False
    assert guest_unknown["deferred_release_3_owners"]["multi_occupant_behavior"] == "#336"
    guest_unknown = summary["guest_unknown_occupant_behavior"]
    assert guest_unknown["applicable"] is True
    assert guest_unknown["behavior_path"] == "governed_guest_unknown_occupant_behavior"
    assert guest_unknown["occupant_state"] == "unknown_occupant"
    assert guest_unknown["guest_safe_mode_active"] is False
    assert guest_unknown["unknown_occupant_mode_active"] is True
    assert guest_unknown["conservative_behavior_required"] is True
    assert guest_unknown["private_personalization_blocked"] is True
    assert guest_unknown["private_memory_inheritance_blocked"] is True
    assert guest_unknown["identity_attribution_enabled"] is False
    assert guest_unknown["restoration_eligibility_allowed"] is False
    assert guest_unknown["governance_controls"]["behavior_enabled"] is True
    assert guest_unknown["deferred_release_3_owners"]["multi_occupant_behavior"] == "#336"
    assert guest_unknown["deferred_release_3_owners"]["occupancy_presence_diagnostics_explainability"] == "#337"
    experience = summary["experience_governance_boundary"]
    assert experience["applicable"] is True
    assert experience["governance_path"] == "capability_consumption_to_experience_governance"
    assert experience["experience_consumes_capability_outputs"] is True
    assert experience["experience_redefines_capability_outputs"] is False
    assert experience["orchestration_constraints"]["route_scope"] == "room"
    assert experience["orchestration_constraints"]["experience_execution_enabled"] is False
    assert experience["deferred_release_2_owners"]["capability_to_experience_handoff"] == "#320"
    assert experience["deferred_release_2_owners"]["experience_projection"] == "#321"
    handoff = summary["capability_to_experience_handoff"]
    assert handoff["applicable"] is True
    assert handoff["handoff_path"] == "capability_to_experience_consumption"
    assert handoff["deterministic_handoff"] is True
    assert handoff["experience_consumption_ready"] is True
    assert handoff["handoff_transfers_authority"] is False
    assert handoff["authority_attribution"]["capability_authority_origin"] == "htbw_governed_contracts_and_models"
    assert handoff["ownership_preservation"]["experience_authority_external"] is True
    assert handoff["deferred_release_2_owners"]["experience_projection"] == "#321"
    projection = summary["experience_projection"]
    assert projection["applicable"] is True
    assert projection["projection_path"] == "experience_projection_from_capability_handoff"
    assert projection["deterministic_projection"] is True
    assert projection["projection_is_authority"] is False
    assert projection["projected_experience_count"] >= 0
    assert projection["authority_attribution"]["capability_authority_origin"] == "htbw_governed_contracts_and_models"
    assert projection["ownership_preservation"]["experience_authority_external"] is True
    assert projection["deferred_release_2_owners"]["experience_restoration_boundary"] == "#322"
    restoration = summary["experience_restoration_boundary"]
    assert restoration["applicable"] is True
    assert restoration["restoration_path"] == "experience_projection_to_restoration_boundary"
    assert restoration["restoration_governance_path"] == "governed_restoration_boundary"
    assert restoration["deterministic_boundary"] is True
    assert restoration["restoration_authority_external"] is True
    assert restoration["restoration_policy_authority_external"] is True
    assert restoration["restoration_authority_transferred"] is False
    assert restoration["restoration_eligible"] is False
    assert restoration["guest_unknown_behavior_consumed"] is True
    assert restoration["restoration_eligibility_visibility"]["eligible_when_projected_experiences_present"] is True
    assert restoration["restoration_eligibility_visibility"]["restricted_by_guest_unknown_behavior"] is True
    assert restoration["restoration_eligibility_visibility"]["guest_unknown_occupant_state"] == "unknown_occupant"
    assert restoration["restoration_owns_identity"] is False
    assert restoration["restoration_owns_occupancy"] is False
    assert restoration["restoration_owns_continuity"] is False
    assert restoration["restoration_owns_affinity"] is False
    assert restoration["restoration_owns_household_memory"] is False
    assert restoration["privacy_boundary_preserved"] is True
    assert restoration["guest_safe_boundary_preserved"] is True
    assert restoration["governance_controls"]["route_scope"] == "room"
    assert restoration["governance_controls"]["restoration_execution_enabled"] is False
    assert restoration["governance_controls"]["restoration_decision_behavior_enabled"] is True
    assert restoration["governance_controls"]["restoration_diagnostics_behavior_enabled"] is True
    assert restoration["governance_controls"]["guest_unknown_behavior_enabled"] is True
    assert restoration["guardrails"]["diagnostics_in_scope"] is True
    assert restoration["deferred_release_3_owners"]["restoration_outcome_implementation"] == "#330"
    assert restoration["deferred_release_3_owners"]["e3a_preservation_alignment"] == "#331"
    assert restoration["deferred_release_3_owners"]["restoration_diagnostics_explainability"] == "#332"
    assert restoration["deferred_release_2_owners"]["experience_diagnostics_explainability"] == "#323"
    outcome = summary["experience_restoration_outcome"]
    assert outcome["applicable"] is True
    assert outcome["outcome_path"] == "experience_projection_to_restoration_outcome"
    assert outcome["deterministic_outcome"] is True
    assert outcome["outcome_is_authority"] is False
    assert outcome["restoration_applied"] is False
    assert outcome["restoration_execution_handoff_ready"] is False
    assert outcome["restoration_outcome_reason"] == "guest_unknown_occupant_restriction"
    assert outcome["governance_controls"]["route_scope"] == "room"
    assert outcome["governance_controls"]["restoration_decision_behavior_enabled"] is True
    assert outcome["governance_controls"]["restoration_execution_enabled"] is False
    assert outcome["governance_controls"]["guest_unknown_behavior_enabled"] is True
    assert outcome["ownership_preservation"]["restoration_decision_authority_transferred"] is False
    assert outcome["deferred_release_3_owners"]["e3a_preservation_alignment"] == "#331"
    preservation_alignment = summary["e3a_preservation_alignment"]
    assert preservation_alignment["applicable"] is True
    assert preservation_alignment["alignment_path"] == "restoration_outcome_to_e3a_preservation_alignment"
    assert preservation_alignment["deterministic_alignment"] is True
    assert preservation_alignment["consumes_restoration_outcomes"] is True
    assert preservation_alignment["preservation_governance_source"] == "adr_013_outcome_preservation"
    assert preservation_alignment["preservation_mode"] == "household_facing_outcomes"
    assert preservation_alignment["preservation_eligible"] is False
    assert preservation_alignment["alignment_reason"] == "restoration_outcome_not_applied"
    assert preservation_alignment["governance_controls"]["route_scope"] == "room"
    assert preservation_alignment["governance_controls"]["alignment_behavior_enabled"] is True
    assert preservation_alignment["governance_controls"]["restoration_decision_behavior_enabled"] is True
    assert preservation_alignment["governance_controls"]["restoration_execution_enabled"] is False
    assert preservation_alignment["ownership_preservation"]["preservation_creates_authority"] is False
    assert preservation_alignment["ownership_preservation"]["preservation_redefines_outcomes"] is False
    assert preservation_alignment["ownership_preservation"]["preservation_redefines_eligibility"] is False


async def test_summary_preserves_global_context_when_room_context_is_unavailable(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Global context should remain available deterministically when room context is unavailable."""
    await hass.services.async_call(
        DOMAIN,
        "update_global_context",
        {
            "context_type": "weather",
            "enabled": True,
            "summary": "Partly cloudy, 85 degrees",
            "detail": "High of 92, low of 75",
            "speakable": "It is currently partly cloudy and 85 degrees.",
        },
        blocking=True,
    )

    summary = await hass.services.async_call(
        DOMAIN,
        "get_summary",
        {"include_context": True, "include_signals": False},
        blocking=True,
        return_response=True,
    )

    assert "Partly cloudy, 85 degrees" in summary["summary"]
    assert summary["context_area_id"] is None
    assert summary["fallback_context_applied"] is True
    assert summary["fallback_reason"] == "no_room_context"
    assert summary["global_context_continuity_available"] is True


async def test_summary_includes_person_productivity_source_bindings(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Summary boundary should expose person productivity source bindings with safe fallback state."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="person.tom",
            name="Tom",
            email_source_ref="sensor.mailbox_tom",
            calendar_source_ref="sensor.calendar_tom",
            task_source_ref="tasks_provider_tom",
            shopping_source_ref="shopping_provider_household",
        )
    )

    summary = await hass.services.async_call(
        DOMAIN,
        "get_summary",
        {"include_context": True, "include_signals": False},
        blocking=True,
        return_response=True,
    )

    boundary = summary["productivity_source_of_record_boundary"]
    bindings = boundary["person_productivity_source_bindings"]
    assert bindings["person_count"] == 1
    assert bindings["configured_reference_present"]["email"] is False
    assert bindings["configured_reference_present"]["calendar"] is False
    assert bindings["configured_reference_present"]["task"] is True
    assert bindings["configured_reference_present"]["shopping"] is True
    assert bindings["safe_fallback_person_count"] == 1

    person_binding = bindings["person_bindings"][0]
    assert person_binding["person_id"] == "person.tom"
    assert person_binding["configuration_complete"] is False
    assert person_binding["safe_fallback_mode_active"] is True
    assert "source_missing_or_configuration_incomplete" in person_binding["safe_fallback_reasons"]
    assert "source_unavailable_or_removed" in person_binding["safe_fallback_reasons"]
    assert person_binding["sources"]["email"]["binding_status"] == "unavailable_or_removed"
    assert person_binding["sources"]["calendar"]["binding_status"] == "unavailable_or_removed"
    assert person_binding["sources"]["task"]["binding_status"] == "configured"
    assert person_binding["sources"]["shopping"]["binding_status"] == "configured"

    calendar_email_boundary = summary["calendar_email_consumption_boundary"]
    assert calendar_email_boundary["applicable"] is True
    assert calendar_email_boundary["boundary_path"] == "governed_calendar_email_consumption_boundary"
    assert calendar_email_boundary["configured_source_reference_count"] == 0
    assert calendar_email_boundary["person_aware_routing"]["routing_enabled"] is False
    assert calendar_email_boundary["person_aware_routing"]["reason_code"] == "no_execution_envelope"
    assert calendar_email_boundary["person_aware_routing"]["domains"]["calendar"]["enabled"] is False
    assert calendar_email_boundary["person_aware_routing"]["domains"]["email"]["enabled"] is False

    task_shopping_boundary = summary["task_shopping_consumption_boundary"]
    assert task_shopping_boundary["applicable"] is True
    assert task_shopping_boundary["boundary_path"] == "governed_task_shopping_consumption_boundary"
    assert task_shopping_boundary["consumption_only"] is True
    assert task_shopping_boundary["person_aware_routing"]["routing_enabled"] is False
    assert task_shopping_boundary["person_aware_routing"]["reason_code"] == "no_execution_envelope"
    assert task_shopping_boundary["person_aware_routing"]["domains"]["task"]["enabled"] is False
    assert task_shopping_boundary["person_aware_routing"]["domains"]["shopping"]["enabled"] is False
    assert task_shopping_boundary["task_reference_kinds"] == [
        "ownership_references",
        "assignment_references",
        "completion_references",
        "due_awareness_references",
        "provenance_references",
    ]
    assert task_shopping_boundary["shopping_reference_kinds"] == [
        "shopping_item_references",
        "ownership_references",
        "duplicate_indicators",
        "completion_references",
        "provenance_references",
        "shopping_explainability_references",
    ]
    assert task_shopping_boundary["clarification_behavior"]["supported"] is True
    assert task_shopping_boundary["clarification_behavior"]["ambiguity_visible"] is True
    assert task_shopping_boundary["clarification_behavior"]["hidden_intent_inference"] is False
    assert task_shopping_boundary["task_reference_boundaries"]["task"]["reference_only_model"] is True
    assert "claims_task_authority" not in task_shopping_boundary["task_reference_boundaries"]["task"]
    assert task_shopping_boundary["person_shopping_bindings"]["required_domains"] == ["shopping"]
    assert task_shopping_boundary["person_shopping_bindings"]["person_count"] == 1
    assert task_shopping_boundary["person_shopping_bindings"]["configured_reference_present"]["shopping"] is True
    assert task_shopping_boundary["person_shopping_bindings"]["safe_fallback_person_count"] == 0
    assert task_shopping_boundary["person_shopping_bindings"]["person_bindings"][0]["sources"]["shopping"]["binding_status"] == "configured"

    calendar_email_bindings = calendar_email_boundary["person_calendar_email_bindings"]
    assert calendar_email_bindings["required_domains"] == ["email", "calendar"]
    assert calendar_email_bindings["person_count"] == 1
    assert calendar_email_bindings["configured_reference_present"]["email"] is False
    assert calendar_email_bindings["configured_reference_present"]["calendar"] is False
    assert calendar_email_bindings["safe_fallback_person_count"] == 1

    calendar_email_person_binding = calendar_email_bindings["person_bindings"][0]
    assert calendar_email_person_binding["person_id"] == "person.tom"
    assert calendar_email_person_binding["configuration_complete"] is False
    assert calendar_email_person_binding["safe_fallback_mode_active"] is True
    assert "source_missing_or_configuration_incomplete" in calendar_email_person_binding["safe_fallback_reasons"]
    assert "source_unavailable_or_removed" in calendar_email_person_binding["safe_fallback_reasons"]
    assert calendar_email_person_binding["sources"]["email"]["binding_status"] == "unavailable_or_removed"
    assert calendar_email_person_binding["sources"]["calendar"]["binding_status"] == "unavailable_or_removed"


async def test_summary_handles_missing_calendar_binding_with_safe_fallback(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Missing calendar setup should surface a safe fallback posture without guessing."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="person.tom",
            name="Tom",
            email_source_ref="sensor.mailbox_tom",
        )
    )

    summary = await hass.services.async_call(
        DOMAIN,
        "get_summary",
        {"include_context": True, "include_signals": False},
        blocking=True,
        return_response=True,
    )

    calendar_email_boundary = summary["calendar_email_consumption_boundary"]
    calendar_email_bindings = calendar_email_boundary["person_calendar_email_bindings"]
    assert calendar_email_bindings["person_count"] == 1
    assert calendar_email_bindings["safe_fallback_person_count"] == 1

    person_binding = calendar_email_bindings["person_bindings"][0]
    assert person_binding["configuration_complete"] is False
    assert person_binding["safe_fallback_mode_active"] is True
    assert "source_missing_or_configuration_incomplete" in person_binding["safe_fallback_reasons"]
    assert person_binding["sources"]["calendar"]["binding_status"] == "missing"
    assert person_binding["sources"]["email"]["binding_status"] == "unavailable_or_removed"

    capture_knowledge_boundary = summary["capture_knowledge_consumption_boundary"]
    assert capture_knowledge_boundary["applicable"] is True
    assert capture_knowledge_boundary["boundary_path"] == "governed_capture_knowledge_consumption_boundary"
    assert capture_knowledge_boundary["knowledge_consumption"]["knowledge_available"] is False
    assert capture_knowledge_boundary["knowledge_consumption"]["safe_fallback_mode_active"] is True
    assert capture_knowledge_boundary["capture_consumption"]["capture_available"] is False
    assert capture_knowledge_boundary["capture_consumption"]["safe_fallback_mode_active"] is True
    assert capture_knowledge_boundary["provenance_visibility"]["provenance_reference_present"] is False

    briefing_boundary = summary["briefing_composition_boundary"]
    assert briefing_boundary["applicable"] is True
    assert briefing_boundary["boundary_path"] == "governed_briefing_composition_boundary"
    assert briefing_boundary["briefing_available"] is True
    assert briefing_boundary["safe_fallback_mode_active"] is True
    assert briefing_boundary["briefing_composition"]["briefing_composition_state"] == "active"
    assert briefing_boundary["briefing_composition"]["priority_ordering"] == [
        "calendar_email",
        "task_shopping",
        "capture_knowledge",
    ]

    household_status_boundary = summary["household_status_synthesis_boundary"]
    assert household_status_boundary["applicable"] is True
    assert household_status_boundary["boundary_path"] == "governed_household_status_synthesis_boundary"
    assert household_status_boundary["household_status_available"] is True
    assert household_status_boundary["safe_fallback_mode_active"] is True
    assert household_status_boundary["coordination_snapshot"]["coordination_snapshot_state"] == "active"
    assert household_status_boundary["briefing_composition_boundary"]["boundary_path"] == "governed_briefing_composition_boundary"
    assert household_status_boundary["open_loop_coordination_visibility"]["open_loop_supported"] is True
    assert household_status_boundary["open_loop_coordination_visibility"]["informational_only"] is True
    assert household_status_boundary["open_loop_coordination_visibility"]["coordination_authority_external"] is True


async def test_summary_surfaces_room_configuration_authority_traceability(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Room summaries should report configuration-authored authority, not discovery-first defaults."""
    area = ar.async_get(hass).async_create(name="Living Room")
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(
        area_id=area.id,
        voice_device_entity_ids=["assist_satellite.living_room"],
        speaker_entity_ids=["media_player.living_room_speaker"],
        weather_source_entity_ids=["weather.living_room"],
        news_source_entity_ids=["sensor.living_room_news"],
        environment_information_outputs=["weather", "news"],
        device_groups=[{"group_name": "Lighting", "entity_ids": ["light.lamp"]}],
        asset_groups=[{"group_name": "Artwork", "device_ids": ["asset.painting"]}],
        ai_knowledge_enabled=True,
    )

    summary = await hass.services.async_call(
        DOMAIN,
        "get_summary",
        {"area_id": area.id, "include_context": True, "include_signals": False},
        blocking=True,
        return_response=True,
    )

    room_authority = summary["room_authority_traceability"]
    assert room_authority["room_configuration_loaded"] is True
    assert room_authority["room_authority_source"] == "room_configuration"
    assert room_authority["room_vocabulary_source"] == "room_configuration"
    assert room_authority["vocabulary_source"] == "room_configuration"
    assert room_authority["information_source_origin"] == "room_configuration"
    assert room_authority["environment_source_origin"] == "room_configuration"
    assert room_authority["asset_authority_source"] == "room_configuration"
    assert room_authority["person_authority_source"] == "person_configuration"
    assert room_authority["room_configuration_area_id"] == area.id
    assert room_authority["room_configuration_voice_device_entity_ids"] == ["assist_satellite.living_room"]
    assert room_authority["room_configuration_speaker_entity_ids"] == ["media_player.living_room_speaker"]
    assert room_authority["room_configuration_environment_information_outputs"] == ["weather", "news"]
    assert room_authority["room_configuration_device_group_count"] == 1
    assert room_authority["room_configuration_asset_group_count"] == 1

    capability_discovery = summary["capability_discovery"]
    assert capability_discovery["authority_traceability"]["room_configuration_loaded"] is True
    assert capability_discovery["authority_traceability"]["room_authority_source"] == "room_configuration"


async def test_summary_includes_capture_and_knowledge_consumption(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Summary boundary should expose bounded capture and knowledge references with safe provenance visibility."""
    area = ar.async_get(hass).async_create(name="Library")
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(area_id=area.id, ai_knowledge_enabled=True)
    await storage.async_record_activity_event(
        ActivityEvent(
            activity_id="activity.capture-knowledge-1",
            correlation_id="corr.capture-knowledge-1",
            started_at="2026-07-20T00:00:00Z",
            channel="summary",
            actor_class="system",
            intent_class="capture_and_knowledge_consumption",
            request_summary="Seed capture and knowledge references",
            external_refs=[
                {"ref_type": "knowledge_request_references", "reference_id": "know.req.1"},
                {"ref_type": "knowledge_response_references", "reference_id": "know.res.1"},
                {"ref_type": "source_references", "reference_id": "know.src.1"},
                {"ref_type": "uncertainty_references", "reference_id": "know.unc.1"},
                {"ref_type": "knowledge_explainability_references", "reference_id": "know.exp.1"},
                {"ref_type": "utterance_reference", "reference_id": "cap.utt.1"},
                {"ref_type": "decomposition_references", "reference_id": "cap.dec.1"},
                {"ref_type": "item_lineage_references", "reference_id": "cap.lineage.1"},
                {"ref_type": "decomposition_explainability_references", "reference_id": "cap.exp.1"},
                {"ref_type": "ambiguity_reference", "reference_id": "cap.amb.1"},
                {"ref_type": "confirmation_reference", "reference_id": "cap.confirm.1"},
                {"ref_type": "provenance_references", "reference_id": "prov.1"},
            ],
        )
    )

    summary = await hass.services.async_call(
        DOMAIN,
        "get_summary",
        {"include_context": True, "include_signals": False},
        blocking=True,
        return_response=True,
    )

    capture_knowledge_boundary = summary["capture_knowledge_consumption_boundary"]
    assert capture_knowledge_boundary["applicable"] is True
    assert capture_knowledge_boundary["boundary_path"] == "governed_capture_knowledge_consumption_boundary"
    assert capture_knowledge_boundary["configured_source_reference_count"] == 11
    assert capture_knowledge_boundary["knowledge_reference_kinds"] == [
        "knowledge_request_references",
        "knowledge_response_references",
        "source_references",
        "uncertainty_references",
        "knowledge_explainability_references",
    ]
    assert capture_knowledge_boundary["capture_reference_kinds"] == [
        "utterance_reference",
        "decomposition_references",
        "item_lineage_references",
        "decomposition_explainability_references",
        "ambiguity_reference",
        "confirmation_reference",
    ]
    assert capture_knowledge_boundary["knowledge_consumption"]["knowledge_available"] is True
    assert capture_knowledge_boundary["knowledge_consumption"]["knowledge_enabled_room_count"] == 1
    assert capture_knowledge_boundary["capture_consumption"]["capture_available"] is True
    assert capture_knowledge_boundary["capture_consumption"]["reference_count"] == 6
    assert capture_knowledge_boundary["provenance_visibility"]["provenance_reference_count"] == 1
    assert capture_knowledge_boundary["clarification_behavior"]["supported"] is True
    assert capture_knowledge_boundary["clarification_behavior"]["ambiguity_visible"] is True
    assert capture_knowledge_boundary["clarification_behavior"]["hidden_intent_inference"] is False
    assert capture_knowledge_boundary["domain_boundaries"]["knowledge"]["source_of_record"] == "configured_knowledge_provider"
    assert capture_knowledge_boundary["domain_boundaries"]["capture"]["source_of_record"] == "configured_capture_provider"
    assert capture_knowledge_boundary["non_authority_assertions"]["claims_knowledge_authority"] is False
    assert capture_knowledge_boundary["non_authority_assertions"]["claims_capture_authority"] is False

    briefing_boundary = summary["briefing_composition_boundary"]
    assert briefing_boundary["applicable"] is True
    assert briefing_boundary["boundary_path"] == "governed_briefing_composition_boundary"
    assert briefing_boundary["configured_source_reference_count"] == 11
    assert briefing_boundary["briefing_available"] is True
    assert briefing_boundary["source_boundary_count"] == 3
    assert briefing_boundary["briefing_composition"]["briefing_composition_state"] == "active"
    assert briefing_boundary["briefing_composition"]["priority_ordering"] == [
        "calendar_email",
        "task_shopping",
        "capture_knowledge",
    ]
    assert briefing_boundary["provenance_visibility"]["provenance_visible"] is True
    assert briefing_boundary["non_authority_assertions"]["claims_briefing_authority"] is False
    assert briefing_boundary["non_authority_assertions"]["claims_household_status_authority"] is False

    household_status_boundary = summary["household_status_synthesis_boundary"]
    assert household_status_boundary["applicable"] is True
    assert household_status_boundary["boundary_path"] == "governed_household_status_synthesis_boundary"
    assert household_status_boundary["configured_source_reference_count"] == 11
    assert household_status_boundary["household_status_available"] is True
    assert household_status_boundary["source_boundary_count"] == 5
    assert household_status_boundary["coordination_snapshot"]["coordination_snapshot_state"] == "active"
    assert household_status_boundary["briefing_composition_boundary"]["boundary_path"] == "governed_briefing_composition_boundary"
    assert household_status_boundary["provenance_visibility"]["provenance_visible"] is True
    assert household_status_boundary["open_loop_coordination_visibility"]["open_loop_supported"] is True
    assert household_status_boundary["open_loop_coordination_visibility"]["source_of_record_external"] is True
    assert household_status_boundary["open_loop_coordination_visibility"]["provenance_visibility_supported"] is True
    assert household_status_boundary["non_authority_assertions"]["claims_household_status_authority"] is False
    assert household_status_boundary["non_authority_assertions"]["creates_planning_engine"] is False

    provenance_ownership_boundary = summary["provenance_ownership_consumption_boundary"]
    assert provenance_ownership_boundary["applicable"] is True
    assert provenance_ownership_boundary["boundary_path"] == "governed_release_6_provenance_ownership_consumption_boundary"
    assert provenance_ownership_boundary["provenance_visibility"]["provenance_visible"] is True
    assert provenance_ownership_boundary["explainability_visibility"]["safe_fallback_visible"] is True
    assert provenance_ownership_boundary["readiness_assessment"]["ownership_visibility_ready"] is True
    assert provenance_ownership_boundary["readiness_assessment"]["attribution_visibility_ready"] is True
    assert provenance_ownership_boundary["readiness_assessment"]["lineage_completeness_ready"] is True
    assert provenance_ownership_boundary["readiness_assessment"]["explainability_readiness"] is True
    assert provenance_ownership_boundary["safe_fallback_mode_active"] is False
    assert provenance_ownership_boundary["non_authority_assertions"]["claims_ownership_authority"] is False
    assert provenance_ownership_boundary["non_authority_assertions"]["claims_provenance_authority"] is False
    assert provenance_ownership_boundary["deferred_release_6_owners"]["provenance_ownership_and_consumption"] == "#368"

    household_coordination_boundary = summary["household_coordination_boundary"]
    assert household_coordination_boundary["applicable"] is True
    assert household_coordination_boundary["boundary_path"] == "governed_household_coordination_boundary"
    assert household_coordination_boundary["coordination_source"] == "governed_release_6_consumption_boundaries"
    assert household_coordination_boundary["consumption_only"] is True
    assert household_coordination_boundary["open_loop_coordination_visibility"]["open_loop_supported"] is True
    assert household_coordination_boundary["open_loop_coordination_visibility"]["informational_only"] is True
    assert household_coordination_boundary["non_authority_assertions"]["claims_coordination_authority"] is False
    assert household_coordination_boundary["non_authority_assertions"]["claims_provenance_authority"] is False

    productivity_coordination_boundary = summary["productivity_coordination_boundary"]
    assert productivity_coordination_boundary["applicable"] is True
    assert productivity_coordination_boundary["boundary_path"] == "governed_productivity_coordination_boundary"
    assert productivity_coordination_boundary["consumption_only"] is True
    assert productivity_coordination_boundary["informational_only"] is True
    assert productivity_coordination_boundary["coordination_awareness"]["cross_domain_coordination_supported"] is True
    assert productivity_coordination_boundary["explainability_visibility"]["routing_inputs_visible"] is True
    assert productivity_coordination_boundary["non_authority_assertions"]["claims_productivity_authority"] is False
    assert productivity_coordination_boundary["non_authority_assertions"]["creates_planning_engine"] is False

    provenance_diagnostics_boundary = summary["provenance_diagnostics_explainability_boundary"]
    assert provenance_diagnostics_boundary["applicable"] is True
    assert (
        provenance_diagnostics_boundary["boundary_path"]
        == "governed_release_6_provenance_diagnostics_explainability_boundary"
    )
    assert provenance_diagnostics_boundary["consumption_only"] is True
    assert provenance_diagnostics_boundary["informational_only"] is True
    assert provenance_diagnostics_boundary["provenance_visibility"]["provenance_visible"] is True
    assert provenance_diagnostics_boundary["diagnostics_visibility"]["safe_source_metadata_only"] is True
    assert (
        provenance_diagnostics_boundary["non_authority_assertions"]["claims_provenance_authority"]
        is False
    )


def _register_weather_forecast_service(
    hass: HomeAssistant,
    *,
    forecast_payload: dict[str, object] | None = None,
    raise_error: bool = False,
) -> None:
    """Register deterministic weather.get_forecasts service payload for weather summary tests."""
    if hass.services.has_service("weather", "get_forecasts"):
        hass.services.async_remove("weather", "get_forecasts")

    async def _handle_get_forecasts(call):
        _ = call
        if raise_error:
            raise RuntimeError("forecast unavailable")
        return forecast_payload or {}

    hass.services.async_register(
        "weather",
        "get_forecasts",
        _handle_get_forecasts,
        supports_response=SupportsResponse.ONLY,
    )


async def test_summary_weather_quality_uses_structured_forecast_and_warning(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Weather summary should use parsed structured fields and include warning headline when available."""
    area = ar.async_get(hass).async_create(name="Living Room")
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(
        area_id=area.id,
        weather_source_entity_ids=["weather.home_accuweather"],
        environment_information_outputs=["weather"],
    )

    _register_weather_forecast_service(
        hass,
        forecast_payload={
            "weather.home_accuweather": {
                "forecast": [
                    {
                        "condition": "partly_cloudy",
                        "temperature": 92,
                        "templow": 74,
                        "humidity": 78,
                        "precipitation_probability": 40,
                        "wind_speed": 5,
                    }
                ]
            }
        },
    )
    hass.states.async_set(
        "sensor.nws_alerts_alerts",
        "1",
        {"Alerts": [{"Headline": "Heat Advisory in effect today"}]},
    )

    summary = await hass.services.async_call(
        DOMAIN,
        "get_summary",
        {"area_id": area.id, "include_context": True, "include_signals": False},
        blocking=True,
        return_response=True,
    )

    assert summary["execution_outcome_category"] == "ANSWER_SUCCESS"
    assert summary["silence_as_success"] is False
    assert summary["response_required"] is True
    assert summary["response_generated"] is True
    weather = summary["weather_response_quality"]
    assert weather["weather_source"] == "weather.home_accuweather"
    assert weather["forecast_provider"] == "weather.home_accuweather"
    assert weather["forecast_data_available"] is True
    assert weather["warning_source"] == "sensor.nws_alerts_alerts"
    assert weather["warning_available"] is True
    assert weather["warning_headline"] == "Heat Advisory in effect today"
    assert weather["weather_response_strategy"] == "forecast_structured_with_warning"
    assert weather["fallback_reason"] is None
    assert weather["raw_provider_text_used"] is False
    assert weather["room_authority_source"] == "room_configuration"
    parsed = weather["parsed_forecast"]
    assert parsed["condition"] == "partly cloudy"
    assert parsed["high"] == 92
    assert parsed["low"] == 74
    assert parsed["humidity"] == 78
    assert parsed["precipitation_probability"] == 40
    assert parsed["wind_text"] == "winds will be light"
    assert "partly cloudy" in weather["generated_speech"].lower()
    assert "high near 92" in weather["generated_speech"].lower()
    assert "low around 74" in weather["generated_speech"].lower()
    assert "humidity" in weather["generated_speech"].lower()
    assert "chance of precipitation" in weather["generated_speech"].lower()
    assert "heat advisory in effect today" in weather["generated_speech"].lower()


async def test_summary_weather_quality_graceful_fallbacks_and_configured_authority_only(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Weather summary should gracefully fallback and stay bound to configured room weather source."""
    area = ar.async_get(hass).async_create(name="Bedroom")
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(
        area_id=area.id,
        weather_source_entity_ids=["weather.configured_source"],
        environment_information_outputs=["weather"],
    )
    # Unrelated weather entity exists but should be ignored.
    hass.states.async_set("weather.unrelated_inventory_entity", "sunny", {})

    _register_weather_forecast_service(hass, raise_error=True)
    hass.states.async_set(
        "sensor.nws_alerts_alerts",
        "1",
        {"Alerts": [{"Headline": "Wind Advisory"}]},
    )

    summary_warning_only = await hass.services.async_call(
        DOMAIN,
        "get_summary",
        {"area_id": area.id, "include_context": True, "include_signals": False},
        blocking=True,
        return_response=True,
    )
    warning_only = summary_warning_only["weather_response_quality"]
    assert warning_only["weather_source"] == "weather.configured_source"
    assert warning_only["forecast_data_available"] is False
    assert warning_only["warning_available"] is True
    assert warning_only["weather_response_strategy"] == "warning_only_fallback"
    assert "forecast" in warning_only["fallback_reason"]
    assert "wind advisory" in warning_only["generated_speech"].lower()
    assert warning_only["raw_provider_text_used"] is False

    hass.states.async_set("sensor.nws_alerts_alerts", "0", {"Alerts": []})
    summary_none = await hass.services.async_call(
        DOMAIN,
        "get_summary",
        {"area_id": area.id, "include_context": True, "include_signals": False},
        blocking=True,
        return_response=True,
    )
    fallback_only = summary_none["weather_response_quality"]
    assert fallback_only["weather_source"] == "weather.configured_source"
    assert fallback_only["forecast_data_available"] is False
    assert fallback_only["warning_available"] is False
    assert fallback_only["weather_response_strategy"] == "graceful_forecast_fallback"
    assert fallback_only["generated_speech"]
    assert fallback_only["weather_source"] != "weather.unrelated_inventory_entity"
    assert fallback_only["room_authority_source"] == "room_configuration"


async def test_summary_weather_quality_handles_missing_configured_source_without_discovery(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Missing configured weather source should not trigger entity discovery scans."""
    area = ar.async_get(hass).async_create(name="Office")
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(
        area_id=area.id,
        weather_source_entity_ids=[],
        environment_information_outputs=["weather"],
    )
    hass.states.async_set("weather.inventory_candidate", "sunny", {})
    if hass.services.has_service("weather", "get_forecasts"):
        hass.services.async_remove("weather", "get_forecasts")

    summary = await hass.services.async_call(
        DOMAIN,
        "get_summary",
        {"area_id": area.id, "include_context": True, "include_signals": False},
        blocking=True,
        return_response=True,
    )

    weather = summary["weather_response_quality"]
    assert weather["weather_source"] is None
    assert weather["forecast_data_available"] is False
    assert weather["warning_source"] == "sensor.nws_alerts_alerts"
    assert weather["weather_response_strategy"] == "configured_source_missing_fallback"
    assert weather["fallback_reason"] == "configured_weather_source_missing"
    assert weather["generated_speech"] == "I do not have a configured weather source for this room yet."
    assert weather["weather_source"] != "weather.inventory_candidate"
    assert (
        provenance_diagnostics_boundary["non_authority_assertions"]["creates_planning_engine"]
        is False
    )


@pytest.mark.parametrize(
    ("query", "capability", "sensor_attributes", "expected_value"),
    [
        ("what is the temperature", "temperature", {"temperature": 71, "unit_of_measurement": "F"}, 71),
        ("what is the humidity", "humidity", {"humidity": 44, "unit_of_measurement": "%"}, 44),
        ("how bright is it", "light", {"illuminance": 315, "unit_of_measurement": "lux"}, 315),
        ("what is the air quality", "air_quality", {"aqi": 18, "unit_of_measurement": "AQI"}, 18),
        ("how noisy is it", "noise", {"noise_level": 39, "unit_of_measurement": "dB"}, 39),
    ],
)
async def test_execute_monitoring_follow_up_uses_configured_room_mapping_only(
    hass: HomeAssistant,
    setup_integration,
    query: str,
    capability: str,
    sensor_attributes: dict[str, object],
    expected_value: int,
) -> None:
    """Monitoring follow-up should resolve from configured room mappings and ignore unrelated sensors."""
    area = ar.async_get(hass).async_create(name="Den")
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(
        area_id=area.id,
        room_sensor_entity_ids=["sensor.den_primary"],
        room_health_entity_ids=["sensor.den_health"],
        human_health_entity_ids=["sensor.den_human_health"],
    )

    hass.states.async_set("sensor.den_primary", "on", sensor_attributes)
    hass.states.async_set("sensor.den_health", "on", sensor_attributes)
    hass.states.async_set("sensor.den_human_health", "on", sensor_attributes)
    hass.states.async_set("sensor.unrelated_room_candidate", "on", sensor_attributes)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "area_id": area.id,
            "target": query,
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    assert result["execution_outcome_category"] == "ANSWER_SUCCESS"
    assert result["silence_as_success"] is False
    assert result["response_required"] is True
    assert result["response_generated"] is True
    monitoring = result["monitoring_follow_up"]
    assert monitoring["monitoring_capability"] == capability
    assert monitoring["room_authority_source"] == "room_configuration"
    assert monitoring["runtime_discovery_reliance"] == "validation_only"
    assert monitoring["refusal_reason"] is None
    assert monitoring["refusal_category"] is None
    assert monitoring["capability_requested"] == capability
    assert monitoring["capability_available"] is True
    assert monitoring["capability_configured"] is True
    assert monitoring["person_policy_evaluated"] is False
    assert monitoring["resolved_monitoring_device"] != "sensor.unrelated_room_candidate"
    assert monitoring["resolved_measurement"]["value"] == pytest.approx(expected_value)


async def test_execute_monitoring_follow_up_deterministic_priority_for_multiple_devices(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Monitoring follow-up should use deterministic first-configured precedence for repeated queries."""
    area = ar.async_get(hass).async_create(name="Office")
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(
        area_id=area.id,
        room_sensor_entity_ids=["sensor.office_temp_a", "sensor.office_temp_b"],
    )

    hass.states.async_set("sensor.office_temp_a", "on", {"temperature": 69, "unit_of_measurement": "F"})
    hass.states.async_set("sensor.office_temp_b", "on", {"temperature": 72, "unit_of_measurement": "F"})

    first = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"area_id": area.id, "target": "what is the temperature", "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )
    second = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"area_id": area.id, "target": "what is the temperature", "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    first_follow_up = first["monitoring_follow_up"]
    second_follow_up = second["monitoring_follow_up"]
    assert first_follow_up["resolved_monitoring_device"] == "sensor.office_temp_a"
    assert second_follow_up["resolved_monitoring_device"] == "sensor.office_temp_a"
    assert first_follow_up["resolution_priority"][0] == "sensor.office_temp_a"
    assert second_follow_up["resolution_priority"][0] == "sensor.office_temp_a"


async def test_execute_monitoring_follow_up_refuses_when_capability_not_configured(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Monitoring follow-up should refuse when no configured mapping exists for a requested capability."""
    area = ar.async_get(hass).async_create(name="Kitchen")
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(
        area_id=area.id,
        room_sensor_entity_ids=["sensor.kitchen_temperature"],
    )
    hass.states.async_set("sensor.kitchen_temperature", "on", {"temperature": 70, "unit_of_measurement": "F"})

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"area_id": area.id, "target": "what is the air quality", "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    assert result["execution_outcome_category"] == "REFUSAL_SUCCESS"
    assert result["silence_as_success"] is False
    assert result["response_required"] is True
    assert result["response_generated"] is True
    assert result["refusal_reason"] == "configured_capability_mapping_missing"
    assert result["refusal_category"] == "capability_unavailable"
    monitoring = result["monitoring_follow_up"]
    assert monitoring["monitoring_capability"] == "air_quality"
    assert monitoring["resolved_monitoring_device"] is None
    assert monitoring["refusal_reason"] == "configured_capability_mapping_missing"
    assert monitoring["refusal_category"] == "capability_unavailable"
    assert monitoring["capability_requested"] == "air_quality"
    assert monitoring["capability_available"] is False
    assert monitoring["capability_configured"] is False
    assert monitoring["person_policy_evaluated"] is False
    assert monitoring["runtime_discovery_reliance"] == "validation_only"


async def test_execute_monitoring_follow_up_merged_room_uses_configuration_authority(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Merged-room monitoring should remain configuration-authored with deterministic room precedence."""
    living = ar.async_get(hass).async_create(name="Living Room")
    den = ar.async_get(hass).async_create(name="Den")
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(
        area_id=living.id,
        room_sensor_entity_ids=["sensor.living_temp"],
    )
    await storage.async_update_room_config(
        area_id=den.id,
        room_sensor_entity_ids=["sensor.den_temp"],
    )
    await storage.async_update_composite_config(
        composite_id="main_suite",
        area_ids=[living.id, den.id],
        primary_area=living.id,
    )

    hass.states.async_set("sensor.living_temp", "on", {"temperature": 70, "unit_of_measurement": "F"})
    hass.states.async_set("sensor.den_temp", "on", {"temperature": 74, "unit_of_measurement": "F"})

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "area_id": living.id,
            "composite_id": "main_suite",
            "target": "what is the temperature",
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    monitoring = result["monitoring_follow_up"]
    assert monitoring["resolved_monitoring_device"] == "sensor.living_temp"
    assert monitoring["room_authority_source"] == "room_configuration"
    assert monitoring["merged_room_authority_source"] == "room_configuration"
    assert monitoring["capability_available"] is True
    assert monitoring["capability_configured"] is True
    assert monitoring["configured_capability_mapping"]["participating_rooms"] == [living.id, den.id]


async def test_execute_monitoring_follow_up_does_not_infer_from_unrelated_inventory(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Runtime inventory candidates must not create monitoring capability ownership."""
    area = ar.async_get(hass).async_create(name="Studio")
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(
        area_id=area.id,
        room_sensor_entity_ids=["sensor.studio_configured_temperature"],
    )

    hass.states.async_set(
        "sensor.studio_configured_temperature",
        "on",
        {"state_class": "measurement"},
    )
    hass.states.async_set(
        "sensor.inventory_air_quality_candidate",
        "35",
        {"aqi": 35, "unit_of_measurement": "AQI"},
    )

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"area_id": area.id, "target": "what is the air quality", "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    monitoring = result["monitoring_follow_up"]
    assert monitoring["resolved_monitoring_device"] is None
    assert monitoring["refusal_reason"] == "configured_capability_mapping_missing"
    assert monitoring["refusal_category"] == "capability_unavailable"
    assert monitoring["capability_available"] is False
    assert monitoring["capability_configured"] is False
    assert "sensor.inventory_air_quality_candidate" not in monitoring["resolution_priority"]
    assert monitoring["runtime_discovery_reliance"] == "validation_only"

async def test_push_person_message_reports_messaging_governance_boundary(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Person push messaging should return and record the governed messaging boundary."""
    area = ar.async_get(hass).async_create(name="Living Room")
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="tom",
            name="Tom",
            linked_area_id=area.id,
            mobile_notify_targets=["phone"],
            preferred_mobile_target="phone",
        )
    )

    notify_calls: list[dict[str, object]] = []

    async def _notify_handler(call) -> None:
        notify_calls.append(dict(call.data))

    hass.services.async_register("notify", "phone", _notify_handler)

    result = await hass.services.async_call(
        DOMAIN,
        "push_person_message",
        {
            "person_id": "tom",
            "message": "Hello Tom",
        },
        blocking=True,
        return_response=True,
    )

    boundary = result["messaging_governance_boundary"]
    assert result["sent"] is True
    assert result["person_id"] == "tom"
    assert result["target_id"] == "phone"
    assert result["service"] == "notify.phone"
    assert boundary["applicable"] is True
    assert boundary["boundary_path"] == "governed_messaging_boundary"
    assert boundary["governance_controls"]["route_scope"] == "room"
    assert boundary["governance_controls"]["recipient_scope"] == "person"
    assert boundary["governance_controls"]["message_context_type"] == "person_push"
    assert boundary["authority_protection"]["messaging_owns_truth"] is False
    assert boundary["authority_protection"]["messaging_owns_provenance"] is False
    assert boundary["authority_protection"]["messaging_owns_memory"] is False
    assert boundary["authority_protection"]["messaging_owns_identity"] is False
    assert boundary["deferred_release_4_owners"]["messaging_provenance"] == "#340"
    assert boundary["deferred_release_4_owners"]["notification_and_delivery_boundary"] == "#341"
    diagnostics_explainability = result["messaging_diagnostics_explainability"]
    assert diagnostics_explainability["boundary_path"] == "governed_messaging_diagnostics_explainability"
    assert diagnostics_explainability["decision_summary"]["delivery_permitted"] is True
    assert diagnostics_explainability["decision_summary"]["decision_reason"] == "delivery_permitted"
    assert diagnostics_explainability["decision_summary"]["governance_boundary_involved"] == "notification_delivery_boundary"
    assert diagnostics_explainability["decision_summary"]["delivery_channel"] == "mobile_notify"
    assert diagnostics_explainability["authority_non_rights"]["creates_authority"] is False
    assert diagnostics_explainability["authority_non_rights"]["creates_truth"] is False
    assert diagnostics_explainability["authority_non_rights"]["creates_memory"] is False
    assert diagnostics_explainability["authority_non_rights"]["creates_identity"] is False
    memory_boundary = result["household_memory_governance_boundary"]
    assert memory_boundary["boundary_path"] == "governed_household_memory_boundary"
    assert memory_boundary["boundary_status"] == "active"
    assert memory_boundary["household_memory_role"] == "bounded_record_reference_consumer"
    assert memory_boundary["prohibited_authority_claims"]["claims_household_truth_authority"] is False
    assert memory_boundary["prohibited_authority_claims"]["claims_identity_authority"] is False
    assert memory_boundary["prohibited_authority_claims"]["claims_occupancy_authority"] is False
    assert memory_boundary["prohibited_authority_claims"]["claims_messaging_authority"] is False
    assert memory_boundary["prohibited_authority_claims"]["claims_consent_authority"] is False
    assert memory_boundary["prohibited_authority_claims"]["claims_privacy_authority"] is False
    assert memory_boundary["prohibited_authority_claims"]["claims_source_of_truth_authority"] is False
    ownership_consumption_boundary = result["household_memory_ownership_consumption_boundary"]
    assert (
        ownership_consumption_boundary["boundary_path"]
        == "governed_household_memory_ownership_consumption_boundary"
    )
    assert ownership_consumption_boundary["boundary_status"] == "active"
    assert ownership_consumption_boundary["memory_ownership"]["memory_owner"] == "household_memory_governance"
    assert ownership_consumption_boundary["memory_ownership"]["memory_runtime_owner"] == "concierge"
    assert ownership_consumption_boundary["memory_ownership"]["owner_may_create_authority"] is False
    assert ownership_consumption_boundary["memory_creation_boundary"]["creation_allowed"] is True
    assert (
        ownership_consumption_boundary["memory_consumption_boundary"]["consumption_permitted"]
        is True
    )
    assert (
        ownership_consumption_boundary["memory_consumption_boundary"]["consumption_decision_reason"]
        == "delivery_permitted"
    )
    assert ownership_consumption_boundary["non_authority_assertions"]["ownership_is_not_authority"] is True
    assert ownership_consumption_boundary["non_authority_assertions"]["consumption_is_not_authority"] is True
    assert ownership_consumption_boundary["authority_relationships"]["redefines_identity_authority"] is False
    assert ownership_consumption_boundary["authority_relationships"]["redefines_occupancy_authority"] is False
    assert ownership_consumption_boundary["authority_relationships"]["redefines_messaging_authority"] is False
    assert ownership_consumption_boundary["authority_relationships"]["redefines_consent_authority"] is False
    assert ownership_consumption_boundary["authority_relationships"]["redefines_privacy_authority"] is False
    assert (
        ownership_consumption_boundary["authority_relationships"]["replaces_source_of_truth_authority"]
        is False
    )
    assert (
        ownership_consumption_boundary["deferred_release_4_owners"]["memory_identity_privacy_retention_separation"]
        == "#346"
    )
    identity_privacy_retention_boundary = result[
        "household_memory_identity_privacy_retention_separation_boundary"
    ]
    assert (
        identity_privacy_retention_boundary["boundary_path"]
        == "governed_household_memory_identity_privacy_retention_separation_boundary"
    )
    assert identity_privacy_retention_boundary["boundary_status"] == "active"
    assert identity_privacy_retention_boundary["identity_separation"]["identity_separated"] is True
    assert identity_privacy_retention_boundary["privacy_separation"]["privacy_separated"] is True
    assert identity_privacy_retention_boundary["retention_separation"]["retention_separated"] is True
    assert (
        identity_privacy_retention_boundary["separation_explainability"]["separation_permitted"]
        is True
    )
    assert (
        identity_privacy_retention_boundary["separation_explainability"]["separation_decision_reason"]
        == "delivery_permitted"
    )
    assert (
        identity_privacy_retention_boundary["authority_relationships"]["redefines_identity_authority"]
        is False
    )
    assert (
        identity_privacy_retention_boundary["authority_relationships"]["redefines_privacy_authority"]
        is False
    )
    assert (
        identity_privacy_retention_boundary["authority_relationships"]["redefines_retention_authority"]
        is False
    )
    assert (
        identity_privacy_retention_boundary["authority_relationships"]["replaces_source_of_truth_authority"]
        is False
    )
    assert (
        identity_privacy_retention_boundary["non_authority_assertions"]["identity_reference_is_not_identity_authority"]
        is True
    )
    assert (
        identity_privacy_retention_boundary["non_authority_assertions"]["privacy_classification_is_not_privacy_authority"]
        is True
    )
    assert (
        identity_privacy_retention_boundary["non_authority_assertions"]["retention_metadata_is_not_retention_authority"]
        is True
    )
    assert (
        identity_privacy_retention_boundary["non_authority_assertions"]["memory_is_not_source_of_truth"]
        is True
    )
    messaging_continuity_affinity_occupancy_restoration_boundary = result[
        "household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary"
    ]
    assert (
        messaging_continuity_affinity_occupancy_restoration_boundary["boundary_path"]
        == "governed_household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary"
    )
    assert messaging_continuity_affinity_occupancy_restoration_boundary["boundary_status"] == "active"
    assert (
        messaging_continuity_affinity_occupancy_restoration_boundary["messaging_separation"][
            "messaging_separated"
        ]
        is True
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_boundary["continuity_separation"][
            "continuity_separated"
        ]
        is True
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_boundary["affinity_separation"][
            "affinity_separated"
        ]
        is True
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_boundary["occupancy_separation"][
            "occupancy_separated"
        ]
        is True
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_boundary["restoration_separation"][
            "restoration_separated"
        ]
        is True
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_boundary["separation_explainability"][
            "separation_permitted"
        ]
        is True
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_boundary["authority_relationships"][
            "redefines_messaging_authority"
        ]
        is False
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_boundary["authority_relationships"][
            "redefines_occupancy_authority"
        ]
        is False
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_boundary["authority_relationships"][
            "redefines_restoration_authority"
        ]
        is False
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_boundary["authority_relationships"][
            "replaces_source_of_truth_authority"
        ]
        is False
    )
    provenance_diagnostics_explainability_boundary = result[
        "household_memory_provenance_diagnostics_explainability_boundary"
    ]
    assert (
        provenance_diagnostics_explainability_boundary["boundary_path"]
        == "governed_household_memory_provenance_diagnostics_explainability_boundary"
    )
    assert provenance_diagnostics_explainability_boundary["boundary_status"] == "active"
    assert (
        provenance_diagnostics_explainability_boundary["provenance_visibility"]["provenance_ref_count"]
        == 1
    )
    assert (
        provenance_diagnostics_explainability_boundary["provenance_visibility"]["provenance_status"]
        == "active"
    )
    assert (
        provenance_diagnostics_explainability_boundary["diagnostics_visibility"][
            "governance_boundary_ref_count"
        ]
        == 1
    )
    assert (
        provenance_diagnostics_explainability_boundary["diagnostics_visibility"][
            "provenance_ref_count"
        ]
        == 1
    )
    assert (
        provenance_diagnostics_explainability_boundary["governance_explainability"][
            "delivery_permitted"
        ]
        is True
    )
    assert (
        provenance_diagnostics_explainability_boundary["governance_explainability"]["decision_reason"]
        == "delivery_permitted"
    )
    assert (
        provenance_diagnostics_explainability_boundary["governance_explainability"][
            "governance_boundary_involved"
        ]
        == "notification_delivery_boundary"
    )
    assert (
        provenance_diagnostics_explainability_boundary["explainability_visibility"]["runtime_derived_only"]
        is True
    )
    assert (
        provenance_diagnostics_explainability_boundary["explainability_visibility"][
            "generated_reasoning_used"
        ]
        is False
    )
    assert (
        provenance_diagnostics_explainability_boundary["non_authority_assertions"][
            "claims_household_truth_authority"
        ]
        is False
    )
    assert (
        provenance_diagnostics_explainability_boundary["non_authority_assertions"][
            "claims_identity_authority"
        ]
        is False
    )
    assert (
        provenance_diagnostics_explainability_boundary["non_authority_assertions"][
            "claims_messaging_authority"
        ]
        is False
    )
    assert (
        provenance_diagnostics_explainability_boundary["non_authority_assertions"][
            "claims_occupancy_authority"
        ]
        is False
    )
    assert (
        provenance_diagnostics_explainability_boundary["non_authority_assertions"][
            "claims_privacy_authority"
        ]
        is False
    )
    assert (
        provenance_diagnostics_explainability_boundary["non_authority_assertions"][
            "claims_retention_authority"
        ]
        is False
    )
    assert (
        provenance_diagnostics_explainability_boundary["non_authority_assertions"][
            "claims_restoration_authority"
        ]
        is False
    )
    assert (
        provenance_diagnostics_explainability_boundary["non_authority_assertions"][
            "claims_source_of_truth_authority"
        ]
        is False
    )
    provenance = result["messaging_provenance"]
    assert provenance["created_by"]["actor_state"] == "system"
    assert provenance["delivered_to"]["destination_reference"]["target_id"] == "phone"
    assert provenance["delivered_to"]["destination_reference"]["service"] == "notify.phone"
    assert provenance["created_in_room"]["room_reference"]["area_id"] == area.id
    assert provenance["created_via"]["method"] == "service"
    assert provenance["routing_decision"]["delivery_channel"] == "mobile_notify"
    assert provenance["routing_decision"]["routing_path"] == "person_mobile_target_fallback"
    assert provenance["authority_boundary"]["claims_upstream_truth"] is False
    assert provenance["authority_boundary"]["claims_identity_authority"] is False
    assert provenance["authority_boundary"]["claims_household_memory_authority"] is False
    delivery_boundary = result["notification_delivery_boundary"]
    assert delivery_boundary["applicable"] is True
    assert delivery_boundary["boundary_path"] == "governed_notification_delivery_boundary"
    assert delivery_boundary["governance_controls"]["delivery_channel"] == "mobile_notify"
    assert delivery_boundary["governance_controls"]["selected_service"] == "notify.phone"
    assert delivery_boundary["governance_controls"]["selected_target_id"] == "phone"
    assert delivery_boundary["governance_controls"]["routing_path"] == "person_mobile_target_fallback"
    assert delivery_boundary["governance_controls"]["recipient_authorization_enabled"] is False
    assert delivery_boundary["governance_controls"]["consent_adjudication_enabled"] is False
    assert delivery_boundary["governance_controls"]["visibility_adjudication_enabled"] is False
    recipient_boundary = result["recipient_consent_privacy_visibility_boundary"]
    assert recipient_boundary["applicable"] is True
    assert recipient_boundary["boundary_path"] == "governed_recipient_consent_privacy_visibility_boundary"
    assert recipient_boundary["eligibility_decision"]["delivery_permitted"] is True
    assert recipient_boundary["eligibility_decision"]["decision_reason"] == "delivery_permitted"
    assert recipient_boundary["explainability"]["recipient_authority_claimed"] is False
    assert recipient_boundary["explainability"]["consent_authority_claimed"] is False
    assert recipient_boundary["explainability"]["privacy_authority_claimed"] is False
    assert recipient_boundary["explainability"]["visibility_authority_claimed"] is False
    assert notify_calls[0]["message"] == "Hello Tom"
    assert notify_calls[0]["title"] == "Concierge"


async def test_push_person_message_routes_to_room_voice_assistant(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Room-linked voice assistant delivery should use Assist Satellite announce with TTS media."""
    area = ar.async_get(hass).async_create(name="Den")
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="tom",
            name="Tom",
            linked_area_id=area.id,
            mobile_notify_targets=["phone"],
            preferred_mobile_target="phone",
        )
    )
    await storage.async_update_room_config(
        area.id,
        voice_device_entity_ids=["assist_satellite.den_voice"],
    )

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    entry.options["tts_enabled"] = True
    entry.options["tts_provider"] = "google_translate"

    assist_calls: list[dict[str, object]] = []
    tts_calls: list[dict[str, object]] = []

    async def _assist_handler(call) -> None:
        assist_calls.append(dict(call.data))

    async def _tts_get_url_handler(call) -> dict[str, object]:
        tts_calls.append(dict(call.data))
        return {"path": "media-source://tts/den-voice-test"}

    hass.services.async_register("assist_satellite", "announce", _assist_handler)
    hass.services.async_register("tts", "get_url", _tts_get_url_handler)

    result = await hass.services.async_call(
        DOMAIN,
        "push_person_message",
        {
            "person_id": "tom",
            "target_id": "voice_assistant",
            "message": "Hello Den",
        },
        blocking=True,
        return_response=True,
    )

    assert result["sent"] is True
    assert result["target_id"] == "assist_satellite.den_voice"
    assert result["service"] == "assist_satellite.announce"
    assert result["messaging_provenance"]["routing_decision"]["delivery_channel"] == "voice_assistant"
    assert result["messaging_provenance"]["routing_decision"]["routing_path"] == "resolved_room_voice_assistant_target"
    assert result["notification_delivery_boundary"]["governance_controls"]["delivery_channel"] == "voice_assistant"
    assert result["notification_delivery_boundary"]["governance_controls"]["selected_service"] == "assist_satellite.announce"
    assert result["notification_delivery_boundary"]["governance_controls"]["routing_path"] == "resolved_room_voice_assistant_target"
    assert assist_calls[0]["entity_id"] == "assist_satellite.den_voice"
    assert assist_calls[0]["media_id"] == "media-source://tts/den-voice-test"
    assert "message" not in assist_calls[0]
    assert tts_calls[0]["engine_id"] == "tts.google_translate_en_com"
    assert tts_calls[0]["message"] == "Hello Den"


async def test_push_person_message_routes_to_room_speakers_as_tts(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Room-linked speakers should receive TTS announcements through the configured engine."""
    area = ar.async_get(hass).async_create(name="Den")
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="tom",
            name="Tom",
            linked_area_id=area.id,
            mobile_notify_targets=["phone"],
            preferred_mobile_target="phone",
        )
    )
    await storage.async_update_room_config(
        area.id,
        media_player_entity_ids=["media_player.den_speaker"],
        tts_voice="alice",
        tts_language="en",
    )

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    entry.options["tts_enabled"] = True
    entry.options["tts_provider"] = "google_translate"

    tts_calls: list[dict[str, object]] = []

    async def _tts_handler(call) -> None:
        tts_calls.append(dict(call.data))

    hass.services.async_register("tts", "speak", _tts_handler)

    result = await hass.services.async_call(
        DOMAIN,
        "push_person_message",
        {
            "person_id": "tom",
            "target_id": "speaker",
            "message": "Hello Den",
        },
        blocking=True,
        return_response=True,
    )

    assert result["sent"] is True
    assert result["target_id"] == "media_player.den_speaker"
    assert result["service"] == "tts.speak"
    assert result["messaging_provenance"]["routing_decision"]["delivery_channel"] == "room_tts"
    assert result["messaging_provenance"]["routing_decision"]["routing_path"] == "resolved_room_speaker_target"
    assert result["notification_delivery_boundary"]["governance_controls"]["delivery_channel"] == "room_tts"
    assert result["notification_delivery_boundary"]["governance_controls"]["selected_service"] == "tts.speak"
    assert result["notification_delivery_boundary"]["governance_controls"]["routing_path"] == "resolved_room_speaker_target"
    assert tts_calls[0]["entity_id"] == "tts.google_translate_en_com"
    assert tts_calls[0]["media_player_entity_id"] == "media_player.den_speaker"
    assert tts_calls[0]["message"] == "Hello Den"
    assert tts_calls[0]["language"] == "en"
    assert tts_calls[0]["options"]["voice"] == "alice"


async def test_push_person_message_falls_back_to_integration_tts_defaults(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Empty room TTS settings should fall back to Assistant defaults when available."""
    area = ar.async_get(hass).async_create(name="Den")
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="tom",
            name="Tom",
            linked_area_id=area.id,
            mobile_notify_targets=["phone"],
            preferred_mobile_target="phone",
        )
    )
    await storage.async_update_room_config(
        area.id,
        media_player_entity_ids=["media_player.den_speaker"],
    )

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    entry.options["tts_enabled"] = True
    entry.options["tts_provider"] = "google_translate"

    tts_calls: list[dict[str, object]] = []

    async def _tts_handler(call) -> None:
        tts_calls.append(dict(call.data))

    hass.services.async_register("tts", "speak", _tts_handler)

    result = await hass.services.async_call(
        DOMAIN,
        "push_person_message",
        {
            "person_id": "tom",
            "target_id": "speaker",
            "message": "Hello Den",
        },
        blocking=True,
        return_response=True,
    )

    assert result["sent"] is True
    assert result["target_id"] == "media_player.den_speaker"
    assert result["service"] == "tts.speak"
    assert tts_calls[0]["media_player_entity_id"] == "media_player.den_speaker"
    assert tts_calls[0]["message"] == "Hello Den"


async def test_push_person_message_room_tts_runs_bounded_duck_speak_restore_lifecycle(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Room TTS should apply bounded duck/speak/restore without media continuation behavior."""
    area = ar.async_get(hass).async_create(name="Den")
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="tom",
            name="Tom",
            linked_area_id=area.id,
            mobile_notify_targets=["phone"],
            preferred_mobile_target="phone",
        )
    )
    await storage.async_update_room_config(
        area.id,
        media_player_entity_ids=["media_player.den_a", "media_player.den_b"],
    )

    state = await storage.async_load_state()
    state.usual_states[services_module._room_audio_state_id(area_id=area.id, channel="duck")] = UsualState(
        state_id=services_module._room_audio_state_id(area_id=area.id, channel="duck"),
        scope="room",
        scope_ref=area.id,
        basis=UsualStateBasis.LEARNED,
        updated_at=datetime.now(timezone.utc).isoformat(),
        values={"channel": "duck", "volume_pct": 20, "area_id": area.id},
        metadata={"policy_name": "experience_continuity_room_audio_memory_ec_d_01"},
    )
    state.usual_states[services_module._room_audio_state_id(area_id=area.id, channel="tts")] = UsualState(
        state_id=services_module._room_audio_state_id(area_id=area.id, channel="tts"),
        scope="room",
        scope_ref=area.id,
        basis=UsualStateBasis.LEARNED,
        updated_at=datetime.now(timezone.utc).isoformat(),
        values={"channel": "tts", "volume_pct": 55, "area_id": area.id},
        metadata={"policy_name": "experience_continuity_room_audio_memory_ec_d_01"},
    )
    await storage.async_save_state(state)

    hass.states.async_set("media_player.den_a", "playing", {"volume_level": 0.6})
    hass.states.async_set("media_player.den_b", "paused", {"volume_level": 0.4})

    volume_calls: list[dict[str, object]] = []
    tts_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")
    if hass.services.has_service("tts", "speak"):
        hass.services.async_remove("tts", "speak")

    async def _volume_set(call):
        volume_calls.append(dict(call.data))

    async def _tts_speak(call):
        tts_calls.append(dict(call.data))

    hass.services.async_register("media_player", "volume_set", _volume_set)
    hass.services.async_register("tts", "speak", _tts_speak)

    result = await hass.services.async_call(
        DOMAIN,
        "push_person_message",
        {
            "person_id": "tom",
            "target_id": "speaker",
            "message": "Bounded lifecycle test",
        },
        blocking=True,
        return_response=True,
    )

    lifecycle = result["speech_media_separation_lifecycle"]
    assert result["sent"] is True
    assert lifecycle["policy_name"] == "experience_continuity_sonos_speech_ec_d_02"
    assert lifecycle["speech"]["delivery_succeeded"] is True
    assert lifecycle["duck"]["volume_pct"] == 20
    assert lifecycle["speech"]["volume_pct"] == 55
    assert lifecycle["restore"]["media_continuation_performed"] is False
    assert lifecycle["restore"]["playback_resume_performed"] is False
    assert tts_calls and tts_calls[0]["media_player_entity_id"] == "media_player.den_a"
    assert len(volume_calls) == 5


async def test_push_person_message_room_tts_uses_deterministic_fallback_when_room_audio_memory_missing(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Missing duck/TTS room memory should use deterministic fallback and still avoid media continuation."""
    area = ar.async_get(hass).async_create(name="Den")
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="tom",
            name="Tom",
            linked_area_id=area.id,
            mobile_notify_targets=["phone"],
            preferred_mobile_target="phone",
        )
    )
    await storage.async_update_room_config(
        area.id,
        media_player_entity_ids=["media_player.den_speaker"],
    )

    hass.states.async_set("media_player.den_speaker", "playing", {})

    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")
    if hass.services.has_service("tts", "speak"):
        hass.services.async_remove("tts", "speak")

    async def _volume_set(_call):
        return None

    async def _tts_speak(_call):
        return None

    hass.services.async_register("media_player", "volume_set", _volume_set)
    hass.services.async_register("tts", "speak", _tts_speak)

    result = await hass.services.async_call(
        DOMAIN,
        "push_person_message",
        {
            "person_id": "tom",
            "target_id": "speaker",
            "message": "Fallback lifecycle test",
        },
        blocking=True,
        return_response=True,
    )

    lifecycle = result["speech_media_separation_lifecycle"]
    assert result["sent"] is True
    assert lifecycle["fallback_used"] is True
    assert lifecycle["duck"]["fallback_reason"] == "room_audio_value_missing"
    assert lifecycle["speech"]["fallback_reason"] == "room_audio_value_missing"
    assert lifecycle["restore"]["media_continuation_performed"] is False
    assert lifecycle["restore"]["playback_resume_performed"] is False


async def test_push_person_message_room_tts_restores_after_tts_failure_without_media_resume(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """TTS failures should still run restore and must not trigger any media continuation behavior."""
    area = ar.async_get(hass).async_create(name="Den")
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="tom",
            name="Tom",
            linked_area_id=area.id,
            mobile_notify_targets=["phone"],
            preferred_mobile_target="phone",
        )
    )
    await storage.async_update_room_config(
        area.id,
        media_player_entity_ids=["media_player.den_speaker"],
    )

    hass.states.async_set("media_player.den_speaker", "paused", {"volume_level": 0.49})

    volume_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")
    if hass.services.has_service("tts", "speak"):
        hass.services.async_remove("tts", "speak")

    async def _volume_set(call):
        volume_calls.append(dict(call.data))

    async def _tts_speak(_call):
        raise RuntimeError("tts speak failed")

    hass.services.async_register("media_player", "volume_set", _volume_set)
    hass.services.async_register("tts", "speak", _tts_speak)

    with pytest.raises(Exception):
        await hass.services.async_call(
            DOMAIN,
            "push_person_message",
            {
                "person_id": "tom",
                "target_id": "speaker",
                "message": "Failure lifecycle test",
            },
            blocking=True,
            return_response=True,
        )

    assert len(volume_calls) >= 3
    assert abs(float(volume_calls[-1]["volume_level"]) - 0.49) < 0.0001


async def test_push_person_message_room_tts_merged_room_grouped_lifecycle_preserves_constituent_memory(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Merged-room room-TTS should group output while preserving per-room memory and no merged-memory key."""
    floor = fr.async_get(hass).async_create(name="Main")
    area_registry = ar.async_get(hass)
    room_a = area_registry.async_create(name="Living Room", floor_id=floor.floor_id)
    room_b = area_registry.async_create(name="Kitchen", floor_id=floor.floor_id)

    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="tom",
            name="Tom",
            linked_area_id=room_a.id,
            mobile_notify_targets=["phone"],
            preferred_mobile_target="phone",
        )
    )
    await storage.async_update_room_config(
        room_a.id,
        media_player_entity_ids=["media_player.living_main"],
    )
    await storage.async_update_room_config(
        room_b.id,
        media_player_entity_ids=["media_player.kitchen_main"],
    )
    await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "public_space",
            "name": "Public Space",
            "area_ids": [room_a.id, room_b.id],
            "primary_area": room_a.id,
        },
        blocking=True,
    )

    state = await storage.async_load_state()
    state.usual_states[services_module._room_audio_state_id(area_id=room_a.id, channel="music")] = UsualState(
        state_id=services_module._room_audio_state_id(area_id=room_a.id, channel="music"),
        scope="room",
        scope_ref=room_a.id,
        basis=UsualStateBasis.LEARNED,
        updated_at=datetime.now(timezone.utc).isoformat(),
        values={"channel": "music", "volume_pct": 30, "area_id": room_a.id},
        metadata={"policy_name": "experience_continuity_room_audio_memory_ec_d_01"},
    )
    state.usual_states[services_module._room_audio_state_id(area_id=room_b.id, channel="music")] = UsualState(
        state_id=services_module._room_audio_state_id(area_id=room_b.id, channel="music"),
        scope="room",
        scope_ref=room_b.id,
        basis=UsualStateBasis.LEARNED,
        updated_at=datetime.now(timezone.utc).isoformat(),
        values={"channel": "music", "volume_pct": 60, "area_id": room_b.id},
        metadata={"policy_name": "experience_continuity_room_audio_memory_ec_d_01"},
    )
    state.usual_states[services_module._room_audio_state_id(area_id=room_a.id, channel="duck")] = UsualState(
        state_id=services_module._room_audio_state_id(area_id=room_a.id, channel="duck"),
        scope="room",
        scope_ref=room_a.id,
        basis=UsualStateBasis.LEARNED,
        updated_at=datetime.now(timezone.utc).isoformat(),
        values={"channel": "duck", "volume_pct": 18, "area_id": room_a.id},
        metadata={"policy_name": "experience_continuity_room_audio_memory_ec_d_01"},
    )
    state.usual_states[services_module._room_audio_state_id(area_id=room_b.id, channel="duck")] = UsualState(
        state_id=services_module._room_audio_state_id(area_id=room_b.id, channel="duck"),
        scope="room",
        scope_ref=room_b.id,
        basis=UsualStateBasis.LEARNED,
        updated_at=datetime.now(timezone.utc).isoformat(),
        values={"channel": "duck", "volume_pct": 22, "area_id": room_b.id},
        metadata={"policy_name": "experience_continuity_room_audio_memory_ec_d_01"},
    )
    state.usual_states[services_module._room_audio_state_id(area_id=room_a.id, channel="tts")] = UsualState(
        state_id=services_module._room_audio_state_id(area_id=room_a.id, channel="tts"),
        scope="room",
        scope_ref=room_a.id,
        basis=UsualStateBasis.LEARNED,
        updated_at=datetime.now(timezone.utc).isoformat(),
        values={"channel": "tts", "volume_pct": 45, "area_id": room_a.id},
        metadata={"policy_name": "experience_continuity_room_audio_memory_ec_d_01"},
    )
    state.usual_states[services_module._room_audio_state_id(area_id=room_b.id, channel="tts")] = UsualState(
        state_id=services_module._room_audio_state_id(area_id=room_b.id, channel="tts"),
        scope="room",
        scope_ref=room_b.id,
        basis=UsualStateBasis.LEARNED,
        updated_at=datetime.now(timezone.utc).isoformat(),
        values={"channel": "tts", "volume_pct": 52, "area_id": room_b.id},
        metadata={"policy_name": "experience_continuity_room_audio_memory_ec_d_01"},
    )
    await storage.async_save_state(state)

    hass.states.async_set("media_player.living_main", "playing", {"volume_level": 0.61})
    hass.states.async_set("media_player.kitchen_main", "paused", {"volume_level": 0.42})

    volume_calls: list[dict[str, object]] = []
    tts_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")
    if hass.services.has_service("tts", "speak"):
        hass.services.async_remove("tts", "speak")

    async def _volume_set(call):
        volume_calls.append(dict(call.data))

    async def _tts_speak(call):
        tts_calls.append(dict(call.data))

    hass.services.async_register("media_player", "volume_set", _volume_set)
    hass.services.async_register("tts", "speak", _tts_speak)

    result = await hass.services.async_call(
        DOMAIN,
        "push_person_message",
        {
            "person_id": "tom",
            "target_id": "speaker",
            "message": "Merged room lifecycle test",
        },
        blocking=True,
        return_response=True,
    )

    lifecycle = result["speech_media_separation_lifecycle"]
    assert result["sent"] is True
    assert lifecycle["merged_room_participation"] is True
    assert lifecycle["resolved_composite_id"] == "public_space"
    assert sorted(lifecycle["participating_rooms"]) == sorted([room_a.id, room_b.id])
    assert sorted(lifecycle["group_targeted_speakers"]) == ["media_player.kitchen_main", "media_player.living_main"]
    assert lifecycle["restore"]["media_continuation_performed"] is False
    assert lifecycle["restore"]["playback_resume_performed"] is False
    assert len(tts_calls) == 2
    assert sorted(str(item["media_player_entity_id"]) for item in tts_calls) == [
        "media_player.kitchen_main",
        "media_player.living_main",
    ]

    duck_by_speaker = {
        str(item["entity_id"]): int(item["duck_volume_pct"])
        for item in lifecycle["duck"]["actions"]
        if item.get("applied")
    }
    assert duck_by_speaker["media_player.living_main"] == 18
    assert duck_by_speaker["media_player.kitchen_main"] == 22

    speech_by_speaker = {
        str(item["entity_id"]): int(item["volume_pct"])
        for item in lifecycle["speech"]["actions"]
    }
    assert speech_by_speaker["media_player.living_main"] == 45
    assert speech_by_speaker["media_player.kitchen_main"] == 52
    assert all(item.get("delivery_succeeded") for item in lifecycle["speech"]["actions"])

    restored_by_speaker = {
        str(item["entity_id"]): int(item["restored_volume_pct"])
        for item in lifecycle["restore"]["actions"]
        if item.get("restored")
    }
    assert restored_by_speaker["media_player.living_main"] == 61
    assert restored_by_speaker["media_player.kitchen_main"] == 42

    assert all(item.get("domain") == "media_player" and item.get("service") == "volume_set" for item in volume_calls)

    post = await storage.async_load_state()
    a_music, _, _ = services_module._resolve_room_audio_level(state=post, area_id=room_a.id, channel="music")
    b_music, _, _ = services_module._resolve_room_audio_level(state=post, area_id=room_b.id, channel="music")
    a_duck, _, _ = services_module._resolve_room_audio_level(state=post, area_id=room_a.id, channel="duck")
    b_duck, _, _ = services_module._resolve_room_audio_level(state=post, area_id=room_b.id, channel="duck")
    a_tts, _, _ = services_module._resolve_room_audio_level(state=post, area_id=room_a.id, channel="tts")
    b_tts, _, _ = services_module._resolve_room_audio_level(state=post, area_id=room_b.id, channel="tts")
    assert (a_music, b_music) == (30, 60)
    assert (a_duck, b_duck) == (18, 22)
    assert (a_tts, b_tts) == (45, 52)
    assert all("public_space" not in key for key in post.usual_states)


async def test_push_person_message_room_tts_merged_room_does_not_discover_replacement_speakers(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Merged-room room-TTS must not discover replacement speakers for rooms with no configured mappings."""
    floor = fr.async_get(hass).async_create(name="Main")
    area_registry = ar.async_get(hass)
    room_a = area_registry.async_create(name="Living Room", floor_id=floor.floor_id)
    room_b = area_registry.async_create(name="Kitchen", floor_id=floor.floor_id)

    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="tom",
            name="Tom",
            linked_area_id=room_a.id,
            mobile_notify_targets=["phone"],
            preferred_mobile_target="phone",
        )
    )
    await storage.async_update_room_config(
        room_a.id,
        media_player_entity_ids=["media_player.living_main"],
    )
    await storage.async_update_room_config(
        room_b.id,
        media_player_entity_ids=[],
        speaker_entity_ids=[],
    )
    await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "public_space",
            "name": "Public Space",
            "area_ids": [room_a.id, room_b.id],
            "primary_area": room_a.id,
        },
        blocking=True,
    )

    entity = er.async_get(hass).async_get_or_create(
        "media_player",
        DOMAIN,
        "kitchen_unconfigured",
        area_id=room_b.id,
    )
    hass.states.async_set("media_player.living_main", "playing", {"volume_level": 0.45})
    hass.states.async_set(entity.entity_id, "playing", {"volume_level": 0.88})

    tts_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")
    if hass.services.has_service("tts", "speak"):
        hass.services.async_remove("tts", "speak")

    async def _volume_set(_call):
        return None

    async def _tts_speak(call):
        tts_calls.append(dict(call.data))

    hass.services.async_register("media_player", "volume_set", _volume_set)
    hass.services.async_register("tts", "speak", _tts_speak)

    result = await hass.services.async_call(
        DOMAIN,
        "push_person_message",
        {
            "person_id": "tom",
            "target_id": "speaker",
            "message": "No replacement discovery",
        },
        blocking=True,
        return_response=True,
    )

    lifecycle = result["speech_media_separation_lifecycle"]
    assert lifecycle["merged_room_participation"] is True
    assert lifecycle["group_targeted_speakers"] == ["media_player.living_main"]
    assert all(
        str(item.get("area_id")) != room_b.id or not item.get("validated_speakers")
        for item in lifecycle["grouped_validation_results"]
    )
    assert tts_calls and tts_calls[0]["media_player_entity_id"] == "media_player.living_main"
    assert all(str(item.get("media_player_entity_id")) != entity.entity_id for item in tts_calls)


async def test_push_person_message_room_tts_falls_back_when_preferred_speaker_unavailable(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Unavailable preferred speaker should deterministically fall back to validated configured room speakers."""
    area = ar.async_get(hass).async_create(name="Den")
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="tom",
            name="Tom",
            linked_area_id=area.id,
            mobile_notify_targets=["phone"],
            preferred_mobile_target="phone",
        )
    )
    await storage.async_update_room_config(
        area.id,
        media_player_entity_ids=["media_player.den_a", "media_player.den_b"],
    )

    hass.states.async_set("media_player.den_a", "unavailable", {})
    hass.states.async_set("media_player.den_b", "playing", {"volume_level": 0.5})

    tts_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")
    if hass.services.has_service("tts", "speak"):
        hass.services.async_remove("tts", "speak")

    async def _volume_set(_call):
        return None

    async def _tts_speak(call):
        tts_calls.append(dict(call.data))

    hass.services.async_register("media_player", "volume_set", _volume_set)
    hass.services.async_register("tts", "speak", _tts_speak)

    result = await hass.services.async_call(
        DOMAIN,
        "push_person_message",
        {
            "person_id": "tom",
            "target_id": "media_player.den_a",
            "message": "Fallback preferred speaker",
        },
        blocking=True,
        return_response=True,
    )

    lifecycle = result["speech_media_separation_lifecycle"]
    assert result["sent"] is True
    assert lifecycle["group_targeted_speakers"] == ["media_player.den_b"]
    assert lifecycle["target_resolution"]["fallback_reason"] == "preferred_speaker_unavailable"
    assert lifecycle["target_resolution"]["decision_reason"] == "preferred_speaker_unavailable_fallback_to_validated_speakers"
    assert lifecycle["speech"]["delivery_succeeded"] is True
    assert tts_calls and tts_calls[0]["media_player_entity_id"] == "media_player.den_b"


async def test_push_person_message_room_tts_refuses_when_no_valid_configured_speakers(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """When no configured speakers validate, room-TTS should fail deterministically without replacement discovery."""
    area = ar.async_get(hass).async_create(name="Den")
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="tom",
            name="Tom",
            linked_area_id=area.id,
            mobile_notify_targets=["phone"],
            preferred_mobile_target="phone",
        )
    )
    await storage.async_update_room_config(
        area.id,
        media_player_entity_ids=["media_player.den_a"],
    )

    hass.states.async_set("media_player.den_a", "unavailable", {})

    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")
    if hass.services.has_service("tts", "speak"):
        hass.services.async_remove("tts", "speak")

    async def _volume_set(_call):
        return None

    async def _tts_speak(_call):
        return None

    hass.services.async_register("media_player", "volume_set", _volume_set)
    hass.services.async_register("tts", "speak", _tts_speak)

    with pytest.raises(Exception, match="no_target_speakers_available"):
        await hass.services.async_call(
            DOMAIN,
            "push_person_message",
            {
                "person_id": "tom",
                "target_id": "speaker",
                "message": "No valid speakers",
            },
            blocking=True,
            return_response=True,
        )


async def test_push_person_message_delivery_failure_records_error_activity(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Delivery failures should be tracked as execution errors with bounded delivery refs."""
    area = ar.async_get(hass).async_create(name="Living Room")
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="tom",
            name="Tom",
            linked_area_id=area.id,
            mobile_notify_targets=["missing_target"],
            preferred_mobile_target="missing_target",
        )
    )

    with pytest.raises(Exception):
        await hass.services.async_call(
            DOMAIN,
            "push_person_message",
            {
                "person_id": "tom",
                "message": "Hello Tom",
            },
            blocking=True,
            return_response=True,
        )

    state = await ConciergeStorage(hass).async_load_state()
    activities = sorted(
        [item for item in state.activities.values() if item.intent_class == "push_person_message"],
        key=lambda item: str(item.started_at),
        reverse=True,
    )
    assert activities
    latest = activities[0]
    assert latest.outcome == "error"
    boundary_ref = next(
        ref for ref in latest.external_refs if ref.get("ref_type") == "notification_delivery_boundary"
    )
    assert boundary_ref["boundary_path"] == "governed_notification_delivery_boundary"
    assert boundary_ref["delivery_channel"] == "mobile_notify"
    assert boundary_ref["selected_service"] == "notify.missing_target"
    assert boundary_ref["routing_path"] == "person_mobile_target_fallback"
    execution_refs = [
        ref for ref in latest.external_refs if ref.get("ref_type") == "delivery_execution"
    ]
    assert execution_refs
    assert any(ref.get("execution_state") == "attempting" for ref in execution_refs)
    assert not any(ref.get("execution_state") == "success" for ref in execution_refs)


async def test_push_person_message_denies_when_consent_is_required_but_absent(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Consent-required profiles should fail closed when delivery consent is not granted."""
    area = ar.async_get(hass).async_create(name="Living Room")
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="tom",
            name="Tom",
            linked_area_id=area.id,
            consent={"require_delivery_consent": True},
            mobile_notify_targets=["phone"],
            preferred_mobile_target="phone",
        )
    )

    with pytest.raises(Exception):
        await hass.services.async_call(
            DOMAIN,
            "push_person_message",
            {
                "person_id": "tom",
                "target_id": "web_ui",
                "message": "Consent gate test",
            },
            blocking=True,
            return_response=True,
        )

    state = await ConciergeStorage(hass).async_load_state()
    activities = sorted(
        [item for item in state.activities.values() if item.intent_class == "push_person_message"],
        key=lambda item: str(item.started_at),
        reverse=True,
    )
    assert activities
    latest = activities[0]
    assert latest.outcome == "policy_denied"
    assert "consent_required_not_granted" in latest.outcome_reason
    boundary_ref = next(
        ref
        for ref in latest.external_refs
        if ref.get("ref_type") == "recipient_consent_privacy_visibility_boundary"
    )
    assert boundary_ref["delivery_permitted"] is False
    assert boundary_ref["decision_reason"] == "consent_required_not_granted"
    assert boundary_ref["refusal_reason"] == "consent_required_not_granted"
    assert boundary_ref["refusal_category"] == "policy_denied"
    diagnostics_ref = next(
        ref
        for ref in latest.external_refs
        if ref.get("ref_type") == "messaging_diagnostics_explainability"
    )
    assert diagnostics_ref["delivery_permitted"] is False
    assert diagnostics_ref["decision_reason"] == "consent_required_not_granted"
    assert diagnostics_ref["governance_boundary_involved"] == "recipient_consent_privacy_visibility_boundary"
    memory_boundary_ref = next(
        ref
        for ref in latest.external_refs
        if ref.get("ref_type") == "household_memory_governance_boundary"
    )
    assert memory_boundary_ref["boundary_path"] == "governed_household_memory_boundary"
    assert memory_boundary_ref["claims_household_truth_authority"] is False
    assert memory_boundary_ref["claims_identity_authority"] is False
    assert memory_boundary_ref["claims_occupancy_authority"] is False
    assert memory_boundary_ref["claims_messaging_authority"] is False
    assert memory_boundary_ref["claims_consent_authority"] is False
    assert memory_boundary_ref["claims_privacy_authority"] is False
    assert memory_boundary_ref["claims_source_of_truth_authority"] is False
    ownership_consumption_ref = next(
        ref
        for ref in latest.external_refs
        if ref.get("ref_type") == "household_memory_ownership_consumption_boundary"
    )
    assert (
        ownership_consumption_ref["boundary_path"]
        == "governed_household_memory_ownership_consumption_boundary"
    )
    assert ownership_consumption_ref["memory_owner"] == "household_memory_governance"
    assert ownership_consumption_ref["memory_runtime_owner"] == "concierge"
    assert ownership_consumption_ref["consumption_permitted"] is False
    assert ownership_consumption_ref["consumption_decision_reason"] == "consent_required_not_granted"
    assert ownership_consumption_ref["claims_household_truth_authority"] is False
    assert ownership_consumption_ref["claims_identity_authority"] is False
    assert ownership_consumption_ref["claims_occupancy_authority"] is False
    assert ownership_consumption_ref["claims_messaging_authority"] is False
    assert ownership_consumption_ref["claims_consent_authority"] is False
    assert ownership_consumption_ref["claims_privacy_authority"] is False
    assert ownership_consumption_ref["claims_source_of_truth_authority"] is False
    identity_privacy_retention_ref = next(
        ref
        for ref in latest.external_refs
        if ref.get("ref_type") == "household_memory_identity_privacy_retention_separation_boundary"
    )
    assert (
        identity_privacy_retention_ref["boundary_path"]
        == "governed_household_memory_identity_privacy_retention_separation_boundary"
    )
    assert identity_privacy_retention_ref["identity_separated"] is True
    assert identity_privacy_retention_ref["privacy_separated"] is True
    assert identity_privacy_retention_ref["retention_separated"] is True
    assert identity_privacy_retention_ref["separation_permitted"] is False
    assert (
        identity_privacy_retention_ref["separation_decision_reason"]
        == "consent_required_not_granted"
    )
    assert identity_privacy_retention_ref["claims_identity_authority"] is False
    assert identity_privacy_retention_ref["claims_privacy_authority"] is False
    assert identity_privacy_retention_ref["claims_retention_authority"] is False
    assert identity_privacy_retention_ref["claims_source_of_truth_authority"] is False
    messaging_continuity_affinity_occupancy_restoration_ref = next(
        ref
        for ref in latest.external_refs
        if ref.get("ref_type")
        == "household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary"
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_ref["boundary_path"]
        == "governed_household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary"
    )
    assert messaging_continuity_affinity_occupancy_restoration_ref["messaging_separated"] is True
    assert messaging_continuity_affinity_occupancy_restoration_ref["continuity_separated"] is True
    assert messaging_continuity_affinity_occupancy_restoration_ref["affinity_separated"] is True
    assert messaging_continuity_affinity_occupancy_restoration_ref["occupancy_separated"] is True
    assert messaging_continuity_affinity_occupancy_restoration_ref["restoration_separated"] is True
    assert messaging_continuity_affinity_occupancy_restoration_ref["separation_permitted"] is False
    assert (
        messaging_continuity_affinity_occupancy_restoration_ref["separation_decision_reason"]
        == "consent_required_not_granted"
    )
    assert messaging_continuity_affinity_occupancy_restoration_ref["claims_household_truth_authority"] is False
    assert messaging_continuity_affinity_occupancy_restoration_ref["claims_messaging_authority"] is False
    assert messaging_continuity_affinity_occupancy_restoration_ref["claims_continuity_authority"] is False
    assert messaging_continuity_affinity_occupancy_restoration_ref["claims_affinity_authority"] is False
    assert messaging_continuity_affinity_occupancy_restoration_ref["claims_occupancy_authority"] is False
    assert messaging_continuity_affinity_occupancy_restoration_ref["claims_restoration_authority"] is False
    assert messaging_continuity_affinity_occupancy_restoration_ref["claims_source_of_truth_authority"] is False
    provenance_diagnostics_explainability_ref = next(
        ref
        for ref in latest.external_refs
        if ref.get("ref_type")
        == "household_memory_provenance_diagnostics_explainability_boundary"
    )
    assert (
        provenance_diagnostics_explainability_ref["boundary_path"]
        == "governed_household_memory_provenance_diagnostics_explainability_boundary"
    )
    assert provenance_diagnostics_explainability_ref["provenance_ref_count"] == 1
    assert provenance_diagnostics_explainability_ref["provenance_status"] == "active"
    assert provenance_diagnostics_explainability_ref["delivery_permitted"] is False
    assert (
        provenance_diagnostics_explainability_ref["decision_reason"]
        == "consent_required_not_granted"
    )
    assert (
        provenance_diagnostics_explainability_ref["governance_boundary_involved"]
        == "recipient_consent_privacy_visibility_boundary"
    )
    assert provenance_diagnostics_explainability_ref["claims_household_truth_authority"] is False
    assert provenance_diagnostics_explainability_ref["claims_identity_authority"] is False
    assert provenance_diagnostics_explainability_ref["claims_messaging_authority"] is False
    assert provenance_diagnostics_explainability_ref["claims_continuity_authority"] is False
    assert provenance_diagnostics_explainability_ref["claims_affinity_authority"] is False
    assert provenance_diagnostics_explainability_ref["claims_occupancy_authority"] is False
    assert provenance_diagnostics_explainability_ref["claims_privacy_authority"] is False
    assert provenance_diagnostics_explainability_ref["claims_retention_authority"] is False
    assert provenance_diagnostics_explainability_ref["claims_restoration_authority"] is False
    assert provenance_diagnostics_explainability_ref["claims_source_of_truth_authority"] is False


async def test_push_person_message_denies_voice_delivery_for_private_only_mode(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Private-only mode should block non-private delivery channels like room voice output."""
    area = ar.async_get(hass).async_create(name="Den")
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="tom",
            name="Tom",
            linked_area_id=area.id,
            consent={"privacy_mode": "private_only"},
            mobile_notify_targets=["phone"],
            preferred_mobile_target="phone",
        )
    )
    await storage.async_update_room_config(
        area.id,
        voice_device_entity_ids=["assist_satellite.den_voice"],
    )

    with pytest.raises(Exception):
        await hass.services.async_call(
            DOMAIN,
            "push_person_message",
            {
                "person_id": "tom",
                "target_id": "voice_assistant",
                "message": "Privacy gate test",
            },
            blocking=True,
            return_response=True,
        )

    state = await ConciergeStorage(hass).async_load_state()
    activities = sorted(
        [item for item in state.activities.values() if item.intent_class == "push_person_message"],
        key=lambda item: str(item.started_at),
        reverse=True,
    )
    assert activities
    latest = activities[0]
    assert latest.outcome == "policy_denied"
    assert "privacy_boundary_channel_restricted" in latest.outcome_reason


async def test_summary_promotes_member_area_to_composite_context(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Summary requests should promote member areas to enabled composite context."""
    floor_registry = fr.async_get(hass)
    main_floor = floor_registry.async_create(name="Main")

    area_registry = ar.async_get(hass)
    kitchen = area_registry.async_create(name="Kitchen", floor_id=main_floor.floor_id)
    dining = area_registry.async_create(name="Dining", floor_id=main_floor.floor_id)

    await hass.services.async_call(
        DOMAIN,
        "update_global_context",
        {
            "context_type": "weather",
            "enabled": True,
            "summary": "Sunny and warm",
            "detail": "High of 82",
            "speakable": "Sunny and warm.",
        },
        blocking=True,
    )

    await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "public_space",
            "name": "Public Space",
            "area_ids": [kitchen.id, dining.id],
            "primary_area": dining.id,
        },
        blocking=True,
    )

    summary = await hass.services.async_call(
        DOMAIN,
        "get_summary",
        {"area_id": kitchen.id, "include_context": True, "include_signals": False},
        blocking=True,
        return_response=True,
    )

    assert summary["area_id"] == kitchen.id
    assert summary["context_area_id"] == dining.id
    assert summary["resolved_composite_id"] == "public_space"
    assert "Sunny and warm" in summary["summary"]


async def test_room_config_service_persists_posture_and_media_targets(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Room config service should persist playback targets and posture."""
    from custom_components.concierge.storage import ConciergeStorage

    area = ar.async_get(hass).async_create(name="Living Room")

    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "posture": "night",
            "media_player_entity_ids": ["media_player.living_room_sonos_2"],
            "tts_voice": "alloy",
            "aliases": {"movie time": "scene.movie_time"},
            "global_overlays": {"weather": True},
        },
        blocking=True,
    )

    state = await ConciergeStorage(hass).async_load_state()
    room = state.rooms[area.id]
    assert room.posture == "night"
    assert room.media_player_entity_ids == ["media_player.living_room_sonos_2"]
    assert room.tts_voice == "alloy"


async def test_room_config_service_rejects_unknown_foundation_area(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Room config mutations must not create room identities outside the HA area registry."""
    with pytest.raises(Exception, match="area registry"):
        await hass.services.async_call(
            DOMAIN,
            "update_room_config",
            {
                "area_id": "missing_room",
                "posture": "night",
            },
            blocking=True,
        )


async def test_room_config_service_persists_voice_devices(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Room config service should persist room voice assistant bindings."""
    from custom_components.concierge.storage import ConciergeStorage

    area = ar.async_get(hass).async_create(name="Den")

    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "voice_device_entity_ids": [
                "assist_satellite.home_assistant_voice_0a87d9_assist_satellite"
            ],
        },
        blocking=True,
    )

    state = await ConciergeStorage(hass).async_load_state()
    assert state.rooms[area.id].voice_device_entity_ids == [
        "assist_satellite.home_assistant_voice_0a87d9_assist_satellite"
    ]


async def test_identity_profile_service_persists_default_profile(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Identity profile service should persist user-facing presentation preferences."""
    from custom_components.concierge.storage import ConciergeStorage

    result = await hass.services.async_call(
        DOMAIN,
        "update_identity_profile",
        {
            "profile_id": "tom",
            "name": "Tom",
            "persona": "technical",
            "tts_voice": "coral",
            "verbosity": "detailed",
            "allow_ai": True,
            "content_type": "technical",
            "detail_level": "high",
            "set_as_default": True,
        },
        blocking=True,
        return_response=True,
    )

    state = await ConciergeStorage(hass).async_load_state()
    profile = state.identity_profiles["tom"]
    assert result["identity_profile_count"] == 1
    assert profile.persona == "technical"
    assert profile.tts_voice == "coral"
    assert state.default_identity_profile is not None
    assert state.default_identity_profile.profile_id == "tom"


async def test_person_profile_service_persists_bindings(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Person profile service should persist consent and device binding state."""
    from custom_components.concierge.storage import ConciergeStorage

    result = await hass.services.async_call(
        DOMAIN,
        "update_person_profile",
        {
            "person_id": "tom",
            "name": "Tom",
            "linked_area_id": "living_room",
            "ble_device_ids": ["ble.tom_tag"],
            "aqara_presence_entity_ids": ["binary_sensor.tom_presence"],
            "voice_profile_id": "tom_voice",
            "email_source_ref": "mailbox.tom@example.com",
            "calendar_source_ref": "calendar.tom",
            "task_source_ref": "tasks.tom",
            "shopping_source_ref": "shopping_list.household",
            "consent": {"person_identity": True},
            "notes": "Primary person profile",
            "set_as_default": True,
        },
        blocking=True,
        return_response=True,
    )

    state = await ConciergeStorage(hass).async_load_state()
    profile = state.person_profiles["tom"]
    assert result["person_profile_count"] == 1
    assert profile.linked_area_id == "living_room"
    assert profile.ble_device_ids == ["ble.tom_tag"]
    assert profile.voice_profile_id == "tom_voice"
    assert profile.email_source_ref == "mailbox.tom@example.com"
    assert profile.calendar_source_ref == "calendar.tom"
    assert profile.task_source_ref == "tasks.tom"
    assert profile.shopping_source_ref == "shopping_list.household"
    assert state.default_person_profile is not None
    assert state.default_person_profile.person_id == "tom"


async def test_runtime_person_context_resolves_exact_person_id_and_exposes_bindings(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Runtime person context should resolve canonical person_id matches and expose approved bindings."""
    area = ar.async_get(hass).async_create(name="Living Room")
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="person.tom",
            name="Tom",
            linked_area_id=area.id,
            voice_profile_id="voice.tom",
            ble_device_ids=["ble.tom_tag"],
            aqara_presence_entity_ids=["binary_sensor.tom_presence"],
            mobile_notify_targets=["mobile_app.tom"],
            preferred_mobile_target="mobile_app.tom",
            email_source_ref="sensor.mailbox_tom",
            calendar_source_ref="sensor.calendar_tom",
            task_source_ref="tasks_provider_tom",
            shopping_source_ref="shopping_list.household",
            consent={"delivery_consent_granted": True},
            minor_allowed_intent_classes=["calendar", "email"],
            guardian_controls_required=True,
        )
    )
    state = await storage.async_load_state()

    active_person_resolution = {
        "active_person_state": "active_person_available",
        "active_person_available": True,
        "resolved_person_id": "person.tom",
        "resolved_voice_profile_id": "voice.tom",
        "reason_code": "attribution_ready",
    }

    runtime_person_context = services_module._build_runtime_person_context(
        state,
        active_person_resolution=active_person_resolution,
    )
    routing = services_module._build_person_aware_productivity_routing(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
    )

    assert runtime_person_context["person_context_state"] == "person_context_resolved"
    assert runtime_person_context["reason_code"] == "person_context_resolved"
    assert runtime_person_context["resolved_person_id"] == "person.tom"
    assert runtime_person_context["resolved_concierge_person_profile_id"] == "person.tom"
    assert runtime_person_context["identity"]["voice_profile_ref"] == "voice.tom"
    assert runtime_person_context["productivity"]["email_source_refs"][0] == "sensor.mailbox_tom"
    assert runtime_person_context["productivity"]["calendar_source_refs"][0] == "sensor.calendar_tom"
    assert runtime_person_context["productivity"]["task_source_refs"][0] == "tasks_provider_tom"
    assert runtime_person_context["productivity"]["shopping_source_refs"][0] == "shopping_list.household"
    assert runtime_person_context["presence"]["ble_device_refs"] == ["ble.tom_tag"]
    assert runtime_person_context["presence"]["presence_entity_refs"] == ["binary_sensor.tom_presence"]
    assert runtime_person_context["presence"]["location_ref"] == area.id
    assert runtime_person_context["mobility"]["mobile_device_refs"] == ["mobile_app.tom"]
    assert runtime_person_context["mobility"]["read_later_target"] == "mobile_app.tom"
    assert runtime_person_context["policy"]["available"] is True
    assert runtime_person_context["policy"]["allowed_intent_abilities"] == ["calendar", "email"]
    assert runtime_person_context["policy"]["minor_controls"]["guardian_controls_required"] is True
    assert routing["routing_enabled"] is True
    assert routing["runtime_person_context"]["person_context_state"] == "person_context_resolved"
    assert routing["domain_routing"]["email"]["selected_source_ref"] == "sensor.mailbox_tom"
    assert routing["domain_routing"]["calendar"]["selected_source_ref"] == "sensor.calendar_tom"
    assert routing["domain_routing"]["task"]["selected_source_ref"] == "tasks_provider_tom"
    assert routing["domain_routing"]["task"]["selection_mode"] == "person_binding"
    assert routing["domain_routing"]["shopping"]["selected_source_ref"] == "shopping_list.household"


def test_preference_resolution_blocks_known_identity_when_policy_disallows_personalization() -> None:
    """Service-layer resolver should fail closed when policy blocks personalization."""
    request = PreferenceResolutionRequest(
        preference_key="music_preference",
        identity_state=PreferenceIdentityState.KNOWN,
        confidence_band=ContinuityConfidenceBand.HIGH,
        person_preference_value="person-choice",
        person_room_exception_value="person-room-choice",
        person_room_exception_enabled=True,
        room_default_value="room-default",
        household_default_value="household-default",
        system_safe_value="system-safe",
        personalization_policy_allowed=False,
        personalization_policy_reason="privacy_opt_out",
    )

    result = services_module._resolve_preference_hierarchy(request)

    assert result.identity_decision["personalization_allowed"] is False
    assert result.identity_decision["policy_allowed"] is False
    assert result.identity_decision["reason_code"] == "identity_policy_disallowed"
    assert result.selected_tier.value == "room_default"
    assert result.selected_value == "room-default"


def test_preference_resolution_missing_room_default_falls_back_to_household_then_system() -> None:
    """Service-layer resolver should retain safe fallback progression when room defaults are absent."""
    household_result = services_module._resolve_preference_hierarchy(
        PreferenceResolutionRequest(
            preference_key="music_preference",
            identity_state=PreferenceIdentityState.GUEST,
            confidence_band=ContinuityConfidenceBand.HIGH,
            person_preference_value="person-choice",
            room_default_value=None,
            household_default_value="household-default",
            system_safe_value="system-safe",
        )
    )
    system_result = services_module._resolve_preference_hierarchy(
        PreferenceResolutionRequest(
            preference_key="music_preference",
            identity_state=PreferenceIdentityState.GUEST,
            confidence_band=ContinuityConfidenceBand.HIGH,
            person_preference_value="person-choice",
            room_default_value=None,
            household_default_value=None,
            system_safe_value="system-safe",
        )
    )

    assert household_result.selected_tier.value == "household_default"
    assert household_result.selected_value == "household-default"
    assert system_result.selected_tier.value == "system_safe_default"
    assert system_result.selected_value == "system-safe"


def test_learning_policy_allows_known_identity_person_scope() -> None:
    """Known high-confidence identity with policy permission should allow learning."""
    outcome = services_module._evaluate_learning_policy(
        LearningPolicyEvaluationRequest(
            learning_key="preferred_genre",
            ownership_scope=LearningOwnershipScope.PERSON,
            identity_state=PreferenceIdentityState.KNOWN,
            confidence_band=ContinuityConfidenceBand.HIGH,
            learning_policy_enabled=True,
            ownership_supported=True,
            entity_eligible=True,
            preference_eligible=True,
            safety_restrictions_clear=True,
            personalization_policy_allowed=True,
            policy_reason="guardian_controls_satisfied",
            metadata={"learning_source": "interaction"},
        )
    )

    assert outcome.learning_allowed is True
    assert outcome.denial_reason is None
    assert outcome.ownership_scope.value == "person"
    assert outcome.write_path.value == "async"
    assert outcome.policy_decision["policy_name"] == "experience_continuity_learning_governance_ec_b_03"
    assert outcome.explainability["storage_target"] == "person_profile_learning"


@pytest.mark.parametrize(
    ("identity_state", "expected_reason"),
    [
        (PreferenceIdentityState.GUEST, "guest_identity_blocked"),
        (PreferenceIdentityState.UNKNOWN, "unknown_identity_blocked"),
        (PreferenceIdentityState.UNAVAILABLE, "unavailable_identity_blocked"),
        (PreferenceIdentityState.LOW_CONFIDENCE, "low_confidence_identity_blocked"),
    ],
)
def test_learning_policy_denies_identity_fail_closed_states(
    identity_state: PreferenceIdentityState,
    expected_reason: str,
) -> None:
    """Guest, unknown, unavailable, and low-confidence states must fail closed."""
    outcome = services_module._evaluate_learning_policy(
        LearningPolicyEvaluationRequest(
            learning_key="preferred_artist",
            ownership_scope=LearningOwnershipScope.PERSON,
            identity_state=identity_state,
            confidence_band=ContinuityConfidenceBand.HIGH,
        )
    )

    assert outcome.learning_allowed is False
    assert outcome.denial_reason == expected_reason
    assert outcome.write_path.value == "none"


def test_learning_policy_denies_when_policy_disabled() -> None:
    """Learning policy disabled must deny writes while preserving explainability metadata."""
    outcome = services_module._evaluate_learning_policy(
        LearningPolicyEvaluationRequest(
            learning_key="preferred_album",
            ownership_scope=LearningOwnershipScope.PERSON,
            identity_state=PreferenceIdentityState.KNOWN,
            confidence_band=ContinuityConfidenceBand.HIGH,
            learning_policy_enabled=False,
        )
    )

    assert outcome.learning_allowed is False
    assert outcome.denial_reason == "learning_policy_disabled"
    assert outcome.explainability["write_disposition"] == "none"


def test_learning_policy_denies_invalid_ownership_target() -> None:
    """Unsupported ownership targets must be denied with deterministic policy reason."""
    outcome = services_module._evaluate_learning_policy(
        LearningPolicyEvaluationRequest(
            learning_key="room_media_context",
            ownership_scope=LearningOwnershipScope.ROOM,
            identity_state=PreferenceIdentityState.KNOWN,
            confidence_band=ContinuityConfidenceBand.HIGH,
            ownership_supported=False,
        )
    )

    assert outcome.learning_allowed is False
    assert outcome.denial_reason == "unsupported_ownership_scope"


def test_learning_policy_enforces_scope_specific_storage_targets() -> None:
    """Learning explainability should preserve person, room, and household ownership targets."""
    person = services_module._evaluate_learning_policy(
        LearningPolicyEvaluationRequest(
            learning_key="preferred_playlist",
            ownership_scope=LearningOwnershipScope.PERSON,
            identity_state=PreferenceIdentityState.KNOWN,
            confidence_band=ContinuityConfidenceBand.HIGH,
        )
    )
    room = services_module._evaluate_learning_policy(
        LearningPolicyEvaluationRequest(
            learning_key="room_media_context",
            ownership_scope=LearningOwnershipScope.ROOM,
            identity_state=PreferenceIdentityState.UNAVAILABLE,
            confidence_band=ContinuityConfidenceBand.UNKNOWN,
            identity_sensitive_learning=False,
        )
    )
    household = services_module._evaluate_learning_policy(
        LearningPolicyEvaluationRequest(
            learning_key="household_default_music",
            ownership_scope=LearningOwnershipScope.HOUSEHOLD,
            identity_state=PreferenceIdentityState.UNAVAILABLE,
            confidence_band=ContinuityConfidenceBand.UNKNOWN,
            identity_sensitive_learning=False,
        )
    )

    assert person.learning_allowed is True
    assert room.learning_allowed is True
    assert household.learning_allowed is True
    assert person.explainability["storage_target"] == "person_profile_learning"
    assert room.explainability["storage_target"] == "room_config_learning"
    assert household.explainability["storage_target"] == "household_default_learning"


def test_learning_policy_identity_sensitive_restriction_blocks_unknown_identity() -> None:
    """Identity-sensitive learning must deny unknown identity when personalization context is required."""
    outcome = services_module._evaluate_learning_policy(
        LearningPolicyEvaluationRequest(
            learning_key="preferred_genre",
            ownership_scope=LearningOwnershipScope.PERSON,
            identity_state=PreferenceIdentityState.UNKNOWN,
            confidence_band=ContinuityConfidenceBand.HIGH,
            identity_sensitive_learning=True,
        )
    )

    assert outcome.learning_allowed is False
    assert outcome.denial_reason == "unknown_identity_blocked"


def test_learning_policy_produces_reversibility_metadata() -> None:
    """Allowed learning must provide rollback-supporting reversibility metadata."""
    outcome = services_module._evaluate_learning_policy(
        LearningPolicyEvaluationRequest(
            learning_key="preferred_genre",
            ownership_scope=LearningOwnershipScope.PERSON,
            identity_state=PreferenceIdentityState.KNOWN,
            confidence_band=ContinuityConfidenceBand.HIGH,
            personalization_policy_allowed=True,
            metadata={"learning_source": "execute"},
        )
    )

    assert outcome.reversibility_metadata["learning_source"] == "execute"
    assert outcome.reversibility_metadata["owner_scope"] == "person"
    assert outcome.reversibility_metadata["policy_used"] == "experience_continuity_learning_governance_ec_b_03"
    assert outcome.reversibility_metadata["rollback_supporting_metadata"] is True


def test_learning_write_enqueue_is_non_blocking_and_async() -> None:
    """Learning writes should be enqueued asynchronously without blocking interaction flow."""

    class _TaskStub:
        def add_done_callback(self, callback):
            self._callback = callback

    class _FakeHass:
        def __init__(self) -> None:
            self.enqueued_count = 0

        def async_create_task(self, coro):
            self.enqueued_count += 1
            coro.close()
            return _TaskStub()

    hass = _FakeHass()
    response = services_module._enqueue_learning_write(
        hass,
        LearningWriteRequest(
            learning_event_id="evt-001",
            learning_key="preferred_genre",
            ownership_scope=LearningOwnershipScope.PERSON,
            owner_ref="person.tom",
            learned_value="jazz",
            reason_code="explicit_user_feedback",
            policy_used="experience_continuity_learning_governance_ec_b_03",
            reversibility_metadata={"owner_scope": "person", "timestamp": "2026-07-22T00:00:00Z"},
            explainability={"learning_allowed": True, "storage_target": "person_profile_learning"},
        ),
    )

    assert hass.enqueued_count == 1
    assert response["write_path"] == "async"
    assert response["write_enqueued"] is True


def test_learning_write_failure_does_not_interrupt_flow() -> None:
    """Asynchronous write failures should not break the immediate interaction response path."""

    class _FailureTask:
        def add_done_callback(self, callback):
            callback(self)

        def result(self):
            raise RuntimeError("write_failure")

    class _FakeHass:
        def async_create_task(self, coro):
            coro.close()
            return _FailureTask()

    response = services_module._enqueue_learning_write(
        _FakeHass(),
        LearningWriteRequest(
            learning_event_id="evt-002",
            learning_key="room_media_context",
            ownership_scope=LearningOwnershipScope.ROOM,
            owner_ref="area.kitchen",
            learned_value={"last_media": "playlist:123"},
            reason_code="continuity_capture",
            policy_used="experience_continuity_learning_governance_ec_b_03",
            reversibility_metadata={"owner_scope": "room", "timestamp": "2026-07-22T00:00:00Z"},
            explainability={"learning_allowed": True, "storage_target": "room_config_learning"},
        ),
    )

    assert response["write_enqueued"] is True
    assert response["queue_ref"] == "learning_queue:evt-002"


async def test_runtime_person_context_resolves_via_voice_profile_reference(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Runtime person context should use voice-profile references when the active person id is not the stored person_id."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="person.tom_grounds",
            name="Tom Grounds",
            voice_profile_id="person.tom",
            email_source_ref="sensor.mailbox_tom",
            calendar_source_ref="sensor.calendar_tom",
            task_source_ref="tasks_provider_tom",
            shopping_source_ref="shopping_list.household",
            consent={"delivery_consent_granted": True},
            minor_allowed_intent_classes=["calendar"],
        )
    )
    state = await storage.async_load_state()

    active_person_resolution = {
        "active_person_state": "active_person_available",
        "active_person_available": True,
        "resolved_person_id": "person.tom",
        "resolved_voice_profile_id": "voice.tom",
        "reason_code": "attribution_ready",
    }

    runtime_person_context = services_module._build_runtime_person_context(
        state,
        active_person_resolution=active_person_resolution,
    )

    assert runtime_person_context["person_context_state"] == "person_context_resolved"
    assert runtime_person_context["reason_code"] == "person_context_resolved"
    assert runtime_person_context["resolved_concierge_person_profile_id"] == "person.tom_grounds"
    assert runtime_person_context["match_mode"] == "voice_profile_reference"
    assert runtime_person_context["identity"]["resolved_person_id"] == "person.tom"


async def test_runtime_person_context_fails_closed_for_missing_profile(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Missing person profiles should fail closed without inventing routing inputs."""
    state = await ConciergeStorage(hass).async_load_state()

    active_person_resolution = {
        "active_person_state": "active_person_available",
        "active_person_available": True,
        "resolved_person_id": "person.david",
        "resolved_voice_profile_id": "voice.david",
        "reason_code": "attribution_ready",
    }

    runtime_person_context = services_module._build_runtime_person_context(
        state,
        active_person_resolution=active_person_resolution,
    )
    routing = services_module._build_person_aware_productivity_routing(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
    )

    assert runtime_person_context["person_context_state"] == "person_context_unresolved"
    assert runtime_person_context["reason_code"] == "person_profile_not_configured"
    assert runtime_person_context["resolved_concierge_person_profile_id"] is None
    assert runtime_person_context["fail_closed"] is True
    assert routing["routing_enabled"] is False
    assert routing["reason_code"] == "person_profile_not_configured"
    assert routing["refusal_reason"] == "person_profile_not_configured"
    assert routing["refusal_category"] == "configuration_unavailable"
    assert routing["capability_requested"] == "person_aware_productivity_routing"
    assert routing["capability_available"] is False
    assert routing["capability_configured"] is False
    assert routing["person_policy_evaluated"] is True
    assert routing["domain_routing"]["email"]["enabled"] is False
    assert routing["domain_routing"]["calendar"]["enabled"] is False
    assert routing["domain_routing"]["shopping"]["enabled"] is False


async def test_runtime_person_context_reports_partial_states_safely(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Partial person profiles should fail closed with explicit missing-binding reason codes."""
    area = ar.async_get(hass).async_create(name="Bedroom")
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="person.tom",
            name="Tom",
            email_source_ref="sensor.mailbox_tom",
            calendar_source_ref="sensor.calendar_tom",
            shopping_source_ref="shopping_list.household",
            consent={"delivery_consent_granted": True},
            minor_allowed_intent_classes=["calendar"],
        )
    )
    state = await storage.async_load_state()

    active_person_resolution = {
        "active_person_state": "active_person_available",
        "active_person_available": True,
        "resolved_person_id": "person.tom",
        "resolved_voice_profile_id": "voice.tom",
        "reason_code": "attribution_ready",
    }

    runtime_person_context = services_module._build_runtime_person_context(
        state,
        active_person_resolution=active_person_resolution,
    )
    routing = services_module._build_person_aware_productivity_routing(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
    )

    assert runtime_person_context["person_context_state"] == "person_context_partial"
    assert runtime_person_context["reason_code"] == "presence_bindings_missing"
    assert runtime_person_context["presence"]["available"] is False
    assert runtime_person_context["presence"]["location_ref"] is None
    assert runtime_person_context["productivity"]["available"] is True
    assert runtime_person_context["policy"]["available"] is True
    assert routing["routing_enabled"] is False
    assert routing["reason_code"] == "presence_bindings_missing"
    assert routing["refusal_category"] == "configuration_unavailable"
    assert routing["person_policy_evaluated"] is True
    assert routing["domain_routing"]["email"]["enabled"] is False
    assert routing["domain_routing"]["calendar"]["enabled"] is False
    assert routing["domain_routing"]["task"]["enabled"] is False
    assert routing["domain_routing"]["shopping"]["enabled"] is False

    await storage.async_update_person_profile(
        PersonProfile(
            person_id="person.jane",
            name="Jane",
            linked_area_id=area.id,
            ble_device_ids=["ble.jane_tag"],
            aqara_presence_entity_ids=["binary_sensor.jane_presence"],
            mobile_notify_targets=["mobile_app.jane"],
            preferred_mobile_target="mobile_app.jane",
            consent={"delivery_consent_granted": True},
            minor_allowed_intent_classes=["calendar"],
        )
    )
    state = await storage.async_load_state()
    active_person_resolution = {
        "active_person_state": "active_person_available",
        "active_person_available": True,
        "resolved_person_id": "person.jane",
        "resolved_voice_profile_id": "voice.jane",
        "reason_code": "attribution_ready",
    }

    runtime_person_context = services_module._build_runtime_person_context(
        state,
        active_person_resolution=active_person_resolution,
    )
    routing = services_module._build_person_aware_productivity_routing(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
    )

    assert runtime_person_context["person_context_state"] == "person_context_partial"
    assert runtime_person_context["reason_code"] == "productivity_bindings_missing"
    assert runtime_person_context["productivity"]["available"] is False
    assert runtime_person_context["presence"]["available"] is True
    assert routing["routing_enabled"] is False
    assert routing["reason_code"] == "productivity_bindings_missing"
    assert routing["domain_routing"]["email"]["enabled"] is False
    assert routing["domain_routing"]["calendar"]["enabled"] is False
    assert routing["domain_routing"]["task"]["enabled"] is False
    assert routing["domain_routing"]["shopping"]["enabled"] is False

    await storage.async_update_person_profile(
        PersonProfile(
            person_id="person.alex",
            name="Alex",
            linked_area_id=area.id,
            voice_profile_id="voice.alex",
            ble_device_ids=["ble.alex_tag"],
            aqara_presence_entity_ids=["binary_sensor.alex_presence"],
            mobile_notify_targets=["mobile_app.alex"],
            preferred_mobile_target="mobile_app.alex",
            email_source_ref="sensor.mailbox_alex",
            calendar_source_ref="sensor.calendar_alex",
            shopping_source_ref="shopping_list.household",
        )
    )
    state = await storage.async_load_state()
    active_person_resolution = {
        "active_person_state": "active_person_available",
        "active_person_available": True,
        "resolved_person_id": "person.alex",
        "resolved_voice_profile_id": "voice.alex",
        "reason_code": "attribution_ready",
    }

    runtime_person_context = services_module._build_runtime_person_context(
        state,
        active_person_resolution=active_person_resolution,
    )
    routing = services_module._build_person_aware_productivity_routing(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
    )

    assert runtime_person_context["person_context_state"] == "person_context_partial"
    assert runtime_person_context["reason_code"] == "policy_context_missing"
    assert runtime_person_context["policy"]["available"] is False
    assert routing["routing_enabled"] is False
    assert routing["reason_code"] == "policy_context_missing"


async def test_voice_profile_service_persists_enrollment(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Voice profile service should persist voice enrollment state."""
    from custom_components.concierge.storage import ConciergeStorage

    result = await hass.services.async_call(
        DOMAIN,
        "update_voice_profile",
        {
            "voice_profile_id": "tom_voice",
            "name": "Tom Voice",
            "tts_voice": "alloy",
            "enrollment_state": "trained",
            "enrollment_source": "local",
            "speaker_embedding_id": "embedding-1",
            "sample_count": 4,
            "consent": {"voice_training": True},
            "set_as_default": True,
        },
        blocking=True,
        return_response=True,
    )

    state = await ConciergeStorage(hass).async_load_state()
    profile = state.voice_profiles["tom_voice"]
    assert result["voice_profile_count"] == 1
    assert profile.tts_voice == "alloy"
    assert profile.enrollment_state == "trained"
    assert profile.sample_count == 4
    assert state.default_voice_profile is not None
    assert state.default_voice_profile.voice_profile_id == "tom_voice"


async def test_voice_enrollment_lifecycle_services_round_trip(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Voice enrollment lifecycle services should persist deterministic state transitions."""
    from custom_components.concierge.storage import ConciergeStorage

    await hass.services.async_call(
        DOMAIN,
        "update_person_profile",
        {
            "person_id": "tom",
            "name": "Tom Grounds",
        },
        blocking=True,
    )

    started = await hass.services.async_call(
        DOMAIN,
        "start_voice_enrollment",
        {
            "person_id": "tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "consent_acknowledged": True,
            "local_only": True,
        },
        blocking=True,
        return_response=True,
    )
    assert started["started"] is True
    assert started["voice_profile_id"] == "tom_voice"

    first_capture = await hass.services.async_call(
        DOMAIN,
        "capture_voice_enrollment_sample",
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Hello Concierge, test phrase one.",
            "phrase_index": 0,
        },
        blocking=True,
        return_response=True,
    )
    second_capture = await hass.services.async_call(
        DOMAIN,
        "capture_voice_enrollment_sample",
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Hello Concierge, test phrase two.",
            "phrase_index": 1,
        },
        blocking=True,
        return_response=True,
    )
    third_capture = await hass.services.async_call(
        DOMAIN,
        "capture_voice_enrollment_sample",
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Hello Concierge, test phrase three.",
            "phrase_index": 2,
        },
        blocking=True,
        return_response=True,
    )
    assert first_capture["captured"] is True
    assert second_capture["captured"] is True
    assert third_capture["sample_count"] == 3

    removed = await hass.services.async_call(
        DOMAIN,
        "remove_voice_enrollment_sample",
        {
            "voice_profile_id": "tom_voice",
            "sample_id": first_capture["sample_id"],
        },
        blocking=True,
        return_response=True,
    )
    assert removed["removed"] is True
    assert removed["sample_count"] == 2

    built = await hass.services.async_call(
        DOMAIN,
        "build_voice_profile",
        {
            "voice_profile_id": "tom_voice",
            "person_id": "tom",
            "min_samples": 2,
        },
        blocking=True,
        return_response=True,
    )
    assert built["built"] is True
    assert built["sample_count"] == 2
    assert built["person_id"] == "tom"

    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    assert state.voice_profiles["tom_voice"].enrollment_state == "trained"
    assert state.person_profiles["tom"].voice_profile_id == "tom_voice"

    reset = await hass.services.async_call(
        DOMAIN,
        "reset_voice_profile",
        {
            "voice_profile_id": "tom_voice",
            "preserve_consent": True,
        },
        blocking=True,
        return_response=True,
    )
    assert reset["reset"] is True

    reset_state = await storage.async_load_state()
    assert reset_state.voice_profiles["tom_voice"].sample_count == 0
    assert reset_state.voice_profiles["tom_voice"].enrollment_state == "untrained"

    deleted = await hass.services.async_call(
        DOMAIN,
        "delete_voice_profile",
        {
            "voice_profile_id": "tom_voice",
            "unlink_from_people": True,
        },
        blocking=True,
        return_response=True,
    )
    assert deleted["deleted"] is True

    final_state = await storage.async_load_state()
    assert "tom_voice" not in final_state.voice_profiles
    assert final_state.person_profiles["tom"].voice_profile_id is None


async def test_start_voice_enrollment_fails_closed_when_storage_unavailable(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Preflight failure should block session creation before enrollment starts."""
    from custom_components.concierge import services as services_module
    from custom_components.concierge.storage import ConciergeStorage
    import voluptuous as vol

    await hass.services.async_call(
        DOMAIN,
        "update_person_profile",
        {
            "person_id": "tom",
            "name": "Tom Grounds",
        },
        blocking=True,
    )

    async def _fail_preflight(self):
        raise vol.Invalid("external enrollment storage is unavailable: storage_unavailable")

    monkeypatch.setattr(services_module.EnrollmentOrchestrator, "require_storage_preflight", _fail_preflight)

    with pytest.raises(Exception, match="storage_unavailable"):
        await hass.services.async_call(
            DOMAIN,
            "start_voice_enrollment",
            {
                "person_id": "tom",
                "voice_profile_id": "tom_voice",
                "voice_name": "Tom Voice",
                "consent_acknowledged": True,
                "local_only": True,
            },
            blocking=True,
            return_response=True,
        )

    state = await ConciergeStorage(hass).async_load_state()
    assert state.enrollment_sessions == {}


async def test_start_voice_enrollment_delegates_to_orchestrator(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Service layer should delegate enrollment start sequencing to the orchestrator."""
    from custom_components.concierge import services as services_module

    delegated = {}

    async def _fake_start(self, call_data):
        delegated.update(call_data)
        return {
            "started": True,
            "person_id": call_data["person_id"],
            "voice_profile_id": "delegated_voice",
            "enrollment_session_id": "session_delegated",
            "enrollment_state": "ready",
            "sample_count": 0,
            "local_only": True,
        }

    monkeypatch.setattr(services_module.EnrollmentOrchestrator, "start_enrollment", _fake_start)

    result = await hass.services.async_call(
        DOMAIN,
        "start_voice_enrollment",
        {
            "person_id": "tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "consent_acknowledged": True,
            "local_only": True,
        },
        blocking=True,
        return_response=True,
    )

    assert delegated["person_id"] == "tom"
    assert result["voice_profile_id"] == "delegated_voice"


async def test_start_voice_enrollment_satellite_provider_delegates_to_orchestrator(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Start service should delegate satellite provider selection through shared orchestrator start path."""
    from custom_components.concierge import services as services_module

    delegated = {}

    async def _fake_start(self, call_data):
        delegated.update(call_data)
        return {
            "started": True,
            "person_id": call_data["person_id"],
            "voice_profile_id": "satellite_voice",
            "enrollment_session_id": "session_satellite",
            "enrollment_state": "ready",
            "sample_count": 0,
            "local_only": True,
            "capture_provider": "satellite",
        }

    monkeypatch.setattr(services_module.EnrollmentOrchestrator, "start_enrollment", _fake_start)

    result = await hass.services.async_call(
        DOMAIN,
        "start_voice_enrollment",
        {
            "person_id": "tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "capture_provider": "satellite",
            "consent_acknowledged": True,
            "local_only": True,
        },
        blocking=True,
        return_response=True,
    )

    assert delegated["person_id"] == "tom"
    assert delegated["capture_provider"] == "satellite"
    assert result["capture_provider"] == "satellite"


async def test_capture_voice_enrollment_sample_satellite_provider_delegates_to_orchestrator(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Capture service should delegate satellite transport through shared orchestrator capture path."""
    from custom_components.concierge import services as services_module

    delegated = {}

    async def _fake_capture(self, call_data):
        delegated.update(call_data)
        return {
            "provider_type": "satellite",
            "sample_written": True,
            "sample_registered": True,
            "sample_id": "sample_satellite_1",
            "sample_count": 1,
            "failure_code": None,
        }

    monkeypatch.setattr(services_module.EnrollmentOrchestrator, "capture_enrollment_sample", _fake_capture)

    result = await hass.services.async_call(
        DOMAIN,
        "capture_voice_enrollment_sample",
        {
            "voice_profile_id": "tom_voice",
            "capture_provider": "satellite",
            "prompt_text": "Please say phrase one now",
            "speech_text": "phrase one",
        },
        blocking=True,
        return_response=True,
    )

    assert delegated["voice_profile_id"] == "tom_voice"
    assert delegated["prompt_text"] == "Please say phrase one now"
    assert result["sample_registered"] is True


async def test_cancel_voice_enrollment_service_delegates_to_orchestrator(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Cancel service should delegate sequencing to orchestrator."""
    from custom_components.concierge import services as services_module

    delegated = {}

    async def _fake_cancel(self, call_data):
        delegated.update(call_data)
        return {
            "canceled": True,
            "already_terminal": False,
            "not_found": False,
            "person_id": call_data.get("person_id"),
            "voice_profile_id": call_data.get("voice_profile_id"),
            "cleanup_result_code": "complete",
            "session_id": "session_1",
        }

    monkeypatch.setattr(services_module.EnrollmentOrchestrator, "cancel_enrollment", _fake_cancel)

    result = await hass.services.async_call(
        DOMAIN,
        "cancel_voice_enrollment",
        {"person_id": "person.tom", "voice_profile_id": "tom_voice"},
        blocking=True,
        return_response=True,
    )

    assert delegated["person_id"] == "person.tom"
    assert result["canceled"] is True


async def test_recover_voice_enrollment_service_delegates_to_orchestrator(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Recover service should delegate sequencing to orchestrator."""
    from custom_components.concierge import services as services_module

    delegated = {}

    async def _fake_recover(self, call_data):
        delegated.update(call_data)
        return {
            "recoverable": True,
            "recovered": True,
            "not_found": False,
            "person_id": call_data.get("person_id"),
            "voice_profile_id": call_data.get("voice_profile_id"),
            "recovery_state": "resume_available",
            "progress": {
                "sample_count": 1,
                "target_sample_count": 3,
                "completion_percentage": 33,
            },
        }

    monkeypatch.setattr(services_module.EnrollmentOrchestrator, "recover_enrollment", _fake_recover)

    result = await hass.services.async_call(
        DOMAIN,
        "recover_voice_enrollment",
        {"person_id": "person.tom", "voice_profile_id": "tom_voice"},
        blocking=True,
        return_response=True,
    )

    assert delegated["person_id"] == "person.tom"
    assert result["recoverable"] is True


async def test_complete_voice_enrollment_service_delegates_to_orchestrator(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Completion service should delegate deterministic completion sequencing to orchestrator."""
    from custom_components.concierge import services as services_module

    delegated = {}

    async def _fake_complete(self, call_data):
        delegated.update(call_data)
        return {
            "completed": True,
            "voice_profile_id": call_data.get("voice_profile_id"),
            "sample_count": 3,
            "person_id": call_data.get("person_id"),
            "cleanup_result_code": "complete",
            "completion_state": "completed_pending_cleanup",
            "ready_for_recovery": False,
        }

    monkeypatch.setattr(services_module.EnrollmentOrchestrator, "complete_enrollment", _fake_complete)

    result = await hass.services.async_call(
        DOMAIN,
        "complete_voice_enrollment",
        {
            "voice_profile_id": "tom_voice",
            "person_id": "person.tom",
            "min_samples": 3,
        },
        blocking=True,
        return_response=True,
    )

    assert delegated["voice_profile_id"] == "tom_voice"
    assert result["completed"] is True


async def test_completion_readiness_service_delegates_to_orchestrator(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Readiness service should delegate deterministic readiness evaluation to orchestrator."""
    from custom_components.concierge import services as services_module

    delegated = {}

    async def _fake_readiness(self, call_data):
        delegated.update(call_data)
        return {
            "ready": True,
            "reason_code": "ready",
            "voice_profile_id": call_data.get("voice_profile_id"),
            "sample_count": 3,
            "min_samples": int(call_data.get("min_samples", 3)),
            "enrollment_state": "sample_received",
            "user_safe_status_summary": "Enrollment is ready for profile completion.",
        }

    monkeypatch.setattr(services_module.EnrollmentOrchestrator, "get_completion_readiness", _fake_readiness)

    result = await hass.services.async_call(
        DOMAIN,
        "get_voice_enrollment_completion_readiness",
        {
            "voice_profile_id": "tom_voice",
            "min_samples": 3,
        },
        blocking=True,
        return_response=True,
    )

    assert delegated["voice_profile_id"] == "tom_voice"
    assert result["ready"] is True


async def test_sync_rooms_service_reports_success(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Sync rooms service should complete and report room synchronization status."""
    result = await hass.services.async_call(
        DOMAIN,
        "sync_rooms",
        {
            "add_missing": True,
            "remove_missing": False,
        },
        blocking=True,
        return_response=True,
    )

    assert result["synced"] is True
    assert "room_count" in result


async def test_update_composite_config_same_floor_rename_and_dismantle(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Composite service should support same-floor merge, rename, and dismantle."""
    from custom_components.concierge.storage import ConciergeStorage

    floor_registry = fr.async_get(hass)
    main_floor = floor_registry.async_create(name="Main")

    area_registry = ar.async_get(hass)
    kitchen = area_registry.async_create(name="Kitchen", floor_id=main_floor.floor_id)
    dining = area_registry.async_create(name="Dining", floor_id=main_floor.floor_id)
    living = area_registry.async_create(name="Living", floor_id=main_floor.floor_id)

    created = await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "upstairs_public_space",
            "name": "Upstairs Public Space",
            "area_ids": [kitchen.id, dining.id, living.id],
            "primary_area": kitchen.id,
        },
        blocking=True,
        return_response=True,
    )
    assert created["dismantled"] is False
    assert created["area_count"] == 3

    renamed = await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "upstairs_public_space",
            "name": "Main Public Space",
            "area_ids": [kitchen.id, living.id],
            "primary_area": living.id,
        },
        blocking=True,
        return_response=True,
    )
    assert renamed["dismantled"] is False
    assert renamed["area_count"] == 2

    state = await ConciergeStorage(hass).async_load_state()
    composite = state.composites["upstairs_public_space"]
    assert composite.name == "Main Public Space"
    assert composite.area_ids == [kitchen.id, living.id]
    assert composite.primary_area == living.id

    dismantled = await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "upstairs_public_space",
            "area_ids": [],
        },
        blocking=True,
        return_response=True,
    )
    assert dismantled["dismantled"] is True

    post = await ConciergeStorage(hass).async_load_state()
    assert "upstairs_public_space" not in post.composites


async def test_update_composite_config_rejects_cross_floor_membership(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Composite service must reject area lists that span multiple floors."""
    floor_registry = fr.async_get(hass)
    first_floor = floor_registry.async_create(name="First")
    second_floor = floor_registry.async_create(name="Second")

    area_registry = ar.async_get(hass)
    kitchen = area_registry.async_create(name="Kitchen", floor_id=first_floor.floor_id)
    bedroom = area_registry.async_create(name="Bedroom", floor_id=second_floor.floor_id)

    with pytest.raises(Exception, match="same floor"):
        await hass.services.async_call(
            DOMAIN,
            "update_composite_config",
            {
                "composite_id": "invalid_composite",
                "name": "Invalid Composite",
                "area_ids": [kitchen.id, bedroom.id],
            },
            blocking=True,
        )


async def test_sync_composites_removes_invalid_members(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Sync composites should remove missing area members and dismantle empty composites."""
    from custom_components.concierge.storage import ConciergeStorage

    floor_registry = fr.async_get(hass)
    main_floor = floor_registry.async_create(name="Main")
    area_registry = ar.async_get(hass)
    kitchen = area_registry.async_create(name="Kitchen", floor_id=main_floor.floor_id)

    storage = ConciergeStorage(hass)
    await storage.async_update_composite_config(
        composite_id="test_composite",
        name="Test Composite",
        area_ids=[kitchen.id, "missing_area"],
        primary_area=kitchen.id,
    )

    result = await hass.services.async_call(
        DOMAIN,
        "sync_composites",
        {"remove_invalid": True},
        blocking=True,
        return_response=True,
    )
    assert result["synced"] is True
    assert result["validation_errors"]

    state = await storage.async_load_state()
    assert "test_composite" in state.composites
    assert state.composites["test_composite"].area_ids == [kitchen.id]

    # If the only valid area disappears, sync should dismantle the composite.
    area_registry.async_delete(kitchen.id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        "sync_composites",
        {"remove_invalid": True},
        blocking=True,
        return_response=True,
    )
    state_after = await storage.async_load_state()
    assert "test_composite" not in state_after.composites


async def test_update_composite_config_persists_and_prunes_selected_entities(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Composite selections should persist and prune entities from removed member rooms."""
    from custom_components.concierge.storage import ConciergeStorage

    floor_registry = fr.async_get(hass)
    main_floor = floor_registry.async_create(name="Main")

    area_registry = ar.async_get(hass)
    kitchen = area_registry.async_create(name="Kitchen", floor_id=main_floor.floor_id)
    dining = area_registry.async_create(name="Dining", floor_id=main_floor.floor_id)

    entity_registry = er.async_get(hass)
    kitchen_light = entity_registry.async_get_or_create(
        "light",
        DOMAIN,
        "kitchen_light",
        area_id=kitchen.id,
    )
    dining_light = entity_registry.async_get_or_create(
        "light",
        DOMAIN,
        "dining_light",
        area_id=dining.id,
    )

    await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "public_space",
            "name": "Public Space",
            "area_ids": [kitchen.id, dining.id],
            "light_entity_ids": [kitchen_light.entity_id, dining_light.entity_id],
        },
        blocking=True,
    )

    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    assert state.composites["public_space"].light_entity_ids == [
        kitchen_light.entity_id,
        dining_light.entity_id,
    ]

    await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "public_space",
            "area_ids": [kitchen.id],
        },
        blocking=True,
    )

    updated = await storage.async_load_state()
    assert updated.composites["public_space"].light_entity_ids == [kitchen_light.entity_id]


async def test_sync_composites_prunes_stale_selected_entities(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Sync composites should remove selected entities no longer scoped to member areas."""
    from custom_components.concierge.storage import ConciergeStorage

    floor_registry = fr.async_get(hass)
    main_floor = floor_registry.async_create(name="Main")

    area_registry = ar.async_get(hass)
    kitchen = area_registry.async_create(name="Kitchen", floor_id=main_floor.floor_id)
    den = area_registry.async_create(name="Den", floor_id=main_floor.floor_id)

    entity_registry = er.async_get(hass)
    kitchen_light = entity_registry.async_get_or_create(
        "light",
        DOMAIN,
        "sync_kitchen_light",
        area_id=kitchen.id,
    )
    den_light = entity_registry.async_get_or_create(
        "light",
        DOMAIN,
        "sync_den_light",
        area_id=den.id,
    )

    await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "sync_test",
            "name": "Sync Test",
            "area_ids": [kitchen.id, den.id],
            "light_entity_ids": [kitchen_light.entity_id, den_light.entity_id],
        },
        blocking=True,
    )

    area_registry.async_delete(den.id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        "sync_composites",
        {"remove_invalid": True},
        blocking=True,
        return_response=True,
    )

    state = await ConciergeStorage(hass).async_load_state()
    composite = state.composites["sync_test"]
    assert composite.area_ids == [kitchen.id]
    assert composite.light_entity_ids == [kitchen_light.entity_id]


async def test_update_global_context_records_activity_timeline(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Global context mutations should emit backend activity timeline entries."""
    await hass.services.async_call(
        DOMAIN,
        "update_global_context",
        {
            "context_type": "weather",
            "enabled": True,
            "summary": "Sunny",
            "detail": "High of 82",
            "speakable": "Sunny and warm",
        },
        blocking=True,
    )

    timeline = await hass.services.async_call(
        DOMAIN,
        "get_activity_timeline",
        {},
        blocking=True,
        return_response=True,
    )
    activities = timeline.get("activities", [])
    assert any(
        item.get("intent_class") == "update_global_context"
        and item.get("outcome") == "success"
        for item in activities
    )


async def test_execute_records_success_activity(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Composite member-room execution should preserve the configured composite outcome."""
    events: list[dict] = []

    def _listener(event: Event) -> None:
        events.append(dict(event.data))

    unsub = hass.bus.async_listen(EVENT_EXECUTION, _listener)

    floor_registry = fr.async_get(hass)
    main_floor = floor_registry.async_create(name="Main")

    area_registry = ar.async_get(hass)
    kitchen = area_registry.async_create(name="Kitchen", floor_id=main_floor.floor_id)
    dining = area_registry.async_create(name="Dining", floor_id=main_floor.floor_id)

    await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "public_space",
            "name": "Public Space",
            "area_ids": [kitchen.id, dining.id],
            "primary_area": dining.id,
        },
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "update_execution_preferences",
        {
            "scope_id": "public_space",
            "preferences": {"mode": "scene", "target": "scene.public_space"},
        },
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "update_global_context",
        {
            "context_type": "weather",
            "enabled": True,
            "summary": "Clear skies",
            "detail": "Mild evening",
            "speakable": "Clear skies tonight.",
        },
        blocking=True,
    )

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "area_id": kitchen.id,
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    assert result["executed"] is True
    assert result["resolved_target"] == "scene.public_space"
    envelope = result["execution_envelope"]
    assert envelope["execution_kind"] == "orchestration"
    boundary = envelope["capability_projection_boundary"]
    assert boundary["projection_role"] == "governed_projection_consumer"
    assert boundary["projection_is_authority"] is False
    assert boundary["deferred_release_2_owners"]["authoritative_input_consumption"] == "#314"
    assert boundary["deferred_release_2_owners"]["capability_discovery"] == "#317"
    consumption = envelope["authoritative_capability_input_consumption"]
    assert consumption["deterministic_consumption"] is True
    assert consumption["concierge_role"] == "bounded_consumer_orchestrator"
    assert consumption["capability_authority_origin"] == "htbw_governed_contracts_and_models"
    assert consumption["input_origin_owners"]["voice_identity_status"] == "voice_identity"
    assert consumption["deferred_release_2_owners"]["vocabulary_to_capability_handoff"] == "#315"
    assert envelope["planning"]["plan_kind"] == "scene_turn_on"
    assert envelope["routing"]["route_scope"] == "composite"
    assert envelope["routing"]["requested_area_id"] == kitchen.id
    assert envelope["routing"]["context_area_id"] == dining.id
    assert envelope["routing"]["resolved_composite_id"] == "public_space"
    assert envelope["routing"]["execution_preference_scope_id"] == "public_space"
    assert envelope["routing"]["execution_preference_present"] is True
    assert envelope["context"]["summary"] == "Clear skies"
    assert envelope["context"]["context_source_count"] == 1
    assert envelope["execution"]["domain"] == "scene"
    assert envelope["execution"]["service"] == "turn_on"
    discovery = envelope["capability_discovery"]
    assert discovery["applicable"] is True
    assert discovery["route_scope"] == "composite"
    assert discovery["authority_traceability"]["capability_authority_origin"] == "htbw_governed_contracts_and_models"
    assert discovery["deferred_release_2_owners"]["experience_implementation"] == "#319+"
    continuity = envelope["continuity_governance_boundary"]
    assert continuity["applicable"] is True
    assert continuity["continuity_path"] == "governed_continuity_boundary"
    assert continuity["deterministic_boundary"] is True
    assert continuity["continuity_authority_external"] is True
    assert continuity["continuity_owns_identity"] is False
    assert continuity["continuity_owns_occupancy"] is False
    assert continuity["continuity_owns_memory"] is False
    assert continuity["privacy_boundary_preserved"] is True
    assert continuity["orchestration_constraints"]["route_scope"] == "composite"
    assert continuity["orchestration_constraints"]["affinity_behavior_enabled"] is True
    assert continuity["orchestration_constraints"]["diagnostics_behavior_enabled"] is True
    assert continuity["deferred_release_3_owners"]["person_room_affinity_boundary"] == "#326"
    assert continuity["deferred_release_3_owners"]["privacy_household_memory_boundary"] == "#327"
    affinity = envelope["person_room_affinity_boundary"]
    assert affinity["applicable"] is True
    assert affinity["affinity_path"] == "governed_person_room_affinity_boundary"
    assert affinity["deterministic_boundary"] is True
    assert affinity["affinity_authority_external"] is True
    assert affinity["affinity_owns_identity"] is False
    assert affinity["affinity_owns_room_truth"] is False
    assert affinity["affinity_owns_occupancy"] is False
    assert affinity["affinity_owns_memory"] is False
    assert affinity["guest_safe_boundary_preserved"] is True
    assert affinity["privacy_boundary_preserved"] is True
    assert affinity["orchestration_constraints"]["route_scope"] == "composite"
    assert affinity["orchestration_constraints"]["affinity_learning_enabled"] is False
    assert affinity["orchestration_constraints"]["diagnostics_behavior_enabled"] is True
    assert affinity["deferred_release_3_owners"]["privacy_household_memory_boundary"] == "#327"
    assert affinity["deferred_release_3_owners"]["continuity_affinity_diagnostics_explainability"] == "#328"
    memory = envelope["privacy_household_memory_boundary"]
    assert memory["applicable"] is True
    assert memory["boundary_path"] == "governed_privacy_household_memory_boundary"
    assert memory["deterministic_boundary"] is True
    assert memory["privacy_authority_external"] is True
    assert memory["household_memory_authority_external"] is True
    assert memory["memory_owns_identity"] is False
    assert memory["memory_owns_retention_policy"] is False
    assert memory["memory_owns_storage"] is False
    assert memory["memory_owns_provenance"] is False
    assert memory["guest_safe_boundary_preserved"] is True
    assert memory["orchestration_constraints"]["route_scope"] == "composite"
    assert memory["orchestration_constraints"]["household_memory_diagnostics_enabled"] is False
    assert memory["deferred_release_3_owners"]["continuity_affinity_diagnostics_explainability"] == "#328"
    occupancy = envelope["occupancy_governance_boundary"]
    assert occupancy["applicable"] is True
    assert occupancy["occupancy_path"] == "governed_occupancy_boundary"
    assert occupancy["deterministic_boundary"] is True
    assert occupancy["occupancy_authority_external"] is True
    assert occupancy["occupancy_policy_authority_external"] is True
    assert occupancy["occupancy_truth_authority_external"] is True
    assert occupancy["occupancy_owns_room_truth"] is False
    assert occupancy["occupancy_owns_identity"] is False
    assert occupancy["occupancy_owns_household_memory"] is False
    assert occupancy["occupancy_owns_restoration"] is False
    assert occupancy["guest_safe_boundary_preserved"] is True
    assert occupancy["privacy_boundary_preserved"] is True
    assert occupancy["orchestration_constraints"]["route_scope"] == "composite"
    assert occupancy["orchestration_constraints"]["occupancy_boundary_only"] is True
    assert occupancy["orchestration_constraints"]["occupancy_decision_behavior_enabled"] is False
    assert occupancy["orchestration_constraints"]["occupancy_execution_enabled"] is False
    assert occupancy["orchestration_constraints"]["occupancy_inference_enabled"] is False
    assert occupancy["orchestration_constraints"]["occupancy_diagnostics_behavior_enabled"] is False
    assert occupancy["deferred_release_3_owners"]["presence_governance_boundary"] == "#334"
    assert occupancy["deferred_release_3_owners"]["occupancy_presence_diagnostics_explainability"] == "#337"
    presence = envelope["presence_governance_boundary"]
    assert presence["applicable"] is True
    assert presence["presence_path"] == "governed_presence_boundary"
    assert presence["deterministic_boundary"] is True
    assert presence["presence_authority_external"] is True
    assert presence["presence_policy_authority_external"] is True
    assert presence["presence_truth_authority_external"] is True
    assert presence["presence_owns_occupancy"] is False
    assert presence["presence_owns_room_truth"] is False
    assert presence["presence_owns_identity"] is False
    assert presence["presence_owns_household_memory"] is False
    assert presence["presence_owns_restoration"] is False
    assert presence["guest_safe_boundary_preserved"] is True
    assert presence["privacy_boundary_preserved"] is True
    assert presence["consumes_occupancy_governance_visibility"] is True
    assert presence["orchestration_constraints"]["route_scope"] == "composite"
    assert presence["orchestration_constraints"]["presence_boundary_only"] is True
    assert presence["orchestration_constraints"]["presence_detection_enabled"] is False
    assert presence["orchestration_constraints"]["presence_inference_enabled"] is False
    assert presence["orchestration_constraints"]["presence_attribution_enabled"] is False
    assert presence["orchestration_constraints"]["presence_behavior_enabled"] is False
    assert presence["orchestration_constraints"]["presence_diagnostics_behavior_enabled"] is False
    assert presence["deferred_release_3_owners"]["guest_unknown_occupant_behavior"] == "#335"
    assert presence["deferred_release_3_owners"]["occupancy_presence_diagnostics_explainability"] == "#337"
    experience = envelope["experience_governance_boundary"]
    assert experience["applicable"] is True
    assert experience["experience_authority_external"] is True
    assert experience["experience_consumes_capability_outputs"] is True
    assert experience["experience_redefines_capability_outputs"] is False
    assert experience["consumption_boundary_rules"]["consume_capability_outputs_only"] is True
    assert experience["orchestration_constraints"]["route_scope"] == "composite"
    assert experience["orchestration_constraints"]["experience_execution_enabled"] is False
    assert experience["deferred_release_2_owners"]["experience_restoration_boundary"] == "#322"
    assert experience["deferred_release_2_owners"]["experience_diagnostics_explainability"] == "#323"
    handoff = envelope["capability_to_experience_handoff"]
    assert handoff["applicable"] is True
    assert handoff["handoff_path"] == "capability_to_experience_consumption"
    assert handoff["experience_consumption_ready"] is True
    assert handoff["handoff_transfers_authority"] is False
    assert handoff["authority_attribution"]["capability_authority_origin"] == "htbw_governed_contracts_and_models"
    assert handoff["capability_source_traceability"]["route_scope"] == "composite"
    assert handoff["ownership_preservation"]["capability_authority_external"] is True
    assert handoff["deferred_release_2_owners"]["experience_restoration_boundary"] == "#322"
    projection = envelope["experience_projection"]
    assert projection["applicable"] is True
    assert projection["projection_path"] == "experience_projection_from_capability_handoff"
    assert projection["projection_is_authority"] is False
    assert projection["projection_source"]["route_scope"] == "composite"
    assert projection["projected_experience_count"] >= 0
    assert projection["authority_attribution"]["capability_authority_origin"] == "htbw_governed_contracts_and_models"
    assert projection["deferred_release_2_owners"]["experience_diagnostics_explainability"] == "#323"
    restoration = envelope["experience_restoration_boundary"]
    assert restoration["applicable"] is True
    assert restoration["restoration_path"] == "experience_projection_to_restoration_boundary"
    assert restoration["restoration_governance_path"] == "governed_restoration_boundary"
    assert restoration["restoration_authority_transferred"] is False
    assert restoration["restoration_authority_external"] is True
    assert restoration["restoration_policy_authority_external"] is True
    assert restoration["restoration_eligible"] is False
    assert restoration["guest_unknown_behavior_consumed"] is True
    assert restoration["restoration_owns_identity"] is False
    assert restoration["restoration_owns_occupancy"] is False
    assert restoration["restoration_owns_continuity"] is False
    assert restoration["restoration_owns_affinity"] is False
    assert restoration["restoration_owns_household_memory"] is False
    assert restoration["governance_controls"]["route_scope"] == "composite"
    assert restoration["governance_controls"]["restoration_execution_enabled"] is True
    assert restoration["governance_controls"]["restoration_decision_behavior_enabled"] is True
    assert restoration["governance_controls"]["restoration_diagnostics_behavior_enabled"] is True
    assert restoration["governance_controls"]["guest_unknown_behavior_enabled"] is True
    assert restoration["restoration_traceability"]["projection_route_scope"] == "composite"
    assert restoration["ownership_visibility"]["experience_authority_external"] is True
    assert restoration["guardrails"]["validation_in_scope"] is False
    assert restoration["deferred_release_3_owners"]["restoration_outcome_implementation"] == "#330"
    assert restoration["deferred_release_3_owners"]["e3a_preservation_alignment"] == "#331"
    assert restoration["deferred_release_3_owners"]["restoration_diagnostics_explainability"] == "#332"
    assert restoration["deferred_release_2_owners"]["release_2_validation"] == "#324"
    outcome = envelope["experience_restoration_outcome"]
    assert outcome["applicable"] is True
    assert outcome["outcome_path"] == "experience_projection_to_restoration_outcome"
    assert outcome["restoration_applied"] is False
    assert outcome["restoration_execution_handoff_ready"] is False
    assert outcome["restoration_outcome_reason"] == "guest_unknown_occupant_restriction"
    assert outcome["selected_outcome"]["experience_id"].startswith("exp_")
    assert outcome["governance_controls"]["route_scope"] == "composite"
    assert outcome["governance_controls"]["restoration_decision_behavior_enabled"] is True
    assert outcome["governance_controls"]["restoration_execution_enabled"] is True
    assert outcome["governance_controls"]["guest_unknown_behavior_enabled"] is True
    assert outcome["ownership_preservation"]["restoration_decision_authority_transferred"] is False
    preservation_alignment = envelope["e3a_preservation_alignment"]
    assert preservation_alignment["applicable"] is True
    assert preservation_alignment["alignment_path"] == "restoration_outcome_to_e3a_preservation_alignment"
    assert preservation_alignment["preservation_eligible"] is False
    assert preservation_alignment["alignment_reason"] == "restoration_outcome_not_applied"
    assert preservation_alignment["preserved_outcome_clusters"]["execution_hierarchy"] is True
    assert preservation_alignment["governance_controls"]["route_scope"] == "composite"
    assert preservation_alignment["governance_controls"]["alignment_behavior_enabled"] is True
    assert preservation_alignment["governance_controls"]["restoration_decision_behavior_enabled"] is True
    assert preservation_alignment["governance_controls"]["restoration_execution_enabled"] is True
    assert preservation_alignment["ownership_preservation"]["preservation_creates_authority"] is False
    assert preservation_alignment["ownership_preservation"]["preservation_redefines_outcomes"] is False
    assert preservation_alignment["restoration_linkage"]["selected_experience_id"].startswith("exp_")

    await hass.async_block_till_done()
    assert events
    event_envelope = events[-1]["execution_envelope"]
    assert event_envelope["planning"]["resolved_target"] == "scene.public_space"
    assert event_envelope["routing"]["resolved_composite_id"] == "public_space"

    timeline = await hass.services.async_call(
        DOMAIN,
        "get_activity_timeline",
        {"area_id": kitchen.id},
        blocking=True,
        return_response=True,
    )
    activities = timeline.get("activities", [])
    assert any(
        item.get("intent_class") == "execute_orchestration"
        and item.get("outcome") == "success"
        and any(
            ref.get("ref_type") == "preservation_outcome"
            and ref.get("preservation_cluster") == "composite_room_execution"
            and ref.get("resolved_target") == "scene.public_space"
            for ref in item.get("external_refs", [])
        )
        and any(
            ref.get("ref_type") == "preservation_alignment"
            and ref.get("applicable") is True
            and ref.get("preservation_eligible") is False
            and ref.get("restoration_outcome_path") == "experience_projection_to_restoration_outcome"
            for ref in item.get("external_refs", [])
        )
        for item in activities
    )
    unsub()


def test_lighting_stability_threshold_accepts_stable_level() -> None:
    """A state older than the stability threshold is eligible for stable learning capture."""

    class _StateStub:
        def __init__(self) -> None:
            self.state = "on"
            self.attributes = {"brightness": 128}
            self.last_changed = datetime.now(timezone.utc) - timedelta(seconds=45)

    result = services_module._evaluate_entity_stability_for_usual_learning(
        _StateStub(),
        stability_seconds=30,
    )

    assert result["stable"] is True
    assert result["required_seconds"] == 30
    assert result["observed_seconds"] >= 45


def test_lighting_stability_threshold_rejects_unstable_level() -> None:
    """A recent state change should not satisfy learned-usual stability capture."""

    class _StateStub:
        def __init__(self) -> None:
            self.state = "on"
            self.attributes = {"brightness": 191}
            self.last_changed = datetime.now(timezone.utc) - timedelta(seconds=5)

    result = services_module._evaluate_entity_stability_for_usual_learning(
        _StateStub(),
        stability_seconds=30,
    )

    assert result["stable"] is False
    assert result["reason"] == "stable_threshold_not_met"


async def test_execute_turn_on_lights_applies_per_entity_learned_usual_levels(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Turn on lights should learn and apply distinct per-entity usual brightness levels."""
    area = ar.async_get(hass).async_create(name="Living Room")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "light_entity_ids": ["light.living_room_lamp_a", "light.living_room_lamp_b"],
        },
        blocking=True,
    )

    hass.states.async_set("light.living_room_lamp_a", "on", {"brightness": 89})
    hass.states.async_set("light.living_room_lamp_b", "on", {"brightness": 179})

    def _stable(_state_obj, *, stability_seconds: int) -> dict[str, object]:
        return {
            "stable": True,
            "observed_seconds": max(45, stability_seconds),
            "required_seconds": stability_seconds,
            "reason": "stable_threshold_satisfied",
        }

    monkeypatch.setattr(services_module, "_evaluate_entity_stability_for_usual_learning", _stable)

    light_calls: list[dict[str, object]] = []

    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        light_calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "turn on lights",
            "area_id": area.id,
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    outcomes = result["learned_usual_lighting"]["entity_outcomes"]
    by_entity = {item["entity_id"]: item for item in outcomes}

    assert result["resolved_target"] == "usual_lighting:lights"
    assert len(light_calls) == 2
    assert by_entity["light.living_room_lamp_a"]["applied_brightness_pct"] == 35
    assert by_entity["light.living_room_lamp_b"]["applied_brightness_pct"] == 70
    assert by_entity["light.living_room_lamp_a"]["used_learned_level"] is True
    assert by_entity["light.living_room_lamp_b"]["used_learned_level"] is True

    state = await ConciergeStorage(hass).async_load_state()
    stored_a = state.usual_states["usual_lighting::" + area.id + "::light.living_room_lamp_a"]
    stored_b = state.usual_states["usual_lighting::" + area.id + "::light.living_room_lamp_b"]
    assert stored_a.values["brightness_pct"] == 35
    assert stored_b.values["brightness_pct"] == 70


async def test_execute_turn_on_lamps_uses_configured_membership_only(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Turn on lamps should only target configured room lamp membership, never inferred entities."""
    area = ar.async_get(hass).async_create(name="Den")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "lamp_entity_ids": ["light.den_configured_lamp"],
        },
        blocking=True,
    )

    hass.states.async_set("light.den_configured_lamp", "on", {"brightness": 128})
    hass.states.async_set("light.den_unconfigured_lamp", "on", {"brightness": 200})

    def _stable(_state_obj, *, stability_seconds: int) -> dict[str, object]:
        return {
            "stable": True,
            "observed_seconds": max(60, stability_seconds),
            "required_seconds": stability_seconds,
            "reason": "stable_threshold_satisfied",
        }

    monkeypatch.setattr(services_module, "_evaluate_entity_stability_for_usual_learning", _stable)

    light_calls: list[dict[str, object]] = []
    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        light_calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "turn on lamps",
            "area_id": area.id,
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    assert result["resolved_target"] == "usual_lighting:lamps"
    assert [item["entity_id"] for item in light_calls] == ["light.den_configured_lamp"]


async def test_execute_resume_lights_fallback_missing_learned_value(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Resume lights should fall back safely when no learned value exists."""
    area = ar.async_get(hass).async_create(name="Bedroom")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "light_entity_ids": ["light.bedroom_overhead"],
        },
        blocking=True,
    )

    hass.states.async_set("light.bedroom_overhead", "off", {})

    def _unstable(_state_obj, *, stability_seconds: int) -> dict[str, object]:
        return {
            "stable": False,
            "observed_seconds": 1,
            "required_seconds": stability_seconds,
            "reason": "stable_threshold_not_met",
        }

    monkeypatch.setattr(services_module, "_evaluate_entity_stability_for_usual_learning", _unstable)

    light_calls: list[dict[str, object]] = []
    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        light_calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "resume lights",
            "area_id": area.id,
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    outcome = result["learned_usual_lighting"]["entity_outcomes"][0]
    assert light_calls[0]["brightness_pct"] == 50
    assert result["learned_usual_lighting"]["fallback_used"] is True
    assert result["learned_usual_lighting"]["fallback_path"] == "entity_fallback_default"
    assert result["learned_usual_lighting"]["deterministic_default"] == "per_entity_fallback"
    assert outcome["fallback_used"] is True
    assert outcome["fallback_path"] == "entity_fallback_default"
    assert outcome["fallback_reason"] == "learned_value_missing"
    assert outcome["fallback_source"] == "safe_default_brightness"
    assert outcome["deterministic_default"] == "safe_default_brightness"


async def test_execute_usual_lights_fallback_when_learning_denied(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Usual lights should use deterministic fallback when learning policy denies capture."""
    area = ar.async_get(hass).async_create(name="Kitchen")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "light_entity_ids": ["light.kitchen_overhead"],
        },
        blocking=True,
    )
    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    state.global_features["experience_continuity_lighting_learning_policy"] = {
        "enabled": False,
        "options": {"stability_seconds": 30},
    }
    await storage.async_save_state(state)

    hass.states.async_set("light.kitchen_overhead", "on", {"brightness": 153})

    def _stable(_state_obj, *, stability_seconds: int) -> dict[str, object]:
        return {
            "stable": True,
            "observed_seconds": 90,
            "required_seconds": stability_seconds,
            "reason": "stable_threshold_satisfied",
        }

    monkeypatch.setattr(services_module, "_evaluate_entity_stability_for_usual_learning", _stable)

    light_calls: list[dict[str, object]] = []
    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        light_calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "usual lights",
            "area_id": area.id,
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    outcome = result["learned_usual_lighting"]["entity_outcomes"][0]
    assert light_calls[0]["brightness_pct"] == 60
    assert outcome["fallback_used"] is True
    assert outcome["fallback_path"] == "entity_fallback_default"
    assert outcome["fallback_reason"] == "learned_value_denied"
    assert outcome["fallback_source"] == "current_state_brightness"
    assert outcome["deterministic_default"] == "current_state_brightness"


async def test_execute_usual_lights_fallback_unavailable_learned_value(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Unavailable learned payloads should fall back safely and remain explainable."""
    area = ar.async_get(hass).async_create(name="Office")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "light_entity_ids": ["light.office_overhead"],
        },
        blocking=True,
    )

    storage = ConciergeStorage(hass)
    await storage.async_upsert_usual_state(
        UsualState(
            state_id=f"usual_lighting::{area.id}::light.office_overhead",
            scope="entity",
            scope_ref="light.office_overhead",
            basis=UsualStateBasis.LEARNED,
            updated_at=datetime.now(timezone.utc).isoformat(),
            values={"brightness_pct": 0, "area_id": area.id},
            metadata={"policy_name": "test"},
        )
    )
    hass.states.async_set("light.office_overhead", "on", {"brightness": 102})

    def _unstable(_state_obj, *, stability_seconds: int) -> dict[str, object]:
        return {
            "stable": False,
            "observed_seconds": 2,
            "required_seconds": stability_seconds,
            "reason": "stable_threshold_not_met",
        }

    monkeypatch.setattr(services_module, "_evaluate_entity_stability_for_usual_learning", _unstable)

    light_calls: list[dict[str, object]] = []
    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        light_calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "usual lights",
            "area_id": area.id,
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    outcome = result["learned_usual_lighting"]["entity_outcomes"][0]
    assert light_calls[0]["brightness_pct"] == 40
    assert outcome["fallback_reason"] == "learned_value_unavailable"
    assert outcome["fallback_source"] == "current_state_brightness"
    assert outcome["deterministic_default"] == "current_state_brightness"


async def test_execute_resume_lights_applies_learned_value_when_available(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Resume lights should apply persisted learned usual values when present."""
    area = ar.async_get(hass).async_create(name="Media Room")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "light_entity_ids": ["light.media_room_main"],
        },
        blocking=True,
    )

    storage = ConciergeStorage(hass)
    await storage.async_upsert_usual_state(
        UsualState(
            state_id=f"usual_lighting::{area.id}::light.media_room_main",
            scope="entity",
            scope_ref="light.media_room_main",
            basis=UsualStateBasis.LEARNED,
            updated_at=datetime.now(timezone.utc).isoformat(),
            values={"brightness_pct": 72, "area_id": area.id},
            metadata={"policy_name": "experience_continuity_learned_lighting_ec_c_01"},
        )
    )
    hass.states.async_set("light.media_room_main", "on", {"brightness": 50})

    def _unstable(_state_obj, *, stability_seconds: int) -> dict[str, object]:
        return {
            "stable": False,
            "observed_seconds": 2,
            "required_seconds": stability_seconds,
            "reason": "stable_threshold_not_met",
        }

    monkeypatch.setattr(services_module, "_evaluate_entity_stability_for_usual_learning", _unstable)

    calls: list[dict[str, object]] = []
    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "resume lights", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    outcome = result["learned_usual_lighting"]["entity_outcomes"][0]
    assert calls[0]["brightness_pct"] == 72
    assert outcome["used_learned_level"] is True
    assert outcome["fallback_used"] is False


async def test_execute_usual_lights_applies_learned_value_when_available(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Usual lights should apply persisted learned usual values when present."""
    area = ar.async_get(hass).async_create(name="Library")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "light_entity_ids": ["light.library_main"],
        },
        blocking=True,
    )

    storage = ConciergeStorage(hass)
    await storage.async_upsert_usual_state(
        UsualState(
            state_id=f"usual_lighting::{area.id}::light.library_main",
            scope="entity",
            scope_ref="light.library_main",
            basis=UsualStateBasis.LEARNED,
            updated_at=datetime.now(timezone.utc).isoformat(),
            values={"brightness_pct": 61, "area_id": area.id},
            metadata={"policy_name": "experience_continuity_learned_lighting_ec_c_01"},
        )
    )
    hass.states.async_set("light.library_main", "on", {"brightness": 200})

    def _unstable(_state_obj, *, stability_seconds: int) -> dict[str, object]:
        return {
            "stable": False,
            "observed_seconds": 2,
            "required_seconds": stability_seconds,
            "reason": "stable_threshold_not_met",
        }

    monkeypatch.setattr(services_module, "_evaluate_entity_stability_for_usual_learning", _unstable)

    calls: list[dict[str, object]] = []
    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "usual lights", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    outcome = result["learned_usual_lighting"]["entity_outcomes"][0]
    assert calls[0]["brightness_pct"] == 61
    assert outcome["used_learned_level"] is True
    assert outcome["fallback_used"] is False


async def test_execute_room_aware_lighting_records_decision_reason_for_fallback(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Degraded room-aware failures should emit deterministic decision reason metadata."""
    area = ar.async_get(hass).async_create(name="Hall")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
        },
        blocking=True,
    )

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "turn on lights", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    learned = result["learned_usual_lighting"]
    assert learned["fallback_used"] is True
    assert learned["deterministic_default"] == "safe_noop"
    assert learned["decision_reason"] == "configured_room_authority_validation"


async def test_usual_state_and_operational_snapshot_remain_separate(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Usual-state lighting memory should remain distinct from operational snapshot records."""
    storage = ConciergeStorage(hass)
    area_id = "area.test_room"
    entity_id = "light.test_room_lamp"

    await storage.async_upsert_usual_state(
        UsualState(
            state_id=f"usual_lighting::{area_id}::{entity_id}",
            scope="entity",
            scope_ref=entity_id,
            basis=UsualStateBasis.LEARNED,
            updated_at=datetime.now(timezone.utc).isoformat(),
            values={"brightness_pct": 65, "area_id": area_id},
            metadata={"policy_name": "experience_continuity_learned_lighting_ec_c_01"},
        )
    )
    await storage.async_upsert_experience_snapshot(
        ExperienceSnapshot(
            snapshot_id=f"opsnap::{entity_id}",
            scope="entity",
            scope_ref=entity_id,
            captured_at=datetime.now(timezone.utc).isoformat(),
            event_id="evt-op-1",
            state={"brightness_pct": 15},
            metadata={"snapshot_kind": "operational"},
        )
    )

    state = await storage.async_load_state()
    usual = state.usual_states[f"usual_lighting::{area_id}::{entity_id}"]
    snapshot = state.experience_snapshots[f"opsnap::{entity_id}"]

    assert usual.values["brightness_pct"] == 65
    assert snapshot.state["brightness_pct"] == 15


async def test_execute_room_alias_vocabulary_routes_to_room_aware_lighting(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Room-configured alias vocabulary should route to room-aware configured lighting capability."""
    area = ar.async_get(hass).async_create(name="Family Room")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "aliases": {"ambient lights": "turn on lights"},
            "light_entity_ids": ["light.family_room_main"],
        },
        blocking=True,
    )

    hass.states.async_set("light.family_room_main", "on", {"brightness": 166})

    def _stable(_state_obj, *, stability_seconds: int) -> dict[str, object]:
        return {
            "stable": True,
            "observed_seconds": max(60, stability_seconds),
            "required_seconds": stability_seconds,
            "reason": "stable_threshold_satisfied",
        }

    monkeypatch.setattr(services_module, "_evaluate_entity_stability_for_usual_learning", _stable)

    calls: list[dict[str, object]] = []
    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "ambient lights",
            "area_id": area.id,
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    assert result["executed"] is True
    assert result["resolved_target"] == "usual_lighting:lights"
    learned = result["learned_usual_lighting"]
    assert learned["command_kind"] == "lights"
    assert learned["room_source"] == "room_configuration"
    assert learned["capability_source"] == "configured_room_capability_mapping"
    assert learned["membership_source"] == "room_configuration_membership"
    assert learned["targeted_entities"] == ["light.family_room_main"]
    assert [item["entity_id"] for item in calls] == ["light.family_room_main"]


async def test_execute_room_aware_lighting_capability_mapping_controls_targeting(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Configured capability membership should deterministically select lamp vs light targets."""
    area = ar.async_get(hass).async_create(name="Kitchen")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "lamp_entity_ids": ["light.kitchen_lamp"],
            "light_entity_ids": ["light.kitchen_ceiling"],
        },
        blocking=True,
    )

    hass.states.async_set("light.kitchen_lamp", "on", {"brightness": 140})
    hass.states.async_set("light.kitchen_ceiling", "on", {"brightness": 191})

    def _stable(_state_obj, *, stability_seconds: int) -> dict[str, object]:
        return {
            "stable": True,
            "observed_seconds": max(60, stability_seconds),
            "required_seconds": stability_seconds,
            "reason": "stable_threshold_satisfied",
        }

    monkeypatch.setattr(services_module, "_evaluate_entity_stability_for_usual_learning", _stable)

    calls: list[dict[str, object]] = []
    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    lamps_result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "turn on lamps", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )
    lights_result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "turn on lights", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    assert lamps_result["learned_usual_lighting"]["targeted_entities"] == ["light.kitchen_lamp"]
    assert lights_result["learned_usual_lighting"]["targeted_entities"] == ["light.kitchen_ceiling"]
    assert lamps_result["execution_outcome_category"] == "SILENCE_SUCCESS"
    assert lamps_result["silence_as_success"] is True
    assert lamps_result["response_required"] is False
    assert lamps_result["response_generated"] is False
    assert lights_result["execution_outcome_category"] == "SILENCE_SUCCESS"
    assert lights_result["silence_as_success"] is True
    assert [item["entity_id"] for item in calls] == ["light.kitchen_lamp", "light.kitchen_ceiling"]


async def test_execute_room_aware_lighting_fails_when_capability_mapping_missing(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """When room capability mapping is missing, execution should fail safely without discovery fallback."""
    area = ar.async_get(hass).async_create(name="Entry")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "light_entity_ids": ["light.entry_overhead"],
        },
        blocking=True,
    )
    hass.states.async_set("light.entry_overhead", "on", {"brightness": 140})
    hass.states.async_set("light.entry_unconfigured", "on", {"brightness": 191})

    calls: list[dict[str, object]] = []
    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "turn on lamps", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    assert result["executed"] is False
    assert result["execution_outcome_category"] == "REFUSAL_SUCCESS"
    assert result["silence_as_success"] is False
    assert result["response_required"] is True
    assert result["response_generated"] is True
    assert result["refusal_reason"] == "configured_capability_mapping_missing"
    assert result["refusal_category"] == "capability_unavailable"
    learned = result["learned_usual_lighting"]
    assert learned["failure_reason"] == "configured_capability_mapping_missing"
    assert learned["failure_condition"] == "configured_capability_mapping_missing"
    assert learned["fallback_used"] is True
    assert learned["fallback_path"] == "degraded_safe_failure"
    assert learned["deterministic_default"] == "safe_noop"
    assert learned["targeted_entities"] == []
    assert calls == []


async def test_execute_room_aware_lighting_fails_for_unavailable_configured_device(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Unavailable configured entities should fail safely with explainable denial reason."""
    area = ar.async_get(hass).async_create(name="Den")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "light_entity_ids": ["light.den_overhead"],
        },
        blocking=True,
    )
    hass.states.async_set("light.den_overhead", "unavailable", {})

    calls: list[dict[str, object]] = []
    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "turn on lights", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    assert result["executed"] is False
    learned = result["learned_usual_lighting"]
    assert learned["failure_reason"] == "configured_device_unavailable"
    assert learned["failure_condition"] == "configured_device_unavailable"
    assert learned["deterministic_default"] == "safe_noop"
    assert any(item["reason"] == "configured_device_unavailable" for item in learned["validation_results"])
    assert calls == []


async def test_execute_room_aware_lighting_fails_for_invalid_configured_entity(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Invalid configured entity identifiers should fail safely without targeting unrelated entities."""
    area = ar.async_get(hass).async_create(name="Office")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "light_entity_ids": ["switch.office_lamp"],
        },
        blocking=True,
    )

    calls: list[dict[str, object]] = []
    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "turn on lights", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    assert result["executed"] is False
    learned = result["learned_usual_lighting"]
    assert learned["failure_reason"] == "configured_entity_invalid"
    assert learned["failure_condition"] == "configured_entity_invalid"
    assert learned["deterministic_default"] == "safe_noop"
    assert any(item["reason"] == "configured_entity_invalid" for item in learned["validation_results"])
    assert calls == []


async def test_execute_room_aware_lighting_excludes_unrelated_devices(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Configured membership should exclude unrelated devices even when they exist and are available."""
    area = ar.async_get(hass).async_create(name="Studio")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "light_entity_ids": ["light.studio_main"],
        },
        blocking=True,
    )

    hass.states.async_set("light.studio_main", "on", {"brightness": 128})
    hass.states.async_set("light.unrelated_room", "on", {"brightness": 200})

    def _stable(_state_obj, *, stability_seconds: int) -> dict[str, object]:
        return {
            "stable": True,
            "observed_seconds": max(45, stability_seconds),
            "required_seconds": stability_seconds,
            "reason": "stable_threshold_satisfied",
        }

    monkeypatch.setattr(services_module, "_evaluate_entity_stability_for_usual_learning", _stable)

    calls: list[dict[str, object]] = []
    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "turn on lights", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    assert result["executed"] is True
    assert [item["entity_id"] for item in calls] == ["light.studio_main"]
    assert result["learned_usual_lighting"]["targeted_entities"] == ["light.studio_main"]


async def test_execute_room_aware_lighting_does_not_infer_runtime_replacement_membership(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """When room mapping is empty, runtime entity presence should not be used as replacement membership."""
    area = ar.async_get(hass).async_create(name="Hall")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
        },
        blocking=True,
    )
    hass.states.async_set("light.hall_runtime_discovered", "on", {"brightness": 153})

    calls: list[dict[str, object]] = []
    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "turn on lights", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    assert result["executed"] is False
    learned = result["learned_usual_lighting"]
    assert learned["failure_reason"] == "configured_capability_mapping_missing"
    assert learned["fallback_path"] == "degraded_safe_failure"
    assert learned["targeted_entities"] == []
    assert calls == []


async def test_execute_room_aware_lighting_fails_when_room_configuration_missing(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Room-aware commands should fail safely when room configuration does not exist."""
    area = ar.async_get(hass).async_create(name="Unconfigured Room")

    calls: list[dict[str, object]] = []
    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "turn on lights", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    learned = result["learned_usual_lighting"]
    assert result["executed"] is False
    assert learned["failure_reason"] == "room_configuration_missing"
    assert learned["failure_condition"] == "room_configuration_missing"
    assert learned["fallback_used"] is True
    assert learned["fallback_path"] == "degraded_safe_failure"
    assert learned["deterministic_default"] == "safe_noop"
    assert calls == []


async def test_execute_room_aware_lighting_fails_for_unsupported_device_capability(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Configured entities without brightness support should fail safely with deterministic no-op."""
    area = ar.async_get(hass).async_create(name="Porch")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "light_entity_ids": ["light.porch_binary"],
        },
        blocking=True,
    )
    hass.states.async_set("light.porch_binary", "on", {"supported_color_modes": ["onoff"]})

    calls: list[dict[str, object]] = []
    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "turn on lights", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    learned = result["learned_usual_lighting"]
    assert result["executed"] is False
    assert learned["failure_reason"] == "unsupported_device_capability"
    assert learned["failure_condition"] == "unsupported_device_capability"
    assert learned["deterministic_default"] == "safe_noop"
    assert any(item["reason"] == "unsupported_device_capability" for item in learned["validation_results"])
    assert calls == []


async def test_execute_room_aware_lighting_fails_when_command_not_supported_by_configured_capability(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Lighting command should fail safely when configured room capability does not support command type."""
    area = ar.async_get(hass).async_create(name="Entry")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "light_entity_ids": ["light.entry_overhead"],
        },
        blocking=True,
    )
    hass.states.async_set("light.entry_overhead", "on", {"brightness": 140})

    calls: list[dict[str, object]] = []
    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "turn on lamps", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    learned = result["learned_usual_lighting"]
    assert result["executed"] is False
    assert learned["failure_reason"] == "lighting_command_not_supported_by_configured_room_capability"
    assert learned["fallback_path"] == "degraded_safe_failure"
    assert learned["deterministic_default"] == "safe_command_rejection"
    assert calls == []


async def test_execute_room_aware_lighting_fails_when_lighting_command_kind_not_supported(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Unsupported room-aware lighting command kinds should be rejected deterministically."""
    area = ar.async_get(hass).async_create(name="Kitchen")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "light_entity_ids": ["light.kitchen_ceiling"],
        },
        blocking=True,
    )

    monkeypatch.setattr(
        services_module,
        "_classify_usual_lighting_command",
        lambda _target: "color_temperature_restore",
    )

    calls: list[dict[str, object]] = []
    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "turn on lights", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    learned = result["learned_usual_lighting"]
    assert result["executed"] is False
    assert learned["failure_reason"] == "lighting_command_not_supported"
    assert learned["deterministic_default"] == "safe_command_rejection"
    assert calls == []


async def test_execute_room_aware_lighting_fails_when_no_eligible_targets(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """No eligible targets after validation should produce deterministic no-op failure."""
    area = ar.async_get(hass).async_create(name="Loft")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "light_entity_ids": ["switch.invalid_member", "light.missing_member"],
        },
        blocking=True,
    )

    calls: list[dict[str, object]] = []
    if hass.services.has_service("light", "turn_on"):
        hass.services.async_remove("light", "turn_on")

    async def _turn_on(call):
        calls.append(dict(call.data))

    hass.services.async_register("light", "turn_on", _turn_on)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "turn on lights", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    learned = result["learned_usual_lighting"]
    assert result["executed"] is False
    assert learned["failure_reason"] == "no_eligible_lighting_targets"
    assert learned["deterministic_default"] == "safe_noop"
    assert calls == []


async def test_room_audio_capture_learns_stable_music_duck_and_tts_channels(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Stable room speaker volume should be learned independently for music, duck, and TTS channels."""
    area = ar.async_get(hass).async_create(name="Media Room")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "media_player_entity_ids": ["media_player.media_room_main"],
        },
        blocking=True,
    )
    hass.states.async_set("media_player.media_room_main", "playing", {"volume_level": 0.41})

    monkeypatch.setattr(
        services_module,
        "_evaluate_entity_stability_for_room_audio_learning",
        lambda _state_obj, *, stability_seconds: {
            "stable": True,
            "observed_seconds": stability_seconds + 60,
            "required_seconds": stability_seconds,
            "reason": "stable_threshold_satisfied",
        },
    )

    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    room = state.rooms[area.id]
    speakers = services_module._resolve_room_audio_speaker_membership(room)

    music = await services_module._async_capture_room_audio_channel(
        hass,
        storage=storage,
        state=state,
        area_id=area.id,
        channel="music",
        configured_speakers=speakers,
    )
    hass.states.async_set("media_player.media_room_main", "playing", {"volume_level": 0.33})
    duck = await services_module._async_capture_room_audio_channel(
        hass,
        storage=storage,
        state=state,
        area_id=area.id,
        channel="duck",
        configured_speakers=speakers,
    )
    hass.states.async_set("media_player.media_room_main", "playing", {"volume_level": 0.55})
    tts = await services_module._async_capture_room_audio_channel(
        hass,
        storage=storage,
        state=state,
        area_id=area.id,
        channel="tts",
        configured_speakers=speakers,
    )

    assert music["learning_status"] == "learned"
    assert duck["learning_status"] == "learned"
    assert tts["learning_status"] == "learned"

    refreshed = await storage.async_load_state()
    music_level, _, _ = services_module._resolve_room_audio_level(state=refreshed, area_id=area.id, channel="music")
    duck_level, _, _ = services_module._resolve_room_audio_level(state=refreshed, area_id=area.id, channel="duck")
    tts_level, _, _ = services_module._resolve_room_audio_level(state=refreshed, area_id=area.id, channel="tts")
    assert music_level == 41
    assert duck_level == 33
    assert tts_level == 55


async def test_room_audio_capture_rejects_unstable_and_preserves_previous_value_when_denied(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Unstable or denied learning should preserve prior room-audio memory value."""
    area = ar.async_get(hass).async_create(name="Kitchen")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "media_player_entity_ids": ["media_player.kitchen_sonos"],
        },
        blocking=True,
    )
    hass.states.async_set("media_player.kitchen_sonos", "playing", {"volume_level": 0.62})

    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    room = state.rooms[area.id]
    speakers = services_module._resolve_room_audio_speaker_membership(room)

    monkeypatch.setattr(
        services_module,
        "_evaluate_entity_stability_for_room_audio_learning",
        lambda _state_obj, *, stability_seconds: {
            "stable": True,
            "observed_seconds": stability_seconds + 30,
            "required_seconds": stability_seconds,
            "reason": "stable_threshold_satisfied",
        },
    )

    first = await services_module._async_capture_room_audio_channel(
        hass,
        storage=storage,
        state=state,
        area_id=area.id,
        channel="music",
        configured_speakers=speakers,
    )
    assert first["learning_status"] == "learned"

    state.global_features["experience_continuity_room_audio_learning_policy"] = {
        "enabled": False,
        "options": {"stability_seconds": 30},
    }
    hass.states.async_set("media_player.kitchen_sonos", "playing", {"volume_level": 0.2})

    denied = await services_module._async_capture_room_audio_channel(
        hass,
        storage=storage,
        state=state,
        area_id=area.id,
        channel="music",
        configured_speakers=speakers,
    )
    assert denied["learning_status"] == "denied_previous_preserved"
    assert denied["denial_reason"] == "learning_policy_disabled"

    refreshed = await storage.async_load_state()
    level, _, _ = services_module._resolve_room_audio_level(state=refreshed, area_id=area.id, channel="music")
    assert level == 62


async def test_execute_play_music_uses_configured_room_speakers_and_learned_room_music_volume(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Playback start should target configured room speakers and reuse learned room music volume."""
    _enable_music_assistant_provider(hass, monkeypatch)
    area = ar.async_get(hass).async_create(name="Den")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "media_player_entity_ids": ["media_player.den_main", "media_player.den_side"],
        },
        blocking=True,
    )

    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    state.usual_states[services_module._room_audio_state_id(area_id=area.id, channel="music")] = UsualState(
        state_id=services_module._room_audio_state_id(area_id=area.id, channel="music"),
        scope="room",
        scope_ref=area.id,
        basis=UsualStateBasis.LEARNED,
        updated_at=datetime.now(timezone.utc).isoformat(),
        values={"channel": "music", "volume_pct": 47, "area_id": area.id},
        metadata={"policy_name": "experience_continuity_room_audio_memory_ec_d_01"},
    )
    await storage.async_save_state(state)

    hass.states.async_set("media_player.den_main", "playing", {"volume_level": 0.1})
    hass.states.async_set("media_player.den_side", "playing", {"volume_level": 0.1})
    hass.states.async_set("media_player.unrelated", "playing", {"volume_level": 0.9})

    calls: list[dict[str, object]] = []
    ma_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")

    async def _volume_set(call):
        calls.append(dict(call.data))

    hass.services.async_register("media_player", "volume_set", _volume_set)
    _register_music_assistant_play_media(hass, ma_calls)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "play music", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    audio = result["room_audio_continuity"]
    assert result["execution_outcome_category"] == "SILENCE_SUCCESS"
    assert result["silence_as_success"] is True
    assert result["response_required"] is False
    assert result["response_generated"] is False
    assert result["executed"] is True
    assert audio["channel"] == "music"
    assert audio["playback_scope"] == "room"
    assert audio["memory_scope"] == "room"
    assert audio["group_targeted_speakers"] == ["media_player.den_main", "media_player.den_side"]
    provider = result["media_provider_resolution"]
    assert provider["provider_selected"] == "music_assistant"
    assert provider["provider_available"] is True
    assert provider["music_assistant_request"]["data"]["media_id"] == "music"
    room_result = audio["room_results"][0]
    assert room_result["resolved_volume_pct"] == 47
    assert room_result["resolved_source"] == "room_audio_usual_state"
    assert sorted(item["entity_id"] for item in calls) == ["media_player.den_main", "media_player.den_side"]
    assert all(abs(float(item["volume_level"]) - 0.47) < 0.0001 for item in calls)
    assert ma_calls and ma_calls[0]["media_id"] == "music"


async def test_execute_play_music_missing_room_volume_uses_safe_fallback(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Missing room music memory should use deterministic safe room-audio fallback volume."""
    _enable_music_assistant_provider(hass, monkeypatch)
    area = ar.async_get(hass).async_create(name="Office")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "media_player_entity_ids": ["media_player.office_main"],
        },
        blocking=True,
    )
    hass.states.async_set("media_player.office_main", "playing", {})

    calls: list[dict[str, object]] = []
    ma_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")

    async def _volume_set(call):
        calls.append(dict(call.data))

    hass.services.async_register("media_player", "volume_set", _volume_set)
    _register_music_assistant_play_media(hass, ma_calls)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "play music", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    audio = result["room_audio_continuity"]
    assert result["executed"] is True
    room_result = audio["room_results"][0]
    assert room_result["resolved_source"] == "safe_default_volume"
    assert room_result["fallback_reason"] == "room_audio_value_missing"
    assert abs(float(calls[0]["volume_level"]) - 0.35) < 0.0001
    assert ma_calls and ma_calls[0]["media_id"] == "music"


async def test_execute_play_music_merged_room_targets_group_and_preserves_per_room_memory(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Merged-room playback should target all constituent configured speakers while preserving per-room memory."""
    _enable_music_assistant_provider(hass, monkeypatch)
    floor = fr.async_get(hass).async_create(name="Main")
    area_registry = ar.async_get(hass)
    room_a = area_registry.async_create(name="Living Room", floor_id=floor.floor_id)
    room_b = area_registry.async_create(name="Kitchen", floor_id=floor.floor_id)

    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {"area_id": room_a.id, "media_player_entity_ids": ["media_player.living_main"]},
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {"area_id": room_b.id, "media_player_entity_ids": ["media_player.kitchen_main"]},
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "public_space",
            "name": "Public Space",
            "area_ids": [room_a.id, room_b.id],
        },
        blocking=True,
    )

    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    state.usual_states[services_module._room_audio_state_id(area_id=room_a.id, channel="music")] = UsualState(
        state_id=services_module._room_audio_state_id(area_id=room_a.id, channel="music"),
        scope="room",
        scope_ref=room_a.id,
        basis=UsualStateBasis.LEARNED,
        updated_at=datetime.now(timezone.utc).isoformat(),
        values={"channel": "music", "volume_pct": 30, "area_id": room_a.id},
        metadata={"policy_name": "experience_continuity_room_audio_memory_ec_d_01"},
    )
    state.usual_states[services_module._room_audio_state_id(area_id=room_b.id, channel="music")] = UsualState(
        state_id=services_module._room_audio_state_id(area_id=room_b.id, channel="music"),
        scope="room",
        scope_ref=room_b.id,
        basis=UsualStateBasis.LEARNED,
        updated_at=datetime.now(timezone.utc).isoformat(),
        values={"channel": "music", "volume_pct": 60, "area_id": room_b.id},
        metadata={"policy_name": "experience_continuity_room_audio_memory_ec_d_01"},
    )
    state.usual_states[services_module._room_audio_state_id(area_id=room_a.id, channel="duck")] = UsualState(
        state_id=services_module._room_audio_state_id(area_id=room_a.id, channel="duck"),
        scope="room",
        scope_ref=room_a.id,
        basis=UsualStateBasis.LEARNED,
        updated_at=datetime.now(timezone.utc).isoformat(),
        values={"channel": "duck", "volume_pct": 18, "area_id": room_a.id},
        metadata={"policy_name": "experience_continuity_room_audio_memory_ec_d_01"},
    )
    state.usual_states[services_module._room_audio_state_id(area_id=room_b.id, channel="duck")] = UsualState(
        state_id=services_module._room_audio_state_id(area_id=room_b.id, channel="duck"),
        scope="room",
        scope_ref=room_b.id,
        basis=UsualStateBasis.LEARNED,
        updated_at=datetime.now(timezone.utc).isoformat(),
        values={"channel": "duck", "volume_pct": 22, "area_id": room_b.id},
        metadata={"policy_name": "experience_continuity_room_audio_memory_ec_d_01"},
    )
    state.usual_states[services_module._room_audio_state_id(area_id=room_a.id, channel="tts")] = UsualState(
        state_id=services_module._room_audio_state_id(area_id=room_a.id, channel="tts"),
        scope="room",
        scope_ref=room_a.id,
        basis=UsualStateBasis.LEARNED,
        updated_at=datetime.now(timezone.utc).isoformat(),
        values={"channel": "tts", "volume_pct": 45, "area_id": room_a.id},
        metadata={"policy_name": "experience_continuity_room_audio_memory_ec_d_01"},
    )
    state.usual_states[services_module._room_audio_state_id(area_id=room_b.id, channel="tts")] = UsualState(
        state_id=services_module._room_audio_state_id(area_id=room_b.id, channel="tts"),
        scope="room",
        scope_ref=room_b.id,
        basis=UsualStateBasis.LEARNED,
        updated_at=datetime.now(timezone.utc).isoformat(),
        values={"channel": "tts", "volume_pct": 52, "area_id": room_b.id},
        metadata={"policy_name": "experience_continuity_room_audio_memory_ec_d_01"},
    )
    await storage.async_save_state(state)

    hass.states.async_set("media_player.living_main", "playing", {"volume_level": 0.1})
    hass.states.async_set("media_player.kitchen_main", "playing", {"volume_level": 0.1})

    calls: list[dict[str, object]] = []
    ma_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")

    async def _volume_set(call):
        calls.append(dict(call.data))

    hass.services.async_register("media_player", "volume_set", _volume_set)
    _register_music_assistant_play_media(hass, ma_calls)

    merged = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "play music",
            "area_id": room_a.id,
            "composite_id": "public_space",
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    audio = merged["room_audio_continuity"]
    provider = merged["media_provider_resolution"]
    assert merged["executed"] is True
    assert audio["playback_scope"] == "merged_room"
    assert audio["merged_room_participation"] is True
    assert sorted(audio["group_targeted_speakers"]) == ["media_player.kitchen_main", "media_player.living_main"]
    assert provider["provider_selected"] == "music_assistant"
    assert provider["merged_room_participation"] is True
    assert sorted(provider["music_assistant_request"]["target"]["entity_id"]) == ["media_player.kitchen_main", "media_player.living_main"]
    assert sorted(item["area_id"] for item in audio["room_results"]) == sorted([room_a.id, room_b.id])

    by_entity = {str(item["entity_id"]): float(item["volume_level"]) for item in calls}
    assert abs(by_entity["media_player.living_main"] - 0.30) < 0.0001
    assert abs(by_entity["media_player.kitchen_main"] - 0.60) < 0.0001

    post_merged = await storage.async_load_state()
    a_music, _, _ = services_module._resolve_room_audio_level(state=post_merged, area_id=room_a.id, channel="music")
    b_music, _, _ = services_module._resolve_room_audio_level(state=post_merged, area_id=room_b.id, channel="music")
    a_duck, _, _ = services_module._resolve_room_audio_level(state=post_merged, area_id=room_a.id, channel="duck")
    b_duck, _, _ = services_module._resolve_room_audio_level(state=post_merged, area_id=room_b.id, channel="duck")
    a_tts, _, _ = services_module._resolve_room_audio_level(state=post_merged, area_id=room_a.id, channel="tts")
    b_tts, _, _ = services_module._resolve_room_audio_level(state=post_merged, area_id=room_b.id, channel="tts")
    assert (a_music, b_music) == (30, 60)
    assert (a_duck, b_duck) == (18, 22)
    assert (a_tts, b_tts) == (45, 52)
    assert all("public_space" not in key for key in post_merged.usual_states)
    assert ma_calls and ma_calls[0]["media_id"] == "music"

    calls.clear()
    single_room = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "play music", "area_id": room_a.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )
    assert single_room["executed"] is True
    assert calls and abs(float(calls[0]["volume_level"]) - 0.30) < 0.0001


async def test_execute_play_music_does_not_discover_replacement_speakers(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Room audio playback must not discover replacement speakers when room configuration has none."""
    _enable_music_assistant_provider(hass, monkeypatch)
    area = ar.async_get(hass).async_create(name="Guest Room")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "media_player_entity_ids": [],
            "speaker_entity_ids": [],
        },
        blocking=True,
    )
    entity = er.async_get(hass).async_get_or_create(
        "media_player",
        DOMAIN,
        "guest_room_unconfigured",
        area_id=area.id,
    )
    hass.states.async_set(entity.entity_id, "playing", {"volume_level": 0.75})

    calls: list[dict[str, object]] = []
    ma_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")

    async def _volume_set(call):
        calls.append(dict(call.data))

    hass.services.async_register("media_player", "volume_set", _volume_set)
    _register_music_assistant_play_media(hass, ma_calls)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "play music", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    media = result["media_provider_resolution"]
    assert result["executed"] is False
    assert media["failure_reason"] == "configured_speaker_mapping_missing"
    assert media["group_targeted_speakers"] == []
    assert calls == []
    assert ma_calls == []


@pytest.mark.parametrize(
    (
        "context_kwargs",
        "runtime_context",
        "expected_strategy",
        "expected_media_id",
        "expected_media_type",
        "expected_radio_mode",
        "expected_personalization",
    ),
    [
        (
            {
                "provider_media_id": "track-001",
                "media_type": "track",
                "track_title": "Song A",
                "artist_name": "Artist A",
                "album_name": "Album A",
                "genre": "jazz",
            },
            {},
            "same_song",
            "track-001",
            None,
            False,
            False,
        ),
        (
            {
                "provider_media_id": "album-001",
                "media_type": "album",
                "album_name": "Album B",
                "artist_name": "Artist B",
                "genre": "classical",
            },
            {},
            "same_album",
            "album-001",
            "album",
            False,
            False,
        ),
        (
            {
                "provider_media_id": "artist-001",
                "media_type": "artist",
                "artist_name": "Artist C",
                "genre": "rock",
            },
            {},
            "same_artist",
            "artist-001",
            "artist",
            False,
            False,
        ),
        (
            {
                "media_type": "genre",
                "genre": "jazz",
            },
            {
                "identity_context": {
                    "state": "known",
                    "confidence_band": "high",
                    "source": "voice_identity",
                },
                "media_preference_inputs": {"preferred_artist": "Miles Davis"},
                "room_default_media_query": "room-default",
                "household_default_media_query": "house-default",
                "system_safe_media_query": "safe-music",
            },
            "same_genre",
            "Miles Davis",
            "artist",
            False,
            True,
        ),
    ],
)
async def test_execute_room_media_continue_resume_uses_room_context_and_music_assistant(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
    context_kwargs: dict[str, object],
    runtime_context: dict[str, object],
    expected_strategy: str,
    expected_media_id: str,
    expected_media_type: str | None,
    expected_radio_mode: bool,
    expected_personalization: bool,
) -> None:
    """Continue/resume should resolve from room media context before falling back to person assistance or room defaults."""
    _enable_music_assistant_provider(hass, monkeypatch)
    area = ar.async_get(hass).async_create(name="Listening Room")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "media_player_entity_ids": ["media_player.listening_main"],
        },
        blocking=True,
    )
    hass.states.async_set("media_player.listening_main", "playing", {"volume_level": 0.4})

    storage = ConciergeStorage(hass)
    await _seed_room_media_context(storage, area_id=area.id, **context_kwargs)

    ma_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")

    async def _volume_set(_call):
        return None

    hass.services.async_register("media_player", "volume_set", _volume_set)
    _register_music_assistant_play_media(hass, ma_calls)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "continue music",
            "area_id": area.id,
            "intent_class": "home_control",
            "context": runtime_context,
        },
        blocking=True,
        return_response=True,
    )

    continuity = result["room_media_continuity"]
    provider = result["media_provider_resolution"]
    assert result["executed"] is True
    assert continuity["continuation_strategy"] == expected_strategy
    assert continuity["source_room_id"] == area.id
    assert continuity["follow_me_excluded"] is True
    assert provider["provider_selected"] == "music_assistant"
    assert provider["provider_available"] is True
    assert provider["music_assistant_request"]["data"]["media_id"] == expected_media_id
    if expected_media_type is None:
        assert "media_type" not in provider["music_assistant_request"]["data"]
    else:
        assert provider["music_assistant_request"]["data"]["media_type"] == expected_media_type
    assert bool(provider["music_assistant_request"]["data"].get("radio_mode", False)) is expected_radio_mode
    assert continuity["personalization_applied"] is expected_personalization
    assert ma_calls and ma_calls[0]["media_id"] == expected_media_id

    refreshed = await storage.async_load_state()
    state_id = services_module._room_media_state_id(area_id=area.id)
    assert state_id in refreshed.usual_states
    context_state = refreshed.usual_states[state_id]
    assert context_state.values["provider_source"] == "music_assistant"
    if expected_strategy == "same_genre":
        assert context_state.values["last_genre"] == "jazz"


@pytest.mark.parametrize(
    ("enable_provider", "expected_reason"),
    [
        (False, "media_provider_disabled"),
        (True, "music_assistant_unavailable"),
    ],
)
async def test_execute_room_media_continue_resume_refuses_when_music_assistant_is_disabled_or_unavailable(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
    enable_provider: bool,
    expected_reason: str,
) -> None:
    """Continue/resume should fail closed when the preferred Music Assistant provider is not usable."""
    if enable_provider:
        _enable_music_assistant_provider(hass, monkeypatch)
    area = ar.async_get(hass).async_create(name="Listening Room")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "media_player_entity_ids": ["media_player.listening_main"],
        },
        blocking=True,
    )
    hass.states.async_set("media_player.listening_main", "playing", {"volume_level": 0.4})

    storage = ConciergeStorage(hass)
    await _seed_room_media_context(
        storage,
        area_id=area.id,
        provider_media_id="track-001",
        media_type="track",
        track_title="Song A",
        genre="jazz",
    )

    ma_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")

    async def _volume_set(_call):
        return None

    hass.services.async_register("media_player", "volume_set", _volume_set)
    if enable_provider:
        _register_music_assistant_play_media(hass, ma_calls)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "resume music",
            "area_id": area.id,
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    provider = result["media_provider_resolution"]
    continuity = result.get("room_media_continuity", {})
    assert result["executed"] is False
    assert result["execution_outcome_category"] == "REFUSAL_SUCCESS"
    assert result["silence_as_success"] is False
    assert result["response_required"] is True
    assert result["response_generated"] is True
    assert provider["failure_reason"] == expected_reason
    assert provider["refusal_reason"] == expected_reason
    assert provider["refusal_category"] in {
        "configuration_unavailable",
        "capability_unavailable",
    }
    assert provider["capability_requested"] == "room_media_continuation"
    assert provider["capability_available"] is False
    assert provider["person_policy_evaluated"] is True
    assert provider["fallback_used"] is True
    assert provider["fallback_path"] == "governed_provider_refusal"
    assert continuity.get("fallback_used") is True
    assert ma_calls == []


async def test_execute_room_media_continue_resume_respects_manual_stop_cooldown(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Manual-stop cooldown should suppress automatic continuation even when room media context exists."""
    _enable_music_assistant_provider(hass, monkeypatch)
    area = ar.async_get(hass).async_create(name="Listening Room")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "media_player_entity_ids": ["media_player.listening_main"],
        },
        blocking=True,
    )
    hass.states.async_set("media_player.listening_main", "paused", {"volume_level": 0.4})

    storage = ConciergeStorage(hass)
    future_until = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    await _seed_room_media_context(
        storage,
        area_id=area.id,
        provider_media_id="track-001",
        media_type="track",
        track_title="Song A",
        genre="jazz",
        manual_stop=True,
        manual_stop_cooldown_until=future_until,
    )

    ma_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")

    async def _volume_set(_call):
        return None

    hass.services.async_register("media_player", "volume_set", _volume_set)
    _register_music_assistant_play_media(hass, ma_calls)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "continue music",
            "area_id": area.id,
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    provider = result["media_provider_resolution"]
    continuity = result["room_media_continuity"]
    assert result["executed"] is False
    assert provider["failure_reason"] == "manual_stop_cooldown_active"
    assert provider["refusal_reason"] == "manual_stop_cooldown_active"
    assert provider["refusal_category"] == "policy_denied"
    assert continuity["refusal_reason"] == "manual_stop_cooldown_active"
    assert continuity["refusal_category"] == "policy_denied"
    assert provider["fallback_used"] is True
    assert continuity["cooldown_decision"]["manual_stop_cooldown_active"] is True
    assert ma_calls == []


async def test_execute_room_media_continue_resume_allows_after_manual_stop_cooldown_expires(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Expired manual-stop cooldown should allow governed continuation to proceed."""
    _enable_music_assistant_provider(hass, monkeypatch)
    area = ar.async_get(hass).async_create(name="Listening Room")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "media_player_entity_ids": ["media_player.listening_main"],
        },
        blocking=True,
    )
    hass.states.async_set("media_player.listening_main", "paused", {"volume_level": 0.4})

    storage = ConciergeStorage(hass)
    past_until = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    await _seed_room_media_context(
        storage,
        area_id=area.id,
        provider_media_id="track-002",
        media_type="track",
        track_title="Song B",
        genre="jazz",
        manual_stop=True,
        manual_stop_cooldown_until=past_until,
    )

    ma_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")

    async def _volume_set(_call):
        return None

    hass.services.async_register("media_player", "volume_set", _volume_set)
    _register_music_assistant_play_media(hass, ma_calls)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "continue music",
            "area_id": area.id,
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    provider = result["media_provider_resolution"]
    continuity = result["room_media_continuity"]
    assert result["executed"] is True
    assert provider["failure_reason"] is None
    assert continuity["cooldown_decision"]["manual_stop_cooldown_active"] is False
    assert ma_calls and ma_calls[0]["media_id"] == "track-002"


async def test_execute_room_media_continue_resume_uses_deterministic_source_room_in_merged_room(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Merged-room continuation should select a deterministic source room and preserve constituent-room memory."""
    _enable_music_assistant_provider(hass, monkeypatch)
    floor = fr.async_get(hass).async_create(name="Main")
    area_registry = ar.async_get(hass)
    room_a = area_registry.async_create(name="Living Room", floor_id=floor.floor_id)
    room_b = area_registry.async_create(name="Kitchen", floor_id=floor.floor_id)

    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {"area_id": room_a.id, "media_player_entity_ids": ["media_player.living_main"]},
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {"area_id": room_b.id, "media_player_entity_ids": ["media_player.kitchen_main"]},
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "public_space",
            "name": "Public Space",
            "area_ids": [room_a.id, room_b.id],
            "primary_area": room_a.id,
        },
        blocking=True,
    )

    storage = ConciergeStorage(hass)
    await _seed_room_media_context(
        storage,
        area_id=room_a.id,
        provider_media_id="track-a",
        media_type="track",
        track_title="Song A",
        artist_name="Artist A",
        genre="jazz",
    )
    await _seed_room_media_context(
        storage,
        area_id=room_b.id,
        provider_media_id="track-b",
        media_type="track",
        track_title="Song B",
        artist_name="Artist B",
        genre="classical",
    )

    ma_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")

    async def _volume_set(_call):
        return None

    hass.services.async_register("media_player", "volume_set", _volume_set)
    _register_music_assistant_play_media(hass, ma_calls)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "continue music",
            "area_id": room_b.id,
            "composite_id": "public_space",
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    continuity = result["room_media_continuity"]
    provider = result["media_provider_resolution"]
    assert result["executed"] is True
    assert continuity["source_room_id"] == room_a.id
    assert continuity["source_room_selection_reason"] == "primary_room_selected"
    assert provider["group_targeted_speakers"] == ["media_player.living_main", "media_player.kitchen_main"]
    assert provider["merged_room_participation"] is True
    assert provider["follow_me_excluded"] is True
    assert ma_calls and ma_calls[0]["media_id"] == "track-a"

    refreshed = await storage.async_load_state()
    assert services_module._room_media_state_id(area_id=room_a.id) in refreshed.usual_states
    assert services_module._room_media_state_id(area_id=room_b.id) in refreshed.usual_states
    assert refreshed.usual_states[services_module._room_media_state_id(area_id=room_a.id)].values["last_song"] == "Song A"
    assert refreshed.usual_states[services_module._room_media_state_id(area_id=room_b.id)].values["last_song"] == "Song B"


async def test_execute_room_media_continue_resume_uses_room_default_fallback_when_context_is_missing(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Missing room media context should fall back to governed room defaults rather than a global media history."""
    _enable_music_assistant_provider(hass, monkeypatch)
    area = ar.async_get(hass).async_create(name="Fallback Room")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "media_player_entity_ids": ["media_player.fallback_main"],
        },
        blocking=True,
    )
    hass.states.async_set("media_player.fallback_main", "playing", {"volume_level": 0.4})

    ma_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")

    async def _volume_set(_call):
        return None

    hass.services.async_register("media_player", "volume_set", _volume_set)
    _register_music_assistant_play_media(hass, ma_calls)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "continue music",
            "area_id": area.id,
            "intent_class": "home_control",
            "context": {
                "room_default_media_query": "room-default",
                "household_default_media_query": "house-default",
                "system_safe_media_query": "safe-music",
            },
        },
        blocking=True,
        return_response=True,
    )

    continuity = result["room_media_continuity"]
    provider = result["media_provider_resolution"]
    assert result["executed"] is True
    assert continuity["continuation_strategy"] == "governed_fallback"
    assert provider["music_assistant_request"]["data"]["media_id"] == "room-default"
    assert "media_type" not in provider["music_assistant_request"]["data"]
    assert continuity["personalization_applied"] is False
    assert ma_calls and ma_calls[0]["media_id"] == "room-default"


async def test_execute_follow_me_handoff_moves_media_to_destination_room(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Follow-Me should hand off playback from source room context to destination room speakers."""
    _enable_music_assistant_provider(hass, monkeypatch)
    floor = fr.async_get(hass).async_create(name="Main")
    area_registry = ar.async_get(hass)
    room_a = area_registry.async_create(name="Living Room", floor_id=floor.floor_id)
    room_b = area_registry.async_create(name="Kitchen", floor_id=floor.floor_id)

    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {"area_id": room_a.id, "media_player_entity_ids": ["media_player.living_main"]},
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {"area_id": room_b.id, "media_player_entity_ids": ["media_player.kitchen_main"]},
        blocking=True,
    )

    hass.states.async_set("media_player.living_main", "playing", {"volume_level": 0.52})
    hass.states.async_set("media_player.kitchen_main", "paused", {"volume_level": 0.31})

    storage = ConciergeStorage(hass)
    await _seed_room_media_context(
        storage,
        area_id=room_a.id,
        provider_media_id="track-living",
        media_type="track",
        track_title="Song A",
        artist_name="Artist A",
        album_name="Album A",
        genre="jazz",
    )

    ma_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")

    async def _volume_set(_call):
        return None

    hass.services.async_register("media_player", "volume_set", _volume_set)
    _register_music_assistant_play_media(hass, ma_calls)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "follow me music",
            "area_id": room_b.id,
            "intent_class": "home_control",
            "context": {
                "follow_me_enabled": True,
                "identity_context": {
                    "state": "known",
                    "confidence_band": "high",
                    "source": "voice_identity",
                },
                "room_transition": {
                    "source_room_id": room_a.id,
                    "destination_room_id": room_b.id,
                    "departure_confirmed": True,
                    "arrival_confirmed": True,
                    "source": "presence_runtime",
                },
            },
        },
        blocking=True,
        return_response=True,
    )

    continuity = result["room_media_continuity"]
    provider = result["media_provider_resolution"]
    assert result["executed"] is True
    assert continuity["follow_me_enabled"] is True
    assert continuity["follow_me_candidate"] is True
    assert continuity["follow_me_allowed"] is True
    assert continuity["follow_me_decision"] == "handoff_execute"
    assert continuity["follow_me_reason"] == "handoff_allowed"
    assert continuity["source_room"] == room_a.id
    assert continuity["destination_room"] == room_b.id
    assert continuity["room_transition_source"] == "presence_runtime"
    assert continuity["identity_authority_source"] == "voice_identity_runtime_context"
    assert continuity["manual_stop_blocked"] is False
    assert continuity["cooldown_blocked"] is False
    assert provider["follow_me_excluded"] is False
    assert provider["group_targeted_speakers"] == ["media_player.kitchen_main"]
    assert ma_calls and ma_calls[0]["media_id"] == "track-living"


async def test_execute_follow_me_handoff_preserves_preference_continuity_for_genre(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Follow-Me should preserve person-scoped preferences when source context is genre-based."""
    _enable_music_assistant_provider(hass, monkeypatch)
    area_registry = ar.async_get(hass)
    room_a = area_registry.async_create(name="Den")
    room_b = area_registry.async_create(name="Office")

    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {"area_id": room_a.id, "media_player_entity_ids": ["media_player.den_main"]},
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {"area_id": room_b.id, "media_player_entity_ids": ["media_player.office_main"]},
        blocking=True,
    )
    hass.states.async_set("media_player.den_main", "playing", {"volume_level": 0.41})
    hass.states.async_set("media_player.office_main", "playing", {"volume_level": 0.38})

    storage = ConciergeStorage(hass)
    await _seed_room_media_context(
        storage,
        area_id=room_a.id,
        provider_media_id="genre-seed",
        media_type="genre",
        genre="jazz",
    )

    ma_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")

    async def _volume_set(_call):
        return None

    hass.services.async_register("media_player", "volume_set", _volume_set)
    _register_music_assistant_play_media(hass, ma_calls)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "move music here",
            "area_id": room_b.id,
            "intent_class": "home_control",
            "context": {
                "follow_me_enabled": True,
                "identity_context": {
                    "state": "known",
                    "confidence_band": "high",
                    "source": "voice_identity",
                },
                "media_preference_inputs": {"preferred_artist": "Miles Davis"},
                "room_default_media_query": "room-default",
                "household_default_media_query": "house-default",
                "system_safe_media_query": "safe-music",
                "room_transition": {
                    "source_room_id": room_a.id,
                    "destination_room_id": room_b.id,
                    "source": "presence_runtime",
                },
            },
        },
        blocking=True,
        return_response=True,
    )

    continuity = result["room_media_continuity"]
    assert result["executed"] is True
    assert continuity["continuation_strategy"] == "same_genre"
    assert continuity["personalization_applied"] is True
    assert ma_calls and ma_calls[0]["media_id"] == "Miles Davis"
    assert ma_calls[0]["media_type"] == "artist"


async def test_execute_follow_me_blocks_when_identity_unresolved(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Follow-Me should fail closed when identity authority is unresolved."""
    _enable_music_assistant_provider(hass, monkeypatch)
    area_registry = ar.async_get(hass)
    room_a = area_registry.async_create(name="Living")
    room_b = area_registry.async_create(name="Kitchen")

    await hass.services.async_call(DOMAIN, "update_room_config", {"area_id": room_a.id, "media_player_entity_ids": ["media_player.living_main"]}, blocking=True)
    await hass.services.async_call(DOMAIN, "update_room_config", {"area_id": room_b.id, "media_player_entity_ids": ["media_player.kitchen_main"]}, blocking=True)
    hass.states.async_set("media_player.living_main", "playing", {"volume_level": 0.4})
    hass.states.async_set("media_player.kitchen_main", "playing", {"volume_level": 0.4})

    storage = ConciergeStorage(hass)
    await _seed_room_media_context(storage, area_id=room_a.id, provider_media_id="track-1", media_type="track", track_title="Song A")
    _register_music_assistant_play_media(hass, [])

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "follow me",
            "area_id": room_b.id,
            "intent_class": "home_control",
            "context": {
                "follow_me_enabled": True,
                "identity_context": {"state": "unknown", "confidence_band": "unknown", "source": "voice_identity"},
                "room_transition": {"source_room_id": room_a.id, "destination_room_id": room_b.id, "source": "presence_runtime"},
            },
        },
        blocking=True,
        return_response=True,
    )

    continuity = result["room_media_continuity"]
    assert result["executed"] is False
    assert continuity["follow_me_allowed"] is False
    assert continuity["follow_me_reason"] == "identity_authority_insufficient"
    assert result["media_provider_resolution"]["failure_reason"] == "identity_authority_insufficient"


async def test_execute_follow_me_blocks_for_competing_identity_sources(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Follow-Me should not hand off when competing identity sources are present."""
    _enable_music_assistant_provider(hass, monkeypatch)
    area_registry = ar.async_get(hass)
    room_a = area_registry.async_create(name="Family")
    room_b = area_registry.async_create(name="Hall")

    await hass.services.async_call(DOMAIN, "update_room_config", {"area_id": room_a.id, "media_player_entity_ids": ["media_player.family_main"]}, blocking=True)
    await hass.services.async_call(DOMAIN, "update_room_config", {"area_id": room_b.id, "media_player_entity_ids": ["media_player.hall_main"]}, blocking=True)
    hass.states.async_set("media_player.family_main", "playing", {"volume_level": 0.4})
    hass.states.async_set("media_player.hall_main", "playing", {"volume_level": 0.4})

    storage = ConciergeStorage(hass)
    await _seed_room_media_context(storage, area_id=room_a.id, provider_media_id="track-2", media_type="track", track_title="Song B")

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "follow me music",
            "area_id": room_b.id,
            "intent_class": "home_control",
            "context": {
                "follow_me_enabled": True,
                "identity_context": {
                    "state": "known",
                    "confidence_band": "high",
                    "source": "voice_identity",
                    "candidate_person_ids": ["person.a", "person.b"],
                },
                "room_transition": {"source_room_id": room_a.id, "destination_room_id": room_b.id, "source": "presence_runtime"},
            },
        },
        blocking=True,
        return_response=True,
    )

    assert result["executed"] is False
    assert result["room_media_continuity"]["follow_me_reason"] == "competing_identity_sources"


async def test_execute_follow_me_blocks_manual_stop_and_cooldown(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Follow-Me should respect manual-stop and cooldown guardrails."""
    _enable_music_assistant_provider(hass, monkeypatch)
    area_registry = ar.async_get(hass)
    room_a = area_registry.async_create(name="Source")
    room_b = area_registry.async_create(name="Destination")

    await hass.services.async_call(DOMAIN, "update_room_config", {"area_id": room_a.id, "media_player_entity_ids": ["media_player.source_main"]}, blocking=True)
    await hass.services.async_call(DOMAIN, "update_room_config", {"area_id": room_b.id, "media_player_entity_ids": ["media_player.dest_main"]}, blocking=True)
    hass.states.async_set("media_player.source_main", "playing", {"volume_level": 0.4})
    hass.states.async_set("media_player.dest_main", "playing", {"volume_level": 0.4})

    storage = ConciergeStorage(hass)
    future_until = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    await _seed_room_media_context(
        storage,
        area_id=room_a.id,
        provider_media_id="track-3",
        media_type="track",
        track_title="Song C",
        manual_stop=True,
        manual_stop_cooldown_until=future_until,
    )

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "follow me",
            "area_id": room_b.id,
            "intent_class": "home_control",
            "context": {
                "follow_me_enabled": True,
                "identity_context": {"state": "known", "confidence_band": "high", "source": "voice_identity"},
                "room_transition": {"source_room_id": room_a.id, "destination_room_id": room_b.id, "source": "presence_runtime"},
            },
        },
        blocking=True,
        return_response=True,
    )

    continuity = result["room_media_continuity"]
    assert result["executed"] is False
    assert continuity["manual_stop_blocked"] is True
    assert continuity["cooldown_blocked"] is True
    assert continuity["follow_me_reason"] == "manual_stop_active_follow_me"


async def test_execute_follow_me_blocks_when_disabled_or_destination_unavailable(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Follow-Me should fail when disabled and also when destination room cannot serve playback."""
    _enable_music_assistant_provider(hass, monkeypatch)
    area_registry = ar.async_get(hass)
    room_a = area_registry.async_create(name="A")
    room_b = area_registry.async_create(name="B")

    await hass.services.async_call(DOMAIN, "update_room_config", {"area_id": room_a.id, "media_player_entity_ids": ["media_player.a_main"]}, blocking=True)
    await hass.services.async_call(DOMAIN, "update_room_config", {"area_id": room_b.id, "media_player_entity_ids": []}, blocking=True)
    hass.states.async_set("media_player.a_main", "playing", {"volume_level": 0.4})

    storage = ConciergeStorage(hass)
    await _seed_room_media_context(storage, area_id=room_a.id, provider_media_id="track-4", media_type="track", track_title="Song D")

    disabled = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "follow me music",
            "area_id": room_b.id,
            "intent_class": "home_control",
            "context": {
                "follow_me_enabled": False,
                "identity_context": {"state": "known", "confidence_band": "high", "source": "voice_identity"},
                "room_transition": {"source_room_id": room_a.id, "destination_room_id": room_b.id, "source": "presence_runtime"},
            },
        },
        blocking=True,
        return_response=True,
    )
    assert disabled["executed"] is False
    assert disabled["room_media_continuity"]["follow_me_reason"] == "follow_me_disabled"

    unavailable = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "follow me music",
            "area_id": room_b.id,
            "intent_class": "home_control",
            "context": {
                "follow_me_enabled": True,
                "identity_context": {"state": "known", "confidence_band": "high", "source": "voice_identity"},
                "room_transition": {"source_room_id": room_a.id, "destination_room_id": room_b.id, "source": "presence_runtime"},
            },
        },
        blocking=True,
        return_response=True,
    )
    assert unavailable["executed"] is False
    assert unavailable["media_provider_resolution"]["failure_reason"] == "configured_speaker_mapping_missing"


async def test_execute_follow_me_does_not_override_merged_room_mode(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Follow-Me must not override merged-room playback behavior boundaries."""
    _enable_music_assistant_provider(hass, monkeypatch)
    floor = fr.async_get(hass).async_create(name="Main")
    area_registry = ar.async_get(hass)
    room_a = area_registry.async_create(name="Living", floor_id=floor.floor_id)
    room_b = area_registry.async_create(name="Kitchen", floor_id=floor.floor_id)

    await hass.services.async_call(DOMAIN, "update_room_config", {"area_id": room_a.id, "media_player_entity_ids": ["media_player.living_main"]}, blocking=True)
    await hass.services.async_call(DOMAIN, "update_room_config", {"area_id": room_b.id, "media_player_entity_ids": ["media_player.kitchen_main"]}, blocking=True)
    await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "public_space",
            "name": "Public Space",
            "area_ids": [room_a.id, room_b.id],
            "primary_area": room_a.id,
        },
        blocking=True,
    )

    hass.states.async_set("media_player.living_main", "playing", {"volume_level": 0.51})
    hass.states.async_set("media_player.kitchen_main", "playing", {"volume_level": 0.37})

    storage = ConciergeStorage(hass)
    await _seed_room_media_context(storage, area_id=room_a.id, provider_media_id="track-5", media_type="track", track_title="Song E")

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "follow me",
            "area_id": room_b.id,
            "composite_id": "public_space",
            "intent_class": "home_control",
            "context": {
                "follow_me_enabled": True,
                "identity_context": {"state": "known", "confidence_band": "high", "source": "voice_identity"},
                "room_transition": {"source_room_id": room_a.id, "destination_room_id": room_b.id, "source": "presence_runtime"},
            },
        },
        blocking=True,
        return_response=True,
    )

    continuity = result["room_media_continuity"]
    assert result["executed"] is False
    assert continuity["follow_me_reason"] == "merged_room_scope_not_supported"
    assert continuity["follow_me_allowed"] is False


@pytest.mark.parametrize(
    ("target", "runtime_context", "expected_kind", "expected_media_id", "expected_media_type", "expect_radio"),
    [
        ("play jazz", {}, "genre", "jazz", None, True),
        ("play classic rock", {}, "genre", "classic rock", None, True),
        ("play Miles Davis", {"media_request_type": "artist"}, "artist", "Miles Davis", "artist", False),
        ("play Kind of Blue", {"media_request_type": "album"}, "album", "Kind of Blue", "album", False),
        (
            "play music",
            {
                "identity_context": {
                    "state": "known",
                    "confidence_band": "high",
                    "source": "voice_identity",
                },
                "media_preference_inputs": {"music_affinity": "Miles Davis"},
            },
            "general_music",
            "Miles Davis",
            None,
            False,
        ),
    ],
)
async def test_execute_music_assistant_preferred_media_resolution_requests(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
    target: str,
    runtime_context: dict[str, object],
    expected_kind: str,
    expected_media_id: str,
    expected_media_type: str | None,
    expect_radio: bool,
) -> None:
    """Music Assistant should be the preferred provider for governed room-level media requests."""
    _enable_music_assistant_provider(hass, monkeypatch)
    area = ar.async_get(hass).async_create(name="Media Den")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {"area_id": area.id, "media_player_entity_ids": ["media_player.den_main"]},
        blocking=True,
    )
    hass.states.async_set("media_player.den_main", "playing", {"volume_level": 0.4})

    ma_calls: list[dict[str, object]] = []
    volume_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")

    async def _volume_set(call):
        volume_calls.append(dict(call.data))

    hass.services.async_register("media_player", "volume_set", _volume_set)
    _register_music_assistant_play_media(hass, ma_calls)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": target,
            "area_id": area.id,
            "intent_class": "home_control",
            "context": runtime_context,
        },
        blocking=True,
        return_response=True,
    )

    provider = result["media_provider_resolution"]
    assert result["executed"] is True
    assert provider["provider_selected"] == "music_assistant"
    assert provider["provider_available"] is True
    assert provider["request_kind"] == expected_kind
    assert provider["media_query"] == expected_media_id
    assert provider["group_targeted_speakers"] == ["media_player.den_main"]
    assert provider["follow_me_excluded"] is True
    assert provider["persistent_merged_room_media_memory_created"] is False
    assert ma_calls and ma_calls[0]["media_id"] == expected_media_id
    if expected_media_type is None:
        assert "media_type" not in ma_calls[0]
    else:
        assert ma_calls[0]["media_type"] == expected_media_type
    assert bool(ma_calls[0].get("radio_mode", False)) is expect_radio
    assert volume_calls


async def test_execute_music_assistant_disabled_refuses_deterministically(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """When Music Assistant is not enabled in Concierge configuration, provider selection must refuse deterministically."""
    area = ar.async_get(hass).async_create(name="Media Den")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {"area_id": area.id, "media_player_entity_ids": ["media_player.den_main"]},
        blocking=True,
    )

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "play jazz", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    provider = result["media_provider_resolution"]
    assert result["executed"] is False
    assert provider["failure_reason"] == "media_provider_disabled"
    assert provider["refusal_reason"] == "media_provider_disabled"
    assert provider["refusal_category"] == "configuration_unavailable"
    assert provider["fallback_used"] is True
    assert provider["fallback_path"] == "governed_provider_refusal"


async def test_execute_music_assistant_unavailable_refuses_deterministically(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """When Music Assistant is configured but unavailable, playback should refuse deterministically."""
    _enable_music_assistant_provider(hass, monkeypatch)
    area = ar.async_get(hass).async_create(name="Media Den")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {"area_id": area.id, "media_player_entity_ids": ["media_player.den_main"]},
        blocking=True,
    )

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {"target": "play jazz", "area_id": area.id, "intent_class": "home_control"},
        blocking=True,
        return_response=True,
    )

    provider = result["media_provider_resolution"]
    assert result["executed"] is False
    assert provider["failure_reason"] == "music_assistant_unavailable"
    assert provider["refusal_reason"] == "music_assistant_unavailable"
    assert provider["refusal_category"] == "capability_unavailable"
    assert provider["fallback_used"] is True
    assert provider["fallback_path"] == "governed_provider_refusal"


@pytest.mark.parametrize(
    ("identity_state", "confidence_band", "music_affinity", "room_default", "expected_query", "expected_tier", "expected_reason"),
    [
        ("known", "high", "Miles Davis", "room-default", "Miles Davis", "known_person_preference", "known_person_allowed"),
        ("guest", "high", "Miles Davis", "room-default", "room-default", "room_default", "guest_identity_blocked"),
        ("low_confidence", "low", "Miles Davis", "room-default", "room-default", "room_default", "low_confidence_identity_blocked"),
    ],
)
async def test_execute_music_assistant_identity_governs_preference_inputs(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
    identity_state: str,
    confidence_band: str,
    music_affinity: str,
    room_default: str,
    expected_query: str,
    expected_tier: str,
    expected_reason: str,
) -> None:
    """Identity state and confidence must govern whether person preference inputs are used."""
    _enable_music_assistant_provider(hass, monkeypatch)
    area = ar.async_get(hass).async_create(name="Media Den")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {"area_id": area.id, "media_player_entity_ids": ["media_player.den_main"]},
        blocking=True,
    )
    hass.states.async_set("media_player.den_main", "playing", {"volume_level": 0.4})

    ma_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")

    async def _volume_set(_call):
        return None

    hass.services.async_register("media_player", "volume_set", _volume_set)
    _register_music_assistant_play_media(hass, ma_calls)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "play music",
            "area_id": area.id,
            "intent_class": "home_control",
            "context": {
                "identity_context": {
                    "state": identity_state,
                    "confidence_band": confidence_band,
                    "source": "voice_identity",
                },
                "media_preference_inputs": {"music_affinity": music_affinity},
                "room_default_media_query": room_default,
                "household_default_media_query": "house-default",
                "system_safe_media_query": "safe-music",
            },
        },
        blocking=True,
        return_response=True,
    )

    identity_resolution = result["identity_aware_media_resolution"]["preference_resolution"]
    assert result["media_provider_resolution"]["media_query"] == expected_query
    assert identity_resolution["selected_tier"] == expected_tier
    assert identity_resolution["identity_decision"]["reason_code"] == expected_reason
    assert ma_calls and ma_calls[0]["media_id"] == expected_query


async def test_execute_music_assistant_merged_room_targets_group_and_excludes_follow_me(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Merged-room media playback should target configured grouped speakers without introducing Follow-Me behavior."""
    _enable_music_assistant_provider(hass, monkeypatch)
    floor = fr.async_get(hass).async_create(name="Main")
    area_registry = ar.async_get(hass)
    room_a = area_registry.async_create(name="Living Room", floor_id=floor.floor_id)
    room_b = area_registry.async_create(name="Kitchen", floor_id=floor.floor_id)

    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {"area_id": room_a.id, "media_player_entity_ids": ["media_player.living_main"]},
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {"area_id": room_b.id, "media_player_entity_ids": ["media_player.kitchen_main"]},
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "public_space",
            "name": "Public Space",
            "area_ids": [room_a.id, room_b.id],
            "primary_area": room_a.id,
        },
        blocking=True,
    )

    hass.states.async_set("media_player.living_main", "playing", {"volume_level": 0.61})
    hass.states.async_set("media_player.kitchen_main", "paused", {"volume_level": 0.42})

    ma_calls: list[dict[str, object]] = []
    volume_calls: list[dict[str, object]] = []
    if hass.services.has_service("media_player", "volume_set"):
        hass.services.async_remove("media_player", "volume_set")

    async def _volume_set(call):
        volume_calls.append(dict(call.data))

    hass.services.async_register("media_player", "volume_set", _volume_set)
    _register_music_assistant_play_media(hass, ma_calls)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "play jazz",
            "area_id": room_a.id,
            "composite_id": "public_space",
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    provider = result["media_provider_resolution"]
    assert result["executed"] is True
    assert provider["provider_selected"] == "music_assistant"
    assert provider["merged_room_participation"] is True
    assert sorted(provider["group_targeted_speakers"]) == ["media_player.kitchen_main", "media_player.living_main"]
    assert provider["follow_me_excluded"] is True
    assert provider["persistent_merged_room_media_memory_created"] is False
    assert ma_calls and ma_calls[0]["media_id"] == "jazz"
    assert volume_calls


async def test_execute_preserves_room_target_without_composite_override(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Non-composite execution should preserve the requested room outcome without composite override."""
    area = ar.async_get(hass).async_create(name="Bedroom")

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.bedroom",
            "area_id": area.id,
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    assert result["executed"] is True
    assert result["resolved_target"] == "light.bedroom"
    assert result["execution_envelope"]["routing"]["route_scope"] == "room"


async def test_execute_known_occupant_allows_standard_restoration_behavior(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Known-occupant execution should allow standard governed restoration behavior."""
    area = ar.async_get(hass).async_create(name="Den")

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.den",
            "area_id": area.id,
            "person_id": "person.household_member",
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    envelope = result["execution_envelope"]
    guest_unknown = envelope["guest_unknown_occupant_behavior"]
    assert guest_unknown["occupant_state"] == "known_occupant"
    assert guest_unknown["conservative_behavior_required"] is False
    assert guest_unknown["restoration_eligibility_allowed"] is True
    outcome = envelope["experience_restoration_outcome"]
    assert outcome["restoration_applied"] is True
    assert outcome["restoration_outcome_reason"] == "projected_experience_selected"


async def test_execute_multi_occupant_known_group_uses_conflict_aware_behavior(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Multiple known occupants should surface conflict-aware behavior without guest/unknown restriction."""
    area = ar.async_get(hass).async_create(name="Great Room")

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.great_room",
            "area_id": area.id,
            "person_id": "person.household_member",
            "intent_class": "home_control",
            "context": {
                "occupant_count": 2,
                "occupant_states": ["known_occupant", "known_occupant"],
                "person_ids": ["person.household_member", "person.household_member_2"],
            },
        },
        blocking=True,
        return_response=True,
    )

    envelope = result["execution_envelope"]
    multi = envelope["multi_occupant_behavior"]
    assert multi["applicable"] is True
    assert multi["behavior_path"] == "governed_multi_occupant_behavior"
    assert multi["occupant_state"] == "multiple_known_occupants"
    assert multi["multi_occupant_mode_active"] is True
    assert multi["conflict_aware_behavior_required"] is False
    assert multi["restoration_eligibility_allowed"] is True
    assert multi["multi_occupant_visibility"]["occupant_count"] == 2
    assert multi["multi_occupant_visibility"]["person_ids_present"] == 2
    assert multi["governance_controls"]["behavior_enabled"] is True
    assert multi["governance_controls"]["multi_occupant_mode_active"] is True
    assert multi["governance_controls"]["restoration_eligibility_allowed"] is True
    outcome = envelope["experience_restoration_outcome"]
    assert outcome["restoration_applied"] is True
    assert outcome["restoration_outcome_reason"] == "projected_experience_selected"
    assert outcome["governance_controls"]["multi_occupant_behavior_enabled"] is True
    ref = next(
        item
        for item in result["activity_external_refs"]
        if item.get("ref_type") == "execution_envelope"
    )
    assert ref["multi_occupant_behavior_applicable"] is True
    assert ref["multi_occupant_behavior_path"] == "governed_multi_occupant_behavior"
    assert ref["multi_occupant_occupant_state"] == "multiple_known_occupants"
    assert ref["multi_occupant_mode_active"] is True
    assert ref["multi_occupant_restoration_eligibility_allowed"] is True


async def test_execute_multi_occupant_guest_mix_preserves_guest_safety(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Mixed known/guest occupancy should remain guest-safe and restrict restoration."""
    area = ar.async_get(hass).async_create(name="Den")

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.den",
            "area_id": area.id,
            "person_id": "person.household_member",
            "intent_class": "home_control",
            "context": {
                "occupant_count": 2,
                "occupant_states": ["known_occupant", "guest_occupant"],
                "person_ids": ["person.household_member"],
                "guest_safe": True,
            },
        },
        blocking=True,
        return_response=True,
    )

    envelope = result["execution_envelope"]
    multi = envelope["multi_occupant_behavior"]
    guest_unknown = envelope["guest_unknown_occupant_behavior"]
    assert multi["applicable"] is True
    assert multi["occupant_state"] == "known_guest_mix"
    assert multi["multi_occupant_mode_active"] is True
    assert multi["conflict_aware_behavior_required"] is True
    assert multi["restoration_eligibility_allowed"] is False
    assert multi["multi_occupant_visibility"]["occupant_count"] == 2
    assert guest_unknown["occupant_state"] == "guest_occupant"
    assert guest_unknown["guest_safe_mode_active"] is True
    assert guest_unknown["restoration_eligibility_allowed"] is False
    outcome = envelope["experience_restoration_outcome"]
    assert outcome["restoration_applied"] is False
    assert outcome["restoration_outcome_reason"] == "guest_unknown_occupant_restriction"
    ref = next(
        item
        for item in result["activity_external_refs"]
        if item.get("ref_type") == "execution_envelope"
    )
    assert ref["multi_occupant_behavior_applicable"] is True
    assert ref["multi_occupant_occupant_state"] == "known_guest_mix"
    assert ref["multi_occupant_mode_active"] is True
    assert ref["multi_occupant_conflict_aware_behavior_required"] is True


async def test_execute_multi_occupant_guest_mix_without_guest_hint_still_restricts_restoration(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Mixed known/guest occupant state lists should preserve guest-safe restriction without an explicit guest_safe hint."""
    area = ar.async_get(hass).async_create(name="Great Room")

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.great_room",
            "area_id": area.id,
            "person_id": "person.household_member",
            "intent_class": "home_control",
            "context": {
                "occupant_count": 2,
                "occupant_states": ["known_occupant", "guest_occupant"],
                "person_ids": ["person.household_member", "person.household_member_2"],
            },
        },
        blocking=True,
        return_response=True,
    )

    envelope = result["execution_envelope"]
    guest_unknown = envelope["guest_unknown_occupant_behavior"]
    multi = envelope["multi_occupant_behavior"]
    restoration = envelope["experience_restoration_boundary"]
    outcome = envelope["experience_restoration_outcome"]

    assert guest_unknown["occupant_state"] == "guest_occupant"
    assert guest_unknown["guest_safe_mode_active"] is True
    assert guest_unknown["restoration_eligibility_allowed"] is False
    assert multi["occupant_state"] == "known_guest_mix"
    assert multi["guest_safe_mode_preserved"] is True
    assert multi["restoration_eligibility_allowed"] is False
    assert restoration["restoration_eligible"] is False
    assert restoration["restoration_eligibility_visibility"]["restricted_by_guest_unknown_behavior"] is True
    assert outcome["restoration_applied"] is False
    assert outcome["restoration_outcome_reason"] == "guest_unknown_occupant_restriction"


async def test_execute_consumes_room_vocabulary_registry_for_area_resolution(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should consume authoritative room vocabulary entries to resolve room scope."""
    from custom_components.concierge.storage import ConciergeStorage

    area = ar.async_get(hass).async_create(name="Kitchen")
    storage = ConciergeStorage(hass)
    await storage.async_update_global_feature(
        feature_key="room_vocabulary_registry",
        enabled=True,
        options={
            "entries": [
                {
                    "term": "kitchen",
                    "aliases": ["cook space"],
                    "area_id": area.id,
                }
            ]
        },
    )

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "area_id": "cook space",
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    assert result["executed"] is True
    assert result["execution_envelope"]["routing"]["requested_area_id"] == area.id
    resolution = result["room_vocabulary_resolution"]
    assert resolution["matched_term"] == "cook space"
    assert resolution["canonical_term"] == "kitchen"
    assert resolution["area_id"] == area.id
    assert resolution["composite_id"] is None
    handoff = result["execution_envelope"]["vocabulary_to_capability_handoff"]
    assert handoff["deterministic_resolution"] is True
    assert handoff["vocabulary_authority_external"] is True
    assert handoff["room_vocabulary_consumed"] is True
    assert handoff["device_entity_vocabulary_consumed"] is False
    assert handoff["asset_handoff_deferred_owner"] == "#316"


async def test_execute_consumes_room_vocabulary_registry_for_composite_resolution(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should consume authoritative room vocabulary entries to resolve composite scope."""
    from custom_components.concierge.storage import ConciergeStorage

    floor_registry = fr.async_get(hass)
    main_floor = floor_registry.async_create(name="Main")
    area_registry = ar.async_get(hass)
    kitchen = area_registry.async_create(name="Kitchen", floor_id=main_floor.floor_id)
    dining = area_registry.async_create(name="Dining", floor_id=main_floor.floor_id)

    await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "public_space",
            "name": "Public Space",
            "area_ids": [kitchen.id, dining.id],
            "primary_area": dining.id,
        },
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "update_execution_preferences",
        {
            "scope_id": "public_space",
            "preferences": {"mode": "scene", "target": "scene.public_space"},
        },
        blocking=True,
    )

    storage = ConciergeStorage(hass)
    await storage.async_update_global_feature(
        feature_key="room_vocabulary_registry",
        enabled=True,
        options={
            "entries": [
                {
                    "term": "great room",
                    "aliases": ["public space"],
                    "composite_id": "public_space",
                }
            ]
        },
    )

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "area_id": "public space",
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    assert result["executed"] is True
    assert result["resolved_target"] == "scene.public_space"
    envelope = result["execution_envelope"]
    assert envelope["routing"]["route_scope"] == "composite"
    assert envelope["routing"]["resolved_composite_id"] == "public_space"
    assert envelope["routing"]["requested_area_id"] == dining.id
    resolution = result["room_vocabulary_resolution"]
    assert resolution["matched_term"] == "public space"
    assert resolution["canonical_term"] == "great room"
    assert resolution["composite_id"] == "public_space"


async def test_execute_consumes_device_entity_vocabulary_after_room_scope_resolution(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should consume device/entity vocabulary after room vocabulary scope resolution."""
    from custom_components.concierge.storage import ConciergeStorage

    area = ar.async_get(hass).async_create(name="Kitchen")
    storage = ConciergeStorage(hass)
    await storage.async_update_global_feature(
        feature_key="room_vocabulary_registry",
        enabled=True,
        options={
            "entries": [
                {
                    "term": "kitchen",
                    "aliases": ["cook space"],
                    "area_id": area.id,
                }
            ]
        },
    )
    await storage.async_update_global_feature(
        feature_key="device_entity_vocabulary_registry",
        enabled=True,
        options={
            "entries": [
                {
                    "term": "main lights",
                    "aliases": ["ceiling lights"],
                    "entity_id": "light.kitchen_ceiling",
                    "area_id": area.id,
                }
            ]
        },
    )

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "ceiling lights",
            "area_id": "cook space",
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    assert result["executed"] is True
    assert result["resolved_target"] == "light.kitchen_ceiling"
    room_resolution = result["room_vocabulary_resolution"]
    assert room_resolution["canonical_term"] == "kitchen"
    entity_resolution = result["device_entity_vocabulary_resolution"]
    assert entity_resolution["canonical_term"] == "main lights"
    assert entity_resolution["entity_id"] == "light.kitchen_ceiling"
    assert entity_resolution["area_id"] == area.id
    assert entity_resolution["composite_id"] is None
    handoff = result["execution_envelope"]["vocabulary_to_capability_handoff"]
    assert handoff["room_vocabulary_consumed"] is True
    assert handoff["device_entity_vocabulary_consumed"] is True
    assert handoff["capability_target_handoff"]["entity_id"] == "light.kitchen_ceiling"
    assert handoff["deferred_release_2_owners"]["capability_discovery"] == "#317"


async def test_execute_consumes_device_entity_vocabulary_for_composite_scope(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should consume device/entity vocabulary using resolved composite scope."""
    from custom_components.concierge.storage import ConciergeStorage

    floor_registry = fr.async_get(hass)
    main_floor = floor_registry.async_create(name="Main")
    area_registry = ar.async_get(hass)
    kitchen = area_registry.async_create(name="Kitchen", floor_id=main_floor.floor_id)
    dining = area_registry.async_create(name="Dining", floor_id=main_floor.floor_id)

    await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "public_space",
            "name": "Public Space",
            "area_ids": [kitchen.id, dining.id],
            "primary_area": dining.id,
        },
        blocking=True,
    )

    storage = ConciergeStorage(hass)
    await storage.async_update_global_feature(
        feature_key="room_vocabulary_registry",
        enabled=True,
        options={
            "entries": [
                {
                    "term": "great room",
                    "aliases": ["public space"],
                    "composite_id": "public_space",
                }
            ]
        },
    )
    await storage.async_update_global_feature(
        feature_key="device_entity_vocabulary_registry",
        enabled=True,
        options={
            "entries": [
                {
                    "term": "main lights",
                    "aliases": ["living lights"],
                    "entity_id": "light.public_space_main",
                    "composite_id": "public_space",
                }
            ]
        },
    )

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "living lights",
            "area_id": "public space",
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    assert result["executed"] is True
    assert result["resolved_target"] == "light.public_space_main"
    envelope = result["execution_envelope"]
    assert envelope["routing"]["resolved_composite_id"] == "public_space"
    entity_resolution = result["device_entity_vocabulary_resolution"]
    assert entity_resolution["entity_id"] == "light.public_space_main"
    assert entity_resolution["composite_id"] == "public_space"


async def test_execute_rejects_ambiguous_device_entity_vocabulary_targets(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should reject ambiguous device/entity vocabulary mappings deterministically."""
    from custom_components.concierge.storage import ConciergeStorage

    area = ar.async_get(hass).async_create(name="Kitchen")
    storage = ConciergeStorage(hass)
    await storage.async_update_global_feature(
        feature_key="device_entity_vocabulary_registry",
        enabled=True,
        options={
            "entries": [
                {
                    "term": "main lights",
                    "aliases": ["lights"],
                    "entity_id": "light.kitchen_main",
                    "area_id": area.id,
                },
                {
                    "term": "ceiling lights",
                    "aliases": ["lights"],
                    "entity_id": "light.kitchen_ceiling",
                    "area_id": area.id,
                },
            ]
        },
    )

    with pytest.raises(Exception, match="device_entity_vocabulary_ambiguous_target"):
        await hass.services.async_call(
            DOMAIN,
            "execute",
            {
                "target": "lights",
                "area_id": area.id,
                "intent_class": "home_control",
            },
            blocking=True,
        )


async def test_execute_consumes_asset_vocabulary_handoff_for_area_scope(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should consume handed-off asset vocabulary targets within resolved room scope."""
    from custom_components.concierge.storage import ConciergeStorage

    area = ar.async_get(hass).async_create(name="Music Room")
    storage = ConciergeStorage(hass)
    await storage.async_update_global_feature(
        feature_key="asset_vocabulary_registry",
        enabled=True,
        options={
            "entries": [
                {
                    "term": "piano",
                    "aliases": ["grand piano"],
                    "asset_id": "asset.grand_piano",
                    "handoff_entity_id": "switch.music_room_piano_protect",
                    "area_id": area.id,
                }
            ]
        },
    )

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "grand piano",
            "area_id": area.id,
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    assert result["executed"] is True
    assert result["resolved_target"] == "switch.music_room_piano_protect"
    resolution = result["asset_vocabulary_resolution"]
    assert resolution["canonical_term"] == "piano"
    assert resolution["asset_id"] == "asset.grand_piano"
    assert resolution["entity_id"] == "switch.music_room_piano_protect"
    assert resolution["area_id"] == area.id
    assert resolution["composite_id"] is None
    cp00 = result["execution_envelope"]["asset_intelligence_cp00_handoff"]
    assert cp00["applicable"] is True
    assert cp00["deterministic_consumption"] is True
    assert cp00["asset_intelligence_authority_preserved"] is True
    assert cp00["authoritative_origin"]["authority_owner"] == "asset_intelligence"
    assert cp00["consumed_handoff_output"]["handed_off_entity_id"] == "switch.music_room_piano_protect"


async def test_execute_consumes_asset_vocabulary_handoff_for_composite_scope(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should consume handed-off asset vocabulary targets within resolved composite scope."""
    from custom_components.concierge.storage import ConciergeStorage

    floor_registry = fr.async_get(hass)
    main_floor = floor_registry.async_create(name="Main")
    area_registry = ar.async_get(hass)
    lounge = area_registry.async_create(name="Lounge", floor_id=main_floor.floor_id)
    library = area_registry.async_create(name="Library", floor_id=main_floor.floor_id)

    await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "media_suite",
            "name": "Media Suite",
            "area_ids": [lounge.id, library.id],
            "primary_area": library.id,
        },
        blocking=True,
    )

    storage = ConciergeStorage(hass)
    await storage.async_update_global_feature(
        feature_key="room_vocabulary_registry",
        enabled=True,
        options={
            "entries": [
                {
                    "term": "media suite",
                    "aliases": ["media room"],
                    "composite_id": "media_suite",
                }
            ]
        },
    )
    await storage.async_update_global_feature(
        feature_key="asset_vocabulary_registry",
        enabled=True,
        options={
            "entries": [
                {
                    "term": "receiver",
                    "aliases": ["home theater receiver"],
                    "asset_id": "asset.receiver",
                    "handoff_entity_id": "switch.media_suite_receiver_guard",
                    "composite_id": "media_suite",
                }
            ]
        },
    )

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "home theater receiver",
            "area_id": "media room",
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    assert result["executed"] is True
    assert result["resolved_target"] == "switch.media_suite_receiver_guard"
    envelope = result["execution_envelope"]
    assert envelope["routing"]["resolved_composite_id"] == "media_suite"
    resolution = result["asset_vocabulary_resolution"]
    assert resolution["asset_id"] == "asset.receiver"
    assert resolution["entity_id"] == "switch.media_suite_receiver_guard"
    assert resolution["composite_id"] == "media_suite"
    cp00 = envelope["asset_intelligence_cp00_handoff"]
    assert cp00["applicable"] is True
    assert cp00["consumed_handoff_output"]["asset_id"] == "asset.receiver"
    assert cp00["consumed_handoff_output"]["composite_id"] == "media_suite"
    assert cp00["deferred_release_2_owners"]["capability_discovery"] == "#317"


async def test_execute_rejects_ambiguous_asset_vocabulary_targets(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should reject ambiguous handed-off asset vocabulary targets deterministically."""
    from custom_components.concierge.storage import ConciergeStorage

    area = ar.async_get(hass).async_create(name="Gallery")
    storage = ConciergeStorage(hass)
    await storage.async_update_global_feature(
        feature_key="asset_vocabulary_registry",
        enabled=True,
        options={
            "entries": [
                {
                    "term": "artwork",
                    "aliases": ["painting"],
                    "asset_id": "asset.painting_1",
                    "handoff_entity_id": "switch.gallery_art_1",
                    "area_id": area.id,
                },
                {
                    "term": "featured art",
                    "aliases": ["painting"],
                    "asset_id": "asset.painting_2",
                    "handoff_entity_id": "switch.gallery_art_2",
                    "area_id": area.id,
                },
            ]
        },
    )

    with pytest.raises(Exception, match="asset_vocabulary_ambiguous_target"):
        await hass.services.async_call(
            DOMAIN,
            "execute",
            {
                "target": "painting",
                "area_id": area.id,
                "intent_class": "home_control",
            },
            blocking=True,
        )


async def test_resolve_mobile_context_returns_assembled_foundation_context(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Mobile context resolution should include bounded assembled room/composite context."""
    floor_registry = fr.async_get(hass)
    main_floor = floor_registry.async_create(name="Main")

    area_registry = ar.async_get(hass)
    kitchen = area_registry.async_create(name="Kitchen", floor_id=main_floor.floor_id)
    dining = area_registry.async_create(name="Dining", floor_id=main_floor.floor_id)

    await hass.services.async_call(
        DOMAIN,
        "update_global_context",
        {
            "context_type": "news",
            "enabled": True,
            "summary": "2 headlines available",
            "detail": "Morning digest ready",
            "speakable": "Two headlines are ready.",
        },
        blocking=True,
    )

    await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "great_room",
            "name": "Great Room",
            "area_ids": [kitchen.id, dining.id],
            "primary_area": dining.id,
        },
        blocking=True,
    )

    await hass.services.async_call(
        DOMAIN,
        "update_person_profile",
        {
            "person_id": "tom",
            "name": "Tom",
            "linked_area_id": kitchen.id,
            "ble_device_ids": [],
            "aqara_presence_entity_ids": [],
            "minor_allowed_intent_classes": ["room_context_info"],
            "minor_allow_general_qna": False,
        },
        blocking=True,
    )

    result = await hass.services.async_call(
        DOMAIN,
        "resolve_mobile_context",
        {"person_id": "tom"},
        blocking=True,
        return_response=True,
    )

    assert result["resolved_person_id"] == "tom"
    assert result["resolved_area_id"] == kitchen.id
    assert result["resolved_composite_id"] == "great_room"
    assert result["context_area_id"] == dining.id
    assert result["fallback_context_applied"] is False
    assert result["assembled_context"]["composite"]["primary_area"] == dining.id
    assert result["assembled_context"]["context_source_count"] == 1
    assert result["assembled_context"]["summary"] == "2 headlines available"


async def test_resolve_mobile_context_preserves_global_context_without_room_resolution(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Mobile context resolution should preserve global context continuity when room context is unavailable."""
    await hass.services.async_call(
        DOMAIN,
        "update_global_context",
        {
            "context_type": "weather",
            "enabled": True,
            "summary": "Rain later today",
            "detail": "High of 76",
            "speakable": "Rain is expected later today.",
        },
        blocking=True,
    )

    result = await hass.services.async_call(
        DOMAIN,
        "resolve_mobile_context",
        {},
        blocking=True,
        return_response=True,
    )

    assert result["resolved_person_id"] is None
    assert result["resolved_area_id"] is None
    assert result["clarification_required"] is True
    assert result["fallback_context_applied"] is True
    assert result["fallback_reason"] == "no_room_context"
    assert result["global_context_continuity_available"] is True
    assert result["assembled_context"]["summary"] == "Rain later today"


async def test_execute_direct_returns_execution_envelope_and_event(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Direct execution should shape a bounded execution envelope in both response and event payload."""
    events: list[dict] = []

    def _listener(event: Event) -> None:
        events.append(dict(event.data))

    unsub = hass.bus.async_listen(EVENT_EXECUTION, _listener)

    result = await hass.services.async_call(
        DOMAIN,
        "execute_direct",
        {
            "entity_id": "light.den",
            "service": "homeassistant.turn_on",
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    assert result["executed"] is True
    assert result["execution_outcome_category"] == "EXECUTE_SUCCESS"
    assert result["silence_as_success"] is False
    assert result["response_required"] is False
    assert result["response_generated"] is False
    envelope = result["execution_envelope"]
    assert envelope["execution_kind"] == "direct"
    boundary = envelope["capability_projection_boundary"]
    assert boundary["projection_role"] == "governed_projection_consumer"
    assert boundary["projection_is_authority"] is False
    assert boundary["deferred_release_2_owners"]["capability_diagnostics_explainability"] == "#318"
    consumption = envelope["authoritative_capability_input_consumption"]
    assert consumption["deterministic_consumption"] is True
    assert consumption["derived_capability_flags"]["cap_ai"] is False
    assert consumption["deferred_release_2_owners"]["capability_discovery"] == "#317"
    assert envelope["planning"]["plan_kind"] == "direct_service_call"
    assert envelope["planning"]["requested_service"] == "homeassistant.turn_on"
    assert envelope["routing"]["route_scope"] == "direct"
    assert envelope["context"] is None
    assert envelope["execution"]["domain"] == "homeassistant"
    assert envelope["execution"]["service"] == "turn_on"
    handoff = envelope["vocabulary_to_capability_handoff"]
    assert handoff["applicable"] is False
    assert handoff["handoff_path"] == "not_applicable_direct_execution"
    assert handoff["deferred_release_2_owners"]["asset_intelligence_cp00_handoff"] == "#316"
    cp00 = envelope["asset_intelligence_cp00_handoff"]
    assert cp00["applicable"] is False
    assert cp00["handoff_path"] == "not_applicable_direct_execution"
    assert cp00["asset_intelligence_authority_preserved"] is True
    discovery = envelope["capability_discovery"]
    assert discovery["applicable"] is False
    assert discovery["discovery_path"] == "not_applicable_direct_execution"
    assert discovery["capability_authority_external"] is True
    continuity = envelope["continuity_governance_boundary"]
    assert continuity["applicable"] is False
    assert continuity["continuity_path"] == "not_applicable_direct_execution"
    assert continuity["deterministic_boundary"] is True
    assert continuity["continuity_authority_external"] is True
    assert continuity["continuity_owns_identity"] is False
    assert continuity["continuity_owns_occupancy"] is False
    assert continuity["continuity_owns_memory"] is False
    assert continuity["privacy_boundary_preserved"] is True
    assert continuity["deferred_release_3_owners"]["continuity_affinity_diagnostics_explainability"] == "#328"
    assert continuity["deferred_release_3_owners"]["restoration_governance_boundary"] == "#329"
    affinity = envelope["person_room_affinity_boundary"]
    assert affinity["applicable"] is False
    assert affinity["affinity_path"] == "not_applicable_direct_execution"
    assert affinity["deterministic_boundary"] is True
    assert affinity["affinity_authority_external"] is True
    assert affinity["affinity_owns_identity"] is False
    assert affinity["affinity_owns_room_truth"] is False
    assert affinity["affinity_owns_occupancy"] is False
    assert affinity["affinity_owns_memory"] is False
    assert affinity["guest_safe_boundary_preserved"] is True
    assert affinity["privacy_boundary_preserved"] is True
    assert affinity["deferred_release_3_owners"]["privacy_household_memory_boundary"] == "#327"
    assert affinity["deferred_release_3_owners"]["continuity_affinity_diagnostics_explainability"] == "#328"
    memory = envelope["privacy_household_memory_boundary"]
    assert memory["applicable"] is False
    assert memory["boundary_path"] == "not_applicable_direct_execution"
    assert memory["deterministic_boundary"] is True
    assert memory["privacy_authority_external"] is True
    assert memory["household_memory_authority_external"] is True
    assert memory["memory_owns_identity"] is False
    assert memory["memory_owns_retention_policy"] is False
    assert memory["memory_owns_storage"] is False
    assert memory["memory_owns_provenance"] is False
    assert memory["guest_safe_boundary_preserved"] is True
    assert memory["deferred_release_3_owners"]["continuity_affinity_diagnostics_explainability"] == "#328"
    occupancy = envelope["occupancy_governance_boundary"]
    assert occupancy["applicable"] is False
    assert occupancy["occupancy_path"] == "not_applicable_direct_execution"
    assert occupancy["deterministic_boundary"] is True
    assert occupancy["occupancy_authority_external"] is True
    assert occupancy["occupancy_policy_authority_external"] is True
    assert occupancy["occupancy_truth_authority_external"] is True
    assert occupancy["occupancy_owns_room_truth"] is False
    assert occupancy["occupancy_owns_identity"] is False
    assert occupancy["occupancy_owns_household_memory"] is False
    assert occupancy["occupancy_owns_restoration"] is False
    assert occupancy["guest_safe_boundary_preserved"] is True
    assert occupancy["privacy_boundary_preserved"] is True
    assert occupancy["orchestration_constraints"]["route_scope"] == "direct"
    assert occupancy["orchestration_constraints"]["occupancy_boundary_only"] is True
    assert occupancy["orchestration_constraints"]["occupancy_decision_behavior_enabled"] is False
    assert occupancy["orchestration_constraints"]["occupancy_execution_enabled"] is False
    assert occupancy["orchestration_constraints"]["occupancy_inference_enabled"] is False
    assert occupancy["orchestration_constraints"]["occupancy_diagnostics_behavior_enabled"] is False
    assert occupancy["deferred_release_3_owners"]["presence_governance_boundary"] == "#334"
    assert occupancy["deferred_release_3_owners"]["occupancy_presence_diagnostics_explainability"] == "#337"
    presence = envelope["presence_governance_boundary"]
    assert presence["applicable"] is False
    assert presence["presence_path"] == "not_applicable_direct_execution"
    assert presence["deterministic_boundary"] is True
    assert presence["presence_authority_external"] is True
    assert presence["presence_policy_authority_external"] is True
    assert presence["presence_truth_authority_external"] is True
    assert presence["presence_owns_occupancy"] is False
    assert presence["presence_owns_room_truth"] is False
    assert presence["presence_owns_identity"] is False
    assert presence["presence_owns_household_memory"] is False
    assert presence["presence_owns_restoration"] is False
    assert presence["guest_safe_boundary_preserved"] is True
    assert presence["privacy_boundary_preserved"] is True
    assert presence["consumes_occupancy_governance_visibility"] is True
    assert presence["orchestration_constraints"]["route_scope"] == "direct"
    assert presence["orchestration_constraints"]["presence_boundary_only"] is True
    assert presence["orchestration_constraints"]["presence_detection_enabled"] is False
    assert presence["orchestration_constraints"]["presence_inference_enabled"] is False
    assert presence["orchestration_constraints"]["presence_attribution_enabled"] is False
    assert presence["orchestration_constraints"]["presence_behavior_enabled"] is False
    assert presence["orchestration_constraints"]["presence_diagnostics_behavior_enabled"] is False
    assert presence["deferred_release_3_owners"]["guest_unknown_occupant_behavior"] == "#335"
    assert presence["deferred_release_3_owners"]["occupancy_presence_diagnostics_explainability"] == "#337"
    experience = envelope["experience_governance_boundary"]
    assert experience["applicable"] is True
    assert experience["orchestration_constraints"]["route_scope"] == "direct"
    assert experience["orchestration_constraints"]["experience_projection_enabled"] is False
    assert experience["orchestration_constraints"]["experience_execution_enabled"] is False
    assert experience["orchestration_constraints"]["experience_restoration_enabled"] is False
    assert experience["deferred_release_2_owners"]["release_2_validation"] == "#324"
    experience_handoff = envelope["capability_to_experience_handoff"]
    assert experience_handoff["applicable"] is False
    assert experience_handoff["handoff_path"] == "not_applicable_direct_execution"
    assert experience_handoff["experience_consumption_ready"] is False
    assert experience_handoff["handoff_transfers_authority"] is False
    assert experience_handoff["deferred_release_2_owners"]["experience_projection"] == "#321"
    projection = envelope["experience_projection"]
    assert projection["applicable"] is False
    assert projection["projection_path"] == "not_applicable_direct_execution"
    assert projection["projection_is_authority"] is False
    assert projection["deferred_release_2_owners"]["release_2_validation"] == "#324"
    restoration = envelope["experience_restoration_boundary"]
    assert restoration["applicable"] is False
    assert restoration["restoration_path"] == "not_applicable_direct_execution"
    assert restoration["restoration_governance_path"] == "not_applicable_direct_execution"
    assert restoration["restoration_eligible"] is False
    assert restoration["restoration_authority_external"] is True
    assert restoration["restoration_policy_authority_external"] is True
    assert restoration["restoration_owns_identity"] is False
    assert restoration["restoration_owns_occupancy"] is False
    assert restoration["restoration_owns_continuity"] is False
    assert restoration["restoration_owns_affinity"] is False
    assert restoration["restoration_owns_household_memory"] is False
    assert restoration["governance_controls"]["route_scope"] == "direct"
    assert restoration["governance_controls"]["restoration_execution_enabled"] is False
    assert restoration["governance_controls"]["restoration_decision_behavior_enabled"] is False
    assert restoration["governance_controls"]["restoration_diagnostics_behavior_enabled"] is True
    assert restoration["restoration_authority_transferred"] is False
    assert restoration["deferred_release_3_owners"]["restoration_outcome_implementation"] == "#330"
    assert restoration["deferred_release_3_owners"]["e3a_preservation_alignment"] == "#331"
    assert restoration["deferred_release_3_owners"]["restoration_diagnostics_explainability"] == "#332"
    assert restoration["deferred_release_2_owners"]["experience_diagnostics_explainability"] == "#323"
    outcome = envelope["experience_restoration_outcome"]
    assert outcome["applicable"] is False
    assert outcome["outcome_path"] == "not_applicable_direct_execution"
    assert outcome["restoration_applied"] is False
    assert outcome["restoration_execution_handoff_ready"] is False
    assert outcome["restoration_outcome_reason"] == "direct_execution_not_eligible"
    assert outcome["selected_outcome"] is None
    assert outcome["governance_controls"]["route_scope"] == "direct"
    assert outcome["governance_controls"]["restoration_decision_behavior_enabled"] is False
    assert outcome["governance_controls"]["restoration_execution_enabled"] is False
    assert outcome["governance_controls"]["guest_unknown_behavior_enabled"] is False
    assert outcome["ownership_preservation"]["restoration_decision_authority_transferred"] is False
    preservation_alignment = envelope["e3a_preservation_alignment"]
    assert preservation_alignment["applicable"] is False
    assert preservation_alignment["alignment_path"] == "not_applicable_direct_execution"
    assert preservation_alignment["preservation_eligible"] is False
    assert preservation_alignment["alignment_reason"] == "direct_execution_not_eligible"
    assert preservation_alignment["governance_controls"]["route_scope"] == "direct"
    assert preservation_alignment["governance_controls"]["alignment_behavior_enabled"] is False
    assert preservation_alignment["governance_controls"]["restoration_decision_behavior_enabled"] is False
    assert preservation_alignment["governance_controls"]["restoration_execution_enabled"] is False
    assert preservation_alignment["ownership_preservation"]["preservation_creates_authority"] is False
    assert preservation_alignment["ownership_preservation"]["preservation_redefines_outcomes"] is False

    await hass.async_block_till_done()
    assert events
    event_envelope = events[-1]["execution_envelope"]
    assert event_envelope["planning"]["requested_entity_id"] == "light.den"
    assert event_envelope["execution"]["service"] == "turn_on"
    unsub()


async def test_execute_preserves_global_context_fallback_in_envelope(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execution envelope should preserve global context continuity when room context is unavailable."""
    await hass.services.async_call(
        DOMAIN,
        "update_global_context",
        {
            "context_type": "news",
            "enabled": True,
            "summary": "4 headlines available",
            "detail": "Morning digest ready",
            "speakable": "Four headlines are available.",
        },
        blocking=True,
    )

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    assert result["execution_outcome_category"] == "SILENCE_SUCCESS"
    assert result["silence_as_success"] is True
    assert result["response_required"] is False
    assert result["response_generated"] is False
    envelope = result["execution_envelope"]
    assert envelope["routing"]["route_scope"] == "global"
    assert envelope["context"]["context_area_id"] is None
    assert envelope["context"]["fallback_context_applied"] is True
    assert envelope["context"]["fallback_reason"] == "no_room_context"
    assert envelope["context"]["global_context_continuity_available"] is True
    assert envelope["context"]["summary"] == "4 headlines available"


async def test_execute_direct_records_policy_denied_activity(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Policy-denied execution should still be captured in backend activity timeline."""
    await hass.services.async_call(
        DOMAIN,
        "update_person_profile",
        {
            "person_id": "minor_1",
            "name": "Minor",
            "is_minor": True,
            "minor_allowed_intent_classes": ["media_only"],
            "minor_allow_general_qna": False,
        },
        blocking=True,
    )

    with pytest.raises(Exception, match="minor_policy_denied"):
        await hass.services.async_call(
            DOMAIN,
            "execute_direct",
            {
                "entity_id": "light.den",
                "service": "homeassistant.turn_on",
                "person_id": "minor_1",
                "intent_class": "home_control",
            },
            blocking=True,
            return_response=True,
        )

    timeline = await hass.services.async_call(
        DOMAIN,
        "get_activity_timeline",
        {"person_id": "minor_1"},
        blocking=True,
        return_response=True,
    )
    activities = timeline.get("activities", [])
    assert any(
        item.get("intent_class") == "execute_direct"
        and item.get("outcome") == "policy_denied"
        for item in activities
    )


async def test_update_room_config_records_activity_with_room_scope(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Room setup mutations should be backend-logged in activity timeline."""
    area = ar.async_get(hass).async_create(name="Living Room")

    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": area.id,
            "voice_device_entity_ids": [
                "assist_satellite.home_assistant_voice_0a87d9_assist_satellite"
            ],
        },
        blocking=True,
    )

    timeline = await hass.services.async_call(
        DOMAIN,
        "get_activity_timeline",
        {"area_id": area.id},
        blocking=True,
        return_response=True,
    )
    activities = timeline.get("activities", [])
    assert any(
        item.get("intent_class") == "room_config_update"
        and item.get("outcome") == "success"
        and item.get("resolved_area_id") == area.id
        for item in activities
    )


async def test_update_person_profile_records_activity_with_person_scope(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Person setup mutations should be backend-logged in activity timeline."""
    await hass.services.async_call(
        DOMAIN,
        "update_person_profile",
        {
            "person_id": "tom",
            "name": "Tom",
            "linked_area_id": "living_room",
            "ble_device_ids": [],
            "aqara_presence_entity_ids": [],
            "minor_allowed_intent_classes": ["room_context_info"],
            "minor_allow_general_qna": False,
        },
        blocking=True,
    )

    timeline = await hass.services.async_call(
        DOMAIN,
        "get_activity_timeline",
        {"person_id": "tom"},
        blocking=True,
        return_response=True,
    )
    activities = timeline.get("activities", [])
    assert any(
        item.get("intent_class") == "update_person_profile"
        and item.get("outcome") == "success"
        and item.get("resolved_person_id") == "tom"
        for item in activities
    )


async def test_update_person_profile_persists_productivity_source_bindings(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Person productivity source bindings should be stored as setup-only configuration state."""
    await hass.services.async_call(
        DOMAIN,
        "update_person_profile",
        {
            "person_id": "tom",
            "name": "Tom",
            "email_source_ref": "sensor.mailbox_tom",
            "calendar_source_ref": "sensor.calendar_tom",
            "shopping_source_ref": "shopping_provider_household",
            "email_source_bindings": [
                {"entity_id": "sensor.mailbox_tom", "label": "Mail"},
                {"entity_id": "sensor.mailbox_backup", "label": "Backup mail"},
            ],
            "calendar_source_bindings": [
                {"entity_id": "sensor.calendar_tom", "label": "Calendar"},
            ],
            "shopping_source_bindings": [
                {"entity_id": "shopping_provider_household", "label": "Shopping"},
            ],
        },
        blocking=True,
    )

    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    profile = state.person_profiles["tom"]

    assert profile.email_source_ref == "sensor.mailbox_tom"
    assert profile.calendar_source_ref == "sensor.calendar_tom"
    assert profile.shopping_source_ref == "shopping_provider_household"
    assert [binding["entity_id"] for binding in profile.email_source_bindings] == [
        "sensor.mailbox_tom",
        "sensor.mailbox_backup",
    ]
    assert [binding["entity_id"] for binding in profile.calendar_source_bindings] == [
        "sensor.calendar_tom",
    ]
    assert [binding["entity_id"] for binding in profile.shopping_source_bindings] == [
        "shopping_provider_household",
    ]


async def test_execute_invokes_voice_identity_runtime_services_and_consumes_outputs(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Execute should actively invoke Voice Identity runtime services and consume outputs."""
    _register_voice_identity_runtime_services(
        hass,
        attribution_payload={
            "success": True,
            "status": "ready",
            "identity_confidence_level": "recognized",
            "attributed_person_id": "person.tom",
            "attributed_profile_id": "vp_tom",
            "confidence": 0.91,
            "confidence_band": "high",
            "reason_code": "attribution_ready",
            "diagnostic_summary": {
                "diagnostic_available": True,
                "diagnostic_reason_code": "voice_identity_ready",
                "repair_available": True,
                "health_status": "healthy",
                "attribution_readiness": "ready",
                "compatibility_readiness": "ready",
            },
            "repair_hint_code": "no_action_required",
            "suggested_next_action_code": "no_action_required",
        },
        identity_context_payload={
            "state": "known",
            "person_id": "person.tom",
            "voice_profile_id": "vp_tom",
            "confidence": 0.91,
            "confidence_band": "high",
            "reason_code": "attribution_ready",
            "source": "voice_identity",
        },
    )

    observed_calls: list[tuple[str, str, dict[str, object]]] = []
    original_async_call = hass.services.async_call

    async def _tracking_async_call(domain, service, service_data=None, **kwargs):
        payload = dict(service_data or {})
        if domain == "voice_identity" and service in {"attribute_speaker", "get_identity_context"}:
            observed_calls.append((domain, service, payload))
        return await original_async_call(domain, service, service_data, **kwargs)

    monkeypatch.setattr(hass.services, "async_call", _tracking_async_call)

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "audio_ref": "media://voice/runtime-sample-001.wav",
                "candidate_scope": ["person.tom"],
                "model_preference": "ecapa_v1",
            },
        },
        blocking=True,
        return_response=True,
    )

    invoked_services = [service for _, service, _ in observed_calls]
    assert "attribute_speaker" in invoked_services
    assert "get_identity_context" in invoked_services
    for _, service, payload in observed_calls:
        if service in {"attribute_speaker", "get_identity_context"}:
            assert payload.get("audio_ref") == "media://voice/runtime-sample-001.wav"
            assert payload.get("candidate_scope") == ["person.tom"]
            assert payload.get("model_preference") == "ecapa_v1"

    consumption = result["execution_envelope"]["voice_identity_attribution_confidence_consumption"]
    assert consumption["attribution"]["consumed"] is True
    assert consumption["attribution"]["person_id"] == "person.tom"
    assert consumption["attribution"]["voice_profile_id"] == "vp_tom"
    assert consumption["confidence"]["consumed"] is True
    assert consumption["confidence"]["value"] == pytest.approx(0.91)
    assert consumption["confidence"]["band"] == "high"
    diagnostics = consumption["diagnostics_boundary"]["diagnostics"]
    assert diagnostics["diagnostic_available"] is True
    assert diagnostics["attribution_readiness"] == "ready"


async def test_execute_fails_closed_when_voice_identity_runtime_services_unavailable(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should fail closed to no active attribution when Voice Identity services are unavailable."""
    if hass.services.has_service("voice_identity", "attribute_speaker"):
        hass.services.async_remove("voice_identity", "attribute_speaker")
    if hass.services.has_service("voice_identity", "get_identity_context"):
        hass.services.async_remove("voice_identity", "get_identity_context")

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "audio_ref": "media://voice/runtime-sample-002.wav",
            },
        },
        blocking=True,
        return_response=True,
    )

    consumption = result["execution_envelope"]["voice_identity_attribution_confidence_consumption"]
    assert consumption["attribution"]["consumed"] is False
    assert consumption["attribution"]["state"] == "unavailable"
    assert consumption["attribution"]["reason_code"] == "attribution_service_unavailable"
    assert consumption["confidence"]["consumed"] is False


async def test_execute_consumes_voice_identity_attribution_and_confidence_outcomes(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should consume Voice Identity attribution/confidence outcomes as bounded inputs."""
    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "identity_context": {
                    "state": "known",
                    "person_id": "person.tom",
                    "voice_profile_id": "vp_tom",
                    "confidence": 0.93,
                    "confidence_band": "high",
                    "reason_code": "recognized",
                    "source": "voice_identity",
                }
            },
        },
        blocking=True,
        return_response=True,
    )

    consumption = result["execution_envelope"]["voice_identity_attribution_confidence_consumption"]
    assert consumption["boundary_path"] == "governed_voice_identity_attribution_confidence_consumption"
    assert consumption["voice_identity_authority_external"] is True
    assert consumption["consumption_only"] is True
    assert consumption["attribution"]["consumed"] is True
    assert consumption["attribution"]["state"] == "known"
    assert consumption["attribution"]["person_id"] == "person.tom"
    assert consumption["attribution"]["voice_profile_id"] == "vp_tom"
    assert consumption["confidence"]["consumed"] is True
    assert consumption["confidence"]["value"] == pytest.approx(0.93)
    assert consumption["confidence"]["band"] == "high"


async def test_execute_enables_person_aware_productivity_routing_when_active_person_available(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should enable person-aware productivity routing only for active resolved person context."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="person.tom",
            name="Tom",
            email_source_ref="sensor.mailbox_tom",
            calendar_source_ref="sensor.calendar_tom",
            task_source_ref="tasks_provider_tom",
            shopping_source_ref="shopping_provider_household",
        )
    )
    hass.states.async_set("sensor.mailbox_tom", "ok")
    hass.states.async_set("sensor.calendar_tom", "ok")

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "identity_context": {
                    "state": "known",
                    "person_id": "person.tom",
                    "voice_profile_id": "vp_tom",
                    "confidence": 0.95,
                    "confidence_band": "high",
                    "reason_code": "recognized",
                    "source": "voice_identity",
                }
            },
        },
        blocking=True,
        return_response=True,
    )

    routing = result["execution_envelope"]["person_aware_productivity_routing"]
    assert routing["routing_enabled"] is True
    assert routing["reason_code"] == "person_routing_available"
    assert routing["active_person_state"] == "active_person_available"
    assert routing["active_person_available"] is True
    assert routing["resolved_person_id"] == "person.tom"
    assert routing["domain_routing"]["calendar"]["enabled"] is True
    assert routing["domain_routing"]["calendar"]["selection_mode"] == "person_binding"
    assert routing["domain_routing"]["shopping"]["enabled"] is True
    assert routing["domain_routing"]["shopping"]["selected_source_ref"] == "shopping_provider_household"
    assert routing["domain_routing"]["task"]["enabled"] is True
    assert routing["domain_routing"]["task"]["selection_mode"] == "person_binding"
    assert routing["domain_routing"]["task"]["selected_source_ref"] == "tasks_provider_tom"

    calendar_routing = result["execution_envelope"]["calendar_email_consumption_boundary"]["person_aware_routing"]
    assert calendar_routing["routing_enabled"] is True
    assert calendar_routing["domains"]["calendar"]["enabled"] is True
    assert calendar_routing["domains"]["email"]["enabled"] is True

    task_shopping_routing = result["execution_envelope"]["task_shopping_consumption_boundary"]["person_aware_routing"]
    assert task_shopping_routing["routing_enabled"] is True
    assert task_shopping_routing["domains"]["task"]["enabled"] is True
    assert task_shopping_routing["domains"]["shopping"]["enabled"] is True

    household_coordination_boundary = result["execution_envelope"]["household_coordination_boundary"]
    assert household_coordination_boundary["boundary_path"] == "governed_household_coordination_boundary"
    assert household_coordination_boundary["coordination_context"]["active_person_state"] == "active_person_available"
    assert household_coordination_boundary["person_aware_productivity_routing"]["routing_enabled"] is True
    assert household_coordination_boundary["open_loop_coordination_visibility"]["open_loop_supported"] is True
    assert household_coordination_boundary["open_loop_coordination_visibility"]["coordination_state"] == household_coordination_boundary["coordination_state"]

    productivity_coordination_boundary = result["execution_envelope"]["productivity_coordination_boundary"]
    assert productivity_coordination_boundary["boundary_path"] == "governed_productivity_coordination_boundary"
    assert productivity_coordination_boundary["person_aware_routing_inputs"]["routing_enabled"] is True
    assert productivity_coordination_boundary["person_aware_routing_inputs"]["domain_routing"]["calendar"]["enabled"] is True
    assert productivity_coordination_boundary["provenance_inputs"]["provenance_visible"] is True
    assert productivity_coordination_boundary["non_authority_assertions"]["claims_productivity_authority"] is False

    provenance_diagnostics_boundary = result["execution_envelope"][
        "provenance_diagnostics_explainability_boundary"
    ]
    assert (
        provenance_diagnostics_boundary["boundary_path"]
        == "governed_release_6_provenance_diagnostics_explainability_boundary"
    )
    assert provenance_diagnostics_boundary["governance_context"]["route_scope"] == "global"
    assert provenance_diagnostics_boundary["provenance_visibility"]["provenance_visible"] is True
    assert (
        provenance_diagnostics_boundary["explainability_visibility"]["provenance_inputs_visible"]
        is True
    )
    assert (
        provenance_diagnostics_boundary["non_authority_assertions"]["claims_ownership_authority"]
        is False
    )


async def test_execute_surfaces_room_configuration_authority_traceability_for_composite_room(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should carry room authority from configuration even when a composite is resolved."""
    area = ar.async_get(hass).async_create(name="Living Room")
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(
        area_id=area.id,
        voice_device_entity_ids=["assist_satellite.living_room"],
        speaker_entity_ids=["media_player.living_room_speaker"],
        environment_information_outputs=["weather"],
        weather_source_entity_ids=["weather.living_room"],
    )
    await storage.async_update_composite_config(
        composite_id="living_suite",
        area_ids=[area.id],
        primary_area=area.id,
        voice_device_entity_ids=["assist_satellite.living_room"],
        speaker_entity_ids=["media_player.living_room_speaker"],
        environment_information_outputs=["weather"],
    )

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "area_id": area.id,
            "composite_id": "living_suite",
            "target": "light.kitchen",
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    room_authority = result["execution_envelope"]["room_authority_traceability"]
    assert room_authority["room_configuration_loaded"] is True
    assert room_authority["room_authority_source"] == "room_configuration"
    assert room_authority["merged_room_authority_source"] == "room_configuration"
    assert room_authority["room_configuration_primary_area"] == area.id
    assert room_authority["room_configuration_composite_id"] == "living_suite"
    assert room_authority["environment_source_origin"] == "room_configuration"

    capability_discovery = result["execution_envelope"]["capability_discovery"]
    assert capability_discovery["authority_traceability"]["room_configuration_loaded"] is True
    assert capability_discovery["authority_traceability"]["merged_room_authority_source"] == "room_configuration"


async def test_execute_disables_person_aware_productivity_routing_for_ambiguous_identity(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should fail closed when active person is ambiguous or unavailable."""
    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "identity_context": {
                    "state": "low_confidence",
                    "confidence": 0.42,
                    "confidence_band": "low",
                    "reason_code": "low_confidence",
                    "source": "voice_identity",
                }
            },
        },
        blocking=True,
        return_response=True,
    )

    routing = result["execution_envelope"]["person_aware_productivity_routing"]
    assert routing["routing_enabled"] is False
    assert routing["active_person_state"] == "active_person_ambiguous"
    assert routing["active_person_available"] is False
    assert routing["reason_code"] == "low_confidence"
    assert routing["domain_routing"]["calendar"]["enabled"] is False
    assert routing["domain_routing"]["task"]["enabled"] is False
    assert routing["domain_routing"]["shopping"]["enabled"] is False

    calendar_routing = result["execution_envelope"]["calendar_email_consumption_boundary"]["person_aware_routing"]
    assert calendar_routing["routing_enabled"] is False
    assert calendar_routing["reason_code"] == "low_confidence"

    task_shopping_routing = result["execution_envelope"]["task_shopping_consumption_boundary"]["person_aware_routing"]
    assert task_shopping_routing["routing_enabled"] is False
    assert task_shopping_routing["reason_code"] == "low_confidence"

    household_coordination_boundary = result["execution_envelope"]["household_coordination_boundary"]
    assert household_coordination_boundary["boundary_path"] == "governed_household_coordination_boundary"
    assert household_coordination_boundary["coordination_context"]["active_person_state"] == "active_person_ambiguous"
    assert household_coordination_boundary["person_aware_productivity_routing"]["routing_enabled"] is False
    assert household_coordination_boundary["open_loop_coordination_visibility"]["open_loop_supported"] is True
    assert household_coordination_boundary["open_loop_coordination_visibility"]["informational_only"] is True

    productivity_coordination_boundary = result["execution_envelope"]["productivity_coordination_boundary"]
    assert productivity_coordination_boundary["boundary_path"] == "governed_productivity_coordination_boundary"
    assert productivity_coordination_boundary["person_aware_routing_inputs"]["routing_enabled"] is False
    assert productivity_coordination_boundary["person_aware_routing_inputs"]["active_person_state"] == "active_person_ambiguous"
    assert productivity_coordination_boundary["non_authority_assertions"]["claims_coordination_authority"] is False

    provenance_diagnostics_boundary = result["execution_envelope"][
        "provenance_diagnostics_explainability_boundary"
    ]
    assert provenance_diagnostics_boundary["governance_context"]["route_scope"] == "global"
    assert provenance_diagnostics_boundary["diagnostics_visibility"]["ownership_visibility_supported"] is True
    assert provenance_diagnostics_boundary["safe_fallback_mode_active"] is True
    assert provenance_diagnostics_boundary["safe_fallback_reason"] == "provenance_lineage_incomplete"
    assert (
        provenance_diagnostics_boundary["non_authority_assertions"]["claims_lineage_authority"]
        is False
    )


async def test_execute_consumes_voice_identity_enrollment_and_lifecycle_state(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should consume Voice Identity enrollment/lifecycle state as bounded inputs."""
    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "voice_identity_enrollment_lifecycle_context": {
                    "enrollment_state": "active",
                    "enrollment_readiness": "ready",
                    "enrollment_lifecycle_state": "active",
                    "voice_profile_lifecycle_state": "active",
                    "identity_lifecycle_state": "active",
                    "voice_profile_id": "vp_tom",
                    "speaker_embedding_id": "emb_tom_001",
                    "reason_code": "voice_identity_ready",
                    "source": "voice_identity",
                }
            },
        },
        blocking=True,
        return_response=True,
    )

    enrollment_lifecycle = result["execution_envelope"][
        "voice_identity_attribution_confidence_consumption"
    ]["enrollment_lifecycle"]
    assert enrollment_lifecycle["boundary_path"] == "governed_voice_identity_enrollment_lifecycle_consumption"
    assert enrollment_lifecycle["voice_identity_authority_external"] is True
    assert enrollment_lifecycle["consumption_only"] is True
    assert enrollment_lifecycle["enrollment"]["consumed"] is True
    assert enrollment_lifecycle["enrollment"]["state"] == "active"
    assert enrollment_lifecycle["enrollment"]["readiness"] == "ready"
    assert enrollment_lifecycle["enrollment"]["speaker_embedding_id"] == "emb_tom_001"
    assert enrollment_lifecycle["lifecycle"]["consumed"] is True
    assert enrollment_lifecycle["lifecycle"]["enrollment_lifecycle_state"] == "active"
    assert enrollment_lifecycle["lifecycle"]["voice_profile_lifecycle_state"] == "active"
    assert enrollment_lifecycle["lifecycle"]["identity_lifecycle_state"] == "active"


async def test_execute_consumes_voice_identity_permission_and_consent_outcomes(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should consume Voice Identity permission/consent outcomes as bounded inputs."""
    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "voice_identity_permission_context": {
                    "permission_state": "allowed",
                    "permission_outcome": "permitted",
                    "consent_state": "granted",
                    "consent_outcome": "valid",
                    "eligibility_state": "eligible",
                    "gating_reason": "policy_allows",
                    "permission_reason_code": "permission_ready",
                    "lineage_ref": "vi-permission-001",
                    "source": "voice_identity",
                }
            },
        },
        blocking=True,
        return_response=True,
    )

    permission_boundary = result["execution_envelope"][
        "voice_identity_attribution_confidence_consumption"
    ]["permission_boundary"]
    assert permission_boundary["boundary_path"] == "governed_voice_identity_permission_consumption"
    assert permission_boundary["voice_identity_authority_external"] is True
    assert permission_boundary["consumption_only"] is True
    assert permission_boundary["permission"]["consumed"] is True
    assert permission_boundary["permission"]["state"] == "allowed"
    assert permission_boundary["permission"]["outcome"] == "permitted"
    assert permission_boundary["permission"]["consent_state"] == "granted"
    assert permission_boundary["permission"]["consent_outcome"] == "valid"
    assert permission_boundary["permission"]["lineage_ref"] == "vi-permission-001"


async def test_execute_consumes_voice_identity_legacy_disposition_outcomes(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should consume Voice Identity legacy disposition outcomes as bounded inputs."""
    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "voice_identity_legacy_disposition_context": {
                    "legacy_disposition_state": "superseded",
                    "legacy_disposition_outcome": "replacement_reference_consumed",
                    "legacy_reference": "legacy-fingerprint-001",
                    "replacement_reference": "voiceprint-v2-001",
                    "legacy_reason_code": "replacement_reference_available",
                    "lineage_ref": "vi-legacy-001",
                    "source": "voice_identity",
                }
            },
        },
        blocking=True,
        return_response=True,
    )

    legacy_boundary = result["execution_envelope"][
        "voice_identity_attribution_confidence_consumption"
    ]["legacy_disposition_boundary"]
    assert legacy_boundary["boundary_path"] == "governed_voice_identity_legacy_disposition_consumption"
    assert legacy_boundary["voice_identity_authority_external"] is True
    assert legacy_boundary["consumption_only"] is True
    assert legacy_boundary["legacy_disposition"]["consumed"] is True
    assert legacy_boundary["legacy_disposition"]["state"] == "superseded"
    assert legacy_boundary["legacy_disposition"]["outcome"] == "replacement_reference_consumed"
    assert legacy_boundary["legacy_disposition"]["legacy_reference"] == "legacy-fingerprint-001"
    assert legacy_boundary["legacy_disposition"]["replacement_reference"] == "voiceprint-v2-001"


async def test_execute_reports_unavailable_permission_state_when_missing_permission_fields(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should explicitly report unavailable permission state when Voice Identity omits it."""
    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "voice_identity_permission_context": {
                    "reason_code": "permission_projection_missing",
                    "source": "voice_identity",
                }
            },
        },
        blocking=True,
        return_response=True,
    )

    permission = result["execution_envelope"]["voice_identity_attribution_confidence_consumption"][
        "permission_boundary"
    ]["permission"]
    assert permission["consumed"] is False
    assert permission["state"] == "unavailable"
    assert permission["reason_code"] == "permission_state_unavailable"


async def test_execute_reports_unavailable_legacy_disposition_when_missing_disposition_fields(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should explicitly report unavailable legacy disposition when Voice Identity omits it."""
    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "voice_identity_legacy_disposition_context": {
                    "reason_code": "legacy_projection_missing",
                    "source": "voice_identity",
                }
            },
        },
        blocking=True,
        return_response=True,
    )

    legacy_disposition = result["execution_envelope"]["voice_identity_attribution_confidence_consumption"][
        "legacy_disposition_boundary"
    ]["legacy_disposition"]
    assert legacy_disposition["consumed"] is False
    assert legacy_disposition["state"] == "unavailable"
    assert legacy_disposition["reason_code"] == "legacy_disposition_unavailable"


async def test_execute_consumes_voice_identity_diagnostics_and_explainability_outputs(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should consume Voice Identity diagnostics/explainability as bounded outputs."""
    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "voice_identity_diagnostics_context": {
                    "diagnostic_available": True,
                    "diagnostic_reason_code": "voice_identity_ready",
                    "health_status": "healthy",
                    "attribution_readiness": "ready",
                    "compatibility_readiness": "ready",
                    "repair_available": True,
                    "repair_hint_code": "refresh_voice_profile",
                    "suggested_next_action_code": "retry_after_refresh",
                    "provenance_source": "voice_identity_diagnostics",
                    "source_reference": "vi-diagnostics-001",
                    "lineage_ref": "vi-diagnostics-lineage-001",
                    "source": "voice_identity",
                },
                "voice_identity_explainability_context": {
                    "consumed_outcome": "attribution_abstained",
                    "authority_source": "voice_identity",
                    "provenance_source": "voice_identity_attribution",
                    "source_reference": "vi-explainability-001",
                    "lineage_ref": "vi-explainability-lineage-001",
                    "attribution_source": "voice_identity_attribution_service",
                    "confidence_source": "voice_identity_confidence_band",
                    "enrollment_source": "voice_identity_enrollment_registry",
                    "lifecycle_source": "voice_identity_lifecycle_registry",
                    "permission_source": "voice_identity_permission_policy",
                    "legacy_disposition_source": "voice_identity_legacy_disposition",
                    "reason_code": "voice_identity_explained",
                    "source": "voice_identity",
                },
            },
        },
        blocking=True,
        return_response=True,
    )

    boundary = result["execution_envelope"]["voice_identity_attribution_confidence_consumption"]
    diagnostics_boundary = boundary["diagnostics_boundary"]
    assert diagnostics_boundary["boundary_path"] == "governed_voice_identity_diagnostics_consumption"
    assert diagnostics_boundary["voice_identity_authority_external"] is True
    assert diagnostics_boundary["consumption_only"] is True
    assert diagnostics_boundary["diagnostics"]["consumed"] is True
    assert diagnostics_boundary["diagnostics"]["diagnostic_available"] is True
    assert diagnostics_boundary["diagnostics"]["health_status"] == "healthy"
    assert diagnostics_boundary["diagnostics"]["repair_hint_code"] == "refresh_voice_profile"
    assert diagnostics_boundary["diagnostics"]["provenance_source"] == "voice_identity_diagnostics"
    assert diagnostics_boundary["diagnostics"]["lineage_ref"] == "vi-diagnostics-lineage-001"
    explainability_boundary = boundary["explainability_boundary"]
    assert explainability_boundary["boundary_path"] == "governed_voice_identity_explainability_consumption"
    assert explainability_boundary["voice_identity_authority_external"] is True
    assert explainability_boundary["consumption_only"] is True
    assert explainability_boundary["explainability"]["consumed"] is True
    assert explainability_boundary["explainability"]["consumed_outcome"] == "attribution_abstained"
    assert explainability_boundary["explainability"]["authority_source"] == "voice_identity"
    assert explainability_boundary["explainability"]["provenance_source"] == "voice_identity_attribution"
    assert explainability_boundary["explainability"]["permission_source"] == "voice_identity_permission_policy"
    assert explainability_boundary["explainability"]["legacy_disposition_source"] == "voice_identity_legacy_disposition"


async def test_execute_reports_unavailable_voice_identity_diagnostics_and_explainability_surfaces(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should report unavailable diagnostics/explainability without inventing Voice Identity state."""
    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "voice_identity_diagnostics_context": {
                    "source": "voice_identity",
                },
                "voice_identity_explainability_context": {
                    "source": "voice_identity",
                },
            },
        },
        blocking=True,
        return_response=True,
    )

    boundary = result["execution_envelope"]["voice_identity_attribution_confidence_consumption"]
    diagnostics = boundary["diagnostics_boundary"]["diagnostics"]
    assert diagnostics["consumed"] is False
    assert diagnostics["diagnostic_available"] is False
    assert diagnostics["health_status"] == "unavailable"
    assert diagnostics["diagnostic_reason_code"] == "diagnostics_surface_unavailable"
    assert diagnostics["source"] == "voice_identity_unavailable"
    explainability = boundary["explainability_boundary"]["explainability"]
    assert explainability["consumed"] is False
    assert explainability["unavailable_state"] == "unavailable"
    assert explainability["reason_code"] == "explainability_surface_unavailable"
    assert explainability["source"] == "voice_identity_unavailable"


async def test_execute_reports_unavailable_enrollment_state_when_missing_enrollment_fields(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should explicitly report unavailable enrollment state when Voice Identity omits it."""
    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "voice_identity_enrollment_lifecycle_context": {
                    "enrollment_lifecycle_state": "active",
                    "reason_code": "voice_identity_ready",
                    "source": "voice_identity",
                }
            },
        },
        blocking=True,
        return_response=True,
    )

    enrollment = result["execution_envelope"]["voice_identity_attribution_confidence_consumption"][
        "enrollment_lifecycle"
    ]["enrollment"]
    assert enrollment["consumed"] is False
    assert enrollment["state"] == "unavailable"
    assert enrollment["reason_code"] == "enrollment_state_unavailable"


async def test_execute_reports_unavailable_lifecycle_state_when_missing_lifecycle_fields(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should explicitly report unavailable lifecycle state when Voice Identity omits it."""
    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "voice_identity_enrollment_lifecycle_context": {
                    "enrollment_state": "active",
                    "enrollment_readiness": "ready",
                    "voice_profile_id": "vp_tom",
                    "reason_code": "voice_identity_ready",
                    "source": "voice_identity",
                }
            },
        },
        blocking=True,
        return_response=True,
    )

    lifecycle = result["execution_envelope"]["voice_identity_attribution_confidence_consumption"][
        "enrollment_lifecycle"
    ]["lifecycle"]
    assert lifecycle["consumed"] is False
    assert lifecycle["enrollment_lifecycle_state"] == "unavailable"
    assert lifecycle["reason_code"] == "lifecycle_state_unavailable"


async def test_execute_reports_unavailable_attribution_data_when_missing_identity_context(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should report unavailable attribution data when no identity-context payload is provided."""
    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {"channel": "voice"},
        },
        blocking=True,
        return_response=True,
    )

    attribution = result["execution_envelope"]["voice_identity_attribution_confidence_consumption"][
        "attribution"
    ]
    assert attribution["consumed"] is False
    assert attribution["state"] == "unavailable"
    assert attribution["reason_code"] == "attribution_data_unavailable"


async def test_execute_reports_unavailable_confidence_data_when_missing_confidence_fields(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute should report unavailable confidence data when attribution context omits confidence outputs."""
    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "identity_context": {
                    "state": "known",
                    "person_id": "person.tom",
                    "voice_profile_id": "vp_tom",
                    "reason_code": "recognized",
                    "source": "voice_identity",
                }
            },
        },
        blocking=True,
        return_response=True,
    )

    confidence = result["execution_envelope"]["voice_identity_attribution_confidence_consumption"][
        "confidence"
    ]
    assert confidence["consumed"] is False
    assert confidence["value"] is None
    assert confidence["band"] is None
    assert confidence["reason_code"] == "confidence_data_unavailable"


async def test_execute_preserves_voice_identity_authority_boundary_for_consumption(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute must preserve Voice Identity authority boundaries while consuming outcomes."""
    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "identity_context": {
                    "state": "low_confidence",
                    "confidence": 0.42,
                    "confidence_band": "low",
                    "reason_code": "low_confidence",
                    "source": "voice_identity",
                }
            },
        },
        blocking=True,
        return_response=True,
    )

    boundary = result["execution_envelope"]["voice_identity_attribution_confidence_consumption"]
    assert boundary["derive_attribution_authority"] is False
    assert boundary["derive_confidence_authority"] is False
    assert boundary["calculate_attribution"] is False
    assert boundary["calculate_confidence"] is False
    assert boundary["manage_identity_lifecycle"] is False
    assert boundary["manage_enrollment"] is False
    enrollment_lifecycle = boundary["enrollment_lifecycle"]
    assert enrollment_lifecycle["manage_enrollment_lifecycle"] is False
    assert enrollment_lifecycle["manage_voice_profile_lifecycle"] is False
    assert enrollment_lifecycle["manage_identity_lifecycle"] is False
    assert enrollment_lifecycle["create_voice_profiles"] is False
    assert enrollment_lifecycle["approve_enrollment"] is False
    assert enrollment_lifecycle["reject_enrollment"] is False
    assert enrollment_lifecycle["change_enrollment_state"] is False
    assert enrollment_lifecycle["infer_enrollment_state"] is False
    permission_boundary = boundary["permission_boundary"]
    assert permission_boundary["derive_permission_authority"] is False
    assert permission_boundary["create_permission_policy"] is False
    assert permission_boundary["define_eligibility_rules"] is False
    assert permission_boundary["determine_permission_outcomes"] is False
    assert permission_boundary["override_voice_identity_permission_policy"] is False
    assert permission_boundary["grant_permission"] is False
    assert permission_boundary["revoke_permission"] is False
    assert permission_boundary["approve_consent"] is False
    assert permission_boundary["infer_consent"] is False
    assert permission_boundary["infer_permission_state"] is False
    legacy_boundary = boundary["legacy_disposition_boundary"]
    assert legacy_boundary["manage_legacy_fingerprint_resolution"] is False
    assert legacy_boundary["migrate_legacy_identity_data"] is False
    assert legacy_boundary["dispose_legacy_identity_data"] is False
    assert legacy_boundary["determine_legacy_disposition"] is False
    assert legacy_boundary["infer_legacy_disposition_state"] is False
    assert legacy_boundary["claim_voiceprint_ownership"] is False
    assert legacy_boundary["claim_embedding_ownership"] is False
    assert legacy_boundary["establish_identity_authority"] is False
    assert legacy_boundary["determine_enrollment_state"] is False
    diagnostics_boundary = boundary["diagnostics_boundary"]
    assert diagnostics_boundary["generate_diagnostics_authority"] is False
    assert diagnostics_boundary["rewrite_voice_identity_diagnostics"] is False
    assert diagnostics_boundary["calculate_health_status"] is False
    assert diagnostics_boundary["calculate_readiness"] is False
    assert diagnostics_boundary["generate_repair_hints"] is False
    explainability_boundary = boundary["explainability_boundary"]
    assert explainability_boundary["generate_explainability_authority"] is False
    assert explainability_boundary["replace_voice_identity_provenance"] is False
    assert explainability_boundary["create_explainability_lineage"] is False
    assert explainability_boundary["infer_identity_state"] is False


async def test_ec416_monitoring_degraded_path_preserves_validation_only_authority(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """EC416: degraded monitoring path must refuse deterministically without authority bypass."""
    area = ar.async_get(hass).async_create(name="Office")
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(
        area_id=area.id,
        room_sensor_entity_ids=[],
    )

    result = await hass.services.async_call(
        DOMAIN,
        "get_summary",
        {
            "area_id": area.id,
            "monitoring_capability": "temperature",
        },
        blocking=True,
        return_response=True,
    )

    monitoring = result["monitoring_follow_up"]
    assert monitoring["refusal_reason"] == "configured_capability_mapping_missing"
    assert monitoring["refusal_category"] == "capability_unavailable"
    assert monitoring["runtime_discovery_reliance"] == "validation_only"
    assert monitoring["room_authority_source"] == "room_configuration"

    assert result["execution_outcome_category"] == "REFUSAL_SUCCESS"
    assert result["response_required"] is True
    assert result["response_generated"] is True
