# Experience Continuity Governance Conformance Review

## 1) Review Date
2026-07-21

## 2) Sources Reviewed
- docs/governance/experience-continuity/adr-experience-continuity-architecture.md
- docs/governance/experience-continuity/experience-continuity-scope-decisions.md
- docs/governance/experience-continuity/experience-continuity-requirements-backlog.md
- docs/governance/experience-continuity/experience-continuity-epic-and-issue-roadmap.md
- docs/governance/experience-continuity/experience-continuity-outcome-preservation-review.md
- docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md
- docs/governance/experience-continuity/v1-capability-reconstruction.md
- GitHub EC issue bodies snapshot: tmp/ec_issue_updates/ec_issues_full.json

## 3) Issues Reviewed
- #384 Epic EC-A: Experience Continuity Foundation
- #385 Epic EC-B: Preference Resolution and Identity Safety
- #386 Epic EC-C: Lighting Continuity
- #387 Epic EC-D: Audio Continuity and Sonos Speech
- #388 Epic EC-E: Media Continuity
- #389 Epic EC-F: Room Capability Awareness and Monitoring Follow-Ups
- #390 Epic EC-G: Guardrails, Failure Handling, and Silence-Is-Success
- #391 Epic EC-H: Production Install Gate and Validation
- #392 EC-A-01 Create Experience Continuity Runtime Model and Terminology
- #393 EC-A-02 Implement Continuity Scope and Event Classification
- #394 EC-A-03 Define V1 Helper-Backed State Disposition and V2 State Strategy
- #395 EC-A-04 Add Continuity Diagnostics and Explainability Scaffolding
- #396 EC-B-01 Implement Preference Resolution Hierarchy
- #397 EC-B-02 Implement Identity Confidence and Guest Default Policy
- #398 EC-B-03 Implement Learning Permission Boundaries and Non-Blocking Policy
- #399 EC-C-01 Implement Learned/Usual Lighting Resolution
- #400 EC-C-02 Implement Room-Aware Lamp/Light Actuation Parity
- #401 EC-C-03 Implement Lighting Fallback and No-Capability Behavior
- #402 EC-C-04 Implement Lighting Tests and Documentation Closure
- #403 EC-D-01 Implement Room Audio Preference Resolution
- #404 EC-D-02 Implement Sonos Speech Output with Duck/Restore
- #405 EC-D-03 Implement Audio Fallback and No-Speaker Behavior
- #406 EC-D-04 Implement Audio Tests and Documentation Closure
- #407 EC-E-01 Implement Room-Level Music Playback Resolution
- #408 EC-E-02 Implement Room-Level Continue/Resume Media
- #409 EC-E-03 Implement Room-Level Last-Media Context
- #410 EC-E-04 Implement Manual-Stop Cooldown and No Unwanted Auto-Start
- #411 EC-E-05 Implement Media Tests and Documentation Closure
- #412 EC-F-01 Implement Room Capability Awareness from Room Configuration
- #413 EC-F-02 Implement Monitoring Follow-Up Answers from Configured Room Capabilities
- #414 EC-F-03 Implement Capability-Not-Available Graceful Refusal
- #415 EC-G-01 Implement Silence-Is-Success and Direct-Refusal Policy
- #416 EC-G-02 Implement Degraded-Path Guardrail Validation Suite
- #417 EC-H-01 Build Install-Gate Validation Evidence Package
- #418 EC-H-02 Create Final Production Readiness Review Checklist and Closure Decision
- #419 EC-PE-01 Implement True Cross-Room Follow-Me Media (Post-Install Enhancement)

## 4) Governance Dimensions Reviewed
- ADR conformance
- Scope conformance
- State scope boundary conformance
- Playback scope vs memory scope conformance
- Merged-room behavior conformance
- Room Configuration authority conformance
- Music Assistant and Sonos boundary conformance
- Identity and personalization boundary conformance
- Requirement trace conformance (EC-REQ-001 through EC-REQ-092 set)
- Install-gate tier conformance (required/supporting/post-install)

## 5) Epic-Level Summary
- All eight EC epics remain aligned to the governance chain and authority order.
- Epic language remains planning/tracking oriented and does not introduce implementation conflict.
- Epic-level install-gate posture is appropriately dependent on child issue completion and evidence aggregation.

Disposition roll-up:
- PASS: 26
- PASS_WITH_COMMENT: 9
- UPDATE_RECOMMENDED: 1
- CONFLICT: 0

## 6) State Scope Summary
Conformance status: PASS.

Reviewed issue set preserves the architectural state boundary model:
- Entity-scoped lighting state remains scoped to light/lamp attributes.
- Room-scoped continuity memory remains room-scoped for audio/media state.
- Person-scoped music preference state remains person-scoped by default.
- Household-scoped policy remains guardrail/default oriented.

No issue was found that collapses person, room, and household state into a single undifferentiated store.

## 7) Playback Scope vs Memory Scope Summary
Conformance status: PASS.

The updated EC-D and EC-E issue language consistently distinguishes:
- Playback scope: active speaker participation, including merged-room playback output.
- Memory scope: persistent continuity memory, kept room-scoped unless explicitly governed otherwise.

No reviewed issue makes merged playback equivalent to merged persistence.

## 8) Merged Room Behavior Summary
Conformance status: PASS.

Merged-room behavior is represented as:
- Shared active playback/TTS output across grouped speakers.
- No automatic merged persistent volume/media memory.
- Constituent-room continuity memory remains independent.

This boundary is explicitly reflected in EC-D-01, EC-D-02, EC-E-01, EC-E-02, EC-E-03, EC-E-05, EC-H-01, and EC-H-02.

## 9) Music Assistant / Sonos Boundary Summary
Conformance status: PASS.

The reviewed issue language maintains the intended boundary:
- Music Assistant is preferred for music content resolution/orchestration when configured.
- Sonos/configured speakers are output-path entities.
- Experience Continuity owns continuity memory, resume/fallback policy, and guardrail application.

No issue in the reviewed set reverts to Sonos Favorites as primary content authority when Music Assistant is enabled.

## 10) Identity and Preference Boundary Summary
Conformance status: PASS.

Identity and personalization governance remains aligned:
- Person-scoped preferences are default for music affinity/preference behavior.
- Person+room music preference remains exception-only where explicitly authorized.
- Guest/unknown/low-confidence/unavailable identity contexts remain fail-closed.
- Room media continuity state is not treated as person preference state.

## 11) Requirement Coverage Summary
Coverage status: PASS.

Validation against the reviewed EC issue bodies shows:
- Expected requirement IDs: 36
- Unique requirement IDs found in issue bodies: 36
- Missing expected IDs: none

Expected set covered:
- EC-REQ-001, 002, 003
- EC-REQ-010, 011, 012
- EC-REQ-020, 021, 022, 023
- EC-REQ-030, 031, 032, 033
- EC-REQ-040, 041, 042, 043, 044
- EC-REQ-050, 051, 052
- EC-REQ-060, 061, 062, 063
- EC-REQ-070, 071, 072
- EC-REQ-080, 081, 082, 083
- EC-REQ-090, 091, 092

No orphaned requirement ID was identified in the approved EC-REQ set.

## 12) Install Gate Coverage Summary
Coverage status: PASS.

Issue classification counts from reviewed issue bodies:
- INSTALL_GATE_REQUIRED: 29
- INSTALL_GATE_SUPPORTING: 6
- POST_INSTALL_ENHANCEMENT: 1
- Unspecified: 0

Install-gate structure remains coherent:
- Required and supporting issues are present for all in-scope domains.
- Post-install follow-me behavior is clearly separated into EC-PE-01.

## 13) Issue-by-Issue Conformance Matrix
Legend:
- PASS: Conforms as written.
- PASS_WITH_COMMENT: Conforms, with clarifying note.
- UPDATE_RECOMMENDED: Not conflicting, but wording should be tightened.
- CONFLICT: Conflicts with governing artifacts.

| Issue # | Title | Epic | ADR Conformance | Scope Conformance | State Scope Conformance | Playback vs Memory Conformance | Merged Room Conformance | Room Configuration Conformance | Music Assistant Conformance | Identity Conformance | Requirement Conformance | Install Gate Conformance | Overall Disposition | Recommended Action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 384 | Epic EC-A: Experience Continuity Foundation | EC-A | PASS | PASS | PASS_WITH_COMMENT | N/A | N/A | N/A | N/A | N/A | PASS | PASS_WITH_COMMENT | PASS_WITH_COMMENT | Keep as planning parent; rely on child evidence for dimension closure. |
| 385 | Epic EC-B: Preference Resolution and Identity Safety | EC-B | PASS | PASS | PASS | N/A | N/A | N/A | N/A | PASS | PASS | PASS_WITH_COMMENT | PASS_WITH_COMMENT | Keep; child issues carry detailed identity-state boundary evidence. |
| 386 | Epic EC-C: Lighting Continuity | EC-C | PASS | PASS | PASS | N/A | N/A | PASS_WITH_COMMENT | N/A | N/A | PASS | PASS_WITH_COMMENT | PASS_WITH_COMMENT | Keep; closure depends on EC-C child tests/docs evidence. |
| 387 | Epic EC-D: Audio Continuity and Sonos Speech | EC-D | PASS | PASS | PASS | PASS_WITH_COMMENT | PASS_WITH_COMMENT | PASS_WITH_COMMENT | PASS | PASS_WITH_COMMENT | PASS | PASS_WITH_COMMENT | PASS_WITH_COMMENT | Keep; ensure child evidence captures merged-room validations. |
| 388 | Epic EC-E: Media Continuity | EC-E | PASS | PASS | PASS | PASS | PASS | PASS_WITH_COMMENT | PASS | PASS | PASS | PASS_WITH_COMMENT | PASS_WITH_COMMENT | Keep; child issues already encode MA/Sonos/room-memory boundaries. |
| 389 | Epic EC-F: Room Capability Awareness and Monitoring Follow-Ups | EC-F | PASS | PASS | PASS | N/A | N/A | PASS | N/A | PASS_WITH_COMMENT | PASS | PASS_WITH_COMMENT | PASS_WITH_COMMENT | Keep; child issues drive configured-room authority evidence. |
| 390 | Epic EC-G: Guardrails, Failure Handling, and Silence-Is-Success | EC-G | PASS | PASS | PASS | N/A | N/A | N/A | N/A | PASS | PASS | PASS_WITH_COMMENT | PASS_WITH_COMMENT | Keep; child guardrail issues provide operational proof. |
| 391 | Epic EC-H: Production Install Gate and Validation | EC-H | PASS | PASS | PASS_WITH_COMMENT | PASS_WITH_COMMENT | PASS_WITH_COMMENT | PASS_WITH_COMMENT | PASS_WITH_COMMENT | PASS_WITH_COMMENT | PASS | PASS | PASS_WITH_COMMENT | Keep; gate package must aggregate all required child evidence. |
| 392 | EC-A-01 Create Experience Continuity Runtime Model and Terminology | EC-A | PASS | PASS | PASS | N/A | N/A | N/A | N/A | PASS_WITH_COMMENT | PASS | PASS | PASS | Keep as first implementation dependency. |
| 393 | EC-A-02 Implement Continuity Scope and Event Classification | EC-A | PASS | PASS | PASS | N/A | N/A | N/A | N/A | PASS | PASS | PASS | PASS | Keep; supports diagnostics and scope traceability. |
| 394 | EC-A-03 Define V1 Helper-Backed State Disposition and V2 State Strategy | EC-A | PASS | PASS | PASS | N/A | N/A | N/A | N/A | PASS | PASS | PASS | PASS | Keep; maintain strict schema-independence in implementation details. |
| 395 | EC-A-04 Add Continuity Diagnostics and Explainability Scaffolding | EC-A | PASS | PASS | PASS | N/A | N/A | N/A | N/A | PASS | PASS | PASS | PASS | Keep; required for EC-REQ-092 supportability evidence. |
| 396 | EC-B-01 Implement Preference Resolution Hierarchy | EC-B | PASS | PASS | PASS | PASS | N/A | N/A | PASS_WITH_COMMENT | PASS | PASS | PASS | PASS | Keep; boundary language is aligned (person default, room context separate). |
| 397 | EC-B-02 Implement Identity Confidence and Guest Default Policy | EC-B | PASS | PASS | PASS | N/A | N/A | N/A | N/A | PASS | PASS | PASS | PASS | Keep; fail-closed identity behavior is explicit. |
| 398 | EC-B-03 Implement Learning Permission Boundaries and Non-Blocking Policy | EC-B | PASS | PASS | PASS | N/A | N/A | N/A | N/A | PASS | PASS | PASS | PASS | Keep; aligns to learning governance and safety boundaries. |
| 399 | EC-C-01 Implement Learned/Usual Lighting Resolution | EC-C | PASS | PASS | PASS | N/A | N/A | PASS | N/A | PASS_WITH_COMMENT | PASS | PASS | PASS | Keep; prohibition on helper-shape recreation is explicit. |
| 400 | EC-C-02 Implement Room-Aware Lamp/Light Actuation Parity | EC-C | PASS | PASS | PASS | N/A | N/A | PASS_WITH_COMMENT | N/A | PASS_WITH_COMMENT | PASS | PASS | UPDATE_RECOMMENDED | Add explicit statement that Room Configuration is authoritative for room membership/capability targeting in this issue body. |
| 401 | EC-C-03 Implement Lighting Fallback and No-Capability Behavior | EC-C | PASS | PASS | PASS | N/A | N/A | N/A | N/A | PASS | PASS | PASS | PASS | Keep; fallback posture is deterministic and policy-safe. |
| 402 | EC-C-04 Implement Lighting Tests and Documentation Closure | EC-C | PASS | PASS | PASS | N/A | N/A | N/A | N/A | PASS_WITH_COMMENT | PASS | PASS | PASS | Keep; evidence closure issue is structurally aligned. |
| 403 | EC-D-01 Implement Room Audio Preference Resolution | EC-D | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Keep; merged playback and constituent-room memory boundary is explicit. |
| 404 | EC-D-02 Implement Sonos Speech Output with Duck/Restore | EC-D | PASS | PASS | PASS | PASS_WITH_COMMENT | PASS | N/A | PASS | PASS | PASS | PASS | PASS | Keep; includes merged-room active output and duck/restore handling. |
| 405 | EC-D-03 Implement Audio Fallback and No-Speaker Behavior | EC-D | PASS | PASS | PASS | N/A | N/A | N/A | N/A | PASS | PASS | PASS | PASS | Keep; aligns with degraded-path and refusal posture. |
| 406 | EC-D-04 Implement Audio Tests and Documentation Closure | EC-D | PASS | PASS | PASS | PASS | PASS | N/A | PASS_WITH_COMMENT | PASS_WITH_COMMENT | PASS | PASS | PASS | Original audit recommendation to add explicit merged-room audio validation bullets was remediated on 2026-07-21; issue body now requires grouped playback, duck/restore, constituent-room memory independence, and Follow-Me exclusion validation. |
| 407 | EC-E-01 Implement Room-Level Music Playback Resolution | EC-E | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Keep; MA-preferred resolution and room-targeted output boundary is explicit. |
| 408 | EC-E-02 Implement Room-Level Continue/Resume Media | EC-E | PASS | PASS | PASS | PASS | PASS | PASS_WITH_COMMENT | PASS | PASS | PASS | PASS | PASS | Keep; playback scope vs room-memory scope distinction is explicit. |
| 409 | EC-E-03 Implement Room-Level Last-Media Context | EC-E | PASS | PASS | PASS | PASS | PASS | PASS_WITH_COMMENT | PASS | PASS | PASS | PASS | PASS | Keep; deterministic merged-room write rule requirement is explicit. |
| 410 | EC-E-04 Implement Manual-Stop Cooldown and No Unwanted Auto-Start | EC-E | PASS | PASS | PASS | PASS_WITH_COMMENT | PASS_WITH_COMMENT | N/A | PASS_WITH_COMMENT | PASS | PASS | PASS | PASS_WITH_COMMENT | Keep; maintain alignment with merged-room semantics through linked EC-E issues. |
| 411 | EC-E-05 Implement Media Tests and Documentation Closure | EC-E | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Keep; explicitly validates room-memory/person-preference boundary and merged-room playback expectations. |
| 412 | EC-F-01 Implement Room Capability Awareness from Room Configuration | EC-F | PASS | PASS | PASS | N/A | N/A | PASS | N/A | PASS_WITH_COMMENT | PASS | PASS | PASS | Keep; room authority is explicit and aligned. |
| 413 | EC-F-02 Implement Monitoring Follow-Up Answers from Configured Room Capabilities | EC-F | PASS | PASS | PASS | N/A | N/A | PASS | N/A | PASS_WITH_COMMENT | PASS | PASS | PASS | Keep; configured-room capability grounding is explicit. |
| 414 | EC-F-03 Implement Capability-Not-Available Graceful Refusal | EC-F | PASS | PASS | PASS | N/A | N/A | N/A | N/A | PASS | PASS | PASS | PASS | Keep; deterministic refusal is install-gate aligned. |
| 415 | EC-G-01 Implement Silence-Is-Success and Direct-Refusal Policy | EC-G | PASS | PASS | PASS | N/A | N/A | N/A | N/A | PASS | PASS | PASS | PASS | Keep; silence/refusal policy remains explicit and testable. |
| 416 | EC-G-02 Implement Degraded-Path Guardrail Validation Suite | EC-G | PASS | PASS | PASS | N/A | N/A | N/A | N/A | PASS | PASS | PASS | PASS | Keep; degraded-path matrix supports cross-domain conformance. |
| 417 | EC-H-01 Build Install-Gate Validation Evidence Package | EC-H | PASS | PASS | PASS | PASS | PASS | PASS_WITH_COMMENT | PASS_WITH_COMMENT | PASS_WITH_COMMENT | PASS | PASS | PASS | Keep; includes merged-room validation categories and out-of-scope declarations. |
| 418 | EC-H-02 Create Final Production Readiness Review Checklist and Closure Decision | EC-H | PASS | PASS | PASS | PASS | PASS | PASS_WITH_COMMENT | PASS_WITH_COMMENT | PASS_WITH_COMMENT | PASS | PASS | PASS | Keep; final gate checklist is correctly structured for explicit pass/fail reporting. |
| 419 | EC-PE-01 Implement True Cross-Room Follow-Me Media (Post-Install Enhancement) | EC-PE | PASS | PASS | PASS_WITH_COMMENT | PASS_WITH_COMMENT | PASS_WITH_COMMENT | PASS_WITH_COMMENT | PASS_WITH_COMMENT | PASS_WITH_COMMENT | PASS | PASS | PASS_WITH_COMMENT | Keep as post-install only; do not allow into initial install-gate closure criteria. |

## 14) Findings
- No governance conflicts were identified in the reviewed EC issue set.
- Requirement coverage is complete for the expected EC-REQ set (36 of 36).
- Install-gate tiering is complete and explicit across all reviewed issues.
- State boundary, playback-vs-memory boundary, and merged-room behavior boundaries are materially encoded in the current issue language.

## 15) Recommended Corrections
- Issue #400 (EC-C-02): add explicit Room Configuration authority statement in scope/architecture guidance to remove residual room-inference ambiguity.

Audit history:
- Original review recommendation for Issue #406 (EC-D-04): add explicit merged-room validation criteria to acceptance/tests to keep audio closure criteria symmetric with EC-E and EC-H merged-room checks.
- Corrective action completed on 2026-07-21: Issue #406 was updated to require explicit merged-room music playback, TTS/announcement playback, duck/restore, constituent-room volume-memory preservation, and Follow-Me boundary validation.

## 16) Conflicts
- None.

## 17) Final Readiness Recommendation
Recommendation: CONDITIONAL_PASS_FOR_ROADMAP_GOVERNANCE_CONFORMANCE.

Interpretation:
- Governance conformance is sufficient to proceed with implementation sequencing under the existing dependency order.
- Apply the remaining recommended wording correction (#400) to improve audit clarity before final install-gate evidence closure.
- Original Issue #406 audit recommendation has been remediated and the issue now passes governance conformance review.
- Preserve EC-PE-01 as post-install enhancement and exclude it from initial production install-gate blocking criteria.
