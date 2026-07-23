# ADR: Experience Continuity Architecture

## Status
Proposed

## Date
2026-07-21

## Context
Concierge V1 production behavior included continuity outcomes implemented through Home Assistant automations, scripts, helpers, labels, and runtime patterns, not through Concierge integration services. The production reconstruction and parity analysis show that Concierge V2 has strong orchestration and governance surfaces but does not yet preserve several in-scope V1 continuity outcomes.

This ADR establishes Experience Continuity as a first-class Concierge V2 architecture domain to prevent capability loss during production replacement.

## Production V1 Evidence Summary
Primary production baseline is [docs/governance/experience-continuity/v1-capability-reconstruction.md](docs/governance/experience-continuity/v1-capability-reconstruction.md).

Confirmed baseline facts:
- In-scope V1 automations analyzed: 19.
- In-scope V1 scripts analyzed: 42.
- Helper-family entities analyzed: 112.
- Production authority label: Abilities Concierge.
- V2 parity-scope exclusions by user policy:
  - Bedtime (Concierge).
  - Good Morning (Concierge).
  - Goodnight or Good Night (Concierge).

Confirmed V1 capability domains:
- Voice Interaction.
- Room Awareness.
- Lighting Continuity.
- Audio Continuity.
- Media Continuity.
- Monitoring and Sensor Follow-Ups.
- Learning and Preference Memory.
- Guardrails and Soft Failure Handling.
- Experience Continuity.

## V1-to-V2 Parity Summary
Primary parity baseline is [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md).

Matrix outcomes:
- Capability rows: 26.
- PASS: 1.
- PARTIAL: 6.
- GAP: 16.
- REDESIGN: 3.
- SUPERSEDED: 0.
- OUT_OF_SCOPE: 0.
- SCOPE_CONFIRMATION_REQUIRED: 0.
- Install-readiness classification: NOT_READY.

Conclusion from parity evidence: Concierge V2 is not production-install-ready without capability loss unless Experience Continuity gaps are addressed or intentionally scoped out.

## Problem Statement
Current Concierge V2 implementation provides strong foundations for:
- runtime execution and orchestration envelopes in [custom_components/concierge/services.py](custom_components/concierge/services.py).
- service surfaces in [custom_components/concierge/services.yaml](custom_components/concierge/services.yaml).
- room/person/context storage and models in [custom_components/concierge/models.py](custom_components/concierge/models.py) and [custom_components/concierge/storage.py](custom_components/concierge/storage.py).
- governance-boundary projections in [custom_components/concierge/services.py](custom_components/concierge/services.py) and [custom_components/concierge/coordinator.py](custom_components/concierge/coordinator.py).
- fail-closed identity consumption behavior in [custom_components/concierge/services.py](custom_components/concierge/services.py), [tests/test_services.py](tests/test_services.py), [tests/test_foundation.py](tests/test_foundation.py), and [voice_identity/custom_components/voice_identity/services.py](../voice_identity/custom_components/voice_identity/services.py).

However, production V1 evidence shows a behavioral continuity layer not yet fully implemented in V2, including:
- learned comfort and usual state.
- operational state capture and restore.
- media continuation.
- Sonos duck and restore behavior.
- learned lighting and audio posture.
- calm fallback behavior.

This layer must be formalized as a governed architecture domain, not recreated as disconnected YAML-equivalent features.

## Decision
### Decision 1: Experience Continuity Is First-Class
Experience Continuity is a first-class Concierge V2 architecture domain.

It is not only documentation, not only migration bookkeeping, and not a collection of unrelated convenience behaviors.

### Decision 2: Outcome-Based Parity Is Required
Parity with V1 is evaluated by user outcome and behavioral equivalence, not by automation or script name matching.

### Decision 3: Experience Continuity Owns Behavioral Continuity, Not Raw Inventory Ownership
Experience Continuity owns continuity policy and restoration behavior composition.

Ownership boundaries remain:
- Foundation and HTBW own canonical person, room, presence, and identity-related contracts and models where defined in [homes_that_behave_well/docs/contracts/person-identity-contract.md](../homes_that_behave_well/docs/contracts/person-identity-contract.md), [homes_that_behave_well/docs/contracts/occupancy-and-presence-contract.md](../homes_that_behave_well/docs/contracts/occupancy-and-presence-contract.md), and [homes_that_behave_well/docs/contracts/room-awareness-contract.md](../homes_that_behave_well/docs/contracts/room-awareness-contract.md).
- Concierge owns runtime orchestration and user-facing behavior in [custom_components/concierge/services.py](custom_components/concierge/services.py).
- Voice Identity owns attribution and confidence outcomes in [voice_identity/custom_components/voice_identity/services.py](../voice_identity/custom_components/voice_identity/services.py).
- Asset Intelligence owns asset stewardship and advisory semantics in [asset_intelligence/custom_components/asset_intelligence/advisory.py](../asset_intelligence/custom_components/asset_intelligence/advisory.py).

### Decision 4: State Capture and Restore Must Be Explicit
V2 must explicitly model state capture and restore. Continuity behavior cannot depend on incidental platform behavior.

Continuity state categories:
- learned usual state.
- captured operational snapshot.
- platform-native restore participation.
- scene-based restore participation.
- generated safe fallback default.

### Decision 5: Preference Resolution Hierarchy
Unless superseded by future authority, Experience Continuity resolves behavior in this order:
1. Explicit current command.
2. Safety or policy guardrail.
3. Known person preference.
4. Optional explicit person plus room preference exception (not default).
5. Room default.
6. Household default.
7. System safe default.

For music affinity and preference signals (preferred artist/genre/album/playlist), person-scoped preference is the default portable model across rooms. Person-plus-room music preference is an explicit exception path only when future authority/configuration requires it.

Required handling contexts:
- known person.
- guest.
- unknown speaker.
- low-confidence speaker.
- unavailable Voice Identity.
- room-only context.
- no-room context.

### Decision 6: Identity Confidence Must Fail Closed
Individualized continuity behavior fails closed when identity is unknown, low confidence, unavailable, or not permitted.

Policy outcomes:
- known high-confidence identity may apply person-specific preferences.
- unknown and low-confidence identity use room or household defaults.
- guest mode suppresses personalized learning and personalization unless explicitly allowed.
- absent Voice Identity must not block safe room-default behavior.

This aligns with fail-closed service behavior in [voice_identity/custom_components/voice_identity/services.py](../voice_identity/custom_components/voice_identity/services.py) and Concierge consumption logic in [custom_components/concierge/services.py](custom_components/concierge/services.py).

### Decision 7: Learning Boundaries
Learning is governed and bounded:
- automatic learning is allowed only where explicitly governed.
- intentional learning is preferred for durable personal preferences.
- guest, unknown, and low-confidence contexts must not commit personalized learning.
- learning must be asynchronous and non-blocking for interaction flow.
- learning outputs must be explainable and reversible.
- room-level defaults may be learned when identity is unavailable.
- person-level learning requires identity confidence and policy permission.

### Decision 8: Sonos Is the Voice of the Room Unless Superseded by Future ADR
Based on production V1 evidence in [docs/governance/experience-continuity/v1-capability-reconstruction.md](docs/governance/experience-continuity/v1-capability-reconstruction.md), Sonos remains the default room voice output path for continuity speech behavior unless future authority changes this.

Rules:
- voice assistants are sensors and interaction entry points.
- Sonos speakers are primary room output devices.
- output routes through room-audio resolution behavior.
- fallback paths are required when Sonos is unavailable.
- TTS must not fight active music.
- duck and restore behavior must be explicit and testable.

### Decision 9: Media Continuity Is Separate From TTS Ducking
The following are separate continuity capabilities and must remain architecturally distinct:
- speech ducking for TTS interactions.
- media continuation and resume.
- play genre, artist, and album behavior.
- last-media capture.
- follow-me or cross-room behavior.
- manual-stop cooldown policy.

### Decision 10: Production Installation Requires an Experience Continuity Gate
Concierge V2 cannot replace in-scope V1 Abilities Concierge behavior in production until the Experience Continuity install gate passes or the user explicitly scopes out missing behaviors.

Minimum gate evaluations:
1. learned or usual lighting behavior.
2. room-aware play jazz or play genre behavior.
3. room-aware continue or resume behavior.
4. Sonos ducking and restoration behavior.
5. room capability discovery.
6. monitoring follow-up responses.
7. guest, unknown, and low-confidence safe defaults.
8. silence-is-success fallback behavior.
9. person-aware preference readiness.
10. documentation and tests.

## Architecture Principles
1. Outcome parity over object parity.
2. Continuity is explicit, not incidental.
3. Identity personalization fails closed.
4. Room defaults are always available.
5. Learning is governed and non-blocking.
6. Guest behavior is safe and non-training by default.
7. Silence is success unless user feedback is explicitly required.
8. Voice assistants are sensors, not speakers.
9. Sonos is the room voice unless superseded by future ADR.
10. Restoration must be testable.
11. Manual user intent must be respected.
12. Experience Continuity composes Foundation, Voice Identity, Asset Intelligence, and Concierge runtime inputs rather than duplicating ownership.

## Ownership Boundaries
- Foundation and HTBW own canonical room, person, presence, and identity contracts/models in [homes_that_behave_well/docs/contracts/room-awareness-contract.md](../homes_that_behave_well/docs/contracts/room-awareness-contract.md), [homes_that_behave_well/docs/contracts/person-identity-contract.md](../homes_that_behave_well/docs/contracts/person-identity-contract.md), and [homes_that_behave_well/docs/contracts/occupancy-and-presence-contract.md](../homes_that_behave_well/docs/contracts/occupancy-and-presence-contract.md).
- Concierge owns runtime orchestration and user-facing continuity behavior composition in [custom_components/concierge/services.py](custom_components/concierge/services.py) and [custom_components/concierge/coordinator.py](custom_components/concierge/coordinator.py).
- Voice Identity owns attribution and confidence lifecycle outcomes in [voice_identity/custom_components/voice_identity/services.py](../voice_identity/custom_components/voice_identity/services.py).
- Asset Intelligence owns advisory semantics and environmental stewardship outputs in [asset_intelligence/custom_components/asset_intelligence/advisory.py](../asset_intelligence/custom_components/asset_intelligence/advisory.py).
- Experience Continuity owns continuity policy and restore behavior across these governed inputs.

## Core Concepts
### Experience Snapshot
A captured representation of relevant room, entity, and media state before an interruption or managed transition.

### Usual State
A learned or configured default posture for a room, person, or context, such as usual lighting or usual music volume.

### Operational Restore
Returning a device or room to the state captured immediately before a managed interruption.

### Preference Restore
Applying learned or configured preferences rather than replaying a previous operational snapshot.

### Continuity Event
A runtime event that may require preservation, restoration, continuation, suppression, or fallback.

Examples include:
- voice interaction.
- room entry.
- room exit.
- music start.
- music pause.
- manual stop.
- command follow-up.
- monitoring question.
- identity confidence change.
- guest mode change.

### Continuity Scope
The entity, room, person, household, or mode boundary within which continuity behavior is valid.

### Continuity Confidence
The degree to which Concierge can safely personalize or restore based on identity, room, and state confidence.

## State Capture and Restore Model
Experience Continuity models state capture and restore explicitly for:
- light power state.
- brightness.
- color temperature.
- color values where supported.
- media player state.
- playback source or content metadata where supported.
- volume.
- duck volume.
- chat volume.
- music volume.
- room posture.
- suppression or cooldown state.
- last-media state.

Model distinctions:
- learned usual state is policy-driven and durability-oriented.
- operational snapshot state is interruption-oriented and short-lived.
- platform-native restore can be used but is not a continuity authority replacement.
- scene-based restore may participate as an execution mechanism.
- safe fallback defaults apply when state confidence is insufficient.

## Preference Resolution Model
Continuity behavior resolves with explicit precedence:
1. explicit command intent.
2. safety and policy constraints.
3. known person preference.
4. person plus room preference.
5. room default.
6. household default.
7. system safe default.

Resolution must support:
- person-aware behavior when confidence and policy permit.
- room-aware behavior when identity is unresolved.
- deterministic behavior when both identity and room confidence are limited.

## Identity and Confidence Policy
Identity and confidence signals are consumed, not owned, by Concierge continuity behavior.

Identity policy:
- high-confidence known identity may unlock person-aware continuity.
- unknown, low-confidence, and unavailable identity states must fail closed to room or household defaults.
- no identity signal should prevent safe deterministic room behavior.

Evidence of fail-closed pattern exists in:
- [custom_components/concierge/services.py](custom_components/concierge/services.py).
- [tests/test_services.py](tests/test_services.py).
- [tests/test_foundation.py](tests/test_foundation.py).
- [voice_identity/custom_components/voice_identity/services.py](../voice_identity/custom_components/voice_identity/services.py).

## Learning Policy
Learning policy boundaries:
- automatic learning only where explicitly governed.
- intentional learning preferred for durable personal preferences.
- asynchronous write paths to avoid blocking interactive responses.
- explainable and reversible learning outputs.
- no personalized learning commit for guest, unknown, or low-confidence contexts.
- room-level defaults may be learned when person identity is unavailable.

## Lighting Continuity Policy
Lighting continuity policy includes:
- learned brightness and usual-lighting behavior.
- separation of learned usual restore and operational snapshot restore.
- room-level defaults and entity-level defaults.
- person plus room preference candidates when confidence permits.
- color and color-temperature handling where available.
- deterministic fallback brightness when confidence or data is insufficient.
- safe no-device behavior when no lamps or lights are available.
- time-of-day bias identified as a future requirement implication.

## Audio Continuity Policy
Audio continuity policy includes:
- separate chat, music, and duck volume concerns.
- learned room audio profile behavior.
- person plus room volume preference candidate behavior.
- explicit Sonos ducking and restoration behavior.
- explicit fallback behavior when no suitable speaker exists.
- strict separation between speech output continuity and media continuity.

## Media Continuity Policy
Media continuity policy includes:
- room-aware play jazz and play genre behavior.
- play artist and album behavior where supported.
- continue playing behavior.
- last-media capture behavior.
- person-aware media preference behavior as redesign candidate.
- manual-stop cooldown policy.
- follow-me and cross-room behavior treated separately and not assumed for initial parity.
- no unwanted auto-start behavior.

## Monitoring and Follow-Up Policy
Monitoring continuity policy includes:
- room monitoring capability discovery.
- room-scoped sensor follow-up resolution.
- graceful refusal behavior when capability is unavailable.
- room-scoped calculations and lookups.
- person-specific verbosity only when justified by policy and confidence.

## Guardrails and Failure Policy
Guardrail policy includes:
- silence-is-success by default.
- direct-command-only refusal behavior.
- calm failure messaging.
- diagnostics and logging for explainability.
- policy suppression and cooldown behavior.
- missing-device handling.
- disabled-integration handling.
- missing-helper or missing-state handling during migration period.
- no-room-context handling.
- unavailable-Sonos handling.
- unavailable-Voice-Identity handling.

## Guest, Unknown, and Low-Confidence Behavior
Default behavior in guest, unknown, and low-confidence contexts:
- suppress person-specific personalization.
- suppress person-specific durable learning.
- allow safe room or household defaults.
- preserve calm non-intrusive response style.
- preserve deterministic execution behavior.

This aligns with identity fail-closed consumption evidence in:
- [custom_components/concierge/services.py](custom_components/concierge/services.py).
- [tests/test_foundation.py](tests/test_foundation.py).
- [voice_identity/custom_components/voice_identity/services.py](../voice_identity/custom_components/voice_identity/services.py).

## Production Install Gate
Experience Continuity install gate must pass before replacing in-scope V1 production behavior.

Gate checks:
1. learned or usual lighting behavior preserved or redesign-complete.
2. room-aware play jazz or genre behavior preserved or redesign-complete.
3. room-aware continue or resume behavior preserved or redesign-complete.
4. Sonos ducking and restoration behavior preserved or redesign-complete.
5. room capability discovery behavior available.
6. monitoring follow-up responses available.
7. guest, unknown, and low-confidence defaults verified.
8. silence-is-success and calm fallback behavior verified.
9. person-aware preference readiness verified.
10. tests and documentation coverage verified.

Install readiness remains not ready while critical gate items are gap or redesign without accepted scope cleanup, as shown in [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md).

## Consequences
Positive consequences:
- restores V1 behavioral intent through governed architecture.
- prevents piecemeal recreation of YAML behavior.
- creates a governed migration path.
- supports person-aware and room-aware design.
- makes production install readiness measurable.
- preserves calm, explainable home behavior.

Negative or tradeoff consequences:
- requires additional architecture work before implementation closure.
- requires additional ADRs and requirement packages.
- V2 cannot be declared production-ready until continuity gaps are resolved or intentionally scoped out.
- requires multi-domain tests across lighting, audio, media, person, and guest scenarios.
- may require migration or translation from helper-backed V1 state into V2 continuity state models.

## Non-Goals
- Implementing code in this ADR.
- Migrating production Home Assistant helpers in this ADR.
- Requiring every V1 automation to become a V2 service.
- Copying V1 YAML architecture directly.
- Including Bedtime, Good Morning, or Goodnight in Concierge V2 parity.
- Deciding detailed media provider implementation internals.
- Deciding exact final storage schema for all preferences.
- Overriding Voice Identity ownership of attribution or confidence.
- Overriding Asset Intelligence ownership of asset stewardship semantics.

## Follow-Up ADRs Recommended
1. ADR: Environmental State Snapshot and Restore Model.
- Required before implementation: Yes.

2. ADR: Lighting Continuity and Learned Brightness Model.
- Required before implementation: Yes.

3. ADR: Audio Continuity and Speaker Profile Model.
- Required before implementation: Yes.

4. ADR: Media Continuity and Follow-Me Behavior.
- Required before implementation: Yes for baseline media continuity, follow-me portion may be deferred by scope decision.

5. ADR: Person-Aware Preference Resolution.
- Required before implementation: Yes.

6. ADR: Learning Boundaries and Drift Hygiene.
- Required before implementation: Yes.

7. ADR: Guest, Unknown, and Low-Confidence Identity Behavior.
- Required before implementation: Yes.

8. ADR: Production Install Parity Gate.
- Required before implementation: Yes.

## Follow-Up Requirements Recommended
Requirement groups to generate after ADR acceptance:
- Experience Continuity state model requirements.
- Lighting continuity requirements.
- Audio continuity requirements.
- Media continuity requirements.
- Preference resolution requirements.
- Learning and helper migration requirements.
- Monitoring and follow-up requirements.
- Guardrail and fallback requirements.
- Test and validation requirements.
- Production install readiness requirements.

## Evidence
Primary artifacts:
- [docs/governance/experience-continuity/v1-capability-reconstruction.md](docs/governance/experience-continuity/v1-capability-reconstruction.md).
- [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md).

Concierge implementation and tests:
- [custom_components/concierge/services.yaml](custom_components/concierge/services.yaml).
- [custom_components/concierge/services.py](custom_components/concierge/services.py).
- [custom_components/concierge/const.py](custom_components/concierge/const.py).
- [custom_components/concierge/models.py](custom_components/concierge/models.py).
- [custom_components/concierge/storage.py](custom_components/concierge/storage.py).
- [custom_components/concierge/coordinator.py](custom_components/concierge/coordinator.py).
- [tests/test_services.py](tests/test_services.py).
- [tests/test_foundation.py](tests/test_foundation.py).
- [tests/test_diagnostics.py](tests/test_diagnostics.py).

Foundation and HTBW architecture/contract/model evidence:
- [homes_that_behave_well/docs/models/person-continuity-model.md](../homes_that_behave_well/docs/models/person-continuity-model.md).
- [homes_that_behave_well/docs/models/experience-restoration-context-model.md](../homes_that_behave_well/docs/models/experience-restoration-context-model.md).
- [homes_that_behave_well/docs/models/person-room-affinity-model.md](../homes_that_behave_well/docs/models/person-room-affinity-model.md).
- [homes_that_behave_well/docs/contracts/person-identity-contract.md](../homes_that_behave_well/docs/contracts/person-identity-contract.md).
- [homes_that_behave_well/docs/contracts/occupancy-and-presence-contract.md](../homes_that_behave_well/docs/contracts/occupancy-and-presence-contract.md).
- [homes_that_behave_well/docs/contracts/room-awareness-contract.md](../homes_that_behave_well/docs/contracts/room-awareness-contract.md).

Voice Identity evidence:
- [voice_identity/custom_components/voice_identity/services.py](../voice_identity/custom_components/voice_identity/services.py).

Asset Intelligence evidence:
- [asset_intelligence/custom_components/asset_intelligence/advisory.py](../asset_intelligence/custom_components/asset_intelligence/advisory.py).

## Open Questions
Scope decisions for alarm parity, follow-me media scope, routine exclusions, and helper-migration posture are now governed by [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md).

1. Is Sonos-as-room-voice mandatory for initial install gate or configurable in-phase override?
2. Where should learned preference state live in V2 for continuity behavior?
3. What is the minimum viable evidence threshold for the silence-is-success gate item?
4. Which behaviors remain production Home Assistant automations versus Concierge runtime services?
5. How should mode-aware behavior such as guest, entertaining, and night mode be modeled?
6. How should manual-stop cooldowns be represented?
7. What tests are required before replacing V1 automations?
