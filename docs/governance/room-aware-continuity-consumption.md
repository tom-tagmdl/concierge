# Room-Aware Continuity Consumption

## 1. Purpose

This document defines the authoritative E7-CA4 room-aware continuity consumption architecture baseline.

This document is architecture and governance only.

This document does not define room-transition algorithms, room-selection algorithms, continuity scoring, continuity restoration engines, continuity routing, room-ranking engines, or person inference engines.

## 2. Authority Relationship

Person Continuity Authority remains external through HTBW continuity authorities.

Room Truth Authority remains external through HTBW room and vocabulary truth authorities.

Coordinator Consumption Authority:

- consumes continuity
- consumes room truth
- consumes affinity
- consumes significance context

Coordinator consumes continuity.

Coordinator consumes room truth.

Coordinator does not own continuity.

Coordinator does not own room truth.

Coordinator does not define continuity.

Coordinator does not redefine continuity governance, contracts, or models.

## 3. Dependencies

CA4 consumes:

- HTBW #19 Personalization Governance ADR
- HTBW #31 Person Continuity and Affinity Contract
- HTBW #45 Person Continuity Model
- ADR-004 Coordinator V2 Governance Boundaries
- ADR-005 Room Vocabulary Governance Boundaries
- ADR-006 Capability Projection Governance Boundaries
- docs/governance/coordinator-v2-foundation-summary.md
- docs/governance/continuity-affinity-consumption-architecture.md (CA1)
- docs/governance/person-continuity-resolution-pipeline.md (CA2)
- docs/governance/person-room-affinity-resolution-pipeline.md (CA3)
- docs/governance/room-aware-experience-consumption-architecture.md (EX3)
- docs/governance/merged-room-experience-consumption-architecture.md (EX4)
- docs/governance/composite-room-experience-consumption-architecture.md (EX5)
- docs/governance/guest-aware-experience-consumption-architecture.md (EX6)
- docs/governance/experience-explainability-framework.md (EX7)
- docs/governance/experience-discovery-foundation.md (EX8)
- docs/governance/experience-diagnostics-framework.md (EX9)
- docs/governance/experience-consumption-readiness-review.md (EX10)
- EX10 addendum in issue #100
- docs/governance/experience-significance-consumption-architecture.md (EX11)

CA4 consumes all.

CA4 redefines none.

## 4. Room-Aware Continuity Model

Room-aware continuity means Coordinator consumes governed continuity context together with governed room context so continuity participation remains room-sensitive without transferring continuity or room authority.

Continuity context participates as bounded context that carries recency, last-known state, and continuity references into household-facing runtime participation.

Room context participates as bounded room truth input that anchors continuity participation to current and prior room context boundaries.

This section defines architecture only.

## 5. Current Room Participation

Current room participates as governed room truth context used during room-aware continuity consumption.

Current-room continuity context participates by linking active room context to consumed continuity state so runtime participation remains bounded and explainable.

This section defines architecture only.

## 6. Previous Room Participation

Previous room participates as governed room truth context that preserves prior-room continuity references.

Previous-room continuity context participates by carrying bounded prior-room continuity references into room-aware continuity participation.

This section defines architecture only.

## 7. Room Transition Context Participation

Room-transition context participates as governed transition context between previous and current room references.

Transition context influences continuity participation by bounding how continuity context is consumed across room changes for deterministic household-facing outcomes.

This section defines architecture only.

Do not define transition algorithms.

## 8. Continuity Eligibility Participation

Continuity eligibility participates as governed eligibility context that bounds when room-aware continuity may contribute to household-facing runtime participation.

Eligibility participates in household-facing outcomes by constraining continuity participation to governed, explainable, deterministic eligibility states.

This section defines architecture only.

Do not define eligibility algorithms.

## 9. Room-Aware Continuity Pipeline

Continuity Authority
↓
Continuity Context
↓
Current Room
↓
Previous Room
↓
Room Transition Context
↓
Continuity Eligibility
↓
Coordinator Consumption
↓
Runtime Participation
↓
Explainability
↓
Diagnostics

This pipeline is architecture only.

## 10. Significance Interaction

Grounding: EX11 experience significance consumption architecture.

Significance interacts with room-aware continuity as an independently consumed governed context that may coexist with continuity during runtime participation and household-facing outcomes.

Coordinator consumes significance and continuity independently.

Coordinator does not derive continuity from significance.

Coordinator does not derive significance from continuity.

This section defines architecture only.

## 11. Affinity Interaction

Grounding: CA3 person-room affinity resolution pipeline.

Room affinity interacts with room-aware continuity as an independently consumed governed context during room-aware runtime participation.

Coordinator consumes continuity and affinity independently.

Coordinator does not derive continuity from affinity.

Coordinator does not derive affinity from continuity.

This section defines architecture only.

## 12. Merged-Room Participation

Grounding: EX4 merged-room experience consumption architecture.

Room-aware continuity participates in merged-room behavior by carrying governed current-room, previous-room, and transition-context continuity references into merged-room household-facing participation boundaries.

This section defines architecture only.

## 13. Composite-Room Participation

Grounding: EX5 composite-room experience consumption architecture.

Room-aware continuity participates in composite-room behavior by carrying hierarchy-aware and scope-aware room continuity context into composite-room household-facing participation boundaries.

This section defines architecture only.

## 14. Guest-Aware Participation

Grounding: EX6 guest-aware experience consumption architecture.

Room-aware continuity participates in guest-aware behavior through governed guest-safe eligibility and visibility boundaries that constrain room-aware continuity participation.

This section defines architecture only.

## 15. Deterministic Behavior

Room-aware continuity produces deterministic household-facing outcomes by consuming governed continuity context, current room, previous room, transition context, and eligibility context through fixed bounded participation surfaces.

Current room, previous room, and transition context participate deterministically because the same governed inputs and eligibility boundaries produce the same room-aware continuity participation outcomes.

This section defines architecture only.

## 16. Explainability Hooks

Grounding: EX7 experience explainability framework.

Room-aware continuity explainability hooks include:

- current room hooks
- previous room hooks
- room transition hooks
- continuity eligibility hooks
- continuity freshness hooks

These hooks preserve bounded room-aware continuity rationale and lineage references for human-readable and machine-readable explainability surfaces.

This section defines architecture only.

## 17. Discovery Participation

Grounding: EX8 experience discovery foundation.

Room-aware continuity participates in discovery by contributing governed continuity context, room context, and eligibility boundaries to room-aware discoverability participation.

This section defines architecture only.

## 18. Diagnostics Hooks

Grounding: EX9 experience diagnostics framework.

Room-aware continuity diagnostics hooks include:

- continuity traces
- current-room traces
- previous-room traces
- room-transition traces
- eligibility traces
- freshness traces

These hooks preserve bounded room-aware continuity traceability and troubleshooting participation references.

This section defines architecture only.

## 19. Room-Aware Continuity Lineage Framework

Continuity Authority
↓
Continuity Context
↓
Current Room
↓
Previous Room
↓
Room Transition Context
↓
Continuity Eligibility
↓
Coordinator Consumption
↓
Runtime Outcome
↓
Explainability
↓
Diagnostics

This framework is architecture only.

## 20. Ownership Protection

Coordinator does not own:

- continuity
- affinity
- significance
- relevance
- environmental evaluation
- priority context
- room truth

Coordinator consumes all of the above.

## 21. Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Person Continuity | HTBW continuity governance and model authorities | Consumer | PASS |
| Person-Room Affinity | HTBW affinity governance and model authorities | Consumer | PASS |
| Room Truth | HTBW room and vocabulary truth authorities | Consumer | PASS |
| Significance | HTBW Asset Intelligence significance authority | Consumer | PASS |
| Relevance | HTBW Asset Intelligence relevance authority | Consumer | PASS |
| Environmental Evaluation | HTBW Asset Intelligence environmental evaluation authority | Consumer | PASS |
| Priority Context | HTBW Asset Intelligence priority-context authority | Consumer | PASS |
| Explainability | governed explainability artifacts | Consumer | PASS |
| Diagnostics | governed diagnostics artifacts | Consumer | PASS |

## 22. Risk Review

- continuity ownership drift
- room truth ownership drift
- continuity eligibility drift
- significance ownership drift
- explainability divergence
- diagnostics divergence

## 23. Ownership Preservation Review

Result: PASS

Validated:

- continuity ownership preserved
- affinity ownership preserved
- room truth ownership preserved
- significance ownership preserved
- Asset Intelligence ownership preserved

No ownership drift introduced in this E7 CA4 architecture baseline.

## 24. Readiness Statement

Room-Aware Continuity Consumption is READY.

This document becomes the authoritative room-aware continuity baseline for E7.
