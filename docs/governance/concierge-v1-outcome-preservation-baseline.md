# Concierge V1 Outcome Preservation Baseline

## Purpose
This document defines the required household-facing outcomes from Concierge V1 that must be preserved during Coordinator V2 migration and future implementation.

This document is outcome-based.

This document is not implementation-based.

## Governing Principle
Preserve household-facing outcomes.

Do not preserve implementation details.

Coordinator V2 may replace internal architecture, code paths, services, data structures, helper functions, and storage mechanisms.

Coordinator V2 must preserve observable household behavior.

The correct preservation question is:

Can the household still achieve the same outcome?

The incorrect preservation question is:

Does the implementation work the same way internally?

## Authority Relationship
- ADR-013 governs preservation philosophy.
- Issue #63 is the approved review record.
- This document is the implementation-time preservation baseline.
- Future E3a issues consume this document.
- This document does not replace HTBW ADRs, contracts, or models.

Authority chain:

ADRs
  -> Contracts
  -> Models
  -> Issue #63 review record
  -> This preservation baseline
  -> Implementation issues

## Preservation Rules
- Observable household outcomes must remain.
- Internal implementation may change.
- Backward compatibility is not required unless separately specified.
- API compatibility is not required unless separately specified.
- Data model compatibility is not required unless separately specified.
- Code reuse is not required.
- Compatibility shims are not required.
- Migration adapters are not required unless a later issue explicitly adds them.
- Provider ownership must remain external.
- Concierge must not move HTBW ownership boundaries into Concierge.
- Concierge must not redefine Room Vocabulary, Occupancy, Capability Projection, Experience, Identity, or Provenance authority.

## Capability Inventory Definition
A Concierge V1 capability is any observable household-facing behavior currently provided by Concierge V1.

Capabilities are defined by outcomes.

Capabilities are not defined by:
- classes
- methods
- services
- internal storage
- helper functions
- entity implementation
- API shape

## Inventory Review Method
Evidence sources reviewed:
- `custom_components/concierge/services.py`
- `custom_components/concierge/coordinator.py`
- `custom_components/concierge/panel.py`
- `tests/test_services.py`
- `README.md`
- `docs/development/architecture-guardrails.md`
- `docs/development/implementation-checklist.md`
- Issue #63 inventory comment

The inventory below is normalized for implementation use.

Issue #63 remains the evidence and approval record.

## Outcome Categories
- Room Execution
- Room Targeting
- Composite Scope
- Merged Room Scope
- Floor Scope
- Whole House Scope
- Execution Hierarchy
- Room Restoration
- Context Consumption
- Routing
- Coordination
- Diagnostics / Timeline Visibility

## Required Household-Facing Outcomes

### Room Execution Outcomes
1. Room-scoped execution from target request
- Household-facing behavior: room-targeted requests execute deterministically.
- Preservation requirement: preserve outcome.
- Authority boundary: Concierge orchestrates, provider executes.
- Implementation preservation required: NO.

2. Deterministic execution hierarchy fallback
- Household-facing behavior: predictable scene/script/entity fallback behavior.
- Preservation requirement: preserve outcome.
- Authority boundary: Concierge orchestration only.
- Implementation preservation required: NO.

3. Direct explicit execution
- Household-facing behavior: explicit entity/service action can be executed.
- Preservation requirement: preserve outcome.
- Authority boundary: provider execution remains external.
- Implementation preservation required: NO.

For detailed execution hierarchy parity expectations, see:

- `docs/governance/execution-hierarchy-outcome-preservation-contract.md`

### Room Targeting Outcomes
1. Explicit room targeting
- Household-facing behavior: room can be explicitly targeted.
- Preservation requirement: preserve outcome.
- Authority boundary: room truth external; Concierge consumes it.
- Implementation preservation required: NO.

2. Configured room alias target resolution
- Household-facing behavior: configured room aliases resolve to expected outcomes.
- Preservation requirement: preserve outcome.
- Authority boundary: Room Vocabulary authority remains external.
- Implementation preservation required: NO.

3. Linked person-to-room context resolution
- Household-facing behavior: person-linked context can influence room targeting.
- Preservation requirement: preserve outcome.
- Authority boundary: identity and person context remain external authorities.
- Implementation preservation required: NO.

4. Contextual room targeting where currently observable
- Household-facing behavior: context-aware routing to relevant room scope remains available.
- Preservation requirement: preserve outcome.
- Authority boundary: Concierge consumes context.
- Implementation preservation required: NO.

### Merged Room Outcomes
1. Merged-room creation
- Household-facing behavior: users can create merged room zones.
- Preservation requirement: preserve outcome.
- Authority boundary: Concierge scope orchestration only.
- Implementation preservation required: NO.

2. Merged-room rename and membership edit
- Household-facing behavior: users can rename/edit merged room members.
- Preservation requirement: preserve outcome.
- Authority boundary: room truth remains external.
- Implementation preservation required: NO.

3. Merged-room dismantle
- Household-facing behavior: merged room can be removed cleanly.
- Preservation requirement: preserve outcome.
- Authority boundary: Concierge scope management only.
- Implementation preservation required: NO.

4. Same-floor membership enforcement where applicable
- Household-facing behavior: cross-floor merged membership is rejected.
- Preservation requirement: preserve outcome.
- Authority boundary: floor/area truth remains external.
- Implementation preservation required: NO.

For detailed merged-room parity expectations, see:

- `docs/governance/merged-room-outcome-preservation-contract.md`

### Composite Room Outcomes
1. Composite scoped execution context
- Household-facing behavior: composite zones act as valid execution scopes.
- Preservation requirement: preserve outcome.
- Authority boundary: Concierge orchestration only.
- Implementation preservation required: NO.

2. Composite membership validation and synchronization
- Household-facing behavior: invalid members are pruned/synced.
- Preservation requirement: preserve outcome.
- Authority boundary: area/floor truth remains external.
- Implementation preservation required: NO.

3. Composite entity selection pruning
- Household-facing behavior: selected entities remain constrained to valid composite members.
- Preservation requirement: preserve outcome.
- Authority boundary: provider/entity ownership remains external.
- Implementation preservation required: NO.

4. Composite scope preservation
- Household-facing behavior: configured composite scopes remain operationally meaningful.
- Preservation requirement: preserve outcome.
- Authority boundary: Concierge scope representation only.
- Implementation preservation required: NO.

For detailed composite-room, floor-scope, zone-scope, and hierarchy traversal parity expectations, see:

- `docs/governance/composite-room-scope-outcome-preservation-contract.md`

### Floor Scope Outcomes
1. Same-floor composite enforcement
- Household-facing behavior: composite scope respects floor boundaries.
- Preservation requirement: preserve outcome.
- Authority boundary: floor truth external.
- Implementation preservation required: NO.

2. Floor identity awareness in merged/composite state
- Household-facing behavior: floor-aware context is preserved for merged/composite zones.
- Preservation requirement: preserve outcome.
- Authority boundary: room/floor authority external.
- Implementation preservation required: NO.

3. Floor-aware scope behavior
- Household-facing behavior: floor scope remains a meaningful targeting boundary where currently observable.
- Preservation requirement: preserve outcome.
- Authority boundary: Concierge consumes floor context.
- Implementation preservation required: NO.

For detailed composite-room, floor-scope, zone-scope, and hierarchy traversal parity expectations, see:

- `docs/governance/composite-room-scope-outcome-preservation-contract.md`

### Whole House Outcomes
1. Household-wide summary synthesis
- Household-facing behavior: summary combines available context/signals.
- Preservation requirement: preserve outcome.
- Authority boundary: context source ownership external.
- Implementation preservation required: NO.

2. Household-wide signal/context surfaces
- Household-facing behavior: household-facing context and signal readouts remain available.
- Preservation requirement: preserve outcome.
- Authority boundary: source truth external.
- Implementation preservation required: NO.

3. Whole-house or household-wide targeting where currently evidenced
- Household-facing behavior: household-wide targeting behavior remains where currently provided.
- Preservation requirement: preserve outcome.
- Authority boundary: provider ownership external.
- Implementation preservation required: NO.

If explicit whole-house execution is not fully confirmed, treat it as a follow-up validation item, not a blocker.

For detailed composite-room, floor-scope, zone-scope, and hierarchy traversal parity expectations, see:

- `docs/governance/composite-room-scope-outcome-preservation-contract.md`

For detailed global context, home status, occupancy reference, shared context, and environmental context parity expectations, see:

- `docs/governance/global-context-outcome-preservation-contract.md`

### Execution Hierarchy Outcomes
1. Deterministic target precedence and routing path
- Household-facing behavior: predictable precedence and routing outcome.
- Preservation requirement: preserve outcome.
- Authority boundary: orchestration only.
- Implementation preservation required: NO.

2. Policy gating before execution
- Household-facing behavior: policy-denied requests are blocked before actuation.
- Preservation requirement: preserve outcome.
- Authority boundary: policy authority external.
- Implementation preservation required: NO.

3. Safe fallback behavior where currently observable
- Household-facing behavior: fallback remains safe and deterministic.
- Preservation requirement: preserve outcome.
- Authority boundary: provider execution external.
- Implementation preservation required: NO.

For detailed execution hierarchy parity expectations, see:

- `docs/governance/execution-hierarchy-outcome-preservation-contract.md`

For detailed composite-room, floor-scope, zone-scope, and hierarchy traversal parity expectations, see:

- `docs/governance/composite-room-scope-outcome-preservation-contract.md`

### Room Restoration Outcomes
- No explicit standalone room restoration service is currently confirmed.
- Restoration-adjacent safety outcomes must be preserved.
- Stale or invalid room/composite state must not leak into future behavior.

If explicit restoration command behavior is not yet fully confirmed, treat as follow-up validation, not blocker.

### Global Context Consumption Outcomes
1. Context-informed household summary
- Household-facing behavior: context impacts summary output.
- Preservation requirement: preserve outcome.
- Authority boundary: context truth external.
- Implementation preservation required: NO.

2. Occupancy/presence-aware policy surfaces
- Household-facing behavior: occupancy and presence can constrain outcomes.
- Preservation requirement: preserve outcome.
- Authority boundary: occupancy/presence truth external.
- Implementation preservation required: NO.

3. Home-state/context signal availability
- Household-facing behavior: signal/context visibility remains available.
- Preservation requirement: preserve outcome.
- Authority boundary: source authority external.
- Implementation preservation required: NO.

4. Platform-state awareness where currently observable
- Household-facing behavior: platform-state-informed behavior remains available where currently provided.
- Preservation requirement: preserve outcome.
- Authority boundary: platform/provider truth external.
- Implementation preservation required: NO.

For detailed global context, home status, occupancy reference, shared context, and environmental context parity expectations, see:

- `docs/governance/global-context-outcome-preservation-contract.md`

### Routing and Coordination Outcomes
1. Person-scoped mobile push routing
- Household-facing behavior: person-scoped push routing remains available.
- Preservation requirement: preserve outcome.
- Authority boundary: notification provider ownership external.
- Implementation preservation required: NO.

2. Household signal/context coordination surfaces
- Household-facing behavior: coordinated household-facing status visibility remains available.
- Preservation requirement: preserve outcome.
- Authority boundary: source domains external.
- Implementation preservation required: NO.

3. Routing behavior that respects room/person context
- Household-facing behavior: routing remains room/person aware where currently observable.
- Preservation requirement: preserve outcome.
- Authority boundary: identity/room authorities external.
- Implementation preservation required: NO.

4. Policy-gated routing where currently observable
- Household-facing behavior: policy gating remains enforced.
- Preservation requirement: preserve outcome.
- Authority boundary: policy authority external.
- Implementation preservation required: NO.

### Diagnostics and Timeline Outcomes
1. Activity timeline visibility
- Household-facing behavior: timeline of outcomes remains available.
- Preservation requirement: preserve outcome.
- Authority boundary: diagnostics artifact, not source truth.
- Implementation preservation required: NO.

2. Operator-visible outcome history
- Household-facing behavior: operational review of prior outcomes remains possible.
- Preservation requirement: preserve outcome.
- Authority boundary: evidence surface only.
- Implementation preservation required: NO.

3. Diagnostic visibility required for preservation review
- Household-facing behavior: enough diagnostics remain to validate preserved outcomes.
- Preservation requirement: preserve outcome.
- Authority boundary: diagnostics ownership stays in Concierge observability surface.
- Implementation preservation required: NO.

## Capability Matrix
| Capability | Category | Household-Facing Outcome | Authority Boundary | Must Preserve |
|---|---|---|---|---|
| Room-scoped execute | Room Execution | Room-targeted execution remains available | Concierge orchestration + external providers | YES |
| Direct entity execute | Room Execution | Explicit entity/service execution remains available | External provider execution ownership | YES |
| Deterministic execute hierarchy | Execution Hierarchy | Predictable precedence/fallback remains | Concierge orchestration only | YES |
| Composite creation | Composite Scope | Composite/merged scope creation remains | Concierge scope layer | YES |
| Composite rename/membership edit | Composite Scope | Composite edit behavior remains | Room/floor truth external | YES |
| Composite dismantle | Composite Scope | Composite removal behavior remains | Concierge scope layer | YES |
| Same-floor composite enforcement | Floor Scope | Cross-floor membership blocked | Floor truth external | YES |
| Composite sync pruning | Composite Scope | Invalid members/entities pruned | Entity/provider truth external | YES |
| Explicit room targeting | Room Targeting | Explicit room targeting remains | Room truth external | YES |
| Alias-based target resolution | Room Targeting | Configured aliases resolve predictably | Room Vocabulary authority external | YES |
| Person-linked room resolution | Room Targeting | Person-linked contextual room resolution remains | Identity authority external | YES |
| Household summary aggregation | Whole House Scope | Household summary synthesis remains | Context/signal source authorities external | YES |
| Global context readout | Context Consumption | Global context payload visibility remains | Context authority external | YES |
| Signal readout | Context Consumption | Signal visibility remains | Signal/source authority external | YES |
| Person-scoped mobile push routing | Routing | Person-targeted push routing remains | Notification provider ownership external | YES |
| Minor policy gating | Execution Hierarchy | Policy-denied requests are blocked | Policy authority external | YES |
| Activity timeline visibility | Diagnostics / Timeline Visibility | Timeline and outcome history remain available | Diagnostics evidence surface | YES |

For the authoritative V1-to-V2 parity mapping across contracts, models, Coordinator Foundation areas, and future epics, see:

- `docs/governance/v1-to-v2-capability-parity-matrix.md`

## Preservation Matrix
| Capability | Outcome Preservation Required | Implementation Preservation Required |
|---|---|---|
| Room-scoped execute | YES | NO |
| Direct entity execute | YES | NO |
| Deterministic execute hierarchy | YES | NO |
| Composite creation/edit/dismantle | YES | NO |
| Same-floor composite enforcement | YES | NO |
| Composite sync pruning | YES | NO |
| Explicit room targeting | YES | NO |
| Alias-based target resolution | YES | NO |
| Person-linked room resolution | YES | NO |
| Household summary aggregation | YES | NO |
| Global context readout | YES | NO |
| Signal readout | YES | NO |
| Person-scoped mobile push routing | YES | NO |
| Minor policy gating | YES | NO |
| Activity timeline visibility | YES | NO |

For the authoritative preservation regression checklist, see:

- `docs/governance/v1-outcome-regression-checklist.md`

## Ownership Matrix
| Capability Family | Owner / Authority | Concierge Role | Boundary |
|---|---|---|---|
| Room Vocabulary | HTBW Room Vocabulary governance | consume room language context | no vocabulary ownership transfer |
| Occupancy / Presence | HTBW Occupancy governance | consume occupancy/presence context | no occupancy truth ownership |
| Capability Projection | HTBW Capability governance | consume capability outcomes | no capability ownership transfer |
| Experience Projection | HTBW Experience governance | consume experience outcomes | no experience ownership transfer |
| Voice Identity | Voice Identity authority | consume identity context | no identity authority transfer |
| Asset Intelligence | Asset Intelligence authority | consume significance/context where enabled | no asset reasoning ownership transfer |
| External Providers | provider systems | delegate execution/delivery | provider ownership remains external |
| Concierge Orchestration | Concierge runtime | orchestrate outcomes | bounded orchestration role only |
| Diagnostics / Timeline | Concierge diagnostics surface | expose evidence of outcomes | evidence surface, not source truth |

## Follow-Up Validation Items
- explicit whole-house execution surface
- explicit restoration command surface
- floor-wide announcement behavior

For the authoritative V1-to-V2 parity mapping across contracts, models, Coordinator Foundation areas, and future epics, see:

- `docs/governance/v1-to-v2-capability-parity-matrix.md`

These do not block the preservation baseline.

They must be resolved during later E3a review issues before implementation changes intentionally alter those areas.

## Downstream Use
This document must be consumed by:
- E3a parity planning
- E3a routing reviews
- E3a restoration reviews
- E3a execution reviews
- E3a room targeting reviews
- E4 Room Vocabulary Consumption
- E5 Capability Projection Consumption
- E6 Experience Consumption
- later Coordinator V2 implementation work that may affect preserved outcomes

For the authoritative preservation regression checklist, see:

- `docs/governance/v1-outcome-regression-checklist.md`

## Required Future GitHub Copilot Usage
Before implementation work that may affect Concierge V1 household-facing outcomes, GitHub Copilot must read:
- `docs/governance/coordinator-v2-foundation-summary.md`
- `docs/governance/concierge-v1-outcome-preservation-baseline.md`
- the relevant CF or E3a issue baseline
- relevant HTBW contracts and models
- the target issue last

GitHub Copilot must ask:

Can the household still achieve the same outcome?

GitHub Copilot must not ask:

Does the implementation work the same way internally?

## Implementation Guardrails
Implementation must not:
- remove a preserved outcome
- replace a preserved household behavior without parity
- preserve implementation merely for compatibility
- move HTBW ownership into Concierge
- redefine room vocabulary authority
- redefine occupancy truth
- redefine provider ownership
- redefine identity authority
- remove diagnostics needed to verify preservation
- remove explainability needed to understand changed behavior

## Readiness Statement
This document is the authoritative E3a preservation contract for implementation work.

Concierge V1 outcome preservation baseline is READY for use by downstream E3a planning and implementation.

For the final E3a preservation readiness decision, see:

- `docs/governance/v1-preservation-readiness-review.md`