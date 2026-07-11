# Architecture Guardrails

These guardrails keep Concierge implementation aligned with platform architecture.

## Coordinator V2 Foundation Grounding

Before Coordinator V2 implementation work, read:

- docs/governance/coordinator-v2-foundation-summary.md

This file summarizes the authoritative E3 Coordinator Foundation baseline and must be used before implementation work that touches Coordinator context, capability resolution, experience resolution, planning, explainability, diagnostics, routing, or execution-envelope handling.

## Room Vocabulary Consumption Grounding

Before E4 implementation work read:

- docs/governance/room-vocabulary-consumption-architecture.md

Coordinator consumes room vocabulary.

Coordinator does not own room vocabulary.

## Runtime Vocabulary Resolution Grounding

Before E4 runtime vocabulary implementation work read:

- docs/governance/runtime-vocabulary-resolution-architecture.md

Coordinator consumes and resolves vocabulary.

Coordinator does not own vocabulary.

## Room Context Vocabulary Consumption Grounding

Before E4 room-context work read:

- docs/governance/room-context-aware-vocabulary-consumption-architecture.md

Coordinator consumes room context.

Coordinator does not own room context.

## Merged Room Vocabulary Consumption Grounding

Before E4 merged-room vocabulary work read:

- docs/governance/merged-room-vocabulary-consumption-architecture.md

Coordinator consumes merged-room vocabulary and scope definitions.

Coordinator does not own merged-room governance or membership.

## Composite Room Vocabulary Consumption Grounding

Before E4 composite-room vocabulary work read:

- docs/governance/composite-room-vocabulary-consumption-architecture.md

Coordinator consumes composite-room, zone, floor, and hierarchy scope definitions.

Coordinator does not own composite-room, zone, floor, or hierarchy governance.

## Vocabulary Validation Grounding

Before E4 vocabulary validation work read:

- docs/governance/vocabulary-validation-framework.md

Coordinator validates vocabulary consumption outcomes.

Coordinator does not validate governance ownership.

## Vocabulary Explainability Grounding

Before E4 vocabulary explainability work read:

- docs/governance/vocabulary-explainability-framework.md

Coordinator explains vocabulary consumption outcomes.

Coordinator does not explain governance ownership.

## Vocabulary Discovery Grounding

Before E4 vocabulary discovery work read:

- docs/governance/vocabulary-discovery-framework.md

Coordinator provides room-aware and capability-aware vocabulary discovery.

Coordinator does not expose governance internals or platform internals.

## Vocabulary Diagnostics Grounding

Before E4 vocabulary diagnostics work read:

- docs/governance/vocabulary-diagnostics-framework.md

Coordinator exposes diagnostics for vocabulary consumption behavior.

Coordinator does not diagnose governance authority.

## E4 Readiness Review Grounding

Before beginning E5 work read:

- docs/governance/e4-vocabulary-consumption-readiness-review.md

E5 may only begin after E4 readiness approval.

## Concierge V1 Outcome Preservation Grounding

Before E3a or Coordinator V2 implementation work that may affect existing household-facing outcomes, read:

- docs/governance/coordinator-v2-foundation-summary.md
- docs/governance/concierge-v1-outcome-preservation-baseline.md

Before implementation that may affect merged-room behavior, read:

- docs/governance/concierge-v1-outcome-preservation-baseline.md
- docs/governance/merged-room-outcome-preservation-contract.md

Before implementation that may affect composite-room, floor-scope, zone-scope, whole-house-scope, or hierarchy traversal behavior, read:

- docs/governance/concierge-v1-outcome-preservation-baseline.md
- docs/governance/merged-room-outcome-preservation-contract.md
- docs/governance/composite-room-scope-outcome-preservation-contract.md

Before implementation that may affect execution hierarchy, room-level execution, merged-room execution, composite-room execution, floor-level execution, or whole-house execution behavior, read:

- docs/governance/concierge-v1-outcome-preservation-baseline.md
- docs/governance/merged-room-outcome-preservation-contract.md
- docs/governance/composite-room-scope-outcome-preservation-contract.md
- docs/governance/execution-hierarchy-outcome-preservation-contract.md

Before implementation that may affect global context, home status, occupancy references, shared context, environmental context, platform state, signals, or household-summary behavior, read:

- docs/governance/concierge-v1-outcome-preservation-baseline.md
- docs/governance/global-context-outcome-preservation-contract.md

Before implementation that may affect any preserved V1 household-facing outcome, read:

- docs/governance/concierge-v1-outcome-preservation-baseline.md
- docs/governance/v1-to-v2-capability-parity-matrix.md
- docs/governance/v1-outcome-regression-checklist.md

Before beginning E4 or any post-E3a implementation work, review:

- docs/governance/v1-preservation-readiness-review.md

Preserve household-facing outcomes.

Do not preserve implementation details unless explicitly required by a later issue.

## Non-Negotiable Rules

- Home Assistant Area registry remains the room source of truth.
- Concierge room state is extension data keyed by `area_id`, not a parallel room registry.
- UI must use Home Assistant-native dialog patterns (`ha-dialog`) rather than custom dialog frameworks.
- UI control decisions must start from official Home Assistant references before any fallback implementation is chosen.
- New lifecycle services must include regression tests for state transitions.
- Room language and voice selectors must use Home Assistant provider capability metadata as the single source of truth; Concierge must not maintain a static or duplicate TTS language/voice catalog.

## Canonical UI References

Review these sources first whenever adding or changing controls, selectors, dialogs, or TTS flows:

- Frontend architecture and patterns: https://developers.home-assistant.io/docs/frontend/
- Official selector reference: https://www.home-assistant.io/docs/blueprint/selectors/
- Selector component behavior demos: https://design.home-assistant.io/#components/ha-selector
- TTS building block behavior and constraints: https://www.home-assistant.io/integrations/tts/

If Concierge cannot directly use the documented Home Assistant pattern in the custom panel surface, document the reason in `docs/development/architecture-exceptions.md` and use the closest stable fallback.

## Required PR Checks

- Architecture impact reviewed and documented.
- Canonical Home Assistant docs were consulted for UI/control changes before choosing a fallback.
- Exceptions documented with owner and expiry in `docs/development/architecture-exceptions.md`.
- `scripts/validate_architecture_guardrails.py` passes.
- Test coverage added or updated for changed lifecycle behavior.
