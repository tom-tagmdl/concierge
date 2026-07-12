# Multi-Item Capture Consumption

## 1. Purpose

Define the purpose of Multi-Item Capture Consumption.

This document establishes the authoritative E13-P6 architecture baseline for Concierge multi-item capture consumption.

This document is architecture and governance only.

This document does not define capture engines, task creation, shopping item creation, email creation, calendar creation, persistence logic, storage mechanisms, workflow automation, productivity experiences, reminder systems, or synchronization.

Concierge consumes, interprets, preserves, and routes governed multi-item productivity context from a single interaction.

## 2. Scope Reviewed

Documented review of mandatory authorities and dependencies:

- HTBW #47
- Concierge #139
- E13-P1 outputs

Reviewed associated governance authorities and readiness artifacts:

- docs/governance/household-productivity-experience-consumption-architecture.md
- docs/architecture/adr-coordinator-v2-governance.md
- docs/governance/coordinator-v2-foundation-summary.md
- docs/architecture/canonical-architecture.md
- docs/architecture/concierge-runtime-architecture.md
- docs/architecture/context-before-intent.md
- docs/architecture/identity-governance-reference.md
- docs/governance/provenance-consumption-architecture.md
- docs/governance/messaging-diagnostics-and-explainability-surface.md

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- GitHub issues (#47, #139, #165, #170) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between E13-P6 outputs and authoritative ADR/contract/model artifacts.

## 3. Capture Governance Validation

Validation scope:

- capture governance authority
- capture review authority
- capture consumption authority

Result: PASS

Validated statements:

- Capture governance authority remains in HTBW governance artifacts.
- Capture review authority remains in HTBW governance artifacts.
- Capture consumption authority remains in HTBW governance artifacts.
- Concierge consumes and routes captured productivity context.
- Concierge does not redefine capture governance.

## 4. Source-of-Record Validation

Validation scope:

- captured items remain externally owned
- Concierge remains a consumer/orchestrator

Result: PASS

Validated statements:

- Calendar providers remain systems of record.
- Email providers remain systems of record.
- Task providers remain systems of record.
- Shopping providers remain systems of record.
- Captured items remain externally owned.
- Concierge remains a consumer/orchestrator.

## 5. Multi-Item Capture Validation

Validation scope:

- multi-item capture behavior

Result: PASS

Validated statements:

- Concierge may capture multiple productivity items from a single interaction.
- Concierge does not become a productivity system of record.
- Concierge does not become a capture system of record.
- Concierge does not own captured records.
- Concierge identifies, separates, classifies, and routes governed productivity context.

## 6. Capture Bundling Review

Validation scope:

- bundled capture
- multi-item interactions
- bundled intake boundaries

Result: PASS

Bundled capture represents one interaction containing multiple productivity intents and context fragments.

Multi-item interactions are treated as governed intake bundles that must remain attributable to source interaction context.

Bundled intake boundaries prohibit hidden record ownership, hidden execution ownership, and hidden storage ownership.

## 7. Deterministic Splitting Review

Validation scope:

- item splitting rules
- deterministic classification rules
- routing boundaries

Result: PASS

Item splitting rules require stable, deterministic decomposition from one capture bundle into distinct routed item contexts.

Deterministic classification rules require consistent category assignment from the same normalized capture evidence.

Routing boundaries require routed outputs to remain consumer-only context handoff artifacts.

## 8. Productivity Item Classification Review

Validation scope:

- task-oriented items
- shopping-oriented items
- information-oriented items
- future productivity-oriented items

Result: PASS

Task-oriented items are classified as task-context contributions.

Shopping-oriented items are classified as shopping-context contributions.

Information-oriented items are classified as productivity knowledge-context contributions.

Future productivity-oriented items remain category-extensible under the same deterministic and provenance-preserving rules.

## 9. Provenance Preservation Review

Validation scope:

- provenance preservation
- source lineage preservation
- attribution preservation

Result: PASS

Provenance preservation requires each split item to retain traceable linkage to capture bundle context.

Source lineage preservation requires explicit source and transformation references across classification and routing.

Attribution preservation requires household-facing outcomes to reference consumed source context rather than implied authorship.

## 10. Household Presentation Review

Validation scope:

- household-facing presentation
- presentation boundaries
- presentation expectations

Result: PASS

Household-facing presentation is composed from routed governed context.

Presentation boundaries prohibit Concierge from presenting itself as source-of-record owner.

Presentation expectations require clear item separation, clear category cues, and explainable context-to-outcome linkage.

## 11. Follow-Up Handling Review

Validation scope:

- clarification handling
- incomplete capture handling
- ambiguous capture handling

Result: PASS

Clarification handling must preserve deterministic re-evaluation boundaries.

Incomplete capture handling must preserve bounded partial outcomes without fabricating missing source data.

Ambiguous capture handling must preserve explainable disambiguation paths and unresolved-state visibility.

## 12. Fallback Handling Review

Validation scope:

- missing context handling
- unavailable source handling
- degraded experience handling

Result: PASS

Missing context handling must preserve deterministic bounded fallback behavior.

Unavailable source handling must preserve explicit degraded-state reporting and provenance visibility.

Degraded experience handling must avoid implicit ownership transfer and fabricated source-of-record outcomes.

## 13. Explainability Review

Validation scope:

- explainability hooks
- rationale requirements
- source lineage requirements

Result: PASS

Explainability hooks must expose splitting, classification, and routing rationale.

Rationale requirements must remain deterministic, concise, and diagnosable.

Source lineage requirements must remain explicit and traceable for each routed item context.

## 14. Provenance Governance Review

Validation scope:

- provenance ownership
- provenance traceability
- provenance boundaries

Result: PASS

Provenance ownership remains HTBW governed.

Provenance traceability is mandatory for capture bundles and split item contexts.

Provenance boundaries remain explicit, bounded, and non-authoritative within Concierge.

## 15. Coordinator Integration Review

Validation scope:

- coordinator responsibilities
- capture consumption points
- coordinator boundaries

Result: PASS

Coordinator responsibilities:

- consume governed capture bundles
- deterministically split and classify capture context
- route classified context to governed productivity consumption paths

Capture consumption points:

- capture bundle context
- split item context
- classification evidence
- routing references
- provenance references

Coordinator boundaries:

- no source record ownership
- no capture system ownership
- no productivity system-of-record behavior

## 16. Capture Context Model Review

Validation scope:

- capture context
- bundle context
- routing context
- experience consumption model

Result: PASS

Capture context model includes source references, normalized interaction evidence, deterministic splitting references, deterministic classification references, routing references, and provenance references.

Bundle context captures multi-item intake as governed context only.

Routing context captures bounded handoff references and destination category mapping.

Experience consumption model remains consumer-only and non-authoritative.

## 17. Household Productivity Experience Review

Validation scope:

- experience composition boundaries
- capture contribution boundaries

Result: PASS

Capture contributions are governed context inputs for downstream household productivity experience composition.

Experience composition boundaries preserve source-of-record ownership, provenance traceability, and coordinator consumption boundaries.

## 18. P7 Foundation Review

Validation scope:

- Knowledge Experience Consumption

Result: PASS

E13-P6 preserves Knowledge Experience Consumption as a downstream governed planning surface.

## 19. P8 Foundation Review

Validation scope:

- Briefing Composition Consumption

Result: PASS

E13-P6 preserves Briefing Composition Consumption as a downstream governed planning surface.

## 20. P9 Foundation Review

Validation scope:

- Household Status Synthesis Experience

Result: PASS

E13-P6 preserves Household Status Synthesis Experience as a downstream governed planning surface.

## 21. P10 Foundation Review

Validation scope:

- Productivity Diagnostics and Explainability Surface

Result: PASS

E13-P6 preserves Productivity Diagnostics and Explainability Surface as a downstream governed planning surface.

## 22. Determinism and Traceability Review

Validation scope:

- deterministic processing expectations
- traceability expectations
- replayability expectations

Result: PASS

Deterministic processing expectations require identical splitting, classification, and routing outcomes for identical normalized inputs.

Traceability expectations require capture-to-routing lineage to remain inspectable and attributable.

Replayability expectations require deterministic evaluation replay against preserved normalized evidence and routing references.

## 23. Governance Traceability Matrix

Readiness matrix:

| Governance Surface | Requirement | Traceability Expectation |
|---|---|---|
| Capture | multi-item capture remains governed consumption | bundle-to-item decomposition references are explicit |
| Provenance | provenance ownership remains HTBW governed | lineage remains explicit from capture to routed context |
| Explainability | splitting/classification/routing rationale is required | deterministic rationale references are available |
| Coordinator | coordinator consumes and routes only | coordinator does not own source records |
| Routing | routing boundaries remain bounded and non-authoritative | routing references are explicit and reviewable |
| Productivity context | context remains consumed and externally owned | consumed context remains traceable and non-authoritative |

Result: PASS

## 24. Ownership Matrix Review

Validation scope:

- source ownership
- consumer ownership
- coordinator ownership

Result: PASS

Ownership matrix:

- source ownership: Calendar, Email, Task, and Shopping providers own their records
- consumer ownership: Concierge consumes and routes governed capture context only
- coordinator ownership: Coordinator orchestrates deterministic split/classify/route behavior without source ownership

## 25. Ownership Drift Analysis

Validation scope:

- no source ownership drift
- no provenance ownership drift

Result: PASS

No source ownership drift.

No provenance ownership drift.

## 26. P6 Foundation Determination

Validation scope:

- whether Multi-Item Capture Consumption is sufficiently defined for downstream E13 planning

Result: PASS

Multi-Item Capture Consumption is sufficiently defined for downstream E13 planning.

## 27. Final Determination

E13-P6 MULTI-ITEM CAPTURE CONSUMPTION

APPROVED AS THE AUTHORITATIVE BASELINE

FOR MULTI-ITEM CAPTURE CONSUMPTION