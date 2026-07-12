# Household Memory Consumption Architecture

## 1. Purpose

Define the authoritative E10-HM1 architecture baseline for household memory consumption.

This document defines household memory consumption architecture only.

This document is architecture and governance only.

This document does not implement memory storage, retrieval, ranking, retention behavior, privacy behavior, memory queries, or explainability rendering.

## 2. Scope Reviewed

Reviewed mandatory authorities and dependencies:

- HTBW #20
- HTBW #47
- Concierge #138
- E9 Messaging V2 Readiness Review
- M8 Message Provenance and Delivery History Consumption
- M9 Messaging Diagnostics and Explainability Surface

Reviewed associated architecture authorities:

- ADR-009 Household Memory Governance Boundaries
- Household Memory Contract
- Household Memory Model
- Provenance Contract
- Event Model

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#20, #47, #138, #141) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between HM1 outputs and authoritative ADR/contract/model artifacts.

## 3. Household Memory Authority Validation

Validation scope:

- household memory ownership
- household memory governance
- memory lifecycle governance
- memory retention governance

Result: PASS

Validated statements:

- Household Memory governance remains in HTBW.
- Memory ownership remains in HTBW.
- Memory lifecycle governance remains in HTBW.
- Memory retention governance remains in HTBW.
- Coordinator consumes memory outcomes and memory context.
- Coordinator does not redefine household memory contracts or models.

## 4. Provenance Authority Validation

Validation scope:

- provenance ownership
- provenance governance
- attribution ownership
- attribution governance

Result: PASS

Validated statements:

- Provenance ownership remains in HTBW.
- Provenance governance remains in HTBW.
- Attribution ownership remains in HTBW.
- Attribution governance remains in HTBW.
- Coordinator consumes provenance outcomes.
- Coordinator does not redefine provenance semantics.

## 5. Event History Authority Validation

Validation scope:

- event history ownership
- event history governance
- historical truth authority

Result: PASS

Validated statements:

- Event history ownership remains external to Concierge memory consumption behavior.
- Event history governance remains external to Coordinator.
- Historical truth authority remains with authoritative event systems.
- Coordinator consumes event-history outcomes and context.
- Coordinator does not redefine event history semantics.

## 6. E9 Alignment Review

Validation scope:

- messaging readiness
- diagnostics readiness
- explainability readiness

Result: PASS

E9 readiness approval is validated and HM1 builds on approved E9 outputs, including complete provenance architecture, diagnostics architecture, and explainability architecture.

## 7. M8 Provenance Alignment Review

Validation scope:

- provenance lineage
- attribution lineage
- delivery-history lineage

Result: PASS

HM1 consumes M8 provenance architecture and preserves provenance, attribution, and delivery-history lineage boundaries.

## 8. M9 Diagnostics Alignment Review

Validation scope:

- diagnostics lineage
- troubleshooting lineage
- explainability lineage

Result: PASS

HM1 aligns with M9 diagnostics and explainability foundations and preserves bounded lineage participation.

## 9. Household Memory Consumption Architecture

Validation scope:

- memory participation
- memory consumption
- memory lifecycle
- memory outcomes

Result: PASS

Architecture-only household memory consumption:

- memory participation: consume governed memory context, provenance context, event-history context, occupancy context, and identity context as bounded inputs.
- memory consumption: consume memory outcomes for household-facing experience and explanation participation within Concierge-owned behavior boundaries.
- memory lifecycle: availability -> participation -> bounded memory consumption -> memory outcome handoff.
- memory outcomes: preserve memory outcomes and lineage references for explainability and diagnostics readiness.

## 10. Memory Context Consumption Review

Validation scope:

- context participation
- context consumption
- context lineage

Result: PASS

Memory context participation and consumption remain bounded to governed memory-context outcomes with explicit context lineage preserved.

## 11. Provenance Context Consumption Review

Validation scope:

- provenance participation
- provenance consumption
- provenance lineage

Result: PASS

Provenance context participation and consumption remain bounded to governed provenance outcomes with explicit provenance lineage preserved.

## 12. Event History Consumption Review

Validation scope:

- event-history participation
- event-history consumption
- event-history lineage

Result: PASS

Event-history participation and consumption remain bounded to authoritative event-history outcomes with explicit historical lineage preserved.

## 13. Occupancy and Identity Participation Review

Validation scope:

- occupancy participation
- identity participation
- confidence participation

Result: PASS

Occupancy, identity, and confidence participation remain bounded to governed outputs without occupancy or identity ownership transfer.

## 14. Memory Lifecycle Review

Validation scope:

- memory creation participation
- memory availability participation
- memory consumption participation
- memory retirement participation

Result: PASS

Lifecycle participation is consumption-only:

- Coordinator consumes lifecycle outcomes.
- Coordinator does not define lifecycle policy.
- Lifecycle governance remains external to Coordinator.

## 15. Household-Facing Explanation Review

Validation scope:

- explanation participation
- memory explanation consumption
- provenance explanation participation

Result: PASS

Household-facing explanation participation consumes governed memory and provenance explanation references without redefining explanation governance.

## 16. Memory Traceability Review

Validation scope:

- memory traceability
- provenance traceability
- historical traceability

Result: PASS

Traceability remains explicit and ownership-safe across memory references, provenance lineage, and event-history lineage.

## 17. Memory Lineage Architecture

Validation scope:

- memory inputs
- event-history inputs
- provenance inputs
- occupancy inputs
- identity inputs
- memory outcomes

Result: PASS

Lineage architecture:

- memory-input lineage remains tied to HTBW-governed memory outcomes.
- event-history-input lineage remains tied to authoritative event-history outputs.
- provenance-input lineage remains tied to HTBW-governed provenance and attribution outputs.
- occupancy-input lineage remains tied to HTBW-governed occupancy outputs.
- identity-input lineage remains tied to HTBW-governed identity outputs.
- memory-outcome lineage remains tied to concierge household-facing consumption outcomes.

## 18. Deterministic Memory Consumption Review

Validation scope:

- memory participation
- history participation
- provenance participation
- explanation participation

Result: PASS

Deterministic requirements:

- same governed memory/history/provenance/identity/occupancy inputs produce the same bounded memory participation outcomes.
- history and provenance participation remain deterministic and traceable.
- explanation participation remains deterministic and ownership-safe.

## 19. Explainability Readiness Review

Validation scope:

- future HM7 Why Did This Happen? support

Result: PASS

HM1 preserves memory and provenance lineage sufficiency required for future HM7 explainability planning.

## 20. Diagnostics Readiness Review

Validation scope:

- future HM9 Household Memory Diagnostics Surface support

Result: PASS

HM1 preserves traceability sufficiency required for future HM9 diagnostics planning.

## 21. Ownership Validation

Validation scope:

Coordinator does not own:

- memory governance
- memory lifecycle governance
- provenance governance
- event-history governance
- occupancy governance
- identity governance

Result: PASS

Coordinator consumes governed outcomes and owns none of the listed governance domains.

## 22. Ownership Drift Analysis

Validation scope:

No transfer of:

- memory ownership
- provenance ownership
- event-history ownership
- occupancy ownership
- identity ownership

Result: PASS

No ownership drift identified.

## 23. Downstream Guidance

Provide constraints only. Do not pre-design future issues.

- HM2 Event History and Provenance Relationship: consume event-history/provenance authorities; do not redefine historical truth or attribution semantics.
- HM3 Identity-Linked Memory Boundaries: consume identity/confidence context under governed constraints; do not transfer identity authority.
- HM4 Room-Linked Memory Boundaries: consume room and occupancy context under governed boundaries; do not redefine room truth.
- HM5 Who Did This? Query Planning: derive answers from governed provenance and event lineage only; no inferred alternate attribution truth.
- HM6 What Happened While I Was Away? Planning: derive summaries from governed event-history and provenance lineage only; no alternate historical truth.
- HM7 Why Did This Happen? Explanation Planning: consume memory/provenance/explanation lineage from authoritative domains; no provenance or explainability governance transfer.
- HM8 Privacy, Retention, and Guest-Safe Memory Boundaries: consume HTBW privacy/retention/guest-safe governance and preserve restricted visibility boundaries.
- HM9 Household Memory Diagnostics Surface: consume deterministic traceability and lineage anchors; diagnostics governance remains external.
- HM10 Household Memory Readiness Review: validate HM1-HM9 completeness, ownership preservation, determinism, and supportability readiness.

## 24. HM1 Baseline Determination

Result: PASS

Household memory consumption architecture is sufficiently documented for downstream E10 work.

## 25. Final Determination

E10-HM1 HOUSEHOLD MEMORY CONSUMPTION ARCHITECTURE

APPROVED AS THE AUTHORITATIVE BASELINE

FOR HOUSEHOLD MEMORY CONSUMPTION
