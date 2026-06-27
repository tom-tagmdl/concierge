"""Sensor platform for Concierge."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ConciergeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Concierge sensors from config entry."""
    coordinator: ConciergeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ConciergeStatusSensor(coordinator, entry)], True)


class ConciergeStatusSensor(CoordinatorEntity[ConciergeCoordinator], SensorEntity):
    """Exposes Concierge runtime status."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ConciergeCoordinator, entry: ConfigEntry) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Status"
        self._attr_unique_id = f"{entry.entry_id}_status"

    @property
    def native_value(self) -> str | None:
        """Return sensor value."""
        return self.coordinator.data.get("status")

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        return {
            "enable_notifications": self.coordinator.data.get("enable_notifications"),
            "night_mode_enabled": self.coordinator.data.get("night_mode_enabled"),
            "entry_title": self.coordinator.data.get("entry_title"),
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for registry integration."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            manufacturer="Homes Platform",
            model="Concierge",
            name=self._entry.title,
        )
