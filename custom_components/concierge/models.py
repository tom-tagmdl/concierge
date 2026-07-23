"""Contract-first state models for Concierge foundation."""

from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, ClassVar


def _normalize_asset_groups(value: Any, legacy_device_ids: Any = None) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    if not isinstance(value, list):
        value = []

    for item in value:
        if not isinstance(item, dict):
            continue
        group_name = str(item.get("group_name", "")).strip()
        device_ids = [str(device_id).strip() for device_id in item.get("device_ids", []) if str(device_id).strip()]
        if not group_name and not device_ids:
            continue
        groups.append({"group_name": group_name, "device_ids": device_ids})

    if not groups and isinstance(legacy_device_ids, list):
        legacy_ids = [str(device_id).strip() for device_id in legacy_device_ids if str(device_id).strip()]
        if legacy_ids:
            groups.append(
                {
                    "group_name": "",
                    "device_ids": legacy_ids,
                }
            )

    return groups


def _normalize_device_groups(value: Any) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    if not isinstance(value, list):
        return groups

    for item in value:
        if not isinstance(item, dict):
            continue
        group_name = str(item.get("group_name", "")).strip()
        entity_ids = [str(entity_id).strip() for entity_id in item.get("entity_ids", []) if str(entity_id).strip()]
        if not group_name and not entity_ids:
            continue
        groups.append({"group_name": group_name, "entity_ids": entity_ids})

    return groups


def _normalize_source_bindings(value: Any, legacy_ref: Any = None) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    if isinstance(value, list):
        for item in value:
            if not isinstance(item, dict):
                continue
            entity_id = str(item.get("entity_id", "") or item.get("entityId", "") or "").strip()
            if not entity_id:
                continue
            label = str(item.get("label", "") or item.get("name", "") or "").strip()
            bindings.append(
                {
                    "label": label,
                    "entity_id": entity_id,
                }
            )
    legacy_value = str(legacy_ref or "").strip()
    if legacy_value and not bindings:
        bindings.append({"label": "", "entity_id": legacy_value})
    return bindings


def _require_non_empty_text(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be a non-empty string")
    return text


def _normalize_optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalize_string_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    normalized: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            normalized.append(text)
    return normalized


def _normalize_mapping(value: Any, field_name: str, *, require_non_empty: bool = False) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a dictionary")
    normalized = dict(value)
    if require_non_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _normalize_str_enum(value: Any, enum_cls: type[StrEnum], field_name: str) -> StrEnum:
    if isinstance(value, enum_cls):
        return value
    text = _require_non_empty_text(value, field_name)
    try:
        return enum_cls(text)
    except ValueError as exc:
        allowed = ", ".join(member.value for member in enum_cls)
        raise ValueError(f"{field_name} must be one of: {allowed}") from exc


def _validate_concept_type(value: Any, expected: StrEnum) -> None:
    if value is None:
        return
    if str(value).strip() != expected.value:
        raise ValueError(f"concept_type must be {expected.value}")


class ContinuityConceptType(StrEnum):
    """Stable identifiers for continuity concept serialization and mapping."""

    EXPERIENCE_SNAPSHOT = "experience_snapshot"
    USUAL_STATE = "usual_state"
    OPERATIONAL_RESTORE = "operational_restore"
    PREFERENCE_RESTORE = "preference_restore"
    CONTINUITY_CONFIDENCE = "continuity_confidence"
    CONTINUITY_EVENT_IDENTITY = "continuity_event_identity"


class ContinuityScope(StrEnum):
    """Permitted ownership or routing scopes for continuity concepts."""

    ENTITY = "entity"
    ROOM = "room"
    PERSON = "person"
    HOUSEHOLD = "household"
    MODE = "mode"


class UsualStateBasis(StrEnum):
    """Allowed baseline sources for usual-state references."""

    LEARNED = "learned"
    CONFIGURED = "configured"


class ContinuityConfidenceBand(StrEnum):
    """Normalized trust bands for continuity decisions."""

    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(slots=True)
class ExperienceSnapshot:
    """Captured experience context for future continuity workflows."""

    CONCEPT_TYPE: ClassVar[ContinuityConceptType] = ContinuityConceptType.EXPERIENCE_SNAPSHOT

    snapshot_id: str
    scope: ContinuityScope | str
    scope_ref: str
    captured_at: str
    event_id: str
    state: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.snapshot_id = _require_non_empty_text(self.snapshot_id, "snapshot_id")
        self.scope = _normalize_str_enum(self.scope, ContinuityScope, "scope")
        self.scope_ref = _require_non_empty_text(self.scope_ref, "scope_ref")
        self.captured_at = _require_non_empty_text(self.captured_at, "captured_at")
        self.event_id = _require_non_empty_text(self.event_id, "event_id")
        self.state = _normalize_mapping(self.state, "state", require_non_empty=True)
        self.metadata = _normalize_mapping(self.metadata, "metadata")

    def as_dict(self) -> dict[str, Any]:
        return {
            "concept_type": self.CONCEPT_TYPE.value,
            "snapshot_id": self.snapshot_id,
            "scope": self.scope.value,
            "scope_ref": self.scope_ref,
            "captured_at": self.captured_at,
            "event_id": self.event_id,
            "state": dict(self.state),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExperienceSnapshot:
        payload = _normalize_mapping(data, "data")
        _validate_concept_type(payload.get("concept_type"), cls.CONCEPT_TYPE)
        return cls(
            snapshot_id=payload.get("snapshot_id", ""),
            scope=payload.get("scope", ""),
            scope_ref=payload.get("scope_ref", ""),
            captured_at=payload.get("captured_at", ""),
            event_id=payload.get("event_id", ""),
            state=payload.get("state", {}),
            metadata=payload.get("metadata", {}),
        )


@dataclass(slots=True)
class UsualState:
    """Learned or configured baseline state for continuity decisions."""

    CONCEPT_TYPE: ClassVar[ContinuityConceptType] = ContinuityConceptType.USUAL_STATE

    state_id: str
    scope: ContinuityScope | str
    scope_ref: str
    basis: UsualStateBasis | str
    updated_at: str
    values: dict[str, Any]
    event_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.state_id = _require_non_empty_text(self.state_id, "state_id")
        self.scope = _normalize_str_enum(self.scope, ContinuityScope, "scope")
        self.scope_ref = _require_non_empty_text(self.scope_ref, "scope_ref")
        self.basis = _normalize_str_enum(self.basis, UsualStateBasis, "basis")
        self.updated_at = _require_non_empty_text(self.updated_at, "updated_at")
        self.values = _normalize_mapping(self.values, "values", require_non_empty=True)
        self.event_id = _normalize_optional_text(self.event_id)
        self.metadata = _normalize_mapping(self.metadata, "metadata")

    def as_dict(self) -> dict[str, Any]:
        return {
            "concept_type": self.CONCEPT_TYPE.value,
            "state_id": self.state_id,
            "scope": self.scope.value,
            "scope_ref": self.scope_ref,
            "basis": self.basis.value,
            "updated_at": self.updated_at,
            "values": dict(self.values),
            "event_id": self.event_id,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UsualState:
        payload = _normalize_mapping(data, "data")
        _validate_concept_type(payload.get("concept_type"), cls.CONCEPT_TYPE)
        return cls(
            state_id=payload.get("state_id", ""),
            scope=payload.get("scope", ""),
            scope_ref=payload.get("scope_ref", ""),
            basis=payload.get("basis", ""),
            updated_at=payload.get("updated_at", ""),
            values=payload.get("values", {}),
            event_id=payload.get("event_id"),
            metadata=payload.get("metadata", {}),
        )


@dataclass(slots=True)
class OperationalRestore:
    """Restore concept for replaying prior operational state without preference overrides."""

    CONCEPT_TYPE: ClassVar[ContinuityConceptType] = ContinuityConceptType.OPERATIONAL_RESTORE

    restore_id: str
    scope: ContinuityScope | str
    scope_ref: str
    source_snapshot_id: str
    target_state: dict[str, Any]
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.restore_id = _require_non_empty_text(self.restore_id, "restore_id")
        self.scope = _normalize_str_enum(self.scope, ContinuityScope, "scope")
        self.scope_ref = _require_non_empty_text(self.scope_ref, "scope_ref")
        self.source_snapshot_id = _require_non_empty_text(self.source_snapshot_id, "source_snapshot_id")
        self.target_state = _normalize_mapping(self.target_state, "target_state", require_non_empty=True)
        self.created_at = _require_non_empty_text(self.created_at, "created_at")
        self.metadata = _normalize_mapping(self.metadata, "metadata")

    def as_dict(self) -> dict[str, Any]:
        return {
            "concept_type": self.CONCEPT_TYPE.value,
            "restore_id": self.restore_id,
            "scope": self.scope.value,
            "scope_ref": self.scope_ref,
            "source_snapshot_id": self.source_snapshot_id,
            "target_state": dict(self.target_state),
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OperationalRestore:
        payload = _normalize_mapping(data, "data")
        _validate_concept_type(payload.get("concept_type"), cls.CONCEPT_TYPE)
        return cls(
            restore_id=payload.get("restore_id", ""),
            scope=payload.get("scope", ""),
            scope_ref=payload.get("scope_ref", ""),
            source_snapshot_id=payload.get("source_snapshot_id", ""),
            target_state=payload.get("target_state", {}),
            created_at=payload.get("created_at", ""),
            metadata=payload.get("metadata", {}),
        )


@dataclass(slots=True)
class PreferenceRestore:
    """Restore concept for replaying preference-driven outcomes within policy boundaries."""

    CONCEPT_TYPE: ClassVar[ContinuityConceptType] = ContinuityConceptType.PREFERENCE_RESTORE

    restore_id: str
    scope: ContinuityScope | str
    scope_ref: str
    target_state: dict[str, Any]
    created_at: str
    preference_refs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.restore_id = _require_non_empty_text(self.restore_id, "restore_id")
        self.scope = _normalize_str_enum(self.scope, ContinuityScope, "scope")
        self.scope_ref = _require_non_empty_text(self.scope_ref, "scope_ref")
        self.target_state = _normalize_mapping(self.target_state, "target_state", require_non_empty=True)
        self.created_at = _require_non_empty_text(self.created_at, "created_at")
        self.preference_refs = _normalize_string_list(self.preference_refs, "preference_refs")
        self.metadata = _normalize_mapping(self.metadata, "metadata")

    def as_dict(self) -> dict[str, Any]:
        return {
            "concept_type": self.CONCEPT_TYPE.value,
            "restore_id": self.restore_id,
            "scope": self.scope.value,
            "scope_ref": self.scope_ref,
            "target_state": dict(self.target_state),
            "created_at": self.created_at,
            "preference_refs": list(self.preference_refs),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PreferenceRestore:
        payload = _normalize_mapping(data, "data")
        _validate_concept_type(payload.get("concept_type"), cls.CONCEPT_TYPE)
        return cls(
            restore_id=payload.get("restore_id", ""),
            scope=payload.get("scope", ""),
            scope_ref=payload.get("scope_ref", ""),
            target_state=payload.get("target_state", {}),
            created_at=payload.get("created_at", ""),
            preference_refs=payload.get("preference_refs", []),
            metadata=payload.get("metadata", {}),
        )


@dataclass(slots=True)
class ContinuityConfidence:
    """Normalized trust indicator for continuity decisions."""

    CONCEPT_TYPE: ClassVar[ContinuityConceptType] = ContinuityConceptType.CONTINUITY_CONFIDENCE

    score: float
    band: ContinuityConfidenceBand | str
    reason_codes: list[str] = field(default_factory=list)
    available: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.score = float(self.score)
        if self.score < 0.0 or self.score > 1.0:
            raise ValueError("score must be between 0.0 and 1.0")
        self.band = _normalize_str_enum(self.band, ContinuityConfidenceBand, "band")
        self.reason_codes = _normalize_string_list(self.reason_codes, "reason_codes")
        self.available = bool(self.available)
        self.metadata = _normalize_mapping(self.metadata, "metadata")

    def as_dict(self) -> dict[str, Any]:
        return {
            "concept_type": self.CONCEPT_TYPE.value,
            "score": self.score,
            "band": self.band.value,
            "reason_codes": list(self.reason_codes),
            "available": self.available,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContinuityConfidence:
        payload = _normalize_mapping(data, "data")
        _validate_concept_type(payload.get("concept_type"), cls.CONCEPT_TYPE)
        return cls(
            score=payload.get("score", 0.0),
            band=payload.get("band", "unknown"),
            reason_codes=payload.get("reason_codes", []),
            available=payload.get("available", True),
            metadata=payload.get("metadata", {}),
        )


@dataclass(slots=True)
class ContinuityEventIdentity:
    """Stable event identity record for cross-domain continuity processing."""

    CONCEPT_TYPE: ClassVar[ContinuityConceptType] = ContinuityConceptType.CONTINUITY_EVENT_IDENTITY

    event_id: str
    event_type: str
    scope: ContinuityScope | str
    scope_ref: str
    source_domain: str
    occurred_at: str
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.event_id = _require_non_empty_text(self.event_id, "event_id")
        self.event_type = _require_non_empty_text(self.event_type, "event_type")
        self.scope = _normalize_str_enum(self.scope, ContinuityScope, "scope")
        self.scope_ref = _require_non_empty_text(self.scope_ref, "scope_ref")
        self.source_domain = _require_non_empty_text(self.source_domain, "source_domain")
        self.occurred_at = _require_non_empty_text(self.occurred_at, "occurred_at")
        self.correlation_id = _normalize_optional_text(self.correlation_id)
        self.metadata = _normalize_mapping(self.metadata, "metadata")

    def as_dict(self) -> dict[str, Any]:
        return {
            "concept_type": self.CONCEPT_TYPE.value,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "scope": self.scope.value,
            "scope_ref": self.scope_ref,
            "source_domain": self.source_domain,
            "occurred_at": self.occurred_at,
            "correlation_id": self.correlation_id,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContinuityEventIdentity:
        payload = _normalize_mapping(data, "data")
        _validate_concept_type(payload.get("concept_type"), cls.CONCEPT_TYPE)
        return cls(
            event_id=payload.get("event_id", ""),
            event_type=payload.get("event_type", ""),
            scope=payload.get("scope", ""),
            scope_ref=payload.get("scope_ref", ""),
            source_domain=payload.get("source_domain", ""),
            occurred_at=payload.get("occurred_at", ""),
            correlation_id=payload.get("correlation_id"),
            metadata=payload.get("metadata", {}),
        )


class ContinuityEventClass(StrEnum):
    """Deterministic continuity event categories governed by EC-A-02."""

    UNKNOWN = "unknown"
    VOICE_INTERACTION = "voice_interaction"
    ROOM_ENTRY = "room_entry"
    ROOM_EXIT = "room_exit"
    MUSIC_START = "music_start"
    MUSIC_PAUSE = "music_pause"
    MANUAL_STOP = "manual_stop"
    COMMAND_FOLLOW_UP = "command_follow_up"
    MONITORING_QUESTION = "monitoring_question"
    IDENTITY_CONFIDENCE_CHANGE = "identity_confidence_change"
    GUEST_MODE_CHANGE = "guest_mode_change"


def _first_non_empty_text(payload: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        text = str(payload.get(key, "") or "").strip()
        if text:
            return text
    return None


@dataclass(slots=True)
class ContinuityScopeClassification:
    """Deterministic continuity scope classification result."""

    scope: ContinuityScope | str
    scope_ref: str
    reason_code: str
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.scope = _normalize_str_enum(self.scope, ContinuityScope, "scope")
        self.scope_ref = _require_non_empty_text(self.scope_ref, "scope_ref")
        self.reason_code = _require_non_empty_text(self.reason_code, "reason_code")
        self.evidence = _normalize_string_list(self.evidence, "evidence")
        self.metadata = _normalize_mapping(self.metadata, "metadata")

    def as_dict(self) -> dict[str, Any]:
        return {
            "scope": self.scope.value,
            "scope_ref": self.scope_ref,
            "reason_code": self.reason_code,
            "evidence": list(self.evidence),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContinuityScopeClassification:
        payload = _normalize_mapping(data, "data")
        return cls(
            scope=payload.get("scope", ""),
            scope_ref=payload.get("scope_ref", ""),
            reason_code=payload.get("reason_code", ""),
            evidence=payload.get("evidence", []),
            metadata=payload.get("metadata", {}),
        )


@dataclass(slots=True)
class ContinuityEventClassification:
    """Deterministic continuity event classification result."""

    event_class: ContinuityEventClass | str
    event_type: str
    reason_code: str
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.event_class = _normalize_str_enum(self.event_class, ContinuityEventClass, "event_class")
        self.event_type = _require_non_empty_text(self.event_type, "event_type")
        self.reason_code = _require_non_empty_text(self.reason_code, "reason_code")
        self.evidence = _normalize_string_list(self.evidence, "evidence")
        self.metadata = _normalize_mapping(self.metadata, "metadata")

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_class": self.event_class.value,
            "event_type": self.event_type,
            "reason_code": self.reason_code,
            "evidence": list(self.evidence),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContinuityEventClassification:
        payload = _normalize_mapping(data, "data")
        return cls(
            event_class=payload.get("event_class", "unknown"),
            event_type=payload.get("event_type", "unknown_event"),
            reason_code=payload.get("reason_code", "unknown_event_class"),
            evidence=payload.get("evidence", []),
            metadata=payload.get("metadata", {}),
        )


@dataclass(slots=True)
class ContinuityClassificationTrace:
    """Traceable continuity classification envelope for diagnostics surfaces."""

    scope_classification: ContinuityScopeClassification
    event_classification: ContinuityEventClassification
    trace_source: str
    trace_created_at: str
    continuity_confidence: ContinuityConfidence | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.trace_source = _require_non_empty_text(self.trace_source, "trace_source")
        self.trace_created_at = _require_non_empty_text(self.trace_created_at, "trace_created_at")
        self.metadata = _normalize_mapping(self.metadata, "metadata")

    def as_dict(self) -> dict[str, Any]:
        return {
            "scope_classification": self.scope_classification.as_dict(),
            "event_classification": self.event_classification.as_dict(),
            "trace_source": self.trace_source,
            "trace_created_at": self.trace_created_at,
            "continuity_confidence": (
                self.continuity_confidence.as_dict() if self.continuity_confidence is not None else None
            ),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContinuityClassificationTrace:
        payload = _normalize_mapping(data, "data")
        confidence = payload.get("continuity_confidence")
        return cls(
            scope_classification=ContinuityScopeClassification.from_dict(payload.get("scope_classification", {})),
            event_classification=ContinuityEventClassification.from_dict(payload.get("event_classification", {})),
            trace_source=payload.get("trace_source", ""),
            trace_created_at=payload.get("trace_created_at", ""),
            continuity_confidence=(
                ContinuityConfidence.from_dict(confidence)
                if isinstance(confidence, dict)
                else None
            ),
            metadata=payload.get("metadata", {}),
        )


def classify_continuity_scope(payload: dict[str, Any]) -> ContinuityScopeClassification:
    """Classify one and only one continuity scope using deterministic precedence."""
    normalized = _normalize_mapping(payload, "payload")
    evidence: list[str] = []

    explicit_scope = str(normalized.get("scope", "") or "").strip()
    if explicit_scope:
        scope = _normalize_str_enum(explicit_scope, ContinuityScope, "scope")
        scope_ref = _first_non_empty_text(
            normalized,
            [
                "scope_ref",
                "scope_id",
                "scope_key",
                "entity_id",
                "entity_ref",
                "area_id",
                "room_id",
                "room_ref",
                "person_id",
                "voice_profile_id",
                "household_id",
                "mode_id",
                "mode_ref",
                "posture",
            ],
        )
        if scope_ref is None:
            if scope is ContinuityScope.HOUSEHOLD:
                scope_ref = "household.default"
            else:
                raise ValueError("scope_ref must be provided when scope is set")
        evidence.append("scope")
        return ContinuityScopeClassification(
            scope=scope,
            scope_ref=scope_ref,
            reason_code="explicit_scope_field",
            evidence=evidence,
        )

    entity_ref = _first_non_empty_text(normalized, ["entity_id", "entity_ref", "device_entity_id"])
    room_ref = _first_non_empty_text(normalized, ["area_id", "room_id", "room_ref", "composite_id"])
    person_ref = _first_non_empty_text(normalized, ["person_id", "person_ref", "voice_profile_id", "identity_id"])
    household_ref = _first_non_empty_text(normalized, ["household_id"])
    mode_ref = _first_non_empty_text(normalized, ["mode_id", "mode_ref", "posture", "global_mode"])

    household_hint = bool(
        household_ref
        or normalized.get("guest_mode") is not None
        or normalized.get("unknown_identity") is not None
        or normalized.get("silence_is_success") is not None
        or normalized.get("capability_not_available") is not None
    )

    candidates: list[tuple[ContinuityScope, str, str, str]] = []
    if entity_ref:
        candidates.append((ContinuityScope.ENTITY, entity_ref, "entity_scope_inferred", "entity_id|entity_ref"))
    if room_ref:
        candidates.append((ContinuityScope.ROOM, room_ref, "room_scope_inferred", "area_id|room_id|composite_id"))
    if person_ref:
        candidates.append((ContinuityScope.PERSON, person_ref, "person_scope_inferred", "person_id|voice_profile_id"))
    if household_hint:
        candidates.append(
            (
                ContinuityScope.HOUSEHOLD,
                household_ref or "household.default",
                "household_scope_inferred",
                "household_policy_fields",
            )
        )
    if mode_ref:
        candidates.append((ContinuityScope.MODE, mode_ref, "mode_scope_inferred", "mode_id|mode_ref|posture"))

    precedence = [
        ContinuityScope.ENTITY,
        ContinuityScope.ROOM,
        ContinuityScope.PERSON,
        ContinuityScope.HOUSEHOLD,
        ContinuityScope.MODE,
    ]
    for selected_scope in precedence:
        for candidate in candidates:
            if candidate[0] is selected_scope:
                evidence.append(candidate[3])
                return ContinuityScopeClassification(
                    scope=candidate[0],
                    scope_ref=candidate[1],
                    reason_code=candidate[2],
                    evidence=evidence,
                    metadata={
                        "candidate_scope_count": len(candidates),
                        "candidate_scopes": [scope.value for scope, _, _, _ in candidates],
                    },
                )

    raise ValueError("unable to classify continuity scope from payload")


def classify_continuity_event(payload: dict[str, Any]) -> ContinuityEventClassification:
    """Classify continuity event categories using deterministic rules and precedence."""
    normalized = _normalize_mapping(payload, "payload")
    evidence: list[str] = []

    explicit_event_class = str(normalized.get("event_class", "") or "").strip()
    event_type = _first_non_empty_text(normalized, ["event_type", "event_name", "trigger_type", "intent_class"])
    event_type = event_type or "unknown_event"

    if explicit_event_class:
        evidence.append("event_class")
        return ContinuityEventClassification(
            event_class=_normalize_str_enum(explicit_event_class, ContinuityEventClass, "event_class"),
            event_type=event_type,
            reason_code="explicit_event_class",
            evidence=evidence,
        )

    lowered_event_type = event_type.lower()
    event_keyword_map: list[tuple[ContinuityEventClass, tuple[str, ...], str]] = [
        (ContinuityEventClass.VOICE_INTERACTION, ("voice", "conversation", "assist"), "voice_event_keyword"),
        (ContinuityEventClass.ROOM_ENTRY, ("room_entry", "entered_room", "enter_room"), "room_entry_keyword"),
        (ContinuityEventClass.ROOM_EXIT, ("room_exit", "left_room", "exit_room"), "room_exit_keyword"),
        (ContinuityEventClass.MUSIC_START, ("music_start", "media_start", "playing"), "music_start_keyword"),
        (ContinuityEventClass.MUSIC_PAUSE, ("music_pause", "media_pause", "paused"), "music_pause_keyword"),
        (ContinuityEventClass.MANUAL_STOP, ("manual_stop", "user_stop", "stop"), "manual_stop_keyword"),
        (ContinuityEventClass.COMMAND_FOLLOW_UP, ("follow_up", "followup"), "follow_up_keyword"),
        (
            ContinuityEventClass.MONITORING_QUESTION,
            ("monitoring_question", "sensor_query", "room_monitoring"),
            "monitoring_keyword",
        ),
        (
            ContinuityEventClass.IDENTITY_CONFIDENCE_CHANGE,
            ("identity_confidence", "confidence_change", "low_confidence"),
            "identity_confidence_keyword",
        ),
        (
            ContinuityEventClass.GUEST_MODE_CHANGE,
            ("guest_mode", "guest_mode_change", "guest_toggle"),
            "guest_mode_keyword",
        ),
    ]

    for event_class, keywords, reason_code in event_keyword_map:
        if any(keyword in lowered_event_type for keyword in keywords):
            evidence.append("event_type")
            return ContinuityEventClassification(
                event_class=event_class,
                event_type=event_type,
                reason_code=reason_code,
                evidence=evidence,
            )

    return ContinuityEventClassification(
        event_class=ContinuityEventClass.UNKNOWN,
        event_type=event_type,
        reason_code="unknown_event_class",
        evidence=evidence,
    )


def build_continuity_classification_trace(payload: dict[str, Any]) -> ContinuityClassificationTrace:
    """Build a deterministic scope+event classification trace envelope."""
    normalized = _normalize_mapping(payload, "payload")
    scope_classification = classify_continuity_scope(normalized)
    event_classification = classify_continuity_event(normalized)

    confidence: ContinuityConfidence | None = None
    confidence_payload = normalized.get("continuity_confidence")
    if isinstance(confidence_payload, ContinuityConfidence):
        confidence = confidence_payload
    elif isinstance(confidence_payload, dict):
        confidence = ContinuityConfidence.from_dict(confidence_payload)

    trace_created_at = _first_non_empty_text(normalized, ["occurred_at", "captured_at", "timestamp"]) or datetime.now(
        timezone.utc
    ).isoformat()
    trace_source = _first_non_empty_text(normalized, ["trace_source", "source_domain", "source"]) or "continuity_classifier"

    return ContinuityClassificationTrace(
        scope_classification=scope_classification,
        event_classification=event_classification,
        trace_source=trace_source,
        trace_created_at=trace_created_at,
        continuity_confidence=confidence,
        metadata={
            "classifier_version": "ec_a_02_v1",
        },
    )


class PreferenceResolutionTier(StrEnum):
    """Ordered preference resolution tiers governed by EC-B-01."""

    COMMAND = "command"
    GUARDRAIL = "guardrail"
    KNOWN_PERSON_PREFERENCE = "known_person_preference"
    EXPLICIT_PERSON_ROOM_EXCEPTION = "explicit_person_room_exception"
    ROOM_DEFAULT = "room_default"
    HOUSEHOLD_DEFAULT = "household_default"
    SYSTEM_SAFE_DEFAULT = "system_safe_default"


class PreferenceIdentityState(StrEnum):
    """Policy states used to gate personalized preference application."""

    KNOWN = "known"
    GUEST = "guest"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"
    LOW_CONFIDENCE = "low_confidence"


def _normalize_any_dict_list(value: Any, field_name: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        normalized.append(dict(item))
    return normalized


@dataclass(slots=True)
class PreferenceResolutionRequest:
    """Input contract for deterministic preference resolution."""

    preference_key: str
    identity_state: PreferenceIdentityState | str
    confidence_band: ContinuityConfidenceBand | str | None = None
    command_value: Any = None
    guardrail_value: Any = None
    person_preference_value: Any = None
    person_room_exception_value: Any = None
    room_default_value: Any = None
    household_default_value: Any = None
    system_safe_value: Any = None
    person_room_exception_enabled: bool = False
    personalization_policy_allowed: bool = True
    personalization_policy_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.preference_key = _require_non_empty_text(self.preference_key, "preference_key")
        self.identity_state = _normalize_str_enum(self.identity_state, PreferenceIdentityState, "identity_state")
        self.confidence_band = (
            _normalize_str_enum(self.confidence_band, ContinuityConfidenceBand, "confidence_band")
            if self.confidence_band is not None
            else None
        )
        self.person_room_exception_enabled = bool(self.person_room_exception_enabled)
        self.personalization_policy_allowed = bool(self.personalization_policy_allowed)
        self.personalization_policy_reason = _normalize_optional_text(self.personalization_policy_reason)
        self.metadata = _normalize_mapping(self.metadata, "metadata")
        if self.system_safe_value is None:
            raise ValueError("system_safe_value must be provided")

    def as_dict(self) -> dict[str, Any]:
        return {
            "preference_key": self.preference_key,
            "identity_state": self.identity_state.value,
            "confidence_band": self.confidence_band.value if self.confidence_band is not None else None,
            "command_value": self.command_value,
            "guardrail_value": self.guardrail_value,
            "person_preference_value": self.person_preference_value,
            "person_room_exception_value": self.person_room_exception_value,
            "room_default_value": self.room_default_value,
            "household_default_value": self.household_default_value,
            "system_safe_value": self.system_safe_value,
            "person_room_exception_enabled": self.person_room_exception_enabled,
            "personalization_policy_allowed": self.personalization_policy_allowed,
            "personalization_policy_reason": self.personalization_policy_reason,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PreferenceResolutionRequest:
        payload = _normalize_mapping(data, "data")
        return cls(
            preference_key=payload.get("preference_key", ""),
            identity_state=payload.get("identity_state", ""),
            confidence_band=payload.get("confidence_band"),
            command_value=payload.get("command_value"),
            guardrail_value=payload.get("guardrail_value"),
            person_preference_value=payload.get("person_preference_value"),
            person_room_exception_value=payload.get("person_room_exception_value"),
            room_default_value=payload.get("room_default_value"),
            household_default_value=payload.get("household_default_value"),
            system_safe_value=payload.get("system_safe_value"),
            person_room_exception_enabled=payload.get("person_room_exception_enabled", False),
            personalization_policy_allowed=payload.get("personalization_policy_allowed", True),
            personalization_policy_reason=payload.get("personalization_policy_reason"),
            metadata=payload.get("metadata", {}),
        )


@dataclass(slots=True)
class PreferenceResolutionOutcome:
    """Deterministic preference resolution outcome with explainability metadata."""

    preference_key: str
    selected_tier: PreferenceResolutionTier | str
    selected_scope: str
    selected_value: Any
    evaluation_path: list[dict[str, Any]] = field(default_factory=list)
    applied_policy: dict[str, Any] = field(default_factory=dict)
    identity_decision: dict[str, Any] = field(default_factory=dict)
    fallback_reason: str | None = None
    ownership_boundary: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.preference_key = _require_non_empty_text(self.preference_key, "preference_key")
        self.selected_tier = _normalize_str_enum(self.selected_tier, PreferenceResolutionTier, "selected_tier")
        self.selected_scope = _require_non_empty_text(self.selected_scope, "selected_scope")
        self.evaluation_path = _normalize_any_dict_list(self.evaluation_path, "evaluation_path")
        self.applied_policy = _normalize_mapping(self.applied_policy, "applied_policy")
        self.identity_decision = _normalize_mapping(self.identity_decision, "identity_decision")
        self.fallback_reason = _normalize_optional_text(self.fallback_reason)
        self.ownership_boundary = _normalize_mapping(self.ownership_boundary, "ownership_boundary")
        self.metadata = _normalize_mapping(self.metadata, "metadata")

    def as_dict(self) -> dict[str, Any]:
        return {
            "preference_key": self.preference_key,
            "selected_tier": self.selected_tier.value,
            "selected_scope": self.selected_scope,
            "selected_value": self.selected_value,
            "evaluation_path": [dict(step) for step in self.evaluation_path],
            "applied_policy": dict(self.applied_policy),
            "identity_decision": dict(self.identity_decision),
            "fallback_reason": self.fallback_reason,
            "ownership_boundary": dict(self.ownership_boundary),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PreferenceResolutionOutcome:
        payload = _normalize_mapping(data, "data")
        return cls(
            preference_key=payload.get("preference_key", ""),
            selected_tier=payload.get("selected_tier", "system_safe_default"),
            selected_scope=payload.get("selected_scope", "system"),
            selected_value=payload.get("selected_value"),
            evaluation_path=payload.get("evaluation_path", []),
            applied_policy=payload.get("applied_policy", {}),
            identity_decision=payload.get("identity_decision", {}),
            fallback_reason=payload.get("fallback_reason"),
            ownership_boundary=payload.get("ownership_boundary", {}),
            metadata=payload.get("metadata", {}),
        )


class LearningOwnershipScope(StrEnum):
    """Permitted ownership scopes for governed learning writes."""

    PERSON = "person"
    ROOM = "room"
    HOUSEHOLD = "household"


class LearningWritePath(StrEnum):
    """Write dispositions for learning decisions."""

    NONE = "none"
    ASYNC = "async"


@dataclass(slots=True)
class LearningPolicyEvaluationRequest:
    """Input contract for deterministic EC-B-03 learning eligibility evaluation."""

    learning_key: str
    ownership_scope: LearningOwnershipScope | str
    identity_state: PreferenceIdentityState | str
    confidence_band: ContinuityConfidenceBand | str | None = None
    learning_policy_enabled: bool = True
    ownership_supported: bool = True
    entity_eligible: bool = True
    preference_eligible: bool = True
    safety_restrictions_clear: bool = True
    identity_sensitive_learning: bool = True
    personalization_policy_allowed: bool = True
    policy_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.learning_key = _require_non_empty_text(self.learning_key, "learning_key")
        self.ownership_scope = _normalize_str_enum(self.ownership_scope, LearningOwnershipScope, "ownership_scope")
        self.identity_state = _normalize_str_enum(self.identity_state, PreferenceIdentityState, "identity_state")
        self.confidence_band = (
            _normalize_str_enum(self.confidence_band, ContinuityConfidenceBand, "confidence_band")
            if self.confidence_band is not None
            else None
        )
        self.learning_policy_enabled = bool(self.learning_policy_enabled)
        self.ownership_supported = bool(self.ownership_supported)
        self.entity_eligible = bool(self.entity_eligible)
        self.preference_eligible = bool(self.preference_eligible)
        self.safety_restrictions_clear = bool(self.safety_restrictions_clear)
        self.identity_sensitive_learning = bool(self.identity_sensitive_learning)
        self.personalization_policy_allowed = bool(self.personalization_policy_allowed)
        self.policy_reason = _normalize_optional_text(self.policy_reason)
        self.metadata = _normalize_mapping(self.metadata, "metadata")

    def as_dict(self) -> dict[str, Any]:
        return {
            "learning_key": self.learning_key,
            "ownership_scope": self.ownership_scope.value,
            "identity_state": self.identity_state.value,
            "confidence_band": self.confidence_band.value if self.confidence_band is not None else None,
            "learning_policy_enabled": self.learning_policy_enabled,
            "ownership_supported": self.ownership_supported,
            "entity_eligible": self.entity_eligible,
            "preference_eligible": self.preference_eligible,
            "safety_restrictions_clear": self.safety_restrictions_clear,
            "identity_sensitive_learning": self.identity_sensitive_learning,
            "personalization_policy_allowed": self.personalization_policy_allowed,
            "policy_reason": self.policy_reason,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LearningPolicyEvaluationRequest:
        payload = _normalize_mapping(data, "data")
        return cls(
            learning_key=payload.get("learning_key", ""),
            ownership_scope=payload.get("ownership_scope", "room"),
            identity_state=payload.get("identity_state", "unknown"),
            confidence_band=payload.get("confidence_band"),
            learning_policy_enabled=payload.get("learning_policy_enabled", True),
            ownership_supported=payload.get("ownership_supported", True),
            entity_eligible=payload.get("entity_eligible", True),
            preference_eligible=payload.get("preference_eligible", True),
            safety_restrictions_clear=payload.get("safety_restrictions_clear", True),
            identity_sensitive_learning=payload.get("identity_sensitive_learning", True),
            personalization_policy_allowed=payload.get("personalization_policy_allowed", True),
            policy_reason=payload.get("policy_reason"),
            metadata=payload.get("metadata", {}),
        )


@dataclass(slots=True)
class LearningPolicyEvaluationOutcome:
    """Governed EC-B-03 learning decision output."""

    learning_key: str
    learning_allowed: bool
    denial_reason: str | None
    ownership_scope: LearningOwnershipScope | str
    write_path: LearningWritePath | str
    policy_decision: dict[str, Any] = field(default_factory=dict)
    reversibility_metadata: dict[str, Any] = field(default_factory=dict)
    explainability: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.learning_key = _require_non_empty_text(self.learning_key, "learning_key")
        self.learning_allowed = bool(self.learning_allowed)
        self.denial_reason = _normalize_optional_text(self.denial_reason)
        self.ownership_scope = _normalize_str_enum(self.ownership_scope, LearningOwnershipScope, "ownership_scope")
        self.write_path = _normalize_str_enum(self.write_path, LearningWritePath, "write_path")
        self.policy_decision = _normalize_mapping(self.policy_decision, "policy_decision")
        self.reversibility_metadata = _normalize_mapping(
            self.reversibility_metadata,
            "reversibility_metadata",
        )
        self.explainability = _normalize_mapping(self.explainability, "explainability")
        self.metadata = _normalize_mapping(self.metadata, "metadata")

    def as_dict(self) -> dict[str, Any]:
        return {
            "learning_key": self.learning_key,
            "learning_allowed": self.learning_allowed,
            "denial_reason": self.denial_reason,
            "ownership_scope": self.ownership_scope.value,
            "write_path": self.write_path.value,
            "policy_decision": dict(self.policy_decision),
            "reversibility_metadata": dict(self.reversibility_metadata),
            "explainability": dict(self.explainability),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LearningPolicyEvaluationOutcome:
        payload = _normalize_mapping(data, "data")
        return cls(
            learning_key=payload.get("learning_key", ""),
            learning_allowed=payload.get("learning_allowed", False),
            denial_reason=payload.get("denial_reason"),
            ownership_scope=payload.get("ownership_scope", "room"),
            write_path=payload.get("write_path", "none"),
            policy_decision=payload.get("policy_decision", {}),
            reversibility_metadata=payload.get("reversibility_metadata", {}),
            explainability=payload.get("explainability", {}),
            metadata=payload.get("metadata", {}),
        )


@dataclass(slots=True)
class LearningWriteRequest:
    """Write contract for asynchronous governed learning persistence."""

    learning_event_id: str
    learning_key: str
    ownership_scope: LearningOwnershipScope | str
    owner_ref: str
    learned_value: Any
    reason_code: str
    policy_used: str
    reversibility_metadata: dict[str, Any] = field(default_factory=dict)
    explainability: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.learning_event_id = _require_non_empty_text(self.learning_event_id, "learning_event_id")
        self.learning_key = _require_non_empty_text(self.learning_key, "learning_key")
        self.ownership_scope = _normalize_str_enum(self.ownership_scope, LearningOwnershipScope, "ownership_scope")
        self.owner_ref = _require_non_empty_text(self.owner_ref, "owner_ref")
        self.reason_code = _require_non_empty_text(self.reason_code, "reason_code")
        self.policy_used = _require_non_empty_text(self.policy_used, "policy_used")
        self.reversibility_metadata = _normalize_mapping(
            self.reversibility_metadata,
            "reversibility_metadata",
        )
        self.explainability = _normalize_mapping(self.explainability, "explainability")
        self.metadata = _normalize_mapping(self.metadata, "metadata")

    def as_dict(self) -> dict[str, Any]:
        return {
            "learning_event_id": self.learning_event_id,
            "learning_key": self.learning_key,
            "ownership_scope": self.ownership_scope.value,
            "owner_ref": self.owner_ref,
            "learned_value": self.learned_value,
            "reason_code": self.reason_code,
            "policy_used": self.policy_used,
            "reversibility_metadata": dict(self.reversibility_metadata),
            "explainability": dict(self.explainability),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LearningWriteRequest:
        payload = _normalize_mapping(data, "data")
        return cls(
            learning_event_id=payload.get("learning_event_id", ""),
            learning_key=payload.get("learning_key", ""),
            ownership_scope=payload.get("ownership_scope", "room"),
            owner_ref=payload.get("owner_ref", ""),
            learned_value=payload.get("learned_value"),
            reason_code=payload.get("reason_code", ""),
            policy_used=payload.get("policy_used", ""),
            reversibility_metadata=payload.get("reversibility_metadata", {}),
            explainability=payload.get("explainability", {}),
            metadata=payload.get("metadata", {}),
        )


@dataclass(slots=True)
class RoomConfig:
    """Room-scoped configuration and alias mappings."""

    area_id: str
    aliases: dict[str, str] = field(default_factory=dict)
    global_overlays: dict[str, bool] = field(default_factory=dict)
    posture: str = "day"
    media_player_entity_ids: list[str] = field(default_factory=list)
    voice_device_entity_ids: list[str] = field(default_factory=list)
    tts_voice: str = ""
    tts_language: str = ""
    ai_knowledge_enabled: bool = False
    environment_information_outputs: list[str] = field(default_factory=list)
    device_groups: list[dict[str, Any]] = field(default_factory=list)
    asset_groups: list[dict[str, Any]] = field(default_factory=list)
    room_sensor_entity_ids: list[str] = field(default_factory=list)
    room_health_entity_ids: list[str] = field(default_factory=list)
    human_health_entity_ids: list[str] = field(default_factory=list)
    light_entity_ids: list[str] = field(default_factory=list)
    lamp_entity_ids: list[str] = field(default_factory=list)
    shade_entity_ids: list[str] = field(default_factory=list)
    speaker_entity_ids: list[str] = field(default_factory=list)
    tv_entity_ids: list[str] = field(default_factory=list)
    dashboard_entity_ids: list[str] = field(default_factory=list)
    other_entity_ids: list[str] = field(default_factory=list)
    weather_source_entity_ids: list[str] = field(default_factory=list)
    news_source_entity_ids: list[str] = field(default_factory=list)
    persona: str = ""
    persona_prompt: str = ""


@dataclass(slots=True)
class IdentityProfile:
    """Identity-specific presentation preferences."""

    profile_id: str
    name: str
    persona: str
    tts_voice: str
    verbosity: str
    allow_ai: bool
    content_type: str
    detail_level: str


@dataclass(slots=True)
class PersonProfile:
    """Person identity, consent, and device binding state."""

    person_id: str
    name: str
    linked_area_id: str | None = None
    ble_device_ids: list[str] = field(default_factory=list)
    aqara_presence_entity_ids: list[str] = field(default_factory=list)
    voice_profile_id: str | None = None
    consent: dict[str, Any] = field(default_factory=dict)
    mobile_notify_targets: list[str] = field(default_factory=list)
    preferred_mobile_target: str | None = None
    mobile_voice_endpoint_enabled: bool = False
    is_minor: bool = False
    guardian_controls_required: bool = False
    minor_allow_general_qna: bool = False
    minor_allowed_intent_classes: list[str] = field(default_factory=list)
    minor_content_filter_level: str = "strict"
    email_source_ref: str = ""
    calendar_source_ref: str = ""
    task_source_ref: str = ""
    shopping_source_ref: str = ""
    email_source_bindings: list[dict[str, Any]] = field(default_factory=list)
    calendar_source_bindings: list[dict[str, Any]] = field(default_factory=list)
    task_source_bindings: list[dict[str, Any]] = field(default_factory=list)
    shopping_source_bindings: list[dict[str, Any]] = field(default_factory=list)
    notes: str = ""


@dataclass(slots=True)
class VoiceProfile:
    """Voice enrollment and speaker attribution state."""

    voice_profile_id: str
    name: str
    tts_voice: str = ""
    enrollment_state: str = "untrained"
    enrollment_source: str = ""
    speaker_embedding_id: str = ""
    sample_count: int = 0
    sample_items: list[dict[str, Any]] = field(default_factory=list)
    attribution_confidence: float | None = None
    enrollment_started_at: str = ""
    last_sample_at: str = ""
    last_built_at: str = ""
    disabled: bool = False
    consent: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EnrollmentSession:
    """Enrollment session scaffolding state for deterministic lifecycle ownership."""

    session_id: str
    person_id: str
    voice_profile_id: str
    state: str
    created_at: str
    updated_at: str
    sample_count: int = 0
    sample_items: list[dict[str, Any]] = field(default_factory=list)
    enrollment_started_at: str = ""
    last_sample_at: str = ""
    last_built_at: str = ""
    cleanup_status: str = "not_started"
    capture_provider: str = "browser_microphone"
    last_error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Interaction:
    """Runtime interaction surfaced to UI/voice channels."""

    interaction_id: str
    area_id: str | None
    message: str
    level: str
    state: str
    priority: int


@dataclass(slots=True)
class SignalState:
    """Signal payload exposed by provider integrations."""

    signal_type: str
    available: bool
    summary: str
    state: str


@dataclass(slots=True)
class ContextState:
    """Global context payload exposed by provider integrations."""

    context_type: str
    available: bool
    summary: str
    detail: str
    speakable: str


@dataclass(slots=True)
class ActivityEvent:
    """Stitched orchestration activity event record."""

    activity_id: str
    correlation_id: str
    started_at: str
    channel: str
    actor_class: str
    intent_class: str
    request_summary: str
    resolved_person_id: str | None = None
    resolved_area_id: str | None = None
    confidence: float | None = None
    external_refs: list[dict[str, Any]] = field(default_factory=list)
    ended_at: str | None = None
    outcome: str | None = None
    outcome_reason: str = ""
    actions_taken: list[str] = field(default_factory=list)
    policy_gates: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CompositeConfig:
    """Merged-room (composite) configuration."""

    composite_id: str
    name: str
    floor_id: str | None = None
    area_ids: list[str] = field(default_factory=list)
    primary_area: str | None = None
    enabled: bool = True
    posture: str = "day"
    media_player_entity_ids: list[str] = field(default_factory=list)
    voice_device_entity_ids: list[str] = field(default_factory=list)
    tts_voice: str = ""
    tts_language: str = ""
    device_groups: list[dict[str, Any]] = field(default_factory=list)
    persona: str = ""
    persona_prompt: str = ""
    ai_knowledge_enabled: bool = False
    environment_information_outputs: list[str] = field(default_factory=list)
    asset_groups: list[dict[str, Any]] = field(default_factory=list)
    room_sensor_entity_ids: list[str] = field(default_factory=list)
    room_health_entity_ids: list[str] = field(default_factory=list)
    human_health_entity_ids: list[str] = field(default_factory=list)
    light_entity_ids: list[str] = field(default_factory=list)
    shade_entity_ids: list[str] = field(default_factory=list)
    speaker_entity_ids: list[str] = field(default_factory=list)
    dashboard_entity_ids: list[str] = field(default_factory=list)
    other_entity_ids: list[str] = field(default_factory=list)
    weather_source_entity_ids: list[str] = field(default_factory=list)
    news_source_entity_ids: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class ConciergeState:
    """Persisted Concierge foundation state."""

    rooms: dict[str, RoomConfig] = field(default_factory=dict)
    composites: dict[str, CompositeConfig] = field(default_factory=dict)
    interactions: dict[str, Interaction] = field(default_factory=dict)
    global_context_usage: dict[str, dict[str, Any]] = field(default_factory=dict)
    execution_preferences: dict[str, dict[str, Any]] = field(default_factory=dict)
    signals: dict[str, SignalState] = field(default_factory=dict)
    contexts: dict[str, ContextState] = field(default_factory=dict)
    experience_snapshots: dict[str, ExperienceSnapshot] = field(default_factory=dict)
    usual_states: dict[str, UsualState] = field(default_factory=dict)
    activities: dict[str, ActivityEvent] = field(default_factory=dict)
    default_person_profile: PersonProfile | None = None
    person_profiles: dict[str, PersonProfile] = field(default_factory=dict)
    default_voice_profile: VoiceProfile | None = None
    voice_profiles: dict[str, VoiceProfile] = field(default_factory=dict)
    enrollment_sessions: dict[str, EnrollmentSession] = field(default_factory=dict)
    default_identity_profile: IdentityProfile | None = None
    identity_profiles: dict[str, IdentityProfile] = field(default_factory=dict)
    global_features: dict[str, dict[str, Any]] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Serialize state for Home Assistant storage."""
        return {
            "rooms": {
                area_id: {
                    "area_id": room.area_id,
                    "aliases": room.aliases,
                    "global_overlays": room.global_overlays,
                    "posture": room.posture,
                    "media_player_entity_ids": room.media_player_entity_ids,
                    "voice_device_entity_ids": room.voice_device_entity_ids,
                    "tts_voice": room.tts_voice,
                    "tts_language": room.tts_language,
                    "ai_knowledge_enabled": room.ai_knowledge_enabled,
                    "environment_information_outputs": room.environment_information_outputs,
                    "device_groups": room.device_groups,
                    "asset_groups": room.asset_groups,
                    "room_sensor_entity_ids": room.room_sensor_entity_ids,
                    "room_health_entity_ids": room.room_health_entity_ids,
                    "human_health_entity_ids": room.human_health_entity_ids,
                    "light_entity_ids": room.light_entity_ids,
                    "lamp_entity_ids": room.lamp_entity_ids,
                    "shade_entity_ids": room.shade_entity_ids,
                    "speaker_entity_ids": room.speaker_entity_ids,
                    "tv_entity_ids": room.tv_entity_ids,
                    "dashboard_entity_ids": room.dashboard_entity_ids,
                    "other_entity_ids": room.other_entity_ids,
                    "weather_source_entity_ids": room.weather_source_entity_ids,
                    "news_source_entity_ids": room.news_source_entity_ids,
                    "persona": room.persona,
                    "persona_prompt": room.persona_prompt,
                }
                for area_id, room in self.rooms.items()
            },
            "composites": {
                composite_id: {
                    "composite_id": composite.composite_id,
                    "name": composite.name,
                    "floor_id": composite.floor_id,
                    "area_ids": composite.area_ids,
                    "primary_area": composite.primary_area,
                    "enabled": composite.enabled,
                    "posture": composite.posture,
                    "media_player_entity_ids": composite.media_player_entity_ids,
                    "voice_device_entity_ids": composite.voice_device_entity_ids,
                    "tts_voice": composite.tts_voice,
                    "tts_language": composite.tts_language,
                    "device_groups": composite.device_groups,
                    "persona": composite.persona,
                    "persona_prompt": composite.persona_prompt,
                    "ai_knowledge_enabled": composite.ai_knowledge_enabled,
                    "environment_information_outputs": composite.environment_information_outputs,
                    "asset_groups": composite.asset_groups,
                    "room_sensor_entity_ids": composite.room_sensor_entity_ids,
                    "room_health_entity_ids": composite.room_health_entity_ids,
                    "human_health_entity_ids": composite.human_health_entity_ids,
                    "light_entity_ids": composite.light_entity_ids,
                    "shade_entity_ids": composite.shade_entity_ids,
                    "speaker_entity_ids": composite.speaker_entity_ids,
                    "dashboard_entity_ids": composite.dashboard_entity_ids,
                    "other_entity_ids": composite.other_entity_ids,
                    "weather_source_entity_ids": composite.weather_source_entity_ids,
                    "news_source_entity_ids": composite.news_source_entity_ids,
                    "created_at": composite.created_at,
                    "updated_at": composite.updated_at,
                }
                for composite_id, composite in self.composites.items()
            },
            "interactions": {
                interaction_id: {
                    "interaction_id": interaction.interaction_id,
                    "area_id": interaction.area_id,
                    "message": interaction.message,
                    "level": interaction.level,
                    "state": interaction.state,
                    "priority": interaction.priority,
                }
                for interaction_id, interaction in self.interactions.items()
            },
            "global_context_usage": self.global_context_usage,
            "execution_preferences": self.execution_preferences,
            "signals": {
                signal_type: {
                    "signal_type": signal.signal_type,
                    "available": signal.available,
                    "summary": signal.summary,
                    "state": signal.state,
                }
                for signal_type, signal in self.signals.items()
            },
            "contexts": {
                context_type: {
                    "context_type": context.context_type,
                    "available": context.available,
                    "summary": context.summary,
                    "detail": context.detail,
                    "speakable": context.speakable,
                }
                for context_type, context in self.contexts.items()
            },
            "experience_snapshots": {
                snapshot_id: snapshot.as_dict()
                for snapshot_id, snapshot in self.experience_snapshots.items()
            },
            "usual_states": {
                state_id: usual_state.as_dict()
                for state_id, usual_state in self.usual_states.items()
            },
            "default_person_profile": (
                {
                    "person_id": self.default_person_profile.person_id,
                    "name": self.default_person_profile.name,
                    "linked_area_id": self.default_person_profile.linked_area_id,
                    "ble_device_ids": self.default_person_profile.ble_device_ids,
                    "aqara_presence_entity_ids": self.default_person_profile.aqara_presence_entity_ids,
                    "voice_profile_id": self.default_person_profile.voice_profile_id,
                    "consent": self.default_person_profile.consent,
                    "mobile_notify_targets": self.default_person_profile.mobile_notify_targets,
                    "preferred_mobile_target": self.default_person_profile.preferred_mobile_target,
                    "mobile_voice_endpoint_enabled": self.default_person_profile.mobile_voice_endpoint_enabled,
                    "is_minor": self.default_person_profile.is_minor,
                    "guardian_controls_required": self.default_person_profile.guardian_controls_required,
                    "minor_allow_general_qna": self.default_person_profile.minor_allow_general_qna,
                    "minor_allowed_intent_classes": self.default_person_profile.minor_allowed_intent_classes,
                    "minor_content_filter_level": self.default_person_profile.minor_content_filter_level,
                    "email_source_ref": self.default_person_profile.email_source_ref,
                    "calendar_source_ref": self.default_person_profile.calendar_source_ref,
                    "task_source_ref": self.default_person_profile.task_source_ref,
                    "shopping_source_ref": self.default_person_profile.shopping_source_ref,
                    "email_source_bindings": self.default_person_profile.email_source_bindings,
                    "calendar_source_bindings": self.default_person_profile.calendar_source_bindings,
                    "task_source_bindings": self.default_person_profile.task_source_bindings,
                    "shopping_source_bindings": self.default_person_profile.shopping_source_bindings,
                    "notes": self.default_person_profile.notes,
                }
                if self.default_person_profile is not None
                else None
            ),
            "person_profiles": {
                person_id: {
                    "person_id": profile.person_id,
                    "name": profile.name,
                    "linked_area_id": profile.linked_area_id,
                    "ble_device_ids": profile.ble_device_ids,
                    "aqara_presence_entity_ids": profile.aqara_presence_entity_ids,
                    "voice_profile_id": profile.voice_profile_id,
                    "consent": profile.consent,
                    "mobile_notify_targets": profile.mobile_notify_targets,
                    "preferred_mobile_target": profile.preferred_mobile_target,
                    "mobile_voice_endpoint_enabled": profile.mobile_voice_endpoint_enabled,
                    "is_minor": profile.is_minor,
                    "guardian_controls_required": profile.guardian_controls_required,
                    "minor_allow_general_qna": profile.minor_allow_general_qna,
                    "minor_allowed_intent_classes": profile.minor_allowed_intent_classes,
                    "minor_content_filter_level": profile.minor_content_filter_level,
                    "email_source_ref": profile.email_source_ref,
                    "calendar_source_ref": profile.calendar_source_ref,
                    "task_source_ref": profile.task_source_ref,
                    "shopping_source_ref": profile.shopping_source_ref,
                    "email_source_bindings": profile.email_source_bindings,
                    "calendar_source_bindings": profile.calendar_source_bindings,
                    "task_source_bindings": profile.task_source_bindings,
                    "shopping_source_bindings": profile.shopping_source_bindings,
                    "notes": profile.notes,
                }
                for person_id, profile in self.person_profiles.items()
            },
            "activities": {
                activity_id: {
                    "activity_id": activity.activity_id,
                    "correlation_id": activity.correlation_id,
                    "started_at": activity.started_at,
                    "channel": activity.channel,
                    "actor_class": activity.actor_class,
                    "intent_class": activity.intent_class,
                    "request_summary": activity.request_summary,
                    "resolved_person_id": activity.resolved_person_id,
                    "resolved_area_id": activity.resolved_area_id,
                    "confidence": activity.confidence,
                    "external_refs": activity.external_refs,
                    "ended_at": activity.ended_at,
                    "outcome": activity.outcome,
                    "outcome_reason": activity.outcome_reason,
                    "actions_taken": activity.actions_taken,
                    "policy_gates": activity.policy_gates,
                }
                for activity_id, activity in self.activities.items()
            },
            "default_voice_profile": (
                {
                    "voice_profile_id": self.default_voice_profile.voice_profile_id,
                    "name": self.default_voice_profile.name,
                    "tts_voice": self.default_voice_profile.tts_voice,
                    "enrollment_state": self.default_voice_profile.enrollment_state,
                    "enrollment_source": self.default_voice_profile.enrollment_source,
                    "speaker_embedding_id": self.default_voice_profile.speaker_embedding_id,
                    "sample_count": self.default_voice_profile.sample_count,
                    "sample_items": self.default_voice_profile.sample_items,
                    "attribution_confidence": self.default_voice_profile.attribution_confidence,
                    "enrollment_started_at": self.default_voice_profile.enrollment_started_at,
                    "last_sample_at": self.default_voice_profile.last_sample_at,
                    "last_built_at": self.default_voice_profile.last_built_at,
                    "disabled": self.default_voice_profile.disabled,
                    "consent": self.default_voice_profile.consent,
                }
                if self.default_voice_profile is not None
                else None
            ),
            "voice_profiles": {
                voice_profile_id: {
                    "voice_profile_id": profile.voice_profile_id,
                    "name": profile.name,
                    "tts_voice": profile.tts_voice,
                    "enrollment_state": profile.enrollment_state,
                    "enrollment_source": profile.enrollment_source,
                    "speaker_embedding_id": profile.speaker_embedding_id,
                    "sample_count": profile.sample_count,
                    "sample_items": profile.sample_items,
                    "attribution_confidence": profile.attribution_confidence,
                    "enrollment_started_at": profile.enrollment_started_at,
                    "last_sample_at": profile.last_sample_at,
                    "last_built_at": profile.last_built_at,
                    "disabled": profile.disabled,
                    "consent": profile.consent,
                }
                for voice_profile_id, profile in self.voice_profiles.items()
            },
            "enrollment_sessions": {
                session_id: {
                    "session_id": session.session_id,
                    "person_id": session.person_id,
                    "voice_profile_id": session.voice_profile_id,
                    "state": session.state,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "sample_count": session.sample_count,
                    "sample_items": session.sample_items,
                    "enrollment_started_at": session.enrollment_started_at,
                    "last_sample_at": session.last_sample_at,
                    "last_built_at": session.last_built_at,
                    "cleanup_status": session.cleanup_status,
                    "capture_provider": session.capture_provider,
                    "last_error": session.last_error,
                    "metadata": session.metadata,
                }
                for session_id, session in self.enrollment_sessions.items()
            },
            "default_identity_profile": (
                {
                    "profile_id": self.default_identity_profile.profile_id,
                    "name": self.default_identity_profile.name,
                    "persona": self.default_identity_profile.persona,
                    "tts_voice": self.default_identity_profile.tts_voice,
                    "verbosity": self.default_identity_profile.verbosity,
                    "allow_ai": self.default_identity_profile.allow_ai,
                    "content_type": self.default_identity_profile.content_type,
                    "detail_level": self.default_identity_profile.detail_level,
                }
                if self.default_identity_profile is not None
                else None
            ),
            "identity_profiles": {
                profile_id: {
                    "profile_id": profile.profile_id,
                    "name": profile.name,
                    "persona": profile.persona,
                    "tts_voice": profile.tts_voice,
                    "verbosity": profile.verbosity,
                    "allow_ai": profile.allow_ai,
                    "content_type": profile.content_type,
                    "detail_level": profile.detail_level,
                }
                for profile_id, profile in self.identity_profiles.items()
            },
            "global_features": self.global_features,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConciergeState:
        """Deserialize state from Home Assistant storage."""
        rooms_data = data.get("rooms", {})
        composites_data = data.get("composites", {})
        interactions_data = data.get("interactions", {})
        signals_data = data.get("signals", {})
        contexts_data = data.get("contexts", {})
        experience_snapshots_data = data.get("experience_snapshots", {})
        usual_states_data = data.get("usual_states", {})
        activities_data = data.get("activities", {})
        default_person_data = data.get("default_person_profile")
        person_profiles_data = data.get("person_profiles", {})
        default_voice_data = data.get("default_voice_profile")
        voice_profiles_data = data.get("voice_profiles", {})
        enrollment_sessions_data = data.get("enrollment_sessions", {})
        default_identity_data = data.get("default_identity_profile")
        identity_profiles_data = data.get("identity_profiles", {})

        return cls(
            rooms={
                area_id: RoomConfig(
                    area_id=payload.get("area_id", area_id),
                    aliases=dict(payload.get("aliases", {})),
                    global_overlays=dict(payload.get("global_overlays", {})),
                    posture=payload.get("posture", "day"),
                    media_player_entity_ids=list(payload.get("media_player_entity_ids", [])),
                    voice_device_entity_ids=list(payload.get("voice_device_entity_ids", [])),
                    tts_voice=payload.get("tts_voice", ""),
                    tts_language=payload.get("tts_language", ""),
                    ai_knowledge_enabled=bool(payload.get("ai_knowledge_enabled", False)),
                    environment_information_outputs=list(payload.get("environment_information_outputs", [])),
                    device_groups=_normalize_device_groups(payload.get("device_groups", [])),
                    asset_groups=_normalize_asset_groups(payload.get("asset_groups", []), payload.get("asset_entity_ids", [])),
                    room_sensor_entity_ids=list(payload.get("room_sensor_entity_ids", [])),
                    room_health_entity_ids=list(payload.get("room_health_entity_ids", [])),
                    human_health_entity_ids=list(payload.get("human_health_entity_ids", [])),
                    light_entity_ids=list(payload.get("light_entity_ids", [])),
                    lamp_entity_ids=list(payload.get("lamp_entity_ids", [])),
                    shade_entity_ids=list(payload.get("shade_entity_ids", [])),
                    speaker_entity_ids=list(payload.get("speaker_entity_ids", [])),
                    tv_entity_ids=list(payload.get("tv_entity_ids", [])),
                    dashboard_entity_ids=list(payload.get("dashboard_entity_ids", [])),
                    other_entity_ids=list(payload.get("other_entity_ids", [])),
                    weather_source_entity_ids=list(payload.get("weather_source_entity_ids", [])),
                    news_source_entity_ids=list(payload.get("news_source_entity_ids", [])),
                    persona=payload.get("persona", ""),
                    persona_prompt=payload.get("persona_prompt", ""),
                )
                for area_id, payload in rooms_data.items()
                if isinstance(payload, dict)
            },
            composites={
                composite_id: CompositeConfig(
                    composite_id=payload.get("composite_id", composite_id),
                    name=payload.get("name", composite_id),
                    floor_id=payload.get("floor_id"),
                    area_ids=list(payload.get("area_ids", [])),
                    primary_area=payload.get("primary_area"),
                    enabled=bool(payload.get("enabled", True)),
                    posture=payload.get("posture", "day"),
                    media_player_entity_ids=list(payload.get("media_player_entity_ids", [])),
                    voice_device_entity_ids=list(payload.get("voice_device_entity_ids", [])),
                    tts_voice=payload.get("tts_voice", ""),
                    tts_language=payload.get("tts_language", ""),
                    device_groups=_normalize_device_groups(payload.get("device_groups", [])),
                    persona=payload.get("persona", ""),
                    persona_prompt=payload.get("persona_prompt", ""),
                    ai_knowledge_enabled=bool(payload.get("ai_knowledge_enabled", False)),
                    environment_information_outputs=list(payload.get("environment_information_outputs", [])),
                    asset_groups=_normalize_asset_groups(payload.get("asset_groups", []), payload.get("asset_entity_ids", [])),
                    room_sensor_entity_ids=list(payload.get("room_sensor_entity_ids", [])),
                    room_health_entity_ids=list(payload.get("room_health_entity_ids", [])),
                    human_health_entity_ids=list(payload.get("human_health_entity_ids", [])),
                    light_entity_ids=list(payload.get("light_entity_ids", [])),
                    shade_entity_ids=list(payload.get("shade_entity_ids", [])),
                    speaker_entity_ids=list(payload.get("speaker_entity_ids", [])),
                    dashboard_entity_ids=list(payload.get("dashboard_entity_ids", [])),
                    other_entity_ids=list(payload.get("other_entity_ids", [])),
                    weather_source_entity_ids=list(payload.get("weather_source_entity_ids", [])),
                    news_source_entity_ids=list(payload.get("news_source_entity_ids", [])),
                    created_at=payload.get("created_at", ""),
                    updated_at=payload.get("updated_at", ""),
                )
                for composite_id, payload in composites_data.items()
                if isinstance(payload, dict)
            },
            interactions={
                interaction_id: Interaction(
                    interaction_id=payload.get("interaction_id", interaction_id),
                    area_id=payload.get("area_id"),
                    message=payload.get("message", ""),
                    level=payload.get("level", "info"),
                    state=payload.get("state", "active"),
                    priority=int(payload.get("priority", 0)),
                )
                for interaction_id, payload in interactions_data.items()
                if isinstance(payload, dict)
            },
            global_context_usage=dict(data.get("global_context_usage", {})),
            execution_preferences=dict(data.get("execution_preferences", {})),
            signals={
                signal_type: SignalState(
                    signal_type=payload.get("signal_type", signal_type),
                    available=bool(payload.get("available", False)),
                    summary=payload.get("summary", ""),
                    state=payload.get("state", "unknown"),
                )
                for signal_type, payload in signals_data.items()
                if isinstance(payload, dict)
            },
            contexts={
                context_type: ContextState(
                    context_type=payload.get("context_type", context_type),
                    available=bool(payload.get("available", False)),
                    summary=payload.get("summary", ""),
                    detail=payload.get("detail", ""),
                    speakable=payload.get("speakable", ""),
                )
                for context_type, payload in contexts_data.items()
                if isinstance(payload, dict)
            },
            experience_snapshots={
                snapshot_id: ExperienceSnapshot.from_dict(payload)
                for snapshot_id, payload in experience_snapshots_data.items()
                if isinstance(payload, dict)
            },
            usual_states={
                state_id: UsualState.from_dict(payload)
                for state_id, payload in usual_states_data.items()
                if isinstance(payload, dict)
            },
            default_person_profile=(
                PersonProfile(
                    person_id=default_person_data.get("person_id", "default"),
                    name=default_person_data.get("name", "Default Person"),
                    linked_area_id=default_person_data.get("linked_area_id"),
                    ble_device_ids=list(default_person_data.get("ble_device_ids", [])),
                    aqara_presence_entity_ids=list(default_person_data.get("aqara_presence_entity_ids", [])),
                    voice_profile_id=default_person_data.get("voice_profile_id"),
                    consent=dict(default_person_data.get("consent", {})),
                    mobile_notify_targets=list(default_person_data.get("mobile_notify_targets", [])),
                    preferred_mobile_target=default_person_data.get("preferred_mobile_target"),
                    mobile_voice_endpoint_enabled=bool(
                        default_person_data.get("mobile_voice_endpoint_enabled", False)
                    ),
                    is_minor=bool(default_person_data.get("is_minor", False)),
                    guardian_controls_required=bool(
                        default_person_data.get("guardian_controls_required", False)
                    ),
                    minor_allow_general_qna=bool(
                        default_person_data.get("minor_allow_general_qna", False)
                    ),
                    minor_allowed_intent_classes=list(
                        default_person_data.get("minor_allowed_intent_classes", [])
                    ),
                    minor_content_filter_level=default_person_data.get(
                        "minor_content_filter_level", "strict"
                    ),
                    email_source_ref=str(default_person_data.get("email_source_ref", "") or "").strip(),
                    calendar_source_ref=str(default_person_data.get("calendar_source_ref", "") or "").strip(),
                    task_source_ref=str(default_person_data.get("task_source_ref", "") or "").strip(),
                    shopping_source_ref=str(default_person_data.get("shopping_source_ref", "") or "").strip(),
                    email_source_bindings=_normalize_source_bindings(
                        default_person_data.get("email_source_bindings", []),
                        default_person_data.get("email_source_ref", ""),
                    ),
                    calendar_source_bindings=_normalize_source_bindings(
                        default_person_data.get("calendar_source_bindings", []),
                        default_person_data.get("calendar_source_ref", ""),
                    ),
                    task_source_bindings=_normalize_source_bindings(
                        default_person_data.get("task_source_bindings", []),
                        default_person_data.get("task_source_ref", ""),
                    ),
                    shopping_source_bindings=_normalize_source_bindings(
                        default_person_data.get("shopping_source_bindings", []),
                        default_person_data.get("shopping_source_ref", ""),
                    ),
                    notes=default_person_data.get("notes", ""),
                )
                if isinstance(default_person_data, dict)
                else None
            ),
            person_profiles={
                person_id: PersonProfile(
                    person_id=payload.get("person_id", person_id),
                    name=payload.get("name", ""),
                    linked_area_id=payload.get("linked_area_id"),
                    ble_device_ids=list(payload.get("ble_device_ids", [])),
                    aqara_presence_entity_ids=list(payload.get("aqara_presence_entity_ids", [])),
                    voice_profile_id=payload.get("voice_profile_id"),
                    consent=dict(payload.get("consent", {})),
                    mobile_notify_targets=list(payload.get("mobile_notify_targets", [])),
                    preferred_mobile_target=payload.get("preferred_mobile_target"),
                    mobile_voice_endpoint_enabled=bool(payload.get("mobile_voice_endpoint_enabled", False)),
                    is_minor=bool(payload.get("is_minor", False)),
                    guardian_controls_required=bool(payload.get("guardian_controls_required", False)),
                    minor_allow_general_qna=bool(payload.get("minor_allow_general_qna", False)),
                    minor_allowed_intent_classes=list(payload.get("minor_allowed_intent_classes", [])),
                    minor_content_filter_level=payload.get("minor_content_filter_level", "strict"),
                    email_source_ref=str(payload.get("email_source_ref", "") or "").strip(),
                    calendar_source_ref=str(payload.get("calendar_source_ref", "") or "").strip(),
                    task_source_ref=str(payload.get("task_source_ref", "") or "").strip(),
                    shopping_source_ref=str(payload.get("shopping_source_ref", "") or "").strip(),
                    email_source_bindings=_normalize_source_bindings(
                        payload.get("email_source_bindings", []),
                        payload.get("email_source_ref", ""),
                    ),
                    calendar_source_bindings=_normalize_source_bindings(
                        payload.get("calendar_source_bindings", []),
                        payload.get("calendar_source_ref", ""),
                    ),
                    task_source_bindings=_normalize_source_bindings(
                        payload.get("task_source_bindings", []),
                        payload.get("task_source_ref", ""),
                    ),
                    shopping_source_bindings=_normalize_source_bindings(
                        payload.get("shopping_source_bindings", []),
                        payload.get("shopping_source_ref", ""),
                    ),
                    notes=payload.get("notes", ""),
                )
                for person_id, payload in person_profiles_data.items()
                if isinstance(payload, dict)
            },
            activities={
                activity_id: ActivityEvent(
                    activity_id=payload.get("activity_id", activity_id),
                    correlation_id=payload.get("correlation_id", ""),
                    started_at=payload.get("started_at", ""),
                    channel=payload.get("channel", "unknown"),
                    actor_class=payload.get("actor_class", "unknown"),
                    intent_class=payload.get("intent_class", "unknown"),
                    request_summary=payload.get("request_summary", ""),
                    resolved_person_id=payload.get("resolved_person_id"),
                    resolved_area_id=payload.get("resolved_area_id"),
                    confidence=(
                        float(payload["confidence"])
                        if payload.get("confidence") is not None
                        else None
                    ),
                    external_refs=list(payload.get("external_refs", [])),
                    ended_at=payload.get("ended_at"),
                    outcome=payload.get("outcome"),
                    outcome_reason=payload.get("outcome_reason", ""),
                    actions_taken=list(payload.get("actions_taken", [])),
                    policy_gates=list(payload.get("policy_gates", [])),
                )
                for activity_id, payload in activities_data.items()
                if isinstance(payload, dict)
            },
            default_voice_profile=(
                VoiceProfile(
                    voice_profile_id=default_voice_data.get("voice_profile_id", "default"),
                    name=default_voice_data.get("name", "Default Voice"),
                    tts_voice=default_voice_data.get("tts_voice", ""),
                    enrollment_state=default_voice_data.get("enrollment_state", "untrained"),
                    enrollment_source=default_voice_data.get("enrollment_source", ""),
                    speaker_embedding_id=default_voice_data.get("speaker_embedding_id", ""),
                    sample_count=int(default_voice_data.get("sample_count", 0)),
                    sample_items=list(default_voice_data.get("sample_items", [])),
                    attribution_confidence=(
                        float(default_voice_data["attribution_confidence"])
                        if default_voice_data.get("attribution_confidence") is not None
                        else None
                    ),
                    enrollment_started_at=default_voice_data.get("enrollment_started_at", ""),
                    last_sample_at=default_voice_data.get("last_sample_at", ""),
                    last_built_at=default_voice_data.get("last_built_at", ""),
                    disabled=bool(default_voice_data.get("disabled", False)),
                    consent=dict(default_voice_data.get("consent", {})),
                )
                if isinstance(default_voice_data, dict)
                else None
            ),
            voice_profiles={
                voice_profile_id: VoiceProfile(
                    voice_profile_id=payload.get("voice_profile_id", voice_profile_id),
                    name=payload.get("name", ""),
                    tts_voice=payload.get("tts_voice", ""),
                    enrollment_state=payload.get("enrollment_state", "untrained"),
                    enrollment_source=payload.get("enrollment_source", ""),
                    speaker_embedding_id=payload.get("speaker_embedding_id", ""),
                    sample_count=int(payload.get("sample_count", 0)),
                    sample_items=list(payload.get("sample_items", [])),
                    attribution_confidence=(
                        float(payload["attribution_confidence"])
                        if payload.get("attribution_confidence") is not None
                        else None
                    ),
                    enrollment_started_at=payload.get("enrollment_started_at", ""),
                    last_sample_at=payload.get("last_sample_at", ""),
                    last_built_at=payload.get("last_built_at", ""),
                    disabled=bool(payload.get("disabled", False)),
                    consent=dict(payload.get("consent", {})),
                )
                for voice_profile_id, payload in voice_profiles_data.items()
                if isinstance(payload, dict)
            },
            enrollment_sessions={
                session_id: EnrollmentSession(
                    session_id=payload.get("session_id", session_id),
                    person_id=payload.get("person_id", ""),
                    voice_profile_id=payload.get("voice_profile_id", ""),
                    state=payload.get("state", "idle"),
                    created_at=payload.get("created_at", ""),
                    updated_at=payload.get("updated_at", ""),
                    sample_count=int(payload.get("sample_count", 0)),
                    sample_items=list(payload.get("sample_items", [])),
                    enrollment_started_at=payload.get("enrollment_started_at", ""),
                    last_sample_at=payload.get("last_sample_at", ""),
                    last_built_at=payload.get("last_built_at", ""),
                    cleanup_status=payload.get("cleanup_status", "not_started"),
                    capture_provider=payload.get("capture_provider", "browser_microphone"),
                    last_error=payload.get("last_error", ""),
                    metadata=dict(payload.get("metadata", {})),
                )
                for session_id, payload in enrollment_sessions_data.items()
                if isinstance(payload, dict)
            },
            default_identity_profile=(
                IdentityProfile(
                    profile_id=default_identity_data.get("profile_id", "default"),
                    name=default_identity_data.get("name", "Default"),
                    persona=default_identity_data.get("persona", "concise"),
                    tts_voice=default_identity_data.get("tts_voice", ""),
                    verbosity=default_identity_data.get("verbosity", "standard"),
                    allow_ai=bool(default_identity_data.get("allow_ai", True)),
                    content_type=default_identity_data.get("content_type", "general"),
                    detail_level=default_identity_data.get("detail_level", "medium"),
                )
                if isinstance(default_identity_data, dict)
                else None
            ),
            identity_profiles={
                profile_id: IdentityProfile(
                    profile_id=payload.get("profile_id", profile_id),
                    name=payload.get("name", ""),
                    persona=payload.get("persona", "concise"),
                    tts_voice=payload.get("tts_voice", ""),
                    verbosity=payload.get("verbosity", "standard"),
                    allow_ai=bool(payload.get("allow_ai", True)),
                    content_type=payload.get("content_type", "general"),
                    detail_level=payload.get("detail_level", "medium"),
                )
                for profile_id, payload in identity_profiles_data.items()
                if isinstance(payload, dict)
            },
            global_features=dict(data.get("global_features", {})),
        )
