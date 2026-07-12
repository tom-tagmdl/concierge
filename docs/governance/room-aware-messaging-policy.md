# Room-Aware Messaging Policy

## 1. Purpose

Define the authoritative E9-M3 architecture baseline for room-aware messaging consumption.

This document defines room-aware messaging consumption architecture only.

This document is architecture and governance only.

This document does not implement room determination, message delivery, notification delivery, room routing logic, room selection algorithms, or occupancy calculations.

## 2. Scope Reviewed

Reviewed authorities and governance inputs:

- HTBW #50
- Concierge #113
- M1 Messaging V2 Consumption Architecture
- M2 Person-Aware Messaging Policy
- E8A room-aware artifacts

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#50, #113, #133) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between M3 outputs and authoritative ADR/contract/model artifacts.

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

## 4. Room Authority Validation

Validation scope:

- room truth ownership
- room determination ownership
- room governance
- room confidence ownership

Result: PASS

Validated statements:

- Room truth ownership remains in HTBW/Foundation authorities.
- Room determination ownership remains in HTBW/Foundation authorities.
- Room governance remains external to Coordinator.
- Room confidence ownership remains external to Coordinator.
- Coordinator consumes room-aware outcomes, room occupancy outcomes, and room context outcomes.
- Coordinator does not redefine room truth, room determination, room contracts, room models, or room governance.

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

M3 conforms to M1 by preserving Concierge ownership of messaging/notification/delivery behavior while preserving HTBW ownership of room, occupancy, identity, and provenance governance domains.

## 7. M2 Architecture Alignment Review

Validation scope:

- person-aware participation
- identity participation
- targeting participation
- messaging lineage

Result: PASS

M3 aligns with M2 by consuming person-aware and identity participation as bounded context while adding room-aware participation without redefining targeting, identity, or lineage authorities.

## 8. E8A Room-Aware Alignment Review

Validation scope:

- room-aware participation
- room transitions
- room vacancy participation
- room confidence participation
- room lineage

Result: PASS

M3 consumes E8A room-aware outputs, including current-room, previous-room, transition, vacancy, confidence, and lineage outcomes, without room or occupancy ownership transfer.

## 9. Room-Aware Messaging Architecture

Validation scope:

- room-aware participation
- room-aware messaging consumption
- room-aware delivery participation
- room-aware outcomes

Result: PASS

Architecture-only room-aware messaging consumption:

- room-aware participation: consume governed room-aware context as bounded messaging inputs.
- room-aware messaging consumption: consume room-aware outcomes for messaging behavior orchestration within Concierge-owned boundaries.
- room-aware delivery participation: consume room-aware delivery participation outcomes as bounded delivery inputs.
- room-aware outcomes: preserve consumed room-aware outcomes for downstream explainability and diagnostics readiness.

## 10. Room Targeting Review

Validation scope:

- room targeting participation
- room targeting consumption
- room targeting lineage

Result: PASS

Validated statements:

- Coordinator consumes room-targeting outcomes.
- Coordinator does not define room-targeting policy.
- Room-targeting participation and consumption remain bounded to externally governed room-targeting outcomes with explicit lineage preserved.

## 11. Room-Specific Delivery Review

Validation scope:

- room delivery participation
- room delivery consumption
- room delivery lineage

Result: PASS

Room-specific delivery participation and consumption remain bounded to governed delivery outcomes with explicit room-delivery lineage preserved.

## 12. Room-Specific Messaging Review

Validation scope:

- room-specific message participation
- room-specific message consumption
- room-specific message lineage

Result: PASS

Room-specific message participation and consumption remain bounded to governed room-context messaging outcomes with explicit lineage preserved.

## 13. Current Room Participation Review

Validation scope:

- current room participation
- current room consumption
- current room lineage

Result: PASS

Current-room participation and consumption remain bounded to governed current-room outcomes with explicit lineage preserved.

## 14. Previous Room Participation Review

Validation scope:

- previous room participation
- previous room consumption
- previous room lineage

Result: PASS

Previous-room participation and consumption remain bounded to governed previous-room context outcomes with explicit lineage preserved.

## 15. Room Transition Participation Review

Validation scope:

- room transition participation
- room transition consumption
- room transition lineage

Result: PASS

Room-transition participation and consumption remain bounded to governed transition outcomes with explicit transition lineage preserved.

## 16. Room Vacancy Participation Review

Validation scope:

- room vacancy participation
- room vacancy consumption
- room vacancy lineage

Result: PASS

Room-vacancy participation and consumption remain bounded to governed vacancy outcomes with explicit vacancy lineage preserved.

## 17. Room-Aware Messaging Lineage Architecture

Validation scope:

- room inputs
- occupancy inputs
- identity inputs
- provenance inputs
- messaging outcomes

Result: PASS

Lineage architecture:

- room-input lineage remains tied to HTBW/Foundation-governed room truth and determination outputs.
- occupancy-input lineage remains tied to HTBW-governed occupancy outputs.
- identity-input lineage remains tied to HTBW-governed identity outputs.
- provenance-input lineage remains tied to HTBW-governed provenance references.
- messaging-outcome lineage remains tied to concierge-owned messaging outcomes and bounded delivery participation references.

## 18. Deterministic Room-Aware Behavior Review

Validation scope:

- room targeting
- room delivery participation
- room transition participation
- room vacancy participation

Result: PASS

Deterministic requirements:

- same governed room-aware inputs produce the same room-targeting and room-delivery participation outcomes.
- room-transition participation remains deterministic and traceable.
- room-vacancy participation remains deterministic and traceable.
- deterministic behavior remains ownership-safe across room-aware messaging surfaces.

## 19. Explainability Readiness Review

Validation scope:

- future M9 Messaging Diagnostics and Explainability Surface support

Result: PASS

M3 preserves room-aware lineage references sufficient for M9 explainability participation without pre-designing M9.

## 20. Diagnostics Readiness Review

Validation scope:

- future M9 Messaging Diagnostics and Explainability Surface support

Result: PASS

M3 preserves room-aware traceability anchors sufficient for M9 diagnostics participation without pre-designing M9.

## 21. Ownership Validation

Validation scope:

Coordinator does not own:

- room governance
- room determination
- occupancy governance
- identity governance
- provenance governance

Result: PASS

Coordinator consumes governed outcomes and owns none of the listed governance domains.

## 22. Ownership Drift Analysis

Validation scope:

No transfer of:

- room truth ownership
- room determination ownership
- occupancy ownership
- identity ownership
- provenance ownership

Result: PASS

No ownership drift identified.

## 23. Downstream Guidance

Provide constraints only. Do not pre-design future issues.

- M4 Occupancy-Aware Message Routing: consume occupancy and room-aware outcomes as governed routing participation context without transferring occupancy or room authority.
- M5 Guest-Safe Messaging Boundaries: consume guest-safe and unknown-presence outcomes with room-aware context under external privacy and fallback governance boundaries.
- M6 Notification Discipline and Calm-by-Default Policy: define concierge notification discipline while consuming room-aware, occupancy, identity, and provenance outcomes.
- M7 Escalation and Acknowledgement Model: define concierge escalation and acknowledgement behavior with deterministic room-aware lineage references.
- M8 Message Provenance and Delivery History Consumption: consume HTBW-governed provenance and preserve bounded room-aware delivery history references without redefining provenance truth.
- M9 Messaging Diagnostics and Explainability Surface: consume M1/M2/M3 lineage and traceability anchors for diagnostics and explainability surfaces.
- M10 Messaging V2 Readiness Review: validate M1 through M9 completeness, authority alignment, ownership preservation, determinism, and supportability readiness.

## 24. M3 Baseline Determination

Result: PASS

Room-aware messaging policy is sufficiently documented for downstream E9 work.

## 25. Final Determination

E9-M3 ROOM-AWARE MESSAGING POLICY

APPROVED AS THE AUTHORITATIVE BASELINE

FOR ROOM-AWARE MESSAGING CONSUMPTION
