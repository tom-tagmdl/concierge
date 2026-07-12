# Continuity and Affinity Explainability Framework

## 1. Purpose

This document defines the authoritative E7-CA7 continuity and affinity explainability framework baseline.

This document is architecture and governance only.

This document does not define explainability engines, explanation generators, AI reasoning systems, narrative generation, affinity scoring, or continuity scoring.

## 2. Authority Relationship

Continuity Authority remains external through HTBW continuity authorities.

Affinity Authority remains external through HTBW affinity authorities.

Explainability Authority remains external through governed explainability authorities.

Coordinator Explainability Role:

- explains consumed outcomes
- references governed continuity, affinity, significance, and guest-governance inputs
- exposes bounded machine-readable and human-readable explanation surfaces

Coordinator explains consumed outcomes.

Coordinator does not own continuity truth.

Coordinator does not own affinity truth.

Coordinator does not own significance truth.

## 3. Dependencies

CA7 consumes:

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
- docs/governance/experience-explainability-framework.md (EX7)
- docs/governance/experience-discovery-foundation.md (EX8)
- docs/governance/experience-diagnostics-framework.md (EX9)
- docs/governance/experience-consumption-readiness-review.md (EX10)
- EX10 addendum in issue #100
- docs/governance/experience-significance-consumption-architecture.md (EX11)

CA7 consumes all.

CA7 redefines none.

## 4. Continuity Explainability Model

Continuity explainability participates by carrying governed continuity references and rationale through runtime outcomes into explanation artifacts.

Prior-context reuse is explained through explicit continuity-context references and continuity-lineage references that describe why continuity context participated.

Continuity context becomes explainable evidence by preserving bounded continuity identifiers, continuity state references, and continuity eligibility references.

This section defines architecture only.

## 5. Affinity Explainability Model

Affinity explainability participates by carrying governed affinity references and rationale through runtime outcomes into explanation artifacts.

Preference application is explained through explicit affinity-context references and preference-lineage references that describe why affinity context participated.

Affinity context becomes explainable evidence by preserving bounded affinity identifiers, preference references, and affinity eligibility references.

This section defines architecture only.

## 6. Room Selection Explainability

Room-selection outcomes are explained as consumed outcome references that include room-aware continuity and room-aware affinity evidence from governed context.

Room-aware evidence participates by preserving bounded room context references, room eligibility references, and room-affinity or continuity contributions in explanation artifacts.

This section defines architecture only.

Do not define selection algorithms.

## 7. Preference Application Explainability

Preference application outcomes are explained through bounded references to governed affinity context and room-specific preference participation.

Affinity evidence participates by preserving preference references, override references, and eligibility references that support explainable preference participation outcomes.

This section defines architecture only.

## 8. Prior Context Reuse Explainability

Prior-context reuse is explained through bounded references to governed continuity context, including last-known and continuity-state participation references.

Continuity evidence participates by preserving continuity references, recency references, and continuity eligibility participation references.

This section defines architecture only.

## 9. Machine-Readable Explanation Model

Required machine-readable explanation structure includes:

- explanation identifier
- outcome reference
- continuity references
- affinity references
- room references when applicable
- guest references when applicable
- significance references when applicable
- eligibility references
- lineage references
- timestamp

Required evidence references include continuity evidence, affinity evidence, room evidence, guest evidence, and significance references.

Required lineage references include continuity lineage, affinity lineage, and bounded integration lineage to runtime outcomes.

This section defines architecture only.

## 10. Human-Readable Explanation Model

Required human-readable explanation structure includes concise rationale, bounded evidence summary, and ownership-safe phrasing.

Required explanation components include:

- outcome summary
- continuity participation summary when applicable
- affinity participation summary when applicable
- room-aware rationale when applicable
- guest or fallback rationale when applicable
- significance-reference rationale when applicable

This section defines architecture only.

## 11. Significance Explainability Integration

Grounding: EX11 experience significance consumption architecture.

Significance participates in explanations as externally governed referenced context that may influence outcomes and explanation rationale.

Coordinator references significance.

Coordinator does not explain significance as coordinator-owned truth.

This section defines architecture only.

## 12. Continuity Lineage Framework

Continuity Authority
↓
Continuity Context
↓
Coordinator Consumption
↓
Runtime Outcome
↓
Machine Explanation
↓
Human Explanation

This framework is architecture only.

## 13. Affinity Lineage Framework

Affinity Authority
↓
Affinity Context
↓
Coordinator Consumption
↓
Runtime Outcome
↓
Machine Explanation
↓
Human Explanation

This framework is architecture only.

## 14. Room-Aware Explainability

Grounding: CA4 room-aware continuity consumption.

Room-aware continuity explanations participate by preserving bounded room context references and continuity participation rationale in explanation artifacts.

This section defines architecture only.

## 15. Affinity-Aware Explainability

Grounding: CA5 room-aware affinity consumption.

Room-aware affinity explanations participate by preserving bounded room-affinity context and preference-participation rationale in explanation artifacts.

This section defines architecture only.

## 16. Guest-Aware Explainability

Grounding: CA6 guest-aware continuity and affinity behavior.

Guest-aware continuity explanations participate by preserving bounded guest eligibility and continuity participation rationale.

Guest-aware affinity explanations participate by preserving bounded guest eligibility and affinity participation rationale.

Fallback explanations participate by preserving bounded unknown-person and privacy-safe fallback rationale.

This section defines architecture only.

## 17. Explainability Evidence Model

Explainability evidence includes:

- continuity evidence
- affinity evidence
- room evidence
- guest evidence
- significance references

Evidence remains governed, bounded, traceable, and ownership-preserving.

This section defines architecture only.

## 18. Diagnostics Integration

Grounding: EX9 experience diagnostics framework.

Explainability references diagnostics by carrying shared trace and lineage references into diagnostics surfaces.

Diagnostics supports explainability by preserving traceability and troubleshooting evidence for explanation rationale.

This section defines architecture only.

## 19. Discovery Integration

Grounding: EX8 experience discovery foundation.

Explainability participates in discovery by supplying bounded explanation rationale and evidence references for discoverable outcomes.

This section defines architecture only.

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
- explanation truth drift
- guest governance drift
- diagnostics divergence

## 23. Ownership Preservation Review

Result: PASS

Validated:

- continuity ownership preserved
- affinity ownership preserved
- significance ownership preserved
- guest governance preserved
- Asset Intelligence ownership preserved

No ownership drift introduced in this E7 CA7 architecture baseline.

## 24. Readiness Statement

Continuity and Affinity Explainability Framework is READY.

This document becomes the authoritative explainability baseline for E7.
