# Restoration Candidate Resolution Pipeline

## 1. Purpose

Define the authoritative E8-ER2 architecture baseline for how Coordinator consumes and resolves restoration candidates using governed restoration context.

This document is architecture and governance only.

This document does not implement restoration behavior, restoration selection algorithms, restoration prioritization, restoration suppression, restoration execution, restoration diagnostics, or restoration explainability.

## 2. Scope Reviewed

Reviewed authorities and governance inputs:

- HTBW #20
- HTBW #32
- HTBW #47
- HTBW #39
- HTBW #50
- ER1 Restoration Consumption Architecture
- CA1 through CA10

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#39 and #50) are execution inputs and are not architecture authority.

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
- Restoration confidence remains HTBW-governed.
- Restoration prioritization remains HTBW-governed.
- Coordinator consumes restoration candidates.
- Coordinator resolves restoration candidates as consumption behavior only.
- Coordinator does not create restoration candidates.
- Coordinator does not define restoration candidates, restoration eligibility, restoration confidence, or restoration prioritization.

## 4. ER1 Architecture Alignment Review

Validation scope:

- ER1 ownership boundaries
- ER1 lifecycle boundaries
- ER1 consumption boundaries
- ER1 governance constraints

Result: PASS

ER2 aligns with ER1 baseline, ownership boundaries, lifecycle boundaries, and governance hardening constraints.

## 5. Restoration Candidate Resolution Pipeline

Validation scope:

- candidate acquisition
- candidate consumption
- candidate evaluation
- candidate filtering
- candidate resolution
- candidate handoff

Result: PASS

Pipeline architecture:

- candidate acquisition: Coordinator acquires governed candidates through restoration context inputs under HTBW #47.
- candidate consumption: Coordinator consumes candidate sets and candidate metadata without ownership transfer.
- candidate evaluation: Coordinator evaluates candidate participation against governed context references and boundaries.
- candidate filtering: Coordinator applies consumption-time bounded filtering surfaces informed by governed context.
- candidate resolution: Coordinator resolves candidate sets into bounded candidate-resolution outputs.
- candidate handoff: Coordinator hands resolved candidate outputs to downstream restoration consumption stages.

This section defines architecture only.

## 6. Candidate Lineage Architecture

Validation scope:

- restoration definition source
- restoration context source
- candidate source
- continuity influences
- affinity influences
- occupancy influences

Result: PASS

Lineage architecture requirements:

- restoration definition source lineage references must be retained from HTBW #32 authority inputs.
- restoration context source lineage references must be retained from HTBW #47 context inputs.
- candidate source lineage references must remain traceable from consumed restoration context.
- continuity influence lineage must remain traceable via CA2 and CA4 participation references.
- affinity influence lineage must remain traceable via CA3 and CA5 participation references.
- occupancy influence lineage must remain traceable via occupancy and confidence references in governed context.

Lineage is sufficient to support ER8 explainability and ER9 diagnostics without redefining governance.

## 7. Continuity Influence Validation

Validation scope:

- continuity participates in candidate resolution
- continuity ownership preserved
- continuity lineage preserved

Result: PASS

Continuity participates as governed input for candidate resolution. Continuity ownership and lineage remain external and preserved.

## 8. Affinity Influence Validation

Validation scope:

- affinity participates in candidate resolution
- affinity ownership preserved
- affinity lineage preserved

Result: PASS

Affinity participates as governed input for candidate resolution. Affinity ownership and lineage remain external and preserved.

## 9. Occupancy Influence Validation

Validation scope:

- occupancy participates in candidate resolution
- occupancy ownership preserved
- occupancy lineage preserved

Result: PASS

Occupancy participates as governed input for candidate resolution. Occupancy ownership and lineage remain external and preserved.

## 10. Candidate Resolution Boundaries

Validation scope:

Coordinator MAY:

- consume candidate inputs
- resolve candidate sets
- produce candidate-resolution outputs

Coordinator MAY NOT:

- define restoration governance
- define restoration eligibility
- define restoration confidence
- define restoration prioritization
- create restoration categories

Result: PASS

All candidate-resolution boundaries remain ownership-preserving and authority-aligned.

## 11. Explainability Readiness Review

Validation scope:

- future ER8 Explainability support
- lineage availability

Result: PASS

Candidate-resolution lineage and influence references are sufficiently defined for ER8 explainability consumption.

## 12. Diagnostics Readiness Review

Validation scope:

- future ER9 Diagnostics support
- traceability availability

Result: PASS

Candidate-resolution lineage and traceability references are sufficiently defined for ER9 diagnostics consumption.

## 13. Ownership Validation

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

Coordinator consumes all listed domains and owns none of them.

## 14. Ownership Drift Analysis

Validation scope:

No transfer of:

- restoration governance
- restoration definitions
- restoration categories
- restoration eligibility
- restoration confidence
- restoration prioritization

Result: PASS

No ownership drift identified.

## 15. Downstream Guidance

Provide constraints only. Do not pre-design ER3 through ER10.

- ER3: consume room-aware candidate-resolution context using CA4 and CA5 boundaries without ownership transfer.
- ER4: consume person-aware candidate-resolution context using governed continuity and affinity references without ownership transfer.
- ER5: consume guest and unknown constraints using CA6 boundaries and HTBW guest-safe policy boundaries.
- ER6: conflict-policy work must preserve HTBW ownership and expose conflict visibility lineage only.
- ER7: suppression and prioritization work must consume HTBW policy boundaries and preserve ownership.
- ER8: explainability framework must consume candidate-resolution lineage and authority references from ER2 outputs.
- ER9: diagnostics framework must consume candidate-resolution traceability and lineage references from ER2 outputs.
- ER10: readiness review must validate ownership preservation, lineage completeness, explainability readiness, diagnostics readiness, and no drift across ER3 through ER9.

## 16. ER2 Baseline Determination

Result: PASS

ER2 candidate-resolution architecture is sufficiently documented for downstream E8 restoration-consumption work.

## 17. Final Determination

E8-ER2 RESTORATION CANDIDATE RESOLUTION PIPELINE

APPROVED AS THE AUTHORITATIVE BASELINE

FOR RESTORATION CANDIDATE RESOLUTION
