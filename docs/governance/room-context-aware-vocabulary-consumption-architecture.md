# Room Context Aware Vocabulary Consumption Architecture

## Purpose
This document is the authoritative Room Context Aware Vocabulary Consumption architecture document.

Future E4 implementation issues consume this document.

This document defines:
- room-aware vocabulary behavior
- room-context influence
- room-specific vocabulary behavior
- room-based ambiguity reduction
- room targeting influence
- room-context explainability

This document does NOT define room governance.

## Authority Relationship
Room Vocabulary authority remains in HTBW through:
- ADR-005 Room Vocabulary Governance
- Room Vocabulary Registry Contract
- Room Vocabulary Registry Model

Room Context authority remains in:
- Context Assembly
- Room Truth governance

Coordinator authority is:
- consumer only

Coordinator consumes room context.

Coordinator does not own room context.

## Room Context Consumption Overview
Room-context-aware vocabulary consumption means Coordinator uses governed room context to improve deterministic vocabulary consumption for:
- room-scoped vocabulary
- room-specific aliases
- room-aware targeting
- room-aware resolution
- room-aware planning
- room-aware routing

Room context influences runtime outcomes.

Room context does not redefine vocabulary meaning.

## Consumption Principles
- consume governed room context
- room context influences resolution
- room context does not replace vocabulary governance
- deterministic outcomes required
- explainability required
- ownership remains external

Validation participation for room-context-aware behavior is defined in:

- `docs/governance/vocabulary-validation-framework.md`

## Room Context Influence Architecture
Context Assembly
  -> Room Context
  -> Vocabulary Resolution
  -> Target Resolution
  -> Capability Resolution
  -> Experience Resolution
  -> Planning
  -> Routing

Room context participates as a governed input that narrows or clarifies vocabulary resolution.

## Room-Specific Vocabulary Behavior
Room-specific vocabulary may participate through:
- room aliases
- room-specific references
- room-local naming
- room-targeted terminology

Coordinator consumes provided vocabulary.

Coordinator does not define vocabulary.

## Room-Aware Resolution Architecture
Room context influences resolution by:
- selecting among candidate matches
- reducing ambiguity
- improving targeting
- guiding deterministic resolution ordering

Room context influences.

Room context does not become authority.

## Room Override Behavior
Room-specific context may override broader context where appropriate through deterministic precedence such as:
- local room alias over broader-scope term when governed context supports it
- local room vocabulary preference under governed scope constraints
- room-specific interpretation ahead of broader fallback where context supports it

Override behavior must remain deterministic and explainable.

## Room Targeting Integration
Room context influences:
- room targeting
- room selection
- room routing
- room planning

Merged-room scope behavior participates in this room-context-aware path; see:

- `docs/governance/merged-room-vocabulary-consumption-architecture.md`

Composite-room scope behavior participates in this room-context-aware path; see:

- `docs/governance/composite-room-vocabulary-consumption-architecture.md`

Vocabulary discovery participation for room-context behavior is defined in:

- `docs/governance/vocabulary-discovery-framework.md`

Preservation expectations remain governed by existing V1 outcome artifacts; this document defines consumption architecture only.

## Ambiguity Reduction Architecture
Room context helps resolve ambiguity for:
- duplicate aliases
- overlapping terms
- multiple room matches
- competing targets

Room context must reduce ambiguity deterministically.

## Conflict Handling
Conflicts are handled through deterministic governed outcomes for:
- room-specific alias conflicts
- room-level ambiguity
- context conflicts
- targeting conflicts

Conflict outcomes must remain deterministic and explainable.

## Context Assembly Integration
Mapped to CF2.

Context Assembly supplies:
- resolved room truth references
- available room aliases and room-scoped vocabulary references
- relevant room, floor, and scope context

Room-context-aware vocabulary consumption consumes those inputs.

## Capability Resolution Integration
Mapped to CF3.

Room-aware vocabulary participates in capability resolution by supplying narrowed room/scope resolution for capability filtering and visibility.

## Experience Resolution Integration
Mapped to CF4.

Room-aware vocabulary participates in experience resolution by supplying narrowed room/scope resolution for experience visibility and prioritization.

## Planning Integration
Mapped to CF5.

Room-aware vocabulary participates in planning through room-target resolution, scope-target selection, and execution planning.

## Routing Integration
Mapped to CF8.

Room-aware vocabulary participates in routing through room-aware scope resolution for room, merged-room, composite-room, floor, and broader household routing paths.

## Explainability Integration
Mapped to CF6.

Vocabulary explainability participation for room-context behavior is defined in:

- `docs/governance/vocabulary-explainability-framework.md`

Coordinator must explain:
- room influence
- room-specific interpretation
- targeting decisions
- ambiguity reduction
- conflict outcomes

## Diagnostics Integration
Mapped to CF7.

Vocabulary diagnostics participation for room-context behavior is defined in:

- `docs/governance/vocabulary-diagnostics-framework.md`

Diagnostics must expose:
- room context influence
- room-aware match decisions
- room-aware ambiguity outcomes
- room-aware conflict outcomes

## Ownership Matrix
| Area | Authority | Coordinator Role |
|---|---|---|
| Room Vocabulary | HTBW Room Vocabulary governance | Consumer |
| Room Truth | Foundation / room truth authority | Consumer |
| Room Context | Context Assembly and governed room truth inputs | Consumer |
| Room Aliases | HTBW Room Vocabulary governance | Consumer |
| Merged Rooms | Governed merged-room vocabulary/scope definitions | Consumer |
| Composite Rooms | Governed composite-room vocabulary/scope definitions | Consumer |
| Floor Scope | Governed floor references and floor truth | Consumer |

Coordinator is never authority in these areas.

## Room Context Influence Matrix
| Context Element | Influences | Outcome |
|---|---|---|
| room identity | candidate selection | narrower deterministic room resolution |
| room alias | alias normalization | room-aware alias resolution |
| room scope | scope narrowing | valid room or grouped-scope targeting |
| floor relationship | broader scope qualification | deterministic floor-aware routing/targeting |
| room metadata | contextual qualification | explainable room-aware interpretation |

## Resolution Precedence Matrix
| Resolution Scenario | Deterministic Outcome | Explainability Required |
|---|---|---|
| explicit room match | room match wins before broader scope fallback | Yes |
| room alias match | alias normalizes to governed room target deterministically | Yes |
| duplicate room aliases | governed precedence or clarification | Yes |
| competing room candidates | room context narrows or clarification occurs | Yes |
| room vs broader scope | narrower room-specific outcome wins when governed context supports it | Yes |

## Risks
- stale room context
- conflicting room aliases
- ambiguous room vocabulary
- room-context drift
- ownership drift

## Non-Rights
Coordinator does NOT own:
- room vocabulary
- room truth
- room aliases
- room context truth
- merged-room definitions
- composite-room definitions
- floor scope definitions

Coordinator only consumes.

## Required Future GitHub Copilot Usage
Before implementing room-context-aware vocabulary features, GitHub Copilot must read:
- `docs/governance/room-vocabulary-consumption-architecture.md`
- `docs/governance/runtime-vocabulary-resolution-architecture.md`
- `docs/governance/room-context-aware-vocabulary-consumption-architecture.md`
- `docs/governance/coordinator-v2-foundation-summary.md`
- relevant HTBW ADRs
- relevant HTBW contracts
- relevant HTBW models
- relevant E4 issue
- target issue last

## Future Epic Dependencies
| Future Epic | Dependency |
|---|---|
| Remaining E4 work | core architecture for room-aware vocabulary consumption |
| E5 | room-aware capability filtering depends on resolved room context |
| E6 | room-aware experience selection depends on resolved room context |
| E7 | continuity and affinity behavior may consume room-aware resolution outputs |
| E8 | restoration scope selection depends on room-aware targeting |
| E8a | occupancy and room-context interaction depends on room-aware consumption |
| E9 | room-aware routing depends on room-context vocabulary resolution |
| E10 | explainability/diagnostics of room influence depend on room-aware consumption |
| E13 | productivity experiences may use room-aware context narrowing |
| E14 | household coordination may consume room-aware scope resolution |

## Readiness Statement
Room Context Aware Vocabulary Consumption Architecture is READY.

This document is the baseline architecture authority for room-context-aware vocabulary behavior.