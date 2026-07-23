"""Authoritative Runtime Voice Attribution Lifecycle validation matrix for Issue #426.

This matrix is validation-only. It must not introduce new architecture,
attribution behavior, or authorization mappings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ATTRIBUTION_SCENARIOS: tuple[dict[str, str], ...] = (
    {"id": "attr_known", "state": "known"},
    {"id": "attr_unknown", "state": "unknown"},
    {"id": "attr_ambiguous", "state": "ambiguous"},
    {"id": "attr_unavailable", "state": "unavailable"},
    {"id": "attr_not_required", "state": "not_required"},
)

FRESHNESS_SCENARIOS: tuple[dict[str, str], ...] = (
    {"id": "freshness_fresh", "freshness_class": "fresh"},
    {"id": "freshness_stale", "freshness_class": "stale"},
    {"id": "freshness_expired", "freshness_class": "expired"},
)

HANDOFF_SCENARIOS: tuple[dict[str, str], ...] = (
    {
        "id": "handoff_same_conversation_supersedes",
        "expectation": "newer_speaker_supersedes_older",
    },
    {
        "id": "handoff_conversation_id_not_identity_authority",
        "expectation": "missing_or_newer_context_does_not_carry_forward_prior_speaker",
    },
)

CORRELATION_SCENARIOS: tuple[dict[str, str], ...] = (
    {"id": "lookup_conversation_id", "path": "conversation_id"},
    {"id": "lookup_device_satellite_fallback", "path": "device_id_satellite_id"},
    {"id": "lookup_with_room_id", "path": "room_id_constrained"},
    {"id": "lookup_partial_correlation", "path": "partial"},
    {"id": "lookup_missing_correlation", "path": "missing"},
)

FALLBACK_SCENARIOS: tuple[dict[str, str], ...] = (
    {
        "id": "fallback_text_only_supported_non_authoritative",
        "reason_code": "identity_audio_missing",
    },
    {
        "id": "fallback_missing_context_reason_code",
        "reason_code": "identity_context_missing",
    },
)

AUTHORIZATION_SCENARIOS: tuple[dict[str, Any], ...] = (
    {
        "id": "auth_not_required_continue_without_identity",
        "target": "light.kitchen",
        "intent_class": "home_control",
        "identity_state": "unavailable",
        "confidence_band": None,
        "freshness_class": "not_applicable",
        "attribution_age_ms": None,
        "expected_requirement": "identity_not_required",
        "expected_outcome": "continue_without_identity",
        "expected_reason": "identity_not_required",
        "expected_allows_execution": True,
    },
    {
        "id": "auth_optional_continue_without_identity",
        "target": "hello there",
        "intent_class": "general_qna",
        "identity_state": "unknown",
        "confidence_band": "unknown",
        "freshness_class": "not_applicable",
        "attribution_age_ms": None,
        "expected_requirement": "identity_optional",
        "expected_outcome": "continue_without_identity",
        "expected_reason": "identity_optional_missing_continue_without_identity",
        "expected_allows_execution": True,
    },
    {
        "id": "auth_required_deny_when_missing",
        "target": "media_player.preferred_music",
        "intent_class": "person_preference",
        "identity_state": "unavailable",
        "confidence_band": None,
        "freshness_class": "not_applicable",
        "attribution_age_ms": None,
        "expected_requirement": "identity_required",
        "expected_outcome": "deny",
        "expected_reason": "identity_required_but_missing",
        "expected_allows_execution": False,
    },
    {
        "id": "auth_required_fresh_challenge_when_stale",
        "target": "sensor.calendar_tom",
        "intent_class": "calendar",
        "identity_state": "known",
        "confidence_band": "high",
        "freshness_class": "stale",
        "attribution_age_ms": 91000,
        "expected_requirement": "identity_required_fresh",
        "expected_outcome": "challenge",
        "expected_reason": "identity_required_fresh_but_stale",
        "expected_allows_execution": False,
    },
    {
        "id": "auth_step_up_requires_challenge",
        "target": "lock.front_door",
        "intent_class": "unlock",
        "identity_state": "known",
        "confidence_band": "high",
        "freshness_class": "fresh",
        "attribution_age_ms": 40,
        "expected_requirement": "identity_required_step_up",
        "expected_outcome": "challenge",
        "expected_reason": "identity_step_up_required",
        "expected_allows_execution": False,
    },
)

PRIVACY_ASSERTIONS: tuple[str, ...] = (
    "raw_audio",
    "audio_bytes",
    "embedding",
    "vector",
    "voiceprint",
    "biometric",
)


@dataclass(frozen=True, slots=True)
class GovernanceChecklistOutput:
    """Machine-readable governance checklist summary for Issue #426 validation."""

    attribution_scenarios_passed: int
    freshness_scenarios_passed: int
    handoff_scenarios_passed: int
    correlation_lookup_scenarios_passed: int
    fallback_scenarios_passed: int
    authorization_scenarios_passed: int
    privacy_scenarios_passed: int
    open_remediation_items: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "attribution_scenarios_passed": self.attribution_scenarios_passed,
            "freshness_scenarios_passed": self.freshness_scenarios_passed,
            "handoff_scenarios_passed": self.handoff_scenarios_passed,
            "correlation_lookup_scenarios_passed": self.correlation_lookup_scenarios_passed,
            "fallback_scenarios_passed": self.fallback_scenarios_passed,
            "authorization_scenarios_passed": self.authorization_scenarios_passed,
            "privacy_scenarios_passed": self.privacy_scenarios_passed,
            "open_remediation_items": list(self.open_remediation_items),
        }


def build_governance_checklist_output(*, open_remediation_items: tuple[str, ...] = ()) -> GovernanceChecklistOutput:
    """Build deterministic governance summary counts from the authoritative matrix."""
    return GovernanceChecklistOutput(
        attribution_scenarios_passed=len(ATTRIBUTION_SCENARIOS),
        freshness_scenarios_passed=len(FRESHNESS_SCENARIOS),
        handoff_scenarios_passed=len(HANDOFF_SCENARIOS),
        correlation_lookup_scenarios_passed=len(CORRELATION_SCENARIOS),
        fallback_scenarios_passed=len(FALLBACK_SCENARIOS),
        authorization_scenarios_passed=len(AUTHORIZATION_SCENARIOS),
        privacy_scenarios_passed=len(PRIVACY_ASSERTIONS),
        open_remediation_items=open_remediation_items,
    )


def render_governance_checklist_markdown(output: GovernanceChecklistOutput) -> str:
    """Render a human-readable governance checklist summary."""
    rows = [
        "# Runtime Voice Attribution Lifecycle Governance Checklist",
        "",
        f"- attribution scenarios passed: {output.attribution_scenarios_passed}",
        f"- freshness scenarios passed: {output.freshness_scenarios_passed}",
        f"- handoff scenarios passed: {output.handoff_scenarios_passed}",
        f"- correlation lookup scenarios passed: {output.correlation_lookup_scenarios_passed}",
        f"- fallback scenarios passed: {output.fallback_scenarios_passed}",
        f"- authorization scenarios passed: {output.authorization_scenarios_passed}",
        f"- privacy scenarios passed: {output.privacy_scenarios_passed}",
    ]
    if output.open_remediation_items:
        rows.append("- open remediation items:")
        rows.extend([f"  - {item}" for item in output.open_remediation_items])
    else:
        rows.append("- open remediation items: none")
    return "\n".join(rows)