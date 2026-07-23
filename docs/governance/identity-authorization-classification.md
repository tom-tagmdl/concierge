# Identity Authorization Classification

## Purpose

Define Concierge identity requirement classification used before intent execution.

This document consumes architecture authority from:

- `docs/architecture/adr-runtime-voice-attribution-lifecycle.md`
- `docs/governance/runtime-attribution-consumption-boundary.md`

## Classification Taxonomy

Concierge must classify each intent into one of:

- `identity_not_required`
- `identity_optional`
- `identity_required`
- `identity_required_fresh`
- `identity_required_step_up`

## Examples

### identity_not_required

- room-scoped lights
- room-scoped status
- general weather
- "what can I do in this room"

### identity_optional

- personalization may improve response but is not required for safe execution

### identity_required

- person-scoped preferences
- preferred music
- person-specific memory
- household member-specific routines

### identity_required_fresh

- calendar
- messages
- private reminders
- personal schedule

### identity_required_step_up

- unlock
- disarm
- purchases
- security-sensitive changes
- administrative identity/profile changes

## Policy Mapping

- known + fresh + sufficient confidence -> `allow`
- not_required -> `allow` or `continue_without_identity`
- optional + missing identity -> `continue_without_identity` or `constrain`
- required + missing/stale/unknown -> `challenge` or `deny`
- required_fresh + stale -> `challenge`
- step_up + uncertainty -> `deny` or step-up challenge

## Runtime Execution Gate

Concierge applies identity authorization classification before sensitive or
person-scoped execution:

Conversation / service runtime context

-> room resolution

-> Voice Identity current-speaker context consumption

-> identity authorization classification

-> policy outcome

-> execute / challenge / deny / constrain / continue_without_identity

Concierge remains attribution-consumer only. Concierge does not perform
speaker attribution and does not redefine Voice Identity confidence or
ambiguity semantics.

## Conservative Initial Classification Mapping

Concierge runtime classification currently uses deterministic intent-class and
target-keyword mapping with conservative fallbacks:

- `identity_not_required`: room-scoped control, room status, general weather,
	room capability inquiry
- `identity_optional`: general Q&A and briefing-style responses where
	non-personal behavior is valid
- `identity_required`: person-scoped preference/music/memory/routine behaviors
- `identity_required_fresh`: calendar/messages/schedule/reminder and private
	person-specific information intents
- `identity_required_step_up`: unlock/disarm/purchase/admin identity-profile
	change behaviors

Any unmapped behavior defaults to `identity_optional` until a stricter
classification is explicitly declared by accepted architecture authority.

## Runtime Inputs

Concierge consumes safe attribution context from Voice Identity using correlation
keys:

- `conversation_id`
- `device_id`
- `satellite_id`
- optional resolved `room_id`

`conversation_id` is correlation context and not identity authority.

## Safe Reason Codes

Required normalized safe reason codes include:

- `identity_known_high_confidence`
- `identity_known_medium_confidence`
- `identity_known_low_confidence`
- `identity_ambiguous_match`
- `identity_unknown`
- `identity_unavailable`
- `identity_audio_missing`
- `identity_context_missing`
- `identity_context_stale`
- `identity_context_expired`
- `identity_not_required`
- `identity_required_but_missing`
- `identity_required_but_unknown`
- `identity_required_but_ambiguous`
- `identity_required_fresh_but_stale`
- `identity_optional_missing_continue_without_identity`
- `identity_step_up_required`
- `identity_policy_allow`
- `identity_policy_challenge`
- `identity_policy_deny`
- `identity_policy_constrain`

## Required Envelope Projection

Execution envelope diagnostics-safe projection includes:

- `identity_requirement_class`
- `identity_policy_outcome`
- `identity_policy_reason_code`
- `identity_policy_source`
- `identity_freshness_class`
- `attribution_age_ms`
- `identity_state`
- `confidence_band`

These fields are safe diagnostics outputs only and must not include biometric
or raw-audio internals.

## Privacy Boundary

This classification surface must not expose:

- raw audio
- embeddings
- vectors
- biometric internals
- Voice Identity store internals

Diagnostics may expose policy outcome, reason code, freshness class,
attribution age, and room-resolution source.

## Issue #426 Validation References

Issue #426 uses a validation-only matrix and test suite to prove lifecycle
conformance without changing architecture or authorization mappings.

Authoritative validation artifacts:

- `tests/runtime_voice_attribution_lifecycle_matrix.py`
- `tests/test_runtime_voice_attribution_lifecycle_validation.py`
- `../voice_identity/tests/test_attribution_context_store.py`

Validation expectations for classification and policy outcomes:

- each requirement class (`identity_not_required`, `identity_optional`,
	`identity_required`, `identity_required_fresh`,
	`identity_required_step_up`) must emit deterministic policy outcomes and
	reason codes for governed speaker/freshness inputs
- fallback conversation-trigger paths remain supported and non-authoritative
	for identity and must not permit sensitive/person-scoped bypass
- diagnostics-safe policy projection must not expose biometric internals,
	embeddings, vectors, voiceprints, or raw audio payloads

Environment parity note:

- when HA-integrated tests are blocked by environment dependencies,
	policy/store/correlation validation may execute in the supporting environment
	and must be reported separately from infrastructure parity gaps.
