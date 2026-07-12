# Briefing Composition Consumption

## 1. Purpose

Define the purpose of Briefing Composition Consumption.

This document establishes the authoritative E13-P8 architecture baseline for Concierge briefing composition consumption.

This document is architecture and governance only.

This document does not define briefing generation, briefing delivery, notification systems, TTS delivery, dashboard experiences, recommendation engines, prioritization engines, AI summarization, or productivity experiences.

Concierge composes household briefings from governed productivity context.

## 2. Scope Reviewed

Documented review of mandatory authorities and dependencies:

- HTBW #47
- HTBW #50
- Concierge #132
- Concierge #133
- Concierge #134
- Concierge #137
- E13-P1 outputs
- E13-P2 outputs
- E13-P3 outputs
- E13-P4 outputs
- E13-P5 outputs
- E13-P6 outputs
- E13-P7 outputs

Reviewed associated governance authorities and readiness artifacts:

- docs/governance/household-productivity-experience-consumption-architecture.md
- docs/governance/calendar-experience-consumption.md
- docs/governance/email-experience-consumption.md
- docs/governance/task-experience-consumption.md
- docs/governance/shopping-experience-consumption.md
- docs/governance/multi-item-capture-consumption.md
- docs/governance/knowledge-experience-consumption.md
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
- GitHub issues (#47, #50, #132, #133, #134, #137, #165, #166, #167, #168, #169, #170, #171, #172) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between E13-P8 outputs and authoritative ADR/contract/model artifacts.

## 3. Briefing Governance Validation

Validation scope:

- briefing governance authority
- briefing review authority
- briefing composition authority

Result: PASS

Validated statements:

- Briefing governance authority remains in HTBW governance artifacts.
- Briefing review authority remains in HTBW governance artifacts.
- Briefing composition authority remains in HTBW governance artifacts.
- Concierge composes briefings from governed productivity context.
- Concierge does not redefine briefing governance.

## 4. Source-of-Record Validation

Validation scope:

- source systems remain authoritative
- Concierge remains a consumer/composer

Result: PASS

Source systems remain authoritative for Calendar, Email, Task, Shopping, and Knowledge context.

Concierge remains a consumer/composer and does not become a system of record.

## 5. Briefing Composition Validation

Validation scope:

- briefing composition behavior

Result: PASS

Validated statements:

- Briefings are derived experiences.
- Concierge composes household briefings from governed productivity context.
- Concierge does not own source records.
- Briefings preserve provenance.
- Briefings preserve explainability.
- Briefings are deterministic and traceable.

## 6. Briefing Assembly Review

Validation scope:

- briefing assembly
- composition flow
- assembly boundaries

Result: PASS

Briefing assembly combines governed source contributions into a bounded composition artifact.

Composition flow remains deterministic from consumed context through selection, ordering, suppression, and household-facing output assembly.

Assembly boundaries prohibit source mutation, source ownership transfer, and hidden record creation.

## 7. Content Selection Review

Validation scope:

- selection rules
- relevance rules
- inclusion criteria

Result: PASS

Selection rules require deterministic, criteria-based inclusion from governed source context.

Relevance rules require explainable household relevance with explicit context lineage.

Inclusion criteria require bounded context, non-duplication intent, and explicit category compatibility.

## 8. Content Ordering Review

Validation scope:

- ordering rules
- prioritization rules
- sequencing expectations

Result: PASS

Ordering rules require deterministic sequence generation for equivalent normalized inputs.

Prioritization rules require governed precedence criteria and explainable ties.

Sequencing expectations require consistent cross-source ordering behavior and traceable rationale.

## 9. Content Suppression Review

Validation scope:

- suppression rules
- duplication prevention
- noise reduction expectations

Result: PASS

Suppression rules require deterministic suppression of redundant or low-value context.

Duplication prevention requires stable cross-source deduplication behavior.

Noise reduction expectations require bounded briefing output while preserving significant context and lineage.

## 10. Calendar Contribution Review

Validation scope:

- calendar context
- household schedule context
- availability context

Result: PASS

Calendar contribution uses governed calendar context, household schedule context, and availability context as non-authoritative composition inputs.

## 11. Email Contribution Review

Validation scope:

- communication context
- household relevance
- productivity relevance

Result: PASS

Email contribution uses governed communication context with bounded household relevance and productivity relevance cues.

## 12. Task Contribution Review

Validation scope:

- task context
- responsibility context
- progress context

Result: PASS

Task contribution uses governed task context, responsibility context, and progress context as non-authoritative composition inputs.

## 13. Shopping Contribution Review

Validation scope:

- household coordination context
- shopping context
- shopping relevance

Result: PASS

Shopping contribution uses governed household coordination context, shopping context, and shopping relevance cues.

## 14. Knowledge Contribution Review

Validation scope:

- household knowledge context
- historical context
- reference context

Result: PASS

Knowledge contribution uses governed household knowledge context, historical context, and reference context with explicit lineage.

## 15. Multi-Item Capture Contribution Review

Validation scope:

- capture context
- routing context
- bundled productivity context

Result: PASS

Multi-item capture contribution uses governed capture context, routing context, and bundled productivity context as deterministic composition inputs.

## 16. Household Presentation Review

Validation scope:

- household-facing presentation
- presentation boundaries
- presentation expectations

Result: PASS

Household-facing presentation is a composed consumer artifact only.

Presentation boundaries prohibit Concierge from presenting itself as a source-of-record owner.

Presentation expectations require clear contribution boundaries, clear rationale, and clear source lineage visibility.

## 17. Explainability Review

Validation scope:

- explainability hooks
- rationale requirements
- source lineage requirements

Result: PASS

Explainability hooks must expose selection, ordering, suppression, and contribution rationale.

Rationale requirements must remain deterministic, concise, and diagnosable.

Source lineage requirements must remain explicit and traceable across briefing sections.

## 18. Provenance Governance Review

Validation scope:

- provenance ownership
- provenance traceability
- provenance preservation

Result: PASS

Provenance ownership remains HTBW governed.

Provenance traceability is mandatory for all briefing contributions.

Provenance preservation is required for composed briefing outputs.

## 19. Coordinator Integration Review

Validation scope:

- coordinator responsibilities
- composition orchestration
- briefing boundaries

Result: PASS

Coordinator responsibilities:

- consume governed productivity context
- orchestrate deterministic briefing composition
- preserve provenance and explainability boundaries

Composition orchestration:

- deterministic selection
- deterministic ordering
- deterministic suppression
- bounded contribution assembly

Briefing boundaries:

- no source record ownership
- no source mutation behavior
- no system-of-record behavior

## 20. Briefing Context Model Review

Validation scope:

- briefing context
- composition context
- productivity relevance
- experience consumption model

Result: PASS

Briefing context model includes source references, contribution fragments, deterministic selection references, deterministic ordering references, suppression references, relevance cues, and provenance references.

Composition context models bounded cross-source assembly inputs.

Experience consumption model remains consumer-only and non-authoritative.

## 21. Household Experience Review

Validation scope:

- experience composition boundaries
- briefing contribution boundaries
- household experience expectations

Result: PASS

Experience composition boundaries preserve source-of-record ownership and provenance traceability.

Briefing contribution boundaries preserve non-authoritative, consumer-only behavior.

Household experience expectations require clarity, boundedness, relevance, and explainability.

## 22. P9 Foundation Review

Validation scope:

- Household Status Synthesis Experience

Result: PASS

E13-P8 preserves Household Status Synthesis Experience as a downstream governed planning surface.

## 23. P10 Foundation Review

Validation scope:

- Productivity Diagnostics and Explainability Surface

Result: PASS

E13-P8 preserves Productivity Diagnostics and Explainability Surface as a downstream governed planning surface.

## 24. Deterministic Composition Review

Validation scope:

- deterministic selection expectations
- deterministic ordering expectations
- deterministic suppression expectations

Result: PASS

Deterministic selection expectations require stable inclusion outcomes for equivalent normalized input context.

Deterministic ordering expectations require stable sequence outcomes for equivalent normalized input context.

Deterministic suppression expectations require stable deduplication and suppression outcomes for equivalent normalized input context.

## 25. Governance Traceability Matrix

Readiness matrix:

| Governance Surface | Requirement | Traceability Expectation |
|---|---|---|
| Briefing composition | composition remains governed and deterministic | assembly lineage and composition references are explicit |
| Provenance | provenance ownership remains HTBW governed | contribution lineage remains explicit and reviewable |
| Explainability | explainability hooks and rationale are required | rationale references remain deterministic and traceable |
| Coordinator | coordinator consumes and composes only | coordinator does not own source records |
| Relevance | relevance rules remain bounded and explainable | inclusion and suppression rationale remain inspectable |
| Productivity context | context remains externally owned and consumed | source contribution boundaries remain explicit |

Result: PASS

## 26. Ownership Matrix Review

Validation scope:

- source ownership
- consumer ownership
- coordinator ownership

Result: PASS

Ownership matrix:

- source ownership: Calendar, Email, Task, Shopping, and Knowledge providers own source records
- consumer ownership: Concierge consumes governed context and composes briefing outputs only
- coordinator ownership: Coordinator orchestrates composition without source ownership

## 27. Ownership Drift Analysis

Validation scope:

- no source ownership drift
- no provenance ownership drift

Result: PASS

No source ownership drift.

No provenance ownership drift.

## 28. P8 Foundation Determination

Validation scope:

- whether Briefing Composition Consumption is sufficiently defined for downstream E13 planning

Result: PASS

Briefing Composition Consumption is sufficiently defined for downstream E13 planning.

## 29. Final Determination

E13-P8 BRIEFING COMPOSITION CONSUMPTION

APPROVED AS THE AUTHORITATIVE BASELINE

FOR BRIEFING COMPOSITION CONSUMPTION