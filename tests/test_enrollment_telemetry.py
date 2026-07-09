"""Architecture protection tests for enrollment operational telemetry projection."""

from __future__ import annotations

from types import SimpleNamespace

from custom_components.concierge.enrollment_telemetry import build_operational_telemetry
from custom_components.concierge.models import EnrollmentSession


def _session(
    *,
    session_id: str,
    state: str,
    sample_count: int,
    capture_provider: str,
    cleanup_reason: str = "",
    cleanup_result_code: str = "",
    capture_provider_status: str = "",
    last_error: str = "",
) -> EnrollmentSession:
    metadata: dict[str, object] = {}
    if cleanup_reason:
        metadata["cleanup_reason"] = cleanup_reason
    if cleanup_result_code:
        metadata["cleanup_result_code"] = cleanup_result_code
    if capture_provider_status:
        metadata["capture_provider_status"] = capture_provider_status

    return EnrollmentSession(
        session_id=session_id,
        person_id="person.redacted",
        voice_profile_id="voice.redacted",
        state=state,
        created_at="2026-07-08T12:00:00+00:00",
        updated_at="2026-07-08T12:00:00+00:00",
        sample_count=sample_count,
        sample_items=[
            {
                "sample_id": "sample-1",
                "speech_text": "private phrase",
                "recording_path": "\\\\nas\\share\\private.wav",
                "recording_mime_type": "audio/wav",
                "recording_size_bytes": 123,
            }
        ]
        if sample_count > 0
        else [],
        capture_provider=capture_provider,
        last_error=last_error,
        metadata=metadata,
    )


def test_operational_telemetry_is_aggregate_and_authoritative() -> None:
    """Telemetry should derive from authoritative enrollment state and remain aggregate-only."""
    state = SimpleNamespace(
        enrollment_sessions={
            "s1": _session(
                session_id="s1",
                state="ready",
                sample_count=1,
                capture_provider="browser_microphone",
            ),
            "s2": _session(
                session_id="s2",
                state="cleanup_complete",
                sample_count=3,
                capture_provider="browser_microphone",
                cleanup_reason="completed",
                cleanup_result_code="complete",
            ),
            "s3": _session(
                session_id="s3",
                state="cleanup_failed",
                sample_count=2,
                capture_provider="satellite",
                cleanup_reason="failed",
                cleanup_result_code="failed",
                capture_provider_status="no_capture_api",
                last_error="capture_provider_unsupported",
            ),
        }
    )
    reconciliation = SimpleNamespace(
        orphan_count=2,
        cleanup_succeeded_count=1,
        cleanup_failed_count=1,
    )
    capture_capabilities = {
        "provider_type": "browser_microphone",
        "provider_supported": True,
        "provider_available": True,
    }

    telemetry = build_operational_telemetry(
        state=state,
        reconciliation_result=reconciliation,
        capture_capabilities=capture_capabilities,
    )

    assert telemetry["enrollment_activity_summary"]["active_enrollments"] == 1
    assert telemetry["enrollment_activity_summary"]["completed_enrollments"] == 1
    assert telemetry["enrollment_activity_summary"]["failed_enrollments"] >= 1
    assert telemetry["completion_activity_summary"]["completion_attempts"] == 1
    assert telemetry["completion_activity_summary"]["successful_completions"] == 1
    assert telemetry["cleanup_activity_summary"]["cleanup_executions"] == 2
    assert telemetry["cleanup_activity_summary"]["cleanup_failures"] == 1
    assert telemetry["reconciliation_activity_summary"]["orphan_sessions_detected"] == 2
    assert telemetry["capture_provider_activity_summary"]["browser_provider_usage"] == 2
    assert telemetry["capture_provider_activity_summary"]["satellite_provider_selection_attempts"] == 1
    assert telemetry["capture_provider_activity_summary"]["unsupported_provider_selections"] >= 1
    assert telemetry["capture_provider_activity_summary"]["captured_sample_count"] == 6


def test_operational_telemetry_excludes_sensitive_fields() -> None:
    """Telemetry payload should not expose raw artifacts or person-sensitive data."""
    state = SimpleNamespace(
        enrollment_sessions={
            "s1": _session(
                session_id="s1",
                state="ready",
                sample_count=1,
                capture_provider="browser_microphone",
            )
        }
    )

    telemetry = build_operational_telemetry(
        state=state,
        reconciliation_result=None,
        capture_capabilities={
            "provider_type": "browser_microphone",
            "provider_supported": True,
            "provider_available": True,
        },
    )

    serialized = str(telemetry)
    for forbidden in {
        "recording_path",
        "recording_mime_type",
        "recording_size_bytes",
        "speech_text",
        "private phrase",
        "person.redacted",
        "voice.redacted",
        "sample_items",
        "embeddings",
        "profile_vectors",
    }:
        assert forbidden not in serialized
