# ADR: Runtime Voice Attribution Lifecycle

## Status

Proposed

## Date

2026-07-23

## Context

Runtime validation of Home Assistant conversation-trigger automation paths showed
text-only execution contexts that cannot be used as identity authority for
speaker attribution.

Observed runtime evidence included:

- `audio_ref_present=False`
- `trigger_event_data=None`
- `active_person_reason_code=identity_unknown`

Home Assistant Conversation Agent execution provides correlation context
(`conversation_id`, `device_id`, `satellite_id`) but does not provide raw
audio to the Conversation Agent path.

Identity-aware Concierge behavior therefore requires a two-stage runtime model:

1. Attribution while audio is available.
2. Safe attribution-context consumption at conversation/text execution time.

This ADR aligns Concierge with HTBW platform ownership boundaries:

- Voice Identity owns attribution truth and lifecycle.
- Concierge consumes safe attribution context and applies authorization policy.

## Decision

### Decision 1: Runtime Attribution Lifecycle Is Adopted

Approved runtime lifecycle:

Assist Pipeline or audio-capable ingress

-> Voice Identity runtime attribution while audio is available

-> Voice Identity-owned Attribution Context Store (short-lived)

-> Concierge Conversation Agent lookup via correlation context

-> Concierge authorization classification and intent execution

### Decision 2: Ownership Boundaries Are Explicit

Voice Identity owns:

- attribution execution
- attribution records
- attribution confidence and ambiguity determination
- reason-code issuance for attribution outcomes
- attribution context TTL, freshness, and expiry
- biometric boundary enforcement

Concierge owns:

- conversation orchestration
- Foundation-linked room resolution
- room capability awareness and behavior routing
- authorization classification and execution policy application
- user-facing deterministic responses and safe explainability

Concierge does not own:

- biometric comparison
- voiceprint generation
- attribution truth
- attribution source-of-record storage

### Decision 3: Correlation Keys Are Not Identity Authority

`conversation_id` is a correlation key only.

`conversation_id` is not a proof of speaker identity and is not a conversation
owner model.

Primary record identity is `attribution_id`.

Correlation and lookup keys may include:

- `conversation_id`
- `device_id`
- `satellite_id`
- `issued_at_utc`
- optional `turn_index`

Speaker handoff inside the same conversation is explicitly supported.

### Decision 4: Short-Lived Attribution TTL Is Required

Attribution context is a bridge between audio-time and text-time, not a
long-lived identity session.

Default reuse TTL policy:

- known + high confidence: 30 seconds
- known + medium confidence: 15 seconds
- low confidence or ambiguous: 5 to 10 seconds
- unknown: no reuse
- unavailable: no reuse

Absolute maximum cap: 60 seconds unless superseded by accepted ADR.

Voice Identity should attempt attribution for each spoken turn when audio is
available.

### Decision 5: Authorization Classification Is Required

Concierge authorization classification taxonomy:

- `identity_not_required`
- `identity_optional`
- `identity_required`
- `identity_required_fresh`
- `identity_required_step_up`

Policy outcome mapping is deterministic and explainable:

- known + fresh + sufficient confidence -> allow
- not_required -> allow or continue_without_identity
- optional + missing identity -> continue_without_identity or constrain
- required + missing/stale/unknown -> challenge or deny
- required_fresh + stale -> challenge (re-attribution required)
- step_up + uncertainty -> deny or step-up challenge

### Decision 6: `not_required` Attribution State Is Introduced

Attribution decision state includes `not_required` in addition to:

- known
- ambiguous
- unknown
- unavailable

`not_required` indicates identity is not required for the current intent and is
distinct from `unknown`.

### Decision 7: Foundation / Room Linkage Must Be Preserved

`device_id` and `satellite_id` are consumed as room-resolution inputs through
Foundation/Room Configuration Authority pathways.

Resolved room context is explainable via safe diagnostics.

Concierge must not expose raw audio or biometric internals in room-resolution
diagnostics.

### Decision 8: Privacy and Security Controls Are Mandatory

Concierge-consumable attribution contracts must never include:

- raw audio bytes
- embeddings or vectors
- biometric internals
- long-lived identity session artifacts

Safe outputs must include deterministic reason codes, freshness state, and
policy outcomes.

## Runtime Flow

1. Audio-capable ingress receives spoken input.
2. Voice Identity performs attribution using audio-time evidence.
3. Voice Identity stores a short-lived attribution record.
4. Concierge Conversation Agent receives conversation input context.
5. Concierge resolves room context through Foundation-linked room resolution.
6. Concierge resolves current speaker attribution via correlation keys.
7. Concierge classifies identity requirement for intended action.
8. Concierge applies policy before intent execution.
9. Concierge emits deterministic response with safe reason code and policy
   outcome.

## Consequences

Positive:

- preserves platform ownership boundaries
- enables deterministic identity-aware policy behavior
- supports speaker handoff safety across multi-turn flows
- maintains biometric privacy boundaries

Tradeoffs:

- requires additional store and policy coordination surface
- increases dependency on fresh attribution availability
- increases challenge/clarification events for uncertain attribution states

## Test Requirements

Required test coverage includes:

- attribution store freshness, expiry, and no-reuse behavior
- speaker handoff and supersession behavior within shared conversation context
- device/satellite fallback bounded by short TTL
- authorization classification outcome determinism
- fail-closed behavior for sensitive actions under missing/stale/uncertain
  attribution
- diagnostics/privacy assertions that raw audio, embeddings, vectors, and
  biometric internals are never exposed

## Governance Basis

This ADR consumes and aligns with:

- HTBW canonical architecture authority order
- ADR-004 Coordinator V2 Governance Boundaries
- Voice Identity platform architecture ADRs
- runtime attribution consumption boundary governance

This ADR does not transfer attribution ownership to Concierge.