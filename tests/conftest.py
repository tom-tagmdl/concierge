"""Pytest fixtures for Concierge tests."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.concierge import diagnostics as diagnostics_module
from custom_components.concierge import enrollment_orchestrator as orchestrator_module
from custom_components.concierge import enrollment_reconciliation as reconciliation_module
from custom_components.concierge import panel as panel_module
from custom_components.concierge import services as services_module
from custom_components.concierge.archive_runtime import (
    CONF_AUDIT_ARCHIVE_DESTINATION_URI,
    CONF_AUDIT_ARCHIVE_ENABLED,
)
from custom_components.concierge.const import (
    CONF_NIGHT_MODE_ENABLED,
    CONF_UPDATE_INTERVAL_SECONDS,
    DEFAULT_NIGHT_MODE_ENABLED,
    DEFAULT_UPDATE_INTERVAL_SECONDS,
    DOMAIN,
)


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Concierge",
        data={
            CONF_UPDATE_INTERVAL_SECONDS: DEFAULT_UPDATE_INTERVAL_SECONDS,
            CONF_NIGHT_MODE_ENABLED: DEFAULT_NIGHT_MODE_ENABLED,
        },
    )


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading integration code from custom_components during tests."""
    yield


@pytest.fixture
async def setup_integration(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> MockConfigEntry:
    """Set up the integration for tests."""
    from pathlib import Path

    storage_root = Path(hass.config.path("voice-enrollment-test-root"))

    services_module.resolve_voice_enrollment_root = lambda destination_uri: storage_root
    panel_module.resolve_voice_enrollment_root = lambda destination_uri: storage_root
    reconciliation_module.resolve_voice_enrollment_root = lambda destination_uri: storage_root
    diagnostics_module.resolve_voice_enrollment_root = lambda destination_uri: storage_root
    orchestrator_module.resolve_voice_enrollment_root = lambda destination_uri: storage_root

    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={
            CONF_AUDIT_ARCHIVE_DESTINATION_URI: "/media/concierge-tests",
            CONF_AUDIT_ARCHIVE_ENABLED: True,
        },
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)

    class _DiscoveryIntegration:
        async def discover(self, request):
            _ = request
            projection = SimpleNamespace(
                discovery_state="healthy",
                service_available=True,
                service_compatible=True,
                enabled_capabilities=("generate_voiceprint", "voiceprint_status"),
                supported_capabilities=("metadata_retrieval",),
            )
            return SimpleNamespace(success=True, projection=projection)

    class _GenerateVoiceprintOperation:
        async def execute(self, request):
            _ = request
            return SimpleNamespace(
                success=True,
                reason_code="ready",
                failure_category="",
                voiceprint_id="vp_test_001",
                revision=1,
            )

    class _GetVoiceprintStatusOperation:
        async def execute(self, request):
            return SimpleNamespace(
                success=True,
                voiceprint_id=str(getattr(request, "voiceprint_id", "vp_test_001") or "vp_test_001"),
                lifecycle_status="active",
                active=True,
                revision=1,
                status_summary="voiceprint_active",
            )

    hass.data["voice_identity"] = {
        "concierge_discovery_integration": _DiscoveryIntegration(),
        "generate_voiceprint_operation": _GenerateVoiceprintOperation(),
        "get_voiceprint_status_operation": _GetVoiceprintStatusOperation(),
    }

    async def _capture_provider_capabilities(_self):
        return {
            "provider_type": "browser_microphone",
            "provider_available": True,
            "provider_supported": True,
            "capture_supported": True,
            "selection_supported": True,
            "reason_code": "ready",
            "satellite_capture_supported": False,
            "satellite_status_code": "provider_not_selected",
            "provider_status_summary": "ready",
        }

    orchestrator_module.EnrollmentOrchestrator.get_capture_provider_capabilities = (
        _capture_provider_capabilities
    )

    for service_domain in ("homeassistant", "light", "scene"):
        if not hass.services.has_service(service_domain, "turn_on"):
            hass.services.async_register(service_domain, "turn_on", lambda call: None)

    await hass.async_block_till_done()
    return mock_config_entry
