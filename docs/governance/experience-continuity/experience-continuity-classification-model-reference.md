# Experience Continuity Scope and Event Classification Reference

## Purpose
This artifact defines deterministic continuity scope and event classification introduced by EC-A-02.

It provides reusable classification outputs for downstream Experience Continuity issues without implementing orchestration behavior.

## Governing Sources
- docs/governance/experience-continuity/experience-continuity-epic-and-issue-roadmap.md
- docs/governance/experience-continuity/adr-experience-continuity-architecture.md
- docs/governance/experience-continuity/experience-continuity-scope-decisions.md
- docs/governance/experience-continuity/experience-continuity-requirements-backlog.md
- docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md
- docs/governance/experience-continuity/v1-capability-reconstruction.md
- docs/governance/experience-continuity/experience-continuity-runtime-terminology-reference.md

## Requirement Coverage
- EC-REQ-012
- EC-REQ-092

## Scope Classification Model
Supported scopes:
- entity
- room
- person
- household
- mode

Model types:
- `ContinuityScopeClassification`
- `classify_continuity_scope(payload)`

Deterministic precedence when no explicit scope is provided:
1. entity
2. room
3. person
4. household
5. mode

Explicit scope handling:
- If `scope` is present, classifier uses it directly and records `explicit_scope_field`.
- If multiple inferred scope hints are present, precedence is applied deterministically and candidate metadata is emitted.

Ownership-boundary protection:
- Entity identifiers (`entity_id`, `entity_ref`, `device_entity_id`) cannot be downgraded to person or household scope.
- Room references (`area_id`, `room_id`, `room_ref`, `composite_id`) remain room-scoped unless explicit scope overrides.
- Household policy indicators (`guest_mode`, `unknown_identity`, `silence_is_success`, `capability_not_available`) classify to household scope.
- Mode classification is minimal and evidence-driven (`mode_id`, `mode_ref`, `posture`, `global_mode`) and does not define new mode semantics.

## Event Classification Model
Supported event classes:
- unknown
- voice_interaction
- room_entry
- room_exit
- music_start
- music_pause
- manual_stop
- command_follow_up
- monitoring_question
- identity_confidence_change
- guest_mode_change

Model types:
- `ContinuityEventClassification`
- `classify_continuity_event(payload)`

Rule order:
1. Explicit `event_class` (authoritative for classification)
2. Deterministic keyword mapping from `event_type` / `event_name` / `trigger_type` / `intent_class`
3. Fallback to `unknown`

Unknown handling:
- Unknown event types are represented as `unknown` with reason code `unknown_event_class`.
- Unknown handling is deterministic and serializable.

## Deterministic Classification Traceability
Trace model:
- `ContinuityClassificationTrace`
- `build_continuity_classification_trace(payload)`

Trace output includes:
- selected scope and scope reason
- selected event class and event reason
- evidence used
- classifier version metadata
- optional continuity confidence payload from EC-A-01 concept model
- trace source and timestamp

Serialization:
- trace object supports `as_dict()` / `from_dict()` round-trip
- nested scope/event classification objects are also serializable

## Diagnostics Reference
Diagnostics visibility surface:
- `continuity_classification_traceability_visibility`

Diagnostics content:
- classifier version
- deterministic flag
- supported scopes
- supported event classes
- execution envelope reference count
- sample trace outputs for:
  - entity scope classification
  - room scope classification
  - person scope classification
  - household scope classification
  - mode scope classification

Interpretation guidance:
- `reason_code` explains why a classification was chosen.
- `evidence` identifies input fields used in selection.
- `metadata.candidate_scopes` shows ambiguity set where precedence was applied.

## Non-Goal Protection
EC-A-02 classification does not implement:
- lighting behavior
- audio behavior
- media behavior
- operational restore execution
- preference restore execution
- room capability orchestration
- Sonos or Music Assistant integration
- merged-room playback behavior
- Follow-Me Music behavior
- routine replacement behavior
- production Home Assistant changes

## Downstream Usage
This classifier output is designed to be consumed by:
- EC-A-03 state strategy and helper disposition policy planning
- EC-A-04 broader continuity diagnostics and traceability scaffolding
- later continuity domain implementations that require deterministic explainability inputs
