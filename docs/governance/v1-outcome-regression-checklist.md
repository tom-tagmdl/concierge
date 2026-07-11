# V1 Outcome Regression Checklist

## Purpose
This document is the reusable preservation regression checklist for Concierge V1 household-facing outcomes.

It is consumed by E3a and all later implementation and testing efforts.

## Authority Relationship
- ADR-013 governs preservation philosophy.
- Issue #63 defines the broad preservation inventory.
- Issues #64 through #67 define domain preservation contracts.
- Issue #68 defines the V1-to-V2 parity matrix.
- Issue #69 defines the regression checklist.
- This document is the implementation and test-time preservation checklist.
- This document does not replace HTBW ADRs, contracts, or models.

Authority chain:

ADRs
  -> Contracts
  -> Models
  -> E3 Coordinator Foundation
  -> E3a Preservation Contracts
  -> V1-to-V2 Parity Matrix
  -> Issue #69 Regression Checklist Review
  -> This regression checklist
  -> Implementation and testing

## Governing Principle
Preserve household-facing outcomes.

Do not preserve implementation details.

The correct regression question is:

Can the household still achieve the same V1 outcome after the V2 change?

The incorrect regression question is:

Does the V1 implementation work the same way internally?

## Checklist Use Instructions
Use this checklist before closing any issue that could affect preserved V1 household outcomes.

Use this checklist during:
- implementation planning
- PR review
- manual testing
- automated test planning
- regression review
- readiness review

Checklist result values:
- PASS
- FAIL
- NOT APPLICABLE
- FOLLOW-UP REQUIRED

No implementation issue may be marked complete if an applicable preservation checklist item fails.

## Regression Checklist Categories
- Merged Room
- Composite Room
- Room Execution
- Execution Hierarchy
- Room Targeting
- Context Resolution
- Global Context
- Diagnostics and Explainability
- Ownership Boundaries
- Future Copilot Grounding

## Merged Room Regression Checklist
| Check | Expected Outcome | Evidence Source | Result |
|---|---|---|---|
| merged-room creation still works where currently supported | household can still create merged-room scope | merged-room preservation contract, tests/test_services.py | PASS/FAIL/NA/FOLLOW-UP |
| merged-room rename or membership edit still works where currently supported | household can still edit merged-room membership | merged-room preservation contract, tests/test_services.py | PASS/FAIL/NA/FOLLOW-UP |
| merged-room dismantle still works where currently supported | household can still remove merged-room scope | merged-room preservation contract, tests/test_services.py | PASS/FAIL/NA/FOLLOW-UP |
| same-floor enforcement still occurs where currently observable | invalid cross-floor membership is rejected | merged-room preservation contract, tests/test_services.py | PASS/FAIL/NA/FOLLOW-UP |
| merged-room target resolution remains deterministic | merged-room targeting remains stable and explainable | merged-room preservation contract | PASS/FAIL/NA/FOLLOW-UP |
| merged-room routing scope remains consumable | routing can still use merged-room scope | merged-room preservation contract, CF8 | PASS/FAIL/NA/FOLLOW-UP |
| merged-room execution scope remains available where currently supported | merged-room scope still acts as meaningful execution scope | merged-room preservation contract, CF5 | PASS/FAIL/NA/FOLLOW-UP |
| merged-room capability discovery/filtering remains scope-aware | capability scope remains safe and member-aware | merged-room preservation contract, CF3 | PASS/FAIL/NA/FOLLOW-UP |
| merged-room context remains visible to Coordinator V2 | merged scope remains a valid context grouping | merged-room preservation contract, CF2 | PASS/FAIL/NA/FOLLOW-UP |
| merged-room diagnostics/explainability can explain selected/rejected scope | why/why-not remains available | merged-room preservation contract, CF6/CF7 | PASS/FAIL/NA/FOLLOW-UP |

## Composite Room Regression Checklist
| Check | Expected Outcome | Evidence Source | Result |
|---|---|---|---|
| composite scope creation or maintenance remains available where currently supported | household can still create and maintain composite scope | composite-room preservation contract, tests/test_services.py | PASS/FAIL/NA/FOLLOW-UP |
| composite membership validation remains safe | invalid grouping remains rejected or constrained safely | composite-room preservation contract, tests/test_services.py | PASS/FAIL/NA/FOLLOW-UP |
| composite membership synchronization remains safe | stale/invalid members remain pruned safely | composite-room preservation contract, tests/test_services.py | PASS/FAIL/NA/FOLLOW-UP |
| composite entity selection pruning remains safe | removed members do not leak stale selected entities | composite-room preservation contract, tests/test_services.py | PASS/FAIL/NA/FOLLOW-UP |
| composite execution scope remains available where currently supported | composite scope remains meaningful for execution | composite-room preservation contract | PASS/FAIL/NA/FOLLOW-UP |
| floor-aware scope behavior remains preserved | floor context remains meaningful where observable | composite-room preservation contract | PASS/FAIL/NA/FOLLOW-UP |
| same-floor composite enforcement remains preserved | cross-floor composite invalidation still occurs | composite-room preservation contract | PASS/FAIL/NA/FOLLOW-UP |
| scope target resolution remains deterministic | composite/floor/household scope targeting remains stable | composite-room preservation contract | PASS/FAIL/NA/FOLLOW-UP |
| scope capability visibility remains preserved | scope capability discovery stays safe and discoverable | composite-room preservation contract | PASS/FAIL/NA/FOLLOW-UP |
| hierarchy traversal remains deterministic | scope precedence remains stable | composite-room preservation contract, execution hierarchy contract | PASS/FAIL/NA/FOLLOW-UP |
| diagnostics can explain composite/scope decisions | scope choice remains traceable | composite-room preservation contract, CF6/CF7 | PASS/FAIL/NA/FOLLOW-UP |

## Room Execution Regression Checklist
| Check | Expected Outcome | Evidence Source | Result |
|---|---|---|---|
| room-scoped execution still produces observable household outcome | room-targeted actuation still works | preservation baseline, tests/test_services.py | PASS/FAIL/NA/FOLLOW-UP |
| direct entity execution still produces observable household outcome | explicit direct execution still works | preservation baseline, tests/test_services.py | PASS/FAIL/NA/FOLLOW-UP |
| execution remains constrained by capability eligibility | unsupported/unavailable execution is not silently allowed | execution hierarchy contract, CF3/CF5 | PASS/FAIL/NA/FOLLOW-UP |
| invalid room targets are safely handled | invalid target is blocked or constrained safely | execution hierarchy contract | PASS/FAIL/NA/FOLLOW-UP |
| unavailable targets are safely handled | unavailable targets are excluded safely | execution hierarchy contract | PASS/FAIL/NA/FOLLOW-UP |
| unsupported capabilities are safely handled | unsupported capabilities do not misfire | execution hierarchy contract | PASS/FAIL/NA/FOLLOW-UP |
| execution diagnostics capture decision outcome | timeline/diagnostics show execution outcome | CF7, preservation baseline | PASS/FAIL/NA/FOLLOW-UP |

## Execution Hierarchy Regression Checklist
| Check | Expected Outcome | Evidence Source | Result |
|---|---|---|---|
| explicit room target takes precedence where applicable | direct room target still wins | execution hierarchy contract | PASS/FAIL/NA/FOLLOW-UP |
| inferred room target remains deterministic | inferred targeting remains stable | execution hierarchy contract | PASS/FAIL/NA/FOLLOW-UP |
| merged-room target behavior remains deterministic | merged target precedence remains stable | execution hierarchy contract | PASS/FAIL/NA/FOLLOW-UP |
| composite-room target behavior remains deterministic | composite target precedence remains stable | execution hierarchy contract | PASS/FAIL/NA/FOLLOW-UP |
| floor target behavior remains deterministic where currently supported | floor-aware hierarchy remains stable | execution hierarchy contract | PASS/FAIL/NA/FOLLOW-UP |
| whole-house fallback behavior remains documented where currently supported | broader fallback remains safe where evidenced | execution hierarchy contract | PASS/FAIL/NA/FOLLOW-UP |
| policy gating occurs before execution | unsafe/disallowed requests are blocked early | execution hierarchy contract | PASS/FAIL/NA/FOLLOW-UP |
| unavailable targets are eliminated before execution | stale or unavailable targets do not proceed | execution hierarchy contract | PASS/FAIL/NA/FOLLOW-UP |
| unsupported capabilities are eliminated before execution | unsupported capabilities do not proceed | execution hierarchy contract | PASS/FAIL/NA/FOLLOW-UP |
| hierarchy fallback remains explainable | why fallback happened remains available | execution hierarchy contract, CF6 | PASS/FAIL/NA/FOLLOW-UP |

## Room Targeting Regression Checklist
| Check | Expected Outcome | Evidence Source | Result |
|---|---|---|---|
| explicit room targeting remains supported | explicit room targeting still works | preservation baseline, parity matrix | PASS/FAIL/NA/FOLLOW-UP |
| alias-based target resolution remains deterministic | aliases still resolve predictably | preservation baseline, parity matrix | PASS/FAIL/NA/FOLLOW-UP |
| person-linked room resolution remains supported where currently observable | person-linked room resolution remains available | preservation baseline, parity matrix | PASS/FAIL/NA/FOLLOW-UP |
| contextual room targeting remains supported where currently observable | contextual room targeting remains available | preservation baseline, parity matrix | PASS/FAIL/NA/FOLLOW-UP |
| room vocabulary authority remains external | Concierge does not assume vocabulary ownership | ownership sections in contracts/baselines | PASS/FAIL/NA/FOLLOW-UP |
| room truth remains external | Concierge does not assume room truth ownership | ownership sections in contracts/baselines | PASS/FAIL/NA/FOLLOW-UP |
| room targeting remains explainable | why room was selected/rejected remains available | CF6, room preservation artifacts | PASS/FAIL/NA/FOLLOW-UP |

## Context Resolution Regression Checklist
| Check | Expected Outcome | Evidence Source | Result |
|---|---|---|---|
| context assembly remains deterministic | context ordering remains stable | CF2, foundation summary | PASS/FAIL/NA/FOLLOW-UP |
| global context remains consumable | shared/global context still reachable | global context contract | PASS/FAIL/NA/FOLLOW-UP |
| shared context remains available where currently supported | shared context outcomes remain available | global context contract | PASS/FAIL/NA/FOLLOW-UP |
| home status awareness remains available where currently evidenced | household still sees home status awareness | global context contract | PASS/FAIL/NA/FOLLOW-UP |
| occupancy references remain consumable | occupancy remains input to outcomes where observable | global context contract, occupancy contract | PASS/FAIL/NA/FOLLOW-UP |
| presence references remain consumable | presence remains input where observable | global context contract | PASS/FAIL/NA/FOLLOW-UP |
| environmental context remains available where currently evidenced | environment/weather/news awareness remains available | global context contract | PASS/FAIL/NA/FOLLOW-UP |
| platform-state awareness remains available where currently evidenced | platform-state awareness remains visible | global context contract | PASS/FAIL/NA/FOLLOW-UP |
| signal context remains visible where currently evidenced | signal readouts remain available | global context contract | PASS/FAIL/NA/FOLLOW-UP |

## Global Context Regression Checklist
| Check | Expected Outcome | Evidence Source | Result |
|---|---|---|---|
| household-wide context readout remains available | context payload readout still works | global context contract, services.py | PASS/FAIL/NA/FOLLOW-UP |
| context-informed household summary remains available | summary still aggregates context and signals | global context contract, services.py, README | PASS/FAIL/NA/FOLLOW-UP |
| signal readout remains available | signal visibility remains | global context contract, README | PASS/FAIL/NA/FOLLOW-UP |
| diagnostics can explain context participation | context participation remains traceable | global context contract, CF7 | PASS/FAIL/NA/FOLLOW-UP |
| future briefing/productivity/status work can consume context without redefining authority | context remains reusable downstream | global context contract, parity matrix | PASS/FAIL/NA/FOLLOW-UP |
| provider ownership remains external | no provider authority moved into Concierge | global context contract | PASS/FAIL/NA/FOLLOW-UP |

## Diagnostics and Explainability Regression Checklist
| Check | Expected Outcome | Evidence Source | Result |
|---|---|---|---|
| capability decisions remain explainable | capability why/why-not remains available | CF6, CF7 | PASS/FAIL/NA/FOLLOW-UP |
| experience decisions remain explainable | experience why/why-not remains available | CF6, CF7 | PASS/FAIL/NA/FOLLOW-UP |
| room selection remains explainable | room choice remains traceable | CF6, room targeting artifacts | PASS/FAIL/NA/FOLLOW-UP |
| merged-room selection remains explainable | merged-room choice remains traceable | merged-room contract, CF6 | PASS/FAIL/NA/FOLLOW-UP |
| composite-room selection remains explainable | composite-room choice remains traceable | composite-room contract, CF6 | PASS/FAIL/NA/FOLLOW-UP |
| execution hierarchy decisions remain explainable | precedence/fallback remains traceable | execution hierarchy contract, CF6 | PASS/FAIL/NA/FOLLOW-UP |
| context inclusion/exclusion remains explainable | global context why/why-not remains visible | global context contract, CF6 | PASS/FAIL/NA/FOLLOW-UP |
| why-not explanations exist where relevant | non-selection remains explainable | CF6 | PASS/FAIL/NA/FOLLOW-UP |
| diagnostics trace preserved outcome decisions | diagnostics still reflect preserved outcomes | CF7 | PASS/FAIL/NA/FOLLOW-UP |

## Ownership Boundary Regression Checklist
| Check | Expected Outcome | Evidence Source | Result |
|---|---|---|---|
| Concierge does not assume room vocabulary authority | no vocabulary ownership drift | contracts, preservation artifacts | PASS/FAIL/NA/FOLLOW-UP |
| Concierge does not assume room truth authority | no room truth ownership drift | contracts, preservation artifacts | PASS/FAIL/NA/FOLLOW-UP |
| Concierge does not assume floor / zone truth authority | no floor/zone truth ownership drift | contracts, preservation artifacts | PASS/FAIL/NA/FOLLOW-UP |
| Concierge does not assume occupancy truth authority | no occupancy truth ownership drift | occupancy contract/artifacts | PASS/FAIL/NA/FOLLOW-UP |
| Concierge does not assume identity authority | no identity authority drift | foundation summary | PASS/FAIL/NA/FOLLOW-UP |
| Concierge does not assume capability projection authority | no capability authority drift | capability contract/artifacts | PASS/FAIL/NA/FOLLOW-UP |
| Concierge does not assume experience projection authority | no experience authority drift | experience contract/artifacts | PASS/FAIL/NA/FOLLOW-UP |
| Concierge does not assume memory authority | no memory authority drift | memory contract/artifacts | PASS/FAIL/NA/FOLLOW-UP |
| Concierge does not assume provenance authority | no provenance authority drift | provenance contract/artifacts | PASS/FAIL/NA/FOLLOW-UP |
| Concierge does not assume provider ownership | no provider ownership drift | preservation artifacts | PASS/FAIL/NA/FOLLOW-UP |

## V1-to-V2 Mapping Regression Checklist
| Check | Expected Outcome | Evidence Source | Result |
|---|---|---|---|
| affected outcome exists in `v1-to-v2-capability-parity-matrix.md` | no missing mapping | parity matrix | PASS/FAIL/NA/FOLLOW-UP |
| affected outcome is not orphaned | every affected outcome is fully mapped | parity matrix orphan review | PASS/FAIL/NA/FOLLOW-UP |
| affected outcome maps to a contract | contract mapping exists | parity matrix | PASS/FAIL/NA/FOLLOW-UP |
| affected outcome maps to a model | model mapping exists | parity matrix | PASS/FAIL/NA/FOLLOW-UP |
| affected outcome maps to a Coordinator Foundation area | CF area mapping exists | parity matrix | PASS/FAIL/NA/FOLLOW-UP |
| affected outcome maps to a future epic / consumer | downstream mapping exists | parity matrix | PASS/FAIL/NA/FOLLOW-UP |
| `MAPPED WITH FOLLOW-UP` items are not silently treated as fully closed | follow-up remains visible | parity matrix | PASS/FAIL/NA/FOLLOW-UP |

## Future Copilot Grounding Checklist
| Check | Expected Outcome | Evidence Source | Result |
|---|---|---|---|
| Coordinator V2 foundation summary read | grounding confirmed | implementation notes / review record | PASS/FAIL/NA/FOLLOW-UP |
| V1 preservation baseline read | preservation baseline confirmed | implementation notes / review record | PASS/FAIL/NA/FOLLOW-UP |
| domain preservation contract read | affected domain contract confirmed | implementation notes / review record | PASS/FAIL/NA/FOLLOW-UP |
| V1-to-V2 parity matrix read | parity mapping confirmed | implementation notes / review record | PASS/FAIL/NA/FOLLOW-UP |
| regression checklist read | regression review confirmed | implementation notes / review record | PASS/FAIL/NA/FOLLOW-UP |
| relevant HTBW contracts/models read | authority grounding confirmed | implementation notes / review record | PASS/FAIL/NA/FOLLOW-UP |
| target issue read last | issue-order grounding confirmed | implementation notes / review record | PASS/FAIL/NA/FOLLOW-UP |

## Regression Result Rules
- PASS means preserved outcome is validated.
- FAIL means implementation may not close.
- NOT APPLICABLE must include rationale.
- FOLLOW-UP REQUIRED must include linked follow-up issue or documented reason.

Blocking rules:
- Any applicable FAIL blocks closure.
- Any ownership drift blocks closure.
- Any orphaned affected outcome blocks closure.
- Missing diagnostics or explainability for affected outcome blocks closure unless explicitly deferred by governance.

## Checklist Completion Template
## V1 Outcome Regression Checklist Result

Affected preserved outcomes:

- ...

Checklist sections applied:

- ...

Results:

- PASS:
- FAIL:
- NOT APPLICABLE:
- FOLLOW-UP REQUIRED:

Ownership drift found:

YES / NO

Orphan outcome found:

YES / NO

Readiness:

READY / NOT READY

## Follow-Up Validation Items
Inherited non-blocking follow-ups:
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

These are not blockers for checklist creation.

They must be checked when affected implementation touches the relevant area.

## Downstream Use
This document must be consumed by:
- E3a remaining issues
- E4 Room Vocabulary Consumption
- E5 Capability Projection Consumption
- E6 Experience Consumption
- E7 Continuity and Affinity
- E8 Restoration
- E8a Occupancy and Presence
- E9 Messaging and Notification Discipline
- E10 Household Memory and Explainability
- E13 Productivity Experiences
- E14 Household Coordination
- testing and readiness review work

## Required Future GitHub Copilot Usage
Before implementation work that may affect any preserved Concierge V1 household-facing outcome, GitHub Copilot must read:
- `docs/governance/coordinator-v2-foundation-summary.md`
- `docs/governance/concierge-v1-outcome-preservation-baseline.md`
- `docs/governance/v1-to-v2-capability-parity-matrix.md`
- `docs/governance/v1-outcome-regression-checklist.md`
- relevant domain preservation contracts
- relevant HTBW contracts and models
- the target issue last

GitHub Copilot must ask:

Can the household still achieve the same V1 outcome after this change?

GitHub Copilot must not ask:

Does the V1 implementation work the same way internally?

## Readiness Statement
V1 outcome regression checklist is READY for downstream E3a, Coordinator V2 implementation, and testing consumption.