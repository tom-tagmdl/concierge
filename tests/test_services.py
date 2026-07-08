"""Tests for Concierge contract-first services."""

from __future__ import annotations

import pytest

from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import floor_registry as fr
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


async def test_person_profile_service_persists_bindings(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Person profile service should persist consent and device binding state."""
    from custom_components.concierge.storage import ConciergeStorage

    result = await hass.services.async_call(
        DOMAIN,
        "update_person_profile",
        {
            "person_id": "tom",
            "name": "Tom",
            "linked_area_id": "living_room",
            "ble_device_ids": ["ble.tom_tag"],
            "aqara_presence_entity_ids": ["binary_sensor.tom_presence"],
            "voice_profile_id": "tom_voice",
            "consent": {"person_identity": True},
            "notes": "Primary person profile",
            "set_as_default": True,
        },
        blocking=True,
        return_response=True,
    )

    state = await ConciergeStorage(hass).async_load_state()
    profile = state.person_profiles["tom"]
    assert result["person_profile_count"] == 1
    assert profile.linked_area_id == "living_room"
    assert profile.ble_device_ids == ["ble.tom_tag"]
    assert profile.voice_profile_id == "tom_voice"
    assert state.default_person_profile is not None
    assert state.default_person_profile.person_id == "tom"


async def test_voice_profile_service_persists_enrollment(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Voice profile service should persist voice enrollment state."""
    from custom_components.concierge.storage import ConciergeStorage

    result = await hass.services.async_call(
        DOMAIN,
        "update_voice_profile",
        {
            "voice_profile_id": "tom_voice",
            "name": "Tom Voice",
            "tts_voice": "alloy",
            "enrollment_state": "trained",
            "enrollment_source": "local",
            "speaker_embedding_id": "embedding-1",
            "sample_count": 4,
            "consent": {"voice_training": True},
            "set_as_default": True,
        },
        blocking=True,
        return_response=True,
    )

    state = await ConciergeStorage(hass).async_load_state()
    profile = state.voice_profiles["tom_voice"]
    assert result["voice_profile_count"] == 1
    assert profile.tts_voice == "alloy"
    assert profile.enrollment_state == "trained"
    assert profile.sample_count == 4
    assert state.default_voice_profile is not None
    assert state.default_voice_profile.voice_profile_id == "tom_voice"


async def test_voice_enrollment_lifecycle_services_round_trip(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Voice enrollment lifecycle services should persist deterministic state transitions."""
    from custom_components.concierge.storage import ConciergeStorage

    await hass.services.async_call(
        DOMAIN,
        "update_person_profile",
        {
            "person_id": "tom",
            "name": "Tom Grounds",
        },
        blocking=True,
    )

    started = await hass.services.async_call(
        DOMAIN,
        "start_voice_enrollment",
        {
            "person_id": "tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "consent_acknowledged": True,
            "local_only": True,
        },
        blocking=True,
        return_response=True,
    )
    assert started["started"] is True
    assert started["voice_profile_id"] == "tom_voice"

    first_capture = await hass.services.async_call(
        DOMAIN,
        "capture_voice_enrollment_sample",
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Hello Concierge, test phrase one.",
            "phrase_index": 0,
        },
        blocking=True,
        return_response=True,
    )
    second_capture = await hass.services.async_call(
        DOMAIN,
        "capture_voice_enrollment_sample",
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Hello Concierge, test phrase two.",
            "phrase_index": 1,
        },
        blocking=True,
        return_response=True,
    )
    third_capture = await hass.services.async_call(
        DOMAIN,
        "capture_voice_enrollment_sample",
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Hello Concierge, test phrase three.",
            "phrase_index": 2,
        },
        blocking=True,
        return_response=True,
    )
    assert first_capture["captured"] is True
    assert second_capture["captured"] is True
    assert third_capture["sample_count"] == 3

    removed = await hass.services.async_call(
        DOMAIN,
        "remove_voice_enrollment_sample",
        {
            "voice_profile_id": "tom_voice",
            "sample_id": first_capture["sample_id"],
        },
        blocking=True,
        return_response=True,
    )
    assert removed["removed"] is True
    assert removed["sample_count"] == 2

    built = await hass.services.async_call(
        DOMAIN,
        "build_voice_profile",
        {
            "voice_profile_id": "tom_voice",
            "person_id": "tom",
            "min_samples": 2,
        },
        blocking=True,
        return_response=True,
    )
    assert built["built"] is True
    assert built["sample_count"] == 2
    assert built["person_id"] == "tom"

    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    assert state.voice_profiles["tom_voice"].enrollment_state == "trained"
    assert state.person_profiles["tom"].voice_profile_id == "tom_voice"

    reset = await hass.services.async_call(
        DOMAIN,
        "reset_voice_profile",
        {
            "voice_profile_id": "tom_voice",
            "preserve_consent": True,
        },
        blocking=True,
        return_response=True,
    )
    assert reset["reset"] is True

    reset_state = await storage.async_load_state()
    assert reset_state.voice_profiles["tom_voice"].sample_count == 0
    assert reset_state.voice_profiles["tom_voice"].enrollment_state == "untrained"

    deleted = await hass.services.async_call(
        DOMAIN,
        "delete_voice_profile",
        {
            "voice_profile_id": "tom_voice",
            "unlink_from_people": True,
        },
        blocking=True,
        return_response=True,
    )
    assert deleted["deleted"] is True

    final_state = await storage.async_load_state()
    assert "tom_voice" not in final_state.voice_profiles
    assert final_state.person_profiles["tom"].voice_profile_id is None


async def test_start_voice_enrollment_fails_closed_when_storage_unavailable(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Preflight failure should block session creation before enrollment starts."""
    from types import SimpleNamespace

    from custom_components.concierge import services as services_module
    from custom_components.concierge.storage import ConciergeStorage

    await hass.services.async_call(
        DOMAIN,
        "update_person_profile",
        {
            "person_id": "tom",
            "name": "Tom Grounds",
        },
        blocking=True,
    )

    fake_provider = SimpleNamespace(
        validate_ready=lambda: SimpleNamespace(
            ready=False,
            failure_code="storage_unavailable",
            failure_message_safe="external enrollment storage is unavailable",
            provider_type="mounted_path",
        )
    )
    monkeypatch.setattr(services_module, "_voice_storage_provider_from_hass", lambda hass: fake_provider)

    with pytest.raises(Exception, match="storage_unavailable"):
        await hass.services.async_call(
            DOMAIN,
            "start_voice_enrollment",
            {
                "person_id": "tom",
                "voice_profile_id": "tom_voice",
                "voice_name": "Tom Voice",
                "consent_acknowledged": True,
                "local_only": True,
            },
            blocking=True,
            return_response=True,
        )

    state = await ConciergeStorage(hass).async_load_state()
    assert state.enrollment_sessions == {}


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


async def test_update_composite_config_same_floor_rename_and_dismantle(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Composite service should support same-floor merge, rename, and dismantle."""
    from custom_components.concierge.storage import ConciergeStorage

    floor_registry = fr.async_get(hass)
    main_floor = floor_registry.async_create(name="Main")

    area_registry = ar.async_get(hass)
    kitchen = area_registry.async_create(name="Kitchen", floor_id=main_floor.floor_id)
    dining = area_registry.async_create(name="Dining", floor_id=main_floor.floor_id)
    living = area_registry.async_create(name="Living", floor_id=main_floor.floor_id)

    created = await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "upstairs_public_space",
            "name": "Upstairs Public Space",
            "area_ids": [kitchen.id, dining.id, living.id],
            "primary_area": kitchen.id,
        },
        blocking=True,
        return_response=True,
    )
    assert created["dismantled"] is False
    assert created["area_count"] == 3

    renamed = await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "upstairs_public_space",
            "name": "Main Public Space",
            "area_ids": [kitchen.id, living.id],
            "primary_area": living.id,
        },
        blocking=True,
        return_response=True,
    )
    assert renamed["dismantled"] is False
    assert renamed["area_count"] == 2

    state = await ConciergeStorage(hass).async_load_state()
    composite = state.composites["upstairs_public_space"]
    assert composite.name == "Main Public Space"
    assert composite.area_ids == [kitchen.id, living.id]
    assert composite.primary_area == living.id

    dismantled = await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "upstairs_public_space",
            "area_ids": [],
        },
        blocking=True,
        return_response=True,
    )
    assert dismantled["dismantled"] is True

    post = await ConciergeStorage(hass).async_load_state()
    assert "upstairs_public_space" not in post.composites


async def test_update_composite_config_rejects_cross_floor_membership(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Composite service must reject area lists that span multiple floors."""
    floor_registry = fr.async_get(hass)
    first_floor = floor_registry.async_create(name="First")
    second_floor = floor_registry.async_create(name="Second")

    area_registry = ar.async_get(hass)
    kitchen = area_registry.async_create(name="Kitchen", floor_id=first_floor.floor_id)
    bedroom = area_registry.async_create(name="Bedroom", floor_id=second_floor.floor_id)

    with pytest.raises(Exception, match="same floor"):
        await hass.services.async_call(
            DOMAIN,
            "update_composite_config",
            {
                "composite_id": "invalid_composite",
                "name": "Invalid Composite",
                "area_ids": [kitchen.id, bedroom.id],
            },
            blocking=True,
        )


async def test_sync_composites_removes_invalid_members(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Sync composites should remove missing area members and dismantle empty composites."""
    from custom_components.concierge.storage import ConciergeStorage

    floor_registry = fr.async_get(hass)
    main_floor = floor_registry.async_create(name="Main")
    area_registry = ar.async_get(hass)
    kitchen = area_registry.async_create(name="Kitchen", floor_id=main_floor.floor_id)

    storage = ConciergeStorage(hass)
    await storage.async_update_composite_config(
        composite_id="test_composite",
        name="Test Composite",
        area_ids=[kitchen.id, "missing_area"],
        primary_area=kitchen.id,
    )

    result = await hass.services.async_call(
        DOMAIN,
        "sync_composites",
        {"remove_invalid": True},
        blocking=True,
        return_response=True,
    )
    assert result["synced"] is True
    assert result["validation_errors"]

    state = await storage.async_load_state()
    assert "test_composite" in state.composites
    assert state.composites["test_composite"].area_ids == [kitchen.id]

    # If the only valid area disappears, sync should dismantle the composite.
    area_registry.async_delete(kitchen.id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        "sync_composites",
        {"remove_invalid": True},
        blocking=True,
        return_response=True,
    )
    state_after = await storage.async_load_state()
    assert "test_composite" not in state_after.composites


async def test_update_composite_config_persists_and_prunes_selected_entities(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Composite selections should persist and prune entities from removed member rooms."""
    from custom_components.concierge.storage import ConciergeStorage

    floor_registry = fr.async_get(hass)
    main_floor = floor_registry.async_create(name="Main")

    area_registry = ar.async_get(hass)
    kitchen = area_registry.async_create(name="Kitchen", floor_id=main_floor.floor_id)
    dining = area_registry.async_create(name="Dining", floor_id=main_floor.floor_id)

    entity_registry = er.async_get(hass)
    kitchen_light = entity_registry.async_get_or_create(
        "light",
        DOMAIN,
        "kitchen_light",
        area_id=kitchen.id,
    )
    dining_light = entity_registry.async_get_or_create(
        "light",
        DOMAIN,
        "dining_light",
        area_id=dining.id,
    )

    await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "public_space",
            "name": "Public Space",
            "area_ids": [kitchen.id, dining.id],
            "light_entity_ids": [kitchen_light.entity_id, dining_light.entity_id],
        },
        blocking=True,
    )

    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()
    assert state.composites["public_space"].light_entity_ids == [
        kitchen_light.entity_id,
        dining_light.entity_id,
    ]

    await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "public_space",
            "area_ids": [kitchen.id],
        },
        blocking=True,
    )

    updated = await storage.async_load_state()
    assert updated.composites["public_space"].light_entity_ids == [kitchen_light.entity_id]


async def test_sync_composites_prunes_stale_selected_entities(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Sync composites should remove selected entities no longer scoped to member areas."""
    from custom_components.concierge.storage import ConciergeStorage

    floor_registry = fr.async_get(hass)
    main_floor = floor_registry.async_create(name="Main")

    area_registry = ar.async_get(hass)
    kitchen = area_registry.async_create(name="Kitchen", floor_id=main_floor.floor_id)
    den = area_registry.async_create(name="Den", floor_id=main_floor.floor_id)

    entity_registry = er.async_get(hass)
    kitchen_light = entity_registry.async_get_or_create(
        "light",
        DOMAIN,
        "sync_kitchen_light",
        area_id=kitchen.id,
    )
    den_light = entity_registry.async_get_or_create(
        "light",
        DOMAIN,
        "sync_den_light",
        area_id=den.id,
    )

    await hass.services.async_call(
        DOMAIN,
        "update_composite_config",
        {
            "composite_id": "sync_test",
            "name": "Sync Test",
            "area_ids": [kitchen.id, den.id],
            "light_entity_ids": [kitchen_light.entity_id, den_light.entity_id],
        },
        blocking=True,
    )

    area_registry.async_delete(den.id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        "sync_composites",
        {"remove_invalid": True},
        blocking=True,
        return_response=True,
    )

    state = await ConciergeStorage(hass).async_load_state()
    composite = state.composites["sync_test"]
    assert composite.area_ids == [kitchen.id]
    assert composite.light_entity_ids == [kitchen_light.entity_id]


async def test_update_global_context_records_activity_timeline(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Global context mutations should emit backend activity timeline entries."""
    await hass.services.async_call(
        DOMAIN,
        "update_global_context",
        {
            "context_type": "weather",
            "enabled": True,
            "summary": "Sunny",
            "detail": "High of 82",
            "speakable": "Sunny and warm",
        },
        blocking=True,
    )

    timeline = await hass.services.async_call(
        DOMAIN,
        "get_activity_timeline",
        {},
        blocking=True,
        return_response=True,
    )
    activities = timeline.get("activities", [])
    assert any(
        item.get("intent_class") == "update_global_context"
        and item.get("outcome") == "success"
        for item in activities
    )


async def test_execute_records_success_activity(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Execute service should emit successful backend activity entries."""
    await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "light.kitchen",
            "area_id": "living_room",
            "intent_class": "home_control",
        },
        blocking=True,
        return_response=True,
    )

    timeline = await hass.services.async_call(
        DOMAIN,
        "get_activity_timeline",
        {"area_id": "living_room"},
        blocking=True,
        return_response=True,
    )
    activities = timeline.get("activities", [])
    assert any(
        item.get("intent_class") == "execute_orchestration"
        and item.get("outcome") == "success"
        for item in activities
    )


async def test_execute_direct_records_policy_denied_activity(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Policy-denied execution should still be captured in backend activity timeline."""
    await hass.services.async_call(
        DOMAIN,
        "update_person_profile",
        {
            "person_id": "minor_1",
            "name": "Minor",
            "is_minor": True,
            "minor_allowed_intent_classes": ["media_only"],
            "minor_allow_general_qna": False,
        },
        blocking=True,
    )

    with pytest.raises(Exception, match="minor_policy_denied"):
        await hass.services.async_call(
            DOMAIN,
            "execute_direct",
            {
                "entity_id": "light.den",
                "service": "homeassistant.turn_on",
                "person_id": "minor_1",
                "intent_class": "home_control",
            },
            blocking=True,
            return_response=True,
        )

    timeline = await hass.services.async_call(
        DOMAIN,
        "get_activity_timeline",
        {"person_id": "minor_1"},
        blocking=True,
        return_response=True,
    )
    activities = timeline.get("activities", [])
    assert any(
        item.get("intent_class") == "execute_direct"
        and item.get("outcome") == "policy_denied"
        for item in activities
    )


async def test_update_room_config_records_activity_with_room_scope(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Room setup mutations should be backend-logged in activity timeline."""
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {
            "area_id": "living_room",
            "voice_device_entity_ids": [
                "assist_satellite.home_assistant_voice_0a87d9_assist_satellite"
            ],
        },
        blocking=True,
    )

    timeline = await hass.services.async_call(
        DOMAIN,
        "get_activity_timeline",
        {"area_id": "living_room"},
        blocking=True,
        return_response=True,
    )
    activities = timeline.get("activities", [])
    assert any(
        item.get("intent_class") == "room_config_update"
        and item.get("outcome") == "success"
        and item.get("resolved_area_id") == "living_room"
        for item in activities
    )


async def test_update_person_profile_records_activity_with_person_scope(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Person setup mutations should be backend-logged in activity timeline."""
    await hass.services.async_call(
        DOMAIN,
        "update_person_profile",
        {
            "person_id": "tom",
            "name": "Tom",
            "linked_area_id": "living_room",
            "ble_device_ids": [],
            "aqara_presence_entity_ids": [],
            "minor_allowed_intent_classes": ["room_context_info"],
            "minor_allow_general_qna": False,
        },
        blocking=True,
    )

    timeline = await hass.services.async_call(
        DOMAIN,
        "get_activity_timeline",
        {"person_id": "tom"},
        blocking=True,
        return_response=True,
    )
    activities = timeline.get("activities", [])
    assert any(
        item.get("intent_class") == "update_person_profile"
        and item.get("outcome") == "success"
        and item.get("resolved_person_id") == "tom"
        for item in activities
    )
