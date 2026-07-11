# Composite Room and Scope Outcome Preservation Contract

## Purpose
This document is the implementation-time preservation contract for composite-room and scope-aware household-facing outcomes.

This contract is consumed by E3a and later Coordinator V2 implementation work.

## Authority Relationship
- ADR-013 governs preservation philosophy.
- Issue #63 defines the broader V1 preservation inventory.
- Issue #64 defines merged-room preservation expectations.
- Issue #65 defines composite-room and hierarchy-scope preservation expectations.
- This document is the implementation contract for composite-room and scope preservation.
- This document does not replace HTBW ADRs, contracts, or models.

Authority chain:

ADRs
  -> Contracts
  -> Models
  -> Issue #63 V1 preservation baseline
  -> Issue #64 merged-room preservation contract
  -> Issue #65 composite-room/scope review
  -> This preservation contract
  -> Implementation issues

## Governing Principle
Preserve composite-room and scope-aware household-facing outcomes.

Do not preserve composite-room implementation details.

The correct preservation question is:

Can the household still achieve the same composite-room or scope-aware outcome?

The incorrect preservation question is:

Does the composite-room implementation work the same way internally?

## Composite Room Definition
Composite-room behavior is an observable household-facing scope behavior where multiple rooms, zones, floors, or household scopes participate in a single targetable, routable, executable, or context-aware scope.

Composite rooms are not defined by current storage, helper methods, entity shape, panel implementation, or service internals.

## Scope Definitions
- individual room scope
  - household-facing meaning: one resolved room acts as the active targetable space
  - authority boundary: room truth remains external
  - implementation-preservation requirement: NO
- merged-room scope
  - household-facing meaning: multiple rooms behave as one targetable scope
  - authority boundary: room/floor truth remains external
  - implementation-preservation requirement: NO
- composite-room scope
  - household-facing meaning: configured multi-room scope participates as one operational zone
  - authority boundary: room/floor truth remains external
  - implementation-preservation requirement: NO
- floor scope
  - household-facing meaning: floor-aware grouping informs valid targeting and grouping behavior
  - authority boundary: floor truth remains external
  - implementation-preservation requirement: NO
- zone scope
  - household-facing meaning: grouped operational zone if exposed to household behavior
  - authority boundary: scope truth remains external
  - implementation-preservation requirement: NO
- whole-house scope
  - household-facing meaning: house-wide awareness or targeting scope where observable
  - authority boundary: provider and home truth remain external
  - implementation-preservation requirement: NO
- household scope
  - household-facing meaning: household-wide informational or coordination surface
  - authority boundary: source domains remain external
  - implementation-preservation requirement: NO

## Required Preserved Outcomes

### Composite scoped execution context
- household-facing behavior: composite scope can act as a valid execution context
- current evidence source: composite state, panel composite catalog, tests
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Composite room creation or maintenance where currently observable
- household-facing behavior: household can create and maintain composite scope definitions
- current evidence source: `update_composite_config`, panel merge/edit flows, tests
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Composite membership validation
- household-facing behavior: invalid membership is rejected or constrained safely
- current evidence source: cross-floor rejection tests and validation logic
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Composite membership synchronization
- household-facing behavior: missing/invalid members are pruned and stale composites can dismantle
- current evidence source: `sync_composites` tests
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Composite entity selection pruning
- household-facing behavior: selected entities remain constrained to valid member rooms only
- current evidence source: entity pruning tests
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Floor-scope awareness
- household-facing behavior: floor identity participates in scope behavior where configured
- current evidence source: composite `floor_id`, panel floor data, tests
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Same-floor enforcement where currently observable
- household-facing behavior: cross-floor composite grouping is rejected
- current evidence source: tests
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Zone-scope behavior where currently observable
- household-facing behavior: broader grouped-scope behavior remains visible where explicitly surfaced
- current evidence source: panel scope/catalog model, docs, inferred future scope surface
- preservation requirement: preserve currently observable outcome only
- implementation preservation required: NO

### Hierarchy traversal
- household-facing behavior: target/scope resolution follows deterministic precedence
- current evidence source: execution hierarchy docs and composite scope tests
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Hierarchy precedence
- household-facing behavior: explicit/safe precedence is maintained across scope choices
- current evidence source: execution hierarchy docs, implementation checklist
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Scope target resolution
- household-facing behavior: room/composite/floor/household scope can resolve to valid operational target where supported
- current evidence source: services + panel + docs
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Scope routing behavior
- household-facing behavior: scope can participate in routing decisions where observable
- current evidence source: foundation routing baseline plus composite scope evidence
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Scope capability discovery / filtering
- household-facing behavior: capabilities visible to composite/floor/group scopes remain discoverable and safely filtered
- current evidence source: composite catalog build + entity pruning tests
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Scope context visibility
- household-facing behavior: scope remains visible as valid contextual input
- current evidence source: panel state + composite state + foundation context rules
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Scope diagnostics / visibility behavior
- household-facing behavior: scope changes remain visible to diagnostics/timeline and UI state where observable
- current evidence source: activity timeline + panel composite state
- preservation requirement: preserve outcome
- implementation preservation required: NO

## Composite Room Execution Preservation
Composite-room execution must remain observable as a household-facing outcome where composite scope is configured and used as an execution boundary.

What must remain observable:
- composite scope can be acted on as one meaningful target context
- deterministic member validity behavior remains
- invalid or removed member state does not leak into execution behavior

What may change internally:
- storage model
- service handlers
- panel implementation
- helper methods
- internal scope representation

Coordinator V2 may consume composite scope without owning room truth.

## Composite Room Resolution Preservation
Composite-room scope resolution must preserve:
- stable recognition of configured scope
- deterministic handling of valid vs invalid membership
- participation of aliases or vocabulary where currently observable
- deterministic hierarchy traversal where scope ambiguity exists

Room Vocabulary authority remains external.

## Composite Room Targeting Preservation
Preserve:
- explicit composite-room targeting
- contextual composite-room targeting where currently observable
- scope target preservation
- target eligibility preservation

## Floor Scope Preservation
Preserve:
- same-floor enforcement where currently observable
- floor identity awareness in merged/composite state
- floor-aware scope behavior
- prevention of invalid cross-floor behavior where currently observable

Floor authority remains external.

## Zone Scope Preservation
Preserve zone-level scope behavior where currently observable.

Relationship notes:
- zone scope may overlap composite-room behavior
- zone scope may interact with floor scope
- zone scope may interact with whole-house scope

If zone behavior is not fully evidenced, treat it as follow-up validation rather than blocker.

## Whole-House Scope Preservation
Preserve household-wide or whole-house outcomes currently evidenced, including:
- household summary/context surfaces
- whole-house or household-wide targeting where currently evidenced

If explicit whole-house execution is not fully confirmed, treat it as follow-up validation rather than blocker.

## Hierarchy Traversal Preservation
Preserve observable hierarchy behavior, including:
- room before composite where applicable
- composite before floor where applicable
- floor before whole-house where applicable
- deterministic precedence
- safe fallback behavior
- invalid scope fallback behavior

Hierarchy is defined by observable routing/targeting behavior, not helper methods.

## Capability Discovery Preservation
Capabilities visible to composite/floor/zone scopes must remain discoverable as household-facing outcomes.

Capability Projection authority remains external.

Coordinator consumes projected capability context and must handle invalid or unavailable members safely.

## Context Preservation
Composite-room context must remain visible to Coordinator V2 as a governed input.

Floor/zone/whole-house scope context must remain visible where currently observable.

Context may be represented differently internally.

Household-facing behavior must remain.

## Composite / Merged Room Relationship
- merged-room outcomes may overlap composite-scope outcomes
- composite-room scope may include broader hierarchy behavior than merged-room scope
- implementation may unify or separate internal representation
- household-facing outcomes must remain distinct where currently observable

## Coordinator V2 Interaction
Coordinator V2 must consume composite-room and scope behavior through:
- context assembly
- capability resolution
- experience resolution
- planning
- routing
- execution envelope

Coordinator may consume composite/scope context.

Coordinator may not redefine room, vocabulary, floor, occupancy, capability, or provider authority.

## Ownership Matrix
| Capability Family | Authority | Concierge Role | Boundary |
|---|---|---|---|
| Room Vocabulary | HTBW Room Vocabulary governance | consume vocabulary/alias context | no vocabulary ownership transfer |
| Room Truth / Area Truth | Home Assistant area truth + HTBW room governance | consume room truth | no room truth ownership |
| Floor / Zone Truth | Home Assistant floor truth and governed scope semantics | consume floor/zone context | no floor/zone truth ownership |
| Capability Projection | HTBW capability governance | consume projected capability outcomes | no capability ownership |
| Experience Projection | HTBW experience governance | consume experience outcomes | no experience ownership |
| Occupancy / Presence | HTBW occupancy governance | consume occupancy/presence context | no occupancy truth ownership |
| Coordinator V2 | Concierge orchestration runtime | consume and orchestrate scope outcomes | bounded orchestration role only |
| External Providers | provider systems | execute underlying actions/delivery | provider ownership remains external |

## Composite Room Capability Matrix
| Capability | Household-Facing Outcome | Current Evidence | Must Preserve | Implementation Preservation Required |
|---|---|---|---|---|
| Composite scope creation/maintenance | Household can create and maintain grouped scope | services, panel, tests | YES | NO |
| Composite membership validation | Invalid grouping is rejected safely | tests | YES | NO |
| Composite membership synchronization | Missing members are pruned and empty scopes can dismantle | tests | YES | NO |
| Composite entity pruning | Removed members stop contributing stale entities | tests | YES | NO |
| Composite execution scope | Composite remains meaningful execution scope | services/panel/docs | YES | NO |
| Floor-aware scope metadata | Scope retains floor-aware behavior | services/panel/tests | YES | NO |
| Same-floor enforcement | Cross-floor composite invalidation remains | tests | YES | NO |
| Scope target resolution | Scope remains targetable where supported | services/panel | YES | NO |
| Scope capability visibility | Scope capabilities remain discoverable safely | panel catalog/tests | YES | NO |
| Scope diagnostics visibility | Scope changes remain visible diagnostically | timeline/panel state | YES | NO |

## Scope Parity Matrix
| Scope Type | Expected Household Outcome | Parity Required | Notes |
|---|---|---|---|
| room | explicit room remains targetable | YES | baseline scope |
| merged room | merged scope remains targetable/editable | YES | see Issue #64 contract |
| composite room | configured grouped scope remains meaningful | YES | core focus of this contract |
| floor | floor-aware grouping remains respected where observable | YES | no cross-floor invalid scope leakage |
| zone | zone-like grouped scope remains where currently observable | YES | follow-up if evidence incomplete |
| whole house | household-wide scope remains where evidenced | YES | explicit execution may require validation |
| household | household-wide summary/context outcomes remain | YES | informational/coordination surface |

## Hierarchy Traversal Matrix
| Traversal Scenario | Expected Outcome | Must Preserve | Notes |
|---|---|---|---|
| explicit room target | direct room target wins when specified | YES | deterministic targeting |
| explicit composite target | configured composite scope resolves predictably | YES | grouped scope precedence |
| floor target | floor-aware scope remains meaningful where observable | YES | floor truth external |
| invalid cross-floor target | invalid scope rejected safely | YES | no unsafe merge |
| unavailable member target | invalid member pruned or excluded safely | YES | no stale scope leakage |
| whole-house fallback | broader scope fallback remains safe where observable | YES | validate explicit execution separately |
| ambiguous target | ambiguity handled deterministically | YES | may require clarification or stable precedence |

## Parity Expectations
Future implementation must verify:
- household can still consume composite-room scope
- household can still target composite-room scope where currently supported
- household can still benefit from floor-aware behavior
- hierarchy traversal remains deterministic
- invalid scope behavior remains safely handled
- composite capability discovery remains scope-aware
- routing and planning can consume composite scope
- diagnostics can explain scope decisions

## Diagnostics and Explainability Expectations
Future implementation must be able to explain:
- why a composite room was selected
- why a floor scope was selected
- why a zone scope was selected
- why a room member participated
- why a room member was excluded
- why scope traversal occurred
- why scope traversal stopped
- why composite/floor execution was unavailable
- why same-floor enforcement applied

## Non-Rights
Composite-room preservation does NOT require preserving:
- current helper methods
- current service internals
- current storage format
- current API shape
- current entity implementation
- current panel implementation
- current terminology where a clearer governed term replaces it

Composite-room preservation DOES require preserving observable household outcomes.

## Follow-Up Validation Items
Non-blocking follow-up observations:
- floor-wide announcement behavior
- whole-house routing interaction
- explicit whole-house execution
- restoration behavior interaction
- composite/merged terminology ambiguity
- zone terminology ambiguity

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
- later Coordinator V2 implementation work touching composite-room, floor-scope, zone-scope, or hierarchy traversal behavior

## Required Future GitHub Copilot Usage
Before implementation work that may affect composite-room, floor-scope, zone-scope, whole-house-scope, or hierarchy traversal household-facing outcomes, GitHub Copilot must read:
- `docs/governance/coordinator-v2-foundation-summary.md`
- `docs/governance/concierge-v1-outcome-preservation-baseline.md`
- `docs/governance/merged-room-outcome-preservation-contract.md`
- `docs/governance/composite-room-scope-outcome-preservation-contract.md`
- the relevant CF or E3a issue baseline
- relevant HTBW contracts and models
- the target issue last

GitHub Copilot must ask:

Can the household still achieve the same composite-room or scope-aware outcome?

GitHub Copilot must not ask:

Does the composite-room implementation work the same way internally?

## Readiness Statement
Composite-room and scope-aware outcome preservation contract is READY for downstream E3a and Coordinator V2 implementation consumption.