# V1-to-V2 Capability Parity Matrix

## Purpose
This document is the authoritative V1-to-V2 parity matrix for Concierge V1 household-facing outcomes.

This document is consumed by E3a and all later Coordinator V2 implementation work.

## Authority Relationship
- ADR-013 governs preservation philosophy.
- Issue #63 defines the broad V1 outcome inventory.
- Issues #64 through #67 define domain-specific preservation contracts.
- Issue #68 defines the full V1-to-V2 parity mapping.
- This document is the implementation contract for capability parity mapping.
- This document does not replace HTBW ADRs, contracts, or models.

Authority chain:

ADRs
  -> Contracts
  -> Models
  -> E3 Coordinator Foundation
  -> E3a Preservation Contracts
  -> Issue #68 mapping review
  -> This parity matrix
  -> Implementation issues

## Governing Principle
Preserve household-facing outcomes.

Do not preserve implementation details.

The correct preservation question is:

Can the household still achieve the same V1 outcome in the V2 architecture?

The incorrect preservation question is:

Does the V1 implementation work the same way internally?

## Mapping Method
Each V1 outcome is mapped to:
- contract authority
- model authority
- Coordinator Foundation area
- future epic / consumer
- parity expectation
- gap / follow-up status

No V1 household-facing outcome may remain unmapped.

No orphan outcomes are allowed.

## Capability Source Inventory
Source preservation artifacts used:
- `docs/governance/concierge-v1-outcome-preservation-baseline.md`
- `docs/governance/merged-room-outcome-preservation-contract.md`
- `docs/governance/composite-room-scope-outcome-preservation-contract.md`
- `docs/governance/execution-hierarchy-outcome-preservation-contract.md`
- `docs/governance/global-context-outcome-preservation-contract.md`

## Coordinator Foundation Mapping Key
- CF1 Runtime Boundary
- CF2 Context Assembly
- CF3 Capability Resolution
- CF4 Experience Resolution
- CF5 Planning
- CF6 Explainability
- CF7 Diagnostics
- CF8 Routing
- CF9 Execution Envelope
- CF10 Readiness Review

## Future Epic Mapping Key
- E4 Room Vocabulary Consumption
- E5 Capability Projection Consumption
- E6 Experience Consumption
- E7 Continuity and Affinity
- E8 Experience Restoration
- E8a Occupancy and Presence
- E9 Messaging and Notification Discipline
- E10 Household Memory and Explainability
- E13 Productivity Experiences
- E14 Household Coordination

## Full V1-to-V2 Parity Matrix
| V1 Capability | Preserved Household Outcome | Governing Contract | Governing Model | Coordinator Foundation Area | Future Epic / Consumer | Parity Status | Gap / Follow-Up |
|---|---|---|---|---|---|---|---|
| Room-scoped execute | Room-targeted execution remains available | capability-projection-contract.md | capability-projection-model.md | CF5 Planning | E5, E6 | MAPPED | None |
| Direct entity execute | Explicit entity/service execution remains available | capability-projection-contract.md | capability-projection-model.md | CF5 Planning | E5, E6 | MAPPED | None |
| Deterministic execute hierarchy | Predictable precedence/fallback remains | capability-projection-contract.md | capability-projection-model.md | CF5 Planning | E5, E6, E9 | MAPPED | None |
| Minor policy gating | Policy-denied requests are blocked before actuation | occupancy-and-presence-contract.md | occupancy-presence-model.md | CF5 Planning | E8a, E9 | MAPPED | None |
| Explicit room targeting | Explicit room targeting remains | room-vocabulary-registry-contract.md | room-vocabulary-registry-model.md | CF2 Context Assembly | E4, E9 | MAPPED | None |
| Alias-based target resolution | Configured aliases resolve predictably | room-vocabulary-registry-contract.md | room-vocabulary-registry-model.md | CF2 Context Assembly | E4 | MAPPED | None |
| Person-linked room resolution | Person-linked contextual room resolution remains | occupancy-and-presence-contract.md | occupancy-presence-model.md | CF2 Context Assembly | E7, E8a | MAPPED | None |
| Merged-room creation | Household can create merged scope | room-vocabulary-registry-contract.md | room-vocabulary-registry-model.md | CF5 Planning | E4, E9 | MAPPED | None |
| Merged-room rename / membership edit | Household can edit merged scope | room-vocabulary-registry-contract.md | room-vocabulary-registry-model.md | CF5 Planning | E4 | MAPPED | None |
| Merged-room dismantle | Household can remove merged scope | room-vocabulary-registry-contract.md | room-vocabulary-registry-model.md | CF5 Planning | E4 | MAPPED | None |
| Same-floor merged-room enforcement | Cross-floor merged scope is rejected | occupancy-and-presence-contract.md | occupancy-presence-model.md | CF5 Planning | E8a | MAPPED | None |
| Merged-room target resolution | Merged scope remains targetable | room-vocabulary-registry-contract.md | room-vocabulary-registry-model.md | CF8 Routing | E4, E9 | MAPPED | None |
| Merged-room routing scope | Merged scope remains meaningful for routing | experience-projection-contract.md | experience-model.md | CF8 Routing | E9, E14 | MAPPED | None |
| Merged-room execution scope | Merged scope remains meaningful for execution | capability-projection-contract.md | capability-projection-model.md | CF5 Planning | E5, E6 | MAPPED | None |
| Merged-room capability discovery / filtering | Capability visibility remains valid within merged scope | capability-projection-contract.md | capability-projection-model.md | CF3 Capability Resolution | E5 | MAPPED | None |
| Composite scope creation / maintenance | Household can create and maintain grouped scope | room-vocabulary-registry-contract.md | room-vocabulary-registry-model.md | CF5 Planning | E4 | MAPPED | None |
| Composite membership validation | Invalid grouping is rejected safely | occupancy-and-presence-contract.md | occupancy-presence-model.md | CF5 Planning | E8a | MAPPED | None |
| Composite membership synchronization | Missing members are pruned and stale composites can dismantle | room-vocabulary-registry-contract.md | room-vocabulary-registry-model.md | CF7 Diagnostics | E4 | MAPPED | None |
| Composite entity selection pruning | Removed members stop contributing stale entities | capability-projection-contract.md | capability-projection-model.md | CF3 Capability Resolution | E5 | MAPPED | None |
| Composite execution scope | Composite remains meaningful execution scope | capability-projection-contract.md | capability-projection-model.md | CF5 Planning | E5, E6 | MAPPED | None |
| Floor-aware scope metadata | Scope retains floor-aware behavior | occupancy-and-presence-contract.md | occupancy-presence-model.md | CF2 Context Assembly | E8a | MAPPED | None |
| Floor-aware scope behavior | Floor-aware grouping remains respected where observable | occupancy-and-presence-contract.md | occupancy-presence-model.md | CF8 Routing | E8a, E9 | MAPPED WITH FOLLOW-UP | direct floor execution follow-up |
| Same-floor composite enforcement | Cross-floor composite invalidation remains | occupancy-and-presence-contract.md | occupancy-presence-model.md | CF5 Planning | E8a | MAPPED | None |
| Scope target resolution | Scope remains targetable where supported | room-vocabulary-registry-contract.md | room-vocabulary-registry-model.md | CF8 Routing | E4, E9 | MAPPED | None |
| Scope capability visibility | Scope capabilities remain discoverable safely | capability-projection-contract.md | capability-projection-model.md | CF3 Capability Resolution | E5 | MAPPED | None |
| Hierarchy traversal | Target/scope resolution follows deterministic precedence | capability-projection-contract.md | capability-projection-model.md | CF5 Planning | E5, E6, E9 | MAPPED | None |
| Deterministic target precedence | Explicit/safe precedence remains consistent | capability-projection-contract.md | capability-projection-model.md | CF5 Planning | E5, E6 | MAPPED | None |
| Safe invalid target handling | Invalid scope rejected safely | occupancy-and-presence-contract.md | occupancy-presence-model.md | CF5 Planning | E8a, E9 | MAPPED | None |
| Safe unavailable target handling | Unavailable members are safely excluded | capability-projection-contract.md | capability-projection-model.md | CF5 Planning | E5, E9 | MAPPED | None |
| Unsupported capability handling | Unsupported capabilities blocked safely | capability-projection-contract.md | capability-projection-model.md | CF3 Capability Resolution | E5 | MAPPED | None |
| Household-wide context readout | Context payload can be retrieved by type | knowledge-briefing-status-synthesis-contract.md | knowledge-query-experience-model.md | CF2 Context Assembly | E10, E13, E14 | MAPPED | None |
| Household summary aggregation | Household summary synthesis remains | knowledge-briefing-status-synthesis-contract.md | briefing-composition-model.md | CF4 Experience Resolution | E13, E14 | MAPPED | None |
| Context-informed household summary | Summary remains context-informed | knowledge-briefing-status-synthesis-contract.md | briefing-composition-model.md | CF4 Experience Resolution | E13, E14 | MAPPED | None |
| Global context readout | Global context payload visibility remains | knowledge-briefing-status-synthesis-contract.md | knowledge-query-experience-model.md | CF2 Context Assembly | E10, E13 | MAPPED | None |
| Signal readout | Signal visibility remains | knowledge-briefing-status-synthesis-contract.md | briefing-composition-model.md | CF2 Context Assembly | E13, E14 | MAPPED | None |
| Home status awareness | Household-wide awareness remains visible | household-coordination-contract.md | household-coordination-snapshot-model.md | CF4 Experience Resolution | E14 | MAPPED WITH FOLLOW-UP | home-status provider boundary |
| Occupancy / presence reference consumption | Occupancy context remains consumable | occupancy-and-presence-contract.md | occupancy-presence-model.md | CF2 Context Assembly | E8a, E10 | MAPPED | None |
| Environmental context consumption where observable | Weather/news/environment context remains available | knowledge-briefing-status-synthesis-contract.md | knowledge-query-experience-model.md | CF2 Context Assembly | E13 | MAPPED WITH FOLLOW-UP | environmental provider boundary |
| Platform-state awareness where observable | Platform state remains visible | knowledge-briefing-status-synthesis-contract.md | experience-model.md | CF7 Diagnostics | E13 | MAPPED WITH FOLLOW-UP | platform-state visibility scope |
| Shared context availability | Shared context remains accessible | household-memory-contract.md | household-memory-model.md | CF2 Context Assembly | E10, E13, E14 | MAPPED | None |
| Context visibility in diagnostics / timeline | Context changes remain traceable | provenance-contract.md | provenance-model.md | CF7 Diagnostics | E10, E14 | MAPPED | None |
| Context participation in planning / routing | Context remains valid input to decisions | experience-projection-contract.md | experience-model.md | CF5 Planning | E9, E13, E14 | MAPPED | None |
| Person-scoped mobile push routing | Person-targeted push routing remains | occupancy-and-presence-contract.md | occupancy-presence-model.md | CF8 Routing | E9 | MAPPED | None |
| Activity timeline visibility | Timeline and outcome history remain available | provenance-contract.md | provenance-model.md | CF7 Diagnostics | E10, E14 | MAPPED | None |

## Contract Coverage Matrix
| Contract | V1 Outcomes Covered | Notes |
|---|---|---|
| Room Vocabulary Registry Contract | room targeting, alias resolution, merged/composite target resolution | room/scope language remains external authority |
| Capability Projection Contract | room execution, composite capability visibility, unsupported capability handling | capability outcomes consumed, not owned |
| Experience Projection Contract | routing scope, context participation in planning/routing | experience authority remains external |
| Occupancy and Presence Contract | occupancy references, same-floor enforcement, policy gating | occupancy truth remains external |
| Household Memory Contract | shared context availability | memory authority remains external |
| Provenance Contract | diagnostics, timeline, traceability | provenance authority remains external |
| Knowledge / Briefing / Status Synthesis Contract | summary/context/home-status/environment outputs | summary and awareness outcomes |
| Household Coordination Contract | home status / coordination outcomes | coordination consumption only |
| Multi-Item Capture Interpretation Contract | NOT APPLICABLE | no evidenced V1 household-facing outcome in current preservation scope |

## Model Coverage Matrix
| Model | V1 Outcomes Covered | Notes |
|---|---|---|
| Room Vocabulary Registry Model | room targeting, alias resolution, scope targeting | vocabulary consumed externally |
| Capability Projection Model | execution eligibility, scope capability visibility, unsupported capability handling | capability authority external |
| Experience Model | routing/planning/context participation | experience authority external |
| Occupancy Presence Model | occupancy/presence reference consumption, policy gating | occupancy authority external |
| Household Memory Model | shared context availability | memory authority external |
| Provenance Model | diagnostics/timeline visibility | provenance authority external |
| Experience Restoration Context Model | follow-up restoration interaction only | mapped as non-blocking follow-up |
| Household Coordination Snapshot Model | home status / coordination awareness outcomes | coordination authority external |
| Briefing Composition Model | household summary aggregation | summary awareness surface |
| Knowledge Query Experience Model | global context readout/environment knowledge context | context awareness surface |

## Coordinator Foundation Coverage Matrix
| Coordinator Foundation Area | V1 Outcomes Covered | Notes |
|---|---|---|
| CF1 Runtime Boundary | all outcomes via non-rights and external authority boundaries | bounded orchestrator role |
| CF2 Context Assembly | room targeting, context readout, occupancy references, shared/global context | source inputs normalized here |
| CF3 Capability Resolution | capability visibility, unsupported handling, merged/composite scope capability filtering | capability authority consumed |
| CF4 Experience Resolution | household summary, context-aware experience outcomes, coordination/awareness surfaces | experience authority consumed |
| CF5 Planning | execution hierarchy, target precedence, invalid/unavailable target handling | planning preserves outcomes |
| CF6 Explainability | why/why-not for routing, targeting, hierarchy, context participation | explanation support required |
| CF7 Diagnostics | activity timeline visibility, context traceability, execution traceability | diagnostics parity required |
| CF8 Routing | room/person/merged/composite/household routing outcomes | routing parity required |
| CF9 Execution Envelope | routing/planning/explainability references for preserved outcomes | downstream handoff artifact |
| CF10 Readiness Review | overall readiness and no ownership drift baseline | foundation approved |

## Future Epic Coverage Matrix
| Future Epic | V1 Outcomes Covered | Notes |
|---|---|---|
| E4 | room targeting, alias resolution, merged/composite scope naming and targeting | room vocabulary consumption |
| E5 | room execution, capability eligibility, scope capability visibility | capability projection consumption |
| E6 | summary/experience-aware outcomes, routing scope behavior | experience consumption |
| E7 | person-linked room resolution and continuity/affinity-adjacent behavior | future continuity mapping |
| E8 | restoration-adjacent safety outcomes and follow-up restoration interactions | restoration follow-up |
| E8a | occupancy/presence references, same-floor enforcement, policy gating | occupancy consumption |
| E9 | person-scoped mobile push routing, room/merged/composite/household routing | messaging/notification discipline |
| E10 | shared context, timeline visibility, explainability/diagnostics of context | memory and explainability |
| E13 | household summary, global context, signal readout, productivity-aware context consumption | productivity experiences |
| E14 | household coordination, home status awareness, context/routing/diagnostics consumption | household coordination |

## Orphan Outcome Review
All identified V1 outcomes were reviewed.

All outcomes are mapped to at least one contract, model, Coordinator Foundation area, and future epic or are explicitly marked `MAPPED WITH FOLLOW-UP` where additional clarification is non-blocking.

No orphan outcomes remain.

## Follow-Up Mapping Items
Non-blocking follow-up items:
- floor-wide announcement behavior
- explicit floor-level execution
- explicit whole-house execution
- whole-house routing interaction
- restoration behavior interaction
- composite/merged terminology ambiguity
- zone terminology ambiguity
- explicit home-status provider boundary
- explicit environmental context provider boundary
- platform-state visibility scope
- whole-house summary context inputs
- occupancy reference source mapping
- signal/context terminology consistency
- future household status synthesis model mapping

These are non-blocking unless later evidence proves otherwise.

## Ownership Validation
Coordinator V2 may consume, orchestrate, route, plan, explain, diagnose, and envelope preserved outcomes.

Coordinator V2 may not redefine:
- room vocabulary authority
- room truth
- area truth
- floor / zone truth
- occupancy truth
- identity authority
- capability projection authority
- experience projection authority
- memory authority
- provenance authority
- provider ownership

## Parity Rules
For every mapped outcome:
- household-facing outcome must remain
- implementation may change
- internals may be replaced
- diagnostics must support parity verification where relevant
- explainability must support why/why-not where relevant
- no provider ownership moves into Concierge
- no HTBW ownership moves into Concierge

## Required Future GitHub Copilot Usage
Before implementation work that may affect any preserved Concierge V1 household-facing outcome, GitHub Copilot must read:
- `docs/governance/coordinator-v2-foundation-summary.md`
- `docs/governance/concierge-v1-outcome-preservation-baseline.md`
- `docs/governance/merged-room-outcome-preservation-contract.md`
- `docs/governance/composite-room-scope-outcome-preservation-contract.md`
- `docs/governance/execution-hierarchy-outcome-preservation-contract.md`
- `docs/governance/global-context-outcome-preservation-contract.md`
- `docs/governance/v1-to-v2-capability-parity-matrix.md`
- the relevant CF or E3a issue baseline
- relevant HTBW contracts and models
- the target issue last

GitHub Copilot must ask:

Can the household still achieve the same V1 outcome in the V2 architecture?

GitHub Copilot must not ask:

Does the V1 implementation work the same way internally?

## Readiness Statement
V1-to-V2 capability parity mapping matrix is READY for downstream E3a and Coordinator V2 implementation consumption.

For regression validation of mapped outcomes, see:

- `docs/governance/v1-outcome-regression-checklist.md`