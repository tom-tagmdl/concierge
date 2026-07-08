"""Architecture protection tests for repairs mapping and idempotence."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.concierge.const import VOICE_ENROLLMENT_PREFLIGHT_STORAGE_PROBE_FAILED
from custom_components.concierge.const import VOICE_ENROLLMENT_REPAIRS_INVALID_MANIFEST
from custom_components.concierge.const import VOICE_ENROLLMENT_REPAIRS_ORPHAN_CLEANUP_FAILED
from custom_components.concierge.const import VOICE_ENROLLMENT_REPAIRS_STORAGE_PROBE_FAILED
from custom_components.concierge.repairs import async_clear_storage_issue
from custom_components.concierge.repairs import async_create_or_update_reconciliation_issue
from custom_components.concierge.repairs import async_create_or_update_storage_issue


async def test_storage_failure_maps_to_stable_issue_id(hass: HomeAssistant, monkeypatch) -> None:
    """Storage failure codes should map to stable sanitized repair issue ids."""
    created: list[tuple[str, dict[str, str]]] = []

    def _fake_create_issue(hass, domain, issue_id, **kwargs):
        created.append((issue_id, dict(kwargs["translation_placeholders"])))

    monkeypatch.setattr("custom_components.concierge.repairs.ir.async_create_issue", _fake_create_issue)

    issue_id = await async_create_or_update_storage_issue(
        hass,
        failure_code=VOICE_ENROLLMENT_PREFLIGHT_STORAGE_PROBE_FAILED,
        provider_type="mounted_path",
    )

    assert issue_id == VOICE_ENROLLMENT_REPAIRS_STORAGE_PROBE_FAILED
    assert created[0][0] == VOICE_ENROLLMENT_REPAIRS_STORAGE_PROBE_FAILED
    assert created[0][1]["failure_code"] == VOICE_ENROLLMENT_PREFLIGHT_STORAGE_PROBE_FAILED
    assert "path" not in " ".join(created[0][1].keys())


async def test_repairs_clear_is_safe_when_issue_missing(hass: HomeAssistant, monkeypatch) -> None:
    """Clearing repairs should be safe when the issue does not exist."""

    def _fake_delete_issue(hass, domain, issue_id):
        raise RuntimeError("missing issue")

    monkeypatch.setattr("custom_components.concierge.repairs.ir.async_delete_issue", _fake_delete_issue)

    await async_clear_storage_issue(hass, VOICE_ENROLLMENT_REPAIRS_STORAGE_PROBE_FAILED)


async def test_reconciliation_issue_creation_is_stable(hass: HomeAssistant, monkeypatch) -> None:
    """Reconciliation issues should use stable issue ids for invalid manifests and cleanup failures."""
    created: list[str] = []

    def _fake_create_issue(hass, domain, issue_id, **kwargs):
        created.append(issue_id)

    monkeypatch.setattr("custom_components.concierge.repairs.ir.async_create_issue", _fake_create_issue)

    issue_ids = await async_create_or_update_reconciliation_issue(
        hass,
        invalid_manifest_count=2,
        cleanup_failed_count=1,
        orphan_count=3,
    )

    assert set(issue_ids) == {
        VOICE_ENROLLMENT_REPAIRS_INVALID_MANIFEST,
        VOICE_ENROLLMENT_REPAIRS_ORPHAN_CLEANUP_FAILED,
    }
    assert set(created) == set(issue_ids)