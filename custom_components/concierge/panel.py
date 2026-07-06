from __future__ import annotations

from datetime import datetime, timezone
import logging
import os
from pathlib import Path
from typing import Any
from aiohttp import web

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.components.http import HomeAssistantView, StaticPathConfig
from homeassistant.components.tts.const import DATA_COMPONENT as TTS_DATA_COMPONENT
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
    floor_registry as fr,
    label_registry as lr,
)

from .const import DOMAIN
from .const import TTS_PROVIDER_ENTITY_IDS
from .archive_runtime import (
    archive_options_from_entry,
    archive_trigger_age_days,
    get_ha_purge_keep_days,
    resolve_voice_enrollment_root,
)
from .storage import ConciergeStorage

_LOGGER = logging.getLogger(__name__)
_PANEL_REGISTERED_FLAG = "_panel_registered"
_STATIC_REGISTERED_FLAG = "_panel_static_registered"
_VERSION_VIEW_REGISTERED_FLAG = "_panel_version_view_registered"
_SNAPSHOT_VIEW_REGISTERED_FLAG = "_panel_snapshot_view_registered"
_TTS_CATALOG_VIEW_REGISTERED_FLAG = "_panel_tts_catalog_view_registered"
_VOICE_UPLOAD_VIEW_REGISTERED_FLAG = "_panel_voice_upload_view_registered"
_BUILD_INFO_KEY = "_panel_build_info"

_ASSET_INTELLIGENCE_DOMAIN = "asset_intelligence"
_PROVIDER_NONE = "none"
_PROVIDER_ASSET_INTELLIGENCE = "asset_intelligence"

_INTEGRATION_NAME_OVERRIDES: dict[str, str] = {
    "accuweather": "AccuWeather",
    "met": "Met.no",
    "openweathermap": "OpenWeatherMap",
    "pirateweather": "Pirate Weather",
    "feedreader": "Feedreader",
}


def _archive_status_from_options(hass) -> dict[str, Any]:
    """Return archive wiring/status from Concierge integration options."""
    entries = hass.config_entries.async_entries(DOMAIN)
    ha_purge_keep_days = get_ha_purge_keep_days(hass)
    archive_capture_age_days = archive_trigger_age_days(ha_purge_keep_days)

    if not entries:
        return {
            "destination_uri": "",
            "destination_configured": False,
            "archive_enabled": False,
            "include_reference_excerpts": False,
            "ha_purge_keep_days": ha_purge_keep_days,
            "archive_capture_age_days": archive_capture_age_days,
            "archive_retention_days": 30,
        }

    entry = entries[0]
    archive_options = archive_options_from_entry(entry)
    return {
        **archive_options,
        "ha_purge_keep_days": ha_purge_keep_days,
        "archive_capture_age_days": archive_capture_age_days,
    }


def _integration_options_from_entry(hass) -> dict[str, Any]:
    """Return selected Concierge integration options needed by frontend behavior."""
    def _coerce_provider(value: Any) -> str:
        return str(value or _PROVIDER_NONE).strip() or _PROVIDER_NONE

    def _coerce_bool(value: Any, default: bool = False) -> bool:
        if value is None:
            return default
        return bool(value)

    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        capabilities = {
            "cap_ai": False,
            "cap_tts": False,
            "cap_persona": False,
            "cap_assets": False,
            "cap_voice_enrollment": False,
            "cap_extended_history": False,
        }
        return {
            "ai_enabled": False,
            "ai_local_first": True,
            "action_provider": _PROVIDER_NONE,
            "tts_provider": _PROVIDER_NONE,
            "tts_enabled": False,
            "media_provider": _PROVIDER_NONE,
            "asset_intelligence_provider": _PROVIDER_NONE,
            "capabilities": capabilities,
        }

    entry = entries[0]
    options = entry.options
    data = entry.data

    ai_enabled = _coerce_bool(options.get("ai_enabled", data.get("ai_enabled", False)))
    ai_local_first = _coerce_bool(options.get("ai_local_first", data.get("ai_local_first", True)), True)
    action_provider = _coerce_provider(options.get("action_provider", data.get("action_provider", _PROVIDER_NONE)))
    tts_enabled = _coerce_bool(options.get("tts_enabled", data.get("tts_enabled", False)))
    tts_provider = _coerce_provider(options.get("tts_provider", data.get("tts_provider", _PROVIDER_NONE)))
    media_provider = _coerce_provider(options.get("media_provider", data.get("media_provider", _PROVIDER_NONE)))
    asset_intelligence_provider = _coerce_provider(
        options.get("asset_intelligence_provider", data.get("asset_intelligence_provider", _PROVIDER_NONE))
    )

    archive_options = archive_options_from_entry(entry)
    cap_ai = bool(ai_enabled and action_provider != _PROVIDER_NONE)
    cap_tts = bool(tts_enabled and tts_provider != _PROVIDER_NONE)
    cap_persona = bool(cap_ai or cap_tts)
    cap_assets = bool(asset_intelligence_provider == _PROVIDER_ASSET_INTELLIGENCE)
    cap_voice_enrollment = bool(archive_options.get("destination_configured") and archive_options.get("archive_enabled"))
    cap_extended_history = bool(archive_options.get("destination_configured") and archive_options.get("archive_enabled"))

    return {
        "ai_enabled": ai_enabled,
        "ai_local_first": ai_local_first,
        "action_provider": action_provider,
        "tts_provider": tts_provider,
        "tts_enabled": tts_enabled,
        "media_provider": media_provider,
        "asset_intelligence_provider": asset_intelligence_provider,
        "capabilities": {
            "cap_ai": cap_ai,
            "cap_tts": cap_tts,
            "cap_persona": cap_persona,
            "cap_assets": cap_assets,
            "cap_voice_enrollment": cap_voice_enrollment,
            "cap_extended_history": cap_extended_history,
        },
    }


def _normalize_language_tag(tag: str | None) -> str:
    """Normalize a language tag for cross-source comparisons."""
    return str(tag or "").strip().replace("_", "-").lower()


def _match_language_tag(candidate: str | None, languages: list[str]) -> str:
    """Return the best matching language tag from an available catalog."""
    raw_candidate = str(candidate or "").strip()
    if not raw_candidate:
        return ""
    if raw_candidate in languages:
        return raw_candidate

    normalized_candidate = _normalize_language_tag(raw_candidate)
    for language in languages:
        if _normalize_language_tag(language) == normalized_candidate:
            return language
    return raw_candidate


def _preferred_assist_pipeline_tts_language(hass) -> str:
    """Return the preferred Assist pipeline language for TTS defaults."""
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


async def _async_build_tts_catalog(hass) -> dict[str, Any]:
    """Return provider-backed TTS language and voice metadata for Concierge UI."""
    integration_options = _integration_options_from_entry(hass)
    provider = str(integration_options.get("tts_provider", "none") or "none")
    empty_catalog = {
        "provider": provider,
        "default_language": "",
        "languages": [],
        "language_labels": {},
        "voices_by_language": {},
    }

    if not integration_options.get("tts_enabled") or not provider or provider == "none":
        return empty_catalog

    default_language = ""
    language_labels: dict[str, str] = {}
    voices_by_language: dict[str, list[dict[str, str]]] = {}

    tts_services = hass.services.async_services().get("tts", {})
    if "get_voices" in tts_services:
        try:
            try:
                result = await hass.services.async_call(
                    "tts",
                    "get_voices",
                    {"engine_id": provider},
                    blocking=True,
                    return_response=True,
                )
            except Exception:
                result = await hass.services.async_call(
                    "tts",
                    "get_voices",
                    {},
                    blocking=True,
                    return_response=True,
                )

            voice_rows: list[dict[str, str]] = []

            def _walk(node: Any) -> None:
                nonlocal default_language
                if not node:
                    return
                if isinstance(node, list):
                    for item in node:
                        _walk(item)
                    return
                if not isinstance(node, dict):
                    return

                if not default_language:
                    candidate = str(node.get("default_language") or "").strip()
                    if candidate:
                        default_language = candidate

                language = str(node.get("language") or node.get("lang") or "").strip()
                language_label = str(
                    node.get("language_name")
                    or node.get("locale_name")
                    or node.get("display_language")
                    or language
                ).strip()
                if language and language_label and language not in language_labels:
                    language_labels[language] = language_label

                voice_id = str(node.get("voice_id") or node.get("voice") or "").strip()
                voice_name = str(node.get("name") or voice_id or "").strip()
                if voice_id and language:
                    voice_rows.append(
                        {
                            "voice_id": voice_id,
                            "voice_name": voice_name or voice_id,
                            "language": language,
                        }
                    )

                for value in node.values():
                    _walk(value)

            _walk(result)

            seen: set[tuple[str, str]] = set()
            for row in voice_rows:
                key = (row["language"], row["voice_id"])
                if key in seen:
                    continue
                seen.add(key)
                voices_by_language.setdefault(row["language"], []).append(
                    {
                        "voice_id": row["voice_id"],
                        "voice_name": row["voice_name"],
                    }
                )
        except Exception:
            _LOGGER.exception("Concierge: failed loading provider-backed TTS catalog from get_voices")

    if not voices_by_language:
        entity_id = TTS_PROVIDER_ENTITY_IDS.get(provider)
        if entity_id and TTS_DATA_COMPONENT in hass.data:
            entity_component = hass.data[TTS_DATA_COMPONENT]
            tts_entity = entity_component.get_entity(entity_id)
            if tts_entity is not None:
                default_language = str(getattr(tts_entity, "default_language", "") or "").strip()
                raw_languages = getattr(tts_entity, "supported_languages", None)
                languages = []
                if isinstance(raw_languages, (list, tuple, set)):
                    languages = [str(item or "").strip() for item in raw_languages if str(item or "").strip()]
                if default_language and default_language not in languages:
                    languages.insert(0, default_language)
                if not languages and default_language:
                    languages = [default_language]

                for language in languages:
                    language_labels.setdefault(language, language)
                    try:
                        supported_voices = tts_entity.async_get_supported_voices(language)
                    except Exception:
                        supported_voices = None
                    if not supported_voices:
                        continue
                    deduped_for_language: list[dict[str, str]] = []
                    seen_voice_ids: set[str] = set()
                    for voice in supported_voices:
                        voice_id = str(getattr(voice, "voice_id", "") or "").strip()
                        if not voice_id or voice_id in seen_voice_ids:
                            continue
                        seen_voice_ids.add(voice_id)
                        voice_name = str(getattr(voice, "name", "") or voice_id).strip() or voice_id
                        deduped_for_language.append({
                            "voice_id": voice_id,
                            "voice_name": voice_name,
                        })
                    if deduped_for_language:
                        voices_by_language[language] = deduped_for_language

    for language, entries in voices_by_language.items():
        entries.sort(key=lambda item: str(item.get("voice_name") or "").lower())

    normalized_languages = sorted(voices_by_language.keys(), key=str.lower)
    preferred_pipeline_language = _match_language_tag(
        _preferred_assist_pipeline_tts_language(hass),
        normalized_languages,
    )
    if preferred_pipeline_language:
        default_language = preferred_pipeline_language
    elif not default_language and normalized_languages:
        default_language = normalized_languages[0]
    else:
        default_language = _match_language_tag(default_language, normalized_languages)
    for language in normalized_languages:
        language_labels.setdefault(language, language)

    return {
        "provider": provider,
        "default_language": default_language,
        "languages": normalized_languages,
        "language_labels": language_labels,
        "voices_by_language": voices_by_language,
    }


def _entity_name(entry: er.RegistryEntry) -> str:
    """Return best available display name for a registry entity entry."""
    if entry.name:
        return entry.name
    if entry.original_name:
        return entry.original_name
    object_id = entry.entity_id.split(".", 1)[1] if "." in entry.entity_id else entry.entity_id
    return " ".join(part.capitalize() for part in object_id.split("_") if part)


def _entity_object_label(entry: er.RegistryEntry) -> str:
    """Return object-id based label for concise service naming."""
    object_id = entry.entity_id.split(".", 1)[1] if "." in entry.entity_id else entry.entity_id
    return " ".join(part.capitalize() for part in object_id.split("_") if part)


def _format_integration_name(raw: str) -> str:
    """Normalize integration domain/platform to friendly title."""
    if not raw:
        return ""
    key = str(raw).strip().lower()
    if key in _INTEGRATION_NAME_OVERRIDES:
        return _INTEGRATION_NAME_OVERRIDES[key]
    return " ".join(part.capitalize() for part in key.split("_") if part)


def _weather_provider_from_state(hass, entry: er.RegistryEntry) -> str:
    """Infer weather provider integration label from entity state metadata."""
    state = hass.states.get(entry.entity_id)
    if state is None:
        return ""

    for attr_name in ("provider", "source", "attribution"):
        value = state.attributes.get(attr_name)
        if not value:
            continue
        text = str(value)
        lowered = text.lower()
        if "accuweather" in lowered:
            return "AccuWeather"
        if "openweathermap" in lowered or "open weather" in lowered:
            return "OpenWeatherMap"
        if "met.no" in lowered or "met no" in lowered:
            return "Met.no"
        if "pirate weather" in lowered:
            return "Pirate Weather"

    return ""


def _entity_integration_label(hass, entry: er.RegistryEntry) -> str:
    """Resolve the best integration label for an entity row."""
    config_entry = None
    if entry.config_entry_id:
        config_entry = hass.config_entries.async_get_entry(entry.config_entry_id)

    if config_entry is not None:
        if config_entry.domain:
            return _format_integration_name(config_entry.domain)

    platform = entry.platform or ""
    if platform:
        return _format_integration_name(platform)

    domain = entry.entity_id.split(".", 1)[0]
    return _format_integration_name(domain)


def _to_entity_row(entry: er.RegistryEntry, hass=None) -> dict[str, str]:
    """Project a registry entry into a stable entity row payload."""
    name = _entity_name(entry)
    integration = _entity_integration_label(hass, entry) if hass is not None else ""
    display_name = f"{integration} - {name}" if integration else name
    label_ids: list[str] = []
    if hass is not None:
        device_registry = dr.async_get(hass)
        device = device_registry.devices.get(entry.device_id) if entry.device_id else None
        device_labels = [str(label_id) for label_id in (getattr(device, "labels", []) or []) if label_id] if device else []
        entity_labels = [str(label_id) for label_id in (getattr(entry, "labels", set()) or set()) if label_id]
        label_ids = sorted(set(device_labels + entity_labels))
    return {
        "entity_id": entry.entity_id,
        "device_id": entry.device_id or "",
        "name": name,
        "domain": entry.entity_id.split(".", 1)[0],
        "integration": integration,
        "display_name": display_name,
        "label_ids": label_ids,
    }


def _person_ble_suggestions(
    person: Any,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> tuple[list[str], dict[str, list[str]]]:
    """Derive BLE enrollment candidates from a person's attached trackers."""
    tracker_entity_ids = person.attributes.get("device_trackers", []) if getattr(person, "attributes", None) else []
    candidates: dict[str, set[str]] = {}

    for tracker_entity_id in tracker_entity_ids:
        entry = entity_registry.entities.get(tracker_entity_id)
        if entry is None or entry.device_id is None:
            continue

        device = device_registry.devices.get(entry.device_id)
        if device is None:
            continue

        for connection_type, connection_id in getattr(device, "connections", set()):
            if connection_type not in {dr.CONNECTION_BLUETOOTH, dr.CONNECTION_NETWORK_MAC}:
                continue

            candidate = str(connection_id).strip()
            if not candidate:
                continue

            candidates.setdefault(candidate, set()).add(tracker_entity_id)

    suggested_device_ids = sorted(candidates)
    suggestion_sources = {device_id: sorted(candidates[device_id]) for device_id in suggested_device_ids}
    return suggested_device_ids, suggestion_sources


def _build_room_entity_catalog(hass, area_ids: set[str]) -> dict[str, dict[str, list[dict[str, str]]]]:
    """Build categorized entity catalogs for each room/area."""
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)
    label_registry = lr.async_get(hass)
    asset_label_ids = {
        label_id
        for label_id, label in label_registry.labels.items()
        if str(label.name or "").strip().lower() in {"asset", "assets"}
    }
    lamp_label_ids = {
        label_id
        for label_id, label in label_registry.labels.items()
        if str(label.name or "").strip().lower() in {"lamp", "lamps"}
    }
    asset_device_rows_by_area: dict[str, list[dict[str, str]]] = {area_id: [] for area_id in area_ids}

    for device in device_registry.devices.values():
        device_area_id = getattr(device, "area_id", None)
        if device_area_id not in area_ids:
            continue

        device_labels = set(str(label) for label in (getattr(device, "labels", []) or []) if label)
        if not (
            getattr(device, "manufacturer", "") == "Asset Intelligence"
            or bool(asset_label_ids.intersection(device_labels))
        ):
            continue

        device_entities = [
            entry
            for entry in entity_registry.entities.values()
            if entry.device_id == device.id and entry.disabled_by is None
        ]
        if not device_entities:
            continue

        representative = sorted(
            device_entities,
            key=lambda item: (
                0 if item.entity_id.startswith("sensor.") else 1,
                0 if "asset" in item.entity_id.split(".", 1)[-1].lower() else 1,
                _entity_name(item).lower(),
                item.entity_id,
            ),
        )[0]

        row_payload = _to_entity_row(representative, hass)
        device_name = str(device.name_by_user or device.name or "").strip()
        if device_name:
            row_payload["name"] = device_name
            integration = row_payload.get("integration", "")
            row_payload["display_name"] = f"{integration} - {device_name}" if integration else device_name
        row_payload["device_id"] = device.id
        row_payload["label_ids"] = list(device_labels)
        asset_device_rows_by_area.setdefault(device_area_id, []).append(row_payload)

    catalog: dict[str, dict[str, list[er.RegistryEntry]]] = {
        area_id: {
            "asset_device_rows": [],
            "room_sensor_entity_ids": [],
            "room_health_entity_ids": [],
            "human_health_entity_ids": [],
            "light_entity_ids": [],
            "lamp_entity_ids": [],
            "shade_entity_ids": [],
            "speaker_entity_ids": [],
            "tv_entity_ids": [],
            "media_player_entity_ids": [],
            "voice_device_entity_ids": [],
            "dashboard_entity_ids": [],
            "other_entity_ids": [],
        }
        for area_id in area_ids
    }

    for entry in entity_registry.entities.values():
        if entry.disabled_by is not None:
            continue

        area_id = entry.area_id
        if area_id is None and entry.device_id:
            device = device_registry.devices.get(entry.device_id)
            if device is not None:
                area_id = device.area_id

        if area_id not in area_ids:
            continue

        domain = entry.entity_id.split(".", 1)[0]
        object_id = entry.entity_id.split(".", 1)[1] if "." in entry.entity_id else ""
        platform = entry.platform or ""
        device = device_registry.devices.get(entry.device_id) if entry.device_id else None
        device_labels = set(str(label) for label in (getattr(device, "labels", []) or []) if label) if device else set()
        is_asset_intelligence_device = bool(
            device
            and (
                getattr(device, "manufacturer", "") == "Asset Intelligence"
                or bool(asset_label_ids.intersection(device_labels))
            )
        )
        device_class = (entry.original_device_class or "").lower()
        unit = (entry.unit_of_measurement or "").lower()
        is_room_sensor = (
            domain == "sensor"
            and (
                device_class in {"temperature", "humidity", "illuminance"}
                or unit in {"c", "f", "lx", "%"}
                or any(token in object_id for token in ("temperature", "humidity", "illuminance", "lux", "light_level"))
            )
        )
        is_ai_assessment = platform == _ASSET_INTELLIGENCE_DOMAIN and (
            "room_health" in object_id
            or "environment_health" in object_id
            or "human_health" in object_id
            or "occupant_health" in object_id
            or "assessment" in object_id
        )

        room_bucket = catalog[area_id]
        if is_room_sensor:
            room_bucket["room_sensor_entity_ids"].append(entry)
        if is_ai_assessment and ("room_health" in object_id or "environment_health" in object_id):
            room_bucket["room_health_entity_ids"].append(entry)
        if is_ai_assessment and ("human_health" in object_id or "occupant_health" in object_id):
            room_bucket["human_health_entity_ids"].append(entry)
        if domain == "light":
            entry_labels = set(getattr(entry, "labels", set()) or set())
            if lamp_label_ids.intersection(entry_labels):
                room_bucket["lamp_entity_ids"].append(entry)
            else:
                room_bucket["light_entity_ids"].append(entry)
        if domain == "cover":
            room_bucket["shade_entity_ids"].append(entry)
        if domain == "media_player":
            is_tv = any(token in object_id for token in ("tv", "television"))
            if is_tv:
                room_bucket["tv_entity_ids"].append(entry)
            else:
                room_bucket["media_player_entity_ids"].append(entry)
                room_bucket["speaker_entity_ids"].append(entry)
        if domain == "assist_satellite":
            room_bucket["voice_device_entity_ids"].append(entry)
        if "dashboard" in object_id:
            room_bucket["dashboard_entity_ids"].append(entry)

        if not (
            is_asset_intelligence_device
            or is_room_sensor
            or is_ai_assessment
            or domain in {"light", "cover", "media_player", "assist_satellite"}
            or "dashboard" in object_id
        ):
            room_bucket["other_entity_ids"].append(entry)

    result: dict[str, dict[str, list[dict[str, str]]]] = {}
    for area_id, buckets in catalog.items():
        result[area_id] = {}
        for key, rows in buckets.items():
            unique_by_id = {row.entity_id: row for row in rows}
            ordered = sorted(unique_by_id.values(), key=lambda item: _entity_name(item).lower())

            if key == "asset_device_rows":
                # Show one selectable row per asset device to avoid duplicate entities per asset.
                grouped_by_device: dict[str, list[er.RegistryEntry]] = {}
                for item in ordered:
                    group_key = item.device_id or item.entity_id
                    grouped_by_device.setdefault(group_key, []).append(item)

                representative_rows: list[dict[str, str]] = []
                for group_key in sorted(grouped_by_device.keys()):
                    group = grouped_by_device[group_key]
                    representative = sorted(
                        group,
                        key=lambda item: (
                            0 if "asset" in item.entity_id.split(".", 1)[-1].lower() else 1,
                            _entity_name(item).lower(),
                            item.entity_id,
                        ),
                    )[0]

                    row_payload = _to_entity_row(representative, hass)
                    if representative.device_id:
                        device = device_registry.devices.get(representative.device_id)
                        device_name = ""
                        if device is not None:
                            device_name = str(device.name_by_user or device.name or "").strip()
                        if device_name:
                            row_payload["name"] = device_name
                            integration = row_payload.get("integration", "")
                            row_payload["display_name"] = (
                                f"{integration} - {device_name}" if integration else device_name
                            )
                    representative_rows.append(row_payload)

                result[area_id][key] = asset_device_rows_by_area.get(area_id, representative_rows)
                continue

            result[area_id][key] = [_to_entity_row(item, hass) for item in ordered]

    return result


def _build_global_catalog(hass) -> dict[str, list[dict[str, str]]]:
    """Build global feature candidate entities (weather/news/alarm)."""
    entity_registry = er.async_get(hass)

    weather_rows: list[er.RegistryEntry] = []
    news_rows: list[er.RegistryEntry] = []
    alarm_rows: list[er.RegistryEntry] = []

    for entry in entity_registry.entities.values():
        if entry.disabled_by is not None:
            continue

        entity_id = entry.entity_id
        domain = entity_id.split(".", 1)[0]
        object_id = entity_id.split(".", 1)[1] if "." in entity_id else ""

        if domain == "weather":
            weather_rows.append(entry)
        if domain == "alarm_control_panel":
            alarm_rows.append(entry)
        if domain in {"sensor", "binary_sensor", "event"} and any(
            token in object_id for token in ("news", "headline", "rss")
        ):
            news_rows.append(entry)

    # Feedreader is event-driven and may not expose a selectable entity.
    feedreader_entries = [
        entry
        for entry in hass.config_entries.async_entries("feedreader")
        if entry.state == ConfigEntryState.LOADED
    ]
    news_entities = [_to_entity_row(item, hass) for item in sorted(news_rows, key=lambda item: _entity_name(item).lower())]

    if feedreader_entries:
        for entry in feedreader_entries:
            feed_title = str(entry.title or "Feed").strip() or "Feed"
            news_entities.append(
                {
                    "entity_id": f"provider.feedreader.{entry.entry_id}",
                    "name": feed_title,
                    "domain": "provider",
                    "integration": "Feedreader",
                    "display_name": f"Feedreader - {feed_title}",
                }
            )
    news_entities = sorted(news_entities, key=lambda item: str(item.get("display_name", item.get("name", ""))).lower())

    weather_entities: list[dict[str, str]] = []
    for item in sorted(weather_rows, key=lambda row: _entity_name(row).lower()):
        provider = _weather_provider_from_state(hass, item) or _entity_integration_label(hass, item)
        service_name = _entity_object_label(item) or _entity_name(item)
        weather_entities.append(
            {
                "entity_id": item.entity_id,
                "name": service_name,
                "domain": item.entity_id.split(".", 1)[0],
                "integration": provider,
                "display_name": f"{provider} - {service_name}" if provider else service_name,
            }
        )

    return {
        "weather_entity_ids": weather_entities,
        "news_entity_ids": news_entities,
        "alarm_entity_ids": [_to_entity_row(item, hass) for item in sorted(alarm_rows, key=lambda item: _entity_name(item).lower())],
    }


def _build_composite_catalog(
    composites_state: dict[str, dict[str, Any]],
    room_catalog: dict[str, dict[str, list[dict[str, str]]]],
) -> dict[str, dict[str, list[dict[str, str]]]]:
    """Build aggregated selector catalogs for composites from member room catalogs."""
    category_keys = (
        "asset_device_rows",
        "room_sensor_entity_ids",
        "room_health_entity_ids",
        "human_health_entity_ids",
        "light_entity_ids",
        "media_player_entity_ids",
        "shade_entity_ids",
        "speaker_entity_ids",
        "voice_device_entity_ids",
        "dashboard_entity_ids",
        "other_entity_ids",
    )

    composite_catalog: dict[str, dict[str, list[dict[str, str]]]] = {}
    for composite_id, composite in composites_state.items():
        area_ids = composite.get("area_ids") if isinstance(composite, dict) else []
        if not isinstance(area_ids, list):
            area_ids = []

        merged: dict[str, dict[str, dict[str, Any]]] = {
            key: {}
            for key in category_keys
        }

        for area_id in area_ids:
            area_catalog = room_catalog.get(area_id, {}) if isinstance(area_id, str) else {}
            for key in category_keys:
                rows = area_catalog.get(key, [])
                if not isinstance(rows, list):
                    continue
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    entity_id = row.get("entity_id")
                    if not isinstance(entity_id, str) or not entity_id:
                        continue
                    existing = merged[key].get(entity_id, {})
                    existing_labels = set(str(label_id) for label_id in (existing.get("label_ids", []) or []) if label_id)
                    row_labels = set(str(label_id) for label_id in (row.get("label_ids", []) or []) if label_id)
                    merged[key][entity_id] = {
                        "entity_id": entity_id,
                        "device_id": row.get("device_id", existing.get("device_id", "")),
                        "name": row.get("name", existing.get("name", entity_id)),
                        "domain": row.get("domain", existing.get("domain", entity_id.split(".", 1)[0] if "." in entity_id else "")),
                        "integration": row.get("integration", existing.get("integration", "")),
                        "display_name": row.get("display_name", existing.get("display_name", row.get("name", entity_id))),
                        "label_ids": sorted(existing_labels.union(row_labels)),
                    }

        composite_catalog[composite_id] = {
            key: sorted(entities.values(), key=lambda item: str(item.get("name", "")).lower())
            for key, entities in merged.items()
        }

    return composite_catalog


def _is_asset_intelligence_connected(hass) -> bool:
    """Determine whether Asset Intelligence is installed and currently loaded."""
    entries = hass.config_entries.async_entries(_ASSET_INTELLIGENCE_DOMAIN)
    return any(entry.state is ConfigEntryState.LOADED for entry in entries)


def _humanize_floor_id(floor_id: str | None) -> str:
    """Convert floor slug to readable label when registry name is unavailable."""
    if not floor_id:
        return "Unassigned"
    return " ".join(part.capitalize() for part in floor_id.split("_") if part)


def _voice_storage_root_from_hass(hass) -> Path:
    """Return configured attached-storage root for voice enrollment audio."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        raise ValueError("concierge config entry not found")

    archive_options = archive_options_from_entry(entries[0])
    destination_uri = str(archive_options.get("destination_uri", "") or "").strip()
    destination_configured = bool(archive_options.get("destination_configured", False))
    if not destination_configured or not destination_uri:
        raise ValueError("attached storage destination is not configured in Concierge options")

    return resolve_voice_enrollment_root(destination_uri)


def _safe_voice_slug(value: str) -> str:
    """Normalize ids into safe folder-name slugs."""
    normalized = str(value or "").strip().lower().replace(".", "_").replace(" ", "_")
    normalized = "".join(ch for ch in normalized if ch.isalnum() or ch in {"_", "-"})
    return normalized or "unknown"


def _voice_suffix_for_content_type(content_type: str) -> str:
    """Map upload content types to file suffixes."""
    lowered = str(content_type or "").lower()
    if "ogg" in lowered:
        return ".ogg"
    if "wav" in lowered or "wave" in lowered:
        return ".wav"
    if "mpeg" in lowered or "mp3" in lowered:
        return ".mp3"
    if "webm" in lowered:
        return ".webm"
    return ".bin"


def _write_voice_sample_bytes(
    *,
    root_path: Path,
    person_id: str,
    voice_profile_id: str,
    phrase_index: int,
    content_type: str,
    payload: bytes,
) -> Path:
    """Persist uploaded voice sample bytes beneath the configured attached-storage root."""
    sample_dir = root_path / _safe_voice_slug(person_id) / _safe_voice_slug(voice_profile_id)
    sample_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    suffix = _voice_suffix_for_content_type(content_type)
    file_name = f"phrase_{int(phrase_index) + 1:02d}_{stamp}{suffix}"
    destination = sample_dir / file_name
    destination.write_bytes(payload)
    return destination


class ConciergeStorageSnapshotView(HomeAssistantView):
    """Expose Concierge + area snapshot for fast frontend bootstrap."""

    url = "/api/concierge/storage_snapshot"
    name = "api:concierge:storage_snapshot"
    requires_auth = True

    async def get(self, request):
        hass = request.app["hass"]

        rooms_state: dict = {}
        composites_state: dict = {}
        people_state: dict = {}
        person_profiles_state: dict = {}
        voice_profiles_state: dict = {}
        global_features: dict[str, dict[str, Any]] = {}
        global_context_usage: dict[str, dict[str, Any]] = {}
        try:
            state = await ConciergeStorage(hass).async_load_state()
            entity_registry = er.async_get(hass)
            device_registry = dr.async_get(hass)
            rooms_state = {
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
                for area_id, room in state.rooms.items()
            }
            composites_state = {
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
                for composite_id, composite in state.composites.items()
            }
            people_state = {}
            for person in hass.states.async_all("person"):
                suggested_ble_device_ids, suggested_ble_device_sources = _person_ble_suggestions(
                    person,
                    entity_registry,
                    device_registry,
                )
                people_state[person.entity_id] = {
                    "entity_id": person.entity_id,
                    "name": person.name,
                    "state": person.state,
                    "entity_picture": person.attributes.get("entity_picture"),
                    "editable": person.attributes.get("editable"),
                    "device_trackers": person.attributes.get("device_trackers", []),
                    "in_zones": person.attributes.get("in_zones", []),
                    "user_id": person.attributes.get("user_id"),
                    "latitude": person.attributes.get("latitude"),
                    "longitude": person.attributes.get("longitude"),
                    "gps_accuracy": person.attributes.get("gps_accuracy"),
                    "source": person.attributes.get("source"),
                    "id": person.attributes.get("id"),
                    "ble_device_suggestions": suggested_ble_device_ids,
                    "ble_device_suggestion_sources": suggested_ble_device_sources,
                }
            person_profiles_state = {
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
                for person_id, profile in state.person_profiles.items()
            }
            voice_profiles_state = {
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
                for voice_profile_id, profile in state.voice_profiles.items()
            }
            global_features = state.global_features
            global_context_usage = state.global_context_usage
        except Exception:
            _LOGGER.exception("Concierge: failed loading storage snapshot")

        areas = []
        floor_names: dict[str, str] = {}
        try:
            area_registry = ar.async_get(hass)
            floor_registry = fr.async_get(hass)
            floor_names = {
                floor.floor_id: floor.name
                for floor in floor_registry.async_list_floors()
            }
            areas = [
                {
                    "id": area.id,
                    "name": area.name,
                    "picture": area.picture,
                    "icon": area.icon,
                    "floor_id": area.floor_id,
                    "floor_name": floor_names.get(
                        area.floor_id or "",
                        _humanize_floor_id(area.floor_id),
                    ),
                }
                for area in area_registry.async_list_areas()
            ]
        except Exception:
            _LOGGER.exception("Concierge: failed loading area registry snapshot")

        area_ids = {area["id"] for area in areas}
        try:
            room_catalog = _build_room_entity_catalog(hass, area_ids)
        except Exception:
            room_catalog = {area_id: {} for area_id in area_ids}
            _LOGGER.exception("Concierge: failed building room entity catalog")

        try:
            composite_catalog = _build_composite_catalog(composites_state, room_catalog)
        except Exception:
            composite_catalog = {composite_id: {} for composite_id in composites_state}
            _LOGGER.exception("Concierge: failed building composite entity catalog")

        try:
            global_catalog = _build_global_catalog(hass)
        except Exception:
            global_catalog = {
                "weather_entity_ids": [],
                "news_entity_ids": [],
                "alarm_entity_ids": [],
            }
            _LOGGER.exception("Concierge: failed building global catalog")

        response = web.json_response(
            {
                "areas": areas,
                "rooms": rooms_state,
                "composites": composites_state,
                "people": people_state,
                "person_profiles": person_profiles_state,
                "voice_profiles": voice_profiles_state,
                "floors": floor_names,
                "room_catalog": room_catalog,
                "composite_catalog": composite_catalog,
                "global_catalog": global_catalog,
                "global_features": global_features,
                "global_context_usage": global_context_usage,
                "archive_status": _archive_status_from_options(hass),
                "integration_options": _integration_options_from_entry(hass),
                "tts_catalog": await _async_build_tts_catalog(hass),
                "asset_intelligence_connected": _is_asset_intelligence_connected(hass),
            }
        )
        response.headers["Cache-Control"] = "no-store"
        return response


class ConciergeTtsCatalogView(HomeAssistantView):
    """Expose provider-backed TTS capability metadata for Concierge room setup."""

    url = "/api/concierge/tts_catalog"
    name = "api:concierge:tts_catalog"
    requires_auth = True

    async def get(self, request):
        hass = request.app["hass"]
        response = web.json_response(await _async_build_tts_catalog(hass))
        response.headers["Cache-Control"] = "no-store"
        return response


class ConciergePanelVersionView(HomeAssistantView):
    """Expose active panel build token so stale clients can self-detect."""

    url = "/api/concierge/panel_version"
    name = "api:concierge:panel_version"
    requires_auth = True

    async def get(self, request):
        hass = request.app["hass"]
        domain_data = hass.data.setdefault(DOMAIN, {})
        build_info = domain_data.get(_BUILD_INFO_KEY)

        if not isinstance(build_info, dict) or not build_info.get("selected_panel"):
            raise web.HTTPServiceUnavailable(text="Panel build info unavailable")

        response = web.json_response(build_info)
        response.headers["Cache-Control"] = "no-store"
        return response


class ConciergeVoiceEnrollmentUploadView(HomeAssistantView):
    """Accept authenticated microphone uploads and store them on attached storage."""

    url = "/api/concierge/voice_enrollment_upload"
    name = "api:concierge:voice_enrollment_upload"
    requires_auth = True

    async def post(self, request):
        hass = request.app["hass"]

        try:
            reader = await request.multipart()
        except Exception as err:
            raise web.HTTPBadRequest(text=f"Invalid multipart payload: {err}") from err

        fields: dict[str, str] = {}
        audio_bytes = b""
        audio_content_type = "application/octet-stream"

        while True:
            part = await reader.next()
            if part is None:
                break
            if part.name == "audio":
                audio_content_type = str(part.headers.get("Content-Type", "application/octet-stream"))
                audio_bytes = await part.read(decode=False)
            else:
                fields[part.name] = await part.text()

        person_id = str(fields.get("person_id", "") or "").strip()
        voice_profile_id = str(fields.get("voice_profile_id", "") or "").strip()
        phrase_index_raw = str(fields.get("phrase_index", "0") or "0").strip()

        if not person_id:
            raise web.HTTPBadRequest(text="person_id is required")
        if not voice_profile_id:
            raise web.HTTPBadRequest(text="voice_profile_id is required")
        if not audio_bytes:
            raise web.HTTPBadRequest(text="audio file is required")

        try:
            phrase_index = max(0, int(phrase_index_raw))
        except ValueError as err:
            raise web.HTTPBadRequest(text="phrase_index must be an integer") from err

        try:
            root_path = _voice_storage_root_from_hass(hass)
        except ValueError as err:
            raise web.HTTPPreconditionFailed(text=str(err)) from err

        destination = await hass.async_add_executor_job(
            lambda: _write_voice_sample_bytes(
                root_path=root_path,
                person_id=person_id,
                voice_profile_id=voice_profile_id,
                phrase_index=phrase_index,
                content_type=audio_content_type,
                payload=audio_bytes,
            )
        )

        response = web.json_response(
            {
                "saved": True,
                "recording_path": str(destination).replace("\\", "/"),
                "recording_mime_type": audio_content_type,
                "recording_size_bytes": len(audio_bytes),
                "phrase_index": phrase_index,
            }
        )
        response.headers["Cache-Control"] = "no-store"
        return response


def _resolve_panel_asset(frontend_dir: str, panel_candidates: list[str]) -> tuple[str, str]:
    selected_panel = next(
        (
            name
            for name in panel_candidates
            if os.path.exists(os.path.join(frontend_dir, name))
        ),
        panel_candidates[0] if panel_candidates else "panel.js",
    )

    panel_js_path = os.path.join(frontend_dir, selected_panel)
    try:
        cache_token = str(int(os.path.getmtime(panel_js_path)))
    except (OSError, ValueError):
        cache_token = "1"

    return selected_panel, cache_token


async def async_setup_panel(hass):
    """Register Concierge frontend panel."""

    domain_data = hass.data.setdefault(DOMAIN, {})

    frontend_dir = hass.config.path("custom_components/concierge/frontend")
    selected_panel, cache_token = await hass.async_add_executor_job(
        _resolve_panel_asset,
        frontend_dir,
        ["panel.js"],
    )
    domain_data[_BUILD_INFO_KEY] = {
        "selected_panel": selected_panel,
        "cache_token": cache_token,
    }

    if not domain_data.get(_STATIC_REGISTERED_FLAG):
        try:
            await hass.http.async_register_static_paths(
                [
                    StaticPathConfig(
                        url_path="/concierge-static",
                        path=frontend_dir,
                        cache_headers=False,
                    ),
                    StaticPathConfig(
                        url_path="/concierge-brand",
                        path=hass.config.path("custom_components/concierge/brand"),
                        cache_headers=False,
                    ),
                ]
            )
            domain_data[_STATIC_REGISTERED_FLAG] = True
        except Exception:
            _LOGGER.exception("Concierge: failed registering panel static paths")
            return

    if not domain_data.get(_SNAPSHOT_VIEW_REGISTERED_FLAG):
        try:
            hass.http.register_view(ConciergeStorageSnapshotView())
            domain_data[_SNAPSHOT_VIEW_REGISTERED_FLAG] = True
        except Exception:
            _LOGGER.exception("Concierge: failed registering panel snapshot view")
            return

    if not domain_data.get(_TTS_CATALOG_VIEW_REGISTERED_FLAG):
        try:
            hass.http.register_view(ConciergeTtsCatalogView())
            domain_data[_TTS_CATALOG_VIEW_REGISTERED_FLAG] = True
        except Exception:
            _LOGGER.exception("Concierge: failed registering panel TTS catalog view")
            return

    if not domain_data.get(_VOICE_UPLOAD_VIEW_REGISTERED_FLAG):
        try:
            hass.http.register_view(ConciergeVoiceEnrollmentUploadView())
            domain_data[_VOICE_UPLOAD_VIEW_REGISTERED_FLAG] = True
        except Exception:
            _LOGGER.exception("Concierge: failed registering panel voice upload view")
            return

    if not domain_data.get(_VERSION_VIEW_REGISTERED_FLAG):
        try:
            hass.http.register_view(ConciergePanelVersionView())
            domain_data[_VERSION_VIEW_REGISTERED_FLAG] = True
        except Exception:
            _LOGGER.exception("Concierge: failed registering panel version view")
            return

    if domain_data.get(_PANEL_REGISTERED_FLAG):
        return

    try:
        async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title="Concierge",
            sidebar_icon="mdi:home-account",
            frontend_url_path="concierge",
            require_admin=False,
            config={
                "_panel_custom": {
                    "name": "concierge-app",
                    "js_url": f"/concierge-static/{selected_panel}?v={cache_token}",
                    "embed_iframe": False,
                }
            },
        )
        domain_data[_PANEL_REGISTERED_FLAG] = True
    except Exception:
        _LOGGER.exception("Concierge: failed registering frontend panel")
