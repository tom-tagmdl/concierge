"""Test integration setup."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.concierge.const import DOMAIN


async def test_setup_and_unload_entry(hass: HomeAssistant, setup_integration) -> None:
    """Test config entry setup and unload."""
    entry = setup_integration
    assert DOMAIN in hass.data
    assert entry.entry_id in hass.data[DOMAIN]
    assert f"{entry.entry_id}_startup_reconciliation" in hass.data[DOMAIN]

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert DOMAIN not in hass.data
