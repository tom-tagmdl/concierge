# Vocabulary Validation Framework

## Purpose
This document defines the authoritative Vocabulary Validation Framework for Coordinator V2 runtime vocabulary consumption.

This artifact defines:
- vocabulary validation categories
- duplicate detection
- conflict detection
- capability alignment validation
- orphan vocabulary detection
- validation result classification
- diagnostics integration
- explainability integration

This artifact does NOT define governance.

## Authority Relationship
Vocabulary governance authority remains external through:
- ADR-005 Room Vocabulary Governance
- Room Vocabulary Registry Contract
- Room Vocabulary Registry Model

Coordinator authority is:
- Consumer
- Validator

Coordinator validates consumption.

Coordinator does not own governance.

## Validation Framework Overview
Validation exists to identify runtime conditions that may impact:
- resolution
- targeting
- planning
- routing
- explainability
- diagnostics

Validation protects runtime determinism and operational safety.

Validation does NOT:
- create truth
- redefine governance
- transfer ownership

## Validation Principles
- validation does not create truth
- validation does not redefine governance
- validation identifies runtime risk
- validation outcomes must be deterministic
- validation outcomes must be diagnosable
- validation outcomes must be explainable

## Vocabulary Validation Categories
- Duplicate Validation
- Conflict Validation
- Capability Alignment Validation
- Orphan Validation
- Scope Validation
- Hierarchy Validation
- Resolution Validation
- Runtime Validation

## Duplicate Detection Architecture
Duplicate detection covers:
- duplicate aliases
- duplicate room names
- duplicate merged-room references
- duplicate composite references

Expected outcomes:
- deterministic duplicate classification
- severity assignment by runtime impact
- diagnostics and explainability references for operator review

## Conflict Detection Architecture
Conflict detection covers:
- alias conflicts
- room conflicts
- merged-room conflicts
- composite-room conflicts
- hierarchy conflicts
- scope conflicts

Conflict handling remains deterministic and explainable.

## Capability Alignment Validation
Capability alignment validation covers:
- capability visibility
- capability applicability
- capability-target alignment
- capability-scope alignment

Coordinator validates consumption outcomes.

Coordinator does not own capability governance.

## Orphan Vocabulary Detection
Orphan detection covers:
- unresolved aliases
- orphan scope references
- orphan merged rooms
- orphan composite rooms
- orphan floor references

Validation outcomes classify orphan conditions by runtime severity and diagnostics visibility requirements.

## Scope Validation
Scope validation covers:
- room scopes
- merged-room scopes
- composite-room scopes
- floor scopes
- household scopes

## Hierarchy Validation
Hierarchy validation covers:
- hierarchy traversal
- parent-child relationships
- composite membership
- scope expansion relationships

## Resolution Validation
Resolution validation covers:
- deterministic ordering
- ambiguity handling
- conflict handling
- target resolution outcomes

## Runtime Validation Outcomes
Outcome classes:
- PASS
- WARNING
- ERROR
- BLOCKED

Required behavior:
- PASS: continue normal runtime processing
- WARNING: continue with surfaced diagnostic/explainability warning
- ERROR: constrain affected path and surface diagnostics/explainability error
- BLOCKED: block unsafe path and surface deterministic blocking reason

## Validation Reporting Architecture
Validation
  -> Diagnostics
  -> Explainability
  -> Operator Visibility

## Context Assembly Integration
Mapped to CF2.

Validation checks Context Assembly outputs for unresolved, conflicting, or stale vocabulary/scope references before downstream resolution reliance.

## Capability Resolution Integration
Mapped to CF3.

Validation checks capability-target and capability-scope alignment of resolved vocabulary outcomes.

## Experience Resolution Integration
Mapped to CF4.

Validation checks experience-scope consistency and detects invalid vocabulary/scope influences on experience selection.

## Planning Integration
Mapped to CF5.

Validation checks planning inputs and expanded scope references for deterministic and safe execution planning.

## Routing Integration
Mapped to CF8.

Validation checks resolved routing scopes and targets for orphaned/conflicting scope conditions before delivery-target finalization.

## Execution Envelope Integration
Mapped to CF9.

Validation references may appear in execution records as diagnostic/explainability references tied to:
- validation outcome class
- validation reason
- affected scope/reference

## Explainability Integration
Mapped to CF6.

Relationship to explainability framework:

- `docs/governance/vocabulary-explainability-framework.md` defines how validation outcomes are surfaced as machine-readable and human-readable explanation outputs.

Coordinator explains:
- validation failures
- validation warnings
- conflict outcomes
- orphan outcomes
- alignment outcomes

Vocabulary discovery validation participation is defined in:

- `docs/governance/vocabulary-discovery-framework.md`

## Diagnostics Integration
Mapped to CF7.

Relationship to diagnostics framework:

- `docs/governance/vocabulary-diagnostics-framework.md` defines vocabulary diagnostics traces and troubleshooting workflow that consume validation outcomes.

Diagnostics surfaces include:
- validation failures
- warnings
- duplicate conditions
- conflict conditions
- orphan conditions

## Ownership Matrix
| Area | Authority | Coordinator Role |
|---|---|---|
| Vocabulary Governance | HTBW governance | Consumer / Validator |
| Room Truth | Foundation room truth authority | Consumer / Validator |
| Scope Truth | Governed scope authorities | Consumer / Validator |
| Capability Governance | HTBW capability governance | Consumer / Validator |
| Hierarchy Governance | Governed hierarchy/scope contracts | Consumer / Validator |

## Validation Matrix
| Validation Type | Outcome | Severity |
|---|---|---|
| duplicate validation | duplicate condition classified | WARNING or ERROR |
| conflict validation | conflict condition classified | WARNING, ERROR, or BLOCKED |
| capability alignment validation | alignment result classified | PASS, WARNING, or ERROR |
| orphan validation | orphan condition classified | WARNING, ERROR, or BLOCKED |
| scope validation | scope validity classified | PASS, WARNING, or ERROR |
| hierarchy validation | traversal/relationship validity classified | PASS, WARNING, or ERROR |
| resolution validation | deterministic resolution validity classified | PASS, WARNING, ERROR, or BLOCKED |
| runtime validation | aggregated runtime validation decision | PASS, WARNING, ERROR, or BLOCKED |

## Duplicate Detection Matrix
| Duplicate Condition | Validation Result | Diagnostics Required |
|---|---|---|
| duplicate alias | deterministic duplicate classification | Yes |
| duplicate room name | deterministic duplicate classification | Yes |
| duplicate merged-room reference | deterministic duplicate classification | Yes |
| duplicate composite reference | deterministic duplicate classification | Yes |

## Conflict Detection Matrix
| Conflict Type | Validation Result | Explainability Required |
|---|---|---|
| alias conflict | conflict classification and deterministic handling path | Yes |
| room conflict | conflict classification and deterministic handling path | Yes |
| merged-room conflict | conflict classification and deterministic handling path | Yes |
| composite conflict | conflict classification and deterministic handling path | Yes |
| hierarchy conflict | conflict classification and deterministic handling path | Yes |
| scope conflict | conflict classification and deterministic handling path | Yes |

## Orphan Detection Matrix
| Orphan Condition | Outcome | Severity |
|---|---|---|
| unresolved alias | orphan alias classified | WARNING or ERROR |
| orphan scope reference | orphan scope classified | ERROR or BLOCKED |
| orphan merged-room reference | orphan merged-room classified | ERROR or BLOCKED |
| orphan composite reference | orphan composite classified | ERROR or BLOCKED |
| orphan floor reference | orphan floor classified | ERROR or BLOCKED |

## Risks
- stale vocabulary
- conflicting aliases
- orphan structures
- hierarchy drift
- ownership drift

## Non-Rights
Coordinator does NOT own:
- vocabulary governance
- capability governance
- room truth
- scope truth
- hierarchy truth

Coordinator validates consumption.

Coordinator does not redefine authority.

## Required Future GitHub Copilot Usage
Before implementing vocabulary validation features, GitHub Copilot must read:
- `docs/governance/room-vocabulary-consumption-architecture.md`
- `docs/governance/runtime-vocabulary-resolution-architecture.md`
- `docs/governance/room-context-aware-vocabulary-consumption-architecture.md`
- `docs/governance/merged-room-vocabulary-consumption-architecture.md`
- `docs/governance/composite-room-vocabulary-consumption-architecture.md`
- `docs/governance/vocabulary-validation-framework.md`
- `docs/governance/coordinator-v2-foundation-summary.md`
- relevant HTBW contracts
- relevant HTBW models
- relevant E4 issue
- target issue last

## Future Epic Dependencies
| Future Epic | Dependency |
|---|---|
| remaining E4 work | validation guardrails for all vocabulary consumption and scope behaviors |
| E5 | capability alignment validation for scope-aware capability consumption |
| E6 | experience alignment validation for scope-aware experience consumption |
| E7 | continuity and affinity validation context for room/scope references |
| E8 | restoration validation for scope and hierarchy references |
| E8a | occupancy-aware validation for scope and routing behaviors |
| E9 | routing validation outcomes for scope target safety |
| E10 | diagnostics and explainability surfaces for validation outcomes |
| E13 | productivity workflows consuming validation-aware scope results |
| E14 | coordination workflows consuming validation-aware scope results |

## Readiness Statement
Vocabulary Validation Framework is READY.

This document is the baseline architecture authority for vocabulary validation, diagnostics visibility, and explainability participation.