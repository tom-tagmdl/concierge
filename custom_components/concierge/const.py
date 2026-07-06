"""Constants for Concierge."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "concierge"
NAME = "Concierge"

DEFAULT_NAME = "Concierge"
DEFAULT_UPDATE_INTERVAL_SECONDS = 60
DEFAULT_NIGHT_MODE_ENABLED = False

CONF_UPDATE_INTERVAL_SECONDS = "update_interval_seconds"
CONF_NIGHT_MODE_ENABLED = "night_mode_enabled"

COORDINATOR_TIMEOUT_SECONDS = 10
COORDINATOR_MIN_UPDATE_SECONDS = 15
COORDINATOR_MAX_UPDATE_SECONDS = 3600

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_foundation"

SIGNAL_READY = "ready"
SIGNAL_DEGRADED = "degraded"

SERVICE_EXECUTE = "execute"
SERVICE_EXECUTE_DIRECT = "execute_direct"
SERVICE_GET_INTERACTIONS = "get_interactions"
SERVICE_UPDATE_INTERACTION = "update_interaction"
SERVICE_CLEAR_INTERACTION = "clear_interaction"
SERVICE_GET_SIGNAL = "get_signal"
SERVICE_GET_SIGNALS = "get_signals"
SERVICE_UPDATE_ROOM_CONFIG = "update_room_config"
SERVICE_UPDATE_GLOBAL_CONTEXT = "update_global_context"
SERVICE_UPDATE_EXECUTION_PREFERENCES = "update_execution_preferences"
SERVICE_UPDATE_COMPOSITE_CONFIG = "update_composite_config"
SERVICE_UPDATE_PERSON_PROFILE = "update_person_profile"
SERVICE_UPDATE_VOICE_PROFILE = "update_voice_profile"
SERVICE_START_VOICE_ENROLLMENT = "start_voice_enrollment"
SERVICE_CAPTURE_VOICE_ENROLLMENT_SAMPLE = "capture_voice_enrollment_sample"
SERVICE_REMOVE_VOICE_ENROLLMENT_SAMPLE = "remove_voice_enrollment_sample"
SERVICE_BUILD_VOICE_PROFILE = "build_voice_profile"
SERVICE_RESET_VOICE_PROFILE = "reset_voice_profile"
SERVICE_DELETE_VOICE_PROFILE = "delete_voice_profile"
SERVICE_SYNC_COMPOSITES = "sync_composites"
SERVICE_GET_CONTEXT = "get_context"
SERVICE_GET_SUMMARY = "get_summary"
SERVICE_PREVIEW_TTS_VOICE = "preview_tts_voice"
SERVICE_UPDATE_IDENTITY_PROFILE = "update_identity_profile"
SERVICE_SYNC_ROOMS = "sync_rooms"
SERVICE_REFRESH_ENTITY_STRUCTURE = "refresh_entity_structure"
SERVICE_RECORD_ACTIVITY_EVENT = "record_activity_event"
SERVICE_CLOSE_ACTIVITY_OUTCOME = "close_activity_outcome"
SERVICE_GET_ACTIVITY_TIMELINE = "get_activity_timeline"
SERVICE_EXPORT_ACTIVITY_ARCHIVE = "export_activity_archive"
SERVICE_RESOLVE_MOBILE_CONTEXT = "resolve_mobile_context"
SERVICE_PUSH_PERSON_MESSAGE = "push_person_message"

EVENT_EXECUTION = "concierge_execution"

VOICE_SYSTEM_DEFAULT = "system_default"

TTS_PROVIDER_ENTITY_IDS = {
	"openai_conversation": "tts.openai_tts",
	"google_translate": "tts.google_translate_en_com",
}

UPDATE_INTERVAL_FALLBACK = timedelta(seconds=DEFAULT_UPDATE_INTERVAL_SECONDS)
