"""Diagnostics explainability tests for Experience Continuity."""

from __future__ import annotations

import pytest

from custom_components.concierge.diagnostics import _continuity_decision_traceability_visibility
from custom_components.concierge.diagnostics import _continuity_classification_traceability_visibility


@pytest.fixture
def enable_custom_integrations() -> None:
    """Satisfy the shared diagnostics test conftest dependency in isolation."""
    return None


class _FakeActivity:
    def __init__(self, external_refs: list[dict[str, str]] | None = None) -> None:
        self.external_refs = external_refs or []


class _FakeState:
    def __init__(self) -> None:
        self.activities = {
            "activity-1": _FakeActivity([
                {"ref_type": "execution_envelope", "ref_id": "env-1"},
                {"ref_type": "room_context", "ref_id": "room-1"},
            ]),
            "activity-2": _FakeActivity([
                {"ref_type": "execution_envelope", "ref_id": "env-2"},
            ]),
        }


def _contains_forbidden_key(payload: object, forbidden_key: str) -> bool:
    if isinstance(payload, dict):
        if forbidden_key in payload:
            return True
        return any(_contains_forbidden_key(value, forbidden_key) for value in payload.values())
    if isinstance(payload, list):
        return any(_contains_forbidden_key(value, forbidden_key) for value in payload)
    return False


def test_continuity_decision_traceability_visibility_has_complete_structure() -> None:
    """Decision-trace diagnostics should expose the governed structure and sample scenarios."""
    diagnostics = _continuity_decision_traceability_visibility(_FakeState())

    assert diagnostics["diagnostics_version"] == "ec_a_04_v1"
    assert diagnostics["classifier_version"] == "ec_a_02_v1"
    assert diagnostics["deterministic"] is True
    assert diagnostics["execution_envelope_ref_count"] == 2
    assert diagnostics["sample_decision_trace_count"] == 8
    assert diagnostics["trace_visibility"]["scope_trace_fields"]
    assert diagnostics["trace_visibility"]["event_trace_fields"]
    assert diagnostics["trace_visibility"]["confidence_trace_fields"]
    assert diagnostics["trace_visibility"]["fallback_trace_fields"]
    assert diagnostics["trace_visibility"]["decision_summary_trace_fields"]
    assert diagnostics["confidence_visibility"]["confidence_trace_count"] == 8
    assert diagnostics["fallback_visibility"]["sample_fallback_trace_count"] == 3

    sample_traces = diagnostics["sample_decision_traces"]
    assert [trace["scenario"] for trace in sample_traces] == [
        "entity_scope_success",
        "room_scope_success",
        "person_scope_success",
        "household_scope_success",
        "mode_scope_success",
        "unknown_event_fallback",
        "low_confidence_fallback",
        "explicit_scope_success",
    ]
    assert sample_traces[0]["decision_summary_trace"]["final_classification_outcome"]["scope"] == "entity"
    assert sample_traces[1]["decision_summary_trace"]["final_classification_outcome"]["scope"] == "room"
    assert sample_traces[2]["decision_summary_trace"]["final_classification_outcome"]["scope"] == "person"
    assert sample_traces[3]["decision_summary_trace"]["final_classification_outcome"]["scope"] == "household"
    assert sample_traces[4]["decision_summary_trace"]["final_classification_outcome"]["scope"] == "mode"
    assert sample_traces[5]["fallback_trace"]["fallback_category"] == "unknown_event"
    assert sample_traces[6]["fallback_trace"]["fallback_category"] == "low_confidence"
    assert sample_traces[7]["decision_summary_trace"]["final_classification_outcome"]["fallback_applied"] is False


def test_continuity_decision_traceability_visibility_is_deterministic_and_redacted() -> None:
    """Identical input should yield identical diagnostics and no forbidden payload keys."""
    first = _continuity_decision_traceability_visibility(_FakeState())
    second = _continuity_decision_traceability_visibility(_FakeState())

    assert first == second
    assert first["redaction_visibility"]["raw_debug_payloads_exposed"] is False
    assert first["redaction_visibility"]["personally_sensitive_content_exposed"] is False

    forbidden_keys = [
        "request_summary",
        "raw_event_payload",
        "raw_source_payload",
        "full_debug_payload",
        "voice_identity_biometric_artifacts",
        "asset_sensitive_details",
        "email_contents",
        "calendar_event_details",
        "task_contents",
        "shopping_item_contents",
        "mailbox_contents",
        "briefing_text",
        "summary_text",
        "status_text",
        "coordination_plan",
    ]
    for forbidden_key in forbidden_keys:
        assert not _contains_forbidden_key(first, forbidden_key)


def test_classification_trace_visibility_remains_available() -> None:
    """The existing classification traceability view should remain intact."""
    diagnostics = _continuity_classification_traceability_visibility(_FakeState())

    assert diagnostics["classifier_version"] == "ec_a_02_v1"
    assert diagnostics["deterministic"] is True
    assert diagnostics["sample_trace_count"] == 5
    assert diagnostics["sample_traces"][0]["scope_classification"]["scope"] == "entity"
    assert diagnostics["sample_traces"][1]["scope_classification"]["scope"] == "room"
    assert diagnostics["sample_traces"][2]["scope_classification"]["scope"] == "person"
    assert diagnostics["sample_traces"][3]["scope_classification"]["scope"] == "household"
    assert diagnostics["sample_traces"][4]["scope_classification"]["scope"] == "mode"
