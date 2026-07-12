# Vocabulary Diagnostics Framework

## Purpose
This document defines the authoritative diagnostics framework for vocabulary consumption operations.

This artifact defines:
- lookup traces
- alias traces
- conflict traces
- validation traces
- room resolution traces
- merged-room traces
- composite-room traces
- hierarchy traces
- discovery traces
- explainability traces
- troubleshooting workflow
- operator diagnostics
- Asset Intelligence vocabulary diagnostics
- Asset Intelligence answer-content handoff diagnostics
- guest-safe vocabulary and output visibility diagnostics

This artifact does NOT define governance.

This artifact does NOT define implementation.

This artifact does NOT define Asset Intelligence outputs.

This artifact documents how Coordinator diagnostics expose consumption behavior while preserving ownership boundaries.

## Authority Relationship
Vocabulary Governance Authority remains external through:
- ADR-005 Room Vocabulary Governance
- Room Vocabulary Registry Contract
- Room Vocabulary Registry Model

Asset Intelligence Authority remains external through:
- Asset Intelligence Contract
- Asset Model
- Environment Model
- Asset Intelligence implementation

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
- explainability traceability
- vocabulary-to-output boundary clarity

Diagnostics support readiness reviews by showing whether consumption behavior is complete, explainable, diagnosable, and ownership-safe.

Diagnostics support explainability and troubleshooting by linking lookup, resolution, validation, discovery, and handoff behavior back to deterministic evidence.

Diagnostics do NOT:
- define vocabulary meaning
- define vocabulary truth
- redefine governance
- redefine room truth
- redefine scope truth
- redefine hierarchy truth
- redefine Asset Intelligence truth
- redefine human_health truth
- redefine advisory truth
- transfer ownership

## Diagnostics Principles
- deterministic diagnostics
- reproducible diagnostics
- explainable diagnostics
- supportability first
- operational visibility
- governance-preserving
- ownership-preserving
- source-attributed
- guest-safe where relevant

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
- Room Context Diagnostics
- Merged Room Diagnostics
- Composite Room Diagnostics
- Asset Intelligence Vocabulary Diagnostics
- Asset Intelligence Answer-Content Handoff Diagnostics
- Guest-Safe Visibility Diagnostics

## Lookup Trace Architecture
Lookup traces include visibility for:
- vocabulary lookup attempts
- lookup candidates
- lookup outcomes
- failed lookups
- lookup source
- lookup scope

## Alias Trace Architecture
Alias traces include visibility for:
- alias resolution
- alias candidates
- rejected aliases
- alias conflicts
- alias source

## Room Resolution Trace Architecture
Room resolution traces include visibility for:
- room matches
- rejected room candidates
- room-context influence
- room-target selection
- stale room context
- unavailable room context

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
- vocabulary anchor conflicts
- asset group conflicts
- asset label/category/name conflicts

## Validation Trace Architecture
Validation traces include visibility for:
- PASS
- WARNING
- ERROR
- BLOCKED

Reference:
- `docs/governance/vocabulary-validation-framework.md`

Validation traces report validation outcomes.

Validation traces do not redefine validation authority.

## Explainability Trace Architecture
Explainability trace integration connects diagnostics to:
- `docs/governance/vocabulary-explainability-framework.md`

Trace behavior must support:
- explanation retrieval
- explanation references
- explanation linking
- source attribution
- ownership-boundary explanation

## Discovery Trace Architecture
Discovery diagnostics support includes:
- discovery filtering
- room-aware discovery
- capability discovery
- guest-safe discovery
- Asset Intelligence-related vocabulary discovery
- future/non-E4 surface exclusion

Reference:
- `docs/governance/vocabulary-discovery-framework.md`

## Asset Intelligence Vocabulary Diagnostics
Grounded in:
- `docs/governance/asset-intelligence-vocabulary-consumption-architecture.md`

Diagnostics must cover:
- asset label match
- asset type/category match
- asset identity/name metadata match
- Concierge `asset_groups` match
- room context applied to asset vocabulary matching
- asset/group/category/label resolution
- no-match condition
- ambiguity condition
- stale context condition
- guest-safe visibility decision

Concierge `asset_groups` are Concierge room configuration and must not be attributed to Asset Intelligence ownership.

Asset Intelligence labels, asset_type/category, identity metadata, source_status, and confidence metadata are consumed only as surfaced or exposed inputs.

## Asset Intelligence Answer-Content Handoff Diagnostics
Diagnostics must cover post-resolution handoff to Asset Intelligence-authored output.

Diagnostics must include:
- consumed Asset Intelligence output source
- asset descriptions source
- `risk_state` source
- `candidate_state` source
- `reasons` source
- exposure risk source
- advisory source
- `primary_advisory` source
- `human_health` source
- `human_health` reasons source
- `human_health` `advisory_reasons` source
- room environment projection source
- `source_status` / confidence source
- retrieval failure condition
- inaccessible output condition
- ownership-boundary indicator showing Coordinator consumed an Asset Intelligence result rather than authored one

Coordinator may present or route Asset Intelligence-authored output.

Coordinator may not generate alternate conclusions or reinterpret Asset Intelligence output.

## Nonexistent / Future Output Diagnostics Guardrail
Current implementation does not expose first-class outputs under these names:
- asset narratives
- asset-condition narratives
- collection narratives
- environmental narratives
- room-health narratives
- significance assessments
- relevance assessments

Diagnostics must not claim these as current implementation outputs unless future authoritative artifacts or implementation introduce them.

If the term `narrative` appears, diagnostics must map it to implementation-grounded outputs such as:
- descriptions
- advisories
- `risk_state`
- `reasons`
- `primary_advisory`
- `human_health`

## Guest-Safe Diagnostics
Diagnostics must cover:
- whether guest-safe rules affected vocabulary visibility
- whether guest-safe rules affected Asset Intelligence output visibility
- hidden output reason
- safe fallback behavior
- no unauthorized disclosure of sensitive asset, environment, or health details

This artifact does not invent guest-safe policy.

If no specific guest-safe governance exists for a diagnostic path, that absence must be treated as a readiness gap rather than invented behavior.

## Troubleshooting Workflow
Issue Reported
  -> Diagnostics Review
  -> Lookup Trace Review
  -> Room / Scope Resolution Trace Review
  -> Asset Vocabulary Trace Review, if applicable
  -> Answer-Content Handoff Trace Review, if applicable
  -> Validation Trace Review
  -> Explainability Review
  -> Discovery Review
  -> Guest-Safe Visibility Review, if applicable
  -> Root Cause Identification
  -> Corrective Action

This workflow is required.

## Context Assembly Integration
Mapped to CF2.

Context Assembly diagnostics expose:
- vocabulary diagnostics inputs
- room context diagnostics
- Asset Intelligence vocabulary context where applicable
- source attribution

## Capability Resolution Integration
Mapped to CF3.

Diagnostics may show why vocabulary resolution is separate from capability selection.

This prevents E4 asset vocabulary diagnostics from drifting into E5 capability governance.

## Experience Resolution Integration
Mapped to CF4.

Answer-content handoff diagnostics may later inform experience consumption without moving ownership.

## Planning Integration
Mapped to CF5.

Diagnostic references may inform plans without allowing planner ownership of vocabulary or Asset Intelligence outputs.

## Routing Integration
Mapped to CF8.

Routing diagnostics expose how resolved room, scope, hierarchy, and Asset Intelligence handoff references influenced routing decisions.

## Execution Envelope Integration
Mapped to CF9.

Diagnostics references are propagated into execution records through stable trace references, diagnostic state markers, linked explainability/validation references, and Asset Intelligence handoff trace references where applicable.

## Explainability Integration
Mapped to CF6.

Diagnostics support explanation retrieval, explanation references, ownership-boundary explanations, and why/why-not reasoning for vocabulary and post-resolution output consumption.

## Diagnostics Framework Integration
Mapped to CF7.

This framework is a domain-specific diagnostics surface aligned with the Coordinator Diagnostics Framework.

## Ownership Matrix
| Area | Authority | Coordinator Role | Diagnostic Role |
|---|---|---|---|
| Vocabulary Governance | HTBW governance | Consumer / Diagnostics Provider | expose consumed vocabulary behavior only |
| Capability Governance | HTBW capability governance | Consumer / Diagnostics Provider | show separation from capability selection |
| Room Truth | Foundation room truth authority | Consumer / Diagnostics Provider | expose room-context influence only |
| Scope Truth | Governed scope authorities | Consumer / Diagnostics Provider | expose scope consumption and traversal only |
| Hierarchy Truth | Governed hierarchy/scope authorities | Consumer / Diagnostics Provider | expose traversal and expansion only |
| Room Context | Context Assembly and Foundation truth inputs | Consumer / Diagnostics Provider | expose applied, stale, or unavailable context |
| Concierge asset_groups | Concierge room configuration | Consumer / Diagnostics Provider | expose group matching without misattributing ownership |
| Asset Labels | Asset Intelligence exposed metadata | Consumer / Diagnostics Provider | expose label match source only |
| Asset Type / Category | Asset Intelligence exposed metadata | Consumer / Diagnostics Provider | expose category match source only |
| Asset Identity Metadata | Asset Intelligence exposed metadata | Consumer / Diagnostics Provider | expose identity/name match source only |
| Asset Descriptions | Asset Intelligence-authored output | Consumer / Diagnostics Provider | expose description retrieval source only |
| Risk / Advisory Output | Asset Intelligence-authored output | Consumer / Diagnostics Provider | expose status/advisory handoff source only |
| Human Health Output | Asset Intelligence-authored output | Consumer / Diagnostics Provider | expose human_health handoff source only |
| Room Environment Projection | Asset Intelligence-authored output | Consumer / Diagnostics Provider | expose room projection handoff source only |
| Diagnostics Output | Coordinator diagnostics surface | Consumer / Diagnostics Provider | expose consumption behavior without redefining authority |

## Diagnostics Matrix
| Diagnostic Type | Trigger | Consumer | Authority Preserved |
|---|---|---|---|
| Lookup Diagnostics | lookup attempt or lookup result | operator and diagnostics review | vocabulary governance remains external |
| Alias Diagnostics | alias resolution or alias conflict | operator and diagnostics review | alias authority remains external |
| Match Diagnostics | room, scope, asset, or group candidate selection | operator and diagnostics review | truth and metadata ownership remain external |
| Resolution Diagnostics | deterministic resolution outcome | operator and diagnostics review | Coordinator reports outcome only |
| Validation Diagnostics | PASS/WARNING/ERROR/BLOCKED emitted | operator and readiness review | validation authority remains external |
| Conflict Diagnostics | conflict condition encountered | operator and diagnostics review | conflict truth remains external |
| Hierarchy Diagnostics | hierarchy traversal or branch selection | operator and diagnostics review | hierarchy authority remains external |
| Discovery Diagnostics | discovery filtering or visibility decision | operator and guest-safe review | discovery exposes consumption only |
| Explainability Diagnostics | explanation linkage retrieval or outcome | operator and diagnostics review | explainability does not redefine authority |
| Room Context Diagnostics | room context applied, stale, or unavailable | operator and diagnostics review | room truth remains external |
| Merged Room Diagnostics | merged-room lookup or expansion path | operator and diagnostics review | merged-room governance remains external |
| Composite Room Diagnostics | composite lookup, traversal, or expansion path | operator and diagnostics review | composite/hierarchy governance remains external |
| Asset Intelligence Vocabulary Diagnostics | label/category/name/group match behavior | operator and diagnostics review | Asset Intelligence and Concierge ownership boundaries preserved |
| Asset Intelligence Answer-Content Handoff Diagnostics | post-resolution output retrieval or handoff | operator and diagnostics review | Asset Intelligence output authority preserved |
| Guest-Safe Visibility Diagnostics | hidden or reduced vocabulary/output visibility | operator and guest-safe review | guest-safe policy remains external |

## Trace Matrix
| Trace Type | Purpose | Troubleshooting Use | Ownership Boundary |
|---|---|---|---|
| lookup trace | show lookup candidates, source, scope, and outcomes | confirm lookup path and misses | vocabulary ownership remains external |
| alias trace | show alias normalization, source, and conflicts | confirm alias selection or collision | alias authority remains external |
| room resolution trace | show room candidate selection, context use, and stale/unavailable context | confirm room match behavior | Foundation room truth remains external |
| merged-room trace | show merged scope selection and expansion | confirm merged-room behavior | merged-room governance remains external |
| composite trace | show composite selection, traversal, and expansion | confirm hierarchy-aware behavior | composite/hierarchy authority remains external |
| conflict trace | show conflict detection and handling path | confirm deterministic conflict handling | Coordinator reports consumed conflict only |
| validation trace | show validation severity outcomes | confirm PASS/WARNING/ERROR/BLOCKED behavior | validation authority remains external |
| explainability trace | show explanation reference linkage and source attribution | confirm human/machine explanation linkage | explanation references do not redefine authority |
| discovery trace | show discovery filtering and guest-safe visibility | confirm what was shown or hidden and why | discovery remains consumption-only |
| asset vocabulary trace | show label/category/name/group matching | confirm Asset Intelligence-related resolution path | Asset Intelligence and Concierge boundaries preserved |
| answer-content handoff trace | show retrieved Asset Intelligence output source | confirm consumed output rather than authored output | Asset Intelligence output authority preserved |
| guest-safe trace | show visibility reduction or fallback | confirm no unauthorized disclosure | guest-safe policy remains external |

## Troubleshooting Matrix
| Symptom | Diagnostic Path | Expected Evidence | Likely Ownership Boundary |
|---|---|---|---|
| vocabulary not recognized | lookup trace -> resolution trace | candidate inspected and deterministic rejection reason | vocabulary governance external |
| wrong room selected | room resolution trace -> hierarchy trace -> planning trace | selected path, stale context state, rejected candidates | Foundation room truth external |
| wrong merged room selected | merged-room trace -> conflict trace -> explainability trace | merged-room selection path and rejected candidates | merged-room governance external |
| wrong composite scope selected | composite trace -> hierarchy trace -> explainability trace | traversal branch and scope expansion evidence | composite/hierarchy authority external |
| asset group not recognized | asset vocabulary trace -> room context trace | Concierge `asset_groups` source and no-match or stale-context reason | Concierge room configuration |
| asset label not matched | asset vocabulary trace -> lookup trace | label source, candidate set, rejection reason | Asset Intelligence exposed metadata |
| asset type/category not matched | asset vocabulary trace -> lookup trace | category source, candidate set, rejection reason | Asset Intelligence exposed metadata |
| asset answer unavailable | answer-content handoff trace -> retrieval failure trace | resolved target with missing or inaccessible output source | Asset Intelligence output authority |
| room health answer unavailable | room resolution trace -> answer-content handoff trace -> guest-safe trace | room target resolved, handoff attempted, missing or hidden output evidence | Asset Intelligence output authority |
| advisory output missing | answer-content handoff trace -> retrieval failure trace | advisory source absent or inaccessible | Asset Intelligence output authority |
| guest cannot see expected output | guest-safe trace -> discovery trace -> answer-content handoff trace | visibility restriction or safe fallback evidence | guest-safe policy external |
| diagnostic says narrative, significance, or relevance but no such output exists | diagnostics review -> answer-content handoff trace -> nonexistent output guardrail review | implementation-grounded output mapping required | implementation and authority boundary preserved |

## Risks
- missing traces
- incomplete diagnostics
- stale diagnostics
- diagnostics/explainability mismatch
- ownership drift
- hidden inference
- diagnostics claiming nonexistent outputs
- `asset_groups` ownership misattribution
- vocabulary anchor and answer-content confusion
- guest-safe leakage
- E4/E5 boundary drift

## Non-Rights
Coordinator does NOT own:
- vocabulary governance
- room truth
- scope truth
- hierarchy truth
- Asset Intelligence governance
- asset evaluation
- environmental evaluation
- risk/advisory generation
- human_health generation
- significance
- relevance
- Asset Intelligence contracts
- Asset Intelligence models

Coordinator exposes diagnostics.

Coordinator does not redefine authority.

## Required Future GitHub Copilot Usage
Before implementing vocabulary diagnostics features, GitHub Copilot must read:
- `docs/governance/vocabulary-validation-framework.md`
- `docs/governance/vocabulary-explainability-framework.md`
- `docs/governance/vocabulary-discovery-framework.md`
- `docs/governance/vocabulary-diagnostics-framework.md`
- `docs/governance/asset-intelligence-vocabulary-consumption-architecture.md`
- `docs/governance/room-context-aware-vocabulary-consumption-architecture.md`
- `docs/governance/coordinator-v2-foundation-summary.md`
- relevant HTBW contracts
- relevant HTBW models
- relevant E4 issue
- target issue last

## Future Epic Dependencies
| Future Epic | Dependency |
|---|---|
| remaining E4 work | diagnostics baseline for all vocabulary consumption operations, including Asset Intelligence-related vocabulary and handoff traces |
| E5 | capability-consumption diagnostics visibility and evidence that vocabulary resolution remains separate from capability selection |
| E6 | experience-consumption diagnostics visibility and answer-content handoff trace reuse |
| E7 | continuity and affinity diagnostics visibility for room/scope behavior |
| E8 | restoration diagnostics visibility for scope/hierarchy behavior |
| E8a | occupancy-aware diagnostics visibility |
| E9 | routing diagnostics visibility for vocabulary-driven targets |
| E10 | explainability/diagnostics linkage and operator troubleshooting |
| E13 | productivity vocabulary diagnostics visibility |
| E14 | coordination vocabulary diagnostics visibility |

#79 must be complete before #80 can re-approve E4 readiness.

## Readiness Statement
Vocabulary Diagnostics Framework is READY for E4 readiness review once this artifact, all referenced diagnostics integrations, and the #79 readiness comment are complete.

This document is the baseline architecture authority for vocabulary diagnostics, trace visibility, troubleshooting workflows, supportability, Asset Intelligence vocabulary diagnostics, answer-content handoff diagnostics, and readiness reviews.

Only #80 can re-approve E4 readiness.