# Occupancy and Presence Diagnostics Surface

## 1. Purpose

Define the authoritative E8A-OP9 architecture baseline for occupancy and presence diagnostics consumption.

This document is architecture and governance only.

This document does not implement diagnostics collection, trace collection, troubleshooting automation, occupancy resolution, presence resolution, confidence calculations, or explainability generation.

Diagnostics surfaces consumed traces and consumed lineage.

Diagnostics does not become a source of truth.

## 2. Scope Reviewed

Reviewed authorities and governance inputs:

- HTBW #40
- HTBW #50
- Concierge #119
- OP4 Room-Aware Occupancy Consumption
- OP5 Multi-Occupant Context Consumption
- OP6 Guest and Unknown Presence Behavior
- OP7 Occupancy and Presence Influence Matrix
- OP8 Occupancy and Presence Explainability Framework
- ER9 Restoration Diagnostics Surface
- CA9 Continuity and Affinity Diagnostics Surface

Reviewed diagnostics governance artifacts:

- ADR-012 Occupancy and Presence Governance Boundaries
- Occupancy and Presence Contract
- Occupancy and Presence Model
- Experience Diagnostics Framework
- Capability Diagnostics Surface
- Vocabulary Diagnostics Framework

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#40, #50, #119, #124, #125, #126, #127, #128, #129) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between OP9 outputs and authoritative ADR/contract/model/governance artifacts.

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
- Coordinator surfaces diagnostics for consumed occupancy outcomes.
- Coordinator surfaces consumed occupancy traces and consumed occupancy lineage.
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
- Coordinator surfaces diagnostics for consumed presence outcomes.
- Coordinator surfaces consumed presence traces and consumed presence lineage.
- Coordinator does not create presence truth.
- Coordinator does not create presence governance.

## 5. Diagnostics Governance Validation

Validation scope:

- diagnostics ownership
- diagnostics authority
- diagnostics boundaries

Result: PASS

Validated statements:

- Diagnostics ownership remains externally governed through HTBW-aligned diagnostics authorities.
- Diagnostics authority remains external; Coordinator role is bounded to surfacing consumed diagnostics traces, consumed lineage, and troubleshooting navigation references.
- Diagnostics boundaries prevent Coordinator from creating diagnostics truth, troubleshooting policy, or alternate governance truth.

## 6. OP4 Trace Validation

Validation scope:

- room occupancy traces
- room transition traces
- room confidence traces

Result: PASS

OP9 consumes OP4 room occupancy, room transition, and room confidence traceability references and preserves room diagnostics lineage.

## 7. OP5 Trace Validation

Validation scope:

- multi-occupant traces
- conflict traces
- confidence traces

Result: PASS

OP9 consumes OP5 multi-occupant, conflict, and confidence trace references and preserves diagnostics traceability.

## 8. OP6 Trace Validation

Validation scope:

- guest traces
- unknown traces
- fallback traces
- privacy-safe traces

Result: PASS

OP9 consumes OP6 guest, unknown, fallback, and privacy-safe trace references and preserves diagnostics traceability.

## 9. OP7 Influence Trace Validation

Validation scope:

- routing traces
- restoration traces
- eligibility traces
- prioritization traces
- precedence traces

Result: PASS

OP9 consumes OP7 routing/restoration/eligibility/prioritization/precedence trace references and preserves influence diagnostics traceability.

## 10. OP8 Explainability Alignment Review

Validation scope:

- machine-readable explainability references
- human-readable explainability references
- diagnostics linkage

Result: PASS

OP9 consumes OP8 machine-readable and human-readable explainability references and diagnostics linkage references.

OP9 does not redefine explainability architecture.

## 11. Occupancy Diagnostics Category Review

Validation scope:

- occupancy traces
- occupancy state traces
- occupancy confidence traces
- occupancy troubleshooting workflow

Result: PASS

Architecture-only occupancy diagnostics categories:

- occupancy traces: bounded references to consumed occupancy participation and outcomes.
- occupancy state traces: bounded references to occupied/unoccupied/transitional state participation.
- occupancy confidence traces: bounded references to consumed confidence participation.
- occupancy troubleshooting workflow: trace review -> evidence review -> lineage review -> outcome understanding.

## 12. Presence Diagnostics Category Review

Validation scope:

- presence traces
- presence confidence traces
- presence troubleshooting workflow

Result: PASS

Architecture-only presence diagnostics categories:

- presence traces: bounded references to known/unknown presence participation and outcomes.
- presence confidence traces: bounded references to consumed confidence participation.
- presence troubleshooting workflow: trace review -> confidence review -> lineage review -> outcome understanding.

## 13. Room-Aware Diagnostics Review

Validation scope:

- current-room traces
- previous-room traces
- room-transition traces
- room-vacancy traces

Result: PASS

Room-aware diagnostics preserve bounded references to current-room, previous-room, transition, and vacancy traces with explicit room lineage.

## 14. Multi-Occupant Diagnostics Review

Validation scope:

- resident traces
- guest traces
- conflict traces
- occupant participation traces

Result: PASS

Multi-occupant diagnostics preserve bounded references to resident/guest/conflict and occupant-participation traces with explicit multi-occupant lineage.

## 15. Guest and Unknown Diagnostics Review

Validation scope:

- guest traces
- unknown traces
- fallback traces
- privacy-safe traces

Result: PASS

Guest and unknown diagnostics preserve bounded references to guest/unknown/fallback/privacy-safe traces with explicit lineage.

## 16. Influence Diagnostics Review

Validation scope:

- routing traces
- restoration traces
- notification traces
- eligibility traces
- prioritization traces

Result: PASS

Influence diagnostics preserve bounded references to routing/restoration/notification/eligibility/prioritization traces with explicit influence lineage and precedence-linked traceability.

## 17. Confidence Diagnostics Review

Validation scope:

- confidence traces
- threshold traces
- confidence troubleshooting workflow

Result: PASS

Confidence diagnostics categories:

- confidence traces: bounded references to consumed confidence outcomes and participation.
- threshold traces: bounded references to consumed threshold participation and threshold outcomes.
- confidence troubleshooting workflow: threshold evidence review -> confidence lineage review -> participation-path review -> outcome understanding.

## 18. Troubleshooting Workflow Review

Validation scope:

- occupied state
- unoccupied state
- room transitions
- known presence
- unknown presence
- guest presence
- conflict scenarios
- confidence failures

Result: PASS

Deterministic troubleshooting workflow:

1. identify diagnostic category and outcome surface
2. review occupancy/presence/room-aware traces
3. review multi-occupant, guest/unknown, and conflict traces as applicable
4. review confidence and threshold traces
5. review influence and explainability linkage references
6. produce bounded troubleshooting understanding without changing governance truth

## 19. HACS / Platinum Supportability Review

Validation scope:

- HACS requirements
- Home Assistant supportability
- Platinum-quality supportability
- operational troubleshooting

Result: PASS

Supportability statements:

- Diagnostics categories and deterministic troubleshooting workflow provide supportability guidance aligned with HACS expectations.
- Bounded diagnostics traces and lineage references support Home Assistant operational troubleshooting and maintainability.
- Deterministic, ownership-safe diagnostics coverage aligns with Platinum-quality supportability expectations.

Architecture only.

## 20. Diagnostics Lineage Architecture

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

## 21. Ownership Validation

Validation scope:

Coordinator does not own:

- occupancy governance
- presence governance
- confidence governance
- guest governance
- influence governance
- diagnostics governance

Result: PASS

Coordinator surfaces diagnostics for consumed outcomes, consumed traces, and consumed lineage and owns none of the listed domains.

## 22. Ownership Drift Analysis

Validation scope:

No transfer of:

- occupancy governance
- presence governance
- confidence governance
- guest governance
- influence governance
- diagnostics governance

Result: PASS

No ownership drift identified.

## 23. Downstream Guidance

Provide constraints only. Do not pre-design OP10.

- OP10 Occupancy and Presence Consumption Readiness Review: validate OP1 through OP9 authority alignment, diagnostics coverage completeness, troubleshooting workflow determinism, HACS/Platinum supportability coverage, lineage/traceability sufficiency, and ownership preservation.

## 24. OP9 Baseline Determination

Result: PASS

Occupancy and presence diagnostics are sufficiently documented for downstream E8a work.

## 25. Final Determination

E8A-OP9 OCCUPANCY AND PRESENCE DIAGNOSTICS SURFACE

APPROVED AS THE AUTHORITATIVE BASELINE

FOR OCCUPANCY AND PRESENCE DIAGNOSTICS
