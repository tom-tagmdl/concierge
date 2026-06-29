"""Test Concierge config flow."""

from __future__ import annotations

from homeassistant import config_entries, data_entry_flow

from custom_components.concierge.const import DOMAIN


async def test_user_flow(hass) -> None:
    """Test initial user flow."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Concierge",
            "ai_enabled": False,
            "ai_local_first": True,
            "action_provider": "none",
            "action_model": "",
            "action_endpoint": "",
            "tts_enabled": False,
            "tts_provider": "none",
            "tts_voice": "",
            "night_mode_enabled": False,
        },
    )
    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY


async def test_single_instance_abort(hass) -> None:
    """Test duplicate flow aborts."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Concierge",
            "ai_enabled": False,
            "ai_local_first": True,
            "action_provider": "none",
            "action_model": "",
            "action_endpoint": "",
            "tts_enabled": False,
            "tts_provider": "none",
            "tts_voice": "",
            "night_mode_enabled": False,
        },
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

    dup = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert dup["type"] == data_entry_flow.FlowResultType.ABORT
    assert dup["reason"] == "already_configured"
