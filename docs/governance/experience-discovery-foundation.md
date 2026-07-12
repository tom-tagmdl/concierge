# Experience Discovery Foundation

## Purpose

This document defines the authoritative E6 experience discovery foundation baseline.

This document is architecture and governance only.

This document does not define experience governance, experience authorship, experience execution, orchestration, routing, recommendation algorithms, ranking algorithms, or conversational implementation.

## Authority Relationship

Experience Governance Authority remains external through HTBW experience authorities.

Experience Definition Authority remains external through HTBW experience authorities.

Experience Discovery Authority remains external through HTBW discovery authorities.

Coordinator Discovery Authority:

- exposes governed discovery outcomes
- consumes governed experience outcomes and discovery references

Coordinator exposes governed discovery outcomes.

Coordinator does not own experience meaning.

## Dependencies

EX8 consumes:

- `docs/governance/experience-consumption-architecture.md`
- `docs/governance/experience-resolution-consumption-architecture.md`
- `docs/governance/room-aware-experience-consumption-architecture.md`
- `docs/governance/merged-room-experience-consumption-architecture.md`
- `docs/governance/composite-room-experience-consumption-architecture.md`
- `docs/governance/guest-aware-experience-consumption-architecture.md`
- `docs/governance/experience-explainability-framework.md`
- `docs/governance/capability-discovery-foundation.md`

EX8 consumes all.

EX8 redefines none.

## Experience Authority Inputs

EX8 consumes:

- HTBW #18 Experience Model ADR
- HTBW #30 Experience Contract
- HTBW #43 Experience Model

These remain authoritative.

## Experience Discovery Model

Experience discovery means Coordinator presents governed experience outcomes so they can be discovered without redefining experience meaning.

Discoverability means the governed experience set can be surfaced according to bounded consumption, visibility, and lineage rules.

Discovery participation means governed discovery references are carried forward through downstream experience behavior.

This section defines architecture only.

## Discovery Categories

- available experiences
- room-aware experiences
- guest-safe experiences
- capability-linked experiences
- visible experiences
- discoverable experiences

This section defines architecture only.

## Available Experience Discovery

Available experiences participate in discovery by contributing governed available-state context.

Availability participates in discoverability by preserving bounded visibility into experiences that are currently consumable.

This section defines architecture only.

## Room-Aware Discovery Participation

Room-aware experiences participate by preserving room-scoped discovery context from EX3.

Room context influences discoverability by constraining which experiences are visible within room-scoped boundaries.

This section defines architecture only.

## Guest-Safe Discovery Participation

Guest-safe experiences participate by preserving guest-scoped discovery context from EX6.

Guest visibility participates by constraining which experiences are visible under guest-safe policy.

This section defines architecture only.

## Capability-Linked Experience Discovery

Capability-linked experiences participate by preserving governed capability references and lineage.

Capability lineage participates by linking discovery surfaces back to governed capability inputs.

This section defines architecture only.

## Experience Discovery Lineage Framework

Capability Outputs
↓
Experience Consumption
↓
Experience Resolution
↓
Experience Eligibility
↓
Filtering
↓
Visibility
↓
Discoverable Experience Set
↓
Experience Discovery

This framework is architecture only.

## Selection Behavior Participation

Experience selection outcomes participate in discovery as downstream governed outcomes that can be surfaced and referenced.

Selected experiences participate as discoverable outcomes.

Non-selected experiences participate as governed non-discovered outcomes that remain explainable through lineage and visibility references.

This section defines architecture only.

## Explainability Participation

Reference:

- `docs/governance/experience-explainability-framework.md`

Discovery explanations participate by carrying discovery rationale and lineage references.

Discovery rationale participates by explaining why an experience was available, room-aware, guest-safe, or capability-linked.

This section defines architecture only.

## Diagnostics Participation

Reference:

- `docs/governance/capability-diagnostics-surface.md`

Discovery diagnostics references participate by carrying discovery trace references.

Troubleshooting references participate by preserving governed discovery troubleshooting context.

This section defines architecture only.

## Room-Aware Discovery Participation

Room-aware discovery consumes EX3 outputs by preserving room-scoped discovery context and room-aware visibility boundaries.

This section defines architecture only.

## Merged-Room Discovery Participation

Merged-room discovery consumes EX4 outputs by preserving merged-room-scoped discovery context and merged-room visibility boundaries.

This section defines architecture only.

## Composite-Room Discovery Participation

Composite-room discovery consumes EX5 outputs by preserving hierarchy-aware and scope-aware discovery context.

This section defines architecture only.

## Guest-Aware Discovery Participation

Guest-aware discovery consumes EX6 outputs by preserving guest-scoped discovery context and guest visibility boundaries.

This section defines architecture only.

## Asset Intelligence Boundary

Experience discovery may reference outcomes that consumed Asset Intelligence-informed context.

Coordinator does not own Asset Intelligence meaning.

Coordinator does not own Asset Intelligence outputs.

Experience discovery does not reinterpret:

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

EX8 must not assume these outputs exist.

## Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Experience Governance | HTBW experience governance | Consumer | PASS |
| Experience Definitions | HTBW experience authorities | Consumer | PASS |
| Experience Discovery | HTBW discovery authority | Consumer | PASS |
| Capability Discovery | HTBW capability governance | Consumer | PASS |
| Asset Intelligence Outputs | Asset Intelligence | Consumer | PASS |
| Room Truth | HTBW room truth authority | Consumer | PASS |
| Guest Governance | HTBW guest governance authority | Consumer | PASS |

## Dependency Mapping

| Downstream E6 Consumer | E6 Output Dependency |
|---|---|
| EX9 | experience diagnostics integration |
| EX10 | experience readiness review inputs |

## Risks

- experience ownership drift
- discovery drift
- discoverability ambiguity
- visibility ambiguity
- lineage inconsistency
- Asset Intelligence meaning drift
- room-aware discovery divergence
- guest-safe discovery divergence

## Ownership Preservation Review

Result: PASS

Validated:

- experience governance ownership preserved
- experience definition ownership preserved
- capability governance ownership preserved
- Asset Intelligence ownership preserved
- room truth ownership preserved
- guest governance ownership preserved

No ownership drift introduced in this E6 architecture baseline.

## Readiness Statement

Experience Discovery Foundation is READY.

This document becomes the authoritative experience discovery baseline for E6.