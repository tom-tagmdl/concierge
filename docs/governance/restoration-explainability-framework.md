# Restoration Explainability Framework

## 1. Purpose

Define the authoritative E8-ER8 architecture baseline for restoration explainability as consumption architecture.

This document is architecture and governance only.

This document does not implement restoration behavior, explanation generation code, explainability services, diagnostics services, restoration execution, suppression behavior, or prioritization behavior.

Explainability describes consumed outcomes and consumed lineage.

Explainability does not create governance and does not create restoration truth.

## 2. Scope Reviewed

Reviewed authorities and governance inputs:

- HTBW #47
- HTBW #48
- HTBW #50
- Concierge #107
- ER3 Room-Aware Restoration Consumption
- ER4 Person-Aware Restoration Consumption
- ER5 Guest and Unknown Restoration Consumption
- ER6 Multi-Occupant Restoration Conflict Policy
- ER7 Restoration Suppression and Prioritization Framework

Associated authority artifacts reviewed for alignment:

- HTBW Experience Restoration Contract
- HTBW Experience Restoration Context Model
- HTBW Occupancy and Presence Contract
- HTBW Occupancy and Presence Model
- HTBW Provenance Contract
- HTBW Provenance Model
- CA7 Continuity and Affinity Explainability Framework
- Experience Explainability Framework

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- Issues (#47, #48, #50, #107, #118) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between ER8 outputs and authoritative contracts/models/governance baselines.

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
- Coordinator consumes restoration outcomes, restoration lineage, and restoration context.
- Coordinator owns none of the above.

## 4. Explainability Governance Validation

Validation scope:

- explainability ownership
- explainability authority
- explainability boundaries

Result: PASS

Validated statements:

- Explainability ownership remains externally governed through HTBW-aligned explainability authorities.
- Coordinator explainability authority is bounded to explaining consumed outcomes and consumed lineage.
- Explainability boundaries prevent Coordinator from creating restoration governance, restoration policy, restoration eligibility, suppression policy, or prioritization policy.
- Explainability does not become a source of truth.

## 5. CA7 Explainability Alignment Review

Validation scope:

- continuity explainability alignment
- affinity explainability alignment
- existing explainability architecture alignment

Result: PASS

Alignment statements:

- ER8 follows CA7 machine-readable and human-readable explanation surface patterns.
- ER8 preserves continuity and affinity lineage references as consumed evidence.
- ER8 aligns with existing explainability architecture in Concierge governance artifacts.
- Coordinator explains consumed outcomes and consumed lineage.
- Coordinator does not create continuity, affinity, or restoration truth.

## 6. ER3 Lineage Validation

Validation scope:

- room lineage
- room-default lineage
- room restoration lineage

Result: PASS

ER8 consumes room-aware lineage from ER3 and preserves room, room-default, and room-restoration explanation references.

## 7. ER4 Lineage Validation

Validation scope:

- continuity lineage
- affinity lineage
- identity confidence lineage

Result: PASS

ER8 consumes ER4 person-aware lineage and preserves continuity, affinity, and identity-confidence explanation references.

## 8. ER5 Lineage Validation

Validation scope:

- guest lineage
- unknown occupant lineage
- fallback lineage

Result: PASS

ER8 consumes ER5 guest-safe and unknown-occupant lineage and preserves fallback explanation references.

## 9. ER6 Lineage Validation

Validation scope:

- conflict lineage
- shared-room lineage
- suppression participation lineage

Result: PASS

ER8 consumes ER6 conflict/shared-room/suppression-participation lineage and preserves these as explainability evidence references.

## 10. ER7 Lineage Validation

Validation scope:

- suppression lineage
- prioritization lineage
- deferment lineage

Result: PASS

ER8 consumes ER7 suppression, prioritization, and deferment lineage and preserves traceable explanation references for restoration-avoidance outcomes.

## 11. Machine-Readable Explainability Framework

Validation scope:

- machine-readable restoration explanations
- machine-readable lineage structure
- machine-readable decision references
- machine-readable suppression references

Result: PASS

Architecture-only machine-readable framework:

- explanation_id
- restoration_outcome_reference
- restoration_candidate_references
- room_context_references
- continuity_references
- affinity_references
- identity_confidence_references
- guest_governance_references
- conflict_participation_references
- suppression_references
- prioritization_references
- deferment_references
- fallback_references
- lineage_references
- timestamp

Coordinator consumes and emits bounded structured references.

Coordinator does not define restoration policy or explainability governance.

## 12. Human-Readable Explainability Framework

Validation scope:

- human-readable restoration explanations
- human-readable suppression explanations
- human-readable fallback explanations
- human-readable room explanations
- human-readable person explanations

Result: PASS

Architecture-only human-readable framework:

- outcome summary
- restoration-applied rationale
- suppression rationale when applicable
- fallback rationale when applicable
- room-context rationale when applicable
- person-context rationale when applicable
- confidence visibility statement when applicable
- ownership-safe boundary statement

Human-readable outputs describe consumed outcomes and consumed lineage without redefining authority.

## 13. Restoration Applied Explanation Review

Validation scope:

- restoration applied
- restoration chosen
- restoration selected

Result: PASS

Applied/chosen/selected explanations preserve bounded references to consumed candidate lineage, room/person context lineage, and eligibility-participation lineage.

## 14. Restoration Suppressed Explanation Review

Validation scope:

- suppression outcomes
- suppression sources
- suppression participation

Result: PASS

Suppression explanations preserve bounded references to consumed suppression outcomes, suppression source references, and suppression participation lineage.

## 15. Restoration Deferred Explanation Review

Validation scope:

- deferment outcomes
- prioritization outcomes
- higher-priority experience participation

Result: PASS

Deferred explanations preserve bounded references to consumed deferment outcomes, prioritization outcomes, and higher-priority participation lineage.

## 16. Fallback Explanation Review

Validation scope:

- room defaults
- guest defaults
- unknown occupant defaults
- no-personalization defaults

Result: PASS

Fallback explanations preserve bounded references to room-default, guest-default, unknown-occupant-default, and no-personalization-default lineage.

## 17. Lineage Documentation Review

Validation scope:

- room context
- continuity
- affinity
- identity confidence
- guest governance
- conflict participation
- suppression participation
- prioritization participation

Result: PASS

Lineage support is explicitly documented across all listed dimensions as consumed references, with no transfer of ownership into Coordinator.

## 18. Explainability Consistency Review

Validation scope:

- deterministic
- traceable
- ownership-safe
- authority-aligned

Result: PASS

Validated statements:

- Explanations are deterministic for the same governed consumed inputs.
- Explanations are traceable through bounded lineage and reference paths.
- Explanations remain ownership-safe and do not create Coordinator-owned governance.
- Explanations remain authority-aligned with contracts, models, and prior governance baselines.

## 19. Diagnostics Integration Review

Validation scope:

- ER9 diagnostics support
- trace navigation
- root-cause visibility

Result: PASS

ER8 preserves explainability references required for ER9 diagnostics surface, trace navigation, and root-cause visibility without pre-designing ER9 implementation.

## 20. Ownership Validation

Validation scope:

Coordinator does not own:

- restoration
- restoration governance
- restoration policy
- restoration eligibility
- suppression policy
- prioritization policy

Result: PASS

Coordinator explains consumed outcomes and consumes governance outputs.

Coordinator owns none of the listed domains.

## 21. Ownership Drift Analysis

Validation scope:

No transfer of:

- restoration governance
- suppression governance
- prioritization governance
- explainability governance
- restoration definitions

Result: PASS

No ownership drift identified.

## 22. Downstream Guidance

Provide constraints only. Do not pre-design future issue implementations.

- ER9 Restoration Diagnostics Surface must consume ER8 machine-readable and human-readable references, lineage references, suppression/deferment/prioritization references, and fallback references as diagnostics evidence inputs.
- ER9 must preserve ownership boundaries and must not convert diagnostics into restoration-governance authority.
- ER10 Readiness Review must validate ER8 coverage for machine-readable explanations, human-readable explanations, lineage coverage, suppression/fallback/deferment explanation coverage, deterministic consistency, and ownership preservation.

## 23. ER8 Baseline Determination

Result: PASS

Restoration explainability is sufficiently documented as consumption architecture for downstream E8 governance work.

## 24. Final Determination

E8-ER8 RESTORATION EXPLAINABILITY FRAMEWORK

APPROVED AS THE AUTHORITATIVE BASELINE

FOR RESTORATION EXPLAINABILITY
