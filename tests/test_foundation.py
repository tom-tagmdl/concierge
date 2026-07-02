"""Tests for Concierge state storage and coordinator summary."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.concierge.const import DOMAIN
from custom_components.concierge.models import ContextState, IdentityProfile, Interaction, PersonProfile, SignalState, VoiceProfile
from custom_components.concierge.storage import ConciergeStorage


async def test_foundation_defaults_created(hass: HomeAssistant) -> None:
    """Storage should create deterministic empty state on first load."""
    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()

    assert state.rooms == {}
    assert state.composites == {}
    assert state.signals == {}
    assert state.contexts == {}
    assert state.interactions == {}


async def test_foundation_summary_available_in_coordinator(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Coordinator should expose persisted state summary in runtime data."""
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(
        area_id="great_room",
        aliases={"movie time": "scene.movie_mode"},
        global_overlays={"weather": True},
    )
    await storage.async_upsert_interaction(
        Interaction(
            interaction_id="i-1",
            area_id="great_room",
            message="Door left open",
            level="attention",
            state="active",
            priority=60,
        )
    )
    await storage.async_upsert_signal(
        SignalState(
            signal_type="laundry",
            available=True,
            summary="Laundry complete",
            state="active",
        )
    )
    await storage.async_upsert_context(
        ContextState(
            context_type="weather",
            available=True,
            summary="Sunny",
            detail="Warm afternoon",
            speakable="It is sunny.",
        )
    )

    entry = setup_integration
    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_request_refresh()

    summary = coordinator.data["foundation_summary"]
    assert summary["room_count"] == 1
    assert summary["interaction_count"] == 1
    assert summary["signal_count"] == 1
    assert summary["context_source_count"] == 1


async def test_room_and_identity_state_round_trip(hass: HomeAssistant) -> None:
    """State storage should persist room posture, people, voice, and presentation profiles."""
    storage = ConciergeStorage(hass)
    await storage.async_update_room_config(
        area_id="great_room",
        posture="sleep",
        media_player_entity_ids=["media_player.great_room"],
        tts_voice="sage",
    )
    await storage.async_update_identity_profile(
        IdentityProfile(
            profile_id="default",
            name="Default",
            persona="concise",
            tts_voice="alloy",
            verbosity="standard",
            allow_ai=True,
            content_type="general",
            detail_level="medium",
        ),
        set_as_default=True,
    )
    await storage.async_update_person_profile(
        PersonProfile(
            person_id="tom",
            name="Tom",
            linked_area_id="great_room",
            ble_device_ids=["ble.tom_tag"],
            aqara_presence_entity_ids=["binary_sensor.tom_presence"],
            voice_profile_id="tom_voice",
            consent={"person_identity": True},
            notes="Primary person profile",
        ),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            tts_voice="alloy",
            enrollment_state="trained",
            enrollment_source="local",
            speaker_embedding_id="embedding-1",
            sample_count=4,
            consent={"voice_training": True},
        ),
        set_as_default=True,
    )

    state = await storage.async_load_state()
    assert state.rooms["great_room"].posture == "sleep"
    assert state.rooms["great_room"].media_player_entity_ids == ["media_player.great_room"]
    assert state.default_identity_profile is not None
    assert state.default_identity_profile.tts_voice == "alloy"
    assert state.default_person_profile is not None
    assert state.default_person_profile.voice_profile_id == "tom_voice"
    assert state.default_voice_profile is not None
    assert state.default_voice_profile.sample_count == 4
