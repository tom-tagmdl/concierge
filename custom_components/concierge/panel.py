from __future__ import annotations

import logging
import os
from typing import Any
from aiohttp import web

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.components.http import HomeAssistantView, StaticPathConfig
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
    floor_registry as fr,
)

from .const import DOMAIN
from .storage import ConciergeStorage

_LOGGER = logging.getLogger(__name__)
_PANEL_REGISTERED_FLAG = "_panel_registered"
_STATIC_REGISTERED_FLAG = "_panel_static_registered"
_SNAPSHOT_VIEW_REGISTERED_FLAG = "_panel_snapshot_view_registered"
_BUILD_INFO_KEY = "_panel_build_info"

_ASSET_INTELLIGENCE_DOMAIN = "asset_intelligence"


def _entity_name(entry: er.RegistryEntry) -> str:
    """Return best available display name for a registry entity entry."""
    if entry.name:
        return entry.name
    if entry.original_name:
        return entry.original_name
    object_id = entry.entity_id.split(".", 1)[1] if "." in entry.entity_id else entry.entity_id
    return " ".join(part.capitalize() for part in object_id.split("_") if part)


def _to_entity_row(entry: er.RegistryEntry) -> dict[str, str]:
    """Project a registry entry into a stable entity row payload."""
    return {
        "entity_id": entry.entity_id,
        "name": _entity_name(entry),
        "domain": entry.entity_id.split(".", 1)[0],
    }


def _build_room_entity_catalog(hass, area_ids: set[str]) -> dict[str, dict[str, list[dict[str, str]]]]:
    """Build categorized entity catalogs for each room/area."""
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    catalog: dict[str, dict[str, list[er.RegistryEntry]]] = {
        area_id: {
            "asset_entity_ids": [],
            "room_sensor_entity_ids": [],
            "room_health_entity_ids": [],
            "human_health_entity_ids": [],
            "light_entity_ids": [],
            "shade_entity_ids": [],
            "speaker_entity_ids": [],
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
        if platform == _ASSET_INTELLIGENCE_DOMAIN:
            room_bucket["asset_entity_ids"].append(entry)
        if is_room_sensor:
            room_bucket["room_sensor_entity_ids"].append(entry)
        if is_ai_assessment and ("room_health" in object_id or "environment_health" in object_id):
            room_bucket["room_health_entity_ids"].append(entry)
        if is_ai_assessment and ("human_health" in object_id or "occupant_health" in object_id):
            room_bucket["human_health_entity_ids"].append(entry)
        if domain == "light":
            room_bucket["light_entity_ids"].append(entry)
        if domain == "cover":
            room_bucket["shade_entity_ids"].append(entry)
        if domain == "media_player":
            room_bucket["speaker_entity_ids"].append(entry)
        if domain == "assist_satellite":
            room_bucket["voice_device_entity_ids"].append(entry)
        if "dashboard" in object_id:
            room_bucket["dashboard_entity_ids"].append(entry)

        if not (
            platform == _ASSET_INTELLIGENCE_DOMAIN
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
            result[area_id][key] = [_to_entity_row(item) for item in ordered]

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

    return {
        "weather_entity_ids": [_to_entity_row(item) for item in sorted(weather_rows, key=lambda item: _entity_name(item).lower())],
        "news_entity_ids": [_to_entity_row(item) for item in sorted(news_rows, key=lambda item: _entity_name(item).lower())],
        "alarm_entity_ids": [_to_entity_row(item) for item in sorted(alarm_rows, key=lambda item: _entity_name(item).lower())],
    }


def _is_asset_intelligence_connected(hass) -> bool:
    """Determine whether Asset Intelligence is installed and currently loaded."""
    entries = hass.config_entries.async_entries(_ASSET_INTELLIGENCE_DOMAIN)
    return any(entry.state is ConfigEntryState.LOADED for entry in entries)


def _humanize_floor_id(floor_id: str | None) -> str:
    """Convert floor slug to readable label when registry name is unavailable."""
    if not floor_id:
        return "Unassigned"
    return " ".join(part.capitalize() for part in floor_id.split("_") if part)


class ConciergeStorageSnapshotView(HomeAssistantView):
    """Expose Concierge + area snapshot for fast frontend bootstrap."""

    url = "/api/concierge/storage_snapshot"
    name = "api:concierge:storage_snapshot"
    requires_auth = True

    async def get(self, request):
        hass = request.app["hass"]

        rooms_state: dict = {}
        global_features: dict[str, dict[str, Any]] = {}
        global_context_usage: dict[str, dict[str, Any]] = {}
        try:
            state = await ConciergeStorage(hass).async_load_state()
            rooms_state = {
                area_id: {
                    "area_id": room.area_id,
                    "aliases": room.aliases,
                    "global_overlays": room.global_overlays,
                    "posture": room.posture,
                    "media_player_entity_ids": room.media_player_entity_ids,
                    "voice_device_entity_ids": room.voice_device_entity_ids,
                    "tts_voice": room.tts_voice,
                    "asset_entity_ids": room.asset_entity_ids,
                    "room_sensor_entity_ids": room.room_sensor_entity_ids,
                    "room_health_entity_ids": room.room_health_entity_ids,
                    "human_health_entity_ids": room.human_health_entity_ids,
                    "light_entity_ids": room.light_entity_ids,
                    "shade_entity_ids": room.shade_entity_ids,
                    "speaker_entity_ids": room.speaker_entity_ids,
                    "dashboard_entity_ids": room.dashboard_entity_ids,
                    "other_entity_ids": room.other_entity_ids,
                    "persona": room.persona,
                    "persona_prompt": room.persona_prompt,
                }
                for area_id, room in state.rooms.items()
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
                "floors": floor_names,
                "room_catalog": room_catalog,
                "global_catalog": global_catalog,
                "global_features": global_features,
                "global_context_usage": global_context_usage,
                "asset_intelligence_connected": _is_asset_intelligence_connected(hass),
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
