# Experience Continuity Outcome Preservation Review

## Status
Architecture alignment review complete.

## Objective
Preserve V1 user outcomes while removing V1 implementation assumptions from Experience Continuity roadmap language.

## Governing Artifacts Reviewed
- docs/governance/experience-continuity/adr-experience-continuity-architecture.md
- docs/governance/experience-continuity/experience-continuity-scope-decisions.md
- docs/governance/experience-continuity/experience-continuity-requirements-backlog.md
- docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md
- docs/governance/experience-continuity/v1-capability-reconstruction.md
- docs/governance/experience-continuity/experience-continuity-epic-and-issue-roadmap.md
- Current open Experience Continuity epics and issues (#384 through #419)

## Classification Legend
- PRESERVE: V1 outcome remains valid and issue already aligns to V2 architecture.
- REDESIGN: V1 outcome remains valid, but wording/mechanism still implies V1-era implementation patterns.
- SUPERSEDED: V1 implementation approach is replaced by stronger V2 architectural capability.
- RETIRE: Capability should not be implemented in this roadmap scope.

## State Scope Boundary Memorialization
This boundary is architectural ownership guidance, not implementation schema:

Entity-scoped:
- learned light/lamp brightness
- learned light/lamp color temperature, where supported
- learned light/lamp color/effect, where supported

Room-scoped:
- room music volume
- room duck volume
- room TTS volume
- room last song
- room last genre played
- room media context
- configured room speakers/output

Person-scoped:
- preferred artist
- preferred genre
- preferred album
- preferred playlist
- music affinity/play something I like

Household-scoped:
- guest defaults
- unknown-speaker defaults
- unavailable-identity fallback
- silence-is-success policy
- capability-not-available policy

Post-install/future composition:
- BLE/presence-based Follow-Me Music
- cross-room media transfer
- person preference plus current room speaker composition

## Playback Scope vs Memory Scope
Playback scope determines which speakers participate in an active audio event.

Memory scope determines where continuity state is persisted.

Merged-room behavior boundary:
- merged-room playback is shared across participating configured speakers for active music/TTS/Concierge output events.
- merged-room playback does not create merged persistent audio/media preference memory by default.
- constituent-room memory remains independent (music/duck/TTS volumes and room-level media context).
- merged-room playback is distinct from Follow-Me Music.

## Epic-Level Review

### EC-A: Experience Continuity Foundation
- Current Issue: Epic EC-A: Experience Continuity Foundation
- Classification: PRESERVE
- Current Outcome: Shared continuity model and terms exist before domain implementation.
- V1 Implementation Pattern: V1 implicit continuity spread across scripts/helpers.
- Recommended V2 Mechanism: Explicit Experience Continuity runtime model plus diagnostics.
- Recommended Issue Changes: Keep issue set, emphasize model-first and authority boundaries.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Foundation-first sequencing is correct and ADR-aligned.

### EC-B: Preference Resolution and Identity Safety
- Current Issue: Epic EC-B: Preference Resolution and Identity Safety
- Classification: PRESERVE
- Current Outcome: Safe personalization and deterministic defaults.
- V1 Implementation Pattern: Limited room/helper-based memory with lighter identity governance.
- Recommended V2 Mechanism: Explicit preference hierarchy plus Voice Identity fail-closed consumption.
- Recommended Issue Changes: Memorialize person-scoped music preferences as default and treat person+room music preferences as explicit exceptions only.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Matches ADR decisions 5 through 7.

### EC-C: Lighting Continuity
- Current Issue: Epic EC-C: Lighting Continuity
- Classification: PRESERVE
- Current Outcome: Usual lighting and room-aware actuation parity outcomes.
- V1 Implementation Pattern: Helper-backed brightness learning and restore scripts.
- Recommended V2 Mechanism: Experience Continuity state plus preference hierarchy, room definitions, and person context.
- Recommended Issue Changes: Clarify no helper-shape recreation.
- Required Title Changes: No epic title change.
- Required Scope Changes: No change.
- Architectural Reasoning: Outcome remains valid, mechanism must stay V2-governed.

### EC-D: Audio Continuity and Sonos Speech
- Current Issue: Epic EC-D: Audio Continuity and Sonos Speech
- Classification: REDESIGN
- Current Outcome: Room-voice continuity with duck/restore and safe fallback.
- V1 Implementation Pattern: Helper-backed speaker profiles.
- Recommended V2 Mechanism: Audio preference resolution across person, room, time, defaults.
- Recommended Issue Changes: Reframe profile work as preference resolution, not helper recreation.
- Required Title Changes: No epic title change.
- Required Scope Changes: No change.
- Architectural Reasoning: Outcome preserved; mechanism updated to ADR preference model.

### EC-E: Media Continuity
- Current Issue: Epic EC-E: Media Continuity
- Classification: PRESERVE
- Current Outcome: Room-aware play and continue/resume continuity outcomes.
- V1 Implementation Pattern: Script-based room media resolver and helper state.
- Recommended V2 Mechanism: Experience Continuity state model plus provider-aware orchestration where Music Assistant is preferred when enabled.
- Recommended Issue Changes: Make provider distinction explicit: Music Assistant for content resolution/orchestration when enabled, configured room speakers (including Sonos) for output path, Experience Continuity for room state/resume/fallback policy.
- Required Title Changes: No epic title change.
- Required Scope Changes: No change.
- Architectural Reasoning: Initial gate scope is correct and distinct from post-install follow-me.

### EC-F: Room Capability Awareness and Monitoring Follow-Ups
- Current Issue: Epic EC-F: Room Capability Awareness and Monitoring Follow-Ups
- Classification: PRESERVE
- Current Outcome: User can ask what a room can do and get monitoring follow-up answers.
- V1 Implementation Pattern: Runtime discovery/inference through scripts and labels.
- Recommended V2 Mechanism: Room Configuration authored room definitions and capability mappings as authoritative runtime source.
- Recommended Issue Changes: Rename and reword toward authoritative metadata answering.
- Required Title Changes: Rename epic wording from discovery to awareness/answering.
- Required Scope Changes: No change.
- Architectural Reasoning: Outcome is preserved while implementation authority moves to configuration-authored room definitions rather than runtime inference.

### EC-G: Guardrails, Failure Handling, and Silence-Is-Success
- Current Issue: Epic EC-G: Guardrails, Failure Handling, and Silence-Is-Success
- Classification: PRESERVE
- Current Outcome: Calm, safe, deterministic behavior under failures.
- V1 Implementation Pattern: Implicit quiet behavior and script-level refusal.
- Recommended V2 Mechanism: Explicit policy controls and testable guardrail matrix.
- Recommended Issue Changes: Keep as-is.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Fully aligned to ADR guardrail policy.

### EC-H: Production Install Gate and Validation
- Current Issue: Epic EC-H: Production Install Gate and Validation
- Classification: PRESERVE
- Current Outcome: Structured pass/fail replacement gate with evidence package.
- V1 Implementation Pattern: No equivalent explicit gate package.
- Recommended V2 Mechanism: Requirement- and behavior-traceable readiness gate.
- Recommended Issue Changes: Keep as-is.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Required by ADR decision 10 and backlog gate requirements.

## Issue-Level Review

### EC-A Issues

#### EC-A-01
- Current Issue: EC-A-01 Create Experience Continuity Runtime Model and Terminology
- Classification: PRESERVE
- Current Outcome: Shared continuity vocabulary and model baseline.
- V1 Implementation Pattern: Implicit script/helper semantics.
- Recommended V2 Mechanism: Explicit continuity runtime model.
- Recommended Issue Changes: No functional change.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Correct first-step dependency.

#### EC-A-02
- Current Issue: EC-A-02 Implement Continuity Scope and Event Classification
- Classification: PRESERVE
- Current Outcome: Deterministic scope/event classification.
- V1 Implementation Pattern: Event-specific script logic.
- Recommended V2 Mechanism: Unified scope/event model with diagnostics.
- Recommended Issue Changes: Keep wording on diagnostics traceability.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Needed for explainability and install-gate validation.

#### EC-A-03
- Current Issue: EC-A-03 Define V1 Helper-Backed State Disposition and V2 State Strategy
- Classification: REDESIGN
- Current Outcome: Legacy helper families receive governed disposition.
- V1 Implementation Pattern: Helper schema as behavior storage contract.
- Recommended V2 Mechanism: Disposition policy only; V2 schema authority stays independent.
- Recommended Issue Changes: Emphasize disposition and replacement strategy over helper migration mechanics.
- Required Title Changes: Optional refinement to Legacy State Family Disposition and V2 Strategy.
- Required Scope Changes: No change.
- Architectural Reasoning: Preserve migration governance without reifying V1 storage shapes.

#### EC-A-04
- Current Issue: EC-A-04 Add Continuity Diagnostics and Explainability Scaffolding
- Classification: PRESERVE
- Current Outcome: Supportable decision traces.
- V1 Implementation Pattern: Limited/no centralized decision diagnostics.
- Recommended V2 Mechanism: Structured diagnostics aligned to authority boundaries.
- Recommended Issue Changes: No change.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Required for closure evidence quality.

### EC-B Issues

#### EC-B-01
- Current Issue: EC-B-01 Implement Preference Resolution Hierarchy
- Classification: PRESERVE
- Current Outcome: Deterministic preference ordering.
- V1 Implementation Pattern: Partial heuristic/room-centric behavior.
- Recommended V2 Mechanism: ADR hierarchy with explicit precedence.
- Recommended Issue Changes: Clarify that preferred artist/genre/album/playlist and music affinity are person-scoped defaults; room media context remains room-scoped; person+room music preferences are explicit exception behavior only.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Core architectural replacement for implicit V1 ordering.

#### EC-B-02
- Current Issue: EC-B-02 Implement Identity Confidence and Guest Default Policy
- Classification: PRESERVE
- Current Outcome: Safe fail-closed personalization.
- V1 Implementation Pattern: Guest/label controls with less formalized confidence handling.
- Recommended V2 Mechanism: Voice Identity confidence consumption and policy guardrails.
- Recommended Issue Changes: No change.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Directly aligned to ADR decision 6.

#### EC-B-03
- Current Issue: EC-B-03 Implement Learning Permission Boundaries and Non-Blocking Policy
- Classification: PRESERVE
- Current Outcome: Safe learning with policy constraints.
- V1 Implementation Pattern: Helper/script writes tied to specific command flows.
- Recommended V2 Mechanism: Governed async learning with reversible outcomes.
- Recommended Issue Changes: No change.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Matches ADR decision 7 and EC-REQ-080/081.

### EC-C Issues

#### EC-C-01
- Current Issue: EC-C-01 Implement Learned/Usual Lighting Resolution
- Classification: PRESERVE OUTCOME / REDESIGN STORAGE MODEL
- Current Outcome: Usual lighting outcomes preserved.
- V1 Implementation Pattern: Per-entity helper-backed usual brightness storage.
- Recommended V2 Mechanism: Experience Continuity state categories plus preference hierarchy and Foundation room context.
- Recommended Issue Changes: Keep explicit prohibition on helper-schema recreation.
- Required Title Changes: Applied in roadmap.
- Required Scope Changes: No change.
- Architectural Reasoning: Outcome preserved; mechanism upgraded to V2 architecture.

#### EC-C-02
- Current Issue: EC-C-02 Implement Room-Aware Lamp/Light Actuation Parity
- Classification: REDESIGN
- Current Outcome: Room-aware lamp/light outcomes preserved.
- V1 Implementation Pattern: Dynamic room entity enumeration and label intersections.
- Recommended V2 Mechanism: Foundation room definitions plus governed capability consumption.
- Recommended Issue Changes: Clarify authoritative room-definition use over runtime inference.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Preserve behavior without preserving V1 inventory inference implementation.

#### EC-C-03
- Current Issue: EC-C-03 Implement Lighting Fallback and No-Capability Behavior
- Classification: PRESERVE
- Current Outcome: Deterministic safe fallback.
- V1 Implementation Pattern: Script-specific fallback branches.
- Recommended V2 Mechanism: Unified guardrail policy and continuity defaults.
- Recommended Issue Changes: No change.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Already architecture-compatible.

#### EC-C-04
- Current Issue: EC-C-04 Implement Lighting Tests and Documentation Closure
- Classification: PRESERVE
- Current Outcome: Lighting gate evidence completeness.
- V1 Implementation Pattern: No formalized architecture gate pack.
- Recommended V2 Mechanism: Requirement-traceable test and doc closure.
- Recommended Issue Changes: No change.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Essential gate closure work.

### EC-D Issues

#### EC-D-01
- Current Issue: EC-D-01 Implement Room Audio Preference Resolution
- Classification: PRESERVE OUTCOME / ROOM-CONFIGURED SPEAKER + ROOM-LEVEL AUDIO MEMORY
- Current Outcome: Correct continuity volumes and posture for speech/music/duck.
- V1 Implementation Pattern: Helper-backed room speaker profile recreation.
- Recommended V2 Mechanism: Room Configuration speaker authority plus room-level audio memory for music, duck, and TTS values, with governed learning and safe defaults.
- Recommended Issue Changes: Preserve room-level memory outcome explicitly, add merged-room grouped playback participation for active output, and enforce no merged persistent volume preference replacing constituent-room memory.
- Required Title Changes: Applied in roadmap.
- Required Scope Changes: No change.
- Architectural Reasoning: Preserve V1 room-level audio outcome while replacing helper-schema mechanism with V2 room-configured speaker + continuity state model.

#### EC-D-02
- Current Issue: EC-D-02 Implement Sonos Speech Output with Duck/Restore
- Classification: PRESERVE
- Current Outcome: Sonos duck/restore speech continuity.
- V1 Implementation Pattern: Script-orchestrated duck/restore.
- Recommended V2 Mechanism: Explicit runtime lifecycle governed by continuity policies.
- Recommended Issue Changes: Add merged-room grouped TTS/Concierge playback handling and merged-group duck/restore behavior while preserving constituent-room memory integrity.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Outcome and mechanism alignment are already sound.

#### EC-D-03
- Current Issue: EC-D-03 Implement Audio Fallback and No-Speaker Behavior
- Classification: PRESERVE
- Current Outcome: Safe deterministic output fallback.
- V1 Implementation Pattern: Script fallback paths.
- Recommended V2 Mechanism: Guardrail policy with explicit fallback chain.
- Recommended Issue Changes: No change.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Matches ADR guardrail and continuity principles.

#### EC-D-04
- Current Issue: EC-D-04 Implement Audio Tests and Documentation Closure
- Classification: PRESERVE
- Current Outcome: Audio gate evidence completeness.
- V1 Implementation Pattern: No equivalent formal gate evidence package.
- Recommended V2 Mechanism: Traceable test/doc closure.
- Recommended Issue Changes: No change.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Required for install-gate proof.

### EC-E Issues

#### EC-E-01
- Current Issue: EC-E-01 Implement Room-Level Music Playback Resolution
- Classification: PRESERVE OUTCOME / MUSIC ASSISTANT-PREFERRED PROVIDER
- Current Outcome: Room-level music playback by user request.
- V1 Implementation Pattern: Script intent handlers/resolvers with Sonos Favorites-heavy constraints.
- Recommended V2 Mechanism: Music Assistant preferred for content resolution/orchestration when enabled, with configured room speakers as output path and Experience Continuity policy coordination.
- Recommended Issue Changes: Preserve room-level playback scope while explicitly allowing merged-room grouped playback output behavior and enforcing constituent-room memory independence.
- Required Title Changes: Applied in roadmap.
- Required Scope Changes: No change.
- Architectural Reasoning: Preserves V1 playback outcome while replacing provider constraint from Sonos Favorites-centric discovery to configuration-governed provider preference.

#### EC-E-02
- Current Issue: EC-E-02 Implement Room-Level Continue/Resume Media
- Classification: PRESERVE OUTCOME / ROOM-LEVEL MEDIA CONTINUITY USING PROVIDER-COMPATIBLE CONTEXT
- Current Outcome: Continue/resume in current room context.
- V1 Implementation Pattern: Room-scoped continuation scripts.
- Recommended V2 Mechanism: Experience Continuity room-level continuation policy consuming provider-compatible context, preferring Music Assistant-compatible re-resolution paths when enabled.
- Recommended Issue Changes: Keep explicit follow-me exclusion; add merged-room grouped output behavior and deterministic source-context selection when multiple constituent rooms have last-media context.
- Required Title Changes: Applied in roadmap.
- Required Scope Changes: No change.
- Architectural Reasoning: Correctly preserves continue/resume while excluding follow-me.

#### EC-E-03
- Current Issue: EC-E-03 Implement Room-Level Last-Media Context
- Classification: PRESERVE OUTCOME / ROOM-LEVEL MEDIA MEMORY WITH MUSIC ASSISTANT-COMPATIBLE CONTEXT
- Current Outcome: Last-media context supports continuation decisions.
- V1 Implementation Pattern: Helper/input_text state capture.
- Recommended V2 Mechanism: V2 continuity storage model with room-level last song/genre plus provider-compatible identifiers/metadata to support Music Assistant re-resolution when enabled.
- Recommended Issue Changes: Reinforce room-level media memory, explicit EC-E-02 consumption, non-reliance on Sonos-Favorites-only identifiers, explicit exclusion of person preference fields from room context storage, and deterministic merged-room write behavior without creating merged persistent media context.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Outcome remains room-level continuity; storage model is redesigned without preserving helper schema.

#### EC-E-04
- Current Issue: EC-E-04 Implement Manual-Stop Cooldown and No Unwanted Auto-Start
- Classification: PRESERVE
- Current Outcome: Respect explicit stop and avoid unwanted auto-start.
- V1 Implementation Pattern: Suppression helpers and script checks.
- Recommended V2 Mechanism: Guardrail policy and continuity suppression state.
- Recommended Issue Changes: No change.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Clear policy outcome independent of V1 storage details.

#### EC-E-05
- Current Issue: EC-E-05 Implement Media Tests and Documentation Closure
- Classification: PRESERVE
- Current Outcome: Media domain closure evidence.
- V1 Implementation Pattern: No formal domain gate closure artifact.
- Recommended V2 Mechanism: Requirement-linked testing and documentation.
- Recommended Issue Changes: Ensure coverage includes merged-room music/TTS output behavior, merged-room continue/resume behavior, deterministic merged-room last-media persistence rules, and constituent-room memory preservation checks.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Necessary for install-gate completion.

#### EC-PE-01
- Current Issue: EC-PE-01 Implement True Cross-Room Follow-Me Media (Post-Install Enhancement)
- Classification: PRESERVE
- Current Outcome: Follow-me media available as enhancement.
- V1 Implementation Pattern: Cross-room behavior embedded in script logic.
- Recommended V2 Mechanism: Separate enhancement with non-regression validation against install-gate baseline.
- Recommended Issue Changes: Keep post-install isolation explicit.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Correctly deferred per scope decisions and EC-REQ-044.

### EC-F Issues

#### EC-F-01
- Current Issue: EC-F-01 Implement Room Capability Awareness from Room Configuration
- Classification: PRESERVE OUTCOME / V2 CONFIGURATION-AUTHORED MECHANISM
- Current Outcome: User gets accurate answer to what the room can do.
- V1 Implementation Pattern: Runtime discovery and inferred inventory.
- Recommended V2 Mechanism: Room Configuration authored room definition, vocabulary, and explicit capability-device mapping consumed at runtime.
- Recommended Issue Changes: Use awareness/answering language; remove discovery-first framing.
- Required Title Changes: Applied in roadmap.
- Required Scope Changes: No change.
- Architectural Reasoning: The outcome is preserved and does not require runtime broad entity discovery when configuration has already defined the room capabilities.

#### EC-F-02
- Current Issue: EC-F-02 Implement Monitoring Follow-Up Answers from Configured Room Capabilities
- Classification: PRESERVE OUTCOME / CONFIGURATION-BOUNDED RESOLUTION
- Current Outcome: Monitoring follow-up answers for in-scope signals.
- V1 Implementation Pattern: Runtime sensor inference and script-level follow-up handling.
- Recommended V2 Mechanism: Configuration-bounded room capability signal mappings with deterministic precedence and graceful refusal.
- Recommended Issue Changes: Remove inference language and tie answers to authoritative mappings.
- Required Title Changes: Applied in roadmap.
- Required Scope Changes: No change.
- Architectural Reasoning: Outcome preserved while runtime resolution remains bounded to configured room capability mappings.

#### EC-F-03
- Current Issue: EC-F-03 Implement Capability-Not-Available Graceful Refusal
- Classification: PRESERVE
- Current Outcome: Calm refusal when capability unavailable.
- V1 Implementation Pattern: Dedicated refusal script.
- Recommended V2 Mechanism: Policy-driven refusal using authoritative capability state.
- Recommended Issue Changes: Ensure refusal checks are metadata-aware and deterministic.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Guardrail outcome remains correct.

### EC-G Issues

#### EC-G-01
- Current Issue: EC-G-01 Implement Silence-Is-Success and Direct-Refusal Policy
- Classification: PRESERVE
- Current Outcome: Calm non-chatty behavior with explicit refusal only when required.
- V1 Implementation Pattern: Implicit quiet success behavior.
- Recommended V2 Mechanism: Explicit policy branches and testable criteria.
- Recommended Issue Changes: No change.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Precisely ADR-aligned and install-gate required.

#### EC-G-02
- Current Issue: EC-G-02 Implement Degraded-Path Guardrail Validation Suite
- Classification: PRESERVE
- Current Outcome: Deterministic degraded-path safety verification.
- V1 Implementation Pattern: Distributed fallback checks.
- Recommended V2 Mechanism: Unified validation matrix.
- Recommended Issue Changes: No change.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Required to prove safety behavior across domains.

### EC-H Issues

#### EC-H-01
- Current Issue: EC-H-01 Build Install-Gate Validation Evidence Package
- Classification: PRESERVE
- Current Outcome: Evidence-backed pass/fail readiness package.
- V1 Implementation Pattern: No equivalent formal replacement gate.
- Recommended V2 Mechanism: Requirement and behavior traceability package.
- Recommended Issue Changes: Keep ownership-boundary verification explicit.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Mandatory closure artifact for NOT_READY to PASS transition.

#### EC-H-02
- Current Issue: EC-H-02 Create Final Production Readiness Review Checklist and Closure Decision
- Classification: PRESERVE
- Current Outcome: Explicit final readiness decision workflow.
- V1 Implementation Pattern: No equivalent structured closure checklist.
- Recommended V2 Mechanism: Governance-aligned closure checklist with rationale.
- Recommended Issue Changes: Keep out-of-scope and post-install declarations explicit.
- Required Title Changes: No change.
- Required Scope Changes: No change.
- Architectural Reasoning: Ensures governance-compliant production replacement decision.

## Mandatory Focus Reviews

### EC-E-01 Recommendation
Recommended direction: Room-Level Music Playback Resolution with Music Assistant preferred when enabled.

Why:
- V1 outcome to preserve is room-level music playback by request.
- V1 implementation struggled with Sonos Favorites-centric discovery and resolution constraints.
- V2 should prefer Music Assistant for content resolution/orchestration when enabled, while keeping configured room speakers as output path.
- Person-scoped music preferences may be applied only when identity confidence/policy allows, and remain distinct from room-level last-media continuity context.

Review result: PRESERVE OUTCOME / MUSIC ASSISTANT-PREFERRED PROVIDER.

### EC-F-01 Recommendation
Recommended direction: Room Capability Awareness from Room Configuration.

Why:
- The user outcome is answering what this room can do.
- Room Configuration authored room definitions and capability mappings are authoritative at runtime.
- Runtime broad entity discovery/inference is not the primary mechanism.

Review result: PRESERVE OUTCOME / V2 CONFIGURATION-AUTHORED MECHANISM.

### EC-F-02 Recommendation
Recommended direction: Monitoring Follow-Up Answers from Configured Room Capabilities.

How it should work:
- Determine room by authoritative configured context.
- Resolve signal availability from configured room capability mappings.
- Apply deterministic precedence when multiple configured devices satisfy one capability.
- Use configured mappings for temperature, humidity, light, air quality, and noise.
- Return concise answer or graceful refusal when mapping/capability is unavailable.

Review result: PRESERVE OUTCOME / CONFIGURATION-BOUNDED RESOLUTION.

### EC-D-01 Recommendation
Recommended direction: Room Audio Preference Resolution.

Why:
- V1 helper-backed speaker profile reconstruction is implementation-specific.
- Configured room speakers are authoritative and room-level memory for music, duck, and TTS levels must be preserved.
- Person-aware overrides can be layered later and are not required for initial parity.
- Merged-room playback should group participating speakers for active output without merging persistent constituent-room memory.

Review result: PRESERVE OUTCOME / ROOM-CONFIGURED SPEAKER + ROOM-LEVEL AUDIO MEMORY.

### EC-C-01 Recommendation
Recommended direction: Learned/Usual Lighting Resolution.

Why:
- Outcome is usual lighting behavior, not helper storage reproduction.
- V2 should use continuity state categories and Room Configuration authored lamp/light membership.

Review result: PRESERVE OUTCOME / REDESIGN STORAGE MODEL.

### EC-E-02 Recommendation
Continue and Resume must remain distinct from Follow-Me Media.

Verification:
- Continue/Resume stays INSTALL_GATE_REQUIRED.
- Follow-Me remains EC-PE-01 POST_INSTALL_ENHANCEMENT only.
- When Music Assistant is enabled, continue/resume prefers provider-compatible context/re-resolution pathways where available.
- Merged-room continue/resume output can be grouped, but source-memory selection must stay deterministic and room-scoped.

Review result: PRESERVE OUTCOME / ROOM-LEVEL MEDIA CONTINUITY USING PROVIDER-COMPATIBLE CONTEXT.

### EC-E-03 Recommendation
Room-level last-media memory must remain explicit for initial parity.

Verification:
- Room-level last song and last genre context are captured.
- EC-E-02 consumes room-level context.
- Music Assistant-compatible identifier/metadata capture is supported when Music Assistant is enabled.
- Cross-room and person-specific media memory remain future enhancements unless separately required.

Review result: PRESERVE OUTCOME / ROOM-LEVEL MEDIA MEMORY WITH MUSIC ASSISTANT-COMPATIBLE CONTEXT.

## Clarified Classification Register
| Issue | Clarified Classification |
|---|---|
| EC-F-01 | PRESERVE OUTCOME / V2 CONFIGURATION-AUTHORED MECHANISM |
| EC-F-02 | PRESERVE OUTCOME / CONFIGURATION-BOUNDED RESOLUTION |
| EC-D-01 | PRESERVE OUTCOME / ROOM-CONFIGURED SPEAKER + ROOM-LEVEL AUDIO MEMORY |
| EC-C-01 | PRESERVE OUTCOME / REDESIGN STORAGE MODEL |
| EC-E-01 | PRESERVE OUTCOME / MUSIC ASSISTANT-PREFERRED PROVIDER |
| EC-E-02 | PRESERVE OUTCOME / ROOM-LEVEL MEDIA CONTINUITY USING PROVIDER-COMPATIBLE CONTEXT |
| EC-E-03 | PRESERVE OUTCOME / ROOM-LEVEL MEDIA MEMORY WITH MUSIC ASSISTANT-COMPATIBLE CONTEXT |

## Roadmap Language Update Summary
Language updates were applied in the roadmap to remove V1-pattern assumptions while preserving scope and ordering:
- EC-F epic wording shifted to room-configuration-authored capability awareness and answering.
- EC-F-01 and EC-F-02 renamed and reworded to consume configured room capability mappings.
- EC-D-01 renamed and reworded from speaker-profile recreation to room audio preference resolution with room-level memory.
- EC-C-01 title and wording aligned to learned/usual lighting outcome preservation with redesigned storage model.
- EC-E-01 renamed/reworded to room-level music playback resolution with Music Assistant preferred when enabled.
- EC-E-02 and EC-E-03 clarified as room-level continuity (not follow-me) with provider-compatible context support.

## Scope and Ordering Integrity Check
- Scope decisions changed: no.
- Out-of-scope items removed: no.
- Issue coverage removed: no.
- New implementation issues created: no.
- Issue ordering changed: no.

## Principle Confirmation
Preserve V1 outcomes.
Do not preserve V1 implementation details unless no V2 architectural replacement exists.
