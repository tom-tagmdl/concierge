# Experience Continuity Lighting Fallback Decision Matrix

## 1. Purpose
This artifact defines EC-C-03 deterministic degraded-path behavior for room-aware lighting commands.

It preserves the V1 user outcome that lighting failures are safe, calm, and understandable while keeping V2 room and capability authority boundaries intact.

## 2. Governance Sources
- docs/governance/experience-continuity/adr-experience-continuity-architecture.md
- docs/governance/experience-continuity/experience-continuity-scope-decisions.md
- docs/governance/experience-continuity/experience-continuity-requirements-backlog.md
- docs/governance/experience-continuity/experience-continuity-epic-and-issue-roadmap.md
- docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md
- docs/governance/experience-continuity/v1-capability-reconstruction.md
- docs/governance/experience-continuity/experience-continuity-learned-lighting-contract.md
- docs/governance/experience-continuity/experience-continuity-room-aware-lighting-command-behavior.md

## 3. Failure Conditions
EC-C-03 handles these explicit failure conditions:
1. room_configuration_missing
2. configured_capability_mapping_missing
3. configured_entity_missing
4. configured_entity_invalid
5. configured_device_unavailable
6. unsupported_device_capability
7. learned_value_missing
8. learned_value_unavailable or learned_value_denied
9. no_eligible_lighting_targets
10. lighting_command_not_supported and lighting_command_not_supported_by_configured_room_capability

## 4. Deterministic Default Rules
Authoritative default behaviors:
- For learned value degradation, use EC-C-01 fallback hierarchy exactly:
  - current_state_brightness
  - safe_default_brightness (50)
- For unsupported or unavailable command execution paths, use deterministic safe no-actuation or safe command rejection.

Inference labels (governance-bounded naming only):
- deterministic_default=safe_noop
- deterministic_default=safe_command_rejection
These labels are projection metadata names and do not alter governance authority.

## 5. Capability Degradation Rules
- Capability mapping is consumed from configured room capability fields only.
- Unsupported command/capability states do not trigger discovery substitution.
- Unsupported device capability is explicit and produces deterministic no-actuation.

## 6. Membership Degradation Rules
- Membership source remains room_configuration_membership.
- Validation can deny members but cannot add replacement members.
- Empty or invalid effective membership yields deterministic safe failure.

## 7. Learned Lighting Degradation Rules
- Missing, unavailable, or denied learned values degrade per entity.
- Degraded entity behavior remains deterministic and explainable through fallback_reason, fallback_source, deterministic_default, and decision_reason.
- Learned-value degradation does not bypass room authority.

## 8. Safe Failure Matrix
| Condition | Action | Decision Reason | Fallback Path | Deterministic Default |
| --- | --- | --- | --- | --- |
| room_configuration_missing | no actuation | configured_room_authority_validation | degraded_safe_failure | safe_noop |
| configured_capability_mapping_missing | no actuation | configured_room_authority_validation | degraded_safe_failure | safe_noop |
| configured_entity_missing | no actuation when no valid targets remain | configured_room_authority_validation | degraded_safe_failure | safe_noop |
| configured_entity_invalid | no actuation when no valid targets remain | configured_room_authority_validation | degraded_safe_failure | safe_noop |
| configured_device_unavailable | no actuation when no valid targets remain | configured_room_authority_validation | degraded_safe_failure | safe_noop |
| unsupported_device_capability | no actuation when no valid targets remain | device_capability_validation | degraded_safe_failure | safe_noop |
| no_eligible_lighting_targets | no actuation | configured_room_authority_validation | degraded_safe_failure | safe_noop |
| lighting_command_not_supported_by_configured_room_capability | safe command rejection | configured_room_capability_authority | degraded_safe_failure | safe_command_rejection |
| lighting_command_not_supported | safe command rejection | lighting_command_support_policy | degraded_safe_failure | safe_command_rejection |
| learned_value_missing | entity-level fallback actuation | learned_value_missing | entity_fallback_default | safe_default_brightness or current_state_brightness |
| learned_value_unavailable | entity-level fallback actuation | learned_value_unavailable | entity_fallback_default | current_state_brightness or safe_default_brightness |
| learned_value_denied | entity-level fallback actuation | learned_value_denied | entity_fallback_default | current_state_brightness or safe_default_brightness |

## 9. Validation Scenarios
Required validation set:
1. Missing room configuration
2. Missing capability mapping
3. Missing configured entity
4. Invalid configured entity
5. Unavailable configured entity
6. Unsupported device capability
7. Unsupported command
8. Missing learned value
9. Invalid learned value
10. No eligible targets
11. No authority bypass
12. No discovery fallback

Evidence should capture room context, capability context, failure condition, fallback path, deterministic default, and explainability fields.

## 10. Non-Goals
This contract does not implement:
- runtime discovery fallback
- room inference or authority replacement
- restoration behavior
- snapshot restoration behavior
- Follow-Me lighting
- new lighting capabilities
- production Home Assistant changes
