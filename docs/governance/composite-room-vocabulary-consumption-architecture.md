# Composite Room Vocabulary Consumption Architecture

## Purpose
This document defines the authoritative Composite Room Vocabulary Consumption architecture.

This artifact defines:
- composite-room vocabulary participation
- composite-room targeting
- zone participation
- floor participation
- hierarchy traversal
- scope expansion
- explainability
- diagnostics

This artifact does NOT define composite-room governance.

## Authority Relationship
Composite scope governance authority remains external through:
- Room Vocabulary Registry Contract
- Room Vocabulary Registry Model
- Composite Room and Scope Outcome Preservation Contract

Coordinator authority is consumer only.

## Architectural Principle
Composite rooms are vocabulary entities.

Composite rooms are scope targets.

Composite rooms are not a separate vocabulary system.

Hierarchy traversal is scope behavior.

Hierarchy traversal is not a governance authority.

## Composite Scope Consumption Overview
Coordinator consumes governed definitions for:
- composite-room consumption
- zone consumption
- floor consumption
- hierarchy consumption
- scope consumption

## Composite Scope Resolution Participation
Composite scopes participate in:
- vocabulary lookup
- alias lookup
- runtime resolution
- room-context-aware resolution

Participation remains within the same runtime vocabulary resolution pipeline as room, merged room, floor, and household scopes.

## Hierarchy Traversal Architecture
Vocabulary Resolution
  -> Target Resolution
  -> Composite Scope Resolution
  -> Hierarchy Traversal
  -> Scope Expansion
  -> Planning
  -> Routing
  -> Execution

Hierarchy traversal and scope expansion occur after deterministic resolution.

## Composite Scope Participation
Composite scope participation includes:
- composite-room targeting
- composite-room expansion
- composite-room hierarchy behavior

Composite behavior is scope behavior, not distinct vocabulary governance.

## Floor Scope Participation
Floor scope participation includes:
- floor scope resolution
- floor scope targeting
- floor-aware behavior

Floor scope participates in the same shared resolution pipeline.

## Zone Scope Participation
Zone scope participation includes:
- zone references
- zone participation
- zone-aware scope behavior

If zones are not currently fully defined, they remain governed scope entities and require follow-up validation when directly affected.

## Hierarchy Traversal Rules
Hierarchy traversal covers:
- parent scope traversal
- child scope traversal
- composite membership traversal
- floor traversal
- household traversal

Traversal outcomes must be deterministic and explainable.

## Deterministic Resolution Rules
Deterministic ordering across shared scope entities:
1. room
2. merged room
3. composite room
4. floor
5. household

Rationale:
- preserve narrower scope determinism before broader traversal
- keep scope expansion downstream of deterministic resolution
- preserve explainable fallback behavior

## Ambiguity Handling
Ambiguity handling covers:
- room vs composite conflicts
- merged vs composite conflicts
- overlapping composite memberships
- competing scope candidates
- hierarchy ambiguity

Ambiguity outcomes must remain deterministic and explainable.

Validation participation for composite/hierarchy behavior is defined in:

- `docs/governance/vocabulary-validation-framework.md`

## Scope Expansion Architecture
Scope expansion must define:
- how composite scopes expand
- how floor scopes expand
- how hierarchy traversal affects expansion

Expansion is applied after resolved scope selection and before planning/routing execution decisions.

## Context Assembly Integration
Mapped to CF2.

Context Assembly supplies composite, floor, and hierarchy-relevant scope references consumed by runtime resolution.

## Capability Resolution Integration
Mapped to CF3.

Resolved composite and hierarchy scope outcomes participate in scope-aware capability filtering and availability decisions.

## Experience Resolution Integration
Mapped to CF4.

Resolved composite and hierarchy scope outcomes participate in scope-aware experience visibility and selection decisions.

## Planning Integration
Mapped to CF5.

Planning consumes hierarchy traversal and scope expansion outputs for targeting and execution sequence design.

## Routing Integration
Mapped to CF8.

Routing consumes composite and floor scope outcomes plus hierarchy traversal outputs for hierarchy-aware routing behavior.

## Execution Envelope Integration
Mapped to CF9.

Execution envelope carries:
- scope references
- hierarchy references
- expansion references

## Explainability Integration
Mapped to CF6.

Vocabulary explainability participation for composite/hierarchy behavior is defined in:

- `docs/governance/vocabulary-explainability-framework.md`

Coordinator must explain:
- scope selection
- hierarchy traversal
- scope expansion
- conflict resolution
- ambiguity handling

Vocabulary discovery participation for composite/hierarchy behavior is defined in:

- `docs/governance/vocabulary-discovery-framework.md`

## Diagnostics Integration
Mapped to CF7.

Vocabulary diagnostics participation for composite/hierarchy behavior is defined in:

- `docs/governance/vocabulary-diagnostics-framework.md`

Diagnostics must expose:
- hierarchy traversal
- scope expansion
- conflict conditions
- ambiguous scope matches

## Ownership Matrix
| Area | Authority | Coordinator Role |
|---|---|---|
| Composite Rooms | Governed composite scope definitions | Consumer |
| Zone Scope | Governed zone/scope definitions | Consumer |
| Floor Scope | Governed floor scope definitions | Consumer |
| Hierarchy Relationships | Governed hierarchy semantics and scope relationships | Consumer |
| Room Truth | Foundation room truth authority | Consumer |

Coordinator is never authority.

## Resolution Matrix
| Scope Type | Resolution Outcome | Consumer |
|---|---|---|
| room | resolved room scope | Planning, Routing |
| merged room | resolved merged-room scope | Planning, Routing |
| composite room | resolved composite scope | Planning, Routing |
| floor | resolved floor scope | Planning, Routing |
| household | resolved broader household scope | Planning, Routing, Execution Envelope |

## Hierarchy Traversal Matrix
| Traversal Type | Expected Outcome | Explainability Required |
|---|---|---|
| parent scope traversal | deterministic promotion to governed broader scope when required | Yes |
| child scope traversal | deterministic narrowing to valid child/member scope | Yes |
| composite membership traversal | deterministic member traversal bounded by governed membership | Yes |
| floor traversal | deterministic floor-level scope behavior where applicable | Yes |
| household traversal | deterministic fallback to broader household scope where applicable | Yes |

## Scope Expansion Matrix
| Scope Type | Expansion Behavior | Planning Impact |
|---|---|---|
| composite room | expand to governed composite members | shapes target set and execution grouping |
| floor | expand to valid floor-constrained targets | constrains planning scope and fallback |
| household | expand to broader governed household scope | enables broader fallback planning path |

## Risks
- hierarchy drift
- overlapping memberships
- stale scope definitions
- ambiguous scope relationships
- ownership drift

## Non-Rights
Coordinator does NOT own:
- composite definitions
- floor definitions
- zone definitions
- hierarchy definitions
- room truth
- scope truth

Coordinator only consumes and traverses governed structures.

## Required Future GitHub Copilot Usage
Before implementing composite-room vocabulary features, GitHub Copilot must read:
- `docs/governance/room-vocabulary-consumption-architecture.md`
- `docs/governance/runtime-vocabulary-resolution-architecture.md`
- `docs/governance/room-context-aware-vocabulary-consumption-architecture.md`
- `docs/governance/merged-room-vocabulary-consumption-architecture.md`
- `docs/governance/composite-room-vocabulary-consumption-architecture.md`
- `docs/governance/coordinator-v2-foundation-summary.md`
- relevant HTBW contracts
- relevant HTBW models
- relevant E4 issue
- target issue last

## Future Epic Dependencies
| Future Epic | Dependency |
|---|---|
| remaining E4 work | composite/hierarchy scope resolution and expansion baseline |
| E5 | hierarchy-aware capability filtering |
| E6 | hierarchy-aware experience selection |
| E7 | continuity/affinity scope context participation |
| E8 | hierarchy-aware restoration scope handling |
| E8a | occupancy and hierarchy scope interplay |
| E9 | composite/floor/hierarchy-aware routing |
| E10 | diagnostics and explainability of hierarchy traversal |
| E13 | productivity scope behavior and expansion surfaces |
| E14 | coordination scope behavior across hierarchy levels |

## Readiness Statement
Composite Room Vocabulary Consumption Architecture is READY.

This document is the baseline architecture authority for composite-room vocabulary participation, hierarchy traversal, and scope-expansion behavior.