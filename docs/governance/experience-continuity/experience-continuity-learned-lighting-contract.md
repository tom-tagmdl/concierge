# Experience Continuity Learned Lighting Contract

## 1. Purpose
This artifact defines the EC-C-01 learned or usual lighting contract.

It preserves V1 user outcomes for room-aware:
- turn on lamps
- turn on lights
- resume lights
- usual lights

It preserves outcome parity while redesigning storage under V2 Experience Continuity governance.

## 2. Governance Sources
- docs/governance/experience-continuity/adr-experience-continuity-architecture.md
- docs/governance/experience-continuity/experience-continuity-scope-decisions.md
- docs/governance/experience-continuity/experience-continuity-outcome-preservation-review.md
- docs/governance/experience-continuity/experience-continuity-epic-and-issue-roadmap.md
- docs/governance/experience-continuity/experience-continuity-requirements-backlog.md
- docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md
- docs/governance/experience-continuity/v1-capability-reconstruction.md
- docs/governance/experience-continuity/experience-continuity-preference-resolution-contract.md
- docs/governance/experience-continuity/experience-continuity-identity-safety-context-matrix.md
- docs/governance/experience-continuity/experience-continuity-learning-governance-and-reversibility.md

## 3. Learned Lighting Model
Learned usual lighting is persisted as continuity usual-state records, keyed by room plus entity.

State model:
- continuity type: usual_state
- scope: entity
- scope_ref: light or lamp entity id
- state id: usual_lighting::<area_id>::<entity_id>
- values:
  - brightness_pct
  - area_id
- metadata:
  - policy name
  - stability evidence
  - room membership source

Outcome rule:
- each configured light or lamp keeps its own learned usual level.
- room command application fans out per-entity values.
- no aggregate room brightness value is used.

## 4. Stability Learning Rules
Learning capture uses governed stability checks before committing usual-state:
- source state must be on
- source brightness must be valid
- configured stability interval must be met
- governed learning policy must allow write

Default stability interval is 30 seconds.

Stability interval may be governed by feature options under:
- global_features.experience_continuity_lighting_learning_policy.options.stability_seconds

If stability fails, the interaction continues and prior learned value remains unchanged.

## 5. Room Membership Rules
Authoritative membership source is Room Configuration.

Command application uses configured membership only:
- room.light_entity_ids
- room.lamp_entity_ids

Do not dynamically infer arbitrary lights at runtime.

Membership source is reported as:
- room_configuration_membership

## 6. Per-Entity Memory Rules
Per-entity rules are mandatory:
- each member light or lamp has independent learned brightness memory.
- writes are scoped by entity id and area id.
- learned value updates do not overwrite other entities.
- application sends one light.turn_on call per entity with that entity's learned level.

Example:
- Lamp A learned brightness_pct = 35
- Lamp B learned brightness_pct = 70
- command fan-out applies 35 to A and 70 to B

## 7. Fallback Matrix
Fallback behavior is deterministic and non-blocking.

| Condition | Behavior | Fallback Reason | Fallback Source |
| --- | --- | --- | --- |
| learned value exists | apply learned brightness_pct | none | usual_state |
| learned value missing | apply safe fallback | learned_value_missing | current_state_brightness or safe_default_brightness |
| learning denied and no usable learned value | apply safe fallback | learned_value_denied | current_state_brightness or safe_default_brightness |
| learned value unavailable or invalid | apply safe fallback | learned_value_unavailable | current_state_brightness or safe_default_brightness |

Safe default brightness is 50 percent when no current brightness is available.

## 8. Usual State vs Operational Snapshot
Usual state and operational snapshot are distinct continuity categories.

Usual state:
- learned baseline for deterministic reuse
- long-lived per-entity memory

Operational snapshot:
- captured transient state for interruption-oriented restoration
- not the source of usual-state memory

Separation rules:
- snapshot updates must not overwrite usual-state learned values.
- usual-state updates must not become operational snapshots.
- command application for EC-C-01 reads usual_state records, not snapshot records.

## 9. Validation Scenarios
Required validation scenarios:
1. single lamp learns a usual level
2. multiple lamps learn different usual levels
3. stable level accepted
4. unstable level rejected
5. turn on lamps applies learned values
6. turn on lights applies learned values
7. resume lights applies learned values
8. missing learned value uses fallback
9. denied learning uses fallback
10. configured room membership is enforced
11. usual-state and operational-snapshot remain separate
12. per-entity persistence remains independent

## 10. Non-Goals
This contract does not implement:
- helper-schema migration or helper-schema preservation
- scene restoration or operational snapshot restoration logic
- person-specific lighting preferences for this issue
- adaptive lighting intelligence
- Follow-Me lighting
- media behavior
- confidence-sensitive lighting behavior beyond governed learning gates
- production Home Assistant changes
