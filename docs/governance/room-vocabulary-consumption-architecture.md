# Room Vocabulary Consumption Architecture

## Purpose
This document is the authoritative E4 Room Vocabulary Consumption architecture artifact.

Future E4 implementation issues consume this document.

This document defines:
- vocabulary consumption
- lookup patterns
- runtime access patterns
- lifecycle expectations
- Coordinator integration

This document does not define vocabulary governance.

## Authority Relationship
Room Vocabulary governance authority remains in HTBW through:
- ADR-005 Room Vocabulary Governance
- Room Vocabulary Registry Contract
- Room Vocabulary Registry Model

Coordinator authority is:
- consumption only

Coordinator consumes room vocabulary.

Coordinator does not own room vocabulary.

## Vocabulary Consumption Overview
Coordinator needs governed Room Vocabulary outputs for:
- room identity references
- room aliases
- merged-room definitions
- composite-room definitions
- floor relationships
- household scope relationships
- routing vocabulary
- targeting vocabulary

Coordinator consumes these outputs as governed references and context inputs.

## Consumption Principles
- consume governed vocabulary
- do not redefine vocabulary
- do not infer ownership
- consume canonical truth references
- remain deterministic

Coordinator uses vocabulary to resolve and explain runtime scope behavior.

Coordinator does not author vocabulary meaning.

## Runtime Consumption Architecture
Room Vocabulary enters runtime through a deterministic consumption path:

Context Assembly
  -> Vocabulary Resolution
  -> Capability Resolution
  -> Experience Resolution
  -> Planning
  -> Routing
  -> Execution Envelope

Architecture meaning:
- Context Assembly acquires governed vocabulary references
- downstream layers consume resolved vocabulary outputs
- no runtime layer becomes vocabulary authority

## Vocabulary Lookup Architecture
Coordinator lookup architecture must support:
- room lookup
- alias lookup
- merged-room lookup
- composite lookup
- floor lookup
- household scope lookup

Responsibility boundaries:
- Foundation remains room truth owner
- Room Vocabulary Registry remains vocabulary owner
- Coordinator performs runtime consumption lookups only
- Coordinator must preserve deterministic precedence and explainability for lookup outcomes

## Vocabulary Lifecycle
Vocabulary lifecycle expectations:
- startup consumption
- runtime refresh when upstream governed vocabulary changes
- cache refresh if caching is used
- invalidation behavior for stale or removed vocabulary
- deterministic stale-data handling

Coordinator may cache vocabulary-derived references.

Coordinator may not become source of truth.

## Context Assembly Integration
Vocabulary integration with CF2:
- Context Assembly receives governed room and scope vocabulary references
- Context Assembly uses them to normalize room and scope context
- Context Assembly does not own room truth or vocabulary truth

## Capability Resolution Integration
Vocabulary integration with CF3:
- vocabulary participates in room and scope targeting for capability selection
- vocabulary supplies governed room/scope reference language
- vocabulary does not supply capability ownership, capability semantics, or capability authority

## Experience Resolution Integration
Vocabulary integration with CF4:
- vocabulary participates in room and scope-aware experience selection
- vocabulary helps preserve deterministic experience visibility by governed scope
- vocabulary does not define experience taxonomy or experience ownership

## Planning Integration
Vocabulary integration with CF5:
- targeting
- execution planning
- scope planning

Planning consumes room/scope vocabulary references to produce deterministic room, merged-room, composite-room, floor, and household targeting where applicable.

## Routing Integration
Vocabulary integration with CF8:
- room routing
- merged-room routing
- composite-room routing
- floor routing
- household routing

Routing consumes room vocabulary outputs to determine governed scope and routing explainability.

## Execution Envelope Integration
Vocabulary integration with CF9 appears as references in the envelope, including:
- room references
- scope references
- routing references

Execution Envelope carries vocabulary-derived references for downstream routing, diagnostics, and explainability.

## Explainability Integration
Vocabulary integration with CF6 supports explanation of:
- room selections
- room targeting
- merged-room targeting
- composite targeting

Explainability must be able to report matched terms, aliases, scope resolution, and clarification or conflict results where applicable.

## Diagnostics Integration
Vocabulary integration with CF7 must expose:
- lookup results
- lookup failures
- stale vocabulary
- missing vocabulary

Diagnostics must remain deterministic and support troubleshooting without redefining vocabulary ownership.

## Ownership Matrix
| Area | Authority | Coordinator Role |
|---|---|---|
| Room Vocabulary | HTBW Room Vocabulary governance | Consumer |
| Room Truth | Foundation / room truth authority | Consumer |
| Area Truth | Foundation / area truth authority | Consumer |
| Merged Rooms | Governed vocabulary referencing composite interaction spaces | Consumer |
| Composite Rooms | Governed vocabulary referencing composite definitions | Consumer |
| Floor Scope | Governed vocabulary referencing floor truth | Consumer |
| Household Scope | Governed vocabulary referencing household scope semantics | Consumer |

## Consumption Matrix
| Vocabulary Element | Consumed By | Purpose |
|---|---|---|
| room | Context Assembly, Planning, Routing, Explainability | canonical room targeting and explanation |
| alias | Context Assembly, Planning, Explainability, Diagnostics | alternate term normalization |
| merged room | Context Assembly, Capability Resolution, Routing | governed merged-room scope consumption |
| composite room | Context Assembly, Capability Resolution, Planning, Routing | governed composite scope consumption |
| floor | Context Assembly, Planning, Routing | floor-aware scope resolution |
| household scope | Planning, Routing, Execution Envelope | broader household scope references |

## Future Epic Dependencies
| Future Epic | Dependency |
|---|---|
| E4 remaining work | core authority baseline for all room vocabulary consumption |
| E5 | scope-aware capability consumption depends on governed vocabulary lookup |
| E6 | room-aware experience consumption depends on governed vocabulary lookup |
| E7 | continuity/affinity room reference behavior depends on stable room vocabulary consumption |
| E8 | restoration scope references depend on stable room vocabulary consumption |
| E8a | occupancy-to-room scope interpretation depends on vocabulary consumption |
| E9 | room and scope routing depends on governed vocabulary consumption |
| E10 | explainability/diagnostics of room resolution depend on governed vocabulary consumption |
| E13 | productivity room/scope surfaces depend on governed vocabulary consumption |
| E14 | household coordination scope references depend on governed vocabulary consumption |

## Risks
- stale vocabulary
- ambiguous vocabulary
- missing vocabulary
- ownership drift

Risk rule:
all runtime handling must preserve deterministic consumption and explanation without re-owning vocabulary.

## Non-Rights
Coordinator does NOT own:
- vocabulary governance
- vocabulary definitions
- room truth
- area truth
- floor truth
- household truth

Coordinator only consumes.

## Required Future GitHub Copilot Usage
Before implementing Room Vocabulary Consumption features, GitHub Copilot must read:
- `docs/governance/room-vocabulary-consumption-architecture.md`
- `docs/governance/coordinator-v2-foundation-summary.md`
- relevant HTBW ADRs
- relevant HTBW contracts
- relevant HTBW models
- relevant E4 issue
- target issue last

## Readiness Statement
Room Vocabulary Consumption Architecture is READY.

This document is the baseline architecture authority for E4.

For detailed runtime vocabulary resolution behavior, see:

- `docs/governance/runtime-vocabulary-resolution-architecture.md`

For detailed room-context-aware behavior, see:

- `docs/governance/room-context-aware-vocabulary-consumption-architecture.md`