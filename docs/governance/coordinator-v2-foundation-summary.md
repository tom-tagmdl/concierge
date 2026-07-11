# Coordinator V2 Foundation Summary

## Purpose
This document is the required implementation grounding artifact for all Coordinator V2 implementation work.

It summarizes the completed E3 Coordinator V2 Foundation baseline (CF1 through CF10) and provides the quick-start authority map for future implementation sessions.

This summary does not replace:
- HTBW ADRs
- HTBW contracts
- HTBW models
- Concierge runtime architecture
- issue-specific acceptance criteria

It is a consolidation and reference guide for implementation grounding.

## How To Use This Document
Before implementation work on any Coordinator V2 issue:
- read this file first
- read the related CF issue baseline comment
- read the relevant HTBW contracts and models
- read the target issue last
- do not implement behavior that violates this summary

## Authority Order
ADRs
  -> Contracts
  -> Models
  -> Existing implementation
  -> GitHub issue

GitHub issues are execution plans, not architecture authority.

## Coordinator V2 Core Role
Coordinator V2 is:
- orchestration authority
- runtime coordination authority
- planning authority
- routing preparation authority
- envelope production authority
- diagnostic and explainability producer

Coordinator V2 is NOT:
- governance authority
- contract authority
- model authority
- source-of-truth authority
- identity authority
- occupancy authority
- provenance authority
- provider authority

## CF1 Runtime Boundary Summary
CF1 establishes Coordinator V2 as a bounded orchestration and consumption runtime.

Core rights:
- orchestrate runtime decisions
- coordinate workflow and sequencing
- prepare explainable outcomes

Core non-rights:
- no governance ownership
- no contract or model ownership
- no source-of-truth ownership

Relationship summary:
- Foundation remains truth authority
- Asset Intelligence remains asset significance/reasoning authority
- Voice Identity remains identity and confidence authority

## CF2 Context Assembly Summary
Deterministic context assembly order:
1. Room Context
2. Room Vocabulary Context
3. Capability Context
4. Person Context
5. Person Continuity Context
6. Person-Room Affinity Context
7. Occupancy Context
8. Time Context
9. Home State Context
10. Asset Intelligence Context
11. Experience Context
12. Final Orchestration Context

Rule: this order is fixed and must not be bypassed.

## CF3 Capability Resolution Summary
Deterministic capability resolution order:
1. Room Capability Discovery
2. Room Vocabulary Filtering
3. Capability Projection Eligibility
4. Occupancy and Presence Filtering
5. Person-Specific Filtering
6. Continuity and Affinity Filtering
7. Guest-Safe Filtering
8. Unavailable Capability Elimination
9. Unsupported Capability Elimination
10. Resolved Capability Set

Rule: Coordinator consumes projection authority and must not redefine capability ownership.

## CF4 Experience Resolution Summary
Deterministic experience resolution order:
1. Capability Eligibility Validation
2. Experience Discovery
3. Occupancy Eligibility Filtering
4. Person Eligibility Filtering
5. Continuity Filtering
6. Memory-Aware Filtering
7. Guest-Safe Filtering
8. Experience Classification
9. Experience Prioritization
10. Resolved Experience Set

Rule: Coordinator consumes experience authority and must not redefine experience ownership.

## CF5 Planning Summary
Deterministic planning order:
1. Experience Validation
2. Room Target Resolution
3. Person Target Resolution
4. Capability Target Resolution
5. Execution Sequence Construction
6. Constraint Evaluation
7. Plan Classification
8. Plan Explainability Construction
9. Plan Finalization
10. Execution Plan

Canonical execution plan fields:
- plan_id
- timestamp
- context_reference
- experience_reference
- capability_references
- room_target
- person_target
- execution_sequence
- constraint_evaluation
- explainability_references
- provenance_references
- plan_classification

## CF6 Explainability Summary
CF6 requires:
- machine-readable explanations
- human-readable explanations
- why and why-not explanations
- canonical reason codes
- provenance linkage
- household memory relationship
- restoration relationship

Rule: explanation production must remain deterministic and traceable.

## CF7 Diagnostics Summary
Diagnostics categories:
- Request Trace
- Context Trace
- Capability Trace
- Experience Trace
- Planning Trace
- Explainability Trace
- Routing Trace
- Execution Trace
- Constraint Trace
- Health Trace

Rule: diagnostics must support deterministic troubleshooting and operational supportability.

## CF8 Routing Summary
Deterministic routing order:
1. Message Eligibility Validation
2. Room Routing Resolution
3. Person Routing Resolution
4. Occupancy-Aware Routing
5. Guest-Safe Routing
6. Delivery Scope Resolution
7. Delivery Target Construction
8. Routing Explainability Construction
9. Routing Validation
10. Resolved Delivery Target Set

Delivery scopes:
- room-scoped
- person-scoped
- household-scoped
- broadcast-scoped
- private-scoped

Rule: routing does not own content, messaging providers, or notification providers.

## CF9 Execution Envelope Summary
Canonical execution envelope fields:
- envelope_id
- generated_timestamp
- context_reference
- capability_references
- experience_reference
- execution_plan_reference
- explainability_references
- provenance_references
- occupancy_reference
- memory_reference
- envelope_classification

Execution envelope lifecycle:
1. Created
2. Populated
3. Validated
4. Classified
5. Finalized
6. Routed
7. Archived

Rule: envelope is the canonical downstream handoff artifact and must not be mutated after finalization.

## CF10 Readiness Summary
Readiness review outcome:
- CF1 through CF9 passed
- no ownership drift identified
- no blocking gaps identified
- E4, E5, E6 may begin
- downstream E7, E8, E8a, E9, E10, E13, E14 are unblocked from a foundation perspective

## Downstream Consumption Rules
Concierge may consume HTBW authority.

Concierge may not redefine HTBW authority.

Coordinator may consume:
- Room Vocabulary Registry Model
- Capability Projection Model
- Experience Model
- Person Continuity Model
- Person-Room Affinity Model
- Experience Restoration Context Model
- Occupancy Presence Model
- Provenance Model
- Household Memory Model
- Calendar Experience Model
- Email Experience Model
- Task Experience Model
- Shopping Experience Model
- Knowledge Query Experience Model
- Briefing Composition Model
- Household Coordination Snapshot Model
- Multi-Item Capture Result Model

## Implementation Guardrails
Implementation must not:
- move ownership from HTBW into Concierge
- redefine model semantics
- duplicate provenance fields
- calculate identity confidence
- calculate occupancy truth
- create provider-specific assumptions
- bypass deterministic ordering
- skip explainability
- skip diagnostics
- mutate execution envelopes after finalization

## Required Prompt Prefix For Future Work
Future GitHub Copilot implementation prompts must include:

Before implementation, read:
- docs/governance/coordinator-v2-foundation-summary.md
- the relevant CF issue baseline
- relevant HTBW contracts
- relevant HTBW models
- the target issue last

## Related Issue Map
| Foundation Area | Issue | Purpose |
|---|---|---|
| CF1 | #53 | Runtime Boundary |
| CF2 | #54 | Context Assembly |
| CF3 | #55 | Capability Resolution |
| CF4 | #56 | Experience Resolution |
| CF5 | #57 | Planning |
| CF6 | #58 | Explainability |
| CF7 | #59 | Diagnostics |
| CF8 | #60 | Routing |
| CF9 | #61 | Execution Envelope |
| CF10 | #62 | Readiness Review |

## Future Use
This file must be referenced by:
- E4 Room Vocabulary Consumption
- E5 Capability Projection Consumption
- E6 Experience Consumption
- E7 Continuity and Affinity Consumption
- E8 Experience Restoration Consumption
- E8a Occupancy Consumption
- E9 Messaging and Notification Discipline
- E10 Household Memory and Explainability
- E13 Productivity Experiences
- E14 Household Coordination

## Readiness Statement
Coordinator V2 Foundation is READY for downstream implementation.