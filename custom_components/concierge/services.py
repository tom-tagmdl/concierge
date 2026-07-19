"""Contract-first service handlers for Concierge orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Awaitable, Callable
from urllib.parse import unquote, urlparse
from uuid import uuid4

import voluptuous as vol

from homeassistant.components.tts.const import DATA_COMPONENT as TTS_DATA_COMPONENT
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import floor_registry as fr
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse

from .archive_runtime import archive_options_from_entry, resolve_voice_enrollment_root
from .const import (
    SERVICE_BUILD_VOICE_PROFILE,
    SERVICE_COMPLETE_VOICE_ENROLLMENT,
    SERVICE_CAPTURE_VOICE_ENROLLMENT_SAMPLE,
    SERVICE_RUN_SATELLITE_CAPTURE_POC,
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
    SERVICE_GET_VOICE_ENROLLMENT_COMPLETION_READINESS,
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
    SERVICE_ABANDON_VOICE_ENROLLMENT,
    SERVICE_CANCEL_VOICE_ENROLLMENT,
    SERVICE_RECOVER_VOICE_ENROLLMENT,
    SERVICE_RESUME_VOICE_ENROLLMENT,
)
from .enrollment_orchestrator import EnrollmentOrchestrator
from .models import (
    ActivityEvent,
    ContextState,
    IdentityProfile,
    Interaction,
    PersonProfile,
    SignalState,
)
from .storage import ConciergeStorage
from .voice_identity_bridge import async_get_voice_identity_enrollment_status

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
        vol.Optional("capture_provider", default="auto"): str,
        vol.Optional("consent_acknowledged", default=False): bool,
        vol.Optional("local_only", default=True): bool,
    }
)
SERVICE_CAPTURE_VOICE_ENROLLMENT_SAMPLE_SCHEMA = vol.Schema(
    {
        vol.Required("voice_profile_id"): str,
        vol.Required("speech_text"): str,
        vol.Optional("capture_provider", default="browser"): str,
        vol.Optional("prompt_text"): str,
        vol.Optional("source", default="guided_phrase"): str,
        vol.Optional("quality_score"): vol.Coerce(float),
        vol.Optional("recording_path"): str,
        vol.Optional("recording_mime_type"): str,
        vol.Optional("recording_size_bytes"): int,
        vol.Optional("recording_duration_ms"): int,
        vol.Optional("phrase_index"): int,
        vol.Optional("prompt_id"): str,
        vol.Optional("prompt_order"): int,
        vol.Optional("prompt_category"): str,
        vol.Optional("prompt_length_bucket"): str,
        vol.Optional("capture_distance"): str,
        vol.Optional("capture_noise"): str,
        vol.Optional("quality_pass"): bool,
        vol.Optional("person_id"): str,
        vol.Optional("satellite_entity_id"): str,
        vol.Optional("device_id"): str,
        vol.Optional("preannounce", default=False): bool,
        vol.Optional("timeout_seconds", default=8.0): vol.All(
            vol.Coerce(float),
            vol.Range(min=0, min_included=False, max=60),
        ),
    }
)
SERVICE_RUN_SATELLITE_CAPTURE_POC_SCHEMA = vol.Schema(
    {
        vol.Required("voice_profile_id"): str,
        vol.Optional("person_id"): str,
        vol.Optional("satellite_entity_id"): str,
        vol.Optional("device_id"): str,
        vol.Optional("timeout_seconds", default=8.0): vol.All(
            vol.Coerce(float),
            vol.Range(min=0, min_included=False, max=60),
        ),
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
        vol.Optional("min_samples", default=8): vol.All(int, vol.Range(min=1, max=50)),
    }
)
SERVICE_COMPLETE_VOICE_ENROLLMENT_SCHEMA = vol.Schema(
    {
        vol.Required("voice_profile_id"): str,
        vol.Optional("person_id"): str,
        vol.Optional("min_samples", default=8): vol.All(int, vol.Range(min=1, max=50)),
        vol.Optional("min_total_duration_ms", default=30000): vol.All(int, vol.Range(min=1000, max=300000)),
    }
)
SERVICE_GET_VOICE_ENROLLMENT_COMPLETION_READINESS_SCHEMA = vol.Schema(
    {
        vol.Required("voice_profile_id"): str,
        vol.Optional("min_samples", default=8): vol.All(int, vol.Range(min=1, max=50)),
        vol.Optional("min_total_duration_ms", default=30000): vol.All(int, vol.Range(min=1000, max=300000)),
    }
)
SERVICE_CANCEL_VOICE_ENROLLMENT_SCHEMA = vol.Schema(
    {
        vol.Optional("person_id"): str,
        vol.Optional("voice_profile_id"): str,
    }
)
SERVICE_RECOVER_VOICE_ENROLLMENT_SCHEMA = vol.Schema(
    {
        vol.Optional("person_id"): str,
        vol.Optional("voice_profile_id"): str,
    }
)
SERVICE_RESUME_VOICE_ENROLLMENT_SCHEMA = vol.Schema(
    {
        vol.Optional("person_id"): str,
        vol.Optional("voice_profile_id"): str,
    }
)
SERVICE_ABANDON_VOICE_ENROLLMENT_SCHEMA = vol.Schema(
    {
        vol.Optional("person_id"): str,
        vol.Optional("voice_profile_id"): str,
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

_MESSAGE_WEB_UI_TARGETS = {"web_ui", "persistent_notification", "dashboard", "kiosk"}
_MESSAGE_VOICE_ASSISTANT_TARGETS = {"assist_satellite", "satellite", "voice_assistant", "assistant"}
_MESSAGE_TTS_TARGETS = {"speaker", "speakers", "tts", "media_player"}
_MESSAGE_MOBILE_TARGET_PREFIXES = ("notify.",)


def _normalize_message_target(target: str | None) -> str:
    """Normalize a message target to a stable lower-case routing token."""
    return str(target or "").strip().lower()


def _room_entity_ids(room, field_name: str) -> list[str]:
    """Return a room entity list filtered to non-empty string identifiers."""
    values = getattr(room, field_name, []) if room is not None else []
    return [entity_id for entity_id in values if isinstance(entity_id, str) and entity_id]


def _resolve_tts_engine_entity_id(hass: HomeAssistant) -> tuple[str, str]:
    """Resolve the configured TTS provider into a HA TTS engine entity id."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        raise vol.Invalid("Concierge is not configured")

    entry = entries[0]
    provider = str(
        entry.options.get("tts_provider", entry.data.get("tts_provider", _PROVIDER_NONE))
        or _PROVIDER_NONE
    ).strip() or _PROVIDER_NONE
    engine_entity_id = TTS_PROVIDER_ENTITY_IDS.get(provider)
    if engine_entity_id is None:
        raise vol.Invalid("tts_provider is not configured")
    return provider, engine_entity_id


def _preferred_assist_pipeline_tts_voice(hass: HomeAssistant) -> str:
    """Return the preferred Assist pipeline voice when it is available."""
    try:
        from homeassistant.components.assist_pipeline import async_get_pipeline

        pipeline = async_get_pipeline(hass, None)
    except Exception:
        return ""

    for candidate in (
        getattr(pipeline, "tts_voice", None),
        getattr(pipeline, "voice", None),
        getattr(pipeline, "conversation_voice", None),
    ):
        value = str(candidate or "").strip()
        if value:
            return value
    return ""


def _preferred_assist_pipeline_tts_language(hass: HomeAssistant) -> str:
    """Return the preferred Assist pipeline language for room TTS fallbacks."""
    try:
        from homeassistant.components.assist_pipeline import async_get_pipeline

        pipeline = async_get_pipeline(hass, None)
    except Exception:
        return ""

    for candidate in (
        getattr(pipeline, "tts_language", None),
        getattr(pipeline, "language", None),
        getattr(pipeline, "conversation_language", None),
    ):
        value = str(candidate or "").strip()
        if value:
            return value
    return ""


def _resolve_room_tts_settings(
    hass: HomeAssistant,
    *,
    provider: str,
    room,
) -> dict[str, str]:
    """Resolve room TTS settings using room, assistant, then provider defaults."""
    language = str(getattr(room, "tts_language", "") or "").strip()
    voice = str(getattr(room, "tts_voice", "") or "").strip()

    if not language:
        language = _preferred_assist_pipeline_tts_language(hass)

    if not voice:
        voice = _preferred_assist_pipeline_tts_voice(hass)

    if not voice and provider:
        entity_id = TTS_PROVIDER_ENTITY_IDS.get(provider)
        if entity_id and TTS_DATA_COMPONENT in hass.data:
            entity_component = hass.data[TTS_DATA_COMPONENT]
            tts_entity = entity_component.get_entity(entity_id)
            if tts_entity is not None:
                if not language:
                    default_language = str(getattr(tts_entity, "default_language", "") or "").strip()
                    if default_language:
                        language = default_language
                if language:
                    try:
                        supported_voices = tts_entity.async_get_supported_voices(language)
                    except Exception:
                        supported_voices = None
                    if supported_voices:
                        first_voice = next(
                            (
                                str(getattr(voice_info, "voice_id", "") or "").strip()
                                for voice_info in supported_voices
                                if str(getattr(voice_info, "voice_id", "") or "").strip()
                            ),
                            "",
                        )
                        if first_voice:
                            voice = first_voice

    return {"language": language, "voice": voice}


def _build_messaging_provenance(
    *,
    person_id: str,
    linked_area_id: str | None,
    requested_target: str,
    requested_target_supplied: bool,
    selected_target_id: str,
    selected_service: str,
    delivery_channel: str,
    routing_path: str,
    explicit_entity_target: bool,
    messaging_governance_boundary: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build bounded provenance metadata for person-scoped message routing."""
    created_at = datetime.now(timezone.utc).isoformat()
    provenance_id = f"msgprov_{uuid4().hex}"
    room_state = "known" if linked_area_id else "unknown"
    actor_reference = {"service": "concierge.push_person_message"}
    destination_reference: dict[str, Any] = {
        "target_id": selected_target_id,
        "service": selected_service,
        "delivery_channel": delivery_channel,
    }
    if explicit_entity_target:
        destination_reference["entity_id"] = selected_target_id

    provenance = {
        "provenance_id": provenance_id,
        "provenance_state": "known",
        "created_at": created_at,
        "created_by": {
            "actor_reference": actor_reference,
            "actor_state": "system",
            "provenance_reference": f"provenance.created_by.{provenance_id}",
        },
        "delivered_to": {
            "destination_reference": destination_reference,
            "destination_state": "known",
            "provenance_reference": f"provenance.delivered_to.{provenance_id}",
        },
        "created_in_room": {
            "room_reference": ({"area_id": linked_area_id} if linked_area_id else {}),
            "room_state": room_state,
            "room_lineage_reference": (
                f"provenance.room.{linked_area_id}.{provenance_id}" if linked_area_id else None
            ),
        },
        "created_via": {
            "method": "service",
            "interaction_pathway": "person_push_message_service",
            "attribution_pathway": "explicit_person_id",
        },
        "explanation_source": {
            "source_reference": "concierge.push_person_message",
            "lineage_reference": provenance_id,
            "attribution_explanation_references": [
                messaging_governance_boundary["boundary_path"],
                routing_path,
            ],
        },
        "routing_decision": {
            "requested_target_id": requested_target or None,
            "requested_target_supplied": requested_target_supplied,
            "selected_target_id": selected_target_id,
            "selected_service": selected_service,
            "delivery_channel": delivery_channel,
            "routing_path": routing_path,
            "explicit_entity_target": explicit_entity_target,
        },
        "authority_boundary": {
            "concierge_role": "bounded_consumer_orchestrator",
            "message_authority_external": bool(
                messaging_governance_boundary.get("message_authority_external", False)
            ),
            "provenance_authority_external": bool(
                messaging_governance_boundary.get("provenance_authority_external", False)
            ),
            "household_memory_authority_external": bool(
                messaging_governance_boundary.get("household_memory_authority_external", False)
            ),
            "claims_upstream_truth": False,
            "claims_identity_authority": False,
            "claims_household_memory_authority": False,
        },
    }

    activity_ref = {
        "ref_type": "messaging_provenance",
        "provenance_id": provenance_id,
        "created_at": created_at,
        "source_service": "concierge.push_person_message",
        "delivery_channel": delivery_channel,
        "selected_service": selected_service,
        "selected_target_id": selected_target_id,
        "routing_path": routing_path,
        "requested_target_supplied": requested_target_supplied,
        "explicit_entity_target": explicit_entity_target,
        "created_in_room": linked_area_id,
        "boundary_path": messaging_governance_boundary["boundary_path"],
        "message_authority_external": bool(
            messaging_governance_boundary.get("message_authority_external", False)
        ),
        "provenance_authority_external": bool(
            messaging_governance_boundary.get("provenance_authority_external", False)
        ),
        "household_memory_authority_external": bool(
            messaging_governance_boundary.get("household_memory_authority_external", False)
        ),
        "claims_upstream_truth": False,
        "claims_identity_authority": False,
        "claims_household_memory_authority": False,
        "person_id": person_id,
    }
    return provenance, activity_ref


def _build_notification_delivery_boundary(
    *,
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
    recipient_scope: str,
    message_context_type: str,
    delivery_channel: str,
    selected_service: str,
    selected_target_id: str,
    routing_path: str,
    explicit_entity_target: bool,
) -> dict[str, Any]:
    """Return #341-governed notification/delivery boundary metadata."""
    return {
        "notification_delivery_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_notification_delivery_boundary",
        "deterministic_boundary": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "delivery_behavior_owned_by_concierge": True,
        "delivery_authority_external": True,
        "recipient_authority_external": True,
        "consent_authority_external": True,
        "visibility_authority_external": True,
        "delivery_lifecycle_governed": True,
        "delivery_execution_rules": {
            "invoke_configured_home_assistant_service": True,
            "record_execution_outcome": True,
            "record_delivery_channel": True,
            "record_delivery_target": True,
            "derive_recipient_authority": False,
            "derive_consent_authority": False,
            "derive_visibility_authority": False,
            "derive_truth_authority": False,
        },
        "governance_controls": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "recipient_scope": recipient_scope,
            "message_context_type": message_context_type,
            "delivery_channel": delivery_channel,
            "selected_service": selected_service,
            "selected_target_id": selected_target_id,
            "routing_path": routing_path,
            "explicit_entity_target": explicit_entity_target,
            "delivery_boundary_only": True,
            "recipient_authorization_enabled": False,
            "consent_adjudication_enabled": False,
            "visibility_adjudication_enabled": False,
        },
        "ownership_boundaries": {
            "governance_owner": "homes_that_behave_well",
            "delivery_runtime_owner": "concierge",
            "notification_runtime_owner": "concierge",
            "recipient_authority_owner": "identity_and_presence_governance",
            "consent_authority_owner": "privacy_and_consent_governance",
            "visibility_authority_owner": "privacy_and_consent_governance",
            "provenance_owner": "provenance_governance",
        },
        "diagnostics_and_explainability": {
            "delivery_state_visible": True,
            "delivery_success_state_visible": True,
            "delivery_failure_state_visible": True,
            "recipient_acknowledgement_claimed": False,
            "recipient_seen_claimed": False,
        },
        "deferred_release_4_owners": {
            "recipient_consent_privacy_visibility_boundary": "#342",
            "messaging_diagnostics_explainability": "#343",
            "release_4_validation": "#349",
        },
    }


def _to_str_list(value: Any) -> list[str]:
    """Return a normalized string list from optional config values."""
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _build_recipient_consent_privacy_visibility_boundary(
    *,
    profile: PersonProfile,
    requested_target: str,
    selected_target_id: str,
    selected_service: str,
    delivery_channel: str,
    routing_path: str,
    explicit_entity_target: bool,
    route_scope: str,
    context_area_id: str | None,
) -> tuple[dict[str, Any], dict[str, Any], bool, str]:
    """Return #342-governed recipient/consent/privacy/visibility boundary metadata and decision."""
    consent = profile.consent if isinstance(profile.consent, dict) else {}
    recipient_eligible = bool(consent.get("recipient_eligible", True))
    require_delivery_consent = bool(consent.get("require_delivery_consent", False))
    consent_granted = bool(consent.get("delivery_consent_granted", False))
    privacy_mode = str(consent.get("privacy_mode", "standard") or "standard").strip().lower()
    visibility_mode = str(consent.get("visibility_mode", "standard") or "standard").strip().lower()
    allowed_delivery_channels = {
        item.lower() for item in _to_str_list(consent.get("allowed_delivery_channels"))
    }
    blocked_delivery_targets = {
        item.lower() for item in _to_str_list(consent.get("blocked_delivery_targets"))
    }
    blocked_services = {item.lower() for item in _to_str_list(consent.get("blocked_services"))}
    allowed_private_channels = {"mobile_notify", "web_ui"}

    decision_allowed = True
    decision_reason = "delivery_permitted"

    if not recipient_eligible:
        decision_allowed = False
        decision_reason = "recipient_not_eligible"
    elif require_delivery_consent and not consent_granted:
        decision_allowed = False
        decision_reason = "consent_required_not_granted"
    elif (
        requested_target.lower() in blocked_delivery_targets
        or selected_target_id.lower() in blocked_delivery_targets
        or selected_service.lower() in blocked_services
    ):
        decision_allowed = False
        decision_reason = "delivery_target_blocked"
    elif allowed_delivery_channels and delivery_channel.lower() not in allowed_delivery_channels:
        decision_allowed = False
        decision_reason = "delivery_channel_not_allowed"
    elif privacy_mode == "private_only" and delivery_channel not in allowed_private_channels:
        decision_allowed = False
        decision_reason = "privacy_boundary_channel_restricted"
    elif visibility_mode == "restricted" and delivery_channel in {"voice_assistant", "room_tts"}:
        decision_allowed = False
        decision_reason = "visibility_boundary_channel_restricted"

    boundary = {
        "recipient_consent_privacy_visibility_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_recipient_consent_privacy_visibility_boundary",
        "deterministic_boundary": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "recipient_authority_external": True,
        "consent_authority_external": True,
        "privacy_authority_external": True,
        "visibility_authority_external": True,
        "recipient_boundary_enforced": True,
        "consent_boundary_enforced": True,
        "privacy_boundary_enforced": True,
        "visibility_boundary_enforced": True,
        "governance_controls": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "recipient_scope": "person",
            "message_context_type": "person_push",
            "delivery_channel": delivery_channel,
            "selected_service": selected_service,
            "selected_target_id": selected_target_id,
            "routing_path": routing_path,
            "explicit_entity_target": explicit_entity_target,
            "recipient_boundary_only": True,
            "consent_boundary_only": True,
            "privacy_boundary_only": True,
            "visibility_boundary_only": True,
        },
        "eligibility_decision": {
            "delivery_permitted": decision_allowed,
            "decision_reason": decision_reason,
            "recipient_eligible": recipient_eligible,
            "require_delivery_consent": require_delivery_consent,
            "delivery_consent_granted": consent_granted,
            "privacy_mode": privacy_mode,
            "visibility_mode": visibility_mode,
        },
        "ownership_boundaries": {
            "governance_owner": "homes_that_behave_well",
            "recipient_authority_owner": "identity_and_presence_governance",
            "consent_authority_owner": "privacy_and_consent_governance",
            "privacy_authority_owner": "privacy_and_consent_governance",
            "visibility_authority_owner": "privacy_and_consent_governance",
            "messaging_runtime_owner": "concierge",
        },
        "explainability": {
            "eligibility_explainable": True,
            "denial_explainable": not decision_allowed,
            "recipient_authority_claimed": False,
            "consent_authority_claimed": False,
            "privacy_authority_claimed": False,
            "visibility_authority_claimed": False,
        },
        "deferred_release_4_owners": {
            "messaging_diagnostics_explainability": "#343",
            "household_memory_boundary": "#344",
            "release_4_validation": "#349",
        },
    }

    activity_ref = {
        "ref_type": "recipient_consent_privacy_visibility_boundary",
        "boundary_path": boundary["boundary_path"],
        "delivery_permitted": decision_allowed,
        "decision_reason": decision_reason,
        "recipient_eligible": recipient_eligible,
        "require_delivery_consent": require_delivery_consent,
        "delivery_consent_granted": consent_granted,
        "privacy_mode": privacy_mode,
        "visibility_mode": visibility_mode,
        "delivery_channel": delivery_channel,
        "selected_service": selected_service,
        "selected_target_id": selected_target_id,
        "routing_path": routing_path,
        "explicit_entity_target": explicit_entity_target,
    }
    return boundary, activity_ref, decision_allowed, decision_reason


def _build_messaging_diagnostics_explainability(
    *,
    route_scope: str,
    context_area_id: str | None,
    recipient_scope: str,
    message_context_type: str,
    delivery_permitted: bool,
    decision_reason: str,
    delivery_channel: str,
    selected_service: str,
    selected_target_id: str,
    routing_path: str,
    explicit_entity_target: bool,
    requested_target_supplied: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return #343-governed messaging diagnostics and explainability metadata."""
    governance_boundary_involved = (
        "recipient_consent_privacy_visibility_boundary"
        if not delivery_permitted
        else "notification_delivery_boundary"
    )

    explainability = {
        "messaging_diagnostics_explainability_version": 1,
        "applicable": True,
        "boundary_path": "governed_messaging_diagnostics_explainability",
        "deterministic_explainability": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "questions_answered": {
            "what_happened_explainable": True,
            "why_it_happened_explainable": True,
            "why_delivery_occurred_explainable": delivery_permitted,
            "why_delivery_denied_explainable": not delivery_permitted,
            "governance_boundary_visible": True,
            "routing_path_visible": True,
            "delivery_channel_visible": True,
            "decision_inputs_visible": True,
        },
        "decision_summary": {
            "delivery_permitted": delivery_permitted,
            "decision_reason": decision_reason,
            "governance_boundary_involved": governance_boundary_involved,
            "delivery_channel": delivery_channel,
            "selected_service": selected_service,
            "selected_target_id": selected_target_id,
            "routing_path": routing_path,
            "explicit_entity_target": explicit_entity_target,
        },
        "decision_inputs_used": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "recipient_scope": recipient_scope,
            "message_context_type": message_context_type,
            "requested_target_supplied": requested_target_supplied,
        },
        "logging_strategy": {
            "governance_policy_denied_level": "info",
            "operational_delivery_failure_level": "error",
            "unexpected_runtime_condition_level": "warning",
            "normal_success_level": "debug",
            "governance_outcome_is_operational_failure": False,
        },
        "authority_non_rights": {
            "diagnostics_authority_external": True,
            "explainability_authority_external": True,
            "creates_authority": False,
            "creates_truth": False,
            "creates_memory": False,
            "creates_identity": False,
        },
        "deferred_release_4_owners": {
            "household_memory_boundary": "#344",
            "release_4_validation": "#349",
        },
    }

    activity_ref = {
        "ref_type": "messaging_diagnostics_explainability",
        "boundary_path": explainability["boundary_path"],
        "delivery_permitted": delivery_permitted,
        "decision_reason": decision_reason,
        "governance_boundary_involved": governance_boundary_involved,
        "delivery_channel": delivery_channel,
        "selected_service": selected_service,
        "selected_target_id": selected_target_id,
        "routing_path": routing_path,
        "explicit_entity_target": explicit_entity_target,
        "requested_target_supplied": requested_target_supplied,
    }
    return explainability, activity_ref


def _build_household_memory_governance_boundary(
    *,
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
    recipient_scope: str,
    message_context_type: str,
    delivery_channel: str,
    selected_service: str,
    selected_target_id: str,
    routing_path: str,
    explicit_entity_target: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return #344-governed household-memory boundary metadata and activity ref."""
    boundary = {
        "household_memory_governance_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_household_memory_boundary",
        "deterministic_boundary": True,
        "boundary_status": "active",
        "concierge_role": "bounded_consumer_orchestrator",
        "household_memory_role": "bounded_record_reference_consumer",
        "permitted_role_description": "preserve bounded explainable governed context references only",
        "prohibited_authority_claims": {
            "claims_household_truth_authority": False,
            "claims_identity_authority": False,
            "claims_occupancy_authority": False,
            "claims_messaging_authority": False,
            "claims_consent_authority": False,
            "claims_privacy_authority": False,
            "claims_source_of_truth_authority": False,
        },
        "authority_source_relationships": {
            "references_household_memory_governance": True,
            "references_provenance_authority": True,
            "references_messaging_authority": True,
            "references_identity_authority": True,
            "references_privacy_authority": True,
            "references_retention_authority": True,
            "references_occupancy_authority": True,
            "replaces_any_authority": False,
        },
        "governance_controls": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "recipient_scope": recipient_scope,
            "message_context_type": message_context_type,
            "delivery_channel": delivery_channel,
            "selected_service": selected_service,
            "selected_target_id": selected_target_id,
            "routing_path": routing_path,
            "explicit_entity_target": explicit_entity_target,
            "household_memory_boundary_only": True,
            "ownership_rules_enabled": False,
            "consumption_rules_enabled": False,
            "retention_rules_enabled": False,
            "separation_rules_enabled": False,
        },
        "non_authority_assertions": {
            "memory_is_not_truth": True,
            "memory_is_not_identity": True,
            "memory_is_not_consent": True,
            "memory_is_not_privacy_policy": True,
            "memory_is_not_occupancy": True,
            "memory_is_not_messaging": True,
            "memory_is_not_source_of_record": True,
        },
        "ownership_boundaries": {
            "governance_owner": "homes_that_behave_well",
            "household_memory_governance_owner": "homes_that_behave_well",
            "household_memory_runtime_owner": "concierge",
            "identity_authority_owner": "voice_identity",
            "occupancy_authority_owner": "foundation",
            "messaging_authority_owner": "messaging_systems",
            "consent_authority_owner": "privacy_and_consent_governance",
            "privacy_authority_owner": "privacy_and_consent_governance",
            "provenance_owner": "provenance_governance",
        },
        "deferred_release_4_owners": {
            "memory_ownership_and_consumption_boundary": "#345",
            "memory_identity_privacy_retention_separation": "#346",
            "memory_messaging_continuity_affinity_occupancy_restoration_separation": "#347",
            "memory_provenance_diagnostics_explainability": "#348",
            "release_4_validation": "#349",
        },
    }

    ref = {
        "ref_type": "household_memory_governance_boundary",
        "boundary_path": boundary["boundary_path"],
        "boundary_status": boundary["boundary_status"],
        "household_memory_role": boundary["household_memory_role"],
        "route_scope": route_scope,
        "context_area_id": context_area_id,
        "resolved_composite_id": resolved_composite_id,
        "recipient_scope": recipient_scope,
        "message_context_type": message_context_type,
        "delivery_channel": delivery_channel,
        "selected_service": selected_service,
        "selected_target_id": selected_target_id,
        "routing_path": routing_path,
        "explicit_entity_target": explicit_entity_target,
        "claims_household_truth_authority": False,
        "claims_identity_authority": False,
        "claims_occupancy_authority": False,
        "claims_messaging_authority": False,
        "claims_consent_authority": False,
        "claims_privacy_authority": False,
        "claims_source_of_truth_authority": False,
    }
    return boundary, ref


def _build_household_memory_ownership_consumption_boundary(
    *,
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
    recipient_scope: str,
    message_context_type: str,
    delivery_channel: str,
    selected_service: str,
    selected_target_id: str,
    routing_path: str,
    explicit_entity_target: bool,
    consumption_permitted: bool,
    consumption_decision_reason: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return #345-governed household-memory ownership/consumption metadata and activity ref."""
    boundary = {
        "household_memory_ownership_consumption_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_household_memory_ownership_consumption_boundary",
        "deterministic_boundary": True,
        "boundary_status": "active",
        "concierge_role": "bounded_consumer_orchestrator",
        "memory_ownership": {
            "memory_owner": "household_memory_governance",
            "memory_runtime_owner": "concierge",
            "ownership_authority_source": "household_memory_contract",
            "ownership_reason": "governed_household_memory_contract_boundary",
            "ownership_scope": "bounded_memory_visibility_and_explainability_references",
            "owner_may_create_memory_references": True,
            "owner_may_create_authority": False,
            "owner_may_replace_source_of_truth": False,
        },
        "memory_creation_boundary": {
            "creation_allowed": True,
            "created_by_role": "bounded_consumer_orchestrator",
            "creation_source_requirements": {
                "consume_governed_inputs_only": True,
                "provenance_reference_required": True,
                "event_reference_required": False,
                "creates_authority": False,
                "creates_source_of_truth": False,
            },
        },
        "memory_consumption_boundary": {
            "consumption_permitted": consumption_permitted,
            "consumption_decision_reason": consumption_decision_reason,
            "allowed_consumers": [
                "concierge_orchestration_runtime",
                "concierge_messaging_explainability_runtime",
                "concierge_diagnostics_visibility_runtime",
            ],
            "prohibited_consumption_claims": {
                "consumption_claims_identity_authority": False,
                "consumption_claims_occupancy_authority": False,
                "consumption_claims_messaging_authority": False,
                "consumption_claims_consent_authority": False,
                "consumption_claims_privacy_authority": False,
                "consumption_claims_source_of_truth_authority": False,
            },
        },
        "authority_relationships": {
            "references_household_memory_contract_authority": True,
            "references_household_memory_model_authority": True,
            "references_provenance_authority": True,
            "references_event_authority": True,
            "references_signal_authority": True,
            "redefines_identity_authority": False,
            "redefines_occupancy_authority": False,
            "redefines_messaging_authority": False,
            "redefines_consent_authority": False,
            "redefines_privacy_authority": False,
            "replaces_source_of_truth_authority": False,
        },
        "governance_controls": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "recipient_scope": recipient_scope,
            "message_context_type": message_context_type,
            "delivery_channel": delivery_channel,
            "selected_service": selected_service,
            "selected_target_id": selected_target_id,
            "routing_path": routing_path,
            "explicit_entity_target": explicit_entity_target,
            "ownership_boundary_only": True,
            "consumption_boundary_only": True,
            "retention_rules_enabled": False,
            "separation_rules_enabled": False,
        },
        "ownership_explainability": {
            "ownership_explainable": True,
            "ownership_authority_claimed": False,
            "ownership_source_of_truth_claimed": False,
        },
        "consumption_explainability": {
            "consumption_explainable": True,
            "consumption_allowed": consumption_permitted,
            "consumption_denied": not consumption_permitted,
            "consumption_reason": consumption_decision_reason,
            "consumption_authority_claimed": False,
        },
        "non_authority_assertions": {
            "ownership_is_not_authority": True,
            "consumption_is_not_authority": True,
            "memory_is_not_identity": True,
            "memory_is_not_occupancy": True,
            "memory_is_not_messaging": True,
            "memory_is_not_consent": True,
            "memory_is_not_privacy_policy": True,
            "memory_is_not_source_of_record": True,
        },
        "deferred_release_4_owners": {
            "memory_identity_privacy_retention_separation": "#346",
            "memory_messaging_continuity_affinity_occupancy_restoration_separation": "#347",
            "memory_provenance_diagnostics_explainability": "#348",
            "release_4_validation": "#349",
        },
    }

    ref = {
        "ref_type": "household_memory_ownership_consumption_boundary",
        "boundary_path": boundary["boundary_path"],
        "boundary_status": boundary["boundary_status"],
        "memory_owner": boundary["memory_ownership"]["memory_owner"],
        "memory_runtime_owner": boundary["memory_ownership"]["memory_runtime_owner"],
        "consumption_permitted": consumption_permitted,
        "consumption_decision_reason": consumption_decision_reason,
        "route_scope": route_scope,
        "context_area_id": context_area_id,
        "resolved_composite_id": resolved_composite_id,
        "recipient_scope": recipient_scope,
        "message_context_type": message_context_type,
        "delivery_channel": delivery_channel,
        "selected_service": selected_service,
        "selected_target_id": selected_target_id,
        "routing_path": routing_path,
        "explicit_entity_target": explicit_entity_target,
        "claims_household_truth_authority": False,
        "claims_identity_authority": False,
        "claims_occupancy_authority": False,
        "claims_messaging_authority": False,
        "claims_consent_authority": False,
        "claims_privacy_authority": False,
        "claims_source_of_truth_authority": False,
    }
    return boundary, ref


def _build_household_memory_identity_privacy_retention_separation_boundary(
    *,
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
    recipient_scope: str,
    message_context_type: str,
    delivery_channel: str,
    selected_service: str,
    selected_target_id: str,
    routing_path: str,
    explicit_entity_target: bool,
    separation_permitted: bool,
    separation_decision_reason: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return #346-governed household-memory identity/privacy/retention separation metadata."""
    boundary = {
        "household_memory_identity_privacy_retention_separation_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_household_memory_identity_privacy_retention_separation_boundary",
        "deterministic_boundary": True,
        "boundary_status": "active",
        "concierge_role": "bounded_consumer_orchestrator",
        "identity_separation": {
            "identity_separated": True,
            "identity_reference_mode": "bounded_identity_context_reference_only",
            "identity_relationship_reference": "voice_identity_authority_external",
            "identity_authority_claimed": False,
            "identity_truth_decision_enabled": False,
            "identity_resolution_performed": False,
        },
        "privacy_separation": {
            "privacy_separated": True,
            "privacy_boundary_path": "governed_recipient_consent_privacy_visibility_boundary",
            "privacy_reference_mode": "governed_boundary_consumption_only",
            "privacy_authority_claimed": False,
            "privacy_policy_decision_enabled": False,
            "private_memory_content_exposed": False,
        },
        "retention_separation": {
            "retention_separated": True,
            "retention_boundary_mode": "metadata_only",
            "retention_authority_relationship": "htbw_governed_retention_policy_external",
            "retention_authority_claimed": False,
            "retention_decision_enabled": False,
            "retention_deletion_enabled": False,
            "retention_expiration_scheduler_enabled": False,
            "retention_archival_enabled": False,
        },
        "separation_boundary_assertions": {
            "memory_does_not_claim_identity_authority": True,
            "memory_does_not_claim_privacy_authority": True,
            "memory_does_not_claim_retention_authority": True,
            "memory_does_not_claim_source_of_truth_authority": True,
            "memory_does_not_expose_identity_internals": True,
            "memory_does_not_expose_private_memory_content": True,
        },
        "authority_relationships": {
            "references_household_memory_contract_authority": True,
            "references_household_memory_model_authority": True,
            "references_provenance_authority": True,
            "references_privacy_boundary_authority": True,
            "references_identity_authority": True,
            "references_retention_authority": True,
            "redefines_identity_authority": False,
            "redefines_privacy_authority": False,
            "redefines_retention_authority": False,
            "replaces_source_of_truth_authority": False,
        },
        "governance_controls": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "recipient_scope": recipient_scope,
            "message_context_type": message_context_type,
            "delivery_channel": delivery_channel,
            "selected_service": selected_service,
            "selected_target_id": selected_target_id,
            "routing_path": routing_path,
            "explicit_entity_target": explicit_entity_target,
            "identity_separation_boundary_only": True,
            "privacy_separation_boundary_only": True,
            "retention_separation_boundary_only": True,
            "cross_domain_separation_enabled": False,
        },
        "separation_explainability": {
            "separation_explainable": True,
            "separation_permitted": separation_permitted,
            "separation_decision_reason": separation_decision_reason,
            "identity_behavior_not_performed": "identity_authority_or_resolution_not_performed",
            "privacy_behavior_not_performed": "privacy_policy_authority_not_performed",
            "retention_behavior_not_performed": "retention_policy_execution_not_performed",
        },
        "non_authority_assertions": {
            "identity_reference_is_not_identity_authority": True,
            "privacy_classification_is_not_privacy_authority": True,
            "retention_metadata_is_not_retention_authority": True,
            "memory_is_not_source_of_truth": True,
        },
        "deferred_release_4_owners": {
            "memory_messaging_continuity_affinity_occupancy_restoration_separation": "#347",
            "memory_provenance_diagnostics_explainability": "#348",
            "release_4_validation": "#349",
        },
    }

    ref = {
        "ref_type": "household_memory_identity_privacy_retention_separation_boundary",
        "boundary_path": boundary["boundary_path"],
        "boundary_status": boundary["boundary_status"],
        "identity_separated": True,
        "privacy_separated": True,
        "retention_separated": True,
        "separation_permitted": separation_permitted,
        "separation_decision_reason": separation_decision_reason,
        "route_scope": route_scope,
        "context_area_id": context_area_id,
        "resolved_composite_id": resolved_composite_id,
        "recipient_scope": recipient_scope,
        "message_context_type": message_context_type,
        "delivery_channel": delivery_channel,
        "selected_service": selected_service,
        "selected_target_id": selected_target_id,
        "routing_path": routing_path,
        "explicit_entity_target": explicit_entity_target,
        "claims_identity_authority": False,
        "claims_privacy_authority": False,
        "claims_retention_authority": False,
        "claims_source_of_truth_authority": False,
    }
    return boundary, ref


def _build_household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary(
    *,
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
    recipient_scope: str,
    message_context_type: str,
    delivery_channel: str,
    selected_service: str,
    selected_target_id: str,
    routing_path: str,
    explicit_entity_target: bool,
    separation_permitted: bool,
    separation_decision_reason: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return #347-governed household-memory separation metadata for messaging/continuity/affinity/occupancy/restoration."""
    boundary = {
        "household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary",
        "deterministic_boundary": True,
        "boundary_status": "active",
        "concierge_role": "bounded_consumer_orchestrator",
        "messaging_separation": {
            "messaging_separated": True,
            "messaging_reference_mode": "bounded_messaging_context_reference_only",
            "messaging_authority_claimed": False,
            "messaging_delivery_authority_claimed": False,
            "messaging_truth_authority_claimed": False,
        },
        "continuity_separation": {
            "continuity_separated": True,
            "continuity_reference_mode": "bounded_continuity_context_reference_only",
            "continuity_authority_claimed": False,
            "continuity_reconstruction_enabled": False,
        },
        "affinity_separation": {
            "affinity_separated": True,
            "affinity_reference_mode": "bounded_affinity_context_reference_only",
            "affinity_authority_claimed": False,
            "affinity_scoring_enabled": False,
            "affinity_ranking_enabled": False,
        },
        "occupancy_separation": {
            "occupancy_separated": True,
            "occupancy_reference_mode": "bounded_occupancy_context_reference_only",
            "occupancy_authority_claimed": False,
            "occupancy_truth_determination_enabled": False,
        },
        "restoration_separation": {
            "restoration_separated": True,
            "restoration_reference_mode": "bounded_restoration_context_reference_only",
            "restoration_authority_claimed": False,
            "restoration_execution_enabled": False,
            "restoration_outcome_ownership_claimed": False,
        },
        "authority_relationships": {
            "references_household_memory_contract_authority": True,
            "references_household_memory_model_authority": True,
            "references_provenance_authority": True,
            "references_messaging_authority": True,
            "references_continuity_authority": True,
            "references_affinity_authority": True,
            "references_occupancy_authority": True,
            "references_restoration_authority": True,
            "redefines_messaging_authority": False,
            "redefines_continuity_authority": False,
            "redefines_affinity_authority": False,
            "redefines_occupancy_authority": False,
            "redefines_restoration_authority": False,
            "replaces_source_of_truth_authority": False,
        },
        "governance_controls": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "recipient_scope": recipient_scope,
            "message_context_type": message_context_type,
            "delivery_channel": delivery_channel,
            "selected_service": selected_service,
            "selected_target_id": selected_target_id,
            "routing_path": routing_path,
            "explicit_entity_target": explicit_entity_target,
            "messaging_separation_boundary_only": True,
            "continuity_separation_boundary_only": True,
            "affinity_separation_boundary_only": True,
            "occupancy_separation_boundary_only": True,
            "restoration_separation_boundary_only": True,
            "provenance_expansion_enabled": False,
        },
        "separation_explainability": {
            "separation_explainable": True,
            "separation_permitted": separation_permitted,
            "separation_decision_reason": separation_decision_reason,
            "messaging_behavior_not_performed": "messaging_authority_or_delivery_or_truth_not_performed",
            "continuity_behavior_not_performed": "continuity_authority_or_reconstruction_not_performed",
            "affinity_behavior_not_performed": "affinity_authority_or_scoring_not_performed",
            "occupancy_behavior_not_performed": "occupancy_authority_or_truth_not_performed",
            "restoration_behavior_not_performed": "restoration_authority_or_execution_not_performed",
        },
        "non_authority_assertions": {
            "memory_reference_is_not_messaging_authority": True,
            "memory_reference_is_not_continuity_authority": True,
            "memory_reference_is_not_affinity_authority": True,
            "memory_reference_is_not_occupancy_authority": True,
            "memory_reference_is_not_restoration_authority": True,
            "memory_is_not_source_of_truth": True,
        },
        "deferred_release_4_owners": {
            "memory_provenance_diagnostics_explainability": "#348",
            "release_4_validation": "#349",
        },
    }

    ref = {
        "ref_type": "household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary",
        "boundary_path": boundary["boundary_path"],
        "boundary_status": boundary["boundary_status"],
        "messaging_separated": True,
        "continuity_separated": True,
        "affinity_separated": True,
        "occupancy_separated": True,
        "restoration_separated": True,
        "separation_permitted": separation_permitted,
        "separation_decision_reason": separation_decision_reason,
        "route_scope": route_scope,
        "context_area_id": context_area_id,
        "resolved_composite_id": resolved_composite_id,
        "recipient_scope": recipient_scope,
        "message_context_type": message_context_type,
        "delivery_channel": delivery_channel,
        "selected_service": selected_service,
        "selected_target_id": selected_target_id,
        "routing_path": routing_path,
        "explicit_entity_target": explicit_entity_target,
        "claims_household_truth_authority": False,
        "claims_messaging_authority": False,
        "claims_continuity_authority": False,
        "claims_affinity_authority": False,
        "claims_occupancy_authority": False,
        "claims_restoration_authority": False,
        "claims_source_of_truth_authority": False,
    }
    return boundary, ref


def _build_household_memory_provenance_diagnostics_explainability_boundary(
    *,
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
    recipient_scope: str,
    message_context_type: str,
    delivery_channel: str,
    selected_service: str,
    selected_target_id: str,
    routing_path: str,
    explicit_entity_target: bool,
    delivery_permitted: bool,
    decision_reason: str,
    governance_boundary_involved: str,
    provenance_id: str,
    provenance_source_service: str,
    created_in_room: str | None,
    requested_target_supplied: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return #348-governed household-memory provenance/diagnostics/explainability metadata."""
    boundary = {
        "household_memory_provenance_diagnostics_explainability_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_household_memory_provenance_diagnostics_explainability_boundary",
        "deterministic_boundary": True,
        "boundary_status": "active",
        "concierge_role": "bounded_consumer_orchestrator",
        "provenance_visibility": {
            "provenance_ref_count": 1,
            "provenance_status": "active",
            "provenance_reference_type": "messaging_provenance",
            "provenance_id": provenance_id,
            "provenance_source_service": provenance_source_service,
            "provenance_created_in_room": created_in_room,
            "provenance_authority_external": True,
            "provenance_reconstruction_enabled": False,
            "provenance_replacement_enabled": False,
        },
        "diagnostics_visibility": {
            "governance_boundary_ref_count": 1,
            "ownership_boundary_ref_count": 1,
            "consumption_boundary_ref_count": 1,
            "identity_privacy_retention_separation_ref_count": 1,
            "messaging_continuity_affinity_occupancy_restoration_separation_ref_count": 1,
            "provenance_ref_count": 1,
            "latest_governance_status": "active",
            "latest_ownership_status": "active",
            "latest_consumption_status": "active",
            "latest_identity_privacy_retention_separation_status": "active",
            "latest_messaging_continuity_affinity_occupancy_restoration_separation_status": "active",
            "latest_provenance_status": "active",
        },
        "explainability_visibility": {
            "what_happened_explainable": True,
            "why_it_happened_explainable": True,
            "which_boundary_applied_explainable": True,
            "which_authority_established_outcome_explainable": True,
            "which_authority_not_claimed_explainable": True,
            "runtime_derived_only": True,
            "generated_reasoning_used": False,
            "probabilistic_reasoning_used": False,
        },
        "governance_explainability": {
            "delivery_permitted": delivery_permitted,
            "decision_reason": decision_reason,
            "governance_boundary_involved": governance_boundary_involved,
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "recipient_scope": recipient_scope,
            "message_context_type": message_context_type,
            "delivery_channel": delivery_channel,
            "selected_service": selected_service,
            "selected_target_id": selected_target_id,
            "routing_path": routing_path,
            "explicit_entity_target": explicit_entity_target,
            "requested_target_supplied": requested_target_supplied,
        },
        "authority_relationships": {
            "references_household_memory_contract_authority": True,
            "references_household_memory_model_authority": True,
            "references_provenance_contract_authority": True,
            "references_provenance_model_authority": True,
            "references_governance_diagnostics_authority": True,
            "redefines_household_truth_authority": False,
            "redefines_identity_authority": False,
            "redefines_messaging_authority": False,
            "redefines_occupancy_authority": False,
            "redefines_privacy_authority": False,
            "redefines_retention_authority": False,
            "redefines_restoration_authority": False,
            "replaces_source_of_truth_authority": False,
        },
        "non_authority_assertions": {
            "claims_household_truth_authority": False,
            "claims_identity_authority": False,
            "claims_messaging_authority": False,
            "claims_continuity_authority": False,
            "claims_affinity_authority": False,
            "claims_occupancy_authority": False,
            "claims_privacy_authority": False,
            "claims_retention_authority": False,
            "claims_restoration_authority": False,
            "claims_source_of_truth_authority": False,
        },
        "deferred_release_4_owners": {
            "release_4_validation": "#349",
        },
    }

    ref = {
        "ref_type": "household_memory_provenance_diagnostics_explainability_boundary",
        "boundary_path": boundary["boundary_path"],
        "boundary_status": boundary["boundary_status"],
        "provenance_ref_count": 1,
        "provenance_status": "active",
        "governance_boundary_ref_count": 1,
        "ownership_boundary_ref_count": 1,
        "consumption_boundary_ref_count": 1,
        "identity_privacy_retention_separation_ref_count": 1,
        "messaging_continuity_affinity_occupancy_restoration_separation_ref_count": 1,
        "delivery_permitted": delivery_permitted,
        "decision_reason": decision_reason,
        "governance_boundary_involved": governance_boundary_involved,
        "route_scope": route_scope,
        "context_area_id": context_area_id,
        "resolved_composite_id": resolved_composite_id,
        "recipient_scope": recipient_scope,
        "message_context_type": message_context_type,
        "delivery_channel": delivery_channel,
        "selected_service": selected_service,
        "selected_target_id": selected_target_id,
        "routing_path": routing_path,
        "explicit_entity_target": explicit_entity_target,
        "requested_target_supplied": requested_target_supplied,
        "provenance_id": provenance_id,
        "provenance_source_service": provenance_source_service,
        "provenance_created_in_room": created_in_room,
        "claims_household_truth_authority": False,
        "claims_identity_authority": False,
        "claims_messaging_authority": False,
        "claims_continuity_authority": False,
        "claims_affinity_authority": False,
        "claims_occupancy_authority": False,
        "claims_privacy_authority": False,
        "claims_retention_authority": False,
        "claims_restoration_authority": False,
        "claims_source_of_truth_authority": False,
    }
    return boundary, ref


async def _resolve_tts_media_id(
    hass: HomeAssistant,
    *,
    provider: str,
    message: str,
    language: str,
    voice: str,
) -> str:
    """Generate a TTS media identifier using the configured provider and voice settings."""
    engine_entity_id = TTS_PROVIDER_ENTITY_IDS.get(provider)
    if engine_entity_id is None:
        return ""

    payload: dict[str, Any] = {
        "engine_id": engine_entity_id,
        "message": message,
        "cache": False,
    }
    if language:
        payload["language"] = language
    if voice:
        payload["options"] = {"voice": voice}

    try:
        result = await hass.services.async_call(
            "tts",
            "get_url",
            payload,
            blocking=True,
            return_response=True,
        )
    except Exception:
        return ""

    if not isinstance(result, dict):
        return ""
    media_id = str(result.get("path") or result.get("url") or "").strip()
    return media_id

def _resolve_target_from_alias(target: str, area_id: str | None, aliases: dict[str, str]) -> str:
    """Resolve execution alias to concrete target string if configured."""
    if area_id and target in aliases:
        return aliases[target]
    return target


def _room_vocabulary_feature_options(state) -> dict[str, Any]:
    """Return configured room vocabulary feature options when enabled."""
    raw = state.global_features.get("room_vocabulary_registry", {})
    if not isinstance(raw, dict):
        return {}
    if "enabled" in raw and not bool(raw.get("enabled", False)):
        return {}
    options = raw.get("options", {})
    return options if isinstance(options, dict) else {}


def _entry_term(entry: dict[str, Any]) -> str:
    """Extract canonical vocabulary term from one registry entry."""
    direct = str(entry.get("term", "") or "").strip()
    if direct:
        return direct
    nested = entry.get("vocabulary_entry", {})
    if isinstance(nested, dict):
        return str(nested.get("term", "") or "").strip()
    return ""


def _entry_alias_terms(entry: dict[str, Any]) -> list[str]:
    """Extract alias terms from one registry entry."""
    values: list[str] = []
    aliases = entry.get("aliases", [])
    if isinstance(aliases, list):
        for item in aliases:
            if isinstance(item, str):
                text = item.strip()
                if text:
                    values.append(text)
            elif isinstance(item, dict):
                text = str(item.get("alias_term", "") or "").strip()
                if text:
                    values.append(text)
    return values


def _entry_scope_ids(entry: dict[str, Any]) -> tuple[str | None, str | None]:
    """Extract room/composite scope references from one registry entry."""
    area_id = str(entry.get("area_id", "") or "").strip() or None
    composite_id = str(entry.get("composite_id", "") or "").strip() or None
    if area_id or composite_id:
        return area_id, composite_id

    room_refs = entry.get("room_references", [])
    if isinstance(room_refs, list):
        for ref in room_refs:
            if not isinstance(ref, dict):
                continue
            area_id = str(ref.get("area_id", "") or "").strip() or None
            composite_id = str(ref.get("composite_id", "") or "").strip() or None
            if area_id or composite_id:
                return area_id, composite_id
    return None, None


def _resolve_room_scope_from_vocabulary(
    state,
    term: str,
) -> dict[str, Any] | None:
    """Resolve one room/composite scope from authoritative room vocabulary outputs."""
    options = _room_vocabulary_feature_options(state)
    entries = options.get("entries", [])
    if not isinstance(entries, list):
        return None

    probe = term.strip().lower()
    if not probe:
        return None

    matches: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        canonical = _entry_term(entry)
        aliases = _entry_alias_terms(entry)
        area_id, composite_id = _entry_scope_ids(entry)
        if not area_id and not composite_id:
            continue

        terms = [canonical, *aliases]
        normalized = [item.strip().lower() for item in terms if item.strip()]
        if probe not in normalized:
            continue
        matches.append(
            {
                "matched_term": probe,
                "canonical_term": canonical,
                "area_id": area_id,
                "composite_id": composite_id,
                "source": "room_vocabulary_registry",
            }
        )

    if not matches:
        return None

    unique_scopes = {(item.get("area_id"), item.get("composite_id")) for item in matches}
    if len(unique_scopes) > 1:
        raise vol.Invalid("room_vocabulary_ambiguous_scope")

    return matches[0]


def _device_entity_vocabulary_feature_options(state) -> dict[str, Any]:
    """Return configured device/entity vocabulary feature options when enabled."""
    raw = state.global_features.get("device_entity_vocabulary_registry", {})
    if not isinstance(raw, dict):
        return {}
    if "enabled" in raw and not bool(raw.get("enabled", False)):
        return {}
    options = raw.get("options", {})
    return options if isinstance(options, dict) else {}


def _entry_entity_targets(entry: dict[str, Any]) -> list[str]:
    """Extract candidate entity targets from one device/entity vocabulary entry."""
    targets: list[str] = []
    single = str(entry.get("entity_id", "") or "").strip()
    if single:
        targets.append(single)

    multiple = entry.get("entity_ids", [])
    if isinstance(multiple, list):
        for item in multiple:
            if not isinstance(item, str):
                continue
            value = item.strip()
            if value:
                targets.append(value)

    return list(dict.fromkeys(targets))


def _entry_matches_scope(
    entry: dict[str, Any],
    *,
    area_id: str | None,
    composite_id: str | None,
) -> bool:
    """Validate one vocabulary entry against resolved room/composite scope."""
    entry_area_id, entry_composite_id = _entry_scope_ids(entry)

    if composite_id:
        if entry_composite_id:
            return entry_composite_id == composite_id
        return False

    if area_id:
        if entry_area_id:
            return entry_area_id == area_id
        return False

    return not entry_area_id and not entry_composite_id


def _resolve_entity_target_from_vocabulary(
    state,
    *,
    term: str,
    area_id: str | None,
    composite_id: str | None,
) -> dict[str, Any] | None:
    """Resolve one device/entity target from authoritative vocabulary outputs."""
    options = _device_entity_vocabulary_feature_options(state)
    entries = options.get("entries", [])
    if not isinstance(entries, list):
        return None

    probe = term.strip().lower()
    if not probe:
        return None

    matches: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if not _entry_matches_scope(entry, area_id=area_id, composite_id=composite_id):
            continue

        canonical = _entry_term(entry)
        aliases = _entry_alias_terms(entry)
        terms = [canonical, *aliases]
        normalized = [item.strip().lower() for item in terms if item.strip()]
        if probe not in normalized:
            continue

        targets = _entry_entity_targets(entry)
        if len(targets) == 0:
            continue
        if len(targets) > 1:
            raise vol.Invalid("device_entity_vocabulary_ambiguous_target")

        matches.append(
            {
                "matched_term": probe,
                "canonical_term": canonical,
                "entity_id": targets[0],
                "area_id": area_id,
                "composite_id": composite_id,
                "source": "device_entity_vocabulary_registry",
            }
        )

    if not matches:
        return None

    unique_entities = {item["entity_id"] for item in matches}
    if len(unique_entities) > 1:
        raise vol.Invalid("device_entity_vocabulary_ambiguous_target")

    return matches[0]


def _asset_vocabulary_feature_options(state) -> dict[str, Any]:
    """Return configured asset vocabulary feature options when enabled."""
    raw = state.global_features.get("asset_vocabulary_registry", {})
    if not isinstance(raw, dict):
        return {}
    if "enabled" in raw and not bool(raw.get("enabled", False)):
        return {}
    options = raw.get("options", {})
    return options if isinstance(options, dict) else {}


def _entry_asset_targets(entry: dict[str, Any]) -> list[str]:
    """Extract handed-off entity targets from one asset vocabulary entry."""
    targets: list[str] = []

    for field_name in (
        "handoff_entity_id",
        "target_entity_id",
        "asset_entity_id",
        "entity_id",
    ):
        value = str(entry.get(field_name, "") or "").strip()
        if value:
            targets.append(value)

    for field_name in ("handoff_entity_ids", "target_entity_ids", "entity_ids"):
        values = entry.get(field_name, [])
        if not isinstance(values, list):
            continue
        for item in values:
            if not isinstance(item, str):
                continue
            value = item.strip()
            if value:
                targets.append(value)

    return list(dict.fromkeys(targets))


def _resolve_asset_target_from_handoff(
    state,
    *,
    term: str,
    area_id: str | None,
    composite_id: str | None,
) -> dict[str, Any] | None:
    """Resolve one handed-off entity target from authoritative asset vocabulary outputs."""
    options = _asset_vocabulary_feature_options(state)
    entries = options.get("entries", [])
    if not isinstance(entries, list):
        return None

    probe = term.strip().lower()
    if not probe:
        return None

    matches: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if not _entry_matches_scope(entry, area_id=area_id, composite_id=composite_id):
            continue

        canonical = _entry_term(entry)
        aliases = _entry_alias_terms(entry)
        terms = [canonical, *aliases]
        normalized = [item.strip().lower() for item in terms if item.strip()]
        if probe not in normalized:
            continue

        targets = _entry_asset_targets(entry)
        if len(targets) == 0:
            continue
        if len(targets) > 1:
            raise vol.Invalid("asset_vocabulary_ambiguous_target")

        matches.append(
            {
                "matched_term": probe,
                "canonical_term": canonical,
                "asset_id": str(entry.get("asset_id", "") or "").strip() or None,
                "entity_id": targets[0],
                "area_id": area_id,
                "composite_id": composite_id,
                "source": "asset_intelligence_handoff",
            }
        )

    if not matches:
        return None

    unique_entities = {item["entity_id"] for item in matches}
    if len(unique_entities) > 1:
        raise vol.Invalid("asset_vocabulary_ambiguous_target")

    return matches[0]


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


def _require_known_area_id(hass: HomeAssistant, area_id: str, *, field_name: str = "area_id") -> None:
    """Require room-scoped mutations to reference Foundation-owned area truth."""
    if ar.async_get(hass).async_get_area(area_id) is None:
        raise vol.Invalid(f"{field_name} does not exist in Home Assistant area registry: {area_id}")


def _resolve_context_composite(
    state,
    *,
    requested_area_id: str | None,
    composite_id: str | None,
):
    """Resolve composite context deterministically from explicit or member area input."""
    if composite_id:
        composite = state.composites.get(composite_id)
        if composite is None:
            raise vol.Invalid(f"composite_id is not configured: {composite_id}")
        if not composite.enabled:
            raise vol.Invalid(f"composite_id is disabled: {composite_id}")
        return composite

    if not requested_area_id:
        return None

    for configured_id in sorted(state.composites):
        composite = state.composites[configured_id]
        if composite.enabled and requested_area_id in composite.area_ids:
            return composite

    return None


def _select_context_entries(
    state,
    *,
    room,
) -> list[dict[str, Any]]:
    """Return deterministic room-projected global context entries."""
    selected: list[dict[str, Any]] = []
    global_overlays = room.global_overlays if room is not None else {}

    for context_type in sorted(state.contexts):
        context = state.contexts[context_type]
        usage = state.global_context_usage.get(context_type, {})
        globally_enabled = bool(usage.get("enabled", context.available))
        room_enabled = bool(global_overlays.get(context_type, True))
        projection_enabled = globally_enabled and room_enabled and context.available
        if not projection_enabled:
            continue
        selected.append(
            {
                "context_type": context.context_type,
                "summary": context.summary,
                "detail": context.detail,
                "speakable": context.speakable,
                "available": context.available,
            }
        )

    return selected


def _select_signal_entries(state) -> list[dict[str, Any]]:
    """Return deterministic runtime signal entries."""
    selected: list[dict[str, Any]] = []
    for signal_type in sorted(state.signals):
        signal = state.signals[signal_type]
        if not signal.available:
            continue
        selected.append(
            {
                "signal_type": signal.signal_type,
                "summary": signal.summary,
                "state": signal.state,
                "available": signal.available,
            }
        )
    return selected


def _assemble_foundation_context(
    state,
    *,
    requested_area_id: str | None = None,
    composite_id: str | None = None,
    person_profile: PersonProfile | None = None,
    include_context: bool = True,
    include_signals: bool = True,
) -> dict[str, Any]:
    """Assemble a bounded runtime context envelope from existing authoritative inputs."""
    composite = _resolve_context_composite(
        state,
        requested_area_id=requested_area_id,
        composite_id=composite_id,
    )
    resolved_composite_id = composite.composite_id if composite is not None else None
    context_area_id = requested_area_id
    if composite is not None:
        context_area_id = composite.primary_area or (composite.area_ids[0] if composite.area_ids else requested_area_id)

    room = state.rooms.get(context_area_id) if context_area_id else None
    if room is None and requested_area_id and requested_area_id != context_area_id:
        room = state.rooms.get(requested_area_id)

    contexts = _select_context_entries(state, room=room) if include_context else []
    signals = _select_signal_entries(state) if include_signals else []

    summary_parts: list[str] = []
    summary_parts.extend(item["summary"] for item in contexts if item.get("summary"))
    summary_parts.extend(item["summary"] for item in signals if item.get("summary"))

    return {
        "requested_area_id": requested_area_id,
        "context_area_id": context_area_id,
        "resolved_composite_id": resolved_composite_id,
        "room": {
            "area_id": room.area_id if room is not None else context_area_id,
            "posture": room.posture if room is not None else None,
            "global_overlays": dict(room.global_overlays) if room is not None else {},
            "weather_source_entity_ids": list(room.weather_source_entity_ids) if room is not None else [],
            "news_source_entity_ids": list(room.news_source_entity_ids) if room is not None else [],
        },
        "composite": (
            {
                "composite_id": composite.composite_id,
                "name": composite.name,
                "primary_area": composite.primary_area,
                "area_ids": list(composite.area_ids),
            }
            if composite is not None
            else None
        ),
        "person": (
            {
                "person_id": person_profile.person_id,
                "linked_area_id": person_profile.linked_area_id,
            }
            if person_profile is not None
            else None
        ),
        "contexts": contexts,
        "signals": signals,
        "summary": " | ".join(summary_parts),
        "context_source_count": len(contexts),
        "signal_count": len(signals),
    }


def _context_fallback_status(
    state,
    *,
    requested_area_id: str | None,
    assembled_context: dict[str, Any],
) -> dict[str, Any]:
    """Return bounded fallback-context status derived from existing assembled context."""
    has_context_area = bool(assembled_context.get("context_area_id"))
    has_global_context = bool(assembled_context.get("context_source_count", 0))
    requested_room_known = bool(requested_area_id and requested_area_id in state.rooms)

    fallback_reason: str | None = None
    if not requested_area_id:
        fallback_reason = "no_room_context"
    elif not requested_room_known:
        fallback_reason = "room_context_unavailable"
    elif not has_context_area:
        fallback_reason = "context_area_unresolved"

    fallback_applied = bool(fallback_reason and has_global_context)
    return {
        "fallback_context_applied": fallback_applied,
        "fallback_reason": fallback_reason if fallback_applied else None,
        "global_context_continuity_available": has_global_context,
    }


def _resolve_execution_preference_scope_id(
    state,
    *,
    requested_area_id: str | None,
    assembled_context: dict[str, Any] | None,
) -> str | None:
    """Return the most specific configured execution-preference scope."""
    candidates: list[str] = []
    if assembled_context is not None:
        resolved_composite_id = assembled_context.get("resolved_composite_id")
        context_area_id = assembled_context.get("context_area_id")
        if isinstance(resolved_composite_id, str) and resolved_composite_id:
            candidates.append(resolved_composite_id)
        if isinstance(context_area_id, str) and context_area_id:
            candidates.append(context_area_id)
    if requested_area_id and requested_area_id not in candidates:
        candidates.append(requested_area_id)

    for scope_id in candidates:
        if scope_id in state.execution_preferences:
            return scope_id
    return None


def _resolve_preserved_execution_target(
    state,
    *,
    assembled_context: dict[str, Any],
    requested_target: str,
    default_resolved_target: str,
) -> str:
    """Preserve composite-room execution outcomes by honoring composite preferences."""
    resolved_composite_id = assembled_context.get("resolved_composite_id")
    if not isinstance(resolved_composite_id, str) or not resolved_composite_id:
        return default_resolved_target

    preferences = state.execution_preferences.get(resolved_composite_id, {})
    if not isinstance(preferences, dict):
        return default_resolved_target

    preferred_target = str(preferences.get("target", "") or "").strip()
    if not preferred_target:
        return default_resolved_target

    if preferred_target == requested_target:
        return default_resolved_target

    return preferred_target


def _build_execute_envelope(
    state,
    *,
    requested_area_id: str | None,
    call: ServiceCall,
    capabilities: dict[str, Any],
    assembled_context: dict[str, Any],
    resolved_target: str,
    room_vocabulary_resolution: dict[str, Any] | None,
    device_entity_vocabulary_resolution: dict[str, Any] | None,
    asset_vocabulary_resolution: dict[str, Any] | None,
    domain: str,
    service: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Build a bounded execution envelope for orchestration requests."""
    fallback_status = _context_fallback_status(
        state,
        requested_area_id=requested_area_id,
        assembled_context=assembled_context,
    )
    preference_scope_id = _resolve_execution_preference_scope_id(
        state,
        requested_area_id=requested_area_id,
        assembled_context=assembled_context,
    )
    preferences = (
        dict(state.execution_preferences.get(preference_scope_id, {}))
        if preference_scope_id is not None
        else {}
    )
    route_scope = "global"
    if assembled_context.get("resolved_composite_id"):
        route_scope = "composite"
    elif assembled_context.get("context_area_id"):
        route_scope = "room"

    if resolved_target.startswith("scene."):
        plan_kind = "scene_turn_on"
        target_type = "scene"
    elif resolved_target.startswith("script."):
        plan_kind = "script_turn_on"
        target_type = "script"
    else:
        plan_kind = "entity_turn_on"
        target_type = "entity"

    capability_discovery = _build_capability_discovery(
        capabilities=capabilities,
        route_scope=route_scope,
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
        room_vocabulary_resolution=room_vocabulary_resolution,
        device_entity_vocabulary_resolution=device_entity_vocabulary_resolution,
        asset_vocabulary_resolution=asset_vocabulary_resolution,
    )
    experience_governance_boundary = _build_experience_governance_boundary(
        route_scope=route_scope,
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    continuity_governance_boundary = _build_continuity_governance_boundary(
        execution_kind="orchestration",
        route_scope=route_scope,
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    person_room_affinity_boundary = _build_person_room_affinity_boundary(
        execution_kind="orchestration",
        route_scope=route_scope,
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    privacy_household_memory_boundary = _build_privacy_household_memory_boundary(
        execution_kind="orchestration",
        route_scope=route_scope,
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    occupancy_governance_boundary = _build_occupancy_governance_boundary(
        execution_kind="orchestration",
        route_scope=route_scope,
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    presence_governance_boundary = _build_presence_governance_boundary(
        execution_kind="orchestration",
        route_scope=route_scope,
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    guest_unknown_occupant_behavior = _build_guest_unknown_occupant_behavior(
        execution_kind="orchestration",
        route_scope=route_scope,
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
        person_id=call.data.get("person_id"),
        context=call.data.get("context"),
        occupancy_governance_boundary=occupancy_governance_boundary,
        presence_governance_boundary=presence_governance_boundary,
    )
    multi_occupant_behavior = _build_multi_occupant_behavior(
        execution_kind="orchestration",
        route_scope=route_scope,
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
        person_id=call.data.get("person_id"),
        context=call.data.get("context"),
        occupancy_governance_boundary=occupancy_governance_boundary,
        presence_governance_boundary=presence_governance_boundary,
        guest_unknown_occupant_behavior=guest_unknown_occupant_behavior,
    )
    capability_to_experience_handoff = _build_capability_to_experience_handoff(
        capability_discovery=capability_discovery,
        experience_governance_boundary=experience_governance_boundary,
        execution_kind="orchestration",
    )
    experience_projection = _build_experience_projection(
        capability_to_experience_handoff=capability_to_experience_handoff,
        experience_governance_boundary=experience_governance_boundary,
        execution_kind="orchestration",
    )
    experience_restoration_boundary = _build_experience_restoration_boundary(
        experience_projection=experience_projection,
        guest_unknown_occupant_behavior=guest_unknown_occupant_behavior,
        multi_occupant_behavior=multi_occupant_behavior,
        execution_kind="orchestration",
        route_scope=route_scope,
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    experience_restoration_outcome = _build_experience_restoration_outcome(
        experience_projection=experience_projection,
        experience_restoration_boundary=experience_restoration_boundary,
        guest_unknown_occupant_behavior=guest_unknown_occupant_behavior,
        multi_occupant_behavior=multi_occupant_behavior,
        execution_kind="orchestration",
        route_scope=route_scope,
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    e3a_preservation_alignment = _build_e3a_preservation_alignment(
        experience_restoration_boundary=experience_restoration_boundary,
        experience_restoration_outcome=experience_restoration_outcome,
        execution_kind="orchestration",
        route_scope=route_scope,
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
        requested_target=str(call.data["target"]),
        resolved_target=resolved_target,
    )
    return {
        "envelope_version": 1,
        "execution_kind": "orchestration",
        "intent_class": call.data.get("intent_class", "home_control"),
        "capability_projection_boundary": _build_capability_projection_boundary(),
        "authoritative_capability_input_consumption": _build_authoritative_capability_input_consumption(
            capabilities
        ),
        "vocabulary_to_capability_handoff": _build_vocabulary_to_capability_handoff(
            requested_target=str(call.data["target"]),
            resolved_target=resolved_target,
            room_vocabulary_resolution=room_vocabulary_resolution,
            device_entity_vocabulary_resolution=device_entity_vocabulary_resolution,
            asset_vocabulary_resolution=asset_vocabulary_resolution,
        ),
        "asset_intelligence_cp00_handoff": _build_asset_intelligence_cp00_handoff(
            requested_target=str(call.data["target"]),
            resolved_target=resolved_target,
            asset_vocabulary_resolution=asset_vocabulary_resolution,
        ),
        "capability_discovery": capability_discovery,
        "continuity_governance_boundary": continuity_governance_boundary,
        "person_room_affinity_boundary": person_room_affinity_boundary,
        "privacy_household_memory_boundary": privacy_household_memory_boundary,
        "occupancy_governance_boundary": occupancy_governance_boundary,
        "presence_governance_boundary": presence_governance_boundary,
        "guest_unknown_occupant_behavior": guest_unknown_occupant_behavior,
        "multi_occupant_behavior": multi_occupant_behavior,
        "experience_governance_boundary": experience_governance_boundary,
        "capability_to_experience_handoff": capability_to_experience_handoff,
        "experience_projection": experience_projection,
        "experience_restoration_boundary": experience_restoration_boundary,
        "experience_restoration_outcome": experience_restoration_outcome,
        "e3a_preservation_alignment": e3a_preservation_alignment,
        "planning": {
            "plan_kind": plan_kind,
            "target_type": target_type,
            "requested_target": call.data["target"],
            "resolved_target": resolved_target,
        },
        "routing": {
            "route_scope": route_scope,
            "requested_area_id": requested_area_id,
            "context_area_id": assembled_context.get("context_area_id"),
            "resolved_composite_id": assembled_context.get("resolved_composite_id"),
            "execution_preference_scope_id": preference_scope_id,
            "execution_preference_present": bool(preferences),
        },
        "context": {
            "requested_area_id": assembled_context.get("requested_area_id"),
            "context_area_id": assembled_context.get("context_area_id"),
            "resolved_composite_id": assembled_context.get("resolved_composite_id"),
            "summary": assembled_context.get("summary", ""),
            "context_source_count": assembled_context.get("context_source_count", 0),
            "signal_count": assembled_context.get("signal_count", 0),
            "fallback_context_applied": fallback_status["fallback_context_applied"],
            "fallback_reason": fallback_status["fallback_reason"],
            "global_context_continuity_available": fallback_status["global_context_continuity_available"],
        },
        "execution": {
            "domain": domain,
            "service": service,
            "service_data": dict(data),
        },
    }


def _build_execute_direct_envelope(
    *,
    call: ServiceCall,
    capabilities: dict[str, Any],
    domain: str,
    service: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Build a bounded execution envelope for direct execution requests."""
    capability_discovery = {
        "discovery_version": 1,
        "applicable": False,
        "discovery_path": "not_applicable_direct_execution",
        "concierge_role": "bounded_consumer_orchestrator",
        "capability_authority_external": True,
        "deferred_release_2_owners": {
            "capability_diagnostics_explainability": "#318",
            "experience_implementation": "#319+",
        },
    }
    experience_governance_boundary = _build_experience_governance_boundary(
        route_scope="direct",
        context_area_id=None,
        resolved_composite_id=None,
    )
    continuity_governance_boundary = _build_continuity_governance_boundary(
        execution_kind="direct",
        route_scope="direct",
        context_area_id=None,
        resolved_composite_id=None,
    )
    person_room_affinity_boundary = _build_person_room_affinity_boundary(
        execution_kind="direct",
        route_scope="direct",
        context_area_id=None,
        resolved_composite_id=None,
    )
    privacy_household_memory_boundary = _build_privacy_household_memory_boundary(
        execution_kind="direct",
        route_scope="direct",
        context_area_id=None,
        resolved_composite_id=None,
    )
    occupancy_governance_boundary = _build_occupancy_governance_boundary(
        execution_kind="direct",
        route_scope="direct",
        context_area_id=None,
        resolved_composite_id=None,
    )
    presence_governance_boundary = _build_presence_governance_boundary(
        execution_kind="direct",
        route_scope="direct",
        context_area_id=None,
        resolved_composite_id=None,
    )
    guest_unknown_occupant_behavior = _build_guest_unknown_occupant_behavior(
        execution_kind="direct",
        route_scope="direct",
        context_area_id=None,
        resolved_composite_id=None,
        person_id=call.data.get("person_id"),
        context=None,
        occupancy_governance_boundary=occupancy_governance_boundary,
        presence_governance_boundary=presence_governance_boundary,
    )
    multi_occupant_behavior = _build_multi_occupant_behavior(
        execution_kind="direct",
        route_scope="direct",
        context_area_id=None,
        resolved_composite_id=None,
        person_id=call.data.get("person_id"),
        context=None,
        occupancy_governance_boundary=occupancy_governance_boundary,
        presence_governance_boundary=presence_governance_boundary,
        guest_unknown_occupant_behavior=guest_unknown_occupant_behavior,
    )
    capability_to_experience_handoff = _build_capability_to_experience_handoff(
        capability_discovery=capability_discovery,
        experience_governance_boundary=experience_governance_boundary,
        execution_kind="direct",
    )
    experience_projection = _build_experience_projection(
        capability_to_experience_handoff=capability_to_experience_handoff,
        experience_governance_boundary=experience_governance_boundary,
        execution_kind="direct",
    )
    experience_restoration_boundary = _build_experience_restoration_boundary(
        experience_projection=experience_projection,
        guest_unknown_occupant_behavior=guest_unknown_occupant_behavior,
        multi_occupant_behavior=multi_occupant_behavior,
        execution_kind="direct",
        route_scope="direct",
        context_area_id=None,
        resolved_composite_id=None,
    )
    experience_restoration_outcome = _build_experience_restoration_outcome(
        experience_projection=experience_projection,
        experience_restoration_boundary=experience_restoration_boundary,
        guest_unknown_occupant_behavior=guest_unknown_occupant_behavior,
        multi_occupant_behavior=multi_occupant_behavior,
        execution_kind="direct",
        route_scope="direct",
        context_area_id=None,
        resolved_composite_id=None,
    )
    e3a_preservation_alignment = _build_e3a_preservation_alignment(
        experience_restoration_boundary=experience_restoration_boundary,
        experience_restoration_outcome=experience_restoration_outcome,
        execution_kind="direct",
        route_scope="direct",
        context_area_id=None,
        resolved_composite_id=None,
        requested_target=call.data.get("entity_id"),
        resolved_target=call.data.get("entity_id"),
    )
    return {
        "envelope_version": 1,
        "execution_kind": "direct",
        "intent_class": call.data.get("intent_class", "home_control"),
        "capability_projection_boundary": _build_capability_projection_boundary(),
        "authoritative_capability_input_consumption": _build_authoritative_capability_input_consumption(
            capabilities
        ),
        "vocabulary_to_capability_handoff": {
            "handoff_version": 1,
            "applicable": False,
            "handoff_path": "not_applicable_direct_execution",
            "deferred_release_2_owners": {
                "asset_intelligence_cp00_handoff": "#316",
                "capability_discovery": "#317",
                "capability_diagnostics_explainability": "#318",
                "experience_implementation": "#319+",
            },
        },
        "asset_intelligence_cp00_handoff": {
            "handoff_version": 1,
            "applicable": False,
            "handoff_path": "not_applicable_direct_execution",
            "concierge_role": "bounded_consumer_orchestrator",
            "asset_intelligence_authority_preserved": True,
            "authority_chain": [
                "asset_intelligence_authority",
                "asset_intelligence_output",
                "concierge_handoff_consumption",
                "capability_consumption",
            ],
            "deferred_release_2_owners": {
                "capability_discovery": "#317",
                "capability_diagnostics_explainability": "#318",
                "experience_implementation": "#319+",
            },
        },
        "capability_discovery": capability_discovery,
        "continuity_governance_boundary": continuity_governance_boundary,
        "person_room_affinity_boundary": person_room_affinity_boundary,
        "privacy_household_memory_boundary": privacy_household_memory_boundary,
        "occupancy_governance_boundary": occupancy_governance_boundary,
        "presence_governance_boundary": presence_governance_boundary,
        "guest_unknown_occupant_behavior": guest_unknown_occupant_behavior,
        "multi_occupant_behavior": multi_occupant_behavior,
        "experience_governance_boundary": experience_governance_boundary,
        "capability_to_experience_handoff": capability_to_experience_handoff,
        "experience_projection": experience_projection,
        "experience_restoration_boundary": experience_restoration_boundary,
        "experience_restoration_outcome": experience_restoration_outcome,
        "e3a_preservation_alignment": e3a_preservation_alignment,
        "planning": {
            "plan_kind": "direct_service_call",
            "requested_service": call.data["service"],
            "requested_entity_id": call.data["entity_id"],
        },
        "routing": {
            "route_scope": "direct",
            "requested_area_id": None,
            "context_area_id": None,
            "resolved_composite_id": None,
            "execution_preference_scope_id": None,
            "execution_preference_present": False,
        },
        "context": None,
        "execution": {
            "domain": domain,
            "service": service,
            "service_data": dict(data),
        },
    }


def _build_capability_projection_boundary() -> dict[str, Any]:
    """Return the #313-governed capability projection boundary declaration."""
    return {
        "boundary_version": 1,
        "projection_role": "governed_projection_consumer",
        "projection_is_authority": False,
        "coordinator_role": "bounded_consumer_orchestrator",
        "authority_order": [
            "adr",
            "contract",
            "model",
            "existing_implementation",
            "github_issue",
        ],
        "ownership_boundaries": {
            "governance_owner": "homes_that_behave_well",
            "room_truth_owner": "foundation",
            "identity_confidence_owner": "voice_identity",
            "asset_evaluation_owner": "asset_intelligence",
        },
        "deferred_release_2_owners": {
            "authoritative_input_consumption": "#314",
            "vocabulary_to_capability_handoff": "#315",
            "asset_intelligence_cp00_handoff": "#316",
            "capability_discovery": "#317",
            "capability_diagnostics_explainability": "#318",
            "experience_implementation": "#319+",
        },
    }


def _build_authoritative_capability_input_consumption(capabilities: dict[str, Any]) -> dict[str, Any]:
    """Return #314-governed authoritative capability input consumption metadata."""
    snapshot = dict(capabilities.get("input_snapshot", {}))
    return {
        "consumption_version": 1,
        "deterministic_consumption": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "capability_authority_origin": "htbw_governed_contracts_and_models",
        "input_origin_owners": {
            "concierge_config_entry": "home_assistant_config_entry",
            "voice_identity_status": "voice_identity",
        },
        "consumed_inputs": snapshot,
        "derived_capability_flags": {
            "cap_ai": bool(capabilities.get("cap_ai", False)),
            "cap_tts": bool(capabilities.get("cap_tts", False)),
            "cap_persona": bool(capabilities.get("cap_persona", False)),
            "cap_assets": bool(capabilities.get("cap_assets", False)),
            "cap_voice_enrollment": bool(capabilities.get("cap_voice_enrollment", False)),
            "cap_extended_history": bool(capabilities.get("cap_extended_history", False)),
        },
        "deferred_release_2_owners": {
            "vocabulary_to_capability_handoff": "#315",
            "asset_intelligence_cp00_handoff": "#316",
            "capability_discovery": "#317",
            "capability_diagnostics_explainability": "#318",
            "experience_implementation": "#319+",
        },
    }


def _build_vocabulary_to_capability_handoff(
    *,
    requested_target: str,
    resolved_target: str,
    room_vocabulary_resolution: dict[str, Any] | None,
    device_entity_vocabulary_resolution: dict[str, Any] | None,
    asset_vocabulary_resolution: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return #315-governed vocabulary-to-capability handoff metadata."""
    return {
        "handoff_version": 1,
        "applicable": True,
        "deterministic_resolution": True,
        "ambiguity_policy": "reject_on_ambiguous_authoritative_vocabulary",
        "vocabulary_authority_external": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "room_vocabulary_consumed": room_vocabulary_resolution is not None,
        "device_entity_vocabulary_consumed": device_entity_vocabulary_resolution is not None,
        "asset_handoff_consumed": asset_vocabulary_resolution is not None,
        "asset_handoff_deferred_owner": "#316",
        "requested_target": requested_target,
        "resolved_target": resolved_target,
        "room_scope": (
            {
                "matched_term": room_vocabulary_resolution.get("matched_term"),
                "canonical_term": room_vocabulary_resolution.get("canonical_term"),
                "area_id": room_vocabulary_resolution.get("area_id"),
                "composite_id": room_vocabulary_resolution.get("composite_id"),
                "source": room_vocabulary_resolution.get("source", "room_vocabulary_registry"),
            }
            if room_vocabulary_resolution is not None
            else None
        ),
        "capability_target_handoff": (
            {
                "matched_term": device_entity_vocabulary_resolution.get("matched_term"),
                "canonical_term": device_entity_vocabulary_resolution.get("canonical_term"),
                "entity_id": device_entity_vocabulary_resolution.get("entity_id"),
                "area_id": device_entity_vocabulary_resolution.get("area_id"),
                "composite_id": device_entity_vocabulary_resolution.get("composite_id"),
                "source": device_entity_vocabulary_resolution.get(
                    "source",
                    "device_entity_vocabulary_registry",
                ),
            }
            if device_entity_vocabulary_resolution is not None
            else None
        ),
        "handoff_path": "vocabulary_to_capability_consumption",
        "deferred_release_2_owners": {
            "asset_intelligence_cp00_handoff": "#316",
            "capability_discovery": "#317",
            "capability_diagnostics_explainability": "#318",
            "experience_implementation": "#319+",
        },
    }


def _build_asset_intelligence_cp00_handoff(
    *,
    requested_target: str,
    resolved_target: str,
    asset_vocabulary_resolution: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return #316-governed Asset Intelligence CP00 handoff metadata."""
    return {
        "handoff_version": 1,
        "applicable": asset_vocabulary_resolution is not None,
        "deterministic_consumption": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "asset_intelligence_authority_preserved": True,
        "authority_chain": [
            "asset_intelligence_authority",
            "asset_intelligence_output",
            "concierge_handoff_consumption",
            "capability_consumption",
        ],
        "authoritative_origin": {
            "authority_owner": "asset_intelligence",
            "handoff_source": (
                asset_vocabulary_resolution.get("source", "asset_intelligence_handoff")
                if asset_vocabulary_resolution is not None
                else None
            ),
            "concierge_non_rights": [
                "no_asset_evaluation",
                "no_asset_scoring",
                "no_significance_determination",
                "no_asset_lifecycle_ownership",
                "no_recreation_of_asset_intelligence_reasoning",
            ],
        },
        "consumed_handoff_output": (
            {
                "matched_term": asset_vocabulary_resolution.get("matched_term"),
                "canonical_term": asset_vocabulary_resolution.get("canonical_term"),
                "asset_id": asset_vocabulary_resolution.get("asset_id"),
                "handed_off_entity_id": asset_vocabulary_resolution.get("entity_id"),
                "area_id": asset_vocabulary_resolution.get("area_id"),
                "composite_id": asset_vocabulary_resolution.get("composite_id"),
                "requested_target": requested_target,
                "resolved_target": resolved_target,
            }
            if asset_vocabulary_resolution is not None
            else None
        ),
        "deferred_release_2_owners": {
            "capability_discovery": "#317",
            "capability_diagnostics_explainability": "#318",
            "experience_implementation": "#319+",
        },
    }


def _discoverable_capability_entries(capabilities: dict[str, Any]) -> list[dict[str, Any]]:
    """Return deterministic discovery entries assembled from authoritative capability inputs."""
    mapping = [
        ("ai_actions", "cap_ai", "concierge_config_entry.action_provider"),
        ("tts", "cap_tts", "concierge_config_entry.tts_provider"),
        ("persona", "cap_persona", "derived_from_ai_or_tts"),
        ("asset_handoff_consumption", "cap_assets", "concierge_config_entry.asset_intelligence_provider"),
        ("voice_enrollment", "cap_voice_enrollment", "voice_identity_readiness_plus_archive"),
        ("extended_history", "cap_extended_history", "concierge_archive_options"),
    ]
    discovered: list[dict[str, Any]] = []
    for capability_id, flag_key, source_key in mapping:
        discovered.append(
            {
                "capability_id": capability_id,
                "discoverable": bool(capabilities.get(flag_key, False)),
                "source_input": source_key,
            }
        )
    return discovered


def _build_capability_discovery(
    *,
    capabilities: dict[str, Any],
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
    room_vocabulary_resolution: dict[str, Any] | None,
    device_entity_vocabulary_resolution: dict[str, Any] | None,
    asset_vocabulary_resolution: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return #317-governed capability discovery assembly metadata."""
    discovered = _discoverable_capability_entries(capabilities)
    discoverable_ids = [
        item["capability_id"]
        for item in discovered
        if bool(item.get("discoverable", False))
    ]
    return {
        "discovery_version": 1,
        "applicable": True,
        "deterministic_discovery": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "capability_authority_external": True,
        "discovery_path": "capability_consumption_to_discovery",
        "route_scope": route_scope,
        "context_area_id": context_area_id,
        "resolved_composite_id": resolved_composite_id,
        "upstream_handoff_consumption": {
            "room_vocabulary_consumed": room_vocabulary_resolution is not None,
            "device_entity_vocabulary_consumed": device_entity_vocabulary_resolution is not None,
            "asset_intelligence_cp00_handoff_consumed": asset_vocabulary_resolution is not None,
        },
        "authority_traceability": {
            "authority_order": [
                "adr",
                "contract",
                "model",
                "existing_implementation",
                "github_issue",
            ],
            "capability_authority_origin": "htbw_governed_contracts_and_models",
            "vocabulary_authority_origin": "vocabulary_registry_external",
            "asset_intelligence_authority_origin": "asset_intelligence",
        },
        "discovered_capabilities": discovered,
        "discoverable_capability_ids": discoverable_ids,
        "discoverable_count": len(discoverable_ids),
        "deferred_release_2_owners": {
            "capability_diagnostics_explainability": "#318",
            "experience_implementation": "#319+",
        },
    }


def _build_experience_governance_boundary(
    *,
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
) -> dict[str, Any]:
    """Return #319-governed experience boundary declarations without experience execution behavior."""
    return {
        "governance_version": 1,
        "applicable": True,
        "governance_path": "capability_consumption_to_experience_governance",
        "concierge_role": "bounded_consumer_orchestrator",
        "experience_role": "governance_boundary_enforcer",
        "experience_authority_external": True,
        "experience_consumes_capability_outputs": True,
        "experience_redefines_capability_outputs": False,
        "authority_preservation": {
            "capability_authority_external": True,
            "vocabulary_authority_external": True,
            "asset_intelligence_authority_external": True,
        },
        "ownership_boundaries": {
            "governance_owner": "homes_that_behave_well",
            "experience_runtime_owner": "concierge",
            "capability_authority_owner": "homes_that_behave_well",
            "vocabulary_authority_owner": "vocabulary_registry_external",
            "asset_intelligence_authority_owner": "asset_intelligence",
        },
        "consumption_boundary_rules": {
            "consume_capability_outputs_only": True,
            "consume_authoritative_inputs_directly": False,
            "derive_new_capability_authority": False,
            "derive_new_vocabulary_authority": False,
            "derive_new_asset_authority": False,
        },
        "orchestration_constraints": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "experience_projection_enabled": False,
            "experience_execution_enabled": False,
            "experience_restoration_enabled": False,
            "experience_diagnostics_enabled": False,
            "governance_boundary_only": True,
        },
        "deferred_release_2_owners": {
            "capability_to_experience_handoff": "#320",
            "experience_projection": "#321",
            "experience_restoration_boundary": "#322",
            "experience_diagnostics_explainability": "#323",
            "release_2_validation": "#324",
        },
    }


def _build_continuity_governance_boundary(
    *,
    execution_kind: str,
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
) -> dict[str, Any]:
    """Return #325-governed continuity boundary metadata without downstream continuity behavior."""
    if execution_kind == "direct":
        return {
            "continuity_boundary_version": 1,
            "applicable": False,
            "continuity_path": "not_applicable_direct_execution",
            "deterministic_boundary": True,
            "concierge_role": "bounded_consumer_orchestrator",
            "continuity_authority_external": True,
            "continuity_consumption_mode": "bounded_context_consumption",
            "continuity_owns_identity": False,
            "continuity_owns_occupancy": False,
            "continuity_owns_memory": False,
            "privacy_boundary_preserved": True,
            "deferred_release_3_owners": {
                "person_room_affinity_boundary": "#326",
                "privacy_household_memory_boundary": "#327",
                "continuity_affinity_diagnostics_explainability": "#328",
                "restoration_governance_boundary": "#329",
                "release_3_validation": "#338",
            },
        }

    return {
        "continuity_boundary_version": 1,
        "applicable": True,
        "continuity_path": "governed_continuity_boundary",
        "deterministic_boundary": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "continuity_authority_external": True,
        "continuity_consumption_mode": "bounded_context_consumption",
        "continuity_owns_identity": False,
        "continuity_owns_occupancy": False,
        "continuity_owns_memory": False,
        "privacy_boundary_preserved": True,
        "ownership_boundaries": {
            "governance_owner": "homes_that_behave_well",
            "identity_owner": "voice_identity",
            "occupancy_owner": "foundation",
            "memory_owner": "household_memory_governance",
            "continuity_runtime_owner": "concierge",
        },
        "consumption_boundary_rules": {
            "consume_identity_confidence_as_input_only": True,
            "consume_occupancy_context_as_input_only": True,
            "consume_memory_context_as_input_only": True,
            "derive_identity_authority": False,
            "derive_occupancy_authority": False,
            "derive_memory_authority": False,
        },
        "orchestration_constraints": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "continuity_boundary_only": True,
            "affinity_behavior_enabled": True,
            "diagnostics_behavior_enabled": True,
            "restoration_behavior_enabled": False,
            "occupancy_behavior_enabled": False,
        },
        "deferred_release_3_owners": {
            "person_room_affinity_boundary": "#326",
            "privacy_household_memory_boundary": "#327",
            "continuity_affinity_diagnostics_explainability": "#328",
            "restoration_governance_boundary": "#329",
            "release_3_validation": "#338",
        },
    }


def _build_person_room_affinity_boundary(
    *,
    execution_kind: str,
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
) -> dict[str, Any]:
    """Return #326-governed person-room affinity boundary metadata without downstream affinity behavior."""
    if execution_kind == "direct":
        return {
            "affinity_boundary_version": 1,
            "applicable": False,
            "affinity_path": "not_applicable_direct_execution",
            "deterministic_boundary": True,
            "concierge_role": "bounded_consumer_orchestrator",
            "affinity_authority_external": True,
            "affinity_consumption_mode": "bounded_context_consumption",
            "affinity_owns_identity": False,
            "affinity_owns_room_truth": False,
            "affinity_owns_occupancy": False,
            "affinity_owns_memory": False,
            "guest_safe_boundary_preserved": True,
            "privacy_boundary_preserved": True,
            "deferred_release_3_owners": {
                "privacy_household_memory_boundary": "#327",
                "continuity_affinity_diagnostics_explainability": "#328",
                "restoration_governance_boundary": "#329",
                "release_3_validation": "#338",
            },
        }

    return {
        "affinity_boundary_version": 1,
        "applicable": True,
        "affinity_path": "governed_person_room_affinity_boundary",
        "deterministic_boundary": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "affinity_authority_external": True,
        "affinity_consumption_mode": "bounded_context_consumption",
        "affinity_owns_identity": False,
        "affinity_owns_room_truth": False,
        "affinity_owns_occupancy": False,
        "affinity_owns_memory": False,
        "guest_safe_boundary_preserved": True,
        "privacy_boundary_preserved": True,
        "ownership_boundaries": {
            "governance_owner": "homes_that_behave_well",
            "identity_owner": "voice_identity",
            "room_truth_owner": "foundation",
            "occupancy_owner": "foundation",
            "memory_owner": "household_memory_governance",
            "affinity_runtime_owner": "concierge",
        },
        "consumption_boundary_rules": {
            "consume_identity_confidence_as_input_only": True,
            "consume_room_truth_as_input_only": True,
            "consume_occupancy_context_as_input_only": True,
            "consume_profile_context_as_input_only": True,
            "derive_identity_authority": False,
            "derive_room_truth_authority": False,
            "derive_occupancy_authority": False,
            "derive_memory_authority": False,
        },
        "orchestration_constraints": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "affinity_boundary_only": True,
            "affinity_learning_enabled": False,
            "diagnostics_behavior_enabled": True,
            "restoration_behavior_enabled": False,
            "privacy_memory_behavior_enabled": False,
        },
        "deferred_release_3_owners": {
            "privacy_household_memory_boundary": "#327",
            "continuity_affinity_diagnostics_explainability": "#328",
            "restoration_governance_boundary": "#329",
            "release_3_validation": "#338",
        },
    }


def _build_privacy_household_memory_boundary(
    *,
    execution_kind: str,
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
) -> dict[str, Any]:
    """Return #327-governed privacy/household-memory boundary metadata without downstream memory behavior."""
    if execution_kind == "direct":
        return {
            "privacy_household_memory_boundary_version": 1,
            "applicable": False,
            "boundary_path": "not_applicable_direct_execution",
            "deterministic_boundary": True,
            "concierge_role": "bounded_consumer_orchestrator",
            "privacy_authority_external": True,
            "household_memory_authority_external": True,
            "privacy_enforcement_mode": "governed_policy_consumption",
            "memory_consumption_mode": "bounded_context_consumption",
            "memory_owns_identity": False,
            "memory_owns_retention_policy": False,
            "memory_owns_storage": False,
            "memory_owns_provenance": False,
            "guest_safe_boundary_preserved": True,
            "deferred_release_3_owners": {
                "continuity_affinity_diagnostics_explainability": "#328",
                "restoration_governance_boundary": "#329",
                "release_3_validation": "#338",
            },
        }

    return {
        "privacy_household_memory_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_privacy_household_memory_boundary",
        "deterministic_boundary": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "privacy_authority_external": True,
        "household_memory_authority_external": True,
        "privacy_enforcement_mode": "governed_policy_consumption",
        "memory_consumption_mode": "bounded_context_consumption",
        "memory_owns_identity": False,
        "memory_owns_retention_policy": False,
        "memory_owns_storage": False,
        "memory_owns_provenance": False,
        "guest_safe_boundary_preserved": True,
        "ownership_boundaries": {
            "governance_owner": "homes_that_behave_well",
            "identity_owner": "voice_identity",
            "occupancy_owner": "foundation",
            "household_memory_owner": "household_memory_governance",
            "privacy_policy_owner": "homes_that_behave_well",
            "retention_policy_owner": "homes_that_behave_well",
            "concierge_runtime_owner": "concierge",
        },
        "consumption_boundary_rules": {
            "consume_memory_context_as_input_only": True,
            "consume_identity_context_as_input_only": True,
            "consume_occupancy_context_as_input_only": True,
            "derive_memory_authority": False,
            "derive_retention_authority": False,
            "derive_identity_authority": False,
            "derive_occupancy_authority": False,
        },
        "orchestration_constraints": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "privacy_household_memory_boundary_only": True,
            "household_memory_diagnostics_enabled": False,
            "restoration_behavior_enabled": False,
            "occupancy_behavior_enabled": False,
        },
        "deferred_release_3_owners": {
            "continuity_affinity_diagnostics_explainability": "#328",
            "restoration_governance_boundary": "#329",
            "release_3_validation": "#338",
        },
    }


def _build_messaging_governance_boundary(
    *,
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
    recipient_scope: str,
    message_context_type: str,
) -> dict[str, Any]:
    """Return #339-governed messaging boundary metadata without downstream messaging authority."""
    return {
        "messaging_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_messaging_boundary",
        "deterministic_boundary": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "messaging_authority_external": True,
        "message_authority_external": True,
        "provenance_authority_external": True,
        "household_memory_authority_external": True,
        "message_creation_governed": True,
        "message_lifecycle_governed": True,
        "message_creation_rules": {
            "consume_authoritative_inputs_only": True,
            "determine_truth": False,
            "establish_truth": False,
            "override_truth": False,
            "become_source_of_record": False,
        },
        "authority_protection": {
            "messaging_owns_truth": False,
            "messaging_owns_provenance": False,
            "messaging_owns_memory": False,
            "messaging_owns_identity": False,
        },
        "consumption_boundary_rules": {
            "consume_provenance_as_input_only": True,
            "consume_memory_as_input_only": True,
            "consume_identity_outputs_as_input_only": True,
            "consume_occupancy_presence_outputs_as_input_only": True,
            "derive_message_authority": False,
            "derive_truth_authority": False,
        },
        "lifecycle_governance": {
            "creation_governed": True,
            "delivery_governed": True,
            "acknowledgement_governed": True,
            "retention_governed": True,
        },
        "governance_controls": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "recipient_scope": recipient_scope,
            "message_context_type": message_context_type,
            "message_boundary_only": True,
            "truth_determination_enabled": False,
            "source_of_record_enabled": False,
        },
        "ownership_boundaries": {
            "governance_owner": "homes_that_behave_well",
            "messaging_runtime_owner": "concierge",
            "message_authority_owner": "messaging_systems",
            "provenance_owner": "provenance_governance",
            "household_memory_owner": "household_memory_governance",
            "identity_owner": "voice_identity",
        },
        "deferred_release_4_owners": {
            "messaging_provenance": "#340",
            "notification_and_delivery_boundary": "#341",
            "recipient_consent_privacy_visibility_boundary": "#342",
            "messaging_diagnostics_explainability": "#343",
            "household_memory_boundary": "#344",
            "release_4_validation": "#349",
        },
    }


def _build_occupancy_governance_boundary(
    *,
    execution_kind: str,
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
) -> dict[str, Any]:
    """Return #333-governed occupancy boundary metadata without occupancy behavior."""
    if execution_kind == "direct":
        return {
            "occupancy_boundary_version": 1,
            "applicable": False,
            "occupancy_path": "not_applicable_direct_execution",
            "deterministic_boundary": True,
            "concierge_role": "bounded_consumer_orchestrator",
            "occupancy_authority_external": True,
            "occupancy_policy_authority_external": True,
            "occupancy_truth_authority_external": True,
            "occupancy_consumption_mode": "bounded_context_consumption",
            "occupancy_owns_room_truth": False,
            "occupancy_owns_identity": False,
            "occupancy_owns_household_memory": False,
            "occupancy_owns_restoration": False,
            "guest_safe_boundary_preserved": True,
            "privacy_boundary_preserved": True,
            "orchestration_constraints": {
                "route_scope": "direct",
                "context_area_id": None,
                "resolved_composite_id": None,
                "occupancy_boundary_only": True,
                "occupancy_decision_behavior_enabled": False,
                "occupancy_execution_enabled": False,
                "occupancy_inference_enabled": False,
                "occupancy_diagnostics_behavior_enabled": False,
            },
            "explainability_visibility": {
                "occupancy_visibility_enabled": True,
                "authority_visibility_enabled": True,
                "traceability_visibility_enabled": True,
            },
            "deferred_release_3_owners": {
                "presence_governance_boundary": "#334",
                "guest_unknown_occupant_behavior": "#335",
                "multi_occupant_behavior": "#336",
                "occupancy_presence_diagnostics_explainability": "#337",
                "release_3_validation": "#338",
            },
        }

    return {
        "occupancy_boundary_version": 1,
        "applicable": True,
        "occupancy_path": "governed_occupancy_boundary",
        "deterministic_boundary": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "occupancy_authority_external": True,
        "occupancy_policy_authority_external": True,
        "occupancy_truth_authority_external": True,
        "occupancy_consumption_mode": "bounded_context_consumption",
        "occupancy_owns_room_truth": False,
        "occupancy_owns_identity": False,
        "occupancy_owns_household_memory": False,
        "occupancy_owns_restoration": False,
        "guest_safe_boundary_preserved": True,
        "privacy_boundary_preserved": True,
        "ownership_boundaries": {
            "governance_owner": "homes_that_behave_well",
            "occupancy_truth_owner": "foundation",
            "presence_truth_owner": "foundation",
            "room_truth_owner": "foundation",
            "identity_owner": "voice_identity",
            "household_memory_owner": "household_memory_governance",
            "restoration_owner": "experience_restoration_governance",
            "occupancy_runtime_owner": "concierge",
        },
        "consumption_boundary_rules": {
            "consume_room_truth_as_input_only": True,
            "consume_identity_confidence_as_input_only": True,
            "consume_presence_context_as_input_only": True,
            "consume_memory_context_as_input_only": True,
            "consume_restoration_context_as_input_only": True,
            "derive_occupancy_authority": False,
            "derive_occupancy_policy_authority": False,
            "derive_room_truth_authority": False,
            "derive_identity_authority": False,
            "derive_household_memory_authority": False,
            "derive_restoration_authority": False,
        },
        "orchestration_constraints": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "occupancy_boundary_only": True,
            "occupancy_decision_behavior_enabled": False,
            "occupancy_execution_enabled": False,
            "occupancy_inference_enabled": False,
            "occupancy_diagnostics_behavior_enabled": False,
        },
        "explainability_visibility": {
            "occupancy_visibility_enabled": True,
            "authority_visibility_enabled": True,
            "traceability_visibility_enabled": True,
        },
        "deferred_release_3_owners": {
            "presence_governance_boundary": "#334",
            "guest_unknown_occupant_behavior": "#335",
            "multi_occupant_behavior": "#336",
            "occupancy_presence_diagnostics_explainability": "#337",
            "release_3_validation": "#338",
        },
    }


def _build_presence_governance_boundary(
    *,
    execution_kind: str,
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
) -> dict[str, Any]:
    """Return #334-governed presence boundary metadata without presence behavior."""
    if execution_kind == "direct":
        return {
            "presence_boundary_version": 1,
            "applicable": False,
            "presence_path": "not_applicable_direct_execution",
            "deterministic_boundary": True,
            "concierge_role": "bounded_consumer_orchestrator",
            "presence_authority_external": True,
            "presence_policy_authority_external": True,
            "presence_truth_authority_external": True,
            "presence_consumption_mode": "bounded_context_consumption",
            "presence_owns_occupancy": False,
            "presence_owns_room_truth": False,
            "presence_owns_identity": False,
            "presence_owns_household_memory": False,
            "presence_owns_restoration": False,
            "guest_safe_boundary_preserved": True,
            "privacy_boundary_preserved": True,
            "consumes_occupancy_governance_visibility": True,
            "orchestration_constraints": {
                "route_scope": "direct",
                "context_area_id": None,
                "resolved_composite_id": None,
                "presence_boundary_only": True,
                "presence_detection_enabled": False,
                "presence_inference_enabled": False,
                "presence_attribution_enabled": False,
                "presence_behavior_enabled": False,
                "presence_diagnostics_behavior_enabled": False,
            },
            "explainability_visibility": {
                "presence_visibility_enabled": True,
                "authority_visibility_enabled": True,
                "traceability_visibility_enabled": True,
            },
            "deferred_release_3_owners": {
                "guest_unknown_occupant_behavior": "#335",
                "multi_occupant_behavior": "#336",
                "occupancy_presence_diagnostics_explainability": "#337",
                "release_3_validation": "#338",
            },
        }

    return {
        "presence_boundary_version": 1,
        "applicable": True,
        "presence_path": "governed_presence_boundary",
        "deterministic_boundary": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "presence_authority_external": True,
        "presence_policy_authority_external": True,
        "presence_truth_authority_external": True,
        "presence_consumption_mode": "bounded_context_consumption",
        "presence_owns_occupancy": False,
        "presence_owns_room_truth": False,
        "presence_owns_identity": False,
        "presence_owns_household_memory": False,
        "presence_owns_restoration": False,
        "guest_safe_boundary_preserved": True,
        "privacy_boundary_preserved": True,
        "consumes_occupancy_governance_visibility": True,
        "ownership_boundaries": {
            "governance_owner": "homes_that_behave_well",
            "presence_truth_owner": "foundation",
            "occupancy_truth_owner": "foundation",
            "room_truth_owner": "foundation",
            "identity_owner": "voice_identity",
            "household_memory_owner": "household_memory_governance",
            "restoration_owner": "experience_restoration_governance",
            "presence_runtime_owner": "concierge",
        },
        "consumption_boundary_rules": {
            "consume_presence_context_as_input_only": True,
            "consume_occupancy_context_as_input_only": True,
            "consume_room_truth_as_input_only": True,
            "consume_identity_confidence_as_input_only": True,
            "consume_memory_context_as_input_only": True,
            "consume_restoration_context_as_input_only": True,
            "derive_presence_authority": False,
            "derive_presence_policy_authority": False,
            "derive_presence_truth_authority": False,
            "derive_occupancy_authority": False,
            "derive_room_truth_authority": False,
            "derive_identity_authority": False,
            "derive_household_memory_authority": False,
            "derive_restoration_authority": False,
        },
        "orchestration_constraints": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "presence_boundary_only": True,
            "presence_detection_enabled": False,
            "presence_inference_enabled": False,
            "presence_attribution_enabled": False,
            "presence_behavior_enabled": False,
            "presence_diagnostics_behavior_enabled": False,
        },
        "explainability_visibility": {
            "presence_visibility_enabled": True,
            "authority_visibility_enabled": True,
            "traceability_visibility_enabled": True,
        },
        "deferred_release_3_owners": {
            "guest_unknown_occupant_behavior": "#335",
            "multi_occupant_behavior": "#336",
            "occupancy_presence_diagnostics_explainability": "#337",
            "release_3_validation": "#338",
        },
    }


def _build_guest_unknown_occupant_behavior(
    *,
    execution_kind: str,
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
    person_id: str | None,
    context: dict[str, Any] | None,
    occupancy_governance_boundary: dict[str, Any],
    presence_governance_boundary: dict[str, Any],
) -> dict[str, Any]:
    """Return #335-governed guest-safe and unknown-occupant behavior metadata."""
    context_payload = context if isinstance(context, dict) else {}
    actor_class = str(context_payload.get("actor_class", "") or "").strip().lower()
    occupant_state_hint = str(
        context_payload.get("occupant_state", context_payload.get("occupancy_state", "")) or ""
    ).strip().lower()
    raw_occupant_states = context_payload.get("occupant_states", [])
    if isinstance(raw_occupant_states, list):
        occupant_states = {str(item).strip().lower() for item in raw_occupant_states if str(item).strip()}
    else:
        occupant_states = set()
    guest_safe_hint = bool(context_payload.get("guest_safe", False) or context_payload.get("guest_mode", False))

    if (
        actor_class == "guest"
        or occupant_state_hint in {"guest", "guest_occupant", "guest-occupant"}
        or bool(occupant_states & {"guest", "guest_occupant", "guest-occupant"})
        or guest_safe_hint
    ):
        occupant_state = "guest_occupant"
    elif occupant_state_hint in {"known", "known_occupant", "resident", "household_member"} or bool(
        occupant_states & {"known", "known_occupant", "resident", "household_member"}
    ):
        occupant_state = "known_occupant"
    elif occupant_state_hint in {"unknown", "unknown_occupant", "unattributed", "unattributed_occupant"} or bool(
        occupant_states & {"unknown", "unknown_occupant", "unattributed", "unattributed_occupant"}
    ):
        occupant_state = "unknown_occupant"
    elif person_id:
        occupant_state = "known_occupant"
    else:
        occupant_state = "unknown_occupant"

    guest_safe_mode_active = occupant_state == "guest_occupant"
    unknown_occupant_mode_active = occupant_state == "unknown_occupant"
    conservative_behavior_required = guest_safe_mode_active or unknown_occupant_mode_active
    behavior_applicable = execution_kind != "direct"
    restoration_eligibility_allowed = bool(behavior_applicable and not conservative_behavior_required)

    return {
        "guest_unknown_behavior_version": 1,
        "applicable": behavior_applicable,
        "behavior_path": (
            "governed_guest_unknown_occupant_behavior"
            if behavior_applicable
            else "not_applicable_direct_execution"
        ),
        "deterministic_behavior": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "consumes_occupancy_governance_boundary": True,
        "consumes_presence_governance_boundary": True,
        "occupancy_authority_external": bool(
            occupancy_governance_boundary.get("occupancy_authority_external", False)
        ),
        "presence_authority_external": bool(
            presence_governance_boundary.get("presence_authority_external", False)
        ),
        "identity_authority_external": True,
        "household_memory_authority_external": True,
        "occupancy_truth_authority_external": bool(
            occupancy_governance_boundary.get("occupancy_truth_authority_external", False)
        ),
        "presence_truth_authority_external": bool(
            presence_governance_boundary.get("presence_truth_authority_external", False)
        ),
        "occupant_state": occupant_state,
        "guest_safe_mode_active": guest_safe_mode_active,
        "unknown_occupant_mode_active": unknown_occupant_mode_active,
        "conservative_behavior_required": conservative_behavior_required,
        "private_personalization_blocked": conservative_behavior_required,
        "private_memory_inheritance_blocked": conservative_behavior_required,
        "protected_experience_inheritance_blocked": conservative_behavior_required,
        "identity_attribution_enabled": False,
        "occupancy_truth_modification_enabled": False,
        "presence_truth_modification_enabled": False,
        "restoration_eligibility_allowed": restoration_eligibility_allowed,
        "messaging_eligibility_influence": (
            "restricted_influence"
            if conservative_behavior_required
            else "standard_governed_influence"
        ),
        "notification_eligibility_influence": (
            "restricted_influence"
            if conservative_behavior_required
            else "standard_governed_influence"
        ),
        "privacy_boundary_preserved": True,
        "guest_safe_boundary_preserved": True,
        "explainability_visibility": {
            "occupant_state_visibility_enabled": True,
            "authority_visibility_enabled": True,
            "restriction_visibility_enabled": True,
            "traceability_visibility_enabled": True,
        },
        "governance_controls": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "behavior_enabled": behavior_applicable,
            "conservative_behavior_required": conservative_behavior_required,
            "restoration_eligibility_allowed": restoration_eligibility_allowed,
            "identity_attribution_enabled": False,
            "occupancy_truth_modification_enabled": False,
            "presence_truth_modification_enabled": False,
        },
        "deferred_release_3_owners": {
            "multi_occupant_behavior": "#336",
            "occupancy_presence_diagnostics_explainability": "#337",
            "release_3_validation": "#338",
        },
    }


def _build_multi_occupant_behavior(
    *,
    execution_kind: str,
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
    person_id: str | None,
    context: dict[str, Any] | None,
    occupancy_governance_boundary: dict[str, Any],
    presence_governance_boundary: dict[str, Any],
    guest_unknown_occupant_behavior: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return #336-governed multi-occupant behavior metadata."""
    context_payload = context if isinstance(context, dict) else {}

    raw_states = context_payload.get("occupant_states", [])
    if isinstance(raw_states, list):
        occupant_states = [str(item).strip().lower() for item in raw_states if str(item).strip()]
    else:
        occupant_states = []

    raw_people = context_payload.get("person_ids", [])
    if isinstance(raw_people, list):
        person_ids = [str(item).strip() for item in raw_people if str(item).strip()]
    else:
        person_ids = []

    occupant_count_value = context_payload.get("occupant_count")
    try:
        occupant_count = int(occupant_count_value) if occupant_count_value is not None else 0
    except (TypeError, ValueError):
        occupant_count = 0

    multi_hint = bool(
        context_payload.get("multi_occupant", False)
        or context_payload.get("multiple_occupants", False)
        or context_payload.get("conflicting_occupants", False)
        or context_payload.get("mixed_attribution_states", False)
        or occupant_count > 1
        or len(occupant_states) > 1
        or len(person_ids) > 1
    )

    known_like = {"known", "known_occupant", "resident", "household_member"}
    guest_like = {"guest", "guest_occupant", "guest-occupant"}
    unknown_like = {"unknown", "unknown_occupant", "unattributed", "unattributed_occupant"}
    state_set = set(occupant_states)

    if multi_hint:
        if state_set & guest_like and state_set & known_like:
            occupant_state = "known_guest_mix"
        elif state_set & unknown_like and state_set & known_like:
            occupant_state = "mixed_attribution_states"
        elif state_set & guest_like and state_set & unknown_like:
            occupant_state = "guest_unknown_mix"
        elif len(state_set) > 1:
            occupant_state = "multiple_known_occupants" if state_set <= known_like else "multiple_occupants"
        elif occupant_count > 1 or len(person_ids) > 1:
            occupant_state = "multiple_occupants"
        elif context_payload.get("conflicting_occupants", False):
            occupant_state = "conflicting_occupants"
        else:
            occupant_state = "multiple_occupants"
    else:
        occupant_state = "single_occupant"

    guest_unknown = dict(guest_unknown_occupant_behavior or {})
    guest_restriction_active = bool(guest_unknown.get("conservative_behavior_required", False))
    multi_occupant_mode_active = multi_hint
    conflict_aware_behavior_required = bool(
        multi_occupant_mode_active
        and (
            occupant_state != "multiple_known_occupants"
            or guest_restriction_active
            or occupant_state in {"known_guest_mix", "mixed_attribution_states", "guest_unknown_mix", "conflicting_occupants"}
        )
    )
    behavior_applicable = execution_kind != "direct"
    restoration_eligibility_allowed = bool(
        behavior_applicable and multi_occupant_mode_active and not guest_restriction_active
    )
    behavior_enabled = behavior_applicable and multi_occupant_mode_active
    influence_mode = (
        "conflict_aware_influence" if multi_occupant_mode_active else "neutral_influence"
    )

    return {
        "multi_occupant_behavior_version": 1,
        "applicable": behavior_applicable,
        "behavior_path": (
            "governed_multi_occupant_behavior"
            if behavior_applicable
            else "not_applicable_direct_execution"
        ),
        "deterministic_behavior": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "consumes_occupancy_governance_boundary": True,
        "consumes_presence_governance_boundary": True,
        "consumes_guest_unknown_behavior": bool(guest_unknown),
        "occupancy_authority_external": bool(
            occupancy_governance_boundary.get("occupancy_authority_external", False)
        ),
        "presence_authority_external": bool(
            presence_governance_boundary.get("presence_authority_external", False)
        ),
        "identity_authority_external": True,
        "household_memory_authority_external": True,
        "occupancy_truth_authority_external": bool(
            occupancy_governance_boundary.get("occupancy_truth_authority_external", False)
        ),
        "presence_truth_authority_external": bool(
            presence_governance_boundary.get("presence_truth_authority_external", False)
        ),
        "occupant_state": occupant_state,
        "multi_occupant_mode_active": multi_occupant_mode_active,
        "conflict_aware_behavior_required": conflict_aware_behavior_required,
        "guest_safe_boundary_preserved": True,
        "privacy_boundary_preserved": True,
        "guest_safe_mode_preserved": not multi_occupant_mode_active or guest_restriction_active,
        "unknown_occupant_mode_preserved": not multi_occupant_mode_active or bool(
            guest_unknown.get("unknown_occupant_mode_active", False)
        ),
        "multiple_occupants_visible": multi_occupant_mode_active,
        "conflict_visibility_enabled": multi_occupant_mode_active,
        "restoration_eligibility_allowed": restoration_eligibility_allowed,
        "messaging_eligibility_influence": influence_mode,
        "notification_eligibility_influence": influence_mode,
        "personalization_eligibility_influence": influence_mode,
        "identity_attribution_enabled": False,
        "occupancy_truth_modification_enabled": False,
        "presence_truth_modification_enabled": False,
        "explainability_visibility": {
            "occupant_state_visibility_enabled": True,
            "authority_visibility_enabled": True,
            "conflict_visibility_enabled": True,
            "traceability_visibility_enabled": True,
        },
        "governance_controls": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "behavior_enabled": behavior_enabled,
            "multi_occupant_mode_active": multi_occupant_mode_active,
            "conflict_aware_behavior_required": conflict_aware_behavior_required,
            "restoration_eligibility_allowed": restoration_eligibility_allowed,
            "identity_attribution_enabled": False,
            "occupancy_truth_modification_enabled": False,
            "presence_truth_modification_enabled": False,
        },
        "multi_occupant_visibility": {
            "occupant_count": occupant_count if occupant_count > 0 else len(person_ids),
            "occupant_states": occupant_states,
            "person_ids_present": len(person_ids),
        },
        "deferred_release_3_owners": {
            "occupancy_presence_diagnostics_explainability": "#337",
            "release_3_validation": "#338",
        },
    }


def _build_capability_to_experience_handoff(
    *,
    capability_discovery: dict[str, Any],
    experience_governance_boundary: dict[str, Any],
    execution_kind: str,
) -> dict[str, Any]:
    """Return #320-governed capability-to-experience handoff metadata."""
    authority_traceability = dict(capability_discovery.get("authority_traceability", {}))
    discovered_capabilities = list(capability_discovery.get("discovered_capabilities", []))
    discoverable_outputs = [
        {
            "capability_id": item.get("capability_id"),
            "source_input": item.get("source_input"),
        }
        for item in discovered_capabilities
        if bool(item.get("discoverable", False))
    ]
    orchestration_constraints = dict(experience_governance_boundary.get("orchestration_constraints", {}))

    if execution_kind == "direct":
        return {
            "handoff_version": 1,
            "applicable": False,
            "handoff_path": "not_applicable_direct_execution",
            "deterministic_handoff": True,
            "concierge_role": "bounded_consumer_orchestrator",
            "handoff_transfers_authority": False,
            "experience_consumption_ready": False,
            "deferred_release_2_owners": {
                "experience_projection": "#321",
                "experience_restoration_boundary": "#322",
                "experience_diagnostics_explainability": "#323",
                "release_2_validation": "#324",
            },
        }

    return {
        "handoff_version": 1,
        "applicable": True,
        "handoff_path": "capability_to_experience_consumption",
        "deterministic_handoff": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "handoff_transfers_authority": False,
        "experience_consumption_ready": True,
        "authority_attribution": {
            "capability_authority_origin": authority_traceability.get("capability_authority_origin"),
            "vocabulary_authority_origin": authority_traceability.get("vocabulary_authority_origin"),
            "asset_intelligence_authority_origin": authority_traceability.get("asset_intelligence_authority_origin"),
            "experience_governance_owner": (
                dict(experience_governance_boundary.get("ownership_boundaries", {})).get("governance_owner")
            ),
        },
        "capability_source_traceability": {
            "discoverable_capability_ids": list(capability_discovery.get("discoverable_capability_ids", [])),
            "discoverable_count": int(capability_discovery.get("discoverable_count", 0) or 0),
            "discovery_path": capability_discovery.get("discovery_path"),
            "route_scope": orchestration_constraints.get("route_scope"),
            "context_area_id": orchestration_constraints.get("context_area_id"),
            "resolved_composite_id": orchestration_constraints.get("resolved_composite_id"),
        },
        "experience_consumable_capability_outputs": discoverable_outputs,
        "ownership_preservation": {
            "capability_authority_external": True,
            "experience_authority_external": True,
            "vocabulary_authority_external": True,
            "asset_intelligence_authority_external": True,
            "experience_redefines_capability_outputs": False,
        },
        "deferred_release_2_owners": {
            "experience_projection": "#321",
            "experience_restoration_boundary": "#322",
            "experience_diagnostics_explainability": "#323",
            "release_2_validation": "#324",
        },
    }


def _build_experience_projection(
    *,
    capability_to_experience_handoff: dict[str, Any],
    experience_governance_boundary: dict[str, Any],
    execution_kind: str,
) -> dict[str, Any]:
    """Return #321-governed deterministic experience projection metadata."""
    if execution_kind == "direct":
        return {
            "projection_version": 1,
            "applicable": False,
            "projection_path": "not_applicable_direct_execution",
            "deterministic_projection": True,
            "concierge_role": "bounded_consumer_orchestrator",
            "projection_is_authority": False,
            "deferred_release_2_owners": {
                "experience_restoration_boundary": "#322",
                "experience_diagnostics_explainability": "#323",
                "release_2_validation": "#324",
            },
        }

    capability_outputs = list(
        capability_to_experience_handoff.get("experience_consumable_capability_outputs", [])
    )
    projected_experiences = [
        {
            "experience_id": f"exp_{item.get('capability_id')}",
            "source_capability_id": item.get("capability_id"),
            "source_input": item.get("source_input"),
            "projection_mode": "capability_consumption_projection",
        }
        for item in capability_outputs
    ]
    ownership_boundaries = dict(experience_governance_boundary.get("ownership_boundaries", {}))
    authority_attribution = dict(capability_to_experience_handoff.get("authority_attribution", {}))
    source_traceability = dict(capability_to_experience_handoff.get("capability_source_traceability", {}))
    return {
        "projection_version": 1,
        "applicable": bool(capability_to_experience_handoff.get("applicable", False)),
        "projection_path": "experience_projection_from_capability_handoff",
        "deterministic_projection": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "experience_role": "governed_projector",
        "projection_is_authority": False,
        "projection_source": {
            "handoff_path": capability_to_experience_handoff.get("handoff_path"),
            "discoverable_capability_ids": list(source_traceability.get("discoverable_capability_ids", [])),
            "route_scope": source_traceability.get("route_scope"),
            "context_area_id": source_traceability.get("context_area_id"),
            "resolved_composite_id": source_traceability.get("resolved_composite_id"),
        },
        "authority_attribution": {
            "capability_authority_origin": authority_attribution.get("capability_authority_origin"),
            "vocabulary_authority_origin": authority_attribution.get("vocabulary_authority_origin"),
            "asset_intelligence_authority_origin": authority_attribution.get("asset_intelligence_authority_origin"),
            "experience_governance_owner": ownership_boundaries.get("governance_owner"),
        },
        "projected_experiences": projected_experiences,
        "projected_experience_count": len(projected_experiences),
        "ownership_preservation": {
            "capability_authority_external": True,
            "experience_authority_external": True,
            "vocabulary_authority_external": True,
            "asset_intelligence_authority_external": True,
            "projection_redefines_inputs": False,
        },
        "deferred_release_2_owners": {
            "experience_restoration_boundary": "#322",
            "experience_diagnostics_explainability": "#323",
            "release_2_validation": "#324",
        },
    }


def _build_experience_restoration_boundary(
    *,
    experience_projection: dict[str, Any],
    guest_unknown_occupant_behavior: dict[str, Any] | None,
    multi_occupant_behavior: dict[str, Any] | None,
    execution_kind: str,
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
) -> dict[str, Any]:
    """Return #322/#329/#330-governed restoration boundary metadata."""
    if execution_kind == "direct":
        return {
            "restoration_boundary_version": 1,
            "restoration_governance_version": 1,
            "applicable": False,
            "restoration_path": "not_applicable_direct_execution",
            "restoration_governance_path": "not_applicable_direct_execution",
            "deterministic_boundary": True,
            "concierge_role": "bounded_consumer_orchestrator",
            "restoration_authority_external": True,
            "restoration_policy_authority_external": True,
            "restoration_consumption_mode": "governed_boundary_consumption",
            "restoration_authority_transferred": False,
            "restoration_eligible": False,
            "guest_unknown_behavior_consumed": bool(guest_unknown_occupant_behavior),
            "multi_occupant_behavior_consumed": bool(multi_occupant_behavior),
            "restoration_owns_identity": False,
            "restoration_owns_occupancy": False,
            "restoration_owns_continuity": False,
            "restoration_owns_affinity": False,
            "restoration_owns_household_memory": False,
            "privacy_boundary_preserved": True,
            "guest_safe_boundary_preserved": True,
            "governance_controls": {
                "route_scope": "direct",
                "context_area_id": None,
                "resolved_composite_id": None,
                "restoration_boundary_only": True,
                "restoration_execution_enabled": False,
                "restoration_decision_behavior_enabled": False,
                "restoration_diagnostics_behavior_enabled": True,
                "restoration_validation_behavior_enabled": False,
            },
            "deferred_release_2_owners": {
                "experience_diagnostics_explainability": "#323",
                "release_2_validation": "#324",
            },
            "deferred_release_3_owners": {
                "restoration_outcome_implementation": "#330",
                "e3a_preservation_alignment": "#331",
                "restoration_diagnostics_explainability": "#332",
                "release_3_validation": "#338",
            },
        }

    projection_source = dict(experience_projection.get("projection_source", {}))
    authority_attribution = dict(experience_projection.get("authority_attribution", {}))
    projected_count = int(experience_projection.get("projected_experience_count", 0) or 0)
    guest_behavior = dict(guest_unknown_occupant_behavior or {})
    multi_behavior = dict(multi_occupant_behavior or {})
    restoration_allowed_by_guest_behavior = bool(
        guest_behavior.get("restoration_eligibility_allowed", True)
    )
    restoration_allowed_by_multi_behavior = bool(
        multi_behavior.get("restoration_eligibility_allowed", True)
    )
    restoration_eligible = bool(
        projected_count > 0
        and restoration_allowed_by_guest_behavior
        and restoration_allowed_by_multi_behavior
    )
    restoration_decision_behavior_enabled = execution_kind in {"summary", "orchestration"}
    restoration_execution_enabled = execution_kind == "orchestration"
    return {
        "restoration_boundary_version": 1,
        "restoration_governance_version": 1,
        "applicable": bool(experience_projection.get("applicable", False)),
        "restoration_path": "experience_projection_to_restoration_boundary",
        "restoration_governance_path": "governed_restoration_boundary",
        "deterministic_boundary": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "restoration_authority_external": True,
        "restoration_policy_authority_external": True,
        "restoration_consumption_mode": "governed_boundary_consumption",
        "restoration_authority_transferred": False,
        "restoration_eligible": restoration_eligible,
        "guest_unknown_behavior_consumed": bool(guest_behavior),
        "multi_occupant_behavior_consumed": bool(multi_behavior),
        "restoration_owns_identity": False,
        "restoration_owns_occupancy": False,
        "restoration_owns_continuity": False,
        "restoration_owns_affinity": False,
        "restoration_owns_household_memory": False,
        "privacy_boundary_preserved": True,
        "guest_safe_boundary_preserved": True,
        "restoration_eligibility_visibility": {
            "projected_experience_count": projected_count,
            "projection_path": experience_projection.get("projection_path"),
            "eligible_when_projected_experiences_present": True,
            "restricted_by_guest_unknown_behavior": not restoration_allowed_by_guest_behavior,
            "guest_unknown_occupant_state": guest_behavior.get("occupant_state"),
            "restricted_by_multi_occupant_behavior": not restoration_allowed_by_multi_behavior,
            "multi_occupant_state": multi_behavior.get("occupant_state"),
        },
        "authority_attribution": {
            "capability_authority_origin": authority_attribution.get("capability_authority_origin"),
            "vocabulary_authority_origin": authority_attribution.get("vocabulary_authority_origin"),
            "asset_intelligence_authority_origin": authority_attribution.get("asset_intelligence_authority_origin"),
            "experience_governance_owner": authority_attribution.get("experience_governance_owner"),
        },
        "restoration_traceability": {
            "projection_source_path": projection_source.get("handoff_path"),
            "projection_route_scope": projection_source.get("route_scope"),
            "context_area_id": projection_source.get("context_area_id"),
            "resolved_composite_id": projection_source.get("resolved_composite_id"),
        },
        "governance_controls": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "restoration_boundary_only": True,
            "restoration_execution_enabled": restoration_execution_enabled,
            "restoration_decision_behavior_enabled": restoration_decision_behavior_enabled,
            "restoration_diagnostics_behavior_enabled": True,
            "restoration_validation_behavior_enabled": False,
            "guest_unknown_behavior_enabled": bool(
                guest_behavior.get("governance_controls", {}).get("behavior_enabled", False)
            ),
            "multi_occupant_behavior_enabled": bool(
                multi_behavior.get("governance_controls", {}).get("behavior_enabled", False)
            ),
        },
        "ownership_visibility": {
            "capability_authority_external": True,
            "experience_authority_external": True,
            "vocabulary_authority_external": True,
            "asset_intelligence_authority_external": True,
            "restoration_redefines_projection": False,
        },
        "guardrails": {
            "diagnostics_in_scope": True,
            "validation_in_scope": False,
            "authority_transfer_allowed": False,
        },
        "deferred_release_2_owners": {
            "experience_diagnostics_explainability": "#323",
            "release_2_validation": "#324",
        },
        "deferred_release_3_owners": {
            "restoration_outcome_implementation": "#330",
            "e3a_preservation_alignment": "#331",
            "restoration_diagnostics_explainability": "#332",
            "release_3_validation": "#338",
        },
    }


def _build_experience_restoration_outcome(
    *,
    experience_projection: dict[str, Any],
    experience_restoration_boundary: dict[str, Any],
    guest_unknown_occupant_behavior: dict[str, Any] | None,
    multi_occupant_behavior: dict[str, Any] | None,
    execution_kind: str,
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
) -> dict[str, Any]:
    """Return #330-governed outcome restoration consumption metadata."""
    if execution_kind == "direct":
        return {
            "outcome_version": 1,
            "applicable": False,
            "outcome_path": "not_applicable_direct_execution",
            "deterministic_outcome": True,
            "concierge_role": "bounded_consumer_orchestrator",
            "outcome_is_authority": False,
            "restoration_applied": False,
            "restoration_execution_handoff_ready": False,
            "restoration_outcome_reason": "direct_execution_not_eligible",
            "selected_outcome": None,
            "fallback_applied": True,
            "ownership_preservation": {
                "restoration_authority_external": True,
                "restoration_policy_authority_external": True,
                "restoration_decision_authority_transferred": False,
                "restoration_redefines_governance": False,
            },
            "governance_controls": {
                "route_scope": "direct",
                "context_area_id": None,
                "resolved_composite_id": None,
                "restoration_decision_behavior_enabled": False,
                "restoration_execution_enabled": False,
                "restoration_diagnostics_behavior_enabled": True,
                "guest_unknown_behavior_enabled": False,
                "multi_occupant_behavior_enabled": False,
            },
            "deferred_release_3_owners": {
                "e3a_preservation_alignment": "#331",
                "restoration_diagnostics_explainability": "#332",
                "release_3_validation": "#338",
            },
        }

    projected_experiences = list(experience_projection.get("projected_experiences", []))
    projected_count = int(experience_projection.get("projected_experience_count", 0) or 0)
    guest_behavior = dict(guest_unknown_occupant_behavior or {})
    multi_behavior = dict(multi_occupant_behavior or {})
    restoration_allowed_by_guest_behavior = bool(
        guest_behavior.get("restoration_eligibility_allowed", True)
    )
    restoration_allowed_by_multi_behavior = bool(
        multi_behavior.get("restoration_eligibility_allowed", True)
    )
    selected_outcome = projected_experiences[0] if projected_experiences else None
    restoration_applied = bool(
        experience_restoration_boundary.get("applicable", False)
        and experience_restoration_boundary.get("restoration_eligible", False)
        and selected_outcome is not None
    )
    restoration_execution_handoff_ready = bool(restoration_applied and execution_kind == "orchestration")
    return {
        "outcome_version": 1,
        "applicable": bool(experience_restoration_boundary.get("applicable", False)),
        "outcome_path": "experience_projection_to_restoration_outcome",
        "deterministic_outcome": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "outcome_is_authority": False,
        "restoration_applied": restoration_applied,
        "restoration_execution_handoff_ready": restoration_execution_handoff_ready,
        "restoration_outcome_reason": (
            "projected_experience_selected"
            if restoration_applied
            else (
                "guest_unknown_occupant_restriction"
                if bool(experience_restoration_boundary.get("applicable", False))
                and not restoration_allowed_by_guest_behavior
                else (
                    "multi_occupant_conflict_aware_restriction"
                    if bool(experience_restoration_boundary.get("applicable", False))
                    and not restoration_allowed_by_multi_behavior
                    else "no_projected_experiences"
                )
            )
        ),
        "selected_outcome": {
            "experience_id": selected_outcome.get("experience_id"),
            "source_capability_id": selected_outcome.get("source_capability_id"),
            "projection_mode": selected_outcome.get("projection_mode"),
        }
        if selected_outcome is not None
        else None,
        "fallback_applied": not restoration_applied,
        "lineage_references": {
            "projection_path": experience_projection.get("projection_path"),
            "projected_experience_count": projected_count,
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "guest_unknown_occupant_state": guest_behavior.get("occupant_state"),
            "multi_occupant_state": multi_behavior.get("occupant_state"),
        },
        "ownership_preservation": {
            "restoration_authority_external": True,
            "restoration_policy_authority_external": True,
            "restoration_decision_authority_transferred": False,
            "restoration_redefines_governance": False,
        },
        "governance_controls": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "restoration_decision_behavior_enabled": True,
            "restoration_execution_enabled": execution_kind == "orchestration",
            "restoration_diagnostics_behavior_enabled": True,
            "guest_unknown_behavior_enabled": bool(
                guest_behavior.get("governance_controls", {}).get("behavior_enabled", False)
            ),
            "multi_occupant_behavior_enabled": bool(
                multi_behavior.get("governance_controls", {}).get("behavior_enabled", False)
            ),
        },
        "deferred_release_3_owners": {
            "e3a_preservation_alignment": "#331",
            "restoration_diagnostics_explainability": "#332",
            "release_3_validation": "#338",
        },
    }


def _build_e3a_preservation_alignment(
    *,
    experience_restoration_boundary: dict[str, Any],
    experience_restoration_outcome: dict[str, Any],
    execution_kind: str,
    route_scope: str,
    context_area_id: str | None,
    resolved_composite_id: str | None,
    requested_target: str | None,
    resolved_target: str | None,
) -> dict[str, Any]:
    """Return #331-governed preservation alignment metadata consuming restoration outcomes."""
    if execution_kind == "direct":
        return {
            "alignment_version": 1,
            "applicable": False,
            "alignment_path": "not_applicable_direct_execution",
            "deterministic_alignment": True,
            "concierge_role": "bounded_consumer_orchestrator",
            "consumes_restoration_outcomes": True,
            "preservation_governance_source": "adr_013_outcome_preservation",
            "preservation_mode": "household_facing_outcomes",
            "preservation_eligible": False,
            "alignment_reason": "direct_execution_not_eligible",
            "preserved_outcome_clusters": {
                "composite_room_execution": False,
                "execution_hierarchy": True,
                "global_context_provider_parity": False,
            },
            "restoration_linkage": {
                "restoration_outcome_path": experience_restoration_outcome.get("outcome_path"),
                "restoration_applied": bool(experience_restoration_outcome.get("restoration_applied", False)),
                "restoration_outcome_reason": experience_restoration_outcome.get("restoration_outcome_reason"),
            },
            "governance_controls": {
                "route_scope": "direct",
                "context_area_id": None,
                "resolved_composite_id": None,
                "alignment_behavior_enabled": False,
                "restoration_decision_behavior_enabled": False,
                "restoration_execution_enabled": False,
            },
            "ownership_preservation": {
                "restoration_authority_external": True,
                "restoration_policy_authority_external": True,
                "preservation_creates_authority": False,
                "preservation_redefines_outcomes": False,
                "preservation_redefines_eligibility": False,
            },
            "deferred_release_3_owners": {
                "restoration_diagnostics_explainability": "#332",
                "release_3_validation": "#338",
            },
        }

    selected_outcome = experience_restoration_outcome.get("selected_outcome")
    selected_outcome_dict = selected_outcome if isinstance(selected_outcome, dict) else {}
    restoration_applied = bool(experience_restoration_outcome.get("restoration_applied", False))
    preservation_eligible = bool(
        experience_restoration_boundary.get("applicable", False)
        and restoration_applied
    )
    return {
        "alignment_version": 1,
        "applicable": bool(experience_restoration_outcome.get("applicable", False)),
        "alignment_path": "restoration_outcome_to_e3a_preservation_alignment",
        "deterministic_alignment": True,
        "concierge_role": "bounded_consumer_orchestrator",
        "consumes_restoration_outcomes": True,
        "preservation_governance_source": "adr_013_outcome_preservation",
        "preservation_mode": "household_facing_outcomes",
        "preservation_eligible": preservation_eligible,
        "alignment_reason": (
            "restoration_outcome_aligned"
            if preservation_eligible
            else "restoration_outcome_not_applied"
        ),
        "preserved_outcome_clusters": {
            "composite_room_execution": bool(
                route_scope == "composite"
                and requested_target is not None
                and resolved_target is not None
                and requested_target != resolved_target
            ),
            "execution_hierarchy": True,
            "global_context_provider_parity": bool(route_scope == "global"),
        },
        "preservation_traceability": {
            "requested_target": requested_target,
            "resolved_target": resolved_target,
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
        },
        "restoration_linkage": {
            "restoration_path": experience_restoration_boundary.get("restoration_path"),
            "restoration_outcome_path": experience_restoration_outcome.get("outcome_path"),
            "restoration_applied": restoration_applied,
            "restoration_outcome_reason": experience_restoration_outcome.get("restoration_outcome_reason"),
            "selected_experience_id": selected_outcome_dict.get("experience_id"),
        },
        "governance_controls": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "alignment_behavior_enabled": True,
            "restoration_decision_behavior_enabled": bool(
                experience_restoration_boundary.get("governance_controls", {}).get(
                    "restoration_decision_behavior_enabled",
                    False,
                )
            ),
            "restoration_execution_enabled": bool(
                experience_restoration_boundary.get("governance_controls", {}).get(
                    "restoration_execution_enabled",
                    False,
                )
            ),
        },
        "ownership_preservation": {
            "restoration_authority_external": True,
            "restoration_policy_authority_external": True,
            "preservation_creates_authority": False,
            "preservation_redefines_outcomes": False,
            "preservation_redefines_eligibility": False,
        },
        "deferred_release_3_owners": {
            "restoration_diagnostics_explainability": "#332",
            "release_3_validation": "#338",
        },
    }


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

    response = result
    if isinstance(result, dict):
        response = dict(result)
        activity_request_summary = str(response.pop("activity_request_summary", "")).strip()
        activity_external_refs = response.pop("activity_external_refs", [])
        if activity_request_summary or activity_external_refs:
            activity = (await storage.async_load_state()).activities.get(activity_id)
            if activity is not None:
                if activity_request_summary:
                    activity.request_summary = _sanitize_request_summary(actor_class, activity_request_summary)
                if isinstance(activity_external_refs, list) and activity_external_refs:
                    activity.external_refs = list(activity.external_refs) + list(activity_external_refs)
                await storage.async_record_activity_event(activity)

    await storage.async_close_activity_event(
        activity_id=activity_id,
        ended_at=datetime.now(timezone.utc).isoformat(),
        outcome="success",
        outcome_reason="",
        actions_taken=[action_name],
        policy_gates=list(policy_gates or []),
    )
    return response


def _build_context_assembly_ref(assembled_context: dict[str, Any]) -> dict[str, Any]:
    """Return non-sensitive context assembly explainability metadata."""
    return {
        "ref_type": "context_assembly",
        "requested_area_id": assembled_context.get("requested_area_id"),
        "context_area_id": assembled_context.get("context_area_id"),
        "resolved_composite_id": assembled_context.get("resolved_composite_id"),
        "context_source_count": assembled_context.get("context_source_count", 0),
        "signal_count": assembled_context.get("signal_count", 0),
    }


def _build_routing_decision_ref(execution_envelope: dict[str, Any]) -> dict[str, Any]:
    """Return non-sensitive routing explainability metadata."""
    routing = dict(execution_envelope.get("routing", {}))
    return {
        "ref_type": "routing_decision",
        "route_scope": routing.get("route_scope"),
        "requested_area_id": routing.get("requested_area_id"),
        "context_area_id": routing.get("context_area_id"),
        "resolved_composite_id": routing.get("resolved_composite_id"),
        "execution_preference_scope_id": routing.get("execution_preference_scope_id"),
        "execution_preference_present": bool(routing.get("execution_preference_present", False)),
    }


def _build_execution_envelope_ref(execution_envelope: dict[str, Any]) -> dict[str, Any]:
    """Return non-sensitive execution-envelope explainability metadata."""
    planning = dict(execution_envelope.get("planning", {}))
    execution = dict(execution_envelope.get("execution", {}))
    authoritative_inputs = dict(execution_envelope.get("authoritative_capability_input_consumption", {}))
    vocabulary_handoff = dict(execution_envelope.get("vocabulary_to_capability_handoff", {}))
    asset_handoff = dict(execution_envelope.get("asset_intelligence_cp00_handoff", {}))
    discovery = dict(execution_envelope.get("capability_discovery", {}))
    continuity = dict(execution_envelope.get("continuity_governance_boundary", {}))
    affinity = dict(execution_envelope.get("person_room_affinity_boundary", {}))
    privacy_memory = dict(execution_envelope.get("privacy_household_memory_boundary", {}))
    occupancy = dict(execution_envelope.get("occupancy_governance_boundary", {}))
    presence = dict(execution_envelope.get("presence_governance_boundary", {}))
    guest_unknown = dict(execution_envelope.get("guest_unknown_occupant_behavior", {}))
    multi_occupant = dict(execution_envelope.get("multi_occupant_behavior", {}))
    experience = dict(execution_envelope.get("experience_governance_boundary", {}))
    handoff = dict(execution_envelope.get("capability_to_experience_handoff", {}))
    projection = dict(execution_envelope.get("experience_projection", {}))
    restoration = dict(execution_envelope.get("experience_restoration_boundary", {}))
    restoration_outcome = dict(execution_envelope.get("experience_restoration_outcome", {}))
    preservation_alignment = dict(execution_envelope.get("e3a_preservation_alignment", {}))
    restoration_controls = dict(restoration.get("governance_controls", {}))
    selected_outcome_raw = restoration_outcome.get("selected_outcome", {})
    selected_outcome = selected_outcome_raw if isinstance(selected_outcome_raw, dict) else {}
    continuity_constraints = dict(continuity.get("orchestration_constraints", {}))
    affinity_constraints = dict(affinity.get("orchestration_constraints", {}))
    occupancy_constraints = dict(occupancy.get("orchestration_constraints", {}))
    presence_constraints = dict(presence.get("orchestration_constraints", {}))
    guest_unknown_controls = dict(guest_unknown.get("governance_controls", {}))
    multi_occupant_controls = dict(multi_occupant.get("governance_controls", {}))
    experience_constraints = dict(experience.get("orchestration_constraints", {}))
    return {
        "ref_type": "execution_envelope",
        "envelope_version": execution_envelope.get("envelope_version"),
        "execution_kind": execution_envelope.get("execution_kind"),
        "intent_class": execution_envelope.get("intent_class"),
        "plan_kind": planning.get("plan_kind"),
        "target_type": planning.get("target_type"),
        "requested_target": planning.get("requested_target"),
        "resolved_target": planning.get("resolved_target"),
        "requested_service": planning.get("requested_service"),
        "requested_entity_id": planning.get("requested_entity_id"),
        "execution_domain": execution.get("domain"),
        "execution_service": execution.get("service"),
        "capability_authority_origin": authoritative_inputs.get("capability_authority_origin"),
        "vocabulary_room_consumed": bool(vocabulary_handoff.get("room_vocabulary_consumed", False)),
        "vocabulary_device_consumed": bool(vocabulary_handoff.get("device_entity_vocabulary_consumed", False)),
        "asset_cp00_handoff_applicable": bool(asset_handoff.get("applicable", False)),
        "asset_cp00_authority_preserved": bool(
            asset_handoff.get("asset_intelligence_authority_preserved", False)
        ),
        "capability_discovery_applicable": bool(discovery.get("applicable", False)),
        "discoverable_capability_ids": list(discovery.get("discoverable_capability_ids", [])),
        "discoverable_count": int(discovery.get("discoverable_count", 0) or 0),
        "capability_discovery_path": discovery.get("discovery_path"),
        "continuity_governance_applicable": bool(continuity.get("applicable", False)),
        "continuity_governance_path": continuity.get("continuity_path"),
        "continuity_diagnostics_behavior_enabled": bool(
            continuity_constraints.get("diagnostics_behavior_enabled", False)
        ),
        "continuity_owns_identity": bool(continuity.get("continuity_owns_identity", False)),
        "continuity_owns_occupancy": bool(continuity.get("continuity_owns_occupancy", False)),
        "continuity_owns_memory": bool(continuity.get("continuity_owns_memory", False)),
        "continuity_privacy_boundary_preserved": bool(
            continuity.get("privacy_boundary_preserved", False)
        ),
        "affinity_governance_applicable": bool(affinity.get("applicable", False)),
        "affinity_governance_path": affinity.get("affinity_path"),
        "affinity_diagnostics_behavior_enabled": bool(
            affinity_constraints.get("diagnostics_behavior_enabled", False)
        ),
        "affinity_owns_identity": bool(affinity.get("affinity_owns_identity", False)),
        "affinity_owns_room_truth": bool(affinity.get("affinity_owns_room_truth", False)),
        "affinity_owns_occupancy": bool(affinity.get("affinity_owns_occupancy", False)),
        "affinity_owns_memory": bool(affinity.get("affinity_owns_memory", False)),
        "affinity_guest_safe_boundary_preserved": bool(
            affinity.get("guest_safe_boundary_preserved", False)
        ),
        "affinity_privacy_boundary_preserved": bool(
            affinity.get("privacy_boundary_preserved", False)
        ),
        "privacy_household_memory_boundary_applicable": bool(
            privacy_memory.get("applicable", False)
        ),
        "privacy_household_memory_boundary_path": privacy_memory.get("boundary_path"),
        "memory_owns_identity": bool(privacy_memory.get("memory_owns_identity", False)),
        "memory_owns_retention_policy": bool(
            privacy_memory.get("memory_owns_retention_policy", False)
        ),
        "memory_owns_storage": bool(privacy_memory.get("memory_owns_storage", False)),
        "memory_owns_provenance": bool(privacy_memory.get("memory_owns_provenance", False)),
        "privacy_memory_guest_safe_boundary_preserved": bool(
            privacy_memory.get("guest_safe_boundary_preserved", False)
        ),
        "occupancy_governance_applicable": bool(occupancy.get("applicable", False)),
        "occupancy_governance_path": occupancy.get("occupancy_path"),
        "occupancy_authority_external": bool(occupancy.get("occupancy_authority_external", False)),
        "occupancy_policy_authority_external": bool(
            occupancy.get("occupancy_policy_authority_external", False)
        ),
        "occupancy_truth_authority_external": bool(
            occupancy.get("occupancy_truth_authority_external", False)
        ),
        "occupancy_owns_room_truth": bool(occupancy.get("occupancy_owns_room_truth", False)),
        "occupancy_owns_identity": bool(occupancy.get("occupancy_owns_identity", False)),
        "occupancy_owns_household_memory": bool(
            occupancy.get("occupancy_owns_household_memory", False)
        ),
        "occupancy_owns_restoration": bool(occupancy.get("occupancy_owns_restoration", False)),
        "occupancy_guest_safe_boundary_preserved": bool(
            occupancy.get("guest_safe_boundary_preserved", False)
        ),
        "occupancy_privacy_boundary_preserved": bool(
            occupancy.get("privacy_boundary_preserved", False)
        ),
        "occupancy_decision_behavior_enabled": bool(
            occupancy_constraints.get("occupancy_decision_behavior_enabled", False)
        ),
        "occupancy_execution_enabled": bool(
            occupancy_constraints.get("occupancy_execution_enabled", False)
        ),
        "occupancy_inference_enabled": bool(
            occupancy_constraints.get("occupancy_inference_enabled", False)
        ),
        "occupancy_diagnostics_behavior_enabled": bool(
            occupancy_constraints.get("occupancy_diagnostics_behavior_enabled", False)
        ),
        "presence_governance_applicable": bool(presence.get("applicable", False)),
        "presence_governance_path": presence.get("presence_path"),
        "presence_authority_external": bool(presence.get("presence_authority_external", False)),
        "presence_policy_authority_external": bool(
            presence.get("presence_policy_authority_external", False)
        ),
        "presence_truth_authority_external": bool(
            presence.get("presence_truth_authority_external", False)
        ),
        "presence_owns_occupancy": bool(presence.get("presence_owns_occupancy", False)),
        "presence_owns_room_truth": bool(presence.get("presence_owns_room_truth", False)),
        "presence_owns_identity": bool(presence.get("presence_owns_identity", False)),
        "presence_owns_household_memory": bool(
            presence.get("presence_owns_household_memory", False)
        ),
        "presence_owns_restoration": bool(presence.get("presence_owns_restoration", False)),
        "presence_guest_safe_boundary_preserved": bool(
            presence.get("guest_safe_boundary_preserved", False)
        ),
        "presence_privacy_boundary_preserved": bool(
            presence.get("privacy_boundary_preserved", False)
        ),
        "presence_consumes_occupancy_governance_visibility": bool(
            presence.get("consumes_occupancy_governance_visibility", False)
        ),
        "presence_detection_enabled": bool(
            presence_constraints.get("presence_detection_enabled", False)
        ),
        "presence_inference_enabled": bool(
            presence_constraints.get("presence_inference_enabled", False)
        ),
        "presence_attribution_enabled": bool(
            presence_constraints.get("presence_attribution_enabled", False)
        ),
        "presence_behavior_enabled": bool(
            presence_constraints.get("presence_behavior_enabled", False)
        ),
        "presence_diagnostics_behavior_enabled": bool(
            presence_constraints.get("presence_diagnostics_behavior_enabled", False)
        ),
        "guest_unknown_behavior_applicable": bool(guest_unknown.get("applicable", False)),
        "guest_unknown_behavior_path": guest_unknown.get("behavior_path"),
        "guest_unknown_occupant_state": guest_unknown.get("occupant_state"),
        "guest_unknown_guest_safe_mode_active": bool(
            guest_unknown.get("guest_safe_mode_active", False)
        ),
        "guest_unknown_unknown_occupant_mode_active": bool(
            guest_unknown.get("unknown_occupant_mode_active", False)
        ),
        "guest_unknown_conservative_behavior_required": bool(
            guest_unknown.get("conservative_behavior_required", False)
        ),
        "guest_unknown_private_personalization_blocked": bool(
            guest_unknown.get("private_personalization_blocked", False)
        ),
        "guest_unknown_private_memory_inheritance_blocked": bool(
            guest_unknown.get("private_memory_inheritance_blocked", False)
        ),
        "guest_unknown_restoration_eligibility_allowed": bool(
            guest_unknown.get("restoration_eligibility_allowed", False)
        ),
        "guest_unknown_messaging_eligibility_influence": guest_unknown.get(
            "messaging_eligibility_influence"
        ),
        "guest_unknown_notification_eligibility_influence": guest_unknown.get(
            "notification_eligibility_influence"
        ),
        "guest_unknown_identity_attribution_enabled": bool(
            guest_unknown.get("identity_attribution_enabled", False)
        ),
        "guest_unknown_behavior_enabled": bool(
            guest_unknown_controls.get("behavior_enabled", False)
        ),
        "multi_occupant_behavior_applicable": bool(multi_occupant.get("applicable", False)),
        "multi_occupant_behavior_path": multi_occupant.get("behavior_path"),
        "multi_occupant_occupant_state": multi_occupant.get("occupant_state"),
        "multi_occupant_mode_active": bool(multi_occupant.get("multi_occupant_mode_active", False)),
        "multi_occupant_conflict_aware_behavior_required": bool(
            multi_occupant.get("conflict_aware_behavior_required", False)
        ),
        "multi_occupant_restoration_eligibility_allowed": bool(
            multi_occupant.get("restoration_eligibility_allowed", False)
        ),
        "multi_occupant_conflict_visibility_enabled": bool(
            multi_occupant.get("conflict_visibility_enabled", False)
        ),
        "multi_occupant_behavior_enabled": bool(
            multi_occupant_controls.get("behavior_enabled", False)
        ),
        "experience_governance_applicable": bool(experience.get("applicable", False)),
        "experience_governance_path": experience.get("governance_path"),
        "experience_consumes_capability_outputs": bool(
            experience.get("experience_consumes_capability_outputs", False)
        ),
        "experience_redefines_capability_outputs": bool(
            experience.get("experience_redefines_capability_outputs", False)
        ),
        "experience_execution_enabled": bool(experience_constraints.get("experience_execution_enabled", False)),
        "capability_to_experience_handoff_applicable": bool(handoff.get("applicable", False)),
        "capability_to_experience_handoff_path": handoff.get("handoff_path"),
        "experience_consumption_ready": bool(handoff.get("experience_consumption_ready", False)),
        "handoff_transfers_authority": bool(handoff.get("handoff_transfers_authority", False)),
        "experience_projection_applicable": bool(projection.get("applicable", False)),
        "experience_projection_path": projection.get("projection_path"),
        "projected_experience_count": int(projection.get("projected_experience_count", 0) or 0),
        "projection_is_authority": bool(projection.get("projection_is_authority", False)),
        "experience_restoration_boundary_applicable": bool(restoration.get("applicable", False)),
        "experience_restoration_path": restoration.get("restoration_path"),
        "restoration_governance_path": restoration.get("restoration_governance_path"),
        "restoration_eligible": bool(restoration.get("restoration_eligible", False)),
        "restoration_authority_external": bool(restoration.get("restoration_authority_external", False)),
        "restoration_policy_authority_external": bool(
            restoration.get("restoration_policy_authority_external", False)
        ),
        "restoration_owns_identity": bool(restoration.get("restoration_owns_identity", False)),
        "restoration_owns_occupancy": bool(restoration.get("restoration_owns_occupancy", False)),
        "restoration_owns_continuity": bool(restoration.get("restoration_owns_continuity", False)),
        "restoration_owns_affinity": bool(restoration.get("restoration_owns_affinity", False)),
        "restoration_owns_household_memory": bool(
            restoration.get("restoration_owns_household_memory", False)
        ),
        "restoration_execution_enabled": bool(
            restoration_controls.get("restoration_execution_enabled", False)
        ),
        "restoration_decision_behavior_enabled": bool(
            restoration_controls.get("restoration_decision_behavior_enabled", False)
        ),
        "restoration_diagnostics_behavior_enabled": bool(
            restoration_controls.get("restoration_diagnostics_behavior_enabled", False)
        ),
        "restoration_authority_transferred": bool(restoration.get("restoration_authority_transferred", False)),
        "restoration_privacy_boundary_preserved": bool(
            restoration.get("privacy_boundary_preserved", False)
        ),
        "restoration_guest_safe_boundary_preserved": bool(
            restoration.get("guest_safe_boundary_preserved", False)
        ),
        "experience_restoration_outcome_applicable": bool(restoration_outcome.get("applicable", False)),
        "experience_restoration_outcome_path": restoration_outcome.get("outcome_path"),
        "restoration_applied": bool(restoration_outcome.get("restoration_applied", False)),
        "restoration_execution_handoff_ready": bool(
            restoration_outcome.get("restoration_execution_handoff_ready", False)
        ),
        "restoration_outcome_reason": restoration_outcome.get("restoration_outcome_reason"),
        "restoration_selected_experience_id": selected_outcome.get("experience_id"),
        "e3a_preservation_alignment_applicable": bool(
            preservation_alignment.get("applicable", False)
        ),
        "e3a_preservation_alignment_path": preservation_alignment.get("alignment_path"),
        "e3a_preservation_eligible": bool(preservation_alignment.get("preservation_eligible", False)),
        "e3a_preservation_alignment_reason": preservation_alignment.get("alignment_reason"),
        "e3a_preservation_consumes_restoration_outcomes": bool(
            preservation_alignment.get("consumes_restoration_outcomes", False)
        ),
    }


def _build_preservation_alignment_ref(execution_envelope: dict[str, Any]) -> dict[str, Any]:
    """Return bounded preservation-alignment traceability metadata."""
    alignment = dict(execution_envelope.get("e3a_preservation_alignment", {}))
    restoration_linkage = dict(alignment.get("restoration_linkage", {}))
    return {
        "ref_type": "preservation_alignment",
        "alignment_path": alignment.get("alignment_path"),
        "applicable": bool(alignment.get("applicable", False)),
        "preservation_eligible": bool(alignment.get("preservation_eligible", False)),
        "alignment_reason": alignment.get("alignment_reason"),
        "route_scope": alignment.get("governance_controls", {}).get("route_scope"),
        "restoration_outcome_path": restoration_linkage.get("restoration_outcome_path"),
        "restoration_applied": bool(restoration_linkage.get("restoration_applied", False)),
        "selected_experience_id": restoration_linkage.get("selected_experience_id"),
    }


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


async def _async_resolve_integration_capabilities(hass: HomeAssistant) -> dict[str, Any]:
    """Resolve Concierge capability flags from config entry options/data and Voice Identity discovery."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return {
            "cap_ai": False,
            "cap_tts": False,
            "cap_persona": False,
            "cap_assets": False,
            "cap_voice_enrollment": False,
            "cap_extended_history": False,
            "archive_ready": False,
            "voice_enrollment_reason_code": "concierge_not_configured",
            "voice_enrollment_status_summary": "Voice enrollment requires Concierge to be configured.",
            "input_snapshot": {
                "ai_enabled": False,
                "action_provider": _PROVIDER_NONE,
                "tts_enabled": False,
                "tts_provider": _PROVIDER_NONE,
                "asset_intelligence_provider": _PROVIDER_NONE,
                "archive_ready": False,
                "voice_identity_ready": False,
                "voice_enrollment_reason_code": "concierge_not_configured",
            },
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
    archive_ready = bool(
        archive_options.get("destination_configured") and archive_options.get("archive_enabled")
    )
    cap_extended_history = bool(
        archive_options.get("destination_configured") and archive_options.get("archive_enabled")
    )
    voice_identity_status = await async_get_voice_identity_enrollment_status(hass)
    voice_identity_ready = bool(voice_identity_status.get("voice_enrollment_enabled", False))
    cap_voice_enrollment = bool(archive_ready and voice_identity_ready)

    if not archive_ready:
        reason_code = "archive_not_configured"
        status_summary = "Voice enrollment requires attached storage and archive export to be enabled in Concierge options."
    elif not voice_identity_ready:
        reason_code = str(voice_identity_status.get("voice_enrollment_reason_code", "voice_identity_unavailable"))
        status_summary = str(
            voice_identity_status.get(
                "voice_enrollment_status_summary",
                "Voice enrollment is unavailable because Voice Identity is not ready.",
            )
        )
    else:
        reason_code = "ready"
        status_summary = "Voice enrollment is ready."

    return {
        "cap_ai": cap_ai,
        "cap_tts": cap_tts,
        "cap_persona": cap_persona,
        "cap_assets": cap_assets,
        "cap_voice_enrollment": cap_voice_enrollment,
        "cap_extended_history": cap_extended_history,
        "archive_ready": archive_ready,
        "voice_enrollment_reason_code": reason_code,
        "voice_enrollment_status_summary": status_summary,
        "input_snapshot": {
            "ai_enabled": ai_enabled,
            "action_provider": action_provider,
            "tts_enabled": tts_enabled,
            "tts_provider": tts_provider,
            "asset_intelligence_provider": asset_intelligence_provider,
            "archive_ready": archive_ready,
            "voice_identity_ready": voice_identity_ready,
            "voice_enrollment_reason_code": reason_code,
        },
    }


def _voice_enrollment_unavailable_error(capabilities: dict[str, Any], *, action: str) -> str:
    """Build user-safe enrollment unavailable error text from capability projection."""
    summary = str(
        capabilities.get(
            "voice_enrollment_status_summary",
            "Voice enrollment is unavailable because required dependencies are not ready.",
        )
    ).strip()
    if not summary:
        summary = "Voice enrollment is unavailable because required dependencies are not ready."
    return f"{action} is unavailable: {summary}"


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
    capabilities = await _async_resolve_integration_capabilities(hass)

    area_id = call.data.get("area_id")
    composite_id = call.data.get("composite_id")
    room_vocabulary_resolution: dict[str, Any] | None = None
    device_entity_vocabulary_resolution: dict[str, Any] | None = None
    asset_vocabulary_resolution: dict[str, Any] | None = None

    if area_id and not composite_id:
        known_configured_area = area_id in state.rooms or any(
            area_id in composite.area_ids for composite in state.composites.values()
        )
        if not known_configured_area:
            room_vocabulary_resolution = _resolve_room_scope_from_vocabulary(state, area_id)
            if room_vocabulary_resolution is not None:
                if room_vocabulary_resolution.get("composite_id"):
                    composite_id = room_vocabulary_resolution["composite_id"]
                    resolved_composite = state.composites.get(composite_id)
                    if resolved_composite is None:
                        raise vol.Invalid(f"composite_id is not configured: {composite_id}")
                    if not resolved_composite.enabled:
                        raise vol.Invalid(f"composite_id is disabled: {composite_id}")
                    area_id = resolved_composite.primary_area or (
                        resolved_composite.area_ids[0] if resolved_composite.area_ids else area_id
                    )
                elif room_vocabulary_resolution.get("area_id"):
                    area_id = room_vocabulary_resolution["area_id"]

    if area_id and room_vocabulary_resolution is not None:
        _require_known_area_id(hass, area_id, field_name="room_vocabulary area")

    assembled_context = _assemble_foundation_context(
        state,
        requested_area_id=area_id,
        composite_id=composite_id,
        include_context=True,
        include_signals=True,
    )

    if "." not in str(call.data["target"]):
        device_entity_vocabulary_resolution = _resolve_entity_target_from_vocabulary(
            state,
            term=call.data["target"],
            area_id=area_id,
            composite_id=composite_id,
        )

    if "." not in str(call.data["target"]) and device_entity_vocabulary_resolution is None:
        asset_vocabulary_resolution = _resolve_asset_target_from_handoff(
            state,
            term=call.data["target"],
            area_id=area_id,
            composite_id=composite_id,
        )

    vocabulary_resolved_target = (
        device_entity_vocabulary_resolution["entity_id"]
        if device_entity_vocabulary_resolution is not None
        else (
            asset_vocabulary_resolution["entity_id"]
            if asset_vocabulary_resolution is not None
            else call.data["target"]
        )
    )

    room = state.rooms.get(area_id) if area_id else None
    alias_resolved_target = _resolve_target_from_alias(
        vocabulary_resolved_target,
        area_id,
        room.aliases if room else {},
    )
    resolved_target = _resolve_preserved_execution_target(
        state,
        assembled_context=assembled_context,
        requested_target=call.data["target"],
        default_resolved_target=alias_resolved_target,
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

        execution_envelope = _build_execute_envelope(
            state,
            requested_area_id=area_id,
            call=call,
            capabilities=capabilities,
            assembled_context=assembled_context,
            resolved_target=resolved_target,
            room_vocabulary_resolution=room_vocabulary_resolution,
            device_entity_vocabulary_resolution=device_entity_vocabulary_resolution,
            asset_vocabulary_resolution=asset_vocabulary_resolution,
            domain=domain,
            service=service,
            data=data,
        )

        await hass.services.async_call(domain, service, data, blocking=True)

        payload = {
            "target": call.data["target"],
            "resolved_target": resolved_target,
            "area_id": area_id,
            "composite_id": composite_id,
            "context": call.data.get("context", {}),
            "execution_envelope": execution_envelope,
        }
        hass.bus.async_fire(EVENT_EXECUTION, payload)
        response: dict[str, Any] = {
            "executed": True,
            "resolved_target": resolved_target,
            "execution_envelope": execution_envelope,
            "activity_external_refs": [
                _build_context_assembly_ref(assembled_context),
                _build_routing_decision_ref(execution_envelope),
                _build_execution_envelope_ref(execution_envelope),
                _build_preservation_alignment_ref(execution_envelope),
                {
                    "ref_type": "preservation_outcome",
                    "preservation_cluster": "composite_room_execution",
                    "requested_target": call.data["target"],
                    "resolved_target": resolved_target,
                    "resolved_composite_id": assembled_context.get("resolved_composite_id"),
                    "preserved": resolved_target != call.data["target"],
                },
            ],
        }
        if room_vocabulary_resolution is not None:
            response["room_vocabulary_resolution"] = dict(room_vocabulary_resolution)
            response["activity_external_refs"].append(
                {
                    "ref_type": "room_vocabulary_resolution",
                    "matched_term": room_vocabulary_resolution.get("matched_term"),
                    "canonical_term": room_vocabulary_resolution.get("canonical_term"),
                    "resolved_area_id": area_id,
                    "resolved_composite_id": composite_id,
                    "source": room_vocabulary_resolution.get("source", "room_vocabulary_registry"),
                }
            )
        if device_entity_vocabulary_resolution is not None:
            response["device_entity_vocabulary_resolution"] = dict(device_entity_vocabulary_resolution)
            response["activity_external_refs"].append(
                {
                    "ref_type": "device_entity_vocabulary_resolution",
                    "matched_term": device_entity_vocabulary_resolution.get("matched_term"),
                    "canonical_term": device_entity_vocabulary_resolution.get("canonical_term"),
                    "resolved_entity_id": device_entity_vocabulary_resolution.get("entity_id"),
                    "resolved_area_id": area_id,
                    "resolved_composite_id": composite_id,
                    "source": device_entity_vocabulary_resolution.get(
                        "source",
                        "device_entity_vocabulary_registry",
                    ),
                }
            )
        if asset_vocabulary_resolution is not None:
            response["asset_vocabulary_resolution"] = dict(asset_vocabulary_resolution)
            response["activity_external_refs"].append(
                {
                    "ref_type": "asset_vocabulary_resolution",
                    "matched_term": asset_vocabulary_resolution.get("matched_term"),
                    "canonical_term": asset_vocabulary_resolution.get("canonical_term"),
                    "asset_id": asset_vocabulary_resolution.get("asset_id"),
                    "resolved_entity_id": asset_vocabulary_resolution.get("entity_id"),
                    "resolved_area_id": area_id,
                    "resolved_composite_id": composite_id,
                    "source": asset_vocabulary_resolution.get("source", "asset_intelligence_handoff"),
                }
            )
            response["activity_external_refs"].append(
                {
                    "ref_type": "asset_intelligence_cp00_handoff",
                    "authority_owner": "asset_intelligence",
                    "handoff_source": asset_vocabulary_resolution.get(
                        "source",
                        "asset_intelligence_handoff",
                    ),
                    "asset_id": asset_vocabulary_resolution.get("asset_id"),
                    "resolved_entity_id": asset_vocabulary_resolution.get("entity_id"),
                    "resolved_area_id": area_id,
                    "resolved_composite_id": composite_id,
                    "consumption_only": True,
                }
            )
        return response

    return await _async_with_activity(
        hass,
        call,
        intent_class="execute_orchestration",
        request_summary=f"Execute request for {_area_name(hass, area_id)}",
        action_name="execute",
        resolved_area_id=area_id,
        resolved_person_id=call.data.get("person_id"),
        channel="service_execute",
        external_refs=[
            {
                "ref_type": "execute_target",
                "target": call.data["target"],
                "resolved_target": resolved_target,
            }
        ],
        runner=_runner,
    )


async def _async_handle_execute_direct(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    """Execute a direct service/entity action without orchestration."""
    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    capabilities = await _async_resolve_integration_capabilities(hass)
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
        execution_envelope = _build_execute_direct_envelope(
            call=call,
            capabilities=capabilities,
            domain=domain,
            service=service,
            data=data,
        )
        await hass.services.async_call(domain, service, data, blocking=True)

        payload = {
            "entity_id": call.data["entity_id"],
            "service": service_ref,
            "data": call.data.get("data", {}),
            "execution_envelope": execution_envelope,
        }
        hass.bus.async_fire(EVENT_EXECUTION, payload)
        return {
            "executed": True,
            "execution_envelope": execution_envelope,
            "activity_external_refs": [
                _build_routing_decision_ref(execution_envelope),
                _build_execution_envelope_ref(execution_envelope),
                _build_preservation_alignment_ref(execution_envelope),
            ],
        }

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
    _require_known_area_id(hass, area_id)
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
    capabilities = await _async_resolve_integration_capabilities(hass)

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
    capabilities = await _async_resolve_integration_capabilities(hass)
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
        return await EnrollmentOrchestrator(hass).update_voice_profile(dict(call.data))

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
    capabilities = await _async_resolve_integration_capabilities(hass)
    if not capabilities["cap_voice_enrollment"]:
        raise vol.Invalid(_voice_enrollment_unavailable_error(capabilities, action="voice enrollment"))
    person_id = call.data["person_id"]
    if not bool(call.data.get("consent_acknowledged", False)):
        raise vol.Invalid("voice enrollment requires explicit consent_acknowledged=true")

    async def _runner() -> dict[str, Any]:
        return await EnrollmentOrchestrator(hass).start_enrollment(dict(call.data))

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
    capabilities = await _async_resolve_integration_capabilities(hass)
    if not capabilities["cap_voice_enrollment"]:
        raise vol.Invalid(_voice_enrollment_unavailable_error(capabilities, action="voice enrollment capture"))
    voice_profile_id = call.data["voice_profile_id"]
    speech_text = str(call.data.get("speech_text", "")).strip()
    if not speech_text:
        raise vol.Invalid("speech_text is required")

    if str(call.data.get("capture_provider", "browser")).strip().lower() == "satellite":
        prompt_text = str(call.data.get("prompt_text", "")).strip()
        if not prompt_text:
            raise vol.Invalid("prompt_text is required when capture_provider=satellite")

    async def _runner() -> dict[str, Any]:
        return await EnrollmentOrchestrator(hass).capture_enrollment_sample(dict(call.data))

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


async def _async_handle_run_satellite_capture_poc(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Run the bounded satellite capture proof of concept (internal/dev-only)."""
    capabilities = await _async_resolve_integration_capabilities(hass)
    if not capabilities["cap_voice_enrollment"]:
        raise vol.Invalid(_voice_enrollment_unavailable_error(capabilities, action="satellite capture POC"))

    async def _runner() -> dict[str, Any]:
        return await EnrollmentOrchestrator(hass).run_satellite_capture_poc(dict(call.data))

    return await _async_with_activity(
        hass,
        call,
        intent_class="run_satellite_capture_poc_internal_dev_only",
        request_summary="Internal/dev-only satellite capture POC executed",
        action_name="run_satellite_capture_poc_internal_dev_only",
        resolved_person_id=call.data.get("person_id"),
        channel="service_operational",
        external_refs=[{"ref_type": "satellite_capture_poc", "voice_profile_id": call.data.get("voice_profile_id")}],
        policy_gates=["local_first_default"],
        runner=_runner,
    )


async def _async_handle_remove_voice_enrollment_sample(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Remove one previously captured speech item from a voice profile."""
    capabilities = await _async_resolve_integration_capabilities(hass)
    if not capabilities["cap_voice_enrollment"]:
        raise vol.Invalid(_voice_enrollment_unavailable_error(capabilities, action="voice enrollment sample management"))
    voice_profile_id = call.data["voice_profile_id"]
    sample_id = call.data["sample_id"]

    async def _runner() -> dict[str, Any]:
        return await EnrollmentOrchestrator(hass).remove_sample(dict(call.data))

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
    capabilities = await _async_resolve_integration_capabilities(hass)
    if not capabilities["cap_voice_enrollment"]:
        raise vol.Invalid(_voice_enrollment_unavailable_error(capabilities, action="voice profile build"))
    voice_profile_id = call.data["voice_profile_id"]
    min_samples = int(call.data.get("min_samples", 3))

    async def _runner() -> dict[str, Any]:
        return await EnrollmentOrchestrator(hass).build_voice_profile(dict(call.data))

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


async def _async_handle_complete_voice_enrollment(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Run deterministic enrollment completion workflow through orchestrator."""
    capabilities = await _async_resolve_integration_capabilities(hass)
    if not capabilities["cap_voice_enrollment"]:
        raise vol.Invalid(_voice_enrollment_unavailable_error(capabilities, action="voice enrollment completion"))
    voice_profile_id = call.data["voice_profile_id"]

    async def _runner() -> dict[str, Any]:
        return await EnrollmentOrchestrator(hass).complete_enrollment(dict(call.data))

    return await _async_with_activity(
        hass,
        call,
        intent_class="complete_voice_enrollment",
        request_summary=f"Voice enrollment completion requested: {voice_profile_id}",
        action_name="complete_voice_enrollment",
        resolved_person_id=call.data.get("person_id"),
        channel="service_mutation",
        external_refs=[{"ref_type": "voice_enrollment_complete", "voice_profile_id": voice_profile_id}],
        runner=_runner,
    )


async def _async_handle_get_voice_enrollment_completion_readiness(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Return deterministic completion readiness derived from authoritative session state."""
    return await EnrollmentOrchestrator(hass).get_completion_readiness(dict(call.data))


async def _async_handle_cancel_voice_enrollment(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Cancel active voice enrollment and invoke cleanup deterministically."""
    async def _runner() -> dict[str, Any]:
        return await EnrollmentOrchestrator(hass).cancel_enrollment(dict(call.data))

    return await _async_with_activity(
        hass,
        call,
        intent_class="cancel_voice_enrollment",
        request_summary="Voice enrollment cancellation requested",
        action_name="cancel_voice_enrollment",
        resolved_person_id=call.data.get("person_id"),
        channel="service_mutation",
        external_refs=[{"ref_type": "voice_enrollment_cancel", "voice_profile_id": call.data.get("voice_profile_id")}],
        runner=_runner,
    )


async def _async_handle_recover_voice_enrollment(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Return authoritative recovery decision for voice enrollment."""
    async def _runner() -> dict[str, Any]:
        return await EnrollmentOrchestrator(hass).recover_enrollment(dict(call.data))

    return await _async_with_activity(
        hass,
        call,
        intent_class="recover_voice_enrollment",
        request_summary="Voice enrollment recovery requested",
        action_name="recover_voice_enrollment",
        resolved_person_id=call.data.get("person_id"),
        channel="service_operational",
        external_refs=[{"ref_type": "voice_enrollment_recover", "voice_profile_id": call.data.get("voice_profile_id")}],
        runner=_runner,
    )


async def _async_handle_resume_voice_enrollment(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Resume recoverable voice enrollment session from authoritative state."""
    async def _runner() -> dict[str, Any]:
        return await EnrollmentOrchestrator(hass).resume_enrollment(dict(call.data))

    return await _async_with_activity(
        hass,
        call,
        intent_class="resume_voice_enrollment",
        request_summary="Voice enrollment resume requested",
        action_name="resume_voice_enrollment",
        resolved_person_id=call.data.get("person_id"),
        channel="service_operational",
        external_refs=[{"ref_type": "voice_enrollment_resume", "voice_profile_id": call.data.get("voice_profile_id")}],
        runner=_runner,
    )


async def _async_handle_abandon_voice_enrollment(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Abandon active voice enrollment and run cleanup through orchestrator."""
    async def _runner() -> dict[str, Any]:
        return await EnrollmentOrchestrator(hass).abandon_enrollment(dict(call.data))

    return await _async_with_activity(
        hass,
        call,
        intent_class="abandon_voice_enrollment",
        request_summary="Voice enrollment abandon requested",
        action_name="abandon_voice_enrollment",
        resolved_person_id=call.data.get("person_id"),
        channel="service_mutation",
        external_refs=[{"ref_type": "voice_enrollment_abandon", "voice_profile_id": call.data.get("voice_profile_id")}],
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
        return await EnrollmentOrchestrator(hass).reset_voice_profile(dict(call.data))

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
        return await EnrollmentOrchestrator(hass).delete_voice_profile(dict(call.data))

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
    capabilities = await _async_resolve_integration_capabilities(hass)

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
    capabilities = await _async_resolve_integration_capabilities(hass)
    assembled_context = _assemble_foundation_context(
        state,
        requested_area_id=call.data.get("area_id"),
        include_context=bool(call.data.get("include_context", True)),
        include_signals=bool(call.data.get("include_signals", True)),
    )
    fallback_status = _context_fallback_status(
        state,
        requested_area_id=call.data.get("area_id"),
        assembled_context=assembled_context,
    )
    capability_discovery = _build_capability_discovery(
        capabilities=capabilities,
        route_scope=(
            "composite"
            if assembled_context.get("resolved_composite_id")
            else ("room" if assembled_context.get("context_area_id") else "global")
        ),
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
        room_vocabulary_resolution=None,
        device_entity_vocabulary_resolution=None,
        asset_vocabulary_resolution=None,
    )
    experience_governance_boundary = _build_experience_governance_boundary(
        route_scope=(
            "composite"
            if assembled_context.get("resolved_composite_id")
            else ("room" if assembled_context.get("context_area_id") else "global")
        ),
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    continuity_governance_boundary = _build_continuity_governance_boundary(
        execution_kind="summary",
        route_scope=(
            "composite"
            if assembled_context.get("resolved_composite_id")
            else ("room" if assembled_context.get("context_area_id") else "global")
        ),
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    person_room_affinity_boundary = _build_person_room_affinity_boundary(
        execution_kind="summary",
        route_scope=(
            "composite"
            if assembled_context.get("resolved_composite_id")
            else ("room" if assembled_context.get("context_area_id") else "global")
        ),
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    privacy_household_memory_boundary = _build_privacy_household_memory_boundary(
        execution_kind="summary",
        route_scope=(
            "composite"
            if assembled_context.get("resolved_composite_id")
            else ("room" if assembled_context.get("context_area_id") else "global")
        ),
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    messaging_governance_boundary = _build_messaging_governance_boundary(
        route_scope=(
            "composite"
            if assembled_context.get("resolved_composite_id")
            else ("room" if assembled_context.get("context_area_id") else "global")
        ),
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
        recipient_scope="household",
        message_context_type="summary",
    )
    occupancy_governance_boundary = _build_occupancy_governance_boundary(
        execution_kind="summary",
        route_scope=(
            "composite"
            if assembled_context.get("resolved_composite_id")
            else ("room" if assembled_context.get("context_area_id") else "global")
        ),
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    presence_governance_boundary = _build_presence_governance_boundary(
        execution_kind="summary",
        route_scope=(
            "composite"
            if assembled_context.get("resolved_composite_id")
            else ("room" if assembled_context.get("context_area_id") else "global")
        ),
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    guest_unknown_occupant_behavior = _build_guest_unknown_occupant_behavior(
        execution_kind="summary",
        route_scope=(
            "composite"
            if assembled_context.get("resolved_composite_id")
            else ("room" if assembled_context.get("context_area_id") else "global")
        ),
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
        person_id=None,
        context=None,
        occupancy_governance_boundary=occupancy_governance_boundary,
        presence_governance_boundary=presence_governance_boundary,
    )
    multi_occupant_behavior = _build_multi_occupant_behavior(
        execution_kind="summary",
        route_scope=(
            "composite"
            if assembled_context.get("resolved_composite_id")
            else ("room" if assembled_context.get("context_area_id") else "global")
        ),
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
        person_id=None,
        context=None,
        occupancy_governance_boundary=occupancy_governance_boundary,
        presence_governance_boundary=presence_governance_boundary,
        guest_unknown_occupant_behavior=guest_unknown_occupant_behavior,
    )
    capability_to_experience_handoff = _build_capability_to_experience_handoff(
        capability_discovery=capability_discovery,
        experience_governance_boundary=experience_governance_boundary,
        execution_kind="summary",
    )
    experience_projection = _build_experience_projection(
        capability_to_experience_handoff=capability_to_experience_handoff,
        experience_governance_boundary=experience_governance_boundary,
        execution_kind="summary",
    )
    experience_restoration_boundary = _build_experience_restoration_boundary(
        experience_projection=experience_projection,
        guest_unknown_occupant_behavior=guest_unknown_occupant_behavior,
        multi_occupant_behavior=multi_occupant_behavior,
        execution_kind="summary",
        route_scope=(
            "composite"
            if assembled_context.get("resolved_composite_id")
            else ("room" if assembled_context.get("context_area_id") else "global")
        ),
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    experience_restoration_outcome = _build_experience_restoration_outcome(
        experience_projection=experience_projection,
        experience_restoration_boundary=experience_restoration_boundary,
        guest_unknown_occupant_behavior=guest_unknown_occupant_behavior,
        multi_occupant_behavior=multi_occupant_behavior,
        execution_kind="summary",
        route_scope=(
            "composite"
            if assembled_context.get("resolved_composite_id")
            else ("room" if assembled_context.get("context_area_id") else "global")
        ),
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    e3a_preservation_alignment = _build_e3a_preservation_alignment(
        experience_restoration_boundary=experience_restoration_boundary,
        experience_restoration_outcome=experience_restoration_outcome,
        execution_kind="summary",
        route_scope=(
            "composite"
            if assembled_context.get("resolved_composite_id")
            else ("room" if assembled_context.get("context_area_id") else "global")
        ),
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
        requested_target=None,
        resolved_target=None,
    )
    return {
        "summary": assembled_context["summary"],
        "area_id": call.data.get("area_id"),
        "context_area_id": assembled_context["context_area_id"],
        "resolved_composite_id": assembled_context["resolved_composite_id"],
        "include_signals": call.data.get("include_signals", True),
        "include_context": call.data.get("include_context", True),
        "context_source_count": assembled_context["context_source_count"],
        "signal_count": assembled_context["signal_count"],
        "fallback_context_applied": fallback_status["fallback_context_applied"],
        "fallback_reason": fallback_status["fallback_reason"],
        "global_context_continuity_available": fallback_status["global_context_continuity_available"],
        "capability_discovery": capability_discovery,
        "continuity_governance_boundary": continuity_governance_boundary,
        "person_room_affinity_boundary": person_room_affinity_boundary,
        "privacy_household_memory_boundary": privacy_household_memory_boundary,
        "messaging_governance_boundary": messaging_governance_boundary,
        "occupancy_governance_boundary": occupancy_governance_boundary,
        "presence_governance_boundary": presence_governance_boundary,
        "guest_unknown_occupant_behavior": guest_unknown_occupant_behavior,
        "experience_governance_boundary": experience_governance_boundary,
        "capability_to_experience_handoff": capability_to_experience_handoff,
        "experience_projection": experience_projection,
        "experience_restoration_boundary": experience_restoration_boundary,
        "experience_restoration_outcome": experience_restoration_outcome,
        "e3a_preservation_alignment": e3a_preservation_alignment,
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
    capabilities = await _async_resolve_integration_capabilities(hass)
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
    assembled_context = _assemble_foundation_context(
        state,
        requested_area_id=resolved_area_id,
        person_profile=resolved_person,
        include_context=True,
        include_signals=True,
    )
    fallback_status = _context_fallback_status(
        state,
        requested_area_id=resolved_area_id,
        assembled_context=assembled_context,
    )

    return {
        "resolved_person_id": resolved_person.person_id if resolved_person else None,
        "person_confidence": person_confidence,
        "resolved_area_id": resolved_area_id,
        "resolved_composite_id": assembled_context["resolved_composite_id"],
        "context_area_id": assembled_context["context_area_id"],
        "room_confidence": room_confidence,
        "attribution_factors": (
            ["explicit_person_id"]
            if person_id and resolved_person
            else (["mobile_target_match"] if resolved_person else [])
        ),
        "clarification_required": room_confidence < 0.5,
        "fallback_context_applied": fallback_status["fallback_context_applied"],
        "fallback_reason": fallback_status["fallback_reason"],
        "global_context_continuity_available": fallback_status["global_context_continuity_available"],
        "assembled_context": assembled_context,
    }


async def _async_handle_push_person_message(
    hass: HomeAssistant,
    call: ServiceCall,
) -> dict[str, Any]:
    """Send person-scoped messages to the requested room or mobile delivery target."""
    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    profile = state.person_profiles.get(call.data["person_id"])
    if profile is None:
        raise vol.Invalid("person_id is not configured")

    room = state.rooms.get(profile.linked_area_id) if profile.linked_area_id else None

    requested_target = _normalize_message_target(call.data.get("target_id"))
    delivery_mode = "mobile_notify"
    service_domain = "notify"
    service_name = ""
    target_id = ""
    service_ref = ""
    service_data: dict[str, Any] = {}
    routing_path = "person_mobile_target_fallback"
    requested_target_supplied = bool(requested_target)
    explicit_entity_target = False

    if requested_target in _MESSAGE_WEB_UI_TARGETS:
        delivery_mode = "web_ui"
        target_id = requested_target or "web_ui"
        service_domain = "persistent_notification"
        service_name = "create"
        service_ref = "persistent_notification.create"
        routing_path = "explicit_web_ui_target"
        service_data = {
            "title": call.data.get("title", "Concierge"),
            "message": call.data["message"],
            "notification_id": f"concierge.{profile.person_id}.{target_id}",
        }
    elif requested_target.startswith("assist_satellite."):
        delivery_mode = "voice_assistant"
        target_id = requested_target
        routing_path = "explicit_voice_assistant_entity_target"
        explicit_entity_target = True
        if room is not None:
            voice_targets = _room_entity_ids(room, "voice_device_entity_ids")
            if voice_targets and target_id not in voice_targets:
                target_id = voice_targets[0]
        provider, _ = _resolve_tts_engine_entity_id(hass)
        tts_settings = _resolve_room_tts_settings(hass, provider=provider, room=room)
        media_id = await _resolve_tts_media_id(
            hass,
            provider=provider,
            message=call.data["message"],
            language=tts_settings["language"],
            voice=tts_settings["voice"],
        )
        service_domain = "assist_satellite"
        service_name = "announce"
        service_ref = "assist_satellite.announce"
        service_data = {"entity_id": target_id}
        if media_id:
            service_data["media_id"] = media_id
        else:
            service_data["message"] = call.data["message"]
    elif requested_target in _MESSAGE_VOICE_ASSISTANT_TARGETS:
        delivery_mode = "voice_assistant"
        if room is None:
            raise vol.Invalid("person is not linked to a room with voice assistant targets")
        voice_targets = _room_entity_ids(room, "voice_device_entity_ids")
        if not voice_targets:
            raise vol.Invalid("room has no configured voice assistant targets")
        target_id = voice_targets[0]
        routing_path = "resolved_room_voice_assistant_target"
        provider, _ = _resolve_tts_engine_entity_id(hass)
        tts_settings = _resolve_room_tts_settings(hass, provider=provider, room=room)
        media_id = await _resolve_tts_media_id(
            hass,
            provider=provider,
            message=call.data["message"],
            language=tts_settings["language"],
            voice=tts_settings["voice"],
        )
        service_domain = "assist_satellite"
        service_name = "announce"
        service_ref = "assist_satellite.announce"
        service_data = {"entity_id": target_id}
        if media_id:
            service_data["media_id"] = media_id
        else:
            service_data["message"] = call.data["message"]
    elif requested_target.startswith("media_player."):
        delivery_mode = "room_tts"
        target_id = requested_target
        routing_path = "explicit_speaker_entity_target"
        explicit_entity_target = True
        if room is not None:
            speaker_targets = _room_entity_ids(room, "media_player_entity_ids") or _room_entity_ids(
                room,
                "speaker_entity_ids",
            )
            if speaker_targets and target_id not in speaker_targets:
                target_id = speaker_targets[0]
        provider, engine_entity_id = _resolve_tts_engine_entity_id(hass)
        tts_settings = _resolve_room_tts_settings(hass, provider=provider, room=room)
        message_data: dict[str, Any] = {"cache": False}
        if tts_settings["voice"]:
            message_data["options"] = {"voice": tts_settings["voice"]}
        if tts_settings["language"]:
            message_data["language"] = tts_settings["language"]
        service_domain = "tts"
        service_name = "speak"
        service_ref = "tts.speak"
        service_data = {
            "entity_id": engine_entity_id,
            "media_player_entity_id": target_id,
            "message": call.data["message"],
            **message_data,
        }
    elif requested_target in _MESSAGE_TTS_TARGETS:
        delivery_mode = "room_tts"
        if room is None:
            raise vol.Invalid("person is not linked to a room with speaker targets")
        speaker_targets = _room_entity_ids(room, "media_player_entity_ids") or _room_entity_ids(
            room,
            "speaker_entity_ids",
        )
        if not speaker_targets:
            raise vol.Invalid("room has no configured speaker targets")
        routing_path = "resolved_room_speaker_target"
        provider, engine_entity_id = _resolve_tts_engine_entity_id(hass)
        tts_settings = _resolve_room_tts_settings(hass, provider=provider, room=room)
        message_data: dict[str, Any] = {"cache": False}
        if tts_settings["voice"]:
            message_data["options"] = {"voice": tts_settings["voice"]}
        if tts_settings["language"]:
            message_data["language"] = tts_settings["language"]
        target_id = speaker_targets[0]
        service_domain = "tts"
        service_name = "speak"
        service_ref = "tts.speak"
        service_data = {
            "entity_id": engine_entity_id,
            "media_player_entity_id": target_id,
            "message": call.data["message"],
            **message_data,
        }
    else:
        requested_mobile_target = requested_target[7:] if requested_target.startswith(_MESSAGE_MOBILE_TARGET_PREFIXES) else requested_target or None
        target_id = _select_mobile_target(profile, requested_mobile_target)
        routing_path = (
            "explicit_mobile_notify_target" if requested_mobile_target else "person_mobile_target_fallback"
        )
        service_domain = "notify"
        service_name = target_id
        service_ref = f"notify.{target_id}"
        service_data = {
            "title": call.data.get("title", "Concierge"),
            "message": call.data["message"],
            "data": dict(call.data.get("data", {})),
        }

    messaging_governance_boundary = _build_messaging_governance_boundary(
        route_scope="room" if profile.linked_area_id else "global",
        context_area_id=profile.linked_area_id,
        resolved_composite_id=None,
        recipient_scope="person",
        message_context_type="person_push",
    )
    messaging_boundary_ref = {
        "ref_type": "messaging_governance_boundary",
        "boundary_path": messaging_governance_boundary["boundary_path"],
        "messaging_boundary_version": messaging_governance_boundary["messaging_boundary_version"],
        "route_scope": messaging_governance_boundary["governance_controls"]["route_scope"],
        "recipient_scope": messaging_governance_boundary["governance_controls"]["recipient_scope"],
        "message_context_type": messaging_governance_boundary["governance_controls"]["message_context_type"],
        "message_authority_external": messaging_governance_boundary["message_authority_external"],
        "provenance_authority_external": messaging_governance_boundary["provenance_authority_external"],
        "household_memory_authority_external": messaging_governance_boundary["household_memory_authority_external"],
    }
    messaging_provenance, messaging_provenance_ref = _build_messaging_provenance(
        person_id=profile.person_id,
        linked_area_id=profile.linked_area_id,
        requested_target=requested_target,
        requested_target_supplied=requested_target_supplied,
        selected_target_id=target_id,
        selected_service=service_ref,
        delivery_channel=delivery_mode,
        routing_path=routing_path,
        explicit_entity_target=explicit_entity_target,
        messaging_governance_boundary=messaging_governance_boundary,
    )
    notification_delivery_boundary = _build_notification_delivery_boundary(
        route_scope=messaging_governance_boundary["governance_controls"]["route_scope"],
        context_area_id=profile.linked_area_id,
        resolved_composite_id=None,
        recipient_scope="person",
        message_context_type="person_push",
        delivery_channel=delivery_mode,
        selected_service=service_ref,
        selected_target_id=target_id,
        routing_path=routing_path,
        explicit_entity_target=explicit_entity_target,
    )
    notification_delivery_boundary_ref = {
        "ref_type": "notification_delivery_boundary",
        "boundary_path": notification_delivery_boundary["boundary_path"],
        "route_scope": notification_delivery_boundary["governance_controls"]["route_scope"],
        "recipient_scope": notification_delivery_boundary["governance_controls"]["recipient_scope"],
        "message_context_type": notification_delivery_boundary["governance_controls"]["message_context_type"],
        "delivery_channel": delivery_mode,
        "selected_service": service_ref,
        "selected_target_id": target_id,
        "routing_path": routing_path,
        "explicit_entity_target": explicit_entity_target,
        "delivery_authority_external": True,
        "recipient_authority_external": True,
        "consent_authority_external": True,
        "visibility_authority_external": True,
    }
    household_memory_governance_boundary, household_memory_governance_boundary_ref = (
        _build_household_memory_governance_boundary(
            route_scope=messaging_governance_boundary["governance_controls"]["route_scope"],
            context_area_id=profile.linked_area_id,
            resolved_composite_id=None,
            recipient_scope="person",
            message_context_type="person_push",
            delivery_channel=delivery_mode,
            selected_service=service_ref,
            selected_target_id=target_id,
            routing_path=routing_path,
            explicit_entity_target=explicit_entity_target,
        )
    )
    recipient_boundary, recipient_boundary_ref, delivery_permitted, delivery_decision_reason = (
        _build_recipient_consent_privacy_visibility_boundary(
            profile=profile,
            requested_target=requested_target,
            selected_target_id=target_id,
            selected_service=service_ref,
            delivery_channel=delivery_mode,
            routing_path=routing_path,
            explicit_entity_target=explicit_entity_target,
            route_scope=messaging_governance_boundary["governance_controls"]["route_scope"],
            context_area_id=profile.linked_area_id,
        )
    )
    messaging_diagnostics_explainability, messaging_diagnostics_explainability_ref = (
        _build_messaging_diagnostics_explainability(
            route_scope=messaging_governance_boundary["governance_controls"]["route_scope"],
            context_area_id=profile.linked_area_id,
            recipient_scope="person",
            message_context_type="person_push",
            delivery_permitted=delivery_permitted,
            decision_reason=delivery_decision_reason,
            delivery_channel=delivery_mode,
            selected_service=service_ref,
            selected_target_id=target_id,
            routing_path=routing_path,
            explicit_entity_target=explicit_entity_target,
            requested_target_supplied=requested_target_supplied,
        )
    )
    household_memory_ownership_consumption_boundary, household_memory_ownership_consumption_boundary_ref = (
        _build_household_memory_ownership_consumption_boundary(
            route_scope=messaging_governance_boundary["governance_controls"]["route_scope"],
            context_area_id=profile.linked_area_id,
            resolved_composite_id=None,
            recipient_scope="person",
            message_context_type="person_push",
            delivery_channel=delivery_mode,
            selected_service=service_ref,
            selected_target_id=target_id,
            routing_path=routing_path,
            explicit_entity_target=explicit_entity_target,
            consumption_permitted=delivery_permitted,
            consumption_decision_reason=delivery_decision_reason,
        )
    )
    household_memory_identity_privacy_retention_separation_boundary, household_memory_identity_privacy_retention_separation_boundary_ref = (
        _build_household_memory_identity_privacy_retention_separation_boundary(
            route_scope=messaging_governance_boundary["governance_controls"]["route_scope"],
            context_area_id=profile.linked_area_id,
            resolved_composite_id=None,
            recipient_scope="person",
            message_context_type="person_push",
            delivery_channel=delivery_mode,
            selected_service=service_ref,
            selected_target_id=target_id,
            routing_path=routing_path,
            explicit_entity_target=explicit_entity_target,
            separation_permitted=delivery_permitted,
            separation_decision_reason=delivery_decision_reason,
        )
    )
    household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary, household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary_ref = (
        _build_household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary(
            route_scope=messaging_governance_boundary["governance_controls"]["route_scope"],
            context_area_id=profile.linked_area_id,
            resolved_composite_id=None,
            recipient_scope="person",
            message_context_type="person_push",
            delivery_channel=delivery_mode,
            selected_service=service_ref,
            selected_target_id=target_id,
            routing_path=routing_path,
            explicit_entity_target=explicit_entity_target,
            separation_permitted=delivery_permitted,
            separation_decision_reason=delivery_decision_reason,
        )
    )
    household_memory_provenance_diagnostics_explainability_boundary, household_memory_provenance_diagnostics_explainability_boundary_ref = (
        _build_household_memory_provenance_diagnostics_explainability_boundary(
            route_scope=messaging_governance_boundary["governance_controls"]["route_scope"],
            context_area_id=profile.linked_area_id,
            resolved_composite_id=None,
            recipient_scope="person",
            message_context_type="person_push",
            delivery_channel=delivery_mode,
            selected_service=service_ref,
            selected_target_id=target_id,
            routing_path=routing_path,
            explicit_entity_target=explicit_entity_target,
            delivery_permitted=delivery_permitted,
            decision_reason=delivery_decision_reason,
            governance_boundary_involved=messaging_diagnostics_explainability_ref[
                "governance_boundary_involved"
            ],
            provenance_id=messaging_provenance_ref["provenance_id"],
            provenance_source_service=messaging_provenance_ref["source_service"],
            created_in_room=messaging_provenance_ref["created_in_room"],
            requested_target_supplied=requested_target_supplied,
        )
    )
    delivery_execution_attempt_ref = {
        "ref_type": "delivery_execution",
        "execution_state": "attempting",
        "delivery_channel": delivery_mode,
        "selected_service": service_ref,
        "selected_target_id": target_id,
        "routing_path": routing_path,
    }

    async def _runner() -> dict[str, Any]:
        if not delivery_permitted:
            raise vol.Invalid(
                "message delivery denied by recipient-consent-privacy-visibility boundary: "
                + delivery_decision_reason
            )

        await hass.services.async_call(service_domain, service_name, service_data, blocking=True)

        delivery_execution_success_ref = {
            "ref_type": "delivery_execution",
            "execution_state": "success",
            "delivery_channel": delivery_mode,
            "selected_service": service_ref,
            "selected_target_id": target_id,
            "routing_path": routing_path,
        }

        return {
            "sent": True,
            "person_id": profile.person_id,
            "target_id": target_id,
            "service": service_ref,
            "messaging_governance_boundary": messaging_governance_boundary,
            "messaging_provenance": messaging_provenance,
            "notification_delivery_boundary": notification_delivery_boundary,
            "recipient_consent_privacy_visibility_boundary": recipient_boundary,
            "messaging_diagnostics_explainability": messaging_diagnostics_explainability,
            "household_memory_governance_boundary": household_memory_governance_boundary,
            "household_memory_ownership_consumption_boundary": household_memory_ownership_consumption_boundary,
            "household_memory_identity_privacy_retention_separation_boundary": household_memory_identity_privacy_retention_separation_boundary,
            "household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary": household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary,
            "household_memory_provenance_diagnostics_explainability_boundary": household_memory_provenance_diagnostics_explainability_boundary,
            "activity_external_refs": [
                messaging_boundary_ref,
                messaging_provenance_ref,
                notification_delivery_boundary_ref,
                recipient_boundary_ref,
                messaging_diagnostics_explainability_ref,
                household_memory_governance_boundary_ref,
                household_memory_ownership_consumption_boundary_ref,
                household_memory_identity_privacy_retention_separation_boundary_ref,
                household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary_ref,
                household_memory_provenance_diagnostics_explainability_boundary_ref,
                delivery_execution_success_ref,
            ],
        }

    return await _async_with_activity(
        hass,
        call,
        intent_class="push_person_message",
        request_summary=f"Person message sent to {profile.name or profile.person_id}",
        action_name="push_person_message",
        resolved_person_id=profile.person_id,
        resolved_area_id=profile.linked_area_id,
        channel="service_operational",
        external_refs=[
            {
                "ref_type": "message_delivery",
                "delivery_mode": delivery_mode,
                "target_id": target_id,
                "selected_service": service_ref,
                "routing_path": routing_path,
                "explicit_entity_target": explicit_entity_target,
            },
            notification_delivery_boundary_ref,
            recipient_boundary_ref,
            messaging_diagnostics_explainability_ref,
            household_memory_governance_boundary_ref,
            household_memory_ownership_consumption_boundary_ref,
            household_memory_identity_privacy_retention_separation_boundary_ref,
            household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary_ref,
            household_memory_provenance_diagnostics_explainability_boundary_ref,
            delivery_execution_attempt_ref,
        ],
        policy_gates=["recipient_consent_privacy_visibility_boundary"],
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
        SERVICE_RUN_SATELLITE_CAPTURE_POC,
        _bind(_async_handle_run_satellite_capture_poc),
        schema=SERVICE_RUN_SATELLITE_CAPTURE_POC_SCHEMA,
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
        SERVICE_COMPLETE_VOICE_ENROLLMENT,
        _bind(_async_handle_complete_voice_enrollment),
        schema=SERVICE_COMPLETE_VOICE_ENROLLMENT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_VOICE_ENROLLMENT_COMPLETION_READINESS,
        _bind(_async_handle_get_voice_enrollment_completion_readiness),
        schema=SERVICE_GET_VOICE_ENROLLMENT_COMPLETION_READINESS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CANCEL_VOICE_ENROLLMENT,
        _bind(_async_handle_cancel_voice_enrollment),
        schema=SERVICE_CANCEL_VOICE_ENROLLMENT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RECOVER_VOICE_ENROLLMENT,
        _bind(_async_handle_recover_voice_enrollment),
        schema=SERVICE_RECOVER_VOICE_ENROLLMENT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RESUME_VOICE_ENROLLMENT,
        _bind(_async_handle_resume_voice_enrollment),
        schema=SERVICE_RESUME_VOICE_ENROLLMENT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ABANDON_VOICE_ENROLLMENT,
        _bind(_async_handle_abandon_voice_enrollment),
        schema=SERVICE_ABANDON_VOICE_ENROLLMENT_SCHEMA,
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
        SERVICE_RUN_SATELLITE_CAPTURE_POC,
        SERVICE_REMOVE_VOICE_ENROLLMENT_SAMPLE,
        SERVICE_BUILD_VOICE_PROFILE,
        SERVICE_COMPLETE_VOICE_ENROLLMENT,
        SERVICE_GET_VOICE_ENROLLMENT_COMPLETION_READINESS,
        SERVICE_CANCEL_VOICE_ENROLLMENT,
        SERVICE_RECOVER_VOICE_ENROLLMENT,
        SERVICE_RESUME_VOICE_ENROLLMENT,
        SERVICE_ABANDON_VOICE_ENROLLMENT,
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
