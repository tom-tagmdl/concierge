"""Architecture protection tests for enrollment storage provider boundaries."""

from __future__ import annotations

from pathlib import Path

from custom_components.concierge.const import VOICE_ENROLLMENT_PREFLIGHT_STORAGE_CONFIG_CONFLICT
from custom_components.concierge.const import VOICE_ENROLLMENT_PREFLIGHT_STORAGE_RECORDER_CONFLICT
from custom_components.concierge.enrollment_storage import MountedPathEnrollmentStorageProvider


def test_validate_ready_denies_config_and_recorder_locations(tmp_path) -> None:
    """Provider should deny config and recorder-like roots."""
    config_provider = MountedPathEnrollmentStorageProvider(
        root_path=tmp_path,
        hass_config_path=tmp_path,
    )
    config_result = config_provider.validate_ready()
    assert config_result.ready is False
    assert config_result.failure_code == VOICE_ENROLLMENT_PREFLIGHT_STORAGE_CONFIG_CONFLICT
    assert config_result.policy_denied is True

    recorder_provider = MountedPathEnrollmentStorageProvider(
        root_path=Path("/home-assistant_v2.db"),
        hass_config_path=tmp_path / "config",
    )
    recorder_result = recorder_provider.validate_ready()
    assert recorder_result.ready is False
    assert recorder_result.failure_code == VOICE_ENROLLMENT_PREFLIGHT_STORAGE_RECORDER_CONFLICT


def test_validate_ready_cleans_probe_artifacts_on_success(tmp_path) -> None:
    """Readiness probe should leave no probe artifacts behind."""
    provider = MountedPathEnrollmentStorageProvider(
        root_path=tmp_path / "voice_root",
        hass_config_path=tmp_path / "config",
    )

    result = provider.validate_ready()

    assert result.ready is True
    assert result.probe_performed is True
    assert result.probe_successful is True
    assert not (provider.root_path / "active" / ".write_probe").exists()
    assert not (provider.root_path / "active" / ".session_probe").exists()


def test_manifest_inspection_detects_invalid_manifest(tmp_path) -> None:
    """Manifest inspection should classify incomplete session.json as invalid."""
    provider = MountedPathEnrollmentStorageProvider(
        root_path=tmp_path / "voice_root",
        hass_config_path=tmp_path / "config",
    )
    ensured = provider.ensure_session_path("session_test")
    manifest_path = Path(ensured.session_path) / "session.json"
    manifest_path.write_text('{"session_id": "session_test"}', encoding="utf-8")

    inspection = provider.inspect_session_manifest("session_test")

    assert inspection.manifest_present is True
    assert inspection.manifest_valid is False
    assert inspection.schema_valid is False
    assert inspection.unreadable is False
