"""Shared runtime helpers for Concierge audit archive behavior."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

CONF_AUDIT_ARCHIVE_DESTINATION_URI = "audit_archive_destination_uri"
CONF_AUDIT_ARCHIVE_ENABLED = "audit_archive_enabled"
CONF_AUDIT_ARCHIVE_INCLUDE_REFERENCE_EXCERPTS = "audit_archive_include_reference_excerpts"
CONF_AUDIT_ARCHIVE_RETENTION_DAYS = "audit_archive_retention_days"

DEFAULT_AUDIT_ARCHIVE_RETENTION_DAYS = 30
DEFAULT_HA_PURGE_KEEP_DAYS = 10
ARCHIVE_PREPURGE_LEAD_DAYS = 2
VOICE_ENROLLMENT_DIRECTORY = "voice_enrollment"


def normalize_archive_destination(value: str | None) -> str:
    """Normalize archive destination path to Home Assistant-friendly form."""
    destination = os.path.expanduser(str(value or "").strip()).replace("\\", "/")
    if any(destination.startswith(prefix) for prefix in ("media/", "share/")):
        destination = f"/{destination.lstrip('/')}"
    if destination.endswith("/") and destination not in {"/media", "/share"}:
        destination = destination.rstrip("/")
    return destination


def is_valid_archive_destination_uri(value: str) -> bool:
    """Validate archive destination URI/path for supported attached storage targets."""
    candidate = normalize_archive_destination(value)
    if not candidate:
        return False
    return (
        candidate == "/media"
        or candidate.startswith("/media/")
        or candidate == "/share"
        or candidate.startswith("/share/")
    )


def archive_trigger_age_days(ha_purge_keep_days: int) -> int:
    """Return age threshold (days) for pre-purge archive capture."""
    return max(1, int(ha_purge_keep_days) - ARCHIVE_PREPURGE_LEAD_DAYS)


def get_ha_purge_keep_days(hass) -> int:
    """Best-effort read of Home Assistant recorder keep-days setting."""
    recorder = hass.data.get("recorder")
    for attr in ("auto_purge_keep_days", "purge_keep_days", "keep_days"):
        value = getattr(recorder, attr, None)
        if isinstance(value, (int, float)) and value > 0:
            return int(value)

    return DEFAULT_HA_PURGE_KEEP_DAYS


def parse_iso_datetime(value: str | None) -> datetime | None:
    """Parse ISO datetime values and normalize to UTC."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def archive_options_from_entry(entry) -> dict[str, Any]:
    """Return normalized audit archive options from a config entry."""
    options = entry.options
    destination_uri = normalize_archive_destination(options.get(CONF_AUDIT_ARCHIVE_DESTINATION_URI, ""))
    destination_configured = is_valid_archive_destination_uri(destination_uri)
    retention_days_raw = options.get(CONF_AUDIT_ARCHIVE_RETENTION_DAYS, DEFAULT_AUDIT_ARCHIVE_RETENTION_DAYS)
    try:
        retention_days = max(1, int(retention_days_raw))
    except (TypeError, ValueError):
        retention_days = DEFAULT_AUDIT_ARCHIVE_RETENTION_DAYS

    return {
        "destination_uri": destination_uri,
        "destination_configured": destination_configured,
        "archive_enabled": bool(options.get(CONF_AUDIT_ARCHIVE_ENABLED, False)) if destination_configured else False,
        "include_reference_excerpts": bool(options.get(CONF_AUDIT_ARCHIVE_INCLUDE_REFERENCE_EXCERPTS, False)) if destination_configured else False,
        "archive_retention_days": retention_days,
    }


def resolve_archive_destination_path(destination_uri: str) -> Path:
    """Resolve configured archive destination URI to a local/UNC path."""
    raw = str(destination_uri or "").strip()
    if not raw:
        raise ValueError("archive destination is required")

    if raw.lower().startswith("file://"):
        parsed = urlparse(raw)
        path_value = unquote(parsed.path or "")
        if parsed.netloc:
            path_value = f"//{parsed.netloc}{path_value}"
        if not path_value:
            raise ValueError("file:// archive destination must include a path")
        return Path(path_value)

    candidate = normalize_archive_destination(raw)
    return Path(candidate)


def resolve_voice_enrollment_root(destination_uri: str) -> Path:
    """Resolve the attached-storage root used for Concierge voice enrollment audio."""
    return resolve_archive_destination_path(destination_uri) / "concierge" / VOICE_ENROLLMENT_DIRECTORY


def cutoff_datetime(days_ago: int) -> datetime:
    """Return UTC cutoff timestamp for an age threshold in days."""
    return datetime.now(timezone.utc) - timedelta(days=max(1, int(days_ago)))
