# Person-Room Affinity Resolution Pipeline

## 1. Purpose

This document defines the authoritative E7-CA3 person-room affinity resolution pipeline baseline.

This document is architecture and governance only.

This document does not define affinity governance, affinity scoring, affinity ranking algorithms, room-selection algorithms, preference engines, inference engines, or environment scoring.

## 2. Authority Relationship

Person-Room Affinity Authority remains external through HTBW affinity authorities.

Coordinator Resolution Authority:

- consumes governed affinity context
- participates in affinity-aware resolution behavior
- carries affinity outputs into explainability and diagnostics participation

Coordinator consumes affinity.

Coordinator does not own affinity.

Coordinator does not evaluate affinity truth.

## 3. Dependencies

CA3 consumes:

- HTBW #19 Personalization Governance ADR
- HTBW #31 Person Continuity and Affinity Contract
- HTBW #46 Person-Room Affinity Model
- `docs/governance/continuity-affinity-consumption-architecture.md` (CA1)
- `docs/governance/person-continuity-resolution-pipeline.md` (CA2)
- `docs/governance/room-aware-experience-consumption-architecture.md` (EX3)
- `docs/governance/merged-room-experience-consumption-architecture.md` (EX4)
- `docs/governance/composite-room-experience-consumption-architecture.md` (EX5)
- `docs/governance/guest-aware-experience-consumption-architecture.md` (EX6)
- `docs/governance/experience-explainability-framework.md` (EX7)
- `docs/governance/experience-discovery-foundation.md` (EX8)
- `docs/governance/experience-diagnostics-framework.md` (EX9)
- `docs/governance/experience-consumption-readiness-review.md` (EX10)
- `docs/governance/experience-significance-consumption-architecture.md` (EX11)

CA3 consumes all.

CA3 redefines none.

## 4. Affinity Resolution Model

Affinity resolution means Coordinator consumes governed affinity context and participates in affinity-aware resolution behavior without taking affinity ownership.

Affinity context participates as bounded governed input for runtime participation, experience participation, and downstream explanation and diagnostics surfaces.

Coordinator consumes governed affinity references, affinity state, and affinity preference references as architecture inputs.

This section defines architecture only.

## 5. Room Affinity Participation

Room affinity participates as governed affinity context input aligned to HTBW affinity model boundaries.

Room-affinity context participates by carrying room preference references into affinity-aware resolution participation.

This section defines architecture only.

Do not define room-selection algorithms.

## 6. Notification Affinity Participation

Notification affinity participates as governed affinity context input for affinity-aware resolution participation.

Notification-preference context participates by carrying notification preference references and notification affinity state into bounded runtime and experience participation.

This section defines architecture only.

## 7. Media Affinity Participation

Media affinity participates as governed affinity context input for affinity-aware resolution participation.

Media-preference context participates by carrying media preference references and media affinity state into bounded runtime and experience participation.

This section defines architecture only.

## 8. Environment Affinity Participation

Environment affinity participates as governed affinity context input for affinity-aware resolution participation.

Environmental-preference context participates by carrying environment preference references and environment affinity state into bounded runtime and experience participation.

This section defines architecture only.

## 9. Affinity Precedence Participation

Precedence ordering participates as governed context ordering that structures how consumed affinity context participates in downstream runtime and experience behavior.

Affinity precedence contributes to affinity consumption by preserving deterministic, bounded precedence references across room, notification, media, and environment affinity participation.

Precedence participates in explainability and diagnostics by carrying explicit precedence rationale and precedence trace references.

This section defines architecture only.

Do not define precedence algorithms.

## 10. Affinity Resolution Pipeline

Affinity Authority
↓
Affinity Context
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

Significance influences affinity participation as an externally governed context that may coexist with governed affinity context during runtime and experience participation.

Affinity interacts with significance through bounded participation references while preserving separate ownership and lineage boundaries.

Coordinator consumes significance and affinity independently.

Coordinator does not derive affinity from significance.

Coordinator does not derive significance from affinity.

This section defines architecture only.

## 12. Continuity Interaction

Grounding: CA2 continuity resolution pipeline.

Affinity interacts with continuity through bounded participation references in runtime and experience participation while preserving separate ownership boundaries.

Coordinator consumes continuity and affinity independently.

Coordinator does not derive affinity from continuity.

Coordinator does not derive continuity from affinity.

This section defines architecture only.

## 13. Room-Aware Participation

Grounding: EX3 room-aware experience consumption.

Affinity participates in room-aware behavior by carrying room-affinity context as bounded room-aware input.

This section defines architecture only.

## 14. Merged-Room Participation

Grounding: EX4 merged-room experience consumption.

Affinity participates in merged-room behavior by carrying merged-room-relevant affinity context as bounded merged-room input.

This section defines architecture only.

## 15. Composite-Room Participation

Grounding: EX5 composite-room experience consumption.

Affinity participates in composite-room behavior by carrying hierarchy-aware and scope-aware affinity context as bounded composite-room inputs.

This section defines architecture only.

## 16. Guest-Aware Participation

Grounding: EX6 guest-aware experience consumption.

Affinity participates in guest-aware behavior through governed guest-safe affinity boundaries and visibility constraints.

This section defines architecture only.

## 17. Explainability Hooks

Grounding: EX7 experience explainability.

Affinity explainability hooks include:

- room affinity hooks
- notification affinity hooks
- media affinity hooks
- environment affinity hooks
- precedence ordering hooks

These hooks carry bounded affinity rationale and lineage references for human-readable and machine-readable explainability surfaces.

This section defines architecture only.

## 18. Discovery Participation

Grounding: EX8 experience discovery.

Affinity participates in discovery by contributing governed affinity context to affinity-aware discoverability boundaries.

This section defines architecture only.

## 19. Diagnostics Hooks

Grounding: EX9 experience diagnostics.

Affinity diagnostics hooks include:

- affinity traces
- room-affinity traces
- notification-affinity traces
- media-affinity traces
- environment-affinity traces
- precedence traces

These hooks preserve bounded affinity traceability and troubleshooting participation references.

This section defines architecture only.

## 20. Affinity Lineage Framework

Affinity Authority
↓
Affinity Context
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

## 21. Ownership Protection

Coordinator does not own:

- affinity
- continuity
- significance
- relevance
- environmental evaluation
- priority context

Coordinator consumes all of the above.

## 22. Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Person-Room Affinity | HTBW affinity governance and model authorities | Consumer | PASS |
| Person Continuity | HTBW continuity governance and model authorities | Consumer | PASS |
| Significance | HTBW Asset Intelligence significance authority | Consumer | PASS |
| Relevance | HTBW Asset Intelligence relevance authority | Consumer | PASS |
| Environmental Evaluation | HTBW Asset Intelligence environmental evaluation authority | Consumer | PASS |
| Priority Context | HTBW Asset Intelligence priority-context authority | Consumer | PASS |
| Explainability | governed explainability artifacts | Consumer | PASS |
| Diagnostics | governed diagnostics artifacts | Consumer | PASS |

## 23. Risk Review

- affinity ownership drift
- affinity precedence drift
- continuity ownership drift
- significance ownership drift
- explainability divergence
- diagnostics divergence

## 24. Ownership Preservation Review

Result: PASS

Validated:

- affinity ownership preserved
- continuity ownership preserved
- significance ownership preserved
- Asset Intelligence ownership preserved

No ownership drift introduced in this E7 CA3 architecture baseline.

## 25. Readiness Statement

Person-Room Affinity Resolution Pipeline is READY.

This document becomes the authoritative affinity-resolution baseline for E7.
