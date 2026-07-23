# Experience Continuity Manual Stop Suppression Contract

## 1. Purpose
This artifact defines the EC-E-04 manual-stop suppression and cooldown contract for Concierge V2.

It preserves the V1 user outcome that an intentional stop prevents an unwanted automatic restart, while still allowing explicit user-directed continuation when governed policy allows it.

Suppression is room-scoped.
Suppression is not global-scoped.
Suppression is not person-owned.

## 2. Governance Sources
- [ADR: Experience Continuity Architecture](adr-experience-continuity-architecture.md)
- [Experience Continuity Scope Decisions](experience-continuity-scope-decisions.md)
- [Experience Continuity Outcome Preservation Review](experience-continuity-outcome-preservation-review.md)
- [Experience Continuity Epic and Issue Roadmap](experience-continuity-epic-and-issue-roadmap.md)
- [Experience Continuity Requirements Backlog](experience-continuity-requirements-backlog.md)
- [V1-to-V2 Capability Parity Matrix](v1-to-v2-capability-parity-matrix.md)
- [V1 Capability Reconstruction](v1-capability-reconstruction.md)
- [Experience Continuity Room Media Continuation Contract](experience-continuity-room-media-continuation-contract.md)
- [Experience Continuity Room Media Memory Contract](experience-continuity-room-media-memory-contract.md)
- [Experience Continuity Preference Resolution Contract](experience-continuity-preference-resolution-contract.md)
- [#412 Room Runtime Authority Model](tmp/ec_issue_updates/412.md)

## 3. Manual Stop Detection
Manual stop is detected through the room-scoped continuity state already captured by Experience Continuity.

Detection inputs:
- `manual_stop`
- `manual_stop_cooldown_until`
- `manual_stop_cooldown_seconds`
- room media continuity context captured from the authoritative room

Detection authority:
- Room-scoped continuity memory is authoritative for suppression state.
- Room Configuration remains authoritative for room identity and membership.
- Music Assistant remains a content provider only and does not own suppression policy.

This contract does not create a new stop model.
It reuses the existing room-media continuity fields and suppresses auto-resume when those fields indicate a still-active cooldown.

## 4. Suppression Ownership
Suppression owner is the room.

Room ownership rules:
- the selected authoritative room owns the suppression state
- merged-room playback does not create merged suppression memory
- suppression does not leak from one room to another
- no global suppression record is created

Merged-room ownership follows the same deterministic source-room rule used by room media memory:
- primary room first when available
- initiating room when it already owns usable context
- deterministic participating-room priority otherwise

## 5. Cooldown Rules
Cooldown exists after explicit manual stop.

Cooldown storage and evaluation:
- cooldown expiration is captured in `manual_stop_cooldown_until` when available
- `manual_stop_cooldown_seconds` may be used when an expiration timestamp is not present
- active cooldown is evaluated deterministically at runtime
- expired cooldown must stop suppressing governed continuation

This contract does not introduce a new global cooldown duration.
The authoritative expiration value is carried in the room-scoped continuity state.

Cooldown behavior:
- during cooldown, automatic restore or auto-start is denied
- after cooldown expires, governed continuation may proceed
- explicit user-directed continuation remains permitted when policy allows it

## 6. Continuation Integration
Room media continuation consumes room media memory and then checks suppression.

Decision order:
1. resolve room media context
2. evaluate suppression state
3. evaluate cooldown state
4. deny governed continuation if cooldown is active
5. allow governed continuation if cooldown is expired and policy otherwise permits it

When cooldown is active, the denial must be explainable and must not silently restart media.

## 7. Music Assistant Independence
Music Assistant remains the content provider.

Music Assistant does not control suppression policy.

This contract behaves identically whether Music Assistant is:
- enabled
- disabled
- unavailable

Suppression is decided inside Experience Continuity, not by the provider.

## 8. Merged-Room Suppression Rules
Playback scope and suppression scope remain distinct.

In merged-room playback:
- one room still owns suppression state
- other rooms do not inherit that state automatically
- suppression does not create merged-room persistent memory
- merged-room playback remains grouped output only

If Kitchen is suppressed and Living Room is not, suppression applies only to the room that owns the suppression state.

## 9. Follow-Me Exclusion Boundary
This contract does not implement Follow-Me Media.

It does not implement:
- cross-room media transfer
- playback migration
- BLE following
- person tracking playback

Suppression remains room-scoped.

## 10. Validation Scenarios
The governed validation set must cover these scenarios:
1. manual stop detected
2. suppression state created
3. suppression persisted
4. cooldown active
5. continuation denied during cooldown
6. cooldown expiration
7. explicit continue request
8. Music Assistant enabled
9. Music Assistant disabled
10. provider unavailable
11. merged-room suppression ownership
12. no suppression leakage
13. no merged-room persistent suppression
14. no global suppression state
15. no Follow-Me behavior
16. V1 manual-stop outcome preserved

## 11. Retention Rules
Retention follows the room-scoped continuity record.

Retention guidance:
- keep one authoritative suppression record per room
- overwrite on later room-scoped capture
- preserve constituent-room independence
- do not create a separate merged suppression store
- do not promote suppression into person preference truth

## 12. Non-Goals
This contract does not implement:
- Follow-Me Media
- BLE following
- cross-room migration
- provider-owned suppression
- person-owned suppression
- global suppression state
- merged-room persistent suppression state
- room authority bypass
- production Home Assistant changes