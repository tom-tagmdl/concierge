# Experience Continuity Audio Gate Closure Package

## 1. Purpose
This package closes the EC-D audio domain for install-gate evidence readiness.

It proves that room-audio memory, bounded speech duck/restore behavior, deterministic degraded audio fallback, merged-room playback behavior, constituent-room memory preservation, and Follow-Me exclusion are documented and validation-backed before EC-H packaging.

## 2. Governance Sources
- docs/governance/experience-continuity/experience-continuity-governance-conformance-review.md
- docs/governance/experience-continuity/adr-experience-continuity-architecture.md
- docs/governance/experience-continuity/experience-continuity-scope-decisions.md
- docs/governance/experience-continuity/experience-continuity-epic-and-issue-roadmap.md
- docs/governance/experience-continuity/experience-continuity-outcome-preservation-review.md
- docs/governance/experience-continuity/experience-continuity-requirements-backlog.md
- docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md
- docs/governance/experience-continuity/v1-capability-reconstruction.md
- docs/governance/experience-continuity/experience-continuity-room-audio-memory-contract.md
- docs/governance/experience-continuity/experience-continuity-sonos-speech-continuity-policy.md
- docs/governance/experience-continuity/experience-continuity-audio-fallback-decision-matrix.md
- docs/governance/experience-continuity/experience-continuity-runtime-terminology-reference.md
- docs/governance/experience-continuity/experience-continuity-helper-family-disposition-matrix.md
- docs/governance/experience-continuity/experience-continuity-preference-resolution-contract.md
- docs/governance/experience-continuity/experience-continuity-identity-safety-context-matrix.md
- docs/governance/experience-continuity/experience-continuity-learning-governance-and-reversibility.md
- docs/governance/experience-continuity/experience-continuity-diagnostics-reference.md

## 3. EC-D Requirement Coverage
Install-gate requirements represented in this package:
- EC-REQ-030: bounded Sonos speech duck/restore lifecycle.
- EC-REQ-031: speech continuity remains separate from media continuation.
- EC-REQ-032: room-scoped music/duck/TTS audio memory with configured speaker authority.
- EC-REQ-033: deterministic unavailable-speaker fallback or refusal.
- EC-REQ-063: deterministic degraded-path guardrails with explainability.
- EC-REQ-090: every install-gate continuity behavior maps to both documentation and validation evidence.

Coverage matrix artifact:
- tmp/ec406_audio_gate_coverage_matrix.json

EC-REQ-090 in this audio closure means every in-scope EC-D behavior must have at least one architecture-aligned documentation artifact and at least one executable validation artifact.

## 4. Audio Continuity Architecture Summary
The EC-D audio stack preserves V1 user outcomes through V2 architecture by keeping:
- Room Configuration as the authority source for speakers.
- Room-scoped continuity memory for music, duck, and TTS channels.
- Bounded speech duck/restore logic separate from media continuation.
- Deterministic degraded-path and fallback behavior.
- Playback scope and memory scope explicitly separated in merged-room behavior.

Primary implementation surfaces audited:
- custom_components/concierge/services.py
- custom_components/concierge/models.py
- custom_components/concierge/storage.py
- custom_components/concierge/coordinator.py

No runtime modifications were required for this closure package.

## 5. Room Audio Memory Summary
Room-audio memory evidence confirms:
- configured room speakers are authoritative,
- room music volume is room-scoped,
- room duck volume is room-scoped,
- room TTS volume is room-scoped,
- music, duck, and TTS channels remain separate,
- merged-room playback does not collapse constituent-room memory,
- no persistent merged-room volume key is created.

Evidence artifacts:
- tmp/ec403_portable_harness_results.json
- tmp/ec403_room_audio_scenarios.json
- tmp/ec403_room_audio_coverage_matrix.json

## 6. Speech / Duck / Restore Lifecycle Summary
Speech lifecycle evidence confirms:
- duck and speech levels resolve deterministically,
- restore remains volume-only,
- paused or stopped media does not auto-resume,
- TTS failure and restore failure remain bounded and explainable,
- merged-room TTS and Concierge announcement playback target configured grouped speakers.

Evidence artifacts:
- tmp/ec404_portable_harness_results.json
- tmp/ec404_scenarios.json
- tmp/ec404_coverage_matrix.json

## 7. Audio Fallback / Degraded Path Summary
Fallback evidence confirms:
- missing, empty, invalid, missing-state, and unavailable configured speakers fail deterministically,
- preferred unavailable speakers can fall back only to validated configured speakers,
- no replacement discovery is performed,
- no authority bypass occurs,
- merged-room degraded speaker behavior remains bounded and explainable.

Evidence artifacts:
- tmp/ec405_portable_harness_results.json
- tmp/ec405_scenarios.json
- tmp/ec405_coverage_matrix.json

## 8. Merged-Room Playback Validation
Merged-room validation in this package proves:
- merged-room music playback targets all configured participating speakers,
- merged-room TTS playback targets all configured participating speakers,
- merged-room Concierge announcement playback uses the same grouped speaker authority path,
- ducking applies across grouped participating speakers,
- restore applies across grouped participating speakers according to bounded lifecycle rules.

Evidence artifacts:
- tmp/ec403_room_audio_scenarios.json
- tmp/ec404_scenarios.json
- tmp/ec406_audio_gate_scenarios.json

## 9. Constituent-Room Memory Preservation
Constituent-room memory evidence confirms:
- room A music, duck, and TTS values remain independent,
- room B music, duck, and TTS values remain independent,
- exiting merged-room operation does not overwrite room-specific values,
- merged-room grouped playback does not create a shared persistent merged-room continuity memory.

The current ConciergeState persistence model retains audio continuity in room-scoped usual_states only, which aligns with EC-D scope and does not create a separate merged-room media-memory owner.

## 10. Follow-Me Boundary Statement
Merged-room playback is grouped-room output behavior only.

It is not Follow-Me Music, does not implement cross-room transfer, and does not introduce BLE or person-location following behavior.

Follow-Me remains post-install enhancement scope under EC-PE-01 and is not part of the EC-D install gate.

## 11. Test Coverage Matrix
Consolidated audio-domain test and evidence mapping is captured in:
- tmp/ec406_audio_gate_test_results.json
- tmp/ec406_audio_gate_coverage_matrix.json

Closure run summary:
- Native targeted pytest: environment-blocked on this Windows host.
  Full plugin autoload fails due Home Assistant plugin import dependency on `fcntl`.
  Autoload-disabled fallback loses the `hass` fixture.
- Portable executable evidence suites: passing.
  - EC403 room audio: 15/15
  - EC404 speech lifecycle: 6/6 harness scenarios, 18/18 closure checks
  - EC405 fallback/no-speaker: 16/16

## 12. Documentation Cross-Reference Matrix
Behavior-to-governance-to-implementation-to-test mapping is captured in:
- tmp/ec406_audio_gate_doc_cross_reference.json

This matrix links room-audio memory, bounded lifecycle, fallback behavior, merged-room behavior, constituent-room memory preservation, and Follow-Me exclusion to authoritative documentation and validation artifacts.

## 13. Validation Evidence Summary
Executable evidence produced for this closure:
- tmp/ec406_audio_gate_test_results.json
- tmp/ec406_audio_gate_scenarios.json
- tmp/ec406_audio_gate_coverage_matrix.json
- tmp/ec406_audio_gate_doc_cross_reference.json
- tmp/ec406_audio_gate_readiness_summary.json

Execution orchestration:
- tmp/ec406_audio_gate_closure.py

Latest closure run log:
- tmp/ec406_audio_gate_closure_stdout_latest.txt

## 14. Install-Gate Readiness Assessment
Current assessment: READY for EC-D audio closure.

Rationale:
- EC-D dependency evidence from #403, #404, and #405 is present and passing through portable executable suites.
- Merged-room playback scope and constituent-room memory scope are explicitly validated.
- Follow-Me remains excluded and documented as post-install only.
- Native pytest remains environment-blocked on this Windows host in both observed modes, but the limitation is captured and does not invalidate the portable executable evidence package.

Readiness summary artifact:
- tmp/ec406_audio_gate_readiness_summary.json

docs/wiki inspection result:
- no wiki update required.
- existing wiki pages are setup/operator oriented and do not contain a dedicated EC-D audio gate closure section.
- the governance closure package is the canonical operator/architecture artifact for this install-gate closure.

## 15. Non-Goals
This closure package does not:
- implement new runtime audio behavior,
- create persistent merged-room volume memory,
- create persistent merged-room media memory,
- implement Follow-Me Music,
- implement BLE-based music following,
- implement cross-room transfer behavior,
- implement Music Assistant orchestration,
- introduce new media continuation features,
- change production Home Assistant.