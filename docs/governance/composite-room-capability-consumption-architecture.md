# Composite-Room Capability Consumption Architecture

## Purpose

This document defines the authoritative E5-CP5 architecture baseline for composite-room capability consumption.

This document is architecture and governance only.

This document does not define implementation, capability-selection logic, hierarchy traversal algorithms, scope-expansion algorithms, targeting algorithms, execution behavior, ranking behavior, or scoring behavior.

## Authority Relationship

Composite-Room Authority remains external through governed composite-room definitions and preservation contracts.

Hierarchy Truth Authority remains external through governed hierarchy definitions.

Scope Truth Authority remains external through governed scope definitions.

Capability Governance Authority remains external through capability governance ADR, contract, and model authorities.

Coordinator Consumption Authority:

- consumes composite-room capability projections
- consumes hierarchy and scope context

Coordinator does not own hierarchy truth.

Coordinator does not own scope truth.

## CP1 / CP2 / CP3 / CP4 Dependencies

CP5 consumes:

- `docs/governance/capability-consumption-architecture.md`
- `docs/governance/capability-resolution-pipeline-architecture.md`
- `docs/governance/room-aware-capability-consumption-architecture.md`
- `docs/governance/merged-room-capability-consumption-architecture.md`

Dependency boundaries:

- CP1 defines capability consumption.
- CP2 defines capability resolution.
- CP3 defines room-aware capability consumption.
- CP4 defines merged-room capability consumption.
- CP5 defines composite-room capability consumption.

CP5 consumes all prior capability artifacts.

CP5 redefines none of them.

## Completed E4 Composite-Room Inputs

CP5 consumes:

- composite-room vocabulary resolution
- hierarchy traversal outputs
- scope expansion outputs
- explainability references
- diagnostics references
- validation outputs

Inherited inputs consumed:

- room-aware outputs
- merged-room outputs
- discovery outputs

RV8a composite-room inputs consumed through E4:

- asset labels
- asset type/category
- asset identity/name metadata
- Concierge `asset_groups`
- composite-room resolution outputs
- hierarchy-aware room context

CP5 consumes these inputs.

CP5 does not redefine these inputs.

## Composite-Room Capability Model

Composite-room capability projection means capability projections are consumed in the context of resolved composite-room scope behavior.

Floor capability projection means capability projections are consumed in floor-aware context where floor scope is part of composite/hierarchy participation.

Hierarchy-aware capability visibility means capability visibility is consumed with explicit hierarchy context boundaries.

Scope inheritance means consumed capability context may inherit valid scope context from governed hierarchy and expansion outputs.

This section defines architecture only.

## Composite-Room Eligibility Model

Composite-room eligibility architecture states:

- eligible composite room: composite-room context is valid for capability consumption
- ineligible composite room: composite-room context exists but does not satisfy capability consumption constraints
- unavailable composite room: composite-room context is unresolved, stale, or unavailable at decision time
- unsupported composite room: composite-room context cannot support requested capability projection surface

This section defines architecture only.

## Composite-Room Capability Consumption Pipeline

Composite-Room Context
  -> Hierarchy Context
  -> Scope Context
  -> Vocabulary Context
  -> Capability Resolution
  -> Composite-Room Eligibility Evaluation
  -> Composite-Room Capability Projection
  -> Explainability References
  -> Diagnostics References

Pipeline behavior is deterministic and explainable.

No algorithm is defined.

## Hierarchy Traversal Participation

CP5 consumes hierarchy traversal outputs from completed E4 artifacts as inputs into composite-room capability consumption.

CP5 consumes hierarchy traversal results.

CP5 does not define hierarchy truth.

## Scope Inheritance Participation

CP5 consumes scope-expansion outputs from completed E4 artifacts as inputs into composite-room capability consumption.

CP5 consumes scope-expansion outputs.

CP5 does not define scope truth.

## Composite-Room Targeting Boundary

CP5 consumes composite-room targeting context from governed room/scope/hierarchy resolution outputs.

CP5 does not create room truth, scope truth, or hierarchy truth.

## Household-Facing Outcome Preservation

Grounded in:

- `docs/governance/composite-room-scope-outcome-preservation-contract.md`
- `docs/governance/concierge-v1-outcome-preservation-baseline.md`
- `docs/governance/v1-to-v2-capability-parity-matrix.md`
- `docs/governance/v1-outcome-regression-checklist.md`
- `docs/governance/v1-preservation-readiness-review.md`

Preserved requirements:

- preserved composite-room behavior
- preserved hierarchy behavior
- preserved scope-inheritance behavior
- preserved household-facing expectations

Internal mechanisms may change.

Observable outcomes remain authoritative.

## Explainability Participation

Reference:

- `docs/governance/vocabulary-explainability-framework.md`

CP5 explainability participation includes propagation of composite-room, hierarchy, and scope-context rationale references.

## Diagnostics Participation

Reference:

- `docs/governance/vocabulary-diagnostics-framework.md`

CP5 diagnostics participation includes propagation of composite-room, hierarchy, and scope diagnostics references for deterministic troubleshooting.

## Discovery Participation

Reference:

- `docs/governance/vocabulary-discovery-framework.md`

CP5 discovery participation includes consumption of composite/hierarchy-relevant discovery outputs and preservation of guest-safe discovery boundaries.

## Validation Participation

Reference:

- `docs/governance/vocabulary-validation-framework.md`

CP5 validation participation includes consumption of composite/hierarchy validation outputs and propagation of validation state references.

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

CP5 may consume:

- composite-room vocabulary anchors
- hierarchy-aware room context
- Asset Intelligence-informed composite-room context
- diagnostics references
- explainability references

CP5 may reference:

- Asset Intelligence-authored outputs

CP5 does not own:

- asset evaluation
- environmental evaluation
- advisory generation
- risk generation
- human_health generation
- significance
- relevance

Coordinator consumes Asset Intelligence-informed composite-room context.

Coordinator does not own Asset Intelligence outputs.

## Nonexistent Output Protection

Current implementation does not expose first-class:

- significance assessments
- relevance assessments
- asset narratives
- room-health narratives
- collection narratives

Composite-room capability consumption must not assume these outputs exist.

## Resolution Failure Model

Composite-room failure categories:

- composite room unavailable
- composite room not eligible
- hierarchy traversal unavailable
- scope expansion unavailable
- unsupported composite-room projection
- invalid composite-room context

This section defines architecture only.

No runtime algorithm is defined.

## Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Composite-Room Truth | governed composite-room definitions and preservation authority | Consumer | PASS |
| Hierarchy Truth | governed hierarchy definitions | Consumer | PASS |
| Scope Truth | governed scope definitions | Consumer | PASS |
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

| Downstream Issue | CP5 Output Dependency |
|---|---|
| #86 | guest-aware filtering constraints for composite/hierarchy capability visibility |
| #87 | composite/hierarchy explainability propagation into capability explainability surfaces |
| #88 | composite/hierarchy discovery participation into capability discovery surfaces |
| #89 | composite/hierarchy diagnostics propagation into capability diagnostics surfaces |
| #90 | readiness validation for composite/hierarchy ownership and household-facing outcome preservation |

## Risks

- hierarchy truth drift
- scope truth drift
- household-facing regression
- ownership drift
- E4/E5 boundary drift
- diagnostics drift
- explainability drift

## Ownership Preservation Review

Result: PASS

Validated:

- hierarchy truth ownership preserved
- scope truth ownership preserved
- room truth ownership preserved
- vocabulary ownership preserved
- capability governance ownership preserved
- Asset Intelligence ownership preserved

No ownership drift introduced in CP5 architecture baseline.

## Readiness Statement

Composite-Room Capability Consumption Architecture is READY.

This document becomes the authoritative composite-room capability consumption baseline for E5.