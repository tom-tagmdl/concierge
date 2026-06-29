"""Select entities for Concierge room configuration."""

from __future__ import annotations

from collections.abc import Iterable

from homeassistant.components.tts.const import DATA_COMPONENT as TTS_DATA_COMPONENT
from homeassistant.components.select import DOMAIN as SELECT_DOMAIN, SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ConciergeCoordinator
from .storage import ConciergeStorage

POSTURE_OPTIONS = ["day", "night", "sleep", "away"]
MEDIA_PLAYER_NONE = "none"
VOICE_DEVICE_NONE = "none"
VOICE_SYSTEM_DEFAULT = "system_default"
TTS_PROVIDER_ENTITY_IDS = {
    "openai_conversation": "tts.openai_tts",
    "google_translate": "tts.google_translate_en_com",
}
FALLBACK_VOICE_OPTIONS = {
    "openai_conversation": [
        "alloy",
        "ash",
        "ballad",
        "cedar",
        "coral",
        "echo",
        "fable",
        "marin",
        "nova",
        "onyx",
        "sage",
        "shimmer",
        "verse",
    ],
    "google_translate": ["default"],
}


def _tts_provider(entry: ConfigEntry) -> str:
    """Return configured TTS provider."""
    return str(entry.options.get("tts_provider", entry.data.get("tts_provider", "none")))


def _room_media_player_options(hass: HomeAssistant, area_id: str) -> list[str]:
    """Return media player entity IDs associated with an area."""
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    options: set[str] = set()

    for entity in er.async_entries_for_area(entity_registry, area_id):
        if entity.domain == "media_player" and not entity.disabled_by:
            options.add(entity.entity_id)

    area_devices = {device.id for device in dr.async_entries_for_area(device_registry, area_id)}
    for entity in entity_registry.entities.values():
        if entity.device_id in area_devices and entity.domain == "media_player" and not entity.disabled_by:
            options.add(entity.entity_id)

    sorted_options = sorted(options)
    return [MEDIA_PLAYER_NONE, *sorted_options]


def _room_voice_device_options(hass: HomeAssistant, area_id: str) -> list[str]:
    """Return assist satellite entity IDs associated with an area."""
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    options: set[str] = set()

    for entity in er.async_entries_for_area(entity_registry, area_id):
        if entity.domain == "assist_satellite" and not entity.disabled_by:
            options.add(entity.entity_id)

    area_devices = {device.id for device in dr.async_entries_for_area(device_registry, area_id)}
    for entity in entity_registry.entities.values():
        if entity.device_id in area_devices and entity.domain == "assist_satellite" and not entity.disabled_by:
            options.add(entity.entity_id)

    sorted_options = sorted(options)
    return [VOICE_DEVICE_NONE, *sorted_options]


def _voice_options(hass: HomeAssistant, entry: ConfigEntry, current_voice: str = "") -> list[str]:
    """Return voice override options for the configured TTS provider."""
    provider = _tts_provider(entry)
    entity_id = TTS_PROVIDER_ENTITY_IDS.get(provider)
    voices: list[str] = []

    if entity_id and TTS_DATA_COMPONENT in hass.data:
        entity_component = hass.data[TTS_DATA_COMPONENT]
        if tts_entity := entity_component.get_entity(entity_id):
            language = getattr(tts_entity, "default_language", "en-US")
            supported_voices = tts_entity.async_get_supported_voices(language)
            if supported_voices:
                voices = [voice.voice_id for voice in supported_voices]

    if not voices:
        voices = FALLBACK_VOICE_OPTIONS.get(provider, [])

    normalized = list(dict.fromkeys([*voices, *( [current_voice] if current_voice else [] )]))
    if provider == "google_translate" and not normalized:
        normalized = ["default"]
    return [VOICE_SYSTEM_DEFAULT, *normalized] if normalized else [VOICE_SYSTEM_DEFAULT]


def _should_expose_room(
    coordinator: ConciergeCoordinator,
    area_id: str,
) -> bool:
    """Return whether Concierge room controls should exist for an area."""
    room_configs = coordinator.data.get("room_configs", {})
    if area_id in room_configs:
        return True

    media_player_options = _room_media_player_options(coordinator.hass, area_id)
    if len(media_player_options) > 1:
        return True

    voice_device_options = _room_voice_device_options(coordinator.hass, area_id)
    return len(voice_device_options) > 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Concierge room configuration selects."""
    coordinator: ConciergeCoordinator = hass.data[DOMAIN][entry.entry_id]
    area_registry = ar.async_get(hass)
    entity_registry = er.async_get(hass)

    entities: list[SelectEntity] = []
    for area in area_registry.async_list_areas():
        if not _should_expose_room(coordinator, area.id):
            for key in ("posture", "media_player", "voice", "voice_device"):
                unique_id = f"{entry.entry_id}_{area.id}_{key}"
                if entity_id := entity_registry.async_get_entity_id(
                    SELECT_DOMAIN,
                    DOMAIN,
                    unique_id,
                ):
                    entity_registry.async_remove(entity_id)
            continue
        entities.extend(
            [
                ConciergeRoomPostureSelect(coordinator, entry, area.id, area.name),
                ConciergeRoomMediaPlayerSelect(coordinator, entry, area.id, area.name),
                ConciergeRoomVoiceDeviceSelect(coordinator, entry, area.id, area.name),
                ConciergeRoomVoiceSelect(coordinator, entry, area.id, area.name),
            ]
        )

    async_add_entities(entities, True)


class ConciergeRoomConfigSelect(CoordinatorEntity[ConciergeCoordinator], SelectEntity):
    """Base select for room-scoped Concierge configuration."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ConciergeCoordinator,
        entry: ConfigEntry,
        area_id: str,
        area_name: str,
        key: str,
        label: str,
    ) -> None:
        """Initialize room-scoped select."""
        super().__init__(coordinator)
        self._entry = entry
        self._area_id = area_id
        self._area_name = area_name
        self._storage = ConciergeStorage(coordinator.hass)
        self._attr_name = f"{area_name} {label}"
        self._attr_unique_id = f"{entry.entry_id}_{area_id}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Group entities under Concierge integration device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            manufacturer="Homes Platform",
            model="Concierge",
            name=self._entry.title,
        )

    async def _async_room_config(self):
        """Return current room config from storage-backed coordinator state."""
        state = await self._storage.async_load_state()
        return state.rooms.get(self._area_id)


class ConciergeRoomPostureSelect(ConciergeRoomConfigSelect):
    """Select entity for room posture."""

    def __init__(self, coordinator: ConciergeCoordinator, entry: ConfigEntry, area_id: str, area_name: str) -> None:
        super().__init__(coordinator, entry, area_id, area_name, "posture", "Posture")
        self._attr_options = POSTURE_OPTIONS

    @property
    def current_option(self) -> str:
        room = self.coordinator.data.get("room_configs", {}).get(self._area_id, {})
        return str(room.get("posture", "day"))

    async def async_select_option(self, option: str) -> None:
        await self._storage.async_update_room_config(area_id=self._area_id, posture=option)
        await self.coordinator.async_request_refresh()


class ConciergeRoomMediaPlayerSelect(ConciergeRoomConfigSelect):
    """Select entity for room playback target."""

    def __init__(self, coordinator: ConciergeCoordinator, entry: ConfigEntry, area_id: str, area_name: str) -> None:
        super().__init__(coordinator, entry, area_id, area_name, "media_player", "Playback Target")

    @property
    def options(self) -> list[str]:
        return _room_media_player_options(self.coordinator.hass, self._area_id)

    @property
    def current_option(self) -> str:
        room = self.coordinator.data.get("room_configs", {}).get(self._area_id, {})
        targets = room.get("media_player_entity_ids", [])
        if targets:
            return str(targets[0])
        return MEDIA_PLAYER_NONE

    async def async_select_option(self, option: str) -> None:
        targets = [] if option == MEDIA_PLAYER_NONE else [option]
        await self._storage.async_update_room_config(
            area_id=self._area_id,
            media_player_entity_ids=targets,
        )
        await self.coordinator.async_request_refresh()


class ConciergeRoomVoiceSelect(ConciergeRoomConfigSelect):
    """Select entity for room TTS voice override."""

    def __init__(self, coordinator: ConciergeCoordinator, entry: ConfigEntry, area_id: str, area_name: str) -> None:
        super().__init__(coordinator, entry, area_id, area_name, "voice", "Voice")

    @property
    def options(self) -> list[str]:
        room = self.coordinator.data.get("room_configs", {}).get(self._area_id, {})
        current_voice = str(room.get("tts_voice", ""))
        return _voice_options(self.coordinator.hass, self._entry, current_voice)

    @property
    def current_option(self) -> str:
        room = self.coordinator.data.get("room_configs", {}).get(self._area_id, {})
        voice = str(room.get("tts_voice", ""))
        return voice or VOICE_SYSTEM_DEFAULT

    async def async_select_option(self, option: str) -> None:
        await self._storage.async_update_room_config(
            area_id=self._area_id,
            tts_voice="" if option == VOICE_SYSTEM_DEFAULT else option,
        )
        await self.coordinator.async_request_refresh()


class ConciergeRoomVoiceDeviceSelect(ConciergeRoomConfigSelect):
    """Select entity for room voice assistant device binding."""

    def __init__(self, coordinator: ConciergeCoordinator, entry: ConfigEntry, area_id: str, area_name: str) -> None:
        super().__init__(coordinator, entry, area_id, area_name, "voice_device", "Voice Device")

    @property
    def options(self) -> list[str]:
        return _room_voice_device_options(self.coordinator.hass, self._area_id)

    @property
    def current_option(self) -> str:
        room = self.coordinator.data.get("room_configs", {}).get(self._area_id, {})
        targets = room.get("voice_device_entity_ids", [])
        if targets:
            return str(targets[0])
        return VOICE_DEVICE_NONE

    async def async_select_option(self, option: str) -> None:
        targets = [] if option == VOICE_DEVICE_NONE else [option]
        await self._storage.async_update_room_config(
            area_id=self._area_id,
            voice_device_entity_ids=targets,
        )
        await self.coordinator.async_request_refresh()
