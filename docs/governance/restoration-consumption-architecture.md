# Restoration Consumption Architecture

## 1. Purpose

Define the authoritative E8-ER1 architecture baseline for how Coordinator consumes Experience Restoration context governed by HTBW.

This document is architecture and governance only.

This document does not implement restoration behavior, restoration resolution, restoration prioritization, restoration suppression, restoration diagnostics, restoration explainability, or restoration candidates.

## 2. Scope Reviewed

Reviewed authorities and governance inputs:

- HTBW #20
- HTBW #32
- HTBW #47
- HTBW #39
- HTBW #50
- Concierge #101
- Concierge #108
- Concierge #110
- E7 CA1 through CA10
- E6 EX1 through EX11, including EX10 readiness outputs and EX10 addendum handling captured by E7 readiness and EX11 significance grounding

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#39, #50, #101, #108, #110) are execution inputs and are not architecture authority.

## 3. Restoration Authority Validation

Validation scope:

- restoration ownership
- restoration governance
- restoration contract ownership
- restoration model ownership
- restoration category ownership
- restoration eligibility ownership
- restoration confidence ownership
- restoration prioritization ownership

Result: PASS

Validated statements:

- Restoration ownership remains in HTBW.
- Restoration governance remains in HTBW.
- HTBW #32 remains the restoration contract authority.
- HTBW #47 remains the restoration context model authority.
- Restoration categories remain HTBW-governed.
- Restoration eligibility remains HTBW-governed.
- Restoration confidence governance remains HTBW-governed.
- Restoration prioritization governance remains HTBW-governed.
- Coordinator consumes restoration definitions, restoration context, restoration candidates, restoration metadata, and restoration outcomes.
- Coordinator owns none of the above.

## 4. E7 Consumption Foundation Validation

Validation scope:

- continuity consumption architecture
- affinity consumption architecture
- explainability architecture
- diagnostics architecture
- readiness architecture

Result: PASS

CA1 through CA10 provide validated continuity, affinity, room-aware, guest-aware, explainability, diagnostics, influence, and readiness baselines required by E8 restoration consumption planning.

## 5. Coordinator Consumption Architecture

Validation scope:

- restoration inputs
- restoration outputs
- restoration consumption lifecycle
- restoration orchestration responsibilities
- restoration execution responsibilities

Result: PASS

Coordinator restoration consumption architecture:

- Inputs consumed by Coordinator:
  - restoration policy and category authority from HTBW #32
  - restoration context representation authority from HTBW #47
  - continuity inputs from CA2
  - affinity inputs from CA3
  - room-aware inputs from CA4 and CA5
  - guest and unknown constraints from CA6
  - occupancy and confidence gate inputs under HTBW authorities
- Outputs produced by Coordinator:
  - consumed restoration decision context for downstream orchestration
  - explainability references aligned to CA7
  - diagnostics references aligned to CA9
- Lifecycle (consumption-only):
  - governed context acquisition -> context resolution -> eligibility consumption -> candidate availability consumption -> bounded orchestration selection -> execution handoff -> completion state visibility
- Responsibilities:
  - Coordinator orchestrates and consumes.
  - Coordinator does not redefine restoration governance, contracts, models, categories, eligibility, confidence, or prioritization.
- Execution boundary:
  - restoration governance is not execution authority.
  - execution remains outside restoration governance ownership.

## 6. Restoration Context Consumption Review

Validation scope:

- restoration context acquisition
- restoration context lineage
- restoration context consumption
- restoration context traceability

Result: PASS

Validated statements:

- Coordinator acquires governed restoration context as an external input.
- Context lineage is preserved through continuity, affinity, occupancy, confidence, and policy references.
- Context is consumed for orchestration decisions only.
- Traceability requirements align with CA7 and CA9.

## 7. Continuity Relationship Validation

Validation scope:

- continuity influence on restoration
- continuity consumption relationship
- ownership preservation

Result: PASS

Validated statements:

- Continuity influences restoration candidate participation and eligibility consumption.
- Coordinator consumes continuity context and does not own continuity.
- Continuity governance and model authority remain external to Coordinator.

## 8. Affinity Relationship Validation

Validation scope:

- affinity influence on restoration
- affinity consumption relationship
- ownership preservation

Result: PASS

Validated statements:

- Affinity influences restoration preference participation and conflict visibility.
- Coordinator consumes affinity context and does not own affinity.
- Affinity governance and model authority remain external to Coordinator.

## 9. Occupancy Relationship Validation

Validation scope:

- occupancy influence on restoration
- occupancy consumption relationship
- ownership preservation

Result: PASS

Validated statements:

- Occupancy and confidence influence restoration eligibility consumption boundaries.
- Coordinator consumes occupancy context and confidence references.
- Occupancy truth and confidence authority remain external to Coordinator.

## 10. Restoration Lifecycle Architecture

Validation scope:

- restoration availability
- restoration candidate availability
- restoration selection consumption
- restoration execution
- restoration completion

Result: PASS

Lifecycle architecture baseline:

- Restoration availability is governed and externally defined.
- Candidate availability is consumed from governed restoration context.
- Selection is consumption-based orchestration, not governance redefinition.
- Execution is handed off through orchestration boundaries; governance remains external.
- Completion is represented with traceable restoration outcome references.

## 11. Ownership Validation

Validation scope:

Coordinator does not own:

- restoration
- continuity
- affinity
- significance
- relevance
- environmental evaluation
- priority context

Result: PASS

Coordinator consumes governed outputs and owns none of the listed governance domains.

## 12. Restoration Ownership Drift Analysis

Validation scope:

No architecture transfers:

- restoration governance
- restoration definitions
- restoration categories
- restoration eligibility
- restoration confidence
- restoration prioritization

Result: PASS

No ownership drift identified.

## 13. Authority Alignment Analysis

Validation scope:

- HTBW #20
- HTBW #32
- HTBW #47

Result: PASS

Alignment notes:

- HTBW #32 and HTBW #47 remain direct restoration authorities.
- HTBW #20 is treated consistently with existing readiness grounding and does not transfer restoration governance ownership into Coordinator.
- Coordinator remains consumer and orchestrator under ADR authority boundaries.

## 14. Downstream E8 Architecture Guidance

Provide constraints only. Do not pre-design ER2 through ER10.

- ER2: must consume HTBW-governed restoration candidate context without redefining candidate governance.
- ER3: must preserve room-aware restoration consumption boundaries from CA4 and CA5.
- ER4: must preserve person-aware restoration consumption boundaries using governed continuity and affinity inputs.
- ER5: must preserve guest and unknown safeguards from CA6 and HTBW restoration policy boundaries.
- ER6: must preserve conflict visibility and ownership boundaries; no conflict policy ownership transfer into Coordinator.
- ER7: suppression and prioritization must consume HTBW policy boundaries; no Coordinator policy ownership.
- ER8: explainability must preserve lineage and governance references per CA7.
- ER9: diagnostics must preserve trace lineage and governance boundaries per CA9.
- ER10: readiness must validate ownership preservation, authority alignment, and no drift across ER2 through ER9.

## 15. E8 Baseline Architecture Determination

Determine whether ER1 provides sufficient foundation for:

- restoration resolution
- room-aware restoration
- person-aware restoration
- guest restoration
- conflict handling
- suppression
- prioritization
- explainability
- diagnostics
- readiness validation

Result: PASS

ER1 establishes sufficient authority-aligned architecture and ownership boundaries for all downstream E8 restoration-consumption issues.

## 16. Final Determination

E8-ER1 RESTORATION CONSUMPTION ARCHITECTURE

APPROVED AS THE AUTHORITATIVE BASELINE

FOR E8 EXPERIENCE RESTORATION CONSUMPTION

## 17. Governance Hardening Review

### Terminology Consistency Review

Result: PASS

Validated canonical terminology in ER1:

- restoration definitions
- restoration context
- restoration candidates
- restoration metadata
- restoration outcomes

Additional restoration terminology present in ER1 and authority support status:

- restoration policy: supported by HTBW #32
- restoration eligibility: supported by HTBW #32
- restoration confidence: supported by HTBW #32 and HTBW #47 confidence references
- restoration prioritization: supported by HTBW #32 governance scope and E7 CA10 ownership validation
- restoration suppression: supported by HTBW #32 and HTBW #47 optional metadata
- restoration conflict visibility: supported by HTBW #32 multi-person conflict behavior and HTBW #47 conflict indicator

No competing restoration terminology was identified in ER1 that conflicts with HTBW #32, HTBW #47, or E7 CA1 through CA10.

### Restoration Lineage Readiness Review

Result: PASS

ER1 and consumed E7 authorities provide sufficient lineage readiness for ER8 and ER9.

Lineage readiness validation:

- source restoration definition traceability: present through HTBW #32 references in ER1
- source restoration context traceability: present through HTBW #47 references in ER1
- source candidate selection traceability: present through ER1 lifecycle and selection-consumption boundaries
- continuity influence traceability: present through ER1 Section 7 and E7 CA2/CA4/CA7/CA9 lineage hooks
- affinity influence traceability: present through ER1 Section 8 and E7 CA3/CA5/CA7/CA9 lineage hooks
- occupancy influence traceability: present through ER1 Section 9 and HTBW restoration confidence and occupancy gating references

No lineage-readiness gap was identified that would block ER8 explainability or ER9 diagnostics.

### Multi-Occupant Ownership Drift Protection Review

Result: PASS

Validated that ER1 does not transfer ownership into Coordinator for:

- restoration prioritization
- restoration suppression
- restoration conflict arbitration
- restoration eligibility

Validated constraints for downstream issues:

- ER6 remains constrained to conflict visibility and ownership-preserving consumption boundaries.
- ER7 remains constrained to suppression and prioritization consumption under HTBW policy ownership.

No ownership drift was identified.

### Final Hardening Determination

Result: PASS

ER1 GOVERNANCE HARDENING REVIEW

PASS

NO FURTHER ER1 WORK REQUIRED

READY TO CLOSE ISSUE #111
