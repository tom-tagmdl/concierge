# Experience Continuity Room Media Continuation Contract

## Purpose
This artifact defines the governed contract for EC-E-02 room media continue/resume behavior.

It preserves V1 room-level continuation outcomes while keeping room configuration authoritative, Music Assistant preferred for content resolution when enabled, and room-scoped continuity memory stored in Experience Continuity state.

## Governing Sources
- [ADR: Experience Continuity Architecture](adr-experience-continuity-architecture.md)
- [Experience Continuity Scope Decisions](experience-continuity-scope-decisions.md)
- [Experience Continuity Outcome Preservation Review](experience-continuity-outcome-preservation-review.md)
- [Experience Continuity Requirements Backlog](experience-continuity-requirements-backlog.md)
- [V1-to-V2 Capability Parity Matrix](v1-to-v2-capability-parity-matrix.md)
- [Experience Continuity Preference Resolution Contract](experience-continuity-preference-resolution-contract.md)

## Contract Scope
Room media continuation covers:
- continue / resume requests for room media playback
- same-song continuation when prior room media context is specific enough
- same-album continuation when album context is available
- same-artist continuation when artist context is available
- same-genre continuation when genre context is available
- deterministic fallback to governed room defaults when the media context is incomplete
- fail-closed refusal when Music Assistant is disabled, unavailable, or blocked by policy

This contract excludes Follow-Me Music as a behavior model.

## Authority Model
Room configuration remains authoritative for speaker/output selection.

Room media continuity remains authoritative for last-media context, manual-stop cooldown, and deterministic source-room selection.

Person preference resolution may shape content selection only when identity confidence and policy permit it.

Music Assistant is the preferred provider for room media content resolution when enabled and available.

Configured room speakers remain the output path even when Music Assistant provides the resolved content.

## Continuation Hierarchy
Continuation resolution must follow this order:
1. Manual-stop cooldown refusal.
2. Room-scoped last-media context.
3. Explicit room media continuation strategy.
4. Person preference assistance when identity policy allows it.
5. Room default media query.
6. Household default media query.
7. System safe media query.

If the room-scoped last-media context is missing, stale, or insufficient, the resolver must fall back to governed defaults rather than inventing a global media history.

## Source Room Selection
When continuation is requested for a merged room, the source room must be selected deterministically from the room media context.

If the requested room has a usable room media context, it remains the source room.

If a composite or merged-room execution is active, the selected source room must be explainable and stable.

The selected source room must be recorded in the response and in the captured room media context.

## Manual Stop Guardrail
Manual stop is a hard guardrail.

When a manual-stop cooldown is active, continuation must be refused even if room media context exists.

The refusal must surface a clear cooldown decision and must not call the content provider.

## Provider Behavior
When Music Assistant is enabled and available:
- continuation requests should resolve content through Music Assistant
- same-song, same-album, same-artist, and same-genre strategies are permitted
- room output targeting still uses the configured room speakers

When Music Assistant is disabled or unavailable:
- continuation must fail closed
- the response must explain the provider refusal
- no silent fallback to an alternate media provider is allowed in this contract

## Room Memory Requirements
Room media continuation state must be stored in room-scoped Experience Continuity memory.

Required room memory data includes:
- source room id
- source room selection reason
- media type
- media query
- provider source
- last media summary
- manual-stop flags and cooldown values, when present

Merged-room playback must not create merged persistent room media memory by default.

Constituent room memory must remain independent.

## Explainability Requirements
Continuation outcomes must expose:
- continuation strategy
- continuation strategy reason
- source room id
- source room selection reason
- room media context summary
- provider selection and availability
- fallback path and fallback reason, when any
- manual-stop cooldown decision, when any
- Follow-Me exclusion marker

## Validation Scenarios
The governed validation set must cover these scenarios:
1. same-song continuation success
2. same-album continuation success
3. same-artist continuation success
4. same-genre continuation success
5. room-default fallback success
6. Music Assistant disabled refusal
7. Music Assistant unavailable refusal
8. manual-stop cooldown refusal
9. merged-room deterministic source-room selection
10. room media context persistence after successful continuation
11. Follow-Me exclusion remains explicit

## Non-Goals
This artifact does not implement:
- Follow-Me Music behavior
- person-scoped preference schema design
- lighting continuity behavior
- audio duck/restore behavior
- new service surfaces separate from execute
- global media history storage

## Validation Evidence
Evidence for this contract must show:
- deterministic source-room selection
- provider-aware content resolution
- room-configured output targeting
- manual-stop fail-closed behavior
- room-scoped persistence updates
- explainable fallback/refusal paths