# Experience Continuity Diagnostics Reference

## Purpose

This artifact defines the governed diagnostics and explainability surface for Experience Continuity.

It exposes traceability for continuity decisions without implementing continuity behavior, restoration behavior, or ownership-domain logic.

## Governing Sources

- [ADR: Experience Continuity Architecture](adr-experience-continuity-architecture.md)
- [Experience Continuity Scope Decisions](experience-continuity-scope-decisions.md)
- [Experience Continuity Requirements Backlog](experience-continuity-requirements-backlog.md)
- [V1-to-V2 Capability Parity Matrix](v1-to-v2-capability-parity-matrix.md)
- [V1 Capability Reconstruction](v1-capability-reconstruction.md)
- [Experience Continuity Runtime Terminology Reference](experience-continuity-runtime-terminology-reference.md)
- [Experience Continuity Scope and Event Classification Reference](experience-continuity-classification-model-reference.md)
- [Experience Continuity Helper-Family Disposition Matrix](experience-continuity-helper-family-disposition-matrix.md)

## Diagnostics Architecture

Experience Continuity diagnostics are supportability surfaces only.

They are used to explain why a decision was classified, why a fallback was selected, and which evidence was considered.

Diagnostics must remain boundary-safe and governance-safe.

Primary surfaces:

- `continuity_classification_traceability_visibility`
- `continuity_decision_traceability_visibility`

The first surface exposes deterministic scope and event classification traces.
The second surface exposes decision-summary traces, confidence traces, fallback traces, and redaction visibility.

## Explainability Model

Explainability is deterministic and projection-only.

Diagnostics may expose:

- selected scope
- alternative scope candidates considered
- selected event class
- classification reason codes
- confidence value and confidence band
- fallback trigger and fallback reason
- decision identifier
- source evidence field names or bounded evidence references

Diagnostics must not expose raw authority data or private payloads.

## Decision Trace Structure

A decision trace is represented as a bounded trace envelope with these sections:

- `scope_classification_trace`
- `event_classification_trace`
- `confidence_trace`
- `fallback_trace`
- `decision_summary_trace`

Required decision-summary fields:

- `decision_identifier`
- `timestamp`
- `source_evidence`
- `final_classification_outcome`
- `explainability_references`

Required classification evidence fields:

- `scope_classification.reason_code`
- `scope_classification.evidence`
- `event_classification.reason_code`
- `event_classification.evidence`

## Confidence Trace Structure

Confidence traces are supportability projections only.

Required confidence fields:

- `score`
- `band`
- `reason_codes`
- `available`
- `metadata`

Confidence bands:

- unknown
- low
- medium
- high

Confidence visibility must not expose raw voice-print artifacts, private identity payloads, or other sensitive source data.

## Fallback Trace Structure

Fallback traces explain why a governed fallback path was selected.

Required fallback fields:

- `fallback_applied`
- `fallback_trigger`
- `fallback_reason`
- `fallback_category`
- `governance_boundary`

Supported fallback categories:

- none
- household_guardrail
- unknown_event
- low_confidence

Fallback traces must remain bounded to policy and category labels.
They must not reveal private content or source-of-truth internals.

## Redaction Rules

Diagnostics must omit or redact the following content categories:

- secrets
- credentials
- tenant tokens
- personally sensitive content
- Voice Identity biometric artifacts
- Asset Intelligence sensitive asset details
- raw debug payloads
- request summaries containing private content

Redaction rules:

- expose identifiers and reason codes only
- do not expose raw source payloads
- do not expose raw event payloads
- do not expose full debug payloads
- do not expose biometric artifacts
- do not expose tenant-specific secrets

Redaction visibility must be documented and tested.

## Validation Scenarios

The diagnostics layer documents the following scenarios:

1. Entity-scope continuity decision
2. Room-scope continuity decision
3. Person-scope continuity decision
4. Household-scope continuity decision
5. Mode-scope continuity decision
6. Unknown-event fallback scenario
7. Low-confidence scenario
8. Successful classification scenario

For each scenario the diagnostics package must expose:

- input evidence
- classification result
- confidence
- fallback status
- trace output

## Non-Goals

Experience Continuity diagnostics do not implement:

- continuity behavior
- restoration behavior
- media orchestration
- lighting orchestration
- room orchestration
- preference resolution execution
- install-gate enforcement
- migration execution
- runtime state mutation
- production Home Assistant changes

## Validation Evidence

Diagnostics validation must prove:

- trace completeness
- trace determinism
- fallback visibility
- confidence visibility
- redaction safety
- serialized structure stability

The companion diagnostics tests must exercise the diagnostics surfaces directly and remain install-gate supporting only.
