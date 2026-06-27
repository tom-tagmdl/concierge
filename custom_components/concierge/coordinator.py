"""Data update coordinator for Concierge."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_ENABLE_NOTIFICATIONS,
    CONF_NIGHT_MODE_ENABLED,
    CONF_UPDATE_INTERVAL_SECONDS,
    COORDINATOR_MAX_UPDATE_SECONDS,
    COORDINATOR_MIN_UPDATE_SECONDS,
    DEFAULT_ENABLE_NOTIFICATIONS,
    DEFAULT_NIGHT_MODE_ENABLED,
    DEFAULT_UPDATE_INTERVAL_SECONDS,
    DOMAIN,
    SIGNAL_READY,
)

_LOGGER = logging.getLogger(__name__)


class ConciergeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinates runtime state for Concierge."""

    def __init__(self, hass, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.entry = entry

        configured_seconds = int(
            entry.options.get(
                CONF_UPDATE_INTERVAL_SECONDS,
                entry.data.get(CONF_UPDATE_INTERVAL_SECONDS, DEFAULT_UPDATE_INTERVAL_SECONDS),
            )
        )
        interval_seconds = max(COORDINATOR_MIN_UPDATE_SECONDS, min(COORDINATOR_MAX_UPDATE_SECONDS, configured_seconds))

        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(seconds=interval_seconds),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch runtime data.

        Concierge currently provides orchestration health and effective options state.
        """
        enable_notifications = bool(
            self.entry.options.get(
                CONF_ENABLE_NOTIFICATIONS,
                self.entry.data.get(CONF_ENABLE_NOTIFICATIONS, DEFAULT_ENABLE_NOTIFICATIONS),
            )
        )
        night_mode_enabled = bool(
            self.entry.options.get(
                CONF_NIGHT_MODE_ENABLED,
                self.entry.data.get(CONF_NIGHT_MODE_ENABLED, DEFAULT_NIGHT_MODE_ENABLED),
            )
        )

        return {
            "status": SIGNAL_READY,
            "enable_notifications": enable_notifications,
            "night_mode_enabled": night_mode_enabled,
            "entry_title": self.entry.title,
        }
