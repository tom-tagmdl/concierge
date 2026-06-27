"""Constants for Concierge."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "concierge"
NAME = "Concierge"

DEFAULT_NAME = "Concierge"
DEFAULT_ENABLE_NOTIFICATIONS = True
DEFAULT_UPDATE_INTERVAL_SECONDS = 60
DEFAULT_NIGHT_MODE_ENABLED = False

CONF_ENABLE_NOTIFICATIONS = "enable_notifications"
CONF_UPDATE_INTERVAL_SECONDS = "update_interval_seconds"
CONF_NIGHT_MODE_ENABLED = "night_mode_enabled"

COORDINATOR_TIMEOUT_SECONDS = 10
COORDINATOR_MIN_UPDATE_SECONDS = 15
COORDINATOR_MAX_UPDATE_SECONDS = 3600

SIGNAL_READY = "ready"
SIGNAL_DEGRADED = "degraded"

UPDATE_INTERVAL_FALLBACK = timedelta(seconds=DEFAULT_UPDATE_INTERVAL_SECONDS)
