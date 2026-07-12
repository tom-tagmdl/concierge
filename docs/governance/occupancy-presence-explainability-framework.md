# Occupancy and Presence Explainability Framework

## 1. Purpose

Define the authoritative E8A-OP8 architecture baseline for occupancy and presence explainability consumption.

This document is architecture and governance only.

This document does not implement explainability generation, diagnostics behavior, occupancy resolution, presence resolution, confidence calculations, routing logic, eligibility logic, or prioritization logic.

Explainability describes consumed outcomes and consumed lineage.

Explainability does not create truth and does not create governance.

## 2. Scope Reviewed

Reviewed authorities and governance inputs:

- HTBW #50
- Concierge #118
- OP4 Room-Aware Occupancy Consumption
- OP5 Multi-Occupant Context Consumption
- OP6 Guest and Unknown Presence Behavior
- OP7 Occupancy and Presence Influence Matrix
- ER8 Restoration Explainability Framework

Reviewed explainability governance artifacts:

- ADR-012 Occupancy and Presence Governance Boundaries
- Occupancy and Presence Contract
- Occupancy and Presence Model
- Continuity and Affinity Explainability Framework
- Experience Explainability Framework
- Capability Explainability Framework
- Vocabulary Explainability Framework

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#50, #118, #124, #125, #126, #127, #128) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between OP8 outputs and authoritative ADR/contract/model/governance artifacts.

## 3. Occupancy Authority Validation

Validation scope:

- occupancy ownership
- occupancy governance
- occupancy confidence
- occupancy policy

Result: PASS

Validated statements:

- Occupancy ownership remains in HTBW.
- Occupancy governance remains in HTBW.
- Occupancy confidence remains in HTBW authorities.
- Occupancy policy remains in HTBW authorities.
- Coordinator explains consumed occupancy outcomes.
- Coordinator explains consumed confidence outcomes.
- Coordinator does not create occupancy truth.
- Coordinator does not create occupancy governance.

## 4. Presence Authority Validation

Validation scope:

- presence ownership
- presence governance
- presence confidence
- presence policy

Result: PASS

Validated statements:

- Presence ownership remains in HTBW.
- Presence governance remains in HTBW.
- Presence confidence remains in HTBW authorities.
- Presence policy remains in HTBW authorities.
- Coordinator explains consumed presence outcomes.
- Coordinator explains consumed confidence outcomes.
- Coordinator does not create presence truth.
- Coordinator does not create presence governance.

## 5. Explainability Governance Validation

Validation scope:

- explainability ownership
- explainability authority
- explainability boundaries

Result: PASS

Validated statements:

- Explainability ownership remains externally governed through HTBW-aligned explainability authorities.
- Explainability authority remains external; Coordinator role is bounded to explaining consumed outcomes and consumed lineage.
- Explainability boundaries prevent Coordinator from creating confidence policy, influence policy, occupancy truth, presence truth, or alternate governance truth.

## 6. OP4 Lineage Validation

Validation scope:

- room occupancy lineage
- room transition lineage
- room confidence lineage

Result: PASS

OP8 consumes OP4 room occupancy, room transition, and room confidence lineage references and preserves room traceability.

## 7. OP5 Lineage Validation

Validation scope:

- multi-occupant lineage
- conflict lineage
- confidence lineage

Result: PASS

OP8 consumes OP5 multi-occupant, conflict, and confidence lineage references and preserves traceability for explainability surfaces.

## 8. OP6 Lineage Validation

Validation scope:

- guest lineage
- unknown lineage
- fallback lineage
- privacy-safe lineage

Result: PASS

OP8 consumes OP6 guest, unknown, fallback, and privacy-safe lineage references and preserves traceability for explainability surfaces.

## 9. OP7 Influence Lineage Validation

Validation scope:

- routing influence lineage
- restoration influence lineage
- eligibility lineage
- prioritization lineage

Result: PASS

OP8 consumes OP7 influence lineage, including routing, restoration, eligibility, and prioritization lineage, and preserves precedence-linked traceability.

## 10. Machine-Readable Explainability Framework

Validation scope:

- machine-readable occupancy explanations
- machine-readable presence explanations
- machine-readable confidence explanations
- machine-readable lineage references

Result: PASS

Architecture-only machine-readable framework:

- explanation_id
- outcome_reference
- occupancy_references
- presence_references
- confidence_references
- room_lineage_references
- multi_occupant_lineage_references
- guest_unknown_lineage_references
- influence_lineage_references
- precedence_references
- fallback_references
- privacy_safe_references
- traceability_references
- timestamp

Coordinator explains consumed outcomes and consumed lineage using bounded structured references.

Coordinator does not create truth and does not create governance.

## 11. Human-Readable Explainability Framework

Validation scope:

- room occupancy explanations
- presence explanations
- confidence explanations
- guest explanations
- influence explanations

Result: PASS

Architecture-only human-readable framework:

- occupancy outcome summary
- presence validity summary
- confidence participation summary
- room-transition or vacancy rationale when applicable
- guest or unknown rationale when applicable
- influence rationale for routing/restoration/notification/eligibility/prioritization when applicable
- ownership-safe boundary statement

Human-readable explanations describe consumed outcomes and consumed lineage without redefining authority.

## 12. Occupied Room Explanation Review

Validation scope:

- room considered occupied
- room transitions
- room vacancy outcomes

Result: PASS

Room-occupied, room-transition, and room-vacancy explanations preserve bounded references to consumed room-aware outcomes and room lineage.

## 13. Presence Validity Explanation Review

Validation scope:

- known presence
- unknown presence
- confidence participation

Result: PASS

Presence-validity explanations preserve bounded references to known/unknown presence outcomes and confidence participation lineage.

## 14. Confidence Threshold Explanation Review

Validation scope:

- confidence threshold participation
- confidence threshold outcomes
- confidence lineage

Result: PASS

Confidence-threshold explanations preserve bounded references to consumed threshold participation outcomes, threshold outcomes, and confidence lineage.

## 15. Guest and Unknown Explanation Review

Validation scope:

- guest outcomes
- unknown outcomes
- fallback outcomes
- privacy-safe outcomes

Result: PASS

Guest and unknown explanations preserve bounded references to consumed guest/unknown outcomes, fallback outcomes, and privacy-safe outcomes with lineage intact.

## 16. Influence Explanation Review

Validation scope:

- routing influence
- restoration influence
- notification influence
- eligibility influence
- prioritization influence

Result: PASS

Influence explanations preserve bounded references to consumed routing/restoration/notification/eligibility/prioritization influence outcomes and lineage.

## 17. Explainability Lineage Architecture

Validation scope:

- occupancy participation
- presence participation
- confidence participation
- room participation
- guest participation
- multi-occupant participation
- influence participation

Result: PASS

Lineage architecture:

- occupancy participation lineage remains tied to governed occupancy outcomes.
- presence participation lineage remains tied to governed presence outcomes.
- confidence participation lineage remains tied to governed confidence outcomes.
- room participation lineage remains tied to governed room-aware outcomes.
- guest participation lineage remains tied to governed guest/unknown outcomes.
- multi-occupant participation lineage remains tied to governed multi-occupant/conflict outcomes.
- influence participation lineage remains tied to governed routing/restoration/notification/eligibility/prioritization outcomes.

## 18. Explainability Consistency Review

Validation scope:

- deterministic
- traceable
- ownership-safe
- authority-aligned

Result: PASS

Validated statements:

- explainability outputs are deterministic for the same governed consumed inputs.
- explainability references remain traceable through bounded lineage paths.
- explainability remains ownership-safe and does not create Coordinator-owned policy or truth.
- explainability remains authority-aligned with ADRs, contracts, models, and approved governance baselines.

## 19. Diagnostics Alignment Review

Validation scope:

- future OP9 Occupancy and Presence Diagnostics Surface support
- diagnostics navigation support from explainability references

Result: PASS

OP8 preserves explainability references that support OP9 diagnostics navigation, troubleshooting, and trace correlation without pre-designing OP9 implementation.

## 20. Ownership Validation

Validation scope:

Coordinator does not own:

- occupancy governance
- presence governance
- confidence rules
- guest governance
- influence governance
- explainability governance

Result: PASS

Coordinator explains consumed outcomes and consumed lineage and owns none of the listed domains.

## 21. Ownership Drift Analysis

Validation scope:

No transfer of:

- occupancy governance
- presence governance
- confidence governance
- guest governance
- influence governance
- explainability governance

Result: PASS

No ownership drift identified.

## 22. Downstream Guidance

Provide constraints only. Do not pre-design future issues.

- OP9 Occupancy and Presence Diagnostics Surface: consume OP8 explainability references, lineage references, and machine-readable/human-readable explainability anchors for diagnostics navigation and troubleshooting.
- OP10 Occupancy and Presence Consumption Readiness Review: validate OP1 through OP9 authority alignment, explainability coverage, diagnostics alignment, lineage sufficiency, and ownership preservation.

## 23. OP8 Baseline Determination

Result: PASS

Occupancy and presence explainability is sufficiently documented for downstream E8a work.

## 24. Final Determination

E8A-OP8 OCCUPANCY AND PRESENCE EXPLAINABILITY FRAMEWORK

APPROVED AS THE AUTHORITATIVE BASELINE

FOR OCCUPANCY AND PRESENCE EXPLAINABILITY
