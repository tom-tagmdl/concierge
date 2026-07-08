"""Architecture protection tests for enrollment cleanup manager."""

from __future__ import annotations

from custom_components.concierge.enrollment_cleanup import EnrollmentCleanupManager
from custom_components.concierge.enrollment_cleanup import EnrollmentCleanupRequest
from custom_components.concierge.enrollment_session import build_enrollment_session_manifest_payload
from custom_components.concierge.enrollment_session import enrollment_session_for_start
from custom_components.concierge.enrollment_storage import MountedPathEnrollmentStorageProvider


def test_cleanup_is_idempotent_and_preserves_manifest(tmp_path) -> None:
    """Repeated cleanup should converge safely and keep session.json for this phase."""
    provider = MountedPathEnrollmentStorageProvider(
        root_path=tmp_path / "voice_root",
        hass_config_path=tmp_path / "config",
    )
    session = enrollment_session_for_start(
        person_id="person.tom",
        voice_profile_id="tom_voice",
        existing_sample_items=[],
        enrollment_started_at="2026-07-08T11:00:00+00:00",
    )
    provider.upsert_session_manifest(build_enrollment_session_manifest_payload(session, target_sample_count=3))
    provider.write_sample(session.session_id, 0, "audio/wav", b"sample-one")
    provider.write_sample(session.session_id, 1, "audio/wav", b"sample-two")

    manager = EnrollmentCleanupManager(provider)
    first = manager.cleanup(EnrollmentCleanupRequest(session=session, cleanup_reason="manual"))
    second = manager.cleanup(EnrollmentCleanupRequest(session=session, cleanup_reason="manual"))

    assert first.cleanup_result_code == "complete"
    assert first.artifacts_deleted_count >= 2
    assert second.cleanup_result_code == "already_clean"
    assert [artifact.file_name for artifact in provider.list_session_artifacts(session.session_id)] == ["session.json"]


def test_cleanup_manager_uses_provider_api_only() -> None:
    """Cleanup manager should call provider list/delete APIs and nothing else."""

    class FakeProvider:
        def __init__(self) -> None:
            self.list_calls = 0
            self.delete_calls = 0

        def list_session_artifacts(self, session_id: str):
            self.list_calls += 1
            return []

        def delete_session_artifacts(self, session_id: str):
            self.delete_calls += 1
            return type(
                "DeleteSummary",
                (),
                {
                    "deleted_files": 0,
                    "deleted_dirs": 0,
                    "missing_paths": 0,
                    "skipped_paths": 0,
                    "errors": [],
                },
            )()

    provider = FakeProvider()
    session = enrollment_session_for_start(
        person_id="person.tom",
        voice_profile_id="tom_voice",
        existing_sample_items=[],
        enrollment_started_at="2026-07-08T11:00:00+00:00",
    )

    result = EnrollmentCleanupManager(provider).cleanup(EnrollmentCleanupRequest(session=session))

    assert provider.list_calls == 1
    assert provider.delete_calls == 1
    assert result.cleanup_result_code == "already_clean"
