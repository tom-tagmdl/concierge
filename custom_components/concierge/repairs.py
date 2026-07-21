"""Home Assistant Repairs integration for Concierge voice enrollment."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.helpers import issue_registry as ir

from .const import (
    DOMAIN,
    PERSON_CONTEXT_REPAIRS_PARTIAL,
    PERSON_CONTEXT_REPAIRS_UNRESOLVED,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_CONFIG_CONFLICT,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_MISSING,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_NOT_CONFIGURED,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_NOT_WRITABLE,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_POLICY_DENIED,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_PROBE_FAILED,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_RECORDER_CONFLICT,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_UNAVAILABLE,
    VOICE_ENROLLMENT_REPAIRS_CAPTURE_PROVIDER_UNAVAILABLE,
    VOICE_ENROLLMENT_REPAIRS_CAPTURE_PROVIDER_UNSUPPORTED,
    VOICE_ENROLLMENT_REPAIRS_CLEANUP_FAILED,
    VOICE_ENROLLMENT_REPAIRS_INVALID_MANIFEST,
    VOICE_ENROLLMENT_REPAIRS_ORPHAN_CLEANUP_FAILED,
    VOICE_ENROLLMENT_REPAIRS_STORAGE_MISCONFIGURED,
    VOICE_ENROLLMENT_REPAIRS_STORAGE_MISSING,
    VOICE_ENROLLMENT_REPAIRS_STORAGE_NOT_WRITABLE,
    VOICE_ENROLLMENT_REPAIRS_STORAGE_PROBE_FAILED,
    VOICE_ENROLLMENT_REPAIRS_STORAGE_RECORDER_CONFLICT,
    VOICE_ENROLLMENT_REPAIRS_STORAGE_UNAVAILABLE,
)


_STORAGE_ISSUE_IDS = {
    VOICE_ENROLLMENT_REPAIRS_STORAGE_MISSING,
    VOICE_ENROLLMENT_REPAIRS_STORAGE_UNAVAILABLE,
    VOICE_ENROLLMENT_REPAIRS_STORAGE_NOT_WRITABLE,
    VOICE_ENROLLMENT_REPAIRS_STORAGE_MISCONFIGURED,
    VOICE_ENROLLMENT_REPAIRS_STORAGE_RECORDER_CONFLICT,
    VOICE_ENROLLMENT_REPAIRS_STORAGE_PROBE_FAILED,
    VOICE_ENROLLMENT_REPAIRS_CAPTURE_PROVIDER_UNAVAILABLE,
    VOICE_ENROLLMENT_REPAIRS_CAPTURE_PROVIDER_UNSUPPORTED,
}

_RECONCILIATION_ISSUE_IDS = {
    VOICE_ENROLLMENT_REPAIRS_INVALID_MANIFEST,
    VOICE_ENROLLMENT_REPAIRS_ORPHAN_CLEANUP_FAILED,
}

_PERSON_CONTEXT_ISSUE_IDS = {
    PERSON_CONTEXT_REPAIRS_UNRESOLVED,
    PERSON_CONTEXT_REPAIRS_PARTIAL,
}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _storage_issue_for_failure_code(failure_code: str) -> str:
    mapping = {
        VOICE_ENROLLMENT_PREFLIGHT_STORAGE_NOT_CONFIGURED: VOICE_ENROLLMENT_REPAIRS_STORAGE_MISSING,
        VOICE_ENROLLMENT_PREFLIGHT_STORAGE_MISSING: VOICE_ENROLLMENT_REPAIRS_STORAGE_MISSING,
        VOICE_ENROLLMENT_PREFLIGHT_STORAGE_UNAVAILABLE: VOICE_ENROLLMENT_REPAIRS_STORAGE_UNAVAILABLE,
        VOICE_ENROLLMENT_PREFLIGHT_STORAGE_NOT_WRITABLE: VOICE_ENROLLMENT_REPAIRS_STORAGE_NOT_WRITABLE,
        VOICE_ENROLLMENT_PREFLIGHT_STORAGE_POLICY_DENIED: VOICE_ENROLLMENT_REPAIRS_STORAGE_MISCONFIGURED,
        VOICE_ENROLLMENT_PREFLIGHT_STORAGE_CONFIG_CONFLICT: VOICE_ENROLLMENT_REPAIRS_STORAGE_MISCONFIGURED,
        VOICE_ENROLLMENT_PREFLIGHT_STORAGE_RECORDER_CONFLICT: VOICE_ENROLLMENT_REPAIRS_STORAGE_RECORDER_CONFLICT,
        VOICE_ENROLLMENT_PREFLIGHT_STORAGE_PROBE_FAILED: VOICE_ENROLLMENT_REPAIRS_STORAGE_PROBE_FAILED,
    }
    return mapping.get(str(failure_code or ""), VOICE_ENROLLMENT_REPAIRS_STORAGE_UNAVAILABLE)


def _sanitized_placeholders(**values: Any) -> dict[str, str]:
    placeholders: dict[str, str] = {}
    for key, value in values.items():
        if value is None:
            continue
        placeholders[key] = str(value)
    if "last_occurrence" not in placeholders:
        placeholders["last_occurrence"] = _utcnow_iso()
    return placeholders


def _translation_key_for_issue(issue_id: str) -> str:
    return issue_id


async def _async_create_or_update_issue(
    hass,
    *,
    issue_id: str,
    placeholders: dict[str, str],
    severity: ir.IssueSeverity = ir.IssueSeverity.ERROR,
) -> None:
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        is_fixable=False,
        is_persistent=True,
        severity=severity,
        translation_key=_translation_key_for_issue(issue_id),
        translation_placeholders=placeholders,
    )


async def _async_clear_issue(hass, issue_id: str) -> None:
    try:
        ir.async_delete_issue(hass, DOMAIN, issue_id)
    except Exception:
        return


async def async_create_or_update_storage_issue(
    hass,
    *,
    failure_code: str,
    provider_type: str = "mounted_path",
) -> str:
    issue_id = _storage_issue_for_failure_code(failure_code)
    await _async_create_or_update_issue(
        hass,
        issue_id=issue_id,
        placeholders=_sanitized_placeholders(
            failure_code=failure_code,
            provider_type=provider_type,
        ),
    )
    return issue_id


def _capture_provider_issue_for_status(provider_status: str) -> str:
    normalized = str(provider_status or "").strip().lower()
    if normalized in {"unsupported", "future_provider", "no_capture_api"}:
        return VOICE_ENROLLMENT_REPAIRS_CAPTURE_PROVIDER_UNSUPPORTED
    return VOICE_ENROLLMENT_REPAIRS_CAPTURE_PROVIDER_UNAVAILABLE


async def async_create_or_update_capture_provider_issue(
    hass,
    *,
    provider_type: str,
    provider_status: str,
    reason_code: str = "",
    selected_provider: bool = False,
) -> str:
    """Publish sanitized issue for unsupported or unavailable capture provider state."""
    if provider_type == "satellite" and not selected_provider:
        return ""

    issue_id = _capture_provider_issue_for_status(provider_status)
    await _async_create_or_update_issue(
        hass,
        issue_id=issue_id,
        placeholders=_sanitized_placeholders(
            provider_type=provider_type,
            provider_status=provider_status,
            reason_code=reason_code,
        ),
    )
    return issue_id


async def async_clear_capture_provider_issue(hass, issue_id: str | None = None) -> None:
    """Clear capture-provider-specific repairs issues."""
    if issue_id is not None:
        await _async_clear_issue(hass, issue_id)
        return

    await _async_clear_issue(hass, VOICE_ENROLLMENT_REPAIRS_CAPTURE_PROVIDER_UNAVAILABLE)
    await _async_clear_issue(hass, VOICE_ENROLLMENT_REPAIRS_CAPTURE_PROVIDER_UNSUPPORTED)


async def async_clear_storage_issue(hass, issue_id: str | None = None) -> None:
    if issue_id is not None:
        await _async_clear_issue(hass, issue_id)
        return
    for candidate in _STORAGE_ISSUE_IDS:
        await _async_clear_issue(hass, candidate)


async def async_create_or_update_cleanup_issue(
    hass,
    *,
    cleanup_result_code: str,
    cleanup_reason: str,
) -> str:
    issue_id = VOICE_ENROLLMENT_REPAIRS_CLEANUP_FAILED
    await _async_create_or_update_issue(
        hass,
        issue_id=issue_id,
        placeholders=_sanitized_placeholders(
            cleanup_result_code=cleanup_result_code,
            cleanup_reason=cleanup_reason,
        ),
    )
    return issue_id


async def async_clear_cleanup_issue(hass) -> None:
    await _async_clear_issue(hass, VOICE_ENROLLMENT_REPAIRS_CLEANUP_FAILED)


async def async_create_or_update_reconciliation_issue(
    hass,
    *,
    invalid_manifest_count: int = 0,
    cleanup_failed_count: int = 0,
    orphan_count: int = 0,
) -> list[str]:
    created: list[str] = []
    if invalid_manifest_count > 0:
        await _async_create_or_update_issue(
            hass,
            issue_id=VOICE_ENROLLMENT_REPAIRS_INVALID_MANIFEST,
            placeholders=_sanitized_placeholders(invalid_manifest_count=invalid_manifest_count),
        )
        created.append(VOICE_ENROLLMENT_REPAIRS_INVALID_MANIFEST)

    if cleanup_failed_count > 0:
        await _async_create_or_update_issue(
            hass,
            issue_id=VOICE_ENROLLMENT_REPAIRS_ORPHAN_CLEANUP_FAILED,
            placeholders=_sanitized_placeholders(
                cleanup_failed_count=cleanup_failed_count,
                orphan_count=orphan_count,
            ),
        )
        created.append(VOICE_ENROLLMENT_REPAIRS_ORPHAN_CLEANUP_FAILED)

    return created


async def async_clear_reconciliation_issue(hass, issue_id: str | None = None) -> None:
    if issue_id is not None:
        await _async_clear_issue(hass, issue_id)
        return
    for candidate in _RECONCILIATION_ISSUE_IDS:
        await _async_clear_issue(hass, candidate)


def _person_context_issue_for_state(person_context_state: str) -> str:
    normalized = str(person_context_state or "").strip().lower()
    if normalized == "person_context_partial":
        return PERSON_CONTEXT_REPAIRS_PARTIAL
    return PERSON_CONTEXT_REPAIRS_UNRESOLVED


async def async_create_or_update_person_context_issue(
    hass,
    *,
    person_context_state: str,
    reason_code: str,
    active_person_state: str,
    resolved_person_id: str | None,
) -> str:
    """Publish a runtime person-context issue for fail-closed unresolved/partial identity state."""
    issue_id = _person_context_issue_for_state(person_context_state)
    await _async_create_or_update_issue(
        hass,
        issue_id=issue_id,
        placeholders=_sanitized_placeholders(
            person_context_state=person_context_state,
            reason_code=reason_code,
            active_person_state=active_person_state,
            resolved_person_id=resolved_person_id or "",
        ),
    )
    return issue_id


async def async_clear_person_context_issue(hass, issue_id: str | None = None) -> None:
    """Clear person-context repairs issues."""
    if issue_id is not None:
        await _async_clear_issue(hass, issue_id)
        return
    for candidate in _PERSON_CONTEXT_ISSUE_IDS:
        await _async_clear_issue(hass, candidate)
