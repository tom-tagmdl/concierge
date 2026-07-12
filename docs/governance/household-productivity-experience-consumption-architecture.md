# Household Productivity Experience Consumption Architecture

## 1. Purpose

Define the purpose of Household Productivity Experience Consumption.

This document establishes the authoritative E13-P1 architecture baseline for Concierge productivity experience consumption planning.

This document is architecture and governance only.

This document does not define Calendar integrations, Email integrations, Task integrations, Shopping integrations, Microsoft Graph integrations, productivity experiences, briefing experiences, productivity diagnostics, productivity explainability, capture workflows, or household status synthesis.

Concierge consumes governed productivity context.

Concierge composes experiences.

Concierge does not become Calendar, Email, Task Management, To Do, Shopping, Capture, or Productivity Storage.

No implementation planning may begin until productivity consumption criteria are defined.

## 2. Scope Reviewed

Reviewed mandatory authorities and dependencies:

- HTBW #39
- HTBW #47
- HTBW #50
- Concierge #131

Reviewed associated governance authorities and readiness artifacts:

- docs/architecture/canonical-architecture.md
- docs/architecture/adr-coordinator-v2-governance.md
- docs/governance/coordinator-v2-foundation-summary.md
- docs/architecture/concierge-runtime-architecture.md
- docs/architecture/context-before-intent.md
- docs/architecture/identity-governance-reference.md
- docs/architecture/platinum-target-checklist.md
- docs/architecture/implementation-verification-checklist.md
- docs/contracts/concierge-contract.md
- docs/contracts/concierge-scope-contract.md
- docs/contracts/concierge-global-context-contract.md
- docs/contracts/room-awareness-contract.md
- docs/contracts/composite-room-contract.md
- docs/contracts/person-identity-contract.md
- docs/contracts/service-contracts.md
- docs/contracts/performance-contract.md
- docs/contracts/concierge-signal-contract.md
- docs/contracts/concierge-global-config-contract.md
- docs/models/room-model.md
- docs/models/person-profile-model.md
- docs/models/interaction-model.md
- docs/models/event-model.md
- docs/models/environment-model.md
- docs/models/signal-model.md
- docs/philosophy/homes-that-behave-well.md
- docs/philosophy/concierge-philosophy.md

Authority-order treatment:

- ADRs, contracts, and models are architecture authority.
- Existing implementation is supporting evidence only.
- GitHub issues (#39, #47, #50, #131, #165) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between E13-P1 outputs and authoritative ADR/contract/model artifacts.

## 3. Productivity Governance Validation

Validation scope:

- productivity governance authority
- productivity readiness authority
- productivity review authority

Result: PASS

Validated statements:

- Productivity governance authority remains in HTBW governance artifacts.
- Productivity readiness authority remains in HTBW governance artifacts.
- Productivity review authority remains in HTBW governance artifacts.
- Concierge consumes productivity outcomes.
- Concierge does not redefine productivity governance.

## 4. Source-of-Record Validation

Validation scope:

- Calendar ownership
- Email ownership
- Task ownership
- Shopping ownership

Result: PASS

Validated statements:

- Calendar providers remain systems of record.
- Email providers remain systems of record.
- Task providers remain systems of record.
- Shopping systems remain systems of record.

## 5. Concierge Consumption Validation

Validation scope:

- consumption-only responsibilities

Result: PASS

Validated statements:

- Concierge consumes governed productivity context.
- Concierge does not own productivity records.
- Concierge does not create competing productivity data stores.
- Concierge does not become Calendar, Email, Task Management, To Do, Shopping, Capture, or Productivity Storage.

## 6. Calendar Consumption Boundary Review

Validation scope:

- ownership boundaries
- consumption boundaries
- prohibited ownership behaviors

Result: PASS

Calendar ownership remains with Calendar providers.

Calendar data is consumed as governed context only.

Concierge must not store authoritative calendar records or redefine calendar ownership.

## 7. Email Consumption Boundary Review

Validation scope:

- ownership boundaries
- consumption boundaries
- prohibited ownership behaviors

Result: PASS

Email ownership remains with Email providers.

Email data is consumed as governed context only.

Concierge must not store authoritative email records or redefine email ownership.

## 8. Task Consumption Boundary Review

Validation scope:

- ownership boundaries
- consumption boundaries
- prohibited ownership behaviors

Result: PASS

Task ownership remains with task providers such as Microsoft To Do or configured task systems.

Task data is consumed as governed context only.

Concierge must not store authoritative task records or redefine task ownership.

## 9. Shopping Consumption Boundary Review

Validation scope:

- ownership boundaries
- consumption boundaries
- prohibited ownership behaviors

Result: PASS

Shopping ownership remains with shopping systems.

Shopping data is consumed as governed context only.

Concierge must not store authoritative shopping records or redefine shopping ownership.

## 10. Accessory Context Consumption Review

Validation scope:

- supporting context
- contextual enrichment
- non-authoritative consumption

Result: PASS

Accessory context may include knowledge cues, capture-adjacent descriptors, household preferences, temporal cues, and lightweight contextual enrichment.

Accessory context remains non-authoritative and must not supersede source-of-record context.

## 11. Productivity Context Model Review

Validation scope:

- conceptual productivity context consumed by Concierge

Result: PASS

Conceptual productivity context includes governed source references, context payloads, provenance references, household-facing intent cues, and non-authoritative accessory context.

The model is consumption-oriented only.

The model does not define productivity records or competing source-of-record storage.

## 12. Coordinator Integration Review

Validation scope:

- Coordinator responsibilities
- Coordinator consumption points
- Coordinator boundaries

Result: PASS

Coordinator responsibilities:

- consume productivity context
- compose household productivity experiences
- preserve deterministic orchestration

Coordinator consumption points:

- governed productivity context
- provenance references
- accessory context

Coordinator boundaries:

- no ownership of productivity records
- no source-of-record behavior
- no competing productivity data stores

## 13. Household Productivity Experience Review

Validation scope:

- experience responsibilities
- experience boundaries
- experience composition rules

Result: PASS

Household productivity experiences are composed from governed context only.

Experience composition rules:

- preserve source-of-record ownership
- preserve provenance
- preserve household-facing clarity
- avoid hidden inference chains
- avoid storage duplication

## 14. Household Briefing Foundation Review

Validation scope:

- readiness for E13-P8 Briefing Composition Consumption

Result: PASS

E13-P1 preserves briefing composition as a downstream governed planning surface.

## 15. Household Status Foundation Review

Validation scope:

- readiness for E13-P9 Household Status Synthesis Experience

Result: PASS

E13-P1 preserves household status synthesis as a downstream governed planning surface.

## 16. Provenance Governance Review

Validation scope:

- provenance ownership
- provenance traceability
- provenance consumption boundaries

Result: PASS

Provenance ownership remains HTBW governed.

Provenance traceability is required for every consumed productivity context path.

Provenance consumption boundaries remain explicit and bounded.

## 17. Productivity Explainability Review

Validation scope:

- explainability requirements
- explainability boundaries

Result: PASS

Explainability requirements:

- provide why and why-not rationale for consumed productivity context
- preserve source lineage in machine-readable form
- preserve household-facing rationale in human-readable form

Explainability boundaries:

- do not fabricate source-of-record meaning
- do not invent productivity ownership
- do not hide provenance or confidence cues

## 18. Productivity Diagnostics Review

Validation scope:

- diagnostics requirements
- diagnostics boundaries

Result: PASS

Diagnostics requirements:

- expose trace points for context consumption
- expose provenance references
- expose bounded failure and ambiguity categories

Diagnostics boundaries:

- do not diagnose source-of-record systems as if Concierge owned them
- do not create new diagnostics ownership for productivity sources

## 19. Ownership Matrix Review

Validation scope:

- source ownership
- consumer ownership
- coordinator ownership

Result: PASS

Ownership matrix:

- source ownership: Calendar, Email, Task, and Shopping providers own their records
- consumer ownership: Concierge consumes governed context only
- coordinator ownership: Coordinator composes experiences and does not own records

## 20. E13-P2 Foundation Review

Validation scope:

- Calendar Experience Consumption

Result: PASS

E13-P1 preserves Calendar Experience Consumption as a downstream governed planning surface.

## 21. E13-P3 Foundation Review

Validation scope:

- Email Experience Consumption

Result: PASS

E13-P1 preserves Email Experience Consumption as a downstream governed planning surface.

## 22. E13-P4 Foundation Review

Validation scope:

- Task Experience Consumption

Result: PASS

E13-P1 preserves Task Experience Consumption as a downstream governed planning surface.

## 23. E13-P5 Foundation Review

Validation scope:

- Shopping Experience Consumption

Result: PASS

E13-P1 preserves Shopping Experience Consumption as a downstream governed planning surface.

## 24. E13-P6 Foundation Review

Validation scope:

- Multi-Item Capture Consumption

Result: PASS

E13-P1 preserves Multi-Item Capture Consumption as a downstream governed planning surface without implementing capture workflows.

## 25. E13-P7 Foundation Review

Validation scope:

- Knowledge Experience Consumption

Result: PASS

E13-P1 preserves Knowledge Experience Consumption as a downstream governed planning surface.

## 26. E13-P8 Foundation Review

Validation scope:

- Briefing Composition Consumption

Result: PASS

E13-P1 preserves Briefing Composition Consumption as a downstream governed planning surface.

## 27. E13-P9 Foundation Review

Validation scope:

- Household Status Synthesis Experience

Result: PASS

E13-P1 preserves Household Status Synthesis Experience as a downstream governed planning surface.

## 28. E13-P10 Foundation Review

Validation scope:

- Productivity Diagnostics and Explainability Surface

Result: PASS

E13-P1 preserves Productivity Diagnostics and Explainability Surface as a downstream governed planning surface.

## 29. Governance Traceability Matrix

Readiness matrix:

| Governance Surface | Governing Artifact | Traceability Expectation |
|---|---|---|
| Productivity | household-productivity-experience-consumption-architecture.md | governed productivity context must remain reviewable |
| Calendar | source-of-record calendar systems and HTBW governance | calendar records must remain external to Concierge |
| Email | source-of-record email systems and HTBW governance | email records must remain external to Concierge |
| Tasks | source-of-record task systems and HTBW governance | task records must remain external to Concierge |
| Shopping | source-of-record shopping systems and HTBW governance | shopping records must remain external to Concierge |
| Provenance | HTBW governance and consumer boundaries | provenance references must remain traceable |
| Explainability | Coordinator V2 boundaries and governed context | explanations must remain deterministic and lineage-preserving |
| Diagnostics | Coordinator V2 diagnostics boundaries and governed context | diagnostics must remain bounded and supportable |

Result: PASS

## 30. Ownership Drift Analysis

Validation scope:

- Calendar ownership drift
- Email ownership drift
- Task ownership drift
- Shopping ownership drift
- Provenance ownership drift

Result: PASS

No Calendar ownership drift.
No Email ownership drift.
No Task ownership drift.
No Shopping ownership drift.
No Provenance ownership drift.

## 31. E13 Foundation Determination

Validation scope:

- whether productivity consumption architecture is sufficiently defined for downstream E13 planning

Result: PASS

Concierge productivity consumption architecture is sufficiently defined for downstream E13 planning.

## 32. Final Determination

E13-P1 HOUSEHOLD PRODUCTIVITY EXPERIENCE CONSUMPTION ARCHITECTURE

APPROVED AS THE AUTHORITATIVE BASELINE

FOR E13 PRODUCTIVITY EXPERIENCE PLANNING