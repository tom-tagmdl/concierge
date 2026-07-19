# Issue #348 Memory Provenance Diagnostics and Explainability Evidence

## Issue

- #348 - P3-R4-E10-05 Memory Provenance, Diagnostics, and Explainability implementation
- Release: Release 4 - Messaging and Household Memory

## Files Changed

- custom_components/concierge/services.py
- custom_components/concierge/diagnostics.py
- tests/test_services.py
- tests/test_diagnostics.py
- docs/governance/phase-3/issue-348-memory-provenance-diagnostics-explainability-evidence.md
- docs/governance/phase-3/release-4-implementation-tracker.md

## Authority Review

PASS.

Authority order applied: ADR -> Contract -> Model -> Existing Implementation -> GitHub Issue.

Reviewed and aligned to authority sources:

### ADRs

- homes_that_behave_well/docs/architecture/adr-household-memory-governance.md
- homes_that_behave_well/docs/architecture/adr-provenance-governance.md
- homes_that_behave_well/docs/architecture/adr-coordinator-v2-governance.md

### Contracts

- homes_that_behave_well/docs/contracts/household-memory-contract.md
- homes_that_behave_well/docs/contracts/household-coordination-contract.md
- homes_that_behave_well/docs/contracts/concierge-signal-contract.md
- homes_that_behave_well/docs/contracts/provenance-contract.md

### Models

- homes_that_behave_well/docs/models/household-memory-model.md
- homes_that_behave_well/docs/models/provenance-model.md
- homes_that_behave_well/docs/models/signal-model.md
- homes_that_behave_well/docs/models/event-model.md
- homes_that_behave_well/docs/models/household-coordination-snapshot-model.md

### Phase 2 Artifacts

- docs/governance/phase-2/release-4-messaging-and-household-memory-build-execution-plan.md
- docs/governance/phase-2/e10-household-memory-governed-implementation-readiness.md
- docs/governance/phase-2/concierge-v2-end-to-end-governed-implementation-validation.md

No authority conflict identified.

## E15 Execution Review

PASS.

Pre-coding review completed:

1. Memory Provenance: bounded lineage visibility that points to external authority and source service context.
2. Memory Diagnostics: bounded observational status/count surfaces for governance, ownership, consumption, separation, and provenance.
3. Memory Explainability: deterministic runtime-derived explanation of what happened, why, and which boundary governed the outcome.
4. Authority sources establishing memory state: HTBW ADRs/contracts/models plus existing #344-#347 bounded runtime implementation.
5. Provenance information that may be exposed: provenance id presence, source service, room linkage, boundary linkage, routing and decision reason.
6. Provenance information prohibited: identity authority transfer, source-of-truth reassignment, inferred or generated lineage.
7. Required diagnostics: governance/ownership/consumption/separation/provenance counts and latest status fields.
8. Required explainability: runtime decision reason, boundary involved, routing path, delivery/deny outcome context, non-authority assertions.
9. Required non-authority assertions: household truth, identity, messaging, continuity, affinity, occupancy, privacy, retention, restoration, source-of-truth remain false.
10. Intentionally deferred behavior: Release 4 validation closure package work (#349), no new lifecycle/reasoning engines.

## Ownership Drift Review

PASS.

Ownership preserved:

- Concierge remains bounded consumer/orchestrator.
- Voice Identity remains identity authority.
- Asset Intelligence boundaries unchanged.
- HTBW retains governance/contract/model authority.

No new ownership paths were introduced.

## Existing Implementation Review Summary

Reviewed implementation surfaces before coding:

- #344 household memory governance boundary metadata, refs, diagnostics visibility
- #345 ownership/consumption boundary metadata, refs, diagnostics visibility
- #346 identity/privacy/retention separation metadata, refs, diagnostics visibility
- #347 messaging/continuity/affinity/occupancy/restoration separation metadata, refs, diagnostics visibility
- custom_components/concierge/services.py
- custom_components/concierge/diagnostics.py
- tests/test_services.py
- tests/test_diagnostics.py

Findings:

- Existing response and activity ref patterns support additive #348 visibility without behavior changes.
- Existing diagnostics architecture supports an additive visibility slice keyed from activity refs.
- Existing deny-path diagnostics pattern supports deterministic explainability for policy-denied outcomes.

## Provenance Design Summary

Implemented:

- Added response boundary surface: household_memory_provenance_diagnostics_explainability_boundary.
- Added activity ref surface: household_memory_provenance_diagnostics_explainability_boundary.
- Embedded bounded provenance metadata:
  - provenance_ref_count
  - provenance_status
  - provenance_id
  - provenance_source_service
  - provenance_created_in_room
- Added explicit provenance non-authority controls:
  - no provenance replacement
  - no provenance reconstruction
  - no authority transfer

Not implemented:

- provenance creation authority
- inferred lineage generation
- alternate source-of-record behavior

## Diagnostics Design Summary

Implemented diagnostics visibility surface:

- household_memory_provenance_diagnostics_explainability_visibility

Diagnostics now expose observational counts/statuses for:

- governance boundary refs
- ownership boundary refs
- consumption boundary refs
- identity/privacy/retention separation refs
- messaging/continuity/affinity/occupancy/restoration separation refs
- provenance refs

Diagnostics remain observational only and do not alter runtime decisions.

## Explainability Design Summary

Implemented deterministic explainability visibility for #348:

- what_happened_explainable
- why_it_happened_explainable
- which_boundary_applied_explainable
- which_authority_established_outcome_explainable
- which_authority_not_claimed_explainable

Runtime-derived explainability fields include:

- latest_delivery_permitted
- latest_decision_reason
- latest_governance_boundary_involved
- latest_delivery_channel
- latest_selected_service
- latest_selected_target_id
- latest_routing_path

Explicit safeguards:

- runtime_derived_only: true
- generated_reasoning_used: false
- probabilistic_reasoning_used: false

## Non-Authority Assertions

All asserted as false in both response and diagnostics:

- claims_household_truth_authority
- claims_identity_authority
- claims_messaging_authority
- claims_continuity_authority
- claims_affinity_authority
- claims_occupancy_authority
- claims_privacy_authority
- claims_retention_authority
- claims_restoration_authority
- claims_source_of_truth_authority

## Tests Run

Local validation:

- py_compile custom_components/concierge/services.py custom_components/concierge/diagnostics.py tests/test_services.py tests/test_diagnostics.py
  - PASS

Targeted pytest:

- pytest tests/test_services.py -k "push_person_message" -q
  - BLOCKED (environment): ModuleNotFoundError: No module named 'homeassistant.helpers'

Interpretation:

- Blocker is environment-related and previously known.
- Not classified as implementation failure.

## Deployment Result

Deployment command:

- powershell -ExecutionPolicy Bypass -File .\scripts\deploy-to-ha.ps1

Result:

- robocopy exit code: 1 (successful sync)
- files copied: 2

Runtime hash parity verification:

- SERVICES_MATCH=True
- DIAGNOSTICS_MATCH=True
- services.py SHA256: 6C8DCD8E030C5BE092C6957F8341062DEEDD3701F9B9E990F2E531CA1C228756
- diagnostics.py SHA256: DE175BBC0CE4EFF1A086C024AE18292CDD6A94E266EBF0D1797E93D0913E7A6A

Restart guidance:

- Restart Home Assistant before runtime validation execution.
- After restart, run the YAML package below and export diagnostics JSON for evidence capture.

## Runtime Validation Package

Use Developer Tools -> Actions and run each block in order.

### Test 1 Governance Provenance Visibility

```yaml
action: concierge.push_person_message
data:
  person_id: tom
  target_id: web_ui
  message: "#348 Test 1 governance provenance visibility"
```

Expect response keys:

- household_memory_governance_boundary
- household_memory_provenance_diagnostics_explainability_boundary

### Test 2 Ownership Provenance Visibility

```yaml
action: concierge.push_person_message
data:
  person_id: tom
  target_id: web_ui
  message: "#348 Test 2 ownership provenance visibility"
```

Expect response keys:

- household_memory_ownership_consumption_boundary
- household_memory_provenance_diagnostics_explainability_boundary

### Test 3 Consumption Provenance Visibility

```yaml
action: concierge.push_person_message
data:
  person_id: tom
  target_id: web_ui
  message: "#348 Test 3 consumption provenance visibility"
```

Expect:

- household_memory_ownership_consumption_boundary.memory_consumption_boundary.consumption_permitted
- household_memory_provenance_diagnostics_explainability_boundary.governance_explainability.decision_reason

### Test 4 Identity Privacy Retention Separation Provenance Visibility

```yaml
action: concierge.push_person_message
data:
  person_id: tom
  target_id: web_ui
  message: "#348 Test 4 identity privacy retention provenance visibility"
```

Expect response keys:

- household_memory_identity_privacy_retention_separation_boundary
- household_memory_provenance_diagnostics_explainability_boundary

### Test 5 Messaging Continuity Affinity Occupancy Restoration Separation Provenance Visibility

```yaml
action: concierge.push_person_message
data:
  person_id: tom
  target_id: web_ui
  message: "#348 Test 5 messaging continuity affinity occupancy restoration provenance visibility"
```

Expect response keys:

- household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary
- household_memory_provenance_diagnostics_explainability_boundary

### Test 6 Explainability Visibility

```yaml
action: concierge.push_person_message
data:
  person_id: tom
  target_id: web_ui
  message: "#348 Test 6 explainability visibility"
```

Expect in response:

- household_memory_provenance_diagnostics_explainability_boundary.explainability_visibility.what_happened_explainable = true
- household_memory_provenance_diagnostics_explainability_boundary.explainability_visibility.why_it_happened_explainable = true
- household_memory_provenance_diagnostics_explainability_boundary.explainability_visibility.runtime_derived_only = true

### Test 7 Governance Diagnostics Visibility

```yaml
action: concierge.get_diagnostics
```

If get_diagnostics service is unavailable, use diagnostics download in Config Entries and inspect JSON.

Expect diagnostics key:

- household_memory_provenance_diagnostics_explainability_visibility

### Test 8 Memory Diagnostics Visibility

```yaml
action: concierge.push_person_message
data:
  person_id: tom
  target_id: web_ui
  message: "#348 Test 8 memory diagnostics visibility"
```

Then export diagnostics and verify:

- diagnostics_visibility.governance_boundary_ref_count >= 1
- diagnostics_visibility.ownership_boundary_ref_count >= 1
- diagnostics_visibility.consumption_boundary_ref_count >= 1
- diagnostics_visibility.identity_privacy_retention_separation_ref_count >= 1
- diagnostics_visibility.messaging_continuity_affinity_occupancy_restoration_separation_ref_count >= 1
- diagnostics_visibility.provenance_ref_count >= 1

### Test 9 Non-Authority Assertions

```yaml
action: concierge.push_person_message
data:
  person_id: tom
  target_id: web_ui
  message: "#348 Test 9 non-authority assertions"
```

Verify response non_authority_assertions are all false for:

- household truth, identity, messaging, continuity, affinity, occupancy, privacy, retention, restoration, source-of-truth.

### Test 10 Diagnostics Export Verification

Export config entry diagnostics JSON and verify object:

- household_memory_provenance_diagnostics_explainability_visibility

Required PASS checks:

- provenance_visibility.provenance_diagnostics_boundary_ref_count >= 1
- provenance_visibility.latest_boundary_path = governed_household_memory_provenance_diagnostics_explainability_boundary
- provenance_visibility.latest_boundary_status = active
- explainability_visibility.runtime_derived_only = true
- explainability_visibility.generated_reasoning_used = false
- diagnostics_non_rights claims are all false

## Durable Evidence Updated

- Added issue-specific evidence document:
  - docs/governance/phase-3/issue-348-memory-provenance-diagnostics-explainability-evidence.md
- Updated Release 4 tracker:
  - docs/governance/phase-3/release-4-implementation-tracker.md

## Closure Recommendation

PASS Candidate.

Condition:

- Final closure should follow successful runtime package execution and diagnostics export confirmation in Home Assistant.
