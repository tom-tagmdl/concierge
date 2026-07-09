"""Diagnostics support for Concierge."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN
from .const import VOICE_ENROLLMENT_CLEANUP_RESULT_ALREADY_CLEAN
from .const import VOICE_ENROLLMENT_CLEANUP_RESULT_COMPLETE
from .const import VOICE_ENROLLMENT_MANIFEST_SCHEMA_VERSION
from .enrollment_orchestrator import EnrollmentOrchestrator
from .enrollment_orchestrator import resolve_enrollment_storage_provider_from_entry
from .enrollment_storage import MountedPathEnrollmentStorageProvider
from .enrollment_telemetry import build_operational_telemetry
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
