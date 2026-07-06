"""Persistent store for Concierge runtime and configuration state."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION
from .models import (
    ActivityEvent,
    CompositeConfig,
    ConciergeState,
    ContextState,
    IdentityProfile,
    Interaction,
    PersonProfile,
    RoomConfig,
    SignalState,
    VoiceProfile,
)


def _utcnow_iso() -> str:
    """Return timezone-aware UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


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
        tts_language: str | None = None,
        ai_knowledge_enabled: bool | None = None,
        environment_information_outputs: list[str] | None = None,
        device_groups: list[dict[str, Any]] | None = None,
        asset_groups: list[dict[str, Any]] | None = None,
        room_sensor_entity_ids: list[str] | None = None,
        room_health_entity_ids: list[str] | None = None,
        human_health_entity_ids: list[str] | None = None,
        light_entity_ids: list[str] | None = None,
        lamp_entity_ids: list[str] | None = None,
        shade_entity_ids: list[str] | None = None,
        speaker_entity_ids: list[str] | None = None,
        tv_entity_ids: list[str] | None = None,
        dashboard_entity_ids: list[str] | None = None,
        other_entity_ids: list[str] | None = None,
        weather_source_entity_ids: list[str] | None = None,
        news_source_entity_ids: list[str] | None = None,
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
        if tts_language is not None:
            current.tts_language = tts_language
        if ai_knowledge_enabled is not None:
            current.ai_knowledge_enabled = ai_knowledge_enabled
        if environment_information_outputs is not None:
            current.environment_information_outputs = environment_information_outputs
        if device_groups is not None:
            current.device_groups = device_groups
        if asset_groups is not None:
            current.asset_groups = asset_groups
        if room_sensor_entity_ids is not None:
            current.room_sensor_entity_ids = room_sensor_entity_ids
        if room_health_entity_ids is not None:
            current.room_health_entity_ids = room_health_entity_ids
        if human_health_entity_ids is not None:
            current.human_health_entity_ids = human_health_entity_ids
        if light_entity_ids is not None:
            current.light_entity_ids = light_entity_ids
        if lamp_entity_ids is not None:
            current.lamp_entity_ids = lamp_entity_ids
        if shade_entity_ids is not None:
            current.shade_entity_ids = shade_entity_ids
        if speaker_entity_ids is not None:
            current.speaker_entity_ids = speaker_entity_ids
        if tv_entity_ids is not None:
            current.tv_entity_ids = tv_entity_ids
        if dashboard_entity_ids is not None:
            current.dashboard_entity_ids = dashboard_entity_ids
        if other_entity_ids is not None:
            current.other_entity_ids = other_entity_ids
        if weather_source_entity_ids is not None:
            current.weather_source_entity_ids = weather_source_entity_ids
        if news_source_entity_ids is not None:
            current.news_source_entity_ids = news_source_entity_ids
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

    async def async_update_person_profile(
        self,
        profile: PersonProfile,
        *,
        set_as_default: bool = False,
    ) -> ConciergeState:
        """Insert or update a person profile and optionally set it as default."""
        state = await self.async_load_state()
        state.person_profiles[profile.person_id] = profile
        if set_as_default or profile.person_id == "default":
            state.default_person_profile = profile
        await self.async_save_state(state)
        return state

    async def async_record_activity_event(self, activity: ActivityEvent) -> ConciergeState:
        """Append or replace an activity event by identifier and persist state."""
        state = await self.async_load_state()
        state.activities[activity.activity_id] = activity
        await self.async_save_state(state)
        return state

    async def async_close_activity_event(
        self,
        *,
        activity_id: str,
        ended_at: str,
        outcome: str,
        outcome_reason: str,
        actions_taken: list[str],
        policy_gates: list[str],
    ) -> ConciergeState:
        """Close an existing activity with final outcome metadata."""
        state = await self.async_load_state()
        activity = state.activities.get(activity_id)
        if activity is None:
            raise KeyError(activity_id)

        activity.ended_at = ended_at
        activity.outcome = outcome
        activity.outcome_reason = outcome_reason
        activity.actions_taken = actions_taken
        activity.policy_gates = policy_gates

        state.activities[activity_id] = activity
        await self.async_save_state(state)
        return state

    async def async_update_voice_profile(
        self,
        profile: VoiceProfile,
        *,
        set_as_default: bool = False,
    ) -> ConciergeState:
        """Insert or update a voice profile and optionally set it as default."""
        state = await self.async_load_state()
        state.voice_profiles[profile.voice_profile_id] = profile
        if set_as_default or profile.voice_profile_id == "default":
            state.default_voice_profile = profile
        await self.async_save_state(state)
        return state

    async def async_delete_voice_profile(
        self,
        voice_profile_id: str,
        *,
        unlink_from_people: bool = True,
    ) -> ConciergeState:
        """Delete a voice profile and optionally remove person links to it."""
        state = await self.async_load_state()
        state.voice_profiles.pop(voice_profile_id, None)

        if state.default_voice_profile and state.default_voice_profile.voice_profile_id == voice_profile_id:
            state.default_voice_profile = None

        if unlink_from_people:
            if (
                state.default_person_profile is not None
                and state.default_person_profile.voice_profile_id == voice_profile_id
            ):
                state.default_person_profile.voice_profile_id = None
            for profile in state.person_profiles.values():
                if profile.voice_profile_id == voice_profile_id:
                    profile.voice_profile_id = None

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

    async def async_update_composite_config(
        self,
        *,
        composite_id: str,
        name: str | None = None,
        floor_id: str | None = None,
        area_ids: list[str] | None = None,
        primary_area: str | None = None,
        enabled: bool | None = None,
        posture: str | None = None,
        media_player_entity_ids: list[str] | None = None,
        voice_device_entity_ids: list[str] | None = None,
        tts_voice: str | None = None,
        tts_language: str | None = None,
        device_groups: list[dict[str, Any]] | None = None,
        persona: str | None = None,
        persona_prompt: str | None = None,
        ai_knowledge_enabled: bool | None = None,
        environment_information_outputs: list[str] | None = None,
        asset_groups: list[dict[str, Any]] | None = None,
        room_sensor_entity_ids: list[str] | None = None,
        room_health_entity_ids: list[str] | None = None,
        human_health_entity_ids: list[str] | None = None,
        light_entity_ids: list[str] | None = None,
        shade_entity_ids: list[str] | None = None,
        speaker_entity_ids: list[str] | None = None,
        dashboard_entity_ids: list[str] | None = None,
        other_entity_ids: list[str] | None = None,
        weather_source_entity_ids: list[str] | None = None,
        news_source_entity_ids: list[str] | None = None,
    ) -> ConciergeState:
        """Create, update, or dismantle a composite configuration.

        If area_ids is provided and is empty, the composite is dismantled.
        """
        state = await self.async_load_state()

        if area_ids is not None and len(area_ids) == 0:
            state.composites.pop(composite_id, None)
            await self.async_save_state(state)
            return state

        now_iso = _utcnow_iso()
        current = state.composites.get(composite_id)
        if current is None:
            current = CompositeConfig(
                composite_id=composite_id,
                name=name or composite_id,
                floor_id=floor_id,
                area_ids=list(area_ids or []),
                primary_area=primary_area,
                enabled=True if enabled is None else bool(enabled),
                posture=posture if posture is not None else "day",
                media_player_entity_ids=list(media_player_entity_ids or []),
                voice_device_entity_ids=list(voice_device_entity_ids or []),
                tts_voice=tts_voice or "",
                tts_language=tts_language or "",
                device_groups=list(device_groups or []),
                persona=persona or "",
                persona_prompt=persona_prompt or "",
                ai_knowledge_enabled=False if ai_knowledge_enabled is None else bool(ai_knowledge_enabled),
                environment_information_outputs=list(environment_information_outputs or []),
                asset_groups=list(asset_groups or []),
                room_sensor_entity_ids=list(room_sensor_entity_ids or []),
                room_health_entity_ids=list(room_health_entity_ids or []),
                human_health_entity_ids=list(human_health_entity_ids or []),
                light_entity_ids=list(light_entity_ids or []),
                shade_entity_ids=list(shade_entity_ids or []),
                speaker_entity_ids=list(speaker_entity_ids or []),
                dashboard_entity_ids=list(dashboard_entity_ids or []),
                other_entity_ids=list(other_entity_ids or []),
                weather_source_entity_ids=list(weather_source_entity_ids or []),
                news_source_entity_ids=list(news_source_entity_ids or []),
                created_at=now_iso,
                updated_at=now_iso,
            )
        else:
            if name is not None:
                current.name = name
            current.floor_id = floor_id
            if area_ids is not None:
                current.area_ids = list(area_ids)
            if primary_area is not None:
                current.primary_area = primary_area
            if enabled is not None:
                current.enabled = bool(enabled)
            if posture is not None:
                current.posture = posture
            if media_player_entity_ids is not None:
                current.media_player_entity_ids = list(media_player_entity_ids)
            if voice_device_entity_ids is not None:
                current.voice_device_entity_ids = list(voice_device_entity_ids)
            if tts_voice is not None:
                current.tts_voice = tts_voice
            if tts_language is not None:
                current.tts_language = tts_language
            if device_groups is not None:
                current.device_groups = list(device_groups)
            if persona is not None:
                current.persona = persona
            if persona_prompt is not None:
                current.persona_prompt = persona_prompt
            if ai_knowledge_enabled is not None:
                current.ai_knowledge_enabled = bool(ai_knowledge_enabled)
            if environment_information_outputs is not None:
                current.environment_information_outputs = list(environment_information_outputs)
            if asset_groups is not None:
                current.asset_groups = list(asset_groups)
            if room_sensor_entity_ids is not None:
                current.room_sensor_entity_ids = list(room_sensor_entity_ids)
            if room_health_entity_ids is not None:
                current.room_health_entity_ids = list(room_health_entity_ids)
            if human_health_entity_ids is not None:
                current.human_health_entity_ids = list(human_health_entity_ids)
            if light_entity_ids is not None:
                current.light_entity_ids = list(light_entity_ids)
            if shade_entity_ids is not None:
                current.shade_entity_ids = list(shade_entity_ids)
            if speaker_entity_ids is not None:
                current.speaker_entity_ids = list(speaker_entity_ids)
            if dashboard_entity_ids is not None:
                current.dashboard_entity_ids = list(dashboard_entity_ids)
            if other_entity_ids is not None:
                current.other_entity_ids = list(other_entity_ids)
            if weather_source_entity_ids is not None:
                current.weather_source_entity_ids = list(weather_source_entity_ids)
            if news_source_entity_ids is not None:
                current.news_source_entity_ids = list(news_source_entity_ids)
            if not current.created_at:
                current.created_at = now_iso
            current.updated_at = now_iso

        if current.primary_area is None and current.area_ids:
            current.primary_area = current.area_ids[0]

        state.composites[composite_id] = current
        await self.async_save_state(state)
        return state

    async def async_sync_composites(
        self,
        *,
        valid_area_ids: set[str],
        remove_invalid: bool = True,
    ) -> tuple[ConciergeState, list[str]]:
        """Validate and optionally remove invalid composite members.

        Returns updated state and validation errors.
        """
        state = await self.async_load_state()
        validation_errors: list[str] = []
        changed = False

        for composite_id in list(state.composites):
            composite = state.composites[composite_id]
            invalid = [area_id for area_id in composite.area_ids if area_id not in valid_area_ids]
            if invalid:
                validation_errors.append(
                    f"{composite_id}: invalid member areas {', '.join(sorted(invalid))}"
                )
                if remove_invalid:
                    composite.area_ids = [area_id for area_id in composite.area_ids if area_id in valid_area_ids]
                    if composite.primary_area not in composite.area_ids:
                        composite.primary_area = composite.area_ids[0] if composite.area_ids else None
                    composite.updated_at = _utcnow_iso()
                    changed = True

            if remove_invalid and not composite.area_ids:
                state.composites.pop(composite_id, None)
                changed = True

        if changed:
            await self.async_save_state(state)

        return state, validation_errors
