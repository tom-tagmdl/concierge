"""Pytest fixtures for Concierge tests."""

from __future__ import annotations

import shutil
from types import SimpleNamespace
from pathlib import Path

import pytest

from homeassistant import loader
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
    CONF_VOICE_IDENTITY_LINKED,
    DEFAULT_NIGHT_MODE_ENABLED,
    DEFAULT_UPDATE_INTERVAL_SECONDS,
    DOMAIN,
)


@pytest.fixture
def hass_config_dir(hass_tmp_config_dir: str) -> str:
    """Provide a writable HA config dir with this repo's custom integration staged."""
    config_dir = Path(hass_tmp_config_dir)
    repo_custom_components = Path(__file__).resolve().parents[1] / "custom_components"
    target_custom_components = config_dir / "custom_components"

    shutil.copytree(repo_custom_components, target_custom_components, dirs_exist_ok=True)

    return hass_tmp_config_dir


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
def auto_enable_custom_integrations(request):
    """Use plugin integration-loading fixture when available; no-op otherwise."""
    try:
        request.getfixturevalue("enable_custom_integrations")
    except pytest.FixtureLookupError:
        # Standalone runs without the HA pytest plugin can still execute
        # pure unit tests that do not require Home Assistant integration setup.
        pass
    yield


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    enable_custom_integrations,
) -> MockConfigEntry:
    """Set up the integration for tests."""
    storage_root = Path(hass.config.path("voice-enrollment-test-root"))

    # Ensure the integration is discoverable from the active HA config dir.
    custom_components_root = Path(hass.config.path("custom_components"))
    custom_components_root.mkdir(parents=True, exist_ok=True)
    source_integration = Path(__file__).resolve().parents[1] / "custom_components" / DOMAIN
    target_integration = custom_components_root / DOMAIN
    shutil.copytree(source_integration, target_integration, dirs_exist_ok=True)
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS, None)

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
            CONF_VOICE_IDENTITY_LINKED: True,
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

    discovery_integration = _DiscoveryIntegration()
    hass.data["voice_identity"] = {
        mock_config_entry.entry_id: {
            "concierge_discovery_integration": discovery_integration,
            "generate_voiceprint_operation": _GenerateVoiceprintOperation(),
            "get_voiceprint_status_operation": _GetVoiceprintStatusOperation(),
        },
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
