"""Identity authorization classification policy for Concierge.

This module consumes safe attribution context only. It does not perform
biometric attribution.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class IdentityRequirement(StrEnum):
    NOT_REQUIRED = "identity_not_required"
    OPTIONAL = "identity_optional"
    REQUIRED = "identity_required"
    REQUIRED_FRESH = "identity_required_fresh"
    REQUIRED_STEP_UP = "identity_required_step_up"


class AttributionState(StrEnum):
    KNOWN = "known"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"
    NOT_REQUIRED = "not_required"


class FreshnessClass(StrEnum):
    FRESH = "fresh"
    STALE = "stale"
    EXPIRED = "expired"
    NOT_APPLICABLE = "not_applicable"


class PolicyOutcome(StrEnum):
    ALLOW = "allow"
    CHALLENGE = "challenge"
    DENY = "deny"
    CONSTRAIN = "constrain"
    CONTINUE_WITHOUT_IDENTITY = "continue_without_identity"


@dataclass(slots=True, frozen=True)
class IdentityPolicyDecision:
    requirement: IdentityRequirement
    outcome: PolicyOutcome
    reason_code: str
    attribution_state: AttributionState
    confidence_band: str
    freshness_class: FreshnessClass


def build_safe_identity_diagnostics(
    *,
    decision: IdentityPolicyDecision,
    attribution_age_ms: int,
    room_resolution_source: str | None,
) -> dict[str, object]:
    """Build safe diagnostics payload for identity policy explainability."""
    return {
        "reason_code": decision.reason_code,
        "policy_outcome": decision.outcome.value,
        "attribution_age_ms": int(attribution_age_ms),
        "freshness_class": decision.freshness_class.value,
        "room_resolution_source": str(room_resolution_source or "unknown"),
        "attribution_state": decision.attribution_state.value,
        "confidence_band": decision.confidence_band,
    }


_REASON_CODES = {
    "identity_known_high_confidence",
    "identity_known_medium_confidence",
    "identity_known_low_confidence",
    "identity_policy_allow",
    "identity_policy_challenge",
    "identity_policy_deny",
    "identity_policy_constrain",
    "identity_optional_missing_continue_without_identity",
    "identity_ambiguous_match",
    "identity_required_but_unknown",
    "identity_required_but_ambiguous",
    "identity_unknown",
    "identity_unavailable",
    "identity_audio_missing",
    "identity_context_missing",
    "identity_context_stale",
    "identity_context_expired",
    "identity_not_required",
    "identity_required_but_missing",
    "identity_required_fresh_but_stale",
    "identity_policy_blocked_sensitive_intent",
    "identity_step_up_required",
}


def evaluate_identity_authorization(
    *,
    requirement: str,
    attribution_state: str,
    confidence_band: str | None,
    freshness_class: str,
) -> IdentityPolicyDecision:
    """Evaluate deterministic identity policy outcome for one request."""
    req = IdentityRequirement(requirement)
    state = AttributionState(attribution_state)
    freshness = FreshnessClass(freshness_class)
    band = str(confidence_band or "none").strip().lower() or "none"

    if req is IdentityRequirement.NOT_REQUIRED:
        return IdentityPolicyDecision(
            requirement=req,
            outcome=PolicyOutcome.CONTINUE_WITHOUT_IDENTITY,
            reason_code="identity_not_required",
            attribution_state=AttributionState.NOT_REQUIRED,
            confidence_band="none",
            freshness_class=FreshnessClass.NOT_APPLICABLE,
        )

    if req is IdentityRequirement.OPTIONAL:
        if state is AttributionState.KNOWN and freshness in {
            FreshnessClass.FRESH,
            FreshnessClass.NOT_APPLICABLE,
        } and band in {"high", "medium"}:
            return _decision(req, PolicyOutcome.ALLOW, "identity_policy_allow", state, band, freshness)
        if state in {
            AttributionState.AMBIGUOUS,
            AttributionState.UNKNOWN,
            AttributionState.UNAVAILABLE,
            AttributionState.NOT_REQUIRED,
        }:
            return _decision(
                req,
                PolicyOutcome.CONTINUE_WITHOUT_IDENTITY,
                "identity_optional_missing_continue_without_identity",
                state,
                band,
                freshness,
            )
        if freshness in {FreshnessClass.STALE, FreshnessClass.EXPIRED}:
            return _decision(req, PolicyOutcome.CONSTRAIN, "identity_policy_constrain", state, band, freshness)
        return _decision(req, PolicyOutcome.CONSTRAIN, "identity_policy_constrain", state, band, freshness)

    if req is IdentityRequirement.REQUIRED:
        if state is AttributionState.KNOWN and freshness is not FreshnessClass.EXPIRED and band in {"high", "medium"}:
            return _decision(req, PolicyOutcome.ALLOW, "identity_policy_allow", state, band, freshness)
        if state is AttributionState.AMBIGUOUS or band == "low":
            return _decision(req, PolicyOutcome.CHALLENGE, "identity_required_but_ambiguous", state, band, freshness)
        if state is AttributionState.UNKNOWN:
            return _decision(req, PolicyOutcome.DENY, "identity_required_but_unknown", state, band, freshness)
        return _decision(req, PolicyOutcome.DENY, "identity_required_but_missing", state, band, freshness)

    if req is IdentityRequirement.REQUIRED_FRESH:
        if freshness in {FreshnessClass.STALE, FreshnessClass.EXPIRED}:
            return _decision(req, PolicyOutcome.CHALLENGE, "identity_required_fresh_but_stale", state, band, freshness)
        if state is AttributionState.KNOWN and freshness is FreshnessClass.FRESH and band == "high":
            return _decision(req, PolicyOutcome.ALLOW, "identity_policy_allow", state, band, freshness)
        if state is AttributionState.AMBIGUOUS or band == "low":
            return _decision(req, PolicyOutcome.CHALLENGE, "identity_required_but_ambiguous", state, band, freshness)
        if state is AttributionState.UNKNOWN:
            return _decision(req, PolicyOutcome.CHALLENGE, "identity_required_but_unknown", state, band, freshness)
        if state in {AttributionState.UNAVAILABLE, AttributionState.NOT_REQUIRED}:
            return _decision(req, PolicyOutcome.CHALLENGE, "identity_required_but_missing", state, band, freshness)
        return _decision(req, PolicyOutcome.CHALLENGE, "identity_required_but_missing", state, band, freshness)

    # REQUIRED_STEP_UP
    if state is AttributionState.KNOWN and freshness is FreshnessClass.FRESH and band == "high":
        return _decision(req, PolicyOutcome.CHALLENGE, "identity_step_up_required", state, band, freshness)
    if state is AttributionState.AMBIGUOUS or band == "low":
        return _decision(req, PolicyOutcome.DENY, "identity_policy_deny", state, band, freshness)
    return _decision(req, PolicyOutcome.DENY, "identity_policy_deny", state, band, freshness)


def _reason_for_known_band(confidence_band: str) -> str:
    if confidence_band == "high":
        return "identity_known_high_confidence"
    if confidence_band == "medium":
        return "identity_known_medium_confidence"
    return "identity_known_low_confidence"


def _reason_for_freshness(freshness: FreshnessClass) -> str:
    if freshness is FreshnessClass.STALE:
        return "identity_context_stale"
    if freshness is FreshnessClass.EXPIRED:
        return "identity_context_expired"
    return "identity_context_missing"


def _decision(
    requirement: IdentityRequirement,
    outcome: PolicyOutcome,
    reason_code: str,
    state: AttributionState,
    confidence_band: str,
    freshness: FreshnessClass,
) -> IdentityPolicyDecision:
    normalized_reason = str(reason_code).strip().lower()
    if normalized_reason not in _REASON_CODES:
        normalized_reason = "identity_context_missing"

    return IdentityPolicyDecision(
        requirement=requirement,
        outcome=outcome,
        reason_code=normalized_reason,
        attribution_state=state,
        confidence_band=confidence_band,
        freshness_class=freshness,
    )
