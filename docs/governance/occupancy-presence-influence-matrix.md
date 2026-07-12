# Occupancy and Presence Influence Matrix

## 1. Purpose

Define the authoritative E8A-OP7 architecture baseline for occupancy and presence influence consumption.

This document is architecture and governance only.

This document does not implement influence calculations, routing logic, restoration logic, notification logic, eligibility logic, prioritization logic, diagnostics behavior, or explainability behavior.

## 2. Scope Reviewed

Reviewed authorities and governance inputs:

- HTBW #50
- Concierge #111
- Concierge #112
- Concierge #113
- Concierge #114
- Concierge #115
- Concierge #116
- Concierge #117
- Concierge #118
- Concierge #119
- Concierge #120
- OP4 Room-Aware Occupancy Consumption
- OP5 Multi-Occupant Context Consumption
- OP6 Guest and Unknown Presence Behavior

Reviewed influence governance artifacts:

- Continuity and Affinity Influence Matrix (CA8)
- ADR-012 Occupancy and Presence Governance Boundaries
- Occupancy and Presence Contract
- Occupancy and Presence Model

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#50, #111-#120, #124, #125, #126, #127) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between OP7 outputs and authoritative ADR/contract/model artifacts.

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
- Coordinator consumes occupancy outcomes.
- Coordinator consumes confidence outcomes.
- Coordinator does not define occupancy governance or confidence policy.

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
- Coordinator consumes presence outcomes.
- Coordinator consumes confidence outcomes.
- Coordinator does not define presence governance or confidence policy.

## 5. Influence Governance Validation

Validation scope:

- influence ownership
- eligibility ownership
- prioritization ownership
- routing ownership
- notification ownership

Result: PASS

Validated statements:

- Influence governance ownership remains external to Coordinator.
- Eligibility governance ownership remains in HTBW.
- Prioritization governance ownership remains in HTBW.
- Routing governance ownership remains in HTBW.
- Notification governance ownership remains in HTBW.
- Coordinator consumes influence outcomes.
- Coordinator consumes eligibility outcomes.
- Coordinator consumes prioritization outcomes.
- Coordinator does not define any of them.

## 6. OP4 Architecture Alignment Review

Result: PASS

OP7 consumes OP4 room-aware occupancy participation, room transitions, room-vacancy participation, room lineage, and room-confidence participation without redefining room governance.

## 7. OP5 Architecture Alignment Review

Result: PASS

OP7 consumes OP5 multi-occupant participation, conflict participation, occupant-context participation, and confidence participation without redefining multi-occupant governance.

## 8. OP6 Architecture Alignment Review

Result: PASS

OP7 consumes OP6 guest participation, unknown-presence participation, privacy-safe participation, fallback participation, and confidence participation without redefining guest or fallback governance.

## 9. Occupancy and Presence Influence Architecture

Validation scope:

- influence participation
- influence consumption
- influence lifecycle
- influence outcomes

Result: PASS

Architecture-only influence consumption:

- influence participation: consume governed occupancy, presence, room-aware, multi-occupant, guest, and confidence outcomes as bounded influence inputs.
- influence consumption: consume externally governed influence outcomes for downstream decision surfaces without policy-definition ownership.
- influence lifecycle: availability -> bounded influence participation -> consumption handoff -> downstream outcome participation.
- influence outcomes: consume influence outcomes under ownership-preserving boundaries for routing/restoration/notification/eligibility/prioritization participation.

## 10. Routing Influence Review

Validation scope:

- routing participation
- routing influence consumption
- routing influence lineage

Result: PASS

Validated statements:

- Coordinator consumes routing influence outcomes.
- Coordinator does not define routing policy.
- routing influence participation and consumption remain bounded to governed routing outcomes with explicit lineage preserved.

## 11. Restoration Influence Review

Validation scope:

- restoration participation
- restoration influence consumption
- restoration influence lineage

Result: PASS

Validated statements:

- Coordinator consumes restoration influence outcomes.
- Coordinator does not define restoration policy.
- restoration influence participation and consumption remain bounded to governed restoration outcomes with explicit lineage preserved.

## 12. Notification Influence Review

Validation scope:

- notification participation
- notification influence consumption
- notification influence lineage

Result: PASS

Notification influence participation and consumption remain bounded to governed notification outcomes with explicit lineage preserved.

## 13. Experience Eligibility Influence Review

Validation scope:

- eligibility participation
- eligibility influence consumption
- eligibility influence lineage

Result: PASS

Validated statements:

- Coordinator consumes eligibility outcomes.
- Coordinator does not define eligibility policy.
- eligibility influence participation and consumption remain bounded to governed eligibility outcomes with explicit lineage preserved.

## 14. Prioritization Influence Review

Validation scope:

- prioritization participation
- prioritization influence consumption
- prioritization influence lineage

Result: PASS

Validated statements:

- Coordinator consumes prioritization outcomes.
- Coordinator does not define prioritization policy.
- prioritization influence participation and consumption remain bounded to governed prioritization outcomes with explicit lineage preserved.

## 15. Influence Precedence Review

Validation scope:

- precedence participation
- influence precedence consumption
- precedence lineage

Result: PASS

Validated statements:

- Coordinator consumes precedence outcomes.
- Coordinator does not define precedence rules.
- precedence participation and influence consumption remain bounded to governed precedence outcomes with explicit lineage preserved.

## 16. Influence Lineage Architecture

Validation scope:

- occupancy participation
- presence participation
- confidence participation
- room participation
- multi-occupant participation
- guest participation
- influence outcomes

Result: PASS

Lineage architecture:

- occupancy-participation lineage remains tied to governed occupancy outcomes.
- presence-participation lineage remains tied to governed presence outcomes.
- confidence-participation lineage remains tied to governed confidence outcomes.
- room-participation lineage remains tied to governed room-aware outcomes.
- multi-occupant-participation lineage remains tied to governed multi-occupant outcomes.
- guest-participation lineage remains tied to governed guest/unknown outcomes.
- influence-outcome lineage remains traceable through bounded influence handoff boundaries.

## 17. Deterministic Influence Behavior Review

Validation scope:

- routing influence
- restoration influence
- notification influence
- eligibility influence
- prioritization influence
- guest participation
- multi-occupant participation

Result: PASS

Deterministic requirements:

- same governed occupancy/presence influence inputs produce the same influence participation outcomes.
- routing/restoration/notification influence participation remains deterministic and bounded.
- eligibility/prioritization influence participation remains deterministic and bounded.
- guest and multi-occupant participation remains deterministic and traceable under governed boundaries.

## 18. Explainability Review

Validation scope:

- machine-readable influence explanations
- human-readable influence explanations
- influence lineage support

Result: PASS

Explainability support requirements:

- machine-readable explanations consume bounded influence references and lineage references.
- human-readable explanations consume bounded influence summaries and lineage references.
- influence lineage support remains sufficient for OP8 explainability participation.

## 19. Diagnostics Readiness Review

Validation scope:

- future OP9 Occupancy and Presence Diagnostics Surface support
- influence traceability sufficiency

Result: PASS

OP7 preserves influence traceability, precedence traceability, and domain-specific influence traces sufficient for OP9 diagnostics participation.

## 20. Ownership Validation

Validation scope:

Coordinator does not own:

- occupancy governance
- presence governance
- confidence rules
- eligibility policy
- prioritization policy
- routing policy
- notification policy
- precedence rules

Result: PASS

Coordinator consumes governed occupancy, presence, confidence, room-aware, multi-occupant, guest, and influence outcomes and owns none of the listed domains.

## 21. Ownership Drift Analysis

Validation scope:

No transfer of:

- occupancy governance
- presence governance
- confidence governance
- eligibility governance
- prioritization governance
- routing governance
- notification governance
- precedence authority

Result: PASS

No ownership drift identified.

## 22. Downstream Guidance

Provide constraints only. Do not pre-design future issues.

- OP8 Occupancy and Presence Explainability Framework: consume OP7 influence lineage, precedence lineage, and domain influence references for machine-readable and human-readable explainability surfaces.
- OP9 Occupancy and Presence Diagnostics Surface: consume OP7 influence traces, precedence traces, and domain influence participation traces for diagnostics categories and troubleshooting workflows.
- OP10 Occupancy and Presence Consumption Readiness Review: validate OP1 through OP9 authority alignment, deterministic influence coverage, lineage/traceability sufficiency, and ownership preservation.

## 23. OP7 Baseline Determination

Result: PASS

The occupancy and presence influence matrix is sufficiently documented for downstream E8a work.

## 24. Final Determination

E8A-OP7 OCCUPANCY AND PRESENCE INFLUENCE MATRIX

APPROVED AS THE AUTHORITATIVE BASELINE

FOR OCCUPANCY AND PRESENCE INFLUENCE CONSUMPTION
