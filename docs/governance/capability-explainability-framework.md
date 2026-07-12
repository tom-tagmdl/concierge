# Capability Explainability Framework

## Purpose

This document defines the authoritative E5-CP7 capability explainability framework.

This document is architecture and governance only.

This document does not define implementation engines, rendering logic, conversational response generation, LLM prompting, UI behavior, or diagnostics implementation.

## Authority Relationship

Capability Governance Authority remains external through HTBW governance artifacts.

Capability Explainability Authority remains governed by architecture/contract/model boundaries and completed E4 explainability authorities.

Coordinator Explainability Authority:

- explain capability consumption outcomes
- propagate and compose explainability references from governed upstream sources

Coordinator explains consumption.

Coordinator does not define capability meaning.

## CP1-CP6 Dependencies

CP7 consumes:

- `docs/governance/capability-consumption-architecture.md`
- `docs/governance/capability-resolution-pipeline-architecture.md`
- `docs/governance/room-aware-capability-consumption-architecture.md`
- `docs/governance/merged-room-capability-consumption-architecture.md`
- `docs/governance/composite-room-capability-consumption-architecture.md`
- `docs/governance/guest-aware-capability-filtering-architecture.md`

Dependency boundaries:

- CP1 defines capability consumption.
- CP2 defines capability resolution.
- CP3 defines room-aware consumption.
- CP4 defines merged-room consumption.
- CP5 defines composite-room consumption.
- CP6 defines guest-aware filtering.

CP7 consumes all.

CP7 redefines none.

## Completed E4 Explainability Inputs

CP7 consumes:

- resolved vocabulary references
- room-context explanation references
- merged-room explanation references
- composite-room explanation references
- diagnostics-backed explanation references
- RV8a vocabulary explanation boundaries

CP7 consumes these inputs.

CP7 does not redefine them.

## Capability Explainability Model

Capability explainability means deterministic, source-attributed explanation of capability availability, filtering, unavailability, and unsupported outcomes.

Capability lineage means traceable explanation flow from upstream vocabulary and scope resolution through capability outcomes.

Explanation inheritance means downstream capability explanations preserve relevant upstream explanation references.

Explanation composition means multiple explanation sources may be combined under bounded ownership rules for a single capability outcome.

This section defines architecture only.

## Machine-Readable Explainability Model

Machine-readable architecture includes:

- explanation identifiers
- explanation references
- explanation lineage chains
- explanation composition references

Required architecture fields for capability explainability surfaces:

- explanation_id
- capability_reference
- explanation_type
- lineage_references
- composition_references
- ownership_boundary_references
- validation_state
- timestamp_reference

This section defines architecture only.

## Human-Readable Explainability Model

Human-readable architecture includes:

- availability explanations
- filtering explanations
- unavailability explanations
- unsupported-capability explanations

Human-readable capability explanation must remain concise, deterministic, and source-attributed.

This section defines architecture only.

## Capability Lineage Framework

Capability explainability lineage flow:

Vocabulary
  -> Capability Resolution
  -> Room-Aware Consumption
  -> Merged-Room Consumption
  -> Composite-Room Consumption
  -> Guest-Aware Filtering
  -> Capability Outcome

Inheritance rules:

- downstream explanation references inherit applicable upstream references
- inherited references must preserve ownership boundaries
- lineage breaks must be explicit and diagnosable

This section defines architecture only.

## Explanation Composition Framework

Explanation composition allows multiple bounded explanation sources to contribute to one capability outcome explanation.

Composition examples:

- room explanation plus capability explanation
- guest explanation plus capability explanation
- composite-room explanation plus capability explanation

Composition boundaries:

- composition must not transfer ownership
- composition must preserve source attribution
- composition must preserve explainability determinism

This section defines architecture only.

## Availability Explainability

Availability explainability documents why a capability is available under consumed context and governed projection outputs.

Availability explanations must reference lineage and validation state where applicable.

## Filtering Explainability

Filtering explainability documents why a capability was filtered under consumed context, scope, or guest-aware constraints.

Filtering explanations must preserve ownership-boundary references.

## Unavailability Explainability

Unavailability explainability documents why a capability is unavailable under consumed context and governed projection outcomes.

Unavailability explanations must preserve deterministic reasoning references.

## Unsupported Capability Explainability

Unsupported-capability explainability documents why a capability is unsupported for the current context/surface.

Unsupported explanations must not reinterpret unsupported outcomes as owned capability truth.

## Asset Intelligence Boundary

CP7 may explain:

- capability decisions that consumed Asset Intelligence-informed context

CP7 may reference:

- Asset Intelligence-authored outputs as consumed inputs with source attribution

CP7 may not reinterpret:

- advisories
- risk outputs
- human_health outputs
- significance
- relevance

as Coordinator-owned truth.

Coordinator may explain capability decisions that consumed Asset Intelligence-informed context.

Coordinator does not own Asset Intelligence meaning.

Coordinator does not own Asset Intelligence outputs.

## Nonexistent Output Protection

Current implementation does not expose:

- significance assessments
- relevance assessments
- asset narratives
- room-health narratives
- collection narratives
- environmental narratives
- priority-context outputs

CP7 must not assume these outputs exist.

## Explainability Failure Model

Explainability failure categories:

- missing explanation references
- incomplete lineage
- unavailable upstream explanation
- unsupported capability explanation

This section defines architecture only.

## Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Capability Governance | HTBW capability governance | Consumer / Explainer | PASS |
| Capability Explainability | governed capability explainability artifacts | Consumer / Explainer | PASS |
| Vocabulary Explainability | E4 vocabulary explainability authorities | Consumer / Explainer | PASS |
| Room Context Explainability | E4 room-context explainability authorities | Consumer / Explainer | PASS |
| Asset Intelligence Outputs | Asset Intelligence | Consumer / Explainer | PASS |
| Capability Outcomes | governed capability projection outcomes | Consumer / Explainer | PASS |

## Dependency Mapping

| Downstream Issue | CP7 Output Dependency |
|---|---|
| #88 | capability discovery explainability alignment and explanation reference reuse |
| #89 | capability diagnostics explainability-linkage and trace participation |
| #90 | readiness validation for capability explainability ownership and boundary consistency |

## Risks

- explainability drift
- ownership drift
- Asset Intelligence meaning drift
- lineage inconsistency
- cross-scope explanation conflicts

## Ownership Preservation Review

Result: PASS

Validated:

- capability governance ownership preserved
- vocabulary governance ownership preserved
- Asset Intelligence ownership preserved
- room truth ownership preserved
- scope truth ownership preserved
- hierarchy truth ownership preserved

No ownership drift introduced in CP7 architecture baseline.

## Readiness Statement

Capability Explainability Framework is READY.

This document becomes the authoritative capability explainability baseline for E5.