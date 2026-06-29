"""The Concierge integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import ConciergeCoordinator
from .panel import async_setup_panel
from .services import async_register_services, async_unregister_services

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SELECT]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Concierge from YAML (not used)."""
    await async_setup_panel(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Concierge from a config entry."""
    coordinator = ConciergeCoordinator(hass=hass, entry=entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            await async_unregister_services(hass)
            hass.data.pop(DOMAIN, None)
    return unload_ok
