"""Enrollment cleanup manager foundation for provider-owned artifact cleanup."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .const import (
    VOICE_ENROLLMENT_CLEANUP_REASON_UNKNOWN,
    VOICE_ENROLLMENT_CLEANUP_REASONS,
    VOICE_ENROLLMENT_CLEANUP_RESULT_ALREADY_CLEAN,
    VOICE_ENROLLMENT_CLEANUP_RESULT_COMPLETE,
    VOICE_ENROLLMENT_CLEANUP_RESULT_FAILED,
    VOICE_ENROLLMENT_CLEANUP_RESULT_PARTIAL,
)
from .models import EnrollmentSession
from .enrollment_storage import EnrollmentStorageProvider


@dataclass(slots=True)
class EnrollmentCleanupRequest:
    """Cleanup request scoped to one enrollment session."""

    session: EnrollmentSession
    cleanup_reason: str = VOICE_ENROLLMENT_CLEANUP_REASON_UNKNOWN


@dataclass(slots=True)
class EnrollmentCleanupResult:
    """Sanitized cleanup execution result for one enrollment session."""

    session_id: str
    cleanup_reason: str
    cleanup_result_code: str
    artifacts_seen_count: int
    artifacts_deleted_count: int
    artifacts_missing_count: int
    errors_redacted_or_sanitized: list[str]
    cleanup_started_at: str
    cleanup_completed_at: str


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EnrollmentCleanupManager:
    """Execute idempotent provider-owned artifact cleanup for one enrollment session."""

    def __init__(self, provider: EnrollmentStorageProvider) -> None:
        self._provider = provider

    @staticmethod
    def _normalize_reason(reason: str) -> str:
        value = str(reason or "").strip().lower()
        if value in VOICE_ENROLLMENT_CLEANUP_REASONS:
            return value
        return VOICE_ENROLLMENT_CLEANUP_REASON_UNKNOWN

    @staticmethod
    def _sanitize_errors(raw_errors: list[str]) -> list[str]:
        if not raw_errors:
            return []
        # Only expose non-sensitive error categories.
        return ["provider_cleanup_error" for _ in raw_errors]

    def cleanup(self, request: EnrollmentCleanupRequest) -> EnrollmentCleanupResult:
        started_at = _utcnow_iso()
        session_id = request.session.session_id
        reason = self._normalize_reason(request.cleanup_reason)

        artifacts = self._provider.list_session_artifacts(session_id)
        artifacts_seen_count = len(artifacts)

        delete_summary = self._provider.delete_session_artifacts(session_id)
        artifacts_deleted_count = int(delete_summary.deleted_files)

        missing_from_observed = max(0, artifacts_seen_count - artifacts_deleted_count)
        artifacts_missing_count = int(delete_summary.missing_paths) + missing_from_observed

        sanitized_errors = self._sanitize_errors(list(delete_summary.errors))

        if sanitized_errors:
            if artifacts_deleted_count > 0:
                result_code = VOICE_ENROLLMENT_CLEANUP_RESULT_PARTIAL
            else:
                result_code = VOICE_ENROLLMENT_CLEANUP_RESULT_FAILED
        else:
            if artifacts_seen_count == 0 and artifacts_deleted_count == 0:
                result_code = VOICE_ENROLLMENT_CLEANUP_RESULT_ALREADY_CLEAN
            else:
                result_code = VOICE_ENROLLMENT_CLEANUP_RESULT_COMPLETE

        completed_at = _utcnow_iso()
        return EnrollmentCleanupResult(
            session_id=session_id,
            cleanup_reason=reason,
            cleanup_result_code=result_code,
            artifacts_seen_count=artifacts_seen_count,
            artifacts_deleted_count=artifacts_deleted_count,
            artifacts_missing_count=artifacts_missing_count,
            errors_redacted_or_sanitized=sanitized_errors,
            cleanup_started_at=started_at,
            cleanup_completed_at=completed_at,
        )
