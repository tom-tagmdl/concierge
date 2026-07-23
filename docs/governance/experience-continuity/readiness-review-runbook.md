# Readiness Review Runbook

Issue: #418
Classification: INSTALL_GATE_REQUIRED
Purpose: Define how reviewers perform the final Experience Continuity install-gate readiness evaluation using existing evidence.

## 1. Preconditions
- Use only existing governance and evidence artifacts.
- Do not modify runtime code, tests, or production Home Assistant during this review.
- Do not reinterpret upstream evidence statuses.

## 2. Inputs
Required governance inputs:
- docs/governance/experience-continuity/adr-experience-continuity-architecture.md
- docs/governance/experience-continuity/experience-continuity-scope-decisions.md
- docs/governance/experience-continuity/experience-continuity-epic-and-issue-roadmap.md
- docs/governance/experience-continuity/experience-continuity-requirements-backlog.md
- docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md
- docs/governance/experience-continuity/v1-capability-reconstruction.md

Required #417 evidence inputs:
- docs/governance/experience-continuity/install-gate-evidence-binder.md
- docs/governance/experience-continuity/install-gate-checklist.md
- tmp/ec417_requirement_matrix.json
- tmp/ec417_behavior_matrix.json
- tmp/ec417_merged_room_matrix.json
- tmp/ec417_scope_matrix.json
- tmp/ec417_test_results.json

Required #418 package inputs:
- docs/governance/experience-continuity/final-readiness-checklist.md
- docs/governance/experience-continuity/closure-decision-record-template.md
- docs/governance/experience-continuity/example-closure-decision-record.md
- tmp/ec418_readiness_matrix.json
- tmp/ec418_checklist_validation.json
- tmp/ec418_scope_validation.json
- tmp/ec418_test_results.json

## 3. Review Procedure
1. Confirm governance baseline and authority order alignment.
2. Confirm EC-REQ-003 and EC-REQ-091 are explicitly represented.
3. Confirm supporting requirement mappings from #417 are present.
4. Confirm behavior matrix includes explicit statuses and evidence links.
5. Confirm merged-room matrix contains all 10 required merged-room checks.
6. Confirm refusal, outcome, and degraded-context checks reference upstream evidence.
7. Confirm out-of-scope declarations and rationale are explicit.
8. Confirm Follow-Me is explicitly POST-INSTALL and separated from merged-room playback.
9. Confirm final checklist lines contain explicit statuses only.
10. Complete closure decision record using the template.

## 4. Status Rules
Allowed review statuses:
- PASS
- FAIL
- POST-INSTALL
- OUT OF SCOPE

Decision values in closure record:
- READY
- NOT READY

## 5. Follow-Me Separation Rule
Mandatory interpretation rule:
- Merged-room playback is in-scope for install-gate review.
- Follow-Me Music is POST-INSTALL and not install-gate scope.
- Follow-Me must not contribute negative or positive scoring for install-gate readiness.

## 6. Decision Execution Rules
- Do not upgrade FAIL to PASS.
- Do not downgrade PASS to FAIL.
- Do not create inferred evidence rows.
- Use only documented evidence links.

## 7. Closure Record Completion
Use:
- docs/governance/experience-continuity/closure-decision-record-template.md

Populate every section with direct references to matrix entries.

## 8. Completion Criteria
Runbook execution is complete when:
- Final readiness checklist is reviewed end-to-end.
- Closure decision record is fully populated.
- Decision rationale cites requirement, behavior, and scope evidence.
- READY/NOT READY is recorded by reviewer authority.
