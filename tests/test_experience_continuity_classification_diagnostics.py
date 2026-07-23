"""Unit tests for continuity classification diagnostics visibility."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from custom_components.concierge.diagnostics import _continuity_classification_traceability_visibility


@dataclass(slots=True)
class _FakeActivity:
    external_refs: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class _FakeState:
    activities: dict[str, _FakeActivity] = field(default_factory=dict)


def test_continuity_classification_traceability_visibility_structure() -> None:
    """Diagnostics visibility should expose deterministic classification samples."""
    state = _FakeState(
        activities={
            "a-1": _FakeActivity(external_refs=[{"ref_type": "execution_envelope"}]),
            "a-2": _FakeActivity(external_refs=[{"ref_type": "routing_decision"}]),
        }
    )

    payload = _continuity_classification_traceability_visibility(state)

    assert payload["classifier_version"] == "ec_a_02_v1"
    assert payload["deterministic"] is True
    assert payload["execution_envelope_ref_count"] == 1
    assert payload["sample_trace_count"] == 5
    assert payload["supported_scopes"] == ["entity", "room", "person", "household", "mode"]
    assert "identity_confidence_change" in payload["supported_event_classes"]


def test_continuity_classification_traceability_visibility_samples_cover_all_scopes() -> None:
    """Sample traces should include one deterministic example per governed scope."""
    payload = _continuity_classification_traceability_visibility(_FakeState())
    scopes = [trace["scope_classification"]["scope"] for trace in payload["sample_traces"]]

    assert scopes == ["entity", "room", "person", "household", "mode"]
