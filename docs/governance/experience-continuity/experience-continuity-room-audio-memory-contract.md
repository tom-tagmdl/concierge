# Experience Continuity Room Audio Memory Contract

## 1. Purpose
This artifact defines the EC-D-01 room-audio continuity memory contract for preserving room-level audio outcomes in V2.

Preserved V1 user outcomes:
- A room can remember and reuse room-level audio volumes.
- Room audio behavior uses configured room speaker outputs.
- Music, duck, and TTS channel memories remain separate.
- Room-aware audio continuity remains stable and explainable.

Retired V1 mechanisms:
- Helper-schema storage as runtime authority.
- Runtime speaker discovery as authority replacement.
- Global merged-room persistent volume memory.

## 2. Governance Sources
- [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md)
- [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md)
- [docs/governance/experience-continuity/experience-continuity-outcome-preservation-review.md](docs/governance/experience-continuity/experience-continuity-outcome-preservation-review.md)
- [docs/governance/experience-continuity/experience-continuity-epic-and-issue-roadmap.md](docs/governance/experience-continuity/experience-continuity-epic-and-issue-roadmap.md)
- [docs/governance/experience-continuity/experience-continuity-requirements-backlog.md](docs/governance/experience-continuity/experience-continuity-requirements-backlog.md)
- [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md)
- [docs/governance/experience-continuity/v1-capability-reconstruction.md](docs/governance/experience-continuity/v1-capability-reconstruction.md)
- [docs/governance/experience-continuity/experience-continuity-runtime-terminology-reference.md](docs/governance/experience-continuity/experience-continuity-runtime-terminology-reference.md)
- [docs/governance/experience-continuity/experience-continuity-helper-family-disposition-matrix.md](docs/governance/experience-continuity/experience-continuity-helper-family-disposition-matrix.md)
- [docs/governance/experience-continuity/experience-continuity-preference-resolution-contract.md](docs/governance/experience-continuity/experience-continuity-preference-resolution-contract.md)
- [docs/governance/experience-continuity/experience-continuity-identity-safety-context-matrix.md](docs/governance/experience-continuity/experience-continuity-identity-safety-context-matrix.md)
- [docs/governance/experience-continuity/experience-continuity-learning-governance-and-reversibility.md](docs/governance/experience-continuity/experience-continuity-learning-governance-and-reversibility.md)
- [docs/governance/experience-continuity/experience-continuity-room-aware-lighting-command-behavior.md](docs/governance/experience-continuity/experience-continuity-room-aware-lighting-command-behavior.md)

## 3. Room Speaker Authority
Room Configuration is the authority source for room speaker membership.

Authoritative room inputs:
- `room.media_player_entity_ids`
- `room.speaker_entity_ids`

Authority rules:
- Runtime may validate configured speakers for existence and availability.
- Runtime validation does not discover replacement speakers.
- Runtime validation does not infer speakers from labels, areas, or broad scans.

## 4. Room Audio Memory Model
Room-audio memory uses room-scoped continuity usual-state records, keyed by room and channel.

State ID format:
- `room_audio::<area_id>::music`
- `room_audio::<area_id>::duck`
- `room_audio::<area_id>::tts`

Persistence model:
- continuity type: usual_state
- scope: room
- scope_ref: area_id
- values:
  - channel
  - volume_pct
  - area_id
  - configured_speakers
- metadata:
  - policy_name
  - policy_decision
  - stability evidence
  - membership_source

## 5. Music / Duck / TTS Channel Separation
Channels are independent continuity concerns:
- `music`
- `duck`
- `tts`

Separation rules:
- Learning writes are channel-specific.
- Resolve/apply reads are channel-specific.
- `music` playback-start reads do not consume `duck` or `tts` values.
- Merged-room playback does not collapse channel memory into a single global value.

## 6. Governed Learning Rules
Learning follows EC-B-03 policy and remains non-blocking.

Eligibility conditions:
- learning policy enabled,
- ownership scope supported,
- stable room speaker volume evidence satisfied,
- safe context and entity eligibility satisfied.

Learning denial behavior:
- preserve prior room value,
- emit deterministic denial reason,
- keep flow non-blocking,
- keep explainability and reversibility metadata.

Default stability interval:
- 30 seconds

Policy feature key:
- `global_features.experience_continuity_room_audio_learning_policy.options.stability_seconds`

## 7. Playback Start Resolution
Playback-start resolution for room music volume:
1. Resolve room/composite context.
2. Resolve participating room speaker memberships from Room Configuration.
3. Validate configured speakers without replacing authority.
4. Resolve room music volume from room usual-state.
5. Fallback deterministically when missing/invalid.
6. Apply resolved room volume to configured speakers.
7. Emit explainability metadata and decision refs.

This issue resolves volume continuity only. It does not implement media selection/orchestration.

## 8. Merged-Room Audio Memory Rules
Merged-room behavior uses shared playback scope with room-scoped memory.

Rules:
- Grouped playback targets configured speakers across participating constituent rooms.
- Each constituent room keeps independent `music`, `duck`, and `tts` memory.
- No persistent merged-room volume memory is created.
- No constituent-room memory is overwritten by merged-room playback.
- Exiting merged-room context must preserve constituent-room memory values.

## 9. Fallback Matrix
| Condition | Behavior | Fallback Reason | Source | Discovery Replacement |
| --- | --- | --- | --- | --- |
| no room scope | safe no-op | room_scope_missing | room_audio_fallback_policy | prohibited |
| composite missing | safe no-op | composite_configuration_missing | room_audio_fallback_policy | prohibited |
| no configured speakers | safe no-op | configured_speaker_mapping_missing | room_audio_fallback_policy | prohibited |
| configured speaker missing | safe no-op for that room | configured_speaker_missing | room_audio_fallback_policy | prohibited |
| configured speaker unavailable | safe no-op for that room | configured_speaker_unavailable | room_audio_fallback_policy | prohibited |
| configured speaker invalid | safe no-op for that room | configured_speaker_invalid | room_audio_fallback_policy | prohibited |
| missing room channel memory | apply fallback volume | room_audio_value_missing | current_state_volume or safe_default_volume | prohibited |
| invalid room channel memory | apply fallback volume | room_audio_value_invalid | current_state_volume or safe_default_volume | prohibited |
| learning denied | preserve previous memory | policy denial reason | learning governance policy | prohibited |

Safe default volume:
- 35 percent

## 10. Validation Scenarios
Required EC-D-01 validation scenarios:
1. Configured room speaker authority.
2. Stable music volume learning.
3. Stable duck volume learning.
4. Stable TTS volume learning.
5. Unstable volume rejected.
6. Music start applies learned room music volume.
7. Missing room music volume fallback.
8. Music/duck/TTS values remain separate.
9. Merged-room grouped output targets all configured constituent speakers.
10. Merged-room Room A keeps independent music/duck/TTS memory.
11. Merged-room Room B keeps independent music/duck/TTS memory.
12. No single merged-room volume persisted.
13. Exiting merged-room context does not corrupt constituent-room memory.
14. Runtime discovery not used.
15. V1 room-audio outcome preserved via configured speaker + room-memory model.

## 11. Non-Goals
This contract does not implement:
- duck/restore lifecycle,
- Sonos duck/restore lifecycle behavior,
- Music Assistant orchestration,
- media continuation,
- Follow-Me Music,
- person-scoped audio preference behavior,
- persistent merged-room audio memory,
- runtime speaker discovery,
- production Home Assistant changes.
