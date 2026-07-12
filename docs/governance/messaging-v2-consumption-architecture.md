# Messaging V2 Consumption Architecture

## 1. Purpose

Define the authoritative E9-M1 architecture baseline for Coordinator messaging and notification consumption.

This document is architecture and governance only.

This document does not implement messaging delivery, notification delivery, routing logic, escalation logic, messaging policy, notification policy, or provenance tracking.

## 2. Scope Reviewed

Reviewed authorities and governance inputs:

- HTBW #39
- Concierge #111
- Concierge #112
- Concierge #121
- ER10 Restoration Consumption Readiness Review
- OP10 Occupancy and Presence Consumption Readiness Review

Reviewed messaging governance artifacts:

- ADR-012 Occupancy and Presence Governance Boundaries
- Occupancy and Presence Contract
- Occupancy and Presence Model
- Coordinator V2 Foundation Summary
- Concierge V1 Outcome Preservation Baseline

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#39, #111, #112, #121, #130, #131) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between M1 outputs and authoritative ADR/contract/model artifacts.

## 3. Messaging Authority Validation

Validation scope:

- messaging ownership
- messaging governance
- delivery ownership
- notification ownership

Result: PASS

Validated statements:

- Messaging behavior is owned by Concierge.
- Messaging governance for concierge messaging behavior remains in Concierge scope.
- Delivery behavior is owned by Concierge.
- Notification behavior is owned by Concierge.
- Coordinator consumes messaging outcomes and notification outcomes.

## 4. Provenance Authority Validation

Validation scope:

- provenance ownership
- provenance governance
- provenance definitions
- provenance lineage authority

Result: PASS

Validated statements:

- Provenance ownership remains in HTBW.
- Provenance governance remains in HTBW.
- Provenance definitions remain in HTBW authorities.
- Provenance lineage authority remains external to Coordinator.
- Coordinator consumes provenance outcomes.
- Coordinator does not redefine provenance contracts, models, lineage authority, or truth.

## 5. Occupancy and Identity Authority Validation

Validation scope:

- occupancy ownership
- occupancy governance
- identity ownership
- identity governance

Result: PASS

Validated statements:

- Occupancy ownership remains in HTBW.
- Occupancy governance remains in HTBW.
- Identity ownership remains in HTBW.
- Identity governance remains in HTBW.
- Coordinator consumes occupancy outcomes and identity outcomes.
- Coordinator does not redefine occupancy or identity contracts/models/truth.

## 6. E8 Alignment Review

Validation scope:

- restoration consumption alignment
- restoration dependency alignment
- restoration explainability alignment

Result: PASS

M1 aligns with ER10 readiness conclusions and consumes restoration outcomes, explainability references, and diagnostics references as dependency inputs only.

## 7. E8A Alignment Review

Validation scope:

- occupancy alignment
- presence alignment
- room-aware alignment
- multi-occupant alignment
- guest-safe alignment

Result: PASS

M1 aligns with OP10 readiness conclusions and consumes occupancy/presence/room-aware/multi-occupant/guest-safe/influence outcomes without ownership transfer.

## 8. Messaging Consumption Architecture

Validation scope:

- messaging inputs
- messaging outcomes
- messaging lifecycle
- Coordinator messaging participation

Result: PASS

Architecture-only messaging consumption:

- messaging inputs: consumed occupancy/presence/identity/provenance/restoration context references and messaging configuration references.
- messaging outcomes: consumed messaging outcome references for downstream participation.
- messaging lifecycle: availability -> eligibility participation -> routing participation -> delivery participation -> completion references.
- Coordinator messaging participation: Coordinator orchestrates bounded messaging consumption and does not redefine messaging policy truth outside Concierge-owned behavior.

## 9. Notification Consumption Architecture

Validation scope:

- notification inputs
- notification outcomes
- notification lifecycle
- Coordinator notification participation

Result: PASS

Architecture-only notification consumption:

- notification inputs: consumed notification context, occupancy/presence context, identity context, and provenance references.
- notification outcomes: consumed notification outcome references and delivery-state references.
- notification lifecycle: availability -> eligibility participation -> channel/routing participation -> delivery participation -> completion references.
- Coordinator notification participation: bounded consumption-only orchestration with no transfer of external governance domains.

## 10. Delivery Lifecycle Architecture

Validation scope:

- message creation
- message eligibility
- message routing
- message delivery
- message completion

Result: PASS

Architecture-only delivery lifecycle:

- message creation: create concierge-owned messaging artifacts from consumed context.
- message eligibility: consume governed eligibility outcomes from upstream domains.
- message routing: consume governed routing participation context and route within concierge messaging behavior boundaries.
- message delivery: consume delivery participation outcomes and preserve provenance/trace references.
- message completion: preserve completion outcomes and lineage references for explainability/diagnostics readiness.

## 11. Provenance Consumption Architecture

Validation scope:

- provenance participation
- provenance consumption
- provenance lineage requirements
- provenance traceability requirements

Result: PASS

Provenance consumption architecture:

- provenance participation: provenance context participates as externally governed references.
- provenance consumption: Coordinator consumes provenance outcomes and does not own provenance authority.
- provenance lineage requirements: preserve external provenance identifiers, source references, and bounded lineage references.
- provenance traceability requirements: preserve traceable provenance references for diagnostics and explainability readiness.

## 12. Occupancy Participation Review

Validation scope:

- occupancy participation in messaging
- occupancy participation in notification decisions

Result: PASS

Occupancy participates as consumed governed context in messaging and notification participation surfaces without policy ownership transfer.

## 13. Identity Participation Review

Validation scope:

- identity participation
- identity-aware delivery participation
- identity-aware messaging participation

Result: PASS

Identity participates as consumed governed context in messaging/delivery participation surfaces without identity governance transfer.

## 14. Restoration Relationship Review

Validation scope:

- restoration-driven messaging dependencies
- restoration-driven notification dependencies

Result: PASS

Restoration-driven messaging/notification dependencies are consumption-only and preserve restoration governance ownership external to Coordinator.

## 15. Ownership Boundary Architecture

Validation scope:

Explicit ownership boundaries.

Result: PASS

HTBW owns:

- provenance
- occupancy
- identity

Concierge owns:

- messaging behavior
- notification behavior
- delivery behavior

Coordinator consumes all governed outcomes.

## 16. Messaging Lineage Architecture

Validation scope:

- message source
- provenance inputs
- occupancy inputs
- identity inputs
- delivery outcomes

Result: PASS

Lineage architecture:

- message-source lineage remains tied to concierge-owned messaging generation surfaces.
- provenance-input lineage remains tied to HTBW-governed provenance references.
- occupancy-input lineage remains tied to HTBW-governed occupancy outputs.
- identity-input lineage remains tied to HTBW-governed identity outputs.
- delivery-outcome lineage remains tied to bounded lifecycle completion references.

## 17. Deterministic Messaging Consumption Review

Validation scope:

- messaging participation
- notification participation
- delivery participation
- provenance participation

Result: PASS

Deterministic requirements:

- same governed consumed inputs produce the same messaging and notification participation outcomes.
- delivery participation remains deterministic and traceable.
- provenance participation remains deterministic and ownership-safe.

## 18. Explainability Readiness Review

Validation scope:

- future M9 Messaging Diagnostics and Explainability Surface support

Result: PASS

M1 preserves messaging/provenance/occupancy/identity lineage references required for M9 explainability participation without pre-designing M9.

## 19. Diagnostics Readiness Review

Validation scope:

- future M9 Messaging Diagnostics and Explainability Surface support

Result: PASS

M1 preserves diagnostics traceability requirements and troubleshooting anchor references required for M9 diagnostics participation without pre-designing M9.

## 20. Ownership Validation

Validation scope:

Coordinator does not own:

- provenance governance
- occupancy governance
- identity governance
- messaging governance authorities outside Concierge

Result: PASS

Coordinator consumes governed outcomes and owns none of the listed external governance domains.

## 21. Ownership Drift Analysis

Validation scope:

No transfer of:

- provenance ownership
- occupancy ownership
- identity ownership

Result: PASS

No ownership drift identified.

## 22. Downstream Guidance

Provide constraints only. Do not pre-design future issues.

- M2 Person-Aware Messaging Policy: define person-aware messaging policy within Concierge ownership while consuming external identity/provenance/occupancy outcomes.
- M3 Room-Aware Messaging Policy: define room-aware messaging policy within Concierge ownership while preserving external room/occupancy governance boundaries.
- M4 Occupancy-Aware Message Routing: consume occupancy outcomes as governed routing participation context without transferring occupancy authority.
- M5 Guest-Safe Messaging Boundaries: consume guest-safe occupancy/presence outcomes while preserving external guest governance domains.
- M6 Notification Discipline and Calm-by-Default Policy: define concierge notification discipline while consuming externally governed confidence/influence/provenance references.
- M7 Escalation and Acknowledgement Model: define concierge escalation/acknowledgement behavior with deterministic provenance and delivery lineage references.
- M8 Message Provenance and Delivery History Consumption: consume HTBW-governed provenance and maintain bounded delivery history references without redefining provenance truth.
- M9 Messaging Diagnostics and Explainability Surface: consume M1 lineage/traceability anchors and downstream policy outcomes for diagnostics/explainability surfaces.
- M10 Messaging V2 Readiness Review: validate M1 through M9 completeness, ownership preservation, authority alignment, and supportability readiness.

## 23. M1 Baseline Determination

Result: PASS

Messaging V2 consumption architecture is sufficiently documented for all downstream E9 work.

## 24. Final Determination

E9-M1 MESSAGING V2 CONSUMPTION ARCHITECTURE

APPROVED AS THE AUTHORITATIVE BASELINE

FOR MESSAGING V2 GOVERNANCE CONSUMPTION
