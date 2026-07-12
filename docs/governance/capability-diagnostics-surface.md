# Capability Diagnostics Surface

## Purpose

This document defines the authoritative E5-CP9 capability diagnostics surface.

This document is architecture and governance only.

This document does not define implementation, diagnostics engines, telemetry pipelines, tracing infrastructure, logging frameworks, support tooling, or troubleshooting automation.

## Authority Relationship

Capability Governance Authority remains external through HTBW governance artifacts.

Capability Diagnostics Authority remains governed by architecture/contract/model boundaries and completed E4 diagnostics authorities.

Coordinator Diagnostics Authority:

- expose diagnostics for capability decisions
- expose diagnostics for discovery and inventory behavior

Coordinator diagnoses capability decisions.

Coordinator does not define capability meaning.

## CP4-CP8 Dependencies

CP9 consumes:

- `docs/governance/merged-room-capability-consumption-architecture.md`
- `docs/governance/composite-room-capability-consumption-architecture.md`
- `docs/governance/guest-aware-capability-filtering-architecture.md`
- `docs/governance/capability-explainability-framework.md`
- `docs/governance/capability-discovery-foundation.md` 

Dependency boundaries:

- CP4 defines merged-room capability consumption.
- CP5 defines composite-room capability consumption.
- CP6 defines guest-aware capability filtering.
- CP7 defines capability explainability.
- CP8 defines capability discovery.

CP9 consumes all.

CP9 redefines none.

## Completed E4 Diagnostics Inputs

CP9 consumes:

- vocabulary diagnostics references
- room-context diagnostics references
- merged-room diagnostics references
- composite-room diagnostics references
- validation outputs
- explainability references
- discovery references
- RV8a Asset Intelligence vocabulary diagnostics
- RV8a answer-content handoff diagnostics

CP9 consumes these inputs.

CP9 does not redefine them.

## Capability Diagnostics Model

Capability diagnostics is the architecture for exposing evidence about capability consumption, filtering, eligibility, discovery, and outcome behavior.

Diagnostics lineage means traceable evidence flow from upstream vocabulary, scope, discovery, explainability, and validation sources into capability diagnostics surfaces.

Troubleshooting means a bounded supportability workflow for tracing outcomes back through governed references.

Diagnostic categories mean bounded classes of evidence for capability-related behavior.

This section defines architecture only.

## Capability Trace Model

Capability trace architecture includes:

- capability eligibility trace
- capability availability trace
- capability filtering trace
- capability outcome trace

Capability traces are source-attributed, deterministic, and ownership-preserving.

This section defines architecture only.

## Room Trace Model

Room-aware traces participate by showing room influence on capability consumption and discovery decisions.

Merged-room traces participate by showing merged-room selection, grouping, and scope expansion evidence.

Composite-room traces participate by showing composite selection, hierarchy traversal, and scope expansion evidence.

This section defines architecture only.

## Eligibility Trace Model

Guest eligibility traces participate by showing guest-safe eligibility and visibility participation.

Restriction traces participate by showing restricted capability handling and guest-safe constraints.

This section defines architecture only.

## Discovery Trace Model

Discovery traces participate by showing capability inventory visibility and guest-safe inventory reduction.

Inventory visibility traces participate by showing which capabilities are surfaced, hidden, unavailable, or restricted.

This section defines architecture only.

## Diagnostics Lineage Framework

Diagnostics lineage flow:

Vocabulary Diagnostics
  -> Capability Resolution
  -> Room-Aware Consumption
  -> Merged-Room Consumption
  -> Composite-Room Consumption
  -> Guest-Aware Filtering
  -> Discovery
  -> Capability Outcome

Inheritance expectations:

- diagnostics references inherit applicable upstream references
- lineage breaks must be explicit and diagnosable
- inherited diagnostics must preserve ownership boundaries

This section defines architecture only.

## Troubleshooting Workflow

Supportability workflow:

Capability Outcome
  -> Discovery Trace
  -> Eligibility Trace
  -> Room Trace
  -> Capability Trace
  -> Vocabulary Diagnostics Reference

Troubleshooting supports root-cause identification without redefining governed truth.

This section defines architecture only.

## Explainability Integration

Reference:

- `docs/governance/capability-explainability-framework.md`

CP9 consumes explainability references and aligns diagnostic references to explanation lineage and ownership-boundary explanation.

## Discovery Integration

Reference:

- `docs/governance/capability-discovery-foundation.md`

CP9 consumes discovery references and aligns diagnostic references to discovery lineage and inventory visibility behavior.

## Asset Intelligence Boundary

Capability diagnostics may reference capability decisions that consumed Asset Intelligence-informed context.

Capability diagnostics does not own Asset Intelligence meaning.

Capability diagnostics does not own Asset Intelligence outputs.

Capability diagnostics may not reinterpret:

- descriptions
- advisories
- risk_state
- primary_advisory
- human_health
- significance
- relevance

as diagnostics-owned truth.

## Nonexistent Output Protection

Current implementation does not expose:

- significance assessments
- relevance assessments
- asset narratives
- room-health narratives
- collection narratives
- environmental narratives
- priority-context outputs

CP9 must not assume these outputs exist.

## Diagnostics Failure Model

Diagnostics failure categories:

- missing diagnostic references
- incomplete capability trace
- incomplete room trace
- incomplete eligibility trace
- incomplete discovery trace
- unsupported diagnostics request

This section defines architecture only.

## Ownership Matrix

| Area | Authority | Coordinator Role | Status |
|---|---|---|---|
| Capability Governance | HTBW capability governance | Consumer / Diagnostics Provider | PASS |
| Capability Diagnostics | governed capability diagnostics artifacts | Consumer / Diagnostics Provider | PASS |
| Vocabulary Diagnostics | E4 vocabulary diagnostics authorities | Consumer / Diagnostics Provider | PASS |
| Room Truth | Foundation room truth authority | Consumer / Diagnostics Provider | PASS |
| Asset Intelligence Outputs | Asset Intelligence | Consumer / Diagnostics Provider | PASS |
| Capability Discovery | governed discovery artifacts | Consumer / Diagnostics Provider | PASS |
| Explainability | governed explainability artifacts | Consumer / Diagnostics Provider | PASS |
| Validation | governed validation artifacts | Consumer / Diagnostics Provider | PASS |

## Dependency Mapping

| Downstream Issue | CP9 Output Dependency |
|---|---|
| #90 | readiness validation for diagnostics completeness and boundary preservation |

## Risks

- diagnostics drift
- ownership drift
- Asset Intelligence meaning drift
- troubleshooting ambiguity
- trace lineage inconsistency
- explainability/diagnostics divergence

## Ownership Preservation Review

Result: PASS

Validated:

- capability governance ownership preserved
- vocabulary governance ownership preserved
- Asset Intelligence ownership preserved
- room truth ownership preserved
- scope truth ownership preserved
- hierarchy truth ownership preserved

No ownership drift introduced in CP9 architecture baseline.

## Readiness Statement

Capability Diagnostics Surface is READY.

This document becomes the authoritative capability diagnostics baseline for E5.