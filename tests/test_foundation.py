"""Tests for Concierge state storage and coordinator summary."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar

from custom_components.concierge.const import DOMAIN
from custom_components.concierge.models import ContextState, IdentityProfile, Interaction, PersonProfile, SignalState, VoiceProfile
from custom_components.concierge.storage import ConciergeStorage


async def test_foundation_defaults_created(hass: HomeAssistant) -> None:
    """Storage should create deterministic empty state on first load."""
    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()

    assert state.rooms == {}
    assert state.composites == {}
    assert state.signals == {}
    assert state.contexts == {}
    assert state.interactions == {}


async def test_foundation_summary_available_in_coordinator(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Coordinator should expose persisted state summary in runtime data."""
    area = ar.async_get(hass).async_create(name="Great Room")
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(
        area_id=area.id,
        aliases={"movie time": "scene.movie_mode"},
        global_overlays={"weather": True},
    )
    await storage.async_upsert_interaction(
        Interaction(
            interaction_id="i-1",
            area_id=area.id,
            message="Door left open",
            level="attention",
            state="active",
            priority=60,
        )
    )
    await storage.async_upsert_signal(
        SignalState(
            signal_type="laundry",
            available=True,
            summary="Laundry complete",
            state="active",
        )
    )
    await storage.async_upsert_context(
        ContextState(
            context_type="weather",
            available=True,
            summary="Sunny",
            detail="Warm afternoon",
            speakable="It is sunny.",
        )
    )

    entry = setup_integration
    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_request_refresh()

    summary = coordinator.data["foundation_summary"]
    assert summary["room_identity_source"] == "home_assistant_area_registry"
    assert summary["concierge_role"] == "bounded_consumer_orchestrator"
    boundary = summary["capability_projection_boundary"]
    assert boundary["projection_role"] == "governed_projection_consumer"
    assert boundary["projection_is_authority"] is False
    assert boundary["deferred_release_2_owners"]["authoritative_input_consumption"] == "#314"
    assert boundary["deferred_release_2_owners"]["capability_discovery"] == "#317"
    continuity_boundary = summary["continuity_governance_boundary"]
    assert continuity_boundary["continuity_role"] == "governed_continuity_consumer"
    assert continuity_boundary["continuity_is_authority"] is False
    assert continuity_boundary["privacy_boundary_preserved"] is True
    assert continuity_boundary["continuity_diagnostics_explainability_enabled"] is True
    assert continuity_boundary["deferred_release_3_owners"]["person_room_affinity_boundary"] == "#326"
    assert continuity_boundary["deferred_release_3_owners"]["continuity_affinity_diagnostics_explainability"] == "#328"
    affinity_boundary = summary["person_room_affinity_boundary"]
    assert affinity_boundary["affinity_role"] == "governed_person_room_affinity_consumer"
    assert affinity_boundary["affinity_is_authority"] is False
    assert affinity_boundary["guest_safe_boundary_preserved"] is True
    assert affinity_boundary["privacy_boundary_preserved"] is True
    assert affinity_boundary["affinity_diagnostics_explainability_enabled"] is True
    assert affinity_boundary["deferred_release_3_owners"]["privacy_household_memory_boundary"] == "#327"
    assert affinity_boundary["deferred_release_3_owners"]["continuity_affinity_diagnostics_explainability"] == "#328"
    memory_boundary = summary["privacy_household_memory_boundary"]
    assert memory_boundary["privacy_memory_role"] == "governed_privacy_household_memory_consumer"
    assert memory_boundary["privacy_memory_is_authority"] is False
    assert memory_boundary["guest_safe_boundary_preserved"] is True
    assert memory_boundary["deferred_release_3_owners"]["continuity_affinity_diagnostics_explainability"] == "#328"
    messaging_boundary = summary["messaging_governance_boundary"]
    assert messaging_boundary["messaging_boundary_version"] == 1
    assert messaging_boundary["boundary_path"] == "governed_messaging_boundary"
    assert messaging_boundary["messaging_authority_external"] is True
    assert messaging_boundary["message_authority_external"] is True
    assert messaging_boundary["provenance_authority_external"] is True
    assert messaging_boundary["household_memory_authority_external"] is True
    assert messaging_boundary["message_creation_governed"] is True
    assert messaging_boundary["message_lifecycle_governed"] is True
    assert messaging_boundary["authority_protection"]["messaging_owns_truth"] is False
    assert messaging_boundary["authority_protection"]["messaging_owns_provenance"] is False
    assert messaging_boundary["authority_protection"]["messaging_owns_memory"] is False
    assert messaging_boundary["authority_protection"]["messaging_owns_identity"] is False
    assert messaging_boundary["deferred_release_4_owners"]["messaging_provenance"] == "#340"
    assert messaging_boundary["deferred_release_4_owners"]["messaging_diagnostics_explainability"] == "#343"
    occupancy_boundary = summary["occupancy_governance_boundary"]
    assert occupancy_boundary["occupancy_role"] == "governed_occupancy_boundary_consumer"
    assert occupancy_boundary["occupancy_is_authority"] is False
    assert occupancy_boundary["occupancy_authority_external"] is True
    assert occupancy_boundary["occupancy_policy_authority_external"] is True
    assert occupancy_boundary["occupancy_truth_authority_external"] is True
    assert occupancy_boundary["guest_safe_boundary_preserved"] is True
    assert occupancy_boundary["privacy_boundary_preserved"] is True
    assert occupancy_boundary["occupancy_decision_behavior_enabled"] is False
    assert occupancy_boundary["occupancy_execution_enabled"] is False
    assert occupancy_boundary["occupancy_inference_enabled"] is False
    assert occupancy_boundary["occupancy_diagnostics_behavior_enabled"] is False
    assert occupancy_boundary["deferred_release_3_owners"]["presence_governance_boundary"] == "#334"
    assert occupancy_boundary["deferred_release_3_owners"]["occupancy_presence_diagnostics_explainability"] == "#337"
    presence_boundary = summary["presence_governance_boundary"]
    assert presence_boundary["presence_role"] == "governed_presence_boundary_consumer"
    assert presence_boundary["presence_is_authority"] is False
    assert presence_boundary["presence_authority_external"] is True
    assert presence_boundary["presence_policy_authority_external"] is True
    assert presence_boundary["presence_truth_authority_external"] is True
    assert presence_boundary["guest_safe_boundary_preserved"] is True
    assert presence_boundary["privacy_boundary_preserved"] is True
    assert presence_boundary["presence_detection_enabled"] is False
    assert presence_boundary["presence_inference_enabled"] is False
    assert presence_boundary["presence_attribution_enabled"] is True
    assert presence_boundary["presence_behavior_enabled"] is False
    assert presence_boundary["presence_diagnostics_behavior_enabled"] is False
    assert presence_boundary["deferred_release_3_owners"]["guest_unknown_occupant_behavior"] == "#335"
    assert presence_boundary["deferred_release_3_owners"]["occupancy_presence_diagnostics_explainability"] == "#337"
    guest_unknown_behavior = summary["guest_unknown_occupant_behavior"]
    assert (
        guest_unknown_behavior["guest_unknown_behavior_role"]
        == "governed_guest_unknown_occupant_behavior_consumer"
    )
    assert guest_unknown_behavior["guest_unknown_behavior_is_authority"] is False
    assert guest_unknown_behavior["consumes_occupancy_governance_boundary"] is True
    assert guest_unknown_behavior["consumes_presence_governance_boundary"] is True
    assert guest_unknown_behavior["occupancy_authority_external"] is True
    assert guest_unknown_behavior["presence_authority_external"] is True
    assert guest_unknown_behavior["identity_authority_external"] is True
    assert guest_unknown_behavior["household_memory_authority_external"] is True
    assert guest_unknown_behavior["guest_safe_boundary_preserved"] is True
    assert guest_unknown_behavior["privacy_boundary_preserved"] is True
    assert guest_unknown_behavior["identity_attribution_enabled"] is True
    assert guest_unknown_behavior["occupancy_truth_modification_enabled"] is False
    assert guest_unknown_behavior["presence_truth_modification_enabled"] is False
    assert guest_unknown_behavior["behavior_enabled"] is True
    assert guest_unknown_behavior["deferred_release_3_owners"]["multi_occupant_behavior"] == "#336"
    assert (
        guest_unknown_behavior["deferred_release_3_owners"]["occupancy_presence_diagnostics_explainability"]
        == "#337"
    )
    multi_occupant_behavior = summary["multi_occupant_behavior"]
    assert (
        multi_occupant_behavior["multi_occupant_behavior_role"]
        == "governed_multi_occupant_behavior_consumer"
    )
    assert multi_occupant_behavior["multi_occupant_behavior_is_authority"] is False
    assert multi_occupant_behavior["consumes_occupancy_governance_boundary"] is True
    assert multi_occupant_behavior["consumes_presence_governance_boundary"] is True
    assert multi_occupant_behavior["consumes_guest_unknown_behavior"] is True
    assert multi_occupant_behavior["occupancy_authority_external"] is True
    assert multi_occupant_behavior["presence_authority_external"] is True
    assert multi_occupant_behavior["identity_authority_external"] is True
    assert multi_occupant_behavior["household_memory_authority_external"] is True
    assert multi_occupant_behavior["guest_safe_boundary_preserved"] is True
    assert multi_occupant_behavior["privacy_boundary_preserved"] is True
    assert multi_occupant_behavior["identity_attribution_enabled"] is True
    assert multi_occupant_behavior["occupancy_truth_modification_enabled"] is False
    assert multi_occupant_behavior["presence_truth_modification_enabled"] is False
    assert multi_occupant_behavior["conflict_visibility_enabled"] is True
    assert multi_occupant_behavior["behavior_enabled"] is True
    assert multi_occupant_behavior["deferred_release_3_owners"]["occupancy_presence_diagnostics_explainability"] == "#337"
    restoration_boundary = summary["restoration_governance_boundary"]
    assert restoration_boundary["restoration_role"] == "governed_restoration_boundary_consumer"
    assert restoration_boundary["restoration_is_authority"] is False
    assert restoration_boundary["restoration_authority_external"] is True
    assert restoration_boundary["restoration_policy_authority_external"] is True
    assert restoration_boundary["restoration_execution_enabled"] is True
    assert restoration_boundary["restoration_decision_behavior_enabled"] is True
    assert restoration_boundary["e3a_preservation_alignment_enabled"] is True
    assert restoration_boundary["restoration_diagnostics_behavior_enabled"] is True
    assert restoration_boundary["deferred_release_3_owners"]["restoration_outcome_implementation"] == "#330"
    assert restoration_boundary["deferred_release_3_owners"]["e3a_preservation_alignment"] == "#331"
    assert restoration_boundary["deferred_release_3_owners"]["restoration_diagnostics_explainability"] == "#332"
    assert summary["foundation_area_count"] == 1
    assert summary["room_count"] == 1
    assert summary["composite_count"] == 0
    assert summary["interaction_count"] == 1
    assert summary["signal_count"] == 1
    assert summary["context_source_count"] == 1
    assert summary["configured_room_outside_foundation_count"] == 0
    assert summary["composites_with_missing_area_count"] == 0
    assert summary["active_person_resolution_enabled"] is True
    assert summary["active_person_state"] == "active_person_unavailable"
    assert summary["active_person_reason_code"] == "no_execution_envelope"
    assert summary["active_person_available"] is False
    assert coordinator.data["active_person_resolution"]["active_person_state"] == "active_person_unavailable"
    assert coordinator.data["active_person_resolution"]["fail_closed"] is True


async def test_room_and_identity_state_round_trip(hass: HomeAssistant) -> None:
    """State storage should persist room posture, people, voice, and presentation profiles."""
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(
        area_id="great_room",
        posture="sleep",
        media_player_entity_ids=["media_player.great_room"],
        tts_voice="sage",
    )
    await storage.async_update_identity_profile(
        IdentityProfile(
            profile_id="default",
            name="Default",
            persona="concise",
            tts_voice="alloy",
            verbosity="standard",
            allow_ai=True,
            content_type="general",
            detail_level="medium",
        ),
        set_as_default=True,
    )
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="tom",
            name="Tom",
            linked_area_id="great_room",
            ble_device_ids=["ble.tom_tag"],
            aqara_presence_entity_ids=["binary_sensor.tom_presence"],
            voice_profile_id="tom_voice",
            consent={"person_identity": True},
            notes="Primary person profile",
        ),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            tts_voice="alloy",
            enrollment_state="trained",
            enrollment_source="local",
            speaker_embedding_id="embedding-1",
            sample_count=4,
            consent={"voice_training": True},
        ),
        set_as_default=True,
    )

    state = await storage.async_load_state()
    assert state.rooms["great_room"].posture == "sleep"
    assert state.rooms["great_room"].media_player_entity_ids == ["media_player.great_room"]
    assert state.default_identity_profile is not None
    assert state.default_identity_profile.tts_voice == "alloy"
    assert state.default_person_profile is not None
    assert state.default_person_profile.voice_profile_id == "tom_voice"
    assert state.default_voice_profile is not None
    assert state.default_voice_profile.sample_count == 4


async def test_coordinator_resolves_active_person_available_from_voice_identity_consumption(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Coordinator should resolve active person from consumed Voice Identity outcomes."""
    await hass.services.async_call(
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
                    "confidence": 0.92,
                    "confidence_band": "high",
                    "reason_code": "attribution_ready",
                    "source": "voice_identity",
                }
            },
        },
        blocking=True,
        return_response=True,
    )

    coordinator = hass.data[DOMAIN][setup_integration.entry_id]
    await coordinator.async_request_refresh()
    resolution = coordinator.data["active_person_resolution"]

    assert resolution["active_person_state"] == "active_person_available"
    assert resolution["active_person_available"] is True
    assert resolution["resolved_person_id"] == "person.tom"
    assert resolution["resolved_voice_profile_id"] == "vp_tom"
    assert resolution["confidence_available"] is True
    assert resolution["confidence_accepted"] is True
    assert resolution["fail_closed"] is False


async def test_coordinator_resolves_active_person_unknown_when_identity_is_unknown(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Coordinator should resolve unknown active-person state without guessing identity."""
    await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "identity_context": {
                    "state": "unknown",
                    "confidence": 0.0,
                    "confidence_band": "unknown",
                    "reason_code": "identity_unknown",
                    "source": "voice_identity",
                }
            },
        },
        blocking=True,
        return_response=True,
    )

    coordinator = hass.data[DOMAIN][setup_integration.entry_id]
    await coordinator.async_request_refresh()
    resolution = coordinator.data["active_person_resolution"]

    assert resolution["active_person_state"] == "active_person_unknown"
    assert resolution["active_person_available"] is False
    assert resolution["resolved_person_id"] is None
    assert resolution["fail_closed"] is True


async def test_coordinator_resolves_active_person_ambiguous_for_low_confidence(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Coordinator should resolve ambiguous active-person state for low-confidence attribution."""
    await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "identity_context": {
                    "state": "low_confidence",
                    "confidence": 0.41,
                    "confidence_band": "low",
                    "reason_code": "low_confidence",
                    "source": "voice_identity",
                }
            },
        },
        blocking=True,
        return_response=True,
    )

    coordinator = hass.data[DOMAIN][setup_integration.entry_id]
    await coordinator.async_request_refresh()
    resolution = coordinator.data["active_person_resolution"]

    assert resolution["active_person_state"] == "active_person_ambiguous"
    assert resolution["active_person_available"] is False
    assert resolution["confidence_available"] is True
    assert resolution["confidence_accepted"] is False
    assert resolution["fail_closed"] is True


async def test_coordinator_resolves_active_person_unavailable_when_voice_identity_unavailable(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Coordinator should resolve unavailable active-person state when Voice Identity runtime is unavailable."""
    if hass.services.has_service("voice_identity", "attribute_speaker"):
        hass.services.async_remove("voice_identity", "attribute_speaker")
    if hass.services.has_service("voice_identity", "get_identity_context"):
        hass.services.async_remove("voice_identity", "get_identity_context")

    await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "intent_class": "home_control",
            "context": {
                "audio_ref": "media://voice/runtime-sample-issue381.wav",
            },
        },
        blocking=True,
        return_response=True,
    )

    coordinator = hass.data[DOMAIN][setup_integration.entry_id]
    await coordinator.async_request_refresh()
    resolution = coordinator.data["active_person_resolution"]

    assert resolution["active_person_state"] == "active_person_unavailable"
    assert resolution["active_person_available"] is False
    assert resolution["reason_code"] == "attribution_service_unavailable"
    assert resolution["fail_closed"] is True


async def test_coordinator_nightly_archive_records_activity_lifecycle(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Coordinator nightly archive job should emit backend activity lifecycle records."""
    entry = setup_integration
    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator._async_handle_nightly_archive()

    state = await ConciergeStorage(hass).async_load_state()
    nightly = [
        activity
        for activity in state.activities.values()
        if activity.intent_class == "coordinator_nightly_archive"
    ]
    assert nightly
    latest = sorted(nightly, key=lambda item: item.started_at)[-1]
    assert latest.actor_class == "concierge_coordinator"
    assert latest.channel == "coordinator_job"
    assert latest.outcome == "success"
    assert latest.actions_taken
