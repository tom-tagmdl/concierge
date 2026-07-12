# Productivity Diagnostics and Explainability Surface

## 1. Purpose

Define the purpose of Productivity Diagnostics and Explainability.

This document establishes the authoritative E13-P10 architecture baseline for Concierge productivity diagnostics and explainability surface.

This document is architecture and governance only.

This document does not define diagnostics engines, telemetry collection, logging pipelines, explainability engines, troubleshooting automation, productivity traces implementation, briefing traces implementation, capture traces implementation, or routing traces implementation.

Concierge surfaces diagnostics and explainability for governed productivity consumption.

## 2. Scope Reviewed

Documented review of mandatory authorities and dependencies:

- Concierge #139
- Concierge #140
- HTBW #40
- E13-P1 outputs
- E13-P2 outputs
- E13-P3 outputs
- E13-P4 outputs
- E13-P5 outputs
- E13-P6 outputs
- E13-P7 outputs
- E13-P8 outputs
- E13-P9 outputs

Reviewed associated governance authorities and readiness artifacts:

- docs/governance/household-productivity-experience-consumption-architecture.md
- docs/governance/calendar-experience-consumption.md
- docs/governance/email-experience-consumption.md
- docs/governance/task-experience-consumption.md
- docs/governance/shopping-experience-consumption.md
- docs/governance/multi-item-capture-consumption.md
- docs/governance/knowledge-experience-consumption.md
- docs/governance/briefing-composition-consumption.md
- docs/governance/household-status-synthesis-experience.md
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
- GitHub issues (#139, #140, #40, #165, #166, #167, #168, #169, #170, #171, #172, #173, #174) are execution inputs and are not architecture authority.

Authority conflict review:

- No conflicts identified between E13-P10 outputs and authoritative ADR/contract/model artifacts.

## 3. Diagnostics Governance Validation

Validation scope:

- diagnostics governance authority
- diagnostics review authority
- diagnostics surface authority

Result: PASS

Validated statements:

- Diagnostics governance authority remains in governed architecture artifacts.
- Diagnostics review authority remains in governed architecture artifacts.
- Diagnostics surface authority remains bounded to Concierge consumer/surface responsibilities.
- Concierge diagnostics remain useful and privacy-safe.
- Concierge diagnostics do not redefine source authority.

## 4. Explainability Governance Validation

Validation scope:

- explainability governance authority
- explainability review authority
- explanation boundary authority

Result: PASS

Validated statements:

- Explainability governance authority remains in governed architecture artifacts.
- Explainability review authority remains in governed architecture artifacts.
- Explanation boundary authority remains explicit and non-authoritative.
- Explainability preserves provenance.
- Explainability does not invent authority.

## 5. Source-of-Record Protection Validation

Validation scope:

- source internals are not exposed
- source systems remain authoritative
- Concierge remains a diagnostic consumer/surface

Result: PASS

Source internals are not exposed.

Source systems remain authoritative.

Concierge remains a diagnostic consumer/surface.

## 6. Productivity Diagnostics Validation

Validation scope:

- productivity diagnostic behavior

Result: PASS

Validated statements:

- Productivity diagnostics are traceable.
- Productivity diagnostics are useful for supportability.
- Productivity diagnostics are privacy-safe.
- Productivity diagnostics preserve source-of-record boundaries.
- Productivity diagnostics preserve provenance references.

## 7. Productivity Trace Review

Validation scope:

- productivity traces
- productivity context traces
- productivity consumption traces

Result: PASS

Productivity traces must expose bounded consumption behavior across productivity domains.

Productivity context traces must retain context lineage and category-level rationale.

Productivity consumption traces must preserve non-authoritative consumer boundaries.

## 8. Briefing Trace Review

Validation scope:

- briefing traces
- selection traces
- ordering traces
- suppression traces

Result: PASS

Briefing traces must expose composition path visibility.

Selection traces, ordering traces, and suppression traces must remain deterministic and explainable.

## 9. Capture Trace Review

Validation scope:

- capture traces
- splitting traces
- routing traces
- follow-up traces

Result: PASS

Capture traces must expose bundle handling and downstream contribution paths.

Splitting traces, routing traces, and follow-up traces must preserve deterministic behavior and lineage visibility.

## 10. Routing Trace Review

Validation scope:

- routing paths
- routing decisions
- routing boundaries

Result: PASS

Routing paths must be inspectable and bounded.

Routing decisions must remain deterministic and explainable.

Routing boundaries must prohibit source ownership drift and internal source leakage.

## 11. Provenance Trace Review

Validation scope:

- provenance traces
- source lineage traces
- attribution traces

Result: PASS

Provenance traces must preserve HTBW-governed lineage references.

Source lineage traces must remain explicit and reviewable.

Attribution traces must preserve consumer-only interpretation boundaries.

## 12. Privacy-Safe Diagnostics Review

Validation scope:

- privacy-safe diagnostic boundaries
- redaction expectations
- safe exposure expectations

Result: PASS

Privacy-safe diagnostic boundaries prohibit exposure of source-of-record internals and privacy-sensitive source data.

Redaction expectations require bounded, policy-aligned suppression of sensitive source details.

Safe exposure expectations require operationally useful summaries without leaking protected source details.

## 13. Troubleshooting Workflow Review

Validation scope:

- troubleshooting categories
- troubleshooting boundaries
- supportability expectations

Result: PASS

Troubleshooting workflow categories include trace classification, explainability references, fallback analysis, and source-boundary verification.

Troubleshooting boundaries prohibit source mutation and authority redefinition.

Supportability expectations require reproducible, deterministic troubleshooting context.

## 14. Explainability Surface Review

Validation scope:

- explanation types
- explanation boundaries
- household-facing explanations

Result: PASS

Explanation types include source, relevance, selection, ordering, suppression, synthesis, and fallback explanations.

Explanation boundaries require non-authoritative, provenance-preserving explanations.

Household-facing explanations must remain concise, deterministic, and bounded.

## 15. Calendar Diagnostic Contribution Review

Validation scope:

- calendar context
- schedule context
- availability context

Result: PASS

Calendar diagnostic contributions must expose bounded context usage, schedule relevance, and availability contribution behavior without exposing source internals.

## 16. Email Diagnostic Contribution Review

Validation scope:

- email context
- communication context
- relevance context

Result: PASS

Email diagnostic contributions must expose bounded communication relevance and contribution behavior while preserving privacy-safe context exposure.

## 17. Task Diagnostic Contribution Review

Validation scope:

- task context
- responsibility context
- task status context

Result: PASS

Task diagnostic contributions must expose bounded task-status and responsibility contribution behavior with explicit lineage references.

## 18. Shopping Diagnostic Contribution Review

Validation scope:

- shopping context
- coordination context
- shopping relevance

Result: PASS

Shopping diagnostic contributions must expose bounded household coordination and shopping relevance behavior without source ownership drift.

## 19. Knowledge Diagnostic Contribution Review

Validation scope:

- knowledge context
- reference context
- historical context

Result: PASS

Knowledge diagnostic contributions must expose bounded knowledge-context consumption behavior with lineage-preserving references.

## 20. Briefing Diagnostic Contribution Review

Validation scope:

- briefing assembly
- content selection
- ordering
- suppression

Result: PASS

Briefing diagnostic contributions must expose deterministic assembly, selection, ordering, and suppression behavior with traceable rationale.

## 21. Household Status Diagnostic Contribution Review

Validation scope:

- context fusion
- prioritization
- status synthesis
- fallback behavior

Result: PASS

Household status diagnostic contributions must expose deterministic context fusion, prioritization, synthesis, and fallback behavior with traceable lineage.

## 22. Coordinator Integration Review

Validation scope:

- coordinator responsibilities
- diagnostics orchestration
- explainability boundaries

Result: PASS

Coordinator responsibilities:

- consume governed productivity context
- orchestrate diagnostics and explainability surfaces
- preserve source-of-record and provenance boundaries

Diagnostics orchestration:

- deterministic trace surfacing
- bounded category classification
- troubleshooting-oriented references

Explainability boundaries:

- no authority invention
- no source internals exposure
- no provenance ownership redefinition

## 23. Diagnostic Categories Review

Validation scope:

- productivity traces
- briefing traces
- capture traces
- routing traces
- provenance traces
- privacy-safe traces
- fallback traces

Result: PASS

Diagnostic categories are defined and bounded:

- productivity traces: cross-domain productivity consumption behavior
- briefing traces: briefing composition, selection, ordering, suppression behavior
- capture traces: capture bundle splitting, routing, follow-up behavior
- routing traces: routing path and decision behavior
- provenance traces: lineage and attribution behavior
- privacy-safe traces: redacted and safe diagnostic views
- fallback traces: degraded or unavailable-context handling behavior

## 24. Explainability Categories Review

Validation scope:

- source explanation
- relevance explanation
- selection explanation
- ordering explanation
- suppression explanation
- synthesis explanation
- fallback explanation

Result: PASS

Explainability categories are defined and bounded:

- source explanation: why source context was considered
- relevance explanation: why context was considered relevant
- selection explanation: why context was included
- ordering explanation: why sequence was chosen
- suppression explanation: why context was reduced or excluded
- synthesis explanation: why synthesized status outcomes were produced
- fallback explanation: why degraded or partial outcomes were produced

## 25. Deterministic Diagnostics Review

Validation scope:

- deterministic trace expectations
- reproducibility expectations
- supportability expectations

Result: PASS

Deterministic trace expectations require stable trace outcomes for equivalent normalized inputs.

Reproducibility expectations require support operators to recreate diagnostics paths from bounded trace references.

Supportability expectations require actionable diagnostics without leaking protected source details.

## 26. Governance Traceability Matrix

Readiness matrix:

| Governance Surface | Requirement | Traceability Expectation |
|---|---|---|
| Diagnostics | diagnostic surfaces remain bounded and useful | categories and trace references are explicit |
| Explainability | explanations remain deterministic and bounded | explanation references are explicit and traceable |
| Provenance | provenance ownership remains HTBW governed | lineage references remain explicit and reviewable |
| Privacy | source internals and sensitive data are protected | redaction and safe exposure boundaries are explicit |
| Coordinator | coordinator consumes and surfaces only | coordinator does not own source records or provenance |
| Productivity context | context remains externally owned and consumed | contribution boundaries remain explicit |
| Troubleshooting | troubleshooting workflow remains actionable and bounded | troubleshooting path references are explicit |

Result: PASS

## 27. Ownership Matrix Review

Validation scope:

- source ownership
- diagnostic surface ownership
- coordinator ownership
- provenance ownership

Result: PASS

Ownership matrix:

- source ownership: Calendar, Email, Task, Shopping, and Knowledge providers own source records
- diagnostic surface ownership: Concierge owns diagnostic and explainability presentation surfaces only
- coordinator ownership: Coordinator orchestrates bounded diagnostics/explainability behavior without source ownership
- provenance ownership: provenance governance remains HTBW owned

## 28. Ownership Drift Analysis

Validation scope:

- no source ownership drift
- no provenance ownership drift
- no diagnostics ownership drift
- no explainability ownership drift

Result: PASS

No source ownership drift.

No provenance ownership drift.

No diagnostics ownership drift.

No explainability ownership drift.

## 29. P10 Foundation Determination

Validation scope:

- whether Productivity Diagnostics and Explainability Surface is sufficiently defined for downstream E13 readiness review

Result: PASS

Productivity Diagnostics and Explainability Surface is sufficiently defined for downstream E13 readiness review.

## 30. Final Determination

E13-P10 PRODUCTIVITY DIAGNOSTICS AND EXPLAINABILITY SURFACE

APPROVED AS THE AUTHORITATIVE BASELINE

FOR PRODUCTIVITY DIAGNOSTICS AND EXPLAINABILITY