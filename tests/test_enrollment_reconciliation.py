"""Architecture protection tests for startup reconciliation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.concierge.const import DOMAIN
from custom_components.concierge.enrollment_reconciliation import async_run_startup_reconciliation
from custom_components.concierge.enrollment_session import enrollment_session_for_start
from custom_components.concierge.enrollment_storage import MountedPathEnrollmentStorageProvider
from custom_components.concierge.enrollment_storage import StorageReadinessResult
from custom_components.concierge.storage import ConciergeStorage


async def test_reconciliation_storage_unavailable_is_fail_safe(hass: HomeAssistant, monkeypatch) -> None:
    """Startup reconciliation should stop safely when storage is unavailable."""
    entry = MockConfigEntry(domain=DOMAIN, title="Concierge")

    class UnavailableProvider:
        def validate_ready(self):
            return StorageReadinessResult(
                ready=False,
                failure_code="storage_unavailable",
                failure_message_safe="external enrollment storage is unavailable",
                provider_type="mounted_path",
            )

    monkeypatch.setattr(
        "custom_components.concierge.enrollment_reconciliation._provider_from_entry",
        lambda hass, entry: UnavailableProvider(),
    )
    monkeypatch.setattr(
        "custom_components.concierge.enrollment_reconciliation.async_create_or_update_storage_issue",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "custom_components.concierge.enrollment_reconciliation.async_clear_storage_issue",
        AsyncMock(),
    )

    result = await async_run_startup_reconciliation(hass, entry)

    assert result.storage_available is False
    assert result.cleanup_attempted_count == 0
    assert result.cleanup_failed_count == 0


async def test_reconciliation_identifies_invalid_manifest_and_uses_cleanup_manager(
    hass: HomeAssistant,
    tmp_path,
    monkeypatch,
) -> None:
    """Reconciliation should classify invalid manifests and clean through the provider path."""
    entry = MockConfigEntry(domain=DOMAIN, title="Concierge")
    provider = MountedPathEnrollmentStorageProvider(
        root_path=tmp_path / "voice_root",
        hass_config_path=tmp_path / "config",
    )
    ensured = provider.ensure_session_path("session_orphan")
    session_dir = Path(ensured.session_path)
    (session_dir / "session.json").write_text('{"broken": true}', encoding="utf-8")
    provider.write_sample("session_orphan", 0, "audio/wav", b"artifact")

    monkeypatch.setattr(
        "custom_components.concierge.enrollment_reconciliation._provider_from_entry",
        lambda hass, entry: provider,
    )
    monkeypatch.setattr(
        "custom_components.concierge.enrollment_reconciliation.async_create_or_update_storage_issue",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "custom_components.concierge.enrollment_reconciliation.async_clear_storage_issue",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "custom_components.concierge.enrollment_reconciliation.async_create_or_update_reconciliation_issue",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "custom_components.concierge.enrollment_reconciliation.async_clear_reconciliation_issue",
        AsyncMock(),
    )

    result = await async_run_startup_reconciliation(hass, entry)

    assert result.scanned_sessions == 1
    assert result.invalid_manifest_count == 1
    assert result.orphan_count >= 1
    assert result.cleanup_attempted_count == 1
    assert result.cleanup_succeeded_count == 1
    remaining = provider.list_session_artifacts("session_orphan")
    assert [artifact.file_name for artifact in remaining] == ["session.json"]


async def test_reconciliation_counts_persisted_sessions_missing_manifest(
    hass: HomeAssistant,
    tmp_path,
    monkeypatch,
) -> None:
    """Persisted EnrollmentSession state without active storage projection should count as orphaned."""
    entry = MockConfigEntry(domain=DOMAIN, title="Concierge")
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
    await ConciergeStorage(hass).async_upsert_enrollment_session(session)

    monkeypatch.setattr(
        "custom_components.concierge.enrollment_reconciliation._provider_from_entry",
        lambda hass, entry: provider,
    )
    monkeypatch.setattr(
        "custom_components.concierge.enrollment_reconciliation.async_create_or_update_storage_issue",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "custom_components.concierge.enrollment_reconciliation.async_clear_storage_issue",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "custom_components.concierge.enrollment_reconciliation.async_create_or_update_reconciliation_issue",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "custom_components.concierge.enrollment_reconciliation.async_clear_reconciliation_issue",
        AsyncMock(),
    )

    result = await async_run_startup_reconciliation(hass, entry)

    assert result.orphan_count == 1
    assert result.cleanup_attempted_count == 0
