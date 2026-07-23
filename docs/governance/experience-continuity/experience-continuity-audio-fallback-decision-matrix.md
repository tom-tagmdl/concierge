# Experience Continuity Audio Fallback Decision Matrix

## 1. Purpose
Define deterministic room-audio fallback behavior for unavailable or invalid speaker targets in Experience Continuity audio paths.

This matrix is scoped to EC-D-03 and supports EC-REQ-033 and EC-REQ-063.

## 2. Governance Inputs
- docs/governance/experience-continuity/adr-experience-continuity-architecture.md
- docs/governance/experience-continuity/experience-continuity-scope-decisions.md
- docs/governance/experience-continuity/experience-continuity-requirements-backlog.md
- docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md
- docs/governance/experience-continuity/v1-capability-reconstruction.md
- docs/governance/experience-continuity/experience-continuity-room-audio-memory-contract.md
- docs/governance/experience-continuity/experience-continuity-sonos-speech-continuity-policy.md

## 3. Scope
In scope:
- Room-TTS speaker target fallback for configured room speakers.
- Merged-room grouped validation behavior where one or more constituent rooms degrade.
- Deterministic refusal when no configured speaker validates.
- Explainability fields that show requested targets, resolved targets, and fallback reasons.

Out of scope:
- Cross-room Follow-Me behavior.
- New discovery-based replacement speakers.
- Media continuation or playback resume behavior.
- Production Home Assistant configuration changes.

## 4. Authority Order
1. Room Configuration membership (configured room speaker mappings).
2. Runtime validation (entity shape, existence, state availability).
3. Deterministic fallback to validated configured speakers.
4. Deterministic refusal if no validated configured speakers remain.

Guardrail: Runtime validation may disqualify configured speakers, but may not discover unrelated replacements.

## 5. Decision Inputs
Primary inputs:
- requested_target_speakers
- configured_room_speaker_map
- validation_results per configured speaker
- validated_room_speaker_map
- participating_rooms for merged-room context

Validation classifications:
- configured_speaker_valid
- configured_speaker_unavailable
- configured_speaker_missing
- configured_speaker_invalid

## 6. Decision Matrix
| Condition | Deterministic Action | Fallback Reason | Notes |
| --- | --- | --- | --- |
| Requested preferred speaker validates | Deliver to requested speaker | none | Normal path |
| Requested preferred speaker does not validate, but other configured speakers validate | Deliver to validated configured speakers | preferred_speaker_unavailable | No discovery |
| All configured speakers unavailable | Refuse room-TTS delivery | configured_speaker_unavailable | Explainable degraded path |
| Configured speakers missing state/entity | Refuse room-TTS delivery | configured_speaker_missing | Explainable degraded path |
| Configured speakers invalid type/format | Refuse room-TTS delivery | configured_speaker_invalid | Explainable degraded path |
| Room has no configured speaker mapping | Refuse room-TTS delivery | configured_speaker_mapping_missing | No discovery |
| Merged-room with one degraded constituent and one valid constituent | Deliver to validated speakers from valid constituents only | preferred_speaker_unavailable or constituent validation reason | Grouped playback remains bounded |
| Merged-room with no validated speakers across constituents | Refuse room-TTS delivery | no_target_speakers_available | Deterministic refusal |

## 7. Explainability Contract
Lifecycle payload must include:
- group_targeted_speakers
- target_resolution.requested_target_speakers
- target_resolution.resolved_target_speakers
- target_resolution.decision_reason
- target_resolution.fallback_reason
- grouped_validation_results
- failure_reason
- fallback_used
- fallback_path

This provides deterministic degraded-path evidence for EC-REQ-063.

## 8. Safety Boundaries
- No runtime replacement speaker discovery outside configured room membership.
- No conversion of speech fallback into media continuation behavior.
- Duck, speech, and restore remain bounded lifecycle concerns.
- Manual stop and no-auto-resume boundaries remain preserved.

## 9. Verification Mapping
Required tests:
- Preferred speaker unavailable fallback to alternate configured validated speaker.
- No valid configured speakers refusal path.
- Merged-room grouped path with degraded constituent.
- Existing no-replacement-discovery regression path.

Requirement mapping:
- EC-REQ-033: deterministic speaker fallback when preferred speaker is unavailable.
- EC-REQ-063: deterministic degraded-path behavior and explainability.

## 10. Change Control Notes
Any future fallback extension must preserve:
- Room Configuration authority.
- Deterministic decision ordering.
- No-discovery boundary.
- Explicit explainability fields in runtime outputs and validation artifacts.
