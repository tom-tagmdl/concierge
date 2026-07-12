# Capability Discovery Foundation

## Purpose

This document defines the authoritative E5-CP8 capability discovery foundation for the household-facing behavior commonly described as "What Can I Do Here?".

This document is architecture and governance only.

This document does not define implementation, discovery engines, recommendation systems, ranking algorithms, routing logic, or execution planning.

## Authority Relationship

Capability Governance Authority remains external through HTBW capability governance artifacts.

Capability Discovery Authority remains governed by architecture/contract/model boundaries and completed E4 discovery authorities.

Coordinator Discovery Authority:

- expose discoverable capabilities
- present capability inventory behavior as governed output

Coordinator discovers capabilities.

Coordinator does not define capability meaning.

## CP4-CP7 Dependencies

CP8 consumes:

- `docs/governance/merged-room-capability-consumption-architecture.md`
- `docs/governance/composite-room-capability-consumption-architecture.md`
- `docs/governance/guest-aware-capability-filtering-architecture.md`
- `docs/governance/capability-explainability-framework.md`

Dependency boundaries:

- CP4 defines merged-room consumption.
- CP5 defines composite-room consumption.
- CP6 defines guest-aware filtering.
- CP7 defines capability explainability.

CP8 consumes all.

CP8 redefines none.

## Completed E4 Discovery Inputs

CP8 consumes:

- room-aware vocabulary discovery
- guest-safe discovery
- explainability references
- diagnostics references
- RV8a Asset Intelligence-related vocabulary discovery boundaries

CP8 consumes these inputs.

CP8 does not redefine them.

## Capability Discovery Model

Capability discovery is the architecture for exposing what capabilities are available, visible, restricted, or unavailable for a current governed context.

Capability inventory means the governed presentation of discoverable capability sets for a current context.

Room-aware discovery means room context influences what capability inventory is exposed.

Guest-safe discovery means guest restrictions and visibility rules narrow the capability inventory safely.

Vocabulary-linked discovery means vocabulary and scope discovery outputs participate as discoverable language inputs to capability inventory behavior.

This section defines architecture only.

## Capability Inventory Model

Discoverable capability representation includes:

- discoverable capability
- hidden capability
- unavailable capability
- restricted capability

This section defines architecture only.

## Room-Aware Discovery Model

Room-aware discovery participates by using governed room context to narrow the capability inventory surface.

Room context influences:

- which capabilities are shown
- which capabilities are hidden
- which capability labels are surfaced
- which scope-aware phrases are discoverable

This section defines architecture only.

## Merged-Room Discovery Model

Merged-room discovery participates by exposing discoverable capability language for merged-room contexts while preserving merged-room scope boundaries.

Merged-room discovery does not redefine merged-room truth.

This section defines architecture only.

## Composite-Room Discovery Model

Composite-room discovery participates by exposing discoverable capability language for composite, floor, and hierarchy-aware contexts.

Scope inheritance participates by allowing governed broader-scope discovery when supported.

Hierarchy participation influences discovery by narrowing or expanding visible capability inventory under governed scope relationships.

This section defines architecture only.

## Guest-Aware Discovery Model

Guest-safe discovery participates by reducing capability inventory to guest-safe visible surfaces and by preserving restriction boundaries.

Guest restrictions participate by hiding or constraining capabilities that are not guest-safe for the current context.

This section defines architecture only.

## Vocabulary-Linked Discovery Model

Vocabulary discovery from E4 participates in capability discovery as upstream discoverable language and scope context.

Vocabulary
  -> Capability Discovery
  -> Capability Inventory

This section defines architecture only.

## Discovery Explainability Participation

Reference:

- `docs/governance/capability-explainability-framework.md`

CP8 consumes explainability references and exposes discoverability reasons through bounded explanation references.

Discovery explainability must show why capabilities are shown or hidden without generating arbitrary response content.

## Discovery Diagnostics Participation

Reference:

- `docs/governance/vocabulary-diagnostics-framework.md`

CP8 consumes diagnostics references.

This section defines architecture only.

## Asset Intelligence Boundary

What discovery may expose:

- discoverable capability language
- safe capability labels
- room- and scope-aware capability inventory

What discovery may reference:

- Asset Intelligence-informed context when explicitly authorized by completed E4 artifacts

What discovery may not reinterpret:

- Asset Intelligence-authored content as capabilities

Capability discovery must not treat Asset Intelligence-authored content as capabilities.

Capability discovery must not treat:

- descriptions
- advisories
- risk_state
- primary_advisory
- human_health
- room environment projections

as capabilities.

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

CP8 must not assume these outputs exist.

## Discovery Failure Model

Discovery failure categories:

- no discoverable capabilities
- unavailable capability inventory
- room discovery unavailable
- guest discovery unavailable
- unsupported discovery context

This section defines architecture only.

## Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Capability Governance | HTBW capability governance | Consumer / Discovery Provider | PASS |
| Capability Discovery | governed capability discovery artifacts | Consumer / Discovery Provider | PASS |
| Vocabulary Discovery | E4 vocabulary discovery authorities | Consumer / Discovery Provider | PASS |
| Room Truth | Foundation room truth authority | Consumer / Discovery Provider | PASS |
| Asset Intelligence Outputs | Asset Intelligence | Consumer / Discovery Provider | PASS |
| Capability Inventory | governed discoverable capability surfaces | Consumer / Discovery Provider | PASS |
| Explainability | governed explainability artifacts | Consumer / Discovery Provider | PASS |
| Diagnostics | governed diagnostics artifacts | Consumer / Discovery Provider | PASS |

## Dependency Mapping

| Downstream Issue | CP8 Output Dependency |
|---|---|
| #89 | capability discovery diagnostics/explainability surface consistency |
| #90 | readiness validation for capability discovery ownership and inventory safety |

## Risks

- discovery drift
- ownership drift
- Asset Intelligence meaning drift
- guest-safe exposure drift
- vocabulary-discovery drift
- explainability inconsistency

## Ownership Preservation Review

Result: PASS

Validated:

- capability governance ownership preserved
- vocabulary governance ownership preserved
- Asset Intelligence ownership preserved
- room truth ownership preserved
- scope truth ownership preserved
- hierarchy truth ownership preserved

No ownership drift introduced in CP8 architecture baseline.

## Readiness Statement

What Can I Do Here? Capability Foundation is READY.

This document becomes the authoritative capability discovery baseline for E5.