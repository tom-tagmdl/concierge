"""Contract-first service handlers for Concierge orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
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
    CONF_VOICE_IDENTITY_LINKED,
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
from .identity_authorization_policy import (
    PolicyOutcome,
    evaluate_identity_authorization,
)
from .models import (
    ActivityEvent,
    ContinuityConfidenceBand,
    ContextState,
    ContinuityScope,
    IdentityProfile,
    UsualState,
    UsualStateBasis,
    Interaction,
    LearningOwnershipScope,
    LearningPolicyEvaluationOutcome,
    LearningPolicyEvaluationRequest,
    LearningWritePath,
    LearningWriteRequest,
    PreferenceIdentityState,
    PreferenceResolutionOutcome,
    PreferenceResolutionRequest,
    PreferenceResolutionTier,
    PersonProfile,
    SignalState,
)
from .repairs import (
    async_clear_person_context_issue,
    async_create_or_update_person_context_issue,
)
from .storage import ConciergeStorage
from .voice_identity_bridge import async_get_voice_identity_enrollment_status

_LOGGER = logging.getLogger(__name__)

_PROVIDER_NONE = "none"
_PROVIDER_ASSET_INTELLIGENCE = "asset_intelligence"
_PROVIDER_MUSIC_ASSISTANT = "music_assistant"
_TTS_DATA_COMPONENT = "tts"
_DEFAULT_TARGET_SAMPLE_COUNT = 3
_VOICE_IDENTITY_DOMAIN = "voice_identity"
_VOICE_IDENTITY_SERVICE_GET_IDENTITY_CONTEXT = "get_identity_context"
_VOICE_IDENTITY_NO_ACTIVE_ATTRIBUTION_STATES = {"unavailable", "unknown", "low_confidence"}
_IDENTITY_POLICY_SOURCE = "concierge.identity_authorization_classification.v1"

_IDENTITY_NOT_REQUIRED_INTENT_CLASSES = {
    "home_control",
    "room_context_info",
    "weather",
    "capability_inquiry",
}
_IDENTITY_OPTIONAL_INTENT_CLASSES = {
    "general_qna",
    "briefing",
    "household_status",
}
_IDENTITY_REQUIRED_INTENT_CLASSES = {
    "person_preference",
    "preferred_music",
    "personal_routine",
    "person_memory",
}
_IDENTITY_REQUIRED_FRESH_INTENT_CLASSES = {
    "calendar",
    "messages",
    "personal_schedule",
    "private_reminders",
}
_IDENTITY_REQUIRED_STEP_UP_INTENT_CLASSES = {
    "unlock",
    "disarm",
    "purchase",
    "admin_identity_profile_change",
}

_PRODUCTIVITY_SOURCE_BINDING_FIELDS = ["email", "calendar", "task", "shopping"]
_PRODUCTIVITY_SOURCE_OF_RECORD_DOMAIN_AUTHORITIES = {
    "calendar": {
        "source_of_record": "configured_calendar_provider",
        "configuration_reference_supported": True,
        "derived_context_only": False,
    },
    "email": {
        "source_of_record": "configured_email_provider",
        "configuration_reference_supported": True,
        "derived_context_only": False,
    },
    "task": {
        "source_of_record": "configured_task_provider",
        "configuration_reference_supported": True,
        "derived_context_only": True,
    },
    "shopping": {
        "source_of_record": "configured_shopping_provider",
        "configuration_reference_supported": True,
        "derived_context_only": False,
    },
    "capture": {
        "source_of_record": "configured_capture_provider",
        "configuration_reference_supported": True,
        "derived_context_only": False,
    },
    "knowledge": {
        "source_of_record": "configured_knowledge_provider",
        "configuration_reference_supported": True,
        "derived_context_only": False,
    },
    "briefing": {
        "source_of_record": "composed_briefing_projection",
        "configuration_reference_supported": False,
        "derived_context_only": True,
    },
    "household_status": {
        "source_of_record": "synthesized_household_status_projection",
        "configuration_reference_supported": False,
        "derived_context_only": True,
    },
}

TTS_PROVIDER_ENTITY_IDS = {
    "openai_conversation": "tts.openai_tts",
    "google_translate": "tts.google_translate_en_com",
}


def _normalize_source_binding_rows(value: Any, legacy_ref: Any = None) -> list[dict[str, str]]:
    """Normalize source-binding rows from service payloads with legacy fallback."""
    bindings: list[dict[str, str]] = []
    if isinstance(value, list):
        for item in value:
            if not isinstance(item, dict):
                continue
            entity_id = str(item.get("entity_id", "") or item.get("entityId", "") or "").strip()
            if not entity_id:
                continue
            label = str(item.get("label", "") or item.get("name", "") or "").strip()
            bindings.append(
                {
                    "label": label,
                    "entity_id": entity_id,
                }
            )

    legacy_value = str(legacy_ref or "").strip()
    if legacy_value and not bindings:
        bindings.append({"label": "", "entity_id": legacy_value})

    return bindings


SERVICE_EXECUTE_SCHEMA = vol.Schema(
    {
        vol.Required("target"): str,
        vol.Optional("area_id"): str,
        vol.Optional("composite_id"): str,
        vol.Optional("context"): dict,
        vol.Optional("conversation_id"): str,
        vol.Optional("device_id"): str,
        vol.Optional("satellite_id"): str,
        vol.Optional("agent_id"): str,
        vol.Optional("language"): str,
        vol.Optional("text"): str,
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
SERVICE_PUSH_PERSON_MESSAGE_SCHEMA = vol.Schema(
    {
        vol.Required("person_id"): str,
        vol.Required("message"): str,
        vol.Optional("title", default="Concierge"): str,
        vol.Optional("target_id"): str,
        vol.Optional("data", default={}): dict,
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
        vol.Optional("email_source_ref", default=""): str,
        vol.Optional("calendar_source_ref", default=""): str,
        vol.Optional("task_source_ref", default=""): str,
        vol.Optional("shopping_source_ref", default=""): str,
        vol.Optional("email_source_bindings", default=[]): list,
        vol.Optional("calendar_source_bindings", default=[]): list,
        vol.Optional("task_source_bindings", default=[]): list,
        vol.Optional("shopping_source_bindings", default=[]): list,
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
        vol.Optional("sample_items", default=[]): list,
        vol.Optional("attribution_confidence"): float,
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
        vol.Required("voice_profile_id"): str,
        vol.Optional("voice_name", default=""): str,
        vol.Optional("consent_acknowledged", default=False): bool,
        vol.Optional("local_only", default=True): bool,
        vol.Optional("capture_provider", default="browser"): str,
        vol.Optional("speech_text", default=""): str,
        vol.Optional("prompt_text", default=""): str,
    }
)

SERVICE_CAPTURE_VOICE_ENROLLMENT_SAMPLE_SCHEMA = vol.Schema(
    {
        vol.Required("voice_profile_id"): str,
        vol.Required("speech_text"): str,
        vol.Optional("capture_provider", default="browser"): str,
        vol.Optional("prompt_text", default=""): str,
        vol.Optional("person_id"): str,
        vol.Optional("source", default="guided_phrase"): str,
        vol.Optional("phrase_index"): int,
        vol.Optional("prompt_id", default=""): str,
        vol.Optional("prompt_order"): int,
        vol.Optional("prompt_category", default=""): str,
        vol.Optional("prompt_length_bucket", default=""): str,
        vol.Optional("capture_distance", default=""): str,
        vol.Optional("capture_noise", default=""): str,
        vol.Optional("quality_pass"): bool,
        vol.Optional("satellite_entity_id", default=""): str,
        vol.Optional("timeout_seconds", default=8.0): vol.Coerce(float),
    }
)

SERVICE_RUN_SATELLITE_CAPTURE_POC_SCHEMA = vol.Schema(
    {
        vol.Optional("person_id"): str,
        vol.Optional("voice_profile_id"): str,
        vol.Optional("capture_provider", default="satellite"): str,
        vol.Optional("prompt_text", default=""): str,
    }
)

SERVICE_REMOVE_VOICE_ENROLLMENT_SAMPLE_SCHEMA = vol.Schema(
    {
        vol.Required("voice_profile_id"): str,
        vol.Required("sample_id"): str,
        vol.Optional("person_id"): str,
    }
)

SERVICE_BUILD_VOICE_PROFILE_SCHEMA = vol.Schema(
    {
        vol.Required("voice_profile_id"): str,
        vol.Optional("person_id"): str,
        vol.Optional("min_samples", default=3): int,
    }
)

SERVICE_COMPLETE_VOICE_ENROLLMENT_SCHEMA = vol.Schema(
    {
        vol.Required("voice_profile_id"): str,
        vol.Optional("person_id"): str,
        vol.Optional("min_samples", default=3): int,
        vol.Optional("min_total_duration_ms", default=30000): int,
    }
)

SERVICE_GET_VOICE_ENROLLMENT_COMPLETION_READINESS_SCHEMA = vol.Schema(
    {
        vol.Optional("voice_profile_id"): str,
        vol.Optional("person_id"): str,
        vol.Optional("min_samples", default=3): int,
        vol.Optional("min_total_duration_ms", default=30000): int,
    }
)

SERVICE_CANCEL_VOICE_ENROLLMENT_SCHEMA = vol.Schema(
    {
        vol.Optional("voice_profile_id"): str,
        vol.Optional("person_id"): str,
    }
)

SERVICE_RECOVER_VOICE_ENROLLMENT_SCHEMA = vol.Schema(
    {
        vol.Optional("voice_profile_id"): str,
        vol.Optional("person_id"): str,
    }
)

SERVICE_RESUME_VOICE_ENROLLMENT_SCHEMA = vol.Schema(
    {
        vol.Optional("voice_profile_id"): str,
        vol.Optional("person_id"): str,
    }
)

SERVICE_ABANDON_VOICE_ENROLLMENT_SCHEMA = vol.Schema(
    {
        vol.Optional("voice_profile_id"): str,
        vol.Optional("person_id"): str,
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
        vol.Required("request_summary"): str,
        vol.Optional("resolved_person_id"): str,
        vol.Optional("resolved_area_id"): str,
        vol.Optional("confidence"): float,
        vol.Optional("external_refs", default=[]): list,
    }
)

SERVICE_CLOSE_ACTIVITY_OUTCOME_SCHEMA = vol.Schema(
    {
        vol.Required("activity_id"): str,
        vol.Required("ended_at"): str,
        vol.Required("outcome"): str,
        vol.Optional("outcome_reason", default=""): str,
        vol.Optional("actions_taken", default=[]): list,
        vol.Optional("policy_gates", default=[]): list,
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
        vol.Optional("destination"): str,
        vol.Optional("start"): str,
        vol.Optional("end"): str,
        vol.Optional("include_reference_excerpts", default=False): bool,
    }
)

SERVICE_RESOLVE_MOBILE_CONTEXT_SCHEMA = vol.Schema(
    {
        vol.Optional("person_id"): str,
        vol.Optional("mobile_target_id"): str,
    }
)

_MESSAGE_WEB_UI_TARGETS = {"web_ui", "persistent_notification", "dashboard", "kiosk"}
_MESSAGE_VOICE_ASSISTANT_TARGETS = {"assist_satellite", "satellite", "voice_assistant", "assistant"}
_MESSAGE_TTS_TARGETS = {"speaker", "speakers", "tts", "media_player"}
_MESSAGE_MOBILE_TARGET_PREFIXES = ("notify.",)
_LEARNING_POLICY_NAME = "experience_continuity_learning_governance_ec_b_03"
_LEARNING_POLICY_REASON_ALLOW = "learning_allowed"
_LEARNING_DENIAL_IDENTITY_REASONS = {
    PreferenceIdentityState.GUEST: "guest_identity_blocked",
    PreferenceIdentityState.UNKNOWN: "unknown_identity_blocked",
    PreferenceIdentityState.UNAVAILABLE: "unavailable_identity_blocked",
    PreferenceIdentityState.LOW_CONFIDENCE: "low_confidence_identity_blocked",
}
_LEARNING_SCOPE_STORAGE_TARGET = {
    LearningOwnershipScope.PERSON: "person_profile_learning",
    LearningOwnershipScope.ROOM: "room_config_learning",
    LearningOwnershipScope.HOUSEHOLD: "household_default_learning",
}
_USUAL_LIGHTING_POLICY_NAME = "experience_continuity_learned_lighting_ec_c_01"
_USUAL_LIGHTING_MEMBERSHIP_SOURCE = "room_configuration_membership"
_USUAL_LIGHTING_LEARNING_POLICY_FEATURE_KEY = "experience_continuity_lighting_learning_policy"
_USUAL_LIGHTING_DEFAULT_STABILITY_SECONDS = 30
_USUAL_LIGHTING_DEFAULT_BRIGHTNESS_PCT = 50
_USUAL_LIGHTING_VALIDATION_SOURCE = "configured_room_capability_mapping"
_USUAL_LIGHTING_UNAVAILABLE_STATES = {"unknown", "unavailable"}
_USUAL_LIGHTING_FALLBACK_POLICY_SOURCE = "experience_continuity_lighting_fallback_policy"
_USUAL_LIGHTING_COMMAND_ALIASES = {
    "turn on lamps": "lamps",
    "lamps on": "lamps",
    "turn on lights": "lights",
    "lights on": "lights",
    "resume lights": "resume",
    "usual lights": "usual",
    "lights usual": "usual",
}
_ROOM_AUDIO_POLICY_NAME = "experience_continuity_room_audio_memory_ec_d_01"
_ROOM_AUDIO_MEMBERSHIP_SOURCE = "room_configuration_speaker_membership"
_ROOM_AUDIO_LEARNING_POLICY_FEATURE_KEY = "experience_continuity_room_audio_learning_policy"
_ROOM_AUDIO_DEFAULT_STABILITY_SECONDS = 30
_ROOM_AUDIO_DEFAULT_VOLUME_PCT = 35
_ROOM_AUDIO_UNAVAILABLE_STATES = {"unknown", "unavailable"}
_ROOM_AUDIO_FALLBACK_POLICY_SOURCE = "experience_continuity_room_audio_fallback_policy"
_ROOM_AUDIO_CHANNELS = {"music", "duck", "tts"}
_ROOM_AUDIO_PLAYBACK_START_ALIASES = {
    "play music": "music_start",
    "start music": "music_start",
    "music on": "music_start",
}
_ROOM_MEDIA_PLAYBACK_GENERAL_ALIASES = {
    "play music",
    "start music",
    "music on",
    "play some music",
}
_ROOM_MEDIA_PLAYBACK_GENRE_HINTS = {
    "jazz",
    "classic rock",
    "rock",
    "smooth jazz",
    "pop",
    "classical",
    "country",
    "easy listening",
    "latin",
    "opera",
    "soundtrack",
    "musicals",
    "r and b",
    "r&b",
    "80s",
    "80's",
    "eighties",
}
_ROOM_MEDIA_REQUEST_KIND_HINTS = {"general_music", "genre", "artist", "album", "playlist"}
_ROOM_MEDIA_CONTINUATION_ALIASES = {
    "continue",
    "continue music",
    "continue playing",
    "continue what was playing",
    "continue in this room",
    "resume",
    "resume music",
    "resume playing",
    "resume what was playing",
    "resume in this room",
}
_ROOM_MEDIA_FOLLOW_ME_ALIASES = {
    "follow me music",
    "move music here",
    "bring music here",
    "move playback here",
    "follow me",
}
_MONITORING_FOLLOW_UP_CAPABILITY_ALIASES = {
    "what is the temperature": "temperature",
    "what is the room temperature": "temperature",
    "current temperature": "temperature",
    "how warm is it": "temperature",
    "temperature": "temperature",
    "what is the humidity": "humidity",
    "humidity": "humidity",
    "humidity level": "humidity",
    "moisture": "humidity",
    "what is the light level": "light",
    "light level": "light",
    "room brightness": "light",
    "how bright is it": "light",
    "brightness": "light",
    "what is the air quality": "air_quality",
    "air quality": "air_quality",
    "aqi": "air_quality",
    "environmental quality": "air_quality",
    "what is the noise level": "noise",
    "noise level": "noise",
    "sound level": "noise",
    "how noisy is it": "noise",
}
_IDENTITY_SELF_QUERY_ALIASES = {
    "who am i",
    "who's speaking",
    "who is speaking",
}
_MONITORING_CAPABILITY_FIELDS = {
    "temperature": ["room_sensor_entity_ids"],
    "humidity": ["room_sensor_entity_ids"],
    "light": ["room_sensor_entity_ids"],
    "air_quality": ["room_health_entity_ids", "human_health_entity_ids", "room_sensor_entity_ids"],
    "noise": ["room_sensor_entity_ids"],
}
_MONITORING_MEASUREMENT_KEYS = {
    "temperature": ["temperature", "current_temperature", "measured_temperature"],
    "humidity": ["humidity", "current_humidity"],
    "light": ["illuminance", "light_level", "lux", "brightness"],
    "air_quality": ["aqi", "air_quality_index", "pm2_5", "pm25"],
    "noise": ["noise_level", "sound_level", "sound_pressure", "db", "decibel"],
}
_REFUSAL_CATEGORY_BY_REASON = {
    "composite_configuration_missing": "authority_scope_missing",
    "room_scope_missing": "authority_scope_missing",
    "configured_capability_mapping_missing": "capability_unavailable",
    "configured_capability_measurement_unavailable": "capability_unavailable",
    "configured_room_authority_validation": "authority_scope_missing",
    "source_missing_or_configuration_incomplete": "configuration_unavailable",
    "source_unavailable_or_removed": "capability_unavailable",
    "media_provider_disabled": "configuration_unavailable",
    "music_assistant_unavailable": "capability_unavailable",
    "manual_stop_cooldown_active": "policy_denied",
    "manual_stop_active_follow_me": "policy_denied",
    "follow_me_disabled": "policy_denied",
    "identity_authority_insufficient": "policy_denied",
    "competing_identity_sources": "policy_denied",
    "room_transition_unavailable": "authority_scope_missing",
    "room_transition_ambiguous": "authority_scope_missing",
    "source_room_unavailable": "authority_scope_missing",
    "destination_room_unavailable": "authority_scope_missing",
    "no_room_change_detected": "authority_scope_missing",
    "merged_room_scope_not_supported": "policy_denied",
    "no_usable_room_media_context": "capability_unavailable",
    "recipient_not_eligible": "policy_denied",
    "consent_required_not_granted": "policy_denied",
    "delivery_target_blocked": "policy_denied",
    "delivery_channel_not_allowed": "policy_denied",
    "privacy_boundary_channel_restricted": "policy_denied",
    "visibility_boundary_channel_restricted": "policy_denied",
    "person_profile_not_configured": "configuration_unavailable",
    "person_profile_ambiguous": "configuration_unavailable",
    "productivity_bindings_missing": "configuration_unavailable",
    "presence_bindings_missing": "configuration_unavailable",
    "policy_context_missing": "policy_denied",
    "no_active_person_resolution": "policy_denied",
    "active_person_unavailable": "policy_denied",
}
_ROOM_MEDIA_CONTEXT_POLICY_NAME = "experience_continuity_room_media_context_ec_e_03"
_ROOM_MEDIA_CONTINUATION_POLICY_NAME = "experience_continuity_room_media_continuation_ec_e_02"
_ROOM_MEDIA_MANUAL_STOP_POLICY_SOURCE = "experience_continuity_manual_stop_cooldown_policy"
_SONOS_SPEECH_CONTINUITY_POLICY_NAME = "experience_continuity_sonos_speech_ec_d_02"
_SONOS_SPEECH_FALLBACK_POLICY_SOURCE = "experience_continuity_sonos_speech_fallback_policy"


def _classify_refusal_category(refusal_reason: str | None) -> str | None:
    """Map deterministic refusal reasons to a stable taxonomy category."""
    normalized_reason = str(refusal_reason or "").strip().lower() or None
    if normalized_reason is None:
        return None
    return _REFUSAL_CATEGORY_BY_REASON.get(normalized_reason, "capability_unavailable")


def _attach_refusal_explainability(
    payload: dict[str, Any],
    *,
    refusal_reason_key: str,
    capability_requested: str | None,
    capability_available: bool,
    capability_configured: bool,
    room_authority_source: str,
    merged_room_authority_source: str | None,
    person_policy_evaluated: bool,
) -> dict[str, Any]:
    """Attach deterministic refusal explainability fields required by #414."""
    refusal_reason = str(payload.get(refusal_reason_key) or "").strip() or None
    payload["refusal_reason"] = refusal_reason
    payload["refusal_category"] = _classify_refusal_category(refusal_reason)
    payload["room_authority_source"] = room_authority_source
    payload["merged_room_authority_source"] = merged_room_authority_source
    payload["capability_requested"] = capability_requested
    payload["capability_available"] = bool(capability_available)
    payload["capability_configured"] = bool(capability_configured)
    payload["person_policy_evaluated"] = bool(person_policy_evaluated)
    return payload


def _build_direct_refusal_message(
    refusal_reason: str | None,
    *,
    capability_requested: str | None,
) -> str | None:
    """Return deterministic direct-refusal language with no suggestion fallback."""
    normalized_reason = str(refusal_reason or "").strip().lower() or None
    if normalized_reason is None:
        return None

    refusal_messages = {
        "room_scope_missing": "I cannot complete that because no room is currently resolved.",
        "composite_configuration_missing": "I cannot complete that because this merged room is not configured.",
        "configured_capability_mapping_missing": "This room is not configured with that capability.",
        "configured_capability_measurement_unavailable": "That capability is configured, but readings are unavailable right now.",
        "configured_speaker_mapping_missing": "This room is not configured with speaker output for that capability.",
        "configured_room_authority_failure": "I cannot complete that because room authority validation failed.",
        "configured_room_authority_validation": "I cannot complete that because room authority validation failed.",
        "media_provider_disabled": "That capability is not currently enabled.",
        "music_assistant_unavailable": "That capability is not currently available.",
        "manual_stop_cooldown_active": "I cannot continue playback because manual-stop cooldown is active.",
        "manual_stop_active_follow_me": "I cannot move playback because manual-stop protection is active.",
        "follow_me_disabled": "I cannot move playback because Follow-Me is disabled.",
        "identity_authority_insufficient": "I cannot move playback because identity authority is insufficient.",
        "competing_identity_sources": "I cannot move playback because identity sources are conflicting.",
        "room_transition_unavailable": "I cannot move playback because a room transition was not resolved.",
        "room_transition_ambiguous": "I cannot move playback because the room transition is ambiguous.",
        "source_room_unavailable": "I cannot move playback because the source room is unavailable.",
        "destination_room_unavailable": "I cannot move playback because the destination room is unavailable.",
        "no_room_change_detected": "I cannot move playback because no room change was detected.",
        "merged_room_scope_not_supported": "I cannot move playback because Follow-Me does not override merged-room playback.",
        "no_usable_room_media_context": "I cannot continue playback because no usable room media context is available.",
        "recipient_not_eligible": "Message delivery is denied by recipient eligibility policy.",
        "consent_required_not_granted": "Message delivery is denied because required consent is not granted.",
        "delivery_target_blocked": "Message delivery is denied for the selected target.",
        "delivery_channel_not_allowed": "Message delivery is denied for the selected channel.",
        "privacy_boundary_channel_restricted": "Message delivery is denied by privacy boundary policy.",
        "visibility_boundary_channel_restricted": "Message delivery is denied by visibility boundary policy.",
        "person_profile_not_configured": "Person policy context is not configured for that request.",
        "productivity_bindings_missing": "Productivity capability is unavailable because required source bindings are missing.",
        "presence_bindings_missing": "Person presence context is unavailable for that request.",
        "policy_context_missing": "That request is denied because required policy context is missing.",
        "room_configuration_missing": "This room is not configured with that capability.",
        "configured_device_unavailable": "That configured capability is currently unavailable.",
        "configured_entity_invalid": "That configured capability mapping is invalid.",
        "unsupported_device_capability": "That capability is not currently supported.",
        "lighting_command_not_supported": "That capability is not currently supported.",
        "lighting_command_not_supported_by_configured_room_capability": "This room is not configured with that capability.",
        "no_eligible_lighting_targets": "This room is not configured with eligible targets for that capability.",
    }

    message = refusal_messages.get(normalized_reason)
    if message is not None:
        return message
    if capability_requested:
        return f"I cannot complete {capability_requested} because the capability is unavailable."
    return "That capability is not currently available."


def _normalize_identity_requirement_class_for_runtime(
    *,
    intent_class: str,
    requested_target: str,
    resolved_target: str,
) -> tuple[str, str]:
    """Classify identity requirement before execution with conservative defaults."""
    normalized_intent = str(intent_class or "home_control").strip().lower()
    normalized_tokens = {
        normalized_intent,
        str(requested_target or "").strip().lower(),
        str(resolved_target or "").strip().lower(),
    }
    normalized_text = " ".join(token for token in normalized_tokens if token)

    if normalized_intent in _IDENTITY_REQUIRED_STEP_UP_INTENT_CLASSES:
        return "identity_required_step_up", "intent_class_step_up"
    if normalized_intent in _IDENTITY_REQUIRED_FRESH_INTENT_CLASSES:
        return "identity_required_fresh", "intent_class_required_fresh"
    if normalized_intent in _IDENTITY_REQUIRED_INTENT_CLASSES:
        return "identity_required", "intent_class_required"
    if normalized_intent in _IDENTITY_OPTIONAL_INTENT_CLASSES:
        return "identity_optional", "intent_class_optional"
    if normalized_intent in _IDENTITY_NOT_REQUIRED_INTENT_CLASSES:
        return "identity_not_required", "intent_class_not_required"

    if any(token in normalized_text for token in ("unlock", "disarm", "purchase", "admin", "profile")):
        return "identity_required_step_up", "target_keyword_step_up"
    if any(token in normalized_text for token in ("calendar", "message", "schedule", "reminder")):
        return "identity_required_fresh", "target_keyword_required_fresh"
    if any(token in normalized_text for token in ("personal", "preference", "my_music", "preferred_music")):
        return "identity_required", "target_keyword_required"
    if any(token in normalized_text for token in ("weather", "light.", "scene.", "room", "capability")):
        return "identity_not_required", "target_keyword_not_required"

    return "identity_optional", "conservative_optional_default"


def _normalize_identity_state_for_policy(*, identity_state: str, requirement_class: str) -> str:
    """Map runtime identity states onto policy taxonomy without redefining Voice Identity authority."""
    if requirement_class == "identity_not_required":
        return "not_required"

    normalized = str(identity_state or "").strip().lower()
    if normalized in {"known", "unknown", "unavailable", "not_required", "ambiguous"}:
        return normalized
    if normalized in {"low_confidence", "no_match"}:
        return "ambiguous"
    return "unknown"


def _normalize_identity_freshness_for_policy(
    *,
    requirement_class: str,
    runtime_context: dict[str, Any],
    attribution_state: str,
) -> tuple[str, int]:
    """Resolve freshness class and attribution age from safe runtime attribution context."""
    runtime_attribution = runtime_context.get("voice_identity_runtime_attribution", {})
    runtime_attribution = dict(runtime_attribution) if isinstance(runtime_attribution, dict) else {}
    identity_context = runtime_context.get("identity_context", {})
    identity_context = dict(identity_context) if isinstance(identity_context, dict) else {}

    freshness = str(
        runtime_attribution.get("freshness")
        or identity_context.get("freshness")
        or identity_context.get("freshness_class")
        or ""
    ).strip().lower()

    attribution_age_ms_raw = runtime_attribution.get("attribution_age_ms")
    try:
        attribution_age_ms = int(attribution_age_ms_raw) if attribution_age_ms_raw is not None else -1
    except (TypeError, ValueError):
        attribution_age_ms = -1

    if freshness in {"fresh", "stale", "expired", "not_applicable"}:
        return freshness, attribution_age_ms

    if requirement_class == "identity_not_required":
        return "not_applicable", attribution_age_ms
    if requirement_class in {"identity_required_fresh", "identity_required_step_up"}:
        return "stale", attribution_age_ms
    if requirement_class == "identity_required" and attribution_state == "known":
        return "fresh", attribution_age_ms
    return "not_applicable", attribution_age_ms


def _identity_policy_response_message(*, policy_outcome: str, reason_code: str) -> str:
    """Return deterministic user-facing identity policy response text."""
    if reason_code in {"identity_required_but_missing", "identity_required_but_unknown"}:
        return "I can't do that until I know who is speaking."
    if reason_code == "identity_required_fresh_but_stale":
        return "I need to confirm who is speaking before I use personal information."
    if reason_code == "identity_optional_missing_continue_without_identity":
        return "I can continue without personalizing this."
    if reason_code == "identity_step_up_required":
        return "I need stronger confirmation before I can do that."
    if policy_outcome == "deny":
        return "I can't do that right now because identity authorization failed."
    if policy_outcome == "challenge":
        return "I need to confirm identity before I continue."
    if policy_outcome == "constrain":
        return "I can continue with a safer, non-personalized version of that request."
    return ""


def _evaluate_runtime_identity_authorization_policy(
    *,
    call: ServiceCall,
    requested_target: str,
    resolved_target: str,
    runtime_context: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate mandatory identity authorization policy for runtime execution gating."""
    requirement_class, classification_source = _normalize_identity_requirement_class_for_runtime(
        intent_class=str(call.data.get("intent_class", "home_control") or "home_control"),
        requested_target=requested_target,
        resolved_target=resolved_target,
    )

    identity_context = runtime_context.get("identity_context", {})
    identity_context = dict(identity_context) if isinstance(identity_context, dict) else {}
    identity_state = _normalize_identity_state_for_policy(
        identity_state=str(identity_context.get("state", "") or ""),
        requirement_class=requirement_class,
    )
    confidence_band = str(identity_context.get("confidence_band") or "none").strip().lower() or "none"
    if identity_state == "ambiguous" and confidence_band == "none":
        confidence_band = "low"

    freshness_class, attribution_age_ms = _normalize_identity_freshness_for_policy(
        requirement_class=requirement_class,
        runtime_context=runtime_context,
        attribution_state=identity_state,
    )

    decision = evaluate_identity_authorization(
        requirement=requirement_class,
        attribution_state=identity_state,
        confidence_band=confidence_band,
        freshness_class=freshness_class,
    )

    policy_outcome = decision.outcome.value
    policy_reason_code = str(decision.reason_code or "identity_context_missing").strip().lower()
    response_message = _identity_policy_response_message(
        policy_outcome=policy_outcome,
        reason_code=policy_reason_code,
    )

    return {
        "identity_requirement_class": requirement_class,
        "identity_policy_outcome": policy_outcome,
        "identity_policy_reason_code": policy_reason_code,
        "identity_policy_source": _IDENTITY_POLICY_SOURCE,
        "identity_freshness_class": str(decision.freshness_class.value),
        "attribution_age_ms": attribution_age_ms,
        "identity_state": str(decision.attribution_state.value),
        "confidence_band": str(decision.confidence_band),
        "classification_source": classification_source,
        "response_message": response_message,
        "allows_execution": policy_outcome
        in {
            PolicyOutcome.ALLOW.value,
            PolicyOutcome.CONSTRAIN.value,
            PolicyOutcome.CONTINUE_WITHOUT_IDENTITY.value,
        },
        "requires_challenge": policy_outcome == PolicyOutcome.CHALLENGE.value,
        "denied": policy_outcome == PolicyOutcome.DENY.value,
    }


def _build_execute_outcome_metadata(
    response: dict[str, Any],
    *,
    runtime_context: dict[str, Any] | None,
) -> dict[str, Any]:
    """Classify execute outcomes into execute/answer/refusal/silence success categories."""
    monitoring = dict(response.get("monitoring_follow_up") or {})
    identity_self_query = dict(response.get("identity_self_query") or {})
    identity_policy = dict(response.get("identity_authorization_policy") or {})
    media = dict(response.get("media_provider_resolution") or {})
    learned_lighting = dict(response.get("learned_usual_lighting") or {})
    room_audio = dict(response.get("room_audio_continuity") or {})

    refusal_reason = (
        str(monitoring.get("refusal_reason") or "").strip()
        or str(media.get("refusal_reason") or media.get("failure_reason") or "").strip()
        or str(learned_lighting.get("failure_reason") or "").strip()
        or str(room_audio.get("failure_reason") or "").strip()
        or None
    )
    policy_outcome = str(identity_policy.get("identity_policy_outcome") or "").strip().lower()
    policy_reason_code = str(identity_policy.get("identity_policy_reason_code") or "").strip().lower() or None
    if refusal_reason is None and policy_outcome in {"deny", "challenge"}:
        refusal_reason = policy_reason_code or (
            "identity_policy_deny" if policy_outcome == "deny" else "identity_policy_challenge"
        )

    refusal_category = (
        str(monitoring.get("refusal_category") or "").strip()
        or str(media.get("refusal_category") or "").strip()
        or _classify_refusal_category(refusal_reason)
    )
    if refusal_reason is not None and policy_outcome in {"deny", "challenge"}:
        refusal_category = "identity_authorization_policy"
    if not refusal_category:
        refusal_category = None

    generated_response_text = (
        str(response.get("response_message") or "").strip()
        or
        str(identity_self_query.get("generated_speech") or "").strip()
        or
        str(monitoring.get("generated_speech") or "").strip()
        or _build_direct_refusal_message(
            refusal_reason,
            capability_requested=(
                monitoring.get("capability_requested")
                or media.get("capability_requested")
                or learned_lighting.get("command_kind")
            ),
        )
        or None
    )

    response_generated = generated_response_text is not None
    response_required_hint = (runtime_context or {}).get("response_required")
    if isinstance(response_required_hint, bool):
        response_required = response_required_hint
    else:
        response_required = bool(response_generated or refusal_reason)

    if refusal_reason is not None:
        execution_outcome_category = "REFUSAL_SUCCESS"
        silence_as_success = False
        response_required = True
    elif response_generated:
        execution_outcome_category = "ANSWER_SUCCESS"
        silence_as_success = False
        response_required = True
    elif bool(response.get("executed", False)):
        if response_required:
            execution_outcome_category = "EXECUTE_SUCCESS"
            silence_as_success = False
        else:
            execution_outcome_category = "SILENCE_SUCCESS"
            silence_as_success = True
    else:
        execution_outcome_category = "EXECUTE_SUCCESS"
        silence_as_success = False

    room_authority_source = (
        str(monitoring.get("room_authority_source") or "").strip()
        or str(media.get("room_authority_source") or "").strip()
        or str(learned_lighting.get("room_source") or "").strip()
        or "room_configuration"
    )
    merged_room_authority_source = (
        str(monitoring.get("merged_room_authority_source") or "").strip()
        or str(media.get("merged_room_authority_source") or "").strip()
        or None
    )
    person_policy_evaluated = bool(
        monitoring.get("person_policy_evaluated")
        or media.get("person_policy_evaluated")
        or False
    )

    return {
        "execution_outcome_category": execution_outcome_category,
        "silence_as_success": bool(silence_as_success),
        "response_required": bool(response_required),
        "response_generated": bool(response_generated),
        "response_message": generated_response_text,
        "refusal_reason": refusal_reason,
        "refusal_category": refusal_category,
        "room_authority_source": room_authority_source,
        "person_policy_evaluated": person_policy_evaluated,
        "merged_room_authority_source": merged_room_authority_source,
    }


def _normalize_message_target(target: str | None) -> str:
    """Normalize a message target to a stable lower-case routing token."""
    return str(target or "").strip().lower()


def _room_entity_ids(room, field_name: str) -> list[str]:
    """Return a room entity list filtered to non-empty string identifiers."""
    values = getattr(room, field_name, []) if room is not None else []
    return [entity_id for entity_id in values if isinstance(entity_id, str) and entity_id]


def _normalize_spoken_command_phrase(value: str | None) -> str:
    """Normalize a spoken command phrase for deterministic matching."""
    return " ".join(str(value or "").strip().lower().split())


def _classify_usual_lighting_command(target: str | None) -> str | None:
    """Classify supported EC-C-01 usual lighting command phrases."""
    if target is None:
        return None
    normalized = _normalize_spoken_command_phrase(target)
    if "." in normalized:
        return None
    return _USUAL_LIGHTING_COMMAND_ALIASES.get(normalized)


def _classify_room_audio_playback_start_command(target: str | None) -> str | None:
    """Classify supported EC-D-01 room-audio playback-start command phrases."""
    if target is None:
        return None
    normalized = _normalize_spoken_command_phrase(target)
    if "." in normalized:
        return None
    return _ROOM_AUDIO_PLAYBACK_START_ALIASES.get(normalized)


def _classify_room_media_playback_request(target: str | None) -> dict[str, Any] | None:
    """Classify governed EC-E-01 media playback requests."""
    if target is None:
        return None

    raw = str(target or "").strip()
    normalized = _normalize_spoken_command_phrase(raw)
    if not normalized or "." in normalized:
        return None

    if normalized in _ROOM_MEDIA_PLAYBACK_GENERAL_ALIASES:
        return {
            "request_kind": "general_music",
            "media_query": "music",
            "request_text": raw,
        }

    if normalized.startswith("play "):
        raw_query = raw[5:].strip()
        normalized_query = normalized[5:].strip()
        if not raw_query:
            return None
        request_kind = "genre" if normalized_query in _ROOM_MEDIA_PLAYBACK_GENRE_HINTS else "named_music"
        return {
            "request_kind": request_kind,
            "media_query": raw_query,
            "request_text": raw,
        }

    return None


def _classify_room_media_continuation_request(target: str | None) -> dict[str, Any] | None:
    """Classify governed EC-E-02 room-level continue/resume requests."""
    if target is None:
        return None

    raw = str(target or "").strip()
    normalized = _normalize_spoken_command_phrase(raw)
    if not normalized or "." in normalized:
        return None

    if normalized in _ROOM_MEDIA_CONTINUATION_ALIASES or normalized.startswith("continue ") or normalized.startswith("resume "):
        return {
            "request_kind": "continue_resume",
            "request_text": raw,
        }

    return None


def _classify_room_media_follow_me_request(target: str | None) -> dict[str, Any] | None:
    """Classify explicit Follow-Me media requests for EC-REQ-044."""
    if target is None:
        return None

    raw = str(target or "").strip()
    normalized = _normalize_spoken_command_phrase(raw)
    if not normalized or "." in normalized:
        return None

    if normalized in _ROOM_MEDIA_FOLLOW_ME_ALIASES:
        return {
            "request_kind": "follow_me",
            "request_text": raw,
        }

    return None


def _resolve_follow_me_media_decision(
    *,
    runtime_context: dict[str, Any],
    request_explicit: bool,
    area_id: str | None,
    composite_id: str | None,
    room_media_context: dict[str, Any] | None,
) -> dict[str, Any]:
    """Resolve deterministic Follow-Me eligibility and explainability without changing ownership boundaries."""
    transition = runtime_context.get("room_transition")
    transition = dict(transition) if isinstance(transition, dict) else {}
    identity_context = runtime_context.get("identity_context")
    identity_context = dict(identity_context) if isinstance(identity_context, dict) else {}

    source_room = (
        str(transition.get("source_room_id") or "").strip()
        or str((room_media_context or {}).get("source_room_id") or "").strip()
        or None
    )
    destination_room = (
        str(transition.get("destination_room_id") or "").strip()
        or str(area_id or "").strip()
        or None
    )
    transition_source = (
        str(transition.get("source") or "").strip()
        or str(runtime_context.get("room_transition_source") or "").strip()
        or "runtime_context"
    )

    follow_me_enabled = bool(runtime_context.get("follow_me_enabled", False))
    transition_candidate = bool(source_room and destination_room and source_room != destination_room)
    follow_me_candidate = bool(request_explicit or transition_candidate)

    identity_state, confidence_band = _resolve_media_identity_state(runtime_context)
    confidence_value = str(confidence_band.value if confidence_band is not None else "unknown").strip().lower()
    identity_allowed = identity_state is PreferenceIdentityState.KNOWN and confidence_value not in {
        "low",
        "unknown",
        "unavailable",
        "ambiguous",
        "no_match",
    }

    competing_identity_sources = bool(
        runtime_context.get("identity_competing", False)
        or identity_context.get("multiple_matches", False)
        or (isinstance(identity_context.get("candidate_person_ids"), list) and len(identity_context.get("candidate_person_ids")) > 1)
    )
    transition_ambiguous = bool(
        transition.get("ambiguous", False)
        or transition.get("overlap", False)
        or transition.get("boundary_ambiguous", False)
    )

    media_context_payload = dict((room_media_context or {}).get("room_media_context") or {})
    manual_stop_blocked = bool(media_context_payload.get("manual_stop", False))
    cooldown_blocked = bool((room_media_context or {}).get("manual_stop_cooldown_active", False))

    follow_me_allowed = False
    follow_me_reason = "follow_me_not_requested"
    follow_me_decision = "no_handoff"

    if not follow_me_enabled:
        follow_me_reason = "follow_me_disabled"
    elif composite_id is not None:
        follow_me_reason = "merged_room_scope_not_supported"
    elif not follow_me_candidate:
        follow_me_reason = "follow_me_not_requested"
    elif source_room is None:
        follow_me_reason = "source_room_unavailable"
    elif destination_room is None:
        follow_me_reason = "destination_room_unavailable"
    elif source_room == destination_room:
        follow_me_reason = "no_room_change_detected"
    elif transition_ambiguous:
        follow_me_reason = "room_transition_ambiguous"
    elif competing_identity_sources:
        follow_me_reason = "competing_identity_sources"
    elif not identity_allowed:
        follow_me_reason = "identity_authority_insufficient"
    elif manual_stop_blocked:
        follow_me_reason = "manual_stop_active_follow_me"
    elif cooldown_blocked:
        follow_me_reason = "manual_stop_cooldown_active"
    else:
        follow_me_allowed = True
        follow_me_reason = "handoff_allowed"
        follow_me_decision = "handoff_execute"

    return {
        "follow_me_enabled": follow_me_enabled,
        "follow_me_candidate": follow_me_candidate,
        "follow_me_allowed": follow_me_allowed,
        "follow_me_decision": follow_me_decision,
        "follow_me_reason": follow_me_reason,
        "identity_authority_source": "voice_identity_runtime_context",
        "room_transition_source": transition_source,
        "cooldown_blocked": cooldown_blocked,
        "manual_stop_blocked": manual_stop_blocked,
        "destination_room": destination_room,
        "source_room": source_room,
        "identity_state": identity_state.value,
        "identity_confidence_band": confidence_value,
        "competing_identity_sources": competing_identity_sources,
        "room_transition_ambiguous": transition_ambiguous,
        "request_explicit": bool(request_explicit),
    }


def _classify_monitoring_follow_up_request(target: str | None) -> dict[str, Any] | None:
    """Classify room monitoring follow-up questions for EC-F-02 configuration-bounded handling."""
    if target is None:
        return None

    raw = str(target or "").strip()
    normalized = _normalize_spoken_command_phrase(raw).rstrip("?!. ")
    if not normalized or "." in normalized:
        return None

    capability = _MONITORING_FOLLOW_UP_CAPABILITY_ALIASES.get(normalized)
    if capability is None:
        return None

    return {
        "request_kind": "monitoring_follow_up",
        "request_text": raw,
        "monitoring_capability": capability,
    }


def _classify_identity_self_query_request(target: str | None) -> dict[str, Any] | None:
    """Classify deterministic identity self-query prompts (for example, 'who am I')."""
    if target is None:
        return None

    raw = str(target or "").strip()
    normalized = _normalize_spoken_command_phrase(raw).rstrip("?!. ")
    if not normalized or "." in normalized:
        return None

    if normalized not in _IDENTITY_SELF_QUERY_ALIASES:
        return None

    return {
        "request_kind": "identity_self_query",
        "request_text": raw,
    }


def _build_identity_self_query_response(
    *,
    state,
    execution_envelope: dict[str, Any],
) -> dict[str, Any]:
    """Build deterministic response text for identity self-query prompts."""
    active_person_resolution = dict(execution_envelope.get("active_person_resolution", {}))
    runtime_person_context = dict(execution_envelope.get("runtime_person_context", {}))

    active_person_state = str(
        active_person_resolution.get("active_person_state", "active_person_unavailable")
        or "active_person_unavailable"
    ).strip().lower()
    reason_code = str(
        active_person_resolution.get("reason_code", "identity_unknown")
        or "identity_unknown"
    ).strip().lower()

    resolved_person_id = str(
        runtime_person_context.get("resolved_concierge_person_profile_id")
        or active_person_resolution.get("resolved_person_id")
        or ""
    ).strip() or None
    resolved_voice_profile_id = str(
        runtime_person_context.get("resolved_voice_profile_id")
        or active_person_resolution.get("resolved_voice_profile_id")
        or ""
    ).strip() or None

    person_profile = (
        state.person_profiles.get(resolved_person_id)
        if resolved_person_id is not None
        else None
    )
    resolved_name = str(getattr(person_profile, "name", "") or "").strip()

    if active_person_state == "active_person_available" and resolved_name:
        generated_speech = f"Hi {resolved_name}, how can I help you today?"
    elif active_person_state == "active_person_available":
        generated_speech = "Hi there, how can I help you today?"
    elif active_person_state == "active_person_ambiguous":
        if reason_code == "ambiguous_match":
            generated_speech = "I would greet you by name but Voice Identity reported an ambiguous match."
        else:
            generated_speech = "I would greet you by name but Voice Identity reported low confidence."
    elif active_person_state == "active_person_unavailable":
        generated_speech = "I would greet you by name but Voice Identity was unavailable or not ready."
    elif active_person_state == "active_person_unknown":
        generated_speech = "I would greet you by name but active person is unknown."
    else:
        generated_speech = "I'm not sure who is speaking."

    return {
        "request_kind": "identity_self_query",
        "generated_speech": generated_speech,
        "active_person_state": active_person_state,
        "active_person_reason_code": reason_code,
        "resolved_person_id": resolved_person_id,
        "resolved_voice_profile_id": resolved_voice_profile_id,
    }


def _resolve_monitoring_rooms(
    state: Any,
    *,
    area_id: str | None,
    composite_id: str | None,
) -> tuple[list[str], Any | None]:
    """Resolve deterministic room participation order for monitoring authority consumption."""
    if composite_id:
        composite = getattr(state, "composites", {}).get(composite_id)
        if composite is None:
            return [], None

        configured_rooms = list(dict.fromkeys(list(getattr(composite, "area_ids", []) or [])))
        if not configured_rooms and getattr(composite, "primary_area", None):
            configured_rooms = [str(composite.primary_area)]

        ordered: list[str] = []
        primary_area = str(getattr(composite, "primary_area", "") or "").strip()
        if primary_area and primary_area in configured_rooms:
            ordered.append(primary_area)
        if area_id and area_id in configured_rooms and area_id not in ordered:
            ordered.append(area_id)
        for room_area_id in configured_rooms:
            if room_area_id not in ordered:
                ordered.append(room_area_id)

        return ordered, composite

    if area_id:
        return [area_id], None

    return [], None


def _configured_monitoring_membership(room: Any, capability: str) -> dict[str, Any]:
    """Resolve configured monitoring entity membership for one capability from room configuration."""
    fields = list(_MONITORING_CAPABILITY_FIELDS.get(capability, []))
    configured_membership: list[str] = []
    for field_name in fields:
        configured_membership.extend(_room_entity_ids(room, field_name))
    configured_membership = list(dict.fromkeys(configured_membership))
    return {
        "capability": capability,
        "mapping_fields": fields,
        "configured_membership": configured_membership,
    }


def _validate_configured_monitoring_entities(
    hass: HomeAssistant,
    configured_membership: list[str],
) -> tuple[list[str], list[dict[str, Any]]]:
    """Validate configured monitoring entities without expanding room capability ownership."""
    registry = er.async_get(hass)
    valid_targets: list[str] = []
    validations: list[dict[str, Any]] = []

    for entity_id in configured_membership:
        normalized = str(entity_id or "").strip()
        if not normalized or "." not in normalized:
            validations.append(
                {
                    "entity_id": normalized,
                    "valid": False,
                    "status": "invalid_entity",
                    "reason": "configured_entity_invalid",
                }
            )
            continue

        state_obj = hass.states.get(normalized)
        registry_entry = registry.async_get(normalized)
        if state_obj is None and registry_entry is None:
            validations.append(
                {
                    "entity_id": normalized,
                    "valid": False,
                    "status": "missing_entity",
                    "reason": "configured_entity_missing",
                }
            )
            continue

        if state_obj is None:
            validations.append(
                {
                    "entity_id": normalized,
                    "valid": False,
                    "status": "missing_state",
                    "reason": "configured_entity_missing",
                }
            )
            continue

        state_value = str(getattr(state_obj, "state", "") or "").strip().lower()
        if state_value in _USUAL_LIGHTING_UNAVAILABLE_STATES:
            validations.append(
                {
                    "entity_id": normalized,
                    "valid": False,
                    "status": "unavailable_entity",
                    "reason": "configured_device_unavailable",
                }
            )
            continue

        valid_targets.append(normalized)
        validations.append(
            {
                "entity_id": normalized,
                "valid": True,
                "status": "validated",
                "reason": "configured_entity_valid",
            }
        )

    return valid_targets, validations


def _extract_monitoring_measurement(entity_state: Any, capability: str) -> dict[str, Any] | None:
    """Extract one monitoring measurement from a configured entity state."""
    if entity_state is None:
        return None

    attributes = getattr(entity_state, "attributes", {}) or {}
    if not isinstance(attributes, dict):
        attributes = {}

    measurement_keys = list(_MONITORING_MEASUREMENT_KEYS.get(capability, []))
    for key in measurement_keys:
        value = _coerce_float(attributes.get(key))
        if value is None:
            continue
        return {
            "value": value,
            "unit": attributes.get("unit_of_measurement"),
            "attribute_key": key,
            "state": str(getattr(entity_state, "state", "") or ""),
        }

    state_value = _coerce_float(getattr(entity_state, "state", None))
    if state_value is not None:
        unit = str(attributes.get("unit_of_measurement") or "").strip().lower()
        compatible_units = {
            "temperature": {"f", "c", "\u00b0f", "\u00b0c", "fahrenheit", "celsius", "degrees"},
            "humidity": {"%", "percent", "percentage"},
            "light": {"lux", "lx"},
            "air_quality": {"aqi", "pm2.5", "pm10"},
            "noise": {"db", "dba", "decibel", "decibels"},
        }
        capability_units = compatible_units.get(capability, set())
        if capability == "temperature" and not unit:
            unit = "degrees"
        if not capability_units or unit in capability_units:
            return {
                "value": state_value,
                "unit": attributes.get("unit_of_measurement") or unit,
                "attribute_key": "state",
                "state": str(getattr(entity_state, "state", "") or ""),
            }

    return None


def _monitoring_value_label(capability: str) -> str:
    return {
        "temperature": "temperature",
        "humidity": "humidity",
        "light": "light level",
        "air_quality": "air quality",
        "noise": "noise level",
    }.get(capability, capability.replace("_", " "))


def _format_monitoring_value(measurement: dict[str, Any], capability: str) -> str:
    value = measurement.get("value")
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    unit = str(measurement.get("unit") or "").strip()
    if not unit:
        unit = {
            "temperature": "degrees",
            "humidity": "%",
            "light": "lux",
            "air_quality": "AQI",
            "noise": "dB",
        }.get(capability, "")
    return f"{value} {unit}".strip()


def _build_monitoring_follow_up_resolution(
    hass: HomeAssistant,
    *,
    state: Any,
    area_id: str | None,
    composite_id: str | None,
    monitoring_capability: str,
    room_authority_traceability: dict[str, Any],
) -> dict[str, Any]:
    """Resolve monitoring follow-up answers from configured room capability mappings only."""
    participating_rooms, composite = _resolve_monitoring_rooms(
        state,
        area_id=area_id,
        composite_id=composite_id,
    )

    merged_room_authority_source = room_authority_traceability.get("merged_room_authority_source")
    if composite_id and composite is None:
        return _attach_refusal_explainability({
            "handled": True,
            "executed": False,
            "monitoring_capability": monitoring_capability,
            "configured_capability_mapping": {
                "mapping_source": "room_configuration",
                "mapping_fields": list(_MONITORING_CAPABILITY_FIELDS.get(monitoring_capability, [])),
                "configured_device_set": [],
                "participating_rooms": [],
                "room_mappings": [],
            },
            "resolved_monitoring_device": None,
            "resolution_strategy": "configured_priority_first_valid_measurement",
            "resolution_priority": [],
            "refusal_reason": "composite_configuration_missing",
            "room_authority_source": room_authority_traceability.get("room_authority_source", "room_configuration"),
            "merged_room_authority_source": merged_room_authority_source,
            "runtime_discovery_reliance": "validation_only",
            "generated_speech": "I cannot answer that yet because this merged room configuration is unavailable.",
        },
            refusal_reason_key="refusal_reason",
            capability_requested=monitoring_capability,
            capability_available=False,
            capability_configured=False,
            room_authority_source=room_authority_traceability.get("room_authority_source", "room_configuration"),
            merged_room_authority_source=merged_room_authority_source,
            person_policy_evaluated=False,
        )

    if not participating_rooms:
        return _attach_refusal_explainability({
            "handled": True,
            "executed": False,
            "monitoring_capability": monitoring_capability,
            "configured_capability_mapping": {
                "mapping_source": "room_configuration",
                "mapping_fields": list(_MONITORING_CAPABILITY_FIELDS.get(monitoring_capability, [])),
                "configured_device_set": [],
                "participating_rooms": [],
                "room_mappings": [],
            },
            "resolved_monitoring_device": None,
            "resolution_strategy": "configured_priority_first_valid_measurement",
            "resolution_priority": [],
            "refusal_reason": "room_scope_missing",
            "room_authority_source": room_authority_traceability.get("room_authority_source", "room_configuration"),
            "merged_room_authority_source": merged_room_authority_source,
            "runtime_discovery_reliance": "validation_only",
            "generated_speech": "I cannot answer that yet because no room is currently resolved.",
        },
            refusal_reason_key="refusal_reason",
            capability_requested=monitoring_capability,
            capability_available=False,
            capability_configured=False,
            room_authority_source=room_authority_traceability.get("room_authority_source", "room_configuration"),
            merged_room_authority_source=merged_room_authority_source,
            person_policy_evaluated=False,
        )

    room_mappings: list[dict[str, Any]] = []
    configured_candidates: list[str] = []

    if composite is not None:
        composite_membership = _configured_monitoring_membership(composite, monitoring_capability)
        if composite_membership["configured_membership"]:
            configured_candidates.extend(composite_membership["configured_membership"])
            room_mappings.append(
                {
                    "area_id": None,
                    "mapping_scope": "composite",
                    "mapping_ref": str(getattr(composite, "composite_id", "") or ""),
                    "mapping_fields": list(composite_membership["mapping_fields"]),
                    "configured_device_set": list(composite_membership["configured_membership"]),
                }
            )

    for room_area_id in participating_rooms:
        room = getattr(state, "rooms", {}).get(room_area_id)
        membership = _configured_monitoring_membership(room, monitoring_capability)
        room_mappings.append(
            {
                "area_id": room_area_id,
                "mapping_scope": "room",
                "mapping_ref": room_area_id,
                "mapping_fields": list(membership["mapping_fields"]),
                "configured_device_set": list(membership["configured_membership"]),
            }
        )
        configured_candidates.extend(membership["configured_membership"])

    configured_candidates = list(dict.fromkeys(configured_candidates))
    if not configured_candidates:
        return _attach_refusal_explainability({
            "handled": True,
            "executed": False,
            "monitoring_capability": monitoring_capability,
            "configured_capability_mapping": {
                "mapping_source": "room_configuration",
                "mapping_fields": list(_MONITORING_CAPABILITY_FIELDS.get(monitoring_capability, [])),
                "configured_device_set": [],
                "participating_rooms": participating_rooms,
                "room_mappings": room_mappings,
            },
            "resolved_monitoring_device": None,
            "resolution_strategy": "configured_priority_first_valid_measurement",
            "resolution_priority": [],
            "refusal_reason": "configured_capability_mapping_missing",
            "room_authority_source": room_authority_traceability.get("room_authority_source", "room_configuration"),
            "merged_room_authority_source": merged_room_authority_source,
            "runtime_discovery_reliance": "validation_only",
            "generated_speech": f"I do not have { _monitoring_value_label(monitoring_capability) } configured for this room yet.",
        },
            refusal_reason_key="refusal_reason",
            capability_requested=monitoring_capability,
            capability_available=False,
            capability_configured=False,
            room_authority_source=room_authority_traceability.get("room_authority_source", "room_configuration"),
            merged_room_authority_source=merged_room_authority_source,
            person_policy_evaluated=False,
        )

    valid_entities, validation_results = _validate_configured_monitoring_entities(hass, configured_candidates)
    capability_measurements: dict[str, dict[str, Any]] = {}
    for entity_id in valid_entities:
        measurement = _extract_monitoring_measurement(hass.states.get(entity_id), monitoring_capability)
        if measurement is not None:
            capability_measurements[entity_id] = measurement

    capability_priority = [
        entity_id
        for entity_id in configured_candidates
        if entity_id in capability_measurements
    ]

    resolved_device: str | None = capability_priority[0] if capability_priority else None
    resolved_measurement: dict[str, Any] | None = (
        capability_measurements.get(resolved_device)
        if resolved_device is not None
        else None
    )

    refusal_reason: str | None = None
    generated_speech: str
    if resolved_device is None or resolved_measurement is None:
        refusal_reason = "configured_capability_measurement_unavailable"
        generated_speech = (
            f"I found configured devices for { _monitoring_value_label(monitoring_capability) }, "
            "but they are not reporting usable readings right now."
        )
    else:
        rendered_value = _format_monitoring_value(resolved_measurement, monitoring_capability)
        generated_speech = (
            f"The room { _monitoring_value_label(monitoring_capability) } is {rendered_value} "
            f"from {resolved_device}."
        )

    return _attach_refusal_explainability({
        "handled": True,
        "executed": False,
        "monitoring_capability": monitoring_capability,
        "configured_capability_mapping": {
            "mapping_source": "room_configuration",
            "mapping_fields": list(_MONITORING_CAPABILITY_FIELDS.get(monitoring_capability, [])),
            "configured_device_set": capability_priority,
            "participating_rooms": participating_rooms,
            "room_mappings": room_mappings,
        },
        "resolved_monitoring_device": resolved_device,
        "resolved_measurement": resolved_measurement,
        "resolution_strategy": "configured_priority_first_valid_measurement",
        "resolution_priority": capability_priority,
        "validation_results": validation_results,
        "refusal_reason": refusal_reason,
        "room_authority_source": room_authority_traceability.get("room_authority_source", "room_configuration"),
        "merged_room_authority_source": merged_room_authority_source,
        "runtime_discovery_reliance": "validation_only",
        "generated_speech": generated_speech,
    },
        refusal_reason_key="refusal_reason",
        capability_requested=monitoring_capability,
        capability_available=resolved_device is not None and resolved_measurement is not None,
        capability_configured=bool(configured_candidates),
        room_authority_source=room_authority_traceability.get("room_authority_source", "room_configuration"),
        merged_room_authority_source=merged_room_authority_source,
        person_policy_evaluated=False,
    )


def _build_monitoring_follow_up_summary(
    hass: HomeAssistant,
    *,
    state: Any,
    assembled_context: dict[str, Any],
    room_authority_traceability: dict[str, Any],
) -> dict[str, Any]:
    """Build room monitoring follow-up traceability snapshot for summary diagnostics."""
    monitoring: dict[str, Any] = {}
    for monitoring_capability in ("temperature", "humidity", "light", "air_quality", "noise"):
        monitoring[monitoring_capability] = _build_monitoring_follow_up_resolution(
            hass,
            state=state,
            area_id=assembled_context.get("context_area_id"),
            composite_id=assembled_context.get("resolved_composite_id"),
            monitoring_capability=monitoring_capability,
            room_authority_traceability=room_authority_traceability,
        )

    return {
        "mapping_authority": "room_configuration",
        "runtime_discovery_reliance": "validation_only",
        "capabilities": monitoring,
    }


def _room_media_state_id(*, area_id: str) -> str:
    """Build a stable room-media continuity state identifier."""
    return f"room_media::{area_id}"


def _resolve_room_media_source_rooms(
    state: Any,
    *,
    area_id: str | None,
    composite_id: str | None,
) -> list[str]:
    """Return deterministic candidate source rooms for room-level media continuity."""
    if composite_id:
        composite = getattr(state, "composites", {}).get(composite_id)
        if composite is None:
            return []
        participating_rooms = list(dict.fromkeys(list(getattr(composite, "area_ids", []) or [])))
        if not participating_rooms and getattr(composite, "primary_area", None):
            participating_rooms = [str(composite.primary_area)]
        prioritized: list[str] = []
        primary_area = str(getattr(composite, "primary_area", "") or "").strip()
        if primary_area and primary_area in participating_rooms:
            prioritized.append(primary_area)
        if area_id and area_id in participating_rooms and area_id not in prioritized:
            prioritized.append(area_id)
        for room_area_id in sorted(participating_rooms):
            if room_area_id not in prioritized:
                prioritized.append(room_area_id)
        return prioritized

    if area_id:
        return [area_id]

    return []


def _resolve_room_media_context(state: Any, *, area_id: str | None, composite_id: str | None) -> dict[str, Any]:
    """Resolve room-level media continuity context using deterministic room authority."""
    candidate_rooms = _resolve_room_media_source_rooms(state, area_id=area_id, composite_id=composite_id)
    room_media_state = None
    source_room_id: str | None = None
    source_room_selection_reason = "room_media_context_missing"

    for index, candidate_room_id in enumerate(candidate_rooms):
        state_id = _room_media_state_id(area_id=candidate_room_id)
        candidate_state = None
        if state is not None and hasattr(state, "usual_states"):
            candidate_state = state.usual_states.get(state_id)
        if candidate_state is None:
            continue
        room_media_state = candidate_state
        source_room_id = candidate_room_id
        if composite_id and candidate_room_id == area_id:
            source_room_selection_reason = "initiating_room_selected"
        elif composite_id and index == 0:
            source_room_selection_reason = "primary_room_selected"
        elif area_id and candidate_room_id == area_id:
            source_room_selection_reason = "requested_room_selected"
        else:
            source_room_selection_reason = "deterministic_room_priority_selected"
        break

    if room_media_state is None:
        return {
            "source_room_id": None,
            "source_room_selection_reason": source_room_selection_reason,
            "source_room_candidates": candidate_rooms,
            "room_media_state": None,
            "room_media_context": None,
            "manual_stop_cooldown_active": False,
            "manual_stop_cooldown_reason": None,
        }

    values = dict(getattr(room_media_state, "values", {}) or {})
    metadata = dict(getattr(room_media_state, "metadata", {}) or {})
    last_media = values.get("last_media") if isinstance(values.get("last_media"), dict) else {}
    if not isinstance(last_media, dict):
        last_media = {}

    cooldown_until = str(
        values.get("manual_stop_cooldown_until")
        or metadata.get("manual_stop_cooldown_until")
        or ""
    ).strip()
    cooldown_seconds = values.get("manual_stop_cooldown_seconds", metadata.get("manual_stop_cooldown_seconds"))
    manual_stop_marked = bool(values.get("manual_stop", metadata.get("manual_stop", False)))
    now = datetime.now(timezone.utc)
    cooldown_active = False
    cooldown_reason = None
    if cooldown_until:
        try:
            cooldown_dt = datetime.fromisoformat(cooldown_until.replace("Z", "+00:00"))
            if cooldown_dt.tzinfo is None:
                cooldown_dt = cooldown_dt.replace(tzinfo=timezone.utc)
            cooldown_active = cooldown_dt > now
        except ValueError:
            cooldown_active = False
    elif manual_stop_marked and isinstance(cooldown_seconds, (int, float)):
        try:
            cooldown_window = max(0, int(cooldown_seconds))
        except (TypeError, ValueError):
            cooldown_window = 0
        if cooldown_window > 0:
            cooldown_active = True

    if cooldown_active:
        cooldown_reason = "manual_stop_cooldown_active"

    room_media_context = {
        "room_id": source_room_id,
        "source_room_id": source_room_id,
        "source_room_selection_reason": source_room_selection_reason,
        "provider_source": str(last_media.get("provider_source") or values.get("provider_source") or "").strip() or None,
        "provider_media_id": str(last_media.get("provider_media_id") or values.get("provider_media_id") or "").strip() or None,
        "media_type": str(last_media.get("media_type") or values.get("media_type") or "").strip() or None,
        "track_title": str(last_media.get("track_title") or values.get("track_title") or values.get("last_song") or "").strip() or None,
        "artist_name": str(last_media.get("artist_name") or values.get("artist_name") or values.get("last_artist") or "").strip() or None,
        "album_name": str(last_media.get("album_name") or values.get("album_name") or values.get("last_album") or "").strip() or None,
        "genre": str(last_media.get("genre") or values.get("genre") or values.get("last_genre") or "").strip() or None,
        "media_query": str(last_media.get("media_query") or values.get("media_query") or "").strip() or None,
        "last_song": str(values.get("last_song") or last_media.get("track_title") or "").strip() or None,
        "last_genre": str(values.get("last_genre") or last_media.get("genre") or "").strip() or None,
        "manual_stop": manual_stop_marked,
        "manual_stop_cooldown_until": cooldown_until or None,
        "manual_stop_cooldown_seconds": int(cooldown_seconds) if isinstance(cooldown_seconds, (int, float, str)) and str(cooldown_seconds).strip().isdigit() else None,
        "captured_at": str(values.get("captured_at") or last_media.get("captured_at") or room_media_state.updated_at or "").strip() or None,
        "state": room_media_state.as_dict(),
    }
    return {
        "source_room_id": source_room_id,
        "source_room_selection_reason": source_room_selection_reason,
        "source_room_candidates": candidate_rooms,
        "room_media_state": room_media_state.as_dict(),
        "room_media_context": room_media_context,
        "manual_stop_cooldown_active": cooldown_active,
        "manual_stop_cooldown_reason": cooldown_reason,
    }


def _resolve_room_media_continuation_plan(
    *,
    room_media_context: dict[str, Any] | None,
    runtime_context: dict[str, Any],
) -> dict[str, Any]:
    """Resolve a governed continuation plan from room media context and optional person assistance."""
    context = dict(room_media_context or {})
    media_context = dict(context.get("room_media_context") or {})
    preferred_query_inputs = _resolve_media_preference_inputs(runtime_context)
    identity_state, confidence_band = _resolve_media_identity_state(runtime_context)
    room_default_query = runtime_context.get("room_default_media_query")
    household_default_query = runtime_context.get("household_default_media_query")
    system_safe_query = runtime_context.get("system_safe_media_query", "music")

    provider_source = str(media_context.get("provider_source") or "").strip() or None
    provider_media_id = str(media_context.get("provider_media_id") or "").strip() or None
    media_type = str(media_context.get("media_type") or "").strip() or None
    track_title = str(media_context.get("track_title") or "").strip() or None
    artist_name = str(media_context.get("artist_name") or "").strip() or None
    album_name = str(media_context.get("album_name") or "").strip() or None
    genre = str(media_context.get("genre") or media_context.get("last_genre") or "").strip() or None

    if context.get("manual_stop_cooldown_active"):
        return {
            "continuation_strategy": "governed_refusal",
            "strategy_reason": context.get("manual_stop_cooldown_reason") or "manual_stop_cooldown_active",
            "continuation_query": None,
            "music_assistant_request": None,
            "personalization_applied": False,
            "personalization_reason": None,
            "cooldown_decision": {
                "manual_stop_cooldown_active": True,
                "decision_reason": context.get("manual_stop_cooldown_reason") or "manual_stop_cooldown_active",
            },
        }

    plan = {
        "continuation_strategy": "governed_fallback",
        "strategy_reason": "room_media_context_missing",
        "continuation_query": None,
        "media_type": None,
        "radio_mode": False,
        "personalization_applied": False,
        "personalization_reason": None,
        "cooldown_decision": {
            "manual_stop_cooldown_active": False,
            "decision_reason": "cooldown_not_active",
        },
    }

    if provider_source and provider_source != _PROVIDER_MUSIC_ASSISTANT:
        plan.update(
            {
                "continuation_strategy": "governed_refusal",
                "strategy_reason": "media_provider_disabled",
                "continuation_query": None,
            }
        )
        return plan

    if provider_source == _PROVIDER_MUSIC_ASSISTANT and not provider_media_id and not track_title and not artist_name and not album_name and not genre:
        plan.update(
            {
                "continuation_strategy": "governed_fallback",
                "strategy_reason": "room_media_context_incomplete",
            }
        )
    elif media_type == "album" and album_name:
        plan.update(
            {
                "continuation_strategy": "same_album",
                "strategy_reason": "album_reference_available",
                "continuation_query": album_name,
                "media_type": "album",
            }
        )
    elif media_type == "artist" and artist_name:
        plan.update(
            {
                "continuation_strategy": "same_artist",
                "strategy_reason": "artist_reference_available",
                "continuation_query": artist_name,
                "media_type": "artist",
            }
        )
    elif provider_media_id or track_title:
        plan.update(
            {
                "continuation_strategy": "same_song",
                "strategy_reason": "track_reference_available",
                "continuation_query": provider_media_id or track_title,
            }
        )
    elif album_name:
        plan.update(
            {
                "continuation_strategy": "same_album",
                "strategy_reason": "album_reference_available",
                "continuation_query": album_name,
                "media_type": "album",
            }
        )
    elif artist_name:
        plan.update(
            {
                "continuation_strategy": "same_artist",
                "strategy_reason": "artist_reference_available",
                "continuation_query": artist_name,
                "media_type": "artist",
            }
        )
    elif genre:
        preferred_artist = preferred_query_inputs.get("preferred_artist")
        preference_outcome = _resolve_preference_hierarchy(
            PreferenceResolutionRequest(
                preference_key="media_continuation_query",
                identity_state=identity_state,
                confidence_band=confidence_band,
                command_value=None,
                guardrail_value=None,
                person_preference_value=preferred_artist,
                room_default_value=genre,
                household_default_value=household_default_query,
                system_safe_value=system_safe_query,
                personalization_policy_allowed=True,
                personalization_policy_reason="policy_allows",
                metadata={
                    "source": _ROOM_MEDIA_CONTINUATION_POLICY_NAME,
                    "continuation_strategy": "same_genre",
                },
            )
        )
        selected_query = preference_outcome.selected_value
        selected_tier = preference_outcome.selected_tier.value
        personalization_applied = selected_tier == PreferenceResolutionTier.KNOWN_PERSON_PREFERENCE.value
        plan.update(
            {
                "continuation_strategy": "same_genre",
                "strategy_reason": "genre_reference_available",
                "continuation_query": selected_query,
                "media_type": "artist" if personalization_applied and selected_query is not None else None,
                "radio_mode": not personalization_applied,
                "personalization_applied": personalization_applied,
                "personalization_reason": preference_outcome.identity_decision.get("reason_code"),
                "preference_resolution": preference_outcome.as_dict(),
            }
        )
    else:
        preference_outcome = _resolve_preference_hierarchy(
            PreferenceResolutionRequest(
                preference_key="media_continuation_query",
                identity_state=identity_state,
                confidence_band=confidence_band,
                command_value=None,
                guardrail_value=None,
                person_preference_value=preferred_query_inputs.get("preferred_media_query") or preferred_query_inputs.get("preferred_artist"),
                room_default_value=room_default_query,
                household_default_value=household_default_query,
                system_safe_value=system_safe_query,
                personalization_policy_allowed=True,
                personalization_policy_reason="policy_allows",
                metadata={
                    "source": _ROOM_MEDIA_CONTINUATION_POLICY_NAME,
                    "continuation_strategy": "governed_fallback",
                },
            )
        )
        selected_query = preference_outcome.selected_value
        if selected_query is None:
            plan.update(
                {
                    "continuation_strategy": "governed_refusal",
                    "strategy_reason": "no_usable_room_media_context",
                    "preference_resolution": preference_outcome.as_dict(),
                }
            )
        else:
            plan.update(
                {
                    "continuation_strategy": "governed_fallback",
                    "strategy_reason": "room_media_context_incomplete",
                    "continuation_query": selected_query,
                    "media_type": "artist" if preference_outcome.selected_tier == PreferenceResolutionTier.KNOWN_PERSON_PREFERENCE else None,
                    "radio_mode": bool(preference_outcome.selected_tier == PreferenceResolutionTier.KNOWN_PERSON_PREFERENCE),
                    "personalization_applied": preference_outcome.selected_tier == PreferenceResolutionTier.KNOWN_PERSON_PREFERENCE,
                    "personalization_reason": preference_outcome.identity_decision.get("reason_code"),
                    "preference_resolution": preference_outcome.as_dict(),
                }
            )

    plan["music_assistant_request"] = None
    if plan.get("continuation_query") is not None:
        music_assistant_data: dict[str, Any] = {
            "media_id": plan["continuation_query"],
            "enqueue": "replace",
        }
        if plan.get("media_type"):
            music_assistant_data["media_type"] = plan["media_type"]
        if plan.get("radio_mode"):
            music_assistant_data["radio_mode"] = True
        plan["music_assistant_request"] = music_assistant_data

    if plan.get("continuation_strategy") == "governed_refusal" and plan.get("strategy_reason") == "media_provider_disabled":
        plan["music_assistant_request"] = None

    return plan


async def _async_capture_room_media_context(
    hass: HomeAssistant,
    *,
    storage: ConciergeStorage,
    state: Any,
    area_id: str,
    source_room_id: str,
    provider_source: str,
    media_type: str | None,
    media_query: str | None,
    music_assistant_request: dict[str, Any] | None,
    room_media_context: dict[str, Any] | None,
    manual_stop_cooldown_until: str | None = None,
    manual_stop_cooldown_seconds: int | None = None,
) -> dict[str, Any]:
    """Persist the deterministic room-level last-media context used by continue/resume."""
    source_context = dict(room_media_context or {})
    last_media = dict(source_context.get("room_media_context") or {})
    state_id = _room_media_state_id(area_id=source_room_id)
    now_iso = datetime.now(timezone.utc).isoformat()

    if music_assistant_request is not None:
        request_media_type = str(music_assistant_request.get("media_type") or media_type or "").strip() or None
        request_media_id = str(music_assistant_request.get("media_id") or media_query or "").strip() or None
        request_radio_mode = bool(music_assistant_request.get("radio_mode", False))
    else:
        request_media_type = media_type
        request_media_id = str(media_query or "").strip() or None
        request_radio_mode = False

    if request_media_type == "artist" and request_radio_mode:
        last_song = None
        last_genre = str(last_media.get("genre") or source_context.get("last_genre") or "").strip() or None
    else:
        last_song = str(last_media.get("last_song") or last_media.get("track_title") or media_query or "").strip() or None
        last_genre = str(last_media.get("genre") or source_context.get("last_genre") or "").strip() or None

    room_media_values: dict[str, Any] = {
        "room_id": source_room_id,
        "source_room_id": source_room_id,
        "source_room_selection_reason": source_context.get("source_room_selection_reason") or "deterministic_room_priority_selected",
        "provider_source": provider_source,
        "provider_media_id": request_media_id,
        "media_type": request_media_type,
        "media_query": media_query or request_media_id,
        "last_song": last_song,
        "last_genre": last_genre,
        "last_album": str(last_media.get("album_name") or "").strip() or None,
        "last_artist": str(last_media.get("artist_name") or "").strip() or None,
        "last_media": {
            "provider_source": provider_source,
            "provider_media_id": request_media_id,
            "media_type": request_media_type,
            "track_title": last_song,
            "artist_name": str(last_media.get("artist_name") or "").strip() or None,
            "album_name": str(last_media.get("album_name") or "").strip() or None,
            "genre": last_genre,
            "media_query": media_query or request_media_id,
            "captured_at": now_iso,
        },
        "manual_stop": bool(last_media.get("manual_stop", False)),
        "manual_stop_cooldown_until": manual_stop_cooldown_until or last_media.get("manual_stop_cooldown_until"),
        "manual_stop_cooldown_seconds": manual_stop_cooldown_seconds if manual_stop_cooldown_seconds is not None else last_media.get("manual_stop_cooldown_seconds"),
        "captured_at": now_iso,
    }
    room_media_metadata = {
        "policy_name": _ROOM_MEDIA_CONTEXT_POLICY_NAME,
        "source_room_selection_reason": source_context.get("source_room_selection_reason") or "deterministic_room_priority_selected",
        "merged_room_participation": bool(source_context.get("source_room_candidates") and len(source_context.get("source_room_candidates", [])) > 1),
        "source_room_candidates": list(source_context.get("source_room_candidates", [])),
        "captured_at": now_iso,
    }

    usual_state = UsualState(
        state_id=state_id,
        scope=ContinuityScope.ROOM,
        scope_ref=source_room_id,
        basis=UsualStateBasis.LEARNED,
        updated_at=now_iso,
        values=room_media_values,
        metadata=room_media_metadata,
    )
    await storage.async_upsert_usual_state(usual_state)
    if state is not None and hasattr(state, "usual_states"):
        state.usual_states[state_id] = usual_state
    return usual_state.as_dict()


def _resolve_media_provider_configuration(hass: HomeAssistant) -> dict[str, Any]:
    """Resolve Concierge media provider configuration and availability."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return {
            "configured_provider": _PROVIDER_NONE,
            "provider_selected": _PROVIDER_NONE,
            "provider_reason": "concierge_not_configured",
            "provider_available": False,
            "provider_service_available": False,
            "provider_integration_available": False,
        }

    entry = entries[0]
    provider = str(
        entry.options.get("media_provider", entry.data.get("media_provider", _PROVIDER_NONE))
        or _PROVIDER_NONE
    ).strip() or _PROVIDER_NONE
    music_assistant_entries = hass.config_entries.async_entries(_PROVIDER_MUSIC_ASSISTANT)
    provider_service_available = hass.services.has_service("music_assistant", "play_media")
    provider_integration_available = bool(music_assistant_entries)

    if provider != _PROVIDER_MUSIC_ASSISTANT:
        return {
            "configured_provider": provider,
            "provider_selected": _PROVIDER_NONE,
            "provider_reason": "media_provider_disabled",
            "provider_available": False,
            "provider_service_available": provider_service_available,
            "provider_integration_available": provider_integration_available,
        }

    provider_available = bool(provider_service_available and provider_integration_available)
    return {
        "configured_provider": provider,
        "provider_selected": _PROVIDER_MUSIC_ASSISTANT,
        "provider_reason": (
            "preferred_provider_configured_and_available"
            if provider_available
            else "preferred_provider_unavailable"
        ),
        "provider_available": provider_available,
        "provider_service_available": provider_service_available,
        "provider_integration_available": provider_integration_available,
    }


def _resolve_media_request_type_hint(runtime_context: dict[str, Any]) -> str | None:
    """Resolve an explicit governed media request type hint when supplied."""
    hint = str(runtime_context.get("media_request_type", "") or "").strip().lower()
    if hint in _ROOM_MEDIA_REQUEST_KIND_HINTS:
        return hint
    return None


def _resolve_media_preference_inputs(runtime_context: dict[str, Any]) -> dict[str, Any]:
    """Consume bounded media preference inputs without creating a new persistence model."""
    value = runtime_context.get("media_preference_inputs", {})
    if not isinstance(value, dict):
        return {}
    return dict(value)


def _resolve_media_preference_query(
    *,
    request_kind: str,
    preference_inputs: dict[str, Any],
) -> Any:
    """Resolve one upstream-provided person-scoped media preference input when available."""
    explicit_query = preference_inputs.get("preferred_media_query")
    if explicit_query is not None:
        return explicit_query

    if request_kind == "genre":
        return preference_inputs.get("preferred_genre")
    if request_kind == "artist":
        return preference_inputs.get("preferred_artist")
    if request_kind == "album":
        return preference_inputs.get("preferred_album")
    if request_kind == "playlist":
        return preference_inputs.get("preferred_playlist")
    if request_kind == "general_music":
        return preference_inputs.get("music_affinity")
    return None


def _resolve_media_identity_state(runtime_context: dict[str, Any]) -> tuple[PreferenceIdentityState, ContinuityConfidenceBand | None]:
    """Resolve identity state inputs for media preference consumption."""
    identity_context = runtime_context.get("identity_context", {})
    if not isinstance(identity_context, dict):
        return PreferenceIdentityState.UNAVAILABLE, ContinuityConfidenceBand.UNKNOWN

    raw_state = str(identity_context.get("state", "") or "").strip().lower()
    raw_band = str(identity_context.get("confidence_band", "") or "").strip().lower()

    try:
        identity_state = PreferenceIdentityState(raw_state)
    except ValueError:
        identity_state = PreferenceIdentityState.UNAVAILABLE

    try:
        confidence_band = ContinuityConfidenceBand(raw_band) if raw_band else ContinuityConfidenceBand.UNKNOWN
    except ValueError:
        confidence_band = ContinuityConfidenceBand.UNKNOWN

    return identity_state, confidence_band


def _resolve_media_playback_query(
    *,
    media_request: dict[str, Any],
    runtime_context: dict[str, Any],
) -> dict[str, Any]:
    """Resolve the governed media query and identity-aware preference decision."""
    request_kind = str(media_request.get("request_kind") or "general_music")
    request_hint = _resolve_media_request_type_hint(runtime_context)
    if request_hint is not None:
        request_kind = request_hint

    preference_inputs = _resolve_media_preference_inputs(runtime_context)
    preferred_query = _resolve_media_preference_query(
        request_kind=request_kind,
        preference_inputs=preference_inputs,
    )
    identity_state, confidence_band = _resolve_media_identity_state(runtime_context)
    room_default_query = runtime_context.get("room_default_media_query")
    household_default_query = runtime_context.get("household_default_media_query")
    system_safe_query = runtime_context.get("system_safe_media_query", media_request.get("media_query") or "music")

    if request_kind in {"general_music", "playlist"}:
        preference_outcome = _resolve_preference_hierarchy(
            PreferenceResolutionRequest(
                preference_key="media_playback_query",
                identity_state=identity_state,
                confidence_band=confidence_band,
                command_value=None,
                guardrail_value=None,
                person_preference_value=preferred_query,
                room_default_value=room_default_query,
                household_default_value=household_default_query,
                system_safe_value=system_safe_query,
                personalization_policy_allowed=True,
                personalization_policy_reason="policy_allows",
                metadata={
                    "request_kind": request_kind,
                    "source": "ec_e_01_media_provider_resolution",
                },
            )
        )
        media_query = preference_outcome.selected_value
    else:
        preference_outcome = _resolve_preference_hierarchy(
            PreferenceResolutionRequest(
                preference_key="media_playback_query",
                identity_state=identity_state,
                confidence_band=confidence_band,
                command_value=media_request.get("media_query"),
                guardrail_value=None,
                person_preference_value=preferred_query,
                room_default_value=room_default_query,
                household_default_value=household_default_query,
                system_safe_value=system_safe_query,
                personalization_policy_allowed=True,
                personalization_policy_reason="policy_allows",
                metadata={
                    "request_kind": request_kind,
                    "source": "ec_e_01_media_provider_resolution",
                },
            )
        )
        media_query = preference_outcome.selected_value

    return {
        "request_kind": request_kind,
        "media_query": media_query,
        "preference_outcome": preference_outcome.as_dict(),
        "preference_inputs": preference_inputs,
    }


def _resolve_media_request_output_targets(
    hass: HomeAssistant,
    *,
    state: Any,
    area_id: str | None,
    composite_id: str | None,
) -> dict[str, Any]:
    """Resolve configured playback targets for EC-E-01 without causing playback side effects."""
    if composite_id:
        composite = getattr(state, "composites", {}).get(composite_id)
        if composite is None:
            return {
                "playback_scope": "merged_room",
                "memory_scope": "room",
                "room_authority_source": "room_configuration",
                "merged_room_participation": True,
                "participating_rooms": [],
                "group_targeted_speakers": [],
                "room_results": [],
                "failure_reason": "composite_configuration_missing",
                "decision_reason": "configured_room_authority_validation",
            }
        participating_rooms = list(dict.fromkeys(list(getattr(composite, "area_ids", []) or [])))
        if not participating_rooms and getattr(composite, "primary_area", None):
            participating_rooms = [str(composite.primary_area)]
    elif area_id:
        participating_rooms = [area_id]
    else:
        return {
            "playback_scope": "room",
            "memory_scope": "room",
            "room_authority_source": "room_configuration",
            "merged_room_participation": False,
            "participating_rooms": [],
            "group_targeted_speakers": [],
            "room_results": [],
            "failure_reason": "room_scope_missing",
            "decision_reason": "configured_room_authority_validation",
        }

    room_results: list[dict[str, Any]] = []
    targeted_speakers: list[str] = []
    failure_reason: str | None = None

    for room_area_id in participating_rooms:
        room = getattr(state, "rooms", {}).get(room_area_id)
        configured_speakers = _resolve_room_audio_speaker_membership(room)
        if not configured_speakers:
            room_results.append(
                {
                    "area_id": room_area_id,
                    "configured_speakers": [],
                    "validated_speakers": [],
                    "validation_results": [],
                    "failure_reason": "configured_speaker_mapping_missing",
                    "decision_reason": "configured_room_authority_validation",
                }
            )
            continue

        valid_speakers, validation_results = _validate_configured_room_speakers(hass, configured_speakers)
        if not valid_speakers:
            validation_reasons = {
                str(item.get("reason") or "").strip()
                for item in validation_results
                if str(item.get("reason") or "").strip()
            }
            if len(validation_reasons) > 1:
                room_failure_reason = "no_eligible_configured_speakers"
            elif "configured_speaker_unavailable" in validation_reasons:
                room_failure_reason = "configured_speaker_unavailable"
            elif "configured_speaker_missing" in validation_reasons:
                room_failure_reason = "configured_speaker_missing"
            else:
                room_failure_reason = "configured_speaker_invalid"
            room_results.append(
                {
                    "area_id": room_area_id,
                    "configured_speakers": list(configured_speakers),
                    "validated_speakers": [],
                    "validation_results": validation_results,
                    "failure_reason": room_failure_reason,
                    "decision_reason": "configured_room_authority_validation",
                }
            )
            continue

        targeted_speakers.extend(valid_speakers)
        room_results.append(
            {
                "area_id": room_area_id,
                "configured_speakers": list(configured_speakers),
                "validated_speakers": list(valid_speakers),
                "validation_results": validation_results,
                "failure_reason": None,
                "decision_reason": "configured_room_speaker_authority",
            }
        )

    unique_targeted = list(dict.fromkeys(targeted_speakers))
    if not unique_targeted:
        failure_reason = str(room_results[0].get("failure_reason") or "configured_speaker_mapping_missing") if room_results else "room_scope_missing"

    return {
        "playback_scope": "merged_room" if composite_id else "room",
        "memory_scope": "room",
        "room_authority_source": "room_configuration",
        "merged_room_participation": bool(composite_id),
        "participating_rooms": participating_rooms,
        "group_targeted_speakers": unique_targeted,
        "room_results": room_results,
        "failure_reason": failure_reason,
        "decision_reason": "configured_room_speaker_authority",
    }


def _usual_lighting_state_id(*, area_id: str, entity_id: str) -> str:
    """Build a stable per-room per-entity learned lighting usual-state identifier."""
    return f"usual_lighting::{area_id}::{entity_id}"


def _room_audio_state_id(*, area_id: str, channel: str) -> str:
    """Build a stable per-room per-channel room-audio usual-state identifier."""
    normalized_channel = str(channel or "").strip().lower()
    return f"room_audio::{area_id}::{normalized_channel}"


def _coerce_brightness_pct(value: Any) -> int | None:
    """Normalize brightness percent to an integer in [1, 100] when valid."""
    try:
        normalized = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    if normalized < 1 or normalized > 100:
        return None
    return normalized


def _coerce_volume_pct(value: Any) -> int | None:
    """Normalize room-audio volume percent to an integer in [1, 100] when valid."""
    try:
        normalized = int(round(float(value)))
    except (TypeError, ValueError):
        return None
    if normalized < 1 or normalized > 100:
        return None
    return normalized


def _volume_pct_from_media_state(state_obj: Any) -> int | None:
    """Extract volume percent from one Home Assistant media_player state object."""
    if state_obj is None:
        return None
    attributes = getattr(state_obj, "attributes", {}) or {}
    if not isinstance(attributes, dict):
        return None

    if "volume_level" in attributes:
        try:
            level = float(attributes.get("volume_level"))
        except (TypeError, ValueError):
            return None
        return _coerce_volume_pct(level * 100.0)

    if "media_volume_level" in attributes:
        try:
            level = float(attributes.get("media_volume_level"))
        except (TypeError, ValueError):
            return None
        return _coerce_volume_pct(level * 100.0)

    return None


def _brightness_pct_from_hass_state(state_obj: Any) -> int | None:
    """Extract brightness percent from one Home Assistant light state object."""
    if state_obj is None:
        return None
    state_value = str(getattr(state_obj, "state", "")).strip().lower()
    if state_value != "on":
        return None

    attributes = getattr(state_obj, "attributes", {}) or {}
    if not isinstance(attributes, dict):
        return None

    if "brightness_pct" in attributes:
        return _coerce_brightness_pct(attributes.get("brightness_pct"))

    brightness = attributes.get("brightness")
    if brightness is None:
        return None

    try:
        brightness_raw = float(brightness)
    except (TypeError, ValueError):
        return None

    brightness_pct = int(round((brightness_raw / 255.0) * 100.0))
    return _coerce_brightness_pct(brightness_pct)


def _evaluate_entity_stability_for_usual_learning(
    state_obj: Any,
    *,
    stability_seconds: int,
) -> dict[str, Any]:
    """Evaluate whether one entity level is stable for governed usual-learning capture."""
    if state_obj is None:
        return {
            "stable": False,
            "observed_seconds": 0,
            "required_seconds": int(stability_seconds),
            "reason": "state_missing",
        }

    changed_at = getattr(state_obj, "last_changed", None) or getattr(state_obj, "last_updated", None)
    if not isinstance(changed_at, datetime):
        return {
            "stable": False,
            "observed_seconds": 0,
            "required_seconds": int(stability_seconds),
            "reason": "timestamp_unavailable",
        }

    if changed_at.tzinfo is None:
        changed_at = changed_at.replace(tzinfo=timezone.utc)

    observed_seconds = max(
        0,
        int((datetime.now(timezone.utc) - changed_at).total_seconds()),
    )
    stable = observed_seconds >= int(stability_seconds)
    return {
        "stable": stable,
        "observed_seconds": observed_seconds,
        "required_seconds": int(stability_seconds),
        "reason": "stable_threshold_satisfied" if stable else "stable_threshold_not_met",
    }


def _evaluate_entity_stability_for_room_audio_learning(
    state_obj: Any,
    *,
    stability_seconds: int,
) -> dict[str, Any]:
    """Evaluate whether one speaker volume is stable for governed room-audio capture."""
    return _evaluate_entity_stability_for_usual_learning(
        state_obj,
        stability_seconds=stability_seconds,
    )


def _lighting_learning_stability_seconds(state: Any) -> int:
    """Resolve governed stability interval for learned usual lighting capture."""
    feature = {}
    if state is not None and hasattr(state, "global_features"):
        feature = dict(state.global_features.get(_USUAL_LIGHTING_LEARNING_POLICY_FEATURE_KEY, {}))

    options = dict(feature.get("options", {})) if isinstance(feature.get("options", {}), dict) else {}
    raw_value = options.get("stability_seconds", _USUAL_LIGHTING_DEFAULT_STABILITY_SECONDS)
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        parsed = _USUAL_LIGHTING_DEFAULT_STABILITY_SECONDS
    return max(1, min(parsed, 3600))


def _room_audio_learning_stability_seconds(state: Any) -> int:
    """Resolve governed stability interval for room-audio learning capture."""
    feature = {}
    if state is not None and hasattr(state, "global_features"):
        feature = dict(state.global_features.get(_ROOM_AUDIO_LEARNING_POLICY_FEATURE_KEY, {}))

    options = dict(feature.get("options", {})) if isinstance(feature.get("options", {}), dict) else {}
    raw_value = options.get("stability_seconds", _ROOM_AUDIO_DEFAULT_STABILITY_SECONDS)
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        parsed = _ROOM_AUDIO_DEFAULT_STABILITY_SECONDS
    return max(1, min(parsed, 3600))


def _lighting_learning_policy_enabled(state: Any) -> bool:
    """Resolve whether EC-C-01 usual-lighting learning is enabled by policy."""
    feature = {}
    if state is not None and hasattr(state, "global_features"):
        feature = dict(state.global_features.get(_USUAL_LIGHTING_LEARNING_POLICY_FEATURE_KEY, {}))

    if "enabled" in feature:
        return bool(feature.get("enabled", True))

    options = dict(feature.get("options", {})) if isinstance(feature.get("options", {}), dict) else {}
    if "learning_enabled" in options:
        return bool(options.get("learning_enabled", True))
    return True


def _room_audio_learning_policy_enabled(state: Any) -> bool:
    """Resolve whether EC-D-01 room-audio learning is enabled by policy."""
    feature = {}
    if state is not None and hasattr(state, "global_features"):
        feature = dict(state.global_features.get(_ROOM_AUDIO_LEARNING_POLICY_FEATURE_KEY, {}))

    if "enabled" in feature:
        return bool(feature.get("enabled", True))

    options = dict(feature.get("options", {})) if isinstance(feature.get("options", {}), dict) else {}
    if "learning_enabled" in options:
        return bool(options.get("learning_enabled", True))
    return True


def _resolve_usual_lighting_membership(room: Any, command_kind: str) -> list[str]:
    """Resolve configured room membership for EC-C-01 command handling."""
    lamp_entities = _room_entity_ids(room, "lamp_entity_ids")
    light_entities = _room_entity_ids(room, "light_entity_ids")

    if command_kind == "lamps":
        return lamp_entities
    if command_kind == "lights":
        return light_entities
    return list(dict.fromkeys(lamp_entities + light_entities))


def _resolve_room_audio_speaker_membership(room: Any) -> list[str]:
    """Resolve configured room speaker membership with media-player precedence."""
    media_player_entities = _room_entity_ids(room, "media_player_entity_ids")
    speaker_entities = _room_entity_ids(room, "speaker_entity_ids")
    return list(dict.fromkeys(media_player_entities + speaker_entities))


def _validate_configured_room_speakers(
    hass: HomeAssistant,
    configured_speakers: list[str],
) -> tuple[list[str], list[dict[str, Any]]]:
    """Validate configured room speakers without redefining speaker authority."""
    registry = er.async_get(hass)
    valid_targets: list[str] = []
    validations: list[dict[str, Any]] = []

    for entity_id in configured_speakers:
        normalized = str(entity_id or "").strip()
        if not normalized:
            validations.append(
                {
                    "entity_id": normalized,
                    "valid": False,
                    "status": "invalid_entity",
                    "reason": "configured_speaker_invalid",
                }
            )
            continue

        if not normalized.startswith("media_player."):
            validations.append(
                {
                    "entity_id": normalized,
                    "valid": False,
                    "status": "invalid_entity",
                    "reason": "configured_speaker_invalid",
                }
            )
            continue

        state_obj = hass.states.get(normalized)
        registry_entry = registry.async_get(normalized)
        if state_obj is None and registry_entry is None:
            validations.append(
                {
                    "entity_id": normalized,
                    "valid": False,
                    "status": "missing_entity",
                    "reason": "configured_speaker_missing",
                }
            )
            continue

        if state_obj is None:
            validations.append(
                {
                    "entity_id": normalized,
                    "valid": False,
                    "status": "missing_state",
                    "reason": "configured_speaker_missing",
                }
            )
            continue

        state_value = str(getattr(state_obj, "state", "") or "").strip().lower()
        if state_value in _ROOM_AUDIO_UNAVAILABLE_STATES:
            validations.append(
                {
                    "entity_id": normalized,
                    "valid": False,
                    "status": "unavailable_entity",
                    "reason": "configured_speaker_unavailable",
                }
            )
            continue

        valid_targets.append(normalized)
        validations.append(
            {
                "entity_id": normalized,
                "valid": True,
                "status": "validated",
                "reason": "configured_speaker_valid",
            }
        )

    return valid_targets, validations


def _resolve_room_audio_level(
    *,
    state: Any,
    area_id: str,
    channel: str,
) -> tuple[int | None, str | None, dict[str, Any] | None]:
    """Resolve one stored room-level audio value for one channel when available."""
    state_id = _room_audio_state_id(area_id=area_id, channel=channel)
    usual_state = None
    if state is not None and hasattr(state, "usual_states"):
        usual_state = state.usual_states.get(state_id)
    if usual_state is None:
        return None, "room_audio_value_missing", None

    values = dict(getattr(usual_state, "values", {}) or {})
    level = _coerce_volume_pct(values.get("volume_pct"))
    if level is None:
        return None, "room_audio_value_invalid", usual_state.as_dict()
    return level, None, usual_state.as_dict()


async def _async_capture_room_audio_channel(
    hass: HomeAssistant,
    *,
    storage: ConciergeStorage,
    state: Any,
    area_id: str,
    channel: str,
    configured_speakers: list[str],
    allow_overwrite: bool = True,
) -> dict[str, Any]:
    """Capture one room-scoped channel volume using governed stability and learning policy."""
    normalized_channel = str(channel or "").strip().lower()
    if normalized_channel not in _ROOM_AUDIO_CHANNELS:
        return {
            "learning_status": "denied",
            "denial_reason": "unsupported_room_audio_channel",
            "captured_volume_pct": None,
            "stability_evidence": [],
            "policy_decision": {},
            "learning_write": None,
            "previous_learned_preserved": False,
        }

    stability_seconds = _room_audio_learning_stability_seconds(state)
    learning_policy_enabled = _room_audio_learning_policy_enabled(state)

    stable_levels: list[int] = []
    stability_evidence: list[dict[str, Any]] = []
    for speaker_id in configured_speakers:
        state_obj = hass.states.get(speaker_id)
        level = _volume_pct_from_media_state(state_obj)
        stability = _evaluate_entity_stability_for_room_audio_learning(
            state_obj,
            stability_seconds=stability_seconds,
        )
        if level is not None and bool(stability.get("stable", False)):
            stable_levels.append(level)
        stability_evidence.append(
            {
                "entity_id": speaker_id,
                "volume_pct": level,
                "stability": dict(stability),
            }
        )

    captured_volume_pct: int | None = None
    if stable_levels:
        captured_volume_pct = _coerce_volume_pct(sum(stable_levels) / len(stable_levels))

    policy_outcome = _evaluate_learning_policy(
        LearningPolicyEvaluationRequest(
            learning_key=f"room_audio_volume:{normalized_channel}:{area_id}",
            ownership_scope=LearningOwnershipScope.ROOM,
            identity_state=PreferenceIdentityState.UNAVAILABLE,
            confidence_band="unknown",
            learning_policy_enabled=learning_policy_enabled,
            ownership_supported=True,
            entity_eligible=captured_volume_pct is not None,
            preference_eligible=True,
            safety_restrictions_clear=captured_volume_pct is not None,
            identity_sensitive_learning=False,
            personalization_policy_allowed=True,
            policy_reason="policy_allows",
            metadata={
                "learning_source": "room_audio_stability_capture",
                "area_id": area_id,
                "channel": normalized_channel,
                "membership_source": _ROOM_AUDIO_MEMBERSHIP_SOURCE,
                "configured_speaker_count": len(configured_speakers),
            },
        )
    )

    existing_level, _, _ = _resolve_room_audio_level(
        state=state,
        area_id=area_id,
        channel=normalized_channel,
    )
    learning_status = "denied"
    enqueue_info: dict[str, Any] | None = None

    if existing_level is not None and not allow_overwrite:
        learning_status = "denied_previous_preserved"
    elif policy_outcome.learning_allowed and captured_volume_pct is not None:
        learning_event_id = f"room_audio_{normalized_channel}_{uuid4().hex}"
        state_id = _room_audio_state_id(area_id=area_id, channel=normalized_channel)
        usual_state = UsualState(
            state_id=state_id,
            scope=ContinuityScope.ROOM,
            scope_ref=area_id,
            basis=UsualStateBasis.LEARNED,
            updated_at=datetime.now(timezone.utc).isoformat(),
            values={
                "channel": normalized_channel,
                "volume_pct": captured_volume_pct,
                "area_id": area_id,
                "configured_speakers": list(configured_speakers),
            },
            event_id=learning_event_id,
            metadata={
                "policy_name": _ROOM_AUDIO_POLICY_NAME,
                "policy_decision": dict(policy_outcome.policy_decision),
                "membership_source": _ROOM_AUDIO_MEMBERSHIP_SOURCE,
                "stability_seconds": stability_seconds,
                "stability_evidence": list(stability_evidence),
            },
        )
        await storage.async_upsert_usual_state(usual_state)
        state.usual_states[state_id] = usual_state
        learning_status = "learned"

        enqueue_info = _enqueue_learning_write(
            hass,
            LearningWriteRequest(
                learning_event_id=learning_event_id,
                learning_key=f"room_audio_volume:{normalized_channel}",
                ownership_scope=LearningOwnershipScope.ROOM,
                owner_ref=area_id,
                learned_value={
                    "channel": normalized_channel,
                    "volume_pct": captured_volume_pct,
                    "configured_speakers": list(configured_speakers),
                },
                reason_code="stable_room_audio_volume_capture",
                policy_used=_ROOM_AUDIO_POLICY_NAME,
                reversibility_metadata={
                    "owner_scope": "room",
                    "area_id": area_id,
                    "channel": normalized_channel,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "rollback_supporting_metadata": True,
                },
                explainability={
                    "membership_source": _ROOM_AUDIO_MEMBERSHIP_SOURCE,
                    "policy_decision": dict(policy_outcome.policy_decision),
                    "stability_evidence": list(stability_evidence),
                },
                metadata={
                    "configured_speaker_count": len(configured_speakers),
                },
            ),
        )
    elif existing_level is not None:
        learning_status = "denied_previous_preserved"

    return {
        "learning_status": learning_status,
        "denial_reason": policy_outcome.denial_reason,
        "captured_volume_pct": captured_volume_pct,
        "stability_seconds": stability_seconds,
        "stability_evidence": stability_evidence,
        "policy_decision": dict(policy_outcome.policy_decision),
        "learning_write": enqueue_info,
        "previous_learned_preserved": existing_level is not None and learning_status != "learned",
    }


async def _async_execute_room_audio_playback_start(
    hass: HomeAssistant,
    *,
    storage: ConciergeStorage,
    state: Any,
    area_id: str | None,
    composite_id: str | None,
    channel: str = "music",
) -> dict[str, Any]:
    """Execute EC-D-01 room-audio playback-start volume resolution from room authority."""
    normalized_channel = str(channel or "").strip().lower()
    if normalized_channel not in _ROOM_AUDIO_CHANNELS:
        return {
            "handled": True,
            "executed": False,
            "resolved_target": f"room_audio:{normalized_channel}_start",
            "failure_reason": "unsupported_room_audio_channel",
            "fallback_used": True,
            "fallback_path": "degraded_safe_failure",
            "fallback_source": _ROOM_AUDIO_FALLBACK_POLICY_SOURCE,
            "memory_scope": "room",
            "group_targeted_speakers": [],
            "room_results": [],
            "learning_decisions": [],
            "merged_room_participation": bool(composite_id),
            "participating_rooms": [],
        }

    if composite_id:
        composite = getattr(state, "composites", {}).get(composite_id)
        if composite is None:
            return {
                "handled": True,
                "executed": False,
                "resolved_target": f"room_audio:{normalized_channel}_start",
                "failure_reason": "composite_configuration_missing",
                "fallback_used": True,
                "fallback_path": "degraded_safe_failure",
                "fallback_source": _ROOM_AUDIO_FALLBACK_POLICY_SOURCE,
                "memory_scope": "room",
                "group_targeted_speakers": [],
                "room_results": [],
                "learning_decisions": [],
                "merged_room_participation": True,
                "participating_rooms": [],
            }
        participating_rooms = list(dict.fromkeys(list(getattr(composite, "area_ids", []) or [])))
        if not participating_rooms and getattr(composite, "primary_area", None):
            participating_rooms = [str(composite.primary_area)]
    elif area_id:
        participating_rooms = [area_id]
    else:
        return {
            "handled": True,
            "executed": False,
            "resolved_target": f"room_audio:{normalized_channel}_start",
            "failure_reason": "room_scope_missing",
            "fallback_used": True,
            "fallback_path": "degraded_safe_failure",
            "fallback_source": _ROOM_AUDIO_FALLBACK_POLICY_SOURCE,
            "memory_scope": "room",
            "group_targeted_speakers": [],
            "room_results": [],
            "learning_decisions": [],
            "merged_room_participation": False,
            "participating_rooms": [],
        }

    room_results: list[dict[str, Any]] = []
    learning_decisions: list[dict[str, Any]] = []
    targeted_speakers: list[str] = []

    for room_area_id in participating_rooms:
        room = getattr(state, "rooms", {}).get(room_area_id)
        configured_speakers = _resolve_room_audio_speaker_membership(room)
        if not configured_speakers:
            room_results.append(
                {
                    "area_id": room_area_id,
                    "channel": normalized_channel,
                    "configured_speakers": [],
                    "validated_speakers": [],
                    "validation_results": [],
                    "resolved_volume_pct": None,
                    "resolved_source": None,
                    "fallback_reason": "configured_speaker_mapping_missing",
                    "fallback_source": _ROOM_AUDIO_FALLBACK_POLICY_SOURCE,
                    "decision_reason": "configured_room_authority_validation",
                    "memory_scope": "room",
                }
            )
            continue

        valid_speakers, validation_results = _validate_configured_room_speakers(
            hass,
            configured_speakers,
        )
        if not valid_speakers:
            validation_reasons = {
                str(item.get("reason") or "").strip()
                for item in validation_results
                if str(item.get("reason") or "").strip()
            }
            if len(validation_reasons) > 1:
                fallback_reason = "no_eligible_configured_speakers"
            elif "configured_speaker_unavailable" in validation_reasons:
                fallback_reason = "configured_speaker_unavailable"
            elif "configured_speaker_missing" in validation_reasons:
                fallback_reason = "configured_speaker_missing"
            else:
                fallback_reason = "configured_speaker_invalid"
            room_results.append(
                {
                    "area_id": room_area_id,
                    "channel": normalized_channel,
                    "configured_speakers": list(configured_speakers),
                    "validated_speakers": [],
                    "validation_results": validation_results,
                    "resolved_volume_pct": None,
                    "resolved_source": None,
                    "fallback_reason": fallback_reason,
                    "fallback_source": _ROOM_AUDIO_FALLBACK_POLICY_SOURCE,
                    "decision_reason": "configured_room_authority_validation",
                    "memory_scope": "room",
                }
            )
            continue

        learning = await _async_capture_room_audio_channel(
            hass,
            storage=storage,
            state=state,
            area_id=room_area_id,
            channel=normalized_channel,
            configured_speakers=valid_speakers,
            allow_overwrite=False,
        )
        learning_decisions.append(
            {
                "area_id": room_area_id,
                "channel": normalized_channel,
                **learning,
            }
        )

        resolved_level, resolved_reason, _resolved_state = _resolve_room_audio_level(
            state=state,
            area_id=room_area_id,
            channel=normalized_channel,
        )

        resolved_source = "room_audio_usual_state"
        fallback_reason: str | None = None
        if resolved_level is None:
            fallback_reason = "room_audio_value_missing" if resolved_reason == "room_audio_value_missing" else "room_audio_value_invalid"
            current_levels = [
                _volume_pct_from_media_state(hass.states.get(speaker_id))
                for speaker_id in valid_speakers
            ]
            current_levels = [item for item in current_levels if item is not None]
            if current_levels:
                resolved_level = _coerce_volume_pct(sum(current_levels) / len(current_levels))
                resolved_source = "current_state_volume"
            else:
                resolved_level = _ROOM_AUDIO_DEFAULT_VOLUME_PCT
                resolved_source = "safe_default_volume"

        volume_level = float(resolved_level) / 100.0 if resolved_level is not None else 0.0
        for speaker_id in valid_speakers:
            await hass.services.async_call(
                "media_player",
                "volume_set",
                {
                    "entity_id": speaker_id,
                    "volume_level": volume_level,
                },
                blocking=True,
            )
            targeted_speakers.append(speaker_id)

        room_results.append(
            {
                "area_id": room_area_id,
                "channel": normalized_channel,
                "configured_speakers": list(configured_speakers),
                "validated_speakers": list(valid_speakers),
                "validation_results": validation_results,
                "resolved_volume_pct": resolved_level,
                "resolved_source": resolved_source,
                "fallback_reason": fallback_reason,
                "fallback_source": _ROOM_AUDIO_FALLBACK_POLICY_SOURCE if fallback_reason else None,
                "decision_reason": "configured_room_speaker_authority",
                "memory_scope": "room",
            }
        )

    unique_targeted = list(dict.fromkeys(targeted_speakers))
    fallback_used = any(item.get("fallback_reason") for item in room_results)
    executed = len(unique_targeted) > 0
    failure_reason: str | None = None
    if not executed:
        if room_results:
            failure_reason = str(room_results[0].get("fallback_reason") or "configured_speaker_mapping_missing")
        else:
            failure_reason = "no_participating_rooms"

    return {
        "handled": True,
        "executed": executed,
        "resolved_target": f"room_audio:{normalized_channel}_start",
        "channel": normalized_channel,
        "playback_scope": "merged_room" if composite_id else "room",
        "memory_scope": "room",
        "merged_room_participation": bool(composite_id),
        "participating_rooms": participating_rooms,
        "group_targeted_speakers": unique_targeted,
        "room_results": room_results,
        "learning_decisions": learning_decisions,
        "failure_reason": failure_reason,
        "fallback_used": fallback_used,
        "fallback_path": "room_audio_channel_fallback" if fallback_used else "none",
        "fallback_source": _ROOM_AUDIO_FALLBACK_POLICY_SOURCE,
        "decision_reason": "configured_room_speaker_authority",
        "activity_external_refs": [
            {
                "ref_type": "room_audio_continuity",
                "policy_name": _ROOM_AUDIO_POLICY_NAME,
                "channel": normalized_channel,
                "playback_scope": "merged_room" if composite_id else "room",
                "memory_scope": "room",
                "merged_room_participation": bool(composite_id),
                "participating_rooms": participating_rooms,
                "group_targeted_speakers": unique_targeted,
                "room_results": room_results,
                "learning_decisions": learning_decisions,
                "fallback_used": fallback_used,
                "fallback_path": "room_audio_channel_fallback" if fallback_used else "none",
                "fallback_source": _ROOM_AUDIO_FALLBACK_POLICY_SOURCE,
                "failure_reason": failure_reason,
            }
        ],
    }


def _resolve_room_audio_channel_level_with_fallback(
    hass: HomeAssistant,
    *,
    state: Any,
    area_id: str,
    channel: str,
    speakers: list[str],
) -> tuple[int, str, str | None]:
    """Resolve room-audio channel level with deterministic fallback behavior."""
    resolved_level, resolved_reason, _resolved_state = _resolve_room_audio_level(
        state=state,
        area_id=area_id,
        channel=channel,
    )
    if resolved_level is not None:
        return resolved_level, "room_audio_usual_state", None

    fallback_reason = (
        "room_audio_value_missing" if resolved_reason == "room_audio_value_missing" else "room_audio_value_invalid"
    )
    current_levels = [_volume_pct_from_media_state(hass.states.get(speaker_id)) for speaker_id in speakers]
    current_levels = [item for item in current_levels if item is not None]
    if current_levels:
        current_level = _coerce_volume_pct(sum(current_levels) / len(current_levels))
        if current_level is not None:
            return current_level, "current_state_volume", fallback_reason

    return _ROOM_AUDIO_DEFAULT_VOLUME_PCT, "safe_default_volume", fallback_reason


def _resolve_person_room_tts_context(
    state: Any,
    *,
    linked_area_id: str | None,
) -> dict[str, Any]:
    """Resolve person room/composite context for room-TTS grouped behavior."""
    area_id = str(linked_area_id or "").strip()
    if not area_id:
        return {
            "resolved_composite_id": None,
            "merged_room_participation": False,
            "participating_rooms": [],
        }

    composites = list(getattr(state, "composites", {}).values())
    matches = []
    for composite in composites:
        if not bool(getattr(composite, "enabled", True)):
            continue
        area_ids = list(getattr(composite, "area_ids", []) or [])
        if area_id in area_ids:
            matches.append(composite)

    if not matches:
        return {
            "resolved_composite_id": None,
            "merged_room_participation": False,
            "participating_rooms": [area_id],
        }

    def _sort_key(item):
        primary_match = 0 if str(getattr(item, "primary_area", "") or "") == area_id else 1
        return (primary_match, str(getattr(item, "composite_id", "") or ""))

    selected = sorted(matches, key=_sort_key)[0]
    participating_rooms = list(dict.fromkeys(list(getattr(selected, "area_ids", []) or [])))
    if not participating_rooms:
        participating_rooms = [area_id]

    return {
        "resolved_composite_id": str(getattr(selected, "composite_id", "") or "") or None,
        "merged_room_participation": len(participating_rooms) > 1,
        "participating_rooms": participating_rooms,
    }


def _resolve_grouped_room_tts_speaker_map(
    state: Any,
    *,
    participating_rooms: list[str],
) -> dict[str, list[str]]:
    """Resolve per-room configured speaker mappings for grouped TTS behavior."""
    mapping: dict[str, list[str]] = {}
    for area_id in participating_rooms:
        room = getattr(state, "rooms", {}).get(area_id)
        mapping[area_id] = _resolve_room_audio_speaker_membership(room)
    return mapping


async def _async_execute_bounded_sonos_speech_lifecycle(
    hass: HomeAssistant,
    *,
    state: Any,
    area_id: str,
    target_speakers: list[str],
    room_speaker_map: dict[str, list[str]],
    tts_service_data: dict[str, Any],
    resolved_composite_id: str | None = None,
) -> dict[str, Any]:
    """Run bounded duck/speak/restore for room TTS without media continuation behavior."""
    participating_rooms = list(dict.fromkeys(list(room_speaker_map.keys())))
    grouped_validation_results: list[dict[str, Any]] = []
    valid_room_speakers: dict[str, list[str]] = {}
    speaker_to_area: dict[str, str] = {}
    for room_area_id in participating_rooms:
        configured = list(room_speaker_map.get(room_area_id, []))
        valid, validation = _validate_configured_room_speakers(hass, configured)
        valid_room_speakers[room_area_id] = list(valid)
        for speaker_id in valid:
            speaker_to_area[speaker_id] = room_area_id
        grouped_validation_results.append(
            {
                "area_id": room_area_id,
                "configured_speakers": configured,
                "validated_speakers": list(valid),
                "validation_results": validation,
            }
        )

    lifecycle_speakers = list(dict.fromkeys(item for values in valid_room_speakers.values() for item in values))
    requested_target_speakers = list(
        dict.fromkeys([item for item in target_speakers if isinstance(item, str) and item])
    )

    resolved_target_speakers: list[str] = []
    target_resolution_reason = "configured_room_speaker_authority"
    target_fallback_reason: str | None = None
    if lifecycle_speakers:
        resolved_target_speakers = [
            item for item in requested_target_speakers if item in lifecycle_speakers
        ]
        if requested_target_speakers and not resolved_target_speakers:
            # Preferred target unavailable: deterministically fall back to validated configured speakers.
            resolved_target_speakers = list(lifecycle_speakers)
            target_resolution_reason = "preferred_speaker_unavailable_fallback_to_validated_speakers"
            target_fallback_reason = "preferred_speaker_unavailable"
        elif not requested_target_speakers:
            resolved_target_speakers = list(lifecycle_speakers)
            target_resolution_reason = "configured_room_speaker_default"
    else:
        target_resolution_reason = "configured_room_authority_validation"
        validation_reasons = {
            str(item.get("reason") or "").strip()
            for grouped in grouped_validation_results
            for item in list(grouped.get("validation_results", []))
            if str(item.get("reason") or "").strip()
        }
        configured_count = sum(
            len(list(grouped.get("configured_speakers", [])))
            for grouped in grouped_validation_results
        )
        if configured_count == 0:
            target_fallback_reason = "configured_speaker_mapping_missing"
        elif "configured_speaker_unavailable" in validation_reasons:
            target_fallback_reason = "configured_speaker_unavailable"
        elif "configured_speaker_missing" in validation_reasons:
            target_fallback_reason = "configured_speaker_missing"
        elif validation_reasons:
            target_fallback_reason = "configured_speaker_invalid"
        else:
            target_fallback_reason = "no_eligible_configured_speakers"

    room_channel_resolution: dict[str, dict[str, Any]] = {}
    for room_area_id in participating_rooms or [area_id]:
        room_targets = list(valid_room_speakers.get(room_area_id, []))
        if not room_targets:
            room_targets = [item for item, mapped_area in speaker_to_area.items() if mapped_area == room_area_id]
        duck_level, duck_source, duck_fallback_reason = _resolve_room_audio_channel_level_with_fallback(
            hass,
            state=state,
            area_id=room_area_id,
            channel="duck",
            speakers=room_targets,
        )
        tts_level, tts_source, tts_fallback_reason = _resolve_room_audio_channel_level_with_fallback(
            hass,
            state=state,
            area_id=room_area_id,
            channel="tts",
            speakers=room_targets,
        )
        room_channel_resolution[room_area_id] = {
            "duck": {
                "volume_pct": duck_level,
                "source": duck_source,
                "fallback_reason": duck_fallback_reason,
            },
            "tts": {
                "volume_pct": tts_level,
                "source": tts_source,
                "fallback_reason": tts_fallback_reason,
            },
        }

    pre_duck_states: list[dict[str, Any]] = []
    for speaker_id in lifecycle_speakers:
        state_obj = hass.states.get(speaker_id)
        state_value = str(getattr(state_obj, "state", "") or "").strip().lower()
        room_area_id = speaker_to_area.get(speaker_id, area_id)
        pre_duck_states.append(
            {
                "entity_id": speaker_id,
                "area_id": room_area_id,
                "pre_state": state_value or "state_unknown",
                "pre_volume_pct": _volume_pct_from_media_state(state_obj),
            }
        )

    duck_actions: list[dict[str, Any]] = []
    for speaker_id in lifecycle_speakers:
        room_area_id = speaker_to_area.get(speaker_id, area_id)
        duck_level = int(room_channel_resolution.get(room_area_id, {}).get("duck", {}).get("volume_pct", _ROOM_AUDIO_DEFAULT_VOLUME_PCT))
        try:
            await hass.services.async_call(
                "media_player",
                "volume_set",
                {
                    "entity_id": speaker_id,
                    "volume_level": float(duck_level) / 100.0,
                },
                blocking=True,
            )
            duck_actions.append(
                {
                    "entity_id": speaker_id,
                    "area_id": room_area_id,
                    "applied": True,
                    "duck_volume_pct": duck_level,
                    "reason": "duck_applied",
                }
            )
        except Exception as err:
            duck_actions.append(
                {
                    "entity_id": speaker_id,
                    "area_id": room_area_id,
                    "applied": False,
                    "duck_volume_pct": duck_level,
                    "reason": "duck_failed",
                    "error": str(err),
                }
            )

    speech_actions: list[dict[str, Any]] = []
    for target_speaker in resolved_target_speakers:
        room_area_id = speaker_to_area.get(target_speaker, area_id)
        tts_level = int(room_channel_resolution.get(room_area_id, {}).get("tts", {}).get("volume_pct", _ROOM_AUDIO_DEFAULT_VOLUME_PCT))
        tts_volume_applied = False
        delivery_error: str | None = None
        try:
            await hass.services.async_call(
                "media_player",
                "volume_set",
                {
                    "entity_id": target_speaker,
                    "volume_level": float(tts_level) / 100.0,
                },
                blocking=True,
            )
            tts_volume_applied = True
        except Exception as err:
            delivery_error = f"tts_volume_set_failed: {err}"

        if delivery_error is None:
            try:
                payload = dict(tts_service_data)
                payload["media_player_entity_id"] = target_speaker
                await hass.services.async_call("tts", "speak", payload, blocking=True)
            except Exception as err:
                delivery_error = f"tts_speak_failed: {err}"

        speech_actions.append(
            {
                "entity_id": target_speaker,
                "area_id": room_area_id,
                "volume_pct": tts_level,
                "tts_volume_applied": tts_volume_applied,
                "delivery_succeeded": delivery_error is None,
                "delivery_error": delivery_error,
            }
        )

    restore_actions: list[dict[str, Any]] = []
    for item in pre_duck_states:
        speaker_id = str(item.get("entity_id") or "").strip()
        pre_volume_pct = _coerce_volume_pct(item.get("pre_volume_pct"))
        if not speaker_id or pre_volume_pct is None:
            restore_actions.append(
                {
                    "entity_id": speaker_id,
                    "restored": False,
                    "reason": "pre_volume_unavailable",
                }
            )
            continue
        try:
            await hass.services.async_call(
                "media_player",
                "volume_set",
                {
                    "entity_id": speaker_id,
                    "volume_level": float(pre_volume_pct) / 100.0,
                },
                blocking=True,
            )
            restore_actions.append(
                {
                    "entity_id": speaker_id,
                    "restored": True,
                    "restored_volume_pct": pre_volume_pct,
                    "reason": "pre_duck_volume_restored",
                }
            )
        except Exception as err:
            restore_actions.append(
                {
                    "entity_id": speaker_id,
                    "restored": False,
                    "restored_volume_pct": pre_volume_pct,
                    "reason": "restore_failed",
                    "error": str(err),
                }
            )

    failure_reason: str | None = None
    if not speech_actions:
        failure_reason = target_fallback_reason or "no_target_speakers_available"
    elif any(not item.get("delivery_succeeded") for item in speech_actions):
        failure_reason = "speech_delivery_failed"
    elif any(not item.get("applied") for item in duck_actions):
        failure_reason = "duck_partial_failure"
    elif any(not item.get("restored") for item in restore_actions):
        failure_reason = "restore_partial_failure"

    duck_fallback_reason = any(
        bool(room_channel_resolution.get(room_area_id, {}).get("duck", {}).get("fallback_reason"))
        for room_area_id in room_channel_resolution
    )
    tts_fallback_reason = any(
        bool(room_channel_resolution.get(room_area_id, {}).get("tts", {}).get("fallback_reason"))
        for room_area_id in room_channel_resolution
    )

    primary_room = area_id if area_id in room_channel_resolution else (participating_rooms[0] if participating_rooms else area_id)

    return {
        "bounded": True,
        "policy_name": _SONOS_SPEECH_CONTINUITY_POLICY_NAME,
        "area_id": area_id,
        "resolved_composite_id": resolved_composite_id,
        "merged_room_participation": bool(resolved_composite_id) or len(participating_rooms) > 1,
        "participating_rooms": participating_rooms,
        "group_targeted_speakers": list(resolved_target_speakers),
        "target_resolution": {
            "requested_target_speakers": list(requested_target_speakers),
            "resolved_target_speakers": list(resolved_target_speakers),
            "decision_reason": target_resolution_reason,
            "fallback_reason": target_fallback_reason,
            "fallback_source": _SONOS_SPEECH_FALLBACK_POLICY_SOURCE if target_fallback_reason else None,
        },
        "configured_room_speaker_map": {key: list(value) for key, value in room_speaker_map.items()},
        "validated_room_speaker_map": {key: list(value) for key, value in valid_room_speakers.items()},
        "grouped_validation_results": grouped_validation_results,
        "pre_duck_states": pre_duck_states,
        "duck": {
            "volume_pct": int(room_channel_resolution.get(primary_room, {}).get("duck", {}).get("volume_pct", _ROOM_AUDIO_DEFAULT_VOLUME_PCT)),
            "source": str(room_channel_resolution.get(primary_room, {}).get("duck", {}).get("source", "safe_default_volume")),
            "fallback_reason": room_channel_resolution.get(primary_room, {}).get("duck", {}).get("fallback_reason"),
            "fallback_source": _SONOS_SPEECH_FALLBACK_POLICY_SOURCE,
            "actions": duck_actions,
            "room_channel_resolution": [
                {
                    "area_id": room_area_id,
                    "volume_pct": int(item.get("duck", {}).get("volume_pct", _ROOM_AUDIO_DEFAULT_VOLUME_PCT)),
                    "source": str(item.get("duck", {}).get("source", "safe_default_volume")),
                    "fallback_reason": item.get("duck", {}).get("fallback_reason"),
                }
                for room_area_id, item in room_channel_resolution.items()
            ],
        },
        "speech": {
            "volume_pct": int(room_channel_resolution.get(primary_room, {}).get("tts", {}).get("volume_pct", _ROOM_AUDIO_DEFAULT_VOLUME_PCT)),
            "source": str(room_channel_resolution.get(primary_room, {}).get("tts", {}).get("source", "safe_default_volume")),
            "fallback_reason": room_channel_resolution.get(primary_room, {}).get("tts", {}).get("fallback_reason"),
            "fallback_source": _SONOS_SPEECH_FALLBACK_POLICY_SOURCE,
            "delivery_attempted": bool(speech_actions),
            "tts_volume_applied": all(bool(item.get("tts_volume_applied")) for item in speech_actions),
            "delivery_succeeded": bool(speech_actions) and all(bool(item.get("delivery_succeeded")) for item in speech_actions),
            "delivery_error": (
                next((item.get("delivery_error") for item in speech_actions if item.get("delivery_error")), None)
                if speech_actions
                else "no_target_speakers_available"
            ),
            "actions": speech_actions,
            "room_channel_resolution": [
                {
                    "area_id": room_area_id,
                    "volume_pct": int(item.get("tts", {}).get("volume_pct", _ROOM_AUDIO_DEFAULT_VOLUME_PCT)),
                    "source": str(item.get("tts", {}).get("source", "safe_default_volume")),
                    "fallback_reason": item.get("tts", {}).get("fallback_reason"),
                }
                for room_area_id, item in room_channel_resolution.items()
            ],
        },
        "restore": {
            "actions": restore_actions,
            "media_continuation_performed": False,
            "playback_resume_performed": False,
            "manual_stop_respected": True,
        },
        "failure_reason": failure_reason,
        "fallback_used": bool(duck_fallback_reason or tts_fallback_reason or target_fallback_reason or failure_reason),
        "fallback_path": "bounded_duck_restore_fallback" if (duck_fallback_reason or tts_fallback_reason or target_fallback_reason or failure_reason) else "none",
    }


def _resolve_lighting_capability_mapping(room: Any, command_kind: str) -> dict[str, Any]:
    """Resolve configured room capability mapping for room-aware lighting commands."""
    if room is None:
        return {
            "ok": False,
            "failure_reason": "room_configuration_missing",
            "capability": "lighting",
            "membership_field": None,
            "configured_membership": [],
            "room_source": "room_configuration",
            "capability_source": _USUAL_LIGHTING_VALIDATION_SOURCE,
        }

    if command_kind == "lamps":
        membership_field = "lamp_entity_ids"
        capability = "lamps"
    elif command_kind == "lights":
        membership_field = "light_entity_ids"
        capability = "lights"
    elif command_kind in {"resume", "usual"}:
        membership_field = "light_entity_ids|lamp_entity_ids"
        capability = "lighting"
    else:
        return {
            "ok": False,
            "failure_reason": "lighting_command_not_supported",
            "capability": "lighting",
            "membership_field": None,
            "configured_membership": [],
            "room_source": "room_configuration",
            "capability_source": _USUAL_LIGHTING_VALIDATION_SOURCE,
        }

    configured_membership = _resolve_usual_lighting_membership(room, command_kind)
    lamp_membership = _room_entity_ids(room, "lamp_entity_ids")
    light_membership = _room_entity_ids(room, "light_entity_ids")

    if command_kind == "lamps" and not configured_membership and light_membership:
        return {
            "ok": False,
            "failure_reason": "lighting_command_not_supported_by_configured_room_capability",
            "capability": capability,
            "membership_field": membership_field,
            "configured_membership": [],
            "room_source": "room_configuration",
            "capability_source": _USUAL_LIGHTING_VALIDATION_SOURCE,
        }

    if command_kind == "lights" and not configured_membership and lamp_membership:
        return {
            "ok": False,
            "failure_reason": "lighting_command_not_supported_by_configured_room_capability",
            "capability": capability,
            "membership_field": membership_field,
            "configured_membership": [],
            "room_source": "room_configuration",
            "capability_source": _USUAL_LIGHTING_VALIDATION_SOURCE,
        }

    if not configured_membership:
        return {
            "ok": False,
            "failure_reason": "configured_capability_mapping_missing",
            "capability": capability,
            "membership_field": membership_field,
            "configured_membership": [],
            "room_source": "room_configuration",
            "capability_source": _USUAL_LIGHTING_VALIDATION_SOURCE,
        }

    return {
        "ok": True,
        "failure_reason": None,
        "capability": capability,
        "membership_field": membership_field,
        "configured_membership": configured_membership,
        "room_source": "room_configuration",
        "capability_source": _USUAL_LIGHTING_VALIDATION_SOURCE,
    }


def _validate_configured_lighting_entities(
    hass: HomeAssistant,
    configured_membership: list[str],
) -> tuple[list[str], list[dict[str, Any]]]:
    """Validate configured lighting entities without redefining room membership authority."""
    registry = er.async_get(hass)
    valid_targets: list[str] = []
    validations: list[dict[str, Any]] = []

    for entity_id in configured_membership:
        normalized = str(entity_id or "").strip()
        if not normalized:
            validations.append(
                {
                    "entity_id": normalized,
                    "valid": False,
                    "status": "invalid_entity",
                    "reason": "configured_entity_invalid",
                }
            )
            continue

        if not normalized.startswith("light."):
            validations.append(
                {
                    "entity_id": normalized,
                    "valid": False,
                    "status": "invalid_entity",
                    "reason": "configured_entity_invalid",
                }
            )
            continue

        state_obj = hass.states.get(normalized)
        registry_entry = registry.async_get(normalized)
        if state_obj is None and registry_entry is None:
            validations.append(
                {
                    "entity_id": normalized,
                    "valid": False,
                    "status": "missing_entity",
                    "reason": "configured_entity_missing",
                }
            )
            continue

        if state_obj is None:
            validations.append(
                {
                    "entity_id": normalized,
                    "valid": False,
                    "status": "missing_state",
                    "reason": "configured_entity_missing",
                }
            )
            continue

        state_value = str(getattr(state_obj, "state", "") or "").strip().lower()
        if state_value in _USUAL_LIGHTING_UNAVAILABLE_STATES:
            validations.append(
                {
                    "entity_id": normalized,
                    "valid": False,
                    "status": "unavailable_entity",
                    "reason": "configured_device_unavailable",
                }
            )
            continue

        attributes = getattr(state_obj, "attributes", {}) or {}
        if isinstance(attributes, dict):
            supported_color_modes = attributes.get("supported_color_modes")
            if isinstance(supported_color_modes, (list, tuple, set)):
                normalized_modes = {str(mode or "").strip().lower() for mode in supported_color_modes}
                if normalized_modes and normalized_modes.issubset({"onoff"}):
                    validations.append(
                        {
                            "entity_id": normalized,
                            "valid": False,
                            "status": "unsupported_entity",
                            "reason": "unsupported_device_capability",
                        }
                    )
                    continue

            supported_features = attributes.get("supported_features")
            if isinstance(supported_features, int) and (supported_features & 1) == 0:
                validations.append(
                    {
                        "entity_id": normalized,
                        "valid": False,
                        "status": "unsupported_entity",
                        "reason": "unsupported_device_capability",
                    }
                )
                continue

        valid_targets.append(normalized)
        validations.append(
            {
                "entity_id": normalized,
                "valid": True,
                "status": "validated",
                "reason": "configured_entity_valid",
            }
        )

    return valid_targets, validations


def _resolve_lighting_fallback_decision(
    *,
    failure_reason: str | None,
    validation_results: list[dict[str, Any]],
) -> tuple[str, str, str]:
    """Resolve deterministic fallback decision labels for #401 degraded lighting paths."""
    normalized = str(failure_reason or "").strip() or "no_eligible_lighting_targets"
    if normalized == "lighting_command_not_supported_by_configured_room_capability":
        return (
            normalized,
            "safe_command_rejection",
            "configured_room_capability_authority",
        )
    if normalized == "lighting_command_not_supported":
        return (
            normalized,
            "safe_command_rejection",
            "lighting_command_support_policy",
        )
    if normalized == "unsupported_device_capability":
        return (
            normalized,
            "safe_noop",
            "device_capability_validation",
        )
    if normalized in {
        "room_configuration_missing",
        "configured_capability_mapping_missing",
        "configured_entity_missing",
        "configured_entity_invalid",
        "configured_device_unavailable",
        "no_eligible_lighting_targets",
    }:
        return (
            normalized,
            "safe_noop",
            "configured_room_authority_validation",
        )

    if validation_results:
        return (
            normalized,
            "safe_noop",
            "configured_room_authority_validation",
        )
    return (
        normalized,
        "safe_noop",
        "lighting_degraded_path_default",
    )


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
        if entity_id and _TTS_DATA_COMPONENT in hass.data:
            entity_component = hass.data[_TTS_DATA_COMPONENT]
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


def _resolve_preference_hierarchy(request: PreferenceResolutionRequest) -> PreferenceResolutionOutcome:
    """Resolve a preference request using the governed EC-B-01 precedence hierarchy."""
    normalized_request = request if isinstance(request, PreferenceResolutionRequest) else PreferenceResolutionRequest.from_dict(dict(request))
    identity_state = normalized_request.identity_state
    confidence_band = normalized_request.confidence_band
    policy_allowed = bool(normalized_request.personalization_policy_allowed)
    policy_reason = str(normalized_request.personalization_policy_reason or "").strip().lower() or "policy_allows"
    confidence_band_value = (
        str(confidence_band.value if hasattr(confidence_band, "value") else confidence_band or "")
        .strip()
        .lower()
        if confidence_band is not None
        else ""
    )

    personalization_allowed = (
        identity_state is PreferenceIdentityState.KNOWN
        and confidence_band_value != "low"
        and policy_allowed
    )
    if identity_state in {
        PreferenceIdentityState.GUEST,
        PreferenceIdentityState.UNKNOWN,
        PreferenceIdentityState.UNAVAILABLE,
        PreferenceIdentityState.LOW_CONFIDENCE,
    }:
        personalization_allowed = False
    if confidence_band_value == "low":
        personalization_allowed = False
    if not policy_allowed:
        personalization_allowed = False

    if identity_state is PreferenceIdentityState.GUEST:
        identity_reason = "guest_identity_blocked"
    elif identity_state is PreferenceIdentityState.UNKNOWN:
        identity_reason = "unknown_identity_blocked"
    elif identity_state is PreferenceIdentityState.UNAVAILABLE:
        identity_reason = "unavailable_identity_blocked"
    elif identity_state is PreferenceIdentityState.LOW_CONFIDENCE:
        identity_reason = "low_confidence_identity_blocked"
    elif not policy_allowed:
        identity_reason = "identity_policy_disallowed"
    elif not personalization_allowed:
        identity_reason = "identity_policy_blocked"
    else:
        identity_reason = "known_person_allowed"

    applied_policy = {
        "policy_name": "experience_continuity_preference_resolution",
        "precedence_order": [tier.value for tier in PreferenceResolutionTier],
        "identity_gating_enabled": True,
        "personalization_policy_required": True,
        "personalization_policy_allowed": policy_allowed,
        "personalization_policy_reason": policy_reason,
        "person_room_exception_enabled": normalized_request.person_room_exception_enabled,
        "person_preferences_portable_across_rooms": True,
        "room_media_context_remains_room_scoped": True,
        "command_and_guardrail_override_personalization": True,
    }
    identity_decision = {
        "identity_state": identity_state.value,
        "confidence_band": confidence_band.value if confidence_band is not None else None,
        "personalization_allowed": personalization_allowed,
        "policy_allowed": policy_allowed,
        "policy_reason": policy_reason,
        "safety_mode": "standard" if personalization_allowed else "fail_closed",
        "reason_code": identity_reason,
    }

    tier_inputs: list[tuple[PreferenceResolutionTier, str, Any, bool, str]] = [
        (PreferenceResolutionTier.COMMAND, "command", normalized_request.command_value, True, "command_override"),
        (PreferenceResolutionTier.GUARDRAIL, "policy", normalized_request.guardrail_value, True, "guardrail_override"),
        (
            PreferenceResolutionTier.KNOWN_PERSON_PREFERENCE,
            "person",
            normalized_request.person_preference_value,
            personalization_allowed,
            identity_reason if not personalization_allowed else "known_person_preference_applied",
        ),
        (
            PreferenceResolutionTier.EXPLICIT_PERSON_ROOM_EXCEPTION,
            "person_room",
            normalized_request.person_room_exception_value,
            personalization_allowed and normalized_request.person_room_exception_enabled,
            "person_room_exception_disabled"
            if not normalized_request.person_room_exception_enabled
            else (identity_reason if not personalization_allowed else "explicit_person_room_exception_applied"),
        ),
        (PreferenceResolutionTier.ROOM_DEFAULT, "room", normalized_request.room_default_value, True, "room_default_selected"),
        (
            PreferenceResolutionTier.HOUSEHOLD_DEFAULT,
            "household",
            normalized_request.household_default_value,
            True,
            "household_default_selected",
        ),
        (
            PreferenceResolutionTier.SYSTEM_SAFE_DEFAULT,
            "system",
            normalized_request.system_safe_value,
            True,
            "system_safe_default_selected",
        ),
    ]

    evaluation_path: list[dict[str, Any]] = []
    selected_tier = PreferenceResolutionTier.SYSTEM_SAFE_DEFAULT
    selected_scope = "system"
    selected_value: Any = normalized_request.system_safe_value
    fallback_reason: str | None = None
    rejection_reasons: list[str] = []

    for tier, scope, value, tier_allowed, reason_code in tier_inputs:
        if evaluation_path and selected_tier is not PreferenceResolutionTier.SYSTEM_SAFE_DEFAULT and evaluation_path[-1].get("selected", False):
            evaluation_path.append(
                {
                    "tier": tier.value,
                    "scope": scope,
                    "available": value is not None,
                    "selected": False,
                    "status": "skipped_by_precedence",
                    "reason_code": "higher_precedence_selected",
                    "candidate_value_present": value is not None,
                }
            )
            continue

        if tier in {
            PreferenceResolutionTier.KNOWN_PERSON_PREFERENCE,
            PreferenceResolutionTier.EXPLICIT_PERSON_ROOM_EXCEPTION,
        } and not tier_allowed:
            rejection_reasons.append(reason_code)
            evaluation_path.append(
                {
                    "tier": tier.value,
                    "scope": scope,
                    "available": value is not None,
                    "selected": False,
                    "status": "rejected",
                    "reason_code": reason_code,
                    "candidate_value_present": value is not None,
                }
            )
            continue

        if value is None:
            evaluation_path.append(
                {
                    "tier": tier.value,
                    "scope": scope,
                    "available": False,
                    "selected": False,
                    "status": "rejected",
                    "reason_code": "candidate_missing",
                    "candidate_value_present": False,
                }
            )
            continue

        selected_tier = tier
        selected_scope = scope
        selected_value = value
        evaluation_path.append(
            {
                "tier": tier.value,
                "scope": scope,
                "available": True,
                "selected": True,
                "status": "selected",
                "reason_code": reason_code,
                "candidate_value_present": True,
            }
        )
        break

    if selected_tier in {PreferenceResolutionTier.ROOM_DEFAULT, PreferenceResolutionTier.HOUSEHOLD_DEFAULT, PreferenceResolutionTier.SYSTEM_SAFE_DEFAULT}:
        fallback_reason = rejection_reasons[0] if rejection_reasons else next(
            (entry["reason_code"] for entry in evaluation_path if entry.get("selected", False)),
            None,
        )

    ownership_boundary = {
        "person_preference_scope": "person",
        "person_room_exception_scope": "person_room",
        "room_default_scope": "room",
        "household_default_scope": "household",
        "system_safe_scope": "system",
        "person_preference_portable_across_rooms": True,
        "room_media_context_remains_room_scoped": True,
        "room_history_not_reused_as_person_preference": True,
    }

    outcome_metadata = dict(normalized_request.metadata)
    outcome_metadata["selected_source"] = selected_tier.value
    outcome_metadata["fallback_target"] = selected_tier.value if fallback_reason is not None else None

    return PreferenceResolutionOutcome(
        preference_key=normalized_request.preference_key,
        selected_tier=selected_tier,
        selected_scope=selected_scope,
        selected_value=selected_value,
        evaluation_path=evaluation_path,
        applied_policy=applied_policy,
        identity_decision=identity_decision,
        fallback_reason=fallback_reason,
        ownership_boundary=ownership_boundary,
        metadata=outcome_metadata,
    )


def _evaluate_learning_policy(
    request: LearningPolicyEvaluationRequest,
) -> LearningPolicyEvaluationOutcome:
    """Evaluate governed learning eligibility using EC-B-03 fail-closed policy rules."""
    normalized_request = (
        request
        if isinstance(request, LearningPolicyEvaluationRequest)
        else LearningPolicyEvaluationRequest.from_dict(dict(request))
    )
    identity_state = normalized_request.identity_state
    ownership_scope = normalized_request.ownership_scope
    confidence_band = normalized_request.confidence_band
    identity_sensitive_learning = bool(normalized_request.identity_sensitive_learning)
    confidence_band_value = (
        str(confidence_band.value if hasattr(confidence_band, "value") else confidence_band or "")
        .strip()
        .lower()
        if confidence_band is not None
        else ""
    )
    policy_reason = str(normalized_request.policy_reason or "").strip().lower() or _LEARNING_POLICY_REASON_ALLOW
    storage_target = _LEARNING_SCOPE_STORAGE_TARGET.get(ownership_scope, "unsupported")

    denial_reason: str | None = None
    if not normalized_request.learning_policy_enabled:
        denial_reason = "learning_policy_disabled"
    elif identity_sensitive_learning and identity_state in _LEARNING_DENIAL_IDENTITY_REASONS:
        denial_reason = _LEARNING_DENIAL_IDENTITY_REASONS[identity_state]
    elif identity_sensitive_learning and confidence_band_value == "low":
        denial_reason = "low_confidence_identity_blocked"
    elif ownership_scope is LearningOwnershipScope.PERSON and not normalized_request.personalization_policy_allowed:
        denial_reason = "identity_policy_disallowed"
    elif not normalized_request.ownership_supported:
        denial_reason = "unsupported_ownership_scope"
    elif not normalized_request.entity_eligible:
        denial_reason = "entity_ineligible"
    elif not normalized_request.preference_eligible:
        denial_reason = "preference_ineligible"
    elif not normalized_request.safety_restrictions_clear:
        denial_reason = "unsafe_learning_context"

    learning_allowed = denial_reason is None
    write_path = LearningWritePath.ASYNC if learning_allowed else LearningWritePath.NONE
    evaluated_at = datetime.now(timezone.utc).isoformat()
    reversibility_metadata = {
        "learning_source": str(normalized_request.metadata.get("learning_source", "concierge_interaction") or "concierge_interaction"),
        "owner_scope": ownership_scope.value,
        "timestamp": evaluated_at,
        "reason": denial_reason or _LEARNING_POLICY_REASON_ALLOW,
        "policy_used": _LEARNING_POLICY_NAME,
        "rollback_supporting_metadata": True,
    }

    policy_decision = {
        "policy_name": _LEARNING_POLICY_NAME,
        "learning_allowed": learning_allowed,
        "denial_reason": denial_reason,
        "identity_state": identity_state.value,
        "confidence_band": confidence_band.value if confidence_band is not None else None,
        "learning_policy_enabled": bool(normalized_request.learning_policy_enabled),
        "ownership_supported": bool(normalized_request.ownership_supported),
        "entity_eligible": bool(normalized_request.entity_eligible),
        "preference_eligible": bool(normalized_request.preference_eligible),
        "safety_restrictions_clear": bool(normalized_request.safety_restrictions_clear),
        "identity_sensitive_learning": identity_sensitive_learning,
        "personalization_policy_allowed": bool(normalized_request.personalization_policy_allowed),
        "policy_reason": policy_reason,
    }
    explainability = {
        "learning_allowed": learning_allowed,
        "ownership_scope": ownership_scope.value,
        "policy_result": "allowed" if learning_allowed else "denied",
        "denial_reason": denial_reason,
        "storage_target": storage_target,
        "write_disposition": write_path.value,
    }

    metadata = dict(normalized_request.metadata)
    metadata["storage_target"] = storage_target
    metadata["write_path"] = write_path.value
    metadata["policy_name"] = _LEARNING_POLICY_NAME

    return LearningPolicyEvaluationOutcome(
        learning_key=normalized_request.learning_key,
        learning_allowed=learning_allowed,
        denial_reason=denial_reason,
        ownership_scope=ownership_scope,
        write_path=write_path,
        policy_decision=policy_decision,
        reversibility_metadata=reversibility_metadata,
        explainability=explainability,
        metadata=metadata,
    )


async def _async_commit_learning_write(
    hass: HomeAssistant,
    write_request: LearningWriteRequest,
) -> dict[str, Any]:
    """Persist one governed learning write event as an auditable activity record."""
    normalized_request = (
        write_request
        if isinstance(write_request, LearningWriteRequest)
        else LearningWriteRequest.from_dict(dict(write_request))
    )
    storage = ConciergeStorage(hass)
    activity_id = f"learn_{normalized_request.learning_event_id}"
    started_at = datetime.now(timezone.utc).isoformat()
    external_refs = [
        {
            "ref_type": "learning_write",
            "learning_event_id": normalized_request.learning_event_id,
            "learning_key": normalized_request.learning_key,
            "ownership_scope": normalized_request.ownership_scope.value,
            "owner_ref": normalized_request.owner_ref,
            "policy_used": normalized_request.policy_used,
        },
        {
            "ref_type": "learning_reversibility",
            **dict(normalized_request.reversibility_metadata),
        },
        {
            "ref_type": "learning_explainability",
            **dict(normalized_request.explainability),
        },
    ]

    await storage.async_record_activity_event(
        ActivityEvent(
            activity_id=activity_id,
            correlation_id=normalized_request.learning_event_id,
            started_at=started_at,
            channel="async_learning_write",
            actor_class="concierge",
            intent_class="experience_continuity_learning_write",
            request_summary=_sanitize_request_summary(
                "concierge",
                f"learning_key={normalized_request.learning_key};scope={normalized_request.ownership_scope.value};owner={normalized_request.owner_ref}",
            ),
            external_refs=external_refs,
        )
    )

    try:
        await storage.async_close_activity_event(
            activity_id=activity_id,
            ended_at=datetime.now(timezone.utc).isoformat(),
            outcome="success",
            outcome_reason="",
            actions_taken=["learning_write_committed"],
            policy_gates=["ec_b_03_learning_governance"],
        )
        return {
            "success": True,
            "activity_id": activity_id,
            "learning_event_id": normalized_request.learning_event_id,
            "write_path": LearningWritePath.ASYNC.value,
        }
    except Exception as err:
        await storage.async_append_activity_external_refs(
            activity_id=activity_id,
            external_refs=[
                {
                    "ref_type": "learning_write_error",
                    "error": _safe_outcome_reason(err),
                }
            ],
        )
        await storage.async_close_activity_event(
            activity_id=activity_id,
            ended_at=datetime.now(timezone.utc).isoformat(),
            outcome="error",
            outcome_reason=_safe_outcome_reason(err),
            actions_taken=["learning_write_failed"],
            policy_gates=["ec_b_03_learning_governance"],
        )
        raise


def _enqueue_learning_write(
    hass: HomeAssistant,
    write_request: LearningWriteRequest,
    *,
    commit_runner: Callable[[HomeAssistant, LearningWriteRequest], Awaitable[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Queue one governed learning write without blocking interaction flow."""
    normalized_request = (
        write_request
        if isinstance(write_request, LearningWriteRequest)
        else LearningWriteRequest.from_dict(dict(write_request))
    )
    runner = commit_runner or _async_commit_learning_write
    task = hass.async_create_task(runner(hass, normalized_request))

    def _on_done(done_task) -> None:
        try:
            _ = done_task.result()
        except Exception as err:  # pragma: no cover - log-side fallback
            _LOGGER.warning(
                "Governed learning write failed asynchronously: %s",
                _safe_outcome_reason(err),
            )

    task.add_done_callback(_on_done)
    return {
        "learning_event_id": normalized_request.learning_event_id,
        "write_path": LearningWritePath.ASYNC.value,
        "write_enqueued": True,
        "queue_ref": f"learning_queue:{normalized_request.learning_event_id}",
    }


def _resolve_usual_lighting_level(
    *,
    state: Any,
    area_id: str,
    entity_id: str,
) -> tuple[int | None, str | None, dict[str, Any] | None]:
    """Resolve one stored per-entity usual lighting level when available."""
    state_id = _usual_lighting_state_id(area_id=area_id, entity_id=entity_id)
    usual_state = None
    if state is not None and hasattr(state, "usual_states"):
        usual_state = state.usual_states.get(state_id)
    if usual_state is None:
        return None, "learned_value_missing", None

    values = dict(getattr(usual_state, "values", {}) or {})
    level = _coerce_brightness_pct(values.get("brightness_pct"))
    if level is None:
        return None, "learned_value_unavailable", usual_state.as_dict()
    return level, None, usual_state.as_dict()


async def _async_execute_learned_usual_lighting(
    hass: HomeAssistant,
    *,
    storage: ConciergeStorage,
    state,
    room,
    area_id: str,
    command_kind: str,
) -> dict[str, Any]:
    """Execute EC-C-01 room-aware learned usual lighting using configured membership only."""
    capability_mapping = _resolve_lighting_capability_mapping(room, command_kind)
    configured_membership = list(capability_mapping.get("configured_membership", []))
    validation_results: list[dict[str, Any]] = []
    member_entity_ids: list[str] = []

    if capability_mapping.get("ok", False):
        member_entity_ids, validation_results = _validate_configured_lighting_entities(
            hass,
            configured_membership,
        )
    else:
        validation_results = []

    if not capability_mapping.get("ok", False) or not member_entity_ids:
        failure_reason = str(capability_mapping.get("failure_reason") or "").strip() or "configured_device_invalid"
        if capability_mapping.get("ok", False) and not member_entity_ids:
            validation_reasons = {
                str(item.get("reason") or "").strip()
                for item in validation_results
                if str(item.get("reason") or "").strip()
            }
            if len(validation_reasons) > 1:
                failure_reason = "no_eligible_lighting_targets"
            elif any(item.get("reason") == "unsupported_device_capability" for item in validation_results):
                failure_reason = "unsupported_device_capability"
            elif any(item.get("reason") == "configured_device_unavailable" for item in validation_results):
                failure_reason = "configured_device_unavailable"
            elif any(item.get("reason") == "configured_entity_missing" for item in validation_results):
                failure_reason = "configured_entity_missing"
            elif any(item.get("reason") == "configured_entity_invalid" for item in validation_results):
                failure_reason = "configured_entity_invalid"
            else:
                failure_reason = "no_eligible_lighting_targets"

        failure_condition, deterministic_default, decision_reason = _resolve_lighting_fallback_decision(
            failure_reason=failure_reason,
            validation_results=validation_results,
        )

        return {
            "handled": True,
            "executed": False,
            "command_kind": command_kind,
            "resolved_target": f"usual_lighting:{command_kind}",
            "failure_reason": failure_reason,
            "failure_condition": failure_condition,
            "fallback_used": True,
            "fallback_path": "degraded_safe_failure",
            "fallback_source": _USUAL_LIGHTING_FALLBACK_POLICY_SOURCE,
            "deterministic_default": deterministic_default,
            "decision_reason": decision_reason,
            "room_source": capability_mapping.get("room_source", "room_configuration"),
            "capability_source": capability_mapping.get(
                "capability_source",
                _USUAL_LIGHTING_VALIDATION_SOURCE,
            ),
            "membership_source": _USUAL_LIGHTING_MEMBERSHIP_SOURCE,
            "room_membership": configured_membership,
            "targeted_entities": [],
            "validation_results": validation_results,
            "learning_decisions": [],
            "entity_outcomes": [],
            "activity_external_refs": [
                {
                    "ref_type": "learned_usual_lighting_command",
                    "policy_name": _USUAL_LIGHTING_POLICY_NAME,
                    "command_kind": command_kind,
                    "resolved_area_id": area_id,
                    "room_source": capability_mapping.get("room_source", "room_configuration"),
                    "capability_source": capability_mapping.get(
                        "capability_source",
                        _USUAL_LIGHTING_VALIDATION_SOURCE,
                    ),
                    "membership_source": _USUAL_LIGHTING_MEMBERSHIP_SOURCE,
                    "room_membership": configured_membership,
                    "targeted_entities": [],
                    "entity_validation": "failed",
                    "validation_results": validation_results,
                    "failure_reason": failure_reason,
                    "failure_condition": failure_condition,
                    "fallback_used": True,
                    "fallback_path": "degraded_safe_failure",
                    "fallback_source": _USUAL_LIGHTING_FALLBACK_POLICY_SOURCE,
                    "deterministic_default": deterministic_default,
                    "decision_reason": decision_reason,
                }
            ],
        }

    stability_seconds = _lighting_learning_stability_seconds(state)
    learning_policy_enabled = _lighting_learning_policy_enabled(state)
    learning_decisions: list[dict[str, Any]] = []
    learning_by_entity: dict[str, dict[str, Any]] = {}

    for entity_id in member_entity_ids:
        entity_state = hass.states.get(entity_id)
        brightness_pct = _brightness_pct_from_hass_state(entity_state)
        stability = _evaluate_entity_stability_for_usual_learning(
            entity_state,
            stability_seconds=stability_seconds,
        )
        stability_ok = bool(stability.get("stable", False))

        policy_outcome = _evaluate_learning_policy(
            LearningPolicyEvaluationRequest(
                learning_key=f"usual_lighting_brightness:{entity_id}",
                ownership_scope=LearningOwnershipScope.ROOM,
                identity_state=PreferenceIdentityState.UNAVAILABLE,
                confidence_band="unknown",
                learning_policy_enabled=learning_policy_enabled,
                ownership_supported=True,
                entity_eligible=brightness_pct is not None,
                preference_eligible=True,
                safety_restrictions_clear=stability_ok,
                identity_sensitive_learning=False,
                personalization_policy_allowed=True,
                policy_reason="policy_allows",
                metadata={
                    "learning_source": "lighting_stability_capture",
                    "area_id": area_id,
                    "entity_id": entity_id,
                    "membership_source": _USUAL_LIGHTING_MEMBERSHIP_SOURCE,
                    "command_kind": command_kind,
                },
            )
        )

        state_id = _usual_lighting_state_id(area_id=area_id, entity_id=entity_id)
        existing_level, _, _ = _resolve_usual_lighting_level(
            state=state,
            area_id=area_id,
            entity_id=entity_id,
        )

        learning_status = "denied"
        enqueue_info: dict[str, Any] | None = None
        if policy_outcome.learning_allowed and brightness_pct is not None and stability_ok:
            learning_event_id = f"usual_light_{uuid4().hex}"
            usual_state = UsualState(
                state_id=state_id,
                scope=ContinuityScope.ENTITY,
                scope_ref=entity_id,
                basis=UsualStateBasis.LEARNED,
                updated_at=datetime.now(timezone.utc).isoformat(),
                values={
                    "brightness_pct": brightness_pct,
                    "area_id": area_id,
                },
                event_id=learning_event_id,
                metadata={
                    "policy_name": _USUAL_LIGHTING_POLICY_NAME,
                    "policy_decision": dict(policy_outcome.policy_decision),
                    "membership_source": _USUAL_LIGHTING_MEMBERSHIP_SOURCE,
                    "stability": dict(stability),
                },
            )
            await storage.async_upsert_usual_state(usual_state)
            state.usual_states[state_id] = usual_state
            learning_status = "learned"

            enqueue_info = _enqueue_learning_write(
                hass,
                LearningWriteRequest(
                    learning_event_id=learning_event_id,
                    learning_key=f"usual_lighting_brightness:{entity_id}",
                    ownership_scope=LearningOwnershipScope.ROOM,
                    owner_ref=area_id,
                    learned_value={
                        "entity_id": entity_id,
                        "brightness_pct": brightness_pct,
                    },
                    reason_code="stable_light_level_capture",
                    policy_used=_USUAL_LIGHTING_POLICY_NAME,
                    reversibility_metadata={
                        "owner_scope": "room",
                        "area_id": area_id,
                        "entity_id": entity_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "rollback_supporting_metadata": True,
                    },
                    explainability={
                        "membership_source": _USUAL_LIGHTING_MEMBERSHIP_SOURCE,
                        "stability": dict(stability),
                        "policy_decision": dict(policy_outcome.policy_decision),
                    },
                    metadata={
                        "command_kind": command_kind,
                    },
                ),
            )
        elif existing_level is not None:
            learning_status = "denied_previous_preserved"

        decision = {
            "entity_id": entity_id,
            "learning_status": learning_status,
            "denial_reason": policy_outcome.denial_reason,
            "policy_decision": dict(policy_outcome.policy_decision),
            "stability": dict(stability),
            "captured_brightness_pct": brightness_pct,
            "previous_learned_preserved": existing_level is not None and learning_status != "learned",
            "membership_source": _USUAL_LIGHTING_MEMBERSHIP_SOURCE,
            "learning_write": enqueue_info,
        }
        learning_decisions.append(decision)
        learning_by_entity[entity_id] = decision

    entity_outcomes: list[dict[str, Any]] = []
    for entity_id in member_entity_ids:
        learned_level, learned_reason, learned_state = _resolve_usual_lighting_level(
            state=state,
            area_id=area_id,
            entity_id=entity_id,
        )
        learning_decision = learning_by_entity.get(entity_id, {})

        applied_level = learned_level
        fallback_used = False
        fallback_reason = None
        fallback_source = None

        if applied_level is None:
            fallback_used = True
            denial_reason = str(learning_decision.get("denial_reason") or "").strip()
            if learned_reason == "learned_value_unavailable":
                fallback_reason = "learned_value_unavailable"
            elif learned_reason == "learned_value_missing":
                if denial_reason in {
                    "learning_policy_disabled",
                    "identity_policy_disallowed",
                    "unsupported_ownership_scope",
                }:
                    fallback_reason = "learned_value_denied"
                else:
                    fallback_reason = "learned_value_missing"
            elif denial_reason:
                fallback_reason = "learned_value_denied"
            else:
                fallback_reason = learned_reason or "learned_value_missing"
            current_level = _brightness_pct_from_hass_state(hass.states.get(entity_id))
            if current_level is not None:
                applied_level = current_level
                fallback_source = "current_state_brightness"
            else:
                applied_level = _USUAL_LIGHTING_DEFAULT_BRIGHTNESS_PCT
                fallback_source = "safe_default_brightness"

        deterministic_default = fallback_source if fallback_used else "none"
        decision_reason = fallback_reason if fallback_used else "learned_value_applied"

        await hass.services.async_call(
            "light",
            "turn_on",
            {
                "entity_id": entity_id,
                "brightness_pct": applied_level,
            },
            blocking=True,
        )

        entity_outcomes.append(
            {
                "entity_id": entity_id,
                "applied_brightness_pct": applied_level,
                "used_learned_level": not fallback_used,
                "learned_level": learned_level,
                "learned_source": "usual_state" if learned_level is not None else None,
                "fallback_used": fallback_used,
                "fallback_path": "entity_fallback_default" if fallback_used else "none",
                "fallback_reason": fallback_reason,
                "fallback_source": fallback_source,
                "deterministic_default": deterministic_default,
                "decision_reason": decision_reason,
                "learned_state": learned_state,
                "learning_decision": learning_decision,
                "membership_source": _USUAL_LIGHTING_MEMBERSHIP_SOURCE,
            }
        )

    fallback_used = any(bool(item.get("fallback_used", False)) for item in entity_outcomes)
    fallback_path = "entity_fallback_default" if fallback_used else "none"
    deterministic_default = "per_entity_fallback" if fallback_used else "none"
    decision_reason = "learned_value_fallback_applied" if fallback_used else "learned_values_applied"

    return {
        "handled": True,
        "executed": True,
        "command_kind": command_kind,
        "resolved_target": f"usual_lighting:{command_kind}",
        "failure_reason": None,
        "failure_condition": None,
        "fallback_used": fallback_used,
        "fallback_path": fallback_path,
        "fallback_source": _USUAL_LIGHTING_FALLBACK_POLICY_SOURCE,
        "deterministic_default": deterministic_default,
        "decision_reason": decision_reason,
        "room_source": capability_mapping.get("room_source", "room_configuration"),
        "capability_source": capability_mapping.get(
            "capability_source",
            _USUAL_LIGHTING_VALIDATION_SOURCE,
        ),
        "membership_source": _USUAL_LIGHTING_MEMBERSHIP_SOURCE,
        "room_membership": configured_membership,
        "targeted_entities": list(member_entity_ids),
        "validation_results": validation_results,
        "learning_decisions": learning_decisions,
        "entity_outcomes": entity_outcomes,
        "activity_external_refs": [
            {
                "ref_type": "learned_usual_lighting_command",
                "policy_name": _USUAL_LIGHTING_POLICY_NAME,
                "command_kind": command_kind,
                "resolved_area_id": area_id,
                "room_source": capability_mapping.get("room_source", "room_configuration"),
                "capability_source": capability_mapping.get(
                    "capability_source",
                    _USUAL_LIGHTING_VALIDATION_SOURCE,
                ),
                "membership_source": _USUAL_LIGHTING_MEMBERSHIP_SOURCE,
                "room_membership": configured_membership,
                "targeted_entities": list(member_entity_ids),
                "entity_validation": "success",
                "validation_results": validation_results,
                "entity_outcomes": entity_outcomes,
                "fallback_used": fallback_used,
                "fallback_path": fallback_path,
                "fallback_source": _USUAL_LIGHTING_FALLBACK_POLICY_SOURCE,
                "deterministic_default": deterministic_default,
                "decision_reason": decision_reason,
            },
            {
                "ref_type": "learned_usual_lighting_learning",
                "policy_name": _USUAL_LIGHTING_POLICY_NAME,
                "stability_seconds": stability_seconds,
                "learning_decisions": learning_decisions,
            },
        ],
    }


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

    refusal_reason = None if decision_allowed else decision_reason
    refusal_category = _classify_refusal_category(refusal_reason)

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
            "refusal_reason": refusal_reason,
            "refusal_category": refusal_category,
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
            "person_policy_evaluated": True,
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
        "refusal_reason": refusal_reason,
        "refusal_category": refusal_category,
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


def _coerce_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _read_warning_headline_from_alerts(alerts: Any) -> str | None:
    if not isinstance(alerts, list):
        return None
    for item in alerts:
        if not isinstance(item, dict):
            continue
        headline = str(item.get("Headline", "") or "").strip()
        if headline:
            return headline
    return None


def _read_warning_headline_from_state(hass: HomeAssistant, warning_source: str) -> str | None:
    warning_state = hass.states.get(warning_source)
    if warning_state is None:
        return None

    alerts_headline = _read_warning_headline_from_alerts(warning_state.attributes.get("Alerts"))
    if alerts_headline:
        return alerts_headline

    text_candidates = [
        warning_state.attributes.get("headline"),
        warning_state.attributes.get("Headline"),
        warning_state.attributes.get("message"),
        warning_state.state,
    ]
    for candidate in text_candidates:
        text = str(candidate or "").strip()
        if not text or text.lower() in {"unknown", "unavailable", "none", "0"}:
            continue
        return text

    return None


def _normalize_weather_condition(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return text.replace("_", " ")


def _extract_forecast_field(forecast: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in forecast:
            return forecast[key]
    return None


def _extract_forecast_temperature(value: Any) -> int | None:
    if isinstance(value, dict):
        for key in ("value", "Value"):
            if key in value:
                coerced = _coerce_int(value.get(key))
                if coerced is not None:
                    return coerced
    return _coerce_int(value)


def _extract_forecast_daily_row(forecast_payload: dict[str, Any], weather_source: str) -> dict[str, Any] | None:
    source_payload = forecast_payload.get(weather_source)
    if not isinstance(source_payload, dict):
        return None

    rows = source_payload.get("forecast")
    if isinstance(rows, list) and rows:
        first = rows[0]
        if isinstance(first, dict):
            return first
    return None


def _parse_structured_forecast_row(forecast_row: dict[str, Any]) -> dict[str, Any]:
    condition = _normalize_weather_condition(
        _extract_forecast_field(forecast_row, "condition", "Condition", "summary", "Summary")
    )
    high_value = _extract_forecast_field(forecast_row, "temperature", "high", "temp_high", "high_temp")
    low_value = _extract_forecast_field(forecast_row, "templow", "low", "temp_low", "low_temp")
    humidity_value = _extract_forecast_field(forecast_row, "humidity", "Humidity")
    precipitation_value = _extract_forecast_field(
        forecast_row,
        "precipitation_probability",
        "precipitationProbability",
        "precipitation",
        "rain_probability",
    )
    wind_value = _extract_forecast_field(forecast_row, "wind_speed", "wind", "windSpeed")

    high = _extract_forecast_temperature(high_value)
    low = _extract_forecast_temperature(low_value)
    humidity = _coerce_int(humidity_value)
    precipitation_probability = _coerce_int(precipitation_value)
    wind_speed = _coerce_float(wind_value)

    wind_text = None
    if isinstance(wind_value, str):
        wind_text = wind_value.strip() or None
    if wind_text is None and wind_speed is not None:
        if wind_speed >= 15:
            wind_text = "winds will be brisk"
        elif wind_speed >= 8:
            wind_text = "winds will be moderate"
        else:
            wind_text = "winds will be light"

    parsed_fields_used = [
        field
        for field, present in (
            ("condition", condition is not None),
            ("high", high is not None),
            ("low", low is not None),
            ("humidity", humidity is not None),
            ("precipitation_probability", precipitation_probability is not None),
            ("wind", wind_text is not None),
        )
        if present
    ]

    return {
        "condition": condition,
        "high": high,
        "low": low,
        "humidity": humidity,
        "precipitation_probability": precipitation_probability,
        "wind_text": wind_text,
        "raw": dict(forecast_row),
        "parsed_fields_used": parsed_fields_used,
    }


def _build_weather_summary_speech(parsed_forecast: dict[str, Any], warning_headline: str | None) -> str:
    condition = parsed_forecast.get("condition")
    high = parsed_forecast.get("high")
    low = parsed_forecast.get("low")
    humidity = parsed_forecast.get("humidity")
    precipitation_probability = parsed_forecast.get("precipitation_probability")
    wind_text = parsed_forecast.get("wind_text")

    parts: list[str] = []
    if condition and high is not None and low is not None:
        parts.append(f"Today will be {condition} with a high near {high} and a low around {low}.")
    elif condition:
        parts.append(f"Today will be {condition}.")
    elif high is not None and low is not None:
        parts.append(f"Today has a high near {high} and a low around {low}.")

    if humidity is not None:
        parts.append(f"Humidity will be around {humidity} percent.")

    if precipitation_probability is not None:
        if precipitation_probability >= 60:
            parts.append("Rain is likely today.")
        elif precipitation_probability >= 30:
            parts.append(f"There is a {precipitation_probability} percent chance of precipitation.")

    if wind_text:
        if wind_text.endswith("."):
            parts.append(wind_text)
        else:
            parts.append(f"{wind_text.capitalize()}.")

    if warning_headline:
        parts.append(f"There is also a {warning_headline}.")

    return " ".join(parts).strip()


async def _async_fetch_structured_weather_forecast(
    hass: HomeAssistant,
    *,
    weather_source: str,
) -> tuple[bool, dict[str, Any] | None, str | None]:
    try:
        response = await hass.services.async_call(
            "weather",
            "get_forecasts",
            {"type": "daily"},
            target={"entity_id": weather_source},
            blocking=True,
            return_response=True,
        )
    except Exception as err:
        return False, None, f"forecast_service_error:{str(err).strip() or 'unknown'}"

    if not isinstance(response, dict):
        return False, None, "forecast_response_unavailable"

    return True, response, None


async def _build_room_weather_response(
    hass: HomeAssistant,
    *,
    state,
    assembled_context: dict[str, Any],
    room_authority_traceability: dict[str, Any],
) -> dict[str, Any]:
    context_area_id = assembled_context.get("context_area_id")
    room = state.rooms.get(context_area_id) if context_area_id else None

    configured_weather_sources = list(getattr(room, "weather_source_entity_ids", []) or []) if room is not None else []
    configured_news_sources = list(getattr(room, "news_source_entity_ids", []) or []) if room is not None else []
    warning_source = "sensor.nws_alerts_alerts"

    weather_source = configured_weather_sources[0] if configured_weather_sources else None
    weather_source_available = weather_source is not None

    warning_headline = _read_warning_headline_from_state(hass, warning_source)
    warning_available = bool(warning_headline)

    forecast_service_available = bool(
        weather_source and hass.services.has_service("weather", "get_forecasts")
    )
    forecast_data_available = False
    parsed_forecast: dict[str, Any] | None = None
    forecast_provider = weather_source
    fallback_reason: str | None = None

    raw_provider_text_used = False
    if weather_source and forecast_service_available:
        ok, payload, error_reason = await _async_fetch_structured_weather_forecast(
            hass,
            weather_source=weather_source,
        )
        if ok and payload is not None:
            forecast_row = _extract_forecast_daily_row(payload, weather_source)
            if forecast_row is not None:
                parsed_forecast = _parse_structured_forecast_row(forecast_row)
                forecast_data_available = bool(parsed_forecast.get("parsed_fields_used"))
            else:
                fallback_reason = "forecast_row_missing"
        else:
            fallback_reason = error_reason or "forecast_unavailable"
    elif weather_source and not forecast_service_available:
        fallback_reason = "forecast_service_unavailable"
    else:
        fallback_reason = "configured_weather_source_missing"

    weather_response_strategy = "forecast_warning_combined"
    generated_speech = ""

    if forecast_data_available and parsed_forecast is not None:
        generated_speech = _build_weather_summary_speech(parsed_forecast, warning_headline)
        weather_response_strategy = "forecast_structured_with_warning" if warning_available else "forecast_structured_only"
    elif warning_available:
        generated_speech = f"I cannot reach the configured forecast right now. There is also a {warning_headline}."
        weather_response_strategy = "warning_only_fallback"
        if fallback_reason is None:
            fallback_reason = "forecast_unavailable_warning_available"
    else:
        if weather_source_available:
            generated_speech = "I cannot reach the configured forecast right now, but I will keep trying from your room weather source."
            weather_response_strategy = "graceful_forecast_fallback"
            if fallback_reason is None:
                fallback_reason = "forecast_unavailable"
        else:
            generated_speech = "I do not have a configured weather source for this room yet."
            weather_response_strategy = "configured_source_missing_fallback"
            if fallback_reason is None:
                fallback_reason = "configured_weather_source_missing"

    # Keep warning delivery calm and bounded.
    if warning_headline and "warning" in warning_headline.lower():
        warning_headline = re.sub(r"\s+", " ", warning_headline).strip()

    return {
        "weather_source": weather_source,
        "configured_weather_sources": configured_weather_sources,
        "configured_news_sources": configured_news_sources,
        "forecast_provider": forecast_provider,
        "forecast_data_available": forecast_data_available,
        "warning_source": warning_source,
        "warning_available": warning_available,
        "warning_headline": warning_headline,
        "weather_response_strategy": weather_response_strategy,
        "fallback_reason": fallback_reason,
        "parsed_forecast": parsed_forecast,
        "generated_speech": generated_speech,
        "raw_provider_text_used": raw_provider_text_used,
        "forecast_service_available": forecast_service_available,
        "weather_source_available": weather_source_available,
        "room_authority_source": room_authority_traceability.get("room_authority_source", "room_configuration"),
    }


def _optional_text_field(value: Any) -> str | None:
    """Normalize one optional text field to a stripped value or None."""
    text = str(value or "").strip()
    return text or None


def _optional_int_field(value: Any) -> int | None:
    """Normalize one optional integer field to int or None."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_conversation_input_context(
    *,
    call_data: dict[str, Any],
    raw_context: Any,
) -> dict[str, Any]:
    """Normalize ConversationInput-style metadata from service and context payloads."""
    context = dict(raw_context) if isinstance(raw_context, dict) else {}

    def _pick(name: str) -> Any:
        direct = call_data.get(name)
        if direct is not None:
            return direct
        return context.get(name)

    normalized = {
        "conversation_id": _optional_text_field(_pick("conversation_id")),
        "device_id": _optional_text_field(_pick("device_id")),
        "satellite_id": _optional_text_field(_pick("satellite_id")),
        "agent_id": _optional_text_field(_pick("agent_id")),
        "language": _optional_text_field(_pick("language")),
        "text": _optional_text_field(_pick("text")),
        "pipeline_id": _optional_text_field(_pick("pipeline_id")),
        "turn_index": _optional_int_field(_pick("turn_index")),
    }
    normalized["has_conversation_input"] = any(
        normalized.get(key) is not None
        for key in (
            "conversation_id",
            "device_id",
            "satellite_id",
            "agent_id",
            "language",
            "text",
        )
    )
    return normalized


def _resolve_foundation_area_from_conversation_input(
    hass: HomeAssistant,
    *,
    requested_area_id: str | None,
    device_id: str | None,
    satellite_id: str | None,
) -> tuple[str | None, str]:
    """Resolve room area through Foundation registries from correlation context."""
    requested = _optional_text_field(requested_area_id)
    if requested:
        return requested, "explicit_area_id"

    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    candidate_device_ids: list[str] = []
    device = _optional_text_field(device_id)
    if device:
        candidate_device_ids.append(device)

    satellite = _optional_text_field(satellite_id)
    if satellite and "." in satellite:
        satellite_entry = entity_registry.async_get(satellite)
        if satellite_entry is not None:
            if satellite_entry.area_id:
                return satellite_entry.area_id, "foundation_entity_registry"
            if satellite_entry.device_id:
                candidate_device_ids.append(satellite_entry.device_id)

    if satellite and "." not in satellite:
        candidate_device_ids.append(satellite)

    deduped_device_ids: list[str] = []
    for item in candidate_device_ids:
        if item and item not in deduped_device_ids:
            deduped_device_ids.append(item)

    for candidate_device_id in deduped_device_ids:
        device_entry = device_registry.async_get(candidate_device_id)
        if device_entry is None:
            continue
        if device_entry.area_id:
            return device_entry.area_id, "foundation_device_registry"

        linked_entities = er.async_entries_for_device(entity_registry, candidate_device_id)
        for linked_entity in linked_entities:
            linked_area_id = _optional_text_field(getattr(linked_entity, "area_id", None))
            if linked_area_id:
                return linked_area_id, "foundation_entity_registry"

    return None, "foundation_room_unresolved"


def _build_conversation_agent_ingress_adapter(
    hass: HomeAssistant,
    *,
    call_data: dict[str, Any],
    raw_context: Any,
    requested_area_id: str | None,
) -> dict[str, Any]:
    """Build a dedicated Conversation Agent ingress adapter payload."""
    normalized = _normalize_conversation_input_context(
        call_data=call_data,
        raw_context=raw_context,
    )
    resolved_area_id, room_resolution_source = _resolve_foundation_area_from_conversation_input(
        hass,
        requested_area_id=requested_area_id,
        device_id=normalized.get("device_id"),
        satellite_id=normalized.get("satellite_id"),
    )

    has_conversation_input = bool(normalized.get("has_conversation_input", False))
    return {
        "ingress_mode": (
            "conversation_agent_runtime_ingress"
            if has_conversation_input
            else "fallback_service_or_automation"
        ),
        "identity_authority": (
            "voice_identity_lookup"
            if has_conversation_input
            else "non_authoritative_fallback"
        ),
        "has_conversation_input": has_conversation_input,
        "correlation": {
            "conversation_id": normalized.get("conversation_id"),
            "device_id": normalized.get("device_id"),
            "satellite_id": normalized.get("satellite_id"),
            "agent_id": normalized.get("agent_id"),
            "language": normalized.get("language"),
            "text": normalized.get("text"),
            "pipeline_id": normalized.get("pipeline_id"),
            "turn_index": normalized.get("turn_index"),
        },
        "foundation_room_resolution": {
            "resolved_area_id": resolved_area_id,
            "resolution_source": room_resolution_source,
        },
        "fallback_reason_code": None if has_conversation_input else "identity_audio_missing",
    }


def _context_requires_voice_identity_runtime_invocation(raw_context: Any) -> bool:
    """Return whether runtime Voice Identity identity-context lookup should run."""
    if not isinstance(raw_context, dict):
        return False

    if isinstance(raw_context.get("voice_identity_identity_context"), dict):
        return False

    if isinstance(raw_context.get("identity_context"), dict):
        return False

    if bool(raw_context.get("invoke_voice_identity_runtime", False)):
        return True

    if bool(raw_context.get("require_identity_context", False)):
        return True

    if any(
        _optional_text_field(raw_context.get(key))
        for key in ("conversation_id", "device_id", "satellite_id")
    ):
        return True

    return False


def _voice_identity_request_payload(raw_context: Any) -> dict[str, Any]:
    """Build approved Voice Identity identity-context lookup payload."""
    if not isinstance(raw_context, dict):
        return {}

    payload: dict[str, Any] = {}
    for key in ("conversation_id", "device_id", "satellite_id", "pipeline_id", "room_id"):
        value = _optional_text_field(raw_context.get(key))
        if value is not None:
            payload[key] = value

    turn_index = _optional_int_field(raw_context.get("turn_index"))
    if turn_index is not None:
        payload["turn_index"] = turn_index

    return payload


def _unavailable_identity_context(reason_code: str) -> dict[str, Any]:
    """Return fail-closed identity-context payload when runtime services are unavailable."""
    return {
        "state": "unavailable",
        "person_id": None,
        "voice_profile_id": None,
        "confidence": None,
        "confidence_band": None,
        "reason_code": str(reason_code or "attribution_unavailable").strip().lower() or "attribution_unavailable",
        "source": "voice_identity",
    }


def _diagnostics_context_from_identity_lookup(
    *,
    identity_context: dict[str, Any],
    runtime_attribution: dict[str, Any],
    response_reason_code: str,
) -> dict[str, Any]:
    """Project safe diagnostics from Voice Identity identity-context lookup outputs."""
    reason_code = str(
        identity_context.get("reason_code")
        or runtime_attribution.get("reason_code")
        or response_reason_code
        or "diagnostics_unavailable"
    ).strip().lower() or "diagnostics_unavailable"
    freshness = str(runtime_attribution.get("freshness") or "").strip().lower() or None
    return {
        "diagnostic_available": True,
        "diagnostic_reason_code": reason_code,
        "health_status": "ready",
        "attribution_readiness": "ready",
        "compatibility_readiness": "ready",
        "repair_available": False,
        "repair_hint_code": None,
        "suggested_next_action_code": None,
        "freshness": freshness,
        "attribution_age_ms": runtime_attribution.get("attribution_age_ms"),
        "resolution_source": str(runtime_attribution.get("resolution_source") or "").strip().lower() or None,
        "source": "voice_identity",
    }


def _explainability_context_from_identity_lookup(
    *,
    identity_context: dict[str, Any],
    runtime_attribution: dict[str, Any],
) -> dict[str, Any]:
    """Project deterministic explainability from lookup-only Voice Identity outputs."""
    state = str(identity_context.get("state", "") or "").strip().lower()
    no_active_attribution = state in _VOICE_IDENTITY_NO_ACTIVE_ATTRIBUTION_STATES or not (
        identity_context.get("person_id") or identity_context.get("voice_profile_id")
    )

    return {
        "consumed_outcome": state or "unavailable",
        "authority_source": "voice_identity",
        "attribution_source": "voice_identity.get_identity_context",
        "confidence_source": "voice_identity.get_identity_context",
        "reason_code": str(identity_context.get("reason_code", "") or "unknown").strip().lower() or "unknown",
        "unavailable_state": "no_active_attribution" if no_active_attribution else None,
        "resolution_source": str(runtime_attribution.get("resolution_source") or "").strip().lower() or None,
        "source": "voice_identity",
    }


async def _async_consume_voice_identity_runtime_context(
    hass: HomeAssistant,
    *,
    raw_context: Any,
    voice_identity_linked: bool,
) -> dict[str, Any]:
    """Consume Voice Identity runtime identity context without local attribution logic."""
    context: dict[str, Any] = dict(raw_context) if isinstance(raw_context, dict) else {}

    if not voice_identity_linked:
        identity_context = _unavailable_identity_context("voice_identity_linkage_disabled")
        context["voice_identity_identity_context"] = identity_context
        context["identity_context"] = identity_context
        context["voice_identity_diagnostics_context"] = {
            "diagnostic_available": False,
            "diagnostic_reason_code": "voice_identity_linkage_disabled",
            "health_status": "unavailable",
            "attribution_readiness": "unavailable",
            "compatibility_readiness": "unavailable",
            "repair_available": False,
            "source": "voice_identity",
        }
        context["voice_identity_explainability_context"] = {
            "consumed_outcome": "attribution_unavailable",
            "authority_source": "voice_identity",
            "attribution_source": "voice_identity.get_identity_context",
            "confidence_source": "voice_identity.get_identity_context",
            "unavailable_state": "no_active_attribution",
            "reason_code": "voice_identity_linkage_disabled",
            "source": "voice_identity",
        }
        return context

    if not isinstance(hass.data.get(_VOICE_IDENTITY_DOMAIN), dict):
        identity_context = _unavailable_identity_context("voice_identity_not_loaded")
        context["voice_identity_identity_context"] = identity_context
        context["identity_context"] = identity_context
        return context

    if not hass.services.has_service(_VOICE_IDENTITY_DOMAIN, _VOICE_IDENTITY_SERVICE_GET_IDENTITY_CONTEXT):
        identity_context = _unavailable_identity_context("identity_context_service_unavailable")
        context["voice_identity_identity_context"] = identity_context
        context["identity_context"] = identity_context
        return context

    request_data = _voice_identity_request_payload(raw_context)

    identity_context_payload: dict[str, Any] | None = None
    runtime_attribution_payload: dict[str, Any] = {}
    response_reason_code = "identity_context_unavailable"
    try:
        response = await hass.services.async_call(
            _VOICE_IDENTITY_DOMAIN,
            _VOICE_IDENTITY_SERVICE_GET_IDENTITY_CONTEXT,
            request_data,
            blocking=True,
            return_response=True,
        )
        if isinstance(response, dict):
            response_reason_code = str(response.get("reason_code", "") or "").strip().lower() or response_reason_code
            if isinstance(response.get("identity_context"), dict):
                identity_context_payload = dict(response["identity_context"])
            if isinstance(response.get("runtime_attribution"), dict):
                runtime_attribution_payload = dict(response["runtime_attribution"])
    except Exception:
        identity_context_payload = None

    if identity_context_payload is None:
        identity_context_payload = _unavailable_identity_context("identity_context_missing")

    if not identity_context_payload.get("reason_code"):
        identity_context_payload["reason_code"] = response_reason_code

    identity_context_payload["source"] = "voice_identity"
    context["voice_identity_identity_context"] = identity_context_payload
    context["identity_context"] = identity_context_payload

    context["voice_identity_runtime_attribution"] = runtime_attribution_payload
    context["voice_identity_diagnostics_context"] = _diagnostics_context_from_identity_lookup(
        identity_context=identity_context_payload,
        runtime_attribution=runtime_attribution_payload,
        response_reason_code=response_reason_code,
    )
    context["voice_identity_explainability_context"] = _explainability_context_from_identity_lookup(
        identity_context=identity_context_payload,
        runtime_attribution=runtime_attribution_payload,
    )

    return context


def _extract_voice_identity_identity_context(raw_context: Any) -> dict[str, Any] | None:
    """Return a normalized Voice Identity identity-context payload when present."""
    if not isinstance(raw_context, dict):
        return None

    candidates: list[Any] = [
        raw_context.get("voice_identity_identity_context"),
        raw_context.get("identity_context"),
    ]
    candidates.append(raw_context)

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        source = str(candidate.get("source", "") or "").strip().lower()
        has_shape = any(
            key in candidate
            for key in (
                "state",
                "person_id",
                "voice_profile_id",
                "confidence",
                "confidence_band",
                "reason_code",
            )
        )
        if has_shape and (not source or source == "voice_identity"):
            return {
                "state": str(candidate.get("state", "") or "").strip().lower(),
                "person_id": str(candidate.get("person_id", "") or "").strip() or None,
                "voice_profile_id": str(candidate.get("voice_profile_id", "") or "").strip() or None,
                "confidence": candidate.get("confidence"),
                "confidence_band": str(candidate.get("confidence_band", "") or "").strip().lower() or None,
                "reason_code": str(candidate.get("reason_code", "") or "").strip().lower() or "unknown",
                "source": "voice_identity",
            }

    return None


def _extract_voice_identity_enrollment_lifecycle_context(raw_context: Any) -> dict[str, Any] | None:
    """Return a normalized Voice Identity enrollment/lifecycle payload when present."""
    if not isinstance(raw_context, dict):
        return None

    candidates: list[Any] = [
        raw_context.get("voice_identity_enrollment_lifecycle_context"),
        raw_context.get("voice_identity_enrollment_context"),
        raw_context.get("enrollment_lifecycle_context"),
    ]
    identity_context = raw_context.get("identity_context")
    if isinstance(identity_context, dict):
        candidates.append(identity_context)
    candidates.append(raw_context)

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        source = str(candidate.get("source", "") or "").strip().lower()
        has_shape = any(
            key in candidate
            for key in (
                "enrollment_state",
                "enrollment_readiness",
                "enrollment_lifecycle_state",
                "lifecycle_state",
                "voice_profile_lifecycle_state",
                "identity_lifecycle_state",
                "speaker_embedding_id",
            )
        )
        if has_shape and (not source or source == "voice_identity"):
            lifecycle_state = str(
                candidate.get("enrollment_lifecycle_state")
                or candidate.get("lifecycle_state")
                or ""
            ).strip().lower()
            return {
                "enrollment_state": str(candidate.get("enrollment_state", "") or "").strip().lower() or None,
                "enrollment_readiness": str(candidate.get("enrollment_readiness", "") or "").strip().lower() or None,
                "enrollment_lifecycle_state": lifecycle_state or None,
                "voice_profile_lifecycle_state": str(candidate.get("voice_profile_lifecycle_state", "") or "").strip().lower() or None,
                "identity_lifecycle_state": str(candidate.get("identity_lifecycle_state", "") or "").strip().lower() or None,
                "voice_profile_id": str(candidate.get("voice_profile_id", "") or "").strip() or None,
                "speaker_embedding_id": str(candidate.get("speaker_embedding_id", "") or "").strip() or None,
                "reason_code": str(candidate.get("reason_code", "") or "").strip().lower() or "unknown",
                "source": "voice_identity",
            }

    return None


def _extract_voice_identity_permission_context(raw_context: Any) -> dict[str, Any] | None:
    """Return a normalized Voice Identity permission/consent payload when present."""
    if not isinstance(raw_context, dict):
        return None

    candidates: list[Any] = [
        raw_context.get("voice_identity_permission_context"),
        raw_context.get("permission_context"),
        raw_context.get("consent_context"),
    ]
    identity_context = raw_context.get("identity_context")
    if isinstance(identity_context, dict):
        candidates.append(identity_context)
    candidates.append(raw_context)

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        source = str(candidate.get("source", "") or "").strip().lower()
        has_shape = any(
            key in candidate
            for key in (
                "permission_state",
                "permission_outcome",
                "permission_reason_code",
                "consent_state",
                "consent_outcome",
                "eligibility_state",
                "gating_reason",
            )
        )
        if has_shape and (not source or source == "voice_identity"):
            return {
                "permission_state": str(candidate.get("permission_state", "") or "").strip().lower() or None,
                "permission_outcome": str(candidate.get("permission_outcome", "") or "").strip().lower() or None,
                "consent_state": str(candidate.get("consent_state", "") or "").strip().lower() or None,
                "consent_outcome": str(candidate.get("consent_outcome", "") or "").strip().lower() or None,
                "eligibility_state": str(candidate.get("eligibility_state", "") or "").strip().lower() or None,
                "gating_reason": str(candidate.get("gating_reason", "") or "").strip().lower() or None,
                "reason_code": str(
                    candidate.get("permission_reason_code")
                    or candidate.get("reason_code")
                    or ""
                ).strip().lower() or "unknown",
                "lineage_ref": str(candidate.get("lineage_ref", "") or "").strip() or None,
                "source": "voice_identity",
            }

    return None


def _extract_voice_identity_legacy_disposition_context(raw_context: Any) -> dict[str, Any] | None:
    """Return a normalized Voice Identity legacy-disposition payload when present."""
    if not isinstance(raw_context, dict):
        return None

    candidates: list[Any] = [
        raw_context.get("voice_identity_legacy_disposition_context"),
        raw_context.get("legacy_disposition_context"),
        raw_context.get("legacy_context"),
    ]
    identity_context = raw_context.get("identity_context")
    if isinstance(identity_context, dict):
        candidates.append(identity_context)
    candidates.append(raw_context)

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        source = str(candidate.get("source", "") or "").strip().lower()
        has_shape = any(
            key in candidate
            for key in (
                "legacy_disposition_state",
                "legacy_disposition_outcome",
                "legacy_reference",
                "replacement_reference",
                "replacement_ref",
                "legacy_reason_code",
            )
        )
        if has_shape and (not source or source == "voice_identity"):
            return {
                "legacy_disposition_state": str(candidate.get("legacy_disposition_state", "") or "").strip().lower() or None,
                "legacy_disposition_outcome": str(candidate.get("legacy_disposition_outcome", "") or "").strip().lower() or None,
                "legacy_reference": str(candidate.get("legacy_reference", "") or "").strip() or None,
                "replacement_reference": str(
                    candidate.get("replacement_reference")
                    or candidate.get("replacement_ref")
                    or ""
                ).strip() or None,
                "reason_code": str(
                    candidate.get("legacy_reason_code")
                    or candidate.get("reason_code")
                    or ""
                ).strip().lower() or "unknown",
                "lineage_ref": str(candidate.get("lineage_ref", "") or "").strip() or None,
                "source": "voice_identity",
            }

    return None


def _extract_voice_identity_diagnostics_context(raw_context: Any) -> dict[str, Any] | None:
    """Return a normalized Voice Identity diagnostics payload when present."""
    if not isinstance(raw_context, dict):
        return None

    candidates: list[Any] = [
        raw_context.get("voice_identity_diagnostics_context"),
        raw_context.get("diagnostics_context"),
        raw_context.get("diagnostic_context"),
    ]
    identity_context = raw_context.get("identity_context")
    if isinstance(identity_context, dict):
        candidates.append(identity_context)
    candidates.append(raw_context)

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        source = str(candidate.get("source", "") or "").strip().lower()
        has_shape = any(
            key in candidate
            for key in (
                "diagnostic_available",
                "diagnostics_available",
                "diagnostic_reason_code",
                "health_status",
                "attribution_readiness",
                "compatibility_readiness",
                "repair_available",
                "repair_hint_code",
                "suggested_next_action_code",
            )
        )
        if has_shape and (not source or source == "voice_identity"):
            diagnostic_available = candidate.get("diagnostic_available")
            if diagnostic_available is None:
                diagnostic_available = candidate.get("diagnostics_available")
            return {
                "diagnostic_available": bool(diagnostic_available),
                "diagnostic_reason_code": str(
                    candidate.get("diagnostic_reason_code")
                    or candidate.get("reason_code")
                    or ""
                ).strip().lower() or "unknown",
                "health_status": str(candidate.get("health_status", "") or "").strip().lower() or None,
                "attribution_readiness": str(candidate.get("attribution_readiness", "") or "").strip().lower() or None,
                "compatibility_readiness": str(candidate.get("compatibility_readiness", "") or "").strip().lower() or None,
                "repair_available": bool(candidate.get("repair_available", False)),
                "repair_hint_code": str(candidate.get("repair_hint_code", "") or "").strip().lower() or None,
                "suggested_next_action_code": str(
                    candidate.get("suggested_next_action_code", "") or ""
                ).strip().lower() or None,
                "provenance_source": str(candidate.get("provenance_source", "") or "").strip() or None,
                "source_reference": str(candidate.get("source_reference", "") or "").strip() or None,
                "lineage_ref": str(candidate.get("lineage_ref", "") or "").strip() or None,
                "source": "voice_identity",
            }

    return None


def _extract_voice_identity_explainability_context(raw_context: Any) -> dict[str, Any] | None:
    """Return a normalized Voice Identity explainability payload when present."""
    if not isinstance(raw_context, dict):
        return None

    candidates: list[Any] = [
        raw_context.get("voice_identity_explainability_context"),
        raw_context.get("explainability_context"),
        raw_context.get("explanation_context"),
    ]
    identity_context = raw_context.get("identity_context")
    if isinstance(identity_context, dict):
        candidates.append(identity_context)
    candidates.append(raw_context)

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        source = str(candidate.get("source", "") or "").strip().lower()
        has_shape = any(
            key in candidate
            for key in (
                "consumed_outcome",
                "authority_source",
                "provenance_source",
                "source_reference",
                "lineage_ref",
                "attribution_source",
                "confidence_source",
                "enrollment_source",
                "lifecycle_source",
                "permission_source",
                "legacy_disposition_source",
                "unavailable_state",
            )
        )
        if has_shape and (not source or source == "voice_identity"):
            return {
                "consumed_outcome": str(candidate.get("consumed_outcome", "") or "").strip().lower() or None,
                "authority_source": str(candidate.get("authority_source", "") or "").strip() or "voice_identity",
                "provenance_source": str(candidate.get("provenance_source", "") or "").strip() or None,
                "source_reference": str(candidate.get("source_reference", "") or "").strip() or None,
                "lineage_ref": str(candidate.get("lineage_ref", "") or "").strip() or None,
                "attribution_source": str(candidate.get("attribution_source", "") or "").strip() or None,
                "confidence_source": str(candidate.get("confidence_source", "") or "").strip() or None,
                "enrollment_source": str(candidate.get("enrollment_source", "") or "").strip() or None,
                "lifecycle_source": str(candidate.get("lifecycle_source", "") or "").strip() or None,
                "permission_source": str(candidate.get("permission_source", "") or "").strip() or None,
                "legacy_disposition_source": str(candidate.get("legacy_disposition_source", "") or "").strip() or None,
                "unavailable_state": str(candidate.get("unavailable_state", "") or "").strip().lower() or None,
                "reason_code": str(candidate.get("reason_code", "") or "").strip().lower() or "unknown",
                "source": "voice_identity",
            }

    return None


def _build_voice_identity_attribution_confidence_consumption(
    *,
    raw_context: Any,
) -> dict[str, Any]:
    """Return bounded consumption projection for Voice Identity attribution and confidence."""
    identity_context = _extract_voice_identity_identity_context(raw_context)
    enrollment_lifecycle_context = _extract_voice_identity_enrollment_lifecycle_context(raw_context)
    permission_context = _extract_voice_identity_permission_context(raw_context)
    legacy_disposition_context = _extract_voice_identity_legacy_disposition_context(raw_context)
    diagnostics_context = _extract_voice_identity_diagnostics_context(raw_context)
    explainability_context = _extract_voice_identity_explainability_context(raw_context)

    attribution_available = bool(
        identity_context
        and str(identity_context.get("state", "") or "").strip().lower() not in _VOICE_IDENTITY_NO_ACTIVE_ATTRIBUTION_STATES
        and (
            identity_context.get("person_id") is not None
            or identity_context.get("voice_profile_id") is not None
        )
    )

    confidence_value: float | None = None
    if identity_context and identity_context.get("confidence") is not None:
        try:
            confidence_value = float(identity_context["confidence"])
        except (TypeError, ValueError):
            confidence_value = None

    confidence_band = (
        identity_context.get("confidence_band") if identity_context is not None else None
    )
    confidence_available = bool(confidence_value is not None or confidence_band)

    attribution_reason = (
        str(identity_context.get("reason_code", "unknown") or "unknown")
        if identity_context is not None
        else "attribution_data_unavailable"
    )
    confidence_reason = (
        str(identity_context.get("reason_code", "unknown") or "unknown")
        if confidence_available and identity_context is not None
        else "confidence_data_unavailable"
    )
    enrollment_consumed = bool(
        enrollment_lifecycle_context
        and (
            enrollment_lifecycle_context.get("enrollment_state") is not None
            or enrollment_lifecycle_context.get("enrollment_readiness") is not None
            or enrollment_lifecycle_context.get("voice_profile_id") is not None
            or enrollment_lifecycle_context.get("speaker_embedding_id") is not None
        )
    )
    lifecycle_consumed = bool(
        enrollment_lifecycle_context
        and (
            enrollment_lifecycle_context.get("enrollment_lifecycle_state") is not None
            or enrollment_lifecycle_context.get("voice_profile_lifecycle_state") is not None
            or enrollment_lifecycle_context.get("identity_lifecycle_state") is not None
        )
    )
    enrollment_reason = (
        str(enrollment_lifecycle_context.get("reason_code", "unknown") or "unknown")
        if enrollment_consumed and enrollment_lifecycle_context is not None
        else "enrollment_state_unavailable"
    )
    lifecycle_reason = (
        str(enrollment_lifecycle_context.get("reason_code", "unknown") or "unknown")
        if lifecycle_consumed and enrollment_lifecycle_context is not None
        else "lifecycle_state_unavailable"
    )
    permission_consumed = bool(
        permission_context
        and (
            permission_context.get("permission_state") is not None
            or permission_context.get("permission_outcome") is not None
            or permission_context.get("consent_state") is not None
            or permission_context.get("eligibility_state") is not None
        )
    )
    permission_reason = (
        str(permission_context.get("reason_code", "unknown") or "unknown")
        if permission_consumed and permission_context is not None
        else "permission_state_unavailable"
    )
    legacy_disposition_consumed = bool(
        legacy_disposition_context
        and (
            legacy_disposition_context.get("legacy_disposition_state") is not None
            or legacy_disposition_context.get("legacy_disposition_outcome") is not None
            or legacy_disposition_context.get("legacy_reference") is not None
            or legacy_disposition_context.get("replacement_reference") is not None
        )
    )
    legacy_disposition_reason = (
        str(legacy_disposition_context.get("reason_code", "unknown") or "unknown")
        if legacy_disposition_consumed and legacy_disposition_context is not None
        else "legacy_disposition_unavailable"
    )
    diagnostics_consumed = bool(
        diagnostics_context
        and (
            diagnostics_context.get("diagnostic_available")
            or diagnostics_context.get("diagnostic_reason_code") is not None
            or diagnostics_context.get("health_status") is not None
            or diagnostics_context.get("attribution_readiness") is not None
            or diagnostics_context.get("compatibility_readiness") is not None
            or diagnostics_context.get("repair_hint_code") is not None
        )
    )
    diagnostics_reason = (
        str(diagnostics_context.get("diagnostic_reason_code", "unknown") or "unknown")
        if diagnostics_consumed and diagnostics_context is not None
        else "diagnostics_surface_unavailable"
    )
    explainability_consumed = bool(
        explainability_context
        and (
            explainability_context.get("consumed_outcome") is not None
            or explainability_context.get("provenance_source") is not None
            or explainability_context.get("source_reference") is not None
            or explainability_context.get("lineage_ref") is not None
            or explainability_context.get("unavailable_state") is not None
        )
    )
    explainability_reason = (
        str(explainability_context.get("reason_code", "unknown") or "unknown")
        if explainability_consumed and explainability_context is not None
        else "explainability_surface_unavailable"
    )

    return {
        "boundary_version": 1,
        "boundary_path": "governed_voice_identity_attribution_confidence_consumption",
        "concierge_role": "bounded_consumer_orchestrator",
        "voice_identity_authority_external": True,
        "consumption_only": True,
        "consume_attribution_outcomes_only": True,
        "consume_confidence_outcomes_only": True,
        "derive_attribution_authority": False,
        "derive_confidence_authority": False,
        "calculate_attribution": False,
        "calculate_confidence": False,
        "manage_identity_lifecycle": False,
        "manage_enrollment": False,
        "attribution": {
            "consumed": attribution_available,
            "state": (
                identity_context.get("state") if identity_context is not None else "unavailable"
            ),
            "person_id": identity_context.get("person_id") if identity_context is not None else None,
            "voice_profile_id": (
                identity_context.get("voice_profile_id") if identity_context is not None else None
            ),
            "reason_code": attribution_reason,
            "source": (
                identity_context.get("source") if identity_context is not None else "voice_identity_unavailable"
            ),
        },
        "confidence": {
            "consumed": confidence_available,
            "value": confidence_value,
            "band": confidence_band,
            "reason_code": confidence_reason,
            "source": (
                identity_context.get("source") if identity_context is not None else "voice_identity_unavailable"
            ),
        },
        "enrollment_lifecycle": {
            "boundary_version": 1,
            "boundary_path": "governed_voice_identity_enrollment_lifecycle_consumption",
            "voice_identity_authority_external": True,
            "consumption_only": True,
            "consume_enrollment_state_only": True,
            "consume_lifecycle_state_only": True,
            "manage_enrollment_lifecycle": False,
            "manage_voice_profile_lifecycle": False,
            "manage_identity_lifecycle": False,
            "create_voice_profiles": False,
            "approve_enrollment": False,
            "reject_enrollment": False,
            "change_enrollment_state": False,
            "infer_enrollment_state": False,
            "enrollment": {
                "consumed": enrollment_consumed,
                "state": (
                    enrollment_lifecycle_context.get("enrollment_state")
                    if enrollment_lifecycle_context is not None
                    else "unavailable"
                ) or "unavailable",
                "readiness": (
                    enrollment_lifecycle_context.get("enrollment_readiness")
                    if enrollment_lifecycle_context is not None
                    else None
                ),
                "voice_profile_id": (
                    enrollment_lifecycle_context.get("voice_profile_id")
                    if enrollment_lifecycle_context is not None
                    else None
                ),
                "speaker_embedding_id": (
                    enrollment_lifecycle_context.get("speaker_embedding_id")
                    if enrollment_lifecycle_context is not None
                    else None
                ),
                "reason_code": enrollment_reason,
                "source": (
                    enrollment_lifecycle_context.get("source")
                    if enrollment_lifecycle_context is not None
                    else "voice_identity_unavailable"
                ),
            },
            "lifecycle": {
                "consumed": lifecycle_consumed,
                "enrollment_lifecycle_state": (
                    enrollment_lifecycle_context.get("enrollment_lifecycle_state")
                    if enrollment_lifecycle_context is not None
                    else "unavailable"
                ) or "unavailable",
                "voice_profile_lifecycle_state": (
                    enrollment_lifecycle_context.get("voice_profile_lifecycle_state")
                    if enrollment_lifecycle_context is not None
                    else None
                ),
                "identity_lifecycle_state": (
                    enrollment_lifecycle_context.get("identity_lifecycle_state")
                    if enrollment_lifecycle_context is not None
                    else None
                ),
                "reason_code": lifecycle_reason,
                "source": (
                    enrollment_lifecycle_context.get("source")
                    if enrollment_lifecycle_context is not None
                    else "voice_identity_unavailable"
                ),
            },
        },
        "permission_boundary": {
            "boundary_version": 1,
            "boundary_path": "governed_voice_identity_permission_consumption",
            "voice_identity_authority_external": True,
            "consumption_only": True,
            "consume_permission_outcomes_only": True,
            "consume_consent_outcomes_only": True,
            "derive_permission_authority": False,
            "create_permission_policy": False,
            "define_eligibility_rules": False,
            "determine_permission_outcomes": False,
            "override_voice_identity_permission_policy": False,
            "grant_permission": False,
            "revoke_permission": False,
            "approve_consent": False,
            "infer_consent": False,
            "infer_permission_state": False,
            "permission": {
                "consumed": permission_consumed,
                "state": (
                    permission_context.get("permission_state")
                    if permission_context is not None
                    else "unavailable"
                ) or "unavailable",
                "outcome": (
                    permission_context.get("permission_outcome")
                    if permission_context is not None
                    else None
                ),
                "consent_state": (
                    permission_context.get("consent_state")
                    if permission_context is not None
                    else None
                ),
                "consent_outcome": (
                    permission_context.get("consent_outcome")
                    if permission_context is not None
                    else None
                ),
                "eligibility_state": (
                    permission_context.get("eligibility_state")
                    if permission_context is not None
                    else None
                ),
                "gating_reason": (
                    permission_context.get("gating_reason")
                    if permission_context is not None
                    else None
                ),
                "lineage_ref": (
                    permission_context.get("lineage_ref")
                    if permission_context is not None
                    else None
                ),
                "reason_code": permission_reason,
                "source": (
                    permission_context.get("source")
                    if permission_context is not None
                    else "voice_identity_unavailable"
                ),
            },
        },
        "legacy_disposition_boundary": {
            "boundary_version": 1,
            "boundary_path": "governed_voice_identity_legacy_disposition_consumption",
            "voice_identity_authority_external": True,
            "consumption_only": True,
            "consume_legacy_disposition_outcomes_only": True,
            "manage_legacy_fingerprint_resolution": False,
            "migrate_legacy_identity_data": False,
            "dispose_legacy_identity_data": False,
            "determine_legacy_disposition": False,
            "infer_legacy_disposition_state": False,
            "claim_voiceprint_ownership": False,
            "claim_embedding_ownership": False,
            "establish_identity_authority": False,
            "determine_enrollment_state": False,
            "legacy_disposition": {
                "consumed": legacy_disposition_consumed,
                "state": (
                    legacy_disposition_context.get("legacy_disposition_state")
                    if legacy_disposition_context is not None
                    else "unavailable"
                ) or "unavailable",
                "outcome": (
                    legacy_disposition_context.get("legacy_disposition_outcome")
                    if legacy_disposition_context is not None
                    else None
                ),
                "legacy_reference": (
                    legacy_disposition_context.get("legacy_reference")
                    if legacy_disposition_context is not None
                    else None
                ),
                "replacement_reference": (
                    legacy_disposition_context.get("replacement_reference")
                    if legacy_disposition_context is not None
                    else None
                ),
                "lineage_ref": (
                    legacy_disposition_context.get("lineage_ref")
                    if legacy_disposition_context is not None
                    else None
                ),
                "reason_code": legacy_disposition_reason,
                "source": (
                    legacy_disposition_context.get("source")
                    if legacy_disposition_context is not None
                    else "voice_identity_unavailable"
                ),
            },
        },
        "diagnostics_boundary": {
            "boundary_version": 1,
            "boundary_path": "governed_voice_identity_diagnostics_consumption",
            "voice_identity_authority_external": True,
            "consumption_only": True,
            "consume_diagnostics_outputs_only": True,
            "consume_repair_hints_only": True,
            "diagnostics_authority_source": "voice_identity",
            "generate_diagnostics_authority": False,
            "rewrite_voice_identity_diagnostics": False,
            "calculate_health_status": False,
            "calculate_readiness": False,
            "generate_repair_hints": False,
            "diagnostics": {
                "consumed": diagnostics_consumed,
                "diagnostic_available": (
                    diagnostics_context.get("diagnostic_available")
                    if diagnostics_context is not None
                    else False
                ),
                "diagnostic_reason_code": diagnostics_reason,
                "health_status": (
                    diagnostics_context.get("health_status")
                    if diagnostics_context is not None
                    else "unavailable"
                ) or "unavailable",
                "attribution_readiness": (
                    diagnostics_context.get("attribution_readiness")
                    if diagnostics_context is not None
                    else None
                ),
                "compatibility_readiness": (
                    diagnostics_context.get("compatibility_readiness")
                    if diagnostics_context is not None
                    else None
                ),
                "repair_available": (
                    diagnostics_context.get("repair_available")
                    if diagnostics_context is not None
                    else False
                ),
                "repair_hint_code": (
                    diagnostics_context.get("repair_hint_code")
                    if diagnostics_context is not None
                    else None
                ),
                "suggested_next_action_code": (
                    diagnostics_context.get("suggested_next_action_code")
                    if diagnostics_context is not None
                    else None
                ),
                "provenance_source": (
                    diagnostics_context.get("provenance_source")
                    if diagnostics_context is not None
                    else None
                ),
                "source_reference": (
                    diagnostics_context.get("source_reference")
                    if diagnostics_context is not None
                    else None
                ),
                "lineage_ref": (
                    diagnostics_context.get("lineage_ref")
                    if diagnostics_context is not None
                    else None
                ),
                "source": (
                    diagnostics_context.get("source")
                    if diagnostics_context is not None
                    else "voice_identity_unavailable"
                ),
            },
        },
        "explainability_boundary": {
            "boundary_version": 1,
            "boundary_path": "governed_voice_identity_explainability_consumption",
            "voice_identity_authority_external": True,
            "consumption_only": True,
            "consume_explainability_outputs_only": True,
            "consume_provenance_references_only": True,
            "explainability_authority_source": "voice_identity",
            "generate_explainability_authority": False,
            "replace_voice_identity_provenance": False,
            "create_explainability_lineage": False,
            "infer_identity_state": False,
            "explainability": {
                "consumed": explainability_consumed,
                "consumed_outcome": (
                    explainability_context.get("consumed_outcome")
                    if explainability_context is not None
                    else None
                ),
                "authority_source": (
                    explainability_context.get("authority_source")
                    if explainability_context is not None
                    else "voice_identity"
                ),
                "provenance_source": (
                    explainability_context.get("provenance_source")
                    if explainability_context is not None
                    else None
                ),
                "source_reference": (
                    explainability_context.get("source_reference")
                    if explainability_context is not None
                    else None
                ),
                "lineage_ref": (
                    explainability_context.get("lineage_ref")
                    if explainability_context is not None
                    else None
                ),
                "attribution_source": (
                    explainability_context.get("attribution_source")
                    if explainability_context is not None
                    else None
                ),
                "confidence_source": (
                    explainability_context.get("confidence_source")
                    if explainability_context is not None
                    else None
                ),
                "enrollment_source": (
                    explainability_context.get("enrollment_source")
                    if explainability_context is not None
                    else None
                ),
                "lifecycle_source": (
                    explainability_context.get("lifecycle_source")
                    if explainability_context is not None
                    else None
                ),
                "permission_source": (
                    explainability_context.get("permission_source")
                    if explainability_context is not None
                    else None
                ),
                "legacy_disposition_source": (
                    explainability_context.get("legacy_disposition_source")
                    if explainability_context is not None
                    else None
                ),
                "unavailable_state": (
                    explainability_context.get("unavailable_state")
                    if explainability_context is not None
                    else "unavailable"
                ) or "unavailable",
                "reason_code": explainability_reason,
                "source": (
                    explainability_context.get("source")
                    if explainability_context is not None
                    else "voice_identity_unavailable"
                ),
            },
        },
    }


def _build_productivity_source_of_record_boundary(
    *,
    state=None,
    hass: HomeAssistant | None = None,
    configured_source_references: dict[str, bool] | None = None,
    active_person_resolution: dict[str, Any] | None = None,
    runtime_person_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return governed Release 6 source-of-record boundary metadata."""
    person_source_bindings = _build_person_productivity_source_bindings(
        state,
        hass=hass,
    ) if state is not None else {
        "required_domains": list(_PRODUCTIVITY_SOURCE_BINDING_FIELDS),
        "person_count": 0,
        "configured_reference_counts": {
            domain: 0 for domain in _PRODUCTIVITY_SOURCE_BINDING_FIELDS
        },
        "configured_reference_present": {
            domain: False for domain in _PRODUCTIVITY_SOURCE_BINDING_FIELDS
        },
        "safe_fallback_person_count": 0,
        "person_bindings": [],
    }

    configured_source_references = configured_source_references or dict(
        person_source_bindings.get("configured_reference_present", {})
    )
    domain_boundaries: dict[str, dict[str, Any]] = {}

    for domain, authority in _PRODUCTIVITY_SOURCE_OF_RECORD_DOMAIN_AUTHORITIES.items():
        configured_reference_present = bool(configured_source_references.get(domain, False))
        domain_boundaries[domain] = {
            "source_of_record": authority["source_of_record"],
            "source_of_record_external": True,
            "configuration_reference_supported": bool(
                authority["configuration_reference_supported"]
            ),
            "configured_reference_present": configured_reference_present,
            "consumed_projection_supported": True,
            "generated_explanation_supported": True,
            "coordination_context_supported": True,
            "derived_context_only": bool(authority["derived_context_only"]),
            "concierge_canonical_state_owned": False,
            "source_lineage_required": True,
            "provenance_reference_required": True,
            "sensitive_content_storage_permitted": False,
        }

    configured_reference_count = sum(
        1 for boundary in domain_boundaries.values() if boundary["configured_reference_present"]
    )
    person_aware_routing = _build_person_aware_productivity_routing(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
    )

    return {
        "productivity_source_of_record_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_productivity_source_of_record_boundary",
        "deterministic_boundary": True,
        "boundary_status": "active",
        "concierge_role": "bounded_consumer_orchestrator",
        "representation_kinds": [
            "configuration_reference",
            "consumed_projection",
            "generated_explanation",
            "coordination_context",
        ],
        "configured_source_reference_count": configured_reference_count,
        "person_productivity_source_bindings": person_source_bindings,
        "person_aware_productivity_routing": person_aware_routing,
        "domain_boundaries": domain_boundaries,
        "provenance_requirements": {
            "provenance_authority_external": True,
            "source_lineage_required": True,
            "provenance_reference_required": True,
            "provenance_duplication_permitted": False,
            "explanation_source_required": True,
        },
        "diagnostics_visibility": {
            "boundary_verification_supported": True,
            "safe_source_metadata_only": True,
            "sensitive_source_content_exposed": False,
        },
        "non_authority_assertions": {
            "creates_source_of_record": False,
            "stores_duplicate_canonical_records": False,
            "claims_calendar_authority": False,
            "claims_email_authority": False,
            "claims_task_authority": False,
            "claims_shopping_authority": False,
            "claims_capture_authority": False,
            "claims_knowledge_authority": False,
            "claims_briefing_authority": False,
            "claims_household_status_authority": False,
            "redefines_provenance_authority": False,
        },
        "deferred_release_6_owners": {
            "person_productivity_source_bindings": "#375",
            "calendar_and_email_consumption": "#363",
            "task_and_shopping_consumption": "#364",
            "capture_and_knowledge_consumption": "#365",
            "briefing_and_household_status_synthesis": "#366",
            "productivity_diagnostics_provenance_explainability": "#367",
            "household_coordination": "#368-#372",
            "release_6_validation": "#373",
        },
    }


def _build_person_productivity_source_bindings(
    state,
    *,
    hass: HomeAssistant | None = None,
) -> dict[str, Any]:
    """Build person-level productivity source reference posture with safe fallback metadata."""
    required_domains = list(_PRODUCTIVITY_SOURCE_BINDING_FIELDS)
    configured_reference_counts = {domain: 0 for domain in required_domains}
    person_bindings: list[dict[str, Any]] = []

    profiles = list(getattr(state, "person_profiles", {}).values())
    for profile in profiles:
        person_id = str(getattr(profile, "person_id", "") or "")
        source_refs = {
            "email": str(getattr(profile, "email_source_ref", "") or "").strip(),
            "calendar": str(getattr(profile, "calendar_source_ref", "") or "").strip(),
            "task": str(getattr(profile, "task_source_ref", "") or "").strip(),
            "shopping": str(getattr(profile, "shopping_source_ref", "") or "").strip(),
        }

        sources: dict[str, dict[str, Any]] = {}
        configured_domains: list[str] = []
        unavailable_or_removed_domains: list[str] = []

        for domain in required_domains:
            source_ref = source_refs[domain]
            if not source_ref:
                binding_status = "missing"
            elif domain in {"email", "calendar"}:
                entity_exists = bool(hass and hass.states.get(source_ref) is not None)
                binding_status = "configured" if entity_exists else "unavailable_or_removed"
            else:
                # Shopping/task references are provider IDs, not HA entity_ids.
                binding_status = "configured"

            if binding_status == "configured":
                configured_domains.append(domain)
                configured_reference_counts[domain] += 1
            elif binding_status == "unavailable_or_removed":
                unavailable_or_removed_domains.append(domain)

            sources[domain] = {
                "source_ref": source_ref,
                "binding_status": binding_status,
            }

        fallback_reasons: list[str] = []
        if len(configured_domains) < len(required_domains):
            fallback_reasons.append("source_missing_or_configuration_incomplete")
        if unavailable_or_removed_domains:
            fallback_reasons.append("source_unavailable_or_removed")

        person_bindings.append(
            {
                "person_id": person_id,
                "configured_domain_count": len(configured_domains),
                "configuration_complete": len(configured_domains) == len(required_domains),
                "safe_fallback_mode_active": bool(fallback_reasons),
                "safe_fallback_reasons": fallback_reasons,
                "sources": sources,
            }
        )

    person_bindings.sort(key=lambda item: str(item.get("person_id", "")))

    return {
        "required_domains": required_domains,
        "person_count": len(person_bindings),
        "configured_reference_counts": configured_reference_counts,
        "configured_reference_present": {
            domain: bool(configured_reference_counts[domain]) for domain in required_domains
        },
        "safe_fallback_person_count": sum(
            1 for binding in person_bindings if binding.get("safe_fallback_mode_active")
        ),
        "person_bindings": person_bindings,
    }


def _resolve_runtime_person_profile(
    state,
    active_person_resolution: dict[str, Any] | None,
) -> dict[str, Any]:
    """Resolve a Concierge person profile from the active-person outcome."""
    default_runtime_person_context = {
        "person_context_state": "person_context_unresolved",
        "reason_code": "person_profile_not_configured",
        "resolved_person_id": None,
        "resolved_voice_profile_id": None,
        "resolved_concierge_person_profile_id": None,
        "match_mode": "unresolved",
        "profile_resolution_state": "unresolved",
        "profile_resolution_reason_code": "person_profile_not_configured",
        "profile_resolution_matches": [],
    }
    if state is None:
        return dict(default_runtime_person_context)

    resolved = dict(active_person_resolution or {})
    active_person_available = bool(resolved.get("active_person_available", False))
    resolved_person_id = str(resolved.get("resolved_person_id", "") or "").strip() or None
    resolved_voice_profile_id = str(resolved.get("resolved_voice_profile_id", "") or "").strip() or None
    if not active_person_available or not resolved_person_id:
        return dict(default_runtime_person_context)

    profiles = list(getattr(state, "person_profiles", {}).values())
    exact_profile = getattr(state, "person_profiles", {}).get(resolved_person_id)
    resolved_matches: list[tuple[str, Any]] = []

    if exact_profile is not None:
        resolved_matches.append(("person_id_exact", exact_profile))
    else:
        for profile in profiles:
            profile_voice_profile_id = str(getattr(profile, "voice_profile_id", "") or "").strip()
            if not profile_voice_profile_id:
                continue
            if profile_voice_profile_id in {resolved_person_id, resolved_voice_profile_id}:
                resolved_matches.append(("voice_profile_reference", profile))

    unique_matches: list[tuple[str, Any]] = []
    seen_person_ids: set[str] = set()
    for match_mode, profile in resolved_matches:
        profile_person_id = str(getattr(profile, "person_id", "") or "").strip()
        if not profile_person_id or profile_person_id in seen_person_ids:
            continue
        seen_person_ids.add(profile_person_id)
        unique_matches.append((match_mode, profile))

    if len(unique_matches) == 0:
        return {
            **default_runtime_person_context,
            "resolved_person_id": resolved_person_id,
            "resolved_voice_profile_id": resolved_voice_profile_id,
            "profile_resolution_reason_code": "person_profile_not_configured",
        }

    if len(unique_matches) > 1:
        return {
            **default_runtime_person_context,
            "resolved_person_id": resolved_person_id,
            "resolved_voice_profile_id": resolved_voice_profile_id,
            "reason_code": "person_profile_ambiguous",
            "profile_resolution_state": "ambiguous",
            "profile_resolution_reason_code": "person_profile_ambiguous",
            "profile_resolution_matches": [
                {
                    "person_profile_ref": str(getattr(profile, "person_id", "") or "").strip(),
                    "match_mode": match_mode,
                }
                for match_mode, profile in unique_matches
            ],
        }

    match_mode, profile = unique_matches[0]
    person_profile_ref = str(getattr(profile, "person_id", "") or "").strip() or None
    voice_profile_ref = str(getattr(profile, "voice_profile_id", "") or "").strip() or None
    home_assistant_person_ref = None
    location_ref = str(getattr(profile, "linked_area_id", "") or "").strip() or None

    email_source_ref = str(getattr(profile, "email_source_ref", "") or "").strip()
    calendar_source_ref = str(getattr(profile, "calendar_source_ref", "") or "").strip()
    shopping_source_ref = str(getattr(profile, "shopping_source_ref", "") or "").strip()
    task_source_ref = str(getattr(profile, "task_source_ref", "") or "").strip()
    email_source_refs = [
        str(binding.get("entity_id", "") or "").strip()
        for binding in getattr(profile, "email_source_bindings", [])
        if str(binding.get("entity_id", "") or "").strip()
    ]
    calendar_source_refs = [
        str(binding.get("entity_id", "") or "").strip()
        for binding in getattr(profile, "calendar_source_bindings", [])
        if str(binding.get("entity_id", "") or "").strip()
    ]
    shopping_source_refs = [
        str(binding.get("entity_id", "") or "").strip()
        for binding in getattr(profile, "shopping_source_bindings", [])
        if str(binding.get("entity_id", "") or "").strip()
    ]
    task_source_refs = [
        str(binding.get("entity_id", "") or "").strip()
        for binding in getattr(profile, "task_source_bindings", [])
        if str(binding.get("entity_id", "") or "").strip()
    ]
    if email_source_ref and email_source_ref not in email_source_refs:
        email_source_refs.insert(0, email_source_ref)
    if calendar_source_ref and calendar_source_ref not in calendar_source_refs:
        calendar_source_refs.insert(0, calendar_source_ref)
    if shopping_source_ref and shopping_source_ref not in shopping_source_refs:
        shopping_source_refs.insert(0, shopping_source_ref)
    if task_source_ref and task_source_ref not in task_source_refs:
        task_source_refs.insert(0, task_source_ref)

    ble_device_refs = [
        str(device_id).strip()
        for device_id in getattr(profile, "ble_device_ids", [])
        if str(device_id).strip()
    ]
    presence_entity_refs = [
        str(entity_id).strip()
        for entity_id in getattr(profile, "aqara_presence_entity_ids", [])
        if str(entity_id).strip()
    ]
    mobile_device_refs = [
        str(target).strip()
        for target in getattr(profile, "mobile_notify_targets", [])
        if str(target).strip()
    ]
    notification_target_refs = list(mobile_device_refs)
    preferred_mobile_target = str(getattr(profile, "preferred_mobile_target", "") or "").strip() or None
    if preferred_mobile_target and preferred_mobile_target not in notification_target_refs:
        notification_target_refs.insert(0, preferred_mobile_target)

    allowed_intent_abilities = [
        str(intent_class).strip()
        for intent_class in getattr(profile, "minor_allowed_intent_classes", [])
        if str(intent_class).strip()
    ]
    consent_state = dict(getattr(profile, "consent", {}) or {})
    policy_context_available = bool(
        consent_state
        or getattr(profile, "is_minor", False)
        or getattr(profile, "guardian_controls_required", False)
        or getattr(profile, "minor_allow_general_qna", False)
        or allowed_intent_abilities
    )
    productivity_bindings_available = bool(
        email_source_refs and calendar_source_refs and shopping_source_refs
    )
    presence_bindings_available = bool(
        ble_device_refs or presence_entity_refs or mobile_device_refs or location_ref
    )

    if not productivity_bindings_available:
        person_context_state = "person_context_partial"
        reason_code = "productivity_bindings_missing"
    elif not presence_bindings_available:
        person_context_state = "person_context_partial"
        reason_code = "presence_bindings_missing"
    elif not policy_context_available:
        person_context_state = "person_context_partial"
        reason_code = "policy_context_missing"
    else:
        person_context_state = "person_context_resolved"
        reason_code = "person_context_resolved"

    return {
        "person_context_state": person_context_state,
        "reason_code": reason_code,
        "resolved_person_id": resolved_person_id,
        "resolved_voice_profile_id": resolved_voice_profile_id,
        "resolved_concierge_person_profile_id": person_profile_ref,
        "match_mode": match_mode,
        "profile_resolution_state": "resolved" if person_context_state == "person_context_resolved" else "partial",
        "profile_resolution_reason_code": reason_code,
        "profile_resolution_matches": [
            {
                "person_profile_ref": person_profile_ref,
                "match_mode": match_mode,
            }
        ],
        "person_profile_ref": person_profile_ref,
        "voice_profile_ref": voice_profile_ref,
        "home_assistant_person_ref": home_assistant_person_ref,
        "identity": {
            "person_profile_ref": person_profile_ref,
            "voice_profile_ref": voice_profile_ref,
            "home_assistant_person_ref": home_assistant_person_ref,
            "resolved_person_id": resolved_person_id,
            "resolved_voice_profile_id": resolved_voice_profile_id,
        },
        "productivity": {
            "available": productivity_bindings_available,
            "email_source_refs": email_source_refs,
            "calendar_source_refs": calendar_source_refs,
            "shopping_source_refs": shopping_source_refs,
            "task_source_refs": task_source_refs,
        },
        "presence": {
            "available": presence_bindings_available,
            "ble_device_refs": ble_device_refs,
            "presence_entity_refs": presence_entity_refs,
            "location_ref": location_ref,
        },
        "mobility": {
            "mobile_device_refs": mobile_device_refs,
            "read_later_target": preferred_mobile_target,
            "notification_target_refs": notification_target_refs,
        },
        "policy": {
            "available": policy_context_available,
            "allowed_intent_abilities": allowed_intent_abilities,
            "content_filter_level": str(getattr(profile, "minor_content_filter_level", "") or "").strip() or "strict",
            "minor_controls": {
                "is_minor": bool(getattr(profile, "is_minor", False)),
                "guardian_controls_required": bool(getattr(profile, "guardian_controls_required", False)),
                "minor_allow_general_qna": bool(getattr(profile, "minor_allow_general_qna", False)),
            },
            "step_up_requirements": {
                "guardian_controls_required": bool(getattr(profile, "guardian_controls_required", False)),
            },
            "consent_state": consent_state,
        },
        "binding_availability": {
            "productivity": productivity_bindings_available,
            "presence": presence_bindings_available,
            "policy": policy_context_available,
        },
        "fail_closed": person_context_state != "person_context_resolved",
    }


def _build_runtime_person_context(
    state,
    *,
    active_person_resolution: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build the bounded runtime person context used by downstream orchestration."""
    return _resolve_runtime_person_profile(state, active_person_resolution)


def _build_calendar_email_consumption_boundary(
    *,
    state=None,
    hass: HomeAssistant | None = None,
    active_person_resolution: dict[str, Any] | None = None,
    runtime_person_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return governed Release 6 calendar/email consumption metadata."""
    required_domains = ["email", "calendar"]
    domain_authorities = {
        "calendar": "configured_calendar_provider",
        "email": "configured_email_provider",
    }

    if state is None:
        return {
            "calendar_email_consumption_boundary_version": 1,
            "applicable": True,
            "boundary_path": "governed_calendar_email_consumption_boundary",
            "deterministic_boundary": True,
            "boundary_status": "active",
            "concierge_role": "bounded_consumer_orchestrator",
            "consumption_only": True,
            "representation_kinds": [
                "configuration_reference",
                "consumed_projection",
                "generated_explanation",
                "coordination_context",
            ],
            "configured_source_reference_count": 0,
            "person_aware_routing": {
                "routing_enabled": False,
                "reason_code": "no_active_person_resolution",
                "active_person_state": "active_person_unavailable",
                "active_person_available": False,
                "resolved_person_id": None,
                "domains": {
                    "email": {
                        "enabled": False,
                        "reason_code": "no_active_person_resolution",
                        "selected_person_id": None,
                        "selection_mode": "disabled",
                    },
                    "calendar": {
                        "enabled": False,
                        "reason_code": "no_active_person_resolution",
                        "selected_person_id": None,
                        "selection_mode": "disabled",
                    },
                },
            },
            "person_calendar_email_bindings": {
                "required_domains": required_domains,
                "person_count": 0,
                "configured_reference_counts": {domain: 0 for domain in required_domains},
                "configured_reference_present": {domain: False for domain in required_domains},
                "safe_fallback_person_count": 0,
                "person_bindings": [],
            },
            "domain_boundaries": {
                domain: {
                    "source_of_record": authority,
                    "source_of_record_external": True,
                    "configuration_reference_supported": True,
                    "configured_reference_present": False,
                    "consumed_projection_supported": True,
                    "generated_explanation_supported": True,
                    "coordination_context_supported": True,
                    "derived_context_only": False,
                    "concierge_canonical_state_owned": False,
                    "source_lineage_required": True,
                    "provenance_reference_required": True,
                    "sensitive_content_storage_permitted": False,
                }
                for domain, authority in domain_authorities.items()
            },
            "provenance_requirements": {
                "provenance_authority_external": True,
                "source_lineage_required": True,
                "provenance_reference_required": True,
                "provenance_duplication_permitted": False,
                "explanation_source_required": True,
            },
            "diagnostics_visibility": {
                "boundary_verification_supported": True,
                "safe_source_metadata_only": True,
                "sensitive_source_content_exposed": False,
            },
            "non_authority_assertions": {
                "creates_source_of_record": False,
                "stores_duplicate_canonical_records": False,
                "claims_calendar_authority": False,
                "claims_email_authority": False,
                "redefines_provenance_authority": False,
            },
            "deferred_release_6_owners": {
                "person_productivity_source_bindings": "#375",
                "calendar_and_email_consumption": "#363",
                "task_and_shopping_consumption": "#364",
                "capture_and_knowledge_consumption": "#365",
                "briefing_and_household_status_synthesis": "#366",
                "productivity_diagnostics_provenance_explainability": "#367",
                "household_coordination": "#368-#372",
                "release_6_validation": "#373",
            },
        }

    person_source_bindings = _build_person_productivity_source_bindings(state, hass=hass)
    person_bindings: list[dict[str, Any]] = []
    configured_reference_counts = {domain: 0 for domain in required_domains}

    for person_binding in person_source_bindings.get("person_bindings", []):
        sources = dict(person_binding.get("sources", {}))
        calendar_email_sources = {
            domain: dict(sources.get(domain, {}))
            for domain in required_domains
        }
        configured_domains = [
            domain
            for domain in required_domains
            if calendar_email_sources[domain].get("binding_status") == "configured"
        ]
        unavailable_or_removed_domains = [
            domain
            for domain in required_domains
            if calendar_email_sources[domain].get("binding_status") == "unavailable_or_removed"
        ]
        for domain in configured_domains:
            configured_reference_counts[domain] += 1

        fallback_reasons: list[str] = []
        if len(configured_domains) < len(required_domains):
            fallback_reasons.append("source_missing_or_configuration_incomplete")
        if unavailable_or_removed_domains:
            fallback_reasons.append("source_unavailable_or_removed")

        person_bindings.append(
            {
                "person_id": person_binding.get("person_id"),
                "configured_domain_count": len(configured_domains),
                "configuration_complete": len(configured_domains) == len(required_domains),
                "safe_fallback_mode_active": bool(fallback_reasons),
                "safe_fallback_reasons": fallback_reasons,
                "sources": calendar_email_sources,
            }
        )

    person_bindings.sort(key=lambda item: str(item.get("person_id", "")))
    person_aware_routing = _build_person_aware_productivity_routing(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
    )
    calendar_email_routing = dict(person_aware_routing.get("domain_routing", {}))

    return {
        "calendar_email_consumption_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_calendar_email_consumption_boundary",
        "deterministic_boundary": True,
        "boundary_status": "active",
        "concierge_role": "bounded_consumer_orchestrator",
        "consumption_only": True,
        "representation_kinds": [
            "configuration_reference",
            "consumed_projection",
            "generated_explanation",
            "coordination_context",
        ],
        "configured_source_reference_count": sum(configured_reference_counts.values()),
        "runtime_person_context": dict(person_aware_routing.get("runtime_person_context", {})),
        "person_aware_routing": {
            "routing_enabled": bool(person_aware_routing.get("routing_enabled", False)),
            "reason_code": person_aware_routing.get("reason_code"),
            "active_person_state": person_aware_routing.get("active_person_state"),
            "active_person_available": bool(person_aware_routing.get("active_person_available", False)),
            "resolved_person_id": person_aware_routing.get("resolved_person_id"),
            "domains": {
                "email": dict(calendar_email_routing.get("email", {})),
                "calendar": dict(calendar_email_routing.get("calendar", {})),
            },
        },
        "person_calendar_email_bindings": {
            "required_domains": required_domains,
            "person_count": len(person_bindings),
            "configured_reference_counts": configured_reference_counts,
            "configured_reference_present": {
                domain: bool(configured_reference_counts[domain])
                for domain in required_domains
            },
            "safe_fallback_person_count": sum(
                1 for item in person_bindings if item.get("safe_fallback_mode_active")
            ),
            "person_bindings": person_bindings,
        },
        "domain_boundaries": {
            domain: {
                "source_of_record": authority,
                "source_of_record_external": True,
                "configuration_reference_supported": True,
                "configured_reference_present": bool(configured_reference_counts[domain]),
                "consumed_projection_supported": True,
                "generated_explanation_supported": True,
                "coordination_context_supported": True,
                "derived_context_only": False,
                "concierge_canonical_state_owned": False,
                "source_lineage_required": True,
                "provenance_reference_required": True,
                "sensitive_content_storage_permitted": False,
            }
            for domain, authority in domain_authorities.items()
        },
        "provenance_requirements": {
            "provenance_authority_external": True,
            "source_lineage_required": True,
            "provenance_reference_required": True,
            "provenance_duplication_permitted": False,
            "explanation_source_required": True,
        },
        "diagnostics_visibility": {
            "boundary_verification_supported": True,
            "safe_source_metadata_only": True,
            "sensitive_source_content_exposed": False,
        },
        "non_authority_assertions": {
            "creates_source_of_record": False,
            "stores_duplicate_canonical_records": False,
            "claims_calendar_authority": False,
            "claims_email_authority": False,
            "redefines_provenance_authority": False,
        },
        "deferred_release_6_owners": {
            "person_productivity_source_bindings": "#375",
            "calendar_and_email_consumption": "#363",
            "task_and_shopping_consumption": "#364",
            "capture_and_knowledge_consumption": "#365",
            "briefing_and_household_status_synthesis": "#366",
            "productivity_diagnostics_provenance_explainability": "#367",
            "household_coordination": "#368-#372",
            "release_6_validation": "#373",
        },
    }


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


def _build_room_authority_traceability(
    state,
    *,
    requested_area_id: str | None,
    assembled_context: dict[str, Any],
    room_vocabulary_resolution: dict[str, Any] | None = None,
    device_entity_vocabulary_resolution: dict[str, Any] | None = None,
    asset_vocabulary_resolution: dict[str, Any] | None = None,
    runtime_person_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return room configuration authority traceability for bounded runtime answers."""
    context_area_id = assembled_context.get("context_area_id") or requested_area_id
    room = state.rooms.get(context_area_id) if context_area_id else None
    composite_id = assembled_context.get("resolved_composite_id")
    composite = state.composites.get(composite_id) if composite_id else None

    room_configuration_loaded = room is not None
    merged_room_configuration_loaded = composite is not None

    room_configuration_source = "room_configuration" if room_configuration_loaded else "room_configuration_unavailable"
    room_vocabulary_source = "room_configuration" if room_configuration_loaded or room_vocabulary_resolution is not None else "room_configuration_unavailable"
    information_source_origin = "room_configuration" if room_configuration_loaded else "room_configuration_unavailable"
    environment_source_origin = "room_configuration" if room_configuration_loaded else "room_configuration_unavailable"
    asset_authority_source = "room_configuration" if room_configuration_loaded and bool(getattr(room, "asset_groups", [])) else "room_configuration_unavailable"
    merged_room_authority_source = "room_configuration" if merged_room_configuration_loaded else None
    person_authority_source = "person_configuration"

    return {
        "room_configuration_loaded": room_configuration_loaded,
        "room_authority_source": room_configuration_source,
        "room_vocabulary_source": room_vocabulary_source,
        "vocabulary_source": room_vocabulary_source,
        "information_source_origin": information_source_origin,
        "environment_source_origin": environment_source_origin,
        "asset_authority_source": asset_authority_source,
        "merged_room_authority_source": merged_room_authority_source,
        "person_authority_source": person_authority_source,
        "room_configuration_area_id": room.area_id if room is not None else context_area_id,
        "room_configuration_name": room.area_id if room is not None else context_area_id,
        "room_configuration_primary_area": composite.primary_area if composite is not None else None,
        "room_configuration_composite_id": composite.composite_id if composite is not None else None,
        "room_configuration_media_player_entity_ids": list(room.media_player_entity_ids) if room is not None else [],
        "room_configuration_voice_device_entity_ids": list(room.voice_device_entity_ids) if room is not None else [],
        "room_configuration_speaker_entity_ids": list(room.speaker_entity_ids) if room is not None else [],
        "room_configuration_environment_information_outputs": list(room.environment_information_outputs) if room is not None else [],
        "room_configuration_weather_source_entity_ids": list(room.weather_source_entity_ids) if room is not None else [],
        "room_configuration_news_source_entity_ids": list(room.news_source_entity_ids) if room is not None else [],
        "room_configuration_device_group_count": len(room.device_groups) if room is not None else 0,
        "room_configuration_asset_group_count": len(room.asset_groups) if room is not None else 0,
        "room_configuration_capability_source": "room_configuration",
        "room_runtime_context_source": "room_configuration",
        "runtime_person_context_source": (
            str(runtime_person_context.get("person_context_state", "person_configuration_unavailable"))
            if runtime_person_context is not None
            else "person_configuration_unavailable"
        ),
        "room_discovery_reliance": "configuration_authored",
        "runtime_discovery_reliance": "validation_only",
        "device_entity_vocabulary_source": (
            "room_configuration" if device_entity_vocabulary_resolution is not None else "device_vocabulary_unavailable"
        ),
        "asset_vocabulary_source": (
            "asset_intelligence" if asset_vocabulary_resolution is not None else "asset_vocabulary_unavailable"
        ),
        "merged_room_authority_loaded": merged_room_configuration_loaded,
    }

    
def _build_task_shopping_consumption_boundary(
    *,
    state=None,
    hass: HomeAssistant | None = None,
    active_person_resolution: dict[str, Any] | None = None,
    runtime_person_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return governed Release 6 task/shopping consumption metadata."""
    task_reference_kinds = [
        "ownership_references",
        "assignment_references",
        "completion_references",
        "due_awareness_references",
        "provenance_references",
    ]
    shopping_reference_kinds = [
        "shopping_item_references",
        "ownership_references",
        "duplicate_indicators",
        "completion_references",
        "provenance_references",
        "shopping_explainability_references",
    ]

    if state is None:
        return {
            "task_shopping_consumption_boundary_version": 1,
            "applicable": True,
            "boundary_path": "governed_task_shopping_consumption_boundary",
            "deterministic_boundary": True,
            "boundary_status": "active",
            "concierge_role": "bounded_consumer_orchestrator",
            "consumption_only": True,
            "representation_kinds": [
                "configuration_reference",
                "consumed_projection",
                "generated_explanation",
                "coordination_context",
                "clarification_response",
            ],
            "task_reference_kinds": task_reference_kinds,
            "shopping_reference_kinds": shopping_reference_kinds,
            "configured_source_reference_count": 0,
            "person_aware_routing": {
                "routing_enabled": False,
                "reason_code": "no_active_person_resolution",
                "active_person_state": "active_person_unavailable",
                "active_person_available": False,
                "resolved_person_id": None,
                "domains": {
                    "task": {
                        "enabled": False,
                        "reason_code": "no_active_person_resolution",
                        "selected_person_id": None,
                        "selection_mode": "disabled",
                    },
                    "shopping": {
                        "enabled": False,
                        "reason_code": "no_active_person_resolution",
                        "selected_person_id": None,
                        "selection_mode": "disabled",
                    },
                },
            },
            "person_shopping_bindings": {
                "required_domains": ["shopping"],
                "person_count": 0,
                "configured_reference_counts": {"shopping": 0},
                "configured_reference_present": {"shopping": False},
                "safe_fallback_person_count": 0,
                "person_bindings": [],
            },
            "task_reference_boundaries": {
                "task": {
                    "source_of_record": "configured_task_provider",
                    "source_of_record_external": True,
                    "reference_only_model": True,
                    "ownership_references_supported": True,
                    "assignment_references_supported": True,
                    "completion_references_supported": True,
                    "due_awareness_references_supported": True,
                    "provenance_references_supported": True,
                    "consumed_projection_supported": True,
                    "generated_explanation_supported": True,
                    "coordination_context_supported": True,
                    "derived_context_only": True,
                    "clarification_supported": True,
                    "ambiguity_visible": True,
                    "hidden_intent_inference": False,
                    "concierge_canonical_state_owned": False,
                    "source_lineage_required": True,
                    "provenance_reference_required": True,
                    "sensitive_content_storage_permitted": False,
                },
                "shopping": {
                    "source_of_record": "configured_shopping_provider",
                    "source_of_record_external": True,
                    "reference_only_model": True,
                    "shopping_reference_kinds": shopping_reference_kinds,
                    "shopping_binding_supported": True,
                    "consumed_projection_supported": True,
                    "generated_explanation_supported": True,
                    "coordination_context_supported": True,
                    "derived_context_only": False,
                    "clarification_supported": True,
                    "ambiguity_visible": True,
                    "hidden_intent_inference": False,
                    "concierge_canonical_state_owned": False,
                    "source_lineage_required": True,
                    "provenance_reference_required": True,
                    "sensitive_content_storage_permitted": False,
                },
            },
            "clarification_behavior": {
                "supported": True,
                "ambiguity_visible": True,
                "confirmation_required_when_ambiguous": True,
                "hidden_intent_inference": False,
                "explainable_prompt_required": True,
                "multi_item_capture_aligned": True,
            },
            "provenance_requirements": {
                "provenance_authority_external": True,
                "source_lineage_required": True,
                "provenance_reference_required": True,
                "provenance_duplication_permitted": False,
                "explanation_source_required": True,
            },
            "diagnostics_visibility": {
                "boundary_verification_supported": True,
                "safe_source_metadata_only": True,
                "sensitive_source_content_exposed": False,
            },
            "non_authority_assertions": {
                "creates_source_of_record": False,
                "stores_duplicate_canonical_records": False,
                "claims_task_authority": False,
                "claims_shopping_authority": False,
                "redefines_provenance_authority": False,
                "infers_hidden_intent": False,
            },
            "deferred_release_6_owners": {
                "person_productivity_source_bindings": "#375",
                "calendar_and_email_consumption": "#363",
                "task_and_shopping_consumption": "#364",
                "capture_and_knowledge_consumption": "#365",
                "briefing_and_household_status_synthesis": "#366",
                "productivity_diagnostics_provenance_explainability": "#367",
                "household_coordination": "#368-#372",
                "release_6_validation": "#373",
            },
        }

    person_source_bindings = _build_person_productivity_source_bindings(state, hass=hass)
    person_bindings: list[dict[str, Any]] = []
    configured_reference_counts = {"shopping": 0}

    for person_binding in person_source_bindings.get("person_bindings", []):
        sources = dict(person_binding.get("sources", {}))
        shopping_source = dict(sources.get("shopping", {}))
        shopping_binding_status = str(shopping_source.get("binding_status", "missing") or "missing")
        configured = shopping_binding_status == "configured"

        if configured:
            configured_reference_counts["shopping"] += 1

        fallback_reasons: list[str] = []
        if shopping_binding_status == "missing":
            fallback_reasons.append("source_missing_or_configuration_incomplete")
        if shopping_binding_status == "unavailable_or_removed":
            fallback_reasons.append("source_unavailable_or_removed")

        person_bindings.append(
            {
                "person_id": person_binding.get("person_id"),
                "configured_domain_count": 1 if configured else 0,
                "configuration_complete": configured,
                "safe_fallback_mode_active": bool(fallback_reasons),
                "safe_fallback_reasons": fallback_reasons,
                "sources": {"shopping": shopping_source},
            }
        )

    person_bindings.sort(key=lambda item: str(item.get("person_id", "")))
    person_aware_routing = _build_person_aware_productivity_routing(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
    )
    task_shopping_routing = dict(person_aware_routing.get("domain_routing", {}))

    return {
        "task_shopping_consumption_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_task_shopping_consumption_boundary",
        "deterministic_boundary": True,
        "boundary_status": "active",
        "concierge_role": "bounded_consumer_orchestrator",
        "consumption_only": True,
        "representation_kinds": [
            "configuration_reference",
            "consumed_projection",
            "generated_explanation",
            "coordination_context",
            "clarification_response",
        ],
        "task_reference_kinds": task_reference_kinds,
        "shopping_reference_kinds": shopping_reference_kinds,
        "configured_source_reference_count": configured_reference_counts["shopping"],
        "runtime_person_context": dict(person_aware_routing.get("runtime_person_context", {})),
        "person_aware_routing": {
            "routing_enabled": bool(person_aware_routing.get("routing_enabled", False)),
            "reason_code": person_aware_routing.get("reason_code"),
            "active_person_state": person_aware_routing.get("active_person_state"),
            "active_person_available": bool(person_aware_routing.get("active_person_available", False)),
            "resolved_person_id": person_aware_routing.get("resolved_person_id"),
            "domains": {
                "task": dict(task_shopping_routing.get("task", {})),
                "shopping": dict(task_shopping_routing.get("shopping", {})),
            },
        },
        "person_shopping_bindings": {
            "required_domains": ["shopping"],
            "person_count": len(person_bindings),
            "configured_reference_counts": configured_reference_counts,
            "configured_reference_present": {"shopping": bool(configured_reference_counts["shopping"])},
            "safe_fallback_person_count": sum(
                1 for item in person_bindings if item.get("safe_fallback_mode_active")
            ),
            "person_bindings": person_bindings,
        },
        "task_reference_boundaries": {
            "task": {
                "source_of_record": "configured_task_provider",
                "source_of_record_external": True,
                "reference_only_model": True,
                "ownership_references_supported": True,
                "assignment_references_supported": True,
                "completion_references_supported": True,
                "due_awareness_references_supported": True,
                "provenance_references_supported": True,
                "consumed_projection_supported": True,
                "generated_explanation_supported": True,
                "coordination_context_supported": True,
                "derived_context_only": True,
                "clarification_supported": True,
                "ambiguity_visible": True,
                "hidden_intent_inference": False,
                "concierge_canonical_state_owned": False,
                "source_lineage_required": True,
                "provenance_reference_required": True,
                "sensitive_content_storage_permitted": False,
            },
            "shopping": {
                "source_of_record": "configured_shopping_provider",
                "source_of_record_external": True,
                "reference_only_model": True,
                "shopping_reference_kinds": shopping_reference_kinds,
                "shopping_binding_supported": True,
                "consumed_projection_supported": True,
                "generated_explanation_supported": True,
                "coordination_context_supported": True,
                "derived_context_only": False,
                "clarification_supported": True,
                "ambiguity_visible": True,
                "hidden_intent_inference": False,
                "concierge_canonical_state_owned": False,
                "source_lineage_required": True,
                "provenance_reference_required": True,
                "sensitive_content_storage_permitted": False,
            },
        },
        "clarification_behavior": {
            "supported": True,
            "ambiguity_visible": True,
            "confirmation_required_when_ambiguous": True,
            "hidden_intent_inference": False,
            "explainable_prompt_required": True,
            "multi_item_capture_aligned": True,
        },
        "provenance_requirements": {
            "provenance_authority_external": True,
            "source_lineage_required": True,
            "provenance_reference_required": True,
            "provenance_duplication_permitted": False,
            "explanation_source_required": True,
        },
        "diagnostics_visibility": {
            "boundary_verification_supported": True,
            "safe_source_metadata_only": True,
            "sensitive_source_content_exposed": False,
        },
        "non_authority_assertions": {
            "creates_source_of_record": False,
            "stores_duplicate_canonical_records": False,
            "claims_task_authority": False,
            "claims_shopping_authority": False,
            "redefines_provenance_authority": False,
            "infers_hidden_intent": False,
        },
        "deferred_release_6_owners": {
            "person_productivity_source_bindings": "#375",
            "calendar_and_email_consumption": "#363",
            "task_and_shopping_consumption": "#364",
            "capture_and_knowledge_consumption": "#365",
            "briefing_and_household_status_synthesis": "#366",
            "productivity_diagnostics_provenance_explainability": "#367",
            "household_coordination": "#368-#372",
            "release_6_validation": "#373",
        },
    }


def _build_capture_knowledge_consumption_boundary(
    *,
    state=None,
    hass: HomeAssistant | None = None,
) -> dict[str, Any]:
    """Return governed Release 6 capture/knowledge consumption metadata."""
    knowledge_reference_kinds = [
        "knowledge_request_references",
        "knowledge_response_references",
        "source_references",
        "uncertainty_references",
        "knowledge_explainability_references",
    ]
    capture_reference_kinds = [
        "utterance_reference",
        "decomposition_references",
        "item_lineage_references",
        "decomposition_explainability_references",
        "ambiguity_reference",
        "confirmation_reference",
    ]

    if state is None:
        return {
            "capture_knowledge_consumption_boundary_version": 1,
            "applicable": True,
            "boundary_path": "governed_capture_knowledge_consumption_boundary",
            "deterministic_boundary": True,
            "boundary_status": "active",
            "concierge_role": "bounded_consumer_orchestrator",
            "consumption_only": True,
            "representation_kinds": [
                "configuration_reference",
                "consumed_projection",
                "generated_explanation",
                "coordination_context",
                "clarification_response",
            ],
            "knowledge_reference_kinds": knowledge_reference_kinds,
            "capture_reference_kinds": capture_reference_kinds,
            "configured_source_reference_count": 0,
            "knowledge_consumption": {
                "reference_count": 0,
                "knowledge_enabled_room_count": 0,
                "knowledge_enabled_composite_count": 0,
                "knowledge_available": False,
                "safe_fallback_mode_active": True,
                "safe_fallback_reasons": ["knowledge_references_missing_or_unavailable"],
            },
            "capture_consumption": {
                "reference_count": 0,
                "capture_available": False,
                "safe_fallback_mode_active": True,
                "safe_fallback_reasons": ["capture_references_missing_or_unavailable"],
            },
            "provenance_visibility": {
                "provenance_reference_count": 0,
                "provenance_reference_present": False,
                "provenance_visible": False,
            },
            "clarification_behavior": {
                "supported": True,
                "ambiguity_visible": True,
                "confirmation_required_when_ambiguous": True,
                "hidden_intent_inference": False,
                "explainable_prompt_required": True,
                "multi_item_capture_aligned": True,
            },
            "domain_boundaries": {
                "knowledge": {
                    "source_of_record": "configured_knowledge_provider",
                    "source_of_record_external": True,
                    "reference_only_model": True,
                    "knowledge_reference_kinds": knowledge_reference_kinds,
                    "query_context_supported": True,
                    "consumed_projection_supported": True,
                    "generated_explanation_supported": True,
                    "availability_visibility_supported": True,
                    "derived_context_only": True,
                    "concierge_canonical_state_owned": False,
                    "source_lineage_required": True,
                    "provenance_reference_required": True,
                    "sensitive_content_storage_permitted": False,
                },
                "capture": {
                    "source_of_record": "configured_capture_provider",
                    "source_of_record_external": True,
                    "reference_only_model": True,
                    "capture_reference_kinds": capture_reference_kinds,
                    "interpretation_context_supported": True,
                    "consumed_projection_supported": True,
                    "generated_explanation_supported": True,
                    "availability_visibility_supported": True,
                    "derived_context_only": True,
                    "concierge_canonical_state_owned": False,
                    "source_lineage_required": True,
                    "provenance_reference_required": True,
                    "sensitive_content_storage_permitted": False,
                },
            },
            "provenance_requirements": {
                "provenance_authority_external": True,
                "source_lineage_required": True,
                "provenance_reference_required": True,
                "provenance_duplication_permitted": False,
                "explanation_source_required": True,
            },
            "diagnostics_visibility": {
                "boundary_verification_supported": True,
                "safe_source_metadata_only": True,
                "sensitive_source_content_exposed": False,
            },
            "non_authority_assertions": {
                "creates_source_of_record": False,
                "stores_duplicate_canonical_records": False,
                "claims_capture_authority": False,
                "claims_knowledge_authority": False,
                "redefines_provenance_authority": False,
                "replaces_capture_system": False,
                "replaces_knowledge_system": False,
                "infers_hidden_intent": False,
            },
            "deferred_release_6_owners": {
                "person_productivity_source_bindings": "#375",
                "calendar_and_email_consumption": "#363",
                "task_and_shopping_consumption": "#364",
                "capture_and_knowledge_consumption": "#365",
                "briefing_and_household_status_synthesis": "#366",
                "productivity_diagnostics_provenance_explainability": "#367",
                "household_coordination": "#368-#372",
                "release_6_validation": "#373",
            },
        }

    knowledge_enabled_room_count = sum(
        1 for room in state.rooms.values() if bool(getattr(room, "ai_knowledge_enabled", False))
    )
    knowledge_enabled_composite_count = sum(
        1 for composite in state.composites.values() if bool(getattr(composite, "ai_knowledge_enabled", False))
    )

    knowledge_reference_items: list[dict[str, Any]] = []
    capture_reference_items: list[dict[str, Any]] = []
    provenance_reference_items: list[dict[str, Any]] = []

    for activity in sorted(
        state.activities.values(),
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        for ref in list(getattr(activity, "external_refs", [])):
            ref_type = str(ref.get("ref_type", "") or "")
            if ref_type in knowledge_reference_kinds:
                knowledge_reference_items.append(dict(ref))
            if ref_type in capture_reference_kinds:
                capture_reference_items.append(dict(ref))
            if ref_type == "provenance_references":
                provenance_reference_items.append(dict(ref))

    knowledge_available = bool(
        knowledge_reference_items or knowledge_enabled_room_count or knowledge_enabled_composite_count
    )
    capture_available = bool(capture_reference_items)
    provenance_visible = bool(provenance_reference_items)

    knowledge_fallback_reasons: list[str] = []
    if not knowledge_available:
        knowledge_fallback_reasons.append("knowledge_references_missing_or_unavailable")

    capture_fallback_reasons: list[str] = []
    if not capture_available:
        capture_fallback_reasons.append("capture_references_missing_or_unavailable")

    return {
        "capture_knowledge_consumption_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_capture_knowledge_consumption_boundary",
        "deterministic_boundary": True,
        "boundary_status": "active",
        "concierge_role": "bounded_consumer_orchestrator",
        "consumption_only": True,
        "representation_kinds": [
            "configuration_reference",
            "consumed_projection",
            "generated_explanation",
            "coordination_context",
            "clarification_response",
        ],
        "knowledge_reference_kinds": knowledge_reference_kinds,
        "capture_reference_kinds": capture_reference_kinds,
        "configured_source_reference_count": len(knowledge_reference_items) + len(capture_reference_items),
        "knowledge_consumption": {
            "reference_count": len(knowledge_reference_items),
            "knowledge_enabled_room_count": knowledge_enabled_room_count,
            "knowledge_enabled_composite_count": knowledge_enabled_composite_count,
            "knowledge_available": knowledge_available,
            "safe_fallback_mode_active": not knowledge_available,
            "safe_fallback_reasons": knowledge_fallback_reasons,
        },
        "capture_consumption": {
            "reference_count": len(capture_reference_items),
            "capture_available": capture_available,
            "safe_fallback_mode_active": not capture_available,
            "safe_fallback_reasons": capture_fallback_reasons,
        },
        "provenance_visibility": {
            "provenance_reference_count": len(provenance_reference_items),
            "provenance_reference_present": provenance_visible,
            "provenance_visible": provenance_visible,
        },
        "clarification_behavior": {
            "supported": True,
            "ambiguity_visible": True,
            "confirmation_required_when_ambiguous": True,
            "hidden_intent_inference": False,
            "explainable_prompt_required": True,
            "multi_item_capture_aligned": True,
        },
        "domain_boundaries": {
            "knowledge": {
                "source_of_record": "configured_knowledge_provider",
                "source_of_record_external": True,
                "reference_only_model": True,
                "knowledge_reference_kinds": knowledge_reference_kinds,
                "query_context_supported": True,
                "consumed_projection_supported": True,
                "generated_explanation_supported": True,
                "availability_visibility_supported": True,
                "derived_context_only": True,
                "concierge_canonical_state_owned": False,
                "source_lineage_required": True,
                "provenance_reference_required": True,
                "sensitive_content_storage_permitted": False,
            },
            "capture": {
                "source_of_record": "configured_capture_provider",
                "source_of_record_external": True,
                "reference_only_model": True,
                "capture_reference_kinds": capture_reference_kinds,
                "interpretation_context_supported": True,
                "consumed_projection_supported": True,
                "generated_explanation_supported": True,
                "availability_visibility_supported": True,
                "derived_context_only": True,
                "concierge_canonical_state_owned": False,
                "source_lineage_required": True,
                "provenance_reference_required": True,
                "sensitive_content_storage_permitted": False,
            },
        },
        "provenance_requirements": {
            "provenance_authority_external": True,
            "source_lineage_required": True,
            "provenance_reference_required": True,
            "provenance_duplication_permitted": False,
            "explanation_source_required": True,
        },
        "diagnostics_visibility": {
            "boundary_verification_supported": True,
            "safe_source_metadata_only": True,
            "sensitive_source_content_exposed": False,
        },
        "non_authority_assertions": {
            "creates_source_of_record": False,
            "stores_duplicate_canonical_records": False,
            "claims_capture_authority": False,
            "claims_knowledge_authority": False,
            "redefines_provenance_authority": False,
            "replaces_capture_system": False,
            "replaces_knowledge_system": False,
            "infers_hidden_intent": False,
        },
        "deferred_release_6_owners": {
            "person_productivity_source_bindings": "#375",
            "calendar_and_email_consumption": "#363",
            "task_and_shopping_consumption": "#364",
            "capture_and_knowledge_consumption": "#365",
            "briefing_and_household_status_synthesis": "#366",
            "productivity_diagnostics_provenance_explainability": "#367",
            "household_coordination": "#368-#372",
            "release_6_validation": "#373",
        },
    }


def _build_briefing_composition_boundary(
    *,
    state=None,
    hass: HomeAssistant | None = None,
) -> dict[str, Any]:
    """Return governed Release 6 briefing composition metadata."""
    calendar_email_boundary = _build_calendar_email_consumption_boundary(state=state, hass=hass)
    task_shopping_boundary = _build_task_shopping_consumption_boundary(state=state, hass=hass)
    capture_knowledge_boundary = _build_capture_knowledge_consumption_boundary(state=state, hass=hass)

    source_boundary_items = [
        {
            "source_domain": "calendar_email",
            "source_boundary": "calendar_email_consumption_boundary",
            "boundary_path": calendar_email_boundary.get("boundary_path"),
            "source_reference_count": calendar_email_boundary.get("configured_source_reference_count", 0),
            "availability": bool(
                calendar_email_boundary.get("configured_source_reference_count", 0)
                or calendar_email_boundary.get("person_calendar_email_bindings", {}).get("person_count", 0)
            ),
            "safe_fallback_mode_active": bool(
                calendar_email_boundary.get("person_calendar_email_bindings", {})
                .get("safe_fallback_person_count", 0)
            ),
            "provenance_visible": bool(calendar_email_boundary.get("configured_source_reference_count", 0)),
        },
        {
            "source_domain": "task_shopping",
            "source_boundary": "task_shopping_consumption_boundary",
            "boundary_path": task_shopping_boundary.get("boundary_path"),
            "source_reference_count": task_shopping_boundary.get("configured_source_reference_count", 0),
            "availability": bool(
                task_shopping_boundary.get("configured_source_reference_count", 0)
                or task_shopping_boundary.get("person_shopping_bindings", {}).get("person_count", 0)
            ),
            "safe_fallback_mode_active": bool(
                task_shopping_boundary.get("person_shopping_bindings", {}).get("safe_fallback_person_count", 0)
            ),
            "provenance_visible": bool(task_shopping_boundary.get("configured_source_reference_count", 0)),
        },
        {
            "source_domain": "capture_knowledge",
            "source_boundary": "capture_knowledge_consumption_boundary",
            "boundary_path": capture_knowledge_boundary.get("boundary_path"),
            "source_reference_count": capture_knowledge_boundary.get("configured_source_reference_count", 0),
            "availability": bool(
                capture_knowledge_boundary.get("knowledge_consumption", {}).get("knowledge_available", False)
                or capture_knowledge_boundary.get("capture_consumption", {}).get("capture_available", False)
            ),
            "safe_fallback_mode_active": bool(capture_knowledge_boundary.get("capture_consumption", {}).get("safe_fallback_mode_active", False))
            or bool(capture_knowledge_boundary.get("knowledge_consumption", {}).get("safe_fallback_mode_active", False)),
            "provenance_visible": bool(capture_knowledge_boundary.get("provenance_visibility", {}).get("provenance_reference_present", False)),
        },
    ]

    total_source_reference_count = sum(item["source_reference_count"] for item in source_boundary_items)
    available_source_count = sum(1 for item in source_boundary_items if item["availability"])
    safe_fallback_mode_active = any(item["safe_fallback_mode_active"] for item in source_boundary_items)
    provenance_references = [
        {
            "source_boundary": item["source_boundary"],
            "boundary_path": item["boundary_path"],
            "source_reference_count": item["source_reference_count"],
            "provenance_visible": item["provenance_visible"],
        }
        for item in source_boundary_items
        if item["provenance_visible"] or item["source_reference_count"] > 0
    ]

    section_order = ["calendar_email", "task_shopping", "capture_knowledge"]
    briefing_sections = [
        {
            "section_id": section_name,
            "section_type": section_name,
            "source_boundaries": [item["source_boundary"] for item in source_boundary_items if item["source_domain"] == section_name],
            "source_reference_count": next(item["source_reference_count"] for item in source_boundary_items if item["source_domain"] == section_name),
            "safe_fallback_mode_active": next(item["safe_fallback_mode_active"] for item in source_boundary_items if item["source_domain"] == section_name),
        }
        for section_name in section_order
    ]

    briefing_composition_state = "active" if available_source_count else "restricted"
    return {
        "briefing_composition_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_briefing_composition_boundary",
        "deterministic_boundary": True,
        "boundary_status": "active",
        "concierge_role": "bounded_consumer_orchestrator",
        "consumption_only": True,
        "representation_kinds": [
            "configuration_reference",
            "consumed_projection",
            "generated_explanation",
            "coordination_context",
            "clarification_response",
        ],
        "briefing_composition": {
            "briefing_composition_id": "briefcomp_release_6",
            "briefing_sections": briefing_sections,
            "source_references": source_boundary_items,
            "priority_ordering": section_order,
            "calm_by_default_ordering": section_order,
            "briefing_explainability_references": [
                {
                    "section_id": item["section_id"],
                    "source_boundaries": item["source_boundaries"],
                    "source_reference_count": item["source_reference_count"],
                    "safe_fallback_mode_active": item["safe_fallback_mode_active"],
                }
                for item in briefing_sections
            ],
            "provenance_references": provenance_references,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "briefing_composition_state": briefing_composition_state,
        },
        "briefing_available": bool(available_source_count),
        "source_boundary_count": len(source_boundary_items),
        "configured_source_reference_count": total_source_reference_count,
        "safe_fallback_mode_active": safe_fallback_mode_active,
        "safe_fallback_reasons": [
            "source_boundary_unavailable",
        ] if not available_source_count else [],
        "source_boundaries": source_boundary_items,
        "provenance_visibility": {
            "provenance_reference_count": len(provenance_references),
            "provenance_reference_present": bool(provenance_references),
            "provenance_visible": bool(provenance_references),
        },
        "explainability_visibility": {
            "briefing_explainability_supported": True,
            "source_domain_visible": True,
            "source_type_visible": True,
            "safe_fallback_visible": True,
        },
        "non_authority_assertions": {
            "creates_source_of_record": False,
            "stores_duplicate_canonical_records": False,
            "claims_briefing_authority": False,
            "claims_household_status_authority": False,
            "creates_planning_engine": False,
            "creates_recommendation_engine": False,
            "redefines_provenance_authority": False,
        },
        "deferred_release_6_owners": {
            "person_productivity_source_bindings": "#375",
            "calendar_and_email_consumption": "#363",
            "task_and_shopping_consumption": "#364",
            "capture_and_knowledge_consumption": "#365",
            "briefing_and_household_status_synthesis": "#366",
            "productivity_diagnostics_provenance_explainability": "#367",
            "household_coordination": "#368-#372",
            "release_6_validation": "#373",
        },
    }


def _build_household_status_synthesis_boundary(
    *,
    state=None,
    hass: HomeAssistant | None = None,
) -> dict[str, Any]:
    """Return governed Release 6 household status synthesis metadata."""
    calendar_email_boundary = _build_calendar_email_consumption_boundary(state=state, hass=hass)
    task_shopping_boundary = _build_task_shopping_consumption_boundary(state=state, hass=hass)
    capture_knowledge_boundary = _build_capture_knowledge_consumption_boundary(state=state, hass=hass)
    briefing_composition_boundary = _build_briefing_composition_boundary(state=state, hass=hass)

    source_items = [
        {
            "source_domain": "calendar",
            "source_type": "calendar_email_consumption_boundary",
            "boundary_path": calendar_email_boundary.get("boundary_path"),
            "source_reference_count": calendar_email_boundary.get("configured_source_reference_count", 0),
            "availability": bool(
                calendar_email_boundary.get("configured_source_reference_count", 0)
                or calendar_email_boundary.get("person_calendar_email_bindings", {}).get("person_count", 0)
            ),
            "safe_fallback_mode_active": bool(
                calendar_email_boundary.get("person_calendar_email_bindings", {}).get("person_count", 0)
            ),
            "provenance_visible": bool(calendar_email_boundary.get("configured_source_reference_count", 0)),
        },
        {
            "source_domain": "task",
            "source_type": "task_shopping_consumption_boundary",
            "boundary_path": task_shopping_boundary.get("boundary_path"),
            "source_reference_count": task_shopping_boundary.get("configured_source_reference_count", 0),
            "availability": bool(
                task_shopping_boundary.get("configured_source_reference_count", 0)
                or task_shopping_boundary.get("person_shopping_bindings", {}).get("person_count", 0)
            ),
            "safe_fallback_mode_active": bool(
                task_shopping_boundary.get("person_shopping_bindings", {}).get("safe_fallback_person_count", 0)
            ),
            "provenance_visible": bool(task_shopping_boundary.get("configured_source_reference_count", 0)),
        },
        {
            "source_domain": "shopping",
            "source_type": "task_shopping_consumption_boundary",
            "boundary_path": task_shopping_boundary.get("boundary_path"),
            "source_reference_count": task_shopping_boundary.get("configured_source_reference_count", 0),
            "availability": bool(
                task_shopping_boundary.get("configured_source_reference_count", 0)
                or task_shopping_boundary.get("person_shopping_bindings", {}).get("person_count", 0)
            ),
            "safe_fallback_mode_active": bool(
                task_shopping_boundary.get("person_shopping_bindings", {}).get("safe_fallback_person_count", 0)
            ),
            "provenance_visible": bool(task_shopping_boundary.get("configured_source_reference_count", 0)),
        },
        {
            "source_domain": "capture",
            "source_type": "capture_knowledge_consumption_boundary",
            "boundary_path": capture_knowledge_boundary.get("boundary_path"),
            "source_reference_count": capture_knowledge_boundary.get("configured_source_reference_count", 0),
            "availability": bool(
                capture_knowledge_boundary.get("knowledge_consumption", {}).get("knowledge_available", False)
                or capture_knowledge_boundary.get("capture_consumption", {}).get("capture_available", False)
            ),
            "safe_fallback_mode_active": bool(capture_knowledge_boundary.get("capture_consumption", {}).get("safe_fallback_mode_active", False))
            or bool(capture_knowledge_boundary.get("knowledge_consumption", {}).get("safe_fallback_mode_active", False)),
            "provenance_visible": bool(capture_knowledge_boundary.get("provenance_visibility", {}).get("provenance_reference_present", False)),
        },
        {
            "source_domain": "knowledge",
            "source_type": "capture_knowledge_consumption_boundary",
            "boundary_path": capture_knowledge_boundary.get("boundary_path"),
            "source_reference_count": capture_knowledge_boundary.get("configured_source_reference_count", 0),
            "availability": bool(capture_knowledge_boundary.get("knowledge_consumption", {}).get("knowledge_available", False)),
            "safe_fallback_mode_active": bool(capture_knowledge_boundary.get("knowledge_consumption", {}).get("safe_fallback_mode_active", False)),
            "provenance_visible": bool(capture_knowledge_boundary.get("provenance_visibility", {}).get("provenance_reference_present", False)),
        },
    ]

    available_source_count = sum(1 for item in source_items if item["availability"])
    total_source_reference_count = sum(item["source_reference_count"] for item in source_items)
    safe_fallback_mode_active = any(item["safe_fallback_mode_active"] for item in source_items)
    provenance_references = [
        {
            "source_domain": item["source_domain"],
            "source_type": item["source_type"],
            "boundary_path": item["boundary_path"],
            "source_reference_count": item["source_reference_count"],
            "provenance_visible": item["provenance_visible"],
        }
        for item in source_items
        if item["provenance_visible"] or item["source_reference_count"] > 0
    ]

    unresolved_coordination_domains = sorted(
        {
            str(item.get("source_domain", "") or "").strip()
            for item in source_items
            if not bool(item.get("availability", False))
            or bool(item.get("safe_fallback_mode_active", False))
        }
    )
    open_loop_items = [
        {
            "source_domain": str(item.get("source_domain", "") or "").strip(),
            "source_type": item.get("source_type"),
            "open_loop_state": (
                "pending"
                if (not bool(item.get("availability", False)) or bool(item.get("safe_fallback_mode_active", False)))
                else "resolved"
            ),
            "open_loop_reason_code": (
                "source_boundary_unavailable"
                if not bool(item.get("availability", False))
                else ("safe_fallback_active" if bool(item.get("safe_fallback_mode_active", False)) else "resolved")
            ),
            "source_reference_count": int(item.get("source_reference_count", 0) or 0),
            "provenance_visible": bool(item.get("provenance_visible", False)),
        }
        for item in source_items
    ]
    pending_open_loop_count = sum(1 for item in open_loop_items if item["open_loop_state"] == "pending")
    open_loop_state = "active" if pending_open_loop_count > 0 else "clear"

    status_state = "active" if available_source_count else "simplified"
    return {
        "household_status_synthesis_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_household_status_synthesis_boundary",
        "deterministic_boundary": True,
        "boundary_status": "active",
        "concierge_role": "bounded_consumer_orchestrator",
        "consumption_only": True,
        "representation_kinds": [
            "configuration_reference",
            "consumed_projection",
            "generated_explanation",
            "coordination_context",
            "clarification_response",
        ],
        "coordination_snapshot": {
            "coordination_snapshot_id": "coordsnap_release_6",
            "calendar_references": [item for item in source_items if item["source_domain"] == "calendar"],
            "task_references": [item for item in source_items if item["source_domain"] == "task"],
            "shopping_references": [item for item in source_items if item["source_domain"] == "shopping"],
            "messaging_references": [],
            "home_status_references": [],
            "coordination_explainability_references": [
                {
                    "source_domain": item["source_domain"],
                    "source_type": item["source_type"],
                    "safe_fallback_mode_active": item["safe_fallback_mode_active"],
                    "availability": item["availability"],
                }
                for item in source_items
            ],
            "provenance_references": provenance_references,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "coordination_snapshot_state": status_state,
        },
        "household_status_available": bool(available_source_count),
        "source_boundary_count": len(source_items),
        "configured_source_reference_count": total_source_reference_count,
        "safe_fallback_mode_active": safe_fallback_mode_active,
        "safe_fallback_reasons": [
            "source_boundary_unavailable",
        ] if not available_source_count else [],
        "open_loop_coordination_visibility": {
            "open_loop_supported": True,
            "open_loop_state": open_loop_state,
            "pending_open_loop_count": pending_open_loop_count,
            "unresolved_coordination_domains": unresolved_coordination_domains,
            "open_loop_items": open_loop_items,
            "informational_only": True,
            "coordination_authority_external": True,
            "source_of_record_external": True,
            "explainability_supported": True,
            "provenance_visibility_supported": True,
        },
        "source_boundaries": source_items,
        "briefing_composition_boundary": {
            "boundary_path": briefing_composition_boundary.get("boundary_path"),
            "briefing_composition_state": briefing_composition_boundary.get("briefing_composition", {}).get("briefing_composition_state"),
            "briefing_available": briefing_composition_boundary.get("briefing_available"),
        },
        "provenance_visibility": {
            "provenance_reference_count": len(provenance_references),
            "provenance_reference_present": bool(provenance_references),
            "provenance_visible": bool(provenance_references),
        },
        "explainability_visibility": {
            "household_status_explainability_supported": True,
            "source_domain_visible": True,
            "source_type_visible": True,
            "safe_fallback_visible": True,
        },
        "non_authority_assertions": {
            "creates_source_of_record": False,
            "stores_duplicate_canonical_records": False,
            "claims_household_status_authority": False,
            "creates_planning_engine": False,
            "creates_coordination_engine": False,
            "redefines_provenance_authority": False,
        },
        "deferred_release_6_owners": {
            "person_productivity_source_bindings": "#375",
            "calendar_and_email_consumption": "#363",
            "task_and_shopping_consumption": "#364",
            "capture_and_knowledge_consumption": "#365",
            "briefing_and_household_status_synthesis": "#366",
            "productivity_diagnostics_provenance_explainability": "#367",
            "household_coordination": "#368-#372",
            "release_6_validation": "#373",
        },
    }


def _build_productivity_coordination_boundary(
    *,
    state=None,
    hass: HomeAssistant | None = None,
    active_person_resolution: dict[str, Any] | None = None,
    runtime_person_context: dict[str, Any] | None = None,
    person_aware_productivity_routing: dict[str, Any] | None = None,
    calendar_email_consumption_boundary: dict[str, Any] | None = None,
    task_shopping_consumption_boundary: dict[str, Any] | None = None,
    capture_knowledge_consumption_boundary: dict[str, Any] | None = None,
    provenance_ownership_consumption_boundary: dict[str, Any] | None = None,
    route_scope: str = "global",
    context_area_id: str | None = None,
    resolved_composite_id: str | None = None,
) -> dict[str, Any]:
    """Return governed Release 6 productivity coordination metadata."""
    active_person_resolution = dict(
        active_person_resolution
        or {
            "active_person_state": "active_person_unavailable",
            "active_person_available": False,
            "resolved_person_id": None,
            "reason_code": "no_execution_envelope",
        }
    )
    runtime_person_context = dict(
        runtime_person_context
        or _build_runtime_person_context(state, active_person_resolution=active_person_resolution)
    )
    person_aware_productivity_routing = dict(
        person_aware_productivity_routing
        or _build_person_aware_productivity_routing(
            state=state,
            hass=hass,
            active_person_resolution=active_person_resolution,
            runtime_person_context=runtime_person_context,
        )
    )
    calendar_email_consumption_boundary = dict(
        calendar_email_consumption_boundary
        or _build_calendar_email_consumption_boundary(
            state=state,
            hass=hass,
            active_person_resolution=active_person_resolution,
            runtime_person_context=runtime_person_context,
        )
    )
    task_shopping_consumption_boundary = dict(
        task_shopping_consumption_boundary
        or _build_task_shopping_consumption_boundary(
            state=state,
            hass=hass,
            active_person_resolution=active_person_resolution,
            runtime_person_context=runtime_person_context,
        )
    )
    capture_knowledge_consumption_boundary = dict(
        capture_knowledge_consumption_boundary
        or _build_capture_knowledge_consumption_boundary(
            state=state,
            hass=hass,
        )
    )
    provenance_ownership_consumption_boundary = dict(
        provenance_ownership_consumption_boundary
        or _build_release_6_provenance_ownership_consumption_boundary(state=state, hass=hass)
    )

    routing_domains = dict(person_aware_productivity_routing.get("domain_routing", {}))
    calendar_email_domain_boundaries = dict(
        calendar_email_consumption_boundary.get("domain_boundaries", {})
    )
    task_shopping_domain_boundaries = dict(
        task_shopping_consumption_boundary.get("domain_boundaries", {})
    )
    calendar_email_person_count = int(
        calendar_email_consumption_boundary.get("person_calendar_email_bindings", {}).get(
            "person_count", 0
        )
        or 0
    )
    calendar_email_safe_fallback_count = int(
        calendar_email_consumption_boundary.get("person_calendar_email_bindings", {}).get(
            "safe_fallback_person_count", 0
        )
        or 0
    )
    shopping_person_count = int(
        task_shopping_consumption_boundary.get("person_shopping_bindings", {}).get(
            "person_count", 0
        )
        or 0
    )
    shopping_safe_fallback_count = int(
        task_shopping_consumption_boundary.get("person_shopping_bindings", {}).get(
            "safe_fallback_person_count", 0
        )
        or 0
    )

    domain_details = [
        {
            "domain": "calendar",
            "source_boundary": "calendar_email_consumption_boundary",
            "source_boundary_path": calendar_email_consumption_boundary.get("boundary_path"),
            "source_reference_count": int(
                calendar_email_consumption_boundary.get("configured_source_reference_count", 0)
                or 0
            ),
            "source_available": bool(
                calendar_email_domain_boundaries.get("calendar", {}).get(
                    "configured_reference_present", False
                )
                or calendar_email_person_count
            ),
            "safe_fallback_mode_active": bool(calendar_email_safe_fallback_count),
            "routing_enabled": bool(routing_domains.get("calendar", {}).get("enabled", False)),
            "routing_reason_code": routing_domains.get("calendar", {}).get("reason_code"),
            "selected_source_ref": routing_domains.get("calendar", {}).get("selected_source_ref"),
            "selection_mode": routing_domains.get("calendar", {}).get("selection_mode"),
        },
        {
            "domain": "email",
            "source_boundary": "calendar_email_consumption_boundary",
            "source_boundary_path": calendar_email_consumption_boundary.get("boundary_path"),
            "source_reference_count": int(
                calendar_email_consumption_boundary.get("configured_source_reference_count", 0)
                or 0
            ),
            "source_available": bool(
                calendar_email_domain_boundaries.get("email", {}).get(
                    "configured_reference_present", False
                )
                or calendar_email_person_count
            ),
            "safe_fallback_mode_active": bool(calendar_email_safe_fallback_count),
            "routing_enabled": bool(routing_domains.get("email", {}).get("enabled", False)),
            "routing_reason_code": routing_domains.get("email", {}).get("reason_code"),
            "selected_source_ref": routing_domains.get("email", {}).get("selected_source_ref"),
            "selection_mode": routing_domains.get("email", {}).get("selection_mode"),
        },
        {
            "domain": "task",
            "source_boundary": "task_shopping_consumption_boundary",
            "source_boundary_path": task_shopping_consumption_boundary.get("boundary_path"),
            "source_reference_count": int(
                task_shopping_consumption_boundary.get("configured_source_reference_count", 0)
                or 0
            ),
            "source_available": bool(
                task_shopping_domain_boundaries.get("task", {}).get(
                    "configured_reference_present", False
                )
                or shopping_person_count
            ),
            "safe_fallback_mode_active": bool(shopping_safe_fallback_count),
            "routing_enabled": bool(routing_domains.get("task", {}).get("enabled", False)),
            "routing_reason_code": routing_domains.get("task", {}).get("reason_code"),
            "selected_source_ref": routing_domains.get("task", {}).get("selected_source_ref"),
            "selection_mode": routing_domains.get("task", {}).get("selection_mode"),
        },
        {
            "domain": "shopping",
            "source_boundary": "task_shopping_consumption_boundary",
            "source_boundary_path": task_shopping_consumption_boundary.get("boundary_path"),
            "source_reference_count": int(
                task_shopping_consumption_boundary.get("configured_source_reference_count", 0)
                or 0
            ),
            "source_available": bool(
                task_shopping_domain_boundaries.get("shopping", {}).get(
                    "configured_reference_present", False
                )
                or shopping_person_count
            ),
            "safe_fallback_mode_active": bool(shopping_safe_fallback_count),
            "routing_enabled": bool(routing_domains.get("shopping", {}).get("enabled", False)),
            "routing_reason_code": routing_domains.get("shopping", {}).get("reason_code"),
            "selected_source_ref": routing_domains.get("shopping", {}).get("selected_source_ref"),
            "selection_mode": routing_domains.get("shopping", {}).get("selection_mode"),
        },
        {
            "domain": "capture",
            "source_boundary": "capture_knowledge_consumption_boundary",
            "source_boundary_path": capture_knowledge_consumption_boundary.get("boundary_path"),
            "source_reference_count": int(
                capture_knowledge_consumption_boundary.get("configured_source_reference_count", 0)
                or 0
            ),
            "source_available": bool(
                capture_knowledge_consumption_boundary.get("capture_consumption", {}).get(
                    "capture_available", False
                )
            ),
            "safe_fallback_mode_active": bool(
                capture_knowledge_consumption_boundary.get("capture_consumption", {}).get(
                    "safe_fallback_mode_active", False
                )
            ),
            "routing_enabled": False,
            "routing_reason_code": None,
            "selected_source_ref": None,
            "selection_mode": None,
        },
        {
            "domain": "knowledge",
            "source_boundary": "capture_knowledge_consumption_boundary",
            "source_boundary_path": capture_knowledge_consumption_boundary.get("boundary_path"),
            "source_reference_count": int(
                capture_knowledge_consumption_boundary.get("configured_source_reference_count", 0)
                or 0
            ),
            "source_available": bool(
                capture_knowledge_consumption_boundary.get("knowledge_consumption", {}).get(
                    "knowledge_available", False
                )
            ),
            "safe_fallback_mode_active": bool(
                capture_knowledge_consumption_boundary.get("knowledge_consumption", {}).get(
                    "safe_fallback_mode_active", False
                )
            ),
            "routing_enabled": False,
            "routing_reason_code": None,
            "selected_source_ref": None,
            "selection_mode": None,
        },
    ]

    participating_domains = sorted(
        {
            str(item.get("domain", "") or "").strip()
            for item in domain_details
            if bool(item.get("source_available", False))
            or bool(item.get("routing_enabled", False))
            or bool(item.get("safe_fallback_mode_active", False))
        }
    )
    pending_domains = sorted(
        {
            str(item.get("domain", "") or "").strip()
            for item in domain_details
            if not bool(item.get("source_available", False))
            or bool(item.get("safe_fallback_mode_active", False))
        }
    )
    runtime_context_state = str(
        runtime_person_context.get("person_context_state", "person_context_unresolved")
    ).strip().lower()

    if not participating_domains:
        coordination_state = "simplified"
    elif runtime_context_state in {"person_context_partial", "person_context_unresolved"}:
        coordination_state = "restricted"
    else:
        coordination_state = "active"

    provenance_inputs = {
        "boundary_path": provenance_ownership_consumption_boundary.get("boundary_path"),
        "provenance_reference_count": int(
            provenance_ownership_consumption_boundary.get("provenance_visibility", {}).get(
                "provenance_reference_count", 0
            )
            or 0
        ),
        "provenance_visible": bool(
            provenance_ownership_consumption_boundary.get("provenance_visibility", {}).get(
                "provenance_visible", False
            )
        ),
        "lineage_completeness_ready": bool(
            provenance_ownership_consumption_boundary.get("readiness_assessment", {}).get(
                "lineage_completeness_ready", False
            )
        ),
    }

    return {
        "productivity_coordination_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_productivity_coordination_boundary",
        "deterministic_boundary": True,
        "boundary_status": "active",
        "concierge_role": "bounded_consumer_orchestrator",
        "consumption_only": True,
        "informational_only": True,
        "coordination_state": coordination_state,
        "coordination_awareness": {
            "participating_domains": participating_domains,
            "pending_domains": pending_domains,
            "participating_domain_count": len(participating_domains),
            "pending_domain_count": len(pending_domains),
            "cross_domain_coordination_supported": True,
            "cross_domain_coordination_state": (
                "active" if len(participating_domains) > 1 else "limited"
            ),
        },
        "coordination_categories": [
            "calendar_coordination",
            "email_coordination",
            "task_coordination",
            "shopping_coordination",
            "cross_domain_productivity_coordination",
        ],
        "domain_coordination": domain_details,
        "runtime_person_context": {
            "person_context_state": runtime_person_context.get("person_context_state"),
            "reason_code": runtime_person_context.get("reason_code"),
            "resolved_person_id": runtime_person_context.get("resolved_person_id"),
            "resolved_voice_profile_id": runtime_person_context.get("resolved_voice_profile_id"),
            "resolved_concierge_person_profile_id": runtime_person_context.get(
                "resolved_concierge_person_profile_id"
            ),
        },
        "person_aware_routing_inputs": {
            "routing_enabled": bool(person_aware_productivity_routing.get("routing_enabled", False)),
            "reason_code": person_aware_productivity_routing.get("reason_code"),
            "active_person_state": person_aware_productivity_routing.get("active_person_state"),
            "active_person_available": bool(
                person_aware_productivity_routing.get("active_person_available", False)
            ),
            "resolved_person_id": person_aware_productivity_routing.get("resolved_person_id"),
            "domain_routing": {
                domain: {
                    "enabled": bool(details.get("enabled", False)),
                    "reason_code": details.get("reason_code"),
                    "selected_source_ref": details.get("selected_source_ref"),
                    "selection_mode": details.get("selection_mode"),
                }
                for domain, details in routing_domains.items()
            },
        },
        "provenance_inputs": provenance_inputs,
        "governance_context": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "active_person_state": active_person_resolution.get("active_person_state"),
            "active_person_available": bool(
                active_person_resolution.get("active_person_available", False)
            ),
        },
        "explainability_visibility": {
            "coordination_state_visible": True,
            "participating_domains_visible": True,
            "productivity_inputs_visible": True,
            "routing_inputs_visible": True,
            "provenance_inputs_visible": True,
            "safe_fallback_visible": True,
        },
        "diagnostics_visibility": {
            "coordination_visibility_supported": True,
            "explainability_supported": True,
            "provenance_visibility_supported": True,
            "ownership_verification_supported": True,
            "safe_source_metadata_only": True,
            "sensitive_source_content_exposed": False,
        },
        "non_authority_assertions": {
            "creates_source_of_record": False,
            "stores_duplicate_canonical_records": False,
            "claims_productivity_authority": False,
            "claims_coordination_authority": False,
            "claims_provenance_authority": False,
            "creates_planning_engine": False,
            "creates_workflow_engine": False,
            "redefines_identity_authority": False,
        },
        "deferred_release_6_owners": {
            "person_productivity_source_bindings": "#375",
            "calendar_and_email_consumption": "#363",
            "task_and_shopping_consumption": "#364",
            "capture_and_knowledge_consumption": "#365",
            "briefing_and_household_status_synthesis": "#366",
            "productivity_diagnostics_provenance_explainability": "#367",
            "provenance_ownership_and_consumption": "#368",
            "household_coordination": "#369-#372",
            "release_6_validation": "#373",
        },
    }


def _build_household_coordination_boundary(
    *,
    state=None,
    hass: HomeAssistant | None = None,
    active_person_resolution: dict[str, Any] | None = None,
    runtime_person_context: dict[str, Any] | None = None,
    person_aware_productivity_routing: dict[str, Any] | None = None,
    household_status_synthesis_boundary: dict[str, Any] | None = None,
    provenance_ownership_consumption_boundary: dict[str, Any] | None = None,
    route_scope: str = "global",
    context_area_id: str | None = None,
    resolved_composite_id: str | None = None,
) -> dict[str, Any]:
    """Return governed Release 6 household coordination boundary metadata."""
    household_status_synthesis_boundary = dict(
        household_status_synthesis_boundary
        or _build_household_status_synthesis_boundary(state=state, hass=hass)
    )
    provenance_ownership_consumption_boundary = dict(
        provenance_ownership_consumption_boundary
        or _build_release_6_provenance_ownership_consumption_boundary(state=state, hass=hass)
    )
    active_person_resolution = dict(
        active_person_resolution
        or {
            "active_person_state": "active_person_unavailable",
            "active_person_available": False,
            "resolved_person_id": None,
            "reason_code": "no_execution_envelope",
        }
    )
    runtime_person_context = dict(
        runtime_person_context
        or _build_runtime_person_context(state, active_person_resolution=active_person_resolution)
    )
    person_aware_productivity_routing = dict(
        person_aware_productivity_routing
        or _build_person_aware_productivity_routing(
            state=state,
            hass=hass,
            active_person_resolution=active_person_resolution,
            runtime_person_context=runtime_person_context,
        )
    )

    routing_domains = dict(person_aware_productivity_routing.get("domain_routing", {}))
    source_boundaries = list(household_status_synthesis_boundary.get("source_boundaries", []))
    source_by_domain = {
        str(item.get("source_domain", "") or ""): dict(item)
        for item in source_boundaries
        if isinstance(item, dict)
    }

    contributor_domains = [
        "calendar",
        "email",
        "task",
        "shopping",
        "capture",
        "knowledge",
        "briefing",
        "household_status",
    ]
    contributors: list[dict[str, Any]] = []
    for domain in contributor_domains:
        routing = dict(routing_domains.get(domain, {}))
        source = dict(source_by_domain.get(domain, {}))
        contributor_available = bool(source.get("availability", False))
        if domain in {"calendar", "email", "task", "shopping"}:
            contributor_available = contributor_available or bool(routing.get("enabled", False))
        contributors.append(
            {
                "source_domain": domain,
                "contributor_available": contributor_available,
                "source_type": source.get("source_type"),
                "source_reference_count": int(source.get("source_reference_count", 0) or 0),
                "routing_enabled": bool(routing.get("enabled", False)),
                "routing_reason_code": routing.get("reason_code"),
                "selected_source_ref": routing.get("selected_source_ref"),
                "selection_mode": routing.get("selection_mode"),
                "safe_fallback_mode_active": bool(source.get("safe_fallback_mode_active", False)),
            }
        )

    available_contributor_count = sum(1 for item in contributors if item["contributor_available"])
    configured_source_reference_count = int(
        household_status_synthesis_boundary.get("configured_source_reference_count", 0) or 0
    )
    household_status_available = bool(
        household_status_synthesis_boundary.get("household_status_available", False)
    )
    runtime_context_state = str(
        runtime_person_context.get("person_context_state", "person_context_unresolved")
    ).strip().lower()

    if household_status_available:
        coordination_state = "active"
    elif runtime_context_state in {"person_context_partial", "person_context_unresolved"}:
        coordination_state = "restricted"
    else:
        coordination_state = "simplified"

    provenance_context = {
        "boundary_path": provenance_ownership_consumption_boundary.get("boundary_path"),
        "provenance_reference_count": int(
            provenance_ownership_consumption_boundary.get("provenance_visibility", {}).get(
                "provenance_reference_count", 0
            )
            or 0
        ),
        "provenance_visible": bool(
            provenance_ownership_consumption_boundary.get("provenance_visibility", {}).get(
                "provenance_visible", False
            )
        ),
        "lineage_completeness_ready": bool(
            provenance_ownership_consumption_boundary.get("readiness_assessment", {}).get(
                "lineage_completeness_ready", False
            )
        ),
    }

    coordination_snapshot = dict(
        household_status_synthesis_boundary.get("coordination_snapshot", {})
    )
    coordination_snapshot_state = str(
        coordination_snapshot.get("coordination_snapshot_state", coordination_state)
    ).strip() or coordination_state

    coordination_explainability = {
        "coordination_state": coordination_state,
        "coordination_source": "governed_release_6_consumption_boundaries",
        "coordination_contributors": [
            {
                "source_domain": item["source_domain"],
                "contributor_available": item["contributor_available"],
                "routing_enabled": item["routing_enabled"],
                "routing_reason_code": item["routing_reason_code"],
                "selection_mode": item["selection_mode"],
            }
            for item in contributors
        ],
        "coordination_context": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
            "active_person_state": active_person_resolution.get("active_person_state"),
            "active_person_available": bool(
                active_person_resolution.get("active_person_available", False)
            ),
            "resolved_person_id": active_person_resolution.get("resolved_person_id"),
            "runtime_person_context_state": runtime_context_state,
            "person_aware_routing_enabled": bool(
                person_aware_productivity_routing.get("routing_enabled", False)
            ),
            "person_aware_routing_reason_code": person_aware_productivity_routing.get("reason_code"),
        },
        "provenance_context": provenance_context,
    }

    safe_fallback_mode_active = coordination_state != "active"
    safe_fallback_reasons: list[str] = []
    if not household_status_available:
        safe_fallback_reasons.append("household_status_unavailable")
    if runtime_context_state != "person_context_resolved":
        safe_fallback_reasons.append(runtime_context_state)
    if not provenance_context["lineage_completeness_ready"]:
        safe_fallback_reasons.append("provenance_lineage_incomplete")

    open_loop_visibility = dict(
        household_status_synthesis_boundary.get("open_loop_coordination_visibility", {})
    )
    if not open_loop_visibility:
        open_loop_visibility = {
            "open_loop_supported": True,
            "open_loop_state": "active" if safe_fallback_mode_active else "clear",
            "pending_open_loop_count": 1 if safe_fallback_mode_active else 0,
            "unresolved_coordination_domains": ["household_status"] if safe_fallback_mode_active else [],
            "open_loop_items": [],
            "informational_only": True,
            "coordination_authority_external": True,
            "source_of_record_external": True,
            "explainability_supported": True,
            "provenance_visibility_supported": True,
        }

    return {
        "household_coordination_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_household_coordination_boundary",
        "deterministic_boundary": True,
        "boundary_status": "active",
        "concierge_role": "bounded_consumer_orchestrator",
        "consumption_only": True,
        "coordination_state": coordination_state,
        "coordination_snapshot": {
            "coordination_snapshot_id": coordination_snapshot.get(
                "coordination_snapshot_id", "coordsnap_release_6"
            ),
            "coordination_snapshot_state": coordination_snapshot_state,
            "timestamp": coordination_snapshot.get("timestamp"),
        },
        "coordination_source": "governed_release_6_consumption_boundaries",
        "coordination_contributors": contributors,
        "coordination_context": coordination_explainability["coordination_context"],
        "provenance_context": provenance_context,
        "runtime_person_context": {
            "person_context_state": runtime_person_context.get("person_context_state"),
            "reason_code": runtime_person_context.get("reason_code"),
            "resolved_person_id": runtime_person_context.get("resolved_person_id"),
            "resolved_voice_profile_id": runtime_person_context.get("resolved_voice_profile_id"),
            "resolved_concierge_person_profile_id": runtime_person_context.get(
                "resolved_concierge_person_profile_id"
            ),
        },
        "person_aware_productivity_routing": {
            "routing_enabled": bool(
                person_aware_productivity_routing.get("routing_enabled", False)
            ),
            "reason_code": person_aware_productivity_routing.get("reason_code"),
            "active_person_state": person_aware_productivity_routing.get(
                "active_person_state"
            ),
            "active_person_available": bool(
                person_aware_productivity_routing.get("active_person_available", False)
            ),
            "resolved_person_id": person_aware_productivity_routing.get("resolved_person_id"),
            "domain_routing": {
                domain: {
                    "enabled": bool(details.get("enabled", False)),
                    "reason_code": details.get("reason_code"),
                    "selected_source_ref": details.get("selected_source_ref"),
                    "selection_mode": details.get("selection_mode"),
                }
                for domain, details in routing_domains.items()
            },
        },
        "configured_source_reference_count": configured_source_reference_count,
        "source_boundary_count": len(source_boundaries),
        "available_contributor_count": available_contributor_count,
        "safe_fallback_mode_active": safe_fallback_mode_active,
        "safe_fallback_reasons": safe_fallback_reasons,
        "open_loop_coordination_visibility": {
            **open_loop_visibility,
            "coordination_state": coordination_state,
            "runtime_person_context_state": runtime_context_state,
        },
        "provenance_visibility": {
            "provenance_visible": provenance_context["provenance_visible"],
            "provenance_reference_count": provenance_context["provenance_reference_count"],
            "lineage_completeness_ready": provenance_context["lineage_completeness_ready"],
        },
        "explainability_visibility": {
            "coordination_state_visible": True,
            "coordination_source_visible": True,
            "coordination_contributors_visible": True,
            "coordination_context_visible": True,
            "provenance_context_visible": True,
            "safe_fallback_visible": True,
            "coordination_explainability": coordination_explainability,
        },
        "diagnostics_visibility": {
            "boundary_verification_supported": True,
            "runtime_context_visibility_supported": True,
            "provenance_visibility_supported": True,
            "safe_source_metadata_only": True,
            "sensitive_source_content_exposed": False,
        },
        "non_authority_assertions": {
            "creates_source_of_record": False,
            "stores_duplicate_canonical_records": False,
            "claims_coordination_authority": False,
            "claims_provenance_authority": False,
            "creates_planning_engine": False,
            "redefines_identity_authority": False,
        },
        "deferred_release_6_owners": {
            "person_productivity_source_bindings": "#375",
            "calendar_and_email_consumption": "#363",
            "task_and_shopping_consumption": "#364",
            "capture_and_knowledge_consumption": "#365",
            "briefing_and_household_status_synthesis": "#366",
            "productivity_diagnostics_provenance_explainability": "#367",
            "provenance_ownership_and_consumption": "#368",
            "household_coordination": "#369-#372",
            "release_6_validation": "#373",
        },
    }


def _build_release_6_provenance_ownership_consumption_boundary(
    *,
    state=None,
    hass: HomeAssistant | None = None,
) -> dict[str, Any]:
    """Return governed Release 6 provenance ownership and consumption metadata."""
    source_views = [
        {
            "boundary_name": "productivity_source_of_record_boundary",
            "source_domain": "productivity",
            "source_type": "productivity_source_of_record_boundary",
            "visibility": _build_productivity_source_of_record_boundary(state=state, hass=hass),
            "available": True if state is not None else False,
        },
        {
            "boundary_name": "calendar_email_consumption_boundary",
            "source_domain": "calendar_email",
            "source_type": "calendar_email_consumption_boundary",
            "visibility": _build_calendar_email_consumption_boundary(state=state, hass=hass),
            "available": bool(
                _build_calendar_email_consumption_boundary(state=state, hass=hass).get("configured_source_reference_count", 0)
                or _build_calendar_email_consumption_boundary(state=state, hass=hass).get("person_calendar_email_bindings", {}).get("person_count", 0)
            ),
        },
        {
            "boundary_name": "task_shopping_consumption_boundary",
            "source_domain": "task_shopping",
            "source_type": "task_shopping_consumption_boundary",
            "visibility": _build_task_shopping_consumption_boundary(state=state, hass=hass),
            "available": bool(
                _build_task_shopping_consumption_boundary(state=state, hass=hass).get("configured_source_reference_count", 0)
                or _build_task_shopping_consumption_boundary(state=state, hass=hass).get("person_shopping_bindings", {}).get("person_count", 0)
            ),
        },
        {
            "boundary_name": "capture_knowledge_consumption_boundary",
            "source_domain": "capture_knowledge",
            "source_type": "capture_knowledge_consumption_boundary",
            "visibility": _build_capture_knowledge_consumption_boundary(state=state, hass=hass),
            "available": bool(
                _build_capture_knowledge_consumption_boundary(state=state, hass=hass).get("knowledge_consumption", {}).get("knowledge_available", False)
                or _build_capture_knowledge_consumption_boundary(state=state, hass=hass).get("capture_consumption", {}).get("capture_available", False)
            ),
        },
        {
            "boundary_name": "briefing_composition_boundary",
            "source_domain": "briefing",
            "source_type": "briefing_composition_boundary",
            "visibility": _build_briefing_composition_boundary(state=state, hass=hass),
            "available": bool(_build_briefing_composition_boundary(state=state, hass=hass).get("briefing_available", False)),
        },
        {
            "boundary_name": "household_status_synthesis_boundary",
            "source_domain": "household_status",
            "source_type": "household_status_synthesis_boundary",
            "visibility": _build_household_status_synthesis_boundary(state=state, hass=hass),
            "available": bool(_build_household_status_synthesis_boundary(state=state, hass=hass).get("household_status_available", False)),
        },
    ]

    boundary_entries: list[dict[str, Any]] = []
    for item in source_views:
        visibility = item["visibility"]
        provenance_visibility = visibility.get("provenance_visibility", {})
        explainability_visibility = visibility.get("explainability_visibility", {})
        ownership_visible = bool(visibility.get("non_authority_assertions") or visibility.get("authority_relationships"))
        source_authority_visible = bool(
            visibility.get("provenance_requirements", {}).get("provenance_authority_external", False)
            or visibility.get("domain_boundaries", {})
            or visibility.get("governance_controls", {})
        )
        provenance_visible = bool(provenance_visibility.get("provenance_visible", False))
        attribution_visible = bool(
            provenance_visible
            or bool(explainability_visibility)
            or bool(visibility.get("authority_visibility", {}))
        )
        lineage_visible = bool(provenance_visible or provenance_visibility.get("provenance_reference_count", 0))
        explainability_visible = bool(explainability_visibility or visibility.get("clarification_behavior", {}))
        boundary_entries.append(
            {
                "boundary_name": item["boundary_name"],
                "source_domain": item["source_domain"],
                "source_type": item["source_type"],
                "boundary_path": visibility.get("boundary_path"),
                "available": bool(item["available"]),
                "source_ownership_visible": ownership_visible,
                "source_authority_visible": source_authority_visible,
                "provenance_ownership_visible": provenance_visible or source_authority_visible,
                "provenance_available": provenance_visible,
                "provenance_incomplete": not provenance_visible,
                "attribution_visible": attribution_visible,
                "attribution_incomplete": not attribution_visible,
                "lineage_visible": lineage_visible,
                "explainability_visible": explainability_visible,
            }
        )

    boundary_count = len(boundary_entries)
    provenance_reference_count = sum(
        int(item["visibility"].get("provenance_visibility", {}).get("provenance_reference_count", 0) or 0)
        for item in source_views
    )
    source_ownership_visible_boundary_count = sum(1 for item in boundary_entries if item["source_ownership_visible"])
    source_authority_visible_boundary_count = sum(1 for item in boundary_entries if item["source_authority_visible"])
    provenance_ownership_visible_boundary_count = sum(1 for item in boundary_entries if item["provenance_ownership_visible"])
    provenance_available_boundary_count = sum(1 for item in boundary_entries if item["provenance_available"])
    provenance_incomplete_boundary_count = sum(1 for item in boundary_entries if item["provenance_incomplete"])
    attribution_visible_boundary_count = sum(1 for item in boundary_entries if item["attribution_visible"])
    attribution_incomplete_boundary_count = sum(1 for item in boundary_entries if item["attribution_incomplete"])
    lineage_visible_boundary_count = sum(1 for item in boundary_entries if item["lineage_visible"])
    explainability_visible_boundary_count = sum(1 for item in boundary_entries if item["explainability_visible"])

    ownership_complete_boundary_count = sum(
        1 for item in boundary_entries if item["source_ownership_visible"] and item["source_authority_visible"]
    )

    return {
        "release_6_provenance_ownership_consumption_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_release_6_provenance_ownership_consumption_boundary",
        "deterministic_boundary": True,
        "boundary_status": "active",
        "concierge_role": "bounded_consumer_orchestrator",
        "source_boundaries": boundary_entries,
        "provenance_ownership_visibility": {
            "boundary_count": boundary_count,
            "provenance_reference_count": provenance_reference_count,
            "source_ownership_visible_boundary_count": source_ownership_visible_boundary_count,
            "source_authority_visible_boundary_count": source_authority_visible_boundary_count,
            "provenance_ownership_visible_boundary_count": provenance_ownership_visible_boundary_count,
            "ownership_complete_boundary_count": ownership_complete_boundary_count,
            "ownership_incomplete_boundary_count": boundary_count - ownership_complete_boundary_count,
        },
        "provenance_consumption_visibility": {
            "boundary_count": boundary_count,
            "provenance_visible": provenance_available_boundary_count > 0,
            "provenance_available_boundary_count": provenance_available_boundary_count,
            "provenance_unavailable_boundary_count": boundary_count - provenance_available_boundary_count,
            "provenance_incomplete_boundary_count": provenance_incomplete_boundary_count,
            "attribution_visible_boundary_count": attribution_visible_boundary_count,
            "attribution_incomplete_boundary_count": attribution_incomplete_boundary_count,
            "lineage_visible_boundary_count": lineage_visible_boundary_count,
        },
        "provenance_visibility": {
            "provenance_reference_count": provenance_reference_count,
            "provenance_visible": provenance_available_boundary_count > 0,
        },
        "explainability_visibility": {
            "source_domain_visible": source_ownership_visible_boundary_count > 0,
            "source_type_visible": source_authority_visible_boundary_count > 0,
            "safe_fallback_visible": True,
        },
        "readiness_assessment": {
            "ownership_visibility_ready": ownership_complete_boundary_count == boundary_count,
            "attribution_visibility_ready": attribution_visible_boundary_count == boundary_count,
            "lineage_completeness_ready": provenance_available_boundary_count == boundary_count,
            "boundary_completeness_ready": ownership_complete_boundary_count == boundary_count
            and attribution_visible_boundary_count == boundary_count,
            "explainability_readiness": explainability_visible_boundary_count == boundary_count,
        },
        "safe_fallback_mode_active": not all(item["available"] for item in boundary_entries),
        "safe_fallback_reason": (
            "provenance_lineage_incomplete" if provenance_available_boundary_count < boundary_count else None
        ),
        "safe_fallback_visibility": {
            "available_boundary_count": sum(1 for item in boundary_entries if item["available"]),
            "degraded_boundary_count": sum(1 for item in boundary_entries if not item["available"]),
            "missing_prerequisite_boundary_count": sum(1 for item in boundary_entries if not item["available"]),
        },
        "non_authority_assertions": {
            "creates_source_of_record": False,
            "stores_duplicate_canonical_records": False,
            "claims_ownership_authority": False,
            "claims_provenance_authority": False,
            "claims_coordination_authority": False,
            "claims_governance_authority": False,
        },
        "deferred_release_6_owners": {
            "person_productivity_source_bindings": "#375",
            "calendar_and_email_consumption": "#363",
            "task_and_shopping_consumption": "#364",
            "capture_and_knowledge_consumption": "#365",
            "briefing_and_household_status_synthesis": "#366",
            "productivity_diagnostics_provenance_explainability": "#367",
            "provenance_ownership_and_consumption": "#368",
            "household_coordination": "#369-#372",
            "release_6_validation": "#373",
        },
    }


def _build_release_6_provenance_diagnostics_explainability_boundary(
    *,
    state=None,
    hass: HomeAssistant | None = None,
    route_scope: str = "global",
    context_area_id: str | None = None,
    resolved_composite_id: str | None = None,
    runtime_person_context: dict[str, Any] | None = None,
    person_aware_productivity_routing: dict[str, Any] | None = None,
    productivity_coordination_boundary: dict[str, Any] | None = None,
    household_status_synthesis_boundary: dict[str, Any] | None = None,
    household_coordination_boundary: dict[str, Any] | None = None,
    provenance_ownership_consumption_boundary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return governed Release 6 provenance diagnostics and explainability metadata."""
    runtime_person_context = dict(
        runtime_person_context
        or {
            "person_context_state": "person_context_unresolved",
            "reason_code": "person_profile_not_configured",
            "resolved_person_id": None,
            "resolved_voice_profile_id": None,
            "resolved_concierge_person_profile_id": None,
        }
    )
    person_aware_productivity_routing = dict(
        person_aware_productivity_routing
        or _build_person_aware_productivity_routing(
            state=state,
            hass=hass,
            runtime_person_context=runtime_person_context,
        )
    )
    productivity_coordination_boundary = dict(
        productivity_coordination_boundary
        or _build_productivity_coordination_boundary(
            state=state,
            hass=hass,
            runtime_person_context=runtime_person_context,
            person_aware_productivity_routing=person_aware_productivity_routing,
            route_scope=route_scope,
            context_area_id=context_area_id,
            resolved_composite_id=resolved_composite_id,
        )
    )
    household_status_synthesis_boundary = dict(
        household_status_synthesis_boundary
        or _build_household_status_synthesis_boundary(
            state=state,
            hass=hass,
        )
    )
    provenance_ownership_consumption_boundary = dict(
        provenance_ownership_consumption_boundary
        or _build_release_6_provenance_ownership_consumption_boundary(
            state=state,
            hass=hass,
        )
    )
    household_coordination_boundary = dict(
        household_coordination_boundary
        or _build_household_coordination_boundary(
            state=state,
            hass=hass,
            runtime_person_context=runtime_person_context,
            person_aware_productivity_routing=person_aware_productivity_routing,
            household_status_synthesis_boundary=household_status_synthesis_boundary,
            provenance_ownership_consumption_boundary=provenance_ownership_consumption_boundary,
            route_scope=route_scope,
            context_area_id=context_area_id,
            resolved_composite_id=resolved_composite_id,
        )
    )

    source_boundaries = list(provenance_ownership_consumption_boundary.get("source_boundaries", []))
    provenance_ownership_visibility = dict(
        provenance_ownership_consumption_boundary.get("provenance_ownership_visibility", {})
    )
    provenance_consumption_visibility = dict(
        provenance_ownership_consumption_boundary.get("provenance_consumption_visibility", {})
    )
    readiness_assessment = dict(
        provenance_ownership_consumption_boundary.get("readiness_assessment", {})
    )

    provenance_reference_count = int(
        provenance_ownership_visibility.get("provenance_reference_count", 0) or 0
    )
    boundary_count = int(provenance_ownership_visibility.get("boundary_count", 0) or 0)
    lineage_completeness_ready = bool(readiness_assessment.get("lineage_completeness_ready", False))

    source_boundary_inspection = [
        {
            "boundary_name": str(item.get("boundary_name", "") or ""),
            "source_domain": str(item.get("source_domain", "") or ""),
            "source_type": str(item.get("source_type", "") or ""),
            "boundary_path": item.get("boundary_path"),
            "source_authority_visible": bool(item.get("source_authority_visible", False)),
            "source_ownership_visible": bool(item.get("source_ownership_visible", False)),
            "provenance_ownership_visible": bool(item.get("provenance_ownership_visible", False)),
            "provenance_available": bool(item.get("provenance_available", False)),
            "attribution_visible": bool(item.get("attribution_visible", False)),
            "lineage_visible": bool(item.get("lineage_visible", False)),
            "explainability_visible": bool(item.get("explainability_visible", False)),
        }
        for item in source_boundaries
    ]

    routing_domain_inputs = {
        domain: {
            "enabled": bool(details.get("enabled", False)),
            "reason_code": details.get("reason_code"),
            "selected_source_ref": details.get("selected_source_ref"),
            "selection_mode": details.get("selection_mode"),
        }
        for domain, details in dict(
            person_aware_productivity_routing.get("domain_routing", {})
        ).items()
    }

    return {
        "release_6_provenance_diagnostics_explainability_boundary_version": 1,
        "applicable": True,
        "boundary_path": "governed_release_6_provenance_diagnostics_explainability_boundary",
        "deterministic_boundary": True,
        "boundary_status": "active",
        "concierge_role": "bounded_consumer_orchestrator",
        "consumption_only": True,
        "informational_only": True,
        "provenance_diagnostics": {
            "boundary_count": boundary_count,
            "provenance_reference_count": provenance_reference_count,
            "ownership_visible_boundary_count": int(
                provenance_ownership_visibility.get("source_ownership_visible_boundary_count", 0) or 0
            ),
            "authority_visible_boundary_count": int(
                provenance_ownership_visibility.get("source_authority_visible_boundary_count", 0) or 0
            ),
            "provenance_available_boundary_count": int(
                provenance_consumption_visibility.get("provenance_available_boundary_count", 0) or 0
            ),
            "provenance_incomplete_boundary_count": int(
                provenance_consumption_visibility.get("provenance_incomplete_boundary_count", 0)
                or 0
            ),
            "attribution_visible_boundary_count": int(
                provenance_consumption_visibility.get("attribution_visible_boundary_count", 0)
                or 0
            ),
            "lineage_visible_boundary_count": int(
                provenance_consumption_visibility.get("lineage_visible_boundary_count", 0) or 0
            ),
            "lineage_completeness_ready": lineage_completeness_ready,
            "safe_fallback_reason": provenance_ownership_consumption_boundary.get("safe_fallback_reason"),
        },
        "provenance_explainability": {
            "source_boundary_inspection": source_boundary_inspection,
            "source_boundary_count": len(source_boundary_inspection),
            "productivity_inputs": {
                "boundary_path": productivity_coordination_boundary.get("boundary_path"),
                "coordination_state": productivity_coordination_boundary.get("coordination_state"),
                "coordination_categories": list(
                    productivity_coordination_boundary.get("coordination_categories", [])
                ),
                "domain_coordination": list(
                    productivity_coordination_boundary.get("domain_coordination", [])
                ),
            },
            "routing_inputs": {
                "routing_enabled": bool(
                    person_aware_productivity_routing.get("routing_enabled", False)
                ),
                "reason_code": person_aware_productivity_routing.get("reason_code"),
                "active_person_state": person_aware_productivity_routing.get("active_person_state"),
                "active_person_available": bool(
                    person_aware_productivity_routing.get("active_person_available", False)
                ),
                "resolved_person_id": person_aware_productivity_routing.get("resolved_person_id"),
                "domain_routing": routing_domain_inputs,
            },
            "coordination_inputs": {
                "boundary_path": household_coordination_boundary.get("boundary_path"),
                "coordination_state": household_coordination_boundary.get("coordination_state"),
                "coordination_source": household_coordination_boundary.get("coordination_source"),
                "available_contributor_count": int(
                    household_coordination_boundary.get("available_contributor_count", 0) or 0
                ),
                "provenance_context": dict(
                    household_coordination_boundary.get("provenance_context", {})
                ),
            },
            "status_inputs": {
                "boundary_path": household_status_synthesis_boundary.get("boundary_path"),
                "household_status_available": bool(
                    household_status_synthesis_boundary.get("household_status_available", False)
                ),
                "open_loop_coordination_visibility": dict(
                    household_status_synthesis_boundary.get("open_loop_coordination_visibility", {})
                ),
            },
        },
        "runtime_person_context": {
            "person_context_state": runtime_person_context.get("person_context_state"),
            "reason_code": runtime_person_context.get("reason_code"),
            "resolved_person_id": runtime_person_context.get("resolved_person_id"),
            "resolved_voice_profile_id": runtime_person_context.get("resolved_voice_profile_id"),
            "resolved_concierge_person_profile_id": runtime_person_context.get(
                "resolved_concierge_person_profile_id"
            ),
        },
        "governance_context": {
            "route_scope": route_scope,
            "context_area_id": context_area_id,
            "resolved_composite_id": resolved_composite_id,
        },
        "provenance_visibility": {
            "provenance_reference_count": provenance_reference_count,
            "provenance_visible": provenance_reference_count > 0,
            "lineage_completeness_ready": lineage_completeness_ready,
        },
        "safe_fallback_mode_active": not lineage_completeness_ready,
        "safe_fallback_reason": (
            "provenance_lineage_incomplete" if not lineage_completeness_ready else None
        ),
        "diagnostics_visibility": {
            "provenance_visibility_supported": True,
            "ownership_visibility_supported": True,
            "authority_visibility_supported": True,
            "runtime_inspection_supported": True,
            "safe_source_metadata_only": True,
            "sensitive_source_content_exposed": False,
        },
        "explainability_visibility": {
            "source_boundary_visible": True,
            "source_domain_visible": True,
            "source_type_visible": True,
            "ownership_boundary_visible": True,
            "provenance_inputs_visible": True,
            "routing_inputs_visible": True,
            "coordination_inputs_visible": True,
            "status_inputs_visible": True,
            "runtime_person_context_visible": True,
            "safe_fallback_visible": True,
        },
        "non_authority_assertions": {
            "creates_source_of_record": False,
            "stores_duplicate_canonical_records": False,
            "claims_provenance_authority": False,
            "claims_lineage_authority": False,
            "claims_ownership_authority": False,
            "claims_routing_authority": False,
            "creates_planning_engine": False,
            "creates_workflow_engine": False,
            "redefines_identity_authority": False,
        },
        "deferred_release_6_owners": {
            "person_productivity_source_bindings": "#375",
            "calendar_and_email_consumption": "#363",
            "task_and_shopping_consumption": "#364",
            "capture_and_knowledge_consumption": "#365",
            "briefing_and_household_status_synthesis": "#366",
            "productivity_diagnostics_provenance_explainability": "#367",
            "provenance_ownership_and_consumption": "#368",
            "household_coordination": "#369-#372",
            "provenance_diagnostics_and_explainability": "#372",
            "release_6_validation": "#373",
        },
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


def _latest_execution_envelope_ref_from_state(state) -> dict[str, Any] | None:
    """Return latest execution-envelope reference from persisted activity history."""
    refs: list[dict[str, Any]] = []
    for activity in sorted(
        state.activities.values(),
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        for ref in list(getattr(activity, "external_refs", [])):
            if str(ref.get("ref_type", "") or "") == "execution_envelope":
                refs.append(dict(ref))
    return refs[0] if refs else None


def _resolve_active_person_resolution_from_envelope(
    latest_envelope: dict[str, Any] | None,
) -> dict[str, Any]:
    """Resolve active person state from consumed Voice Identity attribution fields."""
    if latest_envelope is None:
        return {
            "resolution_enabled": True,
            "active_person_state": "active_person_unavailable",
            "active_person_available": False,
            "resolved_person_id": None,
            "resolved_voice_profile_id": None,
            "attribution_available": False,
            "identity_context_available": False,
            "confidence_available": False,
            "confidence_accepted": False,
            "confidence": None,
            "confidence_band": None,
            "readiness_state": "unavailable",
            "reason_code": "no_execution_envelope",
            "resolution_posture": "fail_closed",
            "fail_closed": True,
            "authority_source": "voice_identity",
            "consumption_only": True,
        }

    def _coerce_confidence(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    attribution_consumed = bool(latest_envelope.get("voice_identity_attribution_consumed", False))
    attribution_state = str(latest_envelope.get("voice_identity_attribution_state", "") or "").strip().lower()
    attribution_reason = str(latest_envelope.get("voice_identity_attribution_reason_code", "") or "").strip().lower()
    person_id = str(latest_envelope.get("voice_identity_attribution_person_id", "") or "").strip() or None
    voice_profile_id = str(
        latest_envelope.get("voice_identity_attribution_voice_profile_id", "") or ""
    ).strip() or None
    confidence_consumed = bool(latest_envelope.get("voice_identity_confidence_consumed", False))
    confidence_value = _coerce_confidence(latest_envelope.get("voice_identity_confidence_value"))
    confidence_band = str(latest_envelope.get("voice_identity_confidence_band", "") or "").strip().lower() or None
    readiness_raw = str(latest_envelope.get("voice_identity_attribution_readiness", "") or "").strip().lower()
    readiness_state = readiness_raw or "unspecified"

    ambiguous_reason_codes = {"low_confidence", "ambiguous_match"}
    unavailable_reason_codes = {
        "voice_identity_not_loaded",
        "voice_identity_linkage_disabled",
        "attribution_service_unavailable",
        "identity_context_service_unavailable",
        "attribution_unavailable",
        "attribution_not_ready",
        "identity_audio_missing",
        "identity_context_missing",
    }

    available = bool(attribution_consumed and person_id)
    ambiguous = bool(
        attribution_state == "low_confidence"
        or confidence_band in {"low", "ambiguous"}
        or attribution_reason in ambiguous_reason_codes
    )
    unavailable = bool(
        (readiness_raw and readiness_raw != "ready")
        or attribution_state == "unavailable"
        or attribution_reason in unavailable_reason_codes
    )

    if available:
        state = "active_person_available"
        reason_code = attribution_reason or "attribution_ready"
    elif ambiguous:
        state = "active_person_ambiguous"
        reason_code = attribution_reason or "low_confidence"
    elif unavailable:
        state = "active_person_unavailable"
        reason_code = attribution_reason or "attribution_unavailable"
    else:
        state = "active_person_unknown"
        reason_code = attribution_reason or "identity_unknown"

    confidence_accepted = bool(
        available
        and confidence_consumed
        and confidence_band not in {"low", "ambiguous", "unknown", "unavailable", "no_match"}
    )

    return {
        "resolution_enabled": True,
        "active_person_state": state,
        "active_person_available": available,
        "resolved_person_id": person_id if available else None,
        "resolved_voice_profile_id": voice_profile_id if available else None,
        "attribution_available": attribution_consumed,
        "identity_context_available": attribution_state in {"known", "unknown", "low_confidence"},
        "confidence_available": confidence_consumed,
        "confidence_accepted": confidence_accepted,
        "confidence": confidence_value,
        "confidence_band": confidence_band,
        "readiness_state": readiness_state,
        "reason_code": reason_code,
        "resolution_posture": "resolved" if available else "fail_closed",
        "fail_closed": not available,
        "authority_source": "voice_identity",
        "consumption_only": True,
    }


def _resolve_active_person_resolution_from_voice_identity_consumption(
    voice_identity_consumption: dict[str, Any] | None,
) -> dict[str, Any]:
    """Project active-person resolution using the voice identity consumption envelope shape."""
    consumption = voice_identity_consumption or {}
    attribution = dict(consumption.get("attribution", {}))
    confidence = dict(consumption.get("confidence", {}))
    diagnostics = dict(dict(consumption.get("diagnostics_boundary", {})).get("diagnostics", {}))
    latest_envelope_like = {
        "voice_identity_attribution_consumed": attribution.get("consumed"),
        "voice_identity_attribution_state": attribution.get("state"),
        "voice_identity_attribution_person_id": attribution.get("person_id"),
        "voice_identity_attribution_voice_profile_id": attribution.get("voice_profile_id"),
        "voice_identity_attribution_reason_code": attribution.get("reason_code"),
        "voice_identity_confidence_consumed": confidence.get("consumed"),
        "voice_identity_confidence_value": confidence.get("value"),
        "voice_identity_confidence_band": confidence.get("band"),
        "voice_identity_attribution_readiness": diagnostics.get("attribution_readiness"),
    }
    return _resolve_active_person_resolution_from_envelope(latest_envelope_like)


def _build_person_aware_productivity_routing(
    *,
    state,
    hass: HomeAssistant | None,
    active_person_resolution: dict[str, Any] | None,
    runtime_person_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build person-aware productivity routing decisions with fail-closed explainability."""
    default_active_person_resolution = {
        "active_person_state": "active_person_unavailable",
        "active_person_available": False,
        "resolved_person_id": None,
        "reason_code": "no_active_person_resolution",
    }
    if active_person_resolution is None and state is not None:
        active_person_resolution = _resolve_active_person_resolution_from_envelope(
            _latest_execution_envelope_ref_from_state(state)
        )
    resolved = dict(active_person_resolution or default_active_person_resolution)
    active_person_state = str(resolved.get("active_person_state", "active_person_unavailable") or "active_person_unavailable")
    active_person_available = bool(resolved.get("active_person_available", False))
    resolved_person_id = str(resolved.get("resolved_person_id", "") or "").strip() or None
    reason_code = str(resolved.get("reason_code", "no_active_person_resolution") or "no_active_person_resolution")

    runtime_person_context = dict(
        runtime_person_context
        or _build_runtime_person_context(
            state,
            active_person_resolution=resolved,
        )
    )
    runtime_person_context_state = str(
        runtime_person_context.get("person_context_state", "person_context_unresolved")
        or "person_context_unresolved"
    )
    runtime_person_context_reason = str(
        runtime_person_context.get("reason_code", "person_profile_not_configured")
        or "person_profile_not_configured"
    )

    inactive_reason = reason_code or active_person_state or "active_person_unavailable"
    if not active_person_available or not resolved_person_id:
        return _attach_refusal_explainability({
            "applicable": True,
            "boundary_path": "governed_person_aware_productivity_routing",
            "consumption_only": True,
            "routing_enabled": False,
            "reason_code": inactive_reason,
            "active_person_state": active_person_state,
            "active_person_available": active_person_available,
            "resolved_person_id": None,
            "runtime_person_context": runtime_person_context,
            "domain_routing": {
                "email": {
                    "enabled": False,
                    "reason_code": inactive_reason,
                    "selected_person_id": None,
                    "selected_source_ref": None,
                    "selection_mode": "disabled",
                },
                "calendar": {
                    "enabled": False,
                    "reason_code": inactive_reason,
                    "selected_person_id": None,
                    "selected_source_ref": None,
                    "selection_mode": "disabled",
                },
                "task": {
                    "enabled": False,
                    "reason_code": inactive_reason,
                    "selected_person_id": None,
                    "selected_source_ref": None,
                    "selection_mode": "disabled",
                },
                "shopping": {
                    "enabled": False,
                    "reason_code": inactive_reason,
                    "selected_person_id": None,
                    "selected_source_ref": None,
                    "selection_mode": "disabled",
                },
            },
            "non_authority_assertions": {
                "creates_source_of_record": False,
                "infers_hidden_intent": False,
                "derives_identity_authority": False,
            },
        },
            refusal_reason_key="reason_code",
            capability_requested="person_aware_productivity_routing",
            capability_available=False,
            capability_configured=False,
            room_authority_source="person_configuration",
            merged_room_authority_source=None,
            person_policy_evaluated=True,
        )

    if runtime_person_context_state == "person_context_unresolved":
        return _attach_refusal_explainability({
            "applicable": True,
            "boundary_path": "governed_person_aware_productivity_routing",
            "consumption_only": True,
            "routing_enabled": False,
            "reason_code": runtime_person_context_reason,
            "active_person_state": active_person_state,
            "active_person_available": active_person_available,
            "resolved_person_id": resolved_person_id,
            "runtime_person_context": runtime_person_context,
            "domain_routing": {
                domain: {
                    "enabled": False,
                    "reason_code": runtime_person_context_reason,
                    "selected_person_id": resolved_person_id,
                    "selected_source_ref": None,
                    "selection_mode": "disabled",
                }
                for domain in ["email", "calendar", "task", "shopping"]
            },
            "non_authority_assertions": {
                "creates_source_of_record": False,
                "infers_hidden_intent": False,
                "derives_identity_authority": False,
            },
        },
            refusal_reason_key="reason_code",
            capability_requested="person_aware_productivity_routing",
            capability_available=False,
            capability_configured=False,
            room_authority_source="person_configuration",
            merged_room_authority_source=None,
            person_policy_evaluated=True,
        )

    if runtime_person_context_state == "person_context_partial":
        return _attach_refusal_explainability({
            "applicable": True,
            "boundary_path": "governed_person_aware_productivity_routing",
            "consumption_only": True,
            "routing_enabled": False,
            "reason_code": runtime_person_context_reason,
            "active_person_state": active_person_state,
            "active_person_available": active_person_available,
            "resolved_person_id": resolved_person_id,
            "runtime_person_context": runtime_person_context,
            "domain_routing": {
                domain: {
                    "enabled": False,
                    "reason_code": runtime_person_context_reason,
                    "selected_person_id": resolved_person_id,
                    "selected_source_ref": None,
                    "selection_mode": "disabled",
                }
                for domain in ["email", "calendar", "task", "shopping"]
            },
            "non_authority_assertions": {
                "creates_source_of_record": False,
                "infers_hidden_intent": False,
                "derives_identity_authority": False,
            },
        },
            refusal_reason_key="reason_code",
            capability_requested="person_aware_productivity_routing",
            capability_available=False,
            capability_configured=True,
            room_authority_source="person_configuration",
            merged_room_authority_source=None,
            person_policy_evaluated=True,
        )

    productivity_context = dict(runtime_person_context.get("productivity", {}))

    def _resolve_calendar_email(domain: str, source_ref: str) -> dict[str, Any]:
        selected_source_ref = source_ref or None
        if not selected_source_ref:
            return {
                "enabled": False,
                "reason_code": "source_missing_or_configuration_incomplete",
                "selected_person_id": resolved_person_id,
                "selected_source_ref": None,
                "selection_mode": "disabled",
            }
        entity_exists = bool(hass and hass.states.get(selected_source_ref) is not None)
        if not entity_exists:
            return {
                "enabled": False,
                "reason_code": "source_unavailable_or_removed",
                "selected_person_id": resolved_person_id,
                "selected_source_ref": selected_source_ref,
                "selection_mode": "disabled",
            }
        return {
            "enabled": True,
            "reason_code": "person_source_selected",
            "selected_person_id": resolved_person_id,
            "selected_source_ref": selected_source_ref,
            "selection_mode": "person_binding",
        }

    email_routing = _resolve_calendar_email(
        "email",
        str(productivity_context.get("email_source_refs", [""])[0] if productivity_context.get("email_source_refs") else "").strip(),
    )
    calendar_routing = _resolve_calendar_email(
        "calendar",
        str(productivity_context.get("calendar_source_refs", [""])[0] if productivity_context.get("calendar_source_refs") else "").strip(),
    )

    shopping_source_ref = str(productivity_context.get("shopping_source_refs", [""])[0] if productivity_context.get("shopping_source_refs") else "").strip()
    if shopping_source_ref:
        shopping_routing = {
            "enabled": True,
            "reason_code": "person_source_selected",
            "selected_person_id": resolved_person_id,
            "selected_source_ref": shopping_source_ref,
            "selection_mode": "person_binding",
        }
    else:
        shopping_routing = {
            "enabled": False,
            "reason_code": "source_missing_or_configuration_incomplete",
            "selected_person_id": resolved_person_id,
            "selected_source_ref": None,
            "selection_mode": "disabled",
        }

    task_source_ref = str(
        productivity_context.get("task_source_refs", [""])[0]
        if productivity_context.get("task_source_refs")
        else ""
    ).strip()
    if task_source_ref:
        task_routing = {
            "enabled": True,
            "reason_code": "person_source_selected",
            "selected_person_id": resolved_person_id,
            "selected_source_ref": task_source_ref,
            "selection_mode": "person_binding",
        }
    else:
        task_routing = {
            "enabled": True,
            "reason_code": "person_scope_selected",
            "selected_person_id": resolved_person_id,
            "selected_source_ref": None,
            "selection_mode": "person_scope_only",
        }

    domain_routing = {
        "email": email_routing,
        "calendar": calendar_routing,
        "task": task_routing,
        "shopping": shopping_routing,
    }
    enabled_any = any(bool(item.get("enabled", False)) for item in domain_routing.values())

    return _attach_refusal_explainability({
        "applicable": True,
        "boundary_path": "governed_person_aware_productivity_routing",
        "consumption_only": True,
        "routing_enabled": enabled_any,
        "reason_code": "person_routing_available" if enabled_any else "person_routing_sources_unavailable",
        "active_person_state": active_person_state,
        "active_person_available": active_person_available,
        "resolved_person_id": resolved_person_id,
        "runtime_person_context": runtime_person_context,
        "domain_routing": domain_routing,
        "non_authority_assertions": {
            "creates_source_of_record": False,
            "infers_hidden_intent": False,
            "derives_identity_authority": False,
        },
    },
        refusal_reason_key="reason_code",
        capability_requested="person_aware_productivity_routing",
        capability_available=enabled_any,
        capability_configured=True,
        room_authority_source="person_configuration",
        merged_room_authority_source=None,
        person_policy_evaluated=True,
    )


def _build_execute_envelope(
    state,
    *,
    hass: HomeAssistant,
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
    runtime_context: dict[str, Any] | None = None,
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

    room_authority_traceability = _build_room_authority_traceability(
        state,
        requested_area_id=requested_area_id,
        assembled_context=assembled_context,
        room_vocabulary_resolution=room_vocabulary_resolution,
        device_entity_vocabulary_resolution=device_entity_vocabulary_resolution,
        asset_vocabulary_resolution=asset_vocabulary_resolution,
    )

    capability_discovery = _build_capability_discovery(
        capabilities=capabilities,
        route_scope=route_scope,
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
        room_vocabulary_resolution=room_vocabulary_resolution,
        device_entity_vocabulary_resolution=device_entity_vocabulary_resolution,
        asset_vocabulary_resolution=asset_vocabulary_resolution,
        room_authority_traceability=room_authority_traceability,
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
    voice_identity_consumption = _build_voice_identity_attribution_confidence_consumption(
        raw_context=runtime_context if runtime_context is not None else call.data.get("context"),
    )
    active_person_resolution = _resolve_active_person_resolution_from_voice_identity_consumption(
        voice_identity_consumption
    )
    runtime_person_context = _build_runtime_person_context(
        state,
        active_person_resolution=active_person_resolution,
    )
    productivity_source_of_record_boundary = _build_productivity_source_of_record_boundary(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
    )
    calendar_email_consumption_boundary = _build_calendar_email_consumption_boundary(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
    )
    task_shopping_consumption_boundary = _build_task_shopping_consumption_boundary(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
    )
    household_status_synthesis_boundary = _build_household_status_synthesis_boundary(
        state=state,
        hass=hass,
    )
    provenance_ownership_consumption_boundary = _build_release_6_provenance_ownership_consumption_boundary(
        state=state,
        hass=hass,
    )
    person_aware_productivity_routing = _build_person_aware_productivity_routing(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
    )
    household_coordination_boundary = _build_household_coordination_boundary(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
        person_aware_productivity_routing=person_aware_productivity_routing,
        household_status_synthesis_boundary=household_status_synthesis_boundary,
        provenance_ownership_consumption_boundary=provenance_ownership_consumption_boundary,
        route_scope=route_scope,
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    productivity_coordination_boundary = _build_productivity_coordination_boundary(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
        person_aware_productivity_routing=person_aware_productivity_routing,
        calendar_email_consumption_boundary=calendar_email_consumption_boundary,
        task_shopping_consumption_boundary=task_shopping_consumption_boundary,
        provenance_ownership_consumption_boundary=provenance_ownership_consumption_boundary,
        route_scope=route_scope,
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    provenance_diagnostics_explainability_boundary = _build_release_6_provenance_diagnostics_explainability_boundary(
        state=state,
        hass=hass,
        route_scope=route_scope,
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
        runtime_person_context=runtime_person_context,
        person_aware_productivity_routing=person_aware_productivity_routing,
        productivity_coordination_boundary=productivity_coordination_boundary,
        household_status_synthesis_boundary=household_status_synthesis_boundary,
        household_coordination_boundary=household_coordination_boundary,
        provenance_ownership_consumption_boundary=provenance_ownership_consumption_boundary,
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
        "room_authority_traceability": room_authority_traceability,
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
        "voice_identity_attribution_confidence_consumption": voice_identity_consumption,
        "active_person_resolution": active_person_resolution,
        "runtime_person_context": runtime_person_context,
        "person_aware_productivity_routing": person_aware_productivity_routing,
        "productivity_source_of_record_boundary": productivity_source_of_record_boundary,
        "calendar_email_consumption_boundary": calendar_email_consumption_boundary,
        "task_shopping_consumption_boundary": task_shopping_consumption_boundary,
        "productivity_coordination_boundary": productivity_coordination_boundary,
        "household_coordination_boundary": household_coordination_boundary,
        "provenance_diagnostics_explainability_boundary": provenance_diagnostics_explainability_boundary,
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
    voice_identity_consumption = _build_voice_identity_attribution_confidence_consumption(
        raw_context=call.data.get("context"),
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
        "voice_identity_attribution_confidence_consumption": voice_identity_consumption,
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
    room_authority_traceability: dict[str, Any] | None = None,
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
            **(dict(room_authority_traceability or {})),
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
    voice_identity_consumption = dict(
        execution_envelope.get("voice_identity_attribution_confidence_consumption", {})
    )
    voice_identity_attribution = dict(voice_identity_consumption.get("attribution", {}))
    voice_identity_confidence = dict(voice_identity_consumption.get("confidence", {}))
    voice_identity_enrollment_lifecycle = dict(
        voice_identity_consumption.get("enrollment_lifecycle", {})
    )
    voice_identity_enrollment = dict(voice_identity_enrollment_lifecycle.get("enrollment", {}))
    voice_identity_lifecycle = dict(voice_identity_enrollment_lifecycle.get("lifecycle", {}))
    voice_identity_permission_boundary = dict(
        voice_identity_consumption.get("permission_boundary", {})
    )
    voice_identity_permission = dict(voice_identity_permission_boundary.get("permission", {}))
    voice_identity_legacy_boundary = dict(
        voice_identity_consumption.get("legacy_disposition_boundary", {})
    )
    voice_identity_legacy_disposition = dict(
        voice_identity_legacy_boundary.get("legacy_disposition", {})
    )
    voice_identity_diagnostics_boundary = dict(
        voice_identity_consumption.get("diagnostics_boundary", {})
    )
    voice_identity_diagnostics = dict(
        voice_identity_diagnostics_boundary.get("diagnostics", {})
    )
    voice_identity_explainability_boundary = dict(
        voice_identity_consumption.get("explainability_boundary", {})
    )
    voice_identity_explainability = dict(
        voice_identity_explainability_boundary.get("explainability", {})
    )
    identity_authorization_policy = dict(
        execution_envelope.get("identity_authorization_policy", {})
    )
    person_aware_productivity_routing = dict(
        execution_envelope.get("person_aware_productivity_routing", {})
    )
    person_aware_domain_routing = dict(
        person_aware_productivity_routing.get("domain_routing", {})
    )
    person_aware_calendar = dict(person_aware_domain_routing.get("calendar", {}))
    person_aware_email = dict(person_aware_domain_routing.get("email", {}))
    person_aware_task = dict(person_aware_domain_routing.get("task", {}))
    person_aware_shopping = dict(person_aware_domain_routing.get("shopping", {}))
    room_authority_traceability = dict(execution_envelope.get("room_authority_traceability", {}))
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
        "room_configuration_loaded": bool(room_authority_traceability.get("room_configuration_loaded", False)),
        "room_authority_source": room_authority_traceability.get("room_authority_source"),
        "room_vocabulary_source": room_authority_traceability.get("room_vocabulary_source"),
        "information_source_origin": room_authority_traceability.get("information_source_origin"),
        "environment_source_origin": room_authority_traceability.get("environment_source_origin"),
        "merged_room_authority_source": room_authority_traceability.get("merged_room_authority_source"),
        "person_authority_source": room_authority_traceability.get("person_authority_source"),
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
        "identity_requirement_class": identity_authorization_policy.get("identity_requirement_class"),
        "identity_policy_outcome": identity_authorization_policy.get("identity_policy_outcome"),
        "identity_policy_reason_code": identity_authorization_policy.get("identity_policy_reason_code"),
        "identity_policy_source": identity_authorization_policy.get("identity_policy_source"),
        "identity_freshness_class": identity_authorization_policy.get("identity_freshness_class"),
        "identity_attribution_age_ms": identity_authorization_policy.get("attribution_age_ms"),
        "identity_policy_identity_state": identity_authorization_policy.get("identity_state"),
        "identity_policy_confidence_band": identity_authorization_policy.get("confidence_band"),
        "identity_policy_classification_source": identity_authorization_policy.get("classification_source"),
        "voice_identity_consumption_boundary_path": voice_identity_consumption.get("boundary_path"),
        "voice_identity_authority_external": bool(
            voice_identity_consumption.get("voice_identity_authority_external", False)
        ),
        "voice_identity_consumption_only": bool(
            voice_identity_consumption.get("consumption_only", False)
        ),
        "voice_identity_derives_attribution_authority": bool(
            voice_identity_consumption.get("derive_attribution_authority", False)
        ),
        "voice_identity_derives_confidence_authority": bool(
            voice_identity_consumption.get("derive_confidence_authority", False)
        ),
        "voice_identity_calculates_attribution": bool(
            voice_identity_consumption.get("calculate_attribution", False)
        ),
        "voice_identity_calculates_confidence": bool(
            voice_identity_consumption.get("calculate_confidence", False)
        ),
        "voice_identity_manages_identity_lifecycle": bool(
            voice_identity_consumption.get("manage_identity_lifecycle", False)
        ),
        "voice_identity_manages_enrollment": bool(
            voice_identity_consumption.get("manage_enrollment", False)
        ),
        "voice_identity_attribution_consumed": bool(
            voice_identity_attribution.get("consumed", False)
        ),
        "voice_identity_attribution_state": voice_identity_attribution.get("state"),
        "voice_identity_attribution_person_id": voice_identity_attribution.get("person_id"),
        "voice_identity_attribution_voice_profile_id": voice_identity_attribution.get("voice_profile_id"),
        "voice_identity_attribution_reason_code": voice_identity_attribution.get("reason_code"),
        "voice_identity_confidence_consumed": bool(
            voice_identity_confidence.get("consumed", False)
        ),
        "voice_identity_confidence_value": voice_identity_confidence.get("value"),
        "voice_identity_confidence_band": voice_identity_confidence.get("band"),
        "voice_identity_confidence_reason_code": voice_identity_confidence.get("reason_code"),
        "voice_identity_enrollment_lifecycle_boundary_path": voice_identity_enrollment_lifecycle.get("boundary_path"),
        "voice_identity_enrollment_lifecycle_consumption_only": bool(
            voice_identity_enrollment_lifecycle.get("consumption_only", False)
        ),
        "voice_identity_enrollment_authority_external": bool(
            voice_identity_enrollment_lifecycle.get("voice_identity_authority_external", False)
        ),
        "voice_identity_enrollment_state_consumed": bool(
            voice_identity_enrollment.get("consumed", False)
        ),
        "voice_identity_enrollment_state": voice_identity_enrollment.get("state"),
        "voice_identity_enrollment_readiness": voice_identity_enrollment.get("readiness"),
        "voice_identity_enrollment_reason_code": voice_identity_enrollment.get("reason_code"),
        "voice_identity_lifecycle_state_consumed": bool(
            voice_identity_lifecycle.get("consumed", False)
        ),
        "voice_identity_enrollment_lifecycle_state": voice_identity_lifecycle.get("enrollment_lifecycle_state"),
        "voice_identity_voice_profile_lifecycle_state": voice_identity_lifecycle.get("voice_profile_lifecycle_state"),
        "voice_identity_identity_lifecycle_state": voice_identity_lifecycle.get("identity_lifecycle_state"),
        "voice_identity_lifecycle_reason_code": voice_identity_lifecycle.get("reason_code"),
        "voice_identity_manages_enrollment_lifecycle": bool(
            voice_identity_enrollment_lifecycle.get("manage_enrollment_lifecycle", False)
        ),
        "voice_identity_manages_voice_profile_lifecycle": bool(
            voice_identity_enrollment_lifecycle.get("manage_voice_profile_lifecycle", False)
        ),
        "voice_identity_creates_voice_profiles": bool(
            voice_identity_enrollment_lifecycle.get("create_voice_profiles", False)
        ),
        "voice_identity_changes_enrollment_state": bool(
            voice_identity_enrollment_lifecycle.get("change_enrollment_state", False)
        ),
        "voice_identity_infers_enrollment_state": bool(
            voice_identity_enrollment_lifecycle.get("infer_enrollment_state", False)
        ),
        "voice_identity_permission_boundary_path": voice_identity_permission_boundary.get("boundary_path"),
        "voice_identity_permission_consumption_only": bool(
            voice_identity_permission_boundary.get("consumption_only", False)
        ),
        "voice_identity_permission_authority_external": bool(
            voice_identity_permission_boundary.get("voice_identity_authority_external", False)
        ),
        "voice_identity_permission_state_consumed": bool(
            voice_identity_permission.get("consumed", False)
        ),
        "voice_identity_permission_state": voice_identity_permission.get("state"),
        "voice_identity_permission_outcome": voice_identity_permission.get("outcome"),
        "voice_identity_consent_state": voice_identity_permission.get("consent_state"),
        "voice_identity_consent_outcome": voice_identity_permission.get("consent_outcome"),
        "voice_identity_permission_eligibility_state": voice_identity_permission.get("eligibility_state"),
        "voice_identity_permission_gating_reason": voice_identity_permission.get("gating_reason"),
        "voice_identity_permission_reason_code": voice_identity_permission.get("reason_code"),
        "voice_identity_permission_lineage_ref": voice_identity_permission.get("lineage_ref"),
        "voice_identity_derives_permission_authority": bool(
            voice_identity_permission_boundary.get("derive_permission_authority", False)
        ),
        "voice_identity_creates_permission_policy": bool(
            voice_identity_permission_boundary.get("create_permission_policy", False)
        ),
        "voice_identity_defines_eligibility_rules": bool(
            voice_identity_permission_boundary.get("define_eligibility_rules", False)
        ),
        "voice_identity_determines_permission_outcomes": bool(
            voice_identity_permission_boundary.get("determine_permission_outcomes", False)
        ),
        "voice_identity_overrides_permission_policy": bool(
            voice_identity_permission_boundary.get("override_voice_identity_permission_policy", False)
        ),
        "voice_identity_grants_permission": bool(
            voice_identity_permission_boundary.get("grant_permission", False)
        ),
        "voice_identity_revokes_permission": bool(
            voice_identity_permission_boundary.get("revoke_permission", False)
        ),
        "voice_identity_approves_consent": bool(
            voice_identity_permission_boundary.get("approve_consent", False)
        ),
        "voice_identity_infers_consent": bool(
            voice_identity_permission_boundary.get("infer_consent", False)
        ),
        "voice_identity_infers_permission_state": bool(
            voice_identity_permission_boundary.get("infer_permission_state", False)
        ),
        "voice_identity_legacy_disposition_boundary_path": voice_identity_legacy_boundary.get("boundary_path"),
        "voice_identity_legacy_disposition_consumption_only": bool(
            voice_identity_legacy_boundary.get("consumption_only", False)
        ),
        "voice_identity_legacy_disposition_authority_external": bool(
            voice_identity_legacy_boundary.get("voice_identity_authority_external", False)
        ),
        "voice_identity_legacy_disposition_consumed": bool(
            voice_identity_legacy_disposition.get("consumed", False)
        ),
        "voice_identity_legacy_disposition_state": voice_identity_legacy_disposition.get("state"),
        "voice_identity_legacy_disposition_outcome": voice_identity_legacy_disposition.get("outcome"),
        "voice_identity_legacy_reference": voice_identity_legacy_disposition.get("legacy_reference"),
        "voice_identity_legacy_replacement_reference": voice_identity_legacy_disposition.get("replacement_reference"),
        "voice_identity_legacy_disposition_reason_code": voice_identity_legacy_disposition.get("reason_code"),
        "voice_identity_legacy_disposition_lineage_ref": voice_identity_legacy_disposition.get("lineage_ref"),
        "voice_identity_manages_legacy_fingerprint_resolution": bool(
            voice_identity_legacy_boundary.get("manage_legacy_fingerprint_resolution", False)
        ),
        "voice_identity_migrates_legacy_identity_data": bool(
            voice_identity_legacy_boundary.get("migrate_legacy_identity_data", False)
        ),
        "voice_identity_disposes_legacy_identity_data": bool(
            voice_identity_legacy_boundary.get("dispose_legacy_identity_data", False)
        ),
        "voice_identity_determines_legacy_disposition": bool(
            voice_identity_legacy_boundary.get("determine_legacy_disposition", False)
        ),
        "voice_identity_infers_legacy_disposition_state": bool(
            voice_identity_legacy_boundary.get("infer_legacy_disposition_state", False)
        ),
        "voice_identity_claims_voiceprint_ownership": bool(
            voice_identity_legacy_boundary.get("claim_voiceprint_ownership", False)
        ),
        "voice_identity_claims_embedding_ownership": bool(
            voice_identity_legacy_boundary.get("claim_embedding_ownership", False)
        ),
        "voice_identity_establishes_identity_authority": bool(
            voice_identity_legacy_boundary.get("establish_identity_authority", False)
        ),
        "voice_identity_determines_enrollment_state": bool(
            voice_identity_legacy_boundary.get("determine_enrollment_state", False)
        ),
        "voice_identity_diagnostics_boundary_path": voice_identity_diagnostics_boundary.get("boundary_path"),
        "voice_identity_diagnostics_consumption_only": bool(
            voice_identity_diagnostics_boundary.get("consumption_only", False)
        ),
        "voice_identity_diagnostics_authority_external": bool(
            voice_identity_diagnostics_boundary.get("voice_identity_authority_external", False)
        ),
        "voice_identity_diagnostics_consumed": bool(
            voice_identity_diagnostics.get("consumed", False)
        ),
        "voice_identity_diagnostic_available": bool(
            voice_identity_diagnostics.get("diagnostic_available", False)
        ),
        "voice_identity_diagnostic_reason_code": voice_identity_diagnostics.get("diagnostic_reason_code"),
        "voice_identity_health_status": voice_identity_diagnostics.get("health_status"),
        "voice_identity_attribution_readiness": voice_identity_diagnostics.get("attribution_readiness"),
        "voice_identity_compatibility_readiness": voice_identity_diagnostics.get("compatibility_readiness"),
        "voice_identity_repair_available": bool(
            voice_identity_diagnostics.get("repair_available", False)
        ),
        "voice_identity_repair_hint_code": voice_identity_diagnostics.get("repair_hint_code"),
        "voice_identity_suggested_next_action_code": voice_identity_diagnostics.get("suggested_next_action_code"),
        "voice_identity_diagnostics_provenance_source": voice_identity_diagnostics.get("provenance_source"),
        "voice_identity_diagnostics_source_reference": voice_identity_diagnostics.get("source_reference"),
        "voice_identity_diagnostics_lineage_ref": voice_identity_diagnostics.get("lineage_ref"),
        "voice_identity_generates_diagnostics_authority": bool(
            voice_identity_diagnostics_boundary.get("generate_diagnostics_authority", False)
        ),
        "voice_identity_rewrites_diagnostics": bool(
            voice_identity_diagnostics_boundary.get("rewrite_voice_identity_diagnostics", False)
        ),
        "voice_identity_calculates_health_status": bool(
            voice_identity_diagnostics_boundary.get("calculate_health_status", False)
        ),
        "voice_identity_calculates_readiness": bool(
            voice_identity_diagnostics_boundary.get("calculate_readiness", False)
        ),
        "voice_identity_generates_repair_hints": bool(
            voice_identity_diagnostics_boundary.get("generate_repair_hints", False)
        ),
        "voice_identity_explainability_boundary_path": voice_identity_explainability_boundary.get("boundary_path"),
        "voice_identity_explainability_consumption_only": bool(
            voice_identity_explainability_boundary.get("consumption_only", False)
        ),
        "voice_identity_explainability_authority_external": bool(
            voice_identity_explainability_boundary.get("voice_identity_authority_external", False)
        ),
        "voice_identity_explainability_consumed": bool(
            voice_identity_explainability.get("consumed", False)
        ),
        "voice_identity_explainability_consumed_outcome": voice_identity_explainability.get("consumed_outcome"),
        "voice_identity_explainability_authority_source": voice_identity_explainability.get("authority_source"),
        "voice_identity_explainability_provenance_source": voice_identity_explainability.get("provenance_source"),
        "voice_identity_explainability_source_reference": voice_identity_explainability.get("source_reference"),
        "voice_identity_explainability_lineage_ref": voice_identity_explainability.get("lineage_ref"),
        "voice_identity_explainability_attribution_source": voice_identity_explainability.get("attribution_source"),
        "voice_identity_explainability_confidence_source": voice_identity_explainability.get("confidence_source"),
        "voice_identity_explainability_enrollment_source": voice_identity_explainability.get("enrollment_source"),
        "voice_identity_explainability_lifecycle_source": voice_identity_explainability.get("lifecycle_source"),
        "voice_identity_explainability_permission_source": voice_identity_explainability.get("permission_source"),
        "voice_identity_explainability_legacy_disposition_source": voice_identity_explainability.get("legacy_disposition_source"),
        "voice_identity_explainability_unavailable_state": voice_identity_explainability.get("unavailable_state"),
        "voice_identity_explainability_reason_code": voice_identity_explainability.get("reason_code"),
        "person_aware_productivity_routing_enabled": bool(
            person_aware_productivity_routing.get("routing_enabled", False)
        ),
        "person_aware_productivity_routing_reason_code": person_aware_productivity_routing.get("reason_code"),
        "person_aware_productivity_active_person_state": person_aware_productivity_routing.get("active_person_state"),
        "person_aware_productivity_active_person_available": bool(
            person_aware_productivity_routing.get("active_person_available", False)
        ),
        "person_aware_productivity_resolved_person_id": person_aware_productivity_routing.get("resolved_person_id"),
        "person_aware_calendar_routing_enabled": bool(person_aware_calendar.get("enabled", False)),
        "person_aware_calendar_routing_reason_code": person_aware_calendar.get("reason_code"),
        "person_aware_email_routing_enabled": bool(person_aware_email.get("enabled", False)),
        "person_aware_email_routing_reason_code": person_aware_email.get("reason_code"),
        "person_aware_task_routing_enabled": bool(person_aware_task.get("enabled", False)),
        "person_aware_task_routing_reason_code": person_aware_task.get("reason_code"),
        "person_aware_shopping_routing_enabled": bool(person_aware_shopping.get("enabled", False)),
        "person_aware_shopping_routing_reason_code": person_aware_shopping.get("reason_code"),
        "voice_identity_generates_explainability_authority": bool(
            voice_identity_explainability_boundary.get("generate_explainability_authority", False)
        ),
        "voice_identity_replaces_provenance": bool(
            voice_identity_explainability_boundary.get("replace_voice_identity_provenance", False)
        ),
        "voice_identity_creates_explainability_lineage": bool(
            voice_identity_explainability_boundary.get("create_explainability_lineage", False)
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
                "voice_identity_linked": False,
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
    voice_identity_linked = bool(
        options.get(
            CONF_VOICE_IDENTITY_LINKED,
            data.get(CONF_VOICE_IDENTITY_LINKED, False),
        )
    )
    if voice_identity_linked:
        voice_identity_status = await async_get_voice_identity_enrollment_status(hass)
    else:
        voice_identity_status = {
            "voice_enrollment_enabled": False,
            "voice_enrollment_reason_code": "voice_identity_linkage_disabled",
            "voice_enrollment_status_summary": "Voice enrollment is unavailable because Voice Identity linkage is disabled.",
        }
    voice_identity_ready = bool(voice_identity_status.get("voice_enrollment_enabled", False))
    cap_voice_enrollment = bool(archive_ready and voice_identity_linked and voice_identity_ready)

    if not archive_ready:
        reason_code = "archive_not_configured"
        status_summary = "Voice enrollment requires attached storage and archive export to be enabled in Concierge options."
    elif not voice_identity_linked:
        reason_code = "voice_identity_linkage_disabled"
        status_summary = "Voice enrollment is unavailable because Voice Identity linkage is disabled."
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
            "voice_identity_linked": voice_identity_linked,
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


async def _async_update_person_context_repairs(
    hass: HomeAssistant,
    *,
    execution_envelope: dict[str, Any],
) -> None:
    """Publish or clear person-context fail-closed repair hints from execution outcomes."""
    routing = dict(execution_envelope.get("person_aware_productivity_routing", {}))
    runtime_person_context = dict(execution_envelope.get("runtime_person_context", {}))
    active_person_resolution = dict(execution_envelope.get("active_person_resolution", {}))

    routing_enabled = bool(routing.get("routing_enabled", False))
    reason_code = str(
        routing.get("reason_code")
        or runtime_person_context.get("reason_code")
        or active_person_resolution.get("reason_code")
        or "unknown"
    ).strip().lower() or "unknown"

    if routing_enabled:
        await async_clear_person_context_issue(hass)
        return

    await async_create_or_update_person_context_issue(
        hass,
        person_context_state=str(
            runtime_person_context.get("person_context_state", "person_context_unresolved")
            or "person_context_unresolved"
        ).strip().lower(),
        reason_code=reason_code,
        active_person_state=str(
            active_person_resolution.get("active_person_state", "active_person_unavailable")
            or "active_person_unavailable"
        ).strip().lower(),
        resolved_person_id=str(
            active_person_resolution.get("resolved_person_id")
            or runtime_person_context.get("resolved_person_id")
            or ""
        ).strip() or None,
    )


async def _async_handle_execute(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    """Execute an orchestration target using deterministic hierarchy."""
    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    capabilities = await _async_resolve_integration_capabilities(hass)
    voice_identity_linked = bool(
        capabilities.get("input_snapshot", {}).get("voice_identity_linked", False)
    )

    area_id = call.data.get("area_id")
    composite_id = call.data.get("composite_id")
    raw_context = call.data.get("context")
    conversation_ingress = _build_conversation_agent_ingress_adapter(
        hass,
        call_data=call.data,
        raw_context=raw_context,
        requested_area_id=area_id,
    )
    if area_id is None:
        area_id = conversation_ingress["foundation_room_resolution"].get("resolved_area_id")

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
    usual_lighting_command_kind = _classify_usual_lighting_command(alias_resolved_target)
    room_audio_command_kind = _classify_room_audio_playback_start_command(alias_resolved_target)
    room_media_continuation_request = _classify_room_media_continuation_request(alias_resolved_target)
    room_media_follow_me_request = _classify_room_media_follow_me_request(alias_resolved_target)
    room_media_request = _classify_room_media_playback_request(alias_resolved_target)
    monitoring_follow_up_request = _classify_monitoring_follow_up_request(alias_resolved_target)
    identity_self_query_request = (
        _classify_identity_self_query_request(call.data.get("target"))
        or _classify_identity_self_query_request(alias_resolved_target)
        or _classify_identity_self_query_request(resolved_target)
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
        elif usual_lighting_command_kind is not None and composite_id is None and area_id is not None:
            room_membership = _resolve_usual_lighting_membership(state.rooms.get(area_id), usual_lighting_command_kind)
            domain = "light"
            service = "turn_on"
            data = {
                "entity_id": room_membership,
                "brightness_pct": _USUAL_LIGHTING_DEFAULT_BRIGHTNESS_PCT,
            }
        elif room_media_request is None and room_media_follow_me_request is None and room_audio_command_kind == "music_start" and (area_id is not None or composite_id is not None):
            domain = "media_player"
            service = "volume_set"
            data = {}
        elif (room_media_request is not None or room_media_follow_me_request is not None) and (area_id is not None or composite_id is not None):
            domain = "music_assistant"
            service = "play_media"
            data = {}
        elif monitoring_follow_up_request is not None and (area_id is not None or composite_id is not None):
            domain = "homeassistant"
            service = "turn_on"
            data = {}
        else:
            domain = "homeassistant"
            service = "turn_on"
            data = {"entity_id": resolved_target}

        runtime_context: dict[str, Any]
        if isinstance(raw_context, dict):
            runtime_context = dict(raw_context)
        else:
            runtime_context = {}

        correlation = dict(conversation_ingress.get("correlation", {}))
        for key in ("conversation_id", "device_id", "satellite_id", "agent_id", "language", "text", "pipeline_id"):
            if runtime_context.get(key) is None and correlation.get(key) is not None:
                runtime_context[key] = correlation.get(key)
        if runtime_context.get("turn_index") is None and correlation.get("turn_index") is not None:
            runtime_context["turn_index"] = correlation.get("turn_index")

        context_room_id = assembled_context.get("context_area_id")
        if runtime_context.get("room_id") is None and isinstance(context_room_id, str) and context_room_id:
            runtime_context["room_id"] = context_room_id

        runtime_context["conversation_agent_ingress"] = {
            "ingress_mode": conversation_ingress.get("ingress_mode"),
            "identity_authority": conversation_ingress.get("identity_authority"),
            "room_resolution_source": conversation_ingress.get("foundation_room_resolution", {}).get("resolution_source"),
            "resolved_room_id": context_room_id,
            "correlation": {
                "conversation_id": correlation.get("conversation_id"),
                "device_id": correlation.get("device_id"),
                "satellite_id": correlation.get("satellite_id"),
                "agent_id": correlation.get("agent_id"),
                "language": correlation.get("language"),
                "text": correlation.get("text"),
            },
        }

        should_invoke_voice_identity = _context_requires_voice_identity_runtime_invocation(runtime_context)
        if bool(conversation_ingress.get("has_conversation_input", False)):
            should_invoke_voice_identity = True

        if should_invoke_voice_identity:
            runtime_context = await _async_consume_voice_identity_runtime_context(
                hass,
                raw_context=runtime_context,
                voice_identity_linked=voice_identity_linked,
            )
        else:
            if not isinstance(runtime_context.get("identity_context"), dict):
                fallback_reason_code = str(
                    conversation_ingress.get("fallback_reason_code")
                    or "identity_audio_missing"
                ).strip().lower() or "identity_audio_missing"
                fallback_identity = _unavailable_identity_context(fallback_reason_code)
                runtime_context["voice_identity_identity_context"] = fallback_identity
                runtime_context["identity_context"] = fallback_identity

        execution_envelope = _build_execute_envelope(
            state,
            hass=hass,
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
            runtime_context=runtime_context,
        )

        identity_policy = _evaluate_runtime_identity_authorization_policy(
            call=call,
            requested_target=str(call.data.get("target", "") or ""),
            resolved_target=resolved_target,
            runtime_context=runtime_context,
        )
        execution_envelope["identity_requirement_class"] = identity_policy["identity_requirement_class"]
        execution_envelope["identity_policy_outcome"] = identity_policy["identity_policy_outcome"]
        execution_envelope["identity_policy_reason_code"] = identity_policy["identity_policy_reason_code"]
        execution_envelope["identity_policy_source"] = identity_policy["identity_policy_source"]
        execution_envelope["identity_freshness_class"] = identity_policy["identity_freshness_class"]
        execution_envelope["attribution_age_ms"] = identity_policy["attribution_age_ms"]
        execution_envelope["identity_state"] = identity_policy["identity_state"]
        execution_envelope["confidence_band"] = identity_policy["confidence_band"]
        execution_envelope["identity_authorization_policy"] = {
            "identity_requirement_class": identity_policy["identity_requirement_class"],
            "identity_policy_outcome": identity_policy["identity_policy_outcome"],
            "identity_policy_reason_code": identity_policy["identity_policy_reason_code"],
            "identity_policy_source": identity_policy["identity_policy_source"],
            "identity_freshness_class": identity_policy["identity_freshness_class"],
            "attribution_age_ms": identity_policy["attribution_age_ms"],
            "identity_state": identity_policy["identity_state"],
            "confidence_band": identity_policy["confidence_band"],
            "classification_source": identity_policy["classification_source"],
        }

        if not bool(identity_policy.get("allows_execution", False)):
            response: dict[str, Any] = {
                "executed": False,
                "resolved_target": resolved_target,
                "execution_envelope": execution_envelope,
                "identity_authorization_policy": dict(
                    execution_envelope.get("identity_authorization_policy", {})
                ),
                "response_message": identity_policy.get("response_message") or None,
                "activity_external_refs": [
                    _build_context_assembly_ref(assembled_context),
                    _build_routing_decision_ref(execution_envelope),
                    _build_execution_envelope_ref(execution_envelope),
                    _build_preservation_alignment_ref(execution_envelope),
                    {
                        "ref_type": "identity_authorization_policy",
                        "identity_requirement_class": identity_policy["identity_requirement_class"],
                        "identity_policy_outcome": identity_policy["identity_policy_outcome"],
                        "identity_policy_reason_code": identity_policy["identity_policy_reason_code"],
                        "identity_policy_source": identity_policy["identity_policy_source"],
                        "identity_freshness_class": identity_policy["identity_freshness_class"],
                        "attribution_age_ms": identity_policy["attribution_age_ms"],
                        "identity_state": identity_policy["identity_state"],
                        "confidence_band": identity_policy["confidence_band"],
                        "classification_source": identity_policy["classification_source"],
                    },
                ],
            }
            outcome_metadata = _build_execute_outcome_metadata(
                response,
                runtime_context=runtime_context,
            )
            response.update(outcome_metadata)
            response["activity_external_refs"].append(
                {
                    "ref_type": "execution_outcome_classification",
                    "execution_outcome_category": outcome_metadata["execution_outcome_category"],
                    "silence_as_success": outcome_metadata["silence_as_success"],
                    "response_required": outcome_metadata["response_required"],
                    "response_generated": outcome_metadata["response_generated"],
                    "refusal_reason": outcome_metadata["refusal_reason"],
                    "refusal_category": outcome_metadata["refusal_category"],
                    "room_authority_source": outcome_metadata["room_authority_source"],
                    "person_policy_evaluated": True,
                    "merged_room_authority_source": outcome_metadata["merged_room_authority_source"],
                }
            )
            return response

        await _async_update_person_context_repairs(
            hass,
            execution_envelope=execution_envelope,
        )

        lighting_result: dict[str, Any] | None = None
        room_audio_result: dict[str, Any] | None = None
        room_media_result: dict[str, Any] | None = None
        monitoring_result: dict[str, Any] | None = None
        identity_self_query_result: dict[str, Any] | None = None
        if identity_self_query_request is not None:
            identity_self_query_result = _build_identity_self_query_response(
                state=state,
                execution_envelope=execution_envelope,
            )
        if usual_lighting_command_kind is not None and composite_id is None and area_id is not None:
            room = state.rooms.get(area_id)
            lighting_result = await _async_execute_learned_usual_lighting(
                hass,
                storage=storage,
                state=state,
                room=room,
                area_id=area_id,
                command_kind=usual_lighting_command_kind,
            )
        elif room_media_request is None and room_audio_command_kind == "music_start" and (area_id is not None or composite_id is not None):
            room_audio_result = await _async_execute_room_audio_playback_start(
                hass,
                storage=storage,
                state=state,
                area_id=area_id,
                composite_id=composite_id,
                channel="music",
            )

        if (room_media_continuation_request is not None or room_media_follow_me_request is not None) and (area_id is not None or composite_id is not None):
            media_provider = _resolve_media_provider_configuration(hass)
            output_targets = _resolve_media_request_output_targets(
                hass,
                state=state,
                area_id=area_id,
                composite_id=composite_id,
            )
            room_media_context = _resolve_room_media_context(
                state,
                area_id=area_id,
                composite_id=composite_id,
            )
            follow_me_decision = _resolve_follow_me_media_decision(
                runtime_context=runtime_context,
                request_explicit=room_media_follow_me_request is not None,
                area_id=area_id,
                composite_id=composite_id,
                room_media_context=room_media_context,
            )

            if bool(follow_me_decision.get("follow_me_allowed", False)):
                handoff_source_room = str(follow_me_decision.get("source_room") or "").strip() or None
                if handoff_source_room is not None:
                    room_media_context = _resolve_room_media_context(
                        state,
                        area_id=handoff_source_room,
                        composite_id=None,
                    )

            continuation_plan = _resolve_room_media_continuation_plan(
                room_media_context=room_media_context,
                runtime_context=runtime_context,
            )

            room_media_result = {
                "handled": True,
                "executed": False,
                "resolved_target": "room_media:continue_resume_request",
                "provider_selected": media_provider.get("provider_selected"),
                "provider_reason": media_provider.get("provider_reason"),
                "provider_available": bool(media_provider.get("provider_available", False)),
                "configured_provider": media_provider.get("configured_provider"),
                "provider_service_available": bool(media_provider.get("provider_service_available", False)),
                "provider_integration_available": bool(media_provider.get("provider_integration_available", False)),
                "room_authority_source": output_targets.get("room_authority_source", "room_configuration"),
                "person_authority_source": "person_configuration_runtime_context",
                "asset_authority_source": "asset_intelligence_unused_in_this_resolution",
                "experience_continuity_authority_source": "experience_continuity_room_media_context",
                "media_provider_authority_source": "music_assistant_provider_resolution",
                "playback_scope": output_targets.get("playback_scope", "room"),
                "memory_scope": output_targets.get("memory_scope", "room"),
                "merged_room_participation": bool(output_targets.get("merged_room_participation", False)),
                "participating_rooms": output_targets.get("participating_rooms", []),
                "group_targeted_speakers": output_targets.get("group_targeted_speakers", []),
                "room_results": output_targets.get("room_results", []),
                "source_room_id": room_media_context.get("source_room_id"),
                "source_room_selection_reason": room_media_context.get("source_room_selection_reason"),
                "room_media_context": room_media_context.get("room_media_context"),
                "follow_me_enabled": bool(follow_me_decision.get("follow_me_enabled", False)),
                "follow_me_candidate": bool(follow_me_decision.get("follow_me_candidate", False)),
                "follow_me_allowed": bool(follow_me_decision.get("follow_me_allowed", False)),
                "follow_me_decision": follow_me_decision.get("follow_me_decision"),
                "follow_me_reason": follow_me_decision.get("follow_me_reason"),
                "identity_authority_source": follow_me_decision.get("identity_authority_source"),
                "room_transition_source": follow_me_decision.get("room_transition_source"),
                "cooldown_blocked": bool(follow_me_decision.get("cooldown_blocked", False)),
                "manual_stop_blocked": bool(follow_me_decision.get("manual_stop_blocked", False)),
                "destination_room": follow_me_decision.get("destination_room"),
                "source_room": follow_me_decision.get("source_room"),
                "continuation_strategy": continuation_plan.get("continuation_strategy"),
                "continuation_strategy_reason": continuation_plan.get("strategy_reason"),
                "continuation_query": continuation_plan.get("continuation_query"),
                "music_assistant_request": continuation_plan.get("music_assistant_request"),
                "preference_resolution": continuation_plan.get("preference_resolution"),
                "personalization_applied": bool(continuation_plan.get("personalization_applied", False)),
                "personalization_reason": continuation_plan.get("personalization_reason"),
                "cooldown_decision": continuation_plan.get("cooldown_decision", {}),
                "failure_reason": None,
                "fallback_used": False,
                "fallback_path": "none",
                "fallback_source": None,
                "decision_reason": continuation_plan.get("strategy_reason", "room_media_continuation"),
                "follow_me_excluded": not bool(follow_me_decision.get("follow_me_candidate", False)),
                "persistent_merged_room_media_memory_created": False,
            }

            if (
                bool(follow_me_decision.get("follow_me_candidate", False))
                and not bool(follow_me_decision.get("follow_me_allowed", False))
            ):
                room_media_result["failure_reason"] = follow_me_decision.get("follow_me_reason")
                room_media_result["fallback_used"] = True
                room_media_result["fallback_path"] = "governed_follow_me_refusal"
                room_media_result["fallback_source"] = "experience_continuity_follow_me_policy"
                room_media_result["decision_reason"] = follow_me_decision.get("follow_me_reason")
            elif output_targets.get("failure_reason") is not None:
                room_media_result["failure_reason"] = output_targets.get("failure_reason")
                room_media_result["fallback_used"] = True
                room_media_result["fallback_path"] = "configured_room_authority_failure"
                room_media_result["fallback_source"] = _ROOM_AUDIO_FALLBACK_POLICY_SOURCE
                room_media_result["decision_reason"] = "configured_room_authority_validation"
            elif media_provider.get("configured_provider") != _PROVIDER_MUSIC_ASSISTANT:
                room_media_result["failure_reason"] = "media_provider_disabled"
                room_media_result["fallback_used"] = True
                room_media_result["fallback_path"] = "governed_provider_refusal"
                room_media_result["fallback_source"] = "experience_continuity_media_provider_precedence_policy"
                room_media_result["decision_reason"] = "music_assistant_not_enabled"
            elif not bool(media_provider.get("provider_available", False)):
                room_media_result["failure_reason"] = "music_assistant_unavailable"
                room_media_result["fallback_used"] = True
                room_media_result["fallback_path"] = "governed_provider_refusal"
                room_media_result["fallback_source"] = "experience_continuity_media_provider_precedence_policy"
                room_media_result["decision_reason"] = "preferred_provider_unavailable"
            elif continuation_plan.get("continuation_strategy") == "governed_refusal":
                room_media_result["failure_reason"] = continuation_plan.get("strategy_reason")
                room_media_result["fallback_used"] = True
                room_media_result["fallback_path"] = "governed_refusal"
                room_media_result["fallback_source"] = _ROOM_MEDIA_MANUAL_STOP_POLICY_SOURCE if continuation_plan.get("strategy_reason") == "manual_stop_cooldown_active" else _ROOM_MEDIA_CONTINUATION_POLICY_NAME
                room_media_result["decision_reason"] = continuation_plan.get("strategy_reason")
            else:
                if room_audio_result is None:
                    room_audio_result = await _async_execute_room_audio_playback_start(
                        hass,
                        storage=storage,
                        state=state,
                        area_id=area_id,
                        composite_id=composite_id,
                        channel="music",
                    )
                if room_audio_result is not None and not bool(room_audio_result.get("executed", False)):
                    room_media_result["failure_reason"] = room_audio_result.get("failure_reason")
                    room_media_result["fallback_used"] = True
                    room_media_result["fallback_path"] = "configured_room_authority_failure"
                    room_media_result["fallback_source"] = _ROOM_AUDIO_FALLBACK_POLICY_SOURCE
                    room_media_result["decision_reason"] = "configured_room_authority_validation"
                else:
                    music_assistant_data = dict(continuation_plan.get("music_assistant_request") or {})
                    if not music_assistant_data:
                        room_media_result["failure_reason"] = "no_usable_room_media_context"
                        room_media_result["fallback_used"] = True
                        room_media_result["fallback_path"] = "governed_refusal"
                        room_media_result["fallback_source"] = _ROOM_MEDIA_CONTINUATION_POLICY_NAME
                        room_media_result["decision_reason"] = "room_media_context_missing"
                    else:
                        await hass.services.async_call(
                            "music_assistant",
                            "play_media",
                            music_assistant_data,
                            blocking=True,
                            target={"entity_id": room_media_result["group_targeted_speakers"]},
                        )
                        source_room_id = str(room_media_result.get("source_room_id") or area_id or "").strip()
                        captured_state = None
                        if source_room_id:
                            captured_state = await _async_capture_room_media_context(
                                hass,
                                storage=storage,
                                state=state,
                                area_id=area_id or source_room_id,
                                source_room_id=source_room_id,
                                provider_source="music_assistant",
                                media_type=continuation_plan.get("media_type"),
                                media_query=str(continuation_plan.get("continuation_query") or "").strip() or None,
                                music_assistant_request=music_assistant_data,
                                room_media_context=room_media_context,
                            )
                        room_media_result["executed"] = True
                        room_media_result["music_assistant_request"] = {
                            "target": {"entity_id": room_media_result["group_targeted_speakers"]},
                            "data": music_assistant_data,
                        }
                        room_media_result["captured_room_media_context"] = captured_state
                        room_media_result["activity_external_refs"] = [
                            {
                                "ref_type": "room_media_continuation_resolution",
                                "provider_selected": room_media_result["provider_selected"],
                                "provider_reason": room_media_result["provider_reason"],
                                "provider_available": room_media_result["provider_available"],
                                "room_authority_source": output_targets.get("room_authority_source", "room_configuration"),
                                "source_room_id": room_media_result.get("source_room_id"),
                                "source_room_selection_reason": room_media_result.get("source_room_selection_reason"),
                                "continuation_strategy": room_media_result.get("continuation_strategy"),
                                "continuation_query": room_media_result.get("continuation_query"),
                                "merged_room_participation": room_media_result["merged_room_participation"],
                                "group_targeted_speakers": room_media_result["group_targeted_speakers"],
                                "follow_me_excluded": not bool(room_media_result.get("follow_me_candidate", False)),
                                "follow_me_enabled": bool(room_media_result.get("follow_me_enabled", False)),
                                "follow_me_candidate": bool(room_media_result.get("follow_me_candidate", False)),
                                "follow_me_allowed": bool(room_media_result.get("follow_me_allowed", False)),
                                "follow_me_decision": room_media_result.get("follow_me_decision"),
                                "follow_me_reason": room_media_result.get("follow_me_reason"),
                                "identity_authority_source": room_media_result.get("identity_authority_source"),
                                "room_transition_source": room_media_result.get("room_transition_source"),
                                "cooldown_blocked": bool(room_media_result.get("cooldown_blocked", False)),
                                "manual_stop_blocked": bool(room_media_result.get("manual_stop_blocked", False)),
                                "destination_room": room_media_result.get("destination_room"),
                                "source_room": room_media_result.get("source_room"),
                                "personalization_applied": room_media_result.get("personalization_applied", False),
                                "cooldown_decision": room_media_result.get("cooldown_decision", {}),
                            },
                            {
                                "ref_type": "room_media_context_capture",
                                "state_id": _room_media_state_id(area_id=room_media_result.get("source_room_id") or area_id or ""),
                                "captured": captured_state is not None,
                                "source_room_id": room_media_result.get("source_room_id"),
                                "policy_name": _ROOM_MEDIA_CONTEXT_POLICY_NAME,
                            },
                        ]

            room_media_result = _attach_refusal_explainability(
                room_media_result,
                refusal_reason_key="failure_reason",
                capability_requested=(
                    "room_media_follow_me"
                    if room_media_follow_me_request is not None
                    else "room_media_continuation"
                ),
                capability_available=bool(room_media_result.get("executed", False)),
                capability_configured=bool(room_media_result.get("group_targeted_speakers"))
                and room_media_result.get("configured_provider") == _PROVIDER_MUSIC_ASSISTANT,
                room_authority_source=str(
                    room_media_result.get("room_authority_source") or "room_configuration"
                ),
                merged_room_authority_source=(
                    "room_configuration"
                    if room_media_result.get("merged_room_participation")
                    else None
                ),
                person_policy_evaluated=True,
            )

        if room_media_request is not None and (area_id is not None or composite_id is not None):
            media_provider = _resolve_media_provider_configuration(hass)
            output_targets = _resolve_media_request_output_targets(
                hass,
                state=state,
                area_id=area_id,
                composite_id=composite_id,
            )
            media_query = _resolve_media_playback_query(
                media_request=room_media_request,
                runtime_context=runtime_context,
            )

            room_media_result = {
                "handled": True,
                "executed": False,
                "resolved_target": "room_media:playback_request",
                "provider_selected": media_provider.get("provider_selected"),
                "provider_reason": media_provider.get("provider_reason"),
                "provider_available": bool(media_provider.get("provider_available", False)),
                "configured_provider": media_provider.get("configured_provider"),
                "provider_service_available": bool(media_provider.get("provider_service_available", False)),
                "provider_integration_available": bool(media_provider.get("provider_integration_available", False)),
                "room_authority_source": output_targets.get("room_authority_source", "room_configuration"),
                "person_authority_source": "person_configuration_runtime_context",
                "asset_authority_source": "asset_intelligence_unused_in_this_resolution",
                "experience_continuity_authority_source": "experience_continuity_preference_resolution",
                "media_provider_authority_source": "music_assistant_provider_resolution",
                "playback_scope": output_targets.get("playback_scope", "room"),
                "memory_scope": output_targets.get("memory_scope", "room"),
                "merged_room_participation": bool(output_targets.get("merged_room_participation", False)),
                "participating_rooms": output_targets.get("participating_rooms", []),
                "group_targeted_speakers": output_targets.get("group_targeted_speakers", []),
                "room_results": output_targets.get("room_results", []),
                "request_kind": media_query.get("request_kind"),
                "media_query": media_query.get("media_query"),
                "preference_resolution": media_query.get("preference_outcome"),
                "preference_inputs_used": media_query.get("preference_inputs", {}),
                "failure_reason": None,
                "fallback_used": False,
                "fallback_path": "none",
                "fallback_source": None,
                "decision_reason": "music_assistant_preferred_provider",
                "follow_me_excluded": True,
                "persistent_merged_room_media_memory_created": False,
            }

            if output_targets.get("failure_reason") is not None:
                room_media_result["failure_reason"] = output_targets.get("failure_reason")
                room_media_result["fallback_used"] = True
                room_media_result["fallback_path"] = "configured_room_authority_failure"
                room_media_result["fallback_source"] = _ROOM_AUDIO_FALLBACK_POLICY_SOURCE
                room_media_result["decision_reason"] = "configured_room_authority_validation"
            elif media_provider.get("configured_provider") != _PROVIDER_MUSIC_ASSISTANT:
                room_media_result["failure_reason"] = "media_provider_disabled"
                room_media_result["fallback_used"] = True
                room_media_result["fallback_path"] = "governed_provider_refusal"
                room_media_result["fallback_source"] = "experience_continuity_media_provider_precedence_policy"
                room_media_result["decision_reason"] = "music_assistant_not_enabled"
            elif not bool(media_provider.get("provider_available", False)):
                room_media_result["failure_reason"] = "music_assistant_unavailable"
                room_media_result["fallback_used"] = True
                room_media_result["fallback_path"] = "governed_provider_refusal"
                room_media_result["fallback_source"] = "experience_continuity_media_provider_precedence_policy"
                room_media_result["decision_reason"] = "preferred_provider_unavailable"
            else:
                if room_audio_result is None:
                    room_audio_result = await _async_execute_room_audio_playback_start(
                        hass,
                        storage=storage,
                        state=state,
                        area_id=area_id,
                        composite_id=composite_id,
                        channel="music",
                    )
                if room_audio_result is not None and not bool(room_audio_result.get("executed", False)):
                    room_media_result["failure_reason"] = room_audio_result.get("failure_reason")
                    room_media_result["fallback_used"] = True
                    room_media_result["fallback_path"] = "configured_room_authority_failure"
                    room_media_result["fallback_source"] = _ROOM_AUDIO_FALLBACK_POLICY_SOURCE
                    room_media_result["decision_reason"] = "configured_room_authority_validation"
                else:
                    music_assistant_data: dict[str, Any] = {
                        "media_id": room_media_result["media_query"],
                        "enqueue": "replace",
                    }
                    request_kind = str(room_media_result["request_kind"] or "")
                    if request_kind == "genre":
                        music_assistant_data["radio_mode"] = True
                    elif request_kind == "artist":
                        music_assistant_data["media_type"] = "artist"
                    elif request_kind == "album":
                        music_assistant_data["media_type"] = "album"
                    elif request_kind == "playlist":
                        music_assistant_data["media_type"] = "playlist"

                    await hass.services.async_call(
                        "music_assistant",
                        "play_media",
                        music_assistant_data,
                        blocking=True,
                        target={"entity_id": room_media_result["group_targeted_speakers"]},
                    )
                    source_room_id = str(area_id or room_media_result.get("participating_rooms", [""])[0] or "").strip() or None
                    if room_media_result.get("merged_room_participation") and room_media_result.get("participating_rooms"):
                        source_room_id = str(
                            (room_media_result.get("source_room_id") or room_media_result["participating_rooms"][0])
                        ).strip() or source_room_id
                    captured_state = None
                    if source_room_id:
                        captured_state = await _async_capture_room_media_context(
                            hass,
                            storage=storage,
                            state=state,
                            area_id=area_id or source_room_id,
                            source_room_id=source_room_id,
                            provider_source="music_assistant",
                            media_type=room_media_result.get("request_kind"),
                            media_query=str(room_media_result.get("media_query") or "").strip() or None,
                            music_assistant_request=music_assistant_data,
                            room_media_context=_resolve_room_media_context(
                                state,
                                area_id=area_id,
                                composite_id=composite_id,
                            ),
                        )
                    room_media_result["executed"] = True
                    room_media_result["music_assistant_request"] = {
                        "target": {"entity_id": room_media_result["group_targeted_speakers"]},
                        "data": music_assistant_data,
                    }
                    room_media_result["captured_room_media_context"] = captured_state
                    room_media_result["activity_external_refs"] = [
                        {
                            "ref_type": "media_provider_resolution",
                            "provider_selected": room_media_result["provider_selected"],
                            "provider_reason": room_media_result["provider_reason"],
                            "provider_available": room_media_result["provider_available"],
                            "room_authority_source": output_targets.get("room_authority_source", "room_configuration"),
                            "request_kind": room_media_result["request_kind"],
                            "merged_room_participation": room_media_result["merged_room_participation"],
                            "group_targeted_speakers": room_media_result["group_targeted_speakers"],
                            "follow_me_excluded": True,
                        }
                        ,
                        {
                            "ref_type": "room_media_context_capture",
                            "state_id": _room_media_state_id(area_id=source_room_id),
                            "captured": captured_state is not None,
                            "source_room_id": source_room_id,
                            "policy_name": _ROOM_MEDIA_CONTEXT_POLICY_NAME,
                        }
                    ]

            room_media_result = _attach_refusal_explainability(
                room_media_result,
                refusal_reason_key="failure_reason",
                capability_requested="room_media_playback",
                capability_available=bool(room_media_result.get("executed", False)),
                capability_configured=bool(room_media_result.get("group_targeted_speakers"))
                and room_media_result.get("configured_provider") == _PROVIDER_MUSIC_ASSISTANT,
                room_authority_source=str(
                    room_media_result.get("room_authority_source") or "room_configuration"
                ),
                merged_room_authority_source=(
                    "room_configuration"
                    if room_media_result.get("merged_room_participation")
                    else None
                ),
                person_policy_evaluated=True,
            )

        if monitoring_follow_up_request is not None and (area_id is not None or composite_id is not None):
            monitoring_capability = str(
                monitoring_follow_up_request.get("monitoring_capability") or ""
            ).strip()
            monitoring_result = _build_monitoring_follow_up_resolution(
                hass,
                state=state,
                area_id=area_id,
                composite_id=composite_id,
                monitoring_capability=monitoring_capability,
                room_authority_traceability=dict(execution_envelope.get("room_authority_traceability", {})),
            )
            monitoring_result["activity_external_refs"] = [
                {
                    "ref_type": "monitoring_follow_up_resolution",
                    "monitoring_capability": monitoring_result.get("monitoring_capability"),
                    "configured_capability_mapping": monitoring_result.get("configured_capability_mapping", {}),
                    "resolved_monitoring_device": monitoring_result.get("resolved_monitoring_device"),
                    "resolution_strategy": monitoring_result.get("resolution_strategy"),
                    "resolution_priority": monitoring_result.get("resolution_priority", []),
                    "refusal_reason": monitoring_result.get("refusal_reason"),
                    "refusal_category": monitoring_result.get("refusal_category"),
                    "room_authority_source": monitoring_result.get("room_authority_source"),
                    "merged_room_authority_source": monitoring_result.get("merged_room_authority_source"),
                    "capability_requested": monitoring_result.get("capability_requested"),
                    "capability_available": monitoring_result.get("capability_available"),
                    "capability_configured": monitoring_result.get("capability_configured"),
                    "person_policy_evaluated": monitoring_result.get("person_policy_evaluated"),
                    "runtime_discovery_reliance": monitoring_result.get("runtime_discovery_reliance"),
                }
            ]

        if lighting_result is None and room_audio_result is None and room_media_result is None and monitoring_result is None and identity_self_query_result is None:
            await hass.services.async_call(domain, service, data, blocking=True)

        payload = {
            "target": call.data["target"],
            "resolved_target": (
                lighting_result.get("resolved_target", resolved_target)
                if lighting_result
                else (
                    room_audio_result.get("resolved_target", resolved_target)
                    if room_audio_result
                    else resolved_target
                )
            ),
            "area_id": area_id,
            "composite_id": composite_id,
            "context": runtime_context,
            "execution_envelope": execution_envelope,
        }
        hass.bus.async_fire(EVENT_EXECUTION, payload)
        response: dict[str, Any] = {
            "executed": bool(lighting_result.get("executed", True)) if lighting_result else True,
            "resolved_target": (
                lighting_result.get("resolved_target", resolved_target)
                if lighting_result
                else (
                    room_audio_result.get("resolved_target", resolved_target)
                    if room_audio_result
                    else resolved_target
                )
            ),
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
                {
                    "ref_type": "conversation_agent_ingress",
                    "ingress_mode": conversation_ingress.get("ingress_mode"),
                    "identity_authority": conversation_ingress.get("identity_authority"),
                    "conversation_id": runtime_context.get("conversation_id"),
                    "device_id": runtime_context.get("device_id"),
                    "satellite_id": runtime_context.get("satellite_id"),
                    "room_id": assembled_context.get("context_area_id"),
                    "resolution_source": conversation_ingress.get("foundation_room_resolution", {}).get("resolution_source"),
                },
            ],
        }
        response["identity_authorization_policy"] = dict(
            execution_envelope.get("identity_authorization_policy", {})
        )
        response["activity_external_refs"].append(
            {
                "ref_type": "identity_authorization_policy",
                "identity_requirement_class": identity_policy["identity_requirement_class"],
                "identity_policy_outcome": identity_policy["identity_policy_outcome"],
                "identity_policy_reason_code": identity_policy["identity_policy_reason_code"],
                "identity_policy_source": identity_policy["identity_policy_source"],
                "identity_freshness_class": identity_policy["identity_freshness_class"],
                "attribution_age_ms": identity_policy["attribution_age_ms"],
                "identity_state": identity_policy["identity_state"],
                "confidence_band": identity_policy["confidence_band"],
                "classification_source": identity_policy["classification_source"],
            }
        )
        response["conversation_agent_ingress"] = {
            "ingress_mode": conversation_ingress.get("ingress_mode"),
            "identity_authority": conversation_ingress.get("identity_authority"),
            "correlation": {
                "conversation_id": runtime_context.get("conversation_id"),
                "device_id": runtime_context.get("device_id"),
                "satellite_id": runtime_context.get("satellite_id"),
                "agent_id": runtime_context.get("agent_id"),
                "language": runtime_context.get("language"),
                "text": runtime_context.get("text"),
            },
            "foundation_room_resolution": {
                "resolved_area_id": assembled_context.get("context_area_id"),
                "resolution_source": conversation_ingress.get("foundation_room_resolution", {}).get("resolution_source"),
            },
            "speaker_lookup": {
                "identity_status": str(runtime_context.get("identity_context", {}).get("state", "") or "").strip().lower() or "unavailable",
                "confidence_band": runtime_context.get("identity_context", {}).get("confidence_band"),
                "reason_code": runtime_context.get("identity_context", {}).get("reason_code"),
                "resolution_source": runtime_context.get("voice_identity_runtime_attribution", {}).get("resolution_source"),
            },
            "diagnostics": {
                "conversation_id": runtime_context.get("conversation_id"),
                "device_id": runtime_context.get("device_id"),
                "satellite_id": runtime_context.get("satellite_id"),
                "room_id": assembled_context.get("context_area_id"),
                "identity_status": str(runtime_context.get("identity_context", {}).get("state", "") or "").strip().lower() or "unavailable",
                "confidence_band": runtime_context.get("identity_context", {}).get("confidence_band"),
                "reason_code": runtime_context.get("identity_context", {}).get("reason_code"),
                "resolution_source": runtime_context.get("voice_identity_runtime_attribution", {}).get("resolution_source"),
            },
        }
        if lighting_result is not None:
            response["learned_usual_lighting"] = {
                "command_kind": lighting_result.get("command_kind"),
                "room_source": lighting_result.get("room_source"),
                "capability_source": lighting_result.get("capability_source"),
                "membership_source": lighting_result.get("membership_source"),
                "room_membership": lighting_result.get("room_membership", []),
                "targeted_entities": lighting_result.get("targeted_entities", []),
                "validation_results": lighting_result.get("validation_results", []),
                "failure_reason": lighting_result.get("failure_reason"),
                "failure_condition": lighting_result.get("failure_condition"),
                "fallback_used": bool(lighting_result.get("fallback_used", False)),
                "fallback_path": lighting_result.get("fallback_path", "none"),
                "fallback_source": lighting_result.get("fallback_source"),
                "deterministic_default": lighting_result.get("deterministic_default", "none"),
                "decision_reason": lighting_result.get("decision_reason"),
                "learning_decisions": lighting_result.get("learning_decisions", []),
                "entity_outcomes": lighting_result.get("entity_outcomes", []),
            }
            response["activity_external_refs"].extend(
                list(lighting_result.get("activity_external_refs", []))
            )
        if room_audio_result is not None:
            response["executed"] = bool(room_audio_result.get("executed", False))
            response["room_audio_continuity"] = {
                "channel": room_audio_result.get("channel"),
                "playback_scope": room_audio_result.get("playback_scope"),
                "memory_scope": room_audio_result.get("memory_scope", "room"),
                "merged_room_participation": bool(room_audio_result.get("merged_room_participation", False)),
                "participating_rooms": room_audio_result.get("participating_rooms", []),
                "group_targeted_speakers": room_audio_result.get("group_targeted_speakers", []),
                "room_results": room_audio_result.get("room_results", []),
                "learning_decisions": room_audio_result.get("learning_decisions", []),
                "failure_reason": room_audio_result.get("failure_reason"),
                "fallback_used": bool(room_audio_result.get("fallback_used", False)),
                "fallback_path": room_audio_result.get("fallback_path", "none"),
                "fallback_source": room_audio_result.get("fallback_source"),
                "decision_reason": room_audio_result.get("decision_reason"),
            }
            response["activity_external_refs"].extend(
                list(room_audio_result.get("activity_external_refs", []))
            )
        if room_media_result is not None:
            response["executed"] = bool(room_media_result.get("executed", False))
            response["resolved_target"] = room_media_result.get("resolved_target", response["resolved_target"])
            response["media_provider_resolution"] = {
                "provider_selected": room_media_result.get("provider_selected"),
                "provider_reason": room_media_result.get("provider_reason"),
                "provider_available": room_media_result.get("provider_available"),
                "configured_provider": room_media_result.get("configured_provider"),
                "provider_service_available": room_media_result.get("provider_service_available"),
                "provider_integration_available": room_media_result.get("provider_integration_available"),
                "room_authority_source": room_media_result.get("room_authority_source", "room_configuration"),
                "person_authority_source": room_media_result.get("person_authority_source"),
                "asset_authority_source": room_media_result.get("asset_authority_source"),
                "experience_continuity_authority_source": room_media_result.get("experience_continuity_authority_source"),
                "media_provider_authority_source": room_media_result.get("media_provider_authority_source"),
                "request_kind": room_media_result.get("request_kind"),
                "media_query": room_media_result.get("media_query"),
                "playback_scope": room_media_result.get("playback_scope"),
                "memory_scope": room_media_result.get("memory_scope"),
                "merged_room_participation": room_media_result.get("merged_room_participation"),
                "participating_rooms": room_media_result.get("participating_rooms", []),
                "group_targeted_speakers": room_media_result.get("group_targeted_speakers", []),
                "room_results": room_media_result.get("room_results", []),
                "failure_reason": room_media_result.get("failure_reason"),
                "refusal_reason": room_media_result.get("refusal_reason"),
                "refusal_category": room_media_result.get("refusal_category"),
                "fallback_used": bool(room_media_result.get("fallback_used", False)),
                "fallback_path": room_media_result.get("fallback_path", "none"),
                "fallback_source": room_media_result.get("fallback_source"),
                "decision_reason": room_media_result.get("decision_reason"),
                "capability_requested": room_media_result.get("capability_requested"),
                "capability_available": room_media_result.get("capability_available"),
                "capability_configured": room_media_result.get("capability_configured"),
                "person_policy_evaluated": room_media_result.get("person_policy_evaluated"),
                "merged_room_authority_source": room_media_result.get("merged_room_authority_source"),
                "follow_me_excluded": bool(room_media_result.get("follow_me_excluded", True)),
                "follow_me_enabled": bool(room_media_result.get("follow_me_enabled", False)),
                "follow_me_candidate": bool(room_media_result.get("follow_me_candidate", False)),
                "follow_me_allowed": bool(room_media_result.get("follow_me_allowed", False)),
                "follow_me_decision": room_media_result.get("follow_me_decision"),
                "follow_me_reason": room_media_result.get("follow_me_reason"),
                "identity_authority_source": room_media_result.get("identity_authority_source"),
                "room_transition_source": room_media_result.get("room_transition_source"),
                "cooldown_blocked": bool(room_media_result.get("cooldown_blocked", False)),
                "manual_stop_blocked": bool(room_media_result.get("manual_stop_blocked", False)),
                "destination_room": room_media_result.get("destination_room"),
                "source_room": room_media_result.get("source_room"),
                "persistent_merged_room_media_memory_created": False,
            }
            if room_media_result.get("continuation_strategy") is not None:
                response["room_media_continuity"] = {
                    "continuation_strategy": room_media_result.get("continuation_strategy"),
                    "continuation_strategy_reason": room_media_result.get("continuation_strategy_reason"),
                    "source_room_id": room_media_result.get("source_room_id"),
                    "source_room_selection_reason": room_media_result.get("source_room_selection_reason"),
                    "room_media_context": room_media_result.get("room_media_context"),
                    "continuation_query": room_media_result.get("continuation_query"),
                    "music_assistant_request": room_media_result.get("music_assistant_request"),
                    "personalization_applied": bool(room_media_result.get("personalization_applied", False)),
                    "personalization_reason": room_media_result.get("personalization_reason"),
                    "cooldown_decision": room_media_result.get("cooldown_decision", {}),
                    "fallback_used": bool(room_media_result.get("fallback_used", False)),
                    "fallback_path": room_media_result.get("fallback_path", "none"),
                    "fallback_source": room_media_result.get("fallback_source"),
                    "decision_reason": room_media_result.get("decision_reason"),
                    "refusal_reason": room_media_result.get("refusal_reason"),
                    "refusal_category": room_media_result.get("refusal_category"),
                    "capability_requested": room_media_result.get("capability_requested"),
                    "capability_available": room_media_result.get("capability_available"),
                    "capability_configured": room_media_result.get("capability_configured"),
                    "person_policy_evaluated": room_media_result.get("person_policy_evaluated"),
                    "follow_me_excluded": bool(room_media_result.get("follow_me_excluded", True)),
                    "follow_me_enabled": bool(room_media_result.get("follow_me_enabled", False)),
                    "follow_me_candidate": bool(room_media_result.get("follow_me_candidate", False)),
                    "follow_me_allowed": bool(room_media_result.get("follow_me_allowed", False)),
                    "follow_me_decision": room_media_result.get("follow_me_decision"),
                    "follow_me_reason": room_media_result.get("follow_me_reason"),
                    "identity_authority_source": room_media_result.get("identity_authority_source"),
                    "room_transition_source": room_media_result.get("room_transition_source"),
                    "cooldown_blocked": bool(room_media_result.get("cooldown_blocked", False)),
                    "manual_stop_blocked": bool(room_media_result.get("manual_stop_blocked", False)),
                    "destination_room": room_media_result.get("destination_room"),
                    "source_room": room_media_result.get("source_room"),
                }
                response["media_provider_resolution"]["continuation_strategy"] = room_media_result.get("continuation_strategy")
                response["media_provider_resolution"]["continuation_strategy_reason"] = room_media_result.get("continuation_strategy_reason")
                response["media_provider_resolution"]["source_room_id"] = room_media_result.get("source_room_id")
                response["media_provider_resolution"]["source_room_selection_reason"] = room_media_result.get("source_room_selection_reason")
                response["media_provider_resolution"]["continuation_query"] = room_media_result.get("continuation_query")
                response["media_provider_resolution"]["cooldown_decision"] = room_media_result.get("cooldown_decision", {})
                response["media_provider_resolution"]["personalization_applied"] = bool(room_media_result.get("personalization_applied", False))
                response["media_provider_resolution"]["personalization_reason"] = room_media_result.get("personalization_reason")
                if room_media_result.get("captured_room_media_context") is not None:
                    response["media_provider_resolution"]["captured_room_media_context"] = room_media_result.get("captured_room_media_context")
            response["identity_aware_media_resolution"] = {
                "preference_resolution": room_media_result.get("preference_resolution"),
                "preference_inputs_used": room_media_result.get("preference_inputs_used", {}),
            }
            if room_media_result.get("music_assistant_request") is not None:
                response["media_provider_resolution"]["music_assistant_request"] = room_media_result.get("music_assistant_request")
            response["activity_external_refs"].extend(
                list(room_media_result.get("activity_external_refs", []))
            )
        if monitoring_result is not None:
            response["executed"] = False
            response["resolved_target"] = (
                f"monitoring_follow_up:{monitoring_result.get('monitoring_capability')}"
            )
            response["monitoring_follow_up"] = {
                "monitoring_capability": monitoring_result.get("monitoring_capability"),
                "configured_capability_mapping": monitoring_result.get("configured_capability_mapping", {}),
                "resolved_monitoring_device": monitoring_result.get("resolved_monitoring_device"),
                "resolved_measurement": monitoring_result.get("resolved_measurement"),
                "resolution_strategy": monitoring_result.get("resolution_strategy"),
                "resolution_priority": monitoring_result.get("resolution_priority", []),
                "validation_results": monitoring_result.get("validation_results", []),
                "refusal_reason": monitoring_result.get("refusal_reason"),
                "refusal_category": monitoring_result.get("refusal_category"),
                "room_authority_source": monitoring_result.get("room_authority_source"),
                "merged_room_authority_source": monitoring_result.get("merged_room_authority_source"),
                "capability_requested": monitoring_result.get("capability_requested"),
                "capability_available": monitoring_result.get("capability_available"),
                "capability_configured": monitoring_result.get("capability_configured"),
                "person_policy_evaluated": monitoring_result.get("person_policy_evaluated"),
                "runtime_discovery_reliance": monitoring_result.get("runtime_discovery_reliance"),
                "generated_speech": monitoring_result.get("generated_speech"),
            }
            response["activity_external_refs"].extend(
                list(monitoring_result.get("activity_external_refs", []))
            )
        if identity_self_query_result is not None:
            response["executed"] = True
            response["resolved_target"] = "identity:self_query"
            response["identity_self_query"] = {
                "request_kind": identity_self_query_result.get("request_kind"),
                "generated_speech": identity_self_query_result.get("generated_speech"),
                "active_person_state": identity_self_query_result.get("active_person_state"),
                "active_person_reason_code": identity_self_query_result.get("active_person_reason_code"),
                "resolved_person_id": identity_self_query_result.get("resolved_person_id"),
                "resolved_voice_profile_id": identity_self_query_result.get("resolved_voice_profile_id"),
            }
            response["activity_external_refs"].append(
                {
                    "ref_type": "identity_self_query_resolution",
                    "active_person_state": identity_self_query_result.get("active_person_state"),
                    "active_person_reason_code": identity_self_query_result.get("active_person_reason_code"),
                    "resolved_person_id": identity_self_query_result.get("resolved_person_id"),
                    "resolved_voice_profile_id": identity_self_query_result.get("resolved_voice_profile_id"),
                }
            )
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

        outcome_metadata = _build_execute_outcome_metadata(
            response,
            runtime_context=runtime_context,
        )
        response.update(outcome_metadata)
        response["activity_external_refs"].append(
            {
                "ref_type": "execution_outcome_classification",
                "execution_outcome_category": outcome_metadata["execution_outcome_category"],
                "silence_as_success": outcome_metadata["silence_as_success"],
                "response_required": outcome_metadata["response_required"],
                "response_generated": outcome_metadata["response_generated"],
                "refusal_reason": outcome_metadata["refusal_reason"],
                "refusal_category": outcome_metadata["refusal_category"],
                "room_authority_source": outcome_metadata["room_authority_source"],
                "person_policy_evaluated": outcome_metadata["person_policy_evaluated"],
                "merged_room_authority_source": outcome_metadata["merged_room_authority_source"],
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

        direct_runtime_context = dict(call.data.get("context", {})) if isinstance(call.data.get("context"), dict) else {}
        identity_policy = _evaluate_runtime_identity_authorization_policy(
            call=call,
            requested_target=str(call.data.get("entity_id", "") or ""),
            resolved_target=str(call.data.get("entity_id", "") or ""),
            runtime_context=direct_runtime_context,
        )
        execution_envelope["identity_requirement_class"] = identity_policy["identity_requirement_class"]
        execution_envelope["identity_policy_outcome"] = identity_policy["identity_policy_outcome"]
        execution_envelope["identity_policy_reason_code"] = identity_policy["identity_policy_reason_code"]
        execution_envelope["identity_policy_source"] = identity_policy["identity_policy_source"]
        execution_envelope["identity_freshness_class"] = identity_policy["identity_freshness_class"]
        execution_envelope["attribution_age_ms"] = identity_policy["attribution_age_ms"]
        execution_envelope["identity_state"] = identity_policy["identity_state"]
        execution_envelope["confidence_band"] = identity_policy["confidence_band"]
        execution_envelope["identity_authorization_policy"] = {
            "identity_requirement_class": identity_policy["identity_requirement_class"],
            "identity_policy_outcome": identity_policy["identity_policy_outcome"],
            "identity_policy_reason_code": identity_policy["identity_policy_reason_code"],
            "identity_policy_source": identity_policy["identity_policy_source"],
            "identity_freshness_class": identity_policy["identity_freshness_class"],
            "attribution_age_ms": identity_policy["attribution_age_ms"],
            "identity_state": identity_policy["identity_state"],
            "confidence_band": identity_policy["confidence_band"],
            "classification_source": identity_policy["classification_source"],
        }

        if not bool(identity_policy.get("allows_execution", False)):
            response: dict[str, Any] = {
                "executed": False,
                "execution_envelope": execution_envelope,
                "identity_authorization_policy": dict(
                    execution_envelope.get("identity_authorization_policy", {})
                ),
                "response_message": identity_policy.get("response_message") or None,
                "activity_external_refs": [
                    _build_routing_decision_ref(execution_envelope),
                    _build_execution_envelope_ref(execution_envelope),
                    _build_preservation_alignment_ref(execution_envelope),
                    {
                        "ref_type": "identity_authorization_policy",
                        "identity_requirement_class": identity_policy["identity_requirement_class"],
                        "identity_policy_outcome": identity_policy["identity_policy_outcome"],
                        "identity_policy_reason_code": identity_policy["identity_policy_reason_code"],
                        "identity_policy_source": identity_policy["identity_policy_source"],
                        "identity_freshness_class": identity_policy["identity_freshness_class"],
                        "attribution_age_ms": identity_policy["attribution_age_ms"],
                        "identity_state": identity_policy["identity_state"],
                        "confidence_band": identity_policy["confidence_band"],
                        "classification_source": identity_policy["classification_source"],
                    },
                ],
            }
            outcome_metadata = _build_execute_outcome_metadata(
                response,
                runtime_context=direct_runtime_context,
            )
            response.update(outcome_metadata)
            response["activity_external_refs"].append(
                {
                    "ref_type": "execution_outcome_classification",
                    "execution_outcome_category": outcome_metadata["execution_outcome_category"],
                    "silence_as_success": outcome_metadata["silence_as_success"],
                    "response_required": outcome_metadata["response_required"],
                    "response_generated": outcome_metadata["response_generated"],
                    "refusal_reason": outcome_metadata["refusal_reason"],
                    "refusal_category": outcome_metadata["refusal_category"],
                    "room_authority_source": outcome_metadata["room_authority_source"],
                    "person_policy_evaluated": True,
                    "merged_room_authority_source": outcome_metadata["merged_room_authority_source"],
                },
            )
            return response

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
            "identity_authorization_policy": dict(
                execution_envelope.get("identity_authorization_policy", {})
            ),
            "execution_outcome_category": "EXECUTE_SUCCESS",
            "silence_as_success": False,
            "response_required": False,
            "response_generated": False,
            "response_message": None,
            "refusal_reason": None,
            "refusal_category": None,
            "room_authority_source": "direct_execution",
            "person_policy_evaluated": False,
            "merged_room_authority_source": None,
            "activity_external_refs": [
                _build_routing_decision_ref(execution_envelope),
                _build_execution_envelope_ref(execution_envelope),
                _build_preservation_alignment_ref(execution_envelope),
                {
                    "ref_type": "identity_authorization_policy",
                    "identity_requirement_class": identity_policy["identity_requirement_class"],
                    "identity_policy_outcome": identity_policy["identity_policy_outcome"],
                    "identity_policy_reason_code": identity_policy["identity_policy_reason_code"],
                    "identity_policy_source": identity_policy["identity_policy_source"],
                    "identity_freshness_class": identity_policy["identity_freshness_class"],
                    "attribution_age_ms": identity_policy["attribution_age_ms"],
                    "identity_state": identity_policy["identity_state"],
                    "confidence_band": identity_policy["confidence_band"],
                    "classification_source": identity_policy["classification_source"],
                },
                {
                    "ref_type": "execution_outcome_classification",
                    "execution_outcome_category": "EXECUTE_SUCCESS",
                    "silence_as_success": False,
                    "response_required": False,
                    "response_generated": False,
                    "refusal_reason": None,
                    "refusal_category": None,
                    "room_authority_source": "direct_execution",
                    "person_policy_evaluated": False,
                    "merged_room_authority_source": None,
                },
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
        email_source_bindings = _normalize_source_binding_rows(
            call.data.get("email_source_bindings", []),
            call.data.get("email_source_ref", ""),
        )
        calendar_source_bindings = _normalize_source_binding_rows(
            call.data.get("calendar_source_bindings", []),
            call.data.get("calendar_source_ref", ""),
        )
        shopping_source_bindings = _normalize_source_binding_rows(
            call.data.get("shopping_source_bindings", []),
            call.data.get("shopping_source_ref", ""),
        )
        task_source_bindings = _normalize_source_binding_rows(
            call.data.get("task_source_bindings", []),
            call.data.get("task_source_ref", ""),
        )
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
            email_source_ref=email_source_bindings[0]["entity_id"] if email_source_bindings else "",
            calendar_source_ref=calendar_source_bindings[0]["entity_id"] if calendar_source_bindings else "",
            task_source_ref=task_source_bindings[0]["entity_id"] if task_source_bindings else "",
            shopping_source_ref=shopping_source_bindings[0]["entity_id"] if shopping_source_bindings else "",
            email_source_bindings=email_source_bindings,
            calendar_source_bindings=calendar_source_bindings,
            task_source_bindings=task_source_bindings,
            shopping_source_bindings=shopping_source_bindings,
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
    room_authority_traceability = _build_room_authority_traceability(
        state,
        requested_area_id=call.data.get("area_id"),
        assembled_context=assembled_context,
    )
    weather_response_quality = await _build_room_weather_response(
        hass,
        state=state,
        assembled_context=assembled_context,
        room_authority_traceability=room_authority_traceability,
    )
    monitoring_follow_up = _build_monitoring_follow_up_summary(
        hass,
        state=state,
        assembled_context=assembled_context,
        room_authority_traceability=room_authority_traceability,
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
        room_authority_traceability=room_authority_traceability,
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
    latest_execution_ref = _latest_execution_envelope_ref_from_state(state)
    active_person_resolution = _resolve_active_person_resolution_from_envelope(latest_execution_ref)
    runtime_person_context = _build_runtime_person_context(
        state,
        active_person_resolution=active_person_resolution,
    )
    productivity_source_of_record_boundary = _build_productivity_source_of_record_boundary(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
    )
    calendar_email_consumption_boundary = _build_calendar_email_consumption_boundary(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
    )
    task_shopping_consumption_boundary = _build_task_shopping_consumption_boundary(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
    )
    capture_knowledge_consumption_boundary = _build_capture_knowledge_consumption_boundary(
        state=state,
        hass=hass,
    )
    briefing_composition_boundary = _build_briefing_composition_boundary(
        state=state,
        hass=hass,
    )
    household_status_synthesis_boundary = _build_household_status_synthesis_boundary(
        state=state,
        hass=hass,
    )
    provenance_ownership_consumption_boundary = _build_release_6_provenance_ownership_consumption_boundary(
        state=state,
        hass=hass,
    )
    person_aware_productivity_routing = _build_person_aware_productivity_routing(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
    )
    household_coordination_boundary = _build_household_coordination_boundary(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
        person_aware_productivity_routing=person_aware_productivity_routing,
        household_status_synthesis_boundary=household_status_synthesis_boundary,
        provenance_ownership_consumption_boundary=provenance_ownership_consumption_boundary,
        route_scope=(
            "composite"
            if assembled_context.get("resolved_composite_id")
            else ("room" if assembled_context.get("context_area_id") else "global")
        ),
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    productivity_coordination_boundary = _build_productivity_coordination_boundary(
        state=state,
        hass=hass,
        active_person_resolution=active_person_resolution,
        runtime_person_context=runtime_person_context,
        calendar_email_consumption_boundary=calendar_email_consumption_boundary,
        task_shopping_consumption_boundary=task_shopping_consumption_boundary,
        capture_knowledge_consumption_boundary=capture_knowledge_consumption_boundary,
        provenance_ownership_consumption_boundary=provenance_ownership_consumption_boundary,
        route_scope=(
            "composite"
            if assembled_context.get("resolved_composite_id")
            else ("room" if assembled_context.get("context_area_id") else "global")
        ),
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
    )
    provenance_diagnostics_explainability_boundary = _build_release_6_provenance_diagnostics_explainability_boundary(
        state=state,
        hass=hass,
        route_scope=(
            "composite"
            if assembled_context.get("resolved_composite_id")
            else ("room" if assembled_context.get("context_area_id") else "global")
        ),
        context_area_id=assembled_context.get("context_area_id"),
        resolved_composite_id=assembled_context.get("resolved_composite_id"),
        runtime_person_context=runtime_person_context,
        person_aware_productivity_routing=person_aware_productivity_routing,
        productivity_coordination_boundary=productivity_coordination_boundary,
        household_status_synthesis_boundary=household_status_synthesis_boundary,
        household_coordination_boundary=household_coordination_boundary,
        provenance_ownership_consumption_boundary=provenance_ownership_consumption_boundary,
    )
    summary_response = {
        "summary": assembled_context["summary"],
        "area_id": call.data.get("area_id"),
        "context_area_id": assembled_context["context_area_id"],
        "resolved_composite_id": assembled_context["resolved_composite_id"],
        "include_signals": call.data.get("include_signals", True),
        "include_context": call.data.get("include_context", True),
        "context_source_count": assembled_context["context_source_count"],
        "signal_count": assembled_context["signal_count"],
        "room_authority_traceability": room_authority_traceability,
        "weather_response_quality": weather_response_quality,
        "monitoring_follow_up": monitoring_follow_up,
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
        "productivity_source_of_record_boundary": productivity_source_of_record_boundary,
        "calendar_email_consumption_boundary": calendar_email_consumption_boundary,
        "task_shopping_consumption_boundary": task_shopping_consumption_boundary,
        "capture_knowledge_consumption_boundary": capture_knowledge_consumption_boundary,
        "briefing_composition_boundary": briefing_composition_boundary,
        "productivity_coordination_boundary": productivity_coordination_boundary,
        "household_status_synthesis_boundary": household_status_synthesis_boundary,
        "provenance_ownership_consumption_boundary": provenance_ownership_consumption_boundary,
        "household_coordination_boundary": household_coordination_boundary,
        "provenance_diagnostics_explainability_boundary": provenance_diagnostics_explainability_boundary,
        "active_person_resolution": active_person_resolution,
        "runtime_person_context": runtime_person_context,
        "active_person_state": active_person_resolution["active_person_state"],
        "active_person_reason_code": active_person_resolution["reason_code"],
        "active_person_available": active_person_resolution["active_person_available"],
        "experience_governance_boundary": experience_governance_boundary,
        "capability_to_experience_handoff": capability_to_experience_handoff,
        "experience_projection": experience_projection,
        "experience_restoration_boundary": experience_restoration_boundary,
        "experience_restoration_outcome": experience_restoration_outcome,
        "e3a_preservation_alignment": e3a_preservation_alignment,
    }

    weather_speech = str(weather_response_quality.get("generated_speech") or "").strip()
    monitoring_generated = any(
        bool(str(item.get("generated_speech") or "").strip())
        for item in dict(monitoring_follow_up.get("capabilities", {})).values()
        if isinstance(item, dict)
    )
    response_generated = bool(weather_speech or monitoring_generated or str(assembled_context.get("summary") or "").strip())

    summary_response.update(
        {
            "execution_outcome_category": "ANSWER_SUCCESS",
            "silence_as_success": False,
            "response_required": True,
            "response_generated": response_generated,
            "response_message": weather_speech or str(assembled_context.get("summary") or "").strip() or None,
            "refusal_reason": None,
            "refusal_category": None,
            "room_authority_source": room_authority_traceability.get("room_authority_source", "room_configuration"),
            "person_policy_evaluated": bool(person_aware_productivity_routing.get("person_policy_evaluated", False)),
            "merged_room_authority_source": room_authority_traceability.get("merged_room_authority_source"),
        }
    )
    return summary_response


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
    tts_room_area_id: str | None = None
    configured_room_speakers: list[str] = []
    grouped_room_speaker_map: dict[str, list[str]] = {}
    room_tts_target_speakers: list[str] = []
    merged_room_participation = False
    participating_rooms: list[str] = []
    resolved_composite_id: str | None = None
    room_tts_mode = False

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
        room_tts_mode = True
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
            configured_room_speakers = _resolve_room_audio_speaker_membership(room)
            tts_room_area_id = profile.linked_area_id
            room_context = _resolve_person_room_tts_context(
                state,
                linked_area_id=profile.linked_area_id,
            )
            merged_room_participation = bool(room_context.get("merged_room_participation", False))
            resolved_composite_id = room_context.get("resolved_composite_id")
            participating_rooms = list(room_context.get("participating_rooms", []))
            grouped_room_speaker_map = _resolve_grouped_room_tts_speaker_map(
                state,
                participating_rooms=participating_rooms,
            )
            if merged_room_participation:
                room_tts_target_speakers = list(
                    dict.fromkeys(
                        item for values in grouped_room_speaker_map.values() for item in values
                    )
                )
            else:
                room_tts_target_speakers = [target_id]
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
        room_tts_mode = True
        if room is None:
            raise vol.Invalid("person is not linked to a room with speaker targets")
        speaker_targets = _room_entity_ids(room, "media_player_entity_ids") or _room_entity_ids(
            room,
            "speaker_entity_ids",
        )
        if not speaker_targets:
            raise vol.Invalid("room has no configured speaker targets")
        configured_room_speakers = _resolve_room_audio_speaker_membership(room)
        tts_room_area_id = profile.linked_area_id
        room_context = _resolve_person_room_tts_context(
            state,
            linked_area_id=profile.linked_area_id,
        )
        merged_room_participation = bool(room_context.get("merged_room_participation", False))
        resolved_composite_id = room_context.get("resolved_composite_id")
        participating_rooms = list(room_context.get("participating_rooms", []))
        grouped_room_speaker_map = _resolve_grouped_room_tts_speaker_map(
            state,
            participating_rooms=participating_rooms,
        )
        routing_path = "resolved_room_speaker_target"
        provider, engine_entity_id = _resolve_tts_engine_entity_id(hass)
        tts_settings = _resolve_room_tts_settings(hass, provider=provider, room=room)
        message_data: dict[str, Any] = {"cache": False}
        if tts_settings["voice"]:
            message_data["options"] = {"voice": tts_settings["voice"]}
        if tts_settings["language"]:
            message_data["language"] = tts_settings["language"]
        target_id = speaker_targets[0]
        if merged_room_participation:
            room_tts_target_speakers = list(
                dict.fromkeys(
                    item for values in grouped_room_speaker_map.values() for item in values
                )
            )
        else:
            room_tts_target_speakers = [target_id]
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
        speech_media_separation_lifecycle: dict[str, Any] | None = None
        speech_media_separation_ref: dict[str, Any] | None = None
        if not delivery_permitted:
            raise vol.Invalid(
                "message delivery denied by recipient-consent-privacy-visibility boundary: "
                + delivery_decision_reason
            )

        if room_tts_mode and tts_room_area_id and service_domain == "tts" and service_name == "speak":
            speech_media_separation_lifecycle = await _async_execute_bounded_sonos_speech_lifecycle(
                hass,
                state=state,
                area_id=tts_room_area_id,
                target_speakers=(room_tts_target_speakers or [target_id]),
                room_speaker_map=(
                    grouped_room_speaker_map
                    if grouped_room_speaker_map
                    else {tts_room_area_id: list(configured_room_speakers)}
                ),
                tts_service_data=service_data,
                resolved_composite_id=resolved_composite_id,
            )
            speech_media_separation_ref = {
                "ref_type": "speech_media_separation_lifecycle",
                "policy_name": _SONOS_SPEECH_CONTINUITY_POLICY_NAME,
                "area_id": tts_room_area_id,
                "target_speaker": target_id,
                "group_targeted_speakers": (room_tts_target_speakers or [target_id]),
                "merged_room_participation": merged_room_participation,
                "resolved_composite_id": resolved_composite_id,
                "participating_rooms": participating_rooms,
                "failure_reason": speech_media_separation_lifecycle.get("failure_reason"),
                "fallback_used": bool(speech_media_separation_lifecycle.get("fallback_used", False)),
                "fallback_path": speech_media_separation_lifecycle.get("fallback_path", "none"),
                "media_continuation_performed": False,
                "playback_resume_performed": False,
            }
            delivery_ok = bool(
                speech_media_separation_lifecycle.get("speech", {}).get("delivery_succeeded", False)
            )
            if not delivery_ok:
                error_text = str(
                    speech_media_separation_lifecycle.get("speech", {}).get("delivery_error")
                    or "tts_speak_failed"
                )
                raise vol.Invalid(error_text)
        else:
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
            "speech_media_separation_lifecycle": speech_media_separation_lifecycle,
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
                *(
                    [speech_media_separation_ref]
                    if speech_media_separation_ref is not None
                    else []
                ),
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
