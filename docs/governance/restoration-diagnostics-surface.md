# Restoration Diagnostics Surface

## 1. Purpose

Define the authoritative E8-ER9 architecture baseline for restoration diagnostics as consumption architecture.

This document is architecture and governance only.

This document does not implement diagnostics code, troubleshooting code, trace collection, explainability generation, restoration behavior, suppression behavior, or prioritization behavior.

Diagnostics surfaces consumed information.

Diagnostics does not become a source of truth.

## 2. Scope Reviewed

Reviewed authorities and governance inputs:

- HTBW #40
- HTBW #47
- HTBW #50
- Concierge #109
- ER3 Room-Aware Restoration Consumption
- ER4 Person-Aware Restoration Consumption
- ER5 Guest and Unknown Restoration Consumption
- ER6 Multi-Occupant Restoration Conflict Policy
- ER7 Restoration Suppression and Prioritization Framework
- ER8 Restoration Explainability Framework
- CA9 Continuity and Affinity Diagnostics Surface

Associated authority artifacts reviewed for alignment:

- HTBW Experience Restoration Contract
- HTBW Experience Restoration Context Model
- HTBW Occupancy and Presence Contract
- HTBW Occupancy and Presence Model
- HTBW HACS and Platinum Contract Compliance Checklist
- Experience Diagnostics Framework

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#40, #47, #50, #109, #119) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between ER9 outputs and authoritative contracts/models/governance baselines.

## 3. Restoration Authority Validation

Validation scope:

- restoration ownership
- restoration governance
- restoration policy ownership
- restoration eligibility ownership
- restoration confidence ownership

Result: PASS

Validated statements:

- Restoration ownership remains in HTBW.
- Restoration governance remains in HTBW.
- Restoration policy ownership remains in HTBW.
- Restoration eligibility ownership remains in HTBW.
- Restoration confidence ownership remains in HTBW.
- Coordinator consumes restoration lineage, traces, outcomes, and candidates.
- Coordinator owns none of the above.

## 4. Diagnostics Governance Validation

Validation scope:

- diagnostics authority
- diagnostics ownership
- diagnostics governance boundaries

Result: PASS

Validated statements:

- Diagnostics authority remains externally governed by HTBW-aligned diagnostics authorities.
- Coordinator diagnostics role is bounded to surfacing consumed diagnostics traces, lineage, and troubleshooting information.
- Coordinator does not create diagnostics governance.
- Coordinator does not create diagnostics truth.

## 5. CA9 Diagnostics Alignment Review

Validation scope:

- continuity diagnostics alignment
- affinity diagnostics alignment
- existing diagnostics architecture alignment

Result: PASS

Alignment statements:

- ER9 follows CA9 diagnostics categories and bounded-trace patterns.
- ER9 preserves continuity and affinity traces as consumed observational evidence.
- ER9 aligns with existing diagnostics architecture without redefining diagnostics ownership.
- Coordinator surfaces diagnostics and lineage.
- Coordinator does not diagnose authority truth.

## 6. ER3 Trace Validation

Validation scope:

- room traces
- room context traces
- room-default traces

Result: PASS

ER9 consumes ER3 room lineage and room-context traceability, including room-default trace references and room-restoration trace references.

## 7. ER4 Trace Validation

Validation scope:

- continuity traces
- affinity traces
- identity confidence traces

Result: PASS

ER9 consumes ER4 person-aware traceability and preserves continuity, affinity, and identity-confidence trace references.

## 8. ER5 Trace Validation

Validation scope:

- guest traces
- unknown occupant traces
- fallback traces

Result: PASS

ER9 consumes ER5 guest and unknown-occupant traceability and preserves fallback and privacy-safe trace references.

## 9. ER6 Trace Validation

Validation scope:

- conflict traces
- shared-room traces
- suppression-participation traces

Result: PASS

ER9 consumes ER6 conflict/shared-room/suppression-participation traceability and preserves these as diagnostics evidence references.

## 10. ER7 Trace Validation

Validation scope:

- suppression traces
- prioritization traces
- deferment traces

Result: PASS

ER9 consumes ER7 suppression, prioritization, and deferment traceability including restoration-avoidance trace references.

## 11. ER8 Explainability Alignment Review

Validation scope:

- machine-readable explainability references
- human-readable explainability references
- lineage alignment

Result: PASS

ER9 consumes ER8 machine-readable and human-readable explainability references and shares lineage alignment for diagnostics evidence.

ER9 does not redefine explainability architecture.

## 12. Restoration Candidate Diagnostics

Validation scope:

- candidate traces
- candidate evaluation traces
- candidate lineage references
- candidate troubleshooting workflow

Result: PASS

Architecture-only candidate diagnostics:

- candidate traces: bounded references for candidate acquisition and participation.
- candidate evaluation traces: bounded references for candidate evaluation participation surfaces.
- candidate lineage references: bounded lineage pointers to consumed restoration context.
- candidate troubleshooting workflow: trace review -> evidence review -> lineage review -> outcome understanding.

## 13. Restoration Eligibility Diagnostics

Validation scope:

- eligibility traces
- eligibility participation references
- eligibility troubleshooting workflow

Result: PASS

Architecture-only eligibility diagnostics:

- eligibility traces preserve consumed eligibility outcomes.
- eligibility participation references preserve bounded eligibility participation lineage.
- eligibility troubleshooting workflow remains deterministic and ownership-safe.

## 14. Continuity and Affinity Diagnostics

Validation scope:

- continuity traces
- affinity traces
- continuity troubleshooting workflow
- affinity troubleshooting workflow

Result: PASS

Architecture-only continuity and affinity diagnostics:

- continuity traces are consumed from governed continuity outputs.
- affinity traces are consumed from governed affinity outputs.
- continuity troubleshooting workflow preserves bounded evidence review.
- affinity troubleshooting workflow preserves bounded evidence review.

## 15. Occupancy and Confidence Diagnostics

Validation scope:

- occupancy traces
- occupancy-confidence traces
- identity-confidence traces
- troubleshooting workflow

Result: PASS

Architecture-only occupancy and confidence diagnostics:

- occupancy traces preserve consumed occupancy participation evidence.
- occupancy-confidence traces preserve consumed confidence-gate evidence.
- identity-confidence traces preserve consumed identity-confidence evidence.
- troubleshooting workflow remains bounded to consumed references.

## 16. Suppression and Fallback Diagnostics

Validation scope:

- suppression traces
- fallback traces
- deferment traces
- troubleshooting workflow

Result: PASS

Architecture-only suppression and fallback diagnostics:

- suppression traces preserve consumed suppression outcomes and participation.
- fallback traces preserve room-default, guest-safe, and unknown-occupant fallback evidence.
- deferment traces preserve prioritization and higher-priority participation evidence.
- troubleshooting workflow preserves bounded trace-to-outcome understanding.

## 17. Diagnostics Categories Review

Validation scope:

- restoration candidate traces
- restoration eligibility traces
- continuity traces
- affinity traces
- occupancy traces
- confidence traces
- suppression traces
- fallback traces

Result: PASS

Diagnostics categories are explicitly documented as bounded observational categories and are sufficient for restoration supportability.

## 18. Troubleshooting Workflow Review

Validation scope:

- restoration applied
- restoration suppressed
- restoration deferred
- restoration unavailable
- fallback behavior
- confidence failures

Result: PASS

Deterministic troubleshooting workflow:

1. identify restoration outcome category
2. review candidate and eligibility traces
3. review continuity, affinity, occupancy, and confidence traces
4. review suppression, deferment, and fallback traces as applicable
5. review explainability references for outcome rationale alignment
6. produce bounded outcome understanding without changing governance truth

## 19. HACS / Platinum Supportability Review

Validation scope:

- HACS requirements supportability
- Home Assistant integration supportability
- Platinum-quality troubleshooting expectations

Result: PASS

Supportability statements:

- Diagnostics categories and troubleshooting workflow provide supportability guidance aligned with HACS expectations.
- Diagnostics traces and bounded evidence references support Home Assistant integration troubleshooting surfaces.
- Deterministic troubleshooting path and ownership-safe diagnostics coverage align with Platinum-quality supportability expectations.

Architecture only.

## 20. Diagnostics Consistency Review

Validation scope:

- deterministic
- traceable
- ownership-safe
- authority-aligned

Result: PASS

Validated statements:

- Diagnostics are deterministic for the same governed consumed inputs.
- Diagnostics are traceable through bounded lineage and trace references.
- Diagnostics remain ownership-safe and do not create Coordinator-owned governance.
- Diagnostics remain authority-aligned with contracts, models, and prior governance baselines.

## 21. Ownership Validation

Validation scope:

Coordinator does not own:

- restoration governance
- restoration policy
- restoration eligibility
- suppression policy
- prioritization policy
- diagnostics truth

Result: PASS

Coordinator surfaces diagnostics for consumed outcomes and consumed lineage.

Coordinator owns none of the listed domains.

## 22. Ownership Drift Analysis

Validation scope:

No transfer of:

- restoration governance
- suppression governance
- prioritization governance
- diagnostics governance
- restoration definitions

Result: PASS

No ownership drift identified.

## 23. Downstream Guidance

Provide constraints only. Do not pre-design ER10 implementation.

- ER10 Readiness Review must validate ER9 diagnostics category coverage, deterministic troubleshooting workflow coverage, ER3 through ER8 trace/explainability alignment, HACS and Platinum supportability coverage, ownership preservation, and authority alignment.

## 24. ER9 Baseline Determination

Result: PASS

Restoration diagnostics are sufficiently documented as consumption architecture for downstream E8 governance work.

## 25. Final Determination

E8-ER9 RESTORATION DIAGNOSTICS SURFACE

APPROVED AS THE AUTHORITATIVE BASELINE

FOR RESTORATION DIAGNOSTICS
