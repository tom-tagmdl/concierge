# Merged Room Outcome Preservation Contract

## Purpose
This document is the implementation-time preservation contract for merged-room household-facing outcomes.

It defines what merged-room behavior must remain observable during Coordinator V2 migration and future implementation work.

## Authority Relationship
- ADR-013 governs preservation philosophy.
- Issue #63 defines the broader V1 preservation inventory.
- Issue #64 defines merged-room preservation expectations.
- This document is the implementation contract for merged-room preservation.
- This document does not replace HTBW ADRs, contracts, or models.

Authority chain:

ADRs
  -> Contracts
  -> Models
  -> Issue #63 V1 preservation baseline
  -> Issue #64 merged-room review
  -> This preservation contract
  -> Implementation issues

## Governing Principle
Preserve merged-room household-facing outcomes.

Do not preserve merged-room implementation details.

## Merged Room Definition
Merged-room behavior is an observable household-facing scope behavior where multiple rooms participate as a single targetable, routable, executable, or context-aware household zone.

Merged rooms are not defined by current storage, helper functions, panel code, or service internals.

## Required Preserved Outcomes

### 1. Merged-room creation
- Household-facing behavior: household can create a merged room scope from multiple rooms.
- Current evidence source: `update_composite_config` flow and `tests/test_services.py` merged/composite tests.
- Preservation requirement: preserve creation outcome.
- Implementation preservation required: NO.

### 2. Merged-room rename
- Household-facing behavior: household can rename a merged room scope.
- Current evidence source: composite rename test coverage and panel edit flow.
- Preservation requirement: preserve rename outcome.
- Implementation preservation required: NO.

### 3. Merged-room membership edit
- Household-facing behavior: household can change member rooms of a merged scope.
- Current evidence source: composite membership edit tests and panel edit flow.
- Preservation requirement: preserve membership edit outcome.
- Implementation preservation required: NO.

### 4. Merged-room dismantle
- Household-facing behavior: household can dismantle a merged room scope.
- Current evidence source: dismantle path in `update_composite_config` and tests.
- Preservation requirement: preserve dismantle outcome.
- Implementation preservation required: NO.

### 5. Same-floor membership enforcement where currently observable
- Household-facing behavior: invalid cross-floor merged-room membership is rejected.
- Current evidence source: cross-floor rejection tests.
- Preservation requirement: preserve same-floor enforcement outcome.
- Implementation preservation required: NO.

### 6. Merged-room target resolution
- Household-facing behavior: merged-room scope can be resolved as a valid operational target where configured.
- Current evidence source: composite state, panel composite selection behavior, execution-preference scope handling.
- Preservation requirement: preserve merged-scope targetability.
- Implementation preservation required: NO.

### 7. Merged-room routing scope
- Household-facing behavior: merged-room scope remains a meaningful routing target where currently observable.
- Current evidence source: composite selection state and future routing dependency from Coordinator foundation.
- Preservation requirement: preserve room-group routing outcome.
- Implementation preservation required: NO.

### 8. Merged-room execution scope
- Household-facing behavior: merged-room scope remains a meaningful execution scope where configured.
- Current evidence source: composite configuration/state and room execution model.
- Preservation requirement: preserve merged execution scope outcome.
- Implementation preservation required: NO.

### 9. Merged-room capability discovery or capability filtering behavior
- Household-facing behavior: capabilities available to merged-room scope remain discoverable and constrained to valid members.
- Current evidence source: composite entity pruning/sync behavior and panel composite catalogs.
- Preservation requirement: preserve member-valid capability outcome.
- Implementation preservation required: NO.

### 10. Merged-room context behavior
- Household-facing behavior: merged-room scope remains visible to coordinator/runtime as a valid context grouping.
- Current evidence source: composite state and panel selection behavior.
- Preservation requirement: preserve merged-scope context outcome.
- Implementation preservation required: NO.

### 11. Merged-room diagnostics and visibility where currently observable
- Household-facing behavior: merged-room changes remain visible through diagnostics/timeline evidence and UI-visible state changes.
- Current evidence source: backend activity timeline and panel composite state.
- Preservation requirement: preserve diagnostic visibility outcome.
- Implementation preservation required: NO.

## Merged Room Execution Preservation
Merged-room execution must remain observable as a household-facing outcome where merged scope is configured and used as an execution boundary.

What must remain observable:
- merged scope can be acted on as a group outcome
- deterministic behavior remains consistent
- invalid member state is safely pruned rather than leaking into execution

What may change internally:
- storage model
- service handlers
- helper functions
- UI implementation
- runtime wiring

Coordinator V2 may consume merged-room scope as context and execution scope without owning room truth.

## Merged Room Resolution Preservation
Merged-room scope resolution must preserve:
- stable recognition of merged scope as a household-facing targetable zone
- deterministic handling of valid vs invalid membership
- participation of aliases or vocabulary where currently observable

Room Vocabulary authority remains external.

## Merged Room Targeting Preservation
Preserve:
- explicit merged-room targeting where configured
- contextual merged-room targeting where currently observable
- target-scope preservation
- target eligibility preservation

## Merged Room Capability Discovery Preservation
Capabilities visible to merged rooms must remain discoverable as household-facing outcomes.

Capability Projection authority remains external.

Coordinator consumes projected capability context and must not redefine projection ownership.

## Merged Room Context Preservation
Merged-room context must remain visible to Coordinator V2 as a governed input.

Context may be represented differently internally.

Household-facing behavior must remain.

## Same-Floor / Boundary Preservation
Preserve:
- same-floor membership enforcement where currently observable
- prevention of invalid cross-floor merged-room membership where currently observable

Floor authority remains external.

## Composite Relationship
Merged-room outcomes may overlap with composite-scope outcomes.

Implementation may unify or separate internal representation.

Household-facing outcomes must remain distinct where currently observable.

## Coordinator V2 Interaction
Coordinator V2 must consume merged-room behavior through:
- context assembly
- capability resolution
- experience resolution
- planning
- routing
- execution envelope

Coordinator may consume merged-room context.

Coordinator may not redefine room authority.

## Ownership Matrix
| Capability Family | Authority | Concierge Role | Boundary |
|---|---|---|---|
| Room Vocabulary | HTBW Room Vocabulary governance | consume vocabulary/alias context | no vocabulary ownership transfer |
| Room Truth / Area Truth | Home Assistant area/floor truth + HTBW room governance | consume room/floor truth | no room truth ownership |
| Capability Projection | HTBW capability governance | consume capability outcomes | no capability ownership |
| Experience Projection | HTBW experience governance | consume experience outcomes | no experience ownership |
| Occupancy / Presence | HTBW occupancy governance | consume occupancy/presence context | no occupancy truth ownership |
| Coordinator V2 | Concierge orchestration runtime | consume and orchestrate merged scope outcomes | bounded orchestrator only |
| External Providers | provider systems | execute underlying actions/delivery | provider ownership remains external |

## Merged Room Capability Matrix
| Capability | Household-Facing Outcome | Current Evidence | Must Preserve | Implementation Preservation Required |
|---|---|---|---|---|
| Merged-room creation | Household can create merged scope | `update_composite_config`, tests, panel | YES | NO |
| Merged-room rename | Household can rename merged scope | tests, panel edit flow | YES | NO |
| Merged-room membership edit | Household can change member rooms | tests, panel edit flow | YES | NO |
| Merged-room dismantle | Household can remove merged scope | tests, dismantle path | YES | NO |
| Same-floor enforcement | Cross-floor merged scope is rejected | tests | YES | NO |
| Merged-room target resolution | Merged scope remains targetable | composite state/panel behavior | YES | NO |
| Merged-room execution scope | Merged scope remains executable where supported | runtime scope evidence | YES | NO |
| Member-valid entity pruning | Removed members no longer contribute stale entities | tests | YES | NO |
| Merged-room context visibility | Merged scope remains visible as context grouping | panel/state evidence | YES | NO |
| Merged-room diagnostics visibility | Merged scope changes remain traceable/visible | diagnostics + panel state | YES | NO |

## Parity Expectations
Future implementation must verify:
- household can still create merged-room scope
- household can still edit merged-room membership
- household can still dismantle merged-room scope
- merged-room targeting behaves consistently
- merged-room execution remains possible where currently supported
- invalid scope behavior remains safely handled
- capability discovery respects merged-room scope
- routing and planning can consume merged-room scope

## Diagnostics and Explainability Expectations
Future implementation must be able to explain:
- why a merged room was selected
- why a merged room was rejected
- why a room member participated
- why a room member was excluded
- why merged-room execution was unavailable
- why same-floor enforcement applied

## Non-Rights
Merged-room preservation does NOT require preserving:
- current helper methods
- current service internals
- current storage format
- current API shape
- current entity implementation
- current panel implementation

Merged-room preservation DOES require preserving observable household outcomes.

## Follow-Up Validation Items
Non-blocking follow-up observations:
- floor-wide announcement behavior
- whole-house routing interaction
- restoration behavior interaction
- composite/merged terminology ambiguity

These are not blocking unless later evidence proves otherwise.

## Downstream Use
This document must be consumed by:
- E3a routing reviews
- E3a restoration reviews
- E3a execution reviews
- E3a room targeting reviews
- E4 Room Vocabulary Consumption
- E5 Capability Projection Consumption
- E6 Experience Consumption
- later Coordinator V2 implementation work touching merged-room behavior

## Required Future GitHub Copilot Usage
Before implementation work that may affect merged-room household-facing outcomes, GitHub Copilot must read:
- `docs/governance/coordinator-v2-foundation-summary.md`
- `docs/governance/concierge-v1-outcome-preservation-baseline.md`
- `docs/governance/merged-room-outcome-preservation-contract.md`
- the relevant CF or E3a issue baseline
- relevant HTBW contracts and models
- the target issue last

GitHub Copilot must ask:

Can the household still achieve the same merged-room outcome?

GitHub Copilot must not ask:

Does the merged-room implementation work the same way internally?

## Readiness Statement
Merged-room outcome preservation contract is READY for downstream E3a and Coordinator V2 implementation consumption.