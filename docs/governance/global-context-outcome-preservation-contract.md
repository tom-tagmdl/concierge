# Global Context Outcome Preservation Contract

## Purpose
This document is the implementation-time preservation contract for Concierge V1 global context provider household-facing outcomes.

This contract is consumed by E3a and later Coordinator V2 implementation work.

## Authority Relationship
- ADR-013 governs preservation philosophy.
- Issue #63 defines the broader V1 preservation inventory.
- Issue #67 defines global context preservation expectations.
- This document is the implementation contract for global context outcome preservation.
- This document does not replace HTBW ADRs, contracts, or models.

Authority chain:

ADRs
  -> Contracts
  -> Models
  -> Issue #63 V1 preservation baseline
  -> Issue #67 global context review
  -> This preservation contract
  -> Implementation issues

## Governing Principle
Preserve global context household-facing outcomes.

Do not preserve global context implementation details.

The correct preservation question is:

Can the household still achieve the same global context outcome?

The incorrect preservation question is:

Does the global context implementation work the same way internally?

## Global Context Definition
Global context is the household-facing set of shared home, occupancy, environmental, platform, and status information that Concierge V1 exposes or consumes to support summaries, awareness, routing, diagnostics, and coordination.

Global context is not defined by current provider internals, helper methods, entity shape, panel implementation, service implementation, or storage format.

## Context Areas Covered
- home status
  - household-facing meaning: home-wide status signals and state awareness available to the household
  - authority boundary: Foundation and source systems remain external
  - implementation-preservation requirement: NO
- occupancy references
  - household-facing meaning: occupancy contributes to household-facing awareness and policy outcomes
  - authority boundary: occupancy truth remains external
  - implementation-preservation requirement: NO
- presence references
  - household-facing meaning: person presence context can influence awareness and eligibility outcomes
  - authority boundary: presence truth remains external
  - implementation-preservation requirement: NO
- shared household context
  - household-facing meaning: shared context can be read and summarized for the household
  - authority boundary: source domain authority remains external
  - implementation-preservation requirement: NO
- environmental context
  - household-facing meaning: environmental context contributes to awareness outputs where currently observable
  - authority boundary: environment/home-state truth remains external
  - implementation-preservation requirement: NO
- platform state
  - household-facing meaning: platform availability/status can influence household-facing readiness and context surfaces where observable
  - authority boundary: platform/provider authority remains external
  - implementation-preservation requirement: NO
- signal context
  - household-facing meaning: signal readouts remain visible and meaningful
  - authority boundary: signal source truth remains external
  - implementation-preservation requirement: NO
- summary context
  - household-facing meaning: multiple context and signal inputs can be aggregated into a household summary
  - authority boundary: summary inputs remain externally authoritative
  - implementation-preservation requirement: NO
- diagnostics / timeline context
  - household-facing meaning: context-related outcomes remain visible for operators/support review where currently observable
  - authority boundary: diagnostics is evidence surface, not source truth
  - implementation-preservation requirement: NO
- household coordination context
  - household-facing meaning: context remains consumable by future coordination-oriented household features
  - authority boundary: coordination authority remains governed externally
  - implementation-preservation requirement: NO

## Required Preserved Outcomes

### Household-wide context readout
- household-facing behavior: household can retrieve a global context payload by type
- current evidence source: `get_context` service
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Context-informed household summary
- household-facing behavior: household can receive a deterministic summary assembled from available context and signals
- current evidence source: `get_summary` service and README examples
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Signal readout
- household-facing behavior: active signal states and summaries remain visible
- current evidence source: `get_signal`, `get_signals`, README signal examples
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Home status awareness
- household-facing behavior: household can receive home-wide awareness outcomes through context and summary surfaces
- current evidence source: README whole-home awareness, context/signal readout services
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Occupancy / presence reference consumption
- household-facing behavior: occupancy/presence references remain consumable in policy and awareness pathways where currently observable
- current evidence source: person/room context flows, policy rules, foundation baselines
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Environmental context consumption
- household-facing behavior: environmental context remains available for household awareness where currently observable
- current evidence source: README weather/news/global context model, room/global context configuration
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Platform-state awareness
- household-facing behavior: platform readiness/state remains visible where currently observable
- current evidence source: runtime capability/status summary and configuration-facing context outputs
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Shared context availability
- household-facing behavior: shared context remains accessible to household-facing surfaces and coordinator consumption
- current evidence source: global context update and read services
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Context visibility in diagnostics or timeline where currently observable
- household-facing behavior: context-related changes remain visible in operational evidence surfaces where currently observable
- current evidence source: activity timeline for global context updates
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Context participation in planning / routing where currently observable
- household-facing behavior: context remains a valid governed input to downstream decision-making
- current evidence source: Coordinator foundation summary and runtime architecture
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Context participation in briefing, productivity, or household status work where currently observable
- household-facing behavior: context remains consumable by future awareness and productivity surfaces
- current evidence source: README global context and summary behavior; HTBW productivity governance
- preservation requirement: preserve outcome
- implementation preservation required: NO

## Home Status Outcome Preservation
Home status must remain exposed or consumable as a household-facing outcome through context and summary surfaces.

What must remain observable:
- household can retrieve home-wide awareness context where currently supported
- home-wide summary can reflect available home/signal/context state

What may change internally:
- provider wiring
- storage layout
- update flows
- summary assembly internals

Foundation and home-state truth remain external.

## Occupancy and Presence Reference Preservation
Occupancy/presence references must remain consumable in household-facing behavior where currently observable.

This includes use in:
- awareness surfaces
- summary behavior
- routing or eligibility influence where currently observable

Occupancy and Presence authority remains external.

Coordinator V2 consumes occupancy context without determining occupancy truth.

## Shared Context Preservation
Shared household context surfaces must remain available.

Shared context must remain consumable by:
- summary
- diagnostics
- routing where relevant
- planning where relevant

Implementation may change.

Household-facing shared context outcomes must remain.

## Environmental Context Preservation
Environmental or home-state signals currently exposed or consumed must remain available as household-facing awareness outcomes where currently observable.

If explicit environmental behavior is not fully evidenced, treat it as follow-up validation rather than blocker.

## Signal Context Preservation
Preserve:
- active signals or household signal streams currently exposed
- signal readout and visibility outcomes
- signal participation in summary or context surfaces
- signal authority boundaries remaining external

## Summary Context Preservation
Preserve:
- household summary aggregation outcomes
- context-informed summary behavior
- summary inputs where currently observable
- relationship to future briefing and household status synthesis

Coordinator may change summary assembly internals.

Household-facing summary outcome must remain.

## Diagnostics and Timeline Context Preservation
Preserve:
- context visibility in diagnostics
- activity timeline visibility for context mutations where currently observable
- operator-visible outcome history
- context traceability expectations

Diagnostics may change internally.

Traceable context visibility must remain where currently observable.

## Briefing / Productivity / Household Status Relationship
Global context remains a downstream input for:
- briefing
- productivity experiences
- household status synthesis
- household coordination

Global context should remain consumable as an input.

Coordinator V2 must not redefine provider or context authority.

## Coordinator V2 Interaction
Coordinator V2 must consume global context through:
- context assembly
- capability resolution where relevant
- experience resolution where relevant
- planning
- routing
- explainability
- diagnostics
- execution envelope

Coordinator may consume global context.

Coordinator may not redefine context authority, occupancy truth, home-state truth, provider ownership, or provenance semantics.

## Contract / Model Mapping
| Context Area | Governing Contract | Governing Model | Concierge Role |
|---|---|---|---|
| Home Status | knowledge-briefing-status-synthesis-contract.md | briefing-composition-model.md | consume home/status context for awareness outputs |
| Occupancy / Presence | occupancy-and-presence-contract.md | occupancy-presence-model.md | consume occupancy/presence references |
| Household Memory | household-memory-contract.md | household-memory-model.md | consume memory-informed context where relevant |
| Provenance | provenance-contract.md | provenance-model.md | attach/consume lineage references |
| Knowledge / Briefing / Status Synthesis | knowledge-briefing-status-synthesis-contract.md | knowledge-query-experience-model.md / briefing-composition-model.md | consume context for awareness outputs |
| Household Coordination | household-coordination-contract.md | household-coordination-snapshot-model.md | preserve context consumability for coordination |
| Capability Projection | capability-projection-contract.md | capability-projection-model.md | consume capability context where relevant |
| Experience Projection | experience-projection-contract.md | experience-model.md | consume experience context where relevant |

If an area lacks a perfectly direct model boundary, the nearest HTBW governance authority is used and follow-up model clarification remains non-blocking unless later evidence proves otherwise.

## Ownership Matrix
| Context Family | Authority | Concierge Role | Boundary |
|---|---|---|---|
| Foundation / Home Truth | Foundation and source systems | consume home truth/context | no home-state ownership |
| Occupancy / Presence | HTBW occupancy governance | consume occupancy references | no occupancy truth ownership |
| Household Memory | HTBW memory governance | consume memory context | no memory authority ownership |
| Provenance | HTBW provenance governance | consume lineage references | no provenance authority ownership |
| Asset Intelligence | Asset Intelligence authority | consume significance or context where enabled | no asset reasoning ownership |
| Voice Identity | Voice Identity authority | consume person/identity context where relevant | no identity authority ownership |
| Capability Projection | HTBW capability governance | consume capability context | no capability ownership |
| Experience Projection | HTBW experience governance | consume experience context | no experience ownership |
| External Providers | provider/source systems | provide upstream context truth | ownership remains external |
| Coordinator V2 | Concierge orchestration runtime | consume and assemble global context usage | bounded orchestration only |

## Global Context Capability Matrix
| Capability | Household-Facing Outcome | Current Evidence | Must Preserve | Implementation Preservation Required |
|---|---|---|---|---|
| Global context readout | Context payload can be retrieved by type | `get_context` | YES | NO |
| Context-informed summary | Summary aggregates context and signals | `get_summary`, README | YES | NO |
| Signal readout | Signals remain visible and summarized | `get_signal`, `get_signals`, README | YES | NO |
| Home status awareness | Household-wide awareness remains visible | README, context/signal surfaces | YES | NO |
| Occupancy/presence reference use | Occupancy context remains consumable where observable | policy/context flows | YES | NO |
| Environmental context use | Weather/news/environment context remains available where observable | README, global context updates | YES | NO |
| Platform-state awareness | Platform state remains visible where observable | capability/status summaries | YES | NO |
| Shared context availability | Shared context remains accessible | global context services | YES | NO |
| Diagnostics/timeline context visibility | Context changes remain visible diagnostically | activity timeline | YES | NO |
| Downstream context consumability | Future briefing/productivity/coordination can consume context | foundation baselines + HTBW governance | YES | NO |

## Global Context Parity Matrix
| Context Type | Expected Household Outcome | Parity Required | Notes |
|---|---|---|---|
| home status | home-wide awareness remains available | YES | source truth remains external |
| occupancy | occupancy references remain consumable | YES | no occupancy truth ownership |
| presence | presence references remain consumable where observable | YES | person authority external |
| environmental state | weather/news/environment context remains available where observable | YES | follow-up if provider boundary unclear |
| platform state | platform readiness/state remains visible where observable | YES | provider/platform authority external |
| signals | signal visibility and summaries remain available | YES | source signals external |
| shared context | shared global context remains accessible | YES | no provider ownership transfer |
| summary context | summary remains context-informed | YES | internals may change |
| diagnostics context | context remains traceable in diagnostics | YES | evidence surface only |

## Downstream Parity Expectations
Future implementation must verify:
- household can still retrieve shared/global context where currently supported
- household can still receive context-informed summaries
- occupancy/presence references remain consumable where currently supported
- home/environment/platform state remains visible where currently evidenced
- signal context remains available where currently evidenced
- diagnostics can explain context participation
- future briefing/productivity/household status work can consume context without redefining authority

## Diagnostics and Explainability Expectations
Future implementation must be able to explain:
- why a context item was included
- why a context item was excluded
- why occupancy influenced behavior
- why home status influenced behavior
- why environmental context influenced behavior
- why a summary included a specific context source
- why context was unavailable
- why provider authority remained external

## Non-Rights
Global context preservation does NOT require preserving:
- current provider implementation
- current helper methods
- current service internals
- current storage format
- current API shape
- current entity implementation
- current panel implementation
- current context provider wiring

Global context preservation DOES require preserving observable household outcomes.

## Follow-Up Validation Items
Non-blocking follow-up observations:
- explicit home-status provider boundary
- explicit environmental context provider boundary
- platform-state visibility scope
- whole-house summary context inputs
- occupancy reference source mapping
- signal/context terminology consistency
- future household status synthesis model mapping

These are non-blocking unless later evidence proves otherwise.

## Downstream Use
This document must be consumed by:
- E3a routing reviews
- E3a restoration reviews
- E3a execution reviews
- E3a room targeting reviews
- E4 Room Vocabulary Consumption
- E5 Capability Projection Consumption
- E6 Experience Consumption
- E9 Messaging and Notification Discipline
- E10 Household Memory and Explainability
- E13 Productivity Experiences
- E14 Household Coordination
- later Coordinator V2 implementation work touching global context, shared context, home status, occupancy references, environmental context, briefing, productivity, or household status behavior

## Required Future GitHub Copilot Usage
Before implementation work that may affect global context household-facing outcomes, GitHub Copilot must read:
- `docs/governance/coordinator-v2-foundation-summary.md`
- `docs/governance/concierge-v1-outcome-preservation-baseline.md`
- `docs/governance/global-context-outcome-preservation-contract.md`
- the relevant CF or E3a issue baseline
- relevant HTBW contracts and models
- the target issue last

GitHub Copilot must ask:

Can the household still achieve the same global context outcome?

GitHub Copilot must not ask:

Does the global context implementation work the same way internally?

## Readiness Statement
Global context outcome preservation contract is READY for downstream E3a and Coordinator V2 implementation consumption.