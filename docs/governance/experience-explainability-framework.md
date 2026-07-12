# Experience Explainability Framework

## Purpose

This document defines the authoritative E6 experience explainability framework baseline.

This document is architecture and governance only.

This document does not define experience governance, experience authorship, experience execution, orchestration, routing, conversational narration, or explanation generation algorithms.

## Authority Relationship

Experience Governance Authority remains external through HTBW experience authorities.

Experience Definition Authority remains external through HTBW experience authorities.

Experience Explainability Authority remains external through HTBW explainability authorities.

Coordinator Explainability Authority:

- explains governed outcomes
- consumes governed experience outcomes and explainability references

Coordinator explains governed outcomes.

Coordinator does not own experience meaning.

## Dependencies

EX7 consumes:

- `docs/governance/experience-consumption-architecture.md`
- `docs/governance/experience-resolution-consumption-architecture.md`
- `docs/governance/room-aware-experience-consumption-architecture.md`
- `docs/governance/merged-room-experience-consumption-architecture.md`
- `docs/governance/composite-room-experience-consumption-architecture.md`
- `docs/governance/guest-aware-experience-consumption-architecture.md`
- `docs/governance/capability-explainability-framework.md`

EX7 consumes all.

EX7 redefines none.

## Experience Authority Inputs

EX7 consumes:

- HTBW #18 Experience Model ADR
- HTBW #30 Experience Contract
- HTBW #43 Experience Model

These remain authoritative.

## Experience Explainability Model

Experience explainability means Coordinator presents governed reasons and lineage for experience outcomes without redefining experience meaning.

Explanation participation means governed explanation references are carried forward through downstream experience behavior.

Explainability lineage means the consumed experience path from capability outputs through experience outcomes to explanation artifacts remains traceable and bounded.

This section defines architecture only.

## Explanation Categories

- selection explanation
- eligibility explanation
- restriction explanation
- availability explanation
- visibility explanation
- filtering explanation

This section defines architecture only.

## Machine-Readable Explanation Model

Machine-readable explanation references participate as structured governed references to outcomes, lineage, and ownership boundaries.

Lineage references participate as machine-consumable pointers to the consumed path of governed inputs.

This section defines architecture only.

## Human-Readable Explanation Model

Human-readable explanations participate as bounded narrative representations of governed outcomes.

Explanation summaries participate as concise summaries of why an experience was selected, eligible, unavailable, restricted, filtered, visible, or hidden.

This section defines architecture only.

## Experience Lineage Framework

Capability Outputs
↓
Experience Consumption
↓
Experience Resolution
↓
Eligibility
↓
Filtering
↓
Visibility
↓
Experience Outcome
↓
Experience Explanation

This framework is architecture only.

## Selection Explainability

Selected experiences participate in explanations by carrying the governed reason chain that led to the selected outcome.

This section defines architecture only.

## Eligibility Explainability

Eligible experiences participate in explanations by carrying governed eligibility reasons and lineage references.

This section defines architecture only.

## Restriction Explainability

Restricted experiences participate in explanations by carrying governed restriction reasons and boundary references.

This section defines architecture only.

## Filtering Explainability

Filtered experiences participate in explanations by carrying governed filter reasons and visibility impact references.

This section defines architecture only.

## Visibility Explainability

Visible experiences participate in explanations by carrying the reason they remain visible.

Hidden experiences participate in explanations by carrying the reason they are not visible.

This section defines architecture only.

## Room-Aware Explainability Participation

Room-aware explanations participate by preserving room-scoped explanation context from EX3.

This section defines architecture only.

## Merged-Room Explainability Participation

Merged-room explanations participate by preserving merged-room-scoped explanation context from EX4.

This section defines architecture only.

## Composite-Room Explainability Participation

Composite-room explanations participate by preserving hierarchy-aware and scope-aware explanation context from EX5.

This section defines architecture only.

## Guest-Aware Explainability Participation

Guest-aware explanations participate by preserving guest-scoped explanation context from EX6.

This section defines architecture only.

## Asset Intelligence Boundary

Experience explainability may reference outcomes that consumed Asset Intelligence-informed context.

Coordinator does not own Asset Intelligence meaning.

Coordinator does not own Asset Intelligence outputs.

Experience explainability does not reinterpret:

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

EX7 must not assume these outputs exist.

## Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Experience Governance | HTBW experience governance | Consumer | PASS |
| Experience Definitions | HTBW experience authorities | Consumer | PASS |
| Experience Explainability | HTBW explainability authority | Consumer | PASS |
| Capability Explainability | HTBW capability governance | Consumer | PASS |
| Asset Intelligence Outputs | Asset Intelligence | Consumer | PASS |
| Room Truth | HTBW room truth authority | Consumer | PASS |
| Guest Governance | HTBW guest governance authority | Consumer | PASS |

## Dependency Mapping

| Downstream E6 Consumer | E6 Output Dependency |
|---|---|
| EX8 | experience diagnostics integration |
| EX9 | experience discovery integration |
| EX10 | experience readiness review inputs |

## Risks

- experience ownership drift
- explanation drift
- lineage inconsistency
- explainability ambiguity
- Asset Intelligence meaning drift
- human-readable explanation divergence
- machine-readable explanation divergence

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

Experience Explainability Framework is READY.

This document becomes the authoritative experience explainability baseline for E6.