# Capability Consumption Architecture

## Purpose

This document defines the authoritative E5-CP1 architecture baseline for how Coordinator consumes capability projections.

This document is architecture and governance only.

This document does not define implementation.

This document does not define capability selection algorithms, capability ranking algorithms, execution behavior, routing behavior, or planning behavior.

## Authority Relationship

Capability Governance Authority remains external through:

- ADR capability-projection governance
- `homes_that_behave_well/docs/contracts/capability-projection-contract.md`
- `homes_that_behave_well/docs/models/capability-projection-model.md`

Coordinator Authority is:

- Consumer

Coordinator consumes capability projections.

Coordinator does not own capability governance.

## Completed E4 Inputs

E5-CP1 consumes completed E4 outputs as inputs:

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
- room-context resolution outputs

These inputs are consumed under completed E4 governance artifacts:

- `docs/governance/asset-intelligence-vocabulary-consumption-architecture.md`
- `docs/governance/vocabulary-diagnostics-framework.md`
- `docs/governance/e4-vocabulary-consumption-readiness-review.md`

## Capability Projection Ownership Model

| Authority Domain | Authority | Consumer Rights | Non-Rights |
|---|---|---|---|
| HTBW | architecture, ADRs, contracts, models, canonical governance | define and update platform governance | does not become runtime orchestration |
| Capability Governance | capability-projection contract and model under HTBW governance | provide deterministic capability projection outputs for runtime consumption | does not transfer capability ownership into Coordinator |
| Coordinator | runtime orchestration and projection consumption | consume projections, reference explainability/diagnostics/discovery/validation outputs, orchestrate downstream flows | does not own capability governance, capability definitions, projection truth, or source-of-record authority |
| Foundation | room truth, scope truth, hierarchy truth, occupancy truth | provide governed truth inputs consumed by E4 and E5 | does not transfer truth ownership to Coordinator |
| Asset Intelligence | asset evaluation, environmental evaluation, advisory/status output, risk/advisory output, human_health output, asset descriptions, environmental interpretation | provide externally owned outputs that may be referenced after E4 resolution | does not transfer Asset Intelligence output ownership into Coordinator |

## Capability Consumption Lifecycle

Capability Availability
  -> Capability Projection Creation
  -> Capability Projection Consumption
  -> Capability Explainability
  -> Capability Diagnostics
  -> Downstream Planning and Routing

This lifecycle is consumption only.

This lifecycle does not define execution.

## Coordinator Capability Consumption Model

Coordinator consumes:

- projected capability sets
- available capability sets
- filtered capability sets
- unsupported capability sets
- explainability references
- diagnostics references
- discovery-context references
- validation outcomes relevant to capability consumption

Coordinator stores or carries forward references and bounded runtime state needed for deterministic orchestration and explainability.

Coordinator does not own:

- capability definitions
- capability governance
- projection truth
- capability source-of-record authority

## Capability Projection Access Pattern

Capability projections are accessed through governed projection surfaces and consumed as deterministic outputs.

Access pattern architecture:

- read projection output
- associate projection output with resolved room/scope context
- reference explainability, diagnostics, discovery, and validation artifacts
- apply policy-bounded consumption behavior in Coordinator orchestration

Capability availability is evaluated as consumption of governed projection outputs.

No selection algorithm, ranking algorithm, or execution algorithm is defined in this architecture artifact.

## E4 -> E5 Handoff Boundary

E4 provides:

- vocabulary
- room context
- discovery
- explainability references
- diagnostics references
- validation outcomes

E5 consumes those outputs.

E5 does not redefine those outputs.

E5 capability consumption remains downstream of E4 resolution and boundary governance.

## Asset Intelligence Boundary

Grounded in:

- #190
- #79
- #80
- #187

E5 consumes:

- E4-resolved Asset Intelligence vocabulary anchors

E5 may reference:

- Asset Intelligence-authored output

E5 does not own:

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

Capability consumption architecture must not assume those outputs exist.

If future authority artifacts and implementation explicitly introduce those outputs, downstream issues may consume them then.

## Capability Explainability Participation

Coordinator consumes explainability references produced by completed E4 and capability projection artifacts.

Reference:

- `docs/governance/vocabulary-explainability-framework.md`

Participation boundaries:

- explain projection consumption outcomes
- preserve ownership-boundary explanation
- do not redefine upstream explainability governance

## Capability Diagnostics Participation

Coordinator consumes diagnostics references produced by completed E4 and capability projection artifacts.

Reference:

- `docs/governance/vocabulary-diagnostics-framework.md`

Participation boundaries:

- surface capability-consumption diagnostics with source attribution
- preserve separation between vocabulary diagnostics and capability diagnostics
- do not redefine diagnostics governance authority

## Capability Discovery Participation

Coordinator consumes discovery outputs from completed E4 as contextual inputs into capability projection consumption.

Reference:

- `docs/governance/vocabulary-discovery-framework.md`

Participation boundaries:

- consume room-aware and guest-safe discovery outputs
- preserve future/non-E4 exclusion boundaries
- do not transfer discovery governance ownership into Coordinator

## Validation Participation

Coordinator consumes validation outputs from completed E4 as bounded readiness and runtime safeguards for capability projection consumption.

Reference:

- `docs/governance/vocabulary-validation-framework.md`

Participation boundaries:

- consume PASS/WARNING/ERROR/BLOCKED outcomes where applicable
- preserve external validation authority
- do not redefine validation policy

## Ownership Preservation Review

Result: PASS

Validated:

- capability governance preserved
- vocabulary governance preserved
- room truth preserved
- Asset Intelligence preserved

No ownership drift introduced in this CP1 architecture baseline.

## Risks

- ownership drift
- capability-governance drift
- Asset Intelligence ownership drift
- E4/E5 boundary drift
- explainability drift
- diagnostics drift
- discovery drift

## Future Dependency Mapping

| Issue | CP1 Dependency |
|---|---|
| #82 | consumes CP1 capability consumption baseline and projection access boundary |
| #83 | consumes CP1 room-aware capability-consumption baseline |
| #84 | consumes CP1 merged-room capability-consumption baseline |
| #85 | consumes CP1 composite-room capability-consumption baseline |
| #86 | consumes CP1 guest-aware filtering ownership and boundary rules |
| #87 | consumes CP1 explainability participation boundary |
| #88 | consumes CP1 discovery participation boundary |
| #89 | consumes CP1 diagnostics participation boundary |
| #90 | consumes CP1 readiness baseline and ownership-preservation expectations |

## Readiness Statement

Capability Consumption Architecture is READY.

This document becomes the authoritative capability-consumption baseline for E5.