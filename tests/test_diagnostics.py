"""Diagnostics tests for Concierge."""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar

from custom_components.concierge.const import DOMAIN
from custom_components.concierge.const import CONF_VOICE_IDENTITY_LINKED
from custom_components.concierge.diagnostics import async_get_config_entry_diagnostics
from custom_components.concierge.models import ContextState, Interaction, PersonProfile
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
    hass.config_entries.async_update_entry(
        setup_integration,
        options={
            **dict(setup_integration.options),
            CONF_VOICE_IDENTITY_LINKED: False,
        },
    )
    area = ar.async_get(hass).async_create(name="Great Room")
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(
        area_id=area.id,
        aliases={"movie time": "scene.movie_mode"},
        global_overlays={"weather": True},
    )
    await storage.async_upsert_interaction(
        Interaction(
            interaction_id="interaction-1",
            area_id=area.id,
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
        "foundation_runtime_boundary",
        "context_assembly_visibility",
        "execution_explainability",
        "vocabulary_diagnostics_visibility",
        "capability_diagnostics_explainability_visibility",
        "experience_diagnostics_explainability_visibility",
        "productivity_source_of_record_boundary_visibility",
        "calendar_email_consumption_boundary_visibility",
        "task_shopping_consumption_boundary_visibility",
        "capture_knowledge_consumption_boundary_visibility",
        "briefing_composition_boundary_visibility",
        "household_status_synthesis_boundary_visibility",
        "household_coordination_boundary_visibility",
        "productivity_coordination_boundary_visibility",
        "provenance_ownership_consumption_boundary_visibility",
        "release_6_provenance_diagnostics_explainability_visibility",
        "voice_identity_consumption_boundary_visibility",
        "messaging_governance_boundary_visibility",
        "messaging_provenance_visibility",
        "notification_delivery_boundary_visibility",
        "recipient_consent_privacy_visibility_boundary_visibility",
        "messaging_diagnostics_explainability_visibility",
        "household_memory_governance_boundary_visibility",
        "household_memory_ownership_consumption_boundary_visibility",
        "household_memory_identity_privacy_retention_separation_visibility",
        "household_memory_messaging_continuity_affinity_occupancy_restoration_separation_visibility",
        "household_memory_provenance_diagnostics_explainability_visibility",
        "continuity_affinity_diagnostics_explainability_visibility",
        "occupancy_presence_diagnostics_explainability_visibility",
        "restoration_diagnostics_explainability_visibility",
        "preservation_baseline",
        "enrollment_activity_summary",
        "completion_activity_summary",
        "cleanup_activity_summary",
        "reconciliation_activity_summary",
        "capture_provider_activity_summary",
        "retention_policy",
        "voice_identity_linkage_setup_boundary_visibility",
        "release_6_productivity_diagnostics_visibility",
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
    assert diagnostics["foundation_runtime_boundary"]["room_identity_source"] == "home_assistant_area_registry"
    assert diagnostics["foundation_runtime_boundary"]["concierge_role"] == "bounded_consumer_orchestrator"
    assert diagnostics["foundation_runtime_boundary"]["foundation_area_count"] == 1
    assert diagnostics["foundation_runtime_boundary"]["configured_room_count"] == 1
    assert diagnostics["foundation_runtime_boundary"]["configured_room_outside_foundation_count"] == 0
    assert diagnostics["foundation_runtime_boundary"]["room_configs_bound_to_foundation"] is True
    assert diagnostics["foundation_runtime_boundary"]["composites_bound_to_foundation"] is True
    assert diagnostics["context_assembly_visibility"]["configured_room_projection_count"] == 1
    assert diagnostics["context_assembly_visibility"]["enabled_composite_projection_count"] == 0
    assert diagnostics["context_assembly_visibility"]["active_context_types"] == ["weather"]
    assert diagnostics["context_assembly_visibility"]["room_projection_samples"][0]["context_source_count"] == 1
    assert diagnostics["execution_explainability"]["orchestration_activity_count"] == 0
    assert diagnostics["execution_explainability"]["latest_orchestration"] is None
    assert diagnostics["vocabulary_diagnostics_visibility"]["authority_visibility"]["room_vocabulary_authority"] == "room_vocabulary_registry"
    assert diagnostics["vocabulary_diagnostics_visibility"]["authority_visibility"]["device_entity_vocabulary_authority"] == "device_entity_vocabulary_registry"
    assert diagnostics["vocabulary_diagnostics_visibility"]["authority_visibility"]["asset_handoff_authority"] == "asset_intelligence_handoff"
    assert diagnostics["vocabulary_diagnostics_visibility"]["authority_visibility"]["concierge_role"] == "bounded_consumer_orchestrator"
    assert diagnostics["vocabulary_diagnostics_visibility"]["asset_intelligence_boundary"]["asset_evaluation_logic_visible"] is False
    assert diagnostics["vocabulary_diagnostics_visibility"]["asset_intelligence_boundary"]["asset_scoring_visible"] is False
    assert diagnostics["vocabulary_diagnostics_visibility"]["asset_intelligence_boundary"]["asset_significance_logic_visible"] is False
    assert diagnostics["vocabulary_diagnostics_visibility"]["asset_intelligence_boundary"]["asset_advisory_reasoning_visible"] is False
    capability_diag = diagnostics["capability_diagnostics_explainability_visibility"]
    assert capability_diag["authority_visibility"]["capability_authority_origin"] == "htbw_governed_contracts_and_models"
    assert capability_diag["authority_visibility"]["vocabulary_authority_external"] is True
    assert capability_diag["authority_visibility"]["asset_intelligence_authority_external"] is True
    assert capability_diag["diagnostics_non_rights"]["creates_authority"] is False
    assert capability_diag["diagnostics_non_rights"]["creates_outcomes"] is False
    assert capability_diag["diagnostics_non_rights"]["recreates_capability_reasoning"] is False
    assert capability_diag["diagnostics_non_rights"]["recreates_asset_intelligence_reasoning"] is False
    experience_diag = diagnostics["experience_diagnostics_explainability_visibility"]
    assert experience_diag["authority_visibility"]["capability_authority_origin"] == "htbw_governed_contracts_and_models"
    assert experience_diag["authority_visibility"]["vocabulary_authority_external"] is True
    assert experience_diag["authority_visibility"]["asset_intelligence_authority_external"] is True
    assert experience_diag["authority_visibility"]["experience_authority_external"] is True
    assert experience_diag["diagnostics_non_rights"]["creates_authority"] is False
    assert experience_diag["diagnostics_non_rights"]["creates_outcomes"] is False
    assert experience_diag["diagnostics_non_rights"]["recreates_projection_reasoning"] is False
    assert experience_diag["diagnostics_non_rights"]["recreates_restoration_reasoning"] is False
    productivity_diag = diagnostics["productivity_source_of_record_boundary_visibility"]
    assert productivity_diag["applicable"] is True
    assert productivity_diag["boundary_path"] == "governed_productivity_source_of_record_boundary"
    assert productivity_diag["configured_source_reference_count"] == 0
    assert productivity_diag["domain_boundaries"]["calendar"]["source_of_record"] == "configured_calendar_provider"
    assert productivity_diag["domain_boundaries"]["calendar"]["configured_reference_present"] is False
    assert productivity_diag["domain_boundaries"]["email"]["source_of_record_external"] is True
    assert productivity_diag["domain_boundaries"]["briefing"]["derived_context_only"] is True
    assert productivity_diag["provenance_requirements"]["provenance_authority_external"] is True
    assert productivity_diag["provenance_requirements"]["provenance_duplication_permitted"] is False
    assert productivity_diag["diagnostics_visibility"]["sensitive_source_content_exposed"] is False
    assert productivity_diag["non_authority_assertions"]["creates_source_of_record"] is False
    assert productivity_diag["non_authority_assertions"]["claims_calendar_authority"] is False
    bindings = productivity_diag["person_productivity_source_bindings"]
    assert bindings["required_domains"] == ["email", "calendar", "task", "shopping"]
    assert bindings["person_count"] == 0
    assert bindings["safe_fallback_person_count"] == 0
    productivity_routing = productivity_diag["person_aware_productivity_routing"]
    assert productivity_routing["routing_enabled"] is False
    assert productivity_routing["reason_code"] == "no_execution_envelope"
    assert productivity_routing["active_person_state"] == "active_person_unavailable"
    assert not _contains_key(productivity_diag, "email_contents")
    assert not _contains_key(productivity_diag, "calendar_event_details")
    assert not _contains_key(productivity_diag, "task_contents")
    assert not _contains_key(productivity_diag, "shopping_item_contents")
    calendar_email_diag = diagnostics["calendar_email_consumption_boundary_visibility"]
    assert calendar_email_diag["applicable"] is True
    assert calendar_email_diag["boundary_path"] == "governed_calendar_email_consumption_boundary"
    assert calendar_email_diag["configured_source_reference_count"] == 0
    assert calendar_email_diag["domain_boundaries"]["calendar"]["source_of_record"] == "configured_calendar_provider"
    assert calendar_email_diag["domain_boundaries"]["email"]["source_of_record"] == "configured_email_provider"
    assert calendar_email_diag["diagnostics_visibility"]["sensitive_source_content_exposed"] is False
    assert calendar_email_diag["non_authority_assertions"]["claims_calendar_authority"] is False
    assert calendar_email_diag["non_authority_assertions"]["claims_email_authority"] is False
    assert calendar_email_diag["person_aware_routing"]["routing_enabled"] is False
    assert calendar_email_diag["person_aware_routing"]["reason_code"] == "no_execution_envelope"
    assert not _contains_key(calendar_email_diag, "email_contents")
    assert not _contains_key(calendar_email_diag, "calendar_event_details")
    task_shopping_diag = diagnostics["task_shopping_consumption_boundary_visibility"]
    assert task_shopping_diag["applicable"] is True
    assert task_shopping_diag["boundary_path"] == "governed_task_shopping_consumption_boundary"
    assert task_shopping_diag["configured_source_reference_count"] == 1
    assert task_shopping_diag["task_reference_kinds"] == [
        "ownership_references",
        "assignment_references",
        "completion_references",
        "due_awareness_references",
        "provenance_references",
    ]
    assert task_shopping_diag["shopping_reference_kinds"] == [
        "shopping_item_references",
        "ownership_references",
        "duplicate_indicators",
        "completion_references",
        "provenance_references",
        "shopping_explainability_references",
    ]
    assert task_shopping_diag["clarification_behavior"]["supported"] is True
    assert task_shopping_diag["clarification_behavior"]["ambiguity_visible"] is True
    assert task_shopping_diag["clarification_behavior"]["hidden_intent_inference"] is False
    assert task_shopping_diag["task_reference_boundaries"]["task"]["reference_only_model"] is True
    assert task_shopping_diag["task_reference_boundaries"]["task"]["source_of_record_external"] is True
    assert task_shopping_diag["person_shopping_bindings"]["required_domains"] == ["shopping"]
    assert task_shopping_diag["person_shopping_bindings"]["person_count"] == 1
    assert task_shopping_diag["person_shopping_bindings"]["configured_reference_present"]["shopping"] is True
    assert task_shopping_diag["person_shopping_bindings"]["safe_fallback_person_count"] == 0
    assert task_shopping_diag["person_aware_routing"]["routing_enabled"] is False
    assert task_shopping_diag["person_aware_routing"]["reason_code"] == "no_execution_envelope"
    assert task_shopping_diag["non_authority_assertions"]["claims_task_authority"] is False
    assert task_shopping_diag["non_authority_assertions"]["claims_shopping_authority"] is False
    assert not _contains_key(task_shopping_diag, "task_contents")
    assert not _contains_key(task_shopping_diag, "shopping_item_contents")
    capture_knowledge_diag = diagnostics["capture_knowledge_consumption_boundary_visibility"]
    assert capture_knowledge_diag["applicable"] is True
    assert capture_knowledge_diag["boundary_path"] == "governed_capture_knowledge_consumption_boundary"
    assert capture_knowledge_diag["configured_source_reference_count"] == 0
    assert capture_knowledge_diag["knowledge_consumption"]["knowledge_available"] is False
    assert capture_knowledge_diag["knowledge_consumption"]["safe_fallback_mode_active"] is True
    assert capture_knowledge_diag["capture_consumption"]["capture_available"] is False
    assert capture_knowledge_diag["capture_consumption"]["safe_fallback_mode_active"] is True
    assert capture_knowledge_diag["provenance_visibility"]["provenance_reference_present"] is False
    assert capture_knowledge_diag["clarification_behavior"]["supported"] is True
    assert capture_knowledge_diag["clarification_behavior"]["ambiguity_visible"] is True
    assert capture_knowledge_diag["domain_boundaries"]["knowledge"]["source_of_record"] == "configured_knowledge_provider"
    assert capture_knowledge_diag["domain_boundaries"]["capture"]["source_of_record"] == "configured_capture_provider"
    assert capture_knowledge_diag["non_authority_assertions"]["claims_capture_authority"] is False
    assert capture_knowledge_diag["non_authority_assertions"]["claims_knowledge_authority"] is False
    assert not _contains_key(capture_knowledge_diag, "knowledge_sources")
    assert not _contains_key(capture_knowledge_diag, "capture_contents")

    briefing_diag = diagnostics["briefing_composition_boundary_visibility"]
    assert briefing_diag["applicable"] is True
    assert briefing_diag["boundary_path"] == "governed_briefing_composition_boundary"
    assert briefing_diag["briefing_available"] is False
    assert briefing_diag["briefing_composition"]["briefing_composition_state"] == "restricted"
    assert briefing_diag["safe_fallback_mode_active"] is True
    assert briefing_diag["provenance_visibility"]["provenance_visible"] is False
    assert briefing_diag["explainability_visibility"]["briefing_explainability_supported"] is True
    assert briefing_diag["non_authority_assertions"]["claims_briefing_authority"] is False
    assert briefing_diag["non_authority_assertions"]["claims_household_status_authority"] is False
    assert not _contains_key(briefing_diag, "briefing_text")
    assert not _contains_key(briefing_diag, "summary_text")

    household_status_diag = diagnostics["household_status_synthesis_boundary_visibility"]
    assert household_status_diag["applicable"] is True
    assert household_status_diag["boundary_path"] == "governed_household_status_synthesis_boundary"
    assert household_status_diag["household_status_available"] is False
    assert household_status_diag["coordination_snapshot"]["coordination_snapshot_state"] == "simplified"
    assert household_status_diag["safe_fallback_mode_active"] is True
    assert household_status_diag["provenance_visibility"]["provenance_visible"] is False
    assert household_status_diag["explainability_visibility"]["household_status_explainability_supported"] is True
    assert household_status_diag["open_loop_coordination_visibility"]["open_loop_supported"] is True
    assert household_status_diag["open_loop_coordination_visibility"]["informational_only"] is True
    assert household_status_diag["open_loop_coordination_visibility"]["coordination_authority_external"] is True
    assert household_status_diag["non_authority_assertions"]["claims_household_status_authority"] is False
    assert household_status_diag["non_authority_assertions"]["creates_planning_engine"] is False
    assert not _contains_key(household_status_diag, "status_text")
    assert not _contains_key(household_status_diag, "coordination_plan")

    household_coordination_diag = diagnostics["household_coordination_boundary_visibility"]
    assert household_coordination_diag["applicable"] is True
    assert household_coordination_diag["boundary_path"] == "governed_household_coordination_boundary"
    assert household_coordination_diag["coordination_source"] == "governed_release_6_consumption_boundaries"
    assert household_coordination_diag["consumption_only"] is True
    assert household_coordination_diag["open_loop_coordination_visibility"]["open_loop_supported"] is True
    assert household_coordination_diag["open_loop_coordination_visibility"]["informational_only"] is True
    assert household_coordination_diag["open_loop_coordination_visibility"]["coordination_authority_external"] is True
    assert household_coordination_diag["non_authority_assertions"]["claims_coordination_authority"] is False
    assert household_coordination_diag["non_authority_assertions"]["claims_provenance_authority"] is False
    assert not _contains_key(household_coordination_diag, "mailbox_contents")
    assert not _contains_key(household_coordination_diag, "calendar_entries")

    productivity_coordination_diag = diagnostics["productivity_coordination_boundary_visibility"]
    assert productivity_coordination_diag["applicable"] is True
    assert productivity_coordination_diag["boundary_path"] == "governed_productivity_coordination_boundary"
    assert productivity_coordination_diag["consumption_only"] is True
    assert productivity_coordination_diag["informational_only"] is True
    assert productivity_coordination_diag["coordination_awareness"]["cross_domain_coordination_supported"] is True
    assert productivity_coordination_diag["diagnostics_visibility"]["safe_source_metadata_only"] is True
    assert productivity_coordination_diag["non_authority_assertions"]["claims_productivity_authority"] is False
    assert not _contains_key(productivity_coordination_diag, "mailbox_contents")
    assert not _contains_key(productivity_coordination_diag, "calendar_entries")

    provenance_ownership_diag = diagnostics["provenance_ownership_consumption_boundary_visibility"]
    assert provenance_ownership_diag["applicable"] is True
    assert provenance_ownership_diag["boundary_path"] == "governed_release_6_provenance_ownership_consumption_boundary"
    assert provenance_ownership_diag["provenance_visibility"]["provenance_visible"] is True
    assert provenance_ownership_diag["explainability_visibility"]["safe_fallback_visible"] is True
    assert provenance_ownership_diag["readiness_assessment"]["lineage_completeness_ready"] is False
    assert provenance_ownership_diag["safe_fallback_mode_active"] is True
    assert provenance_ownership_diag["non_authority_assertions"]["claims_ownership_authority"] is False
    assert provenance_ownership_diag["non_authority_assertions"]["claims_provenance_authority"] is False

    provenance_diag_explainability = diagnostics[
        "release_6_provenance_diagnostics_explainability_visibility"
    ]
    assert provenance_diag_explainability["applicable"] is True
    assert (
        provenance_diag_explainability["boundary_path"]
        == "governed_release_6_provenance_diagnostics_explainability_boundary"
    )
    assert provenance_diag_explainability["consumption_only"] is True
    assert provenance_diag_explainability["informational_only"] is True
    assert provenance_diag_explainability["diagnostics_visibility"]["safe_source_metadata_only"] is True
    assert provenance_diag_explainability["explainability_visibility"]["provenance_inputs_visible"] is True
    assert provenance_diag_explainability["non_authority_assertions"]["claims_provenance_authority"] is False
    assert provenance_diag_explainability["non_authority_assertions"]["claims_lineage_authority"] is False
    assert not _contains_key(provenance_diag_explainability, "mailbox_contents")
    assert not _contains_key(provenance_diag_explainability, "calendar_entries")

    release_6_diag = diagnostics["release_6_productivity_diagnostics_visibility"]
    assert release_6_diag["applicable"] is True
    assert release_6_diag["boundary_path"] == "governed_release_6_productivity_diagnostics_boundary"
    assert release_6_diag["diagnostics_visibility"]["boundary_count"] == 10
    assert release_6_diag["diagnostics_visibility"]["available_boundary_count"] == 3
    assert release_6_diag["diagnostics_visibility"]["configured_source_reference_count"] == 0
    assert release_6_diag["diagnostics_visibility"]["safe_fallback_boundary_count"] == 10
    assert release_6_diag["provenance_visibility"]["provenance_reference_count"] >= 1
    assert release_6_diag["explainability_visibility"]["source_domain_visible_boundary_count"] == 10
    assert release_6_diag["explainability_visibility"]["safe_fallback_visible_boundary_count"] == 10
    assert release_6_diag["safe_fallback_visibility"]["missing_prerequisite_boundary_count"] == 10
    assert release_6_diag["non_authority_assertions"]["claims_diagnostics_authority"] is False
    assert release_6_diag["non_authority_assertions"]["claims_provenance_authority"] is False
    assert not _contains_key(release_6_diag, "mailbox_contents")
    assert not _contains_key(release_6_diag, "calendar_entries")
    voice_identity_linkage_diag = diagnostics["voice_identity_linkage_setup_boundary_visibility"]
    assert voice_identity_linkage_diag["linkage_configured"] is False
    assert voice_identity_linkage_diag["voice_identity_loaded"] is True
    assert voice_identity_linkage_diag["voice_identity_connected"] is False
    assert voice_identity_linkage_diag["voice_identity_available"] is False
    assert voice_identity_linkage_diag["voice_identity_compatible"] is False
    assert voice_identity_linkage_diag["voice_identity_discovery_state"] == "unavailable"
    assert voice_identity_linkage_diag["voice_identity_reason_code"] == "voice_identity_linkage_disabled"
    assert voice_identity_linkage_diag["safe_fallback_mode_active"] is True
    voice_identity_diag = diagnostics["voice_identity_consumption_boundary_visibility"]
    assert voice_identity_diag["authority_visibility"]["voice_identity_authority_external"] is False
    assert voice_identity_diag["consumption_visibility"]["execution_envelope_ref_count"] == 0
    assert voice_identity_diag["consumption_visibility"]["latest_attribution_consumed"] is False
    assert voice_identity_diag["consumption_visibility"]["latest_confidence_consumed"] is False
    active_person = voice_identity_diag["consumption_visibility"]["active_person_resolution"]
    assert active_person["active_person_state"] == "active_person_unavailable"
    assert active_person["active_person_available"] is False
    assert active_person["reason_code"] == "no_execution_envelope"
    assert active_person["fail_closed"] is True
    assert voice_identity_diag["enrollment_boundary_visibility"]["latest_enrollment_state_consumed"] is False
    assert voice_identity_diag["enrollment_boundary_visibility"]["latest_boundary_path"] is None
    assert voice_identity_diag["lifecycle_boundary_visibility"]["latest_lifecycle_state_consumed"] is False
    assert voice_identity_diag["permission_boundary_visibility"]["latest_permission_state_consumed"] is False
    assert voice_identity_diag["permission_boundary_visibility"]["latest_boundary_path"] is None
    assert voice_identity_diag["legacy_disposition_boundary_visibility"]["latest_legacy_disposition_consumed"] is False
    assert voice_identity_diag["legacy_disposition_boundary_visibility"]["latest_boundary_path"] is None
    assert voice_identity_diag["diagnostics_boundary_visibility"]["latest_diagnostics_consumed"] is False
    assert voice_identity_diag["diagnostics_boundary_visibility"]["latest_boundary_path"] is None
    assert voice_identity_diag["explainability_boundary_visibility"]["latest_explainability_consumed"] is False
    assert voice_identity_diag["explainability_boundary_visibility"]["latest_boundary_path"] is None
    assert voice_identity_diag["ownership_boundary_visibility"]["derives_attribution_authority"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["derives_confidence_authority"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["calculates_attribution"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["calculates_confidence"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["manages_identity_lifecycle"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["manages_enrollment"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["manages_enrollment_lifecycle"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["manages_voice_profile_lifecycle"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["creates_voice_profiles"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["changes_enrollment_state"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["infers_enrollment_state"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["derives_permission_authority"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["creates_permission_policy"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["defines_eligibility_rules"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["determines_permission_outcomes"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["grants_permission"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["revokes_permission"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["approves_consent"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["infers_consent"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["manages_legacy_fingerprint_resolution"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["migrates_legacy_identity_data"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["disposes_legacy_identity_data"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["determines_legacy_disposition"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["infers_legacy_disposition_state"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["generates_diagnostics_authority"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["rewrites_diagnostics"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["calculates_health_status"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["calculates_readiness"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["generates_repair_hints"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["generates_explainability_authority"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["replaces_provenance"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["creates_explainability_lineage"] is False
    continuity_affinity_diag = diagnostics["continuity_affinity_diagnostics_explainability_visibility"]
    assert continuity_affinity_diag["authority_visibility"]["continuity_authority_external"] is True
    assert continuity_affinity_diag["authority_visibility"]["person_room_affinity_authority_external"] is True
    assert continuity_affinity_diag["availability_explainability"]["continuity_available"] is False
    assert continuity_affinity_diag["availability_explainability"]["affinity_available"] is False
    assert continuity_affinity_diag["ownership_boundary_visibility"]["continuity_owns_identity"] is False
    assert continuity_affinity_diag["ownership_boundary_visibility"]["affinity_owns_room_truth"] is False
    assert continuity_affinity_diag["diagnostics_non_rights"]["creates_authority"] is False
    assert continuity_affinity_diag["diagnostics_non_rights"]["modifies_continuity_behavior"] is False
    assert continuity_affinity_diag["diagnostics_non_rights"]["modifies_affinity_behavior"] is False

    occupancy_presence_diag = diagnostics["occupancy_presence_diagnostics_explainability_visibility"]
    assert occupancy_presence_diag["authority_visibility"]["occupancy_authority_external"] is True
    assert occupancy_presence_diag["authority_visibility"]["presence_authority_external"] is True
    assert occupancy_presence_diag["authority_visibility"]["identity_authority_external"] is True
    assert occupancy_presence_diag["authority_visibility"]["room_truth_authority_external"] is True
    assert occupancy_presence_diag["authority_visibility"]["restoration_authority_external"] is False
    assert occupancy_presence_diag["governance_visibility"]["latest_occupancy_governance_applicable"] is False
    assert occupancy_presence_diag["governance_visibility"]["latest_occupancy_governance_path"] is None
    assert occupancy_presence_diag["governance_visibility"]["latest_occupancy_governance_unavailable_reason"] == "execution_envelope_not_available"
    assert occupancy_presence_diag["governance_visibility"]["latest_presence_governance_applicable"] is False
    assert occupancy_presence_diag["governance_visibility"]["latest_presence_governance_path"] is None
    assert occupancy_presence_diag["governance_visibility"]["latest_presence_governance_unavailable_reason"] == "execution_envelope_not_available"
    assert occupancy_presence_diag["governance_visibility"]["latest_orchestration_occupancy_governance_applicable"] is False
    assert occupancy_presence_diag["governance_visibility"]["latest_orchestration_occupancy_governance_path"] is None
    assert occupancy_presence_diag["governance_visibility"]["latest_orchestration_presence_governance_applicable"] is False
    assert occupancy_presence_diag["governance_visibility"]["latest_orchestration_presence_governance_path"] is None
    assert occupancy_presence_diag["governance_visibility"]["latest_direct_occupancy_governance_applicable"] is False
    assert occupancy_presence_diag["governance_visibility"]["latest_direct_occupancy_governance_path"] is None
    assert occupancy_presence_diag["governance_visibility"]["latest_direct_presence_governance_applicable"] is False
    assert occupancy_presence_diag["governance_visibility"]["latest_direct_presence_governance_path"] is None
    assert occupancy_presence_diag["behavior_visibility"]["latest_guest_unknown_behavior_applicable"] is False
    assert occupancy_presence_diag["behavior_visibility"]["latest_guest_unknown_behavior_path"] is None
    assert occupancy_presence_diag["behavior_visibility"]["latest_multi_occupant_behavior_applicable"] is False
    assert occupancy_presence_diag["behavior_visibility"]["latest_multi_occupant_behavior_path"] is None
    assert occupancy_presence_diag["ownership_boundary_visibility"]["occupancy_owns_room_truth"] is False
    assert occupancy_presence_diag["ownership_boundary_visibility"]["presence_owns_room_truth"] is False
    assert occupancy_presence_diag["ownership_boundary_visibility"]["restoration_authority_external"] is False
    assert occupancy_presence_diag["safeguard_visibility"]["guest_safe_boundary_preserved"] is False
    assert occupancy_presence_diag["safeguard_visibility"]["privacy_boundary_preserved"] is False
    assert occupancy_presence_diag["safeguard_visibility"]["guest_safe_mode_preserved"] is False
    assert occupancy_presence_diag["safeguard_visibility"]["unknown_occupant_mode_preserved"] is False
    assert occupancy_presence_diag["traceability_visibility"]["execution_envelope_ref_count"] == 0
    assert occupancy_presence_diag["traceability_visibility"]["latest_execution_kind"] is None
    assert occupancy_presence_diag["deferred_functionality_visibility"]["occupancy_governance_boundary"] == "#333"
    assert occupancy_presence_diag["deferred_functionality_visibility"]["presence_governance_boundary"] == "#334"
    assert occupancy_presence_diag["deferred_functionality_visibility"]["guest_unknown_occupant_behavior"] == "#335"
    assert occupancy_presence_diag["deferred_functionality_visibility"]["multi_occupant_behavior"] == "#336"
    assert occupancy_presence_diag["deferred_functionality_visibility"]["occupancy_presence_diagnostics_explainability"] == "#337"
    assert occupancy_presence_diag["diagnostics_non_rights"]["creates_authority"] is False
    assert occupancy_presence_diag["diagnostics_non_rights"]["modifies_occupancy_behavior"] is False
    assert occupancy_presence_diag["diagnostics_non_rights"]["modifies_presence_behavior"] is False
    assert occupancy_presence_diag["diagnostics_non_rights"]["modifies_guest_unknown_behavior"] is False
    assert occupancy_presence_diag["diagnostics_non_rights"]["modifies_multi_occupant_behavior"] is False
    restoration_diag = diagnostics["restoration_diagnostics_explainability_visibility"]
    assert restoration_diag["authority_visibility"]["restoration_authority_external"] is False
    assert restoration_diag["authority_visibility"]["restoration_policy_authority_external"] is False
    assert restoration_diag["restoration_explainability"]["restoration_available"] is False
    assert restoration_diag["restoration_explainability"]["restoration_unavailable_reason"] == "execution_envelope_not_available"
    assert restoration_diag["preservation_alignment_explainability"]["alignment_applicable"] is False
    assert restoration_diag["governance_controls_visibility"]["restoration_diagnostics_behavior_enabled"] is False
    assert restoration_diag["traceability_visibility"]["execution_envelope_ref_count"] == 0
    assert restoration_diag["diagnostics_non_rights"]["creates_authority"] is False
    assert restoration_diag["diagnostics_non_rights"]["executes_restoration_behavior"] is False
    assert diagnostics["preservation_baseline"]["preservation_governance_source"] == "adr_013_outcome_preservation"
    assert diagnostics["preservation_baseline"]["preservation_mode"] == "household_facing_outcomes"
    assert diagnostics["preservation_baseline"]["implementation_preservation_required"] is False
    assert diagnostics["preservation_baseline"]["baseline_validation_only"] is True
    assert diagnostics["preservation_baseline"]["global_context_visibility_available"] is True
    assert diagnostics["preservation_baseline"]["observed_outcome_clusters"]["global_context_provider_parity"]["room_projection_sample_count"] == 1
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


async def test_diagnostics_report_room_configs_outside_foundation(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Diagnostics should expose non-sensitive counts when stored room configs drift outside Foundation truth."""
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(area_id="orphaned_room")

    diagnostics = await async_get_config_entry_diagnostics(hass, setup_integration)

    assert diagnostics["foundation_runtime_boundary"]["configured_room_outside_foundation_count"] == 1
    assert diagnostics["foundation_runtime_boundary"]["room_configs_bound_to_foundation"] is False


async def test_diagnostics_include_person_productivity_binding_fallback_visibility(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Diagnostics should expose person productivity binding fallback without source content."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="person.tom",
            name="Tom",
            email_source_ref="sensor.mailbox_tom",
            calendar_source_ref="sensor.calendar_tom",
            shopping_source_ref="shopping_provider_household",
        )
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, setup_integration)

    bindings = diagnostics["productivity_source_of_record_boundary_visibility"]["person_productivity_source_bindings"]
    assert bindings["person_count"] == 1
    assert bindings["safe_fallback_person_count"] == 1
    person_binding = bindings["person_bindings"][0]
    assert person_binding["person_id"] == "person.tom"
    assert person_binding["configuration_complete"] is False
    assert person_binding["safe_fallback_mode_active"] is True
    assert person_binding["sources"]["shopping"]["binding_status"] == "configured"
    assert person_binding["sources"]["email"]["binding_status"] == "unavailable_or_removed"
    assert person_binding["sources"]["calendar"]["binding_status"] == "unavailable_or_removed"
    assert not _contains_key(bindings, "email_contents")
    assert not _contains_key(bindings, "calendar_event_details")
    assert not _contains_key(bindings, "shopping_item_contents")


async def test_diagnostics_expose_voice_identity_enrollment_lifecycle_boundary_visibility(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Diagnostics should expose bounded Voice Identity enrollment/lifecycle consumption visibility."""
    await hass.services.async_call(
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

    diagnostics = await async_get_config_entry_diagnostics(hass, setup_integration)
    voice_identity_diag = diagnostics["voice_identity_consumption_boundary_visibility"]

    assert voice_identity_diag["authority_visibility"]["voice_identity_enrollment_authority_external"] is True
    assert (
        voice_identity_diag["enrollment_boundary_visibility"]["latest_boundary_path"]
        == "governed_voice_identity_enrollment_lifecycle_consumption"
    )
    assert voice_identity_diag["enrollment_boundary_visibility"]["latest_consumption_only"] is True
    assert voice_identity_diag["enrollment_boundary_visibility"]["latest_enrollment_state_consumed"] is True
    assert voice_identity_diag["enrollment_boundary_visibility"]["latest_enrollment_state"] == "active"
    assert voice_identity_diag["enrollment_boundary_visibility"]["latest_enrollment_readiness"] == "ready"
    assert voice_identity_diag["lifecycle_boundary_visibility"]["latest_lifecycle_state_consumed"] is True
    assert voice_identity_diag["lifecycle_boundary_visibility"]["latest_enrollment_lifecycle_state"] == "active"
    assert voice_identity_diag["lifecycle_boundary_visibility"]["latest_voice_profile_lifecycle_state"] == "active"
    assert voice_identity_diag["lifecycle_boundary_visibility"]["latest_identity_lifecycle_state"] == "active"
    assert voice_identity_diag["ownership_boundary_visibility"]["manages_enrollment_lifecycle"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["manages_voice_profile_lifecycle"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["creates_voice_profiles"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["changes_enrollment_state"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["infers_enrollment_state"] is False


async def test_diagnostics_expose_voice_identity_permission_and_legacy_disposition_boundary_visibility(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Diagnostics should expose bounded Voice Identity permission and legacy disposition visibility."""
    await hass.services.async_call(
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
                },
                "voice_identity_legacy_disposition_context": {
                    "legacy_disposition_state": "superseded",
                    "legacy_disposition_outcome": "replacement_reference_consumed",
                    "legacy_reference": "legacy-fingerprint-001",
                    "replacement_reference": "voiceprint-v2-001",
                    "legacy_reason_code": "replacement_reference_available",
                    "lineage_ref": "vi-legacy-001",
                    "source": "voice_identity",
                },
            },
        },
        blocking=True,
        return_response=True,
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, setup_integration)
    voice_identity_diag = diagnostics["voice_identity_consumption_boundary_visibility"]

    assert voice_identity_diag["authority_visibility"]["voice_identity_permission_authority_external"] is True
    assert voice_identity_diag["authority_visibility"]["voice_identity_legacy_disposition_authority_external"] is True
    assert (
        voice_identity_diag["permission_boundary_visibility"]["latest_boundary_path"]
        == "governed_voice_identity_permission_consumption"
    )
    assert voice_identity_diag["permission_boundary_visibility"]["latest_consumption_only"] is True
    assert voice_identity_diag["permission_boundary_visibility"]["latest_permission_state_consumed"] is True
    assert voice_identity_diag["permission_boundary_visibility"]["latest_permission_state"] == "allowed"
    assert voice_identity_diag["permission_boundary_visibility"]["latest_permission_outcome"] == "permitted"
    assert voice_identity_diag["permission_boundary_visibility"]["latest_consent_state"] == "granted"
    assert voice_identity_diag["permission_boundary_visibility"]["latest_consent_outcome"] == "valid"
    assert (
        voice_identity_diag["legacy_disposition_boundary_visibility"]["latest_boundary_path"]
        == "governed_voice_identity_legacy_disposition_consumption"
    )
    assert voice_identity_diag["legacy_disposition_boundary_visibility"]["latest_consumption_only"] is True
    assert voice_identity_diag["legacy_disposition_boundary_visibility"]["latest_legacy_disposition_consumed"] is True
    assert voice_identity_diag["legacy_disposition_boundary_visibility"]["latest_legacy_disposition_state"] == "superseded"
    assert voice_identity_diag["legacy_disposition_boundary_visibility"]["latest_replacement_reference"] == "voiceprint-v2-001"
    assert voice_identity_diag["ownership_boundary_visibility"]["grants_permission"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["revokes_permission"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["approves_consent"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["infers_consent"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["migrates_legacy_identity_data"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["disposes_legacy_identity_data"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["determines_legacy_disposition"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["infers_legacy_disposition_state"] is False


async def test_diagnostics_expose_voice_identity_diagnostics_and_explainability_boundary_visibility(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Diagnostics should expose bounded Voice Identity diagnostics/explainability consumption."""
    await hass.services.async_call(
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

    diagnostics = await async_get_config_entry_diagnostics(hass, setup_integration)
    voice_identity_diag = diagnostics["voice_identity_consumption_boundary_visibility"]

    assert voice_identity_diag["authority_visibility"]["voice_identity_diagnostics_authority_external"] is True
    assert voice_identity_diag["authority_visibility"]["voice_identity_explainability_authority_external"] is True
    assert (
        voice_identity_diag["diagnostics_boundary_visibility"]["latest_boundary_path"]
        == "governed_voice_identity_diagnostics_consumption"
    )
    assert voice_identity_diag["diagnostics_boundary_visibility"]["latest_consumption_only"] is True
    assert voice_identity_diag["diagnostics_boundary_visibility"]["latest_diagnostics_consumed"] is True
    assert voice_identity_diag["diagnostics_boundary_visibility"]["latest_diagnostic_available"] is True
    assert voice_identity_diag["diagnostics_boundary_visibility"]["latest_health_status"] == "healthy"
    assert voice_identity_diag["diagnostics_boundary_visibility"]["latest_repair_hint_code"] == "refresh_voice_profile"
    assert voice_identity_diag["diagnostics_boundary_visibility"]["latest_provenance_source"] == "voice_identity_diagnostics"
    assert voice_identity_diag["diagnostics_boundary_visibility"]["latest_lineage_ref"] == "vi-diagnostics-lineage-001"
    assert (
        voice_identity_diag["explainability_boundary_visibility"]["latest_boundary_path"]
        == "governed_voice_identity_explainability_consumption"
    )
    assert voice_identity_diag["explainability_boundary_visibility"]["latest_consumption_only"] is True
    assert voice_identity_diag["explainability_boundary_visibility"]["latest_explainability_consumed"] is True
    assert voice_identity_diag["explainability_boundary_visibility"]["latest_consumed_outcome"] == "attribution_abstained"
    assert voice_identity_diag["explainability_boundary_visibility"]["latest_authority_source"] == "voice_identity"
    assert voice_identity_diag["explainability_boundary_visibility"]["latest_provenance_source"] == "voice_identity_attribution"
    assert voice_identity_diag["explainability_boundary_visibility"]["latest_attribution_source"] == "voice_identity_attribution_service"
    assert voice_identity_diag["explainability_boundary_visibility"]["latest_confidence_source"] == "voice_identity_confidence_band"
    assert voice_identity_diag["explainability_boundary_visibility"]["latest_enrollment_source"] == "voice_identity_enrollment_registry"
    assert voice_identity_diag["explainability_boundary_visibility"]["latest_lifecycle_source"] == "voice_identity_lifecycle_registry"
    assert voice_identity_diag["explainability_boundary_visibility"]["latest_permission_source"] == "voice_identity_permission_policy"
    assert voice_identity_diag["explainability_boundary_visibility"]["latest_legacy_disposition_source"] == "voice_identity_legacy_disposition"
    assert voice_identity_diag["ownership_boundary_visibility"]["generates_diagnostics_authority"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["rewrites_diagnostics"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["calculates_health_status"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["calculates_readiness"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["generates_repair_hints"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["generates_explainability_authority"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["replaces_provenance"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["creates_explainability_lineage"] is False


async def test_diagnostics_expose_active_person_resolution_visibility_when_resolved(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Diagnostics should expose resolved active-person visibility from Voice Identity consumption."""
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
                    "confidence": 0.9,
                    "confidence_band": "high",
                    "reason_code": "attribution_ready",
                    "source": "voice_identity",
                }
            },
        },
        blocking=True,
        return_response=True,
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, setup_integration)
    active_person = diagnostics["voice_identity_consumption_boundary_visibility"]["consumption_visibility"][
        "active_person_resolution"
    ]

    assert active_person["active_person_state"] == "active_person_available"
    assert active_person["active_person_available"] is True
    assert active_person["resolved_person_id"] == "person.tom"
    assert active_person["resolved_voice_profile_id"] == "vp_tom"
    assert active_person["confidence_available"] is True
    assert active_person["confidence_accepted"] is True
    assert active_person["fail_closed"] is False


async def test_diagnostics_expose_execution_and_routing_explainability(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Diagnostics should expose bounded explainability for routing and execution-envelope outcomes."""
    area_registry = ar.async_get(hass)
    kitchen = area_registry.async_create(name="Kitchen")
    dining = area_registry.async_create(name="Dining")

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
        return_response=True,
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
        return_response=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "update_execution_preferences",
        {
            "scope_id": "public_space",
            "preferences": {"mode": "scene", "target": "scene.public_space"},
        },
        blocking=True,
        return_response=True,
    )

    await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "scene.public_space",
            "area_id": kitchen.id,
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )
    await hass.services.async_call(
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

    diagnostics = await async_get_config_entry_diagnostics(hass, setup_integration)

    latest_orchestration = diagnostics["execution_explainability"]["latest_orchestration"]
    assert diagnostics["execution_explainability"]["orchestration_activity_count"] >= 1
    assert latest_orchestration is not None
    assert latest_orchestration["execution_kind"] == "orchestration"
    assert latest_orchestration["plan_kind"] == "scene_turn_on"
    assert latest_orchestration["route_scope"] == "composite"
    assert latest_orchestration["resolved_composite_id"] == "public_space"
    assert latest_orchestration["execution_preference_scope_id"] == "public_space"
    assert latest_orchestration["execution_preference_present"] is True
    assert latest_orchestration["context_source_count"] == 1

    latest_direct = diagnostics["execution_explainability"]["latest_direct"]
    assert diagnostics["execution_explainability"]["direct_activity_count"] >= 1
    assert latest_direct is not None
    assert latest_direct["execution_kind"] == "direct"
    assert latest_direct["plan_kind"] == "direct_service_call"
    assert latest_direct["route_scope"] == "direct"

    voice_identity_diag = diagnostics["voice_identity_consumption_boundary_visibility"]
    assert voice_identity_diag["authority_visibility"]["voice_identity_authority_external"] is True
    assert voice_identity_diag["consumption_visibility"]["execution_envelope_ref_count"] >= 1
    assert (
        voice_identity_diag["consumption_visibility"]["latest_boundary_path"]
        == "governed_voice_identity_attribution_confidence_consumption"
    )
    assert voice_identity_diag["consumption_visibility"]["latest_consumption_only"] is True
    active_person = voice_identity_diag["consumption_visibility"]["active_person_resolution"]
    assert active_person["active_person_state"] == "active_person_unavailable"
    assert active_person["active_person_available"] is False
    assert active_person["resolved_person_id"] is None
    assert active_person["confidence_accepted"] is False
    assert active_person["fail_closed"] is True
    assert voice_identity_diag["ownership_boundary_visibility"]["derives_attribution_authority"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["derives_confidence_authority"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["calculates_attribution"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["calculates_confidence"] is False
    assert voice_identity_diag["enrollment_boundary_visibility"]["latest_consumption_only"] is True
    assert voice_identity_diag["ownership_boundary_visibility"]["manages_enrollment_lifecycle"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["manages_voice_profile_lifecycle"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["creates_voice_profiles"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["changes_enrollment_state"] is False
    assert voice_identity_diag["ownership_boundary_visibility"]["infers_enrollment_state"] is False

    occupancy_presence_diag = diagnostics["occupancy_presence_diagnostics_explainability_visibility"]
    assert occupancy_presence_diag["authority_visibility"]["occupancy_authority_external"] is True
    assert occupancy_presence_diag["authority_visibility"]["presence_authority_external"] is True
    assert occupancy_presence_diag["authority_visibility"]["identity_authority_external"] is True
    assert occupancy_presence_diag["authority_visibility"]["room_truth_authority_external"] is True
    assert occupancy_presence_diag["authority_visibility"]["restoration_authority_external"] is True
    assert occupancy_presence_diag["governance_visibility"]["latest_occupancy_governance_applicable"] is False
    assert occupancy_presence_diag["governance_visibility"]["latest_occupancy_governance_path"] == "not_applicable_direct_execution"
    assert occupancy_presence_diag["governance_visibility"]["latest_presence_governance_applicable"] is False
    assert occupancy_presence_diag["governance_visibility"]["latest_presence_governance_path"] == "not_applicable_direct_execution"
    assert occupancy_presence_diag["governance_visibility"]["latest_orchestration_occupancy_governance_applicable"] is True
    assert occupancy_presence_diag["governance_visibility"]["latest_orchestration_occupancy_governance_path"] == "governed_occupancy_boundary"
    assert occupancy_presence_diag["governance_visibility"]["latest_orchestration_presence_governance_applicable"] is True
    assert occupancy_presence_diag["governance_visibility"]["latest_orchestration_presence_governance_path"] == "governed_presence_boundary"
    assert occupancy_presence_diag["governance_visibility"]["latest_direct_occupancy_governance_applicable"] is False
    assert occupancy_presence_diag["governance_visibility"]["latest_direct_occupancy_governance_path"] == "not_applicable_direct_execution"
    assert occupancy_presence_diag["governance_visibility"]["latest_direct_presence_governance_applicable"] is False
    assert occupancy_presence_diag["governance_visibility"]["latest_direct_presence_governance_path"] == "not_applicable_direct_execution"
    assert occupancy_presence_diag["behavior_visibility"]["latest_guest_unknown_behavior_applicable"] is False
    assert occupancy_presence_diag["behavior_visibility"]["latest_guest_unknown_behavior_path"] == "not_applicable_direct_execution"
    assert occupancy_presence_diag["behavior_visibility"]["latest_multi_occupant_behavior_applicable"] is False
    assert occupancy_presence_diag["behavior_visibility"]["latest_multi_occupant_behavior_path"] == "not_applicable_direct_execution"
    assert occupancy_presence_diag["ownership_boundary_visibility"]["occupancy_owns_room_truth"] is False
    assert occupancy_presence_diag["ownership_boundary_visibility"]["presence_owns_room_truth"] is False
    assert occupancy_presence_diag["ownership_boundary_visibility"]["restoration_authority_external"] is True
    assert occupancy_presence_diag["safeguard_visibility"]["guest_safe_boundary_preserved"] is True
    assert occupancy_presence_diag["safeguard_visibility"]["privacy_boundary_preserved"] is True
    assert occupancy_presence_diag["safeguard_visibility"]["guest_safe_mode_preserved"] is False
    assert occupancy_presence_diag["safeguard_visibility"]["unknown_occupant_mode_preserved"] is True
    assert occupancy_presence_diag["traceability_visibility"]["execution_envelope_ref_count"] >= 1
    assert occupancy_presence_diag["traceability_visibility"]["latest_execution_kind"] == "direct"
    assert occupancy_presence_diag["deferred_functionality_visibility"]["occupancy_governance_boundary"] == "#333"
    assert occupancy_presence_diag["deferred_functionality_visibility"]["presence_governance_boundary"] == "#334"
    assert occupancy_presence_diag["deferred_functionality_visibility"]["guest_unknown_occupant_behavior"] == "#335"
    assert occupancy_presence_diag["deferred_functionality_visibility"]["multi_occupant_behavior"] == "#336"
    assert occupancy_presence_diag["deferred_functionality_visibility"]["occupancy_presence_diagnostics_explainability"] == "#337"
    assert occupancy_presence_diag["diagnostics_non_rights"]["creates_authority"] is False
    assert occupancy_presence_diag["diagnostics_non_rights"]["modifies_occupancy_behavior"] is False
    assert occupancy_presence_diag["diagnostics_non_rights"]["modifies_presence_behavior"] is False
    assert occupancy_presence_diag["diagnostics_non_rights"]["modifies_guest_unknown_behavior"] is False
    assert occupancy_presence_diag["diagnostics_non_rights"]["modifies_multi_occupant_behavior"] is False

    experience_diag = diagnostics["experience_diagnostics_explainability_visibility"]
    assert experience_diag["governance_visibility"]["latest_experience_governance_applicable"] is True
    assert experience_diag["governance_visibility"]["latest_experience_governance_path"] == "capability_consumption_to_experience_governance"
    assert experience_diag["handoff_visibility"]["latest_capability_to_experience_handoff_applicable"] is False
    assert experience_diag["handoff_visibility"]["latest_capability_to_experience_handoff_path"] == "not_applicable_direct_execution"
    assert experience_diag["handoff_visibility"]["latest_handoff_transfers_authority"] is False
    assert experience_diag["projection_visibility"]["latest_experience_projection_applicable"] is False
    assert experience_diag["projection_visibility"]["latest_experience_projection_path"] == "not_applicable_direct_execution"
    assert experience_diag["projection_visibility"]["latest_projection_is_authority"] is False
    assert experience_diag["restoration_visibility"]["latest_experience_restoration_boundary_applicable"] is False
    assert experience_diag["restoration_visibility"]["latest_experience_restoration_path"] == "not_applicable_direct_execution"
    assert experience_diag["restoration_visibility"]["latest_restoration_governance_path"] == "not_applicable_direct_execution"
    assert experience_diag["restoration_visibility"]["latest_restoration_authority_transferred"] is False
    assert experience_diag["restoration_visibility"]["latest_restoration_authority_external"] is True
    assert experience_diag["restoration_visibility"]["latest_restoration_policy_authority_external"] is True
    assert experience_diag["restoration_visibility"]["latest_restoration_owns_identity"] is False
    assert experience_diag["restoration_visibility"]["latest_restoration_owns_occupancy"] is False
    assert experience_diag["restoration_visibility"]["latest_restoration_owns_continuity"] is False
    assert experience_diag["restoration_visibility"]["latest_restoration_owns_affinity"] is False
    assert experience_diag["restoration_visibility"]["latest_restoration_owns_household_memory"] is False
    assert experience_diag["restoration_visibility"]["latest_restoration_execution_enabled"] is False
    assert experience_diag["restoration_visibility"]["latest_restoration_decision_behavior_enabled"] is False
    assert experience_diag["traceability_visibility"]["execution_envelope_ref_count"] >= 1

    continuity_affinity_diag = diagnostics["continuity_affinity_diagnostics_explainability_visibility"]
    assert continuity_affinity_diag["availability_explainability"]["continuity_available"] is False
    assert continuity_affinity_diag["availability_explainability"]["affinity_available"] is False
    assert continuity_affinity_diag["availability_explainability"]["latest_continuity_path"] == "not_applicable_direct_execution"
    assert continuity_affinity_diag["availability_explainability"]["latest_affinity_path"] == "not_applicable_direct_execution"
    assert continuity_affinity_diag["availability_explainability"]["latest_direct_continuity_path"] == "not_applicable_direct_execution"
    assert continuity_affinity_diag["availability_explainability"]["latest_direct_affinity_path"] == "not_applicable_direct_execution"
    assert continuity_affinity_diag["ownership_boundary_visibility"]["continuity_owns_identity"] is False
    assert continuity_affinity_diag["ownership_boundary_visibility"]["continuity_owns_occupancy"] is False
    assert continuity_affinity_diag["ownership_boundary_visibility"]["continuity_owns_memory"] is False
    assert continuity_affinity_diag["ownership_boundary_visibility"]["affinity_owns_identity"] is False
    assert continuity_affinity_diag["ownership_boundary_visibility"]["affinity_owns_room_truth"] is False
    assert continuity_affinity_diag["ownership_boundary_visibility"]["affinity_owns_occupancy"] is False
    assert continuity_affinity_diag["ownership_boundary_visibility"]["affinity_owns_memory"] is False
    assert continuity_affinity_diag["ownership_boundary_visibility"]["memory_owns_identity"] is False
    assert continuity_affinity_diag["ownership_boundary_visibility"]["memory_owns_retention_policy"] is False
    assert continuity_affinity_diag["ownership_boundary_visibility"]["memory_owns_storage"] is False
    assert continuity_affinity_diag["ownership_boundary_visibility"]["memory_owns_provenance"] is False
    assert continuity_affinity_diag["safeguard_visibility"]["privacy_boundary_preserved"] is True
    assert continuity_affinity_diag["safeguard_visibility"]["affinity_privacy_boundary_preserved"] is True
    assert continuity_affinity_diag["safeguard_visibility"]["affinity_guest_safe_boundary_preserved"] is True
    assert continuity_affinity_diag["safeguard_visibility"]["privacy_memory_guest_safe_boundary_preserved"] is True
    assert continuity_affinity_diag["diagnostics_non_rights"]["creates_authority"] is False
    assert continuity_affinity_diag["diagnostics_non_rights"]["creates_outcomes"] is False
    assert continuity_affinity_diag["diagnostics_non_rights"]["modifies_continuity_behavior"] is False
    assert continuity_affinity_diag["diagnostics_non_rights"]["modifies_affinity_behavior"] is False
    assert continuity_affinity_diag["diagnostics_non_rights"]["modifies_privacy_behavior"] is False

    restoration_diag = diagnostics["restoration_diagnostics_explainability_visibility"]
    assert restoration_diag["authority_visibility"]["restoration_authority_external"] is True
    assert restoration_diag["authority_visibility"]["restoration_policy_authority_external"] is True
    assert restoration_diag["authority_visibility"]["restoration_authority_transferred"] is False
    assert restoration_diag["restoration_explainability"]["restoration_available"] is False
    assert restoration_diag["restoration_explainability"]["restoration_applicable"] is False
    assert restoration_diag["restoration_explainability"]["restoration_eligible"] is False
    assert restoration_diag["restoration_explainability"]["restoration_applied"] is False
    assert restoration_diag["restoration_explainability"]["restoration_outcome_path"] == "not_applicable_direct_execution"
    assert restoration_diag["restoration_explainability"]["restoration_outcome_reason"] == "direct_execution_not_eligible"
    assert restoration_diag["restoration_explainability"]["restoration_suppression_reason"] == "direct_execution_not_eligible"
    assert restoration_diag["restoration_explainability"]["direct_path_reason"] == "direct_execution_not_eligible"
    assert restoration_diag["preservation_alignment_explainability"]["alignment_applicable"] is False
    assert restoration_diag["preservation_alignment_explainability"]["alignment_path"] == "not_applicable_direct_execution"
    assert restoration_diag["preservation_alignment_explainability"]["alignment_eligible"] is False
    assert restoration_diag["preservation_alignment_explainability"]["alignment_reason"] == "direct_execution_not_eligible"
    assert restoration_diag["preservation_alignment_explainability"]["direct_alignment_path"] == "not_applicable_direct_execution"
    assert restoration_diag["preservation_alignment_explainability"]["direct_alignment_reason"] == "direct_execution_not_eligible"
    assert restoration_diag["preservation_alignment_explainability"]["consumes_restoration_outcomes"] is True
    assert restoration_diag["governance_controls_visibility"]["restoration_diagnostics_behavior_enabled"] is True
    assert restoration_diag["governance_controls_visibility"]["restoration_decision_behavior_enabled"] is False
    assert restoration_diag["governance_controls_visibility"]["restoration_execution_enabled"] is False
    assert restoration_diag["governance_controls_visibility"]["direct_restoration_diagnostics_behavior_enabled"] is True
    assert restoration_diag["governance_controls_visibility"]["direct_restoration_decision_behavior_enabled"] is False
    assert restoration_diag["governance_controls_visibility"]["direct_restoration_execution_enabled"] is False
    assert restoration_diag["ownership_boundary_visibility"]["restoration_owns_identity"] is False
    assert restoration_diag["ownership_boundary_visibility"]["restoration_owns_occupancy"] is False
    assert restoration_diag["ownership_boundary_visibility"]["restoration_owns_continuity"] is False
    assert restoration_diag["ownership_boundary_visibility"]["restoration_owns_affinity"] is False
    assert restoration_diag["ownership_boundary_visibility"]["restoration_owns_household_memory"] is False
    assert restoration_diag["safeguard_visibility"]["privacy_boundary_preserved"] is True
    assert restoration_diag["safeguard_visibility"]["guest_safe_boundary_preserved"] is True
    assert restoration_diag["deferred_functionality_visibility"]["restoration_outcome_implementation"] == "#330"
    assert restoration_diag["deferred_functionality_visibility"]["e3a_preservation_alignment"] == "#331"
    assert restoration_diag["deferred_functionality_visibility"]["restoration_diagnostics_explainability"] == "#332"
    assert restoration_diag["deferred_functionality_visibility"]["release_3_validation"] == "#338"
    assert restoration_diag["traceability_visibility"]["execution_envelope_ref_count"] >= 1
    assert restoration_diag["traceability_visibility"]["preservation_alignment_ref_count"] >= 1
    assert restoration_diag["traceability_visibility"]["latest_execution_kind"] == "direct"
    assert restoration_diag["traceability_visibility"]["latest_restoration_path"] == "not_applicable_direct_execution"
    assert restoration_diag["traceability_visibility"]["latest_restoration_outcome_path"] == "not_applicable_direct_execution"
    assert restoration_diag["traceability_visibility"]["latest_preservation_alignment_path"] == "not_applicable_direct_execution"
    assert restoration_diag["diagnostics_non_rights"]["creates_authority"] is False
    assert restoration_diag["diagnostics_non_rights"]["creates_restoration_outcomes"] is False
    assert restoration_diag["diagnostics_non_rights"]["creates_preservation_outcomes"] is False
    assert restoration_diag["diagnostics_non_rights"]["modifies_restoration_decision_logic"] is False
    assert restoration_diag["diagnostics_non_rights"]["modifies_preservation_alignment_logic"] is False
    assert restoration_diag["diagnostics_non_rights"]["executes_restoration_behavior"] is False
    assert restoration_diag["diagnostics_non_rights"]["executes_preservation_alignment_behavior"] is False

    assert diagnostics["context_assembly_visibility"]["enabled_composite_projection_count"] >= 1
    composite_sample = diagnostics["context_assembly_visibility"]["composite_projection_samples"][0]
    assert composite_sample["composite_id"] == "public_space"
    assert composite_sample["context_area_id"] == dining.id

    preservation = diagnostics["preservation_baseline"]
    assert preservation["foundation_boundary_ready"] is True
    assert preservation["composite_scope_visibility_available"] is True
    assert preservation["global_context_visibility_available"] is True
    assert preservation["execution_hierarchy_visibility_available"] is True
    assert preservation["explainability_surface_available"] is True
    assert preservation["observed_outcome_clusters"]["execution_hierarchy"]["latest_orchestration_route_scope"] == "composite"
    assert "merged_room_preservation_logic" in preservation["not_yet_implemented_in_baseline"]


async def test_diagnostics_expose_vocabulary_resolution_visibility(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Diagnostics should expose bounded room/device/asset vocabulary resolution visibility."""
    area = ar.async_get(hass).async_create(name="Studio")
    storage = ConciergeStorage(hass)
    await storage.async_update_global_feature(
        feature_key="room_vocabulary_registry",
        enabled=True,
        options={
            "entries": [
                {
                    "term": "studio",
                    "aliases": ["music room"],
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
                    "entity_id": "light.studio_ceiling",
                    "area_id": area.id,
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
                    "term": "piano",
                    "aliases": ["grand piano"],
                    "asset_id": "asset.grand_piano",
                    "handoff_entity_id": "switch.studio_piano_protect",
                    "area_id": area.id,
                }
            ]
        },
    )

    await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "ceiling lights",
            "area_id": "music room",
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )
    await hass.services.async_call(
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

    diagnostics = await async_get_config_entry_diagnostics(hass, setup_integration)
    vocab = diagnostics["vocabulary_diagnostics_visibility"]

    assert vocab["configured_entry_counts"]["room_vocabulary_entries"] == 1
    assert vocab["configured_entry_counts"]["device_entity_vocabulary_entries"] == 1
    assert vocab["configured_entry_counts"]["asset_vocabulary_entries"] == 1
    assert vocab["resolution_visibility"]["room_resolution_count"] >= 1
    assert vocab["resolution_visibility"]["device_entity_resolution_count"] >= 1
    assert vocab["resolution_visibility"]["asset_handoff_resolution_count"] >= 1
    latest_room = vocab["resolution_visibility"]["latest_room_resolution"]
    assert latest_room is not None
    assert latest_room["source"] == "room_vocabulary_registry"
    latest_device = vocab["resolution_visibility"]["latest_device_entity_resolution"]
    assert latest_device is not None
    assert latest_device["source"] == "device_entity_vocabulary_registry"
    latest_asset = vocab["resolution_visibility"]["latest_asset_handoff_resolution"]
    assert latest_asset is not None
    assert latest_asset["source"] == "asset_intelligence_handoff"

    capability_diag = diagnostics["capability_diagnostics_explainability_visibility"]
    assert capability_diag["discovery_visibility"]["latest_capability_discovery_applicable"] is True
    assert capability_diag["discovery_visibility"]["latest_capability_discovery_path"] == "capability_consumption_to_discovery"
    assert capability_diag["discovery_visibility"]["latest_discovered_capability_count"] >= 0
    assert capability_diag["handoff_visibility"]["room_vocabulary_resolution_count"] >= 1
    assert capability_diag["handoff_visibility"]["device_entity_vocabulary_resolution_count"] >= 1
    assert capability_diag["handoff_visibility"]["asset_vocabulary_resolution_count"] >= 1
    assert capability_diag["handoff_visibility"]["asset_intelligence_cp00_handoff_count"] >= 1
    assert capability_diag["traceability_visibility"]["execution_envelope_ref_count"] >= 1


async def test_diagnostics_expose_messaging_governance_boundary_visibility(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Diagnostics should expose bounded visibility for the recorded messaging governance boundary."""
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

    diagnostics = await async_get_config_entry_diagnostics(hass, setup_integration)

    messaging_diag = diagnostics["messaging_governance_boundary_visibility"]
    assert messaging_diag["authority_visibility"]["message_authority_external"] is True
    assert messaging_diag["authority_visibility"]["provenance_authority_external"] is True
    assert messaging_diag["authority_visibility"]["household_memory_authority_external"] is True
    assert messaging_diag["governance_visibility"]["messaging_boundary_ref_count"] >= 1
    assert messaging_diag["governance_visibility"]["latest_messaging_boundary_applicable"] is True
    assert messaging_diag["governance_visibility"]["latest_messaging_boundary_path"] == "governed_messaging_boundary"
    assert messaging_diag["governance_visibility"]["latest_route_scope"] == "room"
    assert messaging_diag["governance_visibility"]["latest_recipient_scope"] == "person"
    assert messaging_diag["governance_visibility"]["latest_message_context_type"] == "person_push"
    assert messaging_diag["ownership_boundary_visibility"]["messaging_owns_truth"] is False
    assert messaging_diag["ownership_boundary_visibility"]["messaging_owns_provenance"] is False
    assert messaging_diag["ownership_boundary_visibility"]["messaging_owns_memory"] is False
    assert messaging_diag["ownership_boundary_visibility"]["messaging_owns_identity"] is False
    assert messaging_diag["lifecycle_governance_visibility"]["message_creation_governed"] is True
    assert messaging_diag["lifecycle_governance_visibility"]["message_delivery_governed"] is True
    assert messaging_diag["lifecycle_governance_visibility"]["message_acknowledgement_governed"] is True
    assert messaging_diag["lifecycle_governance_visibility"]["message_retention_governed"] is True
    assert messaging_diag["traceability_visibility"]["messaging_boundary_ref_count"] >= 1
    assert messaging_diag["traceability_visibility"]["latest_message_authority_external"] is True
    assert messaging_diag["traceability_visibility"]["latest_provenance_authority_external"] is True
    assert messaging_diag["traceability_visibility"]["latest_household_memory_authority_external"] is True
    assert messaging_diag["deferred_functionality_visibility"]["messaging_provenance"] == "#340"
    assert messaging_diag["deferred_functionality_visibility"]["messaging_diagnostics_explainability"] == "#343"
    provenance_diag = diagnostics["messaging_provenance_visibility"]
    assert provenance_diag["authority_visibility"]["provenance_authority_external"] is True
    assert provenance_diag["traceability_visibility"]["messaging_provenance_ref_count"] >= 1
    assert provenance_diag["traceability_visibility"]["latest_provenance_id_present"] is True
    assert provenance_diag["traceability_visibility"]["latest_source_service"] == "concierge.push_person_message"
    assert provenance_diag["traceability_visibility"]["latest_created_in_room"] == area.id
    assert provenance_diag["delivery_visibility"]["latest_delivery_channel"] == "mobile_notify"
    assert provenance_diag["delivery_visibility"]["latest_selected_service"] == "notify.phone"
    assert provenance_diag["delivery_visibility"]["latest_selected_target_id"] == "phone"
    assert provenance_diag["delivery_visibility"]["latest_routing_path"] == "person_mobile_target_fallback"
    assert provenance_diag["diagnostics_non_rights"]["claims_upstream_truth"] is False
    assert provenance_diag["diagnostics_non_rights"]["claims_identity_authority"] is False
    assert provenance_diag["diagnostics_non_rights"]["claims_household_memory_authority"] is False
    delivery_diag = diagnostics["notification_delivery_boundary_visibility"]
    assert delivery_diag["authority_visibility"]["delivery_authority_external"] is True
    assert delivery_diag["authority_visibility"]["recipient_authority_external"] is True
    assert delivery_diag["authority_visibility"]["consent_authority_external"] is True
    assert delivery_diag["authority_visibility"]["visibility_authority_external"] is True
    assert delivery_diag["delivery_visibility"]["notification_delivery_boundary_ref_count"] >= 1
    assert delivery_diag["delivery_visibility"]["latest_delivery_boundary_path"] == "governed_notification_delivery_boundary"
    assert delivery_diag["delivery_visibility"]["latest_delivery_channel"] == "mobile_notify"
    assert delivery_diag["delivery_visibility"]["latest_selected_service"] == "notify.phone"
    assert delivery_diag["delivery_visibility"]["latest_selected_target_id"] == "phone"
    assert delivery_diag["delivery_visibility"]["latest_routing_path"] == "person_mobile_target_fallback"
    assert delivery_diag["execution_tracking"]["delivery_activity_count"] >= 1
    assert delivery_diag["execution_tracking"]["delivery_success_count"] >= 1
    assert delivery_diag["governance_visibility"]["delivery_boundary_only"] is True
    assert delivery_diag["governance_visibility"]["recipient_authorization_enabled"] is False
    assert delivery_diag["governance_visibility"]["consent_adjudication_enabled"] is False
    assert delivery_diag["governance_visibility"]["visibility_adjudication_enabled"] is False
    assert delivery_diag["diagnostics_non_rights"]["claims_recipient_authority"] is False
    assert delivery_diag["diagnostics_non_rights"]["claims_consent_authority"] is False
    assert delivery_diag["diagnostics_non_rights"]["claims_visibility_authority"] is False
    assert delivery_diag["diagnostics_non_rights"]["claims_delivery_truth"] is False
    assert delivery_diag["diagnostics_non_rights"]["claims_acknowledgement"] is False
    assert delivery_diag["diagnostics_non_rights"]["claims_message_seen"] is False
    recipient_diag = diagnostics["recipient_consent_privacy_visibility_boundary_visibility"]
    assert recipient_diag["authority_visibility"]["recipient_authority_external"] is True
    assert recipient_diag["authority_visibility"]["consent_authority_external"] is True
    assert recipient_diag["authority_visibility"]["privacy_authority_external"] is True
    assert recipient_diag["authority_visibility"]["visibility_authority_external"] is True
    assert recipient_diag["decision_visibility"]["boundary_ref_count"] >= 1
    assert recipient_diag["decision_visibility"]["latest_delivery_permitted"] is True
    assert recipient_diag["decision_visibility"]["latest_decision_reason"] == "delivery_permitted"
    assert recipient_diag["delivery_visibility"]["latest_delivery_channel"] == "mobile_notify"
    assert recipient_diag["delivery_visibility"]["latest_selected_service"] == "notify.phone"
    assert recipient_diag["delivery_visibility"]["latest_selected_target_id"] == "phone"
    assert recipient_diag["delivery_visibility"]["latest_routing_path"] == "person_mobile_target_fallback"
    assert recipient_diag["diagnostics_non_rights"]["claims_identity_authority"] is False
    assert recipient_diag["diagnostics_non_rights"]["claims_recipient_authority"] is False
    assert recipient_diag["diagnostics_non_rights"]["claims_consent_authority"] is False
    assert recipient_diag["diagnostics_non_rights"]["claims_privacy_authority"] is False
    assert recipient_diag["diagnostics_non_rights"]["claims_visibility_authority"] is False
    assert recipient_diag["diagnostics_non_rights"]["claims_message_seen"] is False
    assert recipient_diag["diagnostics_non_rights"]["claims_acknowledgement"] is False
    messaging_diag = diagnostics["messaging_diagnostics_explainability_visibility"]
    assert messaging_diag["authority_visibility"]["diagnostics_authority_external"] is True
    assert messaging_diag["authority_visibility"]["explainability_authority_external"] is True
    assert messaging_diag["explainability_summary"]["messaging_explainability_ref_count"] >= 1
    assert messaging_diag["explainability_summary"]["latest_delivery_permitted"] is True
    assert messaging_diag["explainability_summary"]["latest_decision_reason"] == "delivery_permitted"
    assert messaging_diag["explainability_summary"]["latest_governance_boundary_involved"] == "notification_delivery_boundary"
    assert messaging_diag["explainability_summary"]["latest_delivery_channel"] == "mobile_notify"
    assert messaging_diag["governance_outcome_visibility"]["expected_governance_outcomes_visible"] is True
    assert messaging_diag["governance_outcome_visibility"]["governance_denial_is_runtime_failure"] is False
    assert messaging_diag["logging_strategy_visibility"]["governance_policy_denied_level"] == "info"
    assert messaging_diag["logging_strategy_visibility"]["operational_delivery_failure_level"] == "error"
    assert messaging_diag["diagnostics_non_rights"]["creates_authority"] is False
    assert messaging_diag["diagnostics_non_rights"]["creates_truth"] is False
    assert messaging_diag["diagnostics_non_rights"]["creates_memory"] is False
    assert messaging_diag["diagnostics_non_rights"]["creates_identity"] is False
    memory_diag = diagnostics["household_memory_governance_boundary_visibility"]
    assert memory_diag["authority_visibility"]["household_memory_authority_external"] is True
    assert memory_diag["authority_visibility"]["identity_authority_external"] is True
    assert memory_diag["authority_visibility"]["occupancy_authority_external"] is True
    assert memory_diag["authority_visibility"]["messaging_authority_external"] is True
    assert memory_diag["authority_visibility"]["consent_authority_external"] is True
    assert memory_diag["authority_visibility"]["privacy_authority_external"] is True
    assert memory_diag["authority_visibility"]["source_of_truth_authority_external"] is True
    assert memory_diag["boundary_visibility"]["household_memory_boundary_ref_count"] >= 1
    assert memory_diag["boundary_visibility"]["latest_boundary_path"] == "governed_household_memory_boundary"
    assert memory_diag["boundary_visibility"]["latest_boundary_status"] == "active"
    assert memory_diag["boundary_visibility"]["latest_household_memory_role"] == "bounded_record_reference_consumer"
    assert memory_diag["diagnostics_non_rights"]["claims_household_truth_authority"] is False
    assert memory_diag["diagnostics_non_rights"]["claims_identity_authority"] is False
    assert memory_diag["diagnostics_non_rights"]["claims_occupancy_authority"] is False
    assert memory_diag["diagnostics_non_rights"]["claims_messaging_authority"] is False
    assert memory_diag["diagnostics_non_rights"]["claims_consent_authority"] is False
    assert memory_diag["diagnostics_non_rights"]["claims_privacy_authority"] is False
    assert memory_diag["diagnostics_non_rights"]["claims_source_of_truth_authority"] is False
    ownership_consumption_diag = diagnostics[
        "household_memory_ownership_consumption_boundary_visibility"
    ]
    assert ownership_consumption_diag["authority_visibility"]["household_memory_authority_external"] is True
    assert ownership_consumption_diag["authority_visibility"]["identity_authority_external"] is True
    assert ownership_consumption_diag["authority_visibility"]["occupancy_authority_external"] is True
    assert ownership_consumption_diag["authority_visibility"]["messaging_authority_external"] is True
    assert ownership_consumption_diag["authority_visibility"]["consent_authority_external"] is True
    assert ownership_consumption_diag["authority_visibility"]["privacy_authority_external"] is True
    assert ownership_consumption_diag["authority_visibility"]["source_of_truth_authority_external"] is True
    assert ownership_consumption_diag["ownership_visibility"]["ownership_boundary_ref_count"] >= 1
    assert (
        ownership_consumption_diag["ownership_visibility"]["latest_boundary_path"]
        == "governed_household_memory_ownership_consumption_boundary"
    )
    assert ownership_consumption_diag["ownership_visibility"]["latest_boundary_status"] == "active"
    assert ownership_consumption_diag["ownership_visibility"]["latest_memory_owner"] == "household_memory_governance"
    assert ownership_consumption_diag["ownership_visibility"]["latest_memory_runtime_owner"] == "concierge"
    assert ownership_consumption_diag["consumption_visibility"]["consumption_permitted_count"] >= 1
    assert ownership_consumption_diag["consumption_visibility"]["latest_consumption_permitted"] is True
    assert (
        ownership_consumption_diag["consumption_visibility"]["latest_consumption_decision_reason"]
        == "delivery_permitted"
    )
    assert ownership_consumption_diag["ownership_boundary_assertions"]["ownership_is_not_authority"] is True
    assert ownership_consumption_diag["ownership_boundary_assertions"]["ownership_does_not_replace_identity"] is True
    assert ownership_consumption_diag["ownership_boundary_assertions"]["ownership_does_not_replace_occupancy"] is True
    assert ownership_consumption_diag["ownership_boundary_assertions"]["ownership_does_not_replace_messaging"] is True
    assert ownership_consumption_diag["ownership_boundary_assertions"]["ownership_does_not_replace_consent"] is True
    assert ownership_consumption_diag["ownership_boundary_assertions"]["ownership_does_not_replace_privacy"] is True
    assert (
        ownership_consumption_diag["ownership_boundary_assertions"][
            "ownership_does_not_replace_source_of_truth"
        ]
        is True
    )
    assert ownership_consumption_diag["consumption_boundary_assertions"]["consumption_is_not_authority"] is True
    assert (
        ownership_consumption_diag["consumption_boundary_assertions"][
            "consumption_does_not_replace_identity"
        ]
        is True
    )
    assert (
        ownership_consumption_diag["consumption_boundary_assertions"][
            "consumption_does_not_replace_occupancy"
        ]
        is True
    )
    assert (
        ownership_consumption_diag["consumption_boundary_assertions"][
            "consumption_does_not_replace_messaging"
        ]
        is True
    )
    assert (
        ownership_consumption_diag["consumption_boundary_assertions"][
            "consumption_does_not_replace_consent"
        ]
        is True
    )
    assert (
        ownership_consumption_diag["consumption_boundary_assertions"][
            "consumption_does_not_replace_privacy"
        ]
        is True
    )
    assert (
        ownership_consumption_diag["consumption_boundary_assertions"][
            "consumption_does_not_replace_source_of_truth"
        ]
        is True
    )
    assert ownership_consumption_diag["diagnostics_non_rights"]["claims_household_truth_authority"] is False
    assert ownership_consumption_diag["diagnostics_non_rights"]["claims_identity_authority"] is False
    assert ownership_consumption_diag["diagnostics_non_rights"]["claims_occupancy_authority"] is False
    assert ownership_consumption_diag["diagnostics_non_rights"]["claims_messaging_authority"] is False
    assert ownership_consumption_diag["diagnostics_non_rights"]["claims_consent_authority"] is False
    assert ownership_consumption_diag["diagnostics_non_rights"]["claims_privacy_authority"] is False
    assert ownership_consumption_diag["diagnostics_non_rights"]["claims_source_of_truth_authority"] is False
    identity_privacy_retention_diag = diagnostics[
        "household_memory_identity_privacy_retention_separation_visibility"
    ]
    assert identity_privacy_retention_diag["authority_visibility"]["identity_authority_external"] is True
    assert identity_privacy_retention_diag["authority_visibility"]["privacy_authority_external"] is True
    assert identity_privacy_retention_diag["authority_visibility"]["retention_authority_external"] is True
    assert identity_privacy_retention_diag["authority_visibility"]["source_of_truth_authority_external"] is True
    assert identity_privacy_retention_diag["separation_visibility"]["separation_boundary_ref_count"] >= 1
    assert identity_privacy_retention_diag["separation_visibility"]["identity_separation_ref_count"] >= 1
    assert identity_privacy_retention_diag["separation_visibility"]["privacy_separation_ref_count"] >= 1
    assert identity_privacy_retention_diag["separation_visibility"]["retention_separation_ref_count"] >= 1
    assert (
        identity_privacy_retention_diag["separation_visibility"]["latest_boundary_path"]
        == "governed_household_memory_identity_privacy_retention_separation_boundary"
    )
    assert identity_privacy_retention_diag["separation_visibility"]["latest_boundary_status"] == "active"
    assert identity_privacy_retention_diag["separation_visibility"]["latest_identity_separated"] is True
    assert identity_privacy_retention_diag["separation_visibility"]["latest_privacy_separated"] is True
    assert identity_privacy_retention_diag["separation_visibility"]["latest_retention_separated"] is True
    assert (
        identity_privacy_retention_diag["separation_visibility"]["latest_identity_separation_status"]
        == "active"
    )
    assert (
        identity_privacy_retention_diag["separation_visibility"]["latest_privacy_separation_status"]
        == "active"
    )
    assert (
        identity_privacy_retention_diag["separation_visibility"]["latest_retention_separation_status"]
        == "active"
    )
    assert identity_privacy_retention_diag["separation_visibility"]["latest_separation_permitted"] is True
    assert (
        identity_privacy_retention_diag["separation_visibility"]["latest_separation_decision_reason"]
        == "delivery_permitted"
    )
    assert (
        identity_privacy_retention_diag["separation_boundary_assertions"][
            "identity_reference_is_not_authority"
        ]
        is True
    )
    assert (
        identity_privacy_retention_diag["separation_boundary_assertions"][
            "privacy_reference_is_not_authority"
        ]
        is True
    )
    assert (
        identity_privacy_retention_diag["separation_boundary_assertions"][
            "retention_reference_is_not_authority"
        ]
        is True
    )
    assert (
        identity_privacy_retention_diag["separation_boundary_assertions"][
            "separation_does_not_replace_source_of_truth"
        ]
        is True
    )
    assert (
        identity_privacy_retention_diag["separation_boundary_assertions"][
            "separation_does_not_replace_identity"
        ]
        is True
    )
    assert (
        identity_privacy_retention_diag["separation_boundary_assertions"][
            "separation_does_not_replace_privacy"
        ]
        is True
    )
    assert (
        identity_privacy_retention_diag["separation_boundary_assertions"][
            "separation_does_not_replace_retention"
        ]
        is True
    )
    assert (
        identity_privacy_retention_diag["diagnostics_non_rights"]["claims_household_truth_authority"]
        is False
    )
    assert identity_privacy_retention_diag["diagnostics_non_rights"]["claims_identity_authority"] is False
    assert identity_privacy_retention_diag["diagnostics_non_rights"]["claims_privacy_authority"] is False
    assert identity_privacy_retention_diag["diagnostics_non_rights"]["claims_retention_authority"] is False
    assert (
        identity_privacy_retention_diag["diagnostics_non_rights"]["claims_source_of_truth_authority"]
        is False
    )
    messaging_continuity_affinity_occupancy_restoration_diag = diagnostics[
        "household_memory_messaging_continuity_affinity_occupancy_restoration_separation_visibility"
    ]
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["authority_visibility"][
            "messaging_authority_external"
        ]
        is True
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["authority_visibility"][
            "continuity_authority_external"
        ]
        is True
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["authority_visibility"][
            "affinity_authority_external"
        ]
        is True
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["authority_visibility"][
            "occupancy_authority_external"
        ]
        is True
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["authority_visibility"][
            "restoration_authority_external"
        ]
        is True
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["separation_visibility"][
            "separation_boundary_ref_count"
        ]
        >= 1
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["separation_visibility"][
            "messaging_separation_ref_count"
        ]
        >= 1
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["separation_visibility"][
            "continuity_separation_ref_count"
        ]
        >= 1
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["separation_visibility"][
            "affinity_separation_ref_count"
        ]
        >= 1
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["separation_visibility"][
            "occupancy_separation_ref_count"
        ]
        >= 1
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["separation_visibility"][
            "restoration_separation_ref_count"
        ]
        >= 1
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["separation_visibility"][
            "latest_boundary_path"
        ]
        == "governed_household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary"
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["separation_visibility"][
            "latest_messaging_separation_status"
        ]
        == "active"
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["separation_visibility"][
            "latest_continuity_separation_status"
        ]
        == "active"
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["separation_visibility"][
            "latest_affinity_separation_status"
        ]
        == "active"
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["separation_visibility"][
            "latest_occupancy_separation_status"
        ]
        == "active"
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["separation_visibility"][
            "latest_restoration_separation_status"
        ]
        == "active"
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["separation_boundary_assertions"][
            "memory_reference_is_not_messaging_authority"
        ]
        is True
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["separation_boundary_assertions"][
            "memory_reference_is_not_occupancy_authority"
        ]
        is True
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["separation_boundary_assertions"][
            "memory_reference_is_not_restoration_authority"
        ]
        is True
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["diagnostics_non_rights"][
            "claims_household_truth_authority"
        ]
        is False
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["diagnostics_non_rights"][
            "claims_messaging_authority"
        ]
        is False
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["diagnostics_non_rights"][
            "claims_continuity_authority"
        ]
        is False
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["diagnostics_non_rights"][
            "claims_affinity_authority"
        ]
        is False
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["diagnostics_non_rights"][
            "claims_occupancy_authority"
        ]
        is False
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["diagnostics_non_rights"][
            "claims_restoration_authority"
        ]
        is False
    )
    assert (
        messaging_continuity_affinity_occupancy_restoration_diag["diagnostics_non_rights"][
            "claims_source_of_truth_authority"
        ]
        is False
    )
    provenance_diagnostics_explainability_diag = diagnostics[
        "household_memory_provenance_diagnostics_explainability_visibility"
    ]
    assert (
        provenance_diagnostics_explainability_diag["authority_visibility"][
            "household_memory_authority_external"
        ]
        is True
    )
    assert (
        provenance_diagnostics_explainability_diag["authority_visibility"][
            "provenance_authority_external"
        ]
        is True
    )
    assert (
        provenance_diagnostics_explainability_diag["provenance_visibility"][
            "provenance_diagnostics_boundary_ref_count"
        ]
        >= 1
    )
    assert (
        provenance_diagnostics_explainability_diag["provenance_visibility"][
            "messaging_provenance_ref_count"
        ]
        >= 1
    )
    assert (
        provenance_diagnostics_explainability_diag["provenance_visibility"]["latest_boundary_path"]
        == "governed_household_memory_provenance_diagnostics_explainability_boundary"
    )
    assert (
        provenance_diagnostics_explainability_diag["provenance_visibility"]["latest_boundary_status"]
        == "active"
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_visibility"][
            "governance_boundary_ref_count"
        ]
        >= 1
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_visibility"][
            "ownership_boundary_ref_count"
        ]
        >= 1
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_visibility"][
            "consumption_boundary_ref_count"
        ]
        >= 1
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_visibility"][
            "identity_privacy_retention_separation_ref_count"
        ]
        >= 1
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_visibility"][
            "messaging_continuity_affinity_occupancy_restoration_separation_ref_count"
        ]
        >= 1
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_visibility"][
            "provenance_ref_count"
        ]
        >= 1
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_visibility"][
            "latest_governance_status"
        ]
        == "active"
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_visibility"][
            "latest_ownership_status"
        ]
        == "active"
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_visibility"][
            "latest_consumption_status"
        ]
        == "active"
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_visibility"][
            "latest_identity_privacy_retention_separation_status"
        ]
        == "active"
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_visibility"][
            "latest_messaging_continuity_affinity_occupancy_restoration_separation_status"
        ]
        == "active"
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_visibility"][
            "latest_provenance_status"
        ]
        == "active"
    )
    assert (
        provenance_diagnostics_explainability_diag["explainability_visibility"][
            "what_happened_explainable"
        ]
        is True
    )
    assert (
        provenance_diagnostics_explainability_diag["explainability_visibility"][
            "why_it_happened_explainable"
        ]
        is True
    )
    assert (
        provenance_diagnostics_explainability_diag["explainability_visibility"][
            "latest_decision_reason"
        ]
        == "delivery_permitted"
    )
    assert (
        provenance_diagnostics_explainability_diag["explainability_visibility"][
            "latest_governance_boundary_involved"
        ]
        == "notification_delivery_boundary"
    )
    assert (
        provenance_diagnostics_explainability_diag["explainability_visibility"][
            "runtime_derived_only"
        ]
        is True
    )
    assert (
        provenance_diagnostics_explainability_diag["explainability_visibility"][
            "generated_reasoning_used"
        ]
        is False
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_non_rights"][
            "claims_household_truth_authority"
        ]
        is False
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_non_rights"][
            "claims_identity_authority"
        ]
        is False
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_non_rights"][
            "claims_messaging_authority"
        ]
        is False
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_non_rights"][
            "claims_continuity_authority"
        ]
        is False
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_non_rights"][
            "claims_affinity_authority"
        ]
        is False
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_non_rights"][
            "claims_occupancy_authority"
        ]
        is False
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_non_rights"][
            "claims_privacy_authority"
        ]
        is False
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_non_rights"][
            "claims_retention_authority"
        ]
        is False
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_non_rights"][
            "claims_restoration_authority"
        ]
        is False
    )
    assert (
        provenance_diagnostics_explainability_diag["diagnostics_non_rights"][
            "claims_source_of_truth_authority"
        ]
        is False
    )
    assert notify_calls[0]["message"] == "Hello Tom"


async def test_diagnostics_expose_vocabulary_ambiguity_visibility(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Diagnostics should expose bounded vocabulary ambiguity visibility from config and outcomes."""
    storage = ConciergeStorage(hass)
    area = ar.async_get(hass).async_create(name="Gallery")
    await storage.async_update_global_feature(
        feature_key="room_vocabulary_registry",
        enabled=True,
        options={
            "entries": [
                {
                    "term": "gallery",
                    "aliases": ["art room"],
                    "area_id": area.id,
                },
                {
                    "term": "display room",
                    "aliases": ["art room"],
                    "area_id": area.id,
                },
            ]
        },
    )

    with pytest.raises(Exception):
        await hass.services.async_call(
            DOMAIN,
            "execute",
            {
                "target": "light.gallery",
                "area_id": "art room",
                "intent_class": "home_control",
            },
            blocking=True,
        )

    diagnostics = await async_get_config_entry_diagnostics(hass, setup_integration)
    ambiguity = diagnostics["vocabulary_diagnostics_visibility"]["ambiguity_visibility"]

    assert ambiguity["known_config_ambiguity_count"] >= 1
    assert ambiguity["recent_ambiguity_event_count"] >= 1
    latest_event = ambiguity["recent_ambiguity_events"][0]
    assert "ambiguous" in latest_event["outcome_reason"]