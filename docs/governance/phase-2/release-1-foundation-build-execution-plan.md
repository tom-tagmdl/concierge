# Release 1 Foundation Build Execution Plan

## Issue

Reference:

#195 — P2-B4 Release 1 Foundation Build Execution Plan

Tracker:

#191 — Phase 2 Concierge V2 Governed Implementation Tracker

Consumed readiness gates:

#192 — P2-B1 E3 Foundation Governed Implementation Readiness
#193 — P2-B2 E3a Preservation Governed Implementation Readiness
#194 — P2-B3 E4 Vocabulary Governed Implementation Readiness

## Purpose

This artifact preserves the durable Phase 2 Release 1 execution plan.

This is an execution-planning artifact, not an implementation artifact.

It does not authorize code outside governed implementation issues.

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

## Consumed Readiness Outcomes

### E3 Foundation / #192

Consumed and preserved approved foundation order:

1. CF1 Runtime Boundary
2. CF2 Context Assembly
3. CF3 Capability Resolution
4. CF4 Experience Resolution
5. CF5 Planning
6. CF6 Explainability
7. CF7 Diagnostics
8. CF8 Routing
9. CF9 Execution Envelope
10. CF10 Readiness Review

### E3a Preservation / #193

Consumed and preserved preservation sequence:

1. Preservation baseline
2. Merged-room preservation
3. Composite/scope preservation
4. Execution hierarchy preservation
5. Global/fallback context preservation
6. Parity mapping
7. Diagnostics/explainability for preserved outcomes
8. Preservation regression checklist
9. Ownership validation
10. Final preservation evidence

### E4 Vocabulary / #194

Consumed and preserved vocabulary sequence:

1. Room vocabulary consumption
2. Device/entity vocabulary consumption where applicable
3. Asset vocabulary consumption
4. Asset Intelligence handoff boundary
5. Vocabulary discovery
6. Vocabulary validation
7. Vocabulary diagnostics
8. Vocabulary explainability
9. Readiness/regression validation
10. Final ownership review

## Release 1 Execution Order

Approved governed Release 1 implementation sequence:

1. Establish Coordinator V2 runtime boundary.
2. Implement request/context assembly.
3. Implement capability resolution.
4. Implement experience resolution.
5. Implement intent-to-plan planning.
6. Implement explainability foundation.
7. Implement diagnostics foundation.
8. Implement routing foundation.
9. Implement execution envelope.
10. Validate E3 foundation readiness.
11. Apply E3a outcome preservation overlays.
12. Validate merged-room behavior preservation.
13. Validate composite/scope behavior preservation.
14. Validate execution hierarchy preservation.
15. Validate global/fallback context preservation.
16. Apply parity matrix checks.
17. Apply preservation regression checklist.
18. Implement E4 vocabulary consumption.
19. Implement device/entity vocabulary consumption where applicable.
20. Implement asset vocabulary consumption.
21. Preserve Asset Intelligence handoff boundary.
22. Implement vocabulary discovery.
23. Implement vocabulary validation.
24. Implement vocabulary diagnostics.
25. Implement vocabulary explainability.
26. Perform Release 1 ownership review.
27. Perform Release 1 Home Assistant standards review.
28. Perform Release 1 regression/readiness validation.
29. Prepare Release 1 closure evidence.

This order preserves the dependency chain across E3, E3a, and E4.

Device/entity vocabulary is treated as an implementation sub-step within existing room/entity/device resolution surfaces unless future authoritative governance says otherwise.

## Release 1 Validation Checkpoints

Validation checkpoints are required for:

- Authority order validation
- Ownership validation
- E3 foundation validation
- E3a preservation validation
- E4 vocabulary validation
- Asset Intelligence boundary validation
- Home Assistant standards validation
- Repository pattern reuse validation
- Diagnostics validation
- Explainability validation
- Regression validation
- Closure readiness validation

## Release 1 Closure Criteria

Release 1 may be considered complete only when all of the following are true:

- All implementation issues are completed.
- All validation checkpoints pass.
- No ADR conflicts remain.
- No contract conflicts remain.
- No model conflicts remain.
- No ownership drift remains.
- No generic HTML or non-native UI behavior is introduced.
- Asset Intelligence ownership remains preserved.
- Vocabulary remains consumption/resolution only.
- Preservation outcomes are validated.
- Home Assistant dev environment validation is completed using the existing push script, where applicable.
- Tom’s Home Assistant runtime observations are captured where runtime validation is required.
- Durable governance artifacts are updated.

## Ownership Boundary Review

Release 1 preserves ownership boundaries across:

- HTBW: architecture, ADRs, contracts, models, governance, canonical definitions
- Concierge: consumption, resolution, planning, routing, orchestration, execution
- Voice Identity: attribution, confidence, voice identity lifecycle
- Asset Intelligence: asset evaluation, environmental evaluation, asset significance, asset metadata authority

Release 1 planning must fail if ownership drifts.

## Home Assistant Standards Review

Future Release 1 implementation must remain Home Assistant-native.

Authoritative reference:

https://developers.home-assistant.io/

Future implementation must use:

- Home Assistant selectors
- Home Assistant config flow patterns
- Home Assistant options flow patterns
- Home Assistant diagnostics patterns where applicable
- Home Assistant translation patterns
- Home Assistant accessibility expectations
- Existing repository UI/configuration patterns

The following are prohibited:

- Generic HTML
- Custom web UI frameworks
- Custom form systems
- Non-native Home Assistant UI behavior
- Ad hoc frontend patterns

## Repository Pattern Reuse

Future Release 1 implementation should reuse:

- Contract-first service handling
- Coordinator activity/timeline logging
- HA-native config flow selectors
- Options flow patterns
- Diagnostics and telemetry projection
- Built-in panel registration where applicable
- Room/entity/device cataloging through existing runtime surfaces
- Asset Intelligence handoff boundary diagnostics
- Vocabulary discovery, validation, explainability, and diagnostics frameworks
- Preservation regression checklist

## Blockers

No blockers identified.

## Risks

Risks are distinct from blockers.

- Future implementation could blur entity/device references into ownership if boundary language is not preserved.
- E4/E5 or vocabulary/capability boundaries could drift if discovery or diagnostics start interpreting downstream capability meaning.
- Non-native UI shortcuts could creep in if future implementation ignores HA-native patterns.

## PASS / FAIL Determination

PASS

Release 1 is approved to proceed into governed implementation issue execution.

## Recommended Closing Comment

PASS. Issue #195 followed the required authority order (ADR -> Contract -> Model -> Existing Implementation -> GitHub Issue), applied E15-G1 through E15-G4, validated architecture alignment, contract alignment, model alignment, ownership alignment, existing implementation alignment, vocabulary boundary alignment, Asset Intelligence ownership preservation, Home Assistant standards alignment, repository pattern reuse, dependency readiness, implementation sequencing, and closure readiness, and did not implement code.

Release 1 is approved to proceed into governed implementation issue execution. No generic HTML or non-native UI approach is approved. Asset Intelligence ownership remains preserved. Vocabulary remains consumption/resolution only. The Release 1 closure target is Issue #195.

Recommended next issue: the first Release 1 implementation issue under the approved sequence for E3 Foundation work, as governed by the tracker.

## Recommended Next Issue

The next Phase 2 issue is #196 — P2-B5 E5 Capability Governed Implementation Readiness.

Tracker #191 governs that next step; Release 1 execution planning is complete with #195, and the next Phase 2 issue is the first E5 readiness gate.

## Future Implementation Grounding

Future Release 1 implementation issues must read this artifact before implementation begins.

Future implementation must preserve:

- HTBW authority order
- E15-G1 through E15-G4
- Release 1 execution order
- E3 foundation sequencing
- E3a outcome preservation
- E4 vocabulary consumption boundaries
- Asset Intelligence ownership boundaries
- Home Assistant-native UI/configuration standards
- Existing repository pattern reuse
- No generic HTML
- No implementation guessing
- No ownership drift