"""Tests for Concierge contract-first services."""

from __future__ import annotations

import pytest

from homeassistant.core import Event
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import floor_registry as fr
from homeassistant.core import HomeAssistant

from custom_components.concierge.const import DOMAIN, EVENT_EXECUTION
from custom_components.concierge.models import PersonProfile
from custom_components.concierge.storage import ConciergeStorage


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
    assert state.default_person_profile is not None
    assert state.default_person_profile.person_id == "tom"


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
