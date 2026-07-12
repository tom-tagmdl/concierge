# Occupancy Presence Consumption Architecture

## 1. Purpose

Define the authoritative E8A-OP1 architecture baseline for how Coordinator consumes occupancy and presence governance artifacts.

This document is architecture and governance only.

This document does not implement occupancy behavior, presence behavior, occupancy resolution, presence resolution, confidence evaluation, diagnostics behavior, or explainability behavior.

## 2. Scope Reviewed

Reviewed authorities and governance inputs:

- HTBW #23
- HTBW #39
- HTBW #50
- ER10 Restoration Consumption Readiness Review

Reviewed occupancy and presence authority artifacts:

- ADR-012 Occupancy and Presence Governance Boundaries
- Occupancy and Presence Contract
- Occupancy and Presence Model

Reviewed E8 alignment artifacts:

- ER1 Restoration Consumption Architecture
- ER2 Restoration Candidate Resolution Pipeline
- ER3 Room-Aware Restoration Consumption
- ER4 Person-Aware Restoration Consumption
- ER5 Guest and Unknown Restoration Consumption
- ER6 Multi-Occupant Restoration Conflict Policy
- ER7 Restoration Suppression and Prioritization Framework
- ER8 Restoration Explainability Framework
- ER9 Restoration Diagnostics Surface

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#23, #39, #50, #120, #121) are execution inputs and are not architecture authority.

## 3. Occupancy Authority Validation

Validation scope:

- occupancy ownership
- occupancy governance
- occupancy definitions
- occupancy confidence
- occupancy policy

Result: PASS

Validated statements:

- Occupancy ownership remains in HTBW.
- Occupancy governance remains in HTBW.
- Occupancy definitions remain in HTBW authorities.
- Occupancy confidence governance remains in HTBW authorities.
- Occupancy policy remains in HTBW authorities.
- Coordinator consumes occupancy outcomes and occupancy confidence outcomes.
- Coordinator does not define occupancy ownership, governance, definitions, confidence rules, or policy.

## 4. Presence Authority Validation

Validation scope:

- presence ownership
- presence governance
- presence definitions
- presence confidence
- presence policy

Result: PASS

Validated statements:

- Presence ownership remains in HTBW.
- Presence governance remains in HTBW.
- Presence definitions remain in HTBW authorities.
- Presence confidence governance remains in HTBW authorities.
- Presence policy remains in HTBW authorities.
- Coordinator consumes presence outcomes and presence confidence outcomes.
- Coordinator does not define presence ownership, governance, definitions, confidence rules, or policy.

## 5. E8 Readiness Alignment Review

Validation scope:

- ER10 readiness assumptions
- occupancy dependencies
- presence dependencies
- restoration consumption dependencies

Result: PASS

Validated alignment statements:

- OP1 aligns with ER10 readiness determination and E8a start criteria.
- OP1 preserves occupancy and presence dependency mappings identified during ER10.
- OP1 preserves restoration-consumption relationships where occupancy/presence context participates without ownership transfer.

## 6. Occupancy Consumption Architecture

Validation scope:

- occupancy inputs
- occupancy outcomes
- occupancy confidence consumption
- occupancy participation lifecycle
- occupancy consumption responsibilities

Result: PASS

Architecture-only occupancy consumption:

- occupancy inputs: consumed occupancy state, occupancy source references, room-scoped occupancy context, freshness context.
- occupancy outcomes: consumed occupancy outcomes for downstream participation surfaces.
- occupancy confidence consumption: consumed occupancy-confidence and identity-confidence references.
- occupancy participation lifecycle: availability -> participation -> bounded consumption -> downstream outcome participation.
- occupancy consumption responsibilities: Coordinator consumes and applies bounded participation context only.

## 7. Presence Consumption Architecture

Validation scope:

- presence inputs
- presence outcomes
- presence confidence consumption
- presence participation lifecycle
- presence consumption responsibilities

Result: PASS

Architecture-only presence consumption:

- presence inputs: consumed presence-derived context, attribution-linked presence references, room interaction-space references.
- presence outcomes: consumed presence outcomes for bounded participation.
- presence confidence consumption: consumed presence-confidence and attribution-confidence references.
- presence participation lifecycle: availability -> participation -> bounded consumption -> downstream outcome participation.
- presence consumption responsibilities: Coordinator consumes and applies bounded participation context only.

## 8. Confidence Consumption Architecture

Validation scope:

- occupancy confidence participation
- presence confidence participation
- confidence consumption boundaries
- confidence lineage requirements

Result: PASS

Architecture-only confidence consumption:

- occupancy confidence participation remains externally governed and consumed as explicit confidence references.
- presence confidence participation remains externally governed and consumed as explicit confidence references.
- confidence consumption boundaries prohibit confidence-authority ownership transfer into Coordinator.
- confidence lineage requirements preserve source, timestamp, and participation references for explainability and diagnostics readiness.

## 9. Coordinator Integration Architecture

Validation scope:

- occupancy inputs
- occupancy outputs
- presence inputs
- presence outputs
- orchestration participation
- runtime integration boundaries

Result: PASS

Coordinator integration architecture:

- occupancy inputs: consumed occupancy state, confidence, source references, and freshness references.
- occupancy outputs: bounded occupancy participation references for downstream coordinator decisions.
- presence inputs: consumed presence-derived context and confidence references.
- presence outputs: bounded presence participation references for downstream coordinator decisions.
- orchestration participation: Coordinator orchestrates consumption participation and does not author occupancy/presence truth.
- runtime integration boundaries: integration remains consumption-only and ownership-preserving.

## 10. Ownership Boundary Architecture

Validation scope:

HTBW owns:

- occupancy governance
- occupancy definitions
- occupancy confidence rules
- occupancy policy
- presence governance
- presence definitions
- presence confidence rules
- presence policy

Coordinator consumes:

- occupancy outcomes
- occupancy confidence outcomes
- presence outcomes
- presence confidence outcomes

Result: PASS

Ownership boundaries are explicit and preserved.

## 11. Occupancy Lifecycle Architecture

Validation scope:

- occupancy availability
- occupancy confidence availability
- occupancy participation
- occupancy consumption
- occupancy completion

Result: PASS

Lifecycle architecture:

- occupancy availability: governed occupancy state and source context are made available as external inputs.
- occupancy confidence availability: governed confidence references are made available as external inputs.
- occupancy participation: occupancy context participates in bounded coordinator decision surfaces.
- occupancy consumption: coordinator consumes occupancy context without redefining occupancy authority.
- occupancy completion: occupancy participation outcomes remain traceable and ownership-safe.

## 12. Presence Lifecycle Architecture

Validation scope:

- presence availability
- presence confidence availability
- presence participation
- presence consumption
- presence completion

Result: PASS

Lifecycle architecture:

- presence availability: governed presence context and attribution-linked inputs are made available as external inputs.
- presence confidence availability: governed presence and attribution confidence references are made available as external inputs.
- presence participation: presence context participates in bounded coordinator decision surfaces.
- presence consumption: coordinator consumes presence context without redefining presence authority.
- presence completion: presence participation outcomes remain traceable and ownership-safe.

## 13. Restoration Relationship Review

Validation scope:

- occupancy-to-restoration relationships
- presence-to-restoration relationships
- confidence participation relationships

Result: PASS

Validated statements:

- occupancy and presence context may influence restoration participation boundaries.
- occupancy and presence context do not authorize restoration policy.
- occupancy-confidence and presence-confidence inputs participate as consumed eligibility/suppression/deferment influences under external governance.
- restoration ownership and policy authority remain external to Coordinator.

## 14. Explainability Readiness Review

Validation scope:

- future OP8 Occupancy and Presence Explainability Framework support

Result: PASS

OP1 preserves required lineage and confidence references needed by OP8 explainability without pre-designing OP8 implementation.

## 15. Diagnostics Readiness Review

Validation scope:

- future OP9 Occupancy and Presence Diagnostics Surface support

Result: PASS

OP1 preserves required traceability and bounded participation references needed by OP9 diagnostics without pre-designing OP9 implementation.

## 16. Ownership Validation

Validation scope:

Coordinator does not own:

- occupancy governance
- occupancy policy
- occupancy confidence rules
- presence governance
- presence policy
- presence confidence rules

Result: PASS

Coordinator consumes governed occupancy and presence outputs and owns none of the listed domains.

## 17. Ownership Drift Analysis

Validation scope:

No transfer of:

- occupancy governance
- occupancy policy
- occupancy confidence
- presence governance
- presence policy
- presence confidence

Result: PASS

No ownership drift identified.

## 18. Downstream Guidance

Provide constraints only. Do not pre-design future issues.

- OP2 Occupancy Resolution Pipeline: consume governed occupancy and confidence inputs; preserve ownership boundaries.
- OP3 Presence Resolution Pipeline: consume governed presence and confidence inputs; preserve ownership boundaries.
- OP4 Room-Aware Occupancy Consumption: preserve room-truth boundaries and room-scoped occupancy lineage.
- OP5 Multi-Occupant Context Consumption: preserve conflict visibility and confidence visibility with no policy ownership transfer.
- OP6 Guest and Unknown Presence Behavior: preserve guest-safe and unknown conservative defaults under external governance.
- OP7 Occupancy and Presence Influence Matrix: document bounded influence participation without redefining authority.
- OP8 Occupancy and Presence Explainability Framework: consume OP1 lineage/confidence references for machine and human explainability.
- OP9 Occupancy and Presence Diagnostics Surface: consume OP1 traceability references for diagnostics categories and troubleshooting paths.
- OP10 Occupancy and Presence Consumption Readiness Review: validate OP1 through OP9 ownership preservation, completeness, and authority alignment.

## 19. OP1 Baseline Determination

Result: PASS

Occupancy and presence consumption architecture is sufficiently documented for all downstream E8a work.

## 20. Final Determination

E8A-OP1 COORDINATOR OCCUPANCY AND PRESENCE CONSUMPTION ARCHITECTURE

APPROVED AS THE AUTHORITATIVE BASELINE

FOR OCCUPANCY AND PRESENCE GOVERNANCE CONSUMPTION
