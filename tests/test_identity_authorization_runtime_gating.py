from __future__ import annotations

from types import SimpleNamespace

from custom_components.concierge import services as services_module


def _service_call(*, target: str, intent_class: str) -> SimpleNamespace:
    return SimpleNamespace(data={"target": target, "intent_class": intent_class})


def test_runtime_identity_policy_not_required_allows_room_scoped_control() -> None:
    decision = services_module._evaluate_runtime_identity_authorization_policy(
        call=_service_call(target="light.kitchen", intent_class="home_control"),
        requested_target="light.kitchen",
        resolved_target="light.kitchen",
        runtime_context={
            "identity_context": {
                "state": "unavailable",
                "confidence_band": None,
            }
        },
    )

    assert decision["identity_requirement_class"] == "identity_not_required"
    assert decision["identity_policy_outcome"] == "continue_without_identity"
    assert decision["identity_policy_reason_code"] == "identity_not_required"
    assert decision["allows_execution"] is True


def test_runtime_identity_policy_required_blocks_when_identity_missing() -> None:
    decision = services_module._evaluate_runtime_identity_authorization_policy(
        call=_service_call(target="media_player.preferred_music", intent_class="person_preference"),
        requested_target="media_player.preferred_music",
        resolved_target="media_player.preferred_music",
        runtime_context={
            "identity_context": {
                "state": "unavailable",
                "confidence_band": None,
                "reason_code": "identity_context_missing",
            }
        },
    )

    assert decision["identity_requirement_class"] == "identity_required"
    assert decision["identity_policy_outcome"] == "deny"
    assert decision["identity_policy_reason_code"] == "identity_required_but_missing"
    assert decision["allows_execution"] is False
    assert decision["response_message"] == "I can't do that until I know who is speaking."


def test_runtime_identity_policy_required_fresh_challenges_when_stale() -> None:
    decision = services_module._evaluate_runtime_identity_authorization_policy(
        call=_service_call(target="sensor.calendar_tom", intent_class="calendar"),
        requested_target="sensor.calendar_tom",
        resolved_target="sensor.calendar_tom",
        runtime_context={
            "identity_context": {
                "state": "known",
                "confidence_band": "high",
                "reason_code": "attribution_ready",
            },
            "voice_identity_runtime_attribution": {
                "freshness": "stale",
                "attribution_age_ms": 91000,
            },
        },
    )

    assert decision["identity_requirement_class"] == "identity_required_fresh"
    assert decision["identity_policy_outcome"] == "challenge"
    assert decision["identity_policy_reason_code"] == "identity_required_fresh_but_stale"
    assert decision["identity_freshness_class"] == "stale"
    assert decision["attribution_age_ms"] == 91000


def test_runtime_identity_policy_step_up_requires_challenge_for_known_speaker() -> None:
    decision = services_module._evaluate_runtime_identity_authorization_policy(
        call=_service_call(target="lock.front_door", intent_class="unlock"),
        requested_target="lock.front_door",
        resolved_target="lock.front_door",
        runtime_context={
            "identity_context": {
                "state": "known",
                "confidence_band": "high",
                "reason_code": "attribution_ready",
            },
            "voice_identity_runtime_attribution": {
                "freshness": "fresh",
            },
        },
    )

    assert decision["identity_requirement_class"] == "identity_required_step_up"
    assert decision["identity_policy_outcome"] == "challenge"
    assert decision["identity_policy_reason_code"] == "identity_step_up_required"
    assert decision["allows_execution"] is False


def test_runtime_policy_projection_is_diagnostics_safe() -> None:
    decision = services_module._evaluate_runtime_identity_authorization_policy(
        call=_service_call(target="weather.home", intent_class="weather"),
        requested_target="weather.home",
        resolved_target="weather.home",
        runtime_context={"identity_context": {"state": "unknown", "confidence_band": "unknown"}},
    )

    rendered = str(decision).lower()
    for forbidden in {"audio", "embedding", "vector", "voiceprint", "biometric"}:
        assert forbidden not in rendered
