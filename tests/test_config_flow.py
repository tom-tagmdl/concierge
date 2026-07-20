"""Test Concierge config flow."""

from __future__ import annotations

from homeassistant import config_entries, data_entry_flow
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.concierge.config_flow import (
    CONF_ASSET_INTELLIGENCE_PROVIDER,
    CONF_AUDIT_ARCHIVE_DESTINATION_URI,
    CONF_AUDIT_ARCHIVE_ENABLED,
    CONF_AUDIT_ARCHIVE_INCLUDE_REFERENCE_EXCERPTS,
    CONF_AUDIT_ARCHIVE_RETENTION_DAYS,
    CONF_MEDIA_PROVIDER,
)
from custom_components.concierge.const import DOMAIN


def _current_config_flow_input() -> dict:
    """Return schema-valid config flow input for the current global options surface."""
    return {
        "name": "Concierge",
        "ai_enabled": False,
        "ai_local_first": True,
        "action_provider": "none",
        "tts_enabled": False,
        "tts_provider": "none",
        CONF_MEDIA_PROVIDER: "none",
        CONF_ASSET_INTELLIGENCE_PROVIDER: "none",
        CONF_AUDIT_ARCHIVE_DESTINATION_URI: "",
        CONF_AUDIT_ARCHIVE_ENABLED: False,
        CONF_AUDIT_ARCHIVE_INCLUDE_REFERENCE_EXCERPTS: False,
        CONF_AUDIT_ARCHIVE_RETENTION_DAYS: 30,
    }


async def test_user_flow(hass) -> None:
    """Test initial user flow."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        _current_config_flow_input(),
    )
    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY


async def test_single_instance_abort(hass) -> None:
    """Test duplicate flow aborts."""
    MockConfigEntry(
        domain=DOMAIN,
        title="Concierge",
        data=_current_config_flow_input(),
        unique_id=DOMAIN,
    ).add_to_hass(hass)

    dup = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    assert dup["type"] == data_entry_flow.FlowResultType.FORM
    dup = await hass.config_entries.flow.async_configure(
        dup["flow_id"],
        _current_config_flow_input(),
    )
    assert dup["type"] == data_entry_flow.FlowResultType.ABORT
    assert dup["reason"] == "already_configured"
