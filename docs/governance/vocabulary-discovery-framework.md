# Vocabulary Discovery Framework

## Purpose
This document defines the authoritative architecture for room-aware vocabulary discovery and "What Can I Say Here?" support.

This artifact defines:
- discoverable vocabulary
- room-aware vocabulary discovery
- capability-linked vocabulary discovery
- guest-safe discovery
- explainable discovery
- diagnostics-visible discovery

This document does NOT define governance.

## Authority Relationship
Vocabulary Governance Authority remains external through:
- ADR-005 Room Vocabulary Governance
- Room Vocabulary Registry Contract
- Room Vocabulary Registry Model

Capability Governance Authority remains external through:
- Capability Projection Contract
- Capability Projection Model

Coordinator Authority is:
- Consumer
- Discovery Provider

Coordinator provides discovery.

Coordinator does not own governance.

## Vocabulary Discovery Overview
"What Can I Say Here?" is a household-facing vocabulary discovery capability that provides contextual, room-aware, capability-aware, and guest-safe discoverable language.

Examples:
- room vocabulary discovery
- room-aware discovery
- capability-linked vocabulary discovery
- contextual vocabulary discovery
- guest-safe discovery

## Discovery Principles
- room-aware
- capability-aware
- guest-safe
- explainable
- diagnostics-visible
- deterministic
- governance-preserving

## Discovery Categories
- Room Vocabulary Discovery
- Capability Vocabulary Discovery
- Contextual Vocabulary Discovery
- Guest Vocabulary Discovery
- Scope Vocabulary Discovery
- Room-Specific Discovery
- Merged Room Discovery
- Composite Scope Discovery

## Room-Aware Discovery Architecture
Context Assembly
  -> Room Context
  -> Vocabulary Discovery
  -> Capability Filtering
  -> Presentation
  -> Explainability

## Discoverable Vocabulary Model
Discoverable categories include:
- room references
- aliases
- room-scoped actions
- room-scoped experiences
- contextual references
- scope references

Do not expose implementation details.

## Capability-Linked Vocabulary Discovery
Capabilities participate by providing discoverable language bounded by capability projections and scope context.

Examples:
- What can I do here?
- What can I control here?
- What services are available here?

Coordinator consumes capability projections.

Coordinator does not own capabilities.

## Room-Specific Vocabulary Discovery
Discovery changes by room context.

Examples:
- Kitchen
- Bedroom
- Office
- Garage

Discovery remains contextual and deterministic.

## Merged Room Discovery
Merged rooms participate through:
- merged-room aliases
- merged-room targeting vocabulary
- merged-room scope references

## Composite Scope Discovery
Composite scopes participate through:
- floor references
- zone references
- composite scope references

## Guest-Safe Discovery
Guest-safe discovery includes only safe, household-facing language.

Examples of visible categories:
- room names
- room actions
- room capabilities

Examples of excluded categories:
- internal identifiers
- implementation names
- internal entity names
- platform internals

## Discovery Filtering Rules
Discovery filtering is based on:
- room context
- capability availability
- scope
- visibility
- discoverability

## Explainability Integration
Mapped to CF6.

Coordinator explains:
- why vocabulary was shown
- why vocabulary was hidden
- why capability language appeared
- why room language appeared

## Diagnostics Integration
Mapped to CF7.

Vocabulary diagnostics participation for discovery behavior is defined in:

- `docs/governance/vocabulary-diagnostics-framework.md`

Diagnostics expose:
- discovery results
- discovery filtering
- capability filtering
- visibility decisions
- guest-safe discovery visibility decisions
- Asset Intelligence-related vocabulary discovery visibility decisions
- future/non-E4 surface exclusion decisions

## Context Assembly Integration
Mapped to CF2.

Context assembly provides room/scope context inputs required for deterministic discovery behavior.

## Capability Resolution Integration
Mapped to CF3.

Capability resolution provides capability-aware filtering inputs used by discovery behavior.

## Planning Integration
Mapped to CF5.

Discovery consumes planning-relevant scope/target context where needed to preserve contextual appropriateness.

## Ownership Matrix
| Area | Authority | Coordinator Role |
|---|---|---|
| Vocabulary Governance | HTBW governance | Consumer / Discovery Provider |
| Capability Governance | HTBW capability governance | Consumer / Discovery Provider |
| Room Truth | Foundation room truth authority | Consumer / Discovery Provider |
| Scope Truth | Governed scope authorities | Consumer / Discovery Provider |
| Discovery Output | Coordinator discovery surface | Consumer / Discovery Provider |

## Discovery Matrix
| Discovery Type | Output | Consumer |
|---|---|---|
| Room Vocabulary Discovery | room-aware phrase candidates | household and operator surfaces |
| Capability Vocabulary Discovery | capability-linked phrase candidates | household and operator surfaces |
| Contextual Vocabulary Discovery | context-scoped phrase candidates | household and operator surfaces |
| Guest Vocabulary Discovery | guest-safe phrase candidates | guest-safe surfaces |
| Scope Vocabulary Discovery | scope-targeted phrase candidates | household and operator surfaces |
| Room-Specific Discovery | room-specific phrase candidates | room-context surfaces |
| Merged Room Discovery | merged-room phrase candidates | merged-room scope surfaces |
| Composite Scope Discovery | composite/floor/zone phrase candidates | composite/floor scope surfaces |

## Guest-Safe Matrix
| Information Category | Visible | Hidden |
|---|---|---|
| room names | Yes | No |
| room actions | Yes | No |
| room capabilities (safe labels) | Yes | No |
| internal identifiers | No | Yes |
| implementation names | No | Yes |
| internal entity names | No | Yes |
| platform internals | No | Yes |

## Room Discovery Matrix
| Room Context | Discoverable Vocabulary |
|---|---|
| Kitchen | room aliases, kitchen-scoped actions, kitchen-scoped capabilities |
| Bedroom | room aliases, bedroom-scoped actions, bedroom-scoped capabilities |
| Office | room aliases, office-scoped actions, office-scoped capabilities |
| Garage | room aliases, garage-scoped actions, garage-scoped capabilities |

## Capability Discovery Matrix
| Capability Type | Discovery Outcome |
|---|---|
| room control capabilities | control-oriented room vocabulary shown when available |
| media capabilities | media vocabulary shown when available in current scope |
| environment capabilities | environment vocabulary shown when available in current scope |
| productivity capabilities | productivity vocabulary shown when available and policy-allowed |
| unsupported capabilities | hidden or described as unavailable with explainable rationale |

## Risks
- over-disclosure
- under-disclosure
- stale discovery context
- capability drift
- ownership drift

## Non-Rights
Coordinator does NOT own:
- vocabulary governance
- capability governance
- room truth
- scope truth

Coordinator exposes discoverable vocabulary.

Coordinator does not redefine authority.

## Required Future GitHub Copilot Usage
Before implementing vocabulary discovery features, GitHub Copilot must read:
- `docs/governance/room-vocabulary-consumption-architecture.md`
- `docs/governance/room-context-aware-vocabulary-consumption-architecture.md`
- `docs/governance/merged-room-vocabulary-consumption-architecture.md`
- `docs/governance/composite-room-vocabulary-consumption-architecture.md`
- `docs/governance/vocabulary-validation-framework.md`
- `docs/governance/vocabulary-explainability-framework.md`
- `docs/governance/vocabulary-discovery-framework.md`
- `docs/governance/coordinator-v2-foundation-summary.md`
- relevant HTBW contracts
- relevant HTBW models
- relevant E4 issue
- target issue last

## Future Epic Dependencies
| Future Epic | Dependency |
|---|---|
| remaining E4 work | baseline for room-aware and capability-aware discovery behavior |
| E5 | capability-linked discovery depends on capability projection consumption |
| E6 | experience-linked discovery language depends on experience context consumption |
| E7 | continuity/affinity-aware discovery context refinement |
| E8 | restoration-aware discovery context behavior |
| E8a | occupancy-aware and guest-safe discovery behavior |
| E9 | routing-aware discovery explanation linkage |
| E10 | diagnostics/explainability integration for discovery outcomes |
| E13 | productivity discovery language in room context |
| E14 | household coordination discovery language across scopes |

## Readiness Statement
Vocabulary Discovery Framework is READY.

This document is the baseline architecture authority for room-aware vocabulary discovery and "What Can I Say Here?" behavior.