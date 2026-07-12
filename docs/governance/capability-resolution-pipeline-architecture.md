# Capability Resolution Pipeline Architecture

## Purpose

This document defines the authoritative E5-CP2 architecture baseline for deterministic capability projection resolution.

This document is architecture and governance only.

This document does not define implementation, selection algorithms, ranking algorithms, execution behavior, routing behavior, or planning algorithms.

## Authority Relationship

Capability Governance Authority remains external through:

- ADR capability-projection governance
- `homes_that_behave_well/docs/contracts/capability-projection-contract.md`
- `homes_that_behave_well/docs/models/capability-projection-model.md`

Coordinator Resolution Authority:

- Coordinator consumes projections and resolves projection-consumption state transitions.

Coordinator consumes projections.

Coordinator does not own projection governance.

## CP1 Dependency

CP2 consumes:

- `docs/governance/capability-consumption-architecture.md`

CP1 defines capability consumption.

CP2 defines capability resolution.

CP2 does not redefine CP1.

## Completed E4 Inputs

CP2 consumes completed E4 outputs:

- resolved vocabulary
- room-aware vocabulary
- merged-room vocabulary
- composite-room vocabulary
- explainability references
- diagnostics references
- discovery outputs
- validation outputs

RV8a inputs consumed through E4:

- asset labels
- asset type/category
- asset identity/name metadata
- Concierge `asset_groups`
- room-context results

CP2 consumes these inputs.

CP2 does not redefine these inputs.

## Capability State Model

Capability state architecture:

- projected: capability appears in projection output candidate set
- available: projected capability is currently consumable under governed context
- unavailable: projected capability exists but is not currently consumable under context or policy
- unsupported: capability is out-of-scope or not supported for the current context/surface

This is state architecture only.

No implementation or algorithm is defined here.

## Capability Resolution Pipeline

Inputs
  -> Capability Candidates
  -> Projection Evaluation
  -> Availability Resolution
  -> Support Validation
  -> Capability Resolution
  -> Explainability References
  -> Diagnostics References

Pipeline notes:

- deterministic stage boundaries
- explicit stage inputs and outputs
- no hidden projection mutation
- no execution behavior in CP2

## Resolution Ordering

Resolution ordering principles:

- deterministic for identical governed inputs
- explicit precedence between projected, available, unavailable, and unsupported states
- explicit conflict-handling visibility
- explainable and diagnosable outcomes

Conflict handling architecture:

- preserve governed precedence from upstream artifacts
- surface conflict condition through explainability and diagnostics references
- do not use hidden fallback inference

No ordering algorithm is defined in this architecture artifact.

## Projected Capability Consumption

Projected capabilities are consumed as upstream candidate outputs from governed projection sources.

Coordinator may:

- reference projected capability identifiers
- bind projected candidates to resolved E4 context
- propagate explainability and diagnostics references

Coordinator may not:

- redefine projected capability governance
- redefine projected capability truth

## Available Capability Consumption

Available capabilities are consumed as context-valid capability outputs.

Coordinator may:

- consume available-state outputs for downstream orchestration stages
- propagate explainability and diagnostics references for availability

Coordinator may not:

- redefine availability governance
- reinterpret availability as ownership transfer

## Unavailable Capability Consumption

Unavailable capabilities are consumed as explicit non-availability outcomes.

Coordinator may:

- preserve unavailable-state visibility for explainability, diagnostics, and downstream behavior boundaries

Coordinator may not:

- hide unavailable outcomes through ungoverned inference
- redefine unavailable-state governance

## Unsupported Capability Consumption

Unsupported capabilities are consumed as explicit unsupported-state outcomes.

Coordinator may:

- preserve unsupported-state references for explainability and diagnostics

Coordinator may not:

- reinterpret unsupported-state as executable capability truth
- redefine unsupported-state governance

## Explainability Participation

CP2 consumes and propagates explainability references.

Reference:

- `docs/governance/vocabulary-explainability-framework.md`

Propagation boundaries:

- attach explainability references to resolution outcomes
- preserve ownership-boundary rationale
- do not redefine explainability governance

## Diagnostics Participation

CP2 consumes and propagates diagnostics references.

Reference:

- `docs/governance/vocabulary-diagnostics-framework.md`

Propagation boundaries:

- attach diagnostics references to resolution-stage outcomes
- preserve trace visibility across state transitions
- do not redefine diagnostics governance

## Discovery Participation

CP2 consumes discovery outputs as contextual inputs into capability resolution.

Reference:

- `docs/governance/vocabulary-discovery-framework.md`

Participation boundaries:

- consume discovery outputs and guest-safe visibility constraints
- preserve future/non-E4 exclusions
- do not redefine discovery governance

## Validation Participation

CP2 consumes validation outcomes as bounded inputs into resolution behavior.

Reference:

- `docs/governance/vocabulary-validation-framework.md`

Participation boundaries:

- consume PASS/WARNING/ERROR/BLOCKED as upstream outcomes
- preserve external validation authority
- do not redefine validation governance

## Asset Intelligence Boundary

Grounded in:

- #190
- #79
- #80
- #187
- `docs/governance/capability-consumption-architecture.md`

Capability resolution may consume:

- E4-resolved vocabulary anchors
- room context
- explainability references
- diagnostics references
- discovery outputs
- validation outputs

Capability resolution may reference:

- Asset Intelligence-authored outputs

Capability resolution does not own:

- asset evaluation
- environmental evaluation
- advisory generation
- risk generation
- human_health generation
- significance
- relevance

Coordinator consumes Asset Intelligence-informed context.

Coordinator does not own Asset Intelligence outputs.

## Nonexistent Output Protection

Current implementation does not expose first-class:

- significance assessments
- relevance assessments
- asset narratives
- room-health narratives
- collection narratives
- environmental narratives
- priority-context outputs

Capability resolution architecture must not assume those outputs exist.

## Resolution Failure Model

Architecture-level failure categories:

- unavailable capability
- unsupported capability
- validation failure
- discovery limitation
- vocabulary ambiguity inputs

Failure handling requirements:

- deterministic outcome class
- explainability reference propagation
- diagnostics reference propagation
- no hidden ownership transfer

This is failure architecture only.

No runtime algorithm is defined.

## Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Capability Governance | HTBW capability governance | Consumer / Resolver | PASS |
| Capability Projection | capability-projection contract and model under HTBW governance | Consumer / Resolver | PASS |
| Vocabulary Governance | HTBW room vocabulary governance | Consumer / Resolver | PASS |
| Room Truth | Foundation | Consumer / Resolver | PASS |
| Asset Labels | Asset Intelligence exposed metadata | Consumer / Resolver | PASS |
| Asset Type / Category | Asset Intelligence exposed metadata | Consumer / Resolver | PASS |
| Asset Identity Metadata | Asset Intelligence exposed metadata | Consumer / Resolver | PASS |
| Asset Intelligence Outputs | Asset Intelligence | Consumer / Resolver | PASS |
| Explainability | governed explainability artifacts | Consumer / Resolver | PASS |
| Diagnostics | governed diagnostics artifacts | Consumer / Resolver | PASS |

## Dependency Mapping

| Downstream Issue | CP2 Output Dependency |
|---|---|
| #83 | room-aware capability resolution foundation |
| #84 | merged-room capability resolution foundation |
| #85 | composite-room capability resolution foundation |
| #86 | guest-aware resolution-state boundary inputs |
| #87 | explainability propagation from capability resolution stages |
| #88 | discovery-influenced resolution outputs |
| #89 | diagnostics propagation from resolution stages |
| #90 | readiness validation against deterministic resolution baseline |

## Risks

- ownership drift
- projection drift
- E4/E5 boundary drift
- explainability drift
- diagnostics drift
- discovery drift

## Ownership Preservation Review

Result: PASS

Reviewed:

- capability governance
- vocabulary governance
- room truth
- Asset Intelligence ownership

No ownership drift introduced in CP2 architecture baseline.

## Readiness Statement

Capability Resolution Pipeline Architecture is READY.

This document becomes the authoritative capability-resolution baseline for E5.