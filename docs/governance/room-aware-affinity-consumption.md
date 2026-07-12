# Room-Aware Affinity Consumption

## 1. Purpose

This document defines the authoritative E7-CA5 room-aware affinity consumption architecture baseline.

This document is architecture and governance only.

This document does not define affinity application engines, room-selection algorithms, affinity scoring, affinity ranking, preference engines, room-specific decision engines, or person inference engines.

## 2. Authority Relationship

Person-Room Affinity Authority remains external through HTBW affinity authorities.

Room Truth Authority remains external through HTBW room and vocabulary truth authorities.

Coordinator Consumption Authority:

- consumes affinity
- consumes room truth
- consumes continuity
- consumes significance context

Coordinator consumes affinity.

Coordinator consumes room truth.

Coordinator does not own affinity.

Coordinator does not own room truth.

Coordinator does not define affinity.

Coordinator does not redefine affinity governance, contracts, or models.

## 3. Dependencies

CA5 consumes:

- HTBW #19 Personalization Governance ADR
- HTBW #31 Person Continuity and Affinity Contract
- HTBW #46 Person-Room Affinity Model
- ADR-004 Coordinator V2 Governance Boundaries
- ADR-005 Room Vocabulary Governance Boundaries
- ADR-006 Capability Projection Governance Boundaries
- docs/governance/coordinator-v2-foundation-summary.md
- docs/governance/continuity-affinity-consumption-architecture.md (CA1)
- docs/governance/person-continuity-resolution-pipeline.md (CA2)
- docs/governance/person-room-affinity-resolution-pipeline.md (CA3)
- docs/governance/room-aware-continuity-consumption.md (CA4)
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

CA5 consumes all.

CA5 redefines none.

## 4. Room-Aware Affinity Model

Room-aware affinity means Coordinator consumes governed affinity context together with governed room context so affinity participation remains room-sensitive without transferring affinity or room authority.

Affinity context participates as bounded context that carries room preference state, preference references, and override references into household-facing runtime participation.

Room context participates as bounded room truth input that anchors affinity participation to governed room-scoped boundaries.

This section defines architecture only.

## 5. Room Affinity Participation

Room affinity participates as governed affinity context consumed during room-aware affinity participation.

Room-affinity context participates by linking room preference references to room-scoped runtime participation and explainable household-facing outcomes.

This section defines architecture only.

## 6. Room-Specific Preference Participation

Room-specific preferences participate as governed affinity context that captures room-scoped preference participation boundaries.

Preference context participates by carrying room-specific preference references into bounded runtime participation and household-facing outcomes.

This section defines architecture only.

## 7. Room-Specific Override Participation

Room-specific overrides participate as governed affinity context that constrains or specializes room-aware preference participation for specific room contexts.

Override context participates by carrying governed override references into bounded room-aware affinity participation.

This section defines architecture only.

Do not define override algorithms.

## 8. Affinity Eligibility Participation

Affinity eligibility participates as governed eligibility context that bounds when room-aware affinity may contribute to household-facing runtime participation.

Eligibility participates in household-facing outcomes by constraining affinity participation to governed, explainable, deterministic eligibility states.

This section defines architecture only.

Do not define eligibility algorithms.

## 9. Room-Aware Affinity Pipeline

Affinity Authority
↓
Affinity Context
↓
Room Affinity
↓
Room-Specific Preferences
↓
Room-Specific Overrides
↓
Affinity Eligibility
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

Significance interacts with room-aware affinity as an independently consumed governed context that may coexist with affinity during runtime participation and household-facing outcomes.

Coordinator consumes significance and affinity independently.

Coordinator does not derive affinity from significance.

Coordinator does not derive significance from affinity.

This section defines architecture only.

## 11. Continuity Interaction

Grounding: CA2 person continuity resolution pipeline and CA4 room-aware continuity consumption.

Room-aware affinity interacts with continuity as an independently consumed governed context during room-aware runtime participation.

Coordinator consumes continuity and affinity independently.

Coordinator does not derive affinity from continuity.

Coordinator does not derive continuity from affinity.

This section defines architecture only.

## 12. Merged-Room Participation

Grounding: EX4 merged-room experience consumption architecture.

Room-aware affinity participates in merged-room behavior by carrying governed room-affinity, room-specific preference, and room-specific override context into merged-room household-facing participation boundaries.

This section defines architecture only.

## 13. Composite-Room Participation

Grounding: EX5 composite-room experience consumption architecture.

Room-aware affinity participates in composite-room behavior by carrying hierarchy-aware and scope-aware room-affinity, room-specific preference, and override context into composite-room household-facing participation boundaries.

This section defines architecture only.

## 14. Guest-Aware Participation

Grounding: EX6 guest-aware experience consumption architecture.

Room-aware affinity participates in guest-aware behavior through governed guest-safe eligibility and visibility boundaries that constrain room-aware affinity participation.

This section defines architecture only.

## 15. Deterministic Behavior

Room-aware affinity produces deterministic household-facing outcomes by consuming governed room affinity, room-specific preferences, room-specific overrides, and affinity eligibility through fixed bounded participation surfaces.

Room affinity, room-specific preferences, room-specific overrides, and affinity eligibility participate deterministically because the same governed inputs and eligibility boundaries produce the same room-aware affinity participation outcomes.

This section defines architecture only.

## 16. Explainability Hooks

Grounding: EX7 experience explainability framework.

Room-aware affinity explainability hooks include:

- room affinity hooks
- room-specific preference hooks
- room-specific override hooks
- affinity eligibility hooks
- affinity precedence hooks

These hooks preserve bounded room-aware affinity rationale and lineage references for human-readable and machine-readable explainability surfaces.

This section defines architecture only.

## 17. Discovery Participation

Grounding: EX8 experience discovery foundation.

Room-aware affinity participates in discovery by contributing governed affinity context, room context, and eligibility boundaries to room-aware discoverability participation.

This section defines architecture only.

## 18. Diagnostics Hooks

Grounding: EX9 experience diagnostics framework.

Room-aware affinity diagnostics hooks include:

- affinity traces
- room-affinity traces
- room-preference traces
- room-override traces
- eligibility traces
- precedence traces

These hooks preserve bounded room-aware affinity traceability and troubleshooting participation references.

This section defines architecture only.

## 19. Room-Aware Affinity Lineage Framework

Affinity Authority
↓
Affinity Context
↓
Room Affinity
↓
Room-Specific Preferences
↓
Room-Specific Overrides
↓
Affinity Eligibility
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

- affinity
- continuity
- significance
- relevance
- environmental evaluation
- priority context
- room truth

Coordinator consumes all of the above.

## 21. Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Person-Room Affinity | HTBW affinity governance and model authorities | Consumer | PASS |
| Person Continuity | HTBW continuity governance and model authorities | Consumer | PASS |
| Room Truth | HTBW room and vocabulary truth authorities | Consumer | PASS |
| Significance | HTBW Asset Intelligence significance authority | Consumer | PASS |
| Relevance | HTBW Asset Intelligence relevance authority | Consumer | PASS |
| Environmental Evaluation | HTBW Asset Intelligence environmental evaluation authority | Consumer | PASS |
| Priority Context | HTBW Asset Intelligence priority-context authority | Consumer | PASS |
| Explainability | governed explainability artifacts | Consumer | PASS |
| Diagnostics | governed diagnostics artifacts | Consumer | PASS |

## 22. Risk Review

- affinity ownership drift
- room truth ownership drift
- affinity eligibility drift
- significance ownership drift
- explainability divergence
- diagnostics divergence

## 23. Ownership Preservation Review

Result: PASS

Validated:

- affinity ownership preserved
- continuity ownership preserved
- room truth ownership preserved
- significance ownership preserved
- Asset Intelligence ownership preserved

No ownership drift introduced in this E7 CA5 architecture baseline.

## 24. Readiness Statement

Room-Aware Affinity Consumption is READY.

This document becomes the authoritative room-aware affinity baseline for E7.
