# Merged-Room Capability Consumption Architecture

## Purpose

This document defines the authoritative E5-CP4 architecture baseline for merged-room capability consumption.

This document is architecture and governance only.

This document does not define implementation, capability-selection logic, filtering algorithms, targeting algorithms, execution behavior, ranking behavior, or scoring behavior.

## Authority Relationship

Merged-Room Authority remains external through governed merged-room definitions and preservation contracts.

Capability Governance Authority remains external through capability governance ADR, contract, and model authorities.

Coordinator Consumption Authority:

- consumes merged-room capability projections
- consumes merged-room context and merged-room vocabulary resolution outputs

Coordinator does not own merged-room truth.

## CP1 / CP2 / CP3 Dependencies

CP4 consumes:

- `docs/governance/capability-consumption-architecture.md`
- `docs/governance/capability-resolution-pipeline-architecture.md`
- `docs/governance/room-aware-capability-consumption-architecture.md`

Dependency boundaries:

- CP1 defines capability consumption.
- CP2 defines capability resolution.
- CP3 defines room-aware capability consumption.
- CP4 defines merged-room capability consumption.

CP4 consumes all three.

CP4 redefines none of them.

## Completed E4 Merged-Room Inputs

CP4 consumes:

- merged-room vocabulary resolution
- merged-room explainability references
- merged-room diagnostics references
- merged-room validation outputs

Inherited room-aware inputs consumed:

- room-aware vocabulary resolution
- room-context explainability references
- room-context diagnostics references
- room-context validation outputs

RV8a merged-room inputs consumed through E4:

- asset labels
- asset type/category
- asset identity/name metadata
- Concierge `asset_groups`
- merged-room resolution outputs

CP4 consumes these inputs.

CP4 does not redefine these inputs.

## Merged-Room Capability Model

Merged-room capability projection means capability projections are consumed in the context of a resolved merged-room scope as a household-facing group outcome.

Merged-room capability visibility means visibility and eligibility of capability projections are consumed under merged-room context boundaries and preserved household-facing scope expectations.

Merged-room capability consumption means Coordinator consumes and propagates merged-room-scoped capability outcomes while preserving external truth and governance ownership.

This section defines architecture only.

## Merged-Room Eligibility Model

Merged-room eligibility architecture states:

- eligible merged room: merged-room context is valid for merged-room capability consumption
- ineligible merged room: merged-room context exists but does not satisfy merged-room capability consumption constraints
- unavailable merged room: merged-room context is unresolved, stale, or unavailable at decision time
- unsupported merged room: merged-room context cannot support the requested merged-room capability projection surface

This section defines architecture only.

## Merged-Room Capability Consumption Pipeline

Merged-Room Context
  -> Vocabulary Context
  -> Capability Resolution
  -> Merged-Room Eligibility Evaluation
  -> Merged-Room Capability Projection
  -> Explainability References
  -> Diagnostics References

Pipeline behavior is deterministic and explainable.

No algorithm is defined.

## Merged-Room Targeting Boundary

CP4 consumes merged-room targeting context from governed merged-room and room-context resolution outputs.

CP4 does not create merged-room truth.

CP4 does not redefine merged-room governance.

## Household-Facing Outcome Preservation

Grounded in:

- `docs/governance/merged-room-outcome-preservation-contract.md`
- `docs/governance/concierge-v1-outcome-preservation-baseline.md`
- `docs/governance/v1-to-v2-capability-parity-matrix.md`
- `docs/governance/v1-outcome-regression-checklist.md`
- `docs/governance/v1-preservation-readiness-review.md`

Preserved merged-room behavior requirements:

- merged-room scope remains a meaningful household-facing capability context where configured
- merged-room capability visibility remains deterministic and explainable
- merged-room capability outcomes preserve household-facing scope expectations

Preserved merged-room outcomes remain authoritative.

Internal mechanisms may change.

Observable outcomes remain authoritative.

## Explainability Participation

Reference:

- `docs/governance/vocabulary-explainability-framework.md`

Merged-room explainability participation includes:

- propagation of merged-room scope references through capability outcomes
- propagation of merged-room eligibility rationale references
- preservation of ownership-boundary explanation

## Diagnostics Participation

Reference:

- `docs/governance/vocabulary-diagnostics-framework.md`

Merged-room diagnostics participation includes:

- propagation of merged-room diagnostics references
- visibility into merged-room unavailable, ineligible, and unsupported outcomes
- deterministic merged-room trace participation for supportability

## Discovery Participation

Reference:

- `docs/governance/vocabulary-discovery-framework.md`

Merged-room discovery participation includes:

- consumption of merged-room discovery outputs for contextual capability visibility
- preservation of guest-safe discovery boundaries
- preservation of discovery ownership boundaries

## Validation Participation

Reference:

- `docs/governance/vocabulary-validation-framework.md`

Merged-room validation participation includes:

- consumption of merged-room validation outcomes
- propagation of validation state references through merged-room capability outcomes
- preservation of external validation authority

## Asset Intelligence Boundary

Grounded in:

- #190
- #79
- #80
- #187
- `docs/governance/capability-consumption-architecture.md`
- `docs/governance/capability-resolution-pipeline-architecture.md`
- `docs/governance/room-aware-capability-consumption-architecture.md`

CP4 may consume:

- merged-room vocabulary anchors
- Asset Intelligence-informed merged-room context
- diagnostics references
- explainability references

CP4 may reference:

- Asset Intelligence-authored outputs

CP4 does not own:

- asset evaluation
- environmental evaluation
- advisory generation
- risk generation
- human_health generation
- significance
- relevance

Coordinator consumes Asset Intelligence-informed merged-room context.

Coordinator does not own Asset Intelligence outputs.

## Nonexistent Output Protection

Current implementation does not expose first-class:

- significance assessments
- relevance assessments
- asset narratives
- room-health narratives
- collection narratives

Merged-room capability consumption must not assume these outputs exist.

## Resolution Failure Model

Merged-room failure categories:

- merged room unavailable
- merged room not eligible
- capability unavailable in merged room
- unsupported merged-room projection
- invalid merged-room context

This section defines architecture only.

No runtime algorithm is defined.

## Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Merged-Room Truth | governed merged-room definitions and preservation authority | Consumer | PASS |
| Room Truth | Foundation | Consumer | PASS |
| Capability Governance | HTBW capability governance | Consumer | PASS |
| Vocabulary Governance | HTBW room vocabulary governance | Consumer | PASS |
| Asset Labels | Asset Intelligence exposed metadata | Consumer | PASS |
| Asset Type / Category | Asset Intelligence exposed metadata | Consumer | PASS |
| Asset Identity Metadata | Asset Intelligence exposed metadata | Consumer | PASS |
| Asset Intelligence Outputs | Asset Intelligence | Consumer | PASS |
| Explainability | governed explainability artifacts | Consumer | PASS |
| Diagnostics | governed diagnostics artifacts | Consumer | PASS |

## Dependency Mapping

| Downstream Issue | CP4 Output Dependency |
|---|---|
| #85 | composite-room capability consumption alignment with merged-room outcome boundaries |
| #86 | guest-aware filtering constraints for merged-room capability visibility |
| #87 | merged-room explainability propagation into capability explainability surfaces |
| #88 | merged-room discovery participation into capability discovery surfaces |
| #89 | merged-room diagnostics propagation into capability diagnostics surfaces |
| #90 | readiness validation for merged-room ownership and household-facing outcome preservation |

## Risks

- merged-room truth drift
- household-facing regression
- ownership drift
- E4/E5 boundary drift
- diagnostics drift
- explainability drift

## Ownership Preservation Review

Result: PASS

Validated:

- merged-room truth ownership preserved
- room truth ownership preserved
- vocabulary ownership preserved
- capability governance ownership preserved
- Asset Intelligence ownership preserved

No ownership drift introduced in CP4 architecture baseline.

## Readiness Statement

Merged-Room Capability Consumption Architecture is READY.

This document becomes the authoritative merged-room capability consumption baseline for E5.