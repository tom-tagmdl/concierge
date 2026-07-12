# Continuity and Affinity Influence Matrix

## 1. Purpose

This document defines the authoritative E7-CA8 continuity and affinity influence matrix baseline.

This document is architecture and governance only.

This document does not define influence engines, prioritization engines, routing engines, messaging engines, restoration engines, ranking algorithms, or scoring algorithms.

## 2. Authority Relationship

Continuity Authority remains external through HTBW continuity authorities.

Affinity Authority remains external through HTBW affinity authorities.

Significance Authority remains external through HTBW Asset Intelligence authorities.

Coordinator Influence Participation Role:

- consumes continuity, affinity, significance, relevance, environmental evaluation, and priority context as influence inputs
- exposes influence participation surfaces for downstream household-facing outcomes
- preserves external governance ownership boundaries

Coordinator consumes influence inputs.

Coordinator does not own influence authorities.

## 3. Dependencies

CA8 consumes:

- HTBW #19 Personalization Governance ADR
- HTBW #31 Person Continuity and Affinity Contract
- HTBW #45 Person Continuity Model
- HTBW #46 Person-Room Affinity Model
- ADR-004 Coordinator V2 Governance Boundaries
- ADR-005 Room Vocabulary Governance Boundaries
- ADR-006 Capability Projection Governance Boundaries
- docs/governance/coordinator-v2-foundation-summary.md
- docs/governance/continuity-affinity-consumption-architecture.md (CA1)
- docs/governance/person-continuity-resolution-pipeline.md (CA2)
- docs/governance/person-room-affinity-resolution-pipeline.md (CA3)
- docs/governance/room-aware-continuity-consumption.md (CA4)
- docs/governance/room-aware-affinity-consumption.md (CA5)
- docs/governance/guest-aware-continuity-affinity-behavior.md (CA6)
- docs/governance/continuity-affinity-explainability-framework.md (CA7)
- docs/governance/experience-consumption-architecture.md (EX1)
- docs/governance/experience-resolution-consumption-architecture.md (EX2)
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

CA8 consumes all.

CA8 redefines none.

## 4. Influence Model

Influence participation means Coordinator consumes governed continuity, affinity, significance, room context, and guest context as bounded context that may affect downstream household-facing outcomes.

Influence participation does not mean Coordinator owns, derives, or re-governs continuity, affinity, significance, or guest governance authorities.

This section defines architecture only.

## 5. Experience Influence

Continuity participates in experience influence by contributing governed prior-context and continuity-state context.

Affinity participates in experience influence by contributing governed preference and room-affinity context.

Significance may participate in experience influence by contributing externally governed significance, relevance, environmental evaluation, and priority context references.

This section defines architecture only.

## 6. Routing Influence

Continuity participates in routing influence through governed continuity context that may shape routing participation boundaries.

Affinity participates in routing influence through governed preference context that may shape routing participation boundaries.

Room-awareness participates in routing influence through governed room context references and room-aware continuity/affinity context.

This section defines architecture only.

## 7. Messaging Influence

Continuity participates in messaging influence through governed prior-context continuity references.

Affinity participates in messaging influence through governed notification and preference context references.

Guest-awareness participates in messaging influence through governed guest-safe and fallback boundaries.

This section defines architecture only.

## 8. Restoration Influence

Continuity participates in restoration influence through governed continuity context and prior-context reuse participation.

Affinity participates in restoration influence through governed preference context that may participate in restoration-facing outcomes.

Restoration participation is influenced through bounded governed context consumption and does not transfer restoration authority.

This section defines architecture only.

Do not define restoration algorithms.

## 9. Prioritization Influence

Continuity participates in prioritization influence through governed continuity-state and recency context participation.

Affinity participates in prioritization influence through governed preference participation context.

Significance participates in prioritization influence through externally governed significance and priority context references.

This section defines architecture only.

Do not define prioritization algorithms.

## 10. Influence Precedence Model

Precedence participates as governed context ordering that bounds how consumed continuity, affinity, significance, room, and guest context participate in downstream influence surfaces.

Precedence contributes to influence participation by preserving deterministic, explainable context-order references for influence outcomes.

This section defines architecture only.

Do not define precedence algorithms.

## 11. Influence Matrix

| Influence Domain | Continuity | Affinity | Significance | Room Context | Guest Context |
|---|---|---|---|---|---|
| Experience | Prior-context and continuity-state participation | Preference participation | External significance and priority-context participation | Room-aware participation context | Guest-safe participation boundaries |
| Routing | Continuity participation boundaries | Preference participation boundaries | External context reference participation | Room-aware routing context participation | Guest-safe routing boundary participation |
| Messaging | Prior-context continuity participation | Notification and preference participation | External significance reference participation | Room-scoped messaging context participation | Guest-safe and fallback participation |
| Restoration | Continuity restoration-context participation | Preference restoration-context participation | External significance reference participation | Room-aware restoration context participation | Guest-safe restoration boundaries |
| Prioritization | Continuity-state participation | Preference participation | External significance and priority-context participation | Room-scoped prioritization context participation | Guest-aware prioritization boundary participation |

Documented participation relationships only.

No algorithms are defined here.

## 12. Significance Influence Integration

Grounding: EX11 experience significance consumption architecture.

Significance participates alongside continuity and affinity as externally governed context consumed in parallel influence participation surfaces.

Coordinator consumes all independently.

Coordinator derives none.

This section defines architecture only.

## 13. Room-Aware Influence

Grounding: CA4 room-aware continuity consumption and CA5 room-aware affinity consumption.

Room-aware continuity and affinity participate as bounded room-context influence inputs across experience, routing, messaging, restoration, and prioritization influence surfaces.

This section defines architecture only.

## 14. Guest-Aware Influence

Grounding: CA6 guest-aware continuity and affinity behavior.

Guest-aware continuity and affinity participate as bounded guest-governed influence inputs across downstream household-facing influence surfaces.

This section defines architecture only.

## 15. Explainability Participation

Grounding: CA7 continuity and affinity explainability framework.

Influence outcomes become explainable by preserving bounded influence references, evidence references, and lineage references.

Influence evidence participates by carrying continuity, affinity, significance, room, and guest context evidence into explainability surfaces.

This section defines architecture only.

## 16. Diagnostics Participation

Grounding: EX9 experience diagnostics framework.

Influence outcomes participate in diagnostics by preserving bounded trace references from influence participation into diagnostics surfaces.

Influence traces participate as troubleshooting and lineage evidence across influence domains.

This section defines architecture only.

## 17. Continuity Influence Lineage

Continuity Authority
↓
Continuity Context
↓
Influence Participation
↓
Runtime Outcome
↓
Explainability
↓
Diagnostics

This framework is architecture only.

## 18. Affinity Influence Lineage

Affinity Authority
↓
Affinity Context
↓
Influence Participation
↓
Runtime Outcome
↓
Explainability
↓
Diagnostics

This framework is architecture only.

## 19. Significance Influence Lineage

Significance Authority
↓
Significance Context
↓
Influence Participation
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
- guest governance

Coordinator consumes all of the above.

## 21. Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Person Continuity | HTBW continuity governance and model authorities | Consumer | PASS |
| Person-Room Affinity | HTBW affinity governance and model authorities | Consumer | PASS |
| Guest Governance | external guest-safe governance authorities | Consumer | PASS |
| Significance | HTBW Asset Intelligence significance authority | Consumer | PASS |
| Relevance | HTBW Asset Intelligence relevance authority | Consumer | PASS |
| Environmental Evaluation | HTBW Asset Intelligence environmental evaluation authority | Consumer | PASS |
| Priority Context | HTBW Asset Intelligence priority-context authority | Consumer | PASS |
| Explainability | governed explainability artifacts | Consumer | PASS |
| Diagnostics | governed diagnostics artifacts | Consumer | PASS |

## 22. Risk Review

- continuity ownership drift
- affinity ownership drift
- significance ownership drift
- influence ownership drift
- guest governance drift
- explainability divergence
- diagnostics divergence

## 23. Ownership Preservation Review

Result: PASS

Validated:

- continuity ownership preserved
- affinity ownership preserved
- significance ownership preserved
- guest governance preserved
- Asset Intelligence ownership preserved

No ownership drift introduced in this E7 CA8 architecture baseline.

## 24. Readiness Statement

Continuity and Affinity Influence Matrix is READY.

This document becomes the authoritative influence baseline for E7.
