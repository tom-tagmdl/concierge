# Why Did This Happen Explanation Planning

## 1. Purpose

Define the authoritative E10-HM7 architecture baseline for household explanation planning.

This document defines explanation-planning consumption architecture only.

This document is architecture and governance only.

This document does not implement explanation engines, causality engines, inference engines, root-cause determination, event reconstruction, memory retrieval, provenance generation, diagnostics rendering, or HM8 implementation work.

## 2. Scope Reviewed

Reviewed mandatory authorities and dependencies:

- HTBW #47
- HTBW #48
- Concierge #139
- HM2 Event History and Provenance Relationship
- HM3 Identity-Linked Memory Boundaries
- HM6 What Happened While I Was Away Planning
- E9 Messaging Diagnostics and Explainability Surface

Reviewed associated governance authorities:

- Provenance Contract
- Event Model
- Person Identity Contract
- Occupancy and Presence Contract

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#47, #48, #139, #147) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between HM7 outputs and authoritative ADR/contract/model artifacts.

## 3. Explainability Authority Validation

Validation scope:

- explainability ownership
- explainability governance
- explanation authority
- explanation lifecycle authority

Result: PASS

Validated statements:

- Explainability ownership remains external.
- Explainability governance remains external.
- Explanation authority remains in external governed explainability authorities.
- Explanation lifecycle authority remains external to Coordinator.
- Coordinator consumes explanation inputs and explanation outcomes.
- Coordinator does not redefine explainability governance.

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
- Coordinator consumes provenance and attribution outcomes.
- Coordinator does not redefine provenance or attribution truth.

## 5. Historical Truth Validation

Validation scope:

- historical truth authority
- event-history ownership
- event-history governance

Result: PASS

Validated statements:

- Historical truth authority remains external to Coordinator.
- Event-history ownership remains in HTBW-governed event authorities.
- Event-history governance remains in HTBW-governed event authorities.
- Coordinator consumes event-history outcomes.
- Coordinator does not redefine event-history or historical truth semantics.

## 6. HM2 Alignment Review

Validation scope:

- provenance ownership
- attribution ownership
- historical truth alignment

Result: PASS

HM7 conforms to HM2 provenance/attribution ownership boundaries and historical truth alignment.

## 7. HM3 Alignment Review

Validation scope:

- identity lineage
- confidence lineage
- identity governance alignment

Result: PASS

HM7 conforms to HM3 identity and confidence lineage boundaries and identity governance alignment.

## 8. HM6 Alignment Review

Validation scope:

- summary lineage
- provenance-backed summaries
- historical traceability

Result: PASS

HM7 conforms to HM6 summary-lineage and provenance-backed historical-traceability boundaries.

## 9. E9 Explainability Alignment Review

Validation scope:

- diagnostics lineage
- explainability lineage
- troubleshooting lineage

Result: PASS

HM7 builds on E9 explainability governance by preserving diagnostics, explainability, and troubleshooting lineage boundaries.

## 10. Why-Did-This-Happen Architecture

Validation scope:

- explanation participation
- explanation consumption
- explanation retrieval
- explanation outcomes

Result: PASS

Architecture-only explanation planning:

- explanation participation: consume governed memory/provenance/attribution/event-history/diagnostics/occupancy/room/identity context as bounded explanation inputs.
- explanation consumption: consume explanation-planning outcomes for household-facing explanation orchestration.
- explanation retrieval: consume governed explanation references and lineage anchors.
- explanation outcomes: preserve bounded explanation outcomes for traceability and supportability.

## 11. Explanation Retrieval Review

Validation scope:

- retrieval participation
- retrieval consumption
- retrieval lineage

Result: PASS

Explanation retrieval participation remains bounded to governed explanation references with explicit retrieval lineage preserved.

## 12. Memory Lineage Review

Validation scope:

- memory participation
- memory lineage
- memory explanation lineage

Result: PASS

Memory participation remains consumption-only and memory explanation lineage remains tied to HTBW-governed household-memory outputs.

## 13. Provenance Lineage Review

Validation scope:

- provenance participation
- provenance lineage
- explanation lineage

Result: PASS

Provenance participation remains consumption-only and provenance explanation lineage remains tied to HTBW-governed provenance outputs.

## 14. Attribution Participation Review

Validation scope:

- attribution participation
- attribution consumption
- attribution lineage

Result: PASS

Attribution participation is consumption-only:

- Coordinator consumes attribution outcomes.
- Coordinator does not define attribution truth.
- Attribution lineage remains tied to governed attribution authorities.

## 15. Event History Participation Review

Validation scope:

- event-history participation
- event-history lineage
- historical traceability

Result: PASS

Event-history participation remains bounded to authoritative event-history outputs with explicit historical traceability preserved.

## 16. Identity / Room / Occupancy Review

Validation scope:

- identity participation
- room participation
- occupancy participation

Result: PASS

Identity, room, and occupancy participation remain bounded to governed outputs without ownership transfer.

## 17. Fallback Explanation Review

Validation scope:

- fallback participation
- fallback consumption
- fallback lineage

Result: PASS

Fallback explanation participation is consumption-only:

- Coordinator consumes fallback outcomes.
- Coordinator does not define fallback policy.
- Fallback lineage remains tied to governed explainability/diagnostics/identity/occupancy boundaries.

## 18. Privacy Boundary Review

Validation scope:

- privacy participation
- visibility participation
- privacy lineage

Result: PASS

Privacy and visibility participation remain bounded to governed privacy boundaries with explicit privacy lineage preserved.

## 19. Household-Facing Explanation Review

Validation scope:

- explanation participation
- provenance explanations
- attribution explanations
- historical explanations

Result: PASS

Household-facing explanations consume governed provenance, attribution, and historical explanation references with no alternate explanation authority created.

## 20. Explainability Traceability Review

Validation scope:

- explanation traceability
- provenance traceability
- memory traceability
- diagnostics traceability

Result: PASS

Traceability is preserved across explanation, provenance, memory, and diagnostics participation with explicit lineage anchors.

## 21. Explanation Lineage Architecture

Validation scope:

- memory inputs
- provenance inputs
- attribution inputs
- event-history inputs
- diagnostics inputs
- occupancy inputs
- room inputs
- identity inputs

Result: PASS

Lineage architecture:

- memory-input lineage remains tied to HTBW-governed household-memory outputs.
- provenance-input lineage remains tied to HTBW-governed provenance outputs.
- attribution-input lineage remains tied to HTBW-governed attribution outputs.
- event-history-input lineage remains tied to authoritative event-history outputs.
- diagnostics-input lineage remains tied to externally governed diagnostics outputs.
- occupancy-input lineage remains tied to HTBW/Foundation-governed occupancy outputs.
- room-input lineage remains tied to HTBW/Foundation-governed room outputs.
- identity-input lineage remains tied to HTBW/Voice Identity-governed identity outputs.

## 22. Deterministic Explanation Planning Review

Validation scope:

- explanation participation
- provenance participation
- attribution participation
- historical participation

Result: PASS

Deterministic requirements:

- same governed memory/provenance/attribution/event-history/diagnostics/occupancy/room/identity inputs produce the same explanation-planning participation outcomes.
- explanation, provenance, attribution, and historical participation remain deterministic and traceable.

## 23. Diagnostics Integration Review

Validation scope:

- diagnostics participation
- troubleshooting participation
- traceability participation

Result: PASS

Diagnostics integration remains bounded to consumed diagnostics and troubleshooting outcomes with explicit traceability participation preserved.

## 24. HM9 Readiness Review

Validation scope:

- future HM9 Household Memory Diagnostics Surface support

Result: PASS

Lineage sufficiency for HM9 is preserved through explicit explanation/provenance/memory/diagnostics traceability anchors.

## 25. Ownership Validation

Validation scope:

Coordinator does not own:

- explainability governance
- diagnostics governance
- provenance governance
- attribution governance
- event-history governance
- memory governance

Result: PASS

Coordinator consumes governed outcomes and owns none of the listed governance domains.

## 26. Ownership Drift Analysis

Validation scope:

No transfer of:

- provenance ownership
- attribution ownership
- event-history ownership
- memory ownership
- diagnostics ownership
- explainability ownership

Result: PASS

No ownership drift identified.

## 27. Downstream Guidance

Provide constraints only. Do not pre-design future issues.

- HM8 Privacy, Retention, and Guest-Safe Memory Boundaries: preserve HTBW privacy/retention/guest-safe governance across household explainability surfaces.
- HM9 Household Memory Diagnostics Surface: preserve deterministic explanation/provenance/memory/diagnostics traceability anchors; diagnostics governance remains external.
- HM10 Household Memory Readiness Review: validate HM1-HM9 completeness, ownership preservation, determinism, and supportability readiness.

## 28. HM7 Baseline Determination

Result: PASS

Explanation planning is sufficiently documented for downstream E10 work.

## 29. Explainability Constraint Validation

Validation scope:

- Concierge explains governed history
- Concierge consumes memory context
- Concierge does not create causality truth
- Historical truth remains authoritative
- Provenance remains authoritative

Result: PASS

Explainability constraints are satisfied without governance transfer.

## 30. Final Determination

E10-HM7 WHY DID THIS HAPPEN EXPLANATION PLANNING

APPROVED AS THE AUTHORITATIVE BASELINE

FOR HOUSEHOLD EXPLAINABILITY CONSUMPTION
