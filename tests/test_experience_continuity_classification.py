"""Unit tests for deterministic continuity scope and event classification."""

from __future__ import annotations

from custom_components.concierge.models import ContinuityClassificationTrace
from custom_components.concierge.models import ContinuityEventClass
from custom_components.concierge.models import ContinuityScope
from custom_components.concierge.models import build_continuity_classification_trace
from custom_components.concierge.models import classify_continuity_event
from custom_components.concierge.models import classify_continuity_scope


def test_scope_classification_entity_room_person_household_mode() -> None:
    """Classifier should deterministically resolve each supported continuity scope."""
    assert classify_continuity_scope({"entity_id": "light.kitchen"}).scope is ContinuityScope.ENTITY
    assert classify_continuity_scope({"area_id": "kitchen"}).scope is ContinuityScope.ROOM
    assert classify_continuity_scope({"person_id": "person.tom"}).scope is ContinuityScope.PERSON
    assert classify_continuity_scope({"guest_mode": True}).scope is ContinuityScope.HOUSEHOLD
    assert classify_continuity_scope({"mode_id": "night"}).scope is ContinuityScope.MODE


def test_scope_classification_uses_deterministic_precedence_for_ambiguous_input() -> None:
    """Ambiguous scope hints should resolve by explicit precedence instead of randomness."""
    result = classify_continuity_scope(
        {
            "entity_id": "light.kitchen",
            "area_id": "kitchen",
            "person_id": "person.tom",
            "guest_mode": True,
            "mode_id": "night",
        }
    )

    assert result.scope is ContinuityScope.ENTITY
    assert result.reason_code == "entity_scope_inferred"
    assert result.metadata["candidate_scope_count"] == 5


def test_scope_classification_respects_explicit_scope() -> None:
    """Explicit scope fields should be honored when provided."""
    result = classify_continuity_scope(
        {
            "scope": "room",
            "scope_ref": "great_room",
            "person_id": "person.tom",
        }
    )

    assert result.scope is ContinuityScope.ROOM
    assert result.scope_ref == "great_room"
    assert result.reason_code == "explicit_scope_field"


def test_event_classification_known_and_unknown() -> None:
    """Event classifier should classify known types and preserve unknown values safely."""
    known = classify_continuity_event({"event_type": "voice_interaction"})
    unknown = classify_continuity_event({"event_type": "brand_new_event"})

    assert known.event_class is ContinuityEventClass.VOICE_INTERACTION
    assert known.reason_code == "voice_event_keyword"
    assert unknown.event_class is ContinuityEventClass.UNKNOWN
    assert unknown.reason_code == "unknown_event_class"


def test_event_classification_explicit_class_overrides_keywords() -> None:
    """Explicit event class should win over inferred keyword matching."""
    result = classify_continuity_event(
        {
            "event_class": "guest_mode_change",
            "event_type": "voice_interaction",
        }
    )

    assert result.event_class is ContinuityEventClass.GUEST_MODE_CHANGE
    assert result.reason_code == "explicit_event_class"


def test_classification_trace_serialization_round_trip() -> None:
    """Trace envelopes should serialize and deserialize without data loss."""
    trace = build_continuity_classification_trace(
        {
            "entity_id": "light.kitchen",
            "event_type": "manual_stop",
            "occurred_at": "2026-07-22T00:00:00+00:00",
            "trace_source": "unit_test",
            "continuity_confidence": {
                "score": 0.9,
                "band": "high",
                "reason_codes": ["entity_scope"],
                "available": True,
            },
        }
    )

    payload = trace.as_dict()
    restored = ContinuityClassificationTrace.from_dict(payload)

    assert restored.scope_classification.scope is ContinuityScope.ENTITY
    assert restored.event_classification.event_class is ContinuityEventClass.MANUAL_STOP
    assert restored.trace_source == "unit_test"
    assert restored.continuity_confidence is not None
    assert restored.continuity_confidence.score == 0.9


def test_classification_determinism_same_input_same_output() -> None:
    """Same input should always yield equivalent classification output."""
    payload = {
        "area_id": "kitchen",
        "event_type": "monitoring_question",
        "occurred_at": "2026-07-22T00:00:01+00:00",
    }

    first = build_continuity_classification_trace(payload).as_dict()
    second = build_continuity_classification_trace(payload).as_dict()

    assert first["scope_classification"] == second["scope_classification"]
    assert first["event_classification"] == second["event_classification"]


def test_ownership_boundary_protection_entity_hints_do_not_cross_to_person_scope() -> None:
    """Entity ownership evidence should remain entity-scoped under deterministic precedence."""
    result = classify_continuity_scope(
        {
            "entity_id": "light.kitchen",
            "person_id": "person.tom",
        }
    )

    assert result.scope is ContinuityScope.ENTITY
    assert result.scope_ref == "light.kitchen"
