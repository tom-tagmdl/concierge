# What Happened While I Was Away Planning

## 1. Purpose

Define the authoritative E10-HM6 architecture baseline for away-history household query planning.

This document defines away-history query consumption architecture only.

This document is architecture and governance only.

This document does not implement summarization engines, event reconstruction, narrative generation, history retrieval, occupancy calculations, room-history resolution, memory retrieval, provenance generation, or HM7 implementation work.

## 2. Scope Reviewed

Reviewed mandatory authorities and dependencies:

- HTBW #47
- Concierge #138
- HM2 Event History and Provenance Relationship
- HM4 Room-Linked Memory Boundaries
- HM5 Who Did This Query Planning
- E9 Provenance Consumption
- E9 Diagnostics and Explainability

Reviewed associated governance authorities:

- Event Model
- Provenance Contract
- Occupancy and Presence Contract
- ADR: Occupancy and Presence Governance

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#47, #138, #146) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between HM6 outputs and authoritative ADR/contract/model artifacts.

## 3. Event History Authority Validation

Validation scope:

- event-history ownership
- event-history governance
- historical truth authority
- event-history lifecycle authority

Result: PASS

Validated statements:

- Event-history ownership remains in HTBW-governed event authorities.
- Event-history governance remains in HTBW-governed event authorities.
- Historical truth authority remains in HTBW-governed event-history/provenance authorities.
- Event-history lifecycle authority remains external to Coordinator.
- Coordinator consumes event-history outcomes.
- Coordinator does not redefine event-history semantics.

## 4. Provenance Authority Validation

Validation scope:

- provenance ownership
- provenance governance
- provenance authority
- provenance lifecycle authority

Result: PASS

Validated statements:

- Provenance ownership remains in HTBW.
- Provenance governance remains in HTBW.
- Provenance authority remains in HTBW provenance authorities.
- Provenance lifecycle authority remains external to Coordinator.
- Coordinator consumes provenance outcomes.
- Coordinator does not redefine provenance semantics.

## 5. Occupancy and Presence Validation

Validation scope:

- occupancy ownership
- occupancy governance
- presence ownership
- presence governance

Result: PASS

Validated statements:

- Occupancy ownership remains in HTBW/Foundation authorities.
- Occupancy governance remains in HTBW authorities.
- Presence ownership remains in HTBW/Foundation authorities.
- Presence governance remains in HTBW authorities.
- Coordinator consumes occupancy and presence outcomes.
- Coordinator does not redefine occupancy or presence truth.

## 6. HM2 Alignment Review

Validation scope:

- event-history ownership
- provenance ownership
- historical truth alignment

Result: PASS

HM6 conforms to HM2 event-history/provenance ownership boundaries and historical truth alignment.

## 7. HM4 Alignment Review

Validation scope:

- room participation
- room-history participation
- room lineage

Result: PASS

HM6 aligns with HM4 room participation, room-history participation, and room-lineage boundaries.

## 8. HM5 Alignment Review

Validation scope:

- query planning alignment
- attribution alignment
- explanation alignment

Result: PASS

HM6 remains aligned with HM5 query-planning consumption patterns, attribution participation boundaries, and explanation-lineage architecture.

## 9. Historical Truth Governance Review

Validation scope:

- historical truth remains external
- historical truth remains authoritative
- Concierge remains consumption-only

Result: PASS

Validated statements:

- Historical truth remains external to Concierge and Coordinator.
- Historical truth remains authoritative in HTBW-governed event-history/provenance authorities.
- Concierge and Coordinator remain consumption-only for historical truth.

## 10. Away-History Query Architecture

Validation scope:

- query participation
- query consumption
- history participation
- query outcomes

Result: PASS

Architecture-only away-history query planning:

- query participation: consume governed event-history/provenance/memory/occupancy/presence/room/identity context as bounded query inputs.
- query consumption: consume away-history planning outcomes for household-facing query orchestration.
- history participation: consume authoritative event-history outcomes with explicit lineage anchors.
- query outcomes: preserve bounded query outcomes for explainability and diagnostics readiness.

## 11. Away-State Retrieval Review

Validation scope:

- away-state participation
- away-state consumption
- away-state lineage

Result: PASS

Away-state retrieval is consumption-only:

- Coordinator consumes away-state outcomes.
- Coordinator does not define away-state truth.
- Away-state lineage remains tied to governed occupancy/presence/event-history authorities.

## 12. Event-History Summarization Review

Validation scope:

- event-history participation
- summarization participation
- event-history lineage

Result: PASS

Event-history summarization participation is consumption-only:

- Coordinator consumes event-history outcomes.
- Coordinator does not define event-history semantics.
- Event-history lineage remains tied to authoritative event-history/provenance authorities.

## 13. Room Context Review

Validation scope:

- room participation
- room-history participation
- room lineage

Result: PASS

Room and room-history participation remain bounded to governed room outcomes with explicit room lineage preserved.

## 14. Occupancy and Presence Review

Validation scope:

- occupancy participation
- presence participation
- occupancy lineage

Result: PASS

Occupancy and presence participation remain bounded to governed occupancy/presence outcomes with explicit lineage preserved.

## 15. Identity Participation Review

Validation scope:

- identity participation
- identity consumption
- identity lineage

Result: PASS

Identity participation remains bounded to governed identity outcomes with explicit identity lineage preserved.

## 16. Provenance-Backed Summary Review

Validation scope:

- provenance participation
- event-history participation
- summary lineage

Result: PASS

Provenance-backed summary participation remains bounded to governed provenance and event-history outputs with explicit summary lineage preserved.

## 17. Privacy Boundary Review

Validation scope:

- privacy participation
- visibility participation
- privacy lineage

Result: PASS

Privacy and visibility participation remain bounded to governed privacy boundaries with explicit privacy lineage preserved.

## 18. Household-Facing Summary Review

Validation scope:

- summary participation
- summary explanations
- provenance explanations

Result: PASS

Household-facing summaries consume governed historical context and explanation references with no alternate authority created.

## 19. Historical Traceability Review

Validation scope:

- event-history traceability
- provenance traceability
- room-history traceability

Result: PASS

Traceability is preserved across event-history, provenance, and room-history participation with explicit lineage anchors.

## 20. Query Lineage Architecture

Validation scope:

- event-history inputs
- provenance inputs
- memory inputs
- occupancy inputs
- presence inputs
- room inputs
- identity inputs

Result: PASS

Lineage architecture:

- event-history-input lineage remains tied to authoritative event-history outputs.
- provenance-input lineage remains tied to HTBW-governed provenance outputs.
- memory-input lineage remains tied to HTBW-governed household-memory outputs.
- occupancy-input lineage remains tied to HTBW/Foundation-governed occupancy outputs.
- presence-input lineage remains tied to HTBW/Foundation-governed presence outputs.
- room-input lineage remains tied to HTBW/Foundation-governed room outputs.
- identity-input lineage remains tied to HTBW/Voice Identity-governed identity outputs.

## 21. Deterministic Summarization Review

Validation scope:

- event-history participation
- summary participation
- provenance participation
- explanation participation

Result: PASS

Deterministic requirements:

- same governed event-history/provenance/memory/occupancy/presence/room/identity inputs produce the same away-history query-planning participation outcomes.
- event-history, summary, provenance, and explanation participation remain deterministic and traceable.

## 22. Explainability Readiness Review

Validation scope:

- future HM7 Why Did This Happen? support

Result: PASS

Lineage sufficiency is preserved for HM7 planning through explicit event-history/provenance/room/identity/occupancy explanation anchors.

## 23. Diagnostics Readiness Review

Validation scope:

- future HM9 Household Memory Diagnostics Surface support

Result: PASS

Traceability sufficiency is preserved for HM9 planning with explicit event-history/provenance/room-history lineage anchors.

## 24. Ownership Validation

Validation scope:

Coordinator does not own:

- event-history governance
- provenance governance
- occupancy governance
- presence governance
- memory governance
- room governance

Result: PASS

Coordinator consumes governed outcomes and owns none of the listed governance domains.

## 25. Ownership Drift Analysis

Validation scope:

No transfer of:

- event-history ownership
- provenance ownership
- occupancy ownership
- presence ownership
- memory ownership
- room ownership

Result: PASS

No ownership drift identified.

## 26. Downstream Guidance

Provide constraints only. Do not pre-design future issues.

- HM7 Why Did This Happen? Explanation Planning: consume governed event-history/provenance/memory/occupancy/presence/room/identity lineage and preserve deterministic explanation participation.
- HM8 Privacy, Retention, and Guest-Safe Memory Boundaries: preserve HTBW privacy/retention/guest-safe governance across away-history query and summary surfaces.
- HM9 Household Memory Diagnostics Surface: preserve deterministic event-history/provenance/room-history traceability anchors; diagnostics governance remains external.
- HM10 Household Memory Readiness Review: validate HM1-HM9 completeness, ownership preservation, determinism, and supportability readiness.

## 27. HM6 Baseline Determination

Result: PASS

Away-history query planning is sufficiently documented for downstream E10 work.

## 28. Readiness Constraint Validation

Validation scope:

- Concierge summarizes governed history
- Concierge consumes memory context
- Concierge does not create historical truth
- Event History remains authoritative
- Provenance remains authoritative

Result: PASS

Readiness constraints are satisfied without governance transfer.

## 29. Final Determination

E10-HM6 WHAT HAPPENED WHILE I WAS AWAY PLANNING

APPROVED AS THE AUTHORITATIVE BASELINE

FOR AWAY-HISTORY HOUSEHOLD QUERY CONSUMPTION
