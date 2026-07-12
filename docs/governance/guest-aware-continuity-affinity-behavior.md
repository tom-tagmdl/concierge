# Guest-Aware Continuity and Affinity Behavior

## 1. Purpose

This document defines the authoritative E7-CA6 guest-aware continuity and affinity consumption architecture baseline.

This document is architecture and governance only.

This document does not define guest-detection engines, identity resolution engines, continuity restoration engines, affinity scoring, privacy engines, guest classification algorithms, or unknown-person inference engines.

## 2. Authority Relationship

Person Continuity Authority remains external through HTBW continuity authorities.

Person-Room Affinity Authority remains external through HTBW affinity authorities.

Guest Governance Authority remains external through governed guest-safe policy authorities.

Coordinator Consumption Authority:

- consumes continuity
- consumes affinity
- consumes guest-governance outcomes
- consumes significance context

Coordinator consumes continuity.

Coordinator consumes affinity.

Coordinator consumes guest-governance outcomes.

Coordinator does not own any of them.

Coordinator does not define continuity.

Coordinator does not define affinity.

Coordinator does not define guest categories.

Coordinator does not redefine continuity governance or affinity governance.

## 3. Dependencies

CA6 consumes:

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
- docs/governance/guest-aware-experience-consumption-architecture.md (EX6)
- docs/governance/experience-explainability-framework.md (EX7)
- docs/governance/experience-discovery-foundation.md (EX8)
- docs/governance/experience-diagnostics-framework.md (EX9)
- docs/governance/experience-consumption-readiness-review.md (EX10)
- EX10 addendum in issue #100
- docs/governance/experience-significance-consumption-architecture.md (EX11)

CA6 consumes all.

CA6 redefines none.

## 4. Guest-Aware Consumption Model

Guest-aware continuity means Coordinator consumes governed continuity context under guest-safe and unknown-person boundaries without continuity ownership transfer.

Guest-aware affinity means Coordinator consumes governed affinity context under guest-safe and unknown-person boundaries without affinity ownership transfer.

Guest participation works by consuming externally governed guest outcomes that bound continuity and affinity participation for guest-safe runtime behavior.

Unknown-person participation works by consuming governed unknown-person outcomes and fallback boundaries that constrain continuity and affinity participation.

This section defines architecture only.

## 5. Guest Continuity Participation

Guest continuity participation works as governed continuity consumption bounded by guest-safe eligibility and visibility outcomes.

Continuity eligibility participates for guest scenarios by constraining continuity context to governed guest-safe participation boundaries.

This section defines architecture only.

## 6. Guest Affinity Participation

Guest affinity participation works as governed affinity consumption bounded by guest-safe eligibility and visibility outcomes.

Affinity eligibility participates for guest scenarios by constraining affinity context to governed guest-safe participation boundaries.

This section defines architecture only.

## 7. Unknown-Person Participation

Unknown-person participation works as governed unknown-person outcome consumption that bounds continuity and affinity participation to safe fallback surfaces.

Unknown-person outcomes participate as explicit governed context for household-facing runtime behavior, explainability, and diagnostics.

This section defines architecture only.

Do not define identity algorithms.

## 8. Privacy-Safe Fallback Participation

Privacy-safe fallback behavior participates as governed fallback context that constrains continuity and affinity participation under guest and unknown-person scenarios.

Fallback behavior protects ownership boundaries by preserving external guest governance authority and preventing Coordinator ownership transfer for continuity or affinity.

This section defines architecture only.

## 9. Guest Eligibility Participation

Guest eligibility participates as governed context that bounds guest-safe continuity and affinity participation.

Continuity and affinity eligibility participate by constraining household-facing runtime outcomes to governed guest-safe and unknown-person-safe boundaries.

This section defines architecture only.

Do not define eligibility algorithms.

## 10. Guest-Aware Pipeline

Guest Governance
↓
Continuity Authority
↓
Affinity Authority
↓
Guest Eligibility
↓
Coordinator Consumption
↓
Runtime Participation
↓
Explainability
↓
Diagnostics

This pipeline is architecture only.

## 11. Significance Interaction

Grounding: EX11 experience significance consumption architecture.

Significance interacts with guest-aware continuity and affinity as an independently consumed governed context that may coexist with guest-aware participation.

Coordinator consumes significance independently.

Coordinator does not derive continuity or affinity from significance.

This section defines architecture only.

## 12. Room-Aware Interaction

Grounding: CA4 room-aware continuity consumption and CA5 room-aware affinity consumption.

Room-aware continuity and room-aware affinity interact with guest-aware behavior through bounded guest eligibility and fallback participation surfaces while preserving separate ownership boundaries.

This section defines architecture only.

## 13. Unknown-Person Fallback Interaction

Unknown-person fallback participation interacts with continuity by constraining continuity participation to governed fallback-safe context boundaries.

Unknown-person fallback participation interacts with affinity by constraining affinity participation to governed fallback-safe context boundaries.

This section defines architecture only.

## 14. Deterministic Behavior

Guest and unknown-person handling remain deterministic by consuming fixed governed guest outcomes, governed continuity and affinity inputs, and governed fallback boundaries.

Fallback participation remains deterministic because the same governed guest and unknown-person inputs produce the same bounded guest-safe participation outcomes.

This section defines architecture only.

## 15. Explainability Hooks

Grounding: EX7 experience explainability framework.

Guest-aware explainability hooks include:

- guest continuity hooks
- guest affinity hooks
- unknown-person hooks
- fallback-behavior hooks
- guest eligibility hooks

These hooks preserve bounded guest-aware rationale and lineage references for human-readable and machine-readable explainability surfaces.

This section defines architecture only.

## 16. Discovery Participation

Grounding: EX8 experience discovery foundation.

Guest-aware continuity and affinity participate in discovery by contributing governed guest-safe continuity and affinity context to discoverability participation boundaries.

This section defines architecture only.

## 17. Diagnostics Hooks

Grounding: EX9 experience diagnostics framework.

Guest-aware diagnostics hooks include:

- guest traces
- continuity traces
- affinity traces
- unknown-person traces
- fallback traces
- eligibility traces

These hooks preserve bounded guest-aware traceability and troubleshooting participation references.

This section defines architecture only.

## 18. Guest-Aware Lineage Framework

Guest Governance
↓
Continuity Authority
↓
Affinity Authority
↓
Guest Eligibility
↓
Coordinator Consumption
↓
Runtime Outcome
↓
Explainability
↓
Diagnostics

This framework is architecture only.

## 19. Ownership Protection

Coordinator does not own:

- continuity
- affinity
- significance
- relevance
- environmental evaluation
- priority context
- guest governance

Coordinator consumes all of the above.

## 20. Ownership Matrix

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

## 21. Risk Review

- continuity ownership drift
- affinity ownership drift
- guest governance drift
- fallback behavior drift
- significance ownership drift
- explainability divergence
- diagnostics divergence

## 22. Privacy-Safe Behavior Review

Result: PASS

Validated:

- guest-safe behavior preserved
- unknown-person behavior preserved
- fallback behavior preserved

## 23. Ownership Preservation Review

Result: PASS

Validated:

- continuity ownership preserved
- affinity ownership preserved
- guest governance preserved
- significance ownership preserved
- Asset Intelligence ownership preserved

No ownership drift introduced in this E7 CA6 architecture baseline.

## 24. Readiness Statement

Guest-Aware Continuity and Affinity Behavior is READY.

This document becomes the authoritative guest-aware baseline for E7.
