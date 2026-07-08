"""Contract-first state models for Concierge foundation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _normalize_asset_groups(value: Any, legacy_device_ids: Any = None) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    if not isinstance(value, list):
        value = []

    for item in value:
        if not isinstance(item, dict):
            continue
        group_name = str(item.get("group_name", "")).strip()
        device_ids = [str(device_id).strip() for device_id in item.get("device_ids", []) if str(device_id).strip()]
        if not group_name and not device_ids:
            continue
        groups.append({"group_name": group_name, "device_ids": device_ids})

    if not groups and isinstance(legacy_device_ids, list):
        legacy_ids = [str(device_id).strip() for device_id in legacy_device_ids if str(device_id).strip()]
        if legacy_ids:
            groups.append(
                {
                    "group_name": "",
                    "device_ids": legacy_ids,
                }
            )

    return groups


def _normalize_device_groups(value: Any) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    if not isinstance(value, list):
        return groups

    for item in value:
        if not isinstance(item, dict):
            continue
        group_name = str(item.get("group_name", "")).strip()
        entity_ids = [str(entity_id).strip() for entity_id in item.get("entity_ids", []) if str(entity_id).strip()]
        if not group_name and not entity_ids:
            continue
        groups.append({"group_name": group_name, "entity_ids": entity_ids})

    return groups


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
    tts_language: str = ""
    ai_knowledge_enabled: bool = False
    environment_information_outputs: list[str] = field(default_factory=list)
    device_groups: list[dict[str, Any]] = field(default_factory=list)
    asset_groups: list[dict[str, Any]] = field(default_factory=list)
    room_sensor_entity_ids: list[str] = field(default_factory=list)
    room_health_entity_ids: list[str] = field(default_factory=list)
    human_health_entity_ids: list[str] = field(default_factory=list)
    light_entity_ids: list[str] = field(default_factory=list)
    lamp_entity_ids: list[str] = field(default_factory=list)
    shade_entity_ids: list[str] = field(default_factory=list)
    speaker_entity_ids: list[str] = field(default_factory=list)
    tv_entity_ids: list[str] = field(default_factory=list)
    dashboard_entity_ids: list[str] = field(default_factory=list)
    other_entity_ids: list[str] = field(default_factory=list)
    weather_source_entity_ids: list[str] = field(default_factory=list)
    news_source_entity_ids: list[str] = field(default_factory=list)
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
class PersonProfile:
    """Person identity, consent, and device binding state."""

    person_id: str
    name: str
    linked_area_id: str | None = None
    ble_device_ids: list[str] = field(default_factory=list)
    aqara_presence_entity_ids: list[str] = field(default_factory=list)
    voice_profile_id: str | None = None
    consent: dict[str, Any] = field(default_factory=dict)
    mobile_notify_targets: list[str] = field(default_factory=list)
    preferred_mobile_target: str | None = None
    mobile_voice_endpoint_enabled: bool = False
    is_minor: bool = False
    guardian_controls_required: bool = False
    minor_allow_general_qna: bool = False
    minor_allowed_intent_classes: list[str] = field(default_factory=list)
    minor_content_filter_level: str = "strict"
    notes: str = ""


@dataclass(slots=True)
class VoiceProfile:
    """Voice enrollment and speaker attribution state."""

    voice_profile_id: str
    name: str
    tts_voice: str = ""
    enrollment_state: str = "untrained"
    enrollment_source: str = ""
    speaker_embedding_id: str = ""
    sample_count: int = 0
    sample_items: list[dict[str, Any]] = field(default_factory=list)
    attribution_confidence: float | None = None
    enrollment_started_at: str = ""
    last_sample_at: str = ""
    last_built_at: str = ""
    disabled: bool = False
    consent: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EnrollmentSession:
    """Enrollment session scaffolding state for deterministic lifecycle ownership."""

    session_id: str
    person_id: str
    voice_profile_id: str
    state: str
    created_at: str
    updated_at: str
    sample_count: int = 0
    sample_items: list[dict[str, Any]] = field(default_factory=list)
    enrollment_started_at: str = ""
    last_sample_at: str = ""
    last_built_at: str = ""
    cleanup_status: str = "not_started"
    capture_provider: str = "browser_microphone"
    last_error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


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
class ActivityEvent:
    """Stitched orchestration activity event record."""

    activity_id: str
    correlation_id: str
    started_at: str
    channel: str
    actor_class: str
    intent_class: str
    request_summary: str
    resolved_person_id: str | None = None
    resolved_area_id: str | None = None
    confidence: float | None = None
    external_refs: list[dict[str, Any]] = field(default_factory=list)
    ended_at: str | None = None
    outcome: str | None = None
    outcome_reason: str = ""
    actions_taken: list[str] = field(default_factory=list)
    policy_gates: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CompositeConfig:
    """Merged-room (composite) configuration."""

    composite_id: str
    name: str
    floor_id: str | None = None
    area_ids: list[str] = field(default_factory=list)
    primary_area: str | None = None
    enabled: bool = True
    posture: str = "day"
    media_player_entity_ids: list[str] = field(default_factory=list)
    voice_device_entity_ids: list[str] = field(default_factory=list)
    tts_voice: str = ""
    tts_language: str = ""
    device_groups: list[dict[str, Any]] = field(default_factory=list)
    persona: str = ""
    persona_prompt: str = ""
    ai_knowledge_enabled: bool = False
    environment_information_outputs: list[str] = field(default_factory=list)
    asset_groups: list[dict[str, Any]] = field(default_factory=list)
    room_sensor_entity_ids: list[str] = field(default_factory=list)
    room_health_entity_ids: list[str] = field(default_factory=list)
    human_health_entity_ids: list[str] = field(default_factory=list)
    light_entity_ids: list[str] = field(default_factory=list)
    shade_entity_ids: list[str] = field(default_factory=list)
    speaker_entity_ids: list[str] = field(default_factory=list)
    dashboard_entity_ids: list[str] = field(default_factory=list)
    other_entity_ids: list[str] = field(default_factory=list)
    weather_source_entity_ids: list[str] = field(default_factory=list)
    news_source_entity_ids: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class ConciergeState:
    """Persisted Concierge foundation state."""

    rooms: dict[str, RoomConfig] = field(default_factory=dict)
    composites: dict[str, CompositeConfig] = field(default_factory=dict)
    interactions: dict[str, Interaction] = field(default_factory=dict)
    global_context_usage: dict[str, dict[str, Any]] = field(default_factory=dict)
    execution_preferences: dict[str, dict[str, Any]] = field(default_factory=dict)
    signals: dict[str, SignalState] = field(default_factory=dict)
    contexts: dict[str, ContextState] = field(default_factory=dict)
    activities: dict[str, ActivityEvent] = field(default_factory=dict)
    default_person_profile: PersonProfile | None = None
    person_profiles: dict[str, PersonProfile] = field(default_factory=dict)
    default_voice_profile: VoiceProfile | None = None
    voice_profiles: dict[str, VoiceProfile] = field(default_factory=dict)
    enrollment_sessions: dict[str, EnrollmentSession] = field(default_factory=dict)
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
                    "tts_language": room.tts_language,
                    "ai_knowledge_enabled": room.ai_knowledge_enabled,
                    "environment_information_outputs": room.environment_information_outputs,
                    "device_groups": room.device_groups,
                    "asset_groups": room.asset_groups,
                    "room_sensor_entity_ids": room.room_sensor_entity_ids,
                    "room_health_entity_ids": room.room_health_entity_ids,
                    "human_health_entity_ids": room.human_health_entity_ids,
                    "light_entity_ids": room.light_entity_ids,
                    "lamp_entity_ids": room.lamp_entity_ids,
                    "shade_entity_ids": room.shade_entity_ids,
                    "speaker_entity_ids": room.speaker_entity_ids,
                    "tv_entity_ids": room.tv_entity_ids,
                    "dashboard_entity_ids": room.dashboard_entity_ids,
                    "other_entity_ids": room.other_entity_ids,
                    "weather_source_entity_ids": room.weather_source_entity_ids,
                    "news_source_entity_ids": room.news_source_entity_ids,
                    "persona": room.persona,
                    "persona_prompt": room.persona_prompt,
                }
                for area_id, room in self.rooms.items()
            },
            "composites": {
                composite_id: {
                    "composite_id": composite.composite_id,
                    "name": composite.name,
                    "floor_id": composite.floor_id,
                    "area_ids": composite.area_ids,
                    "primary_area": composite.primary_area,
                    "enabled": composite.enabled,
                    "posture": composite.posture,
                    "media_player_entity_ids": composite.media_player_entity_ids,
                    "voice_device_entity_ids": composite.voice_device_entity_ids,
                    "tts_voice": composite.tts_voice,
                    "tts_language": composite.tts_language,
                    "device_groups": composite.device_groups,
                    "persona": composite.persona,
                    "persona_prompt": composite.persona_prompt,
                    "ai_knowledge_enabled": composite.ai_knowledge_enabled,
                    "environment_information_outputs": composite.environment_information_outputs,
                    "asset_groups": composite.asset_groups,
                    "room_sensor_entity_ids": composite.room_sensor_entity_ids,
                    "room_health_entity_ids": composite.room_health_entity_ids,
                    "human_health_entity_ids": composite.human_health_entity_ids,
                    "light_entity_ids": composite.light_entity_ids,
                    "shade_entity_ids": composite.shade_entity_ids,
                    "speaker_entity_ids": composite.speaker_entity_ids,
                    "dashboard_entity_ids": composite.dashboard_entity_ids,
                    "other_entity_ids": composite.other_entity_ids,
                    "weather_source_entity_ids": composite.weather_source_entity_ids,
                    "news_source_entity_ids": composite.news_source_entity_ids,
                    "created_at": composite.created_at,
                    "updated_at": composite.updated_at,
                }
                for composite_id, composite in self.composites.items()
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
            "default_person_profile": (
                {
                    "person_id": self.default_person_profile.person_id,
                    "name": self.default_person_profile.name,
                    "linked_area_id": self.default_person_profile.linked_area_id,
                    "ble_device_ids": self.default_person_profile.ble_device_ids,
                    "aqara_presence_entity_ids": self.default_person_profile.aqara_presence_entity_ids,
                    "voice_profile_id": self.default_person_profile.voice_profile_id,
                    "consent": self.default_person_profile.consent,
                    "mobile_notify_targets": self.default_person_profile.mobile_notify_targets,
                    "preferred_mobile_target": self.default_person_profile.preferred_mobile_target,
                    "mobile_voice_endpoint_enabled": self.default_person_profile.mobile_voice_endpoint_enabled,
                    "is_minor": self.default_person_profile.is_minor,
                    "guardian_controls_required": self.default_person_profile.guardian_controls_required,
                    "minor_allow_general_qna": self.default_person_profile.minor_allow_general_qna,
                    "minor_allowed_intent_classes": self.default_person_profile.minor_allowed_intent_classes,
                    "minor_content_filter_level": self.default_person_profile.minor_content_filter_level,
                    "notes": self.default_person_profile.notes,
                }
                if self.default_person_profile is not None
                else None
            ),
            "person_profiles": {
                person_id: {
                    "person_id": profile.person_id,
                    "name": profile.name,
                    "linked_area_id": profile.linked_area_id,
                    "ble_device_ids": profile.ble_device_ids,
                    "aqara_presence_entity_ids": profile.aqara_presence_entity_ids,
                    "voice_profile_id": profile.voice_profile_id,
                    "consent": profile.consent,
                    "mobile_notify_targets": profile.mobile_notify_targets,
                    "preferred_mobile_target": profile.preferred_mobile_target,
                    "mobile_voice_endpoint_enabled": profile.mobile_voice_endpoint_enabled,
                    "is_minor": profile.is_minor,
                    "guardian_controls_required": profile.guardian_controls_required,
                    "minor_allow_general_qna": profile.minor_allow_general_qna,
                    "minor_allowed_intent_classes": profile.minor_allowed_intent_classes,
                    "minor_content_filter_level": profile.minor_content_filter_level,
                    "notes": profile.notes,
                }
                for person_id, profile in self.person_profiles.items()
            },
            "activities": {
                activity_id: {
                    "activity_id": activity.activity_id,
                    "correlation_id": activity.correlation_id,
                    "started_at": activity.started_at,
                    "channel": activity.channel,
                    "actor_class": activity.actor_class,
                    "intent_class": activity.intent_class,
                    "request_summary": activity.request_summary,
                    "resolved_person_id": activity.resolved_person_id,
                    "resolved_area_id": activity.resolved_area_id,
                    "confidence": activity.confidence,
                    "external_refs": activity.external_refs,
                    "ended_at": activity.ended_at,
                    "outcome": activity.outcome,
                    "outcome_reason": activity.outcome_reason,
                    "actions_taken": activity.actions_taken,
                    "policy_gates": activity.policy_gates,
                }
                for activity_id, activity in self.activities.items()
            },
            "default_voice_profile": (
                {
                    "voice_profile_id": self.default_voice_profile.voice_profile_id,
                    "name": self.default_voice_profile.name,
                    "tts_voice": self.default_voice_profile.tts_voice,
                    "enrollment_state": self.default_voice_profile.enrollment_state,
                    "enrollment_source": self.default_voice_profile.enrollment_source,
                    "speaker_embedding_id": self.default_voice_profile.speaker_embedding_id,
                    "sample_count": self.default_voice_profile.sample_count,
                    "sample_items": self.default_voice_profile.sample_items,
                    "attribution_confidence": self.default_voice_profile.attribution_confidence,
                    "enrollment_started_at": self.default_voice_profile.enrollment_started_at,
                    "last_sample_at": self.default_voice_profile.last_sample_at,
                    "last_built_at": self.default_voice_profile.last_built_at,
                    "disabled": self.default_voice_profile.disabled,
                    "consent": self.default_voice_profile.consent,
                }
                if self.default_voice_profile is not None
                else None
            ),
            "voice_profiles": {
                voice_profile_id: {
                    "voice_profile_id": profile.voice_profile_id,
                    "name": profile.name,
                    "tts_voice": profile.tts_voice,
                    "enrollment_state": profile.enrollment_state,
                    "enrollment_source": profile.enrollment_source,
                    "speaker_embedding_id": profile.speaker_embedding_id,
                    "sample_count": profile.sample_count,
                    "sample_items": profile.sample_items,
                    "attribution_confidence": profile.attribution_confidence,
                    "enrollment_started_at": profile.enrollment_started_at,
                    "last_sample_at": profile.last_sample_at,
                    "last_built_at": profile.last_built_at,
                    "disabled": profile.disabled,
                    "consent": profile.consent,
                }
                for voice_profile_id, profile in self.voice_profiles.items()
            },
            "enrollment_sessions": {
                session_id: {
                    "session_id": session.session_id,
                    "person_id": session.person_id,
                    "voice_profile_id": session.voice_profile_id,
                    "state": session.state,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "sample_count": session.sample_count,
                    "sample_items": session.sample_items,
                    "enrollment_started_at": session.enrollment_started_at,
                    "last_sample_at": session.last_sample_at,
                    "last_built_at": session.last_built_at,
                    "cleanup_status": session.cleanup_status,
                    "capture_provider": session.capture_provider,
                    "last_error": session.last_error,
                    "metadata": session.metadata,
                }
                for session_id, session in self.enrollment_sessions.items()
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
        composites_data = data.get("composites", {})
        interactions_data = data.get("interactions", {})
        signals_data = data.get("signals", {})
        contexts_data = data.get("contexts", {})
        activities_data = data.get("activities", {})
        default_person_data = data.get("default_person_profile")
        person_profiles_data = data.get("person_profiles", {})
        default_voice_data = data.get("default_voice_profile")
        voice_profiles_data = data.get("voice_profiles", {})
        enrollment_sessions_data = data.get("enrollment_sessions", {})
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
                    tts_language=payload.get("tts_language", ""),
                    ai_knowledge_enabled=bool(payload.get("ai_knowledge_enabled", False)),
                    environment_information_outputs=list(payload.get("environment_information_outputs", [])),
                    device_groups=_normalize_device_groups(payload.get("device_groups", [])),
                    asset_groups=_normalize_asset_groups(payload.get("asset_groups", []), payload.get("asset_entity_ids", [])),
                    room_sensor_entity_ids=list(payload.get("room_sensor_entity_ids", [])),
                    room_health_entity_ids=list(payload.get("room_health_entity_ids", [])),
                    human_health_entity_ids=list(payload.get("human_health_entity_ids", [])),
                    light_entity_ids=list(payload.get("light_entity_ids", [])),
                    lamp_entity_ids=list(payload.get("lamp_entity_ids", [])),
                    shade_entity_ids=list(payload.get("shade_entity_ids", [])),
                    speaker_entity_ids=list(payload.get("speaker_entity_ids", [])),
                    tv_entity_ids=list(payload.get("tv_entity_ids", [])),
                    dashboard_entity_ids=list(payload.get("dashboard_entity_ids", [])),
                    other_entity_ids=list(payload.get("other_entity_ids", [])),
                    weather_source_entity_ids=list(payload.get("weather_source_entity_ids", [])),
                    news_source_entity_ids=list(payload.get("news_source_entity_ids", [])),
                    persona=payload.get("persona", ""),
                    persona_prompt=payload.get("persona_prompt", ""),
                )
                for area_id, payload in rooms_data.items()
                if isinstance(payload, dict)
            },
            composites={
                composite_id: CompositeConfig(
                    composite_id=payload.get("composite_id", composite_id),
                    name=payload.get("name", composite_id),
                    floor_id=payload.get("floor_id"),
                    area_ids=list(payload.get("area_ids", [])),
                    primary_area=payload.get("primary_area"),
                    enabled=bool(payload.get("enabled", True)),
                    posture=payload.get("posture", "day"),
                    media_player_entity_ids=list(payload.get("media_player_entity_ids", [])),
                    voice_device_entity_ids=list(payload.get("voice_device_entity_ids", [])),
                    tts_voice=payload.get("tts_voice", ""),
                    tts_language=payload.get("tts_language", ""),
                    device_groups=_normalize_device_groups(payload.get("device_groups", [])),
                    persona=payload.get("persona", ""),
                    persona_prompt=payload.get("persona_prompt", ""),
                    ai_knowledge_enabled=bool(payload.get("ai_knowledge_enabled", False)),
                    environment_information_outputs=list(payload.get("environment_information_outputs", [])),
                    asset_groups=_normalize_asset_groups(payload.get("asset_groups", []), payload.get("asset_entity_ids", [])),
                    room_sensor_entity_ids=list(payload.get("room_sensor_entity_ids", [])),
                    room_health_entity_ids=list(payload.get("room_health_entity_ids", [])),
                    human_health_entity_ids=list(payload.get("human_health_entity_ids", [])),
                    light_entity_ids=list(payload.get("light_entity_ids", [])),
                    shade_entity_ids=list(payload.get("shade_entity_ids", [])),
                    speaker_entity_ids=list(payload.get("speaker_entity_ids", [])),
                    dashboard_entity_ids=list(payload.get("dashboard_entity_ids", [])),
                    other_entity_ids=list(payload.get("other_entity_ids", [])),
                    weather_source_entity_ids=list(payload.get("weather_source_entity_ids", [])),
                    news_source_entity_ids=list(payload.get("news_source_entity_ids", [])),
                    created_at=payload.get("created_at", ""),
                    updated_at=payload.get("updated_at", ""),
                )
                for composite_id, payload in composites_data.items()
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
            default_person_profile=(
                PersonProfile(
                    person_id=default_person_data.get("person_id", "default"),
                    name=default_person_data.get("name", "Default Person"),
                    linked_area_id=default_person_data.get("linked_area_id"),
                    ble_device_ids=list(default_person_data.get("ble_device_ids", [])),
                    aqara_presence_entity_ids=list(default_person_data.get("aqara_presence_entity_ids", [])),
                    voice_profile_id=default_person_data.get("voice_profile_id"),
                    consent=dict(default_person_data.get("consent", {})),
                    mobile_notify_targets=list(default_person_data.get("mobile_notify_targets", [])),
                    preferred_mobile_target=default_person_data.get("preferred_mobile_target"),
                    mobile_voice_endpoint_enabled=bool(
                        default_person_data.get("mobile_voice_endpoint_enabled", False)
                    ),
                    is_minor=bool(default_person_data.get("is_minor", False)),
                    guardian_controls_required=bool(
                        default_person_data.get("guardian_controls_required", False)
                    ),
                    minor_allow_general_qna=bool(
                        default_person_data.get("minor_allow_general_qna", False)
                    ),
                    minor_allowed_intent_classes=list(
                        default_person_data.get("minor_allowed_intent_classes", [])
                    ),
                    minor_content_filter_level=default_person_data.get(
                        "minor_content_filter_level", "strict"
                    ),
                    notes=default_person_data.get("notes", ""),
                )
                if isinstance(default_person_data, dict)
                else None
            ),
            person_profiles={
                person_id: PersonProfile(
                    person_id=payload.get("person_id", person_id),
                    name=payload.get("name", ""),
                    linked_area_id=payload.get("linked_area_id"),
                    ble_device_ids=list(payload.get("ble_device_ids", [])),
                    aqara_presence_entity_ids=list(payload.get("aqara_presence_entity_ids", [])),
                    voice_profile_id=payload.get("voice_profile_id"),
                    consent=dict(payload.get("consent", {})),
                    mobile_notify_targets=list(payload.get("mobile_notify_targets", [])),
                    preferred_mobile_target=payload.get("preferred_mobile_target"),
                    mobile_voice_endpoint_enabled=bool(payload.get("mobile_voice_endpoint_enabled", False)),
                    is_minor=bool(payload.get("is_minor", False)),
                    guardian_controls_required=bool(payload.get("guardian_controls_required", False)),
                    minor_allow_general_qna=bool(payload.get("minor_allow_general_qna", False)),
                    minor_allowed_intent_classes=list(payload.get("minor_allowed_intent_classes", [])),
                    minor_content_filter_level=payload.get("minor_content_filter_level", "strict"),
                    notes=payload.get("notes", ""),
                )
                for person_id, payload in person_profiles_data.items()
                if isinstance(payload, dict)
            },
            activities={
                activity_id: ActivityEvent(
                    activity_id=payload.get("activity_id", activity_id),
                    correlation_id=payload.get("correlation_id", ""),
                    started_at=payload.get("started_at", ""),
                    channel=payload.get("channel", "unknown"),
                    actor_class=payload.get("actor_class", "unknown"),
                    intent_class=payload.get("intent_class", "unknown"),
                    request_summary=payload.get("request_summary", ""),
                    resolved_person_id=payload.get("resolved_person_id"),
                    resolved_area_id=payload.get("resolved_area_id"),
                    confidence=(
                        float(payload["confidence"])
                        if payload.get("confidence") is not None
                        else None
                    ),
                    external_refs=list(payload.get("external_refs", [])),
                    ended_at=payload.get("ended_at"),
                    outcome=payload.get("outcome"),
                    outcome_reason=payload.get("outcome_reason", ""),
                    actions_taken=list(payload.get("actions_taken", [])),
                    policy_gates=list(payload.get("policy_gates", [])),
                )
                for activity_id, payload in activities_data.items()
                if isinstance(payload, dict)
            },
            default_voice_profile=(
                VoiceProfile(
                    voice_profile_id=default_voice_data.get("voice_profile_id", "default"),
                    name=default_voice_data.get("name", "Default Voice"),
                    tts_voice=default_voice_data.get("tts_voice", ""),
                    enrollment_state=default_voice_data.get("enrollment_state", "untrained"),
                    enrollment_source=default_voice_data.get("enrollment_source", ""),
                    speaker_embedding_id=default_voice_data.get("speaker_embedding_id", ""),
                    sample_count=int(default_voice_data.get("sample_count", 0)),
                    sample_items=list(default_voice_data.get("sample_items", [])),
                    attribution_confidence=(
                        float(default_voice_data["attribution_confidence"])
                        if default_voice_data.get("attribution_confidence") is not None
                        else None
                    ),
                    enrollment_started_at=default_voice_data.get("enrollment_started_at", ""),
                    last_sample_at=default_voice_data.get("last_sample_at", ""),
                    last_built_at=default_voice_data.get("last_built_at", ""),
                    disabled=bool(default_voice_data.get("disabled", False)),
                    consent=dict(default_voice_data.get("consent", {})),
                )
                if isinstance(default_voice_data, dict)
                else None
            ),
            voice_profiles={
                voice_profile_id: VoiceProfile(
                    voice_profile_id=payload.get("voice_profile_id", voice_profile_id),
                    name=payload.get("name", ""),
                    tts_voice=payload.get("tts_voice", ""),
                    enrollment_state=payload.get("enrollment_state", "untrained"),
                    enrollment_source=payload.get("enrollment_source", ""),
                    speaker_embedding_id=payload.get("speaker_embedding_id", ""),
                    sample_count=int(payload.get("sample_count", 0)),
                    sample_items=list(payload.get("sample_items", [])),
                    attribution_confidence=(
                        float(payload["attribution_confidence"])
                        if payload.get("attribution_confidence") is not None
                        else None
                    ),
                    enrollment_started_at=payload.get("enrollment_started_at", ""),
                    last_sample_at=payload.get("last_sample_at", ""),
                    last_built_at=payload.get("last_built_at", ""),
                    disabled=bool(payload.get("disabled", False)),
                    consent=dict(payload.get("consent", {})),
                )
                for voice_profile_id, payload in voice_profiles_data.items()
                if isinstance(payload, dict)
            },
            enrollment_sessions={
                session_id: EnrollmentSession(
                    session_id=payload.get("session_id", session_id),
                    person_id=payload.get("person_id", ""),
                    voice_profile_id=payload.get("voice_profile_id", ""),
                    state=payload.get("state", "idle"),
                    created_at=payload.get("created_at", ""),
                    updated_at=payload.get("updated_at", ""),
                    sample_count=int(payload.get("sample_count", 0)),
                    sample_items=list(payload.get("sample_items", [])),
                    enrollment_started_at=payload.get("enrollment_started_at", ""),
                    last_sample_at=payload.get("last_sample_at", ""),
                    last_built_at=payload.get("last_built_at", ""),
                    cleanup_status=payload.get("cleanup_status", "not_started"),
                    capture_provider=payload.get("capture_provider", "browser_microphone"),
                    last_error=payload.get("last_error", ""),
                    metadata=dict(payload.get("metadata", {})),
                )
                for session_id, payload in enrollment_sessions_data.items()
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
