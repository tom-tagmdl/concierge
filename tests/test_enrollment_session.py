"""Architecture protection tests for enrollment session ownership."""

from __future__ import annotations

from custom_components.concierge.const import VOICE_ENROLLMENT_CLEANUP_STATUS_COMPLETE
from custom_components.concierge.const import VOICE_ENROLLMENT_STATE_SAMPLE_RECEIVED
from custom_components.concierge.enrollment_session import build_enrollment_session_manifest_payload
from custom_components.concierge.enrollment_session import enrollment_session_for_start
from custom_components.concierge.enrollment_session import enrollment_session_mark_cleanup_complete
from custom_components.concierge.enrollment_session import enrollment_session_mark_cleanup_pending
from custom_components.concierge.enrollment_session import enrollment_session_mark_cleanup_running
from custom_components.concierge.enrollment_session import enrollment_session_record_sample
from custom_components.concierge.enrollment_session import resolve_manifest_target_sample_count


def test_manifest_payload_is_allowlisted_projection_only() -> None:
    """Manifest payload should contain only approved projection fields."""
    session = enrollment_session_for_start(
        person_id="person.tom",
        voice_profile_id="tom_voice",
        existing_sample_items=[],
        enrollment_started_at="2026-07-08T11:00:00+00:00",
    )
    session = enrollment_session_record_sample(
        session,
        sample_payload={
            "sample_id": "sample-1",
            "speech_text": "private utterance",
            "recording_path": "/media/private.wav",
        },
        captured_at="2026-07-08T11:01:00+00:00",
    )

    payload = build_enrollment_session_manifest_payload(session, target_sample_count=3)

    assert session.state == VOICE_ENROLLMENT_STATE_SAMPLE_RECEIVED
    assert set(payload) == {
        "session_id",
        "person_ref",
        "provider_type",
        "provider_device_id",
        "enrollment_state",
        "sample_count",
        "target_sample_count",
        "timestamps",
        "cleanup_status",
        "schema_version",
    }
    assert "sample_items" not in payload
    assert "speech_text" not in str(payload)
    assert "recording_path" not in str(payload)


def test_cleanup_status_helpers_update_status_without_changing_lifecycle_state() -> None:
    """Cleanup helpers should update cleanup state while preserving lifecycle ownership."""
    session = enrollment_session_for_start(
        person_id="person.tom",
        voice_profile_id="tom_voice",
        existing_sample_items=[],
        enrollment_started_at="2026-07-08T11:00:00+00:00",
    )
    lifecycle_state = session.state

    pending = enrollment_session_mark_cleanup_pending(session, cleanup_reason="manual")
    running = enrollment_session_mark_cleanup_running(
        pending,
        cleanup_reason="manual",
        cleanup_started_at="2026-07-08T11:02:00+00:00",
    )
    complete = enrollment_session_mark_cleanup_complete(
        running,
        cleanup_reason="manual",
        cleanup_result_code="complete",
        cleanup_started_at="2026-07-08T11:02:00+00:00",
        cleanup_completed_at="2026-07-08T11:03:00+00:00",
        artifacts_seen_count=2,
        artifacts_deleted_count=2,
        artifacts_missing_count=0,
    )

    assert pending.state == lifecycle_state
    assert running.state == lifecycle_state
    assert complete.state == lifecycle_state
    assert complete.cleanup_status == VOICE_ENROLLMENT_CLEANUP_STATUS_COMPLETE
    assert complete.metadata["cleanup_reason"] == "manual"
    assert complete.metadata["cleanup_result_code"] == "complete"


def test_target_sample_count_resolution_prefers_request_then_session_then_existing() -> None:
    """Manifest target count should remain session-owned and deterministic."""
    session = enrollment_session_for_start(
        person_id="person.tom",
        voice_profile_id="tom_voice",
        existing_sample_items=[],
        enrollment_started_at="2026-07-08T11:00:00+00:00",
    )
    session.metadata["target_sample_count"] = 5

    assert resolve_manifest_target_sample_count(
        session,
        requested_target_sample_count=4,
        existing_target_sample_count=2,
        default_target_sample_count=3,
    ) == 4
    assert resolve_manifest_target_sample_count(
        session,
        requested_target_sample_count=None,
        existing_target_sample_count=2,
        default_target_sample_count=3,
    ) == 5
    session.metadata.pop("target_sample_count")
    assert resolve_manifest_target_sample_count(
        session,
        requested_target_sample_count=None,
        existing_target_sample_count=2,
        default_target_sample_count=3,
    ) == 2
