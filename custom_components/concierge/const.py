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
SERVICE_SYNC_COMPOSITES = "sync_composites"
SERVICE_GET_CONTEXT = "get_context"
SERVICE_GET_SUMMARY = "get_summary"
SERVICE_PREVIEW_TTS_VOICE = "preview_tts_voice"
SERVICE_UPDATE_IDENTITY_PROFILE = "update_identity_profile"
SERVICE_SYNC_ROOMS = "sync_rooms"
SERVICE_REFRESH_ENTITY_STRUCTURE = "refresh_entity_structure"

EVENT_EXECUTION = "concierge_execution"

UPDATE_INTERVAL_FALLBACK = timedelta(seconds=DEFAULT_UPDATE_INTERVAL_SECONDS)
