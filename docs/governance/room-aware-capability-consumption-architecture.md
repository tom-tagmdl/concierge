# Room-Aware Capability Consumption Architecture

## Purpose

This document defines the authoritative E5-CP3 architecture baseline for room-aware capability consumption.

This document is architecture and governance only.

This document does not define implementation, capability selection logic, filtering algorithms, targeting algorithms, execution behavior, or ranking/scoring behavior.

## Authority Relationship

Room Truth Authority remains external through Foundation truth governance.

Capability Governance Authority remains external through:

- capability-projection governance ADR authority
- `homes_that_behave_well/docs/contracts/capability-projection-contract.md`
- `homes_that_behave_well/docs/models/capability-projection-model.md`

Coordinator Consumption Authority:

- consumes room-aware capability projections
- consumes room context and room-aware vocabulary outputs

Coordinator does not own room truth.

## CP1 and CP2 Dependencies

CP3 consumes:

- `docs/governance/capability-consumption-architecture.md`
- `docs/governance/capability-resolution-pipeline-architecture.md`

Dependency boundaries:

- CP1 defines capability consumption.
- CP2 defines capability resolution.
- CP3 defines room-aware capability consumption.

CP3 consumes both.

CP3 does not redefine either.

## Completed E4 Room-Aware Inputs

CP3 consumes:

- room-aware vocabulary resolution
- room-context explainability references
- room-context diagnostics references
- room-context validation outputs
- room-aware discovery outputs

RV8a room-aware inputs consumed through E4:

- asset labels
- asset categories
- asset identity metadata
- `asset_groups`
- room-context outputs

CP3 consumes these inputs and does not redefine them.

## Room-Aware Capability Model

Room-aware capability projection means capability projections are consumed with explicit room-context influence from governed room truth and governed room-aware vocabulary outputs.

Room eligibility means the room context is valid for evaluating capability projection consumption state under governed inputs.

Room-aware consumption means Coordinator resolves and consumes capability projection outcomes in the context of a resolved room scope without acquiring room truth or capability governance ownership.

This section is architecture only.

## Room Eligibility Model

Room eligibility architecture states:

- eligible room: resolved room context supports room-aware capability consumption
- ineligible room: resolved room context exists but does not satisfy room-aware capability consumption constraints
- unavailable room: room context is unresolved, stale, or unavailable for consumption at decision time
- unsupported room: room context cannot support the requested room-aware capability projection surface

This is architecture only.

## Room-Aware Capability Consumption Pipeline

Room Context
  -> Vocabulary Context
  -> Capability Resolution
  -> Room Eligibility Evaluation
  -> Room-Aware Capability Projection
  -> Explainability References
  -> Diagnostics References

Pipeline behavior is deterministic and explainable.

No algorithm is defined.

## Room Targeting Boundary

CP3 consumes room targeting context as an input from governed room truth and completed E4 room-aware vocabulary resolution outputs.

CP3 does not create room truth.

CP3 does not redefine targeting governance.

## Explainability Participation

Reference:

- `docs/governance/vocabulary-explainability-framework.md`

Room-aware explainability participation includes:

- propagation of room-context references through capability-consumption outcomes
- propagation of room eligibility rationale references
- ownership-boundary explanation for consumed outputs

## Diagnostics Participation

Reference:

- `docs/governance/vocabulary-diagnostics-framework.md`

Room-aware diagnostics participation includes:

- propagation of room-context diagnostics references
- propagation of room eligibility outcome references
- visibility into room-unavailable, ineligible, and unsupported room conditions

## Discovery Participation

Reference:

- `docs/governance/vocabulary-discovery-framework.md`

Room-aware discovery participation includes:

- consumption of room-aware discovery outputs as contextual inputs to room-aware capability consumption
- preservation of guest-safe discovery boundaries
- preservation of discovery ownership boundaries

## Validation Participation

Reference:

- `docs/governance/vocabulary-validation-framework.md`

Room-aware validation participation includes:

- consumption of room-context validation outcomes
- propagation of validation state references into room-aware capability outcomes
- preservation of external validation authority

## Asset Intelligence Boundary

Grounded in:

- #190
- #79
- #80
- #187
- `docs/governance/capability-consumption-architecture.md`
- `docs/governance/capability-resolution-pipeline-architecture.md`

CP3 may consume:

- room-context-aware vocabulary anchors
- Asset Intelligence-informed room context
- diagnostics references
- explainability references

CP3 may reference:

- Asset Intelligence-authored outputs

CP3 does not own:

- asset evaluation
- environmental evaluation
- advisory generation
- risk generation
- human_health generation
- significance
- relevance

Coordinator consumes Asset Intelligence-informed room context.

Coordinator does not own Asset Intelligence outputs.

## Nonexistent Output Protection

Current implementation does not expose first-class:

- significance assessments
- relevance assessments
- asset narratives
- room-health narratives
- collection narratives

Room-aware capability consumption must not assume those outputs exist.

## Resolution Failure Model

Room-aware failure categories:

- room unavailable
- room not eligible
- capability unavailable in room
- unsupported room projection
- invalid room context

This section defines architecture only.

No runtime algorithm is defined.

## Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Room Truth | Foundation | Consumer | PASS |
| Room Context | Foundation and Context Assembly governed outputs | Consumer | PASS |
| Capability Governance | HTBW capability governance | Consumer | PASS |
| Vocabulary Governance | HTBW room vocabulary governance | Consumer | PASS |
| Asset Labels | Asset Intelligence exposed metadata | Consumer | PASS |
| Asset Type / Category | Asset Intelligence exposed metadata | Consumer | PASS |
| Asset Identity Metadata | Asset Intelligence exposed metadata | Consumer | PASS |
| Asset Intelligence Outputs | Asset Intelligence | Consumer | PASS |
| Explainability | governed explainability artifacts | Consumer | PASS |
| Diagnostics | governed diagnostics artifacts | Consumer | PASS |

## Dependency Mapping

| Downstream Issue | CP3 Output Dependency |
|---|---|
| #84 | merged-room capability consumption consumes room-aware capability baseline |
| #85 | composite-room capability consumption consumes room-aware capability baseline |
| #86 | guest-aware filtering consumes room eligibility and room-aware projection boundaries |
| #87 | capability explainability consumes room-aware explainability propagation |
| #88 | capability discovery consumes room-aware discovery participation outputs |
| #89 | capability diagnostics consumes room-aware diagnostics propagation outputs |
| #90 | E5 readiness review consumes CP3 room-aware ownership and boundary validations |

## Risks

- room truth drift
- ownership drift
- E4/E5 boundary drift
- diagnostics drift
- explainability drift
- discovery drift

## Ownership Preservation Review

Result: PASS

Validated:

- room truth ownership preserved
- vocabulary ownership preserved
- capability governance ownership preserved
- Asset Intelligence ownership preserved

No ownership drift introduced in CP3 architecture baseline.

## Readiness Statement

Room-Aware Capability Consumption Architecture is READY.

This document becomes the authoritative room-aware capability consumption baseline for E5.