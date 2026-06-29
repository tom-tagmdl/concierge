"""Data update coordinator for Concierge."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_NIGHT_MODE_ENABLED,
    CONF_UPDATE_INTERVAL_SECONDS,
    COORDINATOR_MAX_UPDATE_SECONDS,
    COORDINATOR_MIN_UPDATE_SECONDS,
    DEFAULT_NIGHT_MODE_ENABLED,
    DEFAULT_UPDATE_INTERVAL_SECONDS,
    DOMAIN,
    SIGNAL_READY,
)
from .storage import ConciergeStorage

_LOGGER = logging.getLogger(__name__)


class ConciergeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinates runtime state for Concierge."""

    def __init__(self, hass, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.entry = entry
        self.hass = hass
        self._storage = ConciergeStorage(hass)

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
        night_mode_enabled = bool(
            self.entry.options.get(
                CONF_NIGHT_MODE_ENABLED,
                self.entry.data.get(CONF_NIGHT_MODE_ENABLED, DEFAULT_NIGHT_MODE_ENABLED),
            )
        )

        state = await self._storage.async_load_state()
        services_by_domain = self.hass.services.async_services()
        integration_capabilities = {
            domain: sorted(domain_services.keys())
            for domain, domain_services in services_by_domain.items()
            if domain not in {DOMAIN, "homeassistant", "persistent_notification"}
        }

        foundation_summary = {
            "room_count": len(state.rooms),
            "interaction_count": len(state.interactions),
            "signal_count": len(state.signals),
            "context_source_count": len(state.contexts),
        }
        room_configs = {
            area_id: {
                "posture": room.posture,
                "media_player_entity_ids": room.media_player_entity_ids,
                "voice_device_entity_ids": room.voice_device_entity_ids,
                "tts_voice": room.tts_voice,
            }
            for area_id, room in state.rooms.items()
        }

        return {
            "status": SIGNAL_READY,
            "night_mode_enabled": night_mode_enabled,
            "entry_title": self.entry.title,
            "foundation_summary": foundation_summary,
            "capability_domains": sorted(integration_capabilities.keys()),
            "room_configs": room_configs,
        }
