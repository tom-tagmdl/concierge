# Experience Resolution Consumption Architecture

## Purpose

This document defines the authoritative E6 experience resolution consumption architecture baseline.

This document is architecture and governance only.

This document does not define experience governance, authorship, categories, lifecycle governance, execution, orchestration, routing, recommendation logic, ranking algorithms, or selection algorithms.

## Authority Relationship

Experience Governance Authority remains external through HTBW experience authorities.

Experience Definition Authority remains external through HTBW experience authorities.

Experience Contract Authority remains external through HTBW contract authority.

Experience Model Authority remains external through HTBW model authority.

Coordinator Resolution Authority:

- resolves experiences
- integrates experience resolution with governed capability outputs and experience consumption inputs

Coordinator resolves experiences.

Coordinator does not define experiences.

## EX1 Dependencies

EX2 consumes:

- `docs/governance/experience-consumption-architecture.md`
- `docs/governance/capability-consumption-architecture.md`
- `docs/governance/capability-resolution-pipeline-architecture.md`
- `docs/governance/room-aware-capability-consumption-architecture.md`
- `docs/governance/merged-room-capability-consumption-architecture.md`
- `docs/governance/composite-room-capability-consumption-architecture.md`
- `docs/governance/guest-aware-capability-filtering-architecture.md`
- `docs/governance/capability-explainability-framework.md`
- `docs/governance/capability-discovery-foundation.md`
- `docs/governance/capability-diagnostics-surface.md`

EX2 also consumes the relevant E5 capability resolution outputs:

- CP2 Capability Resolution Pipeline
- CP3 Room-Aware Capability Consumption
- CP4 Merged-Room Capability Consumption
- CP5 Composite-Room Capability Consumption
- CP6 Guest-Aware Capability Filtering
- CP7 Capability Explainability
- CP8 Capability Discovery
- CP9 Capability Diagnostics

EX2 consumes all.

EX2 redefines none.

## Experience Authority Inputs

EX2 consumes:

- HTBW #18 Experience Model ADR
- HTBW #30 Experience Contract
- HTBW #43 Experience Model

These remain authoritative.

## Experience Resolution Model

Experience resolution means Coordinator consumes governed experience inputs and determines governed experience resolution outcomes.

Runtime experience resolution means Coordinator applies governed state and boundary rules to consumed experience inputs at runtime without owning experience meaning.

Deterministic resolution means identical governed inputs produce consistent resolution outcomes under the same authority boundaries.

This section defines architecture only.

## Experience State Model

Available experience: governed experience output that is currently consumable under the active context.

Eligible experience: governed experience output that satisfies the active eligibility boundary.

Restricted experience: governed experience output that remains visible in bounded form but is constrained by policy, context, or guest-safe conditions.

Unavailable experience: governed experience output that is not currently consumable under the active context.

This section defines architecture only.

## Experience Resolution Pipeline

Capability Outputs
↓
Experience Consumption
↓
Experience Resolution
↓
Experience Eligibility
↓
Experience State Assignment
↓
Experience Resolution Outcome

This pipeline is architecture only.

No algorithms are defined here.

## Deterministic Resolution Model

Deterministic behavior is preserved by consuming governed inputs, preserving explicit precedence boundaries, and keeping resolution outcomes explainable and diagnosable.

Ordering participates as governed sequence context, not as hidden implementation logic.

Resolution consistency is maintained by preserving the same authority chain, the same state categories, and the same upstream dependency boundaries.

This section defines architecture only.

## Experience Eligibility Participation

Eligibility participates as a governed state boundary consumed during resolution.

Eligibility inputs include governed capability outputs, experience inputs, room context, guest context, and governed availability signals.

This section defines architecture only.

## Experience Restriction Participation

Restricted experiences participate as governed outputs that remain visible only within their bounded restriction state.

Restriction states participate as explicit policy outcomes and must not be collapsed into owned experience truth.

This section defines architecture only.

## Experience Availability Participation

Available experiences participate as governed outputs that can continue through resolution and downstream consumption.

This section defines architecture only.

## Experience Unavailability Participation

Unavailable experiences participate as governed explicit non-availability outcomes.

Unavailable state must remain visible to explainability and diagnostics without being reinterpreted as executable experience truth.

This section defines architecture only.

## Room-Aware Experience Resolution

Room-aware capability outputs participate in experience resolution by providing room-scoped context for resolution boundaries.

This section defines architecture only.

## Merged-Room Experience Resolution

Merged-room capability outputs participate in experience resolution by providing merged-room context for deterministic resolution boundaries.

This section defines architecture only.

## Composite-Room Experience Resolution

Composite-room capability outputs participate in experience resolution by providing hierarchy context and scope context for resolution boundaries.

This section defines architecture only.

## Guest-Aware Experience Resolution

Guest filtering participates in experience resolution by constraining guest eligibility and guest-safe availability boundaries.

Guest eligibility participates as a governed restriction and eligibility boundary, not as owned experience logic.

This section defines architecture only.

## Explainability Participation

Reference:

- `docs/governance/capability-explainability-framework.md`

Explainability hooks participate in experience resolution by carrying lineage, eligibility rationale, availability rationale, and ownership-boundary references.

This section defines architecture only.

## Diagnostics Participation

Reference:

- `docs/governance/capability-diagnostics-surface.md`

Diagnostics references participate in experience resolution by carrying resolution traces, boundary traces, and troubleshooting references.

This section defines architecture only.

## Discovery Participation

Reference:

- `docs/governance/capability-discovery-foundation.md`

Discovery outputs participate in experience resolution as governed discovery context for experience visibility and surface discovery.

This section defines architecture only.

## Asset Intelligence Boundary

Experience resolution may consume capability outputs that consumed Asset Intelligence-informed context.

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

EX2 must not assume these outputs exist.

## Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Experience Governance | HTBW experience governance | Consumer | PASS |
| Experience Definitions | HTBW experience authorities | Consumer | PASS |
| Experience Categories | HTBW experience authorities | Consumer | PASS |
| Experience Resolution | governed resolution consumption architecture | Consumer | PASS |
| Capability Outputs | HTBW capability governance | Consumer | PASS |
| Asset Intelligence Outputs | Asset Intelligence | Consumer | PASS |
| Explainability | governed explainability artifacts | Consumer | PASS |
| Diagnostics | governed diagnostics artifacts | Consumer | PASS |

## Dependency Mapping

| Downstream E6 Consumer | E6 Output Dependency |
|---|---|
| #93 | room-aware experience resolution |
| #94 | merged-room experience resolution |
| #95 | composite-room experience resolution |
| #96 | guest-aware experience resolution |
| #97 | experience explainability integration |
| #98 | experience diagnostics integration |
| #99 | experience discovery integration |

## Risks

- experience ownership drift
- experience governance drift
- resolution ambiguity
- eligibility ambiguity
- Asset Intelligence meaning drift
- room-awareness drift
- explainability divergence

## Ownership Preservation Review

Result: PASS

Validated:

- experience governance ownership preserved
- experience definition ownership preserved
- capability governance ownership preserved
- Asset Intelligence ownership preserved
- room truth ownership preserved
- scope truth ownership preserved
- hierarchy truth ownership preserved

No ownership drift introduced in this E6 architecture baseline.

## Readiness Statement

Experience Resolution Consumption Architecture is READY.

This document becomes the authoritative experience resolution baseline for E6.