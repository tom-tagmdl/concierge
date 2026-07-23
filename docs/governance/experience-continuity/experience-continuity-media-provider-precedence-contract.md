# Experience Continuity Media Provider Precedence Contract

## 1. Purpose
This artifact defines the governed provider-resolution contract for EC-E-01 room-level music playback.

It preserves the V1 user outcome of room-scoped music playback while replacing Sonos-Favorites-centric implementation assumptions with V2 provider-preferred orchestration.

## 2. Governance Sources
- docs/governance/experience-continuity/adr-experience-continuity-architecture.md
- docs/governance/experience-continuity/experience-continuity-scope-decisions.md
- docs/governance/experience-continuity/experience-continuity-outcome-preservation-review.md
- docs/governance/experience-continuity/experience-continuity-epic-and-issue-roadmap.md
- docs/governance/experience-continuity/experience-continuity-requirements-backlog.md
- docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md
- docs/governance/experience-continuity/v1-capability-reconstruction.md
- docs/governance/experience-continuity/experience-continuity-runtime-terminology-reference.md
- docs/governance/experience-continuity/experience-continuity-helper-family-disposition-matrix.md
- docs/governance/experience-continuity/experience-continuity-preference-resolution-contract.md
- docs/governance/experience-continuity/experience-continuity-identity-safety-context-matrix.md
- docs/governance/experience-continuity/experience-continuity-room-audio-memory-contract.md
- docs/governance/experience-continuity/experience-continuity-sonos-speech-continuity-policy.md
- docs/governance/experience-continuity/experience-continuity-audio-fallback-decision-matrix.md
- docs/governance/experience-continuity/experience-continuity-audio-gate-closure-package.md
- tmp/ec_issue_updates/412.md

## 3. Runtime Authority Order
EC-E media playback resolution consumes upstream authority in this order:
1. Room Configuration
2. Person Configuration
3. Asset Intelligence
4. Experience Continuity
5. Media Provider

Authority ownership for this issue:
- Room Configuration determines where playback occurs.
- Person Configuration determines whether personalization may be applied.
- Asset Intelligence remains external authority for asset metadata and relationships and is not reinterpreted as room-awareness for media playback in this issue.
- Experience Continuity contributes room audio memory and optional person-scoped preference signals.
- Media Provider determines what content is played and how that content is orchestrated.

Music Assistant must not become the source of room awareness.

## 4. Provider Precedence Rules
Provider precedence is configuration-governed.

When Concierge configuration sets `media_provider = music_assistant`:
- Music Assistant is the preferred provider for media/content resolution.
- Music Assistant is the preferred provider for playback orchestration.
- Concierge must not treat Sonos Favorites as the primary search/catalog authority.

When Concierge configuration does not enable Music Assistant:
- this issue does not invent an alternate provider orchestration path,
- playback request handling must follow deterministic fallback or refusal behavior,
- room output authority must remain unchanged.

## 5. Music Assistant Preferred Resolution
When Music Assistant is enabled and available:
- `play jazz` resolves through Music Assistant,
- genre requests resolve through Music Assistant,
- artist requests resolve through Music Assistant,
- album requests resolve through Music Assistant,
- general music requests resolve through Music Assistant.

Supported request intent categories for this issue:
- general music
- genre
- artist
- album
- playlist

Room-level playback outcome is preserved while provider-specific catalog/search behavior moves to Music Assistant.

## 6. Room Authority Rules
Room Configuration remains authoritative for output routing.

Provider resolution must not choose playback speakers.

Output routing always comes from configured room speaker membership:
- room media player entity ids
- room speaker entity ids
- merged-room configured constituent participation

Provider success does not authorize runtime speaker discovery, global playback targeting, or authority bypass.

Runtime room-awareness inputs for this issue are limited to configuration-authored room and merged-room membership. Media Provider results must not redefine:
- room membership,
- merged-room membership,
- room vocabulary,
- room assets,
- room information sources,
- configured speaker outputs.

## 7. Identity-Aware Resolution Rules
Person-scoped music preference signals may be consumed only when:
- identity confidence is high enough,
- identity state is known,
- personalization policy allows usage,
- and the signal is supplied through governed input context.

Examples of person-scoped signals:
- preferred artist
- preferred genre
- preferred album
- preferred playlist
- music affinity

This issue consumes optional bounded preference inputs.

It does not create a new persisted music preference store.

## 8. Guest / Low Confidence Rules
When identity is:
- guest
- unknown
- unavailable
- low confidence

person-specific music preferences must not be applied.

Fallback preference order remains:
- room default
- household default
- system safe default

Playback routing remains room-scoped even when personalization is denied.

## 9. Merged-Room Playback Rules
Merged-room behavior expands playback scope but not memory scope.

When room context resolves to a merged room:
- Music Assistant remains the preferred provider when enabled,
- playback targets all configured participating speakers,
- constituent-room music volume memory remains independent,
- constituent-room duck volume memory remains independent,
- constituent-room TTS volume memory remains independent.

This issue does not create:
- merged-room persistent media preference memory,
- merged-room persistent media history ownership,
- merged-room persistent volume memory.

## 10. Fallback / Refusal Matrix
| Condition | Behavior | Reason Code | Notes |
| --- | --- | --- | --- |
| Music Assistant enabled and available | play through Music Assistant | preferred_provider_configured_and_available | normal path |
| Music Assistant disabled in Concierge config | deterministic refusal | media_provider_disabled | no ad-hoc provider switching |
| Music Assistant configured but unavailable | deterministic refusal | music_assistant_unavailable | no hidden provider substitution |
| configured room speakers missing/invalid/unavailable | deterministic refusal | configured room authority failure | provider success does not bypass room authority |
| guest or low-confidence identity | room/household/system default query selection only | guest_identity_blocked / low_confidence_identity_blocked | no person preference use |
| provider request cannot be personalized safely | use non-personalized query path | identity policy reason | routing still room-scoped |

## 11. Follow-Me Exclusion Boundary
Merged-room playback is grouped playback only.

It is not Follow-Me Media.

This issue does not implement:
- cross-room media transfer,
- playback migration between rooms,
- BLE-following playback,
- person-following playback,
- dynamic handoff between room contexts.

True cross-room Follow-Me Media remains post-install enhancement scope.

## 12. Validation Scenarios
Required validation scenarios for this contract:
1. Play jazz using Music Assistant.
2. Play genre using Music Assistant.
3. Play artist using Music Assistant.
4. Play album using Music Assistant.
5. General music playback using Music Assistant.
6. Music Assistant disabled refusal.
7. Music Assistant unavailable refusal.
8. High-confidence identity uses bounded preference input.
9. Guest identity suppresses person preference input.
10. Low-confidence identity suppresses person preference input.
11. Configured room speakers remain authoritative targets.
12. Merged-room grouped playback targets all configured speakers.
13. Constituent-room audio memory remains independent.
14. No merged-room persistent media memory is created.
15. No room authority bypass occurs.
16. No Follow-Me behavior is introduced.
17. Governed fallback behavior remains deterministic.
18. Governed refusal behavior remains deterministic.
19. V1 room-level playback outcome is preserved.
20. Music Assistant preferred-provider rule is enforced.

## 13. Non-Goals
This contract does not implement:
- Follow-Me Media,
- BLE music following,
- Music Assistant as a mandatory provider when disabled,
- Sonos Favorites as the primary search/catalog path when Music Assistant is enabled,
- global playback routing,
- room authority bypass,
- merged-room persistent media memory,
- merged-room preference ownership,
- person-scoped output routing,
- dynamic speaker discovery,
- production Home Assistant changes.
