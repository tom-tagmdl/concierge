# Privacy, Retention, and Guest-Safe Memory Boundaries

## 1. Purpose

Define the authoritative E10-HM8 architecture baseline for privacy-safe household memory consumption.

This document defines consumption architecture only.

This document is architecture and governance only.

This document does not implement retention policies, memory deletion, memory suppression, privacy enforcement, guest detection, access control, visibility filtering, memory retrieval, or HM9 implementation work.

## 2. Scope Reviewed

Reviewed mandatory authorities and dependencies:

- HTBW #47
- HTBW #50
- Concierge #126
- HM3 Identity-Linked Memory Boundaries
- HM4 Room-Linked Memory Boundaries
- HM5 Who Did This Query Planning
- HM7 Why Did This Happen Explanation Planning
- E9 Guest-Safe Messaging Boundaries
- E9 Notification Discipline and Calm-by-Default Policy

Reviewed associated governance authorities:

- Household Memory Contract
- Household Memory Model
- Occupancy and Presence Contract

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#47, #50, #126, #148) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between HM8 outputs and authoritative ADR/contract/model artifacts.

## 3. Privacy Governance Validation

Validation scope:

- privacy ownership
- privacy governance
- privacy authority
- privacy lifecycle authority

Result: PASS

Validated statements:

- Privacy ownership remains in HTBW.
- Privacy governance remains in HTBW.
- Privacy authority remains in HTBW-governed memory/privacy authorities.
- Privacy lifecycle authority remains external to Coordinator.
- Coordinator consumes privacy outcomes.
- Coordinator does not redefine privacy policy.

## 4. Retention Governance Validation

Validation scope:

- retention ownership
- retention governance
- retention authority
- retention lifecycle authority

Result: PASS

Validated statements:

- Retention ownership remains in HTBW.
- Retention governance remains in HTBW.
- Retention authority remains in HTBW-governed memory authorities.
- Retention lifecycle authority remains external to Coordinator.
- Coordinator consumes retention outcomes.
- Coordinator does not define retention policy.

## 5. Guest Governance Validation

Validation scope:

- guest ownership
- guest governance
- guest-safe authority
- guest lifecycle authority

Result: PASS

Validated statements:

- Guest ownership remains in HTBW.
- Guest governance remains in HTBW.
- Guest-safe authority remains in HTBW-governed guest/privacy authorities.
- Guest lifecycle authority remains external to Coordinator.
- Coordinator consumes guest-safe outcomes.
- Coordinator does not define guest policy.

## 6. HM3 Alignment Review

Validation scope:

- identity governance alignment
- confidence governance alignment

Result: PASS

HM8 conforms to HM3 identity and confidence governance boundaries.

## 7. HM4 Alignment Review

Validation scope:

- room visibility alignment
- room privacy alignment

Result: PASS

HM8 conforms to HM4 room visibility and room privacy boundaries.

## 8. HM5 Alignment Review

Validation scope:

- attribution visibility alignment
- query eligibility alignment

Result: PASS

HM8 conforms to HM5 attribution visibility and query-eligibility boundaries.

## 9. HM7 Alignment Review

Validation scope:

- explanation eligibility alignment
- explanation visibility alignment

Result: PASS

HM8 aligns with HM7 explanation eligibility and explanation visibility boundaries.

## 10. Privacy and Retention Architecture

Validation scope:

- privacy participation
- retention participation
- consumption behavior
- outcomes

Result: PASS

Architecture-only privacy and retention consumption:

- privacy participation: consume governed privacy outcomes as bounded memory-consumption inputs.
- retention participation: consume governed retention outcomes as bounded memory-consumption inputs.
- consumption behavior: consume privacy/retention/guest-safe/visibility/suppression outcomes for household-facing experiences and explanations.
- outcomes: preserve bounded consumption outcomes with explicit lineage anchors.

## 11. Retention Behavior Review

Validation scope:

- retention participation
- retention consumption
- retention lineage

Result: PASS

Retention behavior is consumption-only:

- Coordinator consumes retention outcomes.
- Coordinator does not define retention policy.
- Retention lineage remains tied to HTBW-governed retention authorities.

## 12. Privacy-Safe Access Review

Validation scope:

- privacy participation
- access participation
- access lineage

Result: PASS

Privacy-safe access is consumption-only:

- Coordinator consumes access outcomes.
- Coordinator does not define access policy.
- Access lineage remains tied to HTBW-governed privacy/visibility authorities.

## 13. Guest-Safe Exclusion Review

Validation scope:

- guest participation
- exclusion participation
- exclusion lineage

Result: PASS

Guest-safe exclusion is consumption-only:

- Coordinator consumes guest-safe outcomes.
- Coordinator does not define guest policy.
- Exclusion lineage remains tied to HTBW-governed guest-safe authorities.

## 14. Memory Suppression Review

Validation scope:

- suppression participation
- suppression consumption
- suppression lineage

Result: PASS

Memory suppression participation is consumption-only:

- Coordinator consumes suppression outcomes.
- Coordinator does not define suppression policy.
- Suppression lineage remains tied to externally governed suppression authorities.

## 15. Visibility Boundary Review

Validation scope:

- visibility participation
- visibility consumption
- visibility lineage

Result: PASS

Visibility participation remains bounded to governed visibility outcomes with explicit lineage preserved.

## 16. Identity / Room / Guest Review

Validation scope:

- identity participation
- room participation
- guest participation

Result: PASS

Identity, room, and guest participation remain bounded to governed outputs without ownership transfer.

## 17. Provenance Relationship Review

Validation scope:

- provenance participation
- privacy participation
- provenance lineage

Result: PASS

Provenance and privacy participation remain bounded to governed provenance/privacy outputs with explicit lineage preserved.

## 18. Event History Relationship Review

Validation scope:

- event-history participation
- retention participation
- history lineage

Result: PASS

Event-history and retention participation remain bounded to authoritative event-history outputs and governed retention outcomes with explicit lineage preserved.

## 19. Household-Facing Explanation Eligibility Review

Validation scope:

- explanation participation
- explanation eligibility
- explanation lineage

Result: PASS

Household-facing explanation eligibility remains bounded to governed privacy/guest-safe/retention/suppression/visibility outcomes with explicit lineage preserved.

## 20. Privacy Traceability Review

Validation scope:

- privacy traceability
- retention traceability
- guest-safe traceability
- suppression traceability

Result: PASS

Traceability is preserved across privacy, retention, guest-safe, and suppression participation with explicit lineage anchors.

## 21. Privacy and Retention Lineage Architecture

Validation scope:

- privacy inputs
- retention inputs
- guest-safe inputs
- suppression inputs
- memory inputs
- provenance inputs
- event-history inputs
- identity inputs
- room inputs

Result: PASS

Lineage architecture:

- privacy-input lineage remains tied to HTBW-governed privacy outputs.
- retention-input lineage remains tied to HTBW-governed retention outputs.
- guest-safe-input lineage remains tied to HTBW-governed guest-safe outputs.
- suppression-input lineage remains tied to externally governed suppression outputs.
- memory-input lineage remains tied to HTBW-governed household-memory outputs.
- provenance-input lineage remains tied to HTBW-governed provenance outputs.
- event-history-input lineage remains tied to authoritative event-history outputs.
- identity-input lineage remains tied to HTBW/Voice Identity-governed identity outputs.
- room-input lineage remains tied to HTBW/Foundation-governed room outputs.

## 22. Deterministic Boundary Review

Validation scope:

- privacy participation
- retention participation
- guest participation
- suppression participation

Result: PASS

Deterministic requirements:

- same governed privacy/retention/guest-safe/suppression/memory/provenance/event-history/identity/room inputs produce the same boundary participation outcomes.
- privacy, retention, guest, and suppression participation remain deterministic and traceable.

## 23. Explainability Eligibility Review

Validation scope:

- explanation eligibility
- privacy-safe explanations
- guest-safe explanations

Result: PASS

Explainability eligibility remains bounded to governed privacy-safe and guest-safe explanation outcomes with explicit lineage preserved.

## 24. HM9 Readiness Review

Validation scope:

- future HM9 Household Memory Diagnostics Surface support

Result: PASS

Lineage sufficiency for HM9 is preserved through explicit privacy/retention/guest-safe/suppression traceability anchors.

## 25. Ownership Validation

Validation scope:

Coordinator does not own:

- privacy governance
- retention governance
- guest governance
- suppression governance
- visibility governance
- memory governance

Result: PASS

Coordinator consumes governed outcomes and owns none of the listed governance domains.

## 26. Ownership Drift Analysis

Validation scope:

No transfer of:

- privacy ownership
- retention ownership
- guest ownership
- suppression ownership
- memory ownership
- visibility ownership

Result: PASS

No ownership drift identified.

## 27. Downstream Guidance

Provide constraints only. Do not pre-design future issues.

- HM9 Household Memory Diagnostics Surface: preserve deterministic privacy/retention/guest-safe/suppression traceability anchors and keep diagnostics governance external.
- HM10 Household Memory Readiness Review: validate HM1-HM9 completeness, ownership preservation, determinism, and supportability readiness.

## 28. HM8 Baseline Determination

Result: PASS

Privacy, retention, and guest-safe memory boundaries are sufficiently documented for downstream E10 work.

## 29. Privacy Constraint Validation

Validation scope:

- Concierge consumes privacy outcomes
- Concierge consumes retention outcomes
- Concierge consumes guest-safe outcomes
- Concierge does not create privacy rules
- Concierge does not create retention rules
- Concierge does not create guest rules

Result: PASS

Privacy constraints are satisfied without governance transfer.

## 30. Final Determination

E10-HM8 PRIVACY, RETENTION, AND GUEST-SAFE MEMORY BOUNDARIES

APPROVED AS THE AUTHORITATIVE BASELINE

FOR PRIVACY-SAFE HOUSEHOLD MEMORY CONSUMPTION
