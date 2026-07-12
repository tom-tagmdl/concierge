# Room-Aware Restoration Consumption

## 1. Purpose

Define the authoritative E8-ER3 architecture baseline for how Coordinator consumes restoration context in a room-aware manner.

This document is architecture and governance only.

This document does not implement restoration behavior, restoration execution, restoration prioritization, restoration suppression, restoration diagnostics, or restoration explainability.

## 2. Scope Reviewed

Reviewed authorities and governance inputs:

- HTBW #20
- HTBW #32
- HTBW #47
- HTBW #50
- Concierge #104
- Concierge #105
- ER1 Restoration Consumption Architecture
- ER2 Restoration Candidate Resolution Pipeline

Authority-order treatment:

- ADRs, contracts, and models remain architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#20, #50, #104, #105) are execution inputs and are not architecture authority.

## 3. Restoration Authority Validation

Validation scope:

- restoration ownership
- restoration governance
- restoration contract ownership
- restoration model ownership
- restoration eligibility ownership
- restoration confidence ownership
- restoration prioritization ownership

Result: PASS

Validated statements:

- Restoration ownership remains in HTBW.
- Restoration governance remains in HTBW.
- HTBW #32 remains restoration contract authority.
- HTBW #47 remains restoration context model authority.
- Restoration eligibility remains HTBW-governed.
- Restoration confidence remains HTBW-governed.
- Restoration prioritization remains HTBW-governed.
- Coordinator consumes restoration context, restoration candidates, and room context.
- Coordinator does not define room restoration governance, room restoration eligibility, or room restoration confidence.

## 4. ER1 Architecture Alignment Review

Validation scope:

- ownership boundaries
- lifecycle boundaries
- restoration consumption boundaries

Result: PASS

ER3 conforms to ER1 ownership boundaries, lifecycle boundaries, room-related constraints, and governance hardening outcomes.

## 5. ER2 Architecture Alignment Review

Validation scope:

- candidate lineage
- candidate consumption
- candidate resolution architecture

Result: PASS

ER3 consumes ER2 candidate lineage and candidate-resolution outputs and does not redefine ER2 architecture.

## 6. Room-Aware Restoration Architecture

Validation scope:

- current room restoration
- previous room restoration
- room transition restoration
- room default restoration
- room-scoped restoration behavior

Result: PASS

Architecture-only room-aware restoration consumption:

- current room restoration: consumes governed current-room context for restoration candidate participation.
- previous room restoration: consumes governed previous-room context for restoration candidate participation and fallback context.
- room transition restoration: consumes governed transition context linking previous and current room participation.
- room default restoration: consumes governed room-default restoration context from HTBW contract authority.
- room-scoped restoration behavior: consumes room-scoped constraints and room references as bounded inputs to restoration consumption.

## 7. Deterministic Room Behavior Review

Validation scope:

- current room context
- previous room context
- room transition events
- room defaults
- room restoration expectations

Result: PASS

Deterministic expectations:

- same governed room inputs produce same room-aware restoration consumption outcomes.
- current-room and previous-room references are consumed through fixed bounded participation surfaces.
- room transition events are consumed as governed transition context, not hidden inference.
- room defaults are consumed through governed room-default policy boundaries.
- household-facing room-aware restoration expectations remain deterministic and explainable.

## 8. Room Context Lineage Architecture

Validation scope:

- room source
- room determination
- room context consumption
- room transition consumption

Result: PASS

Lineage architecture requirements:

- room source lineage remains tied to governed room truth authority.
- room determination lineage remains explicit and traceable from consumed room references.
- room context consumption lineage remains traceable through candidate consumption and resolution stages.
- room transition consumption lineage remains traceable through previous-room to current-room transition references.

Lineage support is sufficient for future explainability and diagnostics.

## 9. Room Constraint Architecture

Validation scope:

- room-specific constraints
- room-default constraints
- restoration consumption boundaries

Result: PASS

Constraint architecture:

- room-specific constraints are consumed as governed external constraints.
- room-default constraints are consumed under HTBW #32 room default restoration governance.
- restoration consumption boundaries remain consumption-only and ownership-preserving.

Coordinator consumes constraints and does not define constraints.

## 10. Explainability Path Review

Validation scope:

- current room selection path
- previous room selection path
- room transition decision path
- room default decision path

Result: PASS

Explainability path availability:

- current-room participation references are available.
- previous-room participation references are available.
- transition participation references are available.
- room-default participation references are available.

ER3 preserves room-aware explainability path requirements for ER8.

## 11. Diagnostics Readiness Review

Validation scope:

- room context source traceability
- room context change traceability
- room restoration decision traceability
- restoration candidate consumption traceability

Result: PASS

ER3 preserves room-aware traceability requirements for ER9 diagnostics.

## 12. Continuity Integration Validation

Validation scope:

- continuity influences room-aware restoration
- continuity ownership preserved
- continuity lineage preserved

Result: PASS

Continuity influences room-aware restoration consumption through CA2 and CA4 participation boundaries with ownership and lineage preserved.

## 13. Affinity Integration Validation

Validation scope:

- affinity influences room-aware restoration
- affinity ownership preserved
- affinity lineage preserved

Result: PASS

Affinity influences room-aware restoration consumption through CA3 and CA5 participation boundaries with ownership and lineage preserved.

## 14. Occupancy Integration Validation

Validation scope:

- occupancy influences room-aware restoration
- occupancy ownership preserved
- occupancy lineage preserved

Result: PASS

Occupancy influences room-aware restoration consumption through governed occupancy references with ownership and lineage preserved.

## 15. Ownership Validation

Validation scope:

Coordinator does not own:

- restoration
- room truth
- continuity
- affinity
- significance
- relevance
- environmental evaluation
- priority context

Result: PASS

Coordinator consumes all listed domains and owns none of them.

## 16. Ownership Drift Analysis

Validation scope:

No transfer of:

- restoration governance
- restoration definitions
- restoration eligibility
- restoration confidence
- restoration prioritization
- room truth ownership

Result: PASS

No ownership drift identified.

## 17. Downstream Guidance

Provide constraints only. Do not pre-design ER4 through ER10.

- ER4: person-aware restoration must consume ER3 room-aware lineage and room-scoped boundaries without ownership transfer.
- ER5: guest and unknown handling must consume ER3 room-aware context together with guest-safe policy boundaries.
- ER6: conflict policy must preserve HTBW ownership while consuming room-aware continuity and affinity lineage references.
- ER7: suppression and prioritization must consume room-aware context under HTBW policy ownership boundaries.
- ER8: explainability must consume ER3 room-aware participation lineage for current room, previous room, transition, and room-default references.
- ER9: diagnostics must consume ER3 room-aware traceability for room source, room changes, and candidate-consumption paths.
- ER10: readiness must validate room-truth ownership preservation, deterministic room behavior, lineage completeness, and no ownership drift.

## 18. ER3 Baseline Determination

Result: PASS

Room-aware restoration consumption architecture is sufficiently documented for downstream E8 work.

## 19. Final Determination

E8-ER3 ROOM-AWARE RESTORATION CONSUMPTION

APPROVED AS THE AUTHORITATIVE BASELINE

FOR ROOM-AWARE RESTORATION CONSUMPTION
