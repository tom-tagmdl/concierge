# Experience Continuity Room-Aware Lighting Command Behavior

## 1. Purpose
This artifact defines the EC-C-02 room-aware lighting command targeting contract.

It preserves the V1 user outcome that room lighting commands target the correct room devices.

It intentionally replaces the V1 targeting mechanism (runtime entity scanning, label intersections, and broad inference) with V2 Room Configuration authority.

## 2. Governance Sources
- docs/governance/experience-continuity/experience-continuity-governance-conformance-review.md
- docs/governance/experience-continuity/adr-experience-continuity-architecture.md
- docs/governance/experience-continuity/experience-continuity-scope-decisions.md
- docs/governance/experience-continuity/experience-continuity-epic-and-issue-roadmap.md
- docs/governance/experience-continuity/experience-continuity-outcome-preservation-review.md
- docs/governance/experience-continuity/experience-continuity-requirements-backlog.md
- docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md
- docs/governance/experience-continuity/v1-capability-reconstruction.md
- docs/governance/experience-continuity/experience-continuity-learned-lighting-contract.md
- docs/governance/experience-continuity/experience-continuity-preference-resolution-contract.md
- docs/governance/experience-continuity/experience-continuity-identity-safety-context-matrix.md
- docs/governance/experience-continuity/experience-continuity-learning-governance-and-reversibility.md
- docs/governance/room-aware-capability-consumption-architecture.md
- ../homes_that_behave_well/docs/contracts/room-awareness-contract.md
- ../homes_that_behave_well/docs/models/room-model.md

## 3. Room Configuration Authority
Room Configuration and Foundation room definitions are authoritative for room-aware lighting targeting.

Authoritative room inputs:
- room identity (`area_id`)
- configured `light_entity_ids`
- configured `lamp_entity_ids`
- configured room aliases/vocabulary used for command interpretation in room scope

Runtime must consume these inputs. Runtime must not redefine room membership.

## 4. Capability Mapping Authority
Lighting capability targeting is driven by configured capability mappings:
- lamps capability -> `room.lamp_entity_ids`
- lights capability -> `room.light_entity_ids`
- usual/resume lights capability -> configured room lighting membership governed by command kind

Capability resolution may validate configured entities for existence and availability, but validation is not an authority source.

No runtime replacement discovery is allowed when configured capability mappings are absent.

## 5. Vocabulary Resolution Rules
Room-aware lighting command resolution uses governed room-scoped vocabulary surfaces:
- configured room aliases (room configuration)
- governed room vocabulary registry entries when resolving room scope

Supported room-aware command outcomes include:
- turn on lights
- turn on lamps
- usual lights
- resume lights

Vocabulary resolution must remain deterministic and explainable.

## 6. Membership Resolution Rules
Membership resolution pipeline:
Room -> Configured capability mapping -> Configured membership -> Runtime validation -> Execution

Runtime validation includes:
- entity identifier shape/domain validity
- configured entity existence/state visibility
- configured entity availability state

Validation does not add inferred entities.

Validation does not discover replacement entities.

If validation yields no valid targets, execution fails safely with explainable reason codes.

## 7. Safe Failure Matrix
| Condition | Execution Behavior | Failure Reason | Discovery Replacement |
| --- | --- | --- | --- |
| room configuration missing | no room-aware lighting actuation | room_configuration_missing | prohibited |
| capability mapping missing | no room-aware lighting actuation | configured_capability_mapping_missing | prohibited |
| configured entity missing | no actuation for missing targets; fail when no valid targets remain | configured_entity_missing | prohibited |
| configured entity unavailable | no actuation for unavailable targets; fail when no valid targets remain | configured_device_unavailable | prohibited |
| configured entity invalid | no actuation for invalid targets; fail when no valid targets remain | configured_entity_invalid | prohibited |

## 8. V1 Outcome Preservation
Preserved V1 user outcome:
- room-aware lamp/light command behavior applies to room-targeted lighting devices.

Retired V1 implementation mechanisms:
- broad runtime entity discovery
- label-intersection targeting as primary authority
- dynamic room membership inference

V2 replacement mechanism:
- configured room authority and configured capability mappings with deterministic validation and explainability.

## 9. Validation Scenarios
Required EC-C-02 scenarios:
1. known room -> configured lamps
2. known room -> configured lights
3. vocabulary-resolved room command
4. capability-mapped targeting
5. missing room configuration
6. missing capability mapping
7. missing configured entity
8. unavailable configured entity
9. invalid configured entity
10. unrelated device exclusion
11. runtime discovery not used
12. V1 outcome preserved via V2 authority model

Each scenario must provide:
- room input
- configured membership
- capability mapping
- validation result
- targeted entities
- explainability metadata

## 10. Non-Goals
This contract does not implement:
- restoration behavior
- snapshot behavior
- person-specific lighting preference policy expansion
- adaptive optimization behavior
- Follow-Me lighting
- media orchestration
- production Home Assistant changes
