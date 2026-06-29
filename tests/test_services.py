"""Tests for Concierge contract-first services."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.concierge.const import DOMAIN


async def test_interaction_services_round_trip(hass: HomeAssistant, setup_integration) -> None:
    """Interaction service endpoints should support update/get/clear flows."""
    await hass.services.async_call(
        DOMAIN,
        "update_interaction",
        {
            "interaction_id": "int-1",
            "area_id": "living_room",
            "message": "Laundry is done",
            "level": "attention",
            "state": "active",
            "priority": 90,
        },
        blocking=True,
    )

    result = await hass.services.async_call(
        DOMAIN,
        "get_interactions",
        {"area_id": "living_room"},
        blocking=True,
        return_response=True,
    )
    assert len(result["interactions"]) == 1
    assert result["interactions"][0]["interaction_id"] == "int-1"

    await hass.services.async_call(
        DOMAIN,
        "clear_interaction",
        {"interaction_id": "int-1"},
        blocking=True,
    )

    cleared = await hass.services.async_call(
        DOMAIN,
        "get_interactions",
        {"area_id": "living_room"},
        blocking=True,
        return_response=True,
    )
    assert cleared["interactions"] == []


async def test_context_and_summary_services(hass: HomeAssistant, setup_integration) -> None:
    """Context updates should be retrievable and included in summary output."""
    await hass.services.async_call(
        DOMAIN,
        "update_global_context",
        {
            "context_type": "weather",
            "enabled": True,
            "summary": "Partly cloudy, 85 degrees",
            "detail": "High of 92, low of 75",
            "speakable": "It is currently partly cloudy and 85 degrees.",
        },
        blocking=True,
    )

    context = await hass.services.async_call(
        DOMAIN,
        "get_context",
        {"context_type": "weather"},
        blocking=True,
        return_response=True,
    )
    assert context["context"] is not None
    assert context["context"]["summary"] == "Partly cloudy, 85 degrees"

    summary = await hass.services.async_call(
        DOMAIN,
        "get_summary",
        {"include_context": True, "include_signals": False},
        blocking=True,
        return_response=True,
    )
    assert "Partly cloudy, 85 degrees" in summary["summary"]


async def test_room_config_service_persists_posture_and_media_targets(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Room config service should persist playback targets and posture."""
    from custom_components.concierge.storage import ConciergeStorage

    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": "living_room",
            "posture": "night",
            "media_player_entity_ids": ["media_player.living_room_sonos_2"],
            "tts_voice": "alloy",
            "aliases": {"movie time": "scene.movie_time"},
            "global_overlays": {"weather": True},
        },
        blocking=True,
    )

    state = await ConciergeStorage(hass).async_load_state()
    room = state.rooms["living_room"]
    assert room.posture == "night"
    assert room.media_player_entity_ids == ["media_player.living_room_sonos_2"]
    assert room.tts_voice == "alloy"


async def test_room_config_service_persists_voice_devices(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Room config service should persist room voice assistant bindings."""
    from custom_components.concierge.storage import ConciergeStorage

    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": "den",
            "voice_device_entity_ids": [
                "assist_satellite.home_assistant_voice_0a87d9_assist_satellite"
            ],
        },
        blocking=True,
    )

    state = await ConciergeStorage(hass).async_load_state()
    assert state.rooms["den"].voice_device_entity_ids == [
        "assist_satellite.home_assistant_voice_0a87d9_assist_satellite"
    ]


async def test_identity_profile_service_persists_default_profile(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Identity profile service should persist user-facing presentation preferences."""
    from custom_components.concierge.storage import ConciergeStorage

    result = await hass.services.async_call(
        DOMAIN,
        "update_identity_profile",
        {
            "profile_id": "tom",
            "name": "Tom",
            "persona": "technical",
            "tts_voice": "coral",
            "verbosity": "detailed",
            "allow_ai": True,
            "content_type": "technical",
            "detail_level": "high",
            "set_as_default": True,
        },
        blocking=True,
        return_response=True,
    )

    state = await ConciergeStorage(hass).async_load_state()
    profile = state.identity_profiles["tom"]
    assert result["identity_profile_count"] == 1
    assert profile.persona == "technical"
    assert profile.tts_voice == "coral"
    assert state.default_identity_profile is not None
    assert state.default_identity_profile.profile_id == "tom"


async def test_sync_rooms_service_reports_success(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Sync rooms service should complete and report room synchronization status."""
    result = await hass.services.async_call(
        DOMAIN,
        "sync_rooms",
        {
            "add_missing": True,
            "remove_missing": False,
        },
        blocking=True,
        return_response=True,
    )

    assert result["synced"] is True
    assert "room_count" in result
