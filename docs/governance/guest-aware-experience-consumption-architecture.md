# Guest-Aware Experience Consumption Architecture

## Purpose

This document defines the authoritative E6 guest-aware experience consumption architecture baseline.

This document is architecture and governance only.

This document does not define experience governance, eligibility governance, guest governance, restriction governance, experience execution, orchestration, routing, or selection algorithms.

## Authority Relationship

Experience Governance Authority remains external through HTBW experience authorities.

Experience Definition Authority remains external through HTBW experience authorities.

Guest Eligibility Authority remains external through HTBW guest eligibility authorities.

Guest Restriction Authority remains external through HTBW guest restriction authorities.

Guest Visibility Authority remains external through HTBW guest visibility authorities.

Coordinator Guest-Aware Consumption Authority:

- consumes guest-aware experience inputs
- integrates guest context with governed experience consumption, resolution, room-aware, merged-room, and composite-room inputs

Coordinator consumes guest-aware experience inputs.

Coordinator does not own guest governance.

## Dependencies

EX6 consumes:

- `docs/governance/experience-consumption-architecture.md`
- `docs/governance/experience-resolution-consumption-architecture.md`
- `docs/governance/room-aware-experience-consumption-architecture.md`
- `docs/governance/merged-room-experience-consumption-architecture.md`
- `docs/governance/composite-room-experience-consumption-architecture.md`
- `docs/governance/guest-aware-capability-filtering-architecture.md`
- `docs/governance/capability-explainability-framework.md`
- `docs/governance/capability-diagnostics-surface.md`
- `docs/governance/capability-discovery-foundation.md`

EX6 also consumes the relevant E5 guest-aware capability outputs:

- CP6 Guest-Aware Capability Filtering
- CP7 Capability Explainability
- CP8 Capability Discovery
- CP9 Capability Diagnostics

EX6 consumes all.

EX6 redefines none.

## Experience Authority Inputs

EX6 consumes:

- HTBW #18 Experience Model ADR
- HTBW #30 Experience Contract
- HTBW #43 Experience Model

These remain authoritative.

## Guest-Aware Experience Consumption Model

Guest-aware experience consumption means Coordinator consumes governed experience inputs together with guest context so experience behavior can remain guest-sensitive without transferring guest governance.

Guest-safe behavior means guest context is used to preserve guest-safe visibility, restriction, and eligibility boundaries.

Guest eligibility participation means guest context contributes to the guest-aware state boundary for consumed experiences.

Guest visibility means the set of experiences visible to a guest is bounded by governed guest context and downstream filtering.

This section defines architecture only.

## Guest Eligibility Model

Guest context participates in eligible experiences by contributing governed guest-scoped context to the eligibility boundary.

Guest context participates in restricted experiences by preserving bounded guest constraints without redefining guest governance.

Guest context participates in unavailable experiences by preserving explicit non-availability under active guest-scoped context.

Guest context participates in available experiences by preserving guest-scoped visibility and consumability under governed context.

This section defines architecture only.

## Guest Restriction Model

Restriction states participate as governed outcomes that constrain guest-visible experience behavior.

Restriction boundaries participate as explicit guest-safe limits on visibility and consumption.

Restricted experiences participate as governed outputs that remain visible only within bounded guest-safe conditions.

This section defines architecture only.

## Guest-Visible Experience Model

Guest-visible experiences participate as governed outputs that remain visible to the current guest under active guest policy.

Guest-hidden experiences participate as governed outputs that are intentionally hidden from guest-visible surfaces.

Visibility boundaries participate as external guest-safe constraints on experience behavior.

This section defines architecture only.

## Guest-Aware Filtering Model

Guest filtering participates by constraining the visible experience set according to governed guest context.

Guest-safe filtering participates by preserving guest-safe visibility and restriction boundaries.

This section defines architecture only.

## Guest-Aware Resolution Participation

Guest eligibility participates in experience resolution by constraining which governed experiences may remain visible or consumable.

Guest restrictions participate in experience resolution by preserving guest-safe non-visibility and bounded consumption states.

This section defines architecture only.

## Guest-Aware Resolution Pipeline

Guest Context
↓
Capability Outputs
↓
Experience Consumption
↓
Experience Resolution
↓
Guest Eligibility
↓
Guest Restriction Evaluation
↓
Guest-Aware Filtering
↓
Visible Experience Set
↓
Experience Outcome

This pipeline is architecture only.

No algorithms are defined here.

## Deterministic Guest-Aware Behavior

Deterministic guest-aware behavior is achieved by preserving the same guest authority boundaries, the same consumed inputs, and the same guest-scoped state categories.

Guest context participates consistently by remaining governed input rather than mutable ownership.

Restriction participation remains deterministic by preserving explicit restriction states and visibility boundaries.

This section defines architecture only.

## Explainability Participation

Reference:

- `docs/governance/capability-explainability-framework.md`

Guest-aware explanations participate by carrying guest lineage, guest eligibility rationale, guest restriction rationale, and guest visibility rationale.

Eligibility explanations participate by describing why a guest-scoped experience is eligible, restricted, or unavailable.

Restriction explanations participate by describing why a guest-scoped experience is constrained or hidden.

Visibility explanations participate by describing why a guest-scoped experience is visible or hidden.

This section defines architecture only.

## Diagnostics Participation

Reference:

- `docs/governance/capability-diagnostics-surface.md`

Guest-aware traces participate by preserving guest-scoped resolution and filtering trace references.

Restriction traces participate by preserving guest-safe troubleshooting context for restriction states.

Troubleshooting references participate by preserving deterministic guest-aware troubleshooting context.

This section defines architecture only.

## Discovery Participation

Reference:

- `docs/governance/capability-discovery-foundation.md`

Guest-aware discovery participates by exposing guest-scoped discovery context for governed experience surfaces.

Guest-visible discovery participates by exposing the governed visible subset for guest-facing surfaces.

This section defines architecture only.

## Guest Governance Protection

Guest eligibility governance remains external.

Guest restriction governance remains external.

Guest visibility governance remains external.

Guest context is consumed.

Ownership is not transferred.

Coordinator does not become guest-governance authority.

## Asset Intelligence Boundary

Guest-aware experience consumption may consume capability outputs that consumed Asset Intelligence-informed context.

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

EX6 must not assume these outputs exist.

## Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Experience Governance | HTBW experience governance | Consumer | PASS |
| Experience Definitions | HTBW experience authorities | Consumer | PASS |
| Guest Eligibility Governance | HTBW guest eligibility authority | Consumer | PASS |
| Guest Restriction Governance | HTBW guest restriction authority | Consumer | PASS |
| Guest Visibility Governance | HTBW guest visibility authority | Consumer | PASS |
| Capability Outputs | HTBW capability governance | Consumer | PASS |
| Asset Intelligence Outputs | Asset Intelligence | Consumer | PASS |
| Explainability | governed explainability artifacts | Consumer | PASS |
| Diagnostics | governed diagnostics artifacts | Consumer | PASS |

## Dependency Mapping

| Downstream E6 Consumer | E6 Output Dependency |
|---|---|
| EX7 | experience explainability integration |
| EX8 | experience diagnostics integration |
| EX9 | experience discovery integration |

## Risks

- experience ownership drift
- guest governance drift
- eligibility ambiguity
- restriction ambiguity
- visibility ambiguity
- Asset Intelligence meaning drift
- explainability divergence
- diagnostics divergence

## Ownership Preservation Review

Result: PASS

Validated:

- experience governance ownership preserved
- experience definition ownership preserved
- guest governance ownership preserved
- capability governance ownership preserved
- Asset Intelligence ownership preserved

No ownership drift introduced in this E6 architecture baseline.

## Readiness Statement

Guest-Aware Experience Consumption Architecture is READY.

This document becomes the authoritative guest-aware experience baseline for E6.