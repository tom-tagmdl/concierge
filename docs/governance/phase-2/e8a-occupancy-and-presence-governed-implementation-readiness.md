# E8a Occupancy and Presence Governed Implementation Readiness

## Issue

#201 — P2-B10 E8a Occupancy and Presence Governed Implementation Readiness

## Purpose

Document durable E8a readiness determination.

Occupancy and Presence remain governed context signals.

## Authority Order Applied

The review followed this authority order:

1. ADR
2. Contract
3. Model
4. Existing Implementation
5. GitHub Issue

GitHub Issues were treated as execution inputs, not architecture authority.

## E15 Governance Applied

E15-G1 through E15-G4 were applied.

The review preserved authority order, the standard implementation prompt header, the issue execution review checklist, and the cross-repo ownership drift checklist.

## Governance Assessment

PASS. E8a Occupancy and Presence is ready for governed implementation execution.

The review found occupancy and presence governance boundaries to be explicit and external, Voice Identity ownership to remain separate, continuity and affinity boundaries to remain distinct, privacy and multi-occupant boundaries to remain bounded, and no blocking conflict in the reviewed architecture, contract, model, or implementation evidence.

## Validation Checklist

| Category | Status | Evidence |
|---|---|---|
| Architecture Alignment | PASS | Reviewed the occupancy/presence architecture chain OP1 through OP9, which preserves external occupancy and presence authority and defines Concierge as a consumer/orchestrator, not an authority source. |
| Contract Alignment | PASS | Reviewed the Occupancy and Presence Contract, Person Continuity and Affinity Contract, Occupancy and Presence explainability/diagnostics support artifacts, and privacy/guest-safe memory boundaries. No authority transfer was identified. |
| Model Alignment | PASS | Reviewed the Occupancy and Presence Model, Person Continuity Model, Person Continuity and Affinity Model, Person Profile state, and related consumption models. All remain consumption models with external authority preserved. |
| Ownership Alignment | PASS | HTBW retains architecture, ADRs, contracts, models, governance, and canonical definitions. Concierge remains a consumer/orchestrator of occupancy and presence context. Voice Identity retains attribution, confidence, and lifecycle. Occupancy and presence own nothing. |
| Existing Implementation Alignment | PASS | Current Concierge implementation already exposes person profile state, voice profile linkage, occupancy/presence-related person metadata, service orchestration, coordinator-backed activity logging, and diagnostics surfaces that E8a can extend without redefining authority. |
| Occupancy Governance Alignment | PASS | Occupancy remains a governed context signal. It may indicate occupied, unoccupied, uncertain, or multi-occupant context, but it is not identity, attribution, continuity, affinity, or permission authority. |
| Presence Governance Alignment | PASS | Presence remains a governed context signal. It may indicate room participation or occupancy context, but it is not identity, attribution, permission, or canonical resident authority. |
| Room Context Boundary Alignment | PASS | Occupancy may be consumed for room context, room activity, room awareness, routing context, planning context, and explainability context; presence may be consumed for room participation context, occupancy context, room readiness context, planning/routing context, and guest-safe behavior. |
| Voice Identity Boundary Alignment | PASS | Voice Identity remains authoritative for attribution, confidence, and lifecycle. Occupancy and presence may consume Voice Identity outputs where governed, but they do not own speaker identity, attribution, confidence, or enrollment. |
| Continuity Boundary Alignment | PASS | Consumed #199 and validated that continuity remains continuity, occupancy remains occupancy, and presence remains presence. Occupancy and presence do not collapse into continuity, and continuity does not become occupancy. |
| Affinity Boundary Alignment | PASS | Consumed #199 and validated that affinity remains affinity, occupancy remains occupancy, and presence remains presence. Occupancy and presence do not collapse into affinity, and affinity does not become occupancy. |
| Privacy Boundary Alignment | PASS | Privacy, retention, household-memory, guest-safe, and unknown-occupant boundaries remain external. E8a does not introduce protected trait inference, ungoverned profiling, permanent identity records, occupancy-driven identity creation, or presence-driven memory authority. |
| Multi-Occupant Boundary Alignment | PASS | Reviewed multi-occupant conflict behavior and guest/unknown handling. Occupancy conflict handling remains governed and does not create person authority. |
| Explainability Alignment | PASS | Occupancy and presence decisions must remain explainable through bounded rationale and lineage references. Diagnostics and explainability surfaces expose rationale without creating new authority. |
| Home Assistant Standards Alignment | PASS | Future E8a implementation must remain Home Assistant-native. Generic HTML, custom UI frameworks, custom form systems, and non-native UI patterns are not approved. |
| Repository Pattern Reuse | PASS | Reuse contract-first service handling, coordinator activity/timeline logging, room-context consumption patterns, occupancy/presence explainability and diagnostics frameworks, and existing person/room/presence handling where available. |
| Dependency Validation | PASS | #199 and #200 were consumed directly as required. The durable E7 and E8 artifacts, plus the occupancy/presence governance baseline artifacts, were also consumed. No unresolved dependency blocker was identified. |
| Implementation Sequencing | PASS | The approved sequence is bounded by authority order, occupancy governance, presence governance, room context boundaries, Voice Identity boundaries, continuity separation, affinity separation, privacy boundaries, guest-safe behavior, multi-occupant conflict behavior, explainability, diagnostics surfaces, repository reuse, HA-native standards, and final ownership review. |
| Closure Readiness | PASS | Issue #201 contains enough governed evidence for Tom to close after review. No code was implemented as part of this readiness issue. |

## E8a Scope Review

Validated E8a scope:

- occupancy governance and consumption architecture
- presence governance and consumption architecture
- room context boundaries
- guest-safe behavior
- multi-occupant behavior
- explainability and diagnostics surfaces
- privacy-safe participation
- continuity and affinity separation
- final ownership drift review

E8a is bounded to approved tracker work under #191 and does not require roadmap expansion.

## Occupancy Governance Review

Occupancy remains a governed context signal.

Occupancy may indicate occupied, unoccupied, uncertain, or multi-occupant state, but it does not become identity, attribution, continuity, affinity, or permission authority.

Relevant occupancy artifacts reviewed:

- docs/governance/occupancy-presence-consumption-architecture.md
- docs/governance/occupancy-resolution-pipeline.md
- docs/governance/room-aware-occupancy-consumption.md
- docs/governance/occupancy-presence-influence-matrix.md
- docs/governance/occupancy-presence-explainability-framework.md
- docs/governance/occupancy-presence-diagnostics-surface.md
- docs/governance/occupancy-presence-consumption-readiness-review.md

## Presence Governance Review

Presence remains a governed context signal.

Presence may indicate room participation context or occupancy context, but it does not become identity, attribution, permission, or canonical resident authority.

Relevant presence artifacts reviewed:

- docs/governance/occupancy-presence-consumption-architecture.md
- docs/governance/presence-resolution-pipeline.md
- docs/governance/occupancy-presence-influence-matrix.md
- docs/governance/occupancy-presence-explainability-framework.md
- docs/governance/occupancy-presence-diagnostics-surface.md
- docs/governance/occupancy-presence-consumption-readiness-review.md

## Room Context Boundary Review

Occupancy may be consumed for room context, room activity, room awareness, routing context, planning context, and explainability context.

Presence may be consumed for room participation context, occupancy context, room readiness context, planning and routing context, and guest-safe behavior.

Occupancy and presence may not be used as identity proof, speaker attribution, person authority, permission determination, permanent room ownership, guest identity determination, or canonical resident identity.

## Voice Identity Boundary Review

Voice Identity remains authoritative for attribution, confidence, and lifecycle.

Occupancy and presence do not own speaker identity, speaker attribution, confidence, or enrollment.

Occupancy and presence may consume Voice Identity outputs where governed, but they may not replace Voice Identity.

## Continuity Boundary Review

Consumed #199 and validated continuity governance boundaries.

Continuity remains continuity, occupancy remains occupancy, and presence remains presence.

These concepts must not collapse together.

## Affinity Boundary Review

Consumed #199 and validated affinity governance boundaries.

Affinity remains affinity, occupancy remains occupancy, and presence remains presence.

These concepts must not collapse together.

## Privacy Boundary Review

Privacy boundaries remain governed by HTBW privacy, retention, and household-memory rules.

E8a does not introduce ungoverned profiling, permanent identity records, occupancy-driven identity creation, presence-driven memory authority, or protected trait inference.

## Multi-Occupant Boundary Review

Reviewed multi-occupant conflict behavior and guest/unknown handling.

Occupancy conflict handling remains governed and deterministic.

Occupancy does not create person authority.

## Explainability Review

Occupancy and presence decisions must remain explainable through bounded rationale and lineage references.

Diagnostics and explainability surfaces may expose the rationale, but they do not create new authority.

## ADR Alignment Review

Reviewed ADRs:

- ADR-012 Occupancy and Presence Governance Boundaries
- ADR-007 Experience Model Governance Boundaries
- ADR-013 Concierge V1 Household-Facing Outcome Preservation Governance

No conflicts were found.

## Contract Alignment Review

Reviewed contracts:

- Occupancy and Presence Contract
- Person Continuity and Affinity Contract
- Experience Restoration Contract
- Experience Projection Contract
- Household Memory Contract references where relevant

No conflicts were found.

## Model Alignment Review

Reviewed models:

- Occupancy and Presence Model
- Person Continuity Model
- Person Continuity and Affinity Model
- Experience Model
- Person Profile state in Concierge models

No model ownership drift was identified.

## Existing Implementation Review

Implementation evidence reviewed:

- custom_components/concierge/services.py
- custom_components/concierge/coordinator.py
- custom_components/concierge/models.py
- custom_components/concierge/config_flow.py
- custom_components/concierge/panel.py
- custom_components/concierge/diagnostics.py
- custom_components/concierge/enrollment_orchestrator.py
- custom_components/concierge/enrollment_session.py
- custom_components/concierge/enrollment_storage.py

Additional governance evidence reviewed:

- docs/governance/occupancy-presence-consumption-architecture.md
- docs/governance/occupancy-resolution-pipeline.md
- docs/governance/presence-resolution-pipeline.md
- docs/governance/room-aware-occupancy-consumption.md
- docs/governance/multi-occupant-context-consumption.md
- docs/governance/multi-occupant-restoration-conflict-policy.md
- docs/governance/occupancy-presence-influence-matrix.md
- docs/governance/occupancy-presence-explainability-framework.md
- docs/governance/occupancy-presence-diagnostics-surface.md
- docs/governance/occupancy-presence-consumption-readiness-review.md
- docs/governance/privacy-retention-and-guest-safe-memory-boundaries.md
- docs/governance/phase-2/e7-continuity-and-affinity-governed-implementation-readiness.md
- docs/governance/phase-2/e8-restoration-governed-implementation-readiness.md

The implementation can proceed by extending existing patterns rather than creating competing implementation patterns.

## Home Assistant Standards Review

Future E8a implementation must remain Home Assistant-native.

Authoritative reference:

https://developers.home-assistant.io/

Future implementation must use:

- Home Assistant service patterns where applicable
- Home Assistant config flow patterns where applicable
- Home Assistant options flow patterns where applicable
- Home Assistant selectors where applicable
- Home Assistant diagnostics patterns where applicable
- Home Assistant repairs where applicable
- Home Assistant translations
- Home Assistant accessibility expectations
- Existing repository UI/configuration patterns

The following are not approved:

- Generic HTML
- Custom web UI frameworks
- Custom form systems
- Non-native Home Assistant UI behavior
- Ad hoc frontend patterns

## Repository Pattern Reuse Review

Future E8a implementation should reuse:

- Contract-first service handling
- Coordinator activity/timeline logging
- Room-context consumption patterns
- Occupancy and presence explainability frameworks
- Occupancy and presence diagnostics surface patterns
- Continuity and affinity separation patterns from E7 where relevant
- Privacy-safe guest and household-memory boundary patterns
- HA-native config flow selectors
- Diagnostics and telemetry projection
- Existing person/room/presence handling where available

## Recommended E8a Implementation Order

Approved governed implementation sequence:

1. Confirm authority order.
2. Confirm occupancy governance.
3. Confirm presence governance.
4. Confirm room context boundaries.
5. Confirm Voice Identity boundaries.
6. Confirm continuity separation.
7. Confirm affinity separation.
8. Confirm privacy boundaries.
9. Confirm guest-safe behavior.
10. Confirm multi-occupant conflict behavior.
11. Confirm explainability.
12. Validate diagnostics surfaces.
13. Validate occupancy/presence consumption paths.
14. Validate repository pattern reuse.
15. Validate HA-native standards.
16. Final ownership review.
17. Prepare closure evidence.

## Blockers

No blockers identified.

## Risks

- Occupancy could drift into identity inference.
- Presence could drift into permission authority.
- Continuity or affinity boundaries could blur into occupancy semantics.
- Privacy boundaries could be underspecified.
- Non-native UI shortcuts could creep in during future implementation.

These are risks, not blockers.

## PASS / FAIL Determination

PASS.

Issue #201 satisfies governed implementation readiness.

E8a Occupancy and Presence is approved for governed implementation execution.

Issue #201 is ready for Tom to close after review.

## Recommended Closing Comment

PASS. Issue #201 followed the required authority order (ADR -> Contract -> Model -> Existing Implementation -> GitHub Issue), applied E15-G1 through E15-G4, validated architecture alignment, contract alignment, model alignment, ownership alignment, existing implementation alignment, occupancy governance alignment, presence governance alignment, room context boundary alignment, Voice Identity boundary alignment, continuity boundary alignment, affinity boundary alignment, privacy boundary alignment, multi-occupant boundary alignment, explainability alignment, Home Assistant standards alignment, repository pattern reuse, dependency readiness, implementation sequencing, and closure readiness, and did not implement code.

E8a Occupancy and Presence is ready for governed implementation execution. Occupancy and presence remain governed context signals and do not become identity or memory authority. No generic HTML or non-native UI approach is approved. Recommended next issue: #202 — P2-B11 Release 3 Continuity Restoration Occupancy Build Execution Plan.

## Recommended Next Issue

#202 — P2-B11 Release 3 Continuity Restoration Occupancy Build Execution Plan

Use tracker #191.

Do not guess.

## Future Implementation Grounding

Future E8a implementation must preserve:

- Occupancy governance
- Presence governance
- Voice Identity ownership
- Continuity governance
- Affinity governance
- Privacy governance
- Multi-occupant policies
- Guest-safe behavior
- Home Assistant-native standards
- Existing repository pattern reuse
- No generic HTML
- No identity inference
- No occupancy-as-identity
- No ownership drift