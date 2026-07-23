# Monitoring Follow-Up Capability Mapping Contract

## 1. Purpose
Preserve the V1 monitoring follow-up household outcome while replacing runtime scan behavior with V2 configuration-authored room capability mappings.

## 2. Governance Sources
- docs/governance/experience-continuity/adr-experience-continuity-architecture.md
- docs/governance/experience-continuity/experience-continuity-scope-decisions.md
- docs/governance/experience-continuity/experience-continuity-outcome-preservation-review.md
- docs/governance/experience-continuity/experience-continuity-epic-and-issue-roadmap.md
- docs/governance/experience-continuity/experience-continuity-requirements-backlog.md
- docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md
- docs/governance/experience-continuity/v1-capability-reconstruction.md
- docs/governance/experience-continuity/room-runtime-authority-contract.md
- docs/governance/capability-discovery-foundation.md
- docs/governance/room-aware-continuity-consumption.md
- docs/governance/merged-room-capability-consumption-architecture.md

## 3. Monitoring Capability Authority
Monitoring follow-up authority is Room Configuration.

Room Configuration determines:
- which monitoring capabilities are available for a room
- which configured devices are candidates for each capability
- deterministic precedence order for configured candidates
- merged-room participation boundaries

Runtime discovery is validation-only and cannot define capability ownership.

## 4. Capability Mapping Model
In-scope capabilities are fixed:
- temperature
- humidity
- light
- air_quality
- noise

No additional monitoring categories are introduced by this contract.

Capability-to-configuration mapping consumes existing Room Configuration membership fields and keeps mapping deterministic and explainable.

## 5. Deterministic Device Resolution
Resolution strategy:
- configured_priority_first_valid_measurement

Deterministic precedence:
- first configured candidate in authoritative room/composite order that is valid and has a usable measurement

Repeatability requirement:
- identical governed inputs produce identical resolved monitoring device and outcome.

## 6. Refusal Rules
Refusal is required when:
- room scope is missing
- merged-room configuration is missing
- configured capability mapping is missing
- configured capability has no usable measurement at runtime

Refusal is polite, bounded, and does not trigger cross-room or inventory scans.

## 7. Room Boundary Rules
Monitoring follow-up answers are room-scoped.
Only configured candidates from the resolved room participate.
Unrelated rooms and unrelated inventory entities are excluded.

## 8. Merged-Room Rules
Merged-room monitoring remains configuration-authored.
Merged-room authority may consume composite configuration and participating room configuration in deterministic order.
Runtime discovery cannot redefine merged-room capability ownership.

## 9. Runtime Validation vs Runtime Authority
Runtime validation may:
- verify configured entities exist
- verify configured entities are available
- verify configured entities provide usable measurements

Runtime validation may not:
- add capability ownership
- add non-configured devices as candidates
- redefine room or merged-room capability mappings

## 10. Validation Scenarios
Required scenario coverage:
1. Temperature capability resolved
2. Humidity capability resolved
3. Light capability resolved
4. Air quality capability resolved
5. Noise capability resolved
6. Multiple temperature sensors deterministic selection
7. Multiple humidity sensors deterministic selection
8. Multiple light sensors deterministic selection
9. Missing temperature capability refusal
10. Missing humidity capability refusal
11. Missing light capability refusal
12. Missing air-quality capability refusal
13. Missing noise capability refusal
14. Unrelated room sensor ignored
15. Inventory-discovered sensor ignored
16. Merged-room capability authority
17. Runtime discovery cannot add capability
18. Runtime discovery cannot redefine capability ownership
19. Runtime discovery remains validation-only
20. V1 monitoring follow-up outcome preserved

## 11. Non-Goals
- No broad Home Assistant inventory scan for monitoring ownership
- No cross-room monitoring inference
- No replacement of configuration authority with runtime heuristics
- No post-install monitoring enhancements
