"""Unit tests for Experience Continuity runtime concept models."""

from __future__ import annotations

import pytest

from custom_components.concierge.models import ContinuityConfidence
from custom_components.concierge.models import ContinuityConfidenceBand
from custom_components.concierge.models import ContinuityEventIdentity
from custom_components.concierge.models import ContinuityScope
from custom_components.concierge.models import ExperienceSnapshot
from custom_components.concierge.models import OperationalRestore
from custom_components.concierge.models import PreferenceRestore
from custom_components.concierge.models import UsualState
from custom_components.concierge.models import UsualStateBasis


def test_experience_snapshot_round_trip() -> None:
    """Experience snapshots should serialize and deserialize losslessly."""
    snapshot = ExperienceSnapshot(
        snapshot_id="snapshot-1",
        scope=ContinuityScope.ROOM,
        scope_ref="living_room",
        captured_at="2026-07-21T12:00:00+00:00",
        event_id="evt-1",
        state={"scene": "movie", "brightness": 60},
        metadata={"source": "test"},
    )

    payload = snapshot.as_dict()

    assert payload["concept_type"] == "experience_snapshot"
    assert payload["scope"] == "room"
    assert ExperienceSnapshot.from_dict(payload) == snapshot


def test_usual_state_round_trip_and_optional_event_id() -> None:
    """Usual state should preserve configured baseline metadata across round trips."""
    state = UsualState(
        state_id="usual-1",
        scope="person",
        scope_ref="person.tom",
        basis=UsualStateBasis.CONFIGURED,
        updated_at="2026-07-21T12:05:00+00:00",
        values={"preferred_genre": "jazz"},
        metadata={"owner": "voice_identity"},
    )

    restored = UsualState.from_dict(state.as_dict())

    assert restored == state
    assert restored.event_id is None
    assert restored.basis is UsualStateBasis.CONFIGURED


def test_operational_restore_round_trip() -> None:
    """Operational restore should preserve snapshot linkage and target state."""
    restore = OperationalRestore(
        restore_id="restore-1",
        scope=ContinuityScope.ENTITY,
        scope_ref="light.kitchen",
        source_snapshot_id="snapshot-1",
        target_state={"state": "on", "brightness": 80},
        created_at="2026-07-21T12:10:00+00:00",
        metadata={"reason": "managed_transition"},
    )

    assert OperationalRestore.from_dict(restore.as_dict()) == restore


def test_preference_restore_round_trip() -> None:
    """Preference restore should preserve references to preference sources."""
    restore = PreferenceRestore(
        restore_id="restore-pref-1",
        scope=ContinuityScope.ROOM,
        scope_ref="kitchen",
        target_state={"volume": 18},
        created_at="2026-07-21T12:15:00+00:00",
        preference_refs=["room_default", "person_preference"],
        metadata={"policy": "safe_default_allowed"},
    )

    payload = restore.as_dict()

    assert payload["concept_type"] == "preference_restore"
    assert PreferenceRestore.from_dict(payload) == restore


def test_continuity_confidence_round_trip() -> None:
    """Continuity confidence should preserve normalized score and band values."""
    confidence = ContinuityConfidence(
        score=0.92,
        band=ContinuityConfidenceBand.HIGH,
        reason_codes=["identity_available", "room_resolved"],
        available=True,
        metadata={"source": "voice_identity"},
    )

    restored = ContinuityConfidence.from_dict(confidence.as_dict())

    assert restored == confidence
    assert restored.band is ContinuityConfidenceBand.HIGH


def test_continuity_event_identity_round_trip() -> None:
    """Continuity event identity should preserve stable event references."""
    identity = ContinuityEventIdentity(
        event_id="evt-42",
        event_type="voice_interaction",
        scope=ContinuityScope.ROOM,
        scope_ref="great_room",
        source_domain="concierge",
        occurred_at="2026-07-21T12:20:00+00:00",
        correlation_id="corr-1",
        metadata={"channel": "assist"},
    )

    assert ContinuityEventIdentity.from_dict(identity.as_dict()) == identity


@pytest.mark.parametrize(
    ("factory", "expected_message"),
    [
        (
            lambda: ExperienceSnapshot(
                snapshot_id="snapshot-1",
                scope="invalid",
                scope_ref="living_room",
                captured_at="2026-07-21T12:00:00+00:00",
                event_id="evt-1",
                state={"brightness": 60},
            ),
            "scope must be one of:",
        ),
        (
            lambda: UsualState(
                state_id="usual-1",
                scope=ContinuityScope.ROOM,
                scope_ref="kitchen",
                basis="invalid",
                updated_at="2026-07-21T12:05:00+00:00",
                values={"genre": "jazz"},
            ),
            "basis must be one of:",
        ),
        (
            lambda: OperationalRestore(
                restore_id="restore-1",
                scope=ContinuityScope.ROOM,
                scope_ref="kitchen",
                source_snapshot_id="snapshot-1",
                target_state={},
                created_at="2026-07-21T12:10:00+00:00",
            ),
            "target_state must not be empty",
        ),
        (
            lambda: ContinuityConfidence(
                score=1.5,
                band=ContinuityConfidenceBand.HIGH,
            ),
            "score must be between 0.0 and 1.0",
        ),
        (
            lambda: ContinuityEventIdentity(
                event_id="evt-1",
                event_type="",
                scope=ContinuityScope.ROOM,
                scope_ref="kitchen",
                source_domain="concierge",
                occurred_at="2026-07-21T12:20:00+00:00",
            ),
            "event_type must be a non-empty string",
        ),
    ],
)
def test_invalid_values_are_rejected(factory, expected_message: str) -> None:
    """Invalid enum and payload values should be rejected deterministically."""
    with pytest.raises(ValueError, match=expected_message):
        factory()


def test_concept_type_mismatch_is_rejected() -> None:
    """Deserialization should reject payloads tagged for a different concept."""
    with pytest.raises(ValueError, match="concept_type must be experience_snapshot"):
        ExperienceSnapshot.from_dict(
            {
                "concept_type": "usual_state",
                "snapshot_id": "snapshot-1",
                "scope": "room",
                "scope_ref": "living_room",
                "captured_at": "2026-07-21T12:00:00+00:00",
                "event_id": "evt-1",
                "state": {"brightness": 60},
            }
        )


def test_ownership_scope_safe_usage_preserves_scope_boundaries() -> None:
    """Model usage should preserve scope ownership instead of collapsing scopes together."""
    snapshots = [
        ExperienceSnapshot(
            snapshot_id="entity-snapshot",
            scope=ContinuityScope.ENTITY,
            scope_ref="light.kitchen",
            captured_at="2026-07-21T12:00:00+00:00",
            event_id="evt-entity",
            state={"brightness": 55},
        ),
        ExperienceSnapshot(
            snapshot_id="room-snapshot",
            scope=ContinuityScope.ROOM,
            scope_ref="kitchen",
            captured_at="2026-07-21T12:01:00+00:00",
            event_id="evt-room",
            state={"volume": 18},
        ),
        ExperienceSnapshot(
            snapshot_id="person-snapshot",
            scope=ContinuityScope.PERSON,
            scope_ref="person.tom",
            captured_at="2026-07-21T12:02:00+00:00",
            event_id="evt-person",
            state={"preferred_genre": "jazz"},
        ),
        ExperienceSnapshot(
            snapshot_id="household-snapshot",
            scope=ContinuityScope.HOUSEHOLD,
            scope_ref="household.default",
            captured_at="2026-07-21T12:03:00+00:00",
            event_id="evt-household",
            state={"silence_policy": True},
        ),
    ]

    assert [snapshot.scope for snapshot in snapshots] == [
        ContinuityScope.ENTITY,
        ContinuityScope.ROOM,
        ContinuityScope.PERSON,
        ContinuityScope.HOUSEHOLD,
    ]
    assert [ExperienceSnapshot.from_dict(snapshot.as_dict()) for snapshot in snapshots] == snapshots