"""Operational telemetry projection for enrollment diagnostics."""

from __future__ import annotations

from typing import Any

from .const import VOICE_ENROLLMENT_CLEANUP_RESULT_ALREADY_CLEAN
from .const import VOICE_ENROLLMENT_CLEANUP_RESULT_COMPLETE
from .const import VOICE_ENROLLMENT_CLEANUP_RESULT_FAILED
from .const import VOICE_ENROLLMENT_CLEANUP_RESULT_PARTIAL
from .const import VOICE_ENROLLMENT_CLEANUP_REASON_CANCELLED
from .const import VOICE_ENROLLMENT_CLEANUP_REASON_COMPLETED
from .const import VOICE_ENROLLMENT_CLEANUP_REASON_FAILED
from .const import VOICE_ENROLLMENT_STATE_CAPTURING
from .const import VOICE_ENROLLMENT_STATE_CAPTURE_PENDING
from .const import VOICE_ENROLLMENT_STATE_PREFLIGHT_FAILED
from .const import VOICE_ENROLLMENT_STATE_PREFLIGHT_VALIDATING
from .const import VOICE_ENROLLMENT_STATE_PROCESSING
from .const import VOICE_ENROLLMENT_STATE_PROFILE_BUILDING
from .const import VOICE_ENROLLMENT_STATE_READY
from .const import VOICE_ENROLLMENT_STATE_SAMPLE_RECEIVED
from .const import VOICE_ENROLLMENT_STATE_SESSION_CREATED


_ACTIVE_STATES = {
    VOICE_ENROLLMENT_STATE_PREFLIGHT_VALIDATING,
    VOICE_ENROLLMENT_STATE_SESSION_CREATED,
    VOICE_ENROLLMENT_STATE_READY,
    VOICE_ENROLLMENT_STATE_CAPTURE_PENDING,
    VOICE_ENROLLMENT_STATE_CAPTURING,
    VOICE_ENROLLMENT_STATE_SAMPLE_RECEIVED,
    VOICE_ENROLLMENT_STATE_PROCESSING,
    VOICE_ENROLLMENT_STATE_PROFILE_BUILDING,
}

_CLEANUP_SUCCESS_RESULTS = {
    VOICE_ENROLLMENT_CLEANUP_RESULT_COMPLETE,
    VOICE_ENROLLMENT_CLEANUP_RESULT_ALREADY_CLEAN,
}

_CLEANUP_FAILURE_RESULTS = {
    VOICE_ENROLLMENT_CLEANUP_RESULT_FAILED,
    VOICE_ENROLLMENT_CLEANUP_RESULT_PARTIAL,
}

_UNSUPPORTED_CAPTURE_STATUSES = {
    "unsupported",
    "future_provider",
    "not_configured",
    "no_capture_api",
    "capability_unknown",
}


def _cleanup_reason(session) -> str:
    return str(session.metadata.get("cleanup_reason", "") or "").strip().lower()


def _cleanup_result(session) -> str:
    return str(session.metadata.get("cleanup_result_code", "") or "").strip().lower()


def _capture_status(session) -> str:
    return str(session.metadata.get("capture_provider_status", "") or "").strip().lower()


def _is_upload_failure(session) -> bool:
    last_error = str(session.last_error or "").lower()
    if "capture_provider_" in last_error or "upload" in last_error:
        return True
    status = _capture_status(session)
    return status in {"unavailable", "unsupported", "no_capture_api"}


def build_operational_telemetry(
    *,
    state,
    reconciliation_result: Any,
    capture_capabilities: dict[str, Any],
) -> dict[str, dict[str, int | str | bool]]:
    """Build aggregate privacy-safe operational telemetry from authoritative state."""
    sessions = list(state.enrollment_sessions.values())

    completion_attempts = 0
    successful_completions = 0
    failed_completions = 0
    cancelled_enrollments = 0
    failed_enrollments = 0
    recovered_enrollments = 0
    cleanup_executions = 0
    cleanup_successes = 0
    cleanup_failures = 0
    browser_provider_usage = 0
    satellite_provider_selection_attempts = 0
    unsupported_provider_selections = 0
    preflight_failures = 0
    upload_failures = 0
    captured_sample_count = 0

    for session in sessions:
        state_name = str(session.state or "").strip().lower()
        provider_type = str(session.capture_provider or "").strip().lower()
        reason = _cleanup_reason(session)
        result = _cleanup_result(session)
        capture_status = _capture_status(session)

        captured_sample_count += max(0, int(session.sample_count))

        if state_name == VOICE_ENROLLMENT_STATE_PREFLIGHT_FAILED:
            preflight_failures += 1

        if _is_upload_failure(session):
            upload_failures += 1

        if provider_type == "browser_microphone":
            browser_provider_usage += 1
        elif provider_type == "satellite":
            satellite_provider_selection_attempts += 1

        if capture_status in _UNSUPPORTED_CAPTURE_STATUSES:
            unsupported_provider_selections += 1

        if reason == VOICE_ENROLLMENT_CLEANUP_REASON_COMPLETED:
            completion_attempts += 1
            if result in _CLEANUP_SUCCESS_RESULTS:
                successful_completions += 1
            if result in _CLEANUP_FAILURE_RESULTS:
                failed_completions += 1

        if reason == VOICE_ENROLLMENT_CLEANUP_REASON_CANCELLED:
            cancelled_enrollments += 1

        if reason == VOICE_ENROLLMENT_CLEANUP_REASON_FAILED or state_name.endswith("failed"):
            failed_enrollments += 1

        recovery_state = str(session.metadata.get("recovery_state", "") or "").strip().lower()
        if recovery_state in {"resumed", "resume_available", "recovered"}:
            recovered_enrollments += 1

        if result:
            cleanup_executions += 1
            if result in _CLEANUP_SUCCESS_RESULTS:
                cleanup_successes += 1
            elif result in _CLEANUP_FAILURE_RESULTS:
                cleanup_failures += 1

    orphan_sessions_detected = int(getattr(reconciliation_result, "orphan_count", 0) or 0)
    orphan_sessions_repaired = max(
        0,
        int(getattr(reconciliation_result, "cleanup_succeeded_count", 0) or 0),
    )
    reconciliation_failures = int(getattr(reconciliation_result, "cleanup_failed_count", 0) or 0)

    active_enrollments = sum(
        1 for session in sessions if str(session.state or "").strip().lower() in _ACTIVE_STATES
    )

    provider_type = str(capture_capabilities.get("provider_type", "unknown") or "unknown")
    provider_supported = bool(capture_capabilities.get("provider_supported", False))
    provider_available = bool(capture_capabilities.get("provider_available", False))

    return {
        "enrollment_activity_summary": {
            "active_enrollments": int(active_enrollments),
            "completed_enrollments": int(successful_completions),
            "cancelled_enrollments": int(cancelled_enrollments),
            "recovered_enrollments": int(recovered_enrollments),
            "failed_enrollments": int(failed_enrollments),
        },
        "completion_activity_summary": {
            "completion_attempts": int(completion_attempts),
            "successful_completions": int(successful_completions),
            "failed_completions": int(failed_completions),
        },
        "cleanup_activity_summary": {
            "cleanup_executions": int(cleanup_executions),
            "cleanup_successes": int(cleanup_successes),
            "cleanup_failures": int(cleanup_failures),
        },
        "reconciliation_activity_summary": {
            "orphan_sessions_detected": int(orphan_sessions_detected),
            "orphan_sessions_repaired": int(orphan_sessions_repaired),
            "reconciliation_failures": int(reconciliation_failures),
        },
        "capture_provider_activity_summary": {
            "browser_provider_usage": int(browser_provider_usage),
            "satellite_provider_selection_attempts": int(satellite_provider_selection_attempts),
            "unsupported_provider_selections": int(unsupported_provider_selections),
            "captured_sample_count": int(captured_sample_count),
            "upload_failures": int(upload_failures),
            "preflight_failures": int(preflight_failures),
            "provider_type": provider_type,
            "provider_supported": provider_supported,
            "provider_available": provider_available,
        },
    }
