# Room-Aware Experience Consumption Architecture

## Purpose

This document defines the authoritative E6 room-aware experience consumption architecture baseline.

This document is architecture and governance only.

This document does not define experience governance, room governance, room truth, room targeting truth, vocabulary governance, experience execution, orchestration, routing, or room selection algorithms.

## Authority Relationship

Experience Governance Authority remains external through HTBW experience authorities.

Experience Definition Authority remains external through HTBW experience authorities.

Room Truth Authority remains external through HTBW room truth authorities.

Room Vocabulary Authority remains external through HTBW room vocabulary authorities.

Coordinator Room-Aware Consumption Authority:

- consumes room-aware experience inputs
- integrates room context with governed experience consumption and resolution inputs

Coordinator consumes room-aware experience inputs.

Coordinator does not own room truth.

## Dependencies

EX3 consumes:

- `docs/governance/experience-consumption-architecture.md`
- `docs/governance/experience-resolution-consumption-architecture.md`
- `docs/governance/room-aware-capability-consumption-architecture.md`
- `docs/governance/capability-explainability-framework.md`
- `docs/governance/capability-diagnostics-surface.md`
- `docs/governance/capability-discovery-foundation.md`

EX3 also consumes the relevant E5 room-aware capability outputs:

- CP3 Room-Aware Capability Consumption
- CP7 Capability Explainability
- CP8 Capability Discovery
- CP9 Capability Diagnostics

EX3 consumes all.

EX3 redefines none.

## Experience Authority Inputs

EX3 consumes:

- HTBW #18 Experience Model ADR
- HTBW #30 Experience Contract
- HTBW #43 Experience Model

These remain authoritative.

## Room-Aware Experience Consumption Model

Room-aware experience consumption means Coordinator consumes governed experience inputs together with room context so experience behavior can remain room-sensitive without transferring room ownership.

Room awareness means the consumed experience behavior recognizes room context as governed input, not as room authority.

Room participation means room context participates in downstream experience behavior as a bounded input for eligibility, resolution, targeting, and filtering.

This section defines architecture only.

## Room Experience Eligibility Model

Room context participates in eligible experiences by contributing governed room-scoped context to the eligibility boundary.

Room context participates in restricted experiences by preserving bounded room constraints without redefining room truth.

Room context participates in unavailable experiences by preserving explicit non-availability under active room-scoped context.

Room context participates in available experiences by preserving room-scoped visibility and consumability under governed context.

This section defines architecture only.

## Room Experience Resolution Model

Room context participates in experience resolution by providing room-scoped context that is consumed by governed resolution behavior.

This section defines architecture only.

## Room Experience Targeting Model

Room targeting participates as governed room reference consumption and room-scoped boundary preservation.

Room references participate as stable references to governed room truth.

Room-aware boundaries participate as external constraints on experience behavior.

This section defines architecture only.

## Room Experience Filtering Model

Room-based filtering participates by constraining the visible experience set according to governed room context.

This section defines architecture only.

## Room-Aware Resolution Pipeline

Room Context
↓
Capability Outputs
↓
Experience Consumption
↓
Experience Resolution
↓
Room-Aware Eligibility
↓
Room-Aware Filtering
↓
Experience Outcome

This pipeline is architecture only.

No algorithms are defined here.

## Deterministic Room-Aware Behavior

Deterministic room-aware behavior is achieved by preserving the same room authority boundaries, the same consumed inputs, and the same room-scoped state categories.

Room context participates consistently by remaining governed input rather than mutable ownership.

This section defines architecture only.

## Explainability Participation

Reference:

- `docs/governance/capability-explainability-framework.md`

Room-aware explanations participate by carrying room lineage, room-scoped eligibility rationale, and room-scoped filtering rationale.

Eligibility explanations participate by describing why a room-scoped experience is eligible, restricted, or unavailable.

Filtering explanations participate by describing why a room-scoped experience remains visible or hidden.

This section defines architecture only.

## Diagnostics Participation

Reference:

- `docs/governance/capability-diagnostics-surface.md`

Room-aware traces participate by preserving room-scoped resolution and filtering trace references.

Troubleshooting references participate by preserving deterministic room-aware troubleshooting context.

This section defines architecture only.

## Discovery Participation

Reference:

- `docs/governance/capability-discovery-foundation.md`

Room-aware discovery participates by exposing room-scoped discovery context for governed experience surfaces.

This section defines architecture only.

## Room Truth Protection

Room truth remains external.

Room context is consumed.

Room ownership is not transferred.

Coordinator does not become room authority.

## Asset Intelligence Boundary

Room-aware experience consumption may consume capability outputs that consumed Asset Intelligence-informed context.

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

EX3 must not assume these outputs exist.

## Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Experience Governance | HTBW experience governance | Consumer | PASS |
| Experience Definitions | HTBW experience authorities | Consumer | PASS |
| Room Truth | HTBW room truth authority | Consumer | PASS |
| Room Vocabulary | HTBW room vocabulary authority | Consumer | PASS |
| Capability Outputs | HTBW capability governance | Consumer | PASS |
| Asset Intelligence Outputs | Asset Intelligence | Consumer | PASS |
| Explainability | governed explainability artifacts | Consumer | PASS |
| Diagnostics | governed diagnostics artifacts | Consumer | PASS |

## Dependency Mapping

| Downstream E6 Consumer | E6 Output Dependency |
|---|---|
| EX4 | merged-room experience consumption inputs |
| EX5 | composite-room experience consumption inputs |
| EX6 | guest-aware experience consumption inputs |
| EX7 | experience explainability integration |
| EX8 | experience diagnostics integration |
| EX9 | experience discovery integration |

## Risks

- experience ownership drift
- room truth drift
- room targeting drift
- eligibility ambiguity
- Asset Intelligence meaning drift
- explainability divergence
- diagnostics divergence

## Ownership Preservation Review

Result: PASS

Validated:

- experience governance ownership preserved
- experience definition ownership preserved
- room truth ownership preserved
- capability governance ownership preserved
- Asset Intelligence ownership preserved
- vocabulary governance ownership preserved

No ownership drift introduced in this E6 architecture baseline.

## Readiness Statement

Room-Aware Experience Consumption Architecture is READY.

This document becomes the authoritative room-aware experience baseline for E6.