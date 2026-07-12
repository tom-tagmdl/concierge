# Occupancy-Aware Message Routing

## 1. Purpose

Define the authoritative E9-M4 architecture baseline for occupancy-aware routing consumption.

This document defines routing consumption architecture only.

This document is architecture and governance only.

This document does not implement routing engines, occupancy resolution, presence resolution, delivery logic, notification logic, fallback routing logic, or room determination.

## 2. Scope Reviewed

Reviewed authorities and governance inputs:

- HTBW #39
- HTBW #50
- Concierge #121
- Concierge #122
- Concierge #123
- M1 Messaging V2 Consumption Architecture
- M2 Person-Aware Messaging Policy
- M3 Room-Aware Messaging Policy
- E8A occupancy and presence artifacts

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#39, #50, #121, #122, #123, #134) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between M4 outputs and authoritative ADR/contract/model artifacts.

## 3. Messaging Authority Validation

Validation scope:

- messaging ownership
- messaging governance
- delivery ownership
- routing ownership

Result: PASS

Validated statements:

- Messaging behavior is owned by Concierge.
- Messaging governance for concierge messaging behavior remains in Concierge scope.
- Delivery behavior is owned by Concierge.
- Routing behavior is owned by Concierge.
- Coordinator consumes routing outcomes as bounded participation outcomes.

## 4. Occupancy Authority Validation

Validation scope:

- occupancy ownership
- occupancy governance
- occupancy definitions
- occupancy confidence ownership

Result: PASS

Validated statements:

- Occupancy ownership remains in HTBW.
- Occupancy governance remains in HTBW.
- Occupancy definitions remain in HTBW authorities.
- Occupancy confidence ownership remains in HTBW authorities.
- Coordinator consumes occupancy outcomes and occupancy confidence outcomes.
- Coordinator does not redefine occupancy contracts, models, confidence rules, or truth.

## 5. Presence Authority Validation

Validation scope:

- presence ownership
- presence governance
- presence definitions
- presence confidence ownership

Result: PASS

Validated statements:

- Presence ownership remains in HTBW.
- Presence governance remains in HTBW.
- Presence definitions remain in HTBW authorities.
- Presence confidence ownership remains in HTBW authorities.
- Coordinator consumes presence outcomes and presence confidence outcomes.
- Coordinator does not redefine presence contracts, models, confidence rules, or truth.

## 6. M1 Architecture Alignment Review

Result: PASS

M4 aligns with M1 messaging, routing, provenance, occupancy, and identity boundaries by preserving Concierge messaging/routing ownership while consuming externally governed occupancy, presence, identity, and provenance outcomes.

## 7. M2 Architecture Alignment Review

Result: PASS

M4 aligns with M2 identity participation, person-targeting participation, and person-aware lineage boundaries while keeping person and identity governance external.

## 8. M3 Architecture Alignment Review

Result: PASS

M4 aligns with M3 room-aware participation, room-targeting participation, and room-aware lineage boundaries while preserving external room truth and room determination ownership.

## 9. E8A Occupancy and Presence Alignment Review

Validation scope:

- occupancy participation
- presence participation
- room-aware participation
- multi-occupant participation
- guest-safe participation

Result: PASS

M4 consumes E8A occupancy/presence/room-aware/multi-occupant/guest-safe outcomes and confidence participation surfaces without ownership transfer.

## 10. Occupancy-Aware Routing Architecture

Validation scope:

- routing participation
- routing consumption
- routing lifecycle
- routing outcomes

Result: PASS

Architecture-only occupancy-aware routing consumption:

- routing participation: consume governed occupancy, presence, room, identity, and confidence context as routing participation inputs.
- routing consumption: consume routing participation outcomes under Concierge-owned routing behavior boundaries.
- routing lifecycle: availability -> participation -> bounded routing consumption -> routing outcome handoff.
- routing outcomes: preserve routing outcomes and lineage references for downstream explainability and diagnostics readiness.

## 11. Occupied Routing Review

Validation scope:

- occupied participation
- occupied routing consumption
- occupied routing lineage

Result: PASS

Occupied-state routing participation and consumption remain bounded to governed occupied outcomes with explicit lineage preserved.

## 12. Unoccupied Routing Review

Validation scope:

- unoccupied participation
- unoccupied routing consumption
- unoccupied routing lineage

Result: PASS

Unoccupied-state routing participation and consumption remain bounded to governed unoccupied outcomes with explicit lineage preserved.

## 13. Transitional Routing Review

Validation scope:

- transitional participation
- transitional routing consumption
- transitional routing lineage

Result: PASS

Transitional routing participation and consumption remain bounded to governed transition outcomes with explicit transition lineage preserved.

## 14. Occupancy-Aware Fallback Routing Review

Validation scope:

- fallback participation
- fallback routing consumption
- fallback routing lineage

Result: PASS

Fallback-routing participation and consumption remain bounded to governed fallback and guest-safe outcomes with explicit fallback lineage preserved.

## 15. Occupancy Confidence Participation Review

Validation scope:

- confidence participation
- confidence consumption
- confidence lineage
- confidence traceability

Result: PASS

Validated statements:

- Coordinator consumes occupancy confidence outcomes.
- Coordinator does not define confidence rules.
- Occupancy-confidence participation remains externally governed and consumed.
- Confidence lineage remains tied to explicit occupancy/source/context references.
- Confidence traceability is preserved for downstream explainability and diagnostics readiness.

## 16. Presence Participation Review

Validation scope:

- presence participation
- presence routing consumption
- presence lineage

Result: PASS

Presence participation and routing consumption remain bounded to governed presence outcomes with explicit presence lineage preserved.

## 17. Multi-Occupant Participation Review

Validation scope:

- multiple residents
- resident participation
- guest participation
- routing participation

Result: PASS

Multi-occupant routing participation remains bounded to governed resident/guest/context outcomes with explicit participant lineage preserved.

## 18. Occupancy-Aware Routing Lineage Architecture

Validation scope:

- occupancy inputs
- presence inputs
- confidence inputs
- room inputs
- identity inputs
- routing outcomes

Result: PASS

Lineage architecture:

- occupancy-input lineage remains tied to HTBW-governed occupancy outputs.
- presence-input lineage remains tied to HTBW-governed presence outputs.
- confidence-input lineage remains tied to HTBW-governed occupancy/presence confidence outputs.
- room-input lineage remains tied to HTBW/Foundation-governed room truth and determination outputs.
- identity-input lineage remains tied to HTBW-governed identity outputs.
- routing-outcome lineage remains tied to concierge-owned routing outcomes and bounded downstream delivery participation references.

## 19. Deterministic Routing Behavior Review

Validation scope:

- occupied routing
- unoccupied routing
- transitional routing
- fallback routing
- confidence participation

Result: PASS

Deterministic requirements:

- same governed occupancy/presence/room/identity/confidence inputs produce the same routing participation outcomes.
- occupied, unoccupied, and transitional routing handling remain deterministic and traceable.
- fallback routing handling remains deterministic and ownership-safe.
- confidence participation remains deterministic and traceable.

## 20. Explainability Readiness Review

Validation scope:

- future M9 Messaging Diagnostics and Explainability Surface support

Result: PASS

M4 preserves occupancy/presence/routing lineage references sufficient for M9 explainability participation without pre-designing M9.

## 21. Diagnostics Readiness Review

Validation scope:

- future M9 Messaging Diagnostics and Explainability Surface support

Result: PASS

M4 preserves routing traceability anchors and confidence participation references sufficient for M9 diagnostics participation without pre-designing M9.

## 22. Ownership Validation

Validation scope:

Coordinator does not own:

- occupancy governance
- presence governance
- occupancy confidence rules
- presence confidence rules
- room governance
- routing governance outside Concierge

Result: PASS

Coordinator consumes governed outcomes and owns none of the listed governance domains.

## 23. Ownership Drift Analysis

Validation scope:

No transfer of:

- occupancy ownership
- occupancy governance
- presence ownership
- presence governance
- room determination ownership
- provenance ownership

Result: PASS

No ownership drift identified.

## 24. Downstream Guidance

Provide constraints only. Do not pre-design future issues.

- M5 Guest-Safe Messaging Boundaries: consume guest-safe and unknown-presence outcomes, including fallback participation references, without transferring occupancy/presence/privacy governance ownership.
- M6 Notification Discipline and Calm-by-Default Policy: define concierge notification discipline while consuming occupancy/presence/routing/confidence outcomes under external governance boundaries.
- M7 Escalation and Acknowledgement Model: define concierge escalation and acknowledgement behavior with deterministic occupancy-aware routing lineage references.
- M8 Message Provenance and Delivery History Consumption: consume HTBW-governed provenance while preserving occupancy-aware routing and delivery history lineage boundaries.
- M9 Messaging Diagnostics and Explainability Surface: consume M1/M2/M3/M4 lineage and traceability anchors for diagnostics and explainability participation.
- M10 Messaging V2 Readiness Review: validate M1 through M9 completeness, authority alignment, ownership preservation, determinism, and supportability readiness.

## 25. M4 Baseline Determination

Result: PASS

Occupancy-aware routing is sufficiently documented for downstream E9 work.

## 26. Final Determination

E9-M4 OCCUPANCY-AWARE MESSAGE ROUTING

APPROVED AS THE AUTHORITATIVE BASELINE

FOR OCCUPANCY-AWARE ROUTING CONSUMPTION
