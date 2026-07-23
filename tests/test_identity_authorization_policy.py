from __future__ import annotations

from custom_components.concierge.identity_authorization_policy import (
    PolicyOutcome,
    build_safe_identity_diagnostics,
    evaluate_identity_authorization,
)


def test_identity_not_required_proceeds_with_not_required_reason() -> None:
    decision = evaluate_identity_authorization(
        requirement="identity_not_required",
        attribution_state="not_required",
        confidence_band="none",
        freshness_class="not_applicable",
    )

    assert decision.outcome is PolicyOutcome.CONTINUE_WITHOUT_IDENTITY
    assert decision.reason_code == "identity_not_required"


def test_identity_optional_proceeds_when_missing_with_constrained_outcome() -> None:
    decision = evaluate_identity_authorization(
        requirement="identity_optional",
        attribution_state="unknown",
        confidence_band="none",
        freshness_class="not_applicable",
    )

    assert decision.outcome is PolicyOutcome.CONTINUE_WITHOUT_IDENTITY
    assert decision.reason_code == "identity_optional_missing_continue_without_identity"


def test_identity_required_blocks_when_missing() -> None:
    decision = evaluate_identity_authorization(
        requirement="identity_required",
        attribution_state="unknown",
        confidence_band="none",
        freshness_class="not_applicable",
    )

    assert decision.outcome is PolicyOutcome.DENY
    assert decision.reason_code == "identity_required_but_unknown"


def test_identity_required_fresh_challenges_when_stale() -> None:
    decision = evaluate_identity_authorization(
        requirement="identity_required_fresh",
        attribution_state="known",
        confidence_band="high",
        freshness_class="stale",
    )

    assert decision.outcome is PolicyOutcome.CHALLENGE
    assert decision.reason_code == "identity_required_fresh_but_stale"


def test_identity_required_step_up_denies_uncertain_attribution() -> None:
    decision = evaluate_identity_authorization(
        requirement="identity_required_step_up",
        attribution_state="ambiguous",
        confidence_band="low",
        freshness_class="fresh",
    )

    assert decision.outcome is PolicyOutcome.DENY
    assert decision.reason_code == "identity_policy_deny"


def test_high_confidence_fresh_required_allows() -> None:
    decision = evaluate_identity_authorization(
        requirement="identity_required",
        attribution_state="known",
        confidence_band="high",
        freshness_class="fresh",
    )

    assert decision.outcome is PolicyOutcome.ALLOW
    assert decision.reason_code == "identity_policy_allow"


def test_ambiguous_required_challenges() -> None:
    decision = evaluate_identity_authorization(
        requirement="identity_required",
        attribution_state="ambiguous",
        confidence_band="low",
        freshness_class="fresh",
    )

    assert decision.outcome is PolicyOutcome.CHALLENGE
    assert decision.reason_code == "identity_required_but_ambiguous"


def test_low_confidence_required_challenges() -> None:
    decision = evaluate_identity_authorization(
        requirement="identity_required",
        attribution_state="known",
        confidence_band="low",
        freshness_class="fresh",
    )

    assert decision.outcome is PolicyOutcome.CHALLENGE
    assert decision.reason_code == "identity_required_but_ambiguous"


def test_unavailable_fails_closed_for_sensitive() -> None:
    decision = evaluate_identity_authorization(
        requirement="identity_required_step_up",
        attribution_state="unavailable",
        confidence_band="none",
        freshness_class="not_applicable",
    )

    assert decision.outcome is PolicyOutcome.DENY
    assert decision.reason_code == "identity_policy_deny"


def test_policy_payload_does_not_expose_biometric_fields() -> None:
    decision = evaluate_identity_authorization(
        requirement="identity_required",
        attribution_state="known",
        confidence_band="high",
        freshness_class="fresh",
    )
    rendered = str(decision).lower()

    for forbidden in {"audio", "embedding", "vector", "biometric"}:
        assert forbidden not in rendered
    assert decision.reason_code
    assert decision.outcome.value


def test_safe_identity_diagnostics_contains_required_explainability_fields() -> None:
    decision = evaluate_identity_authorization(
        requirement="identity_required",
        attribution_state="known",
        confidence_band="high",
        freshness_class="fresh",
    )

    diagnostics = build_safe_identity_diagnostics(
        decision=decision,
        attribution_age_ms=120,
        room_resolution_source="foundation_room_resolution",
    )

    assert diagnostics["reason_code"] == "identity_policy_allow"
    assert diagnostics["policy_outcome"] == "allow"
    assert diagnostics["attribution_age_ms"] == 120
    assert diagnostics["freshness_class"] == "fresh"
    assert diagnostics["room_resolution_source"] == "foundation_room_resolution"

    rendered = str(diagnostics).lower()
    for forbidden in {"audio", "embedding", "vector", "biometric"}:
        assert forbidden not in rendered
