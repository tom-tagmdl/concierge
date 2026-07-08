"""Pytest fixtures for Concierge tests."""

from __future__ import annotations

import pytest

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.concierge import diagnostics as diagnostics_module
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


@pytest.fixture
async def setup_integration(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> MockConfigEntry:
    """Set up the integration for tests."""
    from pathlib import Path

    storage_root = Path(hass.config.path("voice-enrollment-test-root"))

    mock_config_entry.options = {
        CONF_AUDIT_ARCHIVE_DESTINATION_URI: "/media/concierge-tests",
        CONF_AUDIT_ARCHIVE_ENABLED: True,
    }

    services_module.resolve_voice_enrollment_root = lambda destination_uri: storage_root
    panel_module.resolve_voice_enrollment_root = lambda destination_uri: storage_root
    reconciliation_module.resolve_voice_enrollment_root = lambda destination_uri: storage_root
    diagnostics_module.resolve_voice_enrollment_root = lambda destination_uri: storage_root

    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
