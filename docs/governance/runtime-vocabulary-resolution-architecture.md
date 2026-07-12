# Runtime Vocabulary Resolution Architecture

## Purpose
This document is the authoritative Runtime Vocabulary Resolution architecture document.

Future E4 implementation issues consume this document.

This document defines:
- phrase resolution
- alias resolution
- room lookup
- conflict handling
- ambiguity handling
- deterministic resolution
- Coordinator integration

This document does NOT define vocabulary governance.

## Authority Relationship
Vocabulary Governance Authority remains in HTBW through:
- ADR-005 Room Vocabulary Governance
- Room Vocabulary Registry Contract
- Room Vocabulary Registry Model

Coordinator Authority is:
- runtime consumption
- runtime resolution

Coordinator does not own vocabulary.

## Runtime Vocabulary Resolution Overview
Runtime vocabulary resolution is the deterministic consumption of governed vocabulary to resolve:
- phrase lookup
- alias lookup
- room lookup
- merged-room lookup
- composite-room lookup
- floor lookup
- household lookup

Runtime vocabulary resolution produces governed runtime resolution outcomes for later targeting, capability resolution, experience resolution, planning, routing, and explainability.

Runtime resolution consumes room-context-aware vocabulary behavior as defined in:

- `docs/governance/room-context-aware-vocabulary-consumption-architecture.md`

## Resolution Principles
- deterministic resolution
- governed vocabulary only
- ambiguity must be explainable
- ownership remains external
- no hidden inference chains
- reproducible resolution results

Runtime vocabulary resolution participates in validation as defined in:

- `docs/governance/vocabulary-validation-framework.md`

## Resolution Pipeline Architecture
User Intent
  -> Context Assembly
  -> Vocabulary Resolution
  -> Target Resolution
  -> Capability Resolution
  -> Experience Resolution
  -> Planning
  -> Routing
  -> Execution Envelope

This is a logical architecture.

Vocabulary resolution is a runtime consumption layer between context intake and downstream target/capability/experience handling.

## Phrase Resolution Architecture
Coordinator resolves phrases by:
- canonical phrase lookup against governed vocabulary entries
- vocabulary phrase matching against approved aliases and scope terms
- deterministic lookup ordering
- bounded, reproducible resolution outcomes

Runtime phrase resolution consumes governed terms only.

## Alias Resolution Architecture
Aliases participate through:
- alias lookup
- alias normalization to governed target terms
- alias conflict handling
- alias ambiguity handling

Alias meaning remains external to Coordinator ownership.

Coordinator resolves alias usage at runtime but does not author alias semantics.

## Room Resolution Architecture
Room resolution must support:
- room matching
- room identity lookup via governed vocabulary references
- room ambiguity handling
- deterministic room resolution outcomes

Room truth remains external.

Coordinator resolves room references, not room authority.

## Merged Room Resolution Architecture
Merged-room runtime resolution participates as a governed scope lookup path.

Reference:
- `docs/governance/merged-room-outcome-preservation-contract.md`
- `docs/governance/merged-room-vocabulary-consumption-architecture.md`

This document focuses on runtime resolution, not preservation restatement.

## Composite Room Resolution Architecture
Composite-room runtime resolution participates as a governed grouped-scope lookup path.

Reference:
- `docs/governance/composite-room-scope-outcome-preservation-contract.md`
- `docs/governance/composite-room-vocabulary-consumption-architecture.md`

This document focuses on runtime resolution, not preservation restatement.

## Scope Resolution Architecture
Runtime vocabulary resolution handles:
- room scope
- merged-room scope
- composite-room scope
- floor scope
- household scope

Scope resolution is deterministic and driven by governed scope terms, room references, alias mappings, and scope precedence rules.

## Deterministic Resolution Ordering
Resolution sequence:
1. exact room match
2. exact alias match
3. merged-room match
4. composite-room match
5. floor match
6. broader scope match

Rationale:
- preserve exact-match determinism first
- preserve governed room vocabulary precedence over broader fallback scope
- keep broader scope consumption bounded and explainable

## Ambiguity Handling
Ambiguity handling covers:
- duplicate matches
- alias collisions
- overlapping scopes
- multiple candidate rooms

Coordinator must remain deterministic.

Coordinator must remain explainable.

When ambiguity remains after governed precedence is applied, the runtime outcome must be a deterministic clarification or deterministic conflict result, not hidden guesswork.

## Conflict Resolution
Conflicts are resolved through deterministic governed precedence for:
- alias conflicts
- room-name conflicts
- scope conflicts
- vocabulary conflicts

Conflict outcomes must remain deterministic and explainable.

## Context Assembly Integration
Mapped into CF2.

Context Assembly provides:
- governed room truth references
- available vocabulary references
- relevant scope context

Vocabulary Resolution consumes these inputs.

## Capability Resolution Integration
Mapped into CF3.

Resolved vocabulary participates in capability resolution by supplying deterministic resolved room/scope references used to constrain capability availability and scope-aware filtering.

## Experience Resolution Integration
Mapped into CF4.

Resolved vocabulary participates in experience resolution by supplying deterministic room/scope references for scope-aware experience visibility and selection.

## Planning Integration
Mapped into CF5.

Resolved vocabulary participates in planning through:
- room/scope targeting
- execution planning
- execution-scope selection

## Routing Integration
Mapped into CF8.

Resolved vocabulary participates in routing through:
- room routing
- merged-room routing
- composite-room routing
- floor routing
- household routing

## Execution Envelope Integration
Mapped into CF9.

Vocabulary references appearing in the execution envelope include:
- room references
- scope references
- routing references

## Explainability Integration
Mapped into CF6.

Vocabulary explainability participation is defined in:

- `docs/governance/vocabulary-explainability-framework.md`

Coordinator must explain:
- room resolution
- alias resolution
- merged-room resolution
- composite-room resolution
- ambiguity outcomes
- conflict outcomes

## Diagnostics Integration
Mapped into CF7.

Vocabulary diagnostics participation is defined in:

- `docs/governance/vocabulary-diagnostics-framework.md`

Diagnostics must expose:
- lookup results
- match decisions
- conflicts
- ambiguity
- failed matches
- stale data

Diagnostics must include runtime lookup, match, conflict, and deterministic resolution traces through:

- `docs/governance/vocabulary-diagnostics-framework.md`

## Ownership Matrix
| Area | Authority | Coordinator Role |
|---|---|---|
| Room Vocabulary | HTBW Room Vocabulary governance | Consumer / Resolver |
| Room Truth | Foundation / room truth authority | Consumer / Resolver |
| Room Aliases | HTBW Room Vocabulary governance | Consumer / Resolver |
| Merged Rooms | Governed merged-room vocabulary and scope definitions | Consumer / Resolver |
| Composite Rooms | Governed composite-room vocabulary and scope definitions | Consumer / Resolver |
| Floor Scope | Governed floor vocabulary referencing floor truth | Consumer / Resolver |
| Household Scope | Governed household scope vocabulary | Consumer / Resolver |

Coordinator is never authority in these areas.

## Resolution Matrix
| Input Type | Resolution Outcome | Consumer |
|---|---|---|
| room phrase | resolved room reference or deterministic failure/clarification | Context Assembly, Planning, Routing |
| alias phrase | normalized governed target term | Context Assembly, Planning, Explainability |
| merged-room phrase | resolved merged-room scope reference | Planning, Routing, Explainability |
| composite phrase | resolved composite-room scope reference | Planning, Routing, Explainability |
| floor phrase | resolved floor scope reference | Planning, Routing |
| household phrase | resolved broader household scope reference | Planning, Routing, Execution Envelope |

## Ambiguity Matrix
| Ambiguity Type | Resolution Strategy | Explainability Required |
|---|---|---|
| duplicate alias | deterministic governed precedence or clarification | Yes |
| duplicate room candidate | deterministic scope precedence or clarification | Yes |
| merged/composite overlap | explicit governed scope precedence | Yes |
| floor vs room overlap | narrower governed scope first | Yes |
| broader-scope collision | deterministic fallback ordering | Yes |

## Risks
- stale vocabulary
- ambiguous vocabulary
- conflicting aliases
- overlapping scopes
- ownership drift

## Non-Rights
Coordinator does NOT own:
- room vocabulary
- aliases
- room truth
- merged-room definitions
- composite definitions
- floor definitions
- household scope definitions

Coordinator only consumes and resolves.

## Required Future GitHub Copilot Usage
Before implementing Runtime Vocabulary Resolution features, GitHub Copilot must read:
- `docs/governance/room-vocabulary-consumption-architecture.md`
- `docs/governance/runtime-vocabulary-resolution-architecture.md`
- `docs/governance/coordinator-v2-foundation-summary.md`
- relevant HTBW ADRs
- relevant HTBW contracts
- relevant HTBW models
- relevant E4 issue
- target issue last

## Readiness Statement
Runtime Vocabulary Resolution Architecture is READY.

This document is the baseline architecture authority for E4 runtime vocabulary resolution.