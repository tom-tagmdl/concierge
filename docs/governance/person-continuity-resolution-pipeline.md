# Person Continuity Resolution Pipeline

## 1. Purpose

This document defines the authoritative E7-CA2 person continuity resolution pipeline baseline.

This document is architecture and governance only.

This document does not define continuity governance, continuity scoring, restoration algorithms, freshness algorithms, inference engines, or room-selection algorithms.

## 2. Authority Relationship

Person Continuity Authority remains external through HTBW continuity authorities.

Coordinator Resolution Authority:

- consumes governed continuity context
- participates in continuity-aware resolution behavior
- carries continuity outputs into explainability and diagnostics participation

Coordinator consumes continuity.

Coordinator does not own continuity.

Coordinator does not evaluate continuity truth.

## 3. Dependencies

CA2 consumes:

- HTBW #19 Personalization Governance ADR
- HTBW #31 Person Continuity and Affinity Contract
- HTBW #45 Person Continuity Model
- `docs/governance/continuity-affinity-consumption-architecture.md` (CA1)
- `docs/governance/experience-resolution-consumption-architecture.md` (EX2)
- `docs/governance/room-aware-experience-consumption-architecture.md` (EX3)
- `docs/governance/merged-room-experience-consumption-architecture.md` (EX4)
- `docs/governance/composite-room-experience-consumption-architecture.md` (EX5)
- `docs/governance/guest-aware-experience-consumption-architecture.md` (EX6)
- `docs/governance/experience-explainability-framework.md` (EX7)
- `docs/governance/experience-discovery-foundation.md` (EX8)
- `docs/governance/experience-diagnostics-framework.md` (EX9)
- `docs/governance/experience-consumption-readiness-review.md` (EX10)
- `docs/governance/experience-significance-consumption-architecture.md` (EX11)

CA2 consumes all.

CA2 redefines none.

## 4. Continuity Resolution Model

Continuity resolution means Coordinator consumes governed continuity context and participates in continuity-aware resolution behavior without taking continuity ownership.

Continuity context participates as bounded governed input for runtime participation, experience participation, and downstream explanation and diagnostics surfaces.

Coordinator consumes governed continuity references, continuity state, and continuity context freshness markers as architecture inputs.

This section defines architecture only.

## 5. Last Known Room Participation

Last known room participates as governed continuity context input aligned to HTBW continuity model boundaries.

Room continuity context participates by carrying room-linked continuity references into continuity-aware resolution participation.

This section defines architecture only.

Do not define room-selection algorithms.

## 6. Last Known Activity Participation

Last known activity participates as governed continuity context input for continuity-aware resolution participation.

Activity continuity context participates by carrying activity references and activity state into bounded runtime and experience participation.

This section defines architecture only.

## 7. Last Known Experience Participation

Last known experience participates as governed continuity context input for continuity-aware resolution participation.

Experience continuity context participates by carrying prior experience references into bounded runtime and experience participation.

This section defines architecture only.

## 8. Last Known Media Participation

Last known media participates as governed continuity context input for continuity-aware resolution participation.

Media continuity context participates by carrying media references and media continuity state into bounded runtime and experience participation.

This section defines architecture only.

## 9. Continuity Freshness Participation

Freshness participates by providing governed continuity recency context for continuity-aware resolution participation.

Freshness informs continuity consumption by bounding how continuity context is interpreted for runtime and experience participation under governed policy.

Freshness participates in explainability and diagnostics by contributing explicit freshness rationale and freshness trace references.

This section defines architecture only.

Do not define freshness algorithms.

## 10. Continuity Resolution Pipeline

Continuity Authority
↓
Continuity Context
↓
Coordinator Consumption
↓
Resolution Participation
↓
Runtime Participation
↓
Experience Participation
↓
Explainability
↓
Diagnostics

This pipeline is architecture only.

## 11. Significance Interaction

Grounding: EX11 significance consumption architecture.

Significance influences continuity participation as an externally governed context that may coexist with governed continuity context during runtime and experience participation.

Continuity interacts with significance through bounded participation references while preserving separate ownership and lineage boundaries.

Coordinator consumes significance and continuity independently.

Coordinator does not derive continuity from significance.

Coordinator does not derive significance from continuity.

This section defines architecture only.

## 12. Room-Aware Participation

Grounding: EX3 room-aware experience consumption.

Continuity participates in room-aware behavior by carrying last-known-room and room-linked continuity context as bounded room-aware inputs.

This section defines architecture only.

## 13. Merged-Room Participation

Grounding: EX4 merged-room experience consumption.

Continuity participates in merged-room behavior by carrying merged-room-relevant continuity context as bounded merged-room inputs.

This section defines architecture only.

## 14. Composite-Room Participation

Grounding: EX5 composite-room experience consumption.

Continuity participates in composite-room behavior by carrying hierarchy-aware and scope-aware continuity context as bounded composite-room inputs.

This section defines architecture only.

## 15. Guest-Aware Participation

Grounding: EX6 guest-aware experience consumption.

Continuity participates in guest-aware behavior through governed guest-safe continuity boundaries and visibility constraints.

This section defines architecture only.

## 16. Explainability Hooks

Grounding: EX7 experience explainability.

Continuity explainability hooks include:

- freshness rationale hooks
- last-known-room hooks
- last-known-activity hooks
- last-known-experience hooks
- last-known-media hooks

These hooks carry bounded continuity rationale and lineage references for human-readable and machine-readable explainability surfaces.

This section defines architecture only.

## 17. Discovery Participation

Grounding: EX8 experience discovery.

Continuity participates in discovery by contributing governed continuity context to continuity-aware discoverability boundaries.

This section defines architecture only.

## 18. Diagnostics Hooks

Grounding: EX9 experience diagnostics.

Continuity diagnostics hooks include:

- continuity traces
- freshness traces
- room traces
- activity traces
- experience traces
- media traces

These hooks preserve bounded continuity traceability and troubleshooting participation references.

This section defines architecture only.

## 19. Continuity Lineage Framework

Continuity Authority
↓
Continuity Context
↓
Coordinator Consumption
↓
Resolution Participation
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

Coordinator consumes all of the above.

## 21. Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Person Continuity | HTBW continuity governance and model authorities | Consumer | PASS |
| Person-Room Affinity | HTBW affinity governance and model authorities | Consumer | PASS |
| Significance | HTBW Asset Intelligence significance authority | Consumer | PASS |
| Relevance | HTBW Asset Intelligence relevance authority | Consumer | PASS |
| Environmental Evaluation | HTBW Asset Intelligence environmental evaluation authority | Consumer | PASS |
| Priority Context | HTBW Asset Intelligence priority-context authority | Consumer | PASS |
| Explainability | governed explainability artifacts | Consumer | PASS |
| Diagnostics | governed diagnostics artifacts | Consumer | PASS |

## 22. Risk Review

- continuity ownership drift
- continuity freshness drift
- significance ownership drift
- explainability divergence
- diagnostics divergence

## 23. Ownership Preservation Review

Result: PASS

Validated:

- continuity ownership preserved
- affinity ownership preserved
- significance ownership preserved
- Asset Intelligence ownership preserved

No ownership drift introduced in this E7 CA2 architecture baseline.

## 24. Readiness Statement

Person Continuity Resolution Pipeline is READY.

This document becomes the authoritative continuity-resolution baseline for E7.
