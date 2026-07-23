"""Unit tests for the Experience Continuity preference resolution hierarchy."""

from __future__ import annotations

import pytest

from custom_components.concierge.models import ContinuityConfidenceBand
from custom_components.concierge.models import PreferenceIdentityState
from custom_components.concierge.models import PreferenceResolutionRequest
from custom_components.concierge.models import PreferenceResolutionTier
from custom_components.concierge.services import _resolve_preference_hierarchy


@pytest.fixture
def enable_custom_integrations() -> None:
    """Satisfy the shared test conftest autouse dependency for this standalone audit test."""
    return None


def _request(**overrides: object) -> PreferenceResolutionRequest:
    base = {
        "preference_key": "music_preference",
        "identity_state": PreferenceIdentityState.KNOWN,
        "confidence_band": ContinuityConfidenceBand.HIGH,
        "command_value": None,
        "guardrail_value": None,
        "person_preference_value": None,
        "person_room_exception_value": None,
        "room_default_value": "room-default",
        "household_default_value": "household-default",
        "system_safe_value": "system-safe",
        "person_room_exception_enabled": False,
        "personalization_policy_allowed": True,
        "personalization_policy_reason": "policy_allows",
        "metadata": {"source": "test"},
    }
    base.update(overrides)
    return PreferenceResolutionRequest(**base)


def test_command_and_guardrail_override_personalization() -> None:
    """Command intent and guardrails should outrank all downstream preference tiers."""
    command_result = _resolve_preference_hierarchy(
        _request(command_value="command-choice", person_preference_value="person-choice")
    )
    guardrail_result = _resolve_preference_hierarchy(
        _request(guardrail_value="guardrail-choice", person_preference_value="person-choice")
    )

    assert command_result.selected_tier is PreferenceResolutionTier.COMMAND
    assert command_result.selected_value == "command-choice"
    assert command_result.evaluation_path[0]["selected"] is True
    assert guardrail_result.selected_tier is PreferenceResolutionTier.GUARDRAIL
    assert guardrail_result.selected_value == "guardrail-choice"


def test_known_person_preference_beats_room_and_household_defaults() -> None:
    """Known-person preference should be portable across rooms unless a higher tier overrides it."""
    result = _resolve_preference_hierarchy(
        _request(person_preference_value="person-choice", room_default_value="room-default", household_default_value="household-default")
    )

    assert result.selected_tier is PreferenceResolutionTier.KNOWN_PERSON_PREFERENCE
    assert result.selected_scope == "person"
    assert result.selected_value == "person-choice"
    assert result.identity_decision["personalization_allowed"] is True


def test_explicit_person_room_exception_only_applies_when_enabled() -> None:
    """Person-plus-room preference should remain an explicit exception path."""
    enabled = _resolve_preference_hierarchy(
        _request(
            person_preference_value=None,
            person_room_exception_value="person-room-choice",
            person_room_exception_enabled=True,
            room_default_value="room-default",
        )
    )
    disabled = _resolve_preference_hierarchy(
        _request(
            person_preference_value=None,
            person_room_exception_value="person-room-choice",
            person_room_exception_enabled=False,
            room_default_value="room-default",
        )
    )

    assert enabled.selected_tier is PreferenceResolutionTier.EXPLICIT_PERSON_ROOM_EXCEPTION
    assert enabled.selected_scope == "person_room"
    assert enabled.selected_value == "person-room-choice"
    assert disabled.selected_tier is PreferenceResolutionTier.ROOM_DEFAULT
    assert disabled.selected_value == "room-default"
    assert disabled.fallback_reason == "person_room_exception_disabled"


@pytest.mark.parametrize(
    ("identity_state", "confidence_band", "expected_reason"),
    [
        (PreferenceIdentityState.GUEST, ContinuityConfidenceBand.HIGH, "guest_identity_blocked"),
        (PreferenceIdentityState.UNKNOWN, ContinuityConfidenceBand.HIGH, "unknown_identity_blocked"),
        (PreferenceIdentityState.UNAVAILABLE, ContinuityConfidenceBand.HIGH, "unavailable_identity_blocked"),
        (PreferenceIdentityState.LOW_CONFIDENCE, ContinuityConfidenceBand.LOW, "low_confidence_identity_blocked"),
    ],
)
def test_identity_fail_closed_uses_room_or_household_defaults(
    identity_state: PreferenceIdentityState,
    confidence_band: ContinuityConfidenceBand,
    expected_reason: str,
) -> None:
    """Restricted identity states should suppress personalized preference application."""
    result = _resolve_preference_hierarchy(
        _request(
            identity_state=identity_state,
            confidence_band=confidence_band,
            person_preference_value="person-choice",
            person_room_exception_value="person-room-choice",
            person_room_exception_enabled=True,
            room_default_value="room-default",
            household_default_value="household-default",
        )
    )

    assert result.identity_decision["personalization_allowed"] is False
    assert result.identity_decision["reason_code"] == expected_reason
    assert result.selected_tier is PreferenceResolutionTier.ROOM_DEFAULT
    assert result.selected_value == "room-default"
    assert result.fallback_reason == expected_reason


def test_household_and_system_fallbacks_are_deterministic() -> None:
    """When higher tiers are unavailable, household default should win before system-safe fallback."""
    household_result = _resolve_preference_hierarchy(
        _request(person_preference_value=None, room_default_value=None, household_default_value="household-default")
    )
    system_result = _resolve_preference_hierarchy(
        _request(
            person_preference_value=None,
            room_default_value=None,
            household_default_value=None,
            system_safe_value="system-safe",
        )
    )

    assert household_result.selected_tier is PreferenceResolutionTier.HOUSEHOLD_DEFAULT
    assert household_result.selected_scope == "household"
    assert household_result.selected_value == "household-default"
    assert system_result.selected_tier is PreferenceResolutionTier.SYSTEM_SAFE_DEFAULT
    assert system_result.selected_scope == "system"
    assert system_result.selected_value == "system-safe"


def test_policy_disallow_blocks_personalization_and_fails_closed() -> None:
    """Policy disallow should block personalization even when identity is known and confident."""
    result = _resolve_preference_hierarchy(
        _request(
            identity_state=PreferenceIdentityState.KNOWN,
            confidence_band=ContinuityConfidenceBand.HIGH,
            personalization_policy_allowed=False,
            personalization_policy_reason="privacy_opt_out",
            person_preference_value="person-choice",
            person_room_exception_value="person-room-choice",
            person_room_exception_enabled=True,
            room_default_value="room-default",
        )
    )

    assert result.selected_tier is PreferenceResolutionTier.ROOM_DEFAULT
    assert result.selected_value == "room-default"
    assert result.identity_decision["personalization_allowed"] is False
    assert result.identity_decision["policy_allowed"] is False
    assert result.identity_decision["policy_reason"] == "privacy_opt_out"
    assert result.identity_decision["reason_code"] == "identity_policy_disallowed"
    assert result.identity_decision["safety_mode"] == "fail_closed"
    assert result.fallback_reason == "identity_policy_disallowed"


def test_fail_closed_output_contains_selected_source_and_fallback_target_metadata() -> None:
    """Explainability metadata should include selected source and fail-closed fallback target."""
    result = _resolve_preference_hierarchy(
        _request(
            identity_state=PreferenceIdentityState.UNKNOWN,
            confidence_band=ContinuityConfidenceBand.HIGH,
            person_preference_value="person-choice",
            room_default_value="room-default",
        )
    )

    assert result.selected_tier is PreferenceResolutionTier.ROOM_DEFAULT
    assert result.metadata["selected_source"] == "room_default"
    assert result.metadata["fallback_target"] == "room_default"


def test_resolver_is_deterministic_for_identical_identity_inputs() -> None:
    """Identical identity and policy inputs should produce identical outcomes."""
    request = _request(
        identity_state=PreferenceIdentityState.UNAVAILABLE,
        confidence_band=ContinuityConfidenceBand.HIGH,
        person_preference_value="person-choice",
        person_room_exception_value="person-room-choice",
        person_room_exception_enabled=True,
        room_default_value="room-default",
        household_default_value="household-default",
    )

    first = _resolve_preference_hierarchy(request).as_dict()
    second = _resolve_preference_hierarchy(request).as_dict()

    assert first == second
