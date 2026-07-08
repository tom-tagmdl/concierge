"""Architecture protection tests for enrollment manifest lifecycle."""

from __future__ import annotations

import json
from pathlib import Path

from custom_components.concierge.enrollment_session import build_enrollment_session_manifest_payload
from custom_components.concierge.enrollment_session import enrollment_session_for_start
from custom_components.concierge.enrollment_storage import MountedPathEnrollmentStorageProvider


def test_manifest_round_trip_is_projection_only_and_leaves_no_tmp(tmp_path) -> None:
    """Manifest persistence should be atomic and contain only approved fields."""
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
    payload = build_enrollment_session_manifest_payload(session, target_sample_count=3)

    provider.upsert_session_manifest(payload)

    manifest_path = Path(provider.ensure_session_path(session.session_id).session_path) / "session.json"
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert set(raw) == {
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
    assert not manifest_path.with_name("session.json.tmp").exists()
    assert "speaker_embedding_id" not in raw
    assert "sample_items" not in raw


def test_manifest_survives_current_cleanup_behavior(tmp_path) -> None:
    """Current phase cleanup should preserve session.json while removing artifacts."""
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
    provider.write_sample(session.session_id, 0, "audio/wav", b"sample")

    summary = provider.delete_session_artifacts(session.session_id)
    remaining = provider.list_session_artifacts(session.session_id)

    assert summary.skipped_paths >= 1
    assert [artifact.file_name for artifact in remaining] == ["session.json"]
