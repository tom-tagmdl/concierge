"""Contract-first service handlers for Concierge orchestration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import floor_registry as fr
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse

from .const import (
    DOMAIN,
    EVENT_EXECUTION,
    SERVICE_CLEAR_INTERACTION,
    SERVICE_EXECUTE,
    SERVICE_EXECUTE_DIRECT,
    SERVICE_GET_CONTEXT,
    SERVICE_GET_INTERACTIONS,
    SERVICE_GET_SIGNAL,
    SERVICE_GET_SIGNALS,
    SERVICE_GET_SUMMARY,
    SERVICE_PREVIEW_TTS_VOICE,
    SERVICE_REFRESH_ENTITY_STRUCTURE,
    SERVICE_SYNC_ROOMS,
    SERVICE_SYNC_COMPOSITES,
    SERVICE_UPDATE_COMPOSITE_CONFIG,
    SERVICE_UPDATE_IDENTITY_PROFILE,
    SERVICE_UPDATE_EXECUTION_PREFERENCES,
    SERVICE_UPDATE_GLOBAL_CONTEXT,
    SERVICE_UPDATE_PERSON_PROFILE,
    SERVICE_UPDATE_INTERACTION,
    SERVICE_UPDATE_ROOM_CONFIG,
    SERVICE_UPDATE_VOICE_PROFILE,
)
from .models import ContextState, IdentityProfile, Interaction, PersonProfile, SignalState, VoiceProfile
from .storage import ConciergeStorage

SERVICE_EXECUTE_SCHEMA = vol.Schema(
    {
        vol.Required("target"): str,
        vol.Optional("area_id"): str,
        vol.Optional("composite_id"): str,
        vol.Optional("context"): dict,
    }
)

SERVICE_EXECUTE_DIRECT_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): str,
        vol.Required("service"): str,
        vol.Optional("data"): dict,
    }
)

SERVICE_GET_INTERACTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional("area_id"): str,
        vol.Optional("composite_id"): str,
    }
)

SERVICE_UPDATE_INTERACTION_SCHEMA = vol.Schema(
    {
        vol.Required("interaction_id"): str,
        vol.Optional("area_id"): str,
        vol.Required("message"): str,
        vol.Optional("level", default="info"): str,
        vol.Optional("state", default="active"): str,
        vol.Optional("priority", default=0): int,
    }
)

SERVICE_CLEAR_INTERACTION_SCHEMA = vol.Schema({vol.Required("interaction_id"): str})
SERVICE_GET_SIGNAL_SCHEMA = vol.Schema({vol.Required("signal_type"): str})
SERVICE_GET_SIGNALS_SCHEMA = vol.Schema(
    {
        vol.Optional("area_id"): str,
        vol.Optional("composite_id"): str,
    }
)
SERVICE_UPDATE_ROOM_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required("area_id"): str,
        vol.Optional("aliases"): dict,
        vol.Optional("global_overlays"): dict,
        vol.Optional("posture"): str,
        vol.Optional("media_player_entity_ids"): vol.All(list, [str]),
        vol.Optional("voice_device_entity_ids"): vol.All(list, [str]),
        vol.Optional("tts_voice"): str,
        vol.Optional("asset_entity_ids"): vol.All(list, [str]),
        vol.Optional("room_sensor_entity_ids"): vol.All(list, [str]),
        vol.Optional("room_health_entity_ids"): vol.All(list, [str]),
        vol.Optional("human_health_entity_ids"): vol.All(list, [str]),
        vol.Optional("light_entity_ids"): vol.All(list, [str]),
        vol.Optional("shade_entity_ids"): vol.All(list, [str]),
        vol.Optional("speaker_entity_ids"): vol.All(list, [str]),
        vol.Optional("dashboard_entity_ids"): vol.All(list, [str]),
        vol.Optional("other_entity_ids"): vol.All(list, [str]),
        vol.Optional("persona"): str,
        vol.Optional("persona_prompt"): str,
    }
)
SERVICE_UPDATE_GLOBAL_CONTEXT_SCHEMA = vol.Schema(
    {
        vol.Required("context_type"): str,
        vol.Required("enabled"): bool,
        vol.Optional("options"): dict,
        vol.Optional("summary"): str,
        vol.Optional("detail"): str,
        vol.Optional("speakable"): str,
    }
)
SERVICE_UPDATE_EXEC_PREFS_SCHEMA = vol.Schema(
    {
        vol.Required("scope_id"): str,
        vol.Required("preferences"): dict,
    }
)
SERVICE_UPDATE_COMPOSITE_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required("composite_id"): str,
        vol.Optional("name"): str,
        vol.Optional("area_ids"): vol.All(list, [str]),
        vol.Optional("primary_area"): str,
        vol.Optional("enabled"): bool,
        vol.Optional("media_player_entity_ids"): vol.All(list, [str]),
        vol.Optional("voice_device_entity_ids"): vol.All(list, [str]),
        vol.Optional("asset_entity_ids"): vol.All(list, [str]),
        vol.Optional("room_sensor_entity_ids"): vol.All(list, [str]),
        vol.Optional("room_health_entity_ids"): vol.All(list, [str]),
        vol.Optional("human_health_entity_ids"): vol.All(list, [str]),
        vol.Optional("light_entity_ids"): vol.All(list, [str]),
        vol.Optional("shade_entity_ids"): vol.All(list, [str]),
        vol.Optional("speaker_entity_ids"): vol.All(list, [str]),
        vol.Optional("dashboard_entity_ids"): vol.All(list, [str]),
        vol.Optional("other_entity_ids"): vol.All(list, [str]),
    }
)
SERVICE_SYNC_COMPOSITES_SCHEMA = vol.Schema(
    {
        vol.Optional("remove_invalid", default=True): bool,
    }
)
SERVICE_GET_CONTEXT_SCHEMA = vol.Schema({vol.Required("context_type"): str})
SERVICE_GET_SUMMARY_SCHEMA = vol.Schema(
    {
        vol.Optional("area_id"): str,
        vol.Optional("include_signals", default=True): bool,
        vol.Optional("include_context", default=True): bool,
    }
)
SERVICE_PREVIEW_TTS_VOICE_SCHEMA = vol.Schema(
    {
        vol.Required("provider"): str,
        vol.Required("media_player_entity_id"): vol.All(list, [str]),
        vol.Optional("voice"): str,
        vol.Optional(
            "message",
            default="Welcome to Concierge, where I will be able to help you in every room of your home",
        ): str,
    }
)
SERVICE_UPDATE_IDENTITY_PROFILE_SCHEMA = vol.Schema(
    {
        vol.Required("profile_id"): str,
        vol.Required("name"): str,
        vol.Optional("persona", default="concise"): str,
        vol.Optional("tts_voice", default=""): str,
        vol.Optional("verbosity", default="standard"): str,
        vol.Optional("allow_ai", default=True): bool,
        vol.Optional("content_type", default="general"): str,
        vol.Optional("detail_level", default="medium"): str,
        vol.Optional("set_as_default", default=False): bool,
    }
)
SERVICE_UPDATE_PERSON_PROFILE_SCHEMA = vol.Schema(
    {
        vol.Required("person_id"): str,
        vol.Required("name"): str,
        vol.Optional("linked_area_id"): str,
        vol.Optional("ble_device_ids", default=[]): vol.All(list, [str]),
        vol.Optional("aqara_presence_entity_ids", default=[]): vol.All(list, [str]),
        vol.Optional("voice_profile_id"): str,
        vol.Optional("consent", default={}): dict,
        vol.Optional("notes", default=""): str,
        vol.Optional("set_as_default", default=False): bool,
    }
)
SERVICE_UPDATE_VOICE_PROFILE_SCHEMA = vol.Schema(
    {
        vol.Required("voice_profile_id"): str,
        vol.Required("name"): str,
        vol.Optional("tts_voice", default=""): str,
        vol.Optional("enrollment_state", default="untrained"): str,
        vol.Optional("enrollment_source", default=""): str,
        vol.Optional("speaker_embedding_id", default=""): str,
        vol.Optional("sample_count", default=0): int,
        vol.Optional("consent", default={}): dict,
        vol.Optional("set_as_default", default=False): bool,
    }
)
SERVICE_SYNC_ROOMS_SCHEMA = vol.Schema(
    {
        vol.Optional("add_missing", default=True): bool,
        vol.Optional("remove_missing", default=True): bool,
    }
)
SERVICE_REFRESH_ENTITY_STRUCTURE_SCHEMA = vol.Schema(
    {
        vol.Optional("sync_rooms", default=True): bool,
        vol.Optional("add_missing", default=True): bool,
        vol.Optional("remove_missing", default=True): bool,
    }
)

TTS_PROVIDER_ENTITY_IDS = {
    "openai_conversation": "tts.openai_tts",
    "google_translate": "tts.google_translate_en_com",
}


def _resolve_target_from_alias(target: str, area_id: str | None, aliases: dict[str, str]) -> str:
    """Resolve execution alias to concrete target string if configured."""
    if area_id and target in aliases:
        return aliases[target]
    return target


async def _async_handle_execute(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    """Execute an orchestration target using deterministic hierarchy."""
    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()

    area_id = call.data.get("area_id")
    room = state.rooms.get(area_id) if area_id else None
    resolved_target = _resolve_target_from_alias(
        call.data["target"],
        area_id,
        room.aliases if room else {},
    )

    if resolved_target.startswith("scene."):
        domain = "scene"
        service = "turn_on"
        data: dict[str, Any] = {"entity_id": resolved_target}
    elif resolved_target.startswith("script."):
        domain = "script"
        service = "turn_on"
        data = {"entity_id": resolved_target}
    else:
        domain = "homeassistant"
        service = "turn_on"
        data = {"entity_id": resolved_target}

    await hass.services.async_call(domain, service, data, blocking=True)

    payload = {
        "target": call.data["target"],
        "resolved_target": resolved_target,
        "area_id": area_id,
        "composite_id": call.data.get("composite_id"),
        "context": call.data.get("context", {}),
    }
    hass.bus.async_fire(EVENT_EXECUTION, payload)
    return {"executed": True, "resolved_target": resolved_target}


async def _async_handle_execute_direct(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    """Execute a direct service/entity action without orchestration."""
    service_ref = call.data["service"]
    if "." not in service_ref:
        raise vol.Invalid("service must be in domain.service format")

    domain, service = service_ref.split(".", 1)
    data: dict[str, Any] = {"entity_id": call.data["entity_id"]}
    data.update(call.data.get("data", {}))
    await hass.services.async_call(domain, service, data, blocking=True)

    payload = {
        "entity_id": call.data["entity_id"],
        "service": service_ref,
        "data": call.data.get("data", {}),
    }
    hass.bus.async_fire(EVENT_EXECUTION, payload)
    return {"executed": True}


async def _async_handle_get_interactions(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    """Return active interactions for optional room scope."""
    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    area_id = call.data.get("area_id")
    interactions = list(state.interactions.values())
    if area_id:
        interactions = [item for item in interactions if item.area_id == area_id]

    return {
        "interactions": [
            {
                "interaction_id": item.interaction_id,
                "area_id": item.area_id,
                "message": item.message,
                "level": item.level,
                "state": item.state,
                "priority": item.priority,
            }
            for item in sorted(interactions, key=lambda i: i.priority, reverse=True)
        ]
    }


async def _async_handle_update_interaction(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    """Upsert runtime interaction state."""
    storage = ConciergeStorage(hass)
    interaction = Interaction(
        interaction_id=call.data["interaction_id"],
        area_id=call.data.get("area_id"),
        message=call.data["message"],
        level=call.data.get("level", "info"),
        state=call.data.get("state", "active"),
        priority=int(call.data.get("priority", 0)),
    )
    state = await storage.async_upsert_interaction(interaction)
    return {"interaction_count": len(state.interactions)}


async def _async_handle_clear_interaction(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    """Remove an interaction from runtime state."""
    storage = ConciergeStorage(hass)
    state = await storage.async_remove_interaction(call.data["interaction_id"])
    return {"interaction_count": len(state.interactions)}


async def _async_handle_get_signal(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    """Return a specific signal snapshot."""
    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    signal = state.signals.get(call.data["signal_type"])
    if signal is None:
        return {"signal": None}
    return {
        "signal": {
            "signal_type": signal.signal_type,
            "available": signal.available,
            "summary": signal.summary,
            "state": signal.state,
        }
    }


async def _async_handle_get_signals(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    """Return all known signal snapshots."""
    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    return {
        "signals": [
            {
                "signal_type": signal.signal_type,
                "available": signal.available,
                "summary": signal.summary,
                "state": signal.state,
            }
            for signal in state.signals.values()
        ]
    }


async def _async_handle_update_room_config(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    """Upsert room configuration with deterministic aliases/overlays."""
    aliases = call.data.get("aliases")
    global_overlays = call.data.get("global_overlays")
    media_player_entity_ids = call.data.get("media_player_entity_ids")
    voice_device_entity_ids = call.data.get("voice_device_entity_ids")
    asset_entity_ids = call.data.get("asset_entity_ids")
    room_sensor_entity_ids = call.data.get("room_sensor_entity_ids")
    room_health_entity_ids = call.data.get("room_health_entity_ids")
    human_health_entity_ids = call.data.get("human_health_entity_ids")
    light_entity_ids = call.data.get("light_entity_ids")
    shade_entity_ids = call.data.get("shade_entity_ids")
    speaker_entity_ids = call.data.get("speaker_entity_ids")
    dashboard_entity_ids = call.data.get("dashboard_entity_ids")
    other_entity_ids = call.data.get("other_entity_ids")
    persona = call.data.get("persona")
    persona_prompt = call.data.get("persona_prompt")
    if aliases is not None and not all(isinstance(v, str) for v in aliases.values()):
        raise vol.Invalid("aliases values must be strings")
    if global_overlays is not None and not all(
        isinstance(v, bool) for v in global_overlays.values()
    ):
        raise vol.Invalid("global_overlays values must be booleans")
    if media_player_entity_ids is not None and not all(
        isinstance(v, str) for v in media_player_entity_ids
    ):
        raise vol.Invalid("media_player_entity_ids values must be strings")
    if voice_device_entity_ids is not None and not all(
        isinstance(v, str) for v in voice_device_entity_ids
    ):
        raise vol.Invalid("voice_device_entity_ids values must be strings")
    for field_name, entity_ids in (
        ("asset_entity_ids", asset_entity_ids),
        ("room_sensor_entity_ids", room_sensor_entity_ids),
        ("room_health_entity_ids", room_health_entity_ids),
        ("human_health_entity_ids", human_health_entity_ids),
        ("light_entity_ids", light_entity_ids),
        ("shade_entity_ids", shade_entity_ids),
        ("speaker_entity_ids", speaker_entity_ids),
        ("dashboard_entity_ids", dashboard_entity_ids),
        ("other_entity_ids", other_entity_ids),
    ):
        if entity_ids is not None and not all(isinstance(v, str) for v in entity_ids):
            raise vol.Invalid(f"{field_name} values must be strings")

    storage = ConciergeStorage(hass)
    state = await storage.async_update_room_config(
        area_id=call.data["area_id"],
        aliases=aliases,
        global_overlays=global_overlays,
        posture=call.data.get("posture"),
        media_player_entity_ids=media_player_entity_ids,
        voice_device_entity_ids=voice_device_entity_ids,
        tts_voice=call.data.get("tts_voice"),
        asset_entity_ids=asset_entity_ids,
        room_sensor_entity_ids=room_sensor_entity_ids,
        room_health_entity_ids=room_health_entity_ids,
        human_health_entity_ids=human_health_entity_ids,
        light_entity_ids=light_entity_ids,
        shade_entity_ids=shade_entity_ids,
        speaker_entity_ids=speaker_entity_ids,
        dashboard_entity_ids=dashboard_entity_ids,
        other_entity_ids=other_entity_ids,
        persona=persona,
        persona_prompt=persona_prompt,
    )
    return {"room_count": len(state.rooms)}


async def _async_handle_update_identity_profile(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Insert or update identity preferences for Concierge presentation."""
    storage = ConciergeStorage(hass)
    profile = IdentityProfile(
        profile_id=call.data["profile_id"],
        name=call.data["name"],
        persona=call.data.get("persona", "concise"),
        tts_voice=call.data.get("tts_voice", ""),
        verbosity=call.data.get("verbosity", "standard"),
        allow_ai=bool(call.data.get("allow_ai", True)),
        content_type=call.data.get("content_type", "general"),
        detail_level=call.data.get("detail_level", "medium"),
    )
    state = await storage.async_update_identity_profile(
        profile,
        set_as_default=bool(call.data.get("set_as_default", False)),
    )
    return {
        "identity_profile_count": len(state.identity_profiles),
        "default_profile_id": (
            state.default_identity_profile.profile_id
            if state.default_identity_profile is not None
            else None
        ),
    }


async def _async_handle_update_person_profile(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Insert or update person identity and consent state."""
    storage = ConciergeStorage(hass)
    profile = PersonProfile(
        person_id=call.data["person_id"],
        name=call.data["name"],
        linked_area_id=call.data.get("linked_area_id"),
        ble_device_ids=list(call.data.get("ble_device_ids", [])),
        aqara_presence_entity_ids=list(call.data.get("aqara_presence_entity_ids", [])),
        voice_profile_id=call.data.get("voice_profile_id"),
        consent=dict(call.data.get("consent", {})),
        notes=call.data.get("notes", ""),
    )
    state = await storage.async_update_person_profile(
        profile,
        set_as_default=bool(call.data.get("set_as_default", False)),
    )
    return {
        "person_profile_count": len(state.person_profiles),
        "default_person_id": (
            state.default_person_profile.person_id if state.default_person_profile is not None else None
        ),
    }


async def _async_handle_update_voice_profile(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Insert or update voice enrollment and attribution state."""
    storage = ConciergeStorage(hass)
    profile = VoiceProfile(
        voice_profile_id=call.data["voice_profile_id"],
        name=call.data["name"],
        tts_voice=call.data.get("tts_voice", ""),
        enrollment_state=call.data.get("enrollment_state", "untrained"),
        enrollment_source=call.data.get("enrollment_source", ""),
        speaker_embedding_id=call.data.get("speaker_embedding_id", ""),
        sample_count=int(call.data.get("sample_count", 0)),
        consent=dict(call.data.get("consent", {})),
    )
    state = await storage.async_update_voice_profile(
        profile,
        set_as_default=bool(call.data.get("set_as_default", False)),
    )
    return {
        "voice_profile_count": len(state.voice_profiles),
        "default_voice_profile_id": (
            state.default_voice_profile.voice_profile_id if state.default_voice_profile is not None else None
        ),
    }


async def _async_handle_update_global_context(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    """Update global context usage and optional cached speakable values."""
    storage = ConciergeStorage(hass)
    if call.data["context_type"] in {"weather", "news", "alarm_status"}:
        await storage.async_update_global_feature(
            feature_key=call.data["context_type"],
            enabled=call.data["enabled"],
            options=call.data.get("options"),
        )

    state = await storage.async_update_global_context_usage(
        context_type=call.data["context_type"],
        enabled=call.data["enabled"],
        options=call.data.get("options"),
    )

    context = ContextState(
        context_type=call.data["context_type"],
        available=call.data["enabled"],
        summary=call.data.get("summary", ""),
        detail=call.data.get("detail", ""),
        speakable=call.data.get("speakable", ""),
    )
    state = await storage.async_upsert_context(context)
    return {"context_count": len(state.contexts), "usage_count": len(state.global_context_usage)}


async def _async_handle_update_execution_preferences(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Update execution preferences at area/composite scope."""
    storage = ConciergeStorage(hass)
    state = await storage.async_update_execution_preferences(
        scope_id=call.data["scope_id"],
        preferences=call.data["preferences"],
    )
    return {"execution_preference_count": len(state.execution_preferences)}


def _validate_same_floor_area_ids(hass: HomeAssistant, area_ids: list[str]) -> None:
    """Validate all provided areas exist and belong to the same floor."""
    if len(area_ids) <= 1:
        return

    area_registry = ar.async_get(hass)
    floor_ids: set[str | None] = set()

    for area_id in area_ids:
        area = area_registry.async_get_area(area_id)
        if area is None:
            raise vol.Invalid(f"area_id does not exist: {area_id}")
        floor_ids.add(area.floor_id)

    if len(floor_ids) > 1:
        raise vol.Invalid("composite area_ids must all be on the same floor")


COMPOSITE_ENTITY_FIELDS: tuple[str, ...] = (
    "media_player_entity_ids",
    "voice_device_entity_ids",
    "asset_entity_ids",
    "room_sensor_entity_ids",
    "room_health_entity_ids",
    "human_health_entity_ids",
    "light_entity_ids",
    "shade_entity_ids",
    "speaker_entity_ids",
    "dashboard_entity_ids",
    "other_entity_ids",
)


def _entity_ids_for_area_ids(hass: HomeAssistant, area_ids: list[str]) -> set[str]:
    """Return all entity IDs currently assigned to the given area IDs."""
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)
    target_areas = set(area_ids)
    entity_ids: set[str] = set()

    for entry in entity_registry.entities.values():
        if entry.disabled_by is not None:
            continue

        area_id = entry.area_id
        if area_id is None and entry.device_id:
            device = device_registry.devices.get(entry.device_id)
            if device is not None:
                area_id = device.area_id

        if area_id in target_areas:
            entity_ids.add(entry.entity_id)

    return entity_ids


def _sanitize_composite_entity_payload(
    payload: dict[str, Any],
    *,
    allowed_entity_ids: set[str],
) -> dict[str, list[str] | None]:
    """Keep only selected entity IDs that are members of current composite areas."""
    sanitized: dict[str, list[str] | None] = {}
    for field_name in COMPOSITE_ENTITY_FIELDS:
        if field_name not in payload:
            sanitized[field_name] = None
            continue
        value = payload.get(field_name)
        if not isinstance(value, list):
            raise vol.Invalid(f"{field_name} must be a list of entity IDs")
        unique_values = list(dict.fromkeys(str(item) for item in value if isinstance(item, str)))
        sanitized[field_name] = [entity_id for entity_id in unique_values if entity_id in allowed_entity_ids]
    return sanitized


async def _async_handle_update_composite_config(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Create/update/dismantle a merged-room composite configuration."""
    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()

    composite_id = call.data["composite_id"]
    existing = state.composites.get(composite_id)

    area_ids = call.data.get("area_ids")
    if area_ids is None and existing is not None:
        resolved_area_ids = list(existing.area_ids)
    elif area_ids is None:
        resolved_area_ids = []
    else:
        resolved_area_ids = list(dict.fromkeys(area_ids))

    if resolved_area_ids:
        _validate_same_floor_area_ids(hass, resolved_area_ids)

    primary_area = call.data.get("primary_area")
    if primary_area is not None and resolved_area_ids and primary_area not in resolved_area_ids:
        raise vol.Invalid("primary_area must exist in area_ids")

    # Composite device selections must remain scoped to member areas.
    allowed_entity_ids = _entity_ids_for_area_ids(hass, resolved_area_ids)
    sanitized_entities = _sanitize_composite_entity_payload(call.data, allowed_entity_ids=allowed_entity_ids)

    if area_ids is not None and existing is not None:
        for field_name in COMPOSITE_ENTITY_FIELDS:
            if sanitized_entities[field_name] is not None:
                continue
            current = getattr(existing, field_name, [])
            if not isinstance(current, list):
                sanitized_entities[field_name] = []
                continue
            sanitized_entities[field_name] = [
                entity_id
                for entity_id in current
                if isinstance(entity_id, str) and entity_id in allowed_entity_ids
            ]

    updated = await storage.async_update_composite_config(
        composite_id=composite_id,
        name=call.data.get("name"),
        area_ids=resolved_area_ids if area_ids is not None else None,
        primary_area=primary_area,
        enabled=call.data.get("enabled"),
        media_player_entity_ids=sanitized_entities["media_player_entity_ids"],
        voice_device_entity_ids=sanitized_entities["voice_device_entity_ids"],
        asset_entity_ids=sanitized_entities["asset_entity_ids"],
        room_sensor_entity_ids=sanitized_entities["room_sensor_entity_ids"],
        room_health_entity_ids=sanitized_entities["room_health_entity_ids"],
        human_health_entity_ids=sanitized_entities["human_health_entity_ids"],
        light_entity_ids=sanitized_entities["light_entity_ids"],
        shade_entity_ids=sanitized_entities["shade_entity_ids"],
        speaker_entity_ids=sanitized_entities["speaker_entity_ids"],
        dashboard_entity_ids=sanitized_entities["dashboard_entity_ids"],
        other_entity_ids=sanitized_entities["other_entity_ids"],
    )

    composite = updated.composites.get(composite_id)
    return {
        "updated": True,
        "composite_id": composite_id,
        "dismantled": composite is None,
        "composite_count": len(updated.composites),
        "area_count": len(composite.area_ids) if composite else 0,
    }


async def _async_handle_sync_composites(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Validate and rebuild composite runtime projections."""
    area_registry = ar.async_get(hass)
    _ = fr.async_get(hass)
    valid_area_ids = {area.id for area in area_registry.async_list_areas()}
    remove_invalid = bool(call.data.get("remove_invalid", True))

    storage = ConciergeStorage(hass)
    state, validation_errors = await storage.async_sync_composites(
        valid_area_ids=valid_area_ids,
        remove_invalid=remove_invalid,
    )

    # Validate same-floor membership for all remaining composites.
    for composite_id, composite in state.composites.items():
        try:
            _validate_same_floor_area_ids(hass, composite.area_ids)
        except vol.Invalid as err:
            validation_errors.append(f"{composite_id}: {err}")

    # Also prune stale selected entity IDs when member areas changed.
    if remove_invalid:
        for composite_id, composite in state.composites.items():
            allowed_entity_ids = _entity_ids_for_area_ids(hass, composite.area_ids)
            update_payload: dict[str, list[str]] = {}

            for field_name in COMPOSITE_ENTITY_FIELDS:
                current = getattr(composite, field_name, [])
                if not isinstance(current, list):
                    continue
                filtered = [
                    entity_id
                    for entity_id in current
                    if isinstance(entity_id, str) and entity_id in allowed_entity_ids
                ]
                if filtered != current:
                    update_payload[field_name] = filtered

            if update_payload:
                await storage.async_update_composite_config(
                    composite_id=composite_id,
                    **update_payload,
                )

    return {
        "synced": True,
        "remove_invalid": remove_invalid,
        "composite_count": len(state.composites),
        "validation_errors": validation_errors,
    }


async def _async_handle_get_context(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    """Return a specific global context payload."""
    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    context = state.contexts.get(call.data["context_type"])
    if context is None:
        return {"context": None}
    return {
        "context": {
            "context_type": context.context_type,
            "available": context.available,
            "summary": context.summary,
            "detail": context.detail,
            "speakable": context.speakable,
        }
    }


async def _async_handle_get_summary(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    """Return deterministic summary from available context and signals."""
    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()

    parts: list[str] = []
    if call.data.get("include_context", True):
        parts.extend(
            context.summary
            for context in state.contexts.values()
            if context.available and context.summary
        )
    if call.data.get("include_signals", True):
        parts.extend(
            signal.summary
            for signal in state.signals.values()
            if signal.available and signal.summary
        )

    summary = " | ".join(parts)
    return {
        "summary": summary,
        "area_id": call.data.get("area_id"),
        "include_signals": call.data.get("include_signals", True),
        "include_context": call.data.get("include_context", True),
    }


async def _async_handle_preview_tts_voice(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Preview a TTS voice on a selected media player."""
    provider = call.data["provider"]
    engine_entity_id = TTS_PROVIDER_ENTITY_IDS.get(provider)
    if engine_entity_id is None:
        raise vol.Invalid(f"unsupported provider: {provider}")

    options: dict[str, Any] = {}
    if call.data.get("voice"):
        options["voice"] = call.data["voice"]

    await hass.services.async_call(
        "tts",
        "speak",
        {
            "entity_id": engine_entity_id,
            "media_player_entity_id": call.data["media_player_entity_id"],
            "message": call.data["message"],
            "cache": False,
            "options": options,
        },
        blocking=True,
    )

    return {
        "previewed": True,
        "provider": provider,
        "engine_entity_id": engine_entity_id,
    }


async def _async_handle_sync_rooms(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Synchronize Concierge room config keys to current Home Assistant areas."""
    area_registry = ar.async_get(hass)
    current_area_ids = {area.id for area in area_registry.async_list_areas()}

    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    existing_area_ids = set(state.rooms)

    add_missing = bool(call.data.get("add_missing", True))
    remove_missing = bool(call.data.get("remove_missing", True))

    added = sorted(current_area_ids - existing_area_ids)
    removed = sorted(existing_area_ids - current_area_ids)

    if add_missing:
        for area_id in added:
            await storage.async_update_room_config(area_id=area_id)

    if remove_missing and removed:
        state = await storage.async_load_state()
        for area_id in removed:
            state.rooms.pop(area_id, None)
        await storage.async_save_state(state)

    final_state = await storage.async_load_state()
    return {
        "synced": True,
        "add_missing": add_missing,
        "remove_missing": remove_missing,
        "added_room_ids": added if add_missing else [],
        "removed_room_ids": removed if remove_missing else [],
        "room_count": len(final_state.rooms),
    }


async def _async_handle_refresh_entity_structure(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Optionally sync rooms then reload Concierge entry to rebuild entities."""
    sync_rooms = bool(call.data.get("sync_rooms", True))
    sync_result: dict[str, Any] | None = None

    if sync_rooms:
        sync_result = await _async_handle_sync_rooms(
            hass,
            ServiceCall(
                context=call.context,
                data={
                    "add_missing": bool(call.data.get("add_missing", True)),
                    "remove_missing": bool(call.data.get("remove_missing", True)),
                },
                domain=DOMAIN,
                service=SERVICE_SYNC_ROOMS,
                return_response=True,
                service_data={
                    "add_missing": bool(call.data.get("add_missing", True)),
                    "remove_missing": bool(call.data.get("remove_missing", True)),
                },
                service_data_unmodified={
                    "add_missing": bool(call.data.get("add_missing", True)),
                    "remove_missing": bool(call.data.get("remove_missing", True)),
                },
            ),
        )

    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        raise vol.Invalid("concierge config entry not found")

    entry = entries[0]
    refreshed = await hass.config_entries.async_reload(entry.entry_id)
    return {
        "refreshed": refreshed,
        "entry_id": entry.entry_id,
        "sync_rooms": sync_rooms,
        "sync_result": sync_result,
    }


async def async_register_services(hass: HomeAssistant) -> None:
    """Register Concierge contract services."""
    if hass.services.has_service(DOMAIN, SERVICE_EXECUTE):
        return

    def _bind(handler):
        async def _wrapped(call: ServiceCall):
            return await handler(hass, call)

        return _wrapped

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTE,
        _bind(_async_handle_execute),
        schema=SERVICE_EXECUTE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTE_DIRECT,
        _bind(_async_handle_execute_direct),
        schema=SERVICE_EXECUTE_DIRECT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_INTERACTIONS,
        _bind(_async_handle_get_interactions),
        schema=SERVICE_GET_INTERACTIONS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_INTERACTION,
        _bind(_async_handle_update_interaction),
        schema=SERVICE_UPDATE_INTERACTION_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_INTERACTION,
        _bind(_async_handle_clear_interaction),
        schema=SERVICE_CLEAR_INTERACTION_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_SIGNAL,
        _bind(_async_handle_get_signal),
        schema=SERVICE_GET_SIGNAL_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_SIGNALS,
        _bind(_async_handle_get_signals),
        schema=SERVICE_GET_SIGNALS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_ROOM_CONFIG,
        _bind(_async_handle_update_room_config),
        schema=SERVICE_UPDATE_ROOM_CONFIG_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_IDENTITY_PROFILE,
        _bind(_async_handle_update_identity_profile),
        schema=SERVICE_UPDATE_IDENTITY_PROFILE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_PERSON_PROFILE,
        _bind(_async_handle_update_person_profile),
        schema=SERVICE_UPDATE_PERSON_PROFILE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_VOICE_PROFILE,
        _bind(_async_handle_update_voice_profile),
        schema=SERVICE_UPDATE_VOICE_PROFILE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_GLOBAL_CONTEXT,
        _bind(_async_handle_update_global_context),
        schema=SERVICE_UPDATE_GLOBAL_CONTEXT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_EXECUTION_PREFERENCES,
        _bind(_async_handle_update_execution_preferences),
        schema=SERVICE_UPDATE_EXEC_PREFS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_COMPOSITE_CONFIG,
        _bind(_async_handle_update_composite_config),
        schema=SERVICE_UPDATE_COMPOSITE_CONFIG_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SYNC_COMPOSITES,
        _bind(_async_handle_sync_composites),
        schema=SERVICE_SYNC_COMPOSITES_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_CONTEXT,
        _bind(_async_handle_get_context),
        schema=SERVICE_GET_CONTEXT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_SUMMARY,
        _bind(_async_handle_get_summary),
        schema=SERVICE_GET_SUMMARY_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PREVIEW_TTS_VOICE,
        _bind(_async_handle_preview_tts_voice),
        schema=SERVICE_PREVIEW_TTS_VOICE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SYNC_ROOMS,
        _bind(_async_handle_sync_rooms),
        schema=SERVICE_SYNC_ROOMS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_ENTITY_STRUCTURE,
        _bind(_async_handle_refresh_entity_structure),
        schema=SERVICE_REFRESH_ENTITY_STRUCTURE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
async def async_unregister_services(hass: HomeAssistant) -> None:
    """Unregister Concierge services."""
    for service_name in (
        SERVICE_EXECUTE,
        SERVICE_EXECUTE_DIRECT,
        SERVICE_GET_INTERACTIONS,
        SERVICE_UPDATE_INTERACTION,
        SERVICE_CLEAR_INTERACTION,
        SERVICE_GET_SIGNAL,
        SERVICE_GET_SIGNALS,
        SERVICE_UPDATE_ROOM_CONFIG,
        SERVICE_UPDATE_IDENTITY_PROFILE,
        SERVICE_UPDATE_PERSON_PROFILE,
        SERVICE_UPDATE_VOICE_PROFILE,
        SERVICE_UPDATE_GLOBAL_CONTEXT,
        SERVICE_UPDATE_EXECUTION_PREFERENCES,
        SERVICE_UPDATE_COMPOSITE_CONFIG,
        SERVICE_SYNC_COMPOSITES,
        SERVICE_GET_CONTEXT,
        SERVICE_GET_SUMMARY,
        SERVICE_PREVIEW_TTS_VOICE,
        SERVICE_SYNC_ROOMS,
        SERVICE_REFRESH_ENTITY_STRUCTURE,
    ):
        if hass.services.has_service(DOMAIN, service_name):
            hass.services.async_remove(DOMAIN, service_name)
