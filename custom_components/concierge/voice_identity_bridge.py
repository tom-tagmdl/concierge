"""Bridge helpers for Concierge to consume Voice Identity discovery safely."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from homeassistant.core import HomeAssistant

_VOICE_IDENTITY_DOMAIN = "voice_identity"
_DISCOVERY_INTEGRATION_KEY = "concierge_discovery_integration"
_REQUIRED_ENABLED_CAPABILITIES = {
    "generate_voiceprint",
    "voiceprint_status",
}
_REQUIRED_SUPPORTED_CAPABILITIES = {
    "metadata_retrieval",
}
_COMPATIBLE_DISCOVERY_STATES = {"healthy", "compatible"}


@dataclass(slots=True)
class _DiscoveryRequest:
    requested_contract_version: int = 1
    requested_schema_version: int = 1
    force_refresh: bool = False
    correlation_id: str | None = None
    request_metadata: dict[str, bool | int | float | str | None] = field(default_factory=dict)


def _select_voice_identity_runtime_bucket(domain_data: dict[str, Any]) -> dict[str, Any]:
    """Return Voice Identity runtime bucket that exposes discovery integration.

    Supports both legacy top-level registration and entry-scoped runtime
    registration used by production Voice Identity setup.
    """
    if _DISCOVERY_INTEGRATION_KEY in domain_data:
        return domain_data

    for key in sorted(domain_data):
        candidate = domain_data.get(key)
        if not isinstance(candidate, dict):
            continue
        if _DISCOVERY_INTEGRATION_KEY in candidate:
            return candidate

    return {}


def _status_payload(
    *,
    voice_enrollment_enabled: bool,
    reason_code: str,
    status_summary: str,
    voice_identity_connected: bool,
    voice_identity_available: bool,
    voice_identity_compatible: bool,
    voice_identity_discovery_state: str,
    enabled_capabilities: tuple[str, ...],
    supported_capabilities: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "voice_enrollment_enabled": bool(voice_enrollment_enabled),
        "voice_enrollment_reason_code": str(reason_code),
        "voice_enrollment_status_summary": str(status_summary),
        "voice_identity_connected": bool(voice_identity_connected),
        "voice_identity_available": bool(voice_identity_available),
        "voice_identity_compatible": bool(voice_identity_compatible),
        "voice_identity_discovery_state": str(voice_identity_discovery_state),
        "voice_identity_enabled_capabilities": tuple(sorted(set(enabled_capabilities))),
        "voice_identity_supported_capabilities": tuple(sorted(set(supported_capabilities))),
    }


async def async_get_voice_identity_enrollment_status(hass: HomeAssistant) -> dict[str, Any]:
    """Return Voice Identity discovery projection for Concierge enrollment gating."""
    domain_data = hass.data.get(_VOICE_IDENTITY_DOMAIN)
    if not isinstance(domain_data, dict):
        return _status_payload(
            voice_enrollment_enabled=False,
            reason_code="voice_identity_not_loaded",
            status_summary="Voice enrollment requires Voice Identity to be loaded.",
            voice_identity_connected=False,
            voice_identity_available=False,
            voice_identity_compatible=False,
            voice_identity_discovery_state="unavailable",
            enabled_capabilities=(),
            supported_capabilities=(),
        )

    runtime_bucket = _select_voice_identity_runtime_bucket(domain_data)
    discovery_integration = runtime_bucket.get(_DISCOVERY_INTEGRATION_KEY)
    discover = getattr(discovery_integration, "discover", None)
    if not callable(discover):
        return _status_payload(
            voice_enrollment_enabled=False,
            reason_code="voice_identity_discovery_unavailable",
            status_summary="Voice enrollment requires Voice Identity discovery support.",
            voice_identity_connected=False,
            voice_identity_available=False,
            voice_identity_compatible=False,
            voice_identity_discovery_state="unavailable",
            enabled_capabilities=(),
            supported_capabilities=(),
        )

    try:
        result = await discover(_DiscoveryRequest())
    except Exception:
        return _status_payload(
            voice_enrollment_enabled=False,
            reason_code="voice_identity_discovery_failed",
            status_summary="Voice enrollment is unavailable because Voice Identity discovery failed.",
            voice_identity_connected=True,
            voice_identity_available=False,
            voice_identity_compatible=False,
            voice_identity_discovery_state="unavailable",
            enabled_capabilities=(),
            supported_capabilities=(),
        )

    projection = getattr(result, "projection", None)
    if projection is None:
        return _status_payload(
            voice_enrollment_enabled=False,
            reason_code="voice_identity_projection_missing",
            status_summary="Voice enrollment is unavailable because Voice Identity did not return discovery data.",
            voice_identity_connected=True,
            voice_identity_available=False,
            voice_identity_compatible=False,
            voice_identity_discovery_state="unavailable",
            enabled_capabilities=(),
            supported_capabilities=(),
        )

    discovery_state = str(getattr(projection, "discovery_state", "unavailable") or "unavailable").strip().lower()
    service_available = bool(getattr(projection, "service_available", False))
    service_compatible = bool(getattr(projection, "service_compatible", False))
    enabled_capabilities = tuple(
        sorted({str(item).strip().lower() for item in getattr(projection, "enabled_capabilities", ()) if str(item).strip()})
    )
    supported_capabilities = tuple(
        sorted({str(item).strip().lower() for item in getattr(projection, "supported_capabilities", ()) if str(item).strip()})
    )

    has_required_enabled = _REQUIRED_ENABLED_CAPABILITIES.issubset(set(enabled_capabilities))
    has_required_supported = _REQUIRED_SUPPORTED_CAPABILITIES.issubset(set(supported_capabilities))

    if not service_available:
        return _status_payload(
            voice_enrollment_enabled=False,
            reason_code="voice_identity_unavailable",
            status_summary="Voice enrollment is unavailable because Voice Identity is not currently available.",
            voice_identity_connected=True,
            voice_identity_available=False,
            voice_identity_compatible=False,
            voice_identity_discovery_state=discovery_state,
            enabled_capabilities=enabled_capabilities,
            supported_capabilities=supported_capabilities,
        )

    if not service_compatible or discovery_state not in _COMPATIBLE_DISCOVERY_STATES:
        return _status_payload(
            voice_enrollment_enabled=False,
            reason_code="voice_identity_incompatible",
            status_summary="Voice enrollment is unavailable because Voice Identity compatibility checks did not pass.",
            voice_identity_connected=True,
            voice_identity_available=service_available,
            voice_identity_compatible=False,
            voice_identity_discovery_state=discovery_state,
            enabled_capabilities=enabled_capabilities,
            supported_capabilities=supported_capabilities,
        )

    if not has_required_enabled or not has_required_supported:
        return _status_payload(
            voice_enrollment_enabled=False,
            reason_code="voice_identity_capability_missing",
            status_summary="Voice enrollment is unavailable because required Voice Identity capabilities are missing.",
            voice_identity_connected=True,
            voice_identity_available=service_available,
            voice_identity_compatible=service_compatible,
            voice_identity_discovery_state=discovery_state,
            enabled_capabilities=enabled_capabilities,
            supported_capabilities=supported_capabilities,
        )

    return _status_payload(
        voice_enrollment_enabled=True,
        reason_code="ready",
        status_summary="Voice enrollment is ready.",
        voice_identity_connected=True,
        voice_identity_available=service_available,
        voice_identity_compatible=service_compatible,
        voice_identity_discovery_state=discovery_state,
        enabled_capabilities=enabled_capabilities,
        supported_capabilities=supported_capabilities,
    )
