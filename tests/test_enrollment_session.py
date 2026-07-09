"""Architecture protection tests for enrollment session ownership."""

from __future__ import annotations

from custom_components.concierge.const import VOICE_ENROLLMENT_CLEANUP_STATUS_COMPLETE
from custom_components.concierge.const import VOICE_ENROLLMENT_STATE_CLEANUP_FAILED
from custom_components.concierge.const import VOICE_ENROLLMENT_STATE_SAMPLE_RECEIVED
from custom_components.concierge.enrollment_session import build_enrollment_session_progress_projection
from custom_components.concierge.enrollment_session import build_enrollment_session_manifest_payload
from custom_components.concierge.enrollment_session import enrollment_session_for_start
from custom_components.concierge.enrollment_session import enrollment_session_mark_cleanup_complete
from custom_components.concierge.enrollment_session import enrollment_session_mark_cleanup_pending
from custom_components.concierge.enrollment_session import enrollment_session_mark_cleanup_running
from custom_components.concierge.enrollment_session import enrollment_session_mark_profile_built
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


def test_progress_projection_is_deterministic_and_safe() -> None:
    """Progress projection should be deterministic and exclude sensitive artifacts."""
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
            "speech_text": "private phrase",
            "recording_path": "\\\\nas\\share\\sample.wav",
            "recording_mime_type": "audio/wav",
            "recording_size_bytes": 12345,
        },
        captured_at="2026-07-08T11:01:00+00:00",
    )
    session.metadata["provider_type"] = "browser_microphone"

    progress = build_enrollment_session_progress_projection(session, target_sample_count=3)

    assert progress["sample_count"] == 1
    assert progress["target_sample_count"] == 3
    assert progress["completion_percentage"] == 33
    assert progress["is_complete"] is False
    assert progress["is_active"] is True
    assert progress["is_terminal"] is False
    assert progress["provider_type"] == "browser_microphone"
    assert progress["captured_phrase_indices"] == []
    assert progress["enrollment_state"] == session.state
    assert "recording_path" not in progress
    assert "sample_items" not in progress
    assert "person_ref" not in progress
    assert "provider_device_id" not in progress
    assert "private phrase" not in str(progress)


def test_progress_projection_includes_captured_phrase_indices_without_sensitive_fields() -> None:
    """Progress projection should expose phrase coverage by index while remaining privacy-safe."""
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
            "speech_text": "phrase one",
            "phrase_index": 0,
            "recording_path": "\\\\nas\\private\\sample1.wav",
        },
        captured_at="2026-07-08T11:01:00+00:00",
    )
    session = enrollment_session_record_sample(
        session,
        sample_payload={
            "sample_id": "sample-2",
            "speech_text": "phrase three",
            "phrase_index": 2,
            "recording_path": "\\\\nas\\private\\sample2.wav",
        },
        captured_at="2026-07-08T11:02:00+00:00",
    )
    session = enrollment_session_record_sample(
        session,
        sample_payload={
            "sample_id": "sample-3",
            "speech_text": "phrase three retry",
            "phrase_index": 2,
            "recording_path": "\\\\nas\\private\\sample3.wav",
        },
        captured_at="2026-07-08T11:03:00+00:00",
    )

    progress = build_enrollment_session_progress_projection(session, target_sample_count=8)

    assert progress["captured_phrase_indices"] == [0, 2]
    assert "recording_path" not in progress
    assert "speech_text" not in str(progress)


def test_progress_projection_handles_zero_and_terminal_states() -> None:
    """Progress projection should be safe for zero-sample and terminal states."""
    session = enrollment_session_for_start(
        person_id="person.tom",
        voice_profile_id="tom_voice",
        existing_sample_items=[],
        enrollment_started_at="2026-07-08T11:00:00+00:00",
    )
    zero_progress = build_enrollment_session_progress_projection(session, target_sample_count=3)
    assert zero_progress["sample_count"] == 0
    assert zero_progress["completion_percentage"] == 0
    assert zero_progress["is_complete"] is False

    terminal_session = enrollment_session_mark_cleanup_complete(
        session,
        cleanup_reason="manual",
        cleanup_result_code="complete",
        cleanup_started_at="2026-07-08T11:02:00+00:00",
        cleanup_completed_at="2026-07-08T11:03:00+00:00",
        artifacts_seen_count=0,
        artifacts_deleted_count=0,
        artifacts_missing_count=0,
    )
    terminal_session.state = VOICE_ENROLLMENT_STATE_CLEANUP_FAILED
    terminal_progress = build_enrollment_session_progress_projection(terminal_session, target_sample_count=3)
    assert terminal_progress["is_terminal"] is True
    assert terminal_progress["is_active"] is False


def test_record_sample_allows_second_capture_from_sample_received() -> None:
    """Lifecycle should allow additional captures after one sample is received."""
    session = enrollment_session_for_start(
        person_id="person.tom",
        voice_profile_id="tom_voice",
        existing_sample_items=[],
        enrollment_started_at="2026-07-08T11:00:00+00:00",
    )

    first = enrollment_session_record_sample(
        session,
        sample_payload={"sample_id": "sample-1", "speech_text": "phrase one"},
        captured_at="2026-07-08T11:01:00+00:00",
    )

    second = enrollment_session_record_sample(
        first,
        sample_payload={"sample_id": "sample-2", "speech_text": "phrase two"},
        captured_at="2026-07-08T11:02:00+00:00",
    )

    assert second.state == VOICE_ENROLLMENT_STATE_SAMPLE_RECEIVED
    assert second.sample_count == 2
    assert second.sample_items[-1]["sample_id"] == "sample-2"


def test_mark_profile_built_from_sample_received_uses_valid_transitions() -> None:
    """Completion path should progress from sample_received without invalid capture_pending jump."""
    session = enrollment_session_for_start(
        person_id="person.tom",
        voice_profile_id="tom_voice",
        existing_sample_items=[],
        enrollment_started_at="2026-07-08T11:00:00+00:00",
    )
    session = enrollment_session_record_sample(
        session,
        sample_payload={"sample_id": "sample-1", "speech_text": "phrase one"},
        captured_at="2026-07-08T11:01:00+00:00",
    )

    built = enrollment_session_mark_profile_built(
        session,
        built_at="2026-07-08T11:02:00+00:00",
    )

    assert built.state == "completed_pending_cleanup"
    assert built.last_built_at == "2026-07-08T11:02:00+00:00"
