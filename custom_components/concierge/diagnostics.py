"""Diagnostics support for Concierge."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN
from .const import VOICE_ENROLLMENT_CLEANUP_RESULT_ALREADY_CLEAN
from .const import VOICE_ENROLLMENT_CLEANUP_RESULT_COMPLETE
from .const import VOICE_ENROLLMENT_MANIFEST_SCHEMA_VERSION
from .enrollment_orchestrator import EnrollmentOrchestrator
from .enrollment_orchestrator import resolve_enrollment_storage_provider_from_entry
from .enrollment_storage import MountedPathEnrollmentStorageProvider
from .enrollment_telemetry import build_operational_telemetry
from .services import _assemble_foundation_context
from .services import _build_capture_knowledge_consumption_boundary
from .services import _build_calendar_email_consumption_boundary
from .services import _build_briefing_composition_boundary
from .services import _build_household_coordination_boundary
from .services import _build_household_status_synthesis_boundary
from .services import _build_person_aware_productivity_routing
from .services import _build_productivity_coordination_boundary
from .services import _build_productivity_source_of_record_boundary
from .services import _build_release_6_provenance_diagnostics_explainability_boundary
from .services import _build_release_6_provenance_ownership_consumption_boundary
from .services import _build_runtime_person_context
from .services import _build_task_shopping_consumption_boundary
from .voice_identity_bridge import async_get_voice_identity_enrollment_status
from .storage import ConciergeStorage


def _provider_from_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> MountedPathEnrollmentStorageProvider | None:
    return resolve_enrollment_storage_provider_from_entry(hass, config_entry)


def _active_session_count(state) -> int:
    inactive_states = {"idle", "cleanup_complete"}
    return sum(1 for session in state.enrollment_sessions.values() if session.state not in inactive_states)


def _count_summary(values: list[str]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for value in values:
        key = str(value or "unknown")
        summary[key] = summary.get(key, 0) + 1
    return summary


def _last_cleanup_result_code(state) -> str | None:
    latest_timestamp = ""
    latest_result: str | None = None
    for session in state.enrollment_sessions.values():
        completed_at = str(session.metadata.get("cleanup_completed_at", "") or "")
        result_code = str(session.metadata.get("cleanup_result_code", "") or "")
        if completed_at and result_code and completed_at >= latest_timestamp:
            latest_timestamp = completed_at
            latest_result = result_code
    return latest_result


def _cleanup_counters(state) -> tuple[int, int, int]:
    attempt_count = 0
    success_count = 0
    failure_count = 0
    for session in state.enrollment_sessions.values():
        result_code = str(session.metadata.get("cleanup_result_code", "") or "")
        if not result_code:
            continue
        attempt_count += 1
        if result_code in {VOICE_ENROLLMENT_CLEANUP_RESULT_COMPLETE, VOICE_ENROLLMENT_CLEANUP_RESULT_ALREADY_CLEAN}:
            success_count += 1
        else:
            failure_count += 1
    return attempt_count, success_count, failure_count


def _reconciliation_status(result: Any) -> str:
    if result is None:
        return "not_run"
    if not bool(getattr(result, "storage_available", False)):
        return "storage_unavailable"
    if int(getattr(result, "cleanup_failed_count", 0) or 0) > 0:
        return "completed_with_cleanup_failures"
    if int(getattr(result, "invalid_manifest_count", 0) or 0) > 0:
        return "completed_with_invalid_manifests"
    if int(getattr(result, "orphan_count", 0) or 0) > 0:
        return "completed_with_orphans"
    return "completed"


def _repairs_health(hass: HomeAssistant) -> dict[str, Any]:
    registry = ir.async_get(hass)
    issues = getattr(registry, "issues", {})
    active_types = sorted(
        issue.issue_id
        for issue in issues.values()
        if getattr(issue, "domain", "") == DOMAIN
    )
    return {
        "active_repairs_issue_count": len(active_types),
        "active_repairs_issue_types": active_types,
    }


async def _voice_identity_linkage_setup_boundary_visibility(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> dict[str, Any]:
    linked = bool(
        config_entry.options.get(
            "voice_identity_linked",
            config_entry.data.get("voice_identity_linked", False),
        )
    )
    voice_identity_loaded = isinstance(hass.data.get("voice_identity"), dict)

    if not linked:
        return {
            "linkage_configured": False,
            "voice_identity_loaded": voice_identity_loaded,
            "voice_identity_connected": False,
            "voice_identity_available": False,
            "voice_identity_compatible": False,
            "voice_identity_discovery_state": "unavailable",
            "voice_identity_enabled_capabilities": (),
            "voice_identity_supported_capabilities": (),
            "voice_identity_reason_code": "voice_identity_linkage_disabled",
            "voice_identity_status_summary": "Voice Identity linkage is disabled in Concierge options.",
            "safe_fallback_mode_active": True,
        }

    voice_identity_status = await async_get_voice_identity_enrollment_status(hass)
    return {
        "linkage_configured": True,
        "voice_identity_loaded": voice_identity_loaded,
        "voice_identity_connected": bool(voice_identity_status.get("voice_identity_connected", False)),
        "voice_identity_available": bool(voice_identity_status.get("voice_identity_available", False)),
        "voice_identity_compatible": bool(voice_identity_status.get("voice_identity_compatible", False)),
        "voice_identity_discovery_state": str(voice_identity_status.get("voice_identity_discovery_state", "unavailable")),
        "voice_identity_enabled_capabilities": tuple(voice_identity_status.get("voice_identity_enabled_capabilities", ())),
        "voice_identity_supported_capabilities": tuple(voice_identity_status.get("voice_identity_supported_capabilities", ())),
        "voice_identity_reason_code": str(voice_identity_status.get("voice_enrollment_reason_code", "voice_identity_unavailable")),
        "voice_identity_status_summary": str(
            voice_identity_status.get(
                "voice_enrollment_status_summary",
                "Voice Identity linkage is unavailable.",
            )
        ),
        "safe_fallback_mode_active": not bool(voice_identity_status.get("voice_enrollment_enabled", False)),
    }


def _foundation_runtime_boundary(hass: HomeAssistant, state) -> dict[str, Any]:
    """Return non-sensitive boundary evidence for Foundation-owned room truth."""
    foundation_area_ids = {area.id for area in ar.async_get(hass).async_list_areas()}
    configured_room_outside_foundation_count = sum(
        1 for area_id in state.rooms if area_id not in foundation_area_ids
    )
    composites_with_missing_area_count = sum(
        1
        for composite in state.composites.values()
        if any(area_id not in foundation_area_ids for area_id in composite.area_ids)
    )
    return {
        "room_identity_source": "home_assistant_area_registry",
        "concierge_role": "bounded_consumer_orchestrator",
        "foundation_area_count": len(foundation_area_ids),
        "configured_room_count": len(state.rooms),
        "composite_count": len(state.composites),
        "configured_room_outside_foundation_count": configured_room_outside_foundation_count,
        "composites_with_missing_area_count": composites_with_missing_area_count,
        "room_configs_bound_to_foundation": configured_room_outside_foundation_count == 0,
        "composites_bound_to_foundation": composites_with_missing_area_count == 0,
    }


def _context_assembly_visibility(state) -> dict[str, Any]:
    """Return bounded visibility into current context-assembly outcomes."""
    active_context_types = sorted(
        context.context_type
        for context in state.contexts.values()
        if getattr(context, "available", False)
    )
    active_signal_types = sorted(
        signal.signal_type
        for signal in state.signals.values()
        if getattr(signal, "available", False)
    )

    room_projection_samples: list[dict[str, Any]] = []
    for area_id in sorted(state.rooms)[:10]:
        assembled = _assemble_foundation_context(
            state,
            requested_area_id=area_id,
            include_context=True,
            include_signals=True,
        )
        room_projection_samples.append(
            {
                "requested_area_id": area_id,
                "context_area_id": assembled.get("context_area_id"),
                "resolved_composite_id": assembled.get("resolved_composite_id"),
                "context_source_count": assembled.get("context_source_count", 0),
                "signal_count": assembled.get("signal_count", 0),
            }
        )

    composite_projection_samples: list[dict[str, Any]] = []
    for composite_id in sorted(state.composites)[:10]:
        composite = state.composites[composite_id]
        if not composite.enabled or not composite.area_ids:
            continue
        assembled = _assemble_foundation_context(
            state,
            requested_area_id=composite.area_ids[0],
            composite_id=composite_id,
            include_context=True,
            include_signals=True,
        )
        composite_projection_samples.append(
            {
                "composite_id": composite_id,
                "context_area_id": assembled.get("context_area_id"),
                "member_count": len(composite.area_ids),
                "context_source_count": assembled.get("context_source_count", 0),
                "signal_count": assembled.get("signal_count", 0),
            }
        )

    return {
        "configured_room_projection_count": len(state.rooms),
        "enabled_composite_projection_count": sum(1 for composite in state.composites.values() if composite.enabled),
        "active_context_types": active_context_types,
        "active_signal_types": active_signal_types,
        "room_projection_samples": room_projection_samples,
        "composite_projection_samples": composite_projection_samples,
    }


def _ref_by_type(activity, ref_type: str) -> dict[str, Any] | None:
    for ref in getattr(activity, "external_refs", []):
        if str(ref.get("ref_type", "")) == ref_type:
            return dict(ref)
    return None


def _serialize_execution_activity(activity) -> dict[str, Any]:
    envelope_ref = _ref_by_type(activity, "execution_envelope") or {}
    routing_ref = _ref_by_type(activity, "routing_decision") or {}
    context_ref = _ref_by_type(activity, "context_assembly") or {}
    return {
        "started_at": getattr(activity, "started_at", None),
        "outcome": getattr(activity, "outcome", None),
        "intent_class": getattr(activity, "intent_class", None),
        "execution_kind": envelope_ref.get("execution_kind"),
        "plan_kind": envelope_ref.get("plan_kind"),
        "execution_domain": envelope_ref.get("execution_domain"),
        "execution_service": envelope_ref.get("execution_service"),
        "route_scope": routing_ref.get("route_scope"),
        "requested_area_id": routing_ref.get("requested_area_id"),
        "context_area_id": routing_ref.get("context_area_id"),
        "resolved_composite_id": routing_ref.get("resolved_composite_id"),
        "execution_preference_scope_id": routing_ref.get("execution_preference_scope_id"),
        "execution_preference_present": routing_ref.get("execution_preference_present"),
        "context_source_count": context_ref.get("context_source_count"),
        "signal_count": context_ref.get("signal_count"),
    }


def _execution_explainability(state) -> dict[str, Any]:
    """Return bounded visibility into routing and execution-envelope outcomes."""
    orchestration = sorted(
        [activity for activity in state.activities.values() if activity.intent_class == "execute_orchestration"],
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    )
    direct = sorted(
        [activity for activity in state.activities.values() if activity.intent_class == "execute_direct"],
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    )
    return {
        "orchestration_activity_count": len(orchestration),
        "direct_activity_count": len(direct),
        "latest_orchestration": _serialize_execution_activity(orchestration[0]) if orchestration else None,
        "latest_direct": _serialize_execution_activity(direct[0]) if direct else None,
    }


def _vocabulary_ambiguity_visibility(state) -> dict[str, Any]:
    """Return bounded ambiguity visibility from recent activity outcomes and configured vocabulary inputs."""
    known_conflicts: list[dict[str, Any]] = []

    room_options = state.global_features.get("room_vocabulary_registry", {}).get("options", {})
    room_entries = room_options.get("entries", []) if isinstance(room_options, dict) else []
    if isinstance(room_entries, list):
        alias_map: dict[tuple[str, str | None, str | None], set[str]] = {}
        for entry in room_entries:
            if not isinstance(entry, dict):
                continue
            area_id = str(entry.get("area_id", "") or "").strip() or None
            composite_id = str(entry.get("composite_id", "") or "").strip() or None
            aliases = entry.get("aliases", [])
            if not isinstance(aliases, list):
                continue
            for alias in aliases:
                alias_text = ""
                if isinstance(alias, str):
                    alias_text = alias.strip().lower()
                elif isinstance(alias, dict):
                    alias_text = str(alias.get("alias_term", "") or "").strip().lower()
                if not alias_text:
                    continue
                key = (alias_text, area_id, composite_id)
                alias_map.setdefault(key, set()).add(str(entry.get("term", "") or "").strip())

        for (alias_text, area_id, composite_id), canonical_terms in sorted(alias_map.items()):
            if len(canonical_terms) <= 1:
                continue
            known_conflicts.append(
                {
                    "vocabulary_type": "room",
                    "alias": alias_text,
                    "scope_area_id": area_id,
                    "scope_composite_id": composite_id,
                    "canonical_term_count": len(canonical_terms),
                }
            )

    recent_ambiguity_events: list[dict[str, Any]] = []
    for activity in sorted(
        state.activities.values(),
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        reason = str(getattr(activity, "outcome_reason", "") or "")
        if "ambiguous" not in reason:
            continue
        recent_ambiguity_events.append(
            {
                "started_at": getattr(activity, "started_at", None),
                "intent_class": getattr(activity, "intent_class", None),
                "outcome": getattr(activity, "outcome", None),
                "outcome_reason": reason,
            }
        )
        if len(recent_ambiguity_events) >= 10:
            break

    return {
        "known_config_ambiguity_count": len(known_conflicts),
        "known_config_ambiguity_samples": known_conflicts[:10],
        "recent_ambiguity_event_count": len(recent_ambiguity_events),
        "recent_ambiguity_events": recent_ambiguity_events,
    }


def _vocabulary_diagnostics_visibility(state) -> dict[str, Any]:
    """Return bounded diagnostics/explainability visibility for vocabulary and handoff consumption."""
    room_entries = state.global_features.get("room_vocabulary_registry", {}).get("options", {}).get("entries", [])
    device_entries = state.global_features.get("device_entity_vocabulary_registry", {}).get("options", {}).get("entries", [])
    asset_entries = state.global_features.get("asset_vocabulary_registry", {}).get("options", {}).get("entries", [])

    room_resolution_count = 0
    device_resolution_count = 0
    asset_resolution_count = 0
    latest_room_resolution: dict[str, Any] | None = None
    latest_device_resolution: dict[str, Any] | None = None
    latest_asset_resolution: dict[str, Any] | None = None

    for activity in sorted(
        state.activities.values(),
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        refs = list(getattr(activity, "external_refs", []))
        for ref in refs:
            ref_type = str(ref.get("ref_type", "") or "")
            if ref_type == "room_vocabulary_resolution":
                room_resolution_count += 1
                if latest_room_resolution is None:
                    latest_room_resolution = {
                        "started_at": getattr(activity, "started_at", None),
                        "matched_term": ref.get("matched_term"),
                        "canonical_term": ref.get("canonical_term"),
                        "resolved_area_id": ref.get("resolved_area_id"),
                        "resolved_composite_id": ref.get("resolved_composite_id"),
                        "source": ref.get("source"),
                    }
            elif ref_type == "device_entity_vocabulary_resolution":
                device_resolution_count += 1
                if latest_device_resolution is None:
                    latest_device_resolution = {
                        "started_at": getattr(activity, "started_at", None),
                        "matched_term": ref.get("matched_term"),
                        "canonical_term": ref.get("canonical_term"),
                        "resolved_entity_id": ref.get("resolved_entity_id"),
                        "resolved_area_id": ref.get("resolved_area_id"),
                        "resolved_composite_id": ref.get("resolved_composite_id"),
                        "source": ref.get("source"),
                    }
            elif ref_type == "asset_vocabulary_resolution":
                asset_resolution_count += 1
                if latest_asset_resolution is None:
                    latest_asset_resolution = {
                        "started_at": getattr(activity, "started_at", None),
                        "matched_term": ref.get("matched_term"),
                        "canonical_term": ref.get("canonical_term"),
                        "asset_id": ref.get("asset_id"),
                        "resolved_entity_id": ref.get("resolved_entity_id"),
                        "resolved_area_id": ref.get("resolved_area_id"),
                        "resolved_composite_id": ref.get("resolved_composite_id"),
                        "source": ref.get("source"),
                    }

    ambiguity_visibility = _vocabulary_ambiguity_visibility(state)

    return {
        "authority_visibility": {
            "room_vocabulary_authority": "room_vocabulary_registry",
            "device_entity_vocabulary_authority": "device_entity_vocabulary_registry",
            "asset_handoff_authority": "asset_intelligence_handoff",
            "concierge_role": "bounded_consumer_orchestrator",
        },
        "configured_entry_counts": {
            "room_vocabulary_entries": len(room_entries) if isinstance(room_entries, list) else 0,
            "device_entity_vocabulary_entries": len(device_entries) if isinstance(device_entries, list) else 0,
            "asset_vocabulary_entries": len(asset_entries) if isinstance(asset_entries, list) else 0,
        },
        "resolution_visibility": {
            "room_resolution_count": room_resolution_count,
            "device_entity_resolution_count": device_resolution_count,
            "asset_handoff_resolution_count": asset_resolution_count,
            "latest_room_resolution": latest_room_resolution,
            "latest_device_entity_resolution": latest_device_resolution,
            "latest_asset_handoff_resolution": latest_asset_resolution,
        },
        "ambiguity_visibility": ambiguity_visibility,
        "asset_intelligence_boundary": {
            "handoff_source_visible": True,
            "asset_evaluation_logic_visible": False,
            "asset_scoring_visible": False,
            "asset_significance_logic_visible": False,
            "asset_advisory_reasoning_visible": False,
        },
    }


def _capability_diagnostics_explainability_visibility(state) -> dict[str, Any]:
    """Return bounded capability diagnostics and explainability visibility from existing activity refs."""
    execution_envelope_refs: list[dict[str, Any]] = []
    routing_ref_count = 0
    context_ref_count = 0
    room_resolution_count = 0
    device_resolution_count = 0
    asset_resolution_count = 0
    cp00_handoff_count = 0

    for activity in sorted(
        state.activities.values(),
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        refs = list(getattr(activity, "external_refs", []))
        for ref in refs:
            ref_type = str(ref.get("ref_type", "") or "")
            if ref_type == "execution_envelope":
                execution_envelope_refs.append(dict(ref))
            elif ref_type == "routing_decision":
                routing_ref_count += 1
            elif ref_type == "context_assembly":
                context_ref_count += 1
            elif ref_type == "room_vocabulary_resolution":
                room_resolution_count += 1
            elif ref_type == "device_entity_vocabulary_resolution":
                device_resolution_count += 1
            elif ref_type == "asset_vocabulary_resolution":
                asset_resolution_count += 1
            elif ref_type == "asset_intelligence_cp00_handoff":
                cp00_handoff_count += 1

    latest_envelope = execution_envelope_refs[0] if execution_envelope_refs else None
    latest_discovered_capabilities = (
        list(latest_envelope.get("discoverable_capability_ids", []))
        if latest_envelope is not None
        else []
    )

    return {
        "authority_visibility": {
            "capability_authority_origin": (
                latest_envelope.get("capability_authority_origin")
                if latest_envelope is not None
                else "htbw_governed_contracts_and_models"
            ),
            "vocabulary_authority_external": True,
            "asset_intelligence_authority_external": True,
            "concierge_role": "bounded_consumer_orchestrator",
        },
        "discovery_visibility": {
            "execution_envelope_ref_count": len(execution_envelope_refs),
            "latest_capability_discovery_applicable": (
                bool(latest_envelope.get("capability_discovery_applicable", False))
                if latest_envelope is not None
                else False
            ),
            "latest_capability_discovery_path": (
                latest_envelope.get("capability_discovery_path")
                if latest_envelope is not None
                else None
            ),
            "latest_discovered_capability_ids": latest_discovered_capabilities,
            "latest_discovered_capability_count": len(latest_discovered_capabilities),
        },
        "handoff_visibility": {
            "room_vocabulary_resolution_count": room_resolution_count,
            "device_entity_vocabulary_resolution_count": device_resolution_count,
            "asset_vocabulary_resolution_count": asset_resolution_count,
            "asset_intelligence_cp00_handoff_count": cp00_handoff_count,
            "latest_asset_cp00_handoff_applicable": (
                bool(latest_envelope.get("asset_cp00_handoff_applicable", False))
                if latest_envelope is not None
                else False
            ),
        },
        "traceability_visibility": {
            "routing_decision_ref_count": routing_ref_count,
            "context_assembly_ref_count": context_ref_count,
            "execution_envelope_ref_count": len(execution_envelope_refs),
        },
        "diagnostics_non_rights": {
            "creates_authority": False,
            "creates_outcomes": False,
            "recreates_capability_reasoning": False,
            "recreates_asset_intelligence_reasoning": False,
            "asset_evaluation_visible": False,
            "asset_scoring_visible": False,
            "asset_significance_reasoning_visible": False,
        },
    }


def _experience_diagnostics_explainability_visibility(state) -> dict[str, Any]:
    """Return bounded diagnostics/explainability visibility for E6 experience surfaces."""
    execution_envelope_refs: list[dict[str, Any]] = []
    routing_ref_count = 0
    context_ref_count = 0

    for activity in sorted(
        state.activities.values(),
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        refs = list(getattr(activity, "external_refs", []))
        for ref in refs:
            ref_type = str(ref.get("ref_type", "") or "")
            if ref_type == "execution_envelope":
                execution_envelope_refs.append(dict(ref))
            elif ref_type == "routing_decision":
                routing_ref_count += 1
            elif ref_type == "context_assembly":
                context_ref_count += 1

    latest_envelope = execution_envelope_refs[0] if execution_envelope_refs else None
    latest_discoverable_capabilities = (
        list(latest_envelope.get("discoverable_capability_ids", []))
        if latest_envelope is not None
        else []
    )

    return {
        "authority_visibility": {
            "capability_authority_origin": (
                latest_envelope.get("capability_authority_origin")
                if latest_envelope is not None
                else "htbw_governed_contracts_and_models"
            ),
            "vocabulary_authority_external": True,
            "asset_intelligence_authority_external": True,
            "experience_authority_external": True,
            "concierge_role": "bounded_consumer_orchestrator",
        },
        "governance_visibility": {
            "latest_experience_governance_applicable": (
                bool(latest_envelope.get("experience_governance_applicable", False))
                if latest_envelope is not None
                else False
            ),
            "latest_experience_governance_path": (
                latest_envelope.get("experience_governance_path")
                if latest_envelope is not None
                else None
            ),
            "latest_experience_consumes_capability_outputs": (
                bool(latest_envelope.get("experience_consumes_capability_outputs", False))
                if latest_envelope is not None
                else False
            ),
            "latest_experience_redefines_capability_outputs": (
                bool(latest_envelope.get("experience_redefines_capability_outputs", False))
                if latest_envelope is not None
                else False
            ),
        },
        "handoff_visibility": {
            "latest_capability_to_experience_handoff_applicable": (
                bool(latest_envelope.get("capability_to_experience_handoff_applicable", False))
                if latest_envelope is not None
                else False
            ),
            "latest_capability_to_experience_handoff_path": (
                latest_envelope.get("capability_to_experience_handoff_path")
                if latest_envelope is not None
                else None
            ),
            "latest_experience_consumption_ready": (
                bool(latest_envelope.get("experience_consumption_ready", False))
                if latest_envelope is not None
                else False
            ),
            "latest_handoff_transfers_authority": (
                bool(latest_envelope.get("handoff_transfers_authority", False))
                if latest_envelope is not None
                else False
            ),
            "latest_discoverable_capability_ids": latest_discoverable_capabilities,
            "latest_discoverable_capability_count": len(latest_discoverable_capabilities),
        },
        "projection_visibility": {
            "latest_experience_projection_applicable": (
                bool(latest_envelope.get("experience_projection_applicable", False))
                if latest_envelope is not None
                else False
            ),
            "latest_experience_projection_path": (
                latest_envelope.get("experience_projection_path")
                if latest_envelope is not None
                else None
            ),
            "latest_projected_experience_count": (
                int(latest_envelope.get("projected_experience_count", 0) or 0)
                if latest_envelope is not None
                else 0
            ),
            "latest_projection_is_authority": (
                bool(latest_envelope.get("projection_is_authority", False))
                if latest_envelope is not None
                else False
            ),
        },
        "restoration_visibility": {
            "latest_experience_restoration_boundary_applicable": (
                bool(latest_envelope.get("experience_restoration_boundary_applicable", False))
                if latest_envelope is not None
                else False
            ),
            "latest_experience_restoration_path": (
                latest_envelope.get("experience_restoration_path")
                if latest_envelope is not None
                else None
            ),
            "latest_restoration_governance_path": (
                latest_envelope.get("restoration_governance_path")
                if latest_envelope is not None
                else None
            ),
            "latest_restoration_eligible": (
                bool(latest_envelope.get("restoration_eligible", False))
                if latest_envelope is not None
                else False
            ),
            "latest_restoration_authority_external": (
                bool(latest_envelope.get("restoration_authority_external", False))
                if latest_envelope is not None
                else False
            ),
            "latest_restoration_policy_authority_external": (
                bool(latest_envelope.get("restoration_policy_authority_external", False))
                if latest_envelope is not None
                else False
            ),
            "latest_restoration_owns_identity": (
                bool(latest_envelope.get("restoration_owns_identity", False))
                if latest_envelope is not None
                else False
            ),
            "latest_restoration_owns_occupancy": (
                bool(latest_envelope.get("restoration_owns_occupancy", False))
                if latest_envelope is not None
                else False
            ),
            "latest_restoration_owns_continuity": (
                bool(latest_envelope.get("restoration_owns_continuity", False))
                if latest_envelope is not None
                else False
            ),
            "latest_restoration_owns_affinity": (
                bool(latest_envelope.get("restoration_owns_affinity", False))
                if latest_envelope is not None
                else False
            ),
            "latest_restoration_owns_household_memory": (
                bool(latest_envelope.get("restoration_owns_household_memory", False))
                if latest_envelope is not None
                else False
            ),
            "latest_restoration_execution_enabled": (
                bool(latest_envelope.get("restoration_execution_enabled", False))
                if latest_envelope is not None
                else False
            ),
            "latest_restoration_decision_behavior_enabled": (
                bool(latest_envelope.get("restoration_decision_behavior_enabled", False))
                if latest_envelope is not None
                else False
            ),
            "latest_restoration_authority_transferred": (
                bool(latest_envelope.get("restoration_authority_transferred", False))
                if latest_envelope is not None
                else False
            ),
        },
        "traceability_visibility": {
            "execution_envelope_ref_count": len(execution_envelope_refs),
            "routing_decision_ref_count": routing_ref_count,
            "context_assembly_ref_count": context_ref_count,
        },
        "diagnostics_non_rights": {
            "creates_authority": False,
            "creates_outcomes": False,
            "recreates_projection_reasoning": False,
            "recreates_restoration_reasoning": False,
            "recreates_external_authority_reasoning": False,
            "restoration_decision_logic_visible": False,
            "projection_decision_logic_visible": False,
            "external_scoring_logic_visible": False,
            "external_significance_reasoning_visible": False,
        },
    }


def _voice_identity_consumption_boundary_visibility(state) -> dict[str, Any]:
    """Return bounded visibility into Voice Identity attribution/confidence consumption."""
    execution_envelope_refs: list[dict[str, Any]] = []

    for activity in sorted(
        state.activities.values(),
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        for ref in list(getattr(activity, "external_refs", [])):
            if str(ref.get("ref_type", "") or "") == "execution_envelope":
                execution_envelope_refs.append(dict(ref))

    latest_envelope = execution_envelope_refs[0] if execution_envelope_refs else None

    active_person_resolution_visibility = {
        "active_person_state": "active_person_unavailable",
        "active_person_available": False,
        "resolved_person_id": None,
        "resolved_voice_profile_id": None,
        "attribution_available": False,
        "confidence_available": False,
        "confidence_accepted": False,
        "confidence_value": None,
        "confidence_band": None,
        "readiness_state": "unavailable",
        "reason_code": "no_execution_envelope",
        "resolution_posture": "fail_closed",
        "fail_closed": True,
        "authority_source": "voice_identity",
        "consumption_only": True,
    }

    if latest_envelope is not None:
        attribution_consumed = bool(latest_envelope.get("voice_identity_attribution_consumed", False))
        attribution_state = str(latest_envelope.get("voice_identity_attribution_state", "") or "").strip().lower()
        attribution_reason = str(latest_envelope.get("voice_identity_attribution_reason_code", "") or "").strip().lower()
        person_id = str(latest_envelope.get("voice_identity_attribution_person_id", "") or "").strip() or None
        voice_profile_id = str(
            latest_envelope.get("voice_identity_attribution_voice_profile_id", "") or ""
        ).strip() or None
        confidence_consumed = bool(latest_envelope.get("voice_identity_confidence_consumed", False))
        confidence_value = latest_envelope.get("voice_identity_confidence_value")
        try:
            confidence_value = float(confidence_value) if confidence_value is not None else None
        except (TypeError, ValueError):
            confidence_value = None
        confidence_band = str(latest_envelope.get("voice_identity_confidence_band", "") or "").strip().lower() or None
        readiness_raw = str(latest_envelope.get("voice_identity_attribution_readiness", "") or "").strip().lower()
        readiness_state = readiness_raw or "unspecified"

        ambiguous = bool(
            attribution_state == "low_confidence"
            or confidence_band in {"low", "ambiguous"}
            or attribution_reason in {"low_confidence", "ambiguous_match"}
        )
        unavailable = bool(
            (readiness_raw and readiness_raw != "ready")
            or attribution_state == "unavailable"
            or attribution_reason in {
                "voice_identity_not_loaded",
                "voice_identity_linkage_disabled",
                "attribution_service_unavailable",
                "identity_context_service_unavailable",
                "attribution_unavailable",
                "attribution_not_ready",
            }
        )
        available = bool(attribution_consumed and person_id)

        if available:
            resolution_state = "active_person_available"
            reason_code = attribution_reason or "attribution_ready"
        elif ambiguous:
            resolution_state = "active_person_ambiguous"
            reason_code = attribution_reason or "low_confidence"
        elif unavailable:
            resolution_state = "active_person_unavailable"
            reason_code = attribution_reason or "attribution_unavailable"
        else:
            resolution_state = "active_person_unknown"
            reason_code = attribution_reason or "identity_unknown"

        confidence_accepted = bool(
            available
            and confidence_consumed
            and confidence_band not in {"low", "ambiguous", "unknown", "unavailable", "no_match"}
        )

        active_person_resolution_visibility = {
            "active_person_state": resolution_state,
            "active_person_available": available,
            "resolved_person_id": person_id if available else None,
            "resolved_voice_profile_id": voice_profile_id if available else None,
            "attribution_available": attribution_consumed,
            "confidence_available": confidence_consumed,
            "confidence_accepted": confidence_accepted,
            "confidence_value": confidence_value,
            "confidence_band": confidence_band,
            "readiness_state": readiness_state,
            "reason_code": reason_code,
            "resolution_posture": "resolved" if available else "fail_closed",
            "fail_closed": not available,
            "authority_source": "voice_identity",
            "consumption_only": True,
        }

    return {
        "authority_visibility": {
            "voice_identity_authority_external": (
                bool(latest_envelope.get("voice_identity_authority_external", False))
                if latest_envelope is not None
                else False
            ),
            "voice_identity_enrollment_authority_external": (
                bool(latest_envelope.get("voice_identity_enrollment_authority_external", False))
                if latest_envelope is not None
                else False
            ),
            "voice_identity_permission_authority_external": (
                bool(latest_envelope.get("voice_identity_permission_authority_external", False))
                if latest_envelope is not None
                else False
            ),
            "voice_identity_legacy_disposition_authority_external": (
                bool(latest_envelope.get("voice_identity_legacy_disposition_authority_external", False))
                if latest_envelope is not None
                else False
            ),
            "voice_identity_diagnostics_authority_external": (
                bool(latest_envelope.get("voice_identity_diagnostics_authority_external", False))
                if latest_envelope is not None
                else False
            ),
            "voice_identity_explainability_authority_external": (
                bool(latest_envelope.get("voice_identity_explainability_authority_external", False))
                if latest_envelope is not None
                else False
            ),
            "concierge_role": "bounded_consumer_orchestrator",
        },
        "consumption_visibility": {
            "execution_envelope_ref_count": len(execution_envelope_refs),
            "latest_boundary_path": (
                latest_envelope.get("voice_identity_consumption_boundary_path")
                if latest_envelope is not None
                else None
            ),
            "latest_consumption_only": (
                bool(latest_envelope.get("voice_identity_consumption_only", False))
                if latest_envelope is not None
                else False
            ),
            "latest_attribution_consumed": (
                bool(latest_envelope.get("voice_identity_attribution_consumed", False))
                if latest_envelope is not None
                else False
            ),
            "latest_attribution_state": (
                latest_envelope.get("voice_identity_attribution_state")
                if latest_envelope is not None
                else None
            ),
            "latest_attribution_reason_code": (
                latest_envelope.get("voice_identity_attribution_reason_code")
                if latest_envelope is not None
                else None
            ),
            "latest_confidence_consumed": (
                bool(latest_envelope.get("voice_identity_confidence_consumed", False))
                if latest_envelope is not None
                else False
            ),
            "latest_confidence_value": (
                latest_envelope.get("voice_identity_confidence_value")
                if latest_envelope is not None
                else None
            ),
            "latest_confidence_band": (
                latest_envelope.get("voice_identity_confidence_band")
                if latest_envelope is not None
                else None
            ),
            "latest_confidence_reason_code": (
                latest_envelope.get("voice_identity_confidence_reason_code")
                if latest_envelope is not None
                else None
            ),
            "active_person_resolution": active_person_resolution_visibility,
        },
        "enrollment_boundary_visibility": {
            "latest_boundary_path": (
                latest_envelope.get("voice_identity_enrollment_lifecycle_boundary_path")
                if latest_envelope is not None
                else None
            ),
            "latest_consumption_only": (
                bool(latest_envelope.get("voice_identity_enrollment_lifecycle_consumption_only", False))
                if latest_envelope is not None
                else False
            ),
            "latest_enrollment_state_consumed": (
                bool(latest_envelope.get("voice_identity_enrollment_state_consumed", False))
                if latest_envelope is not None
                else False
            ),
            "latest_enrollment_state": (
                latest_envelope.get("voice_identity_enrollment_state")
                if latest_envelope is not None
                else None
            ),
            "latest_enrollment_readiness": (
                latest_envelope.get("voice_identity_enrollment_readiness")
                if latest_envelope is not None
                else None
            ),
            "latest_enrollment_reason_code": (
                latest_envelope.get("voice_identity_enrollment_reason_code")
                if latest_envelope is not None
                else None
            ),
        },
        "lifecycle_boundary_visibility": {
            "latest_lifecycle_state_consumed": (
                bool(latest_envelope.get("voice_identity_lifecycle_state_consumed", False))
                if latest_envelope is not None
                else False
            ),
            "latest_enrollment_lifecycle_state": (
                latest_envelope.get("voice_identity_enrollment_lifecycle_state")
                if latest_envelope is not None
                else None
            ),
            "latest_voice_profile_lifecycle_state": (
                latest_envelope.get("voice_identity_voice_profile_lifecycle_state")
                if latest_envelope is not None
                else None
            ),
            "latest_identity_lifecycle_state": (
                latest_envelope.get("voice_identity_identity_lifecycle_state")
                if latest_envelope is not None
                else None
            ),
            "latest_lifecycle_reason_code": (
                latest_envelope.get("voice_identity_lifecycle_reason_code")
                if latest_envelope is not None
                else None
            ),
        },
        "permission_boundary_visibility": {
            "latest_boundary_path": (
                latest_envelope.get("voice_identity_permission_boundary_path")
                if latest_envelope is not None
                else None
            ),
            "latest_consumption_only": (
                bool(latest_envelope.get("voice_identity_permission_consumption_only", False))
                if latest_envelope is not None
                else False
            ),
            "latest_permission_state_consumed": (
                bool(latest_envelope.get("voice_identity_permission_state_consumed", False))
                if latest_envelope is not None
                else False
            ),
            "latest_permission_state": (
                latest_envelope.get("voice_identity_permission_state")
                if latest_envelope is not None
                else None
            ),
            "latest_permission_outcome": (
                latest_envelope.get("voice_identity_permission_outcome")
                if latest_envelope is not None
                else None
            ),
            "latest_consent_state": (
                latest_envelope.get("voice_identity_consent_state")
                if latest_envelope is not None
                else None
            ),
            "latest_consent_outcome": (
                latest_envelope.get("voice_identity_consent_outcome")
                if latest_envelope is not None
                else None
            ),
            "latest_eligibility_state": (
                latest_envelope.get("voice_identity_permission_eligibility_state")
                if latest_envelope is not None
                else None
            ),
            "latest_gating_reason": (
                latest_envelope.get("voice_identity_permission_gating_reason")
                if latest_envelope is not None
                else None
            ),
            "latest_permission_reason_code": (
                latest_envelope.get("voice_identity_permission_reason_code")
                if latest_envelope is not None
                else None
            ),
        },
        "legacy_disposition_boundary_visibility": {
            "latest_boundary_path": (
                latest_envelope.get("voice_identity_legacy_disposition_boundary_path")
                if latest_envelope is not None
                else None
            ),
            "latest_consumption_only": (
                bool(latest_envelope.get("voice_identity_legacy_disposition_consumption_only", False))
                if latest_envelope is not None
                else False
            ),
            "latest_legacy_disposition_consumed": (
                bool(latest_envelope.get("voice_identity_legacy_disposition_consumed", False))
                if latest_envelope is not None
                else False
            ),
            "latest_legacy_disposition_state": (
                latest_envelope.get("voice_identity_legacy_disposition_state")
                if latest_envelope is not None
                else None
            ),
            "latest_legacy_disposition_outcome": (
                latest_envelope.get("voice_identity_legacy_disposition_outcome")
                if latest_envelope is not None
                else None
            ),
            "latest_legacy_reference": (
                latest_envelope.get("voice_identity_legacy_reference")
                if latest_envelope is not None
                else None
            ),
            "latest_replacement_reference": (
                latest_envelope.get("voice_identity_legacy_replacement_reference")
                if latest_envelope is not None
                else None
            ),
            "latest_legacy_disposition_reason_code": (
                latest_envelope.get("voice_identity_legacy_disposition_reason_code")
                if latest_envelope is not None
                else None
            ),
        },
        "diagnostics_boundary_visibility": {
            "latest_boundary_path": (
                latest_envelope.get("voice_identity_diagnostics_boundary_path")
                if latest_envelope is not None
                else None
            ),
            "latest_consumption_only": (
                bool(latest_envelope.get("voice_identity_diagnostics_consumption_only", False))
                if latest_envelope is not None
                else False
            ),
            "latest_diagnostics_consumed": (
                bool(latest_envelope.get("voice_identity_diagnostics_consumed", False))
                if latest_envelope is not None
                else False
            ),
            "latest_diagnostic_available": (
                bool(latest_envelope.get("voice_identity_diagnostic_available", False))
                if latest_envelope is not None
                else False
            ),
            "latest_diagnostic_reason_code": (
                latest_envelope.get("voice_identity_diagnostic_reason_code")
                if latest_envelope is not None
                else None
            ),
            "latest_health_status": (
                latest_envelope.get("voice_identity_health_status")
                if latest_envelope is not None
                else None
            ),
            "latest_attribution_readiness": (
                latest_envelope.get("voice_identity_attribution_readiness")
                if latest_envelope is not None
                else None
            ),
            "latest_compatibility_readiness": (
                latest_envelope.get("voice_identity_compatibility_readiness")
                if latest_envelope is not None
                else None
            ),
            "latest_repair_available": (
                bool(latest_envelope.get("voice_identity_repair_available", False))
                if latest_envelope is not None
                else False
            ),
            "latest_repair_hint_code": (
                latest_envelope.get("voice_identity_repair_hint_code")
                if latest_envelope is not None
                else None
            ),
            "latest_suggested_next_action_code": (
                latest_envelope.get("voice_identity_suggested_next_action_code")
                if latest_envelope is not None
                else None
            ),
            "latest_provenance_source": (
                latest_envelope.get("voice_identity_diagnostics_provenance_source")
                if latest_envelope is not None
                else None
            ),
            "latest_source_reference": (
                latest_envelope.get("voice_identity_diagnostics_source_reference")
                if latest_envelope is not None
                else None
            ),
            "latest_lineage_ref": (
                latest_envelope.get("voice_identity_diagnostics_lineage_ref")
                if latest_envelope is not None
                else None
            ),
        },
        "explainability_boundary_visibility": {
            "latest_boundary_path": (
                latest_envelope.get("voice_identity_explainability_boundary_path")
                if latest_envelope is not None
                else None
            ),
            "latest_consumption_only": (
                bool(latest_envelope.get("voice_identity_explainability_consumption_only", False))
                if latest_envelope is not None
                else False
            ),
            "latest_explainability_consumed": (
                bool(latest_envelope.get("voice_identity_explainability_consumed", False))
                if latest_envelope is not None
                else False
            ),
            "latest_consumed_outcome": (
                latest_envelope.get("voice_identity_explainability_consumed_outcome")
                if latest_envelope is not None
                else None
            ),
            "latest_authority_source": (
                latest_envelope.get("voice_identity_explainability_authority_source")
                if latest_envelope is not None
                else None
            ),
            "latest_provenance_source": (
                latest_envelope.get("voice_identity_explainability_provenance_source")
                if latest_envelope is not None
                else None
            ),
            "latest_source_reference": (
                latest_envelope.get("voice_identity_explainability_source_reference")
                if latest_envelope is not None
                else None
            ),
            "latest_lineage_ref": (
                latest_envelope.get("voice_identity_explainability_lineage_ref")
                if latest_envelope is not None
                else None
            ),
            "latest_attribution_source": (
                latest_envelope.get("voice_identity_explainability_attribution_source")
                if latest_envelope is not None
                else None
            ),
            "latest_confidence_source": (
                latest_envelope.get("voice_identity_explainability_confidence_source")
                if latest_envelope is not None
                else None
            ),
            "latest_enrollment_source": (
                latest_envelope.get("voice_identity_explainability_enrollment_source")
                if latest_envelope is not None
                else None
            ),
            "latest_lifecycle_source": (
                latest_envelope.get("voice_identity_explainability_lifecycle_source")
                if latest_envelope is not None
                else None
            ),
            "latest_permission_source": (
                latest_envelope.get("voice_identity_explainability_permission_source")
                if latest_envelope is not None
                else None
            ),
            "latest_legacy_disposition_source": (
                latest_envelope.get("voice_identity_explainability_legacy_disposition_source")
                if latest_envelope is not None
                else None
            ),
            "latest_unavailable_state": (
                latest_envelope.get("voice_identity_explainability_unavailable_state")
                if latest_envelope is not None
                else None
            ),
            "latest_reason_code": (
                latest_envelope.get("voice_identity_explainability_reason_code")
                if latest_envelope is not None
                else None
            ),
        },
        "ownership_boundary_visibility": {
            "derives_attribution_authority": (
                bool(latest_envelope.get("voice_identity_derives_attribution_authority", False))
                if latest_envelope is not None
                else False
            ),
            "derives_confidence_authority": (
                bool(latest_envelope.get("voice_identity_derives_confidence_authority", False))
                if latest_envelope is not None
                else False
            ),
            "calculates_attribution": (
                bool(latest_envelope.get("voice_identity_calculates_attribution", False))
                if latest_envelope is not None
                else False
            ),
            "calculates_confidence": (
                bool(latest_envelope.get("voice_identity_calculates_confidence", False))
                if latest_envelope is not None
                else False
            ),
            "manages_identity_lifecycle": (
                bool(latest_envelope.get("voice_identity_manages_identity_lifecycle", False))
                if latest_envelope is not None
                else False
            ),
            "manages_enrollment": (
                bool(latest_envelope.get("voice_identity_manages_enrollment", False))
                if latest_envelope is not None
                else False
            ),
            "manages_enrollment_lifecycle": (
                bool(latest_envelope.get("voice_identity_manages_enrollment_lifecycle", False))
                if latest_envelope is not None
                else False
            ),
            "manages_voice_profile_lifecycle": (
                bool(latest_envelope.get("voice_identity_manages_voice_profile_lifecycle", False))
                if latest_envelope is not None
                else False
            ),
            "creates_voice_profiles": (
                bool(latest_envelope.get("voice_identity_creates_voice_profiles", False))
                if latest_envelope is not None
                else False
            ),
            "changes_enrollment_state": (
                bool(latest_envelope.get("voice_identity_changes_enrollment_state", False))
                if latest_envelope is not None
                else False
            ),
            "infers_enrollment_state": (
                bool(latest_envelope.get("voice_identity_infers_enrollment_state", False))
                if latest_envelope is not None
                else False
            ),
            "derives_permission_authority": (
                bool(latest_envelope.get("voice_identity_derives_permission_authority", False))
                if latest_envelope is not None
                else False
            ),
            "creates_permission_policy": (
                bool(latest_envelope.get("voice_identity_creates_permission_policy", False))
                if latest_envelope is not None
                else False
            ),
            "defines_eligibility_rules": (
                bool(latest_envelope.get("voice_identity_defines_eligibility_rules", False))
                if latest_envelope is not None
                else False
            ),
            "determines_permission_outcomes": (
                bool(latest_envelope.get("voice_identity_determines_permission_outcomes", False))
                if latest_envelope is not None
                else False
            ),
            "overrides_permission_policy": (
                bool(latest_envelope.get("voice_identity_overrides_permission_policy", False))
                if latest_envelope is not None
                else False
            ),
            "grants_permission": (
                bool(latest_envelope.get("voice_identity_grants_permission", False))
                if latest_envelope is not None
                else False
            ),
            "revokes_permission": (
                bool(latest_envelope.get("voice_identity_revokes_permission", False))
                if latest_envelope is not None
                else False
            ),
            "approves_consent": (
                bool(latest_envelope.get("voice_identity_approves_consent", False))
                if latest_envelope is not None
                else False
            ),
            "infers_consent": (
                bool(latest_envelope.get("voice_identity_infers_consent", False))
                if latest_envelope is not None
                else False
            ),
            "infers_permission_state": (
                bool(latest_envelope.get("voice_identity_infers_permission_state", False))
                if latest_envelope is not None
                else False
            ),
            "manages_legacy_fingerprint_resolution": (
                bool(latest_envelope.get("voice_identity_manages_legacy_fingerprint_resolution", False))
                if latest_envelope is not None
                else False
            ),
            "migrates_legacy_identity_data": (
                bool(latest_envelope.get("voice_identity_migrates_legacy_identity_data", False))
                if latest_envelope is not None
                else False
            ),
            "disposes_legacy_identity_data": (
                bool(latest_envelope.get("voice_identity_disposes_legacy_identity_data", False))
                if latest_envelope is not None
                else False
            ),
            "determines_legacy_disposition": (
                bool(latest_envelope.get("voice_identity_determines_legacy_disposition", False))
                if latest_envelope is not None
                else False
            ),
            "infers_legacy_disposition_state": (
                bool(latest_envelope.get("voice_identity_infers_legacy_disposition_state", False))
                if latest_envelope is not None
                else False
            ),
            "claims_voiceprint_ownership": (
                bool(latest_envelope.get("voice_identity_claims_voiceprint_ownership", False))
                if latest_envelope is not None
                else False
            ),
            "claims_embedding_ownership": (
                bool(latest_envelope.get("voice_identity_claims_embedding_ownership", False))
                if latest_envelope is not None
                else False
            ),
            "establishes_identity_authority": (
                bool(latest_envelope.get("voice_identity_establishes_identity_authority", False))
                if latest_envelope is not None
                else False
            ),
            "determines_enrollment_state": (
                bool(latest_envelope.get("voice_identity_determines_enrollment_state", False))
                if latest_envelope is not None
                else False
            ),
            "generates_diagnostics_authority": (
                bool(latest_envelope.get("voice_identity_generates_diagnostics_authority", False))
                if latest_envelope is not None
                else False
            ),
            "rewrites_diagnostics": (
                bool(latest_envelope.get("voice_identity_rewrites_diagnostics", False))
                if latest_envelope is not None
                else False
            ),
            "calculates_health_status": (
                bool(latest_envelope.get("voice_identity_calculates_health_status", False))
                if latest_envelope is not None
                else False
            ),
            "calculates_readiness": (
                bool(latest_envelope.get("voice_identity_calculates_readiness", False))
                if latest_envelope is not None
                else False
            ),
            "generates_repair_hints": (
                bool(latest_envelope.get("voice_identity_generates_repair_hints", False))
                if latest_envelope is not None
                else False
            ),
            "generates_explainability_authority": (
                bool(latest_envelope.get("voice_identity_generates_explainability_authority", False))
                if latest_envelope is not None
                else False
            ),
            "replaces_provenance": (
                bool(latest_envelope.get("voice_identity_replaces_provenance", False))
                if latest_envelope is not None
                else False
            ),
            "creates_explainability_lineage": (
                bool(latest_envelope.get("voice_identity_creates_explainability_lineage", False))
                if latest_envelope is not None
                else False
            ),
        },
        "diagnostics_non_rights": {
            "creates_authority": False,
            "calculates_attribution": False,
            "calculates_confidence": False,
            "manages_identity_lifecycle": False,
            "manages_enrollment": False,
            "manages_enrollment_lifecycle": False,
            "manages_voice_profile_lifecycle": False,
            "creates_voice_profiles": False,
            "changes_enrollment_state": False,
            "infers_enrollment_state": False,
            "derives_permission_authority": False,
            "creates_permission_policy": False,
            "defines_eligibility_rules": False,
            "determines_permission_outcomes": False,
            "overrides_permission_policy": False,
            "grants_permission": False,
            "revokes_permission": False,
            "approves_consent": False,
            "infers_consent": False,
            "infers_permission_state": False,
            "manages_legacy_fingerprint_resolution": False,
            "migrates_legacy_identity_data": False,
            "disposes_legacy_identity_data": False,
            "determines_legacy_disposition": False,
            "infers_legacy_disposition_state": False,
            "claims_voiceprint_ownership": False,
            "claims_embedding_ownership": False,
            "establishes_identity_authority": False,
            "determines_enrollment_state": False,
            "generates_diagnostics_authority": False,
            "rewrites_diagnostics": False,
            "calculates_health_status": False,
            "calculates_readiness": False,
            "generates_repair_hints": False,
            "generates_explainability_authority": False,
            "replaces_provenance": False,
            "creates_explainability_lineage": False,
        },
    }


def _productivity_source_of_record_boundary_visibility(hass, state) -> dict[str, Any]:
    """Return bounded Release 6 source-of-record boundary visibility."""
    return _build_productivity_source_of_record_boundary(state=state, hass=hass)


def _calendar_email_consumption_boundary_visibility(hass, state) -> dict[str, Any]:
    """Return bounded Release 6 calendar/email consumption visibility."""
    return _build_calendar_email_consumption_boundary(state=state, hass=hass)


def _task_shopping_consumption_boundary_visibility(hass, state) -> dict[str, Any]:
    """Return bounded Release 6 task/shopping consumption visibility."""
    return _build_task_shopping_consumption_boundary(state=state, hass=hass)


def _capture_knowledge_consumption_boundary_visibility(hass, state) -> dict[str, Any]:
    """Return bounded Release 6 capture/knowledge consumption visibility."""
    return _build_capture_knowledge_consumption_boundary(state=state, hass=hass)


def _briefing_composition_boundary_visibility(hass, state) -> dict[str, Any]:
    """Return bounded Release 6 briefing composition visibility."""
    return _build_briefing_composition_boundary(state=state, hass=hass)


def _household_status_synthesis_boundary_visibility(hass, state) -> dict[str, Any]:
    """Return bounded Release 6 household status synthesis visibility."""
    return _build_household_status_synthesis_boundary(state=state, hass=hass)


def _provenance_ownership_consumption_boundary_visibility(hass, state) -> dict[str, Any]:
    """Return bounded Release 6 provenance ownership and consumption visibility."""
    return _build_release_6_provenance_ownership_consumption_boundary(state=state, hass=hass)


def _household_coordination_boundary_visibility(hass, state) -> dict[str, Any]:
    """Return bounded Release 6 household coordination visibility."""
    household_status_synthesis_boundary = _build_household_status_synthesis_boundary(state=state, hass=hass)
    provenance_ownership_consumption_boundary = _build_release_6_provenance_ownership_consumption_boundary(
        state=state,
        hass=hass,
    )
    return _build_household_coordination_boundary(
        state=state,
        hass=hass,
        household_status_synthesis_boundary=household_status_synthesis_boundary,
        provenance_ownership_consumption_boundary=provenance_ownership_consumption_boundary,
    )


def _productivity_coordination_boundary_visibility(hass, state) -> dict[str, Any]:
    """Return bounded Release 6 productivity coordination visibility."""
    return _build_productivity_coordination_boundary(
        state=state,
        hass=hass,
    )


def _release_6_provenance_diagnostics_explainability_visibility(hass, state) -> dict[str, Any]:
    """Return bounded Release 6 provenance diagnostics and explainability visibility."""
    runtime_person_context = _build_runtime_person_context(state)
    person_aware_productivity_routing = _build_person_aware_productivity_routing(
        state=state,
        hass=hass,
        runtime_person_context=runtime_person_context,
    )
    household_status_synthesis_boundary = _build_household_status_synthesis_boundary(
        state=state,
        hass=hass,
    )
    provenance_ownership_consumption_boundary = _build_release_6_provenance_ownership_consumption_boundary(
        state=state,
        hass=hass,
    )
    productivity_coordination_boundary = _build_productivity_coordination_boundary(
        state=state,
        hass=hass,
        runtime_person_context=runtime_person_context,
        person_aware_productivity_routing=person_aware_productivity_routing,
        provenance_ownership_consumption_boundary=provenance_ownership_consumption_boundary,
    )
    household_coordination_boundary = _build_household_coordination_boundary(
        state=state,
        hass=hass,
        runtime_person_context=runtime_person_context,
        person_aware_productivity_routing=person_aware_productivity_routing,
        household_status_synthesis_boundary=household_status_synthesis_boundary,
        provenance_ownership_consumption_boundary=provenance_ownership_consumption_boundary,
    )
    return _build_release_6_provenance_diagnostics_explainability_boundary(
        state=state,
        hass=hass,
        runtime_person_context=runtime_person_context,
        person_aware_productivity_routing=person_aware_productivity_routing,
        productivity_coordination_boundary=productivity_coordination_boundary,
        household_status_synthesis_boundary=household_status_synthesis_boundary,
        household_coordination_boundary=household_coordination_boundary,
        provenance_ownership_consumption_boundary=provenance_ownership_consumption_boundary,
    )


def _release_6_productivity_diagnostics_visibility(hass, state) -> dict[str, Any]:
    """Return consolidated Release 6 productivity diagnostics visibility."""
    boundary_entries = [
        {
            "boundary_name": "productivity_source_of_record_boundary",
            "source_domain": "productivity",
            "source_type": "productivity_source_of_record_boundary",
            "visibility": _productivity_source_of_record_boundary_visibility(hass, state),
            "available": True,
        },
        {
            "boundary_name": "calendar_email_consumption_boundary",
            "source_domain": "calendar_email",
            "source_type": "calendar_email_consumption_boundary",
            "visibility": _calendar_email_consumption_boundary_visibility(hass, state),
            "available": bool(
                _calendar_email_consumption_boundary_visibility(hass, state).get("configured_source_reference_count", 0)
                or _calendar_email_consumption_boundary_visibility(hass, state).get("person_calendar_email_bindings", {}).get("person_count", 0)
            ),
        },
        {
            "boundary_name": "task_shopping_consumption_boundary",
            "source_domain": "task_shopping",
            "source_type": "task_shopping_consumption_boundary",
            "visibility": _task_shopping_consumption_boundary_visibility(hass, state),
            "available": bool(
                _task_shopping_consumption_boundary_visibility(hass, state).get("configured_source_reference_count", 0)
                or _task_shopping_consumption_boundary_visibility(hass, state).get("person_shopping_bindings", {}).get("person_count", 0)
            ),
        },
        {
            "boundary_name": "capture_knowledge_consumption_boundary",
            "source_domain": "capture_knowledge",
            "source_type": "capture_knowledge_consumption_boundary",
            "visibility": _capture_knowledge_consumption_boundary_visibility(hass, state),
            "available": bool(
                _capture_knowledge_consumption_boundary_visibility(hass, state).get("knowledge_consumption", {}).get("knowledge_available", False)
                or _capture_knowledge_consumption_boundary_visibility(hass, state).get("capture_consumption", {}).get("capture_available", False)
            ),
        },
        {
            "boundary_name": "briefing_composition_boundary",
            "source_domain": "briefing",
            "source_type": "briefing_composition_boundary",
            "visibility": _briefing_composition_boundary_visibility(hass, state),
            "available": bool(_briefing_composition_boundary_visibility(hass, state).get("briefing_available", False)),
        },
        {
            "boundary_name": "household_status_synthesis_boundary",
            "source_domain": "household_status",
            "source_type": "household_status_synthesis_boundary",
            "visibility": _household_status_synthesis_boundary_visibility(hass, state),
            "available": bool(_household_status_synthesis_boundary_visibility(hass, state).get("household_status_available", False)),
        },
        {
            "boundary_name": "household_coordination_boundary",
            "source_domain": "household_coordination",
            "source_type": "household_coordination_boundary",
            "visibility": _household_coordination_boundary_visibility(hass, state),
            "available": bool(_household_coordination_boundary_visibility(hass, state).get("available_contributor_count", 0)),
        },
        {
            "boundary_name": "productivity_coordination_boundary",
            "source_domain": "productivity_coordination",
            "source_type": "productivity_coordination_boundary",
            "visibility": _productivity_coordination_boundary_visibility(hass, state),
            "available": bool(
                _productivity_coordination_boundary_visibility(hass, state).get(
                    "coordination_awareness", {}
                ).get("participating_domain_count", 0)
            ),
        },
        {
            "boundary_name": "provenance_ownership_consumption_boundary",
            "source_domain": "provenance_ownership",
            "source_type": "provenance_ownership_consumption_boundary",
            "visibility": _provenance_ownership_consumption_boundary_visibility(hass, state),
            "available": bool(
                _provenance_ownership_consumption_boundary_visibility(hass, state).get("readiness_assessment", {}).get("lineage_completeness_ready", False)
            ),
        },
        {
            "boundary_name": "release_6_provenance_diagnostics_explainability_boundary",
            "source_domain": "provenance_diagnostics",
            "source_type": "release_6_provenance_diagnostics_explainability_boundary",
            "visibility": _release_6_provenance_diagnostics_explainability_visibility(hass, state),
            "available": bool(
                _release_6_provenance_diagnostics_explainability_visibility(hass, state).get(
                    "provenance_diagnostics", {}
                ).get("lineage_completeness_ready", False)
            ),
        },
    ]

    available_boundary_count = sum(1 for item in boundary_entries if bool(item["available"]))
    safe_fallback_boundary_count = sum(
        1
        for item in boundary_entries
        if bool(item["visibility"].get("safe_fallback_mode_active", False))
        or bool(item["visibility"].get("safe_fallback_reason"))
    )
    configured_source_reference_count = sum(
        int(item["visibility"].get("configured_source_reference_count", 0) or 0)
        for item in boundary_entries
    )

    provenance_entries: list[dict[str, Any]] = []
    explainability_entries: list[dict[str, Any]] = []
    for item in boundary_entries:
        visibility = item["visibility"]
        provenance_visibility = visibility.get("provenance_visibility", {})
        explainability_visibility = visibility.get("explainability_visibility", {})
        available = bool(item["available"])
        provenance_entries.append(
            {
                "boundary_name": item["boundary_name"],
                "source_domain": item["source_domain"],
                "source_type": item["source_type"],
                "provenance_reference_count": int(provenance_visibility.get("provenance_reference_count", 0) or 0),
                "provenance_visible": bool(provenance_visibility.get("provenance_visible", False)),
                "available": available,
            }
        )
        explainability_entries.append(
            {
                "boundary_name": item["boundary_name"],
                "source_domain": item["source_domain"],
                "source_type": item["source_type"],
                "source_domain_visible": bool(explainability_visibility.get("source_domain_visible", False)),
                "source_type_visible": bool(explainability_visibility.get("source_type_visible", False)),
                "safe_fallback_visible": bool(explainability_visibility.get("safe_fallback_visible", False)),
                "available": available,
            }
        )

    return {
        "release_6_productivity_diagnostics_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_release_6_productivity_diagnostics_boundary",
        "deterministic_boundary": True,
        "boundary_status": "active",
        "concierge_role": "bounded_consumer_orchestrator",
        "diagnostics_visibility": {
            "boundary_count": len(boundary_entries),
            "available_boundary_count": available_boundary_count,
            "configured_source_reference_count": configured_source_reference_count,
            "safe_fallback_boundary_count": safe_fallback_boundary_count,
            "boundary_names": [item["boundary_name"] for item in boundary_entries],
            "source_domains": [item["source_domain"] for item in boundary_entries],
        },
        "provenance_visibility": {
            "boundary_entries": provenance_entries,
            "provenance_reference_count": sum(item["provenance_reference_count"] for item in provenance_entries),
            "provenance_visible_boundary_count": sum(1 for item in provenance_entries if item["provenance_visible"]),
            "provenance_ready_boundary_count": sum(1 for item in provenance_entries if item["available"]),
        },
        "explainability_visibility": {
            "boundary_entries": explainability_entries,
            "source_domain_visible_boundary_count": sum(1 for item in explainability_entries if item["source_domain_visible"]),
            "source_type_visible_boundary_count": sum(1 for item in explainability_entries if item["source_type_visible"]),
            "safe_fallback_visible_boundary_count": sum(1 for item in explainability_entries if item["safe_fallback_visible"]),
        },
        "safe_fallback_visibility": {
            "boundary_count": safe_fallback_boundary_count,
            "degraded_boundary_count": sum(1 for item in boundary_entries if not bool(item["available"])),
            "missing_prerequisite_boundary_count": sum(
                1
                for item in boundary_entries
                if not bool(item["available"])
                or bool(item["visibility"].get("safe_fallback_mode_active", False))
            ),
        },
        "non_authority_assertions": {
            "creates_source_of_record": False,
            "stores_duplicate_canonical_records": False,
            "claims_diagnostics_authority": False,
            "claims_provenance_authority": False,
            "claims_explainability_authority": False,
            "claims_retrieval_authority": False,
        },
        "deferred_release_6_owners": {
            "person_productivity_source_bindings": "#375",
            "calendar_and_email_consumption": "#363",
            "task_and_shopping_consumption": "#364",
            "capture_and_knowledge_consumption": "#365",
            "briefing_and_household_status_synthesis": "#366",
            "productivity_diagnostics_provenance_explainability": "#367",
            "household_coordination": "#368-#372",
            "release_6_validation": "#373",
        },
    }

def _messaging_governance_boundary_visibility(state) -> dict[str, Any]:
    """Return bounded messaging governance visibility from recorded activity refs."""
    messaging_boundary_refs: list[dict[str, Any]] = []

    for activity in sorted(
        state.activities.values(),
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        for ref in list(getattr(activity, "external_refs", [])):
            if str(ref.get("ref_type", "") or "") == "messaging_governance_boundary":
                messaging_boundary_refs.append(dict(ref))

    latest_ref = messaging_boundary_refs[0] if messaging_boundary_refs else None

    return {
        "authority_visibility": {
            "message_authority_external": True,
            "provenance_authority_external": True,
            "household_memory_authority_external": True,
            "concierge_role": "bounded_consumer_orchestrator",
        },
        "governance_visibility": {
            "messaging_boundary_ref_count": len(messaging_boundary_refs),
            "latest_messaging_boundary_applicable": latest_ref is not None,
            "latest_messaging_boundary_path": (
                latest_ref.get("boundary_path") if latest_ref is not None else None
            ),
            "latest_route_scope": latest_ref.get("route_scope") if latest_ref is not None else None,
            "latest_recipient_scope": latest_ref.get("recipient_scope") if latest_ref is not None else None,
            "latest_message_context_type": (
                latest_ref.get("message_context_type") if latest_ref is not None else None
            ),
        },
        "ownership_boundary_visibility": {
            "messaging_owns_truth": False,
            "messaging_owns_provenance": False,
            "messaging_owns_memory": False,
            "messaging_owns_identity": False,
        },
        "lifecycle_governance_visibility": {
            "message_creation_governed": True,
            "message_delivery_governed": True,
            "message_acknowledgement_governed": True,
            "message_retention_governed": True,
        },
        "traceability_visibility": {
            "messaging_boundary_ref_count": len(messaging_boundary_refs),
            "latest_message_authority_external": (
                bool(latest_ref.get("message_authority_external", False))
                if latest_ref is not None
                else False
            ),
            "latest_provenance_authority_external": (
                bool(latest_ref.get("provenance_authority_external", False))
                if latest_ref is not None
                else False
            ),
            "latest_household_memory_authority_external": (
                bool(latest_ref.get("household_memory_authority_external", False))
                if latest_ref is not None
                else False
            ),
        },
        "deferred_functionality_visibility": {
            "messaging_provenance": "#340",
            "notification_and_delivery_boundary": "#341",
            "recipient_consent_privacy_visibility_boundary": "#342",
            "messaging_diagnostics_explainability": "#343",
            "household_memory_boundary": "#344",
            "release_4_validation": "#349",
        },
        "diagnostics_non_rights": {
            "creates_authority": False,
            "creates_outcomes": False,
            "determines_truth": False,
            "establishes_truth": False,
            "overrides_truth": False,
            "creates_source_of_record": False,
        },
    }


def _messaging_provenance_visibility(state) -> dict[str, Any]:
    """Return bounded visibility into recorded messaging provenance refs."""
    provenance_refs: list[dict[str, Any]] = []

    for activity in sorted(
        state.activities.values(),
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        for ref in list(getattr(activity, "external_refs", [])):
            if str(ref.get("ref_type", "") or "") == "messaging_provenance":
                provenance_refs.append(dict(ref))

    latest_ref = provenance_refs[0] if provenance_refs else None

    return {
        "authority_visibility": {
            "provenance_authority_external": True,
            "message_authority_external": True,
            "household_memory_authority_external": True,
            "concierge_role": "bounded_consumer_orchestrator",
        },
        "traceability_visibility": {
            "messaging_provenance_ref_count": len(provenance_refs),
            "latest_provenance_id_present": bool(latest_ref and latest_ref.get("provenance_id")),
            "latest_source_service": latest_ref.get("source_service") if latest_ref is not None else None,
            "latest_created_in_room": latest_ref.get("created_in_room") if latest_ref is not None else None,
            "latest_boundary_path": latest_ref.get("boundary_path") if latest_ref is not None else None,
            "latest_requested_target_supplied": (
                bool(latest_ref.get("requested_target_supplied", False))
                if latest_ref is not None
                else False
            ),
            "latest_explicit_entity_target": (
                bool(latest_ref.get("explicit_entity_target", False))
                if latest_ref is not None
                else False
            ),
        },
        "delivery_visibility": {
            "latest_delivery_channel": latest_ref.get("delivery_channel") if latest_ref is not None else None,
            "latest_selected_service": latest_ref.get("selected_service") if latest_ref is not None else None,
            "latest_selected_target_id": latest_ref.get("selected_target_id") if latest_ref is not None else None,
            "latest_routing_path": latest_ref.get("routing_path") if latest_ref is not None else None,
        },
        "diagnostics_non_rights": {
            "claims_upstream_truth": False,
            "claims_identity_authority": False,
            "claims_household_memory_authority": False,
            "creates_source_of_record": False,
        },
    }


def _notification_delivery_boundary_visibility(state) -> dict[str, Any]:
    """Return bounded notification/delivery visibility from recorded refs and outcomes."""
    boundary_refs: list[dict[str, Any]] = []
    delivery_execution_refs: list[dict[str, Any]] = []
    delivery_activities = [
        activity
        for activity in state.activities.values()
        if str(getattr(activity, "intent_class", "")) == "push_person_message"
    ]

    for activity in sorted(
        delivery_activities,
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        for ref in list(getattr(activity, "external_refs", [])):
            ref_type = str(ref.get("ref_type", "") or "")
            if ref_type == "notification_delivery_boundary":
                boundary_refs.append(dict(ref))
            elif ref_type == "delivery_execution":
                delivery_execution_refs.append(dict(ref))

    latest_boundary_ref = boundary_refs[0] if boundary_refs else None
    success_count = sum(
        1 for activity in delivery_activities if str(getattr(activity, "outcome", "")) == "success"
    )
    error_count = sum(
        1 for activity in delivery_activities if str(getattr(activity, "outcome", "")) == "error"
    )
    policy_denied_count = sum(
        1 for activity in delivery_activities if str(getattr(activity, "outcome", "")) == "policy_denied"
    )

    return {
        "authority_visibility": {
            "delivery_authority_external": True,
            "recipient_authority_external": True,
            "consent_authority_external": True,
            "visibility_authority_external": True,
            "concierge_role": "bounded_consumer_orchestrator",
        },
        "delivery_visibility": {
            "notification_delivery_boundary_ref_count": len(boundary_refs),
            "latest_delivery_boundary_path": (
                latest_boundary_ref.get("boundary_path") if latest_boundary_ref is not None else None
            ),
            "latest_delivery_channel": (
                latest_boundary_ref.get("delivery_channel") if latest_boundary_ref is not None else None
            ),
            "latest_selected_service": (
                latest_boundary_ref.get("selected_service") if latest_boundary_ref is not None else None
            ),
            "latest_selected_target_id": (
                latest_boundary_ref.get("selected_target_id") if latest_boundary_ref is not None else None
            ),
            "latest_routing_path": (
                latest_boundary_ref.get("routing_path") if latest_boundary_ref is not None else None
            ),
            "latest_explicit_entity_target": (
                bool(latest_boundary_ref.get("explicit_entity_target", False))
                if latest_boundary_ref is not None
                else False
            ),
        },
        "execution_tracking": {
            "delivery_execution_ref_count": len(delivery_execution_refs),
            "delivery_activity_count": len(delivery_activities),
            "delivery_success_count": success_count,
            "delivery_error_count": error_count,
            "delivery_policy_denied_count": policy_denied_count,
        },
        "governance_visibility": {
            "delivery_boundary_only": True,
            "recipient_authorization_enabled": False,
            "consent_adjudication_enabled": False,
            "visibility_adjudication_enabled": False,
        },
        "diagnostics_non_rights": {
            "claims_recipient_authority": False,
            "claims_consent_authority": False,
            "claims_visibility_authority": False,
            "claims_delivery_truth": False,
            "claims_acknowledgement": False,
            "claims_message_seen": False,
        },
    }


def _recipient_consent_privacy_visibility_boundary_visibility(state) -> dict[str, Any]:
    """Return bounded recipient/consent/privacy/visibility decision visibility."""
    boundary_refs: list[dict[str, Any]] = []
    activities = [
        item
        for item in state.activities.values()
        if str(getattr(item, "intent_class", "")) == "push_person_message"
    ]

    for activity in sorted(
        activities,
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        for ref in list(getattr(activity, "external_refs", [])):
            if str(ref.get("ref_type", "") or "") == "recipient_consent_privacy_visibility_boundary":
                boundary_refs.append(dict(ref))

    latest_ref = boundary_refs[0] if boundary_refs else None
    denied_count = sum(
        1 for ref in boundary_refs if not bool(ref.get("delivery_permitted", False))
    )
    allowed_count = sum(
        1 for ref in boundary_refs if bool(ref.get("delivery_permitted", False))
    )

    return {
        "authority_visibility": {
            "recipient_authority_external": True,
            "consent_authority_external": True,
            "privacy_authority_external": True,
            "visibility_authority_external": True,
            "concierge_role": "bounded_consumer_orchestrator",
        },
        "decision_visibility": {
            "boundary_ref_count": len(boundary_refs),
            "delivery_permitted_count": allowed_count,
            "delivery_denied_count": denied_count,
            "latest_delivery_permitted": (
                bool(latest_ref.get("delivery_permitted", False)) if latest_ref is not None else None
            ),
            "latest_decision_reason": latest_ref.get("decision_reason") if latest_ref is not None else None,
            "latest_privacy_mode": latest_ref.get("privacy_mode") if latest_ref is not None else None,
            "latest_visibility_mode": latest_ref.get("visibility_mode") if latest_ref is not None else None,
            "latest_require_delivery_consent": (
                bool(latest_ref.get("require_delivery_consent", False)) if latest_ref is not None else None
            ),
            "latest_delivery_consent_granted": (
                bool(latest_ref.get("delivery_consent_granted", False)) if latest_ref is not None else None
            ),
            "latest_recipient_eligible": (
                bool(latest_ref.get("recipient_eligible", False)) if latest_ref is not None else None
            ),
        },
        "delivery_visibility": {
            "latest_delivery_channel": latest_ref.get("delivery_channel") if latest_ref is not None else None,
            "latest_selected_service": latest_ref.get("selected_service") if latest_ref is not None else None,
            "latest_selected_target_id": (
                latest_ref.get("selected_target_id") if latest_ref is not None else None
            ),
            "latest_routing_path": latest_ref.get("routing_path") if latest_ref is not None else None,
            "latest_explicit_entity_target": (
                bool(latest_ref.get("explicit_entity_target", False)) if latest_ref is not None else False
            ),
        },
        "diagnostics_non_rights": {
            "claims_identity_authority": False,
            "claims_recipient_authority": False,
            "claims_consent_authority": False,
            "claims_privacy_authority": False,
            "claims_visibility_authority": False,
            "claims_message_seen": False,
            "claims_acknowledgement": False,
        },
    }


def _messaging_diagnostics_explainability_visibility(state) -> dict[str, Any]:
    """Return bounded messaging diagnostics/explainability visibility from recorded refs."""
    explainability_refs: list[dict[str, Any]] = []
    activities = [
        item
        for item in state.activities.values()
        if str(getattr(item, "intent_class", "")) == "push_person_message"
    ]

    for activity in sorted(
        activities,
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        for ref in list(getattr(activity, "external_refs", [])):
            if str(ref.get("ref_type", "") or "") == "messaging_diagnostics_explainability":
                explainability_refs.append(dict(ref))

    latest_ref = explainability_refs[0] if explainability_refs else None
    policy_denied_count = sum(
        1 for activity in activities if str(getattr(activity, "outcome", "")) == "policy_denied"
    )
    operational_error_count = sum(
        1 for activity in activities if str(getattr(activity, "outcome", "")) == "error"
    )
    success_count = sum(
        1 for activity in activities if str(getattr(activity, "outcome", "")) == "success"
    )

    return {
        "authority_visibility": {
            "diagnostics_authority_external": True,
            "explainability_authority_external": True,
            "recipient_authority_external": True,
            "consent_authority_external": True,
            "privacy_authority_external": True,
            "visibility_authority_external": True,
            "concierge_role": "bounded_consumer_orchestrator",
        },
        "explainability_summary": {
            "messaging_explainability_ref_count": len(explainability_refs),
            "latest_delivery_permitted": (
                bool(latest_ref.get("delivery_permitted", False)) if latest_ref is not None else None
            ),
            "latest_decision_reason": latest_ref.get("decision_reason") if latest_ref is not None else None,
            "latest_governance_boundary_involved": (
                latest_ref.get("governance_boundary_involved") if latest_ref is not None else None
            ),
            "latest_delivery_channel": latest_ref.get("delivery_channel") if latest_ref is not None else None,
            "latest_selected_service": latest_ref.get("selected_service") if latest_ref is not None else None,
            "latest_selected_target_id": latest_ref.get("selected_target_id") if latest_ref is not None else None,
            "latest_routing_path": latest_ref.get("routing_path") if latest_ref is not None else None,
        },
        "governance_outcome_visibility": {
            "expected_governance_outcomes_visible": True,
            "governance_policy_denied_count": policy_denied_count,
            "operational_error_count": operational_error_count,
            "successful_delivery_count": success_count,
            "governance_denial_is_runtime_failure": False,
        },
        "logging_strategy_visibility": {
            "governance_policy_denied_level": "info",
            "operational_delivery_failure_level": "error",
            "unexpected_runtime_condition_level": "warning",
            "normal_success_level": "debug",
        },
        "diagnostics_non_rights": {
            "creates_authority": False,
            "creates_truth": False,
            "creates_memory": False,
            "creates_identity": False,
            "redefines_governance_outcomes": False,
        },
    }


def _household_memory_governance_boundary_visibility(state) -> dict[str, Any]:
    """Return bounded household-memory governance boundary visibility from activity refs."""
    boundary_refs: list[dict[str, Any]] = []
    activities = [
        item
        for item in state.activities.values()
        if str(getattr(item, "intent_class", "")) == "push_person_message"
    ]

    for activity in sorted(
        activities,
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        for ref in list(getattr(activity, "external_refs", [])):
            if str(ref.get("ref_type", "") or "") == "household_memory_governance_boundary":
                boundary_refs.append(dict(ref))

    latest_ref = boundary_refs[0] if boundary_refs else None
    separation_ref_count = len(boundary_refs)
    latest_boundary_status = latest_ref.get("boundary_status") if latest_ref is not None else None
    latest_identity_separated = (
        bool(latest_ref.get("identity_separated", False)) if latest_ref is not None else None
    )
    latest_privacy_separated = (
        bool(latest_ref.get("privacy_separated", False)) if latest_ref is not None else None
    )
    latest_retention_separated = (
        bool(latest_ref.get("retention_separated", False)) if latest_ref is not None else None
    )

    def _separation_status(separated: bool | None) -> str | None:
        if separated is None:
            return None
        if separated:
            return latest_boundary_status or "active"
        return "inactive"

    return {
        "authority_visibility": {
            "household_memory_authority_external": True,
            "identity_authority_external": True,
            "occupancy_authority_external": True,
            "messaging_authority_external": True,
            "consent_authority_external": True,
            "privacy_authority_external": True,
            "source_of_truth_authority_external": True,
            "concierge_role": "bounded_consumer_orchestrator",
        },
        "boundary_visibility": {
            "household_memory_boundary_ref_count": len(boundary_refs),
            "latest_boundary_path": latest_ref.get("boundary_path") if latest_ref is not None else None,
            "latest_boundary_status": latest_ref.get("boundary_status") if latest_ref is not None else None,
            "latest_household_memory_role": (
                latest_ref.get("household_memory_role") if latest_ref is not None else None
            ),
            "latest_route_scope": latest_ref.get("route_scope") if latest_ref is not None else None,
            "latest_context_area_id": latest_ref.get("context_area_id") if latest_ref is not None else None,
            "latest_message_context_type": (
                latest_ref.get("message_context_type") if latest_ref is not None else None
            ),
        },
        "relationship_visibility": {
            "latest_delivery_channel": latest_ref.get("delivery_channel") if latest_ref is not None else None,
            "latest_selected_service": latest_ref.get("selected_service") if latest_ref is not None else None,
            "latest_selected_target_id": (
                latest_ref.get("selected_target_id") if latest_ref is not None else None
            ),
            "latest_routing_path": latest_ref.get("routing_path") if latest_ref is not None else None,
            "latest_explicit_entity_target": (
                bool(latest_ref.get("explicit_entity_target", False)) if latest_ref is not None else False
            ),
        },
        "diagnostics_non_rights": {
            "claims_household_truth_authority": False,
            "claims_identity_authority": False,
            "claims_occupancy_authority": False,
            "claims_messaging_authority": False,
            "claims_consent_authority": False,
            "claims_privacy_authority": False,
            "claims_source_of_truth_authority": False,
        },
    }


def _household_memory_ownership_consumption_boundary_visibility(state) -> dict[str, Any]:
    """Return bounded household-memory ownership/consumption visibility from activity refs."""
    boundary_refs: list[dict[str, Any]] = []
    activities = [
        item
        for item in state.activities.values()
        if str(getattr(item, "intent_class", "")) == "push_person_message"
    ]

    for activity in sorted(
        activities,
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        for ref in list(getattr(activity, "external_refs", [])):
            if str(ref.get("ref_type", "") or "") == "household_memory_ownership_consumption_boundary":
                boundary_refs.append(dict(ref))

    latest_ref = boundary_refs[0] if boundary_refs else None
    consumption_permitted_count = sum(
        1 for ref in boundary_refs if bool(ref.get("consumption_permitted", False))
    )
    consumption_denied_count = sum(
        1 for ref in boundary_refs if not bool(ref.get("consumption_permitted", False))
    )

    return {
        "authority_visibility": {
            "household_memory_authority_external": True,
            "identity_authority_external": True,
            "occupancy_authority_external": True,
            "messaging_authority_external": True,
            "consent_authority_external": True,
            "privacy_authority_external": True,
            "source_of_truth_authority_external": True,
            "concierge_role": "bounded_consumer_orchestrator",
        },
        "ownership_visibility": {
            "ownership_boundary_ref_count": len(boundary_refs),
            "latest_boundary_path": latest_ref.get("boundary_path") if latest_ref is not None else None,
            "latest_boundary_status": latest_ref.get("boundary_status") if latest_ref is not None else None,
            "latest_memory_owner": latest_ref.get("memory_owner") if latest_ref is not None else None,
            "latest_memory_runtime_owner": (
                latest_ref.get("memory_runtime_owner") if latest_ref is not None else None
            ),
        },
        "consumption_visibility": {
            "consumption_permitted_count": consumption_permitted_count,
            "consumption_denied_count": consumption_denied_count,
            "latest_consumption_permitted": (
                bool(latest_ref.get("consumption_permitted", False)) if latest_ref is not None else None
            ),
            "latest_consumption_decision_reason": (
                latest_ref.get("consumption_decision_reason") if latest_ref is not None else None
            ),
            "latest_delivery_channel": latest_ref.get("delivery_channel") if latest_ref is not None else None,
            "latest_selected_service": latest_ref.get("selected_service") if latest_ref is not None else None,
            "latest_selected_target_id": (
                latest_ref.get("selected_target_id") if latest_ref is not None else None
            ),
            "latest_routing_path": latest_ref.get("routing_path") if latest_ref is not None else None,
        },
        "ownership_boundary_assertions": {
            "ownership_is_not_authority": True,
            "ownership_does_not_replace_source_of_truth": True,
            "ownership_does_not_replace_identity": True,
            "ownership_does_not_replace_occupancy": True,
            "ownership_does_not_replace_messaging": True,
            "ownership_does_not_replace_consent": True,
            "ownership_does_not_replace_privacy": True,
        },
        "consumption_boundary_assertions": {
            "consumption_is_not_authority": True,
            "consumption_does_not_replace_identity": True,
            "consumption_does_not_replace_occupancy": True,
            "consumption_does_not_replace_messaging": True,
            "consumption_does_not_replace_consent": True,
            "consumption_does_not_replace_privacy": True,
            "consumption_does_not_replace_source_of_truth": True,
        },
        "diagnostics_non_rights": {
            "claims_household_truth_authority": False,
            "claims_identity_authority": False,
            "claims_occupancy_authority": False,
            "claims_messaging_authority": False,
            "claims_consent_authority": False,
            "claims_privacy_authority": False,
            "claims_source_of_truth_authority": False,
        },
    }


def _household_memory_identity_privacy_retention_separation_visibility(state) -> dict[str, Any]:
    """Return bounded household-memory identity/privacy/retention separation visibility."""
    boundary_refs: list[dict[str, Any]] = []
    activities = [
        item
        for item in state.activities.values()
        if str(getattr(item, "intent_class", "")) == "push_person_message"
    ]

    for activity in sorted(
        activities,
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        for ref in list(getattr(activity, "external_refs", [])):
            if (
                str(ref.get("ref_type", "") or "")
                == "household_memory_identity_privacy_retention_separation_boundary"
            ):
                boundary_refs.append(dict(ref))

    latest_ref = boundary_refs[0] if boundary_refs else None
    separation_ref_count = len(boundary_refs)
    latest_boundary_status = latest_ref.get("boundary_status") if latest_ref is not None else None
    latest_identity_separated = (
        bool(latest_ref.get("identity_separated", False)) if latest_ref is not None else None
    )
    latest_privacy_separated = (
        bool(latest_ref.get("privacy_separated", False)) if latest_ref is not None else None
    )
    latest_retention_separated = (
        bool(latest_ref.get("retention_separated", False)) if latest_ref is not None else None
    )

    def _separation_status(separated: bool | None) -> str | None:
        if separated is None:
            return None
        if separated:
            return latest_boundary_status or "active"
        return "inactive"

    return {
        "authority_visibility": {
            "identity_authority_external": True,
            "privacy_authority_external": True,
            "retention_authority_external": True,
            "source_of_truth_authority_external": True,
            "concierge_role": "bounded_consumer_orchestrator",
        },
        "separation_visibility": {
            "separation_boundary_ref_count": separation_ref_count,
            "identity_separation_ref_count": separation_ref_count,
            "privacy_separation_ref_count": separation_ref_count,
            "retention_separation_ref_count": separation_ref_count,
            "latest_boundary_path": latest_ref.get("boundary_path") if latest_ref is not None else None,
            "latest_boundary_status": latest_boundary_status,
            "latest_identity_separated": latest_identity_separated,
            "latest_privacy_separated": latest_privacy_separated,
            "latest_retention_separated": latest_retention_separated,
            "latest_identity_separation_status": _separation_status(latest_identity_separated),
            "latest_privacy_separation_status": _separation_status(latest_privacy_separated),
            "latest_retention_separation_status": _separation_status(latest_retention_separated),
            "latest_separation_permitted": (
                bool(latest_ref.get("separation_permitted", False)) if latest_ref is not None else None
            ),
            "latest_separation_decision_reason": (
                latest_ref.get("separation_decision_reason") if latest_ref is not None else None
            ),
            "latest_delivery_channel": latest_ref.get("delivery_channel") if latest_ref is not None else None,
            "latest_selected_service": latest_ref.get("selected_service") if latest_ref is not None else None,
            "latest_selected_target_id": (
                latest_ref.get("selected_target_id") if latest_ref is not None else None
            ),
            "latest_routing_path": latest_ref.get("routing_path") if latest_ref is not None else None,
        },
        "separation_boundary_assertions": {
            "identity_reference_is_not_authority": True,
            "privacy_reference_is_not_authority": True,
            "retention_reference_is_not_authority": True,
            "separation_does_not_replace_source_of_truth": True,
            "separation_does_not_replace_identity": True,
            "separation_does_not_replace_privacy": True,
            "separation_does_not_replace_retention": True,
        },
        "diagnostics_non_rights": {
            "claims_household_truth_authority": False,
            "claims_identity_authority": False,
            "claims_privacy_authority": False,
            "claims_retention_authority": False,
            "claims_source_of_truth_authority": False,
        },
    }


def _household_memory_messaging_continuity_affinity_occupancy_restoration_separation_visibility(
    state,
) -> dict[str, Any]:
    """Return bounded household-memory separation visibility for #347 domains."""
    boundary_refs: list[dict[str, Any]] = []
    activities = [
        item
        for item in state.activities.values()
        if str(getattr(item, "intent_class", "")) == "push_person_message"
    ]

    for activity in sorted(
        activities,
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        for ref in list(getattr(activity, "external_refs", [])):
            if (
                str(ref.get("ref_type", "") or "")
                == "household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary"
            ):
                boundary_refs.append(dict(ref))

    latest_ref = boundary_refs[0] if boundary_refs else None
    separation_ref_count = len(boundary_refs)
    latest_boundary_status = latest_ref.get("boundary_status") if latest_ref is not None else None
    latest_messaging_separated = (
        bool(latest_ref.get("messaging_separated", False)) if latest_ref is not None else None
    )
    latest_continuity_separated = (
        bool(latest_ref.get("continuity_separated", False)) if latest_ref is not None else None
    )
    latest_affinity_separated = (
        bool(latest_ref.get("affinity_separated", False)) if latest_ref is not None else None
    )
    latest_occupancy_separated = (
        bool(latest_ref.get("occupancy_separated", False)) if latest_ref is not None else None
    )
    latest_restoration_separated = (
        bool(latest_ref.get("restoration_separated", False)) if latest_ref is not None else None
    )

    def _separation_status(separated: bool | None) -> str | None:
        if separated is None:
            return None
        if separated:
            return latest_boundary_status or "active"
        return "inactive"

    return {
        "authority_visibility": {
            "messaging_authority_external": True,
            "continuity_authority_external": True,
            "affinity_authority_external": True,
            "occupancy_authority_external": True,
            "restoration_authority_external": True,
            "source_of_truth_authority_external": True,
            "concierge_role": "bounded_consumer_orchestrator",
        },
        "separation_visibility": {
            "separation_boundary_ref_count": separation_ref_count,
            "messaging_separation_ref_count": separation_ref_count,
            "continuity_separation_ref_count": separation_ref_count,
            "affinity_separation_ref_count": separation_ref_count,
            "occupancy_separation_ref_count": separation_ref_count,
            "restoration_separation_ref_count": separation_ref_count,
            "latest_boundary_path": latest_ref.get("boundary_path") if latest_ref is not None else None,
            "latest_boundary_status": latest_boundary_status,
            "latest_messaging_separated": latest_messaging_separated,
            "latest_continuity_separated": latest_continuity_separated,
            "latest_affinity_separated": latest_affinity_separated,
            "latest_occupancy_separated": latest_occupancy_separated,
            "latest_restoration_separated": latest_restoration_separated,
            "latest_messaging_separation_status": _separation_status(latest_messaging_separated),
            "latest_continuity_separation_status": _separation_status(latest_continuity_separated),
            "latest_affinity_separation_status": _separation_status(latest_affinity_separated),
            "latest_occupancy_separation_status": _separation_status(latest_occupancy_separated),
            "latest_restoration_separation_status": _separation_status(latest_restoration_separated),
            "latest_separation_permitted": (
                bool(latest_ref.get("separation_permitted", False)) if latest_ref is not None else None
            ),
            "latest_separation_decision_reason": (
                latest_ref.get("separation_decision_reason") if latest_ref is not None else None
            ),
            "latest_delivery_channel": latest_ref.get("delivery_channel") if latest_ref is not None else None,
            "latest_selected_service": latest_ref.get("selected_service") if latest_ref is not None else None,
            "latest_selected_target_id": (
                latest_ref.get("selected_target_id") if latest_ref is not None else None
            ),
            "latest_routing_path": latest_ref.get("routing_path") if latest_ref is not None else None,
        },
        "separation_boundary_assertions": {
            "memory_reference_is_not_messaging_authority": True,
            "memory_reference_is_not_continuity_authority": True,
            "memory_reference_is_not_affinity_authority": True,
            "memory_reference_is_not_occupancy_authority": True,
            "memory_reference_is_not_restoration_authority": True,
            "separation_does_not_replace_source_of_truth": True,
        },
        "diagnostics_non_rights": {
            "claims_household_truth_authority": False,
            "claims_messaging_authority": False,
            "claims_continuity_authority": False,
            "claims_affinity_authority": False,
            "claims_occupancy_authority": False,
            "claims_restoration_authority": False,
            "claims_source_of_truth_authority": False,
        },
    }


def _household_memory_provenance_diagnostics_explainability_visibility(state) -> dict[str, Any]:
    """Return bounded household-memory provenance/diagnostics/explainability visibility."""
    provenance_diag_refs: list[dict[str, Any]] = []
    governance_refs: list[dict[str, Any]] = []
    ownership_refs: list[dict[str, Any]] = []
    identity_privacy_retention_refs: list[dict[str, Any]] = []
    messaging_continuity_affinity_occupancy_restoration_refs: list[dict[str, Any]] = []
    messaging_provenance_refs: list[dict[str, Any]] = []
    activities = [
        item
        for item in state.activities.values()
        if str(getattr(item, "intent_class", "")) == "push_person_message"
    ]

    for activity in sorted(
        activities,
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        for ref in list(getattr(activity, "external_refs", [])):
            ref_type = str(ref.get("ref_type", "") or "")
            if ref_type == "household_memory_provenance_diagnostics_explainability_boundary":
                provenance_diag_refs.append(dict(ref))
            elif ref_type == "household_memory_governance_boundary":
                governance_refs.append(dict(ref))
            elif ref_type == "household_memory_ownership_consumption_boundary":
                ownership_refs.append(dict(ref))
            elif ref_type == "household_memory_identity_privacy_retention_separation_boundary":
                identity_privacy_retention_refs.append(dict(ref))
            elif (
                ref_type
                == "household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary"
            ):
                messaging_continuity_affinity_occupancy_restoration_refs.append(dict(ref))
            elif ref_type == "messaging_provenance":
                messaging_provenance_refs.append(dict(ref))

    latest_ref = provenance_diag_refs[0] if provenance_diag_refs else None

    return {
        "authority_visibility": {
            "household_memory_authority_external": True,
            "provenance_authority_external": True,
            "identity_authority_external": True,
            "messaging_authority_external": True,
            "occupancy_authority_external": True,
            "privacy_authority_external": True,
            "retention_authority_external": True,
            "restoration_authority_external": True,
            "source_of_truth_authority_external": True,
            "concierge_role": "bounded_consumer_orchestrator",
        },
        "provenance_visibility": {
            "provenance_diagnostics_boundary_ref_count": len(provenance_diag_refs),
            "messaging_provenance_ref_count": len(messaging_provenance_refs),
            "latest_boundary_path": latest_ref.get("boundary_path") if latest_ref is not None else None,
            "latest_boundary_status": latest_ref.get("boundary_status") if latest_ref is not None else None,
            "latest_provenance_id": latest_ref.get("provenance_id") if latest_ref is not None else None,
            "latest_provenance_source_service": (
                latest_ref.get("provenance_source_service") if latest_ref is not None else None
            ),
            "latest_provenance_created_in_room": (
                latest_ref.get("provenance_created_in_room") if latest_ref is not None else None
            ),
            "latest_provenance_status": latest_ref.get("provenance_status") if latest_ref is not None else None,
        },
        "diagnostics_visibility": {
            "governance_boundary_ref_count": len(governance_refs),
            "ownership_boundary_ref_count": len(ownership_refs),
            "consumption_boundary_ref_count": len(ownership_refs),
            "identity_privacy_retention_separation_ref_count": len(identity_privacy_retention_refs),
            "messaging_continuity_affinity_occupancy_restoration_separation_ref_count": len(
                messaging_continuity_affinity_occupancy_restoration_refs
            ),
            "provenance_ref_count": len(messaging_provenance_refs),
            "latest_governance_status": "active" if governance_refs else None,
            "latest_ownership_status": "active" if ownership_refs else None,
            "latest_consumption_status": "active" if ownership_refs else None,
            "latest_identity_privacy_retention_separation_status": (
                "active" if identity_privacy_retention_refs else None
            ),
            "latest_messaging_continuity_affinity_occupancy_restoration_separation_status": (
                "active" if messaging_continuity_affinity_occupancy_restoration_refs else None
            ),
            "latest_provenance_status": "active" if messaging_provenance_refs else None,
        },
        "explainability_visibility": {
            "what_happened_explainable": latest_ref is not None,
            "why_it_happened_explainable": latest_ref is not None,
            "which_boundary_applied_explainable": latest_ref is not None,
            "which_authority_established_outcome_explainable": latest_ref is not None,
            "which_authority_not_claimed_explainable": latest_ref is not None,
            "latest_delivery_permitted": (
                bool(latest_ref.get("delivery_permitted", False)) if latest_ref is not None else None
            ),
            "latest_decision_reason": latest_ref.get("decision_reason") if latest_ref is not None else None,
            "latest_governance_boundary_involved": (
                latest_ref.get("governance_boundary_involved") if latest_ref is not None else None
            ),
            "latest_delivery_channel": latest_ref.get("delivery_channel") if latest_ref is not None else None,
            "latest_selected_service": latest_ref.get("selected_service") if latest_ref is not None else None,
            "latest_selected_target_id": (
                latest_ref.get("selected_target_id") if latest_ref is not None else None
            ),
            "latest_routing_path": latest_ref.get("routing_path") if latest_ref is not None else None,
            "runtime_derived_only": True,
            "generated_reasoning_used": False,
            "probabilistic_reasoning_used": False,
        },
        "diagnostics_non_rights": {
            "claims_household_truth_authority": False,
            "claims_identity_authority": False,
            "claims_messaging_authority": False,
            "claims_continuity_authority": False,
            "claims_affinity_authority": False,
            "claims_occupancy_authority": False,
            "claims_privacy_authority": False,
            "claims_retention_authority": False,
            "claims_restoration_authority": False,
            "claims_source_of_truth_authority": False,
        },
    }


def _continuity_affinity_diagnostics_explainability_visibility(state) -> dict[str, Any]:
    """Return bounded continuity/affinity diagnostics visibility from execution envelope references."""
    execution_envelope_refs: list[dict[str, Any]] = []

    for activity in sorted(
        state.activities.values(),
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        for ref in list(getattr(activity, "external_refs", [])):
            if str(ref.get("ref_type", "") or "") == "execution_envelope":
                execution_envelope_refs.append(dict(ref))

    latest_envelope = execution_envelope_refs[0] if execution_envelope_refs else None
    latest_direct_envelope = next(
        (
            ref
            for ref in execution_envelope_refs
            if str(ref.get("execution_kind", "") or "") == "direct"
        ),
        None,
    )

    continuity_applicable = (
        bool(latest_envelope.get("continuity_governance_applicable", False))
        if latest_envelope is not None
        else False
    )
    affinity_applicable = (
        bool(latest_envelope.get("affinity_governance_applicable", False))
        if latest_envelope is not None
        else False
    )

    continuity_unavailable_reason = "execution_envelope_not_available"
    affinity_unavailable_reason = "execution_envelope_not_available"
    if latest_envelope is not None:
        continuity_unavailable_reason = (
            "available"
            if continuity_applicable
            else str(latest_envelope.get("continuity_governance_path", "") or "not_applicable")
        )
        affinity_unavailable_reason = (
            "available"
            if affinity_applicable
            else str(latest_envelope.get("affinity_governance_path", "") or "not_applicable")
        )

    return {
        "authority_visibility": {
            "continuity_authority_external": True,
            "person_room_affinity_authority_external": True,
            "identity_authority_external": True,
            "occupancy_authority_external": True,
            "memory_authority_external": True,
            "concierge_role": "bounded_consumer_orchestrator",
        },
        "availability_explainability": {
            "continuity_available": continuity_applicable,
            "continuity_unavailable_reason": continuity_unavailable_reason,
            "affinity_available": affinity_applicable,
            "affinity_unavailable_reason": affinity_unavailable_reason,
            "latest_continuity_path": (
                latest_envelope.get("continuity_governance_path")
                if latest_envelope is not None
                else None
            ),
            "latest_affinity_path": (
                latest_envelope.get("affinity_governance_path")
                if latest_envelope is not None
                else None
            ),
            "latest_direct_continuity_path": (
                latest_direct_envelope.get("continuity_governance_path")
                if latest_direct_envelope is not None
                else None
            ),
            "latest_direct_affinity_path": (
                latest_direct_envelope.get("affinity_governance_path")
                if latest_direct_envelope is not None
                else None
            ),
        },
        "ownership_boundary_visibility": {
            "continuity_owns_identity": (
                bool(latest_envelope.get("continuity_owns_identity", False))
                if latest_envelope is not None
                else False
            ),
            "continuity_owns_occupancy": (
                bool(latest_envelope.get("continuity_owns_occupancy", False))
                if latest_envelope is not None
                else False
            ),
            "continuity_owns_memory": (
                bool(latest_envelope.get("continuity_owns_memory", False))
                if latest_envelope is not None
                else False
            ),
            "affinity_owns_identity": (
                bool(latest_envelope.get("affinity_owns_identity", False))
                if latest_envelope is not None
                else False
            ),
            "affinity_owns_room_truth": (
                bool(latest_envelope.get("affinity_owns_room_truth", False))
                if latest_envelope is not None
                else False
            ),
            "affinity_owns_occupancy": (
                bool(latest_envelope.get("affinity_owns_occupancy", False))
                if latest_envelope is not None
                else False
            ),
            "affinity_owns_memory": (
                bool(latest_envelope.get("affinity_owns_memory", False))
                if latest_envelope is not None
                else False
            ),
            "memory_owns_identity": (
                bool(latest_envelope.get("memory_owns_identity", False))
                if latest_envelope is not None
                else False
            ),
            "memory_owns_retention_policy": (
                bool(latest_envelope.get("memory_owns_retention_policy", False))
                if latest_envelope is not None
                else False
            ),
            "memory_owns_storage": (
                bool(latest_envelope.get("memory_owns_storage", False))
                if latest_envelope is not None
                else False
            ),
            "memory_owns_provenance": (
                bool(latest_envelope.get("memory_owns_provenance", False))
                if latest_envelope is not None
                else False
            ),
        },
        "safeguard_visibility": {
            "privacy_boundary_preserved": (
                bool(latest_envelope.get("continuity_privacy_boundary_preserved", False))
                if latest_envelope is not None
                else False
            ),
            "affinity_privacy_boundary_preserved": (
                bool(latest_envelope.get("affinity_privacy_boundary_preserved", False))
                if latest_envelope is not None
                else False
            ),
            "affinity_guest_safe_boundary_preserved": (
                bool(latest_envelope.get("affinity_guest_safe_boundary_preserved", False))
                if latest_envelope is not None
                else False
            ),
            "privacy_memory_guest_safe_boundary_preserved": (
                bool(latest_envelope.get("privacy_memory_guest_safe_boundary_preserved", False))
                if latest_envelope is not None
                else False
            ),
        },
        "traceability_visibility": {
            "execution_envelope_ref_count": len(execution_envelope_refs),
            "latest_execution_kind": (
                latest_envelope.get("execution_kind")
                if latest_envelope is not None
                else None
            ),
            "latest_plan_kind": (
                latest_envelope.get("plan_kind")
                if latest_envelope is not None
                else None
            ),
        },
        "deferred_functionality_visibility": {
            "restoration_governance_boundary": "#329",
            "occupancy_presence_governance": "#333+#334+#335+#336+#337",
            "release_3_validation": "#338",
        },
        "diagnostics_non_rights": {
            "creates_authority": False,
            "creates_outcomes": False,
            "modifies_continuity_behavior": False,
            "modifies_affinity_behavior": False,
            "modifies_privacy_behavior": False,
            "creates_memory": False,
            "creates_identity": False,
        },
    }


def _occupancy_presence_diagnostics_explainability_visibility(state) -> dict[str, Any]:
    """Return bounded occupancy/presence diagnostics visibility from execution envelope references."""
    execution_envelope_refs: list[dict[str, Any]] = []

    for activity in sorted(
        state.activities.values(),
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        for ref in list(getattr(activity, "external_refs", [])):
            if str(ref.get("ref_type", "") or "") == "execution_envelope":
                execution_envelope_refs.append(dict(ref))

    latest_envelope = execution_envelope_refs[0] if execution_envelope_refs else None
    latest_orchestration_envelope = next(
        (
            ref
            for ref in execution_envelope_refs
            if str(ref.get("execution_kind", "") or "") == "orchestration"
        ),
        None,
    )
    latest_direct_envelope = next(
        (
            ref
            for ref in execution_envelope_refs
            if str(ref.get("execution_kind", "") or "") == "direct"
        ),
        None,
    )

    def _availability(envelope: dict[str, Any] | None, applicable_key: str, path_key: str) -> tuple[bool, str]:
        if envelope is None:
            return False, "execution_envelope_not_available"
        applicable = bool(envelope.get(applicable_key, False))
        if applicable:
            return True, "available"
        return False, str(envelope.get(path_key, "") or "not_applicable")

    latest_occupancy_applicable, latest_occupancy_unavailable_reason = _availability(
        latest_envelope,
        "occupancy_governance_applicable",
        "occupancy_governance_path",
    )
    latest_presence_applicable, latest_presence_unavailable_reason = _availability(
        latest_envelope,
        "presence_governance_applicable",
        "presence_governance_path",
    )
    latest_guest_unknown_applicable, latest_guest_unknown_unavailable_reason = _availability(
        latest_envelope,
        "guest_unknown_behavior_applicable",
        "guest_unknown_behavior_path",
    )
    latest_multi_occupant_applicable, latest_multi_occupant_unavailable_reason = _availability(
        latest_envelope,
        "multi_occupant_behavior_applicable",
        "multi_occupant_behavior_path",
    )

    return {
        "authority_visibility": {
            "occupancy_authority_external": True,
            "occupancy_policy_authority_external": True,
            "occupancy_truth_authority_external": True,
            "room_truth_authority_external": True,
            "presence_authority_external": True,
            "presence_policy_authority_external": True,
            "presence_truth_authority_external": True,
            "identity_authority_external": True,
            "household_memory_authority_external": True,
            "restoration_authority_external": (
                bool(latest_envelope.get("restoration_authority_external", False))
                if latest_envelope is not None
                else False
            ),
            "concierge_role": "bounded_consumer_orchestrator",
        },
        "governance_visibility": {
            "latest_occupancy_governance_applicable": latest_occupancy_applicable,
            "latest_occupancy_governance_path": (
                latest_envelope.get("occupancy_governance_path") if latest_envelope is not None else None
            ),
            "latest_occupancy_governance_unavailable_reason": latest_occupancy_unavailable_reason,
            "latest_presence_governance_applicable": latest_presence_applicable,
            "latest_presence_governance_path": (
                latest_envelope.get("presence_governance_path") if latest_envelope is not None else None
            ),
            "latest_presence_governance_unavailable_reason": latest_presence_unavailable_reason,
            "latest_orchestration_occupancy_governance_applicable": (
                bool(latest_orchestration_envelope.get("occupancy_governance_applicable", False))
                if latest_orchestration_envelope is not None
                else False
            ),
            "latest_orchestration_occupancy_governance_path": (
                latest_orchestration_envelope.get("occupancy_governance_path")
                if latest_orchestration_envelope is not None
                else None
            ),
            "latest_orchestration_presence_governance_applicable": (
                bool(latest_orchestration_envelope.get("presence_governance_applicable", False))
                if latest_orchestration_envelope is not None
                else False
            ),
            "latest_orchestration_presence_governance_path": (
                latest_orchestration_envelope.get("presence_governance_path")
                if latest_orchestration_envelope is not None
                else None
            ),
            "latest_direct_occupancy_governance_applicable": (
                bool(latest_direct_envelope.get("occupancy_governance_applicable", False))
                if latest_direct_envelope is not None
                else False
            ),
            "latest_direct_occupancy_governance_path": (
                latest_direct_envelope.get("occupancy_governance_path")
                if latest_direct_envelope is not None
                else None
            ),
            "latest_direct_presence_governance_applicable": (
                bool(latest_direct_envelope.get("presence_governance_applicable", False))
                if latest_direct_envelope is not None
                else False
            ),
            "latest_direct_presence_governance_path": (
                latest_direct_envelope.get("presence_governance_path")
                if latest_direct_envelope is not None
                else None
            ),
        },
        "behavior_visibility": {
            "latest_guest_unknown_behavior_applicable": latest_guest_unknown_applicable,
            "latest_guest_unknown_behavior_path": (
                latest_envelope.get("guest_unknown_behavior_path") if latest_envelope is not None else None
            ),
            "latest_guest_unknown_behavior_unavailable_reason": latest_guest_unknown_unavailable_reason,
            "latest_guest_unknown_occupant_state": (
                latest_envelope.get("guest_unknown_occupant_state") if latest_envelope is not None else None
            ),
            "latest_guest_unknown_restoration_eligibility_allowed": (
                bool(latest_envelope.get("guest_unknown_restoration_eligibility_allowed", False))
                if latest_envelope is not None
                else False
            ),
            "latest_multi_occupant_behavior_applicable": latest_multi_occupant_applicable,
            "latest_multi_occupant_behavior_path": (
                latest_envelope.get("multi_occupant_behavior_path") if latest_envelope is not None else None
            ),
            "latest_multi_occupant_behavior_unavailable_reason": latest_multi_occupant_unavailable_reason,
            "latest_multi_occupant_occupant_state": (
                latest_envelope.get("multi_occupant_occupant_state") if latest_envelope is not None else None
            ),
            "latest_multi_occupant_mode_active": (
                bool(latest_envelope.get("multi_occupant_mode_active", False))
                if latest_envelope is not None
                else False
            ),
            "latest_multi_occupant_conflict_aware_behavior_required": (
                bool(latest_envelope.get("multi_occupant_conflict_aware_behavior_required", False))
                if latest_envelope is not None
                else False
            ),
            "latest_multi_occupant_restoration_eligibility_allowed": (
                bool(latest_envelope.get("multi_occupant_restoration_eligibility_allowed", False))
                if latest_envelope is not None
                else False
            ),
        },
        "ownership_boundary_visibility": {
            "occupancy_is_authority": False,
            "presence_is_authority": False,
            "identity_is_authority": False,
            "room_truth_is_authority": False,
            "restoration_is_authority": False,
            "occupancy_owns_room_truth": (
                bool(latest_envelope.get("occupancy_owns_room_truth", False))
                if latest_envelope is not None
                else False
            ),
            "occupancy_owns_identity": (
                bool(latest_envelope.get("occupancy_owns_identity", False)) if latest_envelope is not None else False
            ),
            "occupancy_owns_restoration": (
                bool(latest_envelope.get("occupancy_owns_restoration", False)) if latest_envelope is not None else False
            ),
            "presence_owns_room_truth": (
                bool(latest_envelope.get("presence_owns_room_truth", False))
                if latest_envelope is not None
                else False
            ),
            "presence_owns_identity": (
                bool(latest_envelope.get("presence_owns_identity", False)) if latest_envelope is not None else False
            ),
            "presence_owns_restoration": (
                bool(latest_envelope.get("presence_owns_restoration", False)) if latest_envelope is not None else False
            ),
            "occupancy_truth_authority_external": True,
            "presence_truth_authority_external": True,
            "household_memory_authority_external": True,
            "restoration_authority_external": (
                bool(latest_envelope.get("restoration_authority_external", False))
                if latest_envelope is not None
                else False
            ),
        },
        "safeguard_visibility": {
            "guest_safe_boundary_preserved": (
                bool(
                    (latest_envelope.get("occupancy_guest_safe_boundary_preserved", False))
                    or (latest_envelope.get("presence_guest_safe_boundary_preserved", False))
                    or (latest_envelope.get("affinity_guest_safe_boundary_preserved", False))
                    or (latest_envelope.get("privacy_memory_guest_safe_boundary_preserved", False))
                    or (latest_envelope.get("restoration_guest_safe_boundary_preserved", False))
                )
                if latest_envelope is not None
                else False
            ),
            "privacy_boundary_preserved": (
                bool(
                    (latest_envelope.get("occupancy_privacy_boundary_preserved", False))
                    or (latest_envelope.get("presence_privacy_boundary_preserved", False))
                    or (latest_envelope.get("continuity_privacy_boundary_preserved", False))
                    or (latest_envelope.get("affinity_privacy_boundary_preserved", False))
                    or (latest_envelope.get("restoration_privacy_boundary_preserved", False))
                )
                if latest_envelope is not None
                else False
            ),
            "guest_safe_mode_preserved": (
                bool(latest_envelope.get("guest_unknown_guest_safe_mode_active", False))
                if latest_envelope is not None
                else False
            ),
            "unknown_occupant_mode_preserved": (
                bool(latest_envelope.get("guest_unknown_unknown_occupant_mode_active", False))
                if latest_envelope is not None
                else False
            ),
        },
        "traceability_visibility": {
            "execution_envelope_ref_count": len(execution_envelope_refs),
            "orchestration_envelope_ref_count": sum(
                1
                for ref in execution_envelope_refs
                if str(ref.get("execution_kind", "") or "") == "orchestration"
            ),
            "direct_envelope_ref_count": sum(
                1
                for ref in execution_envelope_refs
                if str(ref.get("execution_kind", "") or "") == "direct"
            ),
            "latest_execution_kind": (
                latest_envelope.get("execution_kind") if latest_envelope is not None else None
            ),
            "latest_occupancy_governance_path": (
                latest_envelope.get("occupancy_governance_path") if latest_envelope is not None else None
            ),
            "latest_presence_governance_path": (
                latest_envelope.get("presence_governance_path") if latest_envelope is not None else None
            ),
            "latest_guest_unknown_behavior_path": (
                latest_envelope.get("guest_unknown_behavior_path") if latest_envelope is not None else None
            ),
            "latest_multi_occupant_behavior_path": (
                latest_envelope.get("multi_occupant_behavior_path") if latest_envelope is not None else None
            ),
            "latest_direct_occupancy_governance_path": (
                latest_direct_envelope.get("occupancy_governance_path") if latest_direct_envelope is not None else None
            ),
            "latest_direct_presence_governance_path": (
                latest_direct_envelope.get("presence_governance_path") if latest_direct_envelope is not None else None
            ),
            "latest_direct_guest_unknown_behavior_path": (
                latest_direct_envelope.get("guest_unknown_behavior_path") if latest_direct_envelope is not None else None
            ),
            "latest_direct_multi_occupant_behavior_path": (
                latest_direct_envelope.get("multi_occupant_behavior_path") if latest_direct_envelope is not None else None
            ),
        },
        "deferred_functionality_visibility": {
            "occupancy_governance_boundary": "#333",
            "presence_governance_boundary": "#334",
            "guest_unknown_occupant_behavior": "#335",
            "multi_occupant_behavior": "#336",
            "occupancy_presence_diagnostics_explainability": "#337",
            "release_3_validation": "#338",
        },
        "diagnostics_non_rights": {
            "creates_authority": False,
            "creates_outcomes": False,
            "modifies_occupancy_behavior": False,
            "modifies_presence_behavior": False,
            "modifies_guest_unknown_behavior": False,
            "modifies_multi_occupant_behavior": False,
            "creates_occupancy_truth": False,
            "creates_presence_truth": False,
            "creates_identity": False,
            "creates_room_truth": False,
        },
    }


def _restoration_diagnostics_explainability_visibility(state) -> dict[str, Any]:
    """Return bounded restoration diagnostics/explainability visibility from existing refs."""
    execution_envelope_refs: list[dict[str, Any]] = []
    preservation_alignment_refs: list[dict[str, Any]] = []

    for activity in sorted(
        state.activities.values(),
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        for ref in list(getattr(activity, "external_refs", [])):
            ref_type = str(ref.get("ref_type", "") or "")
            if ref_type == "execution_envelope":
                execution_envelope_refs.append(dict(ref))
            if ref_type == "preservation_alignment":
                preservation_alignment_refs.append(dict(ref))

    latest_envelope = execution_envelope_refs[0] if execution_envelope_refs else None
    latest_direct_envelope = next(
        (
            ref
            for ref in execution_envelope_refs
            if str(ref.get("execution_kind", "") or "") == "direct"
        ),
        None,
    )
    latest_preservation = preservation_alignment_refs[0] if preservation_alignment_refs else None

    restoration_available = (
        bool(latest_envelope.get("experience_restoration_boundary_applicable", False))
        if latest_envelope is not None
        else False
    )
    restoration_unavailable_reason = "execution_envelope_not_available"
    if latest_envelope is not None:
        restoration_unavailable_reason = (
            "available"
            if restoration_available
            else str(
                latest_envelope.get("experience_restoration_path", "")
                or latest_envelope.get("restoration_outcome_reason", "")
                or "not_applicable"
            )
        )

    restoration_applied = (
        bool(latest_envelope.get("restoration_applied", False))
        if latest_envelope is not None
        else False
    )

    return {
        "authority_visibility": {
            "restoration_authority_external": (
                bool(latest_envelope.get("restoration_authority_external", False))
                if latest_envelope is not None
                else False
            ),
            "restoration_policy_authority_external": (
                bool(latest_envelope.get("restoration_policy_authority_external", False))
                if latest_envelope is not None
                else False
            ),
            "restoration_authority_transferred": (
                bool(latest_envelope.get("restoration_authority_transferred", False))
                if latest_envelope is not None
                else False
            ),
            "concierge_role": "bounded_consumer_orchestrator",
        },
        "restoration_explainability": {
            "restoration_available": restoration_available,
            "restoration_unavailable_reason": restoration_unavailable_reason,
            "restoration_applicable": (
                bool(latest_envelope.get("experience_restoration_outcome_applicable", False))
                if latest_envelope is not None
                else False
            ),
            "restoration_eligible": (
                bool(latest_envelope.get("restoration_eligible", False))
                if latest_envelope is not None
                else False
            ),
            "restoration_applied": restoration_applied,
            "restoration_outcome_path": (
                latest_envelope.get("experience_restoration_outcome_path")
                if latest_envelope is not None
                else None
            ),
            "restoration_outcome_reason": (
                latest_envelope.get("restoration_outcome_reason")
                if latest_envelope is not None
                else None
            ),
            "selected_experience_id": (
                latest_envelope.get("restoration_selected_experience_id")
                if latest_envelope is not None
                else None
            ),
            "restoration_suppression_reason": (
                "not_suppressed"
                if restoration_applied
                else (
                    latest_envelope.get("restoration_outcome_reason")
                    if latest_envelope is not None
                    else "execution_envelope_not_available"
                )
            ),
            "direct_path_reason": (
                latest_direct_envelope.get("restoration_outcome_reason")
                if latest_direct_envelope is not None
                else None
            ),
        },
        "preservation_alignment_explainability": {
            "alignment_applicable": (
                bool(latest_envelope.get("e3a_preservation_alignment_applicable", False))
                if latest_envelope is not None
                else False
            ),
            "alignment_path": (
                latest_envelope.get("e3a_preservation_alignment_path")
                if latest_envelope is not None
                else None
            ),
            "alignment_eligible": (
                bool(latest_envelope.get("e3a_preservation_eligible", False))
                if latest_envelope is not None
                else False
            ),
            "alignment_reason": (
                latest_envelope.get("e3a_preservation_alignment_reason")
                if latest_envelope is not None
                else None
            ),
            "direct_alignment_path": (
                latest_direct_envelope.get("e3a_preservation_alignment_path")
                if latest_direct_envelope is not None
                else None
            ),
            "direct_alignment_reason": (
                latest_direct_envelope.get("e3a_preservation_alignment_reason")
                if latest_direct_envelope is not None
                else None
            ),
            "consumes_restoration_outcomes": (
                bool(latest_envelope.get("e3a_preservation_consumes_restoration_outcomes", False))
                if latest_envelope is not None
                else False
            ),
        },
        "governance_controls_visibility": {
            "restoration_diagnostics_behavior_enabled": (
                bool(latest_envelope.get("restoration_diagnostics_behavior_enabled", False))
                if latest_envelope is not None
                else False
            ),
            "restoration_decision_behavior_enabled": (
                bool(latest_envelope.get("restoration_decision_behavior_enabled", False))
                if latest_envelope is not None
                else False
            ),
            "restoration_execution_enabled": (
                bool(latest_envelope.get("restoration_execution_enabled", False))
                if latest_envelope is not None
                else False
            ),
            "direct_restoration_diagnostics_behavior_enabled": (
                bool(latest_direct_envelope.get("restoration_diagnostics_behavior_enabled", False))
                if latest_direct_envelope is not None
                else False
            ),
            "direct_restoration_decision_behavior_enabled": (
                bool(latest_direct_envelope.get("restoration_decision_behavior_enabled", False))
                if latest_direct_envelope is not None
                else False
            ),
            "direct_restoration_execution_enabled": (
                bool(latest_direct_envelope.get("restoration_execution_enabled", False))
                if latest_direct_envelope is not None
                else False
            ),
        },
        "ownership_boundary_visibility": {
            "restoration_owns_identity": (
                bool(latest_envelope.get("restoration_owns_identity", False))
                if latest_envelope is not None
                else False
            ),
            "restoration_owns_occupancy": (
                bool(latest_envelope.get("restoration_owns_occupancy", False))
                if latest_envelope is not None
                else False
            ),
            "restoration_owns_continuity": (
                bool(latest_envelope.get("restoration_owns_continuity", False))
                if latest_envelope is not None
                else False
            ),
            "restoration_owns_affinity": (
                bool(latest_envelope.get("restoration_owns_affinity", False))
                if latest_envelope is not None
                else False
            ),
            "restoration_owns_household_memory": (
                bool(latest_envelope.get("restoration_owns_household_memory", False))
                if latest_envelope is not None
                else False
            ),
        },
        "safeguard_visibility": {
            "privacy_boundary_preserved": (
                bool(latest_envelope.get("restoration_privacy_boundary_preserved", False))
                if latest_envelope is not None
                else False
            ),
            "guest_safe_boundary_preserved": (
                bool(latest_envelope.get("restoration_guest_safe_boundary_preserved", False))
                if latest_envelope is not None
                else False
            ),
        },
        "deferred_functionality_visibility": {
            "restoration_outcome_implementation": "#330",
            "e3a_preservation_alignment": "#331",
            "restoration_diagnostics_explainability": "#332",
            "occupancy_presence_governance": "#333+#334+#335+#336+#337",
            "release_3_validation": "#338",
        },
        "traceability_visibility": {
            "execution_envelope_ref_count": len(execution_envelope_refs),
            "preservation_alignment_ref_count": len(preservation_alignment_refs),
            "latest_execution_kind": (
                latest_envelope.get("execution_kind")
                if latest_envelope is not None
                else None
            ),
            "latest_restoration_path": (
                latest_envelope.get("experience_restoration_path")
                if latest_envelope is not None
                else None
            ),
            "latest_restoration_outcome_path": (
                latest_envelope.get("experience_restoration_outcome_path")
                if latest_envelope is not None
                else None
            ),
            "latest_preservation_alignment_path": (
                latest_preservation.get("alignment_path")
                if latest_preservation is not None
                else None
            ),
        },
        "diagnostics_non_rights": {
            "creates_authority": False,
            "creates_restoration_outcomes": False,
            "creates_preservation_outcomes": False,
            "modifies_restoration_decision_logic": False,
            "modifies_preservation_alignment_logic": False,
            "executes_restoration_behavior": False,
            "executes_preservation_alignment_behavior": False,
        },
    }


def _preservation_baseline(hass: HomeAssistant, state) -> dict[str, Any]:
    """Return bounded baseline visibility for ADR-013 outcome preservation clusters."""
    area_registry = ar.async_get(hass)
    areas = list(area_registry.async_list_areas())
    floor_ids = sorted({str(area.floor_id) for area in areas if getattr(area, "floor_id", None)})
    enabled_composites = [composite for composite in state.composites.values() if composite.enabled]
    foundation_boundary = _foundation_runtime_boundary(hass, state)
    context_visibility = _context_assembly_visibility(state)
    execution_visibility = _execution_explainability(state)

    return {
        "preservation_governance_source": "adr_013_outcome_preservation",
        "preservation_mode": "household_facing_outcomes",
        "implementation_preservation_required": False,
        "baseline_validation_only": True,
        "foundation_boundary_ready": bool(foundation_boundary.get("room_configs_bound_to_foundation", False)),
        "composite_scope_visibility_available": bool(enabled_composites),
        "floor_scope_visibility_available": bool(floor_ids),
        "global_context_visibility_available": bool(context_visibility.get("active_context_types", [])),
        "execution_hierarchy_visibility_available": execution_visibility.get("orchestration_activity_count", 0) > 0,
        "explainability_surface_available": bool(execution_visibility.get("latest_orchestration") or execution_visibility.get("latest_direct")),
        "current_floor_ids": floor_ids,
        "enabled_composite_count": len(enabled_composites),
        "active_global_context_types": list(context_visibility.get("active_context_types", [])),
        "observed_outcome_clusters": {
            "composite_floor_scope": {
                "composite_scope_visibility_available": bool(enabled_composites),
                "floor_scope_visibility_available": bool(floor_ids),
            },
            "execution_hierarchy": {
                "execution_visibility_available": execution_visibility.get("orchestration_activity_count", 0) > 0,
                "latest_orchestration_route_scope": (
                    None
                    if execution_visibility.get("latest_orchestration") is None
                    else execution_visibility["latest_orchestration"].get("route_scope")
                ),
            },
            "global_context_provider_parity": {
                "active_global_context_types": list(context_visibility.get("active_context_types", [])),
                "room_projection_sample_count": len(context_visibility.get("room_projection_samples", [])),
            },
        },
        "not_yet_implemented_in_baseline": [
            "merged_room_preservation_logic",
            "composite_room_preservation_logic",
            "global_fallback_preservation_logic",
            "vocabulary_consumption",
            "vocabulary_explainability",
        ],
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    state = await ConciergeStorage(hass).async_load_state()
    provider = _provider_from_entry(hass, config_entry)
    readiness = None
    manifest_count = 0
    invalid_manifest_count = 0
    provider_type = "not_configured"
    provider_available = False
    provider_status_summary = "not_configured"
    provider_supported = False
    capture_supported = False
    selection_supported = False
    provider_reason_code = "capability_unknown"
    satellite_capture_supported = False
    satellite_status_code = "provider_not_selected"

    if provider is not None:
        readiness = await hass.async_add_executor_job(provider.validate_ready)
        provider_type = str(readiness.provider_type or "mounted_path")
        provider_available = bool(readiness.ready)
        provider_status_summary = (
            "ready"
            if readiness.ready
            else str(readiness.failure_code or "unavailable")
        )
        if readiness.ready:
            active_sessions = await hass.async_add_executor_job(provider.list_active_sessions)
            manifest_count = 0
            invalid_manifest_count = 0
            for session_id in active_sessions:
                inspection = await hass.async_add_executor_job(lambda session_id=session_id: provider.inspect_session_manifest(session_id))
                if inspection.manifest_present:
                    manifest_count += 1
                if inspection.manifest_present and not inspection.manifest_valid:
                    invalid_manifest_count += 1

    capture_capabilities = await EnrollmentOrchestrator(hass).get_capture_provider_capabilities()
    provider_type = str(capture_capabilities.get("provider_type", provider_type) or provider_type)
    provider_available = bool(capture_capabilities.get("provider_available", provider_available))
    provider_supported = bool(capture_capabilities.get("provider_supported", provider_supported))
    capture_supported = bool(capture_capabilities.get("capture_supported", capture_supported))
    selection_supported = bool(capture_capabilities.get("selection_supported", selection_supported))
    provider_reason_code = str(capture_capabilities.get("reason_code", provider_reason_code) or provider_reason_code)
    satellite_capture_supported = bool(
        capture_capabilities.get("satellite_capture_supported", satellite_capture_supported)
    )
    satellite_status_code = str(capture_capabilities.get("satellite_status_code", satellite_status_code) or satellite_status_code)
    provider_status_summary = str(
        capture_capabilities.get("provider_status_summary", provider_status_summary) or provider_status_summary
    )

    attempt_count, success_count, failure_count = _cleanup_counters(state)
    reconciliation_result = hass.data.get(DOMAIN, {}).get(f"{config_entry.entry_id}_startup_reconciliation")
    telemetry = build_operational_telemetry(
        state=state,
        reconciliation_result=reconciliation_result,
        capture_capabilities=capture_capabilities,
    )

    return {
        "storage_health": {
            "storage_provider_type": provider_type,
            "storage_available": bool(readiness.ready) if readiness is not None else False,
            "storage_reachable": bool(readiness.reachable) if readiness is not None else False,
            "storage_writable": bool(readiness.writable) if readiness is not None else False,
            "storage_policy_compliant": False if readiness is None else not bool(readiness.policy_denied),
            "last_storage_failure_code": None if readiness is None or readiness.ready else readiness.failure_code,
            "last_storage_preflight_state": provider_status_summary,
        },
        "session_health": {
            "active_session_count": _active_session_count(state),
            "total_session_count": len(state.enrollment_sessions),
            "session_state_summary": _count_summary([session.state for session in state.enrollment_sessions.values()]),
            "cleanup_status_summary": _count_summary([session.cleanup_status for session in state.enrollment_sessions.values()]),
        },
        "manifest_health": {
            "manifest_schema_version": VOICE_ENROLLMENT_MANIFEST_SCHEMA_VERSION,
            "manifest_count": manifest_count,
            "invalid_manifest_count": invalid_manifest_count,
        },
        "cleanup_health": {
            "cleanup_attempt_count": attempt_count,
            "cleanup_success_count": success_count,
            "cleanup_failure_count": failure_count,
            "last_cleanup_result_code": _last_cleanup_result_code(state),
        },
        "reconciliation_health": {
            "startup_reconciliation_enabled": True,
            "last_reconciliation_status": _reconciliation_status(reconciliation_result),
            "orphan_count": int(getattr(reconciliation_result, "orphan_count", 0) or 0),
            "cleanup_attempted_count": int(getattr(reconciliation_result, "cleanup_attempted_count", 0) or 0),
            "cleanup_failed_count": int(getattr(reconciliation_result, "cleanup_failed_count", 0) or 0),
        },
        "repairs_health": _repairs_health(hass),
        "provider_availability": {
            "provider_type": provider_type,
            "provider_available": provider_available,
            "provider_supported": provider_supported,
            "provider_status_summary": provider_status_summary,
            "capture_supported": capture_supported,
            "selection_supported": selection_supported,
            "reason_code": provider_reason_code,
            "satellite_capture_supported": satellite_capture_supported,
            "satellite_status_code": satellite_status_code,
        },
        "foundation_runtime_boundary": _foundation_runtime_boundary(hass, state),
        "context_assembly_visibility": _context_assembly_visibility(state),
        "execution_explainability": _execution_explainability(state),
        "vocabulary_diagnostics_visibility": _vocabulary_diagnostics_visibility(state),
        "capability_diagnostics_explainability_visibility": _capability_diagnostics_explainability_visibility(state),
        "experience_diagnostics_explainability_visibility": _experience_diagnostics_explainability_visibility(state),
        "productivity_source_of_record_boundary_visibility": _productivity_source_of_record_boundary_visibility(hass, state),
        "calendar_email_consumption_boundary_visibility": _calendar_email_consumption_boundary_visibility(hass, state),
        "task_shopping_consumption_boundary_visibility": _task_shopping_consumption_boundary_visibility(hass, state),
        "capture_knowledge_consumption_boundary_visibility": _capture_knowledge_consumption_boundary_visibility(hass, state),
        "briefing_composition_boundary_visibility": _briefing_composition_boundary_visibility(hass, state),
        "household_status_synthesis_boundary_visibility": _household_status_synthesis_boundary_visibility(hass, state),
        "household_coordination_boundary_visibility": _household_coordination_boundary_visibility(hass, state),
        "productivity_coordination_boundary_visibility": _productivity_coordination_boundary_visibility(hass, state),
        "provenance_ownership_consumption_boundary_visibility": _provenance_ownership_consumption_boundary_visibility(hass, state),
        "release_6_provenance_diagnostics_explainability_visibility": _release_6_provenance_diagnostics_explainability_visibility(hass, state),
        "release_6_productivity_diagnostics_visibility": _release_6_productivity_diagnostics_visibility(hass, state),
        "voice_identity_linkage_setup_boundary_visibility": await _voice_identity_linkage_setup_boundary_visibility(hass, config_entry),
        "voice_identity_consumption_boundary_visibility": _voice_identity_consumption_boundary_visibility(state),
        "messaging_governance_boundary_visibility": _messaging_governance_boundary_visibility(state),
        "messaging_provenance_visibility": _messaging_provenance_visibility(state),
        "notification_delivery_boundary_visibility": _notification_delivery_boundary_visibility(state),
        "recipient_consent_privacy_visibility_boundary_visibility": _recipient_consent_privacy_visibility_boundary_visibility(state),
        "messaging_diagnostics_explainability_visibility": _messaging_diagnostics_explainability_visibility(state),
        "household_memory_governance_boundary_visibility": _household_memory_governance_boundary_visibility(state),
        "household_memory_ownership_consumption_boundary_visibility": _household_memory_ownership_consumption_boundary_visibility(state),
        "household_memory_identity_privacy_retention_separation_visibility": _household_memory_identity_privacy_retention_separation_visibility(state),
        "household_memory_messaging_continuity_affinity_occupancy_restoration_separation_visibility": _household_memory_messaging_continuity_affinity_occupancy_restoration_separation_visibility(state),
        "household_memory_provenance_diagnostics_explainability_visibility": _household_memory_provenance_diagnostics_explainability_visibility(state),
        "continuity_affinity_diagnostics_explainability_visibility": _continuity_affinity_diagnostics_explainability_visibility(state),
        "occupancy_presence_diagnostics_explainability_visibility": _occupancy_presence_diagnostics_explainability_visibility(state),
        "restoration_diagnostics_explainability_visibility": _restoration_diagnostics_explainability_visibility(state),
        "preservation_baseline": _preservation_baseline(hass, state),
        "enrollment_activity_summary": telemetry["enrollment_activity_summary"],
        "completion_activity_summary": telemetry["completion_activity_summary"],
        "cleanup_activity_summary": telemetry["cleanup_activity_summary"],
        "reconciliation_activity_summary": telemetry["reconciliation_activity_summary"],
        "capture_provider_activity_summary": telemetry["capture_provider_activity_summary"],
        "retention_policy": {
            "retention_mode": "zero_retention_default",
            "cleanup_policy_version": "phase0_cleanup_foundation_v1",
        },
    }
