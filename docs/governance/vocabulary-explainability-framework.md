# Vocabulary Explainability Framework

## Purpose
This document defines the authoritative Vocabulary Explainability Framework for Coordinator V2.

This artifact defines:
- explainability structure
- machine-readable explanation format
- human-readable explanation format
- resolution explanations
- alias explanations
- targeting explanations
- hierarchy explanations
- scope-expansion explanations

This document defines explainability behavior.

This document does NOT define governance.

## Authority Relationship
Vocabulary governance authority remains external through:
- ADR-005 Room Vocabulary Governance
- Room Vocabulary Registry Contract
- Room Vocabulary Registry Model

Coordinator authority is:
- Consumer
- Explainer

Coordinator explains consumption.

Coordinator does not own governance.

## Explainability Framework Overview
Explainability exists to provide deterministic understanding of runtime vocabulary consumption decisions.

Explainability protects:
- operator understanding
- diagnostic clarity
- safe runtime reasoning transparency
- downstream trust in targeting/routing/planning outcomes

Explainability does NOT:
- define vocabulary meaning
- redefine governance
- transfer ownership

## Explainability Principles
- deterministic explanations
- reproducible explanations
- machine-readable explanations
- human-readable explanations
- provenance visibility
- hierarchy visibility
- ambiguity visibility

## Explanation Categories
- Resolution Explanation
- Alias Explanation
- Match Explanation
- Scope Explanation
- Hierarchy Explanation
- Expansion Explanation
- Validation Explanation
- Routing Explanation

## Machine-Readable Explanation Structure
Canonical logical structure must include:
- explanation_type
- input
- matched_term
- resolved_target
- resolution_path
- validation_state
- confidence
- supporting_context
- timestamp_reference

Logical schema example:

```yaml
explanation:
  explanation_type: scope_resolution
  input: "upstairs"
  matched_term: "upstairs"
  resolved_target: "floor:upstairs"
  resolution_path:
    - room_context
    - vocabulary_lookup
    - scope_resolution
    - hierarchy_traversal
  validation_state: PASS
  confidence: deterministic
  supporting_context:
    room_context_ref: room_ctx_01
    scope_ref: floor_upstairs
    hierarchy_ref: hierarchy_01
  timestamp_reference: "2026-07-10T12:00:00Z"
```

## Human-Readable Explanation Structure
Human-readable explanations must support operator-facing answers such as:
- Why did Bedroom match?
- Why was Upstairs selected?
- Why did a merged room win?
- Why was a composite scope selected?

Human-readable explanations summarize deterministic runtime reasoning and highlight selected vs rejected outcomes.

## Vocabulary Resolution Explanation
Must explain:
- term selection
- match ordering
- match outcome
- rejected candidates

## Alias Resolution Explanation
Must explain:
- alias matched
- canonical term selected
- competing aliases rejected

## Room Match Explanation
Must explain:
- room selected
- room candidates rejected
- room-context influence

## Merged Room Explanation
Must explain:
- merged-room selected
- merged-room rejected
- merged-room scope expansion

## Composite Room Explanation
Must explain:
- composite scope selected
- composite scope rejected
- hierarchy participation
- scope expansion

## Hierarchy Traversal Explanation
Must explain:
- traversal path
- selected hierarchy branch
- rejected hierarchy branches

## Scope Expansion Explanation
Must explain:
- scope selected
- expansion path
- members included
- members excluded

## Ambiguity Resolution Explanation
Must explain:
- ambiguity detected
- ambiguity resolution strategy
- winning outcome
- rejected outcomes

## Validation Explanation Integration
Relationship to:
- `docs/governance/vocabulary-validation-framework.md`

Vocabulary discovery explainability participation is defined in:

- `docs/governance/vocabulary-discovery-framework.md`

Must explain:
- warnings
- errors
- blocked outcomes
- validation-altered outcomes

## Context Assembly Integration
Mapped to CF2.

Context assembly references and room/scope context inputs must be explainable in both machine-readable and human-readable forms.

## Capability Resolution Integration
Mapped to CF3.

Capability-target and capability-scope outcomes influenced by vocabulary resolution must include explainability references.

## Experience Resolution Integration
Mapped to CF4.

Experience selection outcomes influenced by vocabulary resolution must include explainability references.

## Planning Integration
Mapped to CF5.

Planning decisions influenced by scope/target/hierarchy resolution must include explainability references.

## Routing Integration
Mapped to CF8.

Routing decisions influenced by vocabulary and scope resolution must include explainability references.

## Execution Envelope Integration
Mapped to CF9.

Explainability references are carried forward into execution records through stable explanation references and reason summaries.

## Explainability Framework Integration
Mapped to CF6.

Vocabulary explainability is a domain-specific consumption of Coordinator Explainability Framework requirements.

## Diagnostics Integration
Mapped to CF7.

Relationship to diagnostics framework:

- `docs/governance/vocabulary-diagnostics-framework.md` defines diagnostics traces that surface and link explainability references.

Diagnostics must expose explanation references and explanation outcomes for operator-visible troubleshooting.

## Ownership Matrix
| Area | Authority | Coordinator Role |
|---|---|---|
| Vocabulary Governance | HTBW governance | Consumer / Explainer |
| Room Truth | Foundation room truth authority | Consumer / Explainer |
| Scope Truth | Governed scope authorities | Consumer / Explainer |
| Hierarchy Truth | Governed hierarchy/scope authorities | Consumer / Explainer |
| Explainability Output | Coordinator explainability runtime surface | Consumer / Explainer |

## Explanation Matrix
| Explanation Type | Trigger | Consumer |
|---|---|---|
| Resolution Explanation | runtime term/scope resolution completed | diagnostics, operator review |
| Alias Explanation | alias resolution path taken | diagnostics, operator review |
| Match Explanation | room/scope candidate selected | diagnostics, planning/routing explainability |
| Scope Explanation | scope selection/expansion decision | diagnostics, planning/routing explainability |
| Hierarchy Explanation | traversal path evaluated | diagnostics, operator review |
| Expansion Explanation | member expansion performed | planning, routing, operator review |
| Validation Explanation | validation state influences decision | diagnostics, operator review |
| Routing Explanation | routing target/path chosen | diagnostics, operator review |

## Machine-Readable Explanation Matrix
| Explanation Type | Required Fields | Consumer |
|---|---|---|
| Resolution Explanation | explanation_type, input, matched_term, resolved_target, resolution_path, validation_state | diagnostics pipeline |
| Alias Explanation | explanation_type, input, matched_term, resolved_target, resolution_path, supporting_context | diagnostics pipeline |
| Match Explanation | explanation_type, input, matched_term, resolved_target, supporting_context, validation_state | planning/routing surfaces |
| Scope Explanation | explanation_type, resolved_target, resolution_path, supporting_context, validation_state | planning/routing surfaces |
| Hierarchy Explanation | explanation_type, resolution_path, supporting_context, validation_state | diagnostics pipeline |
| Expansion Explanation | explanation_type, resolved_target, supporting_context, validation_state, timestamp_reference | planning/execution records |
| Validation Explanation | explanation_type, validation_state, supporting_context, timestamp_reference | diagnostics and operator review |
| Routing Explanation | explanation_type, resolved_target, resolution_path, validation_state, supporting_context | routing diagnostics |

## Human-Readable Explanation Matrix
| Scenario | Human Explanation Required |
|---|---|
| room matched | Yes |
| alias resolved | Yes |
| merged-room selected/rejected | Yes |
| composite scope selected/rejected | Yes |
| hierarchy traversal performed | Yes |
| scope expansion performed | Yes |
| ambiguity resolved | Yes |
| validation warning/error/blocked | Yes |

## Risks
- missing explanation paths
- ambiguous explanations
- stale explanation context
- validation/explanation inconsistency
- ownership drift

## Non-Rights
Coordinator does NOT own:
- vocabulary governance
- room truth
- hierarchy truth
- scope truth

Coordinator explains decisions.

Coordinator does not redefine authority.

## Required Future GitHub Copilot Usage
Before implementing vocabulary explainability features, GitHub Copilot must read:
- `docs/governance/room-vocabulary-consumption-architecture.md`
- `docs/governance/runtime-vocabulary-resolution-architecture.md`
- `docs/governance/room-context-aware-vocabulary-consumption-architecture.md`
- `docs/governance/merged-room-vocabulary-consumption-architecture.md`
- `docs/governance/composite-room-vocabulary-consumption-architecture.md`
- `docs/governance/vocabulary-validation-framework.md`
- `docs/governance/vocabulary-explainability-framework.md`
- `docs/governance/coordinator-v2-foundation-summary.md`
- relevant HTBW contracts
- relevant HTBW models
- relevant E4 issue
- target issue last

## Future Epic Dependencies
| Future Epic | Dependency |
|---|---|
| remaining E4 work | explainability requirements for all vocabulary resolution and scope decisions |
| E5 | capability explainability for scope-aware capability outcomes |
| E6 | experience explainability for scope-aware experience outcomes |
| E7 | continuity/affinity explainability context for room/scope behavior |
| E8 | restoration explainability for hierarchy/scope decisions |
| E8a | occupancy-aware explainability for scope/routing decisions |
| E9 | routing explainability for scope target selection |
| E10 | diagnostics and operator-facing explanation consumption |
| E13 | user-facing productivity explanation behavior |
| E14 | coordination explainability across scope hierarchy |

## Readiness Statement
Vocabulary Explainability Framework is READY.

This document is the baseline architecture authority for vocabulary explainability, diagnostics visibility, operator understanding, and downstream user-facing explanation behavior.