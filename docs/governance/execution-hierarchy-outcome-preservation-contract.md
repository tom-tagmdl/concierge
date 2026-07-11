# Execution Hierarchy Outcome Preservation Contract

## Purpose
This document is the implementation-time preservation contract for Concierge V1 execution hierarchy household-facing outcomes.

This contract is consumed by E3a and later Coordinator V2 implementation work.

## Authority Relationship
- ADR-013 governs preservation philosophy.
- Issue #63 defines the broader V1 preservation inventory.
- Issue #64 defines merged-room preservation expectations.
- Issue #65 defines composite-room and scope preservation expectations.
- Issue #66 defines execution hierarchy preservation expectations.
- This document is the implementation contract for execution hierarchy preservation.
- This document does not replace HTBW ADRs, contracts, or models.

Authority chain:

ADRs
  -> Contracts
  -> Models
  -> Issue #63 V1 preservation baseline
  -> Issue #64 merged-room preservation contract
  -> Issue #65 composite-room/scope preservation contract
  -> Issue #66 execution hierarchy review
  -> This preservation contract
  -> Implementation issues

## Governing Principle
Preserve execution hierarchy household-facing outcomes.

Do not preserve execution hierarchy implementation details.

The correct preservation question is:

Can the household still achieve the same execution hierarchy outcome?

The incorrect preservation question is:

Does the execution hierarchy implementation work the same way internally?

## Execution Hierarchy Definition
Execution hierarchy is the observable household-facing ordering and fallback behavior used when Concierge determines where and how an execution request should apply across room, merged-room, composite-room, floor, and house-level scopes.

Execution hierarchy is not defined by current helper methods, service internals, entity shape, panel implementation, or storage format.

## Scope Levels Covered
- individual room execution
  - household-facing meaning: a single room is the direct execution scope
  - authority boundary: room truth remains external
  - implementation-preservation requirement: NO
- merged-room execution
  - household-facing meaning: configured merged room acts as one execution scope
  - authority boundary: room/floor truth remains external
  - implementation-preservation requirement: NO
- composite-room execution
  - household-facing meaning: configured composite scope acts as one execution scope
  - authority boundary: room/floor truth remains external
  - implementation-preservation requirement: NO
- floor-level execution
  - household-facing meaning: floor-aware grouping influences execution scope where observable
  - authority boundary: floor truth remains external
  - implementation-preservation requirement: NO
- zone-level execution where currently observable
  - household-facing meaning: grouped zone behavior participates in execution where surfaced
  - authority boundary: scope truth remains external
  - implementation-preservation requirement: NO
- whole-house execution where currently observable
  - household-facing meaning: house-wide targeting/execution behavior participates where evidenced
  - authority boundary: provider and home truth remain external
  - implementation-preservation requirement: NO
- household-level execution where currently observable
  - household-facing meaning: broader household execution/coordination scope where evidenced
  - authority boundary: source/provider truth remains external
  - implementation-preservation requirement: NO

## Required Preserved Outcomes

### Room-level execution outcome
- household-facing behavior: room-level requests execute against the intended room scope
- current evidence source: `execute` handler, README examples, room-target tests
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Merged-room execution outcome
- household-facing behavior: merged-room scope remains a valid execution scope where currently supported
- current evidence source: merged/composite scope tests, panel state, Issue #64 contract
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Composite-room execution outcome
- household-facing behavior: composite-room scope remains a valid execution scope where currently supported
- current evidence source: composite tests, panel composite catalog, Issue #65 contract
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Floor-scope execution outcome where currently observable
- household-facing behavior: floor-aware scope behavior constrains or informs valid execution grouping
- current evidence source: same-floor enforcement tests, floor metadata in state/panel
- preservation requirement: preserve outcome
- implementation preservation required: NO

### House-level or household-level execution outcome where currently observable
- household-facing behavior: whole-house or household-wide targeting/execution behavior remains where evidenced
- current evidence source: README household-wide awareness surfaces, summary/context outputs
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Deterministic execution hierarchy fallback
- household-facing behavior: execution follows a predictable precedence and fallback path
- current evidence source: README execution patterns, `execute` service behavior
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Deterministic target precedence
- household-facing behavior: explicit targets and valid scopes win deterministically over broader or inferred fallbacks
- current evidence source: execution docs/tests and scope contracts
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Policy gating before execution
- household-facing behavior: disallowed or unsafe execution is blocked before actuation
- current evidence source: minor-policy enforcement in services, tests
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Safe invalid-target handling
- household-facing behavior: invalid scope/target is rejected or safely constrained instead of misfiring
- current evidence source: cross-floor rejection, composite sync pruning, service validation
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Safe unavailable-target handling
- household-facing behavior: unavailable or removed members are safely excluded or pruned
- current evidence source: stale entity/member pruning tests
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Capability-aware execution eligibility
- household-facing behavior: execution respects available capability context where currently observable
- current evidence source: CF3/CF5 baseline dependencies and scope filtering evidence
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Scope-aware execution planning
- household-facing behavior: planning respects resolved room/merged/composite/floor scope before downstream execution
- current evidence source: CF5 planning baseline and current target-resolution flow
- preservation requirement: preserve outcome
- implementation preservation required: NO

### Execution diagnostics / visibility behavior
- household-facing behavior: execution intent/outcome remains visible through diagnostics/timeline evidence
- current evidence source: activity timeline tests and service activity lifecycle
- preservation requirement: preserve outcome
- implementation preservation required: NO

## Room-Level Execution Preservation
Room-level execution must remain observable as a household-facing outcome.

What must remain observable:
- explicit room targeting participates in execution
- contextual room targeting may participate where currently observable
- requests execute deterministically against intended room scope

What may change internally:
- routing helpers
- service internals
- state wiring
- panel flows

Coordinator V2 may consume room execution context.

Coordinator V2 may not redefine room authority.

## Merged-Room Execution Preservation
Merged-room execution must preserve observable behavior defined in Issue #64 and [docs/governance/merged-room-outcome-preservation-contract.md](r:/HomesPlatformRepos/concierge/docs/governance/merged-room-outcome-preservation-contract.md).

What must remain observable:
- merged-room scope can participate in execution where currently supported
- invalid merged scope is handled safely

This document references, and does not replace, the merged-room contract.

## Composite-Room Execution Preservation
Composite-room execution must preserve observable behavior defined in Issue #65 and [docs/governance/composite-room-scope-outcome-preservation-contract.md](r:/HomesPlatformRepos/concierge/docs/governance/composite-room-scope-outcome-preservation-contract.md).

What must remain observable:
- composite scope can participate in execution where currently supported
- scope membership and hierarchy traversal inform valid execution behavior

This document references, and does not replace, the composite-room/scope contract.

## Floor-Level Execution Preservation
Preserve:
- floor-level execution outcomes where currently observable
- floor-aware execution scope behavior
- same-floor constraint behavior where currently observable
- invalid cross-floor behavior handling

If direct floor-level execution is not fully confirmed, treat it as follow-up validation rather than blocker.

## Whole-House / Household-Level Execution Preservation
Preserve:
- whole-house or household-level execution outcomes where currently evidenced
- household-wide context or summary execution-adjacent outcomes where currently evidenced
- whole-house targeting interaction with hierarchy traversal

If explicit whole-house execution is not fully confirmed, treat it as follow-up validation rather than blocker.

## Decision Ordering Preservation
The household-facing execution ordering that must remain deterministic includes:
- explicit target before inferred target
- room target before broader scope where applicable
- merged/composite target before floor where applicable
- floor target before house-wide fallback where applicable
- policy gating before execution
- unavailable or unsupported target elimination before execution
- safe fallback behavior when target is invalid or unavailable

These are observable decision-ordering outcomes, not implementation algorithms.

## Capability Eligibility Preservation
Execution must remain constrained by capability availability where currently observable.

Capability Projection authority remains external.

Coordinator V2:
- consumes projected capability context
- may not invent capabilities
- must keep unavailable or unsupported capability behavior explainable

## Planning Integration Preservation
Execution hierarchy must integrate with CF5 Planning through:
- experience validation
- room target resolution
- person target resolution where applicable
- capability target resolution
- execution sequence construction
- constraint evaluation
- plan explainability construction

Planning internals may change.

Household-facing hierarchy outcomes must remain.

## Routing Integration Preservation
Execution hierarchy must integrate with CF8 Routing through:
- room-scoped routing
- merged-room routing
- composite-room routing
- floor-scoped routing
- household-scoped routing
- private or person-scoped execution where applicable

Routing internals may change.

Observable scope outcomes must remain.

## Execution Envelope Integration
Execution hierarchy must be represented in CF9 Execution Envelope through references including:
- context_reference
- capability_references
- experience_reference
- execution_plan_reference
- room_target
- scope_target where applicable
- explainability_references
- provenance_references
- envelope_classification

Execution envelope must carry enough references to explain hierarchy behavior.

## Diagnostics and Explainability Expectations
Future implementation must be able to explain:
- why a room target was selected
- why a merged-room target was selected
- why a composite-room target was selected
- why a floor target was selected
- why broader scope was used
- why execution did not proceed
- why a target was unavailable
- why a target was unsupported
- why policy gating applied
- why fallback occurred

## Ownership Matrix
| Capability Family | Authority | Concierge Role | Boundary |
|---|---|---|---|
| Room Vocabulary | HTBW Room Vocabulary governance | consume vocabulary/alias context | no vocabulary ownership transfer |
| Room Truth / Area Truth | Home Assistant area truth + HTBW room governance | consume room truth | no room truth ownership |
| Floor / Zone Truth | Home Assistant floor/zone truth and governed scope semantics | consume floor/zone context | no floor/zone truth ownership |
| Capability Projection | HTBW capability governance | consume projected capability outcomes | no capability ownership |
| Experience Projection | HTBW experience governance | consume experience outcomes | no experience ownership |
| Occupancy / Presence | HTBW occupancy governance | consume occupancy/presence context | no occupancy truth ownership |
| Coordinator V2 Planning | Concierge runtime planning | plan execution hierarchy outcomes | bounded planning role only |
| Coordinator V2 Routing | Concierge runtime routing | route using hierarchy outputs | bounded routing role only |
| External Providers | provider systems | execute underlying actions | provider ownership remains external |

## Execution Hierarchy Capability Matrix
| Capability | Household-Facing Outcome | Current Evidence | Must Preserve | Implementation Preservation Required |
|---|---|---|---|---|
| Room-level execution | Room executes against intended target scope | services, README, tests | YES | NO |
| Merged-room execution | Merged scope participates where supported | merged contract + tests | YES | NO |
| Composite-room execution | Composite scope participates where supported | composite contract + tests | YES | NO |
| Floor-aware execution behavior | Floor-aware constraints/scopes remain meaningful | tests, panel/state | YES | NO |
| Whole-house/household execution-adjacent behavior | household-wide execution/summary scope remains where evidenced | README, summary service | YES | NO |
| Deterministic fallback | Precedence/fallback remains predictable | README + services | YES | NO |
| Policy gating before execute | Disallowed requests blocked before actuation | services/tests | YES | NO |
| Invalid target handling | Invalid scope rejected safely | tests | YES | NO |
| Unavailable target handling | Removed/unavailable members are safely excluded | tests | YES | NO |
| Diagnostics visibility | execution path remains observable | timeline tests | YES | NO |

## Execution Hierarchy Parity Matrix
| Hierarchy Level | Expected Household Outcome | Parity Required | Notes |
|---|---|---|---|
| room | direct room execution remains possible | YES | baseline scope |
| merged room | merged-room execution remains where supported | YES | see Issue #64 contract |
| composite room | composite execution remains where supported | YES | see Issue #65 contract |
| floor | floor-aware behavior remains meaningful where observable | YES | explicit direct execution may need validation |
| zone | zone-scope behavior remains where observable | YES | follow-up if evidence incomplete |
| whole house | whole-house behavior remains where evidenced | YES | explicit direct execution may need validation |
| household | household-wide summary/context-driven outcome remains | YES | informational/coordination scope |

## Decision Ordering Matrix
| Decision Scenario | Expected Outcome | Must Preserve | Notes |
|---|---|---|---|
| explicit room target | direct room target wins | YES | deterministic precedence |
| inferred room target | resolved room target remains deterministic | YES | context-aware path |
| merged-room target | merged target honored where supported | YES | scope-aware behavior |
| composite-room target | composite target honored where supported | YES | scope-aware behavior |
| floor target | floor-aware scope remains meaningful | YES | no cross-floor invalid behavior |
| whole-house fallback | broader fallback remains safe where observable | YES | validate explicit execution separately |
| invalid target | invalid target rejected safely | YES | no unsafe execution |
| unavailable target | unavailable target removed or blocked safely | YES | explainable elimination |
| unsupported capability | unsupported capability blocked safely | YES | no invented fallback |
| policy-gated execution | policy denial occurs before execution | YES | deterministic gating |

## Parity Expectations
Future implementation must verify:
- household can still execute at room level
- household can still execute at merged-room level where currently supported
- household can still execute at composite-room level where currently supported
- household can still benefit from floor-aware behavior
- hierarchy traversal remains deterministic
- invalid targets are safely handled
- unavailable targets are safely handled
- unsupported capabilities are safely handled
- execution planning remains explainable
- routing and execution envelopes can carry hierarchy references

## Non-Rights
Execution hierarchy preservation does NOT require preserving:
- current helper methods
- current service internals
- current storage format
- current API shape
- current entity implementation
- current panel implementation
- current routing internals
- current execution internals

Execution hierarchy preservation DOES require preserving observable household outcomes.

## Follow-Up Validation Items
Non-blocking follow-up observations:
- floor-wide announcement behavior
- explicit floor-level execution
- explicit whole-house execution
- whole-house routing interaction
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
- later Coordinator V2 implementation work touching room, merged-room, composite-room, floor, house-level, or hierarchy traversal execution behavior

## Required Future GitHub Copilot Usage
Before implementation work that may affect execution hierarchy household-facing outcomes, GitHub Copilot must read:
- `docs/governance/coordinator-v2-foundation-summary.md`
- `docs/governance/concierge-v1-outcome-preservation-baseline.md`
- `docs/governance/merged-room-outcome-preservation-contract.md`
- `docs/governance/composite-room-scope-outcome-preservation-contract.md`
- `docs/governance/execution-hierarchy-outcome-preservation-contract.md`
- the relevant CF or E3a issue baseline
- relevant HTBW contracts and models
- the target issue last

GitHub Copilot must ask:

Can the household still achieve the same execution hierarchy outcome?

GitHub Copilot must not ask:

Does the execution hierarchy implementation work the same way internally?

## Readiness Statement
Execution hierarchy outcome preservation contract is READY for downstream E3a and Coordinator V2 implementation consumption.