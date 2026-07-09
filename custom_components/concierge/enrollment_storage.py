"""Enrollment storage provider abstraction for voice enrollment artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from typing import Protocol

from .const import (
    VOICE_ENROLLMENT_MANIFEST_SCHEMA_VERSION,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_CONFIG_CONFLICT,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_MISSING,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_NOT_WRITABLE,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_POLICY_DENIED,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_PROBE_FAILED,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_RECORDER_CONFLICT,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_UNAVAILABLE,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_UNKNOWN_FAILURE,
    VOICE_ENROLLMENT_REPAIRS_STORAGE_MISCONFIGURED,
    VOICE_ENROLLMENT_REPAIRS_STORAGE_MISSING,
    VOICE_ENROLLMENT_REPAIRS_STORAGE_NOT_WRITABLE,
    VOICE_ENROLLMENT_REPAIRS_STORAGE_RECORDER_CONFLICT,
    VOICE_ENROLLMENT_REPAIRS_STORAGE_UNAVAILABLE,
)


@dataclass(slots=True)
class StorageReadinessResult:
    """Result payload for provider readiness validation."""

    ready: bool
    root_path: str = "external_enrollment_root"
    failure_code: str | None = None
    failure_message_safe: str = ""
    provider_type: str = "mounted_path"
    policy_denied: bool = False
    writable: bool = False
    reachable: bool = False
    probe_performed: bool = False
    probe_successful: bool = False
    issue_id: str | None = None
    denial_reason: str | None = None
    message: str = ""


@dataclass(slots=True)
class SessionPathResult:
    """Result payload for ensured session storage directory."""

    session_id: str
    session_path: str
    created: bool


@dataclass(slots=True)
class SampleWriteResult:
    """Result payload for one stored enrollment sample."""

    session_id: str
    sample_index: int
    sample_path: str
    content_type: str
    bytes_written: int
    written_at: str


@dataclass(slots=True)
class SessionArtifact:
    """Provider-owned view of one enrollment artifact file."""

    session_id: str
    artifact_path: str
    file_name: str
    bytes_size: int
    modified_at: str


@dataclass(slots=True)
class DeleteSummaryResult:
    """Result payload for deleting session artifacts."""

    session_id: str | None
    deleted_files: int
    deleted_dirs: int
    missing_paths: int
    skipped_paths: int
    errors: list[str]


@dataclass(slots=True)
class SessionManifestRecord:
    """Provider-owned session manifest metadata record."""

    session_id: str
    person_ref: str
    provider_type: str
    provider_device_id: str
    enrollment_state: str
    sample_count: int
    target_sample_count: int
    timestamps: dict[str, str]
    cleanup_status: str
    schema_version: int


@dataclass(slots=True)
class SessionManifestInspection:
    """Provider-owned manifest inspection view for reconciliation."""

    session_id: str
    manifest_present: bool
    manifest_valid: bool
    schema_valid: bool
    unreadable: bool


class EnrollmentStorageProvider(Protocol):
    """Enrollment storage boundary contract for Phase 0 scaffolding."""

    def validate_ready(self) -> StorageReadinessResult:
        """Validate provider readiness before enrollment writes."""

    def ensure_session_path(self, session_id: str) -> SessionPathResult:
        """Ensure bounded storage path for one enrollment session."""

    def write_sample(
        self,
        session_id: str,
        sample_index: int,
        content_type: str,
        data_bytes: bytes,
    ) -> SampleWriteResult:
        """Persist one captured audio sample."""

    def list_session_artifacts(self, session_id: str) -> list[SessionArtifact]:
        """List provider-owned artifacts for one enrollment session."""

    def validate_artifact_path(self, session_id: str, artifact_path: str) -> bool:
        """Validate that one path is provider-owned for a given session."""

    def resolve_recording_path(
        self,
        session_id: str,
        *,
        preferred_path: str | None = None,
        phrase_index: int | None = None,
    ) -> str | None:
        """Resolve an authoritative recording path for one session sample."""

    def delete_recording_artifacts(self, session_id: str, artifact_paths: list[str]) -> DeleteSummaryResult:
        """Delete selected artifacts for one session after ownership validation."""

    def delete_owned_artifacts(self, artifact_paths: list[str]) -> DeleteSummaryResult:
        """Delete provider-owned artifacts from legacy metadata paths."""

    def upsert_session_manifest(self, manifest_payload: dict[str, Any]) -> SessionManifestRecord:
        """Create or update atomic session manifest for one enrollment session."""

    def read_session_manifest(self, session_id: str) -> SessionManifestRecord | None:
        """Read session manifest when present."""

    def inspect_session_manifest(self, session_id: str) -> SessionManifestInspection:
        """Inspect manifest presence and validity for one session directory."""

    def list_active_sessions(self) -> list[str]:
        """List active enrollment session identifiers."""

    def delete_session_artifacts(self, session_id: str) -> DeleteSummaryResult:
        """Delete one session directory and all artifacts beneath it."""


class MountedPathEnrollmentStorageProvider:
    """Mounted attached-storage provider bounded to one external root path."""

    def __init__(self, *, root_path: Path, hass_config_path: Path | None = None) -> None:
        self._root_path = root_path
        self._active_root = self._root_path / "active"
        self._hass_config_path = hass_config_path

    @property
    def root_path(self) -> Path:
        """Return provider root path."""
        return self._root_path

    @staticmethod
    def _safe_session_slug(value: str) -> str:
        normalized = str(value or "").strip().lower().replace(".", "_").replace(" ", "_")
        normalized = "".join(ch for ch in normalized if ch.isalnum() or ch in {"_", "-"})
        return normalized or "unknown"

    @staticmethod
    def _voice_suffix_for_content_type(content_type: str) -> str:
        lowered = str(content_type or "").lower()
        if "ogg" in lowered:
            return ".ogg"
        if "wav" in lowered or "wave" in lowered:
            return ".wav"
        if "mpeg" in lowered or "mp3" in lowered:
            return ".mp3"
        if "webm" in lowered:
            return ".webm"
        return ".bin"

    @staticmethod
    def _utcnow_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _bounded(self, path: Path) -> Path:
        root = self._root_path.resolve(strict=False)
        candidate = path.resolve(strict=False)
        if candidate == root:
            return candidate
        if root not in candidate.parents:
            raise ValueError("path escapes enrollment storage root")
        return candidate

    def _session_dir(self, session_id: str) -> Path:
        slug = self._safe_session_slug(session_id)
        return self._active_root / f"session_{slug}"

    def _manifest_path(self, session_id: str) -> Path:
        return self._session_dir(session_id) / "session.json"

    @staticmethod
    def _manifest_from_payload(payload: dict[str, Any]) -> SessionManifestRecord:
        timestamps_raw = payload.get("timestamps", {})
        timestamps = {
            "created_at": str((timestamps_raw or {}).get("created_at", "")),
            "updated_at": str((timestamps_raw or {}).get("updated_at", "")),
            "enrollment_started_at": str((timestamps_raw or {}).get("enrollment_started_at", "")),
            "last_sample_at": str((timestamps_raw or {}).get("last_sample_at", "")),
            "last_built_at": str((timestamps_raw or {}).get("last_built_at", "")),
        }
        return SessionManifestRecord(
            session_id=str(payload.get("session_id", "") or ""),
            person_ref=str(payload.get("person_ref", "") or ""),
            provider_type=str(payload.get("provider_type", "") or "unknown"),
            provider_device_id=str(payload.get("provider_device_id", "") or "unknown"),
            enrollment_state=str(payload.get("enrollment_state", "") or ""),
            sample_count=int(payload.get("sample_count", 0) or 0),
            target_sample_count=max(1, int(payload.get("target_sample_count", 1) or 1)),
            timestamps=timestamps,
            cleanup_status=str(payload.get("cleanup_status", "") or "not_started"),
            schema_version=int(payload.get("schema_version", VOICE_ENROLLMENT_MANIFEST_SCHEMA_VERSION)),
        )

    @staticmethod
    def _manifest_to_payload(record: SessionManifestRecord) -> dict[str, Any]:
        return {
            "session_id": record.session_id,
            "person_ref": record.person_ref,
            "provider_type": record.provider_type,
            "provider_device_id": record.provider_device_id,
            "enrollment_state": record.enrollment_state,
            "sample_count": int(record.sample_count),
            "target_sample_count": int(record.target_sample_count),
            "timestamps": {
                "created_at": str(record.timestamps.get("created_at", "")),
                "updated_at": str(record.timestamps.get("updated_at", "")),
                "enrollment_started_at": str(record.timestamps.get("enrollment_started_at", "")),
                "last_sample_at": str(record.timestamps.get("last_sample_at", "")),
                "last_built_at": str(record.timestamps.get("last_built_at", "")),
            },
            "cleanup_status": record.cleanup_status,
            "schema_version": int(record.schema_version),
        }

    @staticmethod
    def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
        tmp_path = path.with_name(f"{path.name}.tmp")
        encoded = json.dumps(payload, ensure_ascii=True, indent=2)
        tmp_path.write_text(encoded, encoding="utf-8")
        tmp_path.replace(path)

    @staticmethod
    def _is_sqlite_like_path(normalized: str) -> bool:
        lowered = normalized.lower()
        return lowered.endswith(".db") or lowered.endswith(".db-shm") or lowered.endswith(".db-wal")

    @staticmethod
    def _looks_like_recorder_path(normalized: str) -> bool:
        lowered = normalized.lower()
        markers = (
            "home-assistant_v2.db",
            "homeassistant_v2.db",
            "recorder.db",
            "/recorder/",
            "/database/",
            "/databases/",
            "/sqlite/",
        )
        return any(marker in lowered for marker in markers)

    def _policy_denial(self) -> tuple[str, str, str] | None:
        normalized = str(self._root_path).replace("\\", "/").lower()
        if "/.storage" in normalized:
            return (
                VOICE_ENROLLMENT_REPAIRS_STORAGE_MISCONFIGURED,
                "ha_storage_directory",
                "storage root cannot point at Home Assistant .storage",
            )

        if normalized == "/config" or normalized.startswith("/config/"):
            return (
                VOICE_ENROLLMENT_REPAIRS_STORAGE_MISCONFIGURED,
                "ha_config_directory",
                "storage root cannot point at Home Assistant config directory",
            )

        if self._is_sqlite_like_path(normalized) or self._looks_like_recorder_path(normalized):
            return (
                VOICE_ENROLLMENT_REPAIRS_STORAGE_RECORDER_CONFLICT,
                "recorder_database_location",
                "storage root conflicts with recorder or SQLite database locations",
            )

        if self._hass_config_path is not None:
            cfg = self._hass_config_path.resolve(strict=False)
            try:
                root = self._root_path.resolve(strict=False)
                if root == cfg or cfg in root.parents:
                    return (
                        VOICE_ENROLLMENT_REPAIRS_STORAGE_MISCONFIGURED,
                        "ha_config_directory",
                        "storage root cannot be inside Home Assistant config directory",
                    )
            except OSError:
                return (
                    VOICE_ENROLLMENT_REPAIRS_STORAGE_UNAVAILABLE,
                    "path_resolution_failed",
                    "storage root path could not be resolved",
                )

        return None

    @staticmethod
    def _preflight_failure_from_policy(denial_reason: str) -> str:
        if denial_reason == "recorder_database_location":
            return VOICE_ENROLLMENT_PREFLIGHT_STORAGE_RECORDER_CONFLICT
        if denial_reason == "ha_config_directory":
            return VOICE_ENROLLMENT_PREFLIGHT_STORAGE_CONFIG_CONFLICT
        if denial_reason == "path_resolution_failed":
            return VOICE_ENROLLMENT_PREFLIGHT_STORAGE_UNAVAILABLE
        return VOICE_ENROLLMENT_PREFLIGHT_STORAGE_POLICY_DENIED

    @staticmethod
    def _ready_result(*, writable: bool, reachable: bool, probe_performed: bool, probe_successful: bool) -> StorageReadinessResult:
        return StorageReadinessResult(
            ready=True,
            writable=writable,
            reachable=reachable,
            probe_performed=probe_performed,
            probe_successful=probe_successful,
            failure_message_safe="ready",
            message="ready",
        )

    @staticmethod
    def _failure_result(
        *,
        failure_code: str,
        failure_message_safe: str,
        issue_id: str | None = None,
        denial_reason: str | None = None,
        policy_denied: bool = False,
        writable: bool = False,
        reachable: bool = False,
        probe_performed: bool = False,
        probe_successful: bool = False,
    ) -> StorageReadinessResult:
        return StorageReadinessResult(
            ready=False,
            failure_code=failure_code,
            failure_message_safe=failure_message_safe,
            policy_denied=policy_denied,
            writable=writable,
            reachable=reachable,
            probe_performed=probe_performed,
            probe_successful=probe_successful,
            issue_id=issue_id,
            denial_reason=denial_reason,
            message=failure_message_safe,
        )

    def _is_disallowed_root(self) -> bool:
        return self._policy_denial() is not None

    def _normalize_artifact_path(self, artifact_path: str) -> Path | None:
        raw = str(artifact_path or "").strip()
        if not raw:
            return None
        try:
            candidate = self._bounded(Path(raw))
        except (ValueError, OSError):
            return None
        return candidate

    def _delete_file_and_prune(self, path: Path) -> tuple[int, int, int, int, list[str]]:
        deleted_files = 0
        deleted_dirs = 0
        missing_paths = 0
        skipped_paths = 0
        errors: list[str] = []

        candidate = self._normalize_artifact_path(str(path))
        if candidate is None:
            skipped_paths += 1
            return deleted_files, deleted_dirs, missing_paths, skipped_paths, errors

        if not candidate.exists() or not candidate.is_file():
            missing_paths += 1
            return deleted_files, deleted_dirs, missing_paths, skipped_paths, errors

        try:
            candidate.unlink(missing_ok=True)
            deleted_files += 1
        except OSError as err:
            errors.append(str(err))
            return deleted_files, deleted_dirs, missing_paths, skipped_paths, errors

        parent = candidate.parent
        for _ in range(5):
            try:
                bounded_parent = self._bounded(parent)
            except ValueError:
                break

            if bounded_parent == self._root_path.resolve(strict=False):
                break

            try:
                bounded_parent.rmdir()
                deleted_dirs += 1
                parent = bounded_parent.parent
            except OSError:
                break

        return deleted_files, deleted_dirs, missing_paths, skipped_paths, errors

    def validate_ready(self) -> StorageReadinessResult:
        root = self._root_path
        reachable = False
        writable = False
        probe_performed = False
        probe_successful = False

        denial = self._policy_denial()
        if denial is not None:
            issue_id, denial_reason, message = denial
            return self._failure_result(
                failure_code=self._preflight_failure_from_policy(denial_reason),
                failure_message_safe=message,
                issue_id=issue_id,
                denial_reason=denial_reason,
                policy_denied=True,
            )

        try:
            if not root.exists():
                # Preflight is allowed to safely create the configured root.
                root.mkdir(parents=True, exist_ok=True)
        except OSError:
            return self._failure_result(
                failure_code=VOICE_ENROLLMENT_PREFLIGHT_STORAGE_NOT_WRITABLE,
                failure_message_safe="external enrollment storage is not writable",
                issue_id=VOICE_ENROLLMENT_REPAIRS_STORAGE_NOT_WRITABLE,
            )

        if not root.exists():
            return self._failure_result(
                failure_code=VOICE_ENROLLMENT_PREFLIGHT_STORAGE_MISSING,
                failure_message_safe="external enrollment storage is missing",
                issue_id=VOICE_ENROLLMENT_REPAIRS_STORAGE_MISSING,
            )

        if not root.is_dir():
            return self._failure_result(
                failure_code=VOICE_ENROLLMENT_PREFLIGHT_STORAGE_UNAVAILABLE,
                failure_message_safe="external enrollment storage is unavailable",
                issue_id=VOICE_ENROLLMENT_REPAIRS_STORAGE_UNAVAILABLE,
            )

        reachable = True

        probe_file = self._active_root / ".write_probe"
        probe_session_dir = self._active_root / ".session_probe"
        probe_manifest = probe_session_dir / "session.json"
        try:
            self._active_root.mkdir(parents=True, exist_ok=True)
            writable = True

            probe_performed = True
            probe_file.write_text("ok", encoding="utf-8")
            probe_file.unlink(missing_ok=True)

            # Validate that session directories and session.json can be created/updated.
            probe_session_dir.mkdir(parents=True, exist_ok=True)
            self._atomic_write_json(
                probe_manifest,
                {
                    "session_id": "probe",
                    "person_ref": "probe",
                    "provider_type": "mounted_path",
                    "provider_device_id": "probe",
                    "enrollment_state": "probe",
                    "sample_count": 0,
                    "target_sample_count": 1,
                    "timestamps": {
                        "created_at": self._utcnow_iso(),
                        "updated_at": self._utcnow_iso(),
                        "enrollment_started_at": "",
                        "last_sample_at": "",
                        "last_built_at": "",
                    },
                    "cleanup_status": "not_started",
                    "schema_version": VOICE_ENROLLMENT_MANIFEST_SCHEMA_VERSION,
                },
            )
            self._atomic_write_json(
                probe_manifest,
                {
                    "session_id": "probe",
                    "person_ref": "probe",
                    "provider_type": "mounted_path",
                    "provider_device_id": "probe",
                    "enrollment_state": "probe_updated",
                    "sample_count": 0,
                    "target_sample_count": 1,
                    "timestamps": {
                        "created_at": self._utcnow_iso(),
                        "updated_at": self._utcnow_iso(),
                        "enrollment_started_at": "",
                        "last_sample_at": "",
                        "last_built_at": "",
                    },
                    "cleanup_status": "not_started",
                    "schema_version": VOICE_ENROLLMENT_MANIFEST_SCHEMA_VERSION,
                },
            )
            probe_successful = True

            # Cleanup is best-effort only; successful probe writes already prove readiness.
            try:
                probe_manifest.unlink(missing_ok=True)
            except OSError:
                pass
            try:
                probe_session_dir.rmdir()
            except OSError:
                pass
        except OSError:
            # Best-effort probe cleanup; failure remains fail-closed.
            try:
                probe_manifest.unlink(missing_ok=True)
            except OSError:
                pass
            try:
                probe_file.unlink(missing_ok=True)
            except OSError:
                pass
            try:
                for child in probe_session_dir.glob("*"):
                    if child.is_file():
                        child.unlink(missing_ok=True)
            except OSError:
                pass
            try:
                probe_session_dir.rmdir()
            except OSError:
                pass
            return self._failure_result(
                failure_code=VOICE_ENROLLMENT_PREFLIGHT_STORAGE_PROBE_FAILED,
                failure_message_safe="external enrollment storage readiness probe failed",
                issue_id=VOICE_ENROLLMENT_REPAIRS_STORAGE_NOT_WRITABLE,
                writable=writable,
                reachable=reachable,
                probe_performed=probe_performed,
                probe_successful=False,
            )
        except Exception:
            try:
                probe_manifest.unlink(missing_ok=True)
            except OSError:
                pass
            try:
                probe_file.unlink(missing_ok=True)
            except OSError:
                pass
            try:
                for child in probe_session_dir.glob("*"):
                    if child.is_file():
                        child.unlink(missing_ok=True)
            except OSError:
                pass
            try:
                probe_session_dir.rmdir()
            except OSError:
                pass
            return self._failure_result(
                failure_code=VOICE_ENROLLMENT_PREFLIGHT_STORAGE_UNKNOWN_FAILURE,
                failure_message_safe="external enrollment storage readiness failed",
                issue_id=VOICE_ENROLLMENT_REPAIRS_STORAGE_UNAVAILABLE,
                writable=writable,
                reachable=reachable,
                probe_performed=probe_performed,
                probe_successful=False,
            )

        return self._ready_result(
            writable=writable,
            reachable=reachable,
            probe_performed=probe_performed,
            probe_successful=probe_successful,
        )

    def ensure_session_path(self, session_id: str) -> SessionPathResult:
        session_dir = self._bounded(self._session_dir(session_id))
        created = not session_dir.exists()
        session_dir.mkdir(parents=True, exist_ok=True)
        return SessionPathResult(
            session_id=session_id,
            session_path=str(session_dir),
            created=created,
        )

    def write_sample(
        self,
        session_id: str,
        sample_index: int,
        content_type: str,
        data_bytes: bytes,
    ) -> SampleWriteResult:
        ensured = self.ensure_session_path(session_id)
        session_dir = self._bounded(Path(ensured.session_path))
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        suffix = self._voice_suffix_for_content_type(content_type)
        file_name = f"phrase_{int(sample_index) + 1:02d}_{stamp}{suffix}"
        destination = self._bounded(session_dir / file_name)
        destination.write_bytes(data_bytes)
        return SampleWriteResult(
            session_id=session_id,
            sample_index=int(sample_index),
            sample_path=str(destination).replace("\\", "/"),
            content_type=str(content_type or "application/octet-stream"),
            bytes_written=len(data_bytes),
            written_at=self._utcnow_iso(),
        )

    def list_session_artifacts(self, session_id: str) -> list[SessionArtifact]:
        session_dir = self._bounded(self._session_dir(session_id))
        if not session_dir.exists() or not session_dir.is_dir():
            return []

        artifacts: list[SessionArtifact] = []
        for path in sorted(session_dir.iterdir()):
            if not path.is_file():
                continue
            stat = path.stat()
            artifacts.append(
                SessionArtifact(
                    session_id=session_id,
                    artifact_path=str(path).replace("\\", "/"),
                    file_name=path.name,
                    bytes_size=int(stat.st_size),
                    modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                )
            )
        return artifacts

    def validate_artifact_path(self, session_id: str, artifact_path: str) -> bool:
        candidate = self._normalize_artifact_path(artifact_path)
        if candidate is None:
            return False
        expected_session_dir = self._bounded(self._session_dir(session_id))
        return candidate == expected_session_dir or expected_session_dir in candidate.parents

    def resolve_recording_path(
        self,
        session_id: str,
        *,
        preferred_path: str | None = None,
        phrase_index: int | None = None,
    ) -> str | None:
        if preferred_path and self.validate_artifact_path(session_id, preferred_path):
            candidate = self._normalize_artifact_path(preferred_path)
            if candidate is not None and candidate.exists() and candidate.is_file():
                return str(candidate).replace("\\", "/")

        artifacts = self.list_session_artifacts(session_id)
        if not artifacts:
            return None

        if phrase_index is not None:
            prefix = f"phrase_{int(phrase_index) + 1:02d}_"
            matching = [artifact for artifact in artifacts if artifact.file_name.startswith(prefix)]
            if matching:
                matching.sort(key=lambda item: item.modified_at)
                return matching[-1].artifact_path

        artifacts.sort(key=lambda item: item.modified_at)
        return artifacts[-1].artifact_path

    def delete_recording_artifacts(self, session_id: str, artifact_paths: list[str]) -> DeleteSummaryResult:
        deleted_files = 0
        deleted_dirs = 0
        missing_paths = 0
        skipped_paths = 0
        errors: list[str] = []

        for raw_path in artifact_paths:
            if not self.validate_artifact_path(session_id, raw_path):
                skipped_paths += 1
                continue
            file_deleted, dir_deleted, missing, skipped, item_errors = self._delete_file_and_prune(Path(raw_path))
            deleted_files += file_deleted
            deleted_dirs += dir_deleted
            missing_paths += missing
            skipped_paths += skipped
            errors.extend(item_errors)

        return DeleteSummaryResult(
            session_id=session_id,
            deleted_files=deleted_files,
            deleted_dirs=deleted_dirs,
            missing_paths=missing_paths,
            skipped_paths=skipped_paths,
            errors=errors,
        )

    def delete_owned_artifacts(self, artifact_paths: list[str]) -> DeleteSummaryResult:
        deleted_files = 0
        deleted_dirs = 0
        missing_paths = 0
        skipped_paths = 0
        errors: list[str] = []

        for raw_path in artifact_paths:
            file_deleted, dir_deleted, missing, skipped, item_errors = self._delete_file_and_prune(Path(raw_path))
            deleted_files += file_deleted
            deleted_dirs += dir_deleted
            missing_paths += missing
            skipped_paths += skipped
            errors.extend(item_errors)

        return DeleteSummaryResult(
            session_id=None,
            deleted_files=deleted_files,
            deleted_dirs=deleted_dirs,
            missing_paths=missing_paths,
            skipped_paths=skipped_paths,
            errors=errors,
        )

    def upsert_session_manifest(self, manifest_payload: dict[str, Any]) -> SessionManifestRecord:
        payload = dict(manifest_payload)
        session_id = str(payload.get("session_id", "") or "").strip()
        if not session_id:
            raise ValueError("session_id is required for session manifest")

        manifest = self._manifest_from_payload(payload)
        ensured = self.ensure_session_path(session_id)
        manifest_path = self._bounded(Path(ensured.session_path) / "session.json")
        self._atomic_write_json(manifest_path, self._manifest_to_payload(manifest))
        return manifest

    def read_session_manifest(self, session_id: str) -> SessionManifestRecord | None:
        manifest_path = self._bounded(self._manifest_path(session_id))
        if not manifest_path.exists() or not manifest_path.is_file():
            return None
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return None
        if not isinstance(raw, dict):
            return None
        return self._manifest_from_payload(raw)

    def inspect_session_manifest(self, session_id: str) -> SessionManifestInspection:
        manifest_path = self._bounded(self._manifest_path(session_id))
        if not manifest_path.exists() or not manifest_path.is_file():
            return SessionManifestInspection(
                session_id=session_id,
                manifest_present=False,
                manifest_valid=False,
                schema_valid=False,
                unreadable=False,
            )

        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return SessionManifestInspection(
                session_id=session_id,
                manifest_present=True,
                manifest_valid=False,
                schema_valid=False,
                unreadable=True,
            )

        if not isinstance(raw, dict):
            return SessionManifestInspection(
                session_id=session_id,
                manifest_present=True,
                manifest_valid=False,
                schema_valid=False,
                unreadable=True,
            )

        required_keys = {
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
        if any(key not in raw for key in required_keys):
            return SessionManifestInspection(
                session_id=session_id,
                manifest_present=True,
                manifest_valid=False,
                schema_valid=False,
                unreadable=False,
            )

        schema_valid = int(raw.get("schema_version", 0) or 0) == VOICE_ENROLLMENT_MANIFEST_SCHEMA_VERSION
        return SessionManifestInspection(
            session_id=session_id,
            manifest_present=True,
            manifest_valid=schema_valid,
            schema_valid=schema_valid,
            unreadable=False,
        )

    def list_active_sessions(self) -> list[str]:
        if not self._active_root.exists() or not self._active_root.is_dir():
            return []

        session_ids: list[str] = []
        for entry in self._active_root.iterdir():
            if not entry.is_dir():
                continue
            if not entry.name.startswith("session_"):
                continue
            session_ids.append(entry.name.removeprefix("session_"))
        session_ids.sort()
        return session_ids

    def delete_session_artifacts(self, session_id: str) -> DeleteSummaryResult:
        session_dir = self._bounded(self._session_dir(session_id))
        deleted_files = 0
        deleted_dirs = 0
        missing_paths = 0
        skipped_paths = 0
        errors: list[str] = []

        if not session_dir.exists():
            missing_paths += 1
            return DeleteSummaryResult(
                session_id=session_id,
                deleted_files=deleted_files,
                deleted_dirs=deleted_dirs,
                missing_paths=missing_paths,
                skipped_paths=skipped_paths,
                errors=errors,
            )

        # Delete files first, then directories bottom-up.
        for path in sorted(session_dir.rglob("*"), key=lambda item: len(item.parts), reverse=True):
            try:
                bounded = self._bounded(path)
            except ValueError as err:
                errors.append(str(err))
                continue

            if bounded.name == "session.json":
                skipped_paths += 1
                continue

            try:
                if bounded.is_file():
                    bounded.unlink(missing_ok=True)
                    deleted_files += 1
                elif bounded.is_dir():
                    bounded.rmdir()
                    deleted_dirs += 1
            except OSError as err:
                errors.append(str(err))

        if not self._manifest_path(session_id).exists():
            try:
                session_dir.rmdir()
                deleted_dirs += 1
            except FileNotFoundError:
                missing_paths += 1
            except OSError as err:
                errors.append(str(err))

        return DeleteSummaryResult(
            session_id=session_id,
            deleted_files=deleted_files,
            deleted_dirs=deleted_dirs,
            missing_paths=missing_paths,
            skipped_paths=skipped_paths,
            errors=errors,
        )
