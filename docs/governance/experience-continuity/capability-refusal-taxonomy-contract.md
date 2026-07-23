# Capability Refusal Taxonomy Contract

## 1. Purpose
This contract defines deterministic refusal outcomes when Concierge cannot complete a capability request. It standardizes refusal taxonomy, explainability fields, and authority alignment for issue #414.

## 2. Scope
This contract applies to refusal outcomes produced by:
- Monitoring follow-up capability resolution.
- Room media provider resolution and continuation.
- Person-aware productivity routing fail-closed outputs.
- Recipient consent/privacy/visibility messaging boundaries.

This contract does not redefine source-of-truth authority for identity, room configuration, media providers, or person policy.

## 3. Deterministic Refusal Fields
Every governed refusal-capable payload must include:
- refusal_reason
- refusal_category
- room_authority_source
- capability_requested
- capability_available
- capability_configured
- person_policy_evaluated
- merged_room_authority_source

When the capability succeeds, refusal_reason and refusal_category are null while other explainability fields remain present.

## 4. Refusal Categories
Allowed refusal_category values:
- authority_scope_missing
- configuration_unavailable
- capability_unavailable
- policy_denied

Unknown refusal_reason values must fail closed to capability_unavailable rather than inventing a new category at runtime.

## 5. Reason-To-Category Mapping
Deterministic mappings include:
- composite_configuration_missing -> authority_scope_missing
- room_scope_missing -> authority_scope_missing
- configured_capability_mapping_missing -> capability_unavailable
- configured_capability_measurement_unavailable -> capability_unavailable
- media_provider_disabled -> configuration_unavailable
- music_assistant_unavailable -> capability_unavailable
- manual_stop_cooldown_active -> policy_denied
- consent_required_not_granted -> policy_denied
- delivery_target_blocked -> policy_denied
- delivery_channel_not_allowed -> policy_denied
- privacy_boundary_channel_restricted -> policy_denied
- visibility_boundary_channel_restricted -> policy_denied
- person_profile_not_configured -> configuration_unavailable
- productivity_bindings_missing -> configuration_unavailable
- presence_bindings_missing -> configuration_unavailable
- policy_context_missing -> policy_denied

## 6. Authority Alignment
Refusal outputs must describe which configured authority produced the refusal:
- room_authority_source describes room/composite authority lineage.
- merged_room_authority_source describes merged-room authority lineage when applicable.
- person_policy_evaluated indicates whether person/consent policy gates were evaluated.

Concierge remains a bounded consumer and must not claim authority ownership while refusing.

## 7. Monitoring Follow-Up Requirements
For monitoring follow-up responses:
- capability_requested equals the requested monitoring capability.
- capability_configured is true only when configured device mapping exists.
- capability_available is true only when a valid measurement is resolved.
- runtime_discovery_reliance remains validation_only and cannot create ownership.

## 8. Media Resolution Requirements
For media provider resolution and room media continuation:
- refusal_reason mirrors failure_reason when execution is blocked.
- capability_requested is room_media_playback or room_media_continuation.
- capability_configured requires both room output authority and configured provider path.
- capability_available is true only when execution succeeds.

## 9. Policy Boundary Requirements
For person-aware routing and recipient-consent boundaries:
- Fail-closed routing states must emit refusal taxonomy fields.
- Consent/privacy/visibility denials must emit refusal_reason and refusal_category in boundary refs.
- person_policy_evaluated must be true for policy-gated paths.

## 10. Validation And Evidence
Validation for this contract is provided by:
- tests/test_services.py refusal taxonomy assertions.
- tmp/ec414_portable_harness_results.json scenario evidence.
- tmp/ec414_test_results.json closure summary.
- tmp/ec414_coverage_matrix.json and tmp/ec414_doc_cross_reference.json traceability artifacts.
