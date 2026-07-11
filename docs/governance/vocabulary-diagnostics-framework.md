# Vocabulary Diagnostics Framework

## Purpose
This document defines the authoritative diagnostics framework for vocabulary consumption operations.

This artifact defines:
- lookup traces
- alias traces
- conflict traces
- validation traces
- room resolution traces
- hierarchy traces
- troubleshooting workflow
- operator diagnostics

This artifact does NOT define governance.

## Authority Relationship
Vocabulary Governance Authority remains external through:
- ADR-005 Room Vocabulary Governance
- Room Vocabulary Registry Contract
- Room Vocabulary Registry Model

Coordinator Authority is:
- Consumer
- Diagnostics Provider

Coordinator exposes diagnostics.

Coordinator does not own governance.

## Diagnostics Framework Overview
Diagnostics exist to provide deterministic operational visibility into how vocabulary consumption behaves at runtime.

Diagnostics protect:
- supportability
- troubleshooting speed
- operator confidence
- readiness review confidence

Diagnostics do NOT:
- define vocabulary meaning
- define vocabulary truth
- redefine governance
- transfer ownership

## Diagnostics Principles
- deterministic diagnostics
- reproducible diagnostics
- explainable diagnostics
- supportability first
- operational visibility
- governance-preserving

## Diagnostics Categories
- Lookup Diagnostics
- Alias Diagnostics
- Match Diagnostics
- Resolution Diagnostics
- Validation Diagnostics
- Conflict Diagnostics
- Hierarchy Diagnostics
- Discovery Diagnostics
- Explainability Diagnostics

## Lookup Trace Architecture
Lookup traces include visibility for:
- vocabulary lookup attempts
- lookup candidates
- lookup outcomes
- failed lookups

## Alias Trace Architecture
Alias traces include visibility for:
- alias resolution
- alias candidates
- rejected aliases
- alias conflicts

## Room Resolution Trace Architecture
Room resolution traces include visibility for:
- room matches
- rejected room candidates
- room-context influence
- room-target selection

## Merged Room Trace Architecture
Merged-room traces include visibility for:
- merged-room matching
- merged-room selection
- merged-room scope expansion
- merged-room ambiguity

## Composite Room Trace Architecture
Composite-room traces include visibility for:
- composite matching
- hierarchy traversal
- scope expansion
- composite ambiguity

## Conflict Trace Architecture
Conflict traces include visibility for:
- alias conflicts
- room conflicts
- scope conflicts
- hierarchy conflicts
- competing target resolution

## Validation Trace Architecture
Validation traces include visibility for:
- PASS
- WARNING
- ERROR
- BLOCKED

Reference:
- `docs/governance/vocabulary-validation-framework.md`

## Explainability Trace Architecture
Explainability trace integration connects diagnostics to:
- `docs/governance/vocabulary-explainability-framework.md`

Trace behavior must support:
- explanation retrieval
- explanation references
- explanation linking

## Discovery Trace Architecture
Discovery diagnostics support includes:
- discovery filtering
- room-aware discovery
- capability discovery
- guest-safe discovery

Reference:
- `docs/governance/vocabulary-discovery-framework.md`

## Troubleshooting Workflow
Issue Reported
  -> Diagnostics Review
  -> Lookup Trace Review
  -> Resolution Trace Review
  -> Validation Trace Review
  -> Explainability Review
  -> Root Cause Identification
  -> Corrective Action

This workflow is required.

## Context Assembly Integration
Mapped to CF2.

Context Assembly diagnostics expose consumed room/scope context inputs and upstream trace references.

## Capability Resolution Integration
Mapped to CF3.

Capability-resolution diagnostics expose how resolved vocabulary and scope outcomes influenced capability filtering/availability.

## Experience Resolution Integration
Mapped to CF4.

Experience diagnostics expose how vocabulary/scope outcomes influenced experience selection and rejection.

## Planning Integration
Mapped to CF5.

Planning diagnostics expose how resolved targets and expanded scopes influenced execution planning outcomes.

## Routing Integration
Mapped to CF8.

Routing diagnostics expose how resolved room/scope/hierarchy outcomes influenced routing targets and rejections.

## Execution Envelope Integration
Mapped to CF9.

Diagnostics references are propagated into execution records through stable trace references, diagnostic state markers, and linked explainability/validation references.

## Explainability Integration
Mapped to CF6.

Diagnostics must expose explainability linkages for vocabulary, scope, hierarchy, ambiguity, and conflict outcomes.

## Diagnostics Framework Integration
Mapped to CF7.

This framework is a domain-specific diagnostics surface aligned with Coordinator Diagnostics Framework expectations.

## Ownership Matrix
| Area | Authority | Coordinator Role |
|---|---|---|
| Vocabulary Governance | HTBW governance | Consumer / Diagnostics Provider |
| Capability Governance | HTBW capability governance | Consumer / Diagnostics Provider |
| Room Truth | Foundation room truth authority | Consumer / Diagnostics Provider |
| Scope Truth | Governed scope authorities | Consumer / Diagnostics Provider |
| Hierarchy Truth | Governed hierarchy/scope authorities | Consumer / Diagnostics Provider |
| Diagnostics Output | Coordinator diagnostics surface | Consumer / Diagnostics Provider |

## Diagnostics Matrix
| Diagnostic Type | Trigger | Consumer |
|---|---|---|
| Lookup Diagnostics | lookup attempt/lookup result | operator and diagnostics review |
| Alias Diagnostics | alias resolution or alias conflict | operator and diagnostics review |
| Match Diagnostics | room/scope candidate selection | operator and diagnostics review |
| Resolution Diagnostics | deterministic resolution outcome | operator and diagnostics review |
| Validation Diagnostics | PASS/WARNING/ERROR/BLOCKED state emitted | operator and readiness review |
| Conflict Diagnostics | conflict condition encountered | operator and diagnostics review |
| Hierarchy Diagnostics | hierarchy traversal/branch selection | operator and diagnostics review |
| Discovery Diagnostics | discovery filtering/visibility decision | operator and guest-safe review |
| Explainability Diagnostics | explanation linkage retrieval/outcome | operator and diagnostics review |

## Trace Matrix
| Trace Type | Purpose | Troubleshooting Use |
|---|---|---|
| lookup trace | show lookup candidates/outcomes | confirm lookup path and misses |
| alias trace | show alias normalization/conflicts | confirm alias selection or collision |
| room resolution trace | show room candidate selection/rejection | confirm room match behavior |
| merged-room trace | show merged scope selection/expansion | confirm merged-room behavior |
| composite trace | show composite selection/traversal/expansion | confirm hierarchy-aware behavior |
| conflict trace | show conflict detection and handling path | confirm deterministic conflict handling |
| validation trace | show validation severity outcomes | confirm PASS/WARNING/ERROR/BLOCKED behavior |
| explainability trace | show explanation reference linkage | confirm human/machine explanation linkage |
| discovery trace | show discovery filtering and guest-safe visibility | confirm what was shown/hidden and why |

## Troubleshooting Matrix
| Symptom | Diagnostic Path | Expected Evidence |
|---|---|---|
| expected term not matched | lookup trace -> resolution trace | candidate inspected and deterministic rejection reason |
| alias resolved unexpectedly | alias trace -> conflict trace | alias candidates, selected alias, rejected aliases |
| wrong room/scope selected | room resolution trace -> hierarchy trace -> planning trace | selected path and rejected candidates |
| merged/composite behavior unexpected | merged/composite trace -> scope expansion trace | expansion path and membership evidence |
| blocked execution/routing | validation trace -> explainability trace | ERROR/BLOCKED state and linked rationale |
| guest sees unexpected detail | discovery trace -> guest-safe filter trace | visible/hidden decision evidence |

## Risks
- missing traces
- incomplete diagnostics
- stale diagnostics
- diagnostics/explainability mismatch
- ownership drift

## Non-Rights
Coordinator does NOT own:
- vocabulary governance
- room truth
- scope truth
- hierarchy truth

Coordinator exposes diagnostics.

Coordinator does not redefine authority.

## Required Future GitHub Copilot Usage
Before implementing vocabulary diagnostics features, GitHub Copilot must read:
- `docs/governance/vocabulary-validation-framework.md`
- `docs/governance/vocabulary-explainability-framework.md`
- `docs/governance/vocabulary-discovery-framework.md`
- `docs/governance/vocabulary-diagnostics-framework.md`
- `docs/governance/coordinator-v2-foundation-summary.md`
- relevant HTBW contracts
- relevant HTBW models
- relevant E4 issue
- target issue last

## Future Epic Dependencies
| Future Epic | Dependency |
|---|---|
| remaining E4 work | diagnostics baseline for all vocabulary consumption operations |
| E5 | capability-consumption diagnostics visibility |
| E6 | experience-consumption diagnostics visibility |
| E7 | continuity/affinity diagnostics visibility for room/scope behavior |
| E8 | restoration diagnostics visibility for scope/hierarchy behavior |
| E8a | occupancy-aware diagnostics visibility |
| E9 | routing diagnostics visibility for vocabulary-driven targets |
| E10 | explainability/diagnostics linkage and operator troubleshooting |
| E13 | productivity vocabulary diagnostics visibility |
| E14 | coordination vocabulary diagnostics visibility |

## Readiness Statement
Vocabulary Diagnostics Framework is READY.

This document is the baseline architecture authority for vocabulary diagnostics, trace visibility, troubleshooting workflows, supportability, and readiness reviews.