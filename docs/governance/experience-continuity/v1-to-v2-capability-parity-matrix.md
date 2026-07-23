# Concierge V1-to-V2 Capability Parity Matrix

## 1. Executive Summary
This artifact compares Concierge V1 production behavior against current Concierge V2 and related platform repositories using an outcome-based method.

Baseline authority for V1 behavior is:
- docs/governance/experience-continuity/v1-capability-reconstruction.md

Primary conclusion:
- Concierge V2 has strong governance scaffolding, authority boundaries, and identity-consumption safety behavior.
- Core V1 household outcomes for room lighting continuity, room media continuity, Sonos duck/restore, and room monitoring follow-up speech are not yet implemented as equivalent V2 user outcomes.
- Install-readiness is NOT_READY for replacing in-scope V1 production capability without loss.

## 2. Evidence Sources Inspected
### Production + V1 Baseline
- docs/governance/experience-continuity/v1-capability-reconstruction.md

### Concierge V2 implementation and tests
- custom_components/concierge/services.py
- custom_components/concierge/services.yaml
- custom_components/concierge/const.py
- custom_components/concierge/coordinator.py
- custom_components/concierge/diagnostics.py
- custom_components/concierge/panel.py
- custom_components/concierge/storage.py
- tests/test_services.py
- tests/test_foundation.py
- tests/test_diagnostics.py

### Concierge governance and architecture evidence
- docs/governance/capability-discovery-foundation.md
- docs/governance/capability-consumption-architecture.md
- docs/governance/restoration-consumption-architecture.md
- docs/governance/person-aware-restoration-consumption.md
- docs/governance/guest-unknown-restoration-consumption.md
- docs/governance/voice-identity-concierge-contract-alignment.md
- docs/wiki/voice-identity-personalization.md

### Foundation (HTBW) evidence
- homes_that_behave_well/docs/architecture/adr-concierge-v1-capability-preservation-governance.md
- homes_that_behave_well/docs/contracts/person-identity-contract.md
- homes_that_behave_well/docs/contracts/occupancy-and-presence-contract.md
- homes_that_behave_well/docs/models/room-model.md
- homes_that_behave_well/docs/models/person-continuity-model.md
- homes_that_behave_well/docs/models/person-room-affinity-model.md
- homes_that_behave_well/docs/models/experience-restoration-context-model.md

### Voice Identity implementation evidence
- voice_identity/custom_components/voice_identity/services.py
- voice_identity/custom_components/voice_identity/identity_context.py
- voice_identity/tests/test_identity_context.py
- voice_identity/tests/test_diagnostics_services.py

### Asset Intelligence implementation evidence
- asset_intelligence/custom_components/asset_intelligence/coordinator.py
- asset_intelligence/custom_components/asset_intelligence/advisory.py

## 3. Scope and Exclusions
Evaluated capability domains:
1. Voice Interaction
2. Room Awareness
3. Lighting Continuity
4. Audio Continuity
5. Media Continuity
6. Monitoring and Sensor Follow-Ups
7. Learning and Preference Memory
8. Guardrails and Soft Failure Handling
9. Experience Continuity

Explicitly excluded from V2 parity scope by policy:
- Bedtime (Concierge)
- Good Morning (Concierge)
- Goodnight / Good Night (Concierge)

## 4. Alarm-Related Scope Note
V1 production baseline includes Primary Bedroom Alarm automations.

Observed V2 evidence:
- Concierge V2 exposes alarm entity cataloging and global context type alarm_status (panel.py and services.py).
- No direct V2 implementation evidence found for preserving V1 bedroom alarm orchestration outcomes (start/repeat/escalation/stop/chime/snapshot behavior) inside Concierge runtime.

Alarm classification for this parity gate:
- OUT_OF_SCOPE

Alarm continuity is documented separately and does not block this core matrix for initial Concierge V2 Experience Continuity install readiness.

Scope authority reference:
- docs/governance/experience-continuity/experience-continuity-scope-decisions.md

## 5. Methodology
- Extract V1 outcomes from production reconstruction artifact as user-observable outcomes.
- Search V2 implementation, tests, and governance docs for equivalent capability evidence.
- Mark each outcome with one primary disposition:
  - PASS
  - PARTIAL
  - GAP
  - REDESIGN
  - SUPERSEDED
  - OUT_OF_SCOPE
  - SCOPE_CONFIRMATION_REQUIRED
- Use docs-only and deferred-owner markers where implementation is not present.
- Do not claim parity from naming, wiki mention, or architecture intent alone.

## 6. Capability Parity Matrix
| Capability ID | Capability Domain | V1 User Outcome | V1 Evidence | V1 Implementation Pattern | V2 Evidence | V2 Coverage Status | Primary Disposition | Person-Aware Redesign Needed? | Recommended V2 Scope | Dependencies | Tests Needed | Documentation Needed | Install Gate Impact | Recommended Follow-Up |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| VI-01 | Voice Interaction | User can ask what can I do here and get room-aware capability guidance | v1-capability-reconstruction: automation.concierge_voice_entry_ha_voice, script.room_abilities_speak_unified | HA conversation trigger plus room-resolved script speech | services.py _build_capability_discovery and get_summary discovery payload; test_services.py test_context_and_summary_services | Capability discovery metadata exists; direct room voice outcome equivalent not implemented | PARTIAL | Yes | room-scoped then person + room scoped | needs-foundation, needs-provider-contract, docs-only | Integration test for voice query -> room capability response | Runtime mapping of discovery metadata to spoken UX contract | BLOCKER | Implement room-aware capability response path using governed discovery outputs |
| VI-02 | Voice Interaction | User can issue follow-up room commands (lamps/lights/music/shades/tv) | v1-capability-reconstruction: automation.concierge_follow_up_commands_ha_voice | Conversation intent parsing and room entity actuation | services.py execute supports generic target execution; no equivalent follow-up parser flow found | Generic execute exists but no equivalent follow-up experience | GAP | Yes | person + room scoped | needs-experience-continuity, implementation-missing | End-to-end follow-up command tests per domain | Follow-up conversation contract for V2 | BLOCKER | Define V2 follow-up outcome contract and implementation sequence |
| RA-01 | Room Awareness | System resolves speaking device to room context | v1-capability-reconstruction: area_id(trigger.device_id) in voice automations | HA automation device->area resolution | services.py supports area_id/composite_id inputs and _assemble_foundation_context | Room context assembly exists but speaker-device conversational binding not equivalent | PARTIAL | Yes | room-scoped | needs-foundation, needs-tests | Tests for speech-device room resolution path | Clarify room resolution semantics for service and conversation channels | MAJOR | Add explicit speech-source to area resolution contract |
| RA-02 | Room Awareness | System resolves room speakers for output | v1-capability-reconstruction: script.room_audio_resolver_keystone and sonos speak scripts | Room audio resolver and fallback speech paths | services.py has preview_tts_voice and room config speaker_entity_ids; no equivalent resolver behavior | Config surface exists; equivalent runtime resolver outcome not implemented | GAP | Yes | room-scoped with guest-default fallback | needs-foundation, implementation-missing | Resolver tests with and without preferred speaker types | Speaker resolution policy doc for V2 | BLOCKER | Add deterministic room speaker resolver and fallback chain |
| AU-01 | Audio Continuity | Sonos is room voice while voice assistants behave as sensors/input | v1-capability-reconstruction: sonos_speak_with_ducking_room and assist listening automations | Sonos-centric output with assist as trigger/sensor | No direct runtime evidence in concierge custom_components for this policy path | Policy not implemented in V2 runtime | GAP | Yes | room-scoped with unknown-speaker default scoped | needs-provider-contract, needs-experience-continuity | Policy conformance tests for output-device selection | Output policy contract for room voice channel | BLOCKER | Introduce explicit room voice output policy and device-role mapping |
| LI-01 | Lighting Continuity | Lamps can learn used brightness automatically | v1-capability-reconstruction: automation.lamp_profile_learn_on_use and input_number learned brightness helpers | Attribute observation and helper persistence | No equivalent light-level learning implementation found in concierge runtime/tests | Missing | GAP | Yes | person + room + time-of-day scoped with guest-default scoped fallback | needs-state-store, needs-foundation, implementation-missing | Learning capture tests from light state changes | Retained operational values mapping guide | BLOCKER | Implement retained_operational_values write path for room lighting |
| LI-02 | Lighting Continuity | User can intentionally say remember this lighting | v1-capability-reconstruction: automation.concierge_intentional_learning_ha_voice calling script.learn_lighting_usual_room | Intentional learning command + profile update | No equivalent intentional learning service/flow found | Missing | GAP | Yes | person + room scoped | needs-state-store, needs-voice-identity | Command-to-learning tests including unknown identity fallback | Intentional learning contract and phrase mapping | BLOCKER | Add intentional learning orchestration with safe identity posture |
| LI-03 | Lighting Continuity | Lamps/lights can restore to usual brightness | v1-capability-reconstruction: turn_on_lamps_usual_room, turn_on_lights_usual_room | Room-scoped helper-driven restore | HTBW room-model retained_operational_values exists; no concierge runtime implementation | Model available but runtime parity missing | REDESIGN | Yes | person + room + time-of-day scoped with guest-default suppression | needs-foundation, needs-state-store, needs-experience-continuity | Restore-behavior tests per occupancy/identity mode | V2 restoration policy for lighting continuity | BLOCKER | Implement continuity read path from retained operational values |
| LI-04 | Lighting Continuity | Lighting percentage requests are handled | v1-capability-reconstruction: concierge_lighting_percentage_catcher_ha_voice | Conversation parsing and room light actuation | No equivalent percentage intent handling flow found | Missing | GAP | Yes | room-scoped | implementation-missing | Intent parsing and actuation tests for percentage targets | V2 percentage command behavior notes | MAJOR | Add deterministic percentage handler in V2 interaction path |
| AU-02 | Audio Continuity | Speaker profiles exist for chat/music/duck volumes | v1-capability-reconstruction: resolve_speaker_profile helper family | Per-room profile helpers and scripts | No equivalent speaker profile runtime model in concierge services/models for chat/music/duck | Missing | GAP | Yes | person + room + time-of-day scoped | needs-state-store, needs-foundation | Profile resolution tests with fallback hierarchy | Speaker profile model and boundary doc | BLOCKER | Design V2 speaker profile schema aligned to room model retained values |
| AU-03 | Audio Continuity | Music volume can be learned from Sonos changes | v1-capability-reconstruction: automation.learn_music_volume_on_sonos_change and script.learn_music_volume_room | Passive volume learning | No equivalent runtime learning flow found | Missing | GAP | Yes | person + room scoped | needs-state-store, needs-provider-contract | Volume learning tests from media player state events | Volume learning and suppression policy | MAJOR | Add passive volume learning pipeline |
| AU-04 | Audio Continuity | Sonos can duck while assist is listening and restore | v1-capability-reconstruction: automation.duck_sonos_when_any_assist_satellite_is_listening and script.duck_sonos_while_assist_is_listening_room | Assist listening trigger, duck, then restore | No equivalent duck/restore orchestration in concierge runtime | Missing | GAP | Yes | room-scoped with context-scoped exceptions | needs-provider-contract, implementation-missing | Duck/restore lifecycle tests with interruption cases | Audio ducking policy and restoration guarantees | BLOCKER | Implement bounded duck/restore orchestrator |
| ME-01 | Media Continuity | User can play music by room | v1-capability-reconstruction: automation.voice_play_music and play scripts | Room-aware media resolver and play scripts | execute supports generic target execution; no room media intent implementation | Generic actuation only; user outcome not equivalent | GAP | Yes | person + room scoped | needs-foundation, needs-provider-contract | Room media play tests with resolver coverage | Media continuity outcome contract | BLOCKER | Implement media intent-to-room execution pipeline |
| ME-02 | Media Continuity | User can play jazz by room | v1-capability-reconstruction: automation.voice_play_jazz and script.play_genre_room | Genre-aware room music flow | No equivalent jazz/genre room flow in concierge runtime | Missing | GAP | Yes | person + room scoped | needs-state-store, needs-provider-contract | Genre request tests with room context and fallback | Genre handling contract for V2 | BLOCKER | Add genre intent support with room-aware resolver |
| ME-03 | Media Continuity | User can continue/resume music with room context | v1-capability-reconstruction: automation.voice_continue_playing and script.continue_playing_room | Last-media capture and continuation | HTBW person-continuity-model defines last_media and last_room; no concierge runtime continuation implementation | Model exists; runtime parity missing | REDESIGN | Yes | person + room + time-of-day scoped | needs-experience-continuity, needs-state-store | Resume flow tests with explicit stop cooldown rules | Continuation policy and cooldown behavior spec | BLOCKER | Implement continuity-driven media resume with suppression guards |
| ME-04 | Media Continuity | Last played media is captured for continuity | v1-capability-reconstruction: automation.music_capture_last_media_on_playback and script.update_last_media_room | Playback observation and helper persistence | No equivalent media capture pipeline found in concierge runtime | Missing | GAP | Yes | room-scoped and person + room scoped | needs-state-store, needs-provider-contract | Media capture persistence tests | Data retention and provenance notes for media continuity | MAJOR | Add media state capture events into activity/state store |
| ME-05 | Media Continuity | Music genre counters/preferences are tracked | v1-capability-reconstruction: automation.music_genre_observe_playback_all_sources and counters | Counter-based preference accumulation | No equivalent genre counter implementation found in concierge runtime | Missing | GAP | Yes | person + room scoped | needs-state-store | Preference aggregation tests and conflict handling tests | Preference model extension doc | MAJOR | Define and implement V2 preference accumulation model |
| MO-01 | Monitoring and Sensor Follow-Ups | User can ask monitoring questions and hear room capability coverage | v1-capability-reconstruction: concierge_room_monitoring_awareness_ha_voice and room_monitoring_abilities_speak | Room monitoring speech scripts with fallback | services.py has room_sensor_entity_ids config and summary metadata; no equivalent monitoring speech flow | Configuration present; direct outcome missing | PARTIAL | Yes | room-scoped | needs-foundation, docs-only | Monitoring intent tests for room sensors available/unavailable | Monitoring interaction contract | BLOCKER | Implement monitoring query orchestration path |
| MO-02 | Monitoring and Sensor Follow-Ups | Follow-up questions can answer temperature/humidity/light/air/noise | v1-capability-reconstruction: concierge_follow_up_sensor_queries_ha_voice and speak_room_* scripts | Follow-up parser and sensor-specific speech scripts | No equivalent sensor follow-up response implementation found in concierge runtime/tests | Missing | GAP | Yes | room-scoped with optional person verbosity mode-scoped | needs-foundation, needs-tests | Sensor follow-up tests by modality and confidence | Sensor follow-up behavior spec and refusal policy | BLOCKER | Add room sensor follow-up command handling |
| GS-01 | Guardrails and Soft Failure Handling | Capability-not-available refusal exists | v1-capability-reconstruction: script.speak_capability_not_available | Explicit graceful refusal | No equivalent explicit refusal flow found in concierge runtime for these capability domains | Missing | GAP | Yes | context-scoped | implementation-missing | Refusal-path tests by missing capability type | Refusal taxonomy and message policy | MAJOR | Add deterministic refusal outcomes for unavailable capability |
| LP-01 | Learning and Preference Memory | Learning can be intentional and explicit | v1-capability-reconstruction: concierge_intentional_learning_ha_voice | Explicit commands write learning state | No equivalent intentional learning runtime flow in concierge | Missing | GAP | Yes | person + room scoped | needs-state-store, needs-voice-identity | Intentional learning tests with opt-in and consent | Learning opt-in policy and explainability docs | BLOCKER | Implement explicit learning intent workflow |
| GS-02 | Guardrails and Soft Failure Handling | Guest/default behavior exists and avoids private personalization | v1-capability-reconstruction labels include guest; guest-safe operational patterns | Label-aware V1 behavior | services.py and coordinator.py build guest_unknown_occupant_behavior boundaries; tests in test_foundation.py and test_diagnostics.py assert guest-safe flags and external authority | Safety boundary implemented mostly as governed boundary visibility; domain outcomes still incomplete | PARTIAL | Yes | guest-default scoped and unknown-speaker default scoped | needs-foundation, needs-voice-identity | End-to-end guest behavior tests across lighting/media/monitoring | Guest-safe behavior outcomes per domain | BLOCKER | Extend guest-safe behavior from boundary metadata to runtime outcomes |
| GS-03 | Guardrails and Soft Failure Handling | Unknown/low-confidence identity triggers fail-closed personalization | v1-capability-reconstruction and policy label behavior | Conservative fallback | services.py _async_consume_voice_identity_runtime_context and _resolve_active_person_resolution_from_envelope; tests/test_foundation.py active_person_unknown/ambiguous/unavailable fail_closed; voice_identity/services.py unavailable and low-confidence-safe outputs | Implemented and testable as identity-consumption safety | PASS | No | low-confidence identity default scoped | needs-voice-identity, needs-tests | Maintain regression tests for fail-closed behavior | Keep contract alignment docs updated for identity confidence | NONE | Keep as gate criterion with no ownership drift |
| GS-04 | Guardrails and Soft Failure Handling | Silence-is-success and no proactive chatter except direct requests | v1-capability-reconstruction indicates silent success paths in several automations/scripts | Implicit calm operation behavior | HTBW example calm operation states principle; no concierge runtime assertion found for silence-is-success policy behavior per capability | Principle documented; runtime parity not verified | REDESIGN | Yes | mode-scoped and context-scoped | docs-only, needs-tests | Add policy tests for no unsolicited chatter | Calm-operation runtime policy for Concierge | MAJOR | Define measurable silence policy and enforce in orchestrator |
| EC-01 | Experience Continuity | Experience continuity works as cross-cutting operational pattern | v1-capability-reconstruction cross-domain continuity (lighting/audio/media/monitoring memory+resume patterns) | Emergent continuity via automations/helpers/scripts | services.py exposes continuity_governance_boundary, person_room_affinity_boundary, privacy_household_memory_boundary; deferred owners in boundary payloads; tests assert boundary visibility | Governance and scaffolding implemented; outcome continuity not implemented | PARTIAL | Yes | context-scoped | needs-experience-continuity, needs-foundation, docs-only | Cross-domain continuity acceptance suite | Experience continuity architecture domain doc should be first-class runtime requirement | BLOCKER | Promote continuity from boundary metadata to operational behaviors |
| EC-02 | Learning and Preference Memory | Person-aware preference resolution readiness for routing/experience | v1 behavior mostly room/entity scoped with limited explicit person-awareness | Helper-scoped and room-scoped memory patterns | services.py _build_person_aware_productivity_routing, _async_update_person_context_repairs; tests/test_services.py person-aware routing enabled/disabled; Voice Identity services provide identity context | Productivity routing readiness exists; preference resolution for lighting/audio/media outcomes not implemented | PARTIAL | Yes | person + room scoped | needs-voice-identity, needs-state-store, needs-experience-continuity | Preference resolution tests for each capability domain | Person-aware preference resolution contract for continuity domains | BLOCKER | Extend person-aware routing into media/audio/lighting continuity decisions |

## 7. Domain-Level Coverage Summary
### Voice Interaction
- Coverage status: PARTIAL
- Evidence: Concierge execute/get_summary surfaces; capability discovery metadata in services.py; service tests in tests/test_services.py
- Gaps: no equivalent conversational follow-up command engine or room abilities spoken response flow
- Recommended disposition: REDESIGN for conversational orchestration, keep generic execute as substrate

### Room Awareness
- Coverage status: PARTIAL
- Evidence: Foundation context assembly and room config surfaces in services.py/storage.py
- Gaps: no implemented equivalent for room speaker resolution behavior from V1
- Recommended disposition: PARTIAL now, REDESIGN for speaker/output policy

### Lighting Continuity
- Coverage status: GAP
- Evidence: V1 baseline has learning+restore behavior; HTBW room-model retained_operational_values defines target model
- Gaps: no V2 runtime learning/restore implementation
- Recommended disposition: REDESIGN (person+room+time-aware continuity)

### Audio Continuity
- Coverage status: GAP
- Evidence: V1 baseline has speaker profile and Sonos duck/restore
- Gaps: no equivalent V2 runtime duck/restore or profile resolution
- Recommended disposition: REDESIGN

### Media Continuity
- Coverage status: GAP
- Evidence: V1 baseline has play genre/jazz/continue/last media capture; HTBW continuity model supports future form
- Gaps: no equivalent V2 media continuity runtime paths
- Recommended disposition: REDESIGN

### Monitoring and Sensor Follow-Ups
- Coverage status: PARTIAL
- Evidence: room sensor config structures exist in V2; V1 had explicit room monitoring speech scripts
- Gaps: no V2 follow-up conversational sensor-answer implementation
- Recommended disposition: GAP to implement room monitoring outcomes

### Learning and Preference Memory
- Coverage status: PARTIAL
- Evidence: V2 person profile and person-aware productivity routing exist
- Gaps: no continuity memory pipelines for lighting/audio/media preferences
- Recommended disposition: REDESIGN with explicit state-store and retention rules

### Guardrails and Soft Failure Handling
- Coverage status: PARTIAL
- Evidence: fail-closed identity behavior implemented and tested; guest-safe boundaries represented and tested
- Gaps: explicit capability-not-available refusal and silence-is-success runtime guarantees missing for these domains
- Recommended disposition: keep PASS for identity fail-closed, implement remaining guardrails

### Experience Continuity
- Coverage status: PARTIAL
- Evidence: continuity/restoration governance boundaries and deferred-owner mapping in services.py and governance docs
- Gaps: operational continuity outcomes are not implemented equivalently yet
- Recommended disposition: must become first-class runtime architecture domain

## 8. Person-Aware Redesign Recommendations
### Lighting
- Move from entity helper-only memory to layered scope:
  - room defaults
  - person + room preferences
  - guest defaults
  - unknown-speaker defaults
  - low-confidence defaults
  - time-of-day bias
- Suppress learned-person preference in guest mode and low-confidence states.

### Audio
- Add explicit chat/music/duck profile resolution hierarchy:
  - person + room + time-of-day
  - room default
  - household fallback
- Keep Sonos-as-room-voice as policy, with deterministic fallback if no Sonos exists.

### Media
- Implement room-aware and person-aware continuity stack:
  - play genre in room
  - play jazz in room
  - continue last media
  - cooldown after manual stop
  - household fallback if identity unresolved
- True cross-room follow-me continuity is treated as a post-install enhancement and is not required for the initial install gate.

### Monitoring
- Keep room sensor response baseline room-scoped.
- Add person-specific verbosity only when confidence and policy allow.

### Guardrails
- Preserve fail-closed personalization for unknown/low-confidence identity.
- Enforce no proactive chatter by default.
- Only surface explicit refusal for direct user requests when capability is unavailable.

## 9. Experience Continuity Architecture Implications
Current V2 includes continuity governance metadata and ownership boundaries, but not equivalent outcome runtime behaviors from V1 continuity-heavy automations.

Implication:
- Experience Continuity should be treated as a first-class V2 architecture domain (not only deferred metadata), with explicit acceptance criteria for lighting/audio/media monitoring continuity outcomes.

## 10. Install-Readiness Blockers
Critical blockers for V1 replacement without capability loss:
1. Learned light level restore/usual lighting behavior not implemented.
2. Play jazz with room context not implemented.
3. Continue/resume music with room context not implemented.
4. Sonos ducking/restoration behavior not implemented.
5. Room capability spoken discovery equivalent only partial.
6. Monitoring follow-up answers not implemented.
7. Guest/unknown-speaker safe behavior only partially operationalized for these capability outcomes.
8. Silence-is-success fallback not runtime-proven for these domains.
9. Person-aware preference resolution for continuity domains not implemented.

## 11. Recommended Next Artifacts
No ADRs, backlog, or issues are generated in this phase.

Recommended artifact direction after approval:
- scope-cleanup decision note for alarm continuity inclusion/exclusion
- capability-domain requirements package (lighting, audio, media, monitoring, guardrails)
- experience continuity runtime acceptance criteria artifact

## 12. Open Questions
Scope decisions for alarm parity, follow-me media scope, routine exclusions, and helper-migration posture are now governed by:
- docs/governance/experience-continuity/experience-continuity-scope-decisions.md

1. Is Sonos-as-room-voice still a mandatory policy in V2 or configurable by room/person?
2. Should person-aware defaults be applied for media and lighting at medium confidence, or only high confidence?

## 13. Evidence Limitations
- V1 baseline is reconstruction from production evidence artifact, not direct execution replay in this task.
- V2 governance artifacts are extensive; many indicate deferred runtime ownership/implementation.
- No new runtime experiments were executed in Home Assistant for this parity document.

## Install-Readiness Gate
Question: Can Concierge V2 be installed into production without loss of in-scope Concierge V1 capability?

Classification: NOT_READY

Rationale:
- Multiple critical V1 in-scope outcomes are GAP or REDESIGN and not currently testable as equivalent outcomes in V2 runtime.
- Existing PASS evidence is concentrated in governance boundaries and identity fail-closed behavior, not in continuity-heavy household outcomes.

## Stop Point Recommendation
1. V1 domains already covered in V2:
- Guardrails subset: unknown/low-confidence fail-closed identity consumption
- Core orchestration substrate: generic execute/context summary surfaces

2. V1 domains partial in V2:
- Voice Interaction
- Room Awareness
- Monitoring and Sensor Follow-Ups
- Learning and Preference Memory
- Guardrails and Soft Failure Handling
- Experience Continuity

3. V1 domains missing in V2 (outcome-equivalent runtime):
- Lighting Continuity
- Audio Continuity
- Media Continuity

4. Capabilities requiring redesign rather than direct carry-forward:
- Lighting usual/learned behavior
- Speaker profile and ducking strategy
- Media continue/jazz/genre continuity
- Silence-is-success runtime enforcement

5. Experience Continuity first-class domain decision:
- Yes, it must be first-class for parity-complete V2 replacement.

6. Production install readiness without capability loss:
- NOT_READY

7. Recommended immediate next step:
- Scope cleanup first (alarm scope decision), then requirements backlog generation.
