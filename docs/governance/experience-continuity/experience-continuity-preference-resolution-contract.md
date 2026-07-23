# Experience Continuity Preference Resolution Contract

## Purpose
This artifact defines the governed preference resolution contract for EC-B-01.

It preserves deterministic preference ordering, identity gating, and person-vs-room ownership boundaries without defining domain behavior outside the Experience Continuity authority chain.

## Governing Sources
- [ADR: Experience Continuity Architecture](adr-experience-continuity-architecture.md)
- [Experience Continuity Scope Decisions](experience-continuity-scope-decisions.md)
- [Experience Continuity Requirements Backlog](experience-continuity-requirements-backlog.md)
- [Experience Continuity Outcome Preservation Review](experience-continuity-outcome-preservation-review.md)
- [V1-to-V2 Capability Parity Matrix](v1-to-v2-capability-parity-matrix.md)
- [Experience Continuity Runtime Terminology Reference](experience-continuity-runtime-terminology-reference.md)
- [Experience Continuity Diagnostics Reference](experience-continuity-diagnostics-reference.md)

## Preference Ownership Model
Preference ownership is governed by continuity scope and context.

Person-scoped defaults:
- preferred artist
- preferred genre
- preferred album
- preferred playlist
- music affinity

Room-scoped context:
- room media context
- room defaults
- speaker and output routing context

Household-scoped policy:
- guest defaults
- unknown-speaker defaults
- unavailable-identity fallback
- silence-is-success policy
- capability-not-available policy

Preference resolution must not collapse these ownership categories into a single undifferentiated store.

## Resolution Hierarchy
Unless superseded by future authority, preference resolution follows this deterministic order:
1. Explicit current command.
2. Safety or policy guardrail.
3. Known person preference.
4. Optional explicit person plus room preference exception.
5. Room default.
6. Household default.
7. System safe default.

Command intent and guardrail policy always override personalization.

Person preference is the default portable model for music-oriented preference signals.

Person plus room preference is not the default model and is only valid when explicit policy or configuration enables it.

## Identity Gating Rules
Personalized preference application is allowed only when identity confidence and policy permit it.

Fail-closed contexts:
- guest
- unknown
- unavailable
- low confidence

Required behavior:
- guest mode suppresses personalized preference application unless explicit policy authorizes it.
- unknown and unavailable identity contexts use room or household defaults.
- low-confidence identity contexts use room or household defaults.
- safe room-default behavior must remain available when Voice Identity is unavailable.

## Person-vs-Room Boundary Rules
Person-scoped preferences are portable across rooms unless explicitly constrained by governing policy.

Room media context remains room-scoped.

Room defaults are not person preferences and must not be promoted into person truth.

Room history must not be reused as person preference by default.

Person-scoped preference application must not override explicit room ownership boundaries.

## Person+Room Exception Model
Person plus room preference is an explicit exception path only.

This exception may be used when:
- a future governed feature explicitly enables it
- the request is person-scoped and room-scoped together
- identity state is known and policy permits personalized application

This exception must remain distinct from ordinary person-scoped preference resolution.

This exception must not be inferred from room media context alone.

## Explainability Requirements
Preference resolution outcomes must be explainable and deterministic.

Required explainability data:
- resolved preference key
- selected tier
- selected scope
- evaluation path
- applied policy summary
- identity decision summary
- fallback reason, when any
- ownership boundary summary

Diagnostics must expose why a preference was selected, why personalization was blocked, and which fallback tier was chosen.

Diagnostics must remain boundary-safe and must not expose raw private payloads.

## Validation Scenarios
The governed validation set must cover these scenarios:
1. command override success
2. guardrail override success
3. known person preference success
4. explicit person plus room exception success
5. room default fallback success
6. household default fallback success
7. system safe default fallback success
8. guest identity fail-closed behavior
9. unknown identity fail-closed behavior
10. unavailable identity fail-closed behavior
11. low-confidence identity fail-closed behavior
12. person preference portability across rooms

## Non-Goals
This artifact does not implement:
- learning pipelines
- playback execution
- lighting actuation
- media orchestration
- room configuration authoring
- Voice Identity scoring
- persistence schema design
- helper-schema recreation
- production Home Assistant changes

## Validation Evidence
Preference resolution validation must demonstrate:
- deterministic precedence
- fail-closed identity gating
- room-vs-person boundary separation
- exception-only person+room handling
- stable explainability metadata
- no raw payload exposure

The companion resolver tests must exercise the governed precedence path directly.
