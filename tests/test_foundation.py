"""Tests for Concierge state storage and coordinator summary."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.concierge.const import DOMAIN
from custom_components.concierge.models import ContextState, IdentityProfile, Interaction, SignalState
from custom_components.concierge.storage import ConciergeStorage


async def test_foundation_defaults_created(hass: HomeAssistant) -> None:
    """Storage should create deterministic empty state on first load."""
    storage = ConciergeStorage(hass)
    state = await storage.async_load_state()

    assert state.rooms == {}
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
    """State storage should persist room posture/media targets and identity profiles."""
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

    state = await storage.async_load_state()
    assert state.rooms["great_room"].posture == "sleep"
    assert state.rooms["great_room"].media_player_entity_ids == ["media_player.great_room"]
    assert state.default_identity_profile is not None
    assert state.default_identity_profile.tts_voice == "alloy"
