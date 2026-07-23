# Experience Continuity Room Media Memory Contract

## 1. Purpose
This artifact defines the EC-E-03 room-media memory contract for preserving room-level media context in Concierge V2.

It preserves the V1 user outcome that a room remembers what was previously playing and can later continue that experience in a governed and deterministic way.

Room media memory is room-scoped.
Room media memory is not global-scoped.
Room media memory is not person preference.

## 2. Governance Sources
- [ADR: Experience Continuity Architecture](adr-experience-continuity-architecture.md)
- [Experience Continuity Scope Decisions](experience-continuity-scope-decisions.md)
- [Experience Continuity Outcome Preservation Review](experience-continuity-outcome-preservation-review.md)
- [Experience Continuity Epic and Issue Roadmap](experience-continuity-epic-and-issue-roadmap.md)
- [Experience Continuity Requirements Backlog](experience-continuity-requirements-backlog.md)
- [V1-to-V2 Capability Parity Matrix](v1-to-v2-capability-parity-matrix.md)
- [V1 Capability Reconstruction](v1-capability-reconstruction.md)
- [Experience Continuity Preference Resolution Contract](experience-continuity-preference-resolution-contract.md)
- [Experience Continuity Media Provider Precedence Contract](experience-continuity-media-provider-precedence-contract.md)
- [Experience Continuity Room Media Continuation Contract](experience-continuity-room-media-continuation-contract.md)
- [#412 Room Runtime Authority Model](tmp/ec_issue_updates/412.md)

## 3. Room-Level Media Memory Ownership
Room Configuration remains authoritative for room ownership, room membership, room devices, room vocabulary, room assets, room information sources, and merged-room membership.

This contract stores room-level media memory only.
It does not create a new room-awareness model.
It attaches media memory to the authoritative room model already established by Room Configuration.

Ownership rule:
- primary room first when a merged-room context is available
- initiating room if it already owns usable media context
- otherwise deterministic participating-room priority

The selected room is the only room whose media memory is updated.
Constituent room memory remains independent.

## 4. Media Context Schema
The persisted room-media record uses the existing Concierge continuity usual-state model in [custom_components/concierge/storage.py](../../custom_components/concierge/storage.py).

Required stored values:
- room_id
- source_room_id
- source_room_selection_reason
- provider_source
- provider_media_id
- media_type
- media_query
- last_song
- last_genre
- manual_stop
- manual_stop_cooldown_until
- manual_stop_cooldown_seconds
- captured_at

Provider-compatible nested metadata:
- last_media.provider_source
- last_media.provider_media_id
- last_media.media_type
- last_media.track_title
- last_media.artist_name
- last_media.album_name
- last_media.genre
- last_media.media_query
- last_media.captured_at

Optional explainability metadata:
- policy_name
- source_room_selection_reason
- source_room_candidates
- merged_room_participation
- captured_at

`media_query` is the fallback search phrase used by continuation behavior.
It may be a track title, media identifier, genre, or another provider-compatible normalized query.

## 5. Music Assistant-Compatible Context Rules
When Music Assistant is enabled, room media capture must retain enough metadata for future provider-compatible re-resolution.

This contract treats the following as sufficient Music Assistant-compatible context:
- provider_source
- provider_media_id
- media_type
- track_title
- artist_name
- album_name
- genre
- media_query

The contract does not require a deep Music Assistant redesign.
It does not make Sonos Favorites the canonical media-memory format.
It does not introduce person music affinity persistence here.

## 6. Persistence Rules
Room-media capture persists into room-scoped usual-state records keyed as `room_media::<area_id>`.

Persistence rules:
- writes are room-scoped
- updates overwrite the prior record for that room
- capture updates timestamp metadata
- merged-room playback does not create merged persistent media memory
- capture must not promote room history into person preference state

The storage surface is the existing Concierge usual-state store.

## 7. Retrieval Rules
Retrieval reads the room-media record for the authoritative selected room.

If context exists:
- return the room-scoped media memory
- expose source room and selection reason
- expose manual-stop state and cooldown metadata
- expose provider-compatible metadata for continuation

If context is missing:
- return a safe governed fallback path
- do not synthesize global media history
- do not infer person preference from room history

Room media retrieval remains room-scoped even when continuation executes in a merged-room playback scope.

## 8. Merged-Room Ownership Rules
Merged-room playback expands playback scope but not memory scope.

Write ownership is deterministic:
- primary room when available
- initiating room when it already owns usable context
- deterministic participating-room priority otherwise

The selected room receives the updated media memory.
Other rooms keep their own values intact.

This contract does not create:
- merged-room persistent media memory
- merged-room persistent playback ownership
- constituent-room overwrite by default

## 9. Follow-Me Exclusion Boundary
This contract does not implement Follow-Me Media.

It does not implement:
- cross-room media transfer
- playback migration
- BLE following
- person tracking playback

Room media memory remains room-scoped.

## 10. Validation Scenarios
The governed validation set must cover these scenarios:
1. capture last song
2. capture last genre
3. capture Music Assistant metadata
4. persist provider identifier
5. retrieve room media context
6. continuation consumption path
7. missing room media context
8. safe fallback behavior
9. merged-room playback write ownership
10. kitchen context preservation
11. living room context preservation
12. no merged-room persistent media context
13. no person preference persistence
14. no global media context
15. no Follow-Me behavior
16. V1 room-level media memory outcome preserved

## 11. Retention Guidance
Room media memory should be retained until a newer capture overwrites the same room-scoped record.

Retention guidance:
- keep one authoritative last-media record per room
- preserve constituent-room independence
- overwrite on new playback capture for the same room
- do not add a separate merged-room persistence layer
- do not use room history as person preference truth

## 12. Non-Goals
This contract does not implement:
- Follow-Me Media
- person music preference persistence
- global last-media context
- deep Music Assistant redesign
- Sonos Favorites-only storage
- cross-room media migration
- merged-room persistent media ownership
- room authority bypass
- production Home Assistant changes