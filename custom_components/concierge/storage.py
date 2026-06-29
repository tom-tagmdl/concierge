"""Persistent store for Concierge runtime and configuration state."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION
from .models import ConciergeState, ContextState, IdentityProfile, Interaction, RoomConfig, SignalState


class ConciergeStorage:
    """Encapsulate all Concierge persistence operations."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize state store wrapper."""
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)

    async def async_load_state(self) -> ConciergeState:
        """Load state, returning defaults when no data exists yet."""
        raw = await self._store.async_load()
        if raw is None:
            state = ConciergeState()
            await self.async_save_state(state)
            return state
        return ConciergeState.from_dict(raw)

    async def async_save_state(self, state: ConciergeState) -> None:
        """Persist the full Concierge state."""
        await self._store.async_save(state.as_dict())

    async def async_update_room_config(
        self,
        area_id: str,
        aliases: dict[str, str] | None = None,
        global_overlays: dict[str, bool] | None = None,
        posture: str | None = None,
        media_player_entity_ids: list[str] | None = None,
        voice_device_entity_ids: list[str] | None = None,
        tts_voice: str | None = None,
        asset_entity_ids: list[str] | None = None,
        room_sensor_entity_ids: list[str] | None = None,
        room_health_entity_ids: list[str] | None = None,
        human_health_entity_ids: list[str] | None = None,
        light_entity_ids: list[str] | None = None,
        shade_entity_ids: list[str] | None = None,
        speaker_entity_ids: list[str] | None = None,
        dashboard_entity_ids: list[str] | None = None,
        other_entity_ids: list[str] | None = None,
        persona: str | None = None,
        persona_prompt: str | None = None,
    ) -> ConciergeState:
        """Upsert room configuration and persist state."""
        state = await self.async_load_state()
        current = state.rooms.get(area_id, RoomConfig(area_id=area_id))
        if aliases is not None:
            current.aliases = aliases
        if global_overlays is not None:
            current.global_overlays = global_overlays
        if posture is not None:
            current.posture = posture
        if media_player_entity_ids is not None:
            current.media_player_entity_ids = media_player_entity_ids
        if voice_device_entity_ids is not None:
            current.voice_device_entity_ids = voice_device_entity_ids
        if tts_voice is not None:
            current.tts_voice = tts_voice
        if asset_entity_ids is not None:
            current.asset_entity_ids = asset_entity_ids
        if room_sensor_entity_ids is not None:
            current.room_sensor_entity_ids = room_sensor_entity_ids
        if room_health_entity_ids is not None:
            current.room_health_entity_ids = room_health_entity_ids
        if human_health_entity_ids is not None:
            current.human_health_entity_ids = human_health_entity_ids
        if light_entity_ids is not None:
            current.light_entity_ids = light_entity_ids
        if shade_entity_ids is not None:
            current.shade_entity_ids = shade_entity_ids
        if speaker_entity_ids is not None:
            current.speaker_entity_ids = speaker_entity_ids
        if dashboard_entity_ids is not None:
            current.dashboard_entity_ids = dashboard_entity_ids
        if other_entity_ids is not None:
            current.other_entity_ids = other_entity_ids
        if persona is not None:
            current.persona = persona
        if persona_prompt is not None:
            current.persona_prompt = persona_prompt
        state.rooms[area_id] = current
        await self.async_save_state(state)
        return state

    async def async_update_global_feature(
        self,
        feature_key: str,
        enabled: bool,
        options: dict[str, Any] | None = None,
    ) -> ConciergeState:
        """Update one explicit global feature setting and persist state."""
        state = await self.async_load_state()
        state.global_features[feature_key] = {
            "enabled": enabled,
            "options": options or {},
        }
        await self.async_save_state(state)
        return state

    async def async_update_identity_profile(
        self,
        profile: IdentityProfile,
        *,
        set_as_default: bool = False,
    ) -> ConciergeState:
        """Insert or update an identity profile and optionally set it as default."""
        state = await self.async_load_state()
        state.identity_profiles[profile.profile_id] = profile
        if set_as_default or profile.profile_id == "default":
            state.default_identity_profile = profile
        await self.async_save_state(state)
        return state

    async def async_update_global_context_usage(
        self,
        context_type: str,
        enabled: bool,
        options: dict[str, Any] | None,
    ) -> ConciergeState:
        """Update per-context usage preferences and persist state."""
        state = await self.async_load_state()
        state.global_context_usage[context_type] = {
            "enabled": enabled,
            "options": options or {},
        }
        await self.async_save_state(state)
        return state

    async def async_update_execution_preferences(
        self,
        scope_id: str,
        preferences: dict[str, Any],
    ) -> ConciergeState:
        """Update execution preferences for area/composite scope."""
        state = await self.async_load_state()
        state.execution_preferences[scope_id] = preferences
        await self.async_save_state(state)
        return state

    async def async_upsert_interaction(self, interaction: Interaction) -> ConciergeState:
        """Insert or update a runtime interaction."""
        state = await self.async_load_state()
        state.interactions[interaction.interaction_id] = interaction
        await self.async_save_state(state)
        return state

    async def async_remove_interaction(self, interaction_id: str) -> ConciergeState:
        """Remove interaction by identifier."""
        state = await self.async_load_state()
        state.interactions.pop(interaction_id, None)
        await self.async_save_state(state)
        return state

    async def async_upsert_signal(self, signal: SignalState) -> ConciergeState:
        """Insert or update an integration-provided signal snapshot."""
        state = await self.async_load_state()
        state.signals[signal.signal_type] = signal
        await self.async_save_state(state)
        return state

    async def async_upsert_context(self, context: ContextState) -> ConciergeState:
        """Insert or update an integration-provided global context snapshot."""
        state = await self.async_load_state()
        state.contexts[context.context_type] = context
        await self.async_save_state(state)
        return state
