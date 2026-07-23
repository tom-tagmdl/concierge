# Degraded Context Validation Matrix

## 1. Purpose
Define the authoritative validation matrix for deterministic degraded-context behavior in Concierge Experience Continuity.

This artifact is validation-only for issue #416 and does not introduce runtime behavior.

## 2. Governance Sources
- docs/governance/experience-continuity/adr-experience-continuity-architecture.md
- docs/governance/experience-continuity/experience-continuity-scope-decisions.md
- docs/governance/experience-continuity/experience-continuity-epic-and-issue-roadmap.md
- docs/governance/experience-continuity/experience-continuity-requirements-backlog.md
- docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md
- docs/governance/experience-continuity/v1-capability-reconstruction.md
- docs/governance/experience-continuity/room-runtime-authority-contract.md
- docs/governance/experience-continuity/monitoring-follow-up-capability-mapping-contract.md
- docs/governance/experience-continuity/capability-refusal-taxonomy-contract.md
- docs/governance/experience-continuity/calm-behavior-policy-guide.md
- docs/governance/capability-resolution-pipeline-architecture.md
- docs/governance/capability-discovery-foundation.md

## 3. Degraded Context Categories
Category A - Missing Devices
- Missing monitoring sensor mapping
- Missing media player target
- Missing speaker mapping
- Missing lighting target

Category B - Disabled Integrations
- Music Assistant unavailable
- Email source unavailable
- Calendar source unavailable
- Weather provider unavailable

Category C - Voice Identity Degraded
- Voice Identity unavailable
- Person unresolved
- Identity confidence unavailable/low

Category D - Output Device Degraded
- Announcement destination unavailable
- Media destination unavailable

Category E - Room Context Degraded
- Room unresolved
- Room configuration missing
- Composite configuration missing

Category F - Merged-Room Degraded
- Merged-room capability unavailable
- Merged-room configuration degraded

Category G - Behavior Classification
- Refusal classification preserved
- Outcome classification preserved

## 4. Validation Matrix
| Scenario | Category | Degraded Condition | Expected Governed Outcome |
| --- | --- | --- | --- |
| ec416-s01 | A | Missing monitoring sensor mapping | REFUSAL_SUCCESS |
| ec416-s02 | A | Missing media player target | REFUSAL_SUCCESS |
| ec416-s03 | A | Missing speaker mapping | REFUSAL_SUCCESS |
| ec416-s04 | A | Missing lighting target | REFUSAL_SUCCESS |
| ec416-s05 | B | Music Assistant unavailable | REFUSAL_SUCCESS |
| ec416-s06 | B | Email source unavailable | REFUSAL_SUCCESS |
| ec416-s07 | B | Calendar source unavailable | REFUSAL_SUCCESS |
| ec416-s08 | B | Weather provider unavailable | ANSWER_SUCCESS |
| ec416-s09 | C | Voice Identity unavailable | Fail-closed person resolution |
| ec416-s10 | C | Person unresolved | Fail-closed person resolution |
| ec416-s11 | C | Identity confidence unavailable/low | Fail-closed person resolution |
| ec416-s12 | E | Room unresolved | REFUSAL_SUCCESS |
| ec416-s13 | E | Room configuration missing | REFUSAL_SUCCESS |
| ec416-s14 | E | Composite configuration missing | REFUSAL_SUCCESS |
| ec416-s15 | F | Merged-room capability unavailable | REFUSAL_SUCCESS |
| ec416-s16 | F | Merged-room configuration degraded | REFUSAL_SUCCESS |
| ec416-s17 | D | Announcement destination unavailable | REFUSAL_SUCCESS |
| ec416-s18 | D | Media destination unavailable | REFUSAL_SUCCESS |
| ec416-s19 | G | Refusal taxonomy mapping consistency | refusal_category deterministic |
| ec416-s20 | G | Outcome taxonomy consistency | category deterministic |

## 5. Authority Expectations
For every degraded scenario:
- Room authority remains configuration-authored.
- Runtime discovery is validation-only and never replacement authority.
- Composite and merged-room governance boundaries are preserved.
- Voice Identity degradation remains fail-closed for person-specific behavior.

## 6. Outcome Expectations
Allowed deterministic outcomes in degraded contexts:
- EXECUTE_SUCCESS
- ANSWER_SUCCESS
- REFUSAL_SUCCESS
- SILENCE_SUCCESS

A degraded context is not automatically an error. Outcome is determined by authority, policy, and availability rules from #412, #413, #414, and #415.

## 7. Refusal Expectations
Refusal paths must remain explicit and explainable:
- refusal_reason populated
- refusal_category populated
- response_required true for refusal outcomes
- response_generated true for refusal outcomes

No alternate recovery or authority bypass paths are introduced.

## 8. Explainability Validation
Validation requires explicit field checks for:
- execution_outcome_category
- silence_as_success
- refusal_reason
- refusal_category
- room_authority_source
- person_policy_evaluated
- merged_room_authority_source
- response_generated
- response_required

## 9. Evidence Requirements
Issue #416 evidence package:
- tmp/ec416_portable_harness.py
- tmp/ec416_portable_harness_results.json
- tmp/ec416_closure.py
- tmp/ec416_closure_stdout_latest.txt
- tmp/ec416_test_results.json
- tmp/ec416_scenarios.json
- tmp/ec416_coverage_matrix.json
- tmp/ec416_doc_cross_reference.json

Classification for #416 closure package:
- INSTALL_GATE_SUPPORTING

## 10. Non-Goals
- No runtime feature implementation.
- No alternate recovery workflows.
- No dynamic room/speaker discovery as replacement authority.
- No production Home Assistant changes.
- No progression to EC-H from this issue execution.
