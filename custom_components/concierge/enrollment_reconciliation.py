"""Startup orphan reconciliation foundation for enrollment session artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any

from .archive_runtime import archive_options_from_entry, resolve_voice_enrollment_root
from .const import (
    VOICE_ENROLLMENT_CLEANUP_REASON_UNKNOWN,
    VOICE_ENROLLMENT_CLEANUP_RESULT_ALREADY_CLEAN,
    VOICE_ENROLLMENT_CLEANUP_RESULT_COMPLETE,
    VOICE_ENROLLMENT_CLEANUP_RESULT_FAILED,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_NOT_CONFIGURED,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_UNKNOWN_FAILURE,
)
from .enrollment_cleanup import EnrollmentCleanupManager, EnrollmentCleanupRequest
from .enrollment_orchestrator import resolve_enrollment_storage_provider_from_entry
from .enrollment_session import (
    build_enrollment_session_manifest_payload,
    enrollment_session_mark_cleanup_complete,
    enrollment_session_mark_cleanup_failed,
    enrollment_session_mark_cleanup_pending,
    enrollment_session_mark_cleanup_running,
    resolve_manifest_target_sample_count,
)
from .enrollment_storage import MountedPathEnrollmentStorageProvider
from .models import EnrollmentSession
from .repairs import (
    async_clear_reconciliation_issue,
    async_clear_storage_issue,
    async_create_or_update_reconciliation_issue,
    async_create_or_update_storage_issue,
)
from .storage import ConciergeStorage

_LOGGER = logging.getLogger(__name__)
_DEFAULT_TARGET_SAMPLE_COUNT = 3

ORPHAN_DIRECTORY_WITHOUT_SESSION = "directory_without_session"
ORPHAN_SESSION_MISSING_MANIFEST = "session_missing_manifest"
ORPHAN_MANIFEST_WITHOUT_SESSION = "manifest_without_session"
ORPHAN_MANIFEST_ONLY_DIRECTORY = "manifest_only_directory"
ORPHAN_ARTIFACTS_WITHOUT_VALID_MANIFEST = "artifacts_without_valid_manifest"
ORPHAN_INVALID_MANIFEST = "invalid_manifest"


@dataclass(slots=True)
class EnrollmentReconciliationResult:
    """Sanitized startup reconciliation summary."""

    scanned_sessions: int
    scanned_manifests: int
    orphan_count: int
    cleanup_attempted_count: int
    cleanup_succeeded_count: int
    cleanup_failed_count: int
    invalid_manifest_count: int
    storage_available: bool
    reconciliation_started_at: str
    reconciliation_completed_at: str


@dataclass(slots=True)
class _SessionScan:
    session_id: str
    has_session_record: bool
    manifest_present: bool
    manifest_valid: bool
    manifest_unreadable: bool
    artifact_count_excluding_manifest: int


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _provider_from_entry(hass, entry) -> MountedPathEnrollmentStorageProvider | None:
    return resolve_enrollment_storage_provider_from_entry(hass, entry)


async def _async_sync_session_manifest(hass, provider: MountedPathEnrollmentStorageProvider, session: EnrollmentSession) -> None:
    existing_manifest = await hass.async_add_executor_job(
        lambda: provider.read_session_manifest(session.session_id)
    )
    effective_target = resolve_manifest_target_sample_count(
        session,
        requested_target_sample_count=None,
        existing_target_sample_count=(
            int(existing_manifest.target_sample_count)
            if existing_manifest is not None
            else None
        ),
        default_target_sample_count=_DEFAULT_TARGET_SAMPLE_COUNT,
    )
    payload = build_enrollment_session_manifest_payload(
        session,
        target_sample_count=effective_target,
    )
    await hass.async_add_executor_job(lambda: provider.upsert_session_manifest(payload))


async def _async_apply_session_update(storage: ConciergeStorage, session: EnrollmentSession) -> EnrollmentSession:
    return await storage.async_update_enrollment_session(
        session_id=session.session_id,
        state_name=session.state,
        sample_count=session.sample_count,
        sample_items=list(session.sample_items),
        enrollment_started_at=session.enrollment_started_at,
        last_sample_at=session.last_sample_at,
        last_built_at=session.last_built_at,
        cleanup_status=session.cleanup_status,
        metadata=dict(session.metadata),
    )


async def _async_cleanup_existing_session(
    hass,
    storage: ConciergeStorage,
    provider: MountedPathEnrollmentStorageProvider,
    session: EnrollmentSession,
    *,
    cleanup_manager: EnrollmentCleanupManager,
) -> tuple[EnrollmentSession, bool]:
    pending = enrollment_session_mark_cleanup_pending(session, cleanup_reason=VOICE_ENROLLMENT_CLEANUP_REASON_UNKNOWN)
    pending = await _async_apply_session_update(storage, pending)
    await _async_sync_session_manifest(hass, provider, pending)

    started_at = _utcnow_iso()
    running = enrollment_session_mark_cleanup_running(
        pending,
        cleanup_reason=VOICE_ENROLLMENT_CLEANUP_REASON_UNKNOWN,
        cleanup_started_at=started_at,
    )
    running = await _async_apply_session_update(storage, running)
    await _async_sync_session_manifest(hass, provider, running)

    cleanup_result = await hass.async_add_executor_job(
        lambda: cleanup_manager.cleanup(
            EnrollmentCleanupRequest(
                session=running,
                cleanup_reason=VOICE_ENROLLMENT_CLEANUP_REASON_UNKNOWN,
            )
        )
    )

    success = cleanup_result.cleanup_result_code in {
        VOICE_ENROLLMENT_CLEANUP_RESULT_COMPLETE,
        VOICE_ENROLLMENT_CLEANUP_RESULT_ALREADY_CLEAN,
    }
    if success:
        finalized = enrollment_session_mark_cleanup_complete(
            running,
            cleanup_reason=cleanup_result.cleanup_reason,
            cleanup_result_code=cleanup_result.cleanup_result_code,
            cleanup_started_at=cleanup_result.cleanup_started_at,
            cleanup_completed_at=cleanup_result.cleanup_completed_at,
            artifacts_seen_count=cleanup_result.artifacts_seen_count,
            artifacts_deleted_count=cleanup_result.artifacts_deleted_count,
            artifacts_missing_count=cleanup_result.artifacts_missing_count,
        )
    else:
        finalized = enrollment_session_mark_cleanup_failed(
            running,
            cleanup_reason=cleanup_result.cleanup_reason,
            cleanup_result_code=cleanup_result.cleanup_result_code or VOICE_ENROLLMENT_CLEANUP_RESULT_FAILED,
            cleanup_started_at=cleanup_result.cleanup_started_at,
            cleanup_completed_at=cleanup_result.cleanup_completed_at,
            artifacts_seen_count=cleanup_result.artifacts_seen_count,
            artifacts_deleted_count=cleanup_result.artifacts_deleted_count,
            artifacts_missing_count=cleanup_result.artifacts_missing_count,
            error_count=len(cleanup_result.errors_redacted_or_sanitized),
        )

    finalized = await _async_apply_session_update(storage, finalized)
    await _async_sync_session_manifest(hass, provider, finalized)
    return finalized, success


def _classify_orphans(scan: _SessionScan) -> set[str]:
    classes: set[str] = set()

    if not scan.has_session_record and scan.manifest_present:
        classes.add(ORPHAN_MANIFEST_WITHOUT_SESSION)
    if not scan.has_session_record and not scan.manifest_present:
        classes.add(ORPHAN_DIRECTORY_WITHOUT_SESSION)
    if scan.has_session_record and not scan.manifest_present:
        classes.add(ORPHAN_SESSION_MISSING_MANIFEST)
    if scan.manifest_present and not scan.manifest_valid:
        classes.add(ORPHAN_INVALID_MANIFEST)
    if scan.artifact_count_excluding_manifest == 0 and scan.manifest_present:
        classes.add(ORPHAN_MANIFEST_ONLY_DIRECTORY)
    if scan.artifact_count_excluding_manifest > 0 and not scan.manifest_valid:
        classes.add(ORPHAN_ARTIFACTS_WITHOUT_VALID_MANIFEST)

    return classes


def _should_attempt_cleanup(classes: set[str]) -> bool:
    return any(
        item in classes
        for item in {
            ORPHAN_DIRECTORY_WITHOUT_SESSION,
            ORPHAN_MANIFEST_WITHOUT_SESSION,
            ORPHAN_ARTIFACTS_WITHOUT_VALID_MANIFEST,
        }
    )


async def async_run_startup_reconciliation(hass, entry) -> EnrollmentReconciliationResult:
    """Run one startup orphan reconciliation pass for voice enrollment artifacts."""
    started_at = _utcnow_iso()
    storage = ConciergeStorage(hass)

    provider = _provider_from_entry(hass, entry)
    if provider is None:
        await async_create_or_update_storage_issue(
            hass,
            failure_code=VOICE_ENROLLMENT_PREFLIGHT_STORAGE_NOT_CONFIGURED,
        )
        completed_at = _utcnow_iso()
        _LOGGER.info(
            "Concierge startup reconciliation skipped: %s",
            VOICE_ENROLLMENT_PREFLIGHT_STORAGE_NOT_CONFIGURED,
        )
        return EnrollmentReconciliationResult(
            scanned_sessions=0,
            scanned_manifests=0,
            orphan_count=0,
            cleanup_attempted_count=0,
            cleanup_succeeded_count=0,
            cleanup_failed_count=0,
            invalid_manifest_count=0,
            storage_available=False,
            reconciliation_started_at=started_at,
            reconciliation_completed_at=completed_at,
        )

    readiness = await hass.async_add_executor_job(provider.validate_ready)
    if not readiness.ready:
        await async_create_or_update_storage_issue(
            hass,
            failure_code=str(readiness.failure_code or VOICE_ENROLLMENT_PREFLIGHT_STORAGE_UNKNOWN_FAILURE),
            provider_type=str(readiness.provider_type or "mounted_path"),
        )
        completed_at = _utcnow_iso()
        _LOGGER.warning(
            "Concierge startup reconciliation skipped: %s",
            str(readiness.failure_code or VOICE_ENROLLMENT_PREFLIGHT_STORAGE_UNKNOWN_FAILURE),
        )
        return EnrollmentReconciliationResult(
            scanned_sessions=0,
            scanned_manifests=0,
            orphan_count=0,
            cleanup_attempted_count=0,
            cleanup_succeeded_count=0,
            cleanup_failed_count=0,
            invalid_manifest_count=0,
            storage_available=False,
            reconciliation_started_at=started_at,
            reconciliation_completed_at=completed_at,
        )

    await async_clear_storage_issue(hass)

    state = await storage.async_load_state()
    session_records = dict(state.enrollment_sessions)

    active_sessions = await hass.async_add_executor_job(provider.list_active_sessions)
    scanned_sessions = len(active_sessions)
    scanned_manifests = 0
    orphan_count = 0
    cleanup_attempted_count = 0
    cleanup_succeeded_count = 0
    cleanup_failed_count = 0
    invalid_manifest_count = 0

    cleanup_manager = EnrollmentCleanupManager(provider)

    for session_id in active_sessions:
        inspection = await hass.async_add_executor_job(lambda: provider.inspect_session_manifest(session_id))
        artifacts = await hass.async_add_executor_job(lambda: provider.list_session_artifacts(session_id))

        if inspection.manifest_present:
            scanned_manifests += 1
        if inspection.manifest_present and not inspection.manifest_valid:
            invalid_manifest_count += 1

        artifact_count_excluding_manifest = len(
            [artifact for artifact in artifacts if artifact.file_name != "session.json"]
        )
        scan = _SessionScan(
            session_id=session_id,
            has_session_record=session_id in session_records,
            manifest_present=inspection.manifest_present,
            manifest_valid=inspection.manifest_valid,
            manifest_unreadable=inspection.unreadable,
            artifact_count_excluding_manifest=artifact_count_excluding_manifest,
        )

        classes = _classify_orphans(scan)
        if classes:
            orphan_count += 1

        if not _should_attempt_cleanup(classes):
            continue

        cleanup_attempted_count += 1
        session = session_records.get(session_id)
        if session is not None:
            _, cleanup_success = await _async_cleanup_existing_session(
                hass,
                storage,
                provider,
                session,
                cleanup_manager=cleanup_manager,
            )
            if cleanup_success:
                cleanup_succeeded_count += 1
            else:
                cleanup_failed_count += 1
            continue

        synthetic_session = EnrollmentSession(
            session_id=session_id,
            person_id="",
            voice_profile_id="",
            state="idle",
            created_at=started_at,
            updated_at=started_at,
        )
        cleanup_result = await hass.async_add_executor_job(
            lambda: cleanup_manager.cleanup(
                EnrollmentCleanupRequest(
                    session=synthetic_session,
                    cleanup_reason=VOICE_ENROLLMENT_CLEANUP_REASON_UNKNOWN,
                )
            )
        )
        if cleanup_result.cleanup_result_code in {
            VOICE_ENROLLMENT_CLEANUP_RESULT_COMPLETE,
            VOICE_ENROLLMENT_CLEANUP_RESULT_ALREADY_CLEAN,
        }:
            cleanup_succeeded_count += 1
        else:
            cleanup_failed_count += 1

    # Also classify persisted sessions that have no active directory/manifest projection.
    for session_id in session_records:
        if session_id in active_sessions:
            continue
        orphan_count += 1

    completed_at = _utcnow_iso()
    if invalid_manifest_count > 0 or cleanup_failed_count > 0:
        await async_create_or_update_reconciliation_issue(
            hass,
            invalid_manifest_count=invalid_manifest_count,
            cleanup_failed_count=cleanup_failed_count,
            orphan_count=orphan_count,
        )
    else:
        await async_clear_reconciliation_issue(hass)

    _LOGGER.info(
        "Concierge startup reconciliation completed: scanned_sessions=%s orphan_count=%s cleanup_attempted=%s",
        scanned_sessions,
        orphan_count,
        cleanup_attempted_count,
    )

    return EnrollmentReconciliationResult(
        scanned_sessions=scanned_sessions,
        scanned_manifests=scanned_manifests,
        orphan_count=orphan_count,
        cleanup_attempted_count=cleanup_attempted_count,
        cleanup_succeeded_count=cleanup_succeeded_count,
        cleanup_failed_count=cleanup_failed_count,
        invalid_manifest_count=invalid_manifest_count,
        storage_available=True,
        reconciliation_started_at=started_at,
        reconciliation_completed_at=completed_at,
    )
