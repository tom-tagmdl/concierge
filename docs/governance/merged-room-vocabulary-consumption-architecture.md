# Merged Room Vocabulary Consumption Architecture

## Purpose
This document defines the authoritative architecture for merged-room vocabulary consumption.

It defines:
- merged-room vocabulary participation
- merged-room alias participation
- merged-room targeting
- merged-room resolution
- merged-room scope expansion
- merged-room explainability
- merged-room diagnostics

This document does NOT define merged-room governance.

## Authority Relationship
Room Vocabulary authority remains in HTBW through:
- ADR-005 Room Vocabulary Governance
- Room Vocabulary Registry Contract
- Room Vocabulary Registry Model

Merged-room preservation expectations remain governed by:
- `docs/governance/merged-room-outcome-preservation-contract.md`

Coordinator authority is consumption and runtime resolution only.

## Architectural Principle
Merged rooms are vocabulary entities.

Merged rooms are scope targets.

Merged rooms are not a distinct vocabulary system.

Room, merged room, composite room, floor, and household participate in one resolution process.

Differences occur after resolution when scope expansion is applied.

## Merged Room Consumption Overview
Coordinator consumes merged-room definitions as governed vocabulary/scope entities used for:
- lookup participation
- alias participation
- scope targeting
- planning expansion
- routing expansion

## Merged Room Resolution Participation
Merged rooms participate in:
- vocabulary lookup
- alias resolution
- room-aware resolution

Participation is deterministic and governed by common resolution ordering.

## Merged Room Target Resolution
Merged-room target resolution covers:
- explicit merged-room targeting
- alias-based merged-room targeting
- room-context influences

Merged-room targeting outcomes must remain deterministic and explainable.

## Scope Expansion Architecture
Vocabulary Resolution
  -> Merged Room Resolution
  -> Scope Expansion
  -> Planning
  -> Routing
  -> Execution

Scope expansion is downstream of vocabulary resolution.

Merged-room scope expansion applies only after deterministic merged-room resolution is complete.

Relationship to composite-room scope expansion:
- merged-room and composite-room scope expansion share the same runtime resolution pipeline
- both are scope entities in one vocabulary system, not separate vocabulary systems
- differences occur at expansion behavior after deterministic resolution
- see `docs/governance/composite-room-vocabulary-consumption-architecture.md` for composite/hierarchy-specific expansion behavior

## Deterministic Resolution Rules
Deterministic ordering across shared vocabulary entities:
1. room
2. merged room
3. composite room
4. floor
5. household

Ordering is applied consistently with governed precedence and explainability requirements.

## Alias Participation
Merged-room aliases participate in the same alias resolution architecture as other vocabulary entities.

Alias behavior requirements:
- deterministic alias normalization
- deterministic collision handling
- explainable alias outcome reporting

## Ambiguity Handling
Ambiguity handling covers:
- room vs merged-room conflicts
- alias collisions
- competing scope matches

Ambiguity outcomes must be deterministic and explainable.

Validation participation for merged-room behavior is defined in:

- `docs/governance/vocabulary-validation-framework.md`

## Context Assembly Integration
Mapped to CF2.

Context Assembly provides:
- room truth references
- merged-room scope references
- alias and scope context required for merged-room participation

## Capability Resolution Integration
Mapped to CF3.

Merged-room resolved scope participates in capability filtering and scope-aware capability eligibility.

## Experience Resolution Integration
Mapped to CF4.

Merged-room resolved scope participates in experience selection and scope-aware experience eligibility.

## Planning Integration
Mapped to CF5.

Planning consumes merged-room resolved scope and applies scope expansion for execution planning.

## Routing Integration
Mapped to CF8.

Routing consumes merged-room resolved scope to produce merged-room routing and downstream delivery targets.

## Execution Envelope Integration
Mapped to CF9.

Execution Envelope carries merged-room scope references and expansion-derived routing/target references.

## Explainability Integration
Mapped to CF6.

Vocabulary explainability participation for merged-room behavior is defined in:

- `docs/governance/vocabulary-explainability-framework.md`

Coordinator must explain:
- why merged-room selected
- why merged-room rejected
- why scope expanded

Vocabulary discovery participation for merged-room behavior is defined in:

- `docs/governance/vocabulary-discovery-framework.md`

## Diagnostics Integration
Mapped to CF7.

Vocabulary diagnostics participation for merged-room behavior is defined in:

- `docs/governance/vocabulary-diagnostics-framework.md`

Diagnostics must expose:
- merged-room lookup results
- merged-room ambiguity/conflict outcomes
- merged-room scope expansion outcomes

Merged-room diagnostics must align with the merged-room trace architecture in:

- `docs/governance/vocabulary-diagnostics-framework.md`

## Ownership Matrix
| Area | Authority | Coordinator Role |
|---|---|---|
| Room Vocabulary | HTBW Room Vocabulary governance | Consumer |
| Room Truth | Foundation room truth authority | Consumer |
| Merged Room Definitions | Governed merged-room definitions | Consumer |
| Merged Room Governance | HTBW governance and contracts | Consumer |
| Merged Room Membership | Governed scope definitions | Consumer |
| Composite Rooms | Governed composite scope definitions | Consumer |
| Floor Scope | Governed floor scope definitions | Consumer |

Coordinator is never authority.

## Resolution Matrix
| Resolution Scenario | Deterministic Outcome | Consumer |
|---|---|---|
| explicit merged-room target | merged-room scope resolved | Planning, Routing |
| merged-room alias target | merged-room alias normalized then resolved | Planning, Routing, Explainability |
| room vs merged-room candidate | governed precedence selects deterministic scope | Planning, Explainability |
| competing merged-room candidates | deterministic conflict/clarification outcome | Explainability, Diagnostics |

## Scope Expansion Matrix
| Resolved Scope | Expansion Behavior | Downstream Consumer |
|---|---|---|
| merged room | expand to governed member scope set | Planning |
| merged room + capability constraints | expand with capability-aware filtering | Capability Resolution, Planning |
| merged room + routing constraints | expand into routing targets | Routing |
| merged room + envelope handoff | serialize merged scope and expansion refs | Execution Envelope |

## Risks
- stale merged-room definitions
- merged-room alias collisions
- merged-room vs room ambiguity
- scope expansion drift
- ownership drift

## Non-Rights
Coordinator does NOT own:
- merged-room definitions
- merged-room governance
- merged-room membership
- room truth

Coordinator consumes governed merged-room definitions.

## Required Future GitHub Copilot Usage
Before implementing merged-room vocabulary features, GitHub Copilot must read:
- `docs/governance/room-vocabulary-consumption-architecture.md`
- `docs/governance/runtime-vocabulary-resolution-architecture.md`
- `docs/governance/room-context-aware-vocabulary-consumption-architecture.md`
- `docs/governance/merged-room-vocabulary-consumption-architecture.md`
- relevant HTBW ADRs
- relevant HTBW contracts
- relevant HTBW models
- relevant E4 issue
- target issue last

## Future Dependencies
| Future Epic | Dependency |
|---|---|
| E4 remaining issues | merged-room scope participation and expansion baseline |
| E5 | merged-room scope-aware capability consumption |
| E6 | merged-room scope-aware experience consumption |
| E7 | merged-room context influence in continuity/affinity paths |
| E8 | merged-room scope restoration behavior |
| E8a | occupancy-aware merged-room scope handling |
| E9 | merged-room routing and delivery targeting |
| E10 | merged-room explainability and diagnostics consumption |
| E13 | merged-room productivity surface targeting |
| E14 | merged-room coordination scope behavior |

## Readiness Statement
Merged Room Vocabulary Consumption Architecture is READY.

This document is the baseline architecture authority for merged-room vocabulary consumption and scope-expansion behavior.