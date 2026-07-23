# Experience Continuity Runtime Terminology Reference

## Purpose
This artifact codifies the runtime terminology introduced by EC-A-01 so downstream Experience Continuity issues can reuse shared concepts without recreating V1 implementation mechanisms.

This artifact is terminology and model guidance only.

It does not implement lighting behavior, audio behavior, media behavior, routine replacement behavior, Follow-Me Music, or production Home Assistant changes.

## Governing Sources
- docs/governance/experience-continuity/adr-experience-continuity-architecture.md
- docs/governance/experience-continuity/experience-continuity-scope-decisions.md
- docs/governance/experience-continuity/experience-continuity-requirements-backlog.md
- docs/governance/experience-continuity/experience-continuity-epic-and-issue-roadmap.md
- docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md
- docs/governance/experience-continuity/v1-capability-reconstruction.md

## Continuity Terminology Reference
| Concept | Definition | Model Representation | Validation / Serialization | Intended Downstream Consumer |
| --- | --- | --- | --- | --- |
| Experience Snapshot | A normalized continuity state record representing captured experience context before an interruption or managed transition. | `ExperienceSnapshot` | Requires non-empty snapshot identifier, scope, scope reference, captured timestamp, event identifier, and non-empty state payload. Supports `as_dict()` / `from_dict()` round trip. | Lighting, audio, media, and future restoration workflows that need captured operational context. |
| Usual State | A learned or configured baseline state used as a reference for continuity decisions. | `UsualState` | Requires non-empty state identifier, scope, scope reference, basis, timestamp, and non-empty value payload. Supports `as_dict()` / `from_dict()` round trip. | Lighting usual-state work, room audio defaults, and future preference-backed continuity reads. |
| Operational Restore | A restore concept representing reconstruction of prior operational conditions without applying preference overrides. | `OperationalRestore` | Requires non-empty restore identifier, scope, scope reference, source snapshot identifier, timestamp, and non-empty target-state payload. Supports `as_dict()` / `from_dict()` round trip. | Future restore execution work that replays captured operational state. |
| Preference Restore | A restore concept representing reconstruction of preference-driven outcomes according to ownership boundaries and continuity policy. | `PreferenceRestore` | Requires non-empty restore identifier, scope, scope reference, timestamp, and non-empty target-state payload. Supports `as_dict()` / `from_dict()` round trip with optional preference references. | Future preference-driven restore and default-application workflows. |
| Continuity Confidence | A normalized confidence indicator expressing how trustworthy a continuity determination is. | `ContinuityConfidence` | Requires score in `[0.0, 1.0]`, normalized confidence band, and optional reason codes. Supports `as_dict()` / `from_dict()` round trip. | Future decision layers that consume identity, room, or state confidence without inventing behavior in EC-A-01. |
| Continuity Event Identity | A stable event classification identity enabling continuity processing across domains. | `ContinuityEventIdentity` | Requires non-empty event identifier, event type, scope, scope reference, source domain, and occurred timestamp. Supports `as_dict()` / `from_dict()` round trip. | Future continuity event processing, diagnostics, and cross-domain correlation. |

## Model-to-Governance Mapping
| Concept | Purpose | Governing Source | Requirement Coverage | Downstream Issue Usage | Intentionally Not Implemented In EC-A-01 |
| --- | --- | --- | --- | --- | --- |
| Experience Snapshot | Preserve captured operational context as a first-class runtime concept. | ADR Decision 4; ADR Core Concepts; Roadmap EC-A-01 scope | EC-REQ-001, EC-REQ-010, EC-REQ-011 | EC-C, EC-D, and future restore/resume work | No restore execution, no lighting/audio/media behavior, no HA runtime capture pipeline |
| Usual State | Represent learned or configured continuity baselines separately from snapshots. | ADR Decision 4; ADR Core Concepts; Requirements backlog continuity state model section | EC-REQ-010, EC-REQ-011 | EC-C learned/usual lighting; EC-D room-level volume baselines; future default behaviors | No learning pipeline, no room/person preference resolver |
| Operational Restore | Distinguish restoring previous operational conditions from replaying preferences. | ADR Decision 4; ADR Core Concepts; Requirements backlog EC-REQ-011 | EC-REQ-010, EC-REQ-011 | Future restore orchestration issues | No restore executor, no scene/media/light actuation |
| Preference Restore | Distinguish preference-driven reconstruction from operational replay. | ADR Decision 5; ADR Core Concepts; Requirements backlog EC-REQ-011 | EC-REQ-010, EC-REQ-011 | Future preference-aware continuity issues | No preference hierarchy behavior, no person-resolution behavior |
| Continuity Confidence | Normalize trust signals without moving identity ownership into Concierge. | ADR Decisions 3, 5, and 6 | EC-REQ-001 | Future decision and policy layers that consume external confidence | No identity scoring, no personalization behavior |
| Continuity Event Identity | Provide stable event references without implementing event classification behavior. | ADR Core Concepts; Roadmap EC-A-01; future EC-A-02 dependency | EC-REQ-001 | EC-A-02 and later diagnostics/continuity workflows | No event classifier, no scope-resolution engine |

## Ownership-Boundary Alignment
The terminology model remains aligned to the approved ownership boundary model:

Entity-scoped:
- learned light or lamp brightness
- learned light or lamp color temperature where supported
- learned light or lamp color or effect where supported

Room-scoped:
- room music volume
- room duck volume
- room TTS volume
- room last song
- room last genre played
- room media context
- configured room speakers and output surfaces

Person-scoped:
- preferred artist
- preferred genre
- preferred album
- preferred playlist
- music affinity

Household-scoped:
- guest defaults
- unknown-speaker defaults
- unavailable-identity fallback
- silence-is-success policy
- capability-not-available policy

Post-install / future composition:
- BLE or presence-based Follow-Me Music
- cross-room media transfer
- person preference plus current room speaker composition

The EC-A-01 models preserve these boundaries as scope-carrying value objects. They do not classify events, resolve preferences, or execute restores.

## V1 Outcome Preservation And V2 Replacement
- V1 outcome preserved: Experience Continuity becomes an explicit runtime vocabulary instead of remaining implicit in scripts, helpers, and automations.
- V2 architectural replacement: downstream implementation uses typed continuity models and validated serialization rather than preserving V1 helper schema or script structure.
- Install-gate implication: terminology, validation, and mapping evidence exist before any domain behavior issue attempts to implement continuity outcomes.

## Non-Goal Protection
EC-A-01 terminology models do not implement:
- lighting behavior
- audio behavior
- media behavior
- restore execution behavior
- continue or resume behavior
- preference resolution hierarchy
- room capability awareness
- Music Assistant orchestration
- Sonos fallback behavior
- merged-room playback behavior
- Follow-Me Music
- BLE-based following
- Bedtime routine replacement
- Good Morning routine replacement
- Goodnight or Good Night routine replacement
- Primary Bedroom Alarm replacement
- one-to-one V1 helper schema preservation
- production Home Assistant changes