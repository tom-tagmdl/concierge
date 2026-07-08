"""Contract-first service handlers for Concierge orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Awaitable, Callable
from urllib.parse import unquote, urlparse
from uuid import uuid4

import voluptuous as vol

from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import floor_registry as fr
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse

from .archive_runtime import archive_options_from_entry, resolve_voice_enrollment_root
from .const import (
    SERVICE_BUILD_VOICE_PROFILE,
    SERVICE_CAPTURE_VOICE_ENROLLMENT_SAMPLE,
    SERVICE_DELETE_VOICE_PROFILE,
    DOMAIN,
    EVENT_EXECUTION,
    SERVICE_REMOVE_VOICE_ENROLLMENT_SAMPLE,
    SERVICE_RESET_VOICE_PROFILE,
    SERVICE_START_VOICE_ENROLLMENT,
    SERVICE_CLEAR_INTERACTION,
    SERVICE_CLOSE_ACTIVITY_OUTCOME,
    SERVICE_EXECUTE,
    SERVICE_EXECUTE_DIRECT,
    SERVICE_EXPORT_ACTIVITY_ARCHIVE,
    SERVICE_GET_ACTIVITY_TIMELINE,
    SERVICE_GET_CONTEXT,
    SERVICE_GET_INTERACTIONS,
    SERVICE_GET_SIGNAL,
    SERVICE_GET_SIGNALS,
    SERVICE_GET_SUMMARY,
    SERVICE_PREVIEW_TTS_VOICE,
    SERVICE_PUSH_PERSON_MESSAGE,
    SERVICE_REFRESH_ENTITY_STRUCTURE,
    SERVICE_RECORD_ACTIVITY_EVENT,
    SERVICE_RESOLVE_MOBILE_CONTEXT,
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
    TTS_PROVIDER_ENTITY_IDS,
    VOICE_ENROLLMENT_CLEANUP_REASON_CANCELLED,
    VOICE_ENROLLMENT_CLEANUP_REASON_COMPLETED,
    VOICE_ENROLLMENT_CLEANUP_REASON_FAILED,
    VOICE_ENROLLMENT_CLEANUP_REASON_MANUAL,
    VOICE_ENROLLMENT_CLEANUP_REASON_TIMEOUT,
    VOICE_ENROLLMENT_CLEANUP_REASON_UNKNOWN,
    VOICE_ENROLLMENT_CLEANUP_RESULT_FAILED,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_NOT_CONFIGURED,
    VOICE_ENROLLMENT_PREFLIGHT_STORAGE_UNKNOWN_FAILURE,
)
from .enrollment_cleanup import EnrollmentCleanupManager, EnrollmentCleanupRequest
from .enrollment_session import (
    build_enrollment_session_manifest_payload,
    enrollment_session_for_start,
    enrollment_session_mark_cleanup_complete,
    enrollment_session_mark_cleanup_failed,
    enrollment_session_mark_cleanup_pending,
    enrollment_session_mark_cleanup_running,
    enrollment_session_mark_profile_built,
    enrollment_session_record_sample,
    enrollment_session_remove_sample,
    enrollment_session_reset,
    legacy_voice_profile_enrollment_state,
    resolve_manifest_target_sample_count,
)
from .enrollment_storage import MountedPathEnrollmentStorageProvider
from .models import (
    ActivityEvent,
    ContextState,
    EnrollmentSession,
    IdentityProfile,
    Interaction,
    PersonProfile,
    SignalState,
    VoiceProfile,
)
from .repairs import (
    async_clear_cleanup_issue,
    async_clear_storage_issue,
    async_create_or_update_cleanup_issue,
    async_create_or_update_storage_issue,
)
from .storage import ConciergeStorage

_PROVIDER_NONE = "none"
_PROVIDER_ASSET_INTELLIGENCE = "asset_intelligence"
_DEFAULT_TARGET_SAMPLE_COUNT = 3

TTS_PROVIDER_ENTITY_IDS = {
    "openai_conversation": "tts.openai_tts",
    "google_translate": "tts.google_translate_en_com",
}
SERVICE_EXECUTE_SCHEMA = vol.Schema(
    {
        vol.Required("target"): str,
        vol.Optional("area_id"): str,
        vol.Optional("composite_id"): str,
        vol.Optional("context"): dict,
        vol.Optional("person_id"): str,
        vol.Optional("intent_class", default="home_control"): str,
    }
)

SERVICE_EXECUTE_DIRECT_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): str,
        vol.Required("service"): str,
        vol.Optional("data"): dict,
        vol.Optional("person_id"): str,
        vol.Optional("intent_class", default="home_control"): str,
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
        vol.Optional("tts_language"): str,
        vol.Optional("ai_knowledge_enabled"): bool,
        vol.Optional("environment_information_outputs"): vol.All(list, [str]),
        vol.Optional("device_groups"): list,
        vol.Optional("asset_groups"): list,
        vol.Optional("room_sensor_entity_ids"): vol.All(list, [str]),
        vol.Optional("room_health_entity_ids"): vol.All(list, [str]),
        vol.Optional("human_health_entity_ids"): vol.All(list, [str]),
        vol.Optional("light_entity_ids"): vol.All(list, [str]),
        vol.Optional("lamp_entity_ids"): vol.All(list, [str]),
        vol.Optional("shade_entity_ids"): vol.All(list, [str]),
        vol.Optional("speaker_entity_ids"): vol.All(list, [str]),
        vol.Optional("tv_entity_ids"): vol.All(list, [str]),
        vol.Optional("dashboard_entity_ids"): vol.All(list, [str]),
        vol.Optional("other_entity_ids"): vol.All(list, [str]),
        vol.Optional("weather_source_entity_ids"): vol.All(list, [str]),
        vol.Optional("news_source_entity_ids"): vol.All(list, [str]),
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
        vol.Optional("posture"): str,
        vol.Optional("media_player_entity_ids"): vol.All(list, [str]),
        vol.Optional("voice_device_entity_ids"): vol.All(list, [str]),
        vol.Optional("tts_voice"): str,
        vol.Optional("tts_language"): str,
        vol.Optional("device_groups"): list,
        vol.Optional("persona"): str,
        vol.Optional("persona_prompt"): str,
        vol.Optional("ai_knowledge_enabled"): bool,
        vol.Optional("environment_information_outputs"): vol.All(list, [str]),
        vol.Optional("asset_groups"): list,
        vol.Optional("room_sensor_entity_ids"): vol.All(list, [str]),
        vol.Optional("room_health_entity_ids"): vol.All(list, [str]),
        vol.Optional("human_health_entity_ids"): vol.All(list, [str]),
        vol.Optional("light_entity_ids"): vol.All(list, [str]),
        vol.Optional("shade_entity_ids"): vol.All(list, [str]),
        vol.Optional("speaker_entity_ids"): vol.All(list, [str]),
        vol.Optional("dashboard_entity_ids"): vol.All(list, [str]),
        vol.Optional("other_entity_ids"): vol.All(list, [str]),
        vol.Optional("weather_source_entity_ids"): vol.All(list, [str]),
        vol.Optional("news_source_entity_ids"): vol.All(list, [str]),
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
        vol.Optional("language"): str,
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
        vol.Optional("mobile_notify_targets", default=[]): vol.All(list, [str]),
        vol.Optional("preferred_mobile_target"): str,
        vol.Optional("mobile_voice_endpoint_enabled", default=False): bool,
        vol.Optional("is_minor", default=False): bool,
        vol.Optional("guardian_controls_required", default=False): bool,
        vol.Optional("minor_allow_general_qna", default=False): bool,
        vol.Optional("minor_allowed_intent_classes", default=[]): vol.All(list, [str]),
        vol.Optional("minor_content_filter_level", default="strict"): str,
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
        vol.Optional("sample_items", default=[]): vol.All(list, [dict]),
        vol.Optional("attribution_confidence"): vol.Coerce(float),
        vol.Optional("enrollment_started_at", default=""): str,
        vol.Optional("last_sample_at", default=""): str,
        vol.Optional("last_built_at", default=""): str,
        vol.Optional("disabled", default=False): bool,
        vol.Optional("consent", default={}): dict,
        vol.Optional("set_as_default", default=False): bool,
    }
)
SERVICE_START_VOICE_ENROLLMENT_SCHEMA = vol.Schema(
    {
        vol.Required("person_id"): str,
        vol.Optional("voice_profile_id"): str,
        vol.Optional("voice_name"): str,
        vol.Optional("consent_acknowledged", default=False): bool,
        vol.Optional("local_only", default=True): bool,
    }
)
SERVICE_CAPTURE_VOICE_ENROLLMENT_SAMPLE_SCHEMA = vol.Schema(
    {
        vol.Required("voice_profile_id"): str,
        vol.Required("speech_text"): str,
        vol.Optional("source", default="guided_phrase"): str,
        vol.Optional("quality_score"): vol.Coerce(float),
        vol.Optional("recording_path"): str,
        vol.Optional("recording_mime_type"): str,
        vol.Optional("recording_size_bytes"): int,
        vol.Optional("recording_duration_ms"): int,
        vol.Optional("phrase_index"): int,
    }
)
SERVICE_REMOVE_VOICE_ENROLLMENT_SAMPLE_SCHEMA = vol.Schema(
    {
        vol.Required("voice_profile_id"): str,
        vol.Required("sample_id"): str,
    }
)
SERVICE_BUILD_VOICE_PROFILE_SCHEMA = vol.Schema(
    {
        vol.Required("voice_profile_id"): str,
        vol.Optional("person_id"): str,
        vol.Optional("min_samples", default=3): vol.All(int, vol.Range(min=1, max=50)),
    }
)
SERVICE_RESET_VOICE_PROFILE_SCHEMA = vol.Schema(
    {
        vol.Required("voice_profile_id"): str,
        vol.Optional("preserve_consent", default=True): bool,
    }
)
SERVICE_DELETE_VOICE_PROFILE_SCHEMA = vol.Schema(
    {
        vol.Required("voice_profile_id"): str,
        vol.Optional("unlink_from_people", default=True): bool,
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
SERVICE_RECORD_ACTIVITY_EVENT_SCHEMA = vol.Schema(
    {
        vol.Required("activity_id"): str,
        vol.Required("correlation_id"): str,
        vol.Required("started_at"): str,
        vol.Required("channel"): str,
        vol.Required("actor_class"): str,
        vol.Required("intent_class"): str,
        vol.Optional("request_summary", default=""): str,
        vol.Optional("resolved_person_id"): str,
        vol.Optional("resolved_area_id"): str,
        vol.Optional("confidence"): vol.Coerce(float),
        vol.Optional("external_refs", default=[]): vol.All(list, [dict]),
    }
)
SERVICE_CLOSE_ACTIVITY_OUTCOME_SCHEMA = vol.Schema(
    {
        vol.Required("activity_id"): str,
        vol.Required("ended_at"): str,
        vol.Required("outcome"): str,
        vol.Optional("outcome_reason", default=""): str,
        vol.Optional("actions_taken", default=[]): vol.All(list, [str]),
        vol.Optional("policy_gates", default=[]): vol.All(list, [str]),
    }
)
SERVICE_GET_ACTIVITY_TIMELINE_SCHEMA = vol.Schema(
    {
        vol.Optional("start"): str,
        vol.Optional("end"): str,
        vol.Optional("actor_class"): str,
        vol.Optional("person_id"): str,
        vol.Optional("area_id"): str,
        vol.Optional("channel"): str,
    }
)
SERVICE_EXPORT_ACTIVITY_ARCHIVE_SCHEMA = vol.Schema(
    {
        vol.Optional("start"): str,
        vol.Optional("end"): str,
        vol.Optional("destination"): str,
        vol.Optional("include_reference_excerpts"): bool,
    }
)
SERVICE_RESOLVE_MOBILE_CONTEXT_SCHEMA = vol.Schema(
    {
        vol.Optional("mobile_target_id"): str,
        vol.Optional("person_id"): str,
        vol.Optional("request_text", default=""): str,
    }
)
SERVICE_PUSH_PERSON_MESSAGE_SCHEMA = vol.Schema(
    {
        vol.Required("person_id"): str,
        vol.Required("message"): str,
        vol.Optional("title", default="Concierge"): str,
        vol.Optional("target_id"): str,
        vol.Optional("data", default={}): dict,
    }
)

def _resolve_target_from_alias(target: str, area_id: str | None, aliases: dict[str, str]) -> str:
    """Resolve execution alias to concrete target string if configured."""
    if area_id and target in aliases:
        return aliases[target]
    return target


def _sanitize_request_summary(actor_class: str, request_summary: str) -> str:
    """Apply guest/minor audit minimization to request summaries."""
    if actor_class in {"guest", "minor"}:
        return ""
    return request_summary


def _new_activity_id(prefix: str) -> str:
    """Return a stable unique activity identifier."""
    return f"{prefix}_{int(datetime.now(timezone.utc).timestamp() * 1000)}_{uuid4().hex[:8]}"


def _safe_outcome_reason(err: Exception) -> str:
    """Return compact outcome reason text suitable for activity timelines."""
    text = str(err or "").strip()
    return text[:500]


def _area_name(hass: HomeAssistant, area_id: str | None) -> str:
    """Resolve area label for timeline summaries."""
    if not area_id:
        return "room"
    area = ar.async_get(hass).async_get_area(area_id)
    if area is None:
        return area_id
    return area.name or area_id


async def _async_with_activity(
    hass: HomeAssistant,
    call: ServiceCall,
    *,
    intent_class: str,
    request_summary: str,
    action_name: str,
    resolved_area_id: str | None = None,
    resolved_person_id: str | None = None,
    channel: str = "service_call",
    actor_class: str = "concierge",
    confidence: float = 1.0,
    external_refs: list[dict[str, Any]] | None = None,
    policy_gates: list[str] | None = None,
    runner: Callable[[], Awaitable[dict[str, Any]]],
) -> dict[str, Any]:
    """Wrap one service action with backend-authored activity lifecycle logging."""
    storage = ConciergeStorage(hass)
    started_at = datetime.now(timezone.utc).isoformat()
    activity_id = _new_activity_id(intent_class)

    await storage.async_record_activity_event(
        ActivityEvent(
            activity_id=activity_id,
            correlation_id=activity_id,
            started_at=started_at,
            channel=channel,
            actor_class=actor_class,
            intent_class=intent_class,
            request_summary=_sanitize_request_summary(actor_class, request_summary),
            resolved_person_id=resolved_person_id,
            resolved_area_id=resolved_area_id,
            confidence=confidence,
            external_refs=list(external_refs or []),
        )
    )

    try:
        result = await runner()
    except vol.Invalid as err:
        reason = _safe_outcome_reason(err)
        deny_policy = list(policy_gates or [])
        if "minor_policy_denied" in reason and "minor_policy" not in deny_policy:
            deny_policy.append("minor_policy")
        await storage.async_close_activity_event(
            activity_id=activity_id,
            ended_at=datetime.now(timezone.utc).isoformat(),
            outcome="policy_denied",
            outcome_reason=reason,
            actions_taken=[action_name],
            policy_gates=deny_policy,
        )
        raise
    except Exception as err:
        await storage.async_close_activity_event(
            activity_id=activity_id,
            ended_at=datetime.now(timezone.utc).isoformat(),
            outcome="error",
            outcome_reason=_safe_outcome_reason(err),
            actions_taken=[action_name],
            policy_gates=list(policy_gates or []),
        )
        raise

    await storage.async_close_activity_event(
        activity_id=activity_id,
        ended_at=datetime.now(timezone.utc).isoformat(),
        outcome="success",
        outcome_reason="",
        actions_taken=[action_name],
        policy_gates=list(policy_gates or []),
    )
    return result


ROOM_CONFIG_LIST_FIELDS: tuple[str, ...] = (
    "device_groups",
    "media_player_entity_ids",
    "voice_device_entity_ids",
    "asset_groups",
    "room_sensor_entity_ids",
    "room_health_entity_ids",
    "human_health_entity_ids",
    "light_entity_ids",
    "lamp_entity_ids",
    "shade_entity_ids",
    "speaker_entity_ids",
    "tv_entity_ids",
    "dashboard_entity_ids",
    "other_entity_ids",
    "weather_source_entity_ids",
    "news_source_entity_ids",
    "environment_information_outputs",
)

ROOM_DEVICE_ACTIVITY_FIELDS: tuple[str, ...] = (
    "device_groups",
    "media_player_entity_ids",
    "voice_device_entity_ids",
    "light_entity_ids",
    "lamp_entity_ids",
    "shade_entity_ids",
    "speaker_entity_ids",
    "tv_entity_ids",
    "room_sensor_entity_ids",
)

ROOM_INFO_ACTIVITY_FIELDS: tuple[str, ...] = (
    "weather_source_entity_ids",
    "news_source_entity_ids",
    "asset_groups",
    "environment_information_outputs",
    "ai_knowledge_enabled",
)


def _label_for_activity_item(hass: HomeAssistant, value: str) -> str:
    """Return friendly label for a diff item value."""
    text = str(value or "").strip()
    if not text:
        return ""
    if "." in text:
        state = hass.states.get(text)
        if state is not None:
            return str(state.attributes.get("friendly_name") or state.name or text)
    return text


def _asset_group_diff_key(group: Any) -> str:
    """Build a stable comparison key for an asset group."""
    if not isinstance(group, dict):
        return json.dumps(group, sort_keys=True, separators=(",", ":"), default=str)

    normalized = {
        "group_name": str(group.get("group_name", "")).strip(),
        "device_ids": sorted(
            [str(device_id).strip() for device_id in group.get("device_ids", []) if str(device_id).strip()]
        ),
    }
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def _device_group_diff_key(group: Any) -> str:
    """Build a stable comparison key for a room device group."""
    if not isinstance(group, dict):
        return json.dumps(group, sort_keys=True, separators=(",", ":"), default=str)

    normalized = {
        "group_name": str(group.get("group_name", "")).strip(),
        "entity_ids": sorted(
            [str(entity_id).strip() for entity_id in group.get("entity_ids", []) if str(entity_id).strip()]
        ),
    }
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def _device_group_diff_label(group: Any) -> str:
    """Build a readable label for a room device group diff entry."""
    if not isinstance(group, dict):
        return str(group or "").strip()

    group_name = str(group.get("group_name", "")).strip()
    entity_ids = [str(entity_id).strip() for entity_id in group.get("entity_ids", []) if str(entity_id).strip()]

    details: list[str] = []
    if group_name:
        details.append(group_name)
    if entity_ids:
        details.append(f"entities: {', '.join(entity_ids)}")
    return " | ".join(details) if details else "device group"


def _asset_group_diff_label(group: Any) -> str:
    """Build a readable label for an asset group diff entry."""
    if not isinstance(group, dict):
        return str(group or "").strip()

    group_name = str(group.get("group_name", "")).strip()
    device_ids = [str(device_id).strip() for device_id in group.get("device_ids", []) if str(device_id).strip()]

    details: list[str] = []
    if group_name:
        details.append(group_name)
    if device_ids:
        details.append(f"devices: {', '.join(device_ids)}")
    return " | ".join(details) if details else "asset group"


def _build_room_config_diff(
    hass: HomeAssistant,
    before_room: Any,
    after_room: Any,
    changed_keys: set[str],
) -> list[dict[str, Any]]:
    """Compute backend-authored room-config diff payload for timeline details."""
    changes: list[dict[str, Any]] = []

    for field in ROOM_CONFIG_LIST_FIELDS:
        if field not in changed_keys:
            continue
        before_raw = list(getattr(before_room, field, []) or []) if before_room is not None else []
        after_raw = list(getattr(after_room, field, []) or []) if after_room is not None else []

        if field == "asset_groups":
            before_values = {_asset_group_diff_key(item): item for item in before_raw}
            after_values = {_asset_group_diff_key(item): item for item in after_raw}
            added_values = [after_values[key] for key in sorted(after_values.keys() - before_values.keys())]
            removed_values = [before_values[key] for key in sorted(before_values.keys() - after_values.keys())]
        elif field == "device_groups":
            before_values = {_device_group_diff_key(item): item for item in before_raw}
            after_values = {_device_group_diff_key(item): item for item in after_raw}
            added_values = [after_values[key] for key in sorted(after_values.keys() - before_values.keys())]
            removed_values = [before_values[key] for key in sorted(before_values.keys() - after_values.keys())]
        else:
            before_values = {str(item).strip() for item in before_raw if str(item).strip()}
            after_values = {str(item).strip() for item in after_raw if str(item).strip()}
            added_values = sorted(after_values - before_values)
            removed_values = sorted(before_values - after_values)
        if not added_values and not removed_values:
            continue
        changes.append(
            {
                "field": field,
                "added": [
                    {
                        "entity_id": value if isinstance(value, str) else (_device_group_diff_key(value) if field == "device_groups" else _asset_group_diff_key(value)),
                        "label": (
                            _device_group_diff_label(value)
                            if field == "device_groups"
                            else (_asset_group_diff_label(value) if field == "asset_groups" else _label_for_activity_item(hass, value))
                        ),
                    }
                    for value in added_values
                ],
                "removed": [
                    {
                        "entity_id": value if isinstance(value, str) else (_device_group_diff_key(value) if field == "device_groups" else _asset_group_diff_key(value)),
                        "label": (
                            _device_group_diff_label(value)
                            if field == "device_groups"
                            else (_asset_group_diff_label(value) if field == "asset_groups" else _label_for_activity_item(hass, value))
                        ),
                    }
                    for value in removed_values
                ],
            }
        )

    if "ai_knowledge_enabled" in changed_keys:
        before_ai = bool(getattr(before_room, "ai_knowledge_enabled", False)) if before_room is not None else False
        after_ai = bool(getattr(after_room, "ai_knowledge_enabled", False)) if after_room is not None else False
        if before_ai != after_ai:
            changes.append(
                {
                    "field": "ai_knowledge_enabled",
                    "added": ([{"entity_id": "ai_knowledge_enabled", "label": "Enable AI Knowledge"}] if after_ai else []),
                    "removed": ([{"entity_id": "ai_knowledge_enabled", "label": "Enable AI Knowledge"}] if not after_ai else []),
                }
            )

    for scalar_field in ("persona", "persona_prompt", "tts_voice", "tts_language", "posture"):
        if scalar_field not in changed_keys:
            continue
        before_value = "" if before_room is None else str(getattr(before_room, scalar_field, "") or "")
        after_value = "" if after_room is None else str(getattr(after_room, scalar_field, "") or "")
        if before_value == after_value:
            continue
        changes.append(
            {
                "field": scalar_field,
                "added": ([{"entity_id": after_value, "label": after_value}] if after_value else []),
                "removed": ([{"entity_id": before_value, "label": before_value}] if before_value else []),
            }
        )

    return changes


def _summarize_room_update(area_name: str, changed_keys: set[str], diff_changes: list[dict[str, Any]]) -> str:
    """Create concise room update summary text for timeline rows."""
    room_name = area_name or "room"
    changed_device = bool(set(changed_keys) & set(ROOM_DEVICE_ACTIVITY_FIELDS))
    changed_info = bool(set(changed_keys) & set(ROOM_INFO_ACTIVITY_FIELDS))
    changed_persona = bool(set(changed_keys) & {"persona", "persona_prompt", "tts_voice", "tts_language", "posture"})

    added_count = sum(len(change.get("added", [])) for change in diff_changes)
    removed_count = sum(len(change.get("removed", [])) for change in diff_changes)

    if changed_device:
        if added_count > 0 and removed_count == 0:
            return f"Concierge devices added to the {room_name}"
        if removed_count > 0 and added_count == 0:
            return f"Concierge devices removed from the {room_name}"
        return f"Room Devices changed for the {room_name}"
    if changed_info:
        return f"Information Sources changed for the {room_name}"
    if changed_persona:
        return f"Room Persona changed for the {room_name}"
    return f"Room configuration changed for the {room_name}"


def _active_mobile_targets(profile: PersonProfile) -> list[str]:
    """Return enabled mobile notify targets for a person profile."""
    return [target for target in profile.mobile_notify_targets if isinstance(target, str) and target]


def _select_mobile_target(profile: PersonProfile, requested_target: str | None = None) -> str:
    """Choose a valid mobile target for a person using profile defaults."""
    targets = _active_mobile_targets(profile)
    if not targets:
        raise vol.Invalid("person has no enabled mobile targets")

    if requested_target:
        if requested_target not in targets:
            raise vol.Invalid("target_id is not enabled for this person")
        return requested_target

    if profile.preferred_mobile_target and profile.preferred_mobile_target in targets:
        return profile.preferred_mobile_target

    return targets[0]


def _parse_iso_datetime(value: str | None) -> datetime | None:
    """Parse ISO datetime strings while tolerating trailing Z timezone marker."""
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _voice_profile_id_for_person(person_id: str) -> str:
    """Build a stable voice profile identifier from a person entity id."""
    normalized = str(person_id or "").strip().lower().replace(".", "_").replace(" ", "_")
    normalized = "".join(ch for ch in normalized if ch.isalnum() or ch in {"_", "-"})
    return f"{normalized or 'person'}_voice"


def _session_state_from_legacy_enrollment_state(enrollment_state: str, sample_count: int) -> str:
    """Map legacy voice profile enrollment state strings onto session lifecycle states."""
    value = str(enrollment_state or "").strip().lower()
    if value == "trained":
        return "completed_pending_cleanup"
    if value == "untrained":
        return "idle"
    if sample_count > 0:
        return "sample_received"
    return "ready"


def _project_voice_profile_from_session(
    *,
    existing_voice: VoiceProfile | None,
    voice_profile_id: str,
    name: str,
    session,
    enrollment_source: str,
    speaker_embedding_id: str,
    attribution_confidence: float | None,
    disabled: bool,
    consent: dict[str, Any],
    tts_voice: str,
) -> VoiceProfile:
    """Project VoiceProfile lifecycle fields from authoritative EnrollmentSession state."""
    return VoiceProfile(
        voice_profile_id=voice_profile_id,
        name=name,
        tts_voice=tts_voice,
        enrollment_state=legacy_voice_profile_enrollment_state(session),
        enrollment_source=enrollment_source,
        speaker_embedding_id=speaker_embedding_id,
        sample_count=session.sample_count,
        sample_items=list(session.sample_items),
        attribution_confidence=attribution_confidence,
        enrollment_started_at=session.enrollment_started_at,
        last_sample_at=session.last_sample_at,
        last_built_at=session.last_built_at,
        disabled=disabled,
        consent=dict(consent),
    )


def _voice_confidence_for_sample_count(sample_count: int) -> float:
    """Return deterministic confidence estimate based on captured sample count."""
    bounded = max(0, int(sample_count))
    return min(0.95, 0.55 + (0.05 * bounded))


def _sample_recording_paths(sample_items: list[dict[str, Any]]) -> list[str]:
    """Return recording_path values from sample metadata for provider-owned resolution."""
    paths: list[str] = []
    for sample in sample_items:
        raw_path = str(sample.get("recording_path", "") or "").strip()
        if raw_path:
            paths.append(raw_path)
    return paths


def _voice_storage_provider_from_hass(hass: HomeAssistant) -> MountedPathEnrollmentStorageProvider | None:
    """Return mounted-path provider when Concierge attached storage is configured."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return None

    archive_options = archive_options_from_entry(entries[0])
    destination_uri = str(archive_options.get("destination_uri", "") or "").strip()
    destination_configured = bool(archive_options.get("destination_configured", False))
    if not destination_configured or not destination_uri:
        return None

    try:
        root_path = resolve_voice_enrollment_root(destination_uri)
    except ValueError:
        return None

    return MountedPathEnrollmentStorageProvider(
        root_path=root_path,
        hass_config_path=Path(hass.config.path()),
    )


async def _async_sync_session_manifest(
    hass: HomeAssistant,
    session: EnrollmentSession,
    *,
    target_sample_count: int | None = None,
) -> None:
    """Persist atomic provider-owned session manifest from authoritative session state."""
    provider = _voice_storage_provider_from_hass(hass)
    if provider is None:
        return

    readiness = await hass.async_add_executor_job(provider.validate_ready)
    if not readiness.ready:
        return

    existing_manifest = await hass.async_add_executor_job(
        lambda: provider.read_session_manifest(session.session_id)
    )
    effective_target = resolve_manifest_target_sample_count(
        session,
        requested_target_sample_count=target_sample_count,
        existing_target_sample_count=(
            int(existing_manifest.target_sample_count)
            if existing_manifest is not None
            else None
        ),
        default_target_sample_count=_DEFAULT_TARGET_SAMPLE_COUNT,
    )
    manifest_payload = build_enrollment_session_manifest_payload(
        session,
        target_sample_count=effective_target,
    )
    await hass.async_add_executor_job(lambda: provider.upsert_session_manifest(manifest_payload))


async def _async_require_storage_preflight(
    hass: HomeAssistant,
) -> MountedPathEnrollmentStorageProvider:
    """Fail-closed enrollment storage preflight gate for capture/enrollment paths."""
    provider = _voice_storage_provider_from_hass(hass)
    if provider is None:
        await async_create_or_update_storage_issue(
            hass,
            failure_code=VOICE_ENROLLMENT_PREFLIGHT_STORAGE_NOT_CONFIGURED,
        )
        raise vol.Invalid(
            f"external enrollment storage preflight failed: {VOICE_ENROLLMENT_PREFLIGHT_STORAGE_NOT_CONFIGURED}"
        )

    readiness = await hass.async_add_executor_job(provider.validate_ready)
    if readiness.ready:
        await async_clear_storage_issue(hass)
        return provider

    failure_code = str(readiness.failure_code or VOICE_ENROLLMENT_PREFLIGHT_STORAGE_UNKNOWN_FAILURE)
    failure_message = str(readiness.failure_message_safe or "external enrollment storage preflight failed")
    await async_create_or_update_storage_issue(
        hass,
        failure_code=failure_code,
        provider_type=str(readiness.provider_type or "mounted_path"),
    )
    raise vol.Invalid(f"{failure_message}: {failure_code}")


async def _async_execute_enrollment_cleanup(
    hass: HomeAssistant,
    storage: ConciergeStorage,
    session: EnrollmentSession,
    *,
    cleanup_reason: str,
) -> tuple[EnrollmentSession, dict[str, Any]]:
    """Execute provider-backed cleanup while keeping session + manifest synchronized."""
    reason_value = str(cleanup_reason or VOICE_ENROLLMENT_CLEANUP_REASON_UNKNOWN).strip().lower()
    if reason_value not in {
        VOICE_ENROLLMENT_CLEANUP_REASON_COMPLETED,
        VOICE_ENROLLMENT_CLEANUP_REASON_CANCELLED,
        VOICE_ENROLLMENT_CLEANUP_REASON_FAILED,
        VOICE_ENROLLMENT_CLEANUP_REASON_TIMEOUT,
        VOICE_ENROLLMENT_CLEANUP_REASON_MANUAL,
        VOICE_ENROLLMENT_CLEANUP_REASON_UNKNOWN,
    }:
        reason_value = VOICE_ENROLLMENT_CLEANUP_REASON_UNKNOWN

    pending = enrollment_session_mark_cleanup_pending(session, cleanup_reason=reason_value)
    pending = await storage.async_update_enrollment_session(
        session_id=pending.session_id,
        state_name=pending.state,
        sample_count=pending.sample_count,
        sample_items=list(pending.sample_items),
        enrollment_started_at=pending.enrollment_started_at,
        last_sample_at=pending.last_sample_at,
        last_built_at=pending.last_built_at,
        cleanup_status=pending.cleanup_status,
        metadata=dict(pending.metadata),
    )
    await _async_sync_session_manifest(hass, pending)

    running_started_at = datetime.now(timezone.utc).isoformat()
    running = enrollment_session_mark_cleanup_running(
        pending,
        cleanup_reason=reason_value,
        cleanup_started_at=running_started_at,
    )
    running = await storage.async_update_enrollment_session(
        session_id=running.session_id,
        state_name=running.state,
        sample_count=running.sample_count,
        sample_items=list(running.sample_items),
        enrollment_started_at=running.enrollment_started_at,
        last_sample_at=running.last_sample_at,
        last_built_at=running.last_built_at,
        cleanup_status=running.cleanup_status,
        metadata=dict(running.metadata),
    )
    await _async_sync_session_manifest(hass, running)

    provider = _voice_storage_provider_from_hass(hass)
    if provider is None:
        completed_at = datetime.now(timezone.utc).isoformat()
        await async_create_or_update_cleanup_issue(
            hass,
            cleanup_result_code=VOICE_ENROLLMENT_CLEANUP_RESULT_FAILED,
            cleanup_reason=reason_value,
        )
        failed = enrollment_session_mark_cleanup_failed(
            running,
            cleanup_reason=reason_value,
            cleanup_result_code=VOICE_ENROLLMENT_CLEANUP_RESULT_FAILED,
            cleanup_started_at=running_started_at,
            cleanup_completed_at=completed_at,
            artifacts_seen_count=0,
            artifacts_deleted_count=0,
            artifacts_missing_count=0,
            error_count=1,
        )
        failed = await storage.async_update_enrollment_session(
            session_id=failed.session_id,
            state_name=failed.state,
            sample_count=failed.sample_count,
            sample_items=list(failed.sample_items),
            enrollment_started_at=failed.enrollment_started_at,
            last_sample_at=failed.last_sample_at,
            last_built_at=failed.last_built_at,
            cleanup_status=failed.cleanup_status,
            metadata=dict(failed.metadata),
        )
        await _async_sync_session_manifest(hass, failed)
        return failed, {
            "cleanup_reason": reason_value,
            "cleanup_result_code": VOICE_ENROLLMENT_CLEANUP_RESULT_FAILED,
            "artifacts_seen_count": 0,
            "artifacts_deleted_count": 0,
            "artifacts_missing_count": 0,
            "errors_redacted_or_sanitized": ["provider_unavailable"],
            "cleanup_started_at": running_started_at,
            "cleanup_completed_at": completed_at,
        }

    manager = EnrollmentCleanupManager(provider)
    cleanup_result = await hass.async_add_executor_job(
        lambda: manager.cleanup(
            EnrollmentCleanupRequest(
                session=running,
                cleanup_reason=reason_value,
            )
        )
    )

    if cleanup_result.cleanup_result_code in {"failed", "partial"}:
        await async_create_or_update_cleanup_issue(
            hass,
            cleanup_result_code=cleanup_result.cleanup_result_code,
            cleanup_reason=cleanup_result.cleanup_reason,
        )
        finalized = enrollment_session_mark_cleanup_failed(
            running,
            cleanup_reason=cleanup_result.cleanup_reason,
            cleanup_result_code=cleanup_result.cleanup_result_code,
            cleanup_started_at=cleanup_result.cleanup_started_at,
            cleanup_completed_at=cleanup_result.cleanup_completed_at,
            artifacts_seen_count=cleanup_result.artifacts_seen_count,
            artifacts_deleted_count=cleanup_result.artifacts_deleted_count,
            artifacts_missing_count=cleanup_result.artifacts_missing_count,
            error_count=len(cleanup_result.errors_redacted_or_sanitized),
        )
    else:
        await async_clear_cleanup_issue(hass)
        finalized = enrollment_session_mark_cleanup_complete(
            running,
            cleanup_reason=cleanup_result.cleanup_reason,
            cleanup_result_code=cleanup_result.cleanup_result_code,
            cleanup_started_at=cleanup_result.cleanup_started_at,
            cleanup_completed_at=cleanup_result.cleanup_completed_at,
            artifacts_seen_count=cleanup_result.artifacts_seen_count,
            artifacts_deleted_count=cleanup_result.artifacts_deleted_count,
            artifacts_missing_count=cleanup_result.artifacts_missing_count,
        )

    finalized = await storage.async_update_enrollment_session(
        session_id=finalized.session_id,
        state_name=finalized.state,
        sample_count=finalized.sample_count,
        sample_items=list(finalized.sample_items),
        enrollment_started_at=finalized.enrollment_started_at,
        last_sample_at=finalized.last_sample_at,
        last_built_at=finalized.last_built_at,
        cleanup_status=finalized.cleanup_status,
        metadata=dict(finalized.metadata),
    )
    await _async_sync_session_manifest(hass, finalized)

    return finalized, {
        "cleanup_reason": cleanup_result.cleanup_reason,
        "cleanup_result_code": cleanup_result.cleanup_result_code,
        "artifacts_seen_count": cleanup_result.artifacts_seen_count,
        "artifacts_deleted_count": cleanup_result.artifacts_deleted_count,
        "artifacts_missing_count": cleanup_result.artifacts_missing_count,
        "errors_redacted_or_sanitized": list(cleanup_result.errors_redacted_or_sanitized),
        "cleanup_started_at": cleanup_result.cleanup_started_at,
        "cleanup_completed_at": cleanup_result.cleanup_completed_at,
    }


def _event_matches_filters(event: ActivityEvent, call: ServiceCall) -> bool:
    """Apply timeline filters to one activity event."""
    start_dt = _parse_iso_datetime(call.data.get("start"))
    end_dt = _parse_iso_datetime(call.data.get("end"))
    event_start = _parse_iso_datetime(event.started_at)

    if start_dt and event_start and event_start < start_dt:
        return False
    if end_dt and event_start and event_start > end_dt:
        return False
    if call.data.get("actor_class") and event.actor_class != call.data["actor_class"]:
        return False
    if call.data.get("person_id") and event.resolved_person_id != call.data["person_id"]:
        return False
    if call.data.get("area_id") and event.resolved_area_id != call.data["area_id"]:
        return False
    if call.data.get("channel") and event.channel != call.data["channel"]:
        return False
    return True


def _archive_destination_path(destination_uri: str) -> Path:
    """Resolve configured archive destination URI to a local/UNC path."""
    raw = destination_uri.strip()
    if not raw:
        raise vol.Invalid("archive destination is required")

    if raw.lower().startswith("file://"):
        parsed = urlparse(raw)
        path_value = unquote(parsed.path or "")
        if parsed.netloc:
            path_value = f"//{parsed.netloc}{path_value}"
        return Path(path_value)

    # Accept UNC-style //server/share and Windows drive paths.
    return Path(raw)


def _serialize_activity(event: ActivityEvent, include_reference_excerpts: bool) -> dict[str, Any]:
    """Project activity event to stable payload for timeline/archive outputs."""
    payload = {
        "activity_id": event.activity_id,
        "correlation_id": event.correlation_id,
        "started_at": event.started_at,
        "ended_at": event.ended_at,
        "channel": event.channel,
        "actor_class": event.actor_class,
        "intent_class": event.intent_class,
        "request_summary": _sanitize_request_summary(event.actor_class, event.request_summary),
        "resolved_person_id": event.resolved_person_id,
        "resolved_area_id": event.resolved_area_id,
        "confidence": event.confidence,
        "outcome": event.outcome,
        "outcome_reason": event.outcome_reason,
        "actions_taken": list(event.actions_taken),
        "policy_gates": list(event.policy_gates),
    }
    payload["external_refs"] = list(event.external_refs) if include_reference_excerpts else []
    return payload


def _effective_minor_fields(call: ServiceCall) -> tuple[bool, bool, list[str], str, bool, bool]:
    """Resolve explicit minor policy fields with consent fallback for UI compatibility."""
    consent = dict(call.data.get("consent", {}))
    classification = consent.get("household_classification", {}) if isinstance(consent, dict) else {}
    minor_policy = consent.get("minor_interaction_policy", {}) if isinstance(consent, dict) else {}
    targets = consent.get("interaction_targets", {}) if isinstance(consent, dict) else {}

    is_minor = bool(call.data.get("is_minor", classification.get("is_minor", False)))
    guardian_controls_required = bool(
        call.data.get(
            "guardian_controls_required",
            classification.get("guardian_controls_required", is_minor),
        )
    )
    minor_allow_general_qna = bool(
        call.data.get(
            "minor_allow_general_qna",
            minor_policy.get("allow_general_qna", False),
        )
    )
    minor_allowed_intent_classes = list(
        call.data.get(
            "minor_allowed_intent_classes",
            minor_policy.get("allowed_intent_classes", ["room_context_info", "household_help"]),
        )
    )
    minor_content_filter_level = str(
        call.data.get(
            "minor_content_filter_level",
            minor_policy.get("enforce_content_filter_level", "strict"),
        )
    )
    mobile_voice_endpoint_enabled = bool(
        call.data.get(
            "mobile_voice_endpoint_enabled",
            targets.get("mobile_voice_endpoint_enabled", False),
        )
    )

    return (
        is_minor,
        guardian_controls_required,
        minor_allowed_intent_classes,
        minor_content_filter_level,
        minor_allow_general_qna,
        mobile_voice_endpoint_enabled,
    )


def _resolve_integration_capabilities(hass: HomeAssistant) -> dict[str, bool]:
    """Resolve Concierge capability flags from config entry options/data."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return {
            "cap_ai": False,
            "cap_tts": False,
            "cap_persona": False,
            "cap_assets": False,
            "cap_voice_enrollment": False,
            "cap_extended_history": False,
        }

    entry = entries[0]
    options = entry.options
    data = entry.data

    ai_enabled = bool(options.get("ai_enabled", data.get("ai_enabled", False)))
    action_provider = str(
        options.get("action_provider", data.get("action_provider", _PROVIDER_NONE))
        or _PROVIDER_NONE
    ).strip() or _PROVIDER_NONE
    tts_enabled = bool(options.get("tts_enabled", data.get("tts_enabled", False)))
    tts_provider = str(
        options.get("tts_provider", data.get("tts_provider", _PROVIDER_NONE))
        or _PROVIDER_NONE
    ).strip() or _PROVIDER_NONE
    asset_intelligence_provider = str(
        options.get(
            "asset_intelligence_provider",
            data.get("asset_intelligence_provider", _PROVIDER_NONE),
        )
        or _PROVIDER_NONE
    ).strip() or _PROVIDER_NONE

    archive_options = archive_options_from_entry(entry)
    cap_ai = bool(ai_enabled and action_provider != _PROVIDER_NONE)
    cap_tts = bool(tts_enabled and tts_provider != _PROVIDER_NONE)
    cap_persona = bool(cap_ai or cap_tts)
    cap_assets = bool(asset_intelligence_provider == _PROVIDER_ASSET_INTELLIGENCE)
    cap_voice_enrollment = bool(
        archive_options.get("destination_configured") and archive_options.get("archive_enabled")
    )
    cap_extended_history = bool(
        archive_options.get("destination_configured") and archive_options.get("archive_enabled")
    )

    return {
        "cap_ai": cap_ai,
        "cap_tts": cap_tts,
        "cap_persona": cap_persona,
        "cap_assets": cap_assets,
        "cap_voice_enrollment": cap_voice_enrollment,
        "cap_extended_history": cap_extended_history,
    }


def _enforce_minor_intent_policy(
    *,
    state,
    person_id: str | None,
    intent_class: str,
) -> None:
    """Block disallowed intent classes for minors based on configured person policy."""
    if not person_id:
        return
    profile = state.person_profiles.get(person_id)
    if profile is None or not profile.is_minor:
        return

    allowed = set(profile.minor_allowed_intent_classes)
    if intent_class == "general_qna" and not profile.minor_allow_general_qna:
        raise vol.Invalid("minor_policy_denied: general_qna_disabled")

    if allowed and intent_class not in allowed and not (
        intent_class == "general_qna" and profile.minor_allow_general_qna
    ):
        raise vol.Invalid("minor_policy_denied: intent_class_not_allowed")


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

    async def _runner() -> dict[str, Any]:
        _enforce_minor_intent_policy(
            state=state,
            person_id=call.data.get("person_id"),
            intent_class=call.data.get("intent_class", "home_control"),
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

    return await _async_with_activity(
        hass,
        call,
        intent_class="execute_orchestration",
        request_summary=f"Execute request for {_area_name(hass, area_id)}",
        action_name="execute",
        resolved_area_id=area_id,
        resolved_person_id=call.data.get("person_id"),
        channel="service_execute",
        external_refs=[{"ref_type": "execute_target", "target": call.data["target"], "resolved_target": resolved_target}],
        runner=_runner,
    )


async def _async_handle_execute_direct(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    """Execute a direct service/entity action without orchestration."""
    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    service_ref = call.data["service"]

    async def _runner() -> dict[str, Any]:
        _enforce_minor_intent_policy(
            state=state,
            person_id=call.data.get("person_id"),
            intent_class=call.data.get("intent_class", "home_control"),
        )

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

    return await _async_with_activity(
        hass,
        call,
        intent_class="execute_direct",
        request_summary=f"Direct execution request for {call.data.get('entity_id', 'entity')}",
        action_name="execute_direct",
        resolved_person_id=call.data.get("person_id"),
        channel="service_execute",
        external_refs=[{"ref_type": "execute_direct", "entity_id": call.data.get("entity_id"), "service": service_ref}],
        runner=_runner,
    )


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
    async def _runner() -> dict[str, Any]:
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

    return await _async_with_activity(
        hass,
        call,
        intent_class="update_interaction",
        request_summary="Interaction state updated",
        action_name="update_interaction",
        resolved_area_id=call.data.get("area_id"),
        channel="service_mutation",
        external_refs=[{"ref_type": "interaction", "interaction_id": call.data.get("interaction_id")}],
        runner=_runner,
    )


async def _async_handle_clear_interaction(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    """Remove an interaction from runtime state."""
    async def _runner() -> dict[str, Any]:
        storage = ConciergeStorage(hass)
        state = await storage.async_remove_interaction(call.data["interaction_id"])
        return {"interaction_count": len(state.interactions)}

    return await _async_with_activity(
        hass,
        call,
        intent_class="clear_interaction",
        request_summary="Interaction cleared",
        action_name="clear_interaction",
        channel="service_mutation",
        external_refs=[{"ref_type": "interaction", "interaction_id": call.data.get("interaction_id")}],
        runner=_runner,
    )


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
    area_id = call.data["area_id"]
    changed_keys = {key for key in call.data.keys() if key != "area_id"}
    aliases = call.data.get("aliases")
    global_overlays = call.data.get("global_overlays")
    media_player_entity_ids = call.data.get("media_player_entity_ids")
    voice_device_entity_ids = call.data.get("voice_device_entity_ids")
    device_groups = call.data.get("device_groups")
    asset_groups = call.data.get("asset_groups")
    room_sensor_entity_ids = call.data.get("room_sensor_entity_ids")
    room_health_entity_ids = call.data.get("room_health_entity_ids")
    human_health_entity_ids = call.data.get("human_health_entity_ids")
    light_entity_ids = call.data.get("light_entity_ids")
    lamp_entity_ids = call.data.get("lamp_entity_ids")
    shade_entity_ids = call.data.get("shade_entity_ids")
    speaker_entity_ids = call.data.get("speaker_entity_ids")
    tv_entity_ids = call.data.get("tv_entity_ids")
    dashboard_entity_ids = call.data.get("dashboard_entity_ids")
    other_entity_ids = call.data.get("other_entity_ids")
    weather_source_entity_ids = call.data.get("weather_source_entity_ids")
    news_source_entity_ids = call.data.get("news_source_entity_ids")
    environment_information_outputs = call.data.get("environment_information_outputs")
    persona = call.data.get("persona")
    persona_prompt = call.data.get("persona_prompt")
    tts_voice = call.data.get("tts_voice")
    tts_language = call.data.get("tts_language")
    ai_knowledge_enabled = call.data.get("ai_knowledge_enabled")
    capabilities = _resolve_integration_capabilities(hass)

    if not capabilities["cap_ai"] and ai_knowledge_enabled is not None:
        ai_knowledge_enabled = False
    if not capabilities["cap_assets"]:
        if asset_groups is not None:
            asset_groups = []
        if environment_information_outputs is not None:
            environment_information_outputs = []
    if not capabilities["cap_persona"]:
        if persona is not None:
            persona = ""
        if persona_prompt is not None:
            persona_prompt = ""
        if tts_voice is not None:
            tts_voice = ""
        if tts_language is not None:
            tts_language = ""
    elif not capabilities["cap_tts"]:
        if tts_voice is not None:
            tts_voice = ""
        if tts_language is not None:
            tts_language = ""
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
    if device_groups is not None and not isinstance(device_groups, list):
        raise vol.Invalid("device_groups values must be lists")
    if asset_groups is not None and not isinstance(asset_groups, list):
        raise vol.Invalid("asset_groups values must be lists")
    for field_name, entity_ids in (
        ("room_sensor_entity_ids", room_sensor_entity_ids),
        ("room_health_entity_ids", room_health_entity_ids),
        ("human_health_entity_ids", human_health_entity_ids),
        ("light_entity_ids", light_entity_ids),
        ("lamp_entity_ids", lamp_entity_ids),
        ("shade_entity_ids", shade_entity_ids),
        ("speaker_entity_ids", speaker_entity_ids),
        ("tv_entity_ids", tv_entity_ids),
        ("dashboard_entity_ids", dashboard_entity_ids),
        ("other_entity_ids", other_entity_ids),
        ("weather_source_entity_ids", weather_source_entity_ids),
        ("news_source_entity_ids", news_source_entity_ids),
        ("environment_information_outputs", environment_information_outputs),
    ):
        if entity_ids is not None and not all(isinstance(v, str) for v in entity_ids):
            raise vol.Invalid(f"{field_name} values must be strings")

    storage = ConciergeStorage(hass)
    before_state = await storage.async_load_state()
    before_room = before_state.rooms.get(area_id)
    started_at = datetime.now(timezone.utc).isoformat()
    activity_id = _new_activity_id("room_cfg")
    area_name = _area_name(hass, area_id)

    await storage.async_record_activity_event(
        ActivityEvent(
            activity_id=activity_id,
            correlation_id=activity_id,
            started_at=started_at,
            channel="service_mutation",
            actor_class="concierge",
            intent_class="room_config_update",
            request_summary=f"Room configuration update requested for the {area_name}",
            resolved_area_id=area_id,
            confidence=1.0,
            external_refs=[],
        )
    )

    try:
        state = await storage.async_update_room_config(
            area_id=area_id,
            aliases=aliases,
            global_overlays=global_overlays,
            posture=call.data.get("posture"),
            media_player_entity_ids=media_player_entity_ids,
            voice_device_entity_ids=voice_device_entity_ids,
            tts_voice=tts_voice,
            tts_language=tts_language,
            ai_knowledge_enabled=ai_knowledge_enabled,
            environment_information_outputs=environment_information_outputs,
            device_groups=device_groups,
            asset_groups=asset_groups,
            room_sensor_entity_ids=room_sensor_entity_ids,
            room_health_entity_ids=room_health_entity_ids,
            human_health_entity_ids=human_health_entity_ids,
            light_entity_ids=light_entity_ids,
            lamp_entity_ids=lamp_entity_ids,
            shade_entity_ids=shade_entity_ids,
            speaker_entity_ids=speaker_entity_ids,
            tv_entity_ids=tv_entity_ids,
            dashboard_entity_ids=dashboard_entity_ids,
            other_entity_ids=other_entity_ids,
            weather_source_entity_ids=weather_source_entity_ids,
            news_source_entity_ids=news_source_entity_ids,
            persona=persona,
            persona_prompt=persona_prompt,
        )
    except vol.Invalid as err:
        reason = _safe_outcome_reason(err)
        deny_policy: list[str] = []
        if "minor_policy_denied" in reason:
            deny_policy.append("minor_policy")
        await storage.async_close_activity_event(
            activity_id=activity_id,
            ended_at=datetime.now(timezone.utc).isoformat(),
            outcome="policy_denied",
            outcome_reason=reason,
            actions_taken=["update_room_config"],
            policy_gates=deny_policy,
        )
        raise
    except Exception as err:
        await storage.async_close_activity_event(
            activity_id=activity_id,
            ended_at=datetime.now(timezone.utc).isoformat(),
            outcome="error",
            outcome_reason=_safe_outcome_reason(err),
            actions_taken=["update_room_config"],
            policy_gates=[],
        )
        raise

    after_room = state.rooms.get(area_id)
    diff_changes = _build_room_config_diff(hass, before_room, after_room, changed_keys)
    summary = _summarize_room_update(area_name, changed_keys, diff_changes)

    if diff_changes:
        try:
            activity = (await storage.async_load_state()).activities.get(activity_id)
            if activity is not None:
                activity.request_summary = summary
                activity.external_refs = [
                    {
                        "ref_type": "room_config_diff",
                        "changes": diff_changes,
                    }
                ]
                await storage.async_record_activity_event(activity)
        except Exception:
            # Activity enrichment should not block successful configuration writes.
            pass

    await storage.async_close_activity_event(
        activity_id=activity_id,
        ended_at=datetime.now(timezone.utc).isoformat(),
        outcome="success",
        outcome_reason="",
        actions_taken=["update_room_config"],
        policy_gates=[],
    )
    return {"room_count": len(state.rooms)}


async def _async_handle_update_identity_profile(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Insert or update identity preferences for Concierge presentation."""
    async def _runner() -> dict[str, Any]:
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

    return await _async_with_activity(
        hass,
        call,
        intent_class="update_identity_profile",
        request_summary=f"Identity profile updated: {call.data.get('name', call.data.get('profile_id', 'profile'))}",
        action_name="update_identity_profile",
        channel="service_mutation",
        external_refs=[{"ref_type": "identity_profile", "profile_id": call.data.get("profile_id")}],
        runner=_runner,
    )


async def _async_handle_update_person_profile(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Insert or update person identity and consent state."""
    consent = dict(call.data.get("consent", {}))
    interaction_targets = (
        consent.get("interaction_targets", {}) if isinstance(consent, dict) else {}
    )
    mobile_notify_targets = list(
        call.data.get("mobile_notify_targets", interaction_targets.get("mobile_notify_targets", []))
    )
    preferred_mobile_target = call.data.get(
        "preferred_mobile_target",
        interaction_targets.get("preferred_mobile_target"),
    )
    (
        is_minor,
        guardian_controls_required,
        minor_allowed_intent_classes,
        minor_content_filter_level,
        minor_allow_general_qna,
        mobile_voice_endpoint_enabled,
    ) = _effective_minor_fields(call)
    capabilities = _resolve_integration_capabilities(hass)
    voice_profile_id = call.data.get("voice_profile_id")

    if not capabilities["cap_ai"]:
        minor_allow_general_qna = False
        minor_allowed_intent_classes = ["room_context_info", "household_help"]
        minor_content_filter_level = "strict"

    if not capabilities["cap_tts"]:
        mobile_voice_endpoint_enabled = False
        voice_profile_id = None

    if is_minor and not minor_allowed_intent_classes:
        raise vol.Invalid("minor_allowed_intent_classes must not be empty when is_minor is true")

    if preferred_mobile_target and preferred_mobile_target not in mobile_notify_targets:
        raise vol.Invalid("preferred_mobile_target must be in mobile_notify_targets")

    async def _runner() -> dict[str, Any]:
        storage = ConciergeStorage(hass)
        profile = PersonProfile(
            person_id=call.data["person_id"],
            name=call.data["name"],
            linked_area_id=call.data.get("linked_area_id"),
            ble_device_ids=list(call.data.get("ble_device_ids", [])),
            aqara_presence_entity_ids=list(call.data.get("aqara_presence_entity_ids", [])),
            voice_profile_id=voice_profile_id,
            consent=consent,
            mobile_notify_targets=mobile_notify_targets,
            preferred_mobile_target=preferred_mobile_target,
            mobile_voice_endpoint_enabled=mobile_voice_endpoint_enabled,
            is_minor=is_minor,
            guardian_controls_required=guardian_controls_required,
            minor_allow_general_qna=minor_allow_general_qna,
            minor_allowed_intent_classes=minor_allowed_intent_classes,
            minor_content_filter_level=minor_content_filter_level,
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

    return await _async_with_activity(
        hass,
        call,
        intent_class="update_person_profile",
        request_summary=f"Person profile updated: {call.data.get('name', call.data.get('person_id', 'person'))}",
        action_name="update_person_profile",
        resolved_person_id=call.data.get("person_id"),
        resolved_area_id=call.data.get("linked_area_id"),
        channel="service_mutation",
        external_refs=[{"ref_type": "person_profile", "person_id": call.data.get("person_id")}],
        runner=_runner,
    )


async def _async_handle_update_voice_profile(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Insert or update voice enrollment and attribution state."""
    async def _runner() -> dict[str, Any]:
        await _async_require_storage_preflight(hass)

        storage = ConciergeStorage(hass)
        state = await storage.async_load_state()
        voice_profile_id = call.data["voice_profile_id"]
        existing_voice = state.voice_profiles.get(voice_profile_id)

        requested_sample_items = list(call.data.get("sample_items", []))
        requested_sample_count = int(call.data.get("sample_count", len(requested_sample_items)))
        if requested_sample_count != len(requested_sample_items) and requested_sample_items:
            requested_sample_count = len(requested_sample_items)

        session = await storage.async_get_latest_enrollment_session_for_voice_profile(voice_profile_id)
        if session is None:
            now_iso = datetime.now(timezone.utc).isoformat()
            session = await storage.async_create_enrollment_session(
                session_id=f"session_{int(datetime.now(timezone.utc).timestamp() * 1000)}_{uuid4().hex[:8]}",
                person_id="",
                voice_profile_id=voice_profile_id,
                state_name=_session_state_from_legacy_enrollment_state(
                    call.data.get("enrollment_state", "untrained"),
                    requested_sample_count,
                ),
                sample_count=requested_sample_count,
                sample_items=requested_sample_items,
                enrollment_started_at=call.data.get("enrollment_started_at", now_iso),
                last_sample_at=call.data.get("last_sample_at", ""),
                last_built_at=call.data.get("last_built_at", ""),
            )
        else:
            session = await storage.async_update_enrollment_session(
                session_id=session.session_id,
                state_name=_session_state_from_legacy_enrollment_state(
                    call.data.get("enrollment_state", legacy_voice_profile_enrollment_state(session)),
                    requested_sample_count,
                ),
                sample_count=requested_sample_count,
                sample_items=requested_sample_items,
                enrollment_started_at=(
                    call.data.get("enrollment_started_at", session.enrollment_started_at)
                ),
                last_sample_at=call.data.get("last_sample_at", session.last_sample_at),
                last_built_at=call.data.get("last_built_at", session.last_built_at),
            )

        # Legacy compatibility path: keep session+manifest in lockstep even when
        # voice profile mutation is requested outside guided enrollment flows.
        await _async_sync_session_manifest(
            hass,
            session,
            target_sample_count=max(1, requested_sample_count or _DEFAULT_TARGET_SAMPLE_COUNT),
        )

        profile = _project_voice_profile_from_session(
            existing_voice=existing_voice,
            voice_profile_id=voice_profile_id,
            name=call.data["name"],
            session=session,
            enrollment_source=call.data.get("enrollment_source", ""),
            speaker_embedding_id=call.data.get("speaker_embedding_id", ""),
            attribution_confidence=(
                float(call.data["attribution_confidence"])
                if call.data.get("attribution_confidence") is not None
                else None
            ),
            disabled=bool(call.data.get("disabled", False)),
            consent=dict(call.data.get("consent", {})),
            tts_voice=call.data.get("tts_voice", ""),
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

    return await _async_with_activity(
        hass,
        call,
        intent_class="update_voice_profile",
        request_summary=f"Voice profile updated: {call.data.get('name', call.data.get('voice_profile_id', 'voice'))}",
        action_name="update_voice_profile",
        channel="service_mutation",
        external_refs=[{"ref_type": "voice_profile", "voice_profile_id": call.data.get("voice_profile_id")}],
        runner=_runner,
    )


async def _async_handle_start_voice_enrollment(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Start or resume explicit voice enrollment for a person profile."""
    capabilities = _resolve_integration_capabilities(hass)
    if not capabilities["cap_voice_enrollment"]:
        raise vol.Invalid(
            "voice enrollment is unavailable until attached storage and archive export are enabled in Concierge options"
        )
    person_id = call.data["person_id"]
    if not bool(call.data.get("consent_acknowledged", False)):
        raise vol.Invalid("voice enrollment requires explicit consent_acknowledged=true")

    async def _runner() -> dict[str, Any]:
        provider = await _async_require_storage_preflight(hass)

        storage = ConciergeStorage(hass)
        state = await storage.async_load_state()
        existing_person = state.person_profiles.get(person_id)
        person_name = (
            existing_person.name
            if existing_person is not None
            else str(call.data.get("voice_name") or person_id)
        )
        voice_profile_id = (
            str(call.data.get("voice_profile_id") or "").strip()
            or str(existing_person.voice_profile_id or "").strip()
            if existing_person is not None
            else ""
        )
        if not voice_profile_id:
            voice_profile_id = _voice_profile_id_for_person(person_id)

        existing_voice = state.voice_profiles.get(voice_profile_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        existing_consent = dict(existing_voice.consent) if existing_voice is not None else {}
        voice_consent = dict(existing_consent.get("voice_enrollment", {}))
        local_only = bool(call.data.get("local_only", True))
        voice_consent.update(
            {
                "enabled": True,
                "local_only": local_only,
                "consent_acknowledged": True,
                "consent_acknowledged_at": now_iso,
            }
        )
        merged_consent = {
            **existing_consent,
            "voice_enrollment": voice_consent,
        }

        session = enrollment_session_for_start(
            person_id=person_id,
            voice_profile_id=voice_profile_id,
            existing_sample_items=list(existing_voice.sample_items) if existing_voice is not None else [],
            enrollment_started_at=(
                existing_voice.enrollment_started_at if existing_voice and existing_voice.enrollment_started_at else now_iso
            ),
        )
        await storage.async_upsert_enrollment_session(session)
        await _async_sync_session_manifest(
            hass,
            session,
            target_sample_count=_DEFAULT_TARGET_SAMPLE_COUNT,
        )

        profile = _project_voice_profile_from_session(
            existing_voice=existing_voice,
            voice_profile_id=voice_profile_id,
            name=str(call.data.get("voice_name") or person_name),
            session=session,
            enrollment_source=(existing_voice.enrollment_source if existing_voice is not None else "people_setup")
            or "people_setup",
            speaker_embedding_id=existing_voice.speaker_embedding_id if existing_voice is not None else "",
            attribution_confidence=existing_voice.attribution_confidence if existing_voice is not None else None,
            disabled=False,
            consent=merged_consent,
            tts_voice=existing_voice.tts_voice if existing_voice is not None else "",
        )
        await storage.async_update_voice_profile(profile)

        if existing_person is not None:
            person_profile = PersonProfile(
                person_id=existing_person.person_id,
                name=existing_person.name,
                linked_area_id=existing_person.linked_area_id,
                ble_device_ids=list(existing_person.ble_device_ids),
                aqara_presence_entity_ids=list(existing_person.aqara_presence_entity_ids),
                voice_profile_id=voice_profile_id,
                consent=dict(existing_person.consent),
                mobile_notify_targets=list(existing_person.mobile_notify_targets),
                preferred_mobile_target=existing_person.preferred_mobile_target,
                mobile_voice_endpoint_enabled=existing_person.mobile_voice_endpoint_enabled,
                is_minor=existing_person.is_minor,
                guardian_controls_required=existing_person.guardian_controls_required,
                minor_allow_general_qna=existing_person.minor_allow_general_qna,
                minor_allowed_intent_classes=list(existing_person.minor_allowed_intent_classes),
                minor_content_filter_level=existing_person.minor_content_filter_level,
                notes=existing_person.notes,
            )
            await storage.async_update_person_profile(
                person_profile,
                set_as_default=(
                    state.default_person_profile is not None
                    and state.default_person_profile.person_id == person_profile.person_id
                ),
            )

        return {
            "started": True,
            "person_id": person_id,
            "voice_profile_id": voice_profile_id,
            "enrollment_session_id": session.session_id,
            "enrollment_state": profile.enrollment_state,
            "sample_count": profile.sample_count,
            "local_only": local_only,
        }

    return await _async_with_activity(
        hass,
        call,
        intent_class="start_voice_enrollment",
        request_summary=f"Voice enrollment started for {person_id}",
        action_name="start_voice_enrollment",
        resolved_person_id=person_id,
        channel="service_mutation",
        external_refs=[{"ref_type": "voice_enrollment_start", "person_id": person_id}],
        policy_gates=["explicit_consent", "local_first_default"],
        runner=_runner,
    )


async def _async_handle_capture_voice_enrollment_sample(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Capture one speech item for a voice profile during enrollment."""
    capabilities = _resolve_integration_capabilities(hass)
    if not capabilities["cap_voice_enrollment"]:
        raise vol.Invalid(
            "voice enrollment capture is unavailable until attached storage and archive export are enabled in Concierge options"
        )
    voice_profile_id = call.data["voice_profile_id"]
    speech_text = str(call.data.get("speech_text", "")).strip()
    if not speech_text:
        raise vol.Invalid("speech_text is required")

    async def _runner() -> dict[str, Any]:
        storage = ConciergeStorage(hass)
        state = await storage.async_load_state()
        existing_voice = state.voice_profiles.get(voice_profile_id)
        if existing_voice is None:
            raise vol.Invalid("voice_profile_id is not configured")
        if existing_voice.disabled:
            raise vol.Invalid("voice profile is disabled")

        now_iso = datetime.now(timezone.utc).isoformat()
        sample_id = f"sample_{int(datetime.now(timezone.utc).timestamp() * 1000)}_{uuid4().hex[:8]}"
        sample_payload: dict[str, Any] = {
            "sample_id": sample_id,
            "speech_text": speech_text,
            "captured_at": now_iso,
            "source": str(call.data.get("source", "guided_phrase") or "guided_phrase"),
        }
        if call.data.get("quality_score") is not None:
            sample_payload["quality_score"] = float(call.data["quality_score"])
        if call.data.get("recording_duration_ms") is not None:
            sample_payload["recording_duration_ms"] = int(call.data["recording_duration_ms"])
        if call.data.get("phrase_index") is not None:
            sample_payload["phrase_index"] = int(call.data["phrase_index"])

        enrollment_session = await storage.async_get_latest_enrollment_session_for_voice_profile(voice_profile_id)
        if enrollment_session is None:
            matched_person_id = ""
            for profile in state.person_profiles.values():
                if profile.voice_profile_id == voice_profile_id:
                    matched_person_id = profile.person_id
                    break
            enrollment_session = enrollment_session_for_start(
                person_id=matched_person_id,
                voice_profile_id=voice_profile_id,
                existing_sample_items=list(existing_voice.sample_items),
                enrollment_started_at=existing_voice.enrollment_started_at or now_iso,
            )

        phrase_index = call.data.get("phrase_index")
        try:
            phrase_index_value = int(phrase_index) if phrase_index is not None else None
        except (TypeError, ValueError):
            phrase_index_value = None

        preferred_path = str(call.data.get("recording_path", "") or "").strip() or None
        resolved_path = await hass.async_add_executor_job(
            lambda: provider.resolve_recording_path(
                session_id=enrollment_session.session_id,
                preferred_path=preferred_path,
                phrase_index=phrase_index_value,
            )
        )

        if resolved_path:
            sample_payload["recording_path"] = resolved_path
            artifacts = await hass.async_add_executor_job(
                lambda: provider.list_session_artifacts(enrollment_session.session_id)
            )
            matching = next(
                (artifact for artifact in artifacts if artifact.artifact_path == resolved_path),
                None,
            )
            if matching is not None:
                sample_payload["recording_size_bytes"] = int(matching.bytes_size)
            if call.data.get("recording_mime_type"):
                sample_payload["recording_mime_type"] = str(call.data["recording_mime_type"])

        enrollment_session = enrollment_session_record_sample(
            enrollment_session,
            sample_payload=sample_payload,
            captured_at=now_iso,
        )
        enrollment_session = await storage.async_update_enrollment_session(
            session_id=enrollment_session.session_id,
            state_name=enrollment_session.state,
            sample_count=enrollment_session.sample_count,
            sample_items=list(enrollment_session.sample_items),
            enrollment_started_at=enrollment_session.enrollment_started_at,
            last_sample_at=enrollment_session.last_sample_at,
            last_built_at=enrollment_session.last_built_at,
            metadata={
                **dict(enrollment_session.metadata),
                "last_sample_id": sample_id,
                "last_sample_at": now_iso,
            },
        )
        await _async_sync_session_manifest(hass, enrollment_session)

        updated = _project_voice_profile_from_session(
            existing_voice=existing_voice,
            voice_profile_id=existing_voice.voice_profile_id,
            name=existing_voice.name,
            session=enrollment_session,
            enrollment_source=existing_voice.enrollment_source,
            speaker_embedding_id=existing_voice.speaker_embedding_id,
            attribution_confidence=existing_voice.attribution_confidence,
            disabled=existing_voice.disabled,
            consent=dict(existing_voice.consent),
            tts_voice=existing_voice.tts_voice,
        )
        await storage.async_update_voice_profile(updated)

        return {
            "captured": True,
            "voice_profile_id": voice_profile_id,
            "sample_id": sample_id,
            "sample_count": updated.sample_count,
        }

    return await _async_with_activity(
        hass,
        call,
        intent_class="capture_voice_enrollment_sample",
        request_summary=f"Voice sample captured for {voice_profile_id}",
        action_name="capture_voice_enrollment_sample",
        channel="service_mutation",
        external_refs=[{"ref_type": "voice_sample", "voice_profile_id": voice_profile_id}],
        policy_gates=["local_first_default"],
        runner=_runner,
    )


async def _async_handle_remove_voice_enrollment_sample(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Remove one previously captured speech item from a voice profile."""
    capabilities = _resolve_integration_capabilities(hass)
    if not capabilities["cap_voice_enrollment"]:
        raise vol.Invalid(
            "voice enrollment sample management is unavailable until attached storage and archive export are enabled in Concierge options"
        )
    voice_profile_id = call.data["voice_profile_id"]
    sample_id = call.data["sample_id"]

    async def _runner() -> dict[str, Any]:
        storage = ConciergeStorage(hass)
        state = await storage.async_load_state()
        existing_voice = state.voice_profiles.get(voice_profile_id)
        if existing_voice is None:
            raise vol.Invalid("voice_profile_id is not configured")
        now_iso = datetime.now(timezone.utc).isoformat()
        enrollment_session = await storage.async_get_latest_enrollment_session_for_voice_profile(voice_profile_id)
        if enrollment_session is None:
            matched_person_id = ""
            for profile in state.person_profiles.values():
                if profile.voice_profile_id == voice_profile_id:
                    matched_person_id = profile.person_id
                    break
            enrollment_session = enrollment_session_for_start(
                person_id=matched_person_id,
                voice_profile_id=voice_profile_id,
                existing_sample_items=list(existing_voice.sample_items),
                enrollment_started_at=existing_voice.enrollment_started_at or now_iso,
            )

        enrollment_session, removed_items = enrollment_session_remove_sample(
            enrollment_session,
            sample_id=sample_id,
            now_iso=now_iso,
        )
        if not removed_items:
            raise vol.Invalid("sample_id not found")

        provider = _voice_storage_provider_from_hass(hass)
        enrollment_session = await storage.async_update_enrollment_session(
            session_id=enrollment_session.session_id,
            state_name=enrollment_session.state,
            sample_count=enrollment_session.sample_count,
            sample_items=list(enrollment_session.sample_items),
            enrollment_started_at=enrollment_session.enrollment_started_at,
            last_sample_at=enrollment_session.last_sample_at,
            last_built_at=enrollment_session.last_built_at,
        )
        await _async_sync_session_manifest(hass, enrollment_session)

        updated = _project_voice_profile_from_session(
            existing_voice=existing_voice,
            voice_profile_id=existing_voice.voice_profile_id,
            name=existing_voice.name,
            session=enrollment_session,
            enrollment_source=existing_voice.enrollment_source,
            speaker_embedding_id=(
                existing_voice.speaker_embedding_id if enrollment_session.sample_count > 0 else ""
            ),
            attribution_confidence=(
                existing_voice.attribution_confidence if enrollment_session.sample_count > 0 else None
            ),
            disabled=existing_voice.disabled,
            consent=dict(existing_voice.consent),
            tts_voice=existing_voice.tts_voice,
        )
        await storage.async_update_voice_profile(updated)
        if provider is not None:
            recording_paths = _sample_recording_paths(removed_items)
            if recording_paths:
                await hass.async_add_executor_job(
                    lambda: provider.delete_recording_artifacts(
                        session_id=enrollment_session.session_id,
                        artifact_paths=recording_paths,
                    )
                )
        return {
            "removed": True,
            "voice_profile_id": voice_profile_id,
            "sample_count": updated.sample_count,
        }

    return await _async_with_activity(
        hass,
        call,
        intent_class="remove_voice_enrollment_sample",
        request_summary=f"Voice sample removed for {voice_profile_id}",
        action_name="remove_voice_enrollment_sample",
        channel="service_mutation",
        external_refs=[{"ref_type": "voice_sample", "voice_profile_id": voice_profile_id, "sample_id": sample_id}],
        runner=_runner,
    )


async def _async_handle_build_voice_profile(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Build a trained voice profile from captured enrollment samples."""
    capabilities = _resolve_integration_capabilities(hass)
    if not capabilities["cap_voice_enrollment"]:
        raise vol.Invalid(
            "voice profile build is unavailable until attached storage and archive export are enabled in Concierge options"
        )
    voice_profile_id = call.data["voice_profile_id"]
    min_samples = int(call.data.get("min_samples", 3))

    async def _runner() -> dict[str, Any]:
        storage = ConciergeStorage(hass)
        state = await storage.async_load_state()
        existing_voice = state.voice_profiles.get(voice_profile_id)
        if existing_voice is None:
            raise vol.Invalid("voice_profile_id is not configured")
        if existing_voice.disabled:
            raise vol.Invalid("voice profile is disabled")

        enrollment_session = await storage.async_get_latest_enrollment_session_for_voice_profile(voice_profile_id)
        if enrollment_session is None:
            matched_person_id = ""
            for profile in state.person_profiles.values():
                if profile.voice_profile_id == voice_profile_id:
                    matched_person_id = profile.person_id
                    break
            enrollment_session = enrollment_session_for_start(
                person_id=matched_person_id,
                voice_profile_id=voice_profile_id,
                existing_sample_items=list(existing_voice.sample_items),
                enrollment_started_at=existing_voice.enrollment_started_at or datetime.now(timezone.utc).isoformat(),
            )

        sample_count = len(enrollment_session.sample_items)
        if sample_count < min_samples:
            raise vol.Invalid(f"voice profile requires at least {min_samples} samples")

        retained_sample_items = [
            {
                key: value
                for key, value in sample.items()
                if key not in {"recording_path", "recording_mime_type", "recording_size_bytes", "recording_duration_ms"}
            }
            for sample in list(enrollment_session.sample_items)
        ]

        now_iso = datetime.now(timezone.utc).isoformat()
        embedding_id = f"spk_{uuid4().hex}"
        confidence = _voice_confidence_for_sample_count(sample_count)

        enrollment_session = await storage.async_update_enrollment_session(
            session_id=enrollment_session.session_id,
            sample_count=sample_count,
            sample_items=retained_sample_items,
        )
        enrollment_session = enrollment_session_mark_profile_built(enrollment_session, built_at=now_iso)
        enrollment_session = await storage.async_update_enrollment_session(
            session_id=enrollment_session.session_id,
            state_name=enrollment_session.state,
            sample_count=enrollment_session.sample_count,
            sample_items=list(enrollment_session.sample_items),
            enrollment_started_at=enrollment_session.enrollment_started_at,
            last_sample_at=enrollment_session.last_sample_at,
            last_built_at=enrollment_session.last_built_at,
        )
        await _async_sync_session_manifest(
            hass,
            enrollment_session,
            target_sample_count=min_samples,
        )

        updated = _project_voice_profile_from_session(
            existing_voice=existing_voice,
            voice_profile_id=existing_voice.voice_profile_id,
            name=existing_voice.name,
            session=enrollment_session,
            enrollment_source=existing_voice.enrollment_source,
            speaker_embedding_id=embedding_id,
            attribution_confidence=confidence,
            disabled=False,
            consent=dict(existing_voice.consent),
            tts_voice=existing_voice.tts_voice,
        )
        await storage.async_update_voice_profile(updated)
        enrollment_session, cleanup_summary = await _async_execute_enrollment_cleanup(
            hass,
            storage,
            enrollment_session,
            cleanup_reason=VOICE_ENROLLMENT_CLEANUP_REASON_COMPLETED,
        )

        person_id = str(call.data.get("person_id") or "").strip()
        if person_id:
            person_profile = state.person_profiles.get(person_id)
            if person_profile is None:
                raise vol.Invalid("person_id is not configured")
            person_profile.voice_profile_id = voice_profile_id
            await storage.async_update_person_profile(
                person_profile,
                set_as_default=(
                    state.default_person_profile is not None
                    and state.default_person_profile.person_id == person_id
                ),
            )

        return {
            "built": True,
            "voice_profile_id": voice_profile_id,
            "sample_count": sample_count,
            "speaker_embedding_id": embedding_id,
            "attribution_confidence": confidence,
            "person_id": person_id or None,
            "cleanup_result_code": cleanup_summary["cleanup_result_code"],
        }

    return await _async_with_activity(
        hass,
        call,
        intent_class="build_voice_profile",
        request_summary=f"Voice profile built: {voice_profile_id}",
        action_name="build_voice_profile",
        resolved_person_id=call.data.get("person_id"),
        channel="service_mutation",
        external_refs=[{"ref_type": "voice_profile", "voice_profile_id": voice_profile_id}],
        runner=_runner,
    )


async def _async_handle_reset_voice_profile(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Reset a voice profile to untrained state while preserving identity linkage."""
    voice_profile_id = call.data["voice_profile_id"]
    preserve_consent = bool(call.data.get("preserve_consent", True))

    async def _runner() -> dict[str, Any]:
        storage = ConciergeStorage(hass)
        state = await storage.async_load_state()
        existing_voice = state.voice_profiles.get(voice_profile_id)
        if existing_voice is None:
            raise vol.Invalid("voice_profile_id is not configured")

        enrollment_session = await storage.async_get_latest_enrollment_session_for_voice_profile(voice_profile_id)
        if enrollment_session is None:
            matched_person_id = ""
            for profile in state.person_profiles.values():
                if profile.voice_profile_id == voice_profile_id:
                    matched_person_id = profile.person_id
                    break
            enrollment_session = enrollment_session_for_start(
                person_id=matched_person_id,
                voice_profile_id=voice_profile_id,
                existing_sample_items=list(existing_voice.sample_items),
                enrollment_started_at=existing_voice.enrollment_started_at or datetime.now(timezone.utc).isoformat(),
            )

        enrollment_session = enrollment_session_reset(enrollment_session)
        enrollment_session = await storage.async_update_enrollment_session(
            session_id=enrollment_session.session_id,
            state_name=enrollment_session.state,
            sample_count=enrollment_session.sample_count,
            sample_items=list(enrollment_session.sample_items),
            enrollment_started_at=enrollment_session.enrollment_started_at,
            last_sample_at=enrollment_session.last_sample_at,
            last_built_at=enrollment_session.last_built_at,
        )
        await _async_sync_session_manifest(hass, enrollment_session)

        updated = _project_voice_profile_from_session(
            existing_voice=existing_voice,
            voice_profile_id=existing_voice.voice_profile_id,
            name=existing_voice.name,
            session=enrollment_session,
            enrollment_source=existing_voice.enrollment_source,
            speaker_embedding_id="",
            attribution_confidence=None,
            disabled=False,
            consent=(dict(existing_voice.consent) if preserve_consent else {}),
            tts_voice=existing_voice.tts_voice,
        )
        await storage.async_update_voice_profile(updated)
        enrollment_session, cleanup_summary = await _async_execute_enrollment_cleanup(
            hass,
            storage,
            enrollment_session,
            cleanup_reason=VOICE_ENROLLMENT_CLEANUP_REASON_MANUAL,
        )
        return {
            "reset": True,
            "voice_profile_id": voice_profile_id,
            "preserve_consent": preserve_consent,
            "cleanup_result_code": cleanup_summary["cleanup_result_code"],
        }

    return await _async_with_activity(
        hass,
        call,
        intent_class="reset_voice_profile",
        request_summary=f"Voice profile reset: {voice_profile_id}",
        action_name="reset_voice_profile",
        channel="service_mutation",
        external_refs=[{"ref_type": "voice_profile", "voice_profile_id": voice_profile_id}],
        runner=_runner,
    )


async def _async_handle_delete_voice_profile(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Delete a voice profile and optionally unlink associated people."""
    voice_profile_id = call.data["voice_profile_id"]
    unlink_from_people = bool(call.data.get("unlink_from_people", True))

    async def _runner() -> dict[str, Any]:
        storage = ConciergeStorage(hass)
        current_state = await storage.async_load_state()
        existing_voice = current_state.voice_profiles.get(voice_profile_id)
        enrollment_session = await storage.async_get_latest_enrollment_session_for_voice_profile(voice_profile_id)

        cleanup_summary = {
            "cleanup_result_code": "not_started",
            "artifacts_seen_count": 0,
            "artifacts_deleted_count": 0,
            "artifacts_missing_count": 0,
            "errors_redacted_or_sanitized": [],
        }
        if enrollment_session is not None:
            enrollment_session, cleanup_summary = await _async_execute_enrollment_cleanup(
                hass,
                storage,
                enrollment_session,
                cleanup_reason=VOICE_ENROLLMENT_CLEANUP_REASON_CANCELLED,
            )

        storage = ConciergeStorage(hass)
        state = await storage.async_delete_voice_profile(
            voice_profile_id,
            unlink_from_people=unlink_from_people,
        )

        # Preserve enrollment session + manifest authority until startup reconciliation exists.
        if enrollment_session is None and existing_voice is not None:
            provider = _voice_storage_provider_from_hass(hass)
            if provider is not None:
                recording_paths = _sample_recording_paths(list(existing_voice.sample_items))
                if recording_paths:
                    await hass.async_add_executor_job(
                        lambda: provider.delete_owned_artifacts(recording_paths)
                    )

        return {
            "deleted": True,
            "voice_profile_id": voice_profile_id,
            "unlink_from_people": unlink_from_people,
            "voice_profile_count": len(state.voice_profiles),
            "cleanup_result_code": cleanup_summary["cleanup_result_code"],
        }

    return await _async_with_activity(
        hass,
        call,
        intent_class="delete_voice_profile",
        request_summary=f"Voice profile deleted: {voice_profile_id}",
        action_name="delete_voice_profile",
        channel="service_mutation",
        external_refs=[{"ref_type": "voice_profile", "voice_profile_id": voice_profile_id}],
        runner=_runner,
    )


async def _async_handle_update_global_context(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    """Update global context usage and optional cached speakable values."""
    async def _runner() -> dict[str, Any]:
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

    return await _async_with_activity(
        hass,
        call,
        intent_class="update_global_context",
        request_summary=f"Global context updated: {call.data.get('context_type', 'context')}",
        action_name="update_global_context",
        channel="service_mutation",
        external_refs=[{"ref_type": "global_context", "context_type": call.data.get("context_type")}],
        runner=_runner,
    )


async def _async_handle_update_execution_preferences(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Update execution preferences at area/composite scope."""
    async def _runner() -> dict[str, Any]:
        storage = ConciergeStorage(hass)
        state = await storage.async_update_execution_preferences(
            scope_id=call.data["scope_id"],
            preferences=call.data["preferences"],
        )
        return {"execution_preference_count": len(state.execution_preferences)}

    return await _async_with_activity(
        hass,
        call,
        intent_class="update_execution_preferences",
        request_summary=f"Execution preferences updated: {call.data.get('scope_id', 'scope')}",
        action_name="update_execution_preferences",
        channel="service_mutation",
        external_refs=[{"ref_type": "execution_preferences", "scope_id": call.data.get("scope_id")}],
        runner=_runner,
    )


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


def _resolve_floor_id_for_area_ids(hass: HomeAssistant, area_ids: list[str]) -> str | None:
    """Return the shared floor_id for the provided areas, or None when empty."""
    if not area_ids:
        return None

    area_registry = ar.async_get(hass)
    floor_ids: set[str | None] = set()
    for area_id in area_ids:
        area = area_registry.async_get_area(area_id)
        if area is None:
            raise vol.Invalid(f"area_id does not exist: {area_id}")
        floor_ids.add(area.floor_id)

    if len(floor_ids) > 1:
        raise vol.Invalid("composite area_ids must all be on the same floor")

    return next(iter(floor_ids))


COMPOSITE_ENTITY_FIELDS: tuple[str, ...] = (
    "media_player_entity_ids",
    "voice_device_entity_ids",
    "asset_groups",
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
    capabilities = _resolve_integration_capabilities(hass)

    area_ids = call.data.get("area_ids")
    if area_ids is None and existing is not None:
        resolved_area_ids = list(existing.area_ids)
    elif area_ids is None:
        resolved_area_ids = []
    else:
        resolved_area_ids = list(dict.fromkeys(area_ids))

    async def _runner() -> dict[str, Any]:
        composite_floor_id: str | None = existing.floor_id if existing is not None else None
        if resolved_area_ids:
            _validate_same_floor_area_ids(hass, resolved_area_ids)
            composite_floor_id = _resolve_floor_id_for_area_ids(hass, resolved_area_ids)
        elif area_ids is not None:
            composite_floor_id = None

        primary_area = call.data.get("primary_area")
        if primary_area is not None and resolved_area_ids and primary_area not in resolved_area_ids:
            raise vol.Invalid("primary_area must exist in area_ids")

        asset_groups = call.data.get("asset_groups")
        if asset_groups is not None and not isinstance(asset_groups, list):
            raise vol.Invalid("asset_groups must be a list")
        device_groups = call.data.get("device_groups")
        if device_groups is not None and not isinstance(device_groups, list):
            raise vol.Invalid("device_groups must be a list")

        ai_knowledge_enabled = call.data.get("ai_knowledge_enabled")
        environment_information_outputs = call.data.get("environment_information_outputs")
        tts_voice = call.data.get("tts_voice")
        tts_language = call.data.get("tts_language")
        persona = call.data.get("persona")
        persona_prompt = call.data.get("persona_prompt")

        if not capabilities["cap_ai"] and ai_knowledge_enabled is not None:
            ai_knowledge_enabled = False
        if not capabilities["cap_assets"]:
            if asset_groups is not None:
                asset_groups = []
            if environment_information_outputs is not None:
                environment_information_outputs = []
        if not capabilities["cap_persona"]:
            if tts_voice is not None:
                tts_voice = ""
            if tts_language is not None:
                tts_language = ""
            if persona is not None:
                persona = ""
            if persona_prompt is not None:
                persona_prompt = ""
        elif not capabilities["cap_tts"]:
            if tts_voice is not None:
                tts_voice = ""
            if tts_language is not None:
                tts_language = ""

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
            floor_id=composite_floor_id,
            area_ids=resolved_area_ids if area_ids is not None else None,
            primary_area=primary_area,
            enabled=call.data.get("enabled"),
            posture=call.data.get("posture"),
            media_player_entity_ids=sanitized_entities["media_player_entity_ids"],
            voice_device_entity_ids=sanitized_entities["voice_device_entity_ids"],
            tts_voice=tts_voice,
            tts_language=tts_language,
            device_groups=device_groups if device_groups is not None else (list(existing.device_groups) if existing is not None else None),
            persona=persona,
            persona_prompt=persona_prompt,
            ai_knowledge_enabled=ai_knowledge_enabled,
            environment_information_outputs=environment_information_outputs,
            asset_groups=asset_groups if asset_groups is not None else (list(existing.asset_groups) if existing is not None else None),
            room_sensor_entity_ids=sanitized_entities["room_sensor_entity_ids"],
            room_health_entity_ids=sanitized_entities["room_health_entity_ids"],
            human_health_entity_ids=sanitized_entities["human_health_entity_ids"],
            light_entity_ids=sanitized_entities["light_entity_ids"],
            shade_entity_ids=sanitized_entities["shade_entity_ids"],
            speaker_entity_ids=sanitized_entities["speaker_entity_ids"],
            dashboard_entity_ids=sanitized_entities["dashboard_entity_ids"],
            other_entity_ids=sanitized_entities["other_entity_ids"],
            weather_source_entity_ids=call.data.get("weather_source_entity_ids"),
            news_source_entity_ids=call.data.get("news_source_entity_ids"),
        )

        composite = updated.composites.get(composite_id)
        return {
            "updated": True,
            "composite_id": composite_id,
            "dismantled": composite is None,
            "composite_count": len(updated.composites),
            "area_count": len(composite.area_ids) if composite else 0,
        }

    return await _async_with_activity(
        hass,
        call,
        intent_class="update_composite_config",
        request_summary=f"Merged room updated: {call.data.get('name', composite_id)}",
        action_name="update_composite_config",
        resolved_area_id=resolved_area_ids[0] if resolved_area_ids else None,
        channel="service_mutation",
        external_refs=[{"ref_type": "composite", "composite_id": composite_id, "area_ids": resolved_area_ids}],
        runner=_runner,
    )


async def _async_handle_sync_composites(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Validate and rebuild composite runtime projections."""
    area_registry = ar.async_get(hass)
    _ = fr.async_get(hass)
    valid_area_ids = {area.id for area in area_registry.async_list_areas()}
    remove_invalid = bool(call.data.get("remove_invalid", True))

    async def _runner() -> dict[str, Any]:
        storage = ConciergeStorage(hass)
        state, validation_errors = await storage.async_sync_composites(
            valid_area_ids=valid_area_ids,
            remove_invalid=remove_invalid,
        )

        for composite_id, composite in state.composites.items():
            try:
                _validate_same_floor_area_ids(hass, composite.area_ids)
            except vol.Invalid as err:
                validation_errors.append(f"{composite_id}: {err}")

        if remove_invalid:
            for composite_id, composite in state.composites.items():
                allowed_entity_ids = _entity_ids_for_area_ids(hass, composite.area_ids)
                update_payload: dict[str, list[str]] = {}
                floor_id = _resolve_floor_id_for_area_ids(hass, composite.area_ids) if composite.area_ids else None

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
                        floor_id=floor_id,
                        **update_payload,
                    )
                elif composite.floor_id != floor_id:
                    await storage.async_update_composite_config(
                        composite_id=composite_id,
                        floor_id=floor_id,
                    )

        return {
            "synced": True,
            "remove_invalid": remove_invalid,
            "composite_count": len(state.composites),
            "validation_errors": validation_errors,
        }

    return await _async_with_activity(
        hass,
        call,
        intent_class="sync_composites",
        request_summary="Merged rooms synchronized",
        action_name="sync_composites",
        channel="service_mutation",
        external_refs=[{"ref_type": "sync_composites", "remove_invalid": remove_invalid}],
        runner=_runner,
    )


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

    async def _runner() -> dict[str, Any]:
        engine_entity_id = TTS_PROVIDER_ENTITY_IDS.get(provider)
        if engine_entity_id is None:
            raise vol.Invalid(f"unsupported provider: {provider}")

        options: dict[str, Any] = {}
        if call.data.get("voice"):
            options["voice"] = call.data["voice"]

        payload: dict[str, Any] = {
            "entity_id": engine_entity_id,
            "media_player_entity_id": call.data["media_player_entity_id"],
            "message": call.data["message"],
            "cache": False,
        }
        if call.data.get("language"):
            payload["language"] = call.data["language"]
        if options:
            payload["options"] = options

        used_language_fallback = False
        try:
            await hass.services.async_call(
                "tts",
                "speak",
                payload,
                blocking=True,
            )
        except Exception as err:
            error_text = str(err)
            invalid_language = "language" in error_text.lower()
            if not (invalid_language and "language" in payload):
                raise

            payload.pop("language", None)
            await hass.services.async_call(
                "tts",
                "speak",
                payload,
                blocking=True,
            )
            used_language_fallback = True

        return {
            "previewed": True,
            "provider": provider,
            "engine_entity_id": engine_entity_id,
            "used_language_fallback": used_language_fallback,
        }

    return await _async_with_activity(
        hass,
        call,
        intent_class="preview_tts_voice",
        request_summary="Voice preview requested",
        action_name="preview_tts_voice",
        channel="service_operational",
        external_refs=[{"ref_type": "tts_preview", "provider": provider}],
        runner=_runner,
    )


async def _async_handle_sync_rooms(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Synchronize Concierge room config keys to current Home Assistant areas."""
    area_registry = ar.async_get(hass)
    current_area_ids = {area.id for area in area_registry.async_list_areas()}

    add_missing = bool(call.data.get("add_missing", True))
    remove_missing = bool(call.data.get("remove_missing", True))

    async def _runner() -> dict[str, Any]:
        storage = ConciergeStorage(hass)
        state = await storage.async_load_state()
        existing_area_ids = set(state.rooms)

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

    return await _async_with_activity(
        hass,
        call,
        intent_class="sync_rooms",
        request_summary="Rooms synchronized to Home Assistant area registry",
        action_name="sync_rooms",
        channel="service_mutation",
        external_refs=[{"ref_type": "sync_rooms", "add_missing": add_missing, "remove_missing": remove_missing}],
        runner=_runner,
    )


async def _async_handle_refresh_entity_structure(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Optionally sync rooms then reload Concierge entry to rebuild entities."""
    sync_rooms = bool(call.data.get("sync_rooms", True))
    sync_result: dict[str, Any] | None = None

    async def _runner() -> dict[str, Any]:
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
        else:
            sync_result = None

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

    return await _async_with_activity(
        hass,
        call,
        intent_class="refresh_entity_structure",
        request_summary="Entity structure refresh requested",
        action_name="refresh_entity_structure",
        channel="service_operational",
        external_refs=[{"ref_type": "entity_refresh", "sync_rooms": sync_rooms}],
        runner=_runner,
    )


def _archive_options(hass: HomeAssistant) -> tuple[str | None, bool]:
    """Read archive destination and reference-excerpt defaults from entry options."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return None, False
    entry = entries[0]
    destination = entry.options.get("audit_archive_destination_uri")
    include_refs = bool(entry.options.get("audit_archive_include_reference_excerpts", False))
    return destination, include_refs


def _write_archive_package(
    *,
    destination_path: Path,
    activities: list[dict[str, Any]],
    start: str | None,
    end: str | None,
) -> tuple[str, int, str]:
    """Write immutable self-contained archive package to destination path."""
    generated_at = datetime.now(timezone.utc).isoformat()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_dir = destination_path / f"concierge_activity_archive_{stamp}"
    archive_dir.mkdir(parents=True, exist_ok=False)

    manifest = {
        "generated_at": generated_at,
        "window": {"start": start, "end": end},
        "item_count": len(activities),
        "activities": activities,
    }
    (archive_dir / "activity_timeline.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    lines = [
        "Concierge Activity Archive",
        "",
        f"Generated: {generated_at}",
        f"Start: {start or 'unbounded'}",
        f"End: {end or 'unbounded'}",
        f"Items: {len(activities)}",
        "",
        "Timeline:",
    ]
    for activity in activities:
        lines.append(
            "- "
            f"{activity.get('started_at', '')} "
            f"[{activity.get('actor_class', 'unknown')}] "
            f"{activity.get('intent_class', 'unknown')} "
            f"=> {activity.get('outcome') or 'open'}"
        )
    (archive_dir / "README.txt").write_text("\n".join(lines), encoding="utf-8")

    return str(archive_dir), len(activities), generated_at


async def _async_handle_record_activity_event(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Record stitched orchestration metadata for one activity."""
    actor_class = call.data["actor_class"]
    request_summary = _sanitize_request_summary(actor_class, call.data.get("request_summary", ""))

    storage = ConciergeStorage(hass)
    activity = ActivityEvent(
        activity_id=call.data["activity_id"],
        correlation_id=call.data["correlation_id"],
        started_at=call.data["started_at"],
        channel=call.data["channel"],
        actor_class=actor_class,
        intent_class=call.data["intent_class"],
        request_summary=request_summary,
        resolved_person_id=call.data.get("resolved_person_id"),
        resolved_area_id=call.data.get("resolved_area_id"),
        confidence=call.data.get("confidence"),
        external_refs=list(call.data.get("external_refs", [])),
    )
    state = await storage.async_record_activity_event(activity)
    return {"recorded": True, "activity_count": len(state.activities)}


async def _async_handle_close_activity_outcome(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Close a stitched activity with deterministic outcome metadata."""
    storage = ConciergeStorage(hass)
    try:
        await storage.async_close_activity_event(
            activity_id=call.data["activity_id"],
            ended_at=call.data["ended_at"],
            outcome=call.data["outcome"],
            outcome_reason=call.data.get("outcome_reason", ""),
            actions_taken=list(call.data.get("actions_taken", [])),
            policy_gates=list(call.data.get("policy_gates", [])),
        )
    except KeyError as err:
        raise vol.Invalid(f"activity_id not found: {err.args[0]}") from err

    return {"closed": True, "activity_id": call.data["activity_id"]}


async def _async_handle_get_activity_timeline(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Return chronological activity timeline with stitched references."""
    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()

    filtered = [
        event
        for event in state.activities.values()
        if _event_matches_filters(event, call)
    ]
    filtered.sort(key=lambda item: item.started_at)
    return {
        "activities": [
            _serialize_activity(event, include_reference_excerpts=True)
            for event in filtered
        ]
    }


async def _async_handle_export_activity_archive(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Export a self-contained offline activity archive package."""
    capabilities = _resolve_integration_capabilities(hass)
    if not capabilities["cap_extended_history"]:
        raise vol.Invalid(
            "activity archive export is unavailable until attached storage and archive export are enabled in Concierge options"
        )
    configured_destination, default_include_refs = _archive_options(hass)
    destination = call.data.get("destination") or configured_destination
    if not destination:
        raise vol.Invalid("archive destination is not configured in integration options")

    include_reference_excerpts = bool(
        call.data.get("include_reference_excerpts", default_include_refs)
    )
    destination_path = _archive_destination_path(destination)

    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()

    start = call.data.get("start")
    end = call.data.get("end")
    range_call = ServiceCall(
        context=call.context,
        data={"start": start, "end": end},
        domain=DOMAIN,
        service=SERVICE_EXPORT_ACTIVITY_ARCHIVE,
        return_response=True,
        service_data={"start": start, "end": end},
        service_data_unmodified={"start": start, "end": end},
    )
    selected = [
        event
        for event in state.activities.values()
        if _event_matches_filters(event, range_call)
    ]
    selected.sort(key=lambda item: item.started_at)
    serialized = [
        _serialize_activity(event, include_reference_excerpts=include_reference_excerpts)
        for event in selected
    ]

    archive_uri, item_count, generated_at = await hass.async_add_executor_job(
        lambda: _write_archive_package(
            destination_path=destination_path,
            activities=serialized,
            start=start,
            end=end,
        )
    )
    return {
        "archive_uri": archive_uri,
        "item_count": item_count,
        "generated_at": generated_at,
    }


async def _async_handle_resolve_mobile_context(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Resolve person and room context for mobile voice and typed requests."""
    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()

    resolved_person: PersonProfile | None = None
    person_confidence = 0.0
    person_id = call.data.get("person_id")
    mobile_target_id = call.data.get("mobile_target_id")

    if person_id:
        resolved_person = state.person_profiles.get(person_id)
        if resolved_person is not None:
            person_confidence = 1.0
    elif mobile_target_id:
        for profile in state.person_profiles.values():
            if mobile_target_id in _active_mobile_targets(profile):
                resolved_person = profile
                person_confidence = 0.9
                break

    resolved_area_id = resolved_person.linked_area_id if resolved_person is not None else None
    room_confidence = 0.8 if resolved_area_id else 0.0

    return {
        "resolved_person_id": resolved_person.person_id if resolved_person else None,
        "person_confidence": person_confidence,
        "resolved_area_id": resolved_area_id,
        "room_confidence": room_confidence,
        "attribution_factors": (
            ["explicit_person_id"]
            if person_id and resolved_person
            else (["mobile_target_match"] if resolved_person else [])
        ),
        "clarification_required": room_confidence < 0.5,
    }


async def _async_handle_push_person_message(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Send person-scoped mobile push after deterministic target filtering."""
    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    profile = state.person_profiles.get(call.data["person_id"])
    if profile is None:
        raise vol.Invalid("person_id is not configured")

    target_id = _select_mobile_target(profile, call.data.get("target_id"))
    notify_service = f"notify.{target_id}"

    async def _runner() -> dict[str, Any]:
        payload: dict[str, Any] = {
            "title": call.data.get("title", "Concierge"),
            "message": call.data["message"],
            "data": dict(call.data.get("data", {})),
        }
        await hass.services.async_call("notify", target_id, payload, blocking=True)

        return {
            "sent": True,
            "person_id": profile.person_id,
            "target_id": target_id,
            "service": notify_service,
        }

    return await _async_with_activity(
        hass,
        call,
        intent_class="push_person_message",
        request_summary=f"Mobile push sent to {profile.name or profile.person_id}",
        action_name="push_person_message",
        resolved_person_id=profile.person_id,
        resolved_area_id=profile.linked_area_id,
        channel="service_operational",
        external_refs=[{"ref_type": "mobile_notify", "target_id": target_id}],
        runner=_runner,
    )


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
        SERVICE_START_VOICE_ENROLLMENT,
        _bind(_async_handle_start_voice_enrollment),
        schema=SERVICE_START_VOICE_ENROLLMENT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CAPTURE_VOICE_ENROLLMENT_SAMPLE,
        _bind(_async_handle_capture_voice_enrollment_sample),
        schema=SERVICE_CAPTURE_VOICE_ENROLLMENT_SAMPLE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_VOICE_ENROLLMENT_SAMPLE,
        _bind(_async_handle_remove_voice_enrollment_sample),
        schema=SERVICE_REMOVE_VOICE_ENROLLMENT_SAMPLE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_BUILD_VOICE_PROFILE,
        _bind(_async_handle_build_voice_profile),
        schema=SERVICE_BUILD_VOICE_PROFILE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_VOICE_PROFILE,
        _bind(_async_handle_reset_voice_profile),
        schema=SERVICE_RESET_VOICE_PROFILE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_VOICE_PROFILE,
        _bind(_async_handle_delete_voice_profile),
        schema=SERVICE_DELETE_VOICE_PROFILE_SCHEMA,
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
    hass.services.async_register(
        DOMAIN,
        SERVICE_RECORD_ACTIVITY_EVENT,
        _bind(_async_handle_record_activity_event),
        schema=SERVICE_RECORD_ACTIVITY_EVENT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CLOSE_ACTIVITY_OUTCOME,
        _bind(_async_handle_close_activity_outcome),
        schema=SERVICE_CLOSE_ACTIVITY_OUTCOME_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_ACTIVITY_TIMELINE,
        _bind(_async_handle_get_activity_timeline),
        schema=SERVICE_GET_ACTIVITY_TIMELINE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_ACTIVITY_ARCHIVE,
        _bind(_async_handle_export_activity_archive),
        schema=SERVICE_EXPORT_ACTIVITY_ARCHIVE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RESOLVE_MOBILE_CONTEXT,
        _bind(_async_handle_resolve_mobile_context),
        schema=SERVICE_RESOLVE_MOBILE_CONTEXT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PUSH_PERSON_MESSAGE,
        _bind(_async_handle_push_person_message),
        schema=SERVICE_PUSH_PERSON_MESSAGE_SCHEMA,
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
        SERVICE_START_VOICE_ENROLLMENT,
        SERVICE_CAPTURE_VOICE_ENROLLMENT_SAMPLE,
        SERVICE_REMOVE_VOICE_ENROLLMENT_SAMPLE,
        SERVICE_BUILD_VOICE_PROFILE,
        SERVICE_RESET_VOICE_PROFILE,
        SERVICE_DELETE_VOICE_PROFILE,
        SERVICE_UPDATE_GLOBAL_CONTEXT,
        SERVICE_UPDATE_EXECUTION_PREFERENCES,
        SERVICE_UPDATE_COMPOSITE_CONFIG,
        SERVICE_SYNC_COMPOSITES,
        SERVICE_GET_CONTEXT,
        SERVICE_GET_SUMMARY,
        SERVICE_PREVIEW_TTS_VOICE,
        SERVICE_SYNC_ROOMS,
        SERVICE_REFRESH_ENTITY_STRUCTURE,
        SERVICE_RECORD_ACTIVITY_EVENT,
        SERVICE_CLOSE_ACTIVITY_OUTCOME,
        SERVICE_GET_ACTIVITY_TIMELINE,
        SERVICE_EXPORT_ACTIVITY_ARCHIVE,
        SERVICE_RESOLVE_MOBILE_CONTEXT,
        SERVICE_PUSH_PERSON_MESSAGE,
    ):
        if hass.services.has_service(DOMAIN, service_name):
            hass.services.async_remove(DOMAIN, service_name)
