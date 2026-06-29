"""Contract-first state models for Concierge foundation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RoomConfig:
    """Room-scoped configuration and alias mappings."""

    area_id: str
    aliases: dict[str, str] = field(default_factory=dict)
    global_overlays: dict[str, bool] = field(default_factory=dict)
    posture: str = "day"
    media_player_entity_ids: list[str] = field(default_factory=list)
    voice_device_entity_ids: list[str] = field(default_factory=list)
    tts_voice: str = ""
    asset_entity_ids: list[str] = field(default_factory=list)
    room_sensor_entity_ids: list[str] = field(default_factory=list)
    room_health_entity_ids: list[str] = field(default_factory=list)
    human_health_entity_ids: list[str] = field(default_factory=list)
    light_entity_ids: list[str] = field(default_factory=list)
    shade_entity_ids: list[str] = field(default_factory=list)
    speaker_entity_ids: list[str] = field(default_factory=list)
    dashboard_entity_ids: list[str] = field(default_factory=list)
    other_entity_ids: list[str] = field(default_factory=list)
    persona: str = ""
    persona_prompt: str = ""


@dataclass(slots=True)
class IdentityProfile:
    """Identity-specific presentation preferences."""

    profile_id: str
    name: str
    persona: str
    tts_voice: str
    verbosity: str
    allow_ai: bool
    content_type: str
    detail_level: str


@dataclass(slots=True)
class Interaction:
    """Runtime interaction surfaced to UI/voice channels."""

    interaction_id: str
    area_id: str | None
    message: str
    level: str
    state: str
    priority: int


@dataclass(slots=True)
class SignalState:
    """Signal payload exposed by provider integrations."""

    signal_type: str
    available: bool
    summary: str
    state: str


@dataclass(slots=True)
class ContextState:
    """Global context payload exposed by provider integrations."""

    context_type: str
    available: bool
    summary: str
    detail: str
    speakable: str


@dataclass(slots=True)
class ConciergeState:
    """Persisted Concierge foundation state."""

    rooms: dict[str, RoomConfig] = field(default_factory=dict)
    interactions: dict[str, Interaction] = field(default_factory=dict)
    global_context_usage: dict[str, dict[str, Any]] = field(default_factory=dict)
    execution_preferences: dict[str, dict[str, Any]] = field(default_factory=dict)
    signals: dict[str, SignalState] = field(default_factory=dict)
    contexts: dict[str, ContextState] = field(default_factory=dict)
    default_identity_profile: IdentityProfile | None = None
    identity_profiles: dict[str, IdentityProfile] = field(default_factory=dict)
    global_features: dict[str, dict[str, Any]] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Serialize state for Home Assistant storage."""
        return {
            "rooms": {
                area_id: {
                    "area_id": room.area_id,
                    "aliases": room.aliases,
                    "global_overlays": room.global_overlays,
                    "posture": room.posture,
                    "media_player_entity_ids": room.media_player_entity_ids,
                    "voice_device_entity_ids": room.voice_device_entity_ids,
                    "tts_voice": room.tts_voice,
                    "asset_entity_ids": room.asset_entity_ids,
                    "room_sensor_entity_ids": room.room_sensor_entity_ids,
                    "room_health_entity_ids": room.room_health_entity_ids,
                    "human_health_entity_ids": room.human_health_entity_ids,
                    "light_entity_ids": room.light_entity_ids,
                    "shade_entity_ids": room.shade_entity_ids,
                    "speaker_entity_ids": room.speaker_entity_ids,
                    "dashboard_entity_ids": room.dashboard_entity_ids,
                    "other_entity_ids": room.other_entity_ids,
                    "persona": room.persona,
                    "persona_prompt": room.persona_prompt,
                }
                for area_id, room in self.rooms.items()
            },
            "interactions": {
                interaction_id: {
                    "interaction_id": interaction.interaction_id,
                    "area_id": interaction.area_id,
                    "message": interaction.message,
                    "level": interaction.level,
                    "state": interaction.state,
                    "priority": interaction.priority,
                }
                for interaction_id, interaction in self.interactions.items()
            },
            "global_context_usage": self.global_context_usage,
            "execution_preferences": self.execution_preferences,
            "signals": {
                signal_type: {
                    "signal_type": signal.signal_type,
                    "available": signal.available,
                    "summary": signal.summary,
                    "state": signal.state,
                }
                for signal_type, signal in self.signals.items()
            },
            "contexts": {
                context_type: {
                    "context_type": context.context_type,
                    "available": context.available,
                    "summary": context.summary,
                    "detail": context.detail,
                    "speakable": context.speakable,
                }
                for context_type, context in self.contexts.items()
            },
            "default_identity_profile": (
                {
                    "profile_id": self.default_identity_profile.profile_id,
                    "name": self.default_identity_profile.name,
                    "persona": self.default_identity_profile.persona,
                    "tts_voice": self.default_identity_profile.tts_voice,
                    "verbosity": self.default_identity_profile.verbosity,
                    "allow_ai": self.default_identity_profile.allow_ai,
                    "content_type": self.default_identity_profile.content_type,
                    "detail_level": self.default_identity_profile.detail_level,
                }
                if self.default_identity_profile is not None
                else None
            ),
            "identity_profiles": {
                profile_id: {
                    "profile_id": profile.profile_id,
                    "name": profile.name,
                    "persona": profile.persona,
                    "tts_voice": profile.tts_voice,
                    "verbosity": profile.verbosity,
                    "allow_ai": profile.allow_ai,
                    "content_type": profile.content_type,
                    "detail_level": profile.detail_level,
                }
                for profile_id, profile in self.identity_profiles.items()
            },
            "global_features": self.global_features,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConciergeState:
        """Deserialize state from Home Assistant storage."""
        rooms_data = data.get("rooms", {})
        interactions_data = data.get("interactions", {})
        signals_data = data.get("signals", {})
        contexts_data = data.get("contexts", {})
        default_identity_data = data.get("default_identity_profile")
        identity_profiles_data = data.get("identity_profiles", {})

        return cls(
            rooms={
                area_id: RoomConfig(
                    area_id=payload.get("area_id", area_id),
                    aliases=dict(payload.get("aliases", {})),
                    global_overlays=dict(payload.get("global_overlays", {})),
                    posture=payload.get("posture", "day"),
                    media_player_entity_ids=list(payload.get("media_player_entity_ids", [])),
                    voice_device_entity_ids=list(payload.get("voice_device_entity_ids", [])),
                    tts_voice=payload.get("tts_voice", ""),
                    asset_entity_ids=list(payload.get("asset_entity_ids", [])),
                    room_sensor_entity_ids=list(payload.get("room_sensor_entity_ids", [])),
                    room_health_entity_ids=list(payload.get("room_health_entity_ids", [])),
                    human_health_entity_ids=list(payload.get("human_health_entity_ids", [])),
                    light_entity_ids=list(payload.get("light_entity_ids", [])),
                    shade_entity_ids=list(payload.get("shade_entity_ids", [])),
                    speaker_entity_ids=list(payload.get("speaker_entity_ids", [])),
                    dashboard_entity_ids=list(payload.get("dashboard_entity_ids", [])),
                    other_entity_ids=list(payload.get("other_entity_ids", [])),
                    persona=payload.get("persona", ""),
                    persona_prompt=payload.get("persona_prompt", ""),
                )
                for area_id, payload in rooms_data.items()
                if isinstance(payload, dict)
            },
            interactions={
                interaction_id: Interaction(
                    interaction_id=payload.get("interaction_id", interaction_id),
                    area_id=payload.get("area_id"),
                    message=payload.get("message", ""),
                    level=payload.get("level", "info"),
                    state=payload.get("state", "active"),
                    priority=int(payload.get("priority", 0)),
                )
                for interaction_id, payload in interactions_data.items()
                if isinstance(payload, dict)
            },
            global_context_usage=dict(data.get("global_context_usage", {})),
            execution_preferences=dict(data.get("execution_preferences", {})),
            signals={
                signal_type: SignalState(
                    signal_type=payload.get("signal_type", signal_type),
                    available=bool(payload.get("available", False)),
                    summary=payload.get("summary", ""),
                    state=payload.get("state", "unknown"),
                )
                for signal_type, payload in signals_data.items()
                if isinstance(payload, dict)
            },
            contexts={
                context_type: ContextState(
                    context_type=payload.get("context_type", context_type),
                    available=bool(payload.get("available", False)),
                    summary=payload.get("summary", ""),
                    detail=payload.get("detail", ""),
                    speakable=payload.get("speakable", ""),
                )
                for context_type, payload in contexts_data.items()
                if isinstance(payload, dict)
            },
            default_identity_profile=(
                IdentityProfile(
                    profile_id=default_identity_data.get("profile_id", "default"),
                    name=default_identity_data.get("name", "Default"),
                    persona=default_identity_data.get("persona", "concise"),
                    tts_voice=default_identity_data.get("tts_voice", ""),
                    verbosity=default_identity_data.get("verbosity", "standard"),
                    allow_ai=bool(default_identity_data.get("allow_ai", True)),
                    content_type=default_identity_data.get("content_type", "general"),
                    detail_level=default_identity_data.get("detail_level", "medium"),
                )
                if isinstance(default_identity_data, dict)
                else None
            ),
            identity_profiles={
                profile_id: IdentityProfile(
                    profile_id=payload.get("profile_id", profile_id),
                    name=payload.get("name", ""),
                    persona=payload.get("persona", "concise"),
                    tts_voice=payload.get("tts_voice", ""),
                    verbosity=payload.get("verbosity", "standard"),
                    allow_ai=bool(payload.get("allow_ai", True)),
                    content_type=payload.get("content_type", "general"),
                    detail_level=payload.get("detail_level", "medium"),
                )
                for profile_id, payload in identity_profiles_data.items()
                if isinstance(payload, dict)
            },
            global_features=dict(data.get("global_features", {})),
        )
