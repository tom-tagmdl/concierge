# Person-Aware Messaging Policy

## 1. Purpose

Define the authoritative E9-M2 architecture baseline for person-aware messaging consumption.

This document defines person-aware messaging consumption architecture only.

This document is architecture and governance only.

This document does not implement messaging delivery, notification delivery, person resolution, identity resolution, recipient selection algorithms, personalization algorithms, or routing logic.

## 2. Scope Reviewed

Reviewed authorities and governance inputs:

- HTBW #45
- HTBW #47
- Concierge #103
- Concierge #114
- M1 Messaging V2 Consumption Architecture
- E7 person-aware governance artifacts
- E8A person-aware governance artifacts

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#45, #47, #103, #114, #132) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between M2 outputs and authoritative ADR/contract/model artifacts.

## 3. Messaging Authority Validation

Validation scope:

- messaging ownership
- messaging governance
- notification ownership
- delivery ownership

Result: PASS

Validated statements:

- Messaging behavior is owned by Concierge.
- Messaging governance for concierge messaging behavior remains in Concierge scope.
- Notification behavior is owned by Concierge.
- Delivery behavior is owned by Concierge.
- Coordinator consumes messaging outcomes and delivery outcomes.

## 4. Identity Authority Validation

Validation scope:

- identity ownership
- identity governance
- identity definitions
- identity confidence ownership

Result: PASS

Validated statements:

- Identity ownership remains in HTBW.
- Identity governance remains in HTBW.
- Identity definitions remain in HTBW authorities.
- Identity confidence ownership remains in HTBW authorities.
- Coordinator consumes identity outcomes and identity confidence outcomes.
- Coordinator does not redefine identity contracts, models, confidence rules, or truth.

## 5. Provenance Authority Validation

Validation scope:

- provenance ownership
- provenance governance
- provenance lineage authority

Result: PASS

Validated statements:

- Provenance ownership remains in HTBW.
- Provenance governance remains in HTBW.
- Provenance lineage authority remains external to Coordinator.
- Coordinator consumes provenance outcomes.
- Coordinator does not redefine provenance contracts, models, lineage authority, or truth.

## 6. M1 Architecture Alignment Review

Validation scope:

- messaging boundaries
- provenance boundaries
- occupancy boundaries
- identity boundaries

Result: PASS

M2 conforms to M1 by preserving Concierge ownership of messaging/notification/delivery behavior while preserving HTBW ownership of provenance, occupancy, and identity governance domains.

## 7. E7 Person-Aware Alignment Review

Validation scope:

- person-aware participation
- continuity participation
- affinity participation
- identity participation

Result: PASS

M2 consumes E7 outputs by using externally governed person continuity and person-room affinity participation context with no transfer of continuity, affinity, or identity governance ownership.

## 8. E8A Alignment Review

Validation scope:

- occupancy participation
- room-aware participation
- multi-occupant participation
- guest-safe participation

Result: PASS

M2 consumes E8A occupancy/presence outcomes as bounded person-aware context inputs, including room-aware, multi-occupant, and guest-safe participation, without redefining occupancy governance.

## 9. Person-Aware Messaging Architecture

Validation scope:

- person-aware participation
- person-aware messaging consumption
- person-aware delivery participation
- person-aware outcomes

Result: PASS

Architecture-only person-aware messaging consumption:

- person-aware participation: consume governed person context, identity context, and confidence context as bounded inputs.
- person-aware messaging consumption: consume person-aware outcomes for message intent shaping within Concierge-owned messaging behavior boundaries.
- person-aware delivery participation: consume person-aware delivery participation outcomes for bounded delivery orchestration.
- person-aware outcomes: preserve consumed person-aware outcome references for downstream explainability and diagnostics readiness.

## 10. Person Targeting Review

Validation scope:

- targeting participation
- targeting consumption
- targeting lineage

Result: PASS

Validated statements:

- Coordinator consumes targeting outcomes.
- Coordinator does not define targeting policy.
- Targeting participation and targeting consumption remain bounded to externally governed targeting outcomes with explicit lineage preserved.

## 11. Person-Specific Delivery Review

Validation scope:

- delivery participation
- delivery consumption
- delivery lineage

Result: PASS

Person-specific delivery participation and consumption remain bounded to governed delivery outcomes with explicit delivery lineage preserved.

## 12. Person-Specific Message Selection Review

Validation scope:

- message selection participation
- message selection consumption
- message selection lineage

Result: PASS

Validated statements:

- Coordinator consumes message-selection outcomes.
- Coordinator does not define identity policy.
- Message-selection participation and consumption remain bounded to governed selection outcomes with explicit lineage preserved.

## 13. Identity Confidence Participation Review

Validation scope:

- identity confidence participation
- confidence consumption
- confidence lineage
- confidence traceability

Result: PASS

Validated statements:

- Coordinator consumes identity confidence outcomes.
- Coordinator does not define confidence rules.
- Identity-confidence participation remains externally governed and consumed.
- Confidence lineage remains tied to explicit identity/source/context references.
- Confidence traceability is preserved for downstream explainability and diagnostics readiness.

## 14. Occupancy Participation Review

Validation scope:

- occupancy participation in person-aware messaging
- occupancy participation in person-aware delivery

Result: PASS

Occupancy participates as consumed governed context in person-aware messaging and person-aware delivery participation surfaces without occupancy ownership transfer.

## 15. Multi-Occupant Participation Review

Validation scope:

- multiple residents
- resident interactions
- identity participation
- context participation

Result: PASS

Multi-occupant person-aware participation remains bounded to governed resident and interaction outcomes with explicit identity/context lineage preserved.

## 16. Guest-Aware Participation Review

Validation scope:

- guest-aware participation
- guest-safe participation
- unknown-person participation

Result: PASS

Guest-aware and unknown-person participation remain bounded to governed guest-safe and fallback outcomes with explicit lineage preserved.

## 17. Person-Aware Messaging Lineage Architecture

Validation scope:

- identity inputs
- identity confidence inputs
- occupancy inputs
- provenance inputs
- messaging outcomes

Result: PASS

Lineage architecture:

- identity-input lineage remains tied to HTBW-governed identity outputs.
- identity-confidence lineage remains tied to HTBW-governed confidence outputs.
- occupancy-input lineage remains tied to HTBW-governed occupancy outputs.
- provenance-input lineage remains tied to HTBW-governed provenance references.
- messaging-outcome lineage remains tied to concierge-owned messaging outcomes and bounded delivery participation references.

## 18. Deterministic Person-Aware Behavior Review

Validation scope:

- person targeting
- delivery participation
- identity confidence participation
- guest participation
- multi-occupant participation

Result: PASS

Deterministic requirements:

- same governed person-aware inputs produce the same targeting and delivery participation outcomes.
- identity-confidence participation remains deterministic and traceable.
- guest participation remains deterministic under governed guest-safe boundaries.
- multi-occupant participation remains deterministic under governed conflict and precedence boundaries.

## 19. Explainability Readiness Review

Validation scope:

- future M9 Messaging Diagnostics and Explainability Surface support

Result: PASS

M2 preserves identity/person/occupancy/provenance/messaging lineage references sufficient for M9 explainability participation without pre-designing M9.

## 20. Diagnostics Readiness Review

Validation scope:

- future M9 Messaging Diagnostics and Explainability Surface support

Result: PASS

M2 preserves traceability anchors and troubleshooting references sufficient for M9 diagnostics participation without pre-designing M9.

## 21. Ownership Validation

Validation scope:

Coordinator does not own:

- identity governance
- identity confidence rules
- occupancy governance
- provenance governance

Result: PASS

Coordinator consumes governed outcomes and owns none of the listed governance domains.

## 22. Ownership Drift Analysis

Validation scope:

No transfer of:

- identity ownership
- identity governance
- identity confidence ownership
- occupancy ownership
- provenance ownership

Result: PASS

No ownership drift identified.

## 23. Downstream Guidance

Provide constraints only. Do not pre-design future issues.

- M3 Room-Aware Messaging Policy: consume room-aware occupancy and person-aware outputs while preserving external room and occupancy governance ownership.
- M4 Occupancy-Aware Message Routing: consume occupancy outcomes as governed routing participation context without transferring occupancy authority.
- M5 Guest-Safe Messaging Boundaries: consume guest-safe and unknown-person outcomes under external privacy and fallback governance boundaries.
- M6 Notification Discipline and Calm-by-Default Policy: define concierge notification discipline while consuming external identity confidence, occupancy, and provenance outcomes.
- M7 Escalation and Acknowledgement Model: define concierge escalation and acknowledgement behavior with deterministic person-aware lineage references.
- M8 Message Provenance and Delivery History Consumption: consume HTBW-governed provenance and preserve bounded person-aware delivery history references without redefining provenance truth.
- M9 Messaging Diagnostics and Explainability Surface: consume M1 and M2 lineage and traceability anchors for diagnostics and explainability surfaces.
- M10 Messaging V2 Readiness Review: validate M1 through M9 completeness, authority alignment, ownership preservation, determinism, and supportability readiness.

## 24. M2 Baseline Determination

Result: PASS

Person-aware messaging policy is sufficiently documented for downstream E9 work.

## 25. Final Determination

E9-M2 PERSON-AWARE MESSAGING POLICY

APPROVED AS THE AUTHORITATIVE BASELINE

FOR PERSON-AWARE MESSAGING CONSUMPTION
