"""Enrollment session helpers for Phase 0 lifecycle scaffolding."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .const import (
    VOICE_ENROLLMENT_CLEANUP_STATUS_COMPLETE,
    VOICE_ENROLLMENT_CLEANUP_STATUS_FAILED,
    VOICE_ENROLLMENT_CLEANUP_STATUS_PENDING,
    VOICE_ENROLLMENT_CLEANUP_STATUS_RUNNING,
    VOICE_ENROLLMENT_MANIFEST_SCHEMA_VERSION,
    VOICE_ENROLLMENT_STATE_CAPTURE_PENDING,
    VOICE_ENROLLMENT_STATE_CAPTURING,
    VOICE_ENROLLMENT_STATE_CANCELLED_PENDING_CLEANUP,
    VOICE_ENROLLMENT_STATE_CLEANUP_COMPLETE,
    VOICE_ENROLLMENT_STATE_CLEANUP_FAILED,
    VOICE_ENROLLMENT_STATE_CLEANUP_RUNNING,
    VOICE_ENROLLMENT_STATE_COMPLETED_PENDING_CLEANUP,
    VOICE_ENROLLMENT_STATE_FAILED_PENDING_CLEANUP,
    VOICE_ENROLLMENT_STATE_IDLE,
    VOICE_ENROLLMENT_STATE_PREFLIGHT_FAILED,
    VOICE_ENROLLMENT_STATE_PREFLIGHT_VALIDATING,
    VOICE_ENROLLMENT_STATE_PROCESSING,
    VOICE_ENROLLMENT_STATE_PROFILE_BUILDING,
    VOICE_ENROLLMENT_STATE_READY,
    VOICE_ENROLLMENT_STATE_SAMPLE_RECEIVED,
    VOICE_ENROLLMENT_STATE_SESSION_CREATED,
    VOICE_ENROLLMENT_STATE_TIMEOUT_PENDING_CLEANUP,
)
from .models import EnrollmentSession


def _utcnow_iso() -> str:
    """Return timezone-aware UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def new_enrollment_session_id() -> str:
    """Build a sortable unique enrollment session identifier."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return f"session_{stamp}_{uuid4().hex[:8]}"


def new_enrollment_session(*, person_id: str, voice_profile_id: str) -> EnrollmentSession:
    """Create a new enrollment session in session_created state."""
    now_iso = _utcnow_iso()
    return EnrollmentSession(
        session_id=new_enrollment_session_id(),
        person_id=person_id,
        voice_profile_id=voice_profile_id,
        state=VOICE_ENROLLMENT_STATE_SESSION_CREATED,
        created_at=now_iso,
        updated_at=now_iso,
        enrollment_started_at=now_iso,
    )


_ALLOWED_STATE_TRANSITIONS: dict[str, tuple[str, ...]] = {
    VOICE_ENROLLMENT_STATE_IDLE: (VOICE_ENROLLMENT_STATE_PREFLIGHT_VALIDATING,),
    VOICE_ENROLLMENT_STATE_PREFLIGHT_VALIDATING: (
        VOICE_ENROLLMENT_STATE_PREFLIGHT_FAILED,
        VOICE_ENROLLMENT_STATE_SESSION_CREATED,
    ),
    VOICE_ENROLLMENT_STATE_SESSION_CREATED: (VOICE_ENROLLMENT_STATE_READY,),
    VOICE_ENROLLMENT_STATE_READY: (
        VOICE_ENROLLMENT_STATE_CAPTURE_PENDING,
        VOICE_ENROLLMENT_STATE_TIMEOUT_PENDING_CLEANUP,
    ),
    VOICE_ENROLLMENT_STATE_CAPTURE_PENDING: (
        VOICE_ENROLLMENT_STATE_CAPTURING,
        VOICE_ENROLLMENT_STATE_TIMEOUT_PENDING_CLEANUP,
    ),
    VOICE_ENROLLMENT_STATE_CAPTURING: (
        VOICE_ENROLLMENT_STATE_SAMPLE_RECEIVED,
        VOICE_ENROLLMENT_STATE_CANCELLED_PENDING_CLEANUP,
        VOICE_ENROLLMENT_STATE_FAILED_PENDING_CLEANUP,
        VOICE_ENROLLMENT_STATE_TIMEOUT_PENDING_CLEANUP,
    ),
    VOICE_ENROLLMENT_STATE_SAMPLE_RECEIVED: (
        VOICE_ENROLLMENT_STATE_PROCESSING,
        VOICE_ENROLLMENT_STATE_CAPTURING,
        VOICE_ENROLLMENT_STATE_CANCELLED_PENDING_CLEANUP,
        VOICE_ENROLLMENT_STATE_FAILED_PENDING_CLEANUP,
        VOICE_ENROLLMENT_STATE_TIMEOUT_PENDING_CLEANUP,
    ),
    VOICE_ENROLLMENT_STATE_PROCESSING: (
        VOICE_ENROLLMENT_STATE_PROFILE_BUILDING,
        VOICE_ENROLLMENT_STATE_CAPTURING,
        VOICE_ENROLLMENT_STATE_CANCELLED_PENDING_CLEANUP,
        VOICE_ENROLLMENT_STATE_FAILED_PENDING_CLEANUP,
        VOICE_ENROLLMENT_STATE_TIMEOUT_PENDING_CLEANUP,
    ),
    VOICE_ENROLLMENT_STATE_PROFILE_BUILDING: (
        VOICE_ENROLLMENT_STATE_COMPLETED_PENDING_CLEANUP,
        VOICE_ENROLLMENT_STATE_CANCELLED_PENDING_CLEANUP,
        VOICE_ENROLLMENT_STATE_FAILED_PENDING_CLEANUP,
        VOICE_ENROLLMENT_STATE_TIMEOUT_PENDING_CLEANUP,
    ),
    VOICE_ENROLLMENT_STATE_COMPLETED_PENDING_CLEANUP: (VOICE_ENROLLMENT_STATE_CLEANUP_RUNNING,),
    VOICE_ENROLLMENT_STATE_CANCELLED_PENDING_CLEANUP: (VOICE_ENROLLMENT_STATE_CLEANUP_RUNNING,),
    VOICE_ENROLLMENT_STATE_FAILED_PENDING_CLEANUP: (VOICE_ENROLLMENT_STATE_CLEANUP_RUNNING,),
    VOICE_ENROLLMENT_STATE_TIMEOUT_PENDING_CLEANUP: (VOICE_ENROLLMENT_STATE_CLEANUP_RUNNING,),
    VOICE_ENROLLMENT_STATE_CLEANUP_RUNNING: (
        VOICE_ENROLLMENT_STATE_CLEANUP_COMPLETE,
        VOICE_ENROLLMENT_STATE_CLEANUP_FAILED,
    ),
    VOICE_ENROLLMENT_STATE_CLEANUP_COMPLETE: (VOICE_ENROLLMENT_STATE_IDLE,),
    VOICE_ENROLLMENT_STATE_CLEANUP_FAILED: (),
    VOICE_ENROLLMENT_STATE_PREFLIGHT_FAILED: (),
}


def can_transition_enrollment_session(*, from_state: str, to_state: str) -> bool:
    """Return whether a requested session state transition is allowed."""
    return to_state in _ALLOWED_STATE_TRANSITIONS.get(from_state, ())


def transition_enrollment_session(
    session: EnrollmentSession,
    *,
    to_state: str,
    last_error: str = "",
) -> EnrollmentSession:
    """Return a transitioned copy of a session if the move is allowed."""
    if not can_transition_enrollment_session(from_state=session.state, to_state=to_state):
        raise ValueError(f"invalid enrollment session transition: {session.state} -> {to_state}")

    return EnrollmentSession(
        session_id=session.session_id,
        person_id=session.person_id,
        voice_profile_id=session.voice_profile_id,
        state=to_state,
        created_at=session.created_at,
        updated_at=_utcnow_iso(),
        sample_count=session.sample_count,
        sample_items=list(session.sample_items),
        enrollment_started_at=session.enrollment_started_at,
        last_sample_at=session.last_sample_at,
        last_built_at=session.last_built_at,
        cleanup_status=session.cleanup_status,
        capture_provider=session.capture_provider,
        last_error=last_error,
        metadata=dict(session.metadata),
    )


def enrollment_session_for_start(
    *,
    person_id: str,
    voice_profile_id: str,
    existing_sample_items: list[dict],
    enrollment_started_at: str,
) -> EnrollmentSession:
    """Create a start-session snapshot and transition it into ready."""
    session = new_enrollment_session(person_id=person_id, voice_profile_id=voice_profile_id)
    session = EnrollmentSession(
        session_id=session.session_id,
        person_id=session.person_id,
        voice_profile_id=session.voice_profile_id,
        state=session.state,
        created_at=session.created_at,
        updated_at=session.updated_at,
        sample_count=len(existing_sample_items),
        sample_items=list(existing_sample_items),
        enrollment_started_at=enrollment_started_at or session.enrollment_started_at,
        last_sample_at="",
        last_built_at="",
        cleanup_status=session.cleanup_status,
        capture_provider=session.capture_provider,
        last_error=session.last_error,
        metadata=dict(session.metadata),
    )
    return transition_enrollment_session(session, to_state=VOICE_ENROLLMENT_STATE_READY)


def enrollment_session_record_sample(
    session: EnrollmentSession,
    *,
    sample_payload: dict[str, object],
    captured_at: str,
) -> EnrollmentSession:
    """Append one sample and advance lifecycle through capture/sample states."""
    current = session
    if current.state in {VOICE_ENROLLMENT_STATE_READY, VOICE_ENROLLMENT_STATE_SAMPLE_RECEIVED}:
        current = transition_enrollment_session(current, to_state=VOICE_ENROLLMENT_STATE_CAPTURE_PENDING)
    if current.state == VOICE_ENROLLMENT_STATE_CAPTURE_PENDING:
        current = transition_enrollment_session(current, to_state=VOICE_ENROLLMENT_STATE_CAPTURING)

    next_items = [*list(current.sample_items), dict(sample_payload)]
    current = EnrollmentSession(
        session_id=current.session_id,
        person_id=current.person_id,
        voice_profile_id=current.voice_profile_id,
        state=current.state,
        created_at=current.created_at,
        updated_at=_utcnow_iso(),
        sample_count=len(next_items),
        sample_items=next_items,
        enrollment_started_at=current.enrollment_started_at,
        last_sample_at=captured_at,
        last_built_at=current.last_built_at,
        cleanup_status=current.cleanup_status,
        capture_provider=current.capture_provider,
        last_error="",
        metadata=dict(current.metadata),
    )
    return transition_enrollment_session(current, to_state=VOICE_ENROLLMENT_STATE_SAMPLE_RECEIVED)


def enrollment_session_remove_sample(
    session: EnrollmentSession,
    *,
    sample_id: str,
    now_iso: str,
) -> tuple[EnrollmentSession, list[dict[str, object]]]:
    """Remove one sample from session and return removed payloads."""
    removed_items = [
        dict(item)
        for item in list(session.sample_items)
        if str(item.get("sample_id", "")) == sample_id
    ]
    next_items = [
        dict(item)
        for item in list(session.sample_items)
        if str(item.get("sample_id", "")) != sample_id
    ]
    updated = EnrollmentSession(
        session_id=session.session_id,
        person_id=session.person_id,
        voice_profile_id=session.voice_profile_id,
        state=session.state,
        created_at=session.created_at,
        updated_at=_utcnow_iso(),
        sample_count=len(next_items),
        sample_items=next_items,
        enrollment_started_at=session.enrollment_started_at,
        last_sample_at=now_iso if next_items else "",
        last_built_at=session.last_built_at if next_items else "",
        cleanup_status=session.cleanup_status,
        capture_provider=session.capture_provider,
        last_error=session.last_error,
        metadata=dict(session.metadata),
    )
    return updated, removed_items


def enrollment_session_mark_profile_built(session: EnrollmentSession, *, built_at: str) -> EnrollmentSession:
    """Move session through profile_building to completed_pending_cleanup."""
    current = session
    if current.state in {VOICE_ENROLLMENT_STATE_READY, VOICE_ENROLLMENT_STATE_SAMPLE_RECEIVED}:
        current = transition_enrollment_session(current, to_state=VOICE_ENROLLMENT_STATE_CAPTURE_PENDING)
        current = transition_enrollment_session(current, to_state=VOICE_ENROLLMENT_STATE_CAPTURING)
        current = transition_enrollment_session(current, to_state=VOICE_ENROLLMENT_STATE_SAMPLE_RECEIVED)

    current = transition_enrollment_session(current, to_state=VOICE_ENROLLMENT_STATE_PROCESSING)
    current = transition_enrollment_session(current, to_state=VOICE_ENROLLMENT_STATE_PROFILE_BUILDING)
    current = EnrollmentSession(
        session_id=current.session_id,
        person_id=current.person_id,
        voice_profile_id=current.voice_profile_id,
        state=current.state,
        created_at=current.created_at,
        updated_at=_utcnow_iso(),
        sample_count=current.sample_count,
        sample_items=list(current.sample_items),
        enrollment_started_at=current.enrollment_started_at,
        last_sample_at=current.last_sample_at,
        last_built_at=built_at,
        cleanup_status=current.cleanup_status,
        capture_provider=current.capture_provider,
        last_error="",
        metadata=dict(current.metadata),
    )
    return transition_enrollment_session(current, to_state=VOICE_ENROLLMENT_STATE_COMPLETED_PENDING_CLEANUP)


def enrollment_session_reset(session: EnrollmentSession) -> EnrollmentSession:
    """Reset mutable session enrollment sample state without cleanup semantics."""
    return EnrollmentSession(
        session_id=session.session_id,
        person_id=session.person_id,
        voice_profile_id=session.voice_profile_id,
        state=VOICE_ENROLLMENT_STATE_IDLE,
        created_at=session.created_at,
        updated_at=_utcnow_iso(),
        sample_count=0,
        sample_items=[],
        enrollment_started_at=session.enrollment_started_at,
        last_sample_at="",
        last_built_at="",
        cleanup_status=session.cleanup_status,
        capture_provider=session.capture_provider,
        last_error="",
        metadata=dict(session.metadata),
    )


def legacy_voice_profile_enrollment_state(session: EnrollmentSession) -> str:
    """Map authoritative session state to legacy VoiceProfile enrollment_state values."""
    if session.state == VOICE_ENROLLMENT_STATE_IDLE:
        return "untrained"

    if session.state in {
        VOICE_ENROLLMENT_STATE_PROFILE_BUILDING,
        VOICE_ENROLLMENT_STATE_COMPLETED_PENDING_CLEANUP,
    }:
        return "trained"

    if session.sample_count > 0:
        return "capturing"

    return "enrollment_in_progress"


def build_enrollment_session_manifest_payload(
    session: EnrollmentSession,
    *,
    target_sample_count: int,
) -> dict[str, Any]:
    """Build schema-safe manifest payload from authoritative EnrollmentSession state."""
    provider_type, provider_device_id = manifest_provider_identity_from_session(session)
    return {
        "session_id": session.session_id,
        "person_ref": session.person_id,
        "provider_type": provider_type,
        "provider_device_id": provider_device_id,
        "enrollment_state": session.state,
        "sample_count": int(session.sample_count),
        "target_sample_count": max(1, int(target_sample_count)),
        "timestamps": {
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "enrollment_started_at": session.enrollment_started_at,
            "last_sample_at": session.last_sample_at,
            "last_built_at": session.last_built_at,
        },
        "cleanup_status": session.cleanup_status,
        "schema_version": VOICE_ENROLLMENT_MANIFEST_SCHEMA_VERSION,
    }


def manifest_provider_identity_from_session(session: EnrollmentSession) -> tuple[str, str]:
    """Resolve stable manifest provider fields from authoritative session state."""
    provider_type = str(session.metadata.get("provider_type", "") or "").strip()
    provider_device_id = str(session.metadata.get("provider_device_id", "") or "").strip()
    capture_provider = str(session.capture_provider or "").strip()

    if not provider_type:
        provider_type = capture_provider or "browser_microphone"
    if not provider_device_id:
        provider_device_id = capture_provider or "browser_microphone"

    return provider_type, provider_device_id


def resolve_manifest_target_sample_count(
    session: EnrollmentSession,
    *,
    requested_target_sample_count: int | None,
    existing_target_sample_count: int | None,
    default_target_sample_count: int,
) -> int:
    """Resolve target sample count for manifest projection from session ownership context."""
    metadata_target = session.metadata.get("target_sample_count")
    try:
        session_target = int(metadata_target) if metadata_target is not None else None
    except (TypeError, ValueError):
        session_target = None

    if requested_target_sample_count is not None:
        return max(1, int(requested_target_sample_count))
    if session_target is not None:
        return max(1, int(session_target))
    if existing_target_sample_count is not None:
        return max(1, int(existing_target_sample_count))
    return max(1, int(default_target_sample_count))


def _with_cleanup_status(
    session: EnrollmentSession,
    *,
    cleanup_status: str,
    cleanup_reason: str,
    cleanup_result_code: str | None = None,
    cleanup_started_at: str | None = None,
    cleanup_completed_at: str | None = None,
    artifacts_seen_count: int | None = None,
    artifacts_deleted_count: int | None = None,
    artifacts_missing_count: int | None = None,
    error_count: int | None = None,
) -> EnrollmentSession:
    """Return EnrollmentSession with cleanup metadata/status updates."""
    metadata = dict(session.metadata)
    metadata["cleanup_reason"] = str(cleanup_reason or "unknown")
    if cleanup_result_code is not None:
        metadata["cleanup_result_code"] = str(cleanup_result_code)
    if cleanup_started_at is not None:
        metadata["cleanup_started_at"] = str(cleanup_started_at)
    if cleanup_completed_at is not None:
        metadata["cleanup_completed_at"] = str(cleanup_completed_at)
    if artifacts_seen_count is not None:
        metadata["artifacts_seen_count"] = int(artifacts_seen_count)
    if artifacts_deleted_count is not None:
        metadata["artifacts_deleted_count"] = int(artifacts_deleted_count)
    if artifacts_missing_count is not None:
        metadata["artifacts_missing_count"] = int(artifacts_missing_count)
    if error_count is not None:
        metadata["cleanup_error_count"] = int(error_count)

    return EnrollmentSession(
        session_id=session.session_id,
        person_id=session.person_id,
        voice_profile_id=session.voice_profile_id,
        state=session.state,
        created_at=session.created_at,
        updated_at=_utcnow_iso(),
        sample_count=session.sample_count,
        sample_items=list(session.sample_items),
        enrollment_started_at=session.enrollment_started_at,
        last_sample_at=session.last_sample_at,
        last_built_at=session.last_built_at,
        cleanup_status=cleanup_status,
        capture_provider=session.capture_provider,
        last_error=session.last_error,
        metadata=metadata,
    )


def enrollment_session_mark_cleanup_pending(session: EnrollmentSession, *, cleanup_reason: str) -> EnrollmentSession:
    """Mark session cleanup status as pending."""
    return _with_cleanup_status(
        session,
        cleanup_status=VOICE_ENROLLMENT_CLEANUP_STATUS_PENDING,
        cleanup_reason=cleanup_reason,
    )


def enrollment_session_mark_cleanup_running(
    session: EnrollmentSession,
    *,
    cleanup_reason: str,
    cleanup_started_at: str,
) -> EnrollmentSession:
    """Mark session cleanup status as running."""
    return _with_cleanup_status(
        session,
        cleanup_status=VOICE_ENROLLMENT_CLEANUP_STATUS_RUNNING,
        cleanup_reason=cleanup_reason,
        cleanup_started_at=cleanup_started_at,
    )


def enrollment_session_mark_cleanup_complete(
    session: EnrollmentSession,
    *,
    cleanup_reason: str,
    cleanup_result_code: str,
    cleanup_started_at: str,
    cleanup_completed_at: str,
    artifacts_seen_count: int,
    artifacts_deleted_count: int,
    artifacts_missing_count: int,
) -> EnrollmentSession:
    """Mark session cleanup status as complete with summary metadata."""
    return _with_cleanup_status(
        session,
        cleanup_status=VOICE_ENROLLMENT_CLEANUP_STATUS_COMPLETE,
        cleanup_reason=cleanup_reason,
        cleanup_result_code=cleanup_result_code,
        cleanup_started_at=cleanup_started_at,
        cleanup_completed_at=cleanup_completed_at,
        artifacts_seen_count=artifacts_seen_count,
        artifacts_deleted_count=artifacts_deleted_count,
        artifacts_missing_count=artifacts_missing_count,
        error_count=0,
    )


def enrollment_session_mark_cleanup_failed(
    session: EnrollmentSession,
    *,
    cleanup_reason: str,
    cleanup_result_code: str,
    cleanup_started_at: str,
    cleanup_completed_at: str,
    artifacts_seen_count: int,
    artifacts_deleted_count: int,
    artifacts_missing_count: int,
    error_count: int,
) -> EnrollmentSession:
    """Mark session cleanup status as failed with sanitized summary metadata."""
    return _with_cleanup_status(
        session,
        cleanup_status=VOICE_ENROLLMENT_CLEANUP_STATUS_FAILED,
        cleanup_reason=cleanup_reason,
        cleanup_result_code=cleanup_result_code,
        cleanup_started_at=cleanup_started_at,
        cleanup_completed_at=cleanup_completed_at,
        artifacts_seen_count=artifacts_seen_count,
        artifacts_deleted_count=artifacts_deleted_count,
        artifacts_missing_count=artifacts_missing_count,
        error_count=error_count,
    )
