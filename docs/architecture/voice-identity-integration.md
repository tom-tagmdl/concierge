# Voice Identity Integration

Concierge integrates with Voice Identity as an optional capability under
governed platform boundaries.

## Governance Authority

This document is implementation guidance under:

- `docs/architecture/adr-runtime-voice-attribution-lifecycle.md`
- `docs/governance/runtime-attribution-consumption-boundary.md`

When conflicts exist, ADR authority wins.

## Ownership Model

Concierge remains responsible for:

- room context and room capability awareness
- people configuration and permissions
- conversation orchestration
- authorization classification
- user-facing deterministic behavior and explainability

Voice Identity provides:

- speaker fingerprint generation and lifecycle
- attribution while audio is available
- confidence/ambiguity determination
- short-lived attribution context lifecycle
- safe reason-code surfaces

Concierge does not perform biometric comparison, voiceprint generation,
or speaker attribution logic.

## Runtime Attribution Lifecycle

Approved flow:

Assist Pipeline or audio-capable ingress

-> Voice Identity attribution while audio is available

-> Voice Identity-owned short-lived Attribution Context Store

-> Concierge Conversation Agent lookup via correlation context

-> Concierge authorization classification and intent execution

Voice Identity runtime attribution context store interface (owned by Voice
Identity):

- `upsert(record)`
- `resolve_current_speaker(conversation_id, device_id, satellite_id, room_id, now)`
- `invalidate_by_conversation(conversation_id)`
- `invalidate_by_device_satellite(device_id, satellite_id)`
- `sweep_expired(now)`

Naming requirement: use `resolve_current_speaker`.

Do not use conversation-owner naming such as `resolve_conversation_owner`.

## Conversation Agent Context Constraints

Conversation Agent execution can consume correlation context, including:

- `conversation_id`
- `device_id`
- `satellite_id`
- `agent_id`
- `language`
- `text`

The Conversation Agent path does not treat transcript text as identity proof.

`conversation_id` is a correlation key and is not identity authority.

Concierge runtime ingress normalizes ConversationInput metadata into a bounded
execution context before orchestration:

ConversationInput

-> Foundation room resolution (`device_id` / `satellite_id` / explicit `area_id`)

-> Voice Identity `get_identity_context` lookup

-> Concierge orchestration

Foundation remains authoritative for room resolution.
Room Configuration Authority remains authoritative for room behavior.
Room Capability Awareness remains authoritative for room-scoped capability
projection and visibility.

## Text-Only Trigger Boundary

Home Assistant `conversation` trigger and text-only automation paths are
supported for fallback/debug/typed input and non-personal room-scoped behavior.

These paths are not identity-authoritative and must not be documented as
identity truth sources.

Fallback paths are supported but non-authoritative for identity. Safe fallback
reason codes include `identity_audio_missing` and `identity_context_missing`
when attribution evidence/context is unavailable.

## Required Authorization Classification

Concierge identity requirement classes:

- `identity_not_required`
- `identity_optional`
- `identity_required`
- `identity_required_fresh`
- `identity_required_step_up`

Deterministic policy outcomes must be emitted with safe reason codes.

Runtime execution gate order:

Conversation / service runtime context

-> Foundation room resolution

-> Voice Identity `get_identity_context` consumption

-> identity authorization classification

-> policy outcome

-> execute / challenge / deny / constrain / continue_without_identity

Sensitive or person-scoped execution must not run before this classification
and policy outcome are available.

Concierge runtime policy projection is diagnostics-safe and includes:

- `identity_requirement_class`
- `identity_policy_outcome`
- `identity_policy_reason_code`
- `identity_policy_source`
- `identity_freshness_class`
- `attribution_age_ms`
- `identity_state`
- `confidence_band`

User-facing challenge/deny text is deterministic and explainable without
exposing confidence scores, biometric details, or internal model behavior.

## Privacy Boundary

Concierge-consumable identity context must never include:

- raw audio
- embeddings
- vectors
- biometric internals
- long-lived attribution artifacts

## Explainability Boundary

Concierge responses and diagnostics may include:

- safe reason codes
- policy outcomes
- freshness class and attribution age
- room resolution source

Concierge diagnostics must not expose Voice Identity internals.

## Issue #426 Validation Matrix

The authoritative end-to-end runtime lifecycle validation matrix is defined in:

- `tests/runtime_voice_attribution_lifecycle_matrix.py`
- `tests/test_runtime_voice_attribution_lifecycle_validation.py`

Validation scope covered by this matrix:

- attribution states (`known`, `unknown`, `ambiguous`, `unavailable`, `not_required`)
- deterministic freshness classes (`fresh`, `stale`, `expired`)
- speaker handoff supersession in shared conversation context
- correlation-key lookup (`conversation_id`, `device_id`+`satellite_id`, `room_id`, partial/missing inputs)
- text-only fallback posture (`non_authoritative_fallback`)
- authorization-class and policy-outcome determinism
- privacy and diagnostic-safety assertions

Deterministic time-control approach:

- Voice Identity store-level tests pass explicit `now` timestamps for
	`resolve_current_speaker` and `sweep_expired`.
- Fixed timestamps are used for freshness boundary transitions to avoid
	wall-clock dependency.

Governance checklist output for Issue #426 is generated by:

- `build_governance_checklist_output()` for machine-readable summary
- `render_governance_checklist_markdown()` for human-readable summary

Both functions are defined in `tests/runtime_voice_attribution_lifecycle_matrix.py`
and validated by `tests/test_runtime_voice_attribution_lifecycle_validation.py`.
