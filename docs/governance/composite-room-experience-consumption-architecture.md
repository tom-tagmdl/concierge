# Composite-Room Experience Consumption Architecture

## Purpose

This document defines the authoritative E6 composite-room experience consumption architecture baseline.

This document is architecture and governance only.

This document does not define experience governance, hierarchy governance, scope governance, room governance, experience execution, orchestration, routing, or selection algorithms.

## Authority Relationship

Experience Governance Authority remains external through HTBW experience authorities.

Experience Definition Authority remains external through HTBW experience authorities.

Hierarchy Truth Authority remains external through HTBW hierarchy truth authorities.

Scope Truth Authority remains external through HTBW scope truth authorities.

Room Truth Authority remains external through HTBW room truth authorities.

Coordinator Composite-Room Consumption Authority:

- consumes composite-room experience inputs
- integrates hierarchy context, scope context, and room context with governed experience consumption and resolution inputs

Coordinator consumes composite-room experience inputs.

Coordinator does not own hierarchy truth.

Coordinator does not own scope truth.

## Dependencies

EX5 consumes:

- `docs/governance/experience-consumption-architecture.md`
- `docs/governance/experience-resolution-consumption-architecture.md`
- `docs/governance/room-aware-experience-consumption-architecture.md`
- `docs/governance/merged-room-experience-consumption-architecture.md`
- `docs/governance/composite-room-capability-consumption-architecture.md`
- `docs/governance/capability-explainability-framework.md`
- `docs/governance/capability-diagnostics-surface.md`
- `docs/governance/capability-discovery-foundation.md`

EX5 also consumes the relevant E5 composite-room capability outputs:

- CP5 Composite-Room Capability Consumption
- CP7 Capability Explainability
- CP8 Capability Discovery
- CP9 Capability Diagnostics

EX5 consumes all.

EX5 redefines none.

## Experience Authority Inputs

EX5 consumes:

- HTBW #18 Experience Model ADR
- HTBW #30 Experience Contract
- HTBW #43 Experience Model

These remain authoritative.

## Composite-Room Experience Consumption Model

Composite-room experience consumption means Coordinator consumes governed experience inputs together with hierarchy-aware, scope-aware, and room-aware context so experience behavior can remain composite-room aware without transferring hierarchy or scope ownership.

Hierarchy-aware participation means hierarchy context participates as a governed input to downstream experience behavior.

Scope-aware participation means scope context participates as a governed input to downstream experience behavior.

Floor-level participation means floor context participates as a governed input within the composite-room hierarchy and scope boundaries.

Household-facing outcome preservation means composite-room user-facing behavior remains authoritative even if internal implementation changes, provided governance boundaries remain intact.

This section defines architecture only.

## Composite-Room Experience Eligibility Model

Hierarchy context participates in eligible experiences by contributing governed hierarchy-scoped context to the eligibility boundary.

Hierarchy context participates in restricted experiences by preserving bounded hierarchy constraints without redefining hierarchy truth.

Hierarchy context participates in unavailable experiences by preserving explicit non-availability under active hierarchy-scoped context.

Hierarchy context participates in available experiences by preserving hierarchy-scoped visibility and consumability under governed context.

Scope context participates in eligible experiences by contributing governed scope-scoped context to the eligibility boundary.

Scope context participates in restricted experiences by preserving bounded scope constraints without redefining scope truth.

Scope context participates in unavailable experiences by preserving explicit non-availability under active scope-scoped context.

Scope context participates in available experiences by preserving scope-scoped visibility and consumability under governed context.

Floor-level context participates by contributing floor-scoped constraints and visibility boundaries into eligibility handling.

This section defines architecture only.

## Hierarchy Traversal Participation Model

Hierarchy traversal participates as governed hierarchy-context consumption that informs composite-room experience behavior.

Hierarchy context is consumed as a governed input, not as hierarchy authority.

Hierarchy inheritance participates as governed hierarchy context continuity across composite-room boundaries.

This section defines architecture only.

## Scope Inheritance Participation Model

Scope inheritance participates as governed scope-context continuity across composite-room boundaries.

Scope context is consumed as a governed input, not as scope authority.

Inherited scope contributes to eligibility and filtering by preserving governed scope continuity and constraint propagation.

This section defines architecture only.

## Composite-Room Experience Filtering Model

Hierarchy-aware filtering participates by constraining the visible experience set according to governed hierarchy context.

Scope-aware filtering participates by constraining the visible experience set according to governed scope context.

This section defines architecture only.

## Composite-Room Experience Selection Participation Model

Hierarchy context contributes to experience selection inputs as governed hierarchy context.

Scope context contributes to experience selection inputs as governed scope context.

Composite-room eligibility contributes to experience selection inputs as governed state input.

This section defines architecture only.

## Household-Facing Outcome Preservation

Household-facing composite-room outcomes remain authoritative even if internal implementation changes.

Outcome-preservation expectations:

- preserve composite-room user-visible behavior
- preserve hierarchy and scope boundaries
- preserve household-facing determinism
- preserve source-of-record ownership boundaries

This section defines architecture only.

## Composite-Room Resolution Pipeline

Hierarchy Context
↓
Scope Context
↓
Capability Outputs
↓
Experience Consumption
↓
Experience Resolution
↓
Composite-Room Eligibility
↓
Composite-Room Filtering
↓
Experience Selection Inputs
↓
Experience Outcome

This pipeline is architecture only.

No algorithms are defined here.

## Deterministic Composite-Room Behavior

Deterministic composite-room behavior is achieved by preserving the same hierarchy authority boundaries, the same scope authority boundaries, the same consumed inputs, and the same composite-room-scoped state categories.

Hierarchy context participates consistently by remaining governed input rather than mutable ownership.

Scope context participates consistently by remaining governed input rather than mutable ownership.

This section defines architecture only.

## Explainability Participation

Reference:

- `docs/governance/capability-explainability-framework.md`

Composite-room explanations participate by carrying composite-room lineage, hierarchy-aware rationale, scope-aware rationale, and filtering rationale.

Hierarchy-aware explanations participate by describing how hierarchy context affected eligibility, filtering, or selection inputs.

Scope-aware explanations participate by describing how scope context affected eligibility, filtering, or selection inputs.

Eligibility explanations participate by describing why a composite-room-scoped experience is eligible, restricted, or unavailable.

Filtering explanations participate by describing why a composite-room-scoped experience remains visible or hidden.

This section defines architecture only.

## Diagnostics Participation

Reference:

- `docs/governance/capability-diagnostics-surface.md`

Composite-room traces participate by preserving composite-room resolution and filtering trace references.

Hierarchy-aware traces participate by preserving hierarchy-scoped troubleshooting context.

Scope-aware traces participate by preserving scope-scoped troubleshooting context.

Troubleshooting references participate by preserving deterministic composite-room troubleshooting context.

This section defines architecture only.

## Discovery Participation

Reference:

- `docs/governance/capability-discovery-foundation.md`

Composite-room discovery participates by exposing composite-room-scoped discovery context for governed experience surfaces.

Hierarchy-aware discovery participates by exposing hierarchy-scoped discovery context.

Scope-aware discovery participates by exposing scope-scoped discovery context.

This section defines architecture only.

## Hierarchy and Scope Truth Protection

Hierarchy truth remains external.

Scope truth remains external.

Composite-room context is consumed.

Hierarchy ownership is not transferred.

Scope ownership is not transferred.

Coordinator does not become hierarchy authority.

Coordinator does not become scope authority.

## Asset Intelligence Boundary

Composite-room experience consumption may consume capability outputs that consumed Asset Intelligence-informed context.

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

EX5 must not assume these outputs exist.

## Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Experience Governance | HTBW experience governance | Consumer | PASS |
| Experience Definitions | HTBW experience authorities | Consumer | PASS |
| Hierarchy Truth | HTBW hierarchy truth authority | Consumer | PASS |
| Scope Truth | HTBW scope truth authority | Consumer | PASS |
| Room Truth | HTBW room truth authority | Consumer | PASS |
| Capability Outputs | HTBW capability governance | Consumer | PASS |
| Asset Intelligence Outputs | Asset Intelligence | Consumer | PASS |
| Explainability | governed explainability artifacts | Consumer | PASS |
| Diagnostics | governed diagnostics artifacts | Consumer | PASS |

## Dependency Mapping

| Downstream E6 Consumer | E6 Output Dependency |
|---|---|
| EX6 | guest-aware experience consumption inputs |
| EX7 | experience explainability integration |
| EX8 | experience diagnostics integration |
| EX9 | experience discovery integration |

## Risks

- experience ownership drift
- hierarchy truth drift
- scope truth drift
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
- hierarchy truth ownership preserved
- scope truth ownership preserved
- room truth ownership preserved
- capability governance ownership preserved
- Asset Intelligence ownership preserved

No ownership drift introduced in this E6 architecture baseline.

## Readiness Statement

Composite-Room Experience Consumption Architecture is READY.

This document becomes the authoritative composite-room experience baseline for E6.