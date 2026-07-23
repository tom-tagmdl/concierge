# Experience Continuity Sonos Speech Continuity Policy

## 1. Purpose and Scope
This policy defines EC-D-02 bounded speech continuity behavior for room-scoped Sonos output in Concierge V2.

In scope:
- bounded duck, speech output, and restore lifecycle for room TTS output
- deterministic degraded behavior and explainability metadata
- strict separation between speech continuity and media continuation

Out of scope:
- media continuation orchestration
- Music Assistant orchestration
- Follow-Me music behavior
- autonomous replacement speaker discovery

## 2. Governance Authority Chain
Authority order used for this policy:
1. ADR and governance documents
2. Contracts
3. Models
4. Existing implementation
5. Existing tests
6. Issue #404 acceptance criteria
7. Inference only when explicitly labeled

Primary governance sources:
- docs/governance/experience-continuity/adr-experience-continuity-architecture.md
- docs/governance/experience-continuity/experience-continuity-scope-decisions.md
- docs/governance/experience-continuity/experience-continuity-requirements-backlog.md
- docs/governance/experience-continuity/experience-continuity-room-audio-memory-contract.md

## 3. Requirement Mapping
- EC-REQ-030: Concierge V2 provides Sonos speech output with explicit duck and restore behavior for in-scope room continuity interactions.
- EC-REQ-031: speech output continuity is separate from media continuation continuity.

This policy intentionally does not satisfy EC-REQ-041 and related continuation requirements.

## 4. Room Speaker Authority
Room speaker authority remains external and configuration-driven:
- source: room configuration media_player and speaker entity mappings
- Concierge validates configured entities at runtime
- Concierge does not discover replacement speakers when mappings are absent or invalid

## 5. Bounded Lifecycle Definition
The bounded lifecycle phases are:
1. resolve configured room speakers and validate availability
2. capture pre-duck state and pre-duck volume per participating speaker
3. apply duck level
4. apply speech volume and deliver room TTS
5. restore pre-duck volume where available
6. finalize with explainable outcome metadata

No phase includes play, resume, queue, or media continuation commands.

## 6. Channel-Level Volume Separation
Room-audio channels remain separate and room-scoped:
- music channel memory
- duck channel memory
- TTS channel memory

Speech continuity consumes duck and TTS channels only. It must not alter music continuation behavior.

## 7. Degraded and Fallback Behavior
Deterministic fallback behavior:
- if channel memory exists: use room learned value
- if channel memory missing or invalid: use current speaker state average when available
- if current speaker state unavailable: use safe default volume

Degraded paths remain bounded and must still attempt restore when possible.

## 8. Speech and Media Separation Guarantees
The following are mandatory runtime guarantees:
- speech lifecycle never implies media continuation
- paused or stopped pre-state must not be converted into play
- restore operations are volume-only and state-preserving
- manual stop respect remains intact

## 9. Merged-Room and Group Semantics
For merged-room context, room-level memory remains per constituent room and playback can be grouped by configured authority. This policy does not create composite-level persistent speech volume memory.

## 10. Diagnostics and Explainability Contract
Runtime outputs should include explainability metadata for:
- validated versus configured speakers
- pre-duck snapshots
- duck source and fallback reason
- speech source and fallback reason
- restore outcomes per speaker
- explicit flags proving no media continuation or playback resume was performed

## 11. Verification and Evidence Expectations
Verification should include:
- normal bounded lifecycle test coverage (duck, speech, restore)
- degraded-path coverage (missing memory, unavailable state, partial failures)
- explicit separation assertions proving no media continuation/resume behavior
- evidence artifacts in tmp/ documenting scenarios, coverage, and execution results
