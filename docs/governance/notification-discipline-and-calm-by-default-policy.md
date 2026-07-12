# Notification Discipline and Calm-by-Default Policy

## 1. Purpose

Define the authoritative E9-M6 architecture baseline for notification discipline consumption.

This document defines notification discipline consumption architecture only.

This document is architecture and governance only.

This document does not implement notification delivery, suppression engines, prioritization algorithms, escalation logic, urgency calculations, or routing logic.

## 2. Scope Reviewed

Reviewed authorities and governance inputs:

- HTBW #39
- HTBW #47
- HTBW #50
- Concierge #117
- M1 Messaging V2 Consumption Architecture
- M2 Person-Aware Messaging Policy
- M4 Occupancy-Aware Message Routing
- M5 Guest-Safe Messaging Boundaries

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#39, #47, #50, #117, #136) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between M6 outputs and authoritative ADR/contract/model artifacts.

## 3. Messaging Authority Validation

Validation scope:

- messaging ownership
- notification ownership
- delivery ownership
- notification discipline ownership

Result: PASS

Validated statements:

- Messaging behavior is owned by Concierge.
- Notification behavior is owned by Concierge.
- Delivery behavior is owned by Concierge.
- Notification discipline behavior is owned by Concierge.
- Coordinator consumes notification outcomes and messaging outcomes as bounded participation outcomes.

## 4. Suppression and Prioritization Validation

Validation scope:

- suppression governance ownership
- prioritization governance ownership
- urgency governance ownership
- escalation governance ownership

Result: PASS

Validated statements:

- Suppression governance ownership remains external.
- Prioritization governance ownership remains external.
- Urgency governance ownership remains external.
- Escalation governance ownership remains external.
- Coordinator consumes suppression outcomes, prioritization outcomes, and escalation outcomes.
- Coordinator does not define suppression policy, prioritization policy, urgency policy, or escalation policy.

## 5. Occupancy / Identity / Provenance Validation

Validation scope:

- occupancy ownership
- identity ownership
- provenance ownership

Result: PASS

Validated statements:

- Occupancy ownership remains in HTBW.
- Identity ownership remains in HTBW.
- Provenance ownership remains in HTBW.
- Coordinator consumes occupancy outcomes, identity outcomes, and provenance outcomes.
- Coordinator does not redefine occupancy, identity, or provenance contracts/models/truth.

## 6. M1 Architecture Alignment Review

Result: PASS

M6 aligns with M1 messaging/notification/delivery/provenance/occupancy/identity boundaries and preserves consumption-only participation across externally governed domains.

## 7. M2 Architecture Alignment Review

Result: PASS

M6 aligns with M2 identity participation, person-targeting participation, and identity-confidence participation boundaries while preserving external identity governance ownership.

## 8. M4 Architecture Alignment Review

Result: PASS

M6 aligns with M4 occupancy participation, presence participation, routing participation, and confidence participation boundaries while preserving external occupancy and presence governance ownership.

## 9. M5 Architecture Alignment Review

Result: PASS

M6 aligns with M5 guest-safe participation, privacy-safe participation, fallback participation, and restriction participation boundaries while preserving external guest/privacy/fallback governance ownership.

## 10. Notification Discipline Architecture

Validation scope:

- notification participation
- notification consumption
- notification lifecycle
- notification outcomes

Result: PASS

Architecture-only notification discipline consumption:

- notification participation: consume governed suppression, prioritization, escalation, occupancy, identity, and provenance context as notification discipline inputs.
- notification consumption: consume notification-discipline outcomes under Concierge-owned messaging and notification behavior boundaries.
- notification lifecycle: availability -> participation -> bounded discipline consumption -> notification outcome handoff.
- notification outcomes: preserve notification outcomes and lineage references for downstream explainability and diagnostics readiness.

## 11. Calm-by-Default Review

Validation scope:

- calm-by-default participation
- calm-by-default consumption
- calm-by-default lineage

Result: PASS

Validated statements:

- Coordinator consumes calm-by-default outcomes.
- Coordinator does not define calm-by-default governance.
- Calm-by-default participation and consumption remain bounded to governed calm-by-default outcomes with explicit lineage preserved.

## 12. Notification Suppression Review

Validation scope:

- suppression participation
- suppression consumption
- suppression lineage

Result: PASS

Validated statements:

- Coordinator consumes suppression outcomes.
- Coordinator does not define suppression policy.
- Suppression participation and consumption remain bounded to governed suppression outcomes with explicit lineage preserved.

## 13. Notification Prioritization Review

Validation scope:

- prioritization participation
- prioritization consumption
- prioritization lineage

Result: PASS

Validated statements:

- Coordinator consumes prioritization outcomes.
- Coordinator does not define prioritization policy.
- Prioritization participation and consumption remain bounded to governed prioritization outcomes with explicit lineage preserved.

## 14. Occupancy-Aware Quieting Review

Validation scope:

- occupancy participation
- quieting participation
- quieting lineage

Result: PASS

Occupancy-aware quieting participation and consumption remain bounded to governed occupancy outcomes with explicit quieting lineage preserved.

## 15. Identity-Aware Quieting Review

Validation scope:

- identity participation
- quieting participation
- identity-aware lineage

Result: PASS

Identity-aware quieting participation and consumption remain bounded to governed identity outcomes with explicit identity-aware lineage preserved.

## 16. Guest-Safe Quieting Review

Validation scope:

- guest participation
- privacy-safe participation
- quieting participation

Result: PASS

Guest-safe and privacy-safe quieting participation remain bounded to governed guest/privacy outcomes with explicit quieting lineage preserved.

## 17. Escalation Threshold Participation Review

Validation scope:

- escalation participation
- threshold participation
- escalation lineage

Result: PASS

Validated statements:

- Coordinator consumes escalation outcomes.
- Coordinator does not define escalation policy.
- Escalation and threshold participation remain bounded to governed escalation outcomes with explicit lineage preserved.

## 18. Notification Discipline Lineage Architecture

Validation scope:

- occupancy inputs
- identity inputs
- provenance inputs
- suppression outcomes
- prioritization outcomes
- escalation outcomes
- notification outcomes

Result: PASS

Lineage architecture:

- occupancy-input lineage remains tied to HTBW-governed occupancy outputs.
- identity-input lineage remains tied to HTBW-governed identity outputs.
- provenance-input lineage remains tied to HTBW-governed provenance references.
- suppression-outcome lineage remains tied to externally governed suppression outcomes.
- prioritization-outcome lineage remains tied to externally governed prioritization outcomes.
- escalation-outcome lineage remains tied to externally governed escalation outcomes.
- notification-outcome lineage remains tied to concierge-owned notification outcomes and bounded messaging participation references.

## 19. Deterministic Notification Discipline Review

Validation scope:

- suppression participation
- prioritization participation
- escalation participation
- calm-by-default participation
- quieting participation

Result: PASS

Deterministic requirements:

- same governed suppression/prioritization/escalation/occupancy/identity inputs produce the same notification discipline participation outcomes.
- suppression, prioritization, and escalation participation remain deterministic and traceable.
- calm-by-default and quieting participation remain deterministic and ownership-safe.

## 20. Explainability Readiness Review

Validation scope:

- future M9 Messaging Diagnostics and Explainability Surface support

Result: PASS

M6 preserves notification-discipline lineage references sufficient for M9 explainability participation without pre-designing M9.

## 21. Diagnostics Readiness Review

Validation scope:

- future M9 Messaging Diagnostics and Explainability Surface support

Result: PASS

M6 preserves traceability anchors for suppression, prioritization, escalation, calm-by-default, and quieting participation sufficient for M9 diagnostics participation without pre-designing M9.

## 22. Ownership Validation

Validation scope:

Coordinator does not own:

- suppression governance
- prioritization governance
- urgency governance
- escalation governance
- occupancy governance
- identity governance
- provenance governance

Result: PASS

Coordinator consumes governed outcomes and owns none of the listed governance domains.

## 23. Ownership Drift Analysis

Validation scope:

No transfer of:

- suppression governance ownership
- prioritization governance ownership
- escalation governance ownership
- occupancy ownership
- identity ownership
- provenance ownership

Result: PASS

No ownership drift identified.

## 24. Downstream Guidance

Provide constraints only. Do not pre-design future issues.

- M7 Escalation and Acknowledgement Model: consume governed escalation and threshold outcomes while preserving external escalation and urgency governance ownership.
- M8 Message Provenance and Delivery History Consumption: consume HTBW-governed provenance and preserve notification-discipline lineage boundaries across suppression/prioritization/escalation participation.
- M9 Messaging Diagnostics and Explainability Surface: consume M1/M2/M4/M5/M6 lineage and traceability anchors for diagnostics and explainability participation.
- M10 Messaging V2 Readiness Review: validate M1 through M9 completeness, authority alignment, ownership preservation, determinism, and supportability readiness.

## 25. M6 Baseline Determination

Result: PASS

Notification discipline and calm-by-default behavior are sufficiently documented for downstream E9 work.

## 26. Final Determination

E9-M6 NOTIFICATION DISCIPLINE AND CALM-BY-DEFAULT POLICY

APPROVED AS THE AUTHORITATIVE BASELINE

FOR NOTIFICATION DISCIPLINE CONSUMPTION
