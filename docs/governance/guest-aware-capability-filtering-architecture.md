# Guest-Aware Capability Filtering Architecture

## Purpose

This document defines the authoritative E5-CP6 architecture baseline for guest-aware capability filtering.

This document is architecture and governance only.

This document does not define implementation, filtering algorithms, execution eligibility algorithms, routing algorithms, capability-selection algorithms, or occupancy engines.

## Authority Relationship

Capability Governance Authority remains external through capability governance ADR, contract, and model authorities.

Eligibility Authority remains external through governed policy and capability governance authorities.

Occupancy Authority remains external through occupancy and presence truth authorities.

Coordinator Consumption Authority:

- consumes guest-safe capability projections
- consumes guest visibility surfaces
- consumes guest eligibility context

Coordinator consumes guest-safe capability projections.

Coordinator does not own eligibility governance.

## CP1 / CP2 / CP3 / CP4 / CP5 Dependencies

CP6 consumes:

- `docs/governance/capability-consumption-architecture.md`
- `docs/governance/capability-resolution-pipeline-architecture.md`
- `docs/governance/room-aware-capability-consumption-architecture.md`
- `docs/governance/merged-room-capability-consumption-architecture.md`
- `docs/governance/composite-room-capability-consumption-architecture.md`

Dependency boundaries:

- CP1 defines capability consumption.
- CP2 defines capability resolution.
- CP3 defines room-aware behavior.
- CP4 defines merged-room behavior.
- CP5 defines composite-room behavior.
- CP6 defines guest-aware filtering.

CP6 consumes all prior capability artifacts.

CP6 redefines none of them.

## Completed E4 Guest-Safe Inputs

CP6 consumes:

- room-aware vocabulary outputs
- discovery outputs
- explainability references
- diagnostics references
- validation outputs
- guest-safe visibility boundaries
- guest-safe vocabulary boundaries

Inherited inputs consumed:

- room-aware outputs
- merged-room outputs
- composite-room outputs

RV8a guest-aware inputs consumed through E4:

- asset labels
- asset type/category
- asset identity/name metadata
- Concierge `asset_groups`
- room-context outputs

CP6 consumes these inputs.

CP6 does not redefine these inputs.

## Guest-Aware Capability Model

Guest-safe capability means a capability projection is consumable within guest-safe visibility and restriction boundaries.

Restricted capability means a capability projection is present but constrained for guest context consumption.

Guest visibility means which capability projections are visible under guest-safe boundaries.

Guest execution eligibility means execution-eligibility participation references consumed from external governance/authority inputs.

This section defines architecture only.

## Guest Eligibility Model

Guest eligibility architecture states:

- guest-visible capability
- guest-hidden capability
- guest-executable capability
- guest-restricted capability

This section defines architecture only.

## Guest-Aware Capability Filtering Pipeline

Capability Projection
  -> Guest Context
  -> Visibility Evaluation
  -> Restriction Evaluation
  -> Guest Capability Projection
  -> Explainability References
  -> Diagnostics References

Pipeline behavior is deterministic and explainable.

No algorithm is defined.

## Guest Visibility Boundary

CP6 consumes guest visibility boundaries as inputs from completed E4 and governed capability artifacts.

CP6 consumes guest visibility boundaries.

CP6 does not define visibility authority.

## Guest Execution Eligibility Boundary

CP6 consumes execution eligibility inputs as externally governed signals.

CP6 consumes eligibility inputs.

CP6 does not own eligibility governance.

## Household-Facing Outcome Preservation

Grounded in:

- `docs/governance/concierge-v1-outcome-preservation-baseline.md`
- `docs/governance/v1-to-v2-capability-parity-matrix.md`
- `docs/governance/v1-outcome-regression-checklist.md`
- `docs/governance/v1-preservation-readiness-review.md`

Preserved requirements:

- preserved guest-safe behavior
- preserved restriction behavior
- preserved visibility expectations
- preserved household-facing outcomes

Internal mechanisms may change.

Observable guest-safe outcomes remain authoritative.

## Explainability Participation

Reference:

- `docs/governance/vocabulary-explainability-framework.md`

Guest-aware explainability participation includes propagation of guest visibility and restriction rationale references.

## Diagnostics Participation

Reference:

- `docs/governance/vocabulary-diagnostics-framework.md`

Guest-aware diagnostics participation includes propagation of guest visibility, restriction, and fallback diagnostics references.

## Discovery Participation

Reference:

- `docs/governance/vocabulary-discovery-framework.md`

Guest-aware discovery participation includes consumption of guest-safe discovery outputs and preservation of guest visibility boundaries.

## Validation Participation

Reference:

- `docs/governance/vocabulary-validation-framework.md`

Guest-aware validation participation includes consumption of validation outcomes and propagation of validation-state references into guest-aware capability outcomes.

## Asset Intelligence Boundary

Grounded in:

- #190
- #79
- #80
- #187
- `docs/governance/capability-consumption-architecture.md`
- `docs/governance/capability-resolution-pipeline-architecture.md`
- `docs/governance/room-aware-capability-consumption-architecture.md`
- `docs/governance/merged-room-capability-consumption-architecture.md`
- `docs/governance/composite-room-capability-consumption-architecture.md`

CP6 may consume:

- guest-safe vocabulary boundaries
- Asset Intelligence-informed room context
- explainability references
- diagnostics references

CP6 may reference:

- Asset Intelligence-authored outputs

CP6 does not own:

- asset evaluation
- environmental evaluation
- advisory generation
- risk generation
- human_health generation
- significance
- relevance

Coordinator consumes Asset Intelligence-informed guest context.

Coordinator does not own Asset Intelligence outputs.

## Nonexistent Output Protection

Current implementation does not expose first-class:

- significance assessments
- relevance assessments
- asset narratives
- room-health narratives
- collection narratives

Guest-aware capability filtering must not assume those outputs exist.

## Resolution Failure Model

Guest-aware failure categories:

- guest context unavailable
- visibility unavailable
- restricted capability
- ineligible execution
- invalid guest context

This section defines architecture only.

No runtime algorithm is defined.

## Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Capability Governance | HTBW capability governance | Consumer | PASS |
| Eligibility Governance | external policy and capability governance authorities | Consumer | PASS |
| Occupancy Truth | occupancy/presence authority | Consumer | PASS |
| Identity Truth | identity authority | Consumer | PASS |
| Room Truth | Foundation | Consumer | PASS |
| Vocabulary Governance | HTBW room vocabulary governance | Consumer | PASS |
| Asset Intelligence Outputs | Asset Intelligence | Consumer | PASS |
| Explainability | governed explainability artifacts | Consumer | PASS |
| Diagnostics | governed diagnostics artifacts | Consumer | PASS |

## Dependency Mapping

| Downstream Issue | CP6 Output Dependency |
|---|---|
| #87 | guest-aware explainability propagation into capability explainability surfaces |
| #88 | guest-aware discovery participation into capability discovery surfaces |
| #89 | guest-aware diagnostics propagation into capability diagnostics surfaces |
| #90 | readiness validation for guest-safe ownership and household-facing outcome preservation |

## Risks

- guest-safe regression
- occupancy-truth drift
- eligibility-governance drift
- ownership drift
- E4/E5 boundary drift
- diagnostics drift
- explainability drift

## Ownership Preservation Review

Result: PASS

Validated:

- occupancy truth ownership preserved
- eligibility governance ownership preserved
- capability governance ownership preserved
- vocabulary ownership preserved
- Asset Intelligence ownership preserved

No ownership drift introduced in CP6 architecture baseline.

## Readiness Statement

Guest-Aware Capability Filtering Architecture is READY.

This document becomes the authoritative guest-aware capability filtering baseline for E5.