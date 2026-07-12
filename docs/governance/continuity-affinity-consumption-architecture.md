# Coordinator Continuity and Affinity Consumption Architecture

## 1. Purpose

This document defines the authoritative E7-CA1 continuity and affinity consumption architecture baseline.

This document is architecture and governance only.

This document does not define continuity governance, affinity governance, continuity scoring, affinity scoring, continuity algorithms, affinity algorithms, restoration algorithms, room-selection algorithms, or person inference.

## 2. Authority Relationship

Person Continuity Authority remains external through HTBW continuity authorities.

Person-Room Affinity Authority remains external through HTBW affinity authorities.

Asset Intelligence Authority remains external through HTBW Asset Intelligence authorities.

Coordinator Consumption Authority:

- consumes continuity
- consumes affinity
- consumes significance
- consumes relevance
- consumes environmental evaluation outcomes
- consumes priority context

Coordinator consumes continuity.

Coordinator consumes affinity.

Coordinator consumes significance.

Coordinator owns none of them.

Coordinator does not redefine continuity governance.

Coordinator does not redefine affinity governance.

Coordinator does not redefine continuity contracts.

Coordinator does not redefine affinity contracts.

Coordinator does not redefine continuity models.

Coordinator does not redefine affinity models.

## 3. Dependencies

CA1 consumes:

- HTBW #19 Personalization Governance ADR
- HTBW #31 Person Continuity and Affinity Contract
- HTBW #45 Person Continuity Model
- HTBW #46 Person-Room Affinity Model
- `docs/governance/experience-consumption-architecture.md` (EX1)
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

CA1 consumes all.

CA1 redefines none.

## 4. Continuity Consumption Model

Continuity consumption means Coordinator consumes governed continuity context as bounded input for experience participation and runtime participation.

Continuity participates as externally governed context that can influence eligibility, visibility, and continuity-aware household-facing outcomes.

Coordinator consumes continuity references, continuity state, and continuity explainability references without becoming continuity authority.

This section defines architecture only.

## 5. Affinity Consumption Model

Affinity consumption means Coordinator consumes governed affinity context as bounded input for experience participation and runtime participation.

Affinity participates as externally governed context that can influence room-aware preference participation and visibility-aware household-facing outcomes.

Coordinator consumes affinity references, affinity state, and affinity explainability references without becoming affinity authority.

This section defines architecture only.

## 6. Consumption Lifecycle

Governed Continuity
↓
Governed Affinity
↓
Coordinator Consumption
↓
Experience Participation
↓
Runtime Participation
↓
Explainability
↓
Diagnostics

This lifecycle is architecture only.

## 7. Coordinator Integration Model

Continuity integrates with Coordinator as governed continuity context consumed during experience participation and runtime participation.

Affinity integrates with Coordinator as governed affinity context consumed during room-aware, preference-aware, and visibility-aware participation.

Consumed continuity and affinity may influence runtime behavior as bounded participation inputs while preserving external governance ownership.

No continuity or affinity algorithms are defined in this model.

This section defines architecture only.

## 8. Significance Interaction Model

Effect of EX11 on CA1:

- CA1 inherits EX11 ownership boundaries for significance, relevance, environmental evaluation, and priority context.
- CA1 consumes EX11 significance interaction boundaries and does not redefine them.
- EX10 addendum confirmation is preserved: EX11 extends consumption architecture and does not alter E7 readiness.

Significance participates with continuity by providing externally governed context that may coexist with continuity participation in experience behavior.

Significance participates with affinity by providing externally governed context that may coexist with affinity participation in experience behavior.

Significance participates with experience participation as an independent consumed context surface aligned to EX11.

Coordinator consumes significance and continuity independently.

Coordinator does not derive one from the other.

Coordinator does not merge ownership.

This section defines architecture only.

## 9. Room-Aware Participation

Grounding: EX3 room-aware experience consumption.

Continuity participates in room-aware behavior by contributing governed room-linked continuity context as bounded room-aware input.

Affinity participates in room-aware behavior by contributing governed room preference context as bounded room-aware input.

This section defines architecture only.

## 10. Merged-Room Participation

Grounding: EX4 merged-room experience consumption.

Continuity participates in merged-room behavior by contributing governed merged-room-linked continuity context as bounded merged-room input.

Affinity participates in merged-room behavior by contributing governed merged-room preference context as bounded merged-room input.

This section defines architecture only.

## 11. Composite-Room Participation

Grounding: EX5 composite-room experience consumption.

Continuity participates in composite-room behavior by contributing governed hierarchy-aware and scope-aware continuity context.

Affinity participates in composite-room behavior by contributing governed hierarchy-aware and scope-aware affinity context.

Hierarchy participation and scope participation are consumed as external context boundaries and are not ownership-transfer surfaces.

This section defines architecture only.

## 12. Guest-Aware Participation

Grounding: EX6 guest-aware experience consumption.

Continuity participates in guest-aware behavior through governed guest-safe continuity boundaries.

Affinity participates in guest-aware behavior through governed guest-safe affinity visibility boundaries.

Guest boundaries constrain continuity and affinity participation while preserving external guest governance ownership.

This section defines architecture only.

## 13. Explainability Participation

Grounding: EX7 experience explainability.

Continuity participates in explainability through continuity references and continuity rationale lineage.

Affinity participates in explainability through affinity references and affinity rationale lineage.

Significance lineage integrates by preserving EX11 significance reference boundaries in continuity-aware and affinity-aware explanations.

This section defines architecture only.

## 14. Discovery Participation

Grounding: EX8 experience discovery.

Continuity participates in discovery as governed context that may influence discoverability boundaries for continuity-aware experiences.

Affinity participates in discovery as governed context that may influence discoverability boundaries for affinity-aware experiences.

This section defines architecture only.

## 15. Diagnostics Participation

Grounding: EX9 experience diagnostics.

Continuity traces participate by preserving governed continuity references in diagnostics lineage.

Affinity traces participate by preserving governed affinity references in diagnostics lineage.

Significance lineage participates by preserving EX11 significance trace boundaries alongside continuity and affinity diagnostics traces.

This section defines architecture only.

## 16. Continuity Lineage Framework

Continuity Authority
↓
Coordinator Consumption
↓
Experience Participation
↓
Runtime Outcome
↓
Explainability
↓
Diagnostics

This framework is architecture only.

## 17. Affinity Lineage Framework

Affinity Authority
↓
Coordinator Consumption
↓
Experience Participation
↓
Runtime Outcome
↓
Explainability
↓
Diagnostics

This framework is architecture only.

## 18. Ownership Protection

Coordinator does not own:

- continuity
- affinity
- significance
- relevance
- environmental evaluation
- priority context

Coordinator consumes all of the above.

## 19. Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Person Continuity | HTBW continuity governance and model authorities | Consumer | PASS |
| Person-Room Affinity | HTBW affinity governance and model authorities | Consumer | PASS |
| Significance | HTBW Asset Intelligence significance authority | Consumer | PASS |
| Relevance | HTBW Asset Intelligence relevance authority | Consumer | PASS |
| Environmental Evaluation | HTBW Asset Intelligence environmental evaluation authority | Consumer | PASS |
| Priority Context | HTBW Asset Intelligence priority-context authority | Consumer | PASS |
| Experience Governance | HTBW experience governance | Consumer | PASS |
| Explainability | governed explainability artifacts | Consumer | PASS |
| Diagnostics | governed diagnostics artifacts | Consumer | PASS |

## 20. Risk Review

- continuity ownership drift
- affinity ownership drift
- significance ownership drift
- Asset Intelligence ownership drift
- explainability divergence
- diagnostics divergence

## 21. Ownership Preservation Review

Result: PASS

Validated:

- continuity ownership preserved
- affinity ownership preserved
- significance ownership preserved
- Asset Intelligence ownership preserved
- experience ownership preserved

No ownership drift introduced in this E7 CA1 architecture baseline.

## 22. Readiness Statement

Coordinator Continuity and Affinity Consumption Architecture is READY.

This document becomes the authoritative foundation for all E7 work.
