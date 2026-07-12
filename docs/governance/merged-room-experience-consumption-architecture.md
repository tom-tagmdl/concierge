# Merged-Room Experience Consumption Architecture

## Purpose

This document defines the authoritative E6 merged-room experience consumption architecture baseline.

This document is architecture and governance only.

This document does not define experience governance, merged-room governance, merged-room truth, room truth, experience execution, orchestration, routing, or selection algorithms.

## Authority Relationship

Experience Governance Authority remains external through HTBW experience authorities.

Experience Definition Authority remains external through HTBW experience authorities.

Merged-Room Truth Authority remains external through HTBW merged-room truth authorities.

Room Truth Authority remains external through HTBW room truth authorities.

Coordinator Merged-Room Consumption Authority:

- consumes merged-room experience inputs
- integrates merged-room context with governed experience consumption, resolution, and room-aware inputs

Coordinator consumes merged-room experience inputs.

Coordinator does not own merged-room truth.

## Dependencies

EX4 consumes:

- `docs/governance/experience-consumption-architecture.md`
- `docs/governance/experience-resolution-consumption-architecture.md`
- `docs/governance/room-aware-experience-consumption-architecture.md`
- `docs/governance/merged-room-capability-consumption-architecture.md`
- `docs/governance/capability-explainability-framework.md`
- `docs/governance/capability-diagnostics-surface.md`
- `docs/governance/capability-discovery-foundation.md`

EX4 also consumes the relevant E5 merged-room capability outputs:

- CP4 Merged-Room Capability Consumption
- CP7 Capability Explainability
- CP8 Capability Discovery
- CP9 Capability Diagnostics

EX4 consumes all.

EX4 redefines none.

## Experience Authority Inputs

EX4 consumes:

- HTBW #18 Experience Model ADR
- HTBW #30 Experience Contract
- HTBW #43 Experience Model

These remain authoritative.

## Merged-Room Experience Consumption Model

Merged-room experience consumption means Coordinator consumes governed experience inputs together with merged-room context so experience behavior can remain merged-room aware without transferring merged-room ownership.

Merged-room participation means merged-room context participates as a governed input to downstream experience behavior.

Household-facing merged-room outcome preservation means merged-room user-facing behavior remains authoritative even if internal implementation changes, provided governance boundaries remain intact.

This section defines architecture only.

## Merged-Room Experience Eligibility Model

Merged-room context participates in eligible experiences by contributing governed merged-room context to the eligibility boundary.

Merged-room context participates in restricted experiences by preserving bounded merged-room constraints without redefining merged-room truth.

Merged-room context participates in unavailable experiences by preserving explicit non-availability under active merged-room context.

Merged-room context participates in available experiences by preserving merged-room visibility and consumability under governed context.

This section defines architecture only.

## Merged-Room Experience Filtering Model

Merged-room filtering participates by constraining the visible experience set according to governed merged-room context.

This section defines architecture only.

## Merged-Room Experience Selection Participation Model

Merged-room context contributes to experience selection inputs as governed merged-room context.

Merged-room eligibility contributes to experience selection inputs as governed state input.

This section defines architecture only.

## Household-Facing Outcome Preservation

Household-facing merged-room outcomes remain authoritative even if internal implementation changes.

Outcome-preservation expectations:

- preserve merged-room user-visible behavior
- preserve merged-room context boundaries
- preserve household-facing determinism
- preserve source-of-record ownership boundaries

This section defines architecture only.

## Merged-Room Resolution Pipeline

Merged-Room Context
↓
Capability Outputs
↓
Experience Consumption
↓
Experience Resolution
↓
Merged-Room Eligibility
↓
Merged-Room Filtering
↓
Experience Selection Inputs
↓
Experience Outcome

This pipeline is architecture only.

No algorithms are defined here.

## Deterministic Merged-Room Behavior

Deterministic merged-room behavior is achieved by preserving the same merged-room authority boundaries, the same consumed inputs, and the same merged-room-scoped state categories.

Merged-room context participates consistently by remaining governed input rather than mutable ownership.

This section defines architecture only.

## Explainability Participation

Reference:

- `docs/governance/capability-explainability-framework.md`

Merged-room explanations participate by carrying merged-room lineage, merged-room eligibility rationale, and merged-room filtering rationale.

Eligibility explanations participate by describing why a merged-room-scoped experience is eligible, restricted, or unavailable.

Filtering explanations participate by describing why a merged-room-scoped experience remains visible or hidden.

This section defines architecture only.

## Diagnostics Participation

Reference:

- `docs/governance/capability-diagnostics-surface.md`

Merged-room traces participate by preserving merged-room resolution and filtering trace references.

Troubleshooting references participate by preserving deterministic merged-room troubleshooting context.

This section defines architecture only.

## Discovery Participation

Reference:

- `docs/governance/capability-discovery-foundation.md`

Merged-room discovery participates by exposing merged-room-scoped discovery context for governed experience surfaces.

This section defines architecture only.

## Merged-Room Truth Protection

Merged-room truth remains external.

Merged-room context is consumed.

Merged-room ownership is not transferred.

Coordinator does not become merged-room authority.

## Asset Intelligence Boundary

Merged-room experience consumption may consume capability outputs that consumed Asset Intelligence-informed context.

Coordinator does not own Asset Intelligence meaning.

Coordinator does not own Asset Intelligence outputs.

Coordinator does not reinterpret:

- advisories
- risk outputs
- human_health outputs
- significance
- relevance

as experience-owned truth.

## Experience Ownership Protection

Coordinator does not own:

- experience governance
- experience definitions
- experience categories
- experience contracts
- experience models

Coordinator consumes all of the above.

## Nonexistent Output Protection

Current implementation does not expose:

- significance assessments
- relevance assessments
- asset narratives
- room-health narratives
- collection narratives
- environmental narratives
- priority-context outputs

EX4 must not assume these outputs exist.

## Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Experience Governance | HTBW experience governance | Consumer | PASS |
| Experience Definitions | HTBW experience authorities | Consumer | PASS |
| Merged-Room Truth | HTBW merged-room truth authority | Consumer | PASS |
| Room Truth | HTBW room truth authority | Consumer | PASS |
| Capability Outputs | HTBW capability governance | Consumer | PASS |
| Asset Intelligence Outputs | Asset Intelligence | Consumer | PASS |
| Explainability | governed explainability artifacts | Consumer | PASS |
| Diagnostics | governed diagnostics artifacts | Consumer | PASS |

## Dependency Mapping

| Downstream E6 Consumer | E6 Output Dependency |
|---|---|
| EX5 | composite-room experience consumption inputs |
| EX6 | guest-aware experience consumption inputs |
| EX7 | experience explainability integration |
| EX8 | experience diagnostics integration |
| EX9 | experience discovery integration |

## Risks

- experience ownership drift
- merged-room truth drift
- household-outcome drift
- eligibility ambiguity
- Asset Intelligence meaning drift
- explainability divergence
- diagnostics divergence

## Ownership Preservation Review

Result: PASS

Validated:

- experience governance ownership preserved
- experience definition ownership preserved
- merged-room truth ownership preserved
- room truth ownership preserved
- capability governance ownership preserved
- Asset Intelligence ownership preserved

No ownership drift introduced in this E6 architecture baseline.

## Readiness Statement

Merged-Room Experience Consumption Architecture is READY.

This document becomes the authoritative merged-room experience baseline for E6.