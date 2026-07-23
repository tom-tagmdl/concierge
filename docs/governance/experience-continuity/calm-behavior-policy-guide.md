# Calm Behavior Policy Guide

## 1. Purpose
Define measurable, deterministic outcome behavior for Concierge runtime execution so silence, direct refusal, and informational answers are explicitly classified and auditable.

## 2. Scope
Applies to Concierge service outcomes emitted by execute and summary orchestration paths, including room-scoped capability execution, monitoring follow-up, media continuation/playback, and direct execute projections.

## 3. Authority Order
1. HTBW governance and ADR authority in homes_that_behave_well.
2. Concierge architecture contracts in docs/governance and docs/architecture.
3. Concierge runtime implementation in custom_components/concierge/services.py.
4. Concierge behavioral verification in tests/test_services.py.
5. Issue-level acceptance criteria for #415 where not conflicting with higher authority.

## 4. Outcome Taxonomy
Runtime outcomes SHALL emit one deterministic category:
- EXECUTE_SUCCESS: action completed and no refusal condition exists; response may be optional.
- ANSWER_SUCCESS: informational response generated and returned.
- REFUSAL_SUCCESS: request intentionally declined by policy or unavailable capability with direct refusal semantics.
- SILENCE_SUCCESS: action completed with no generated speech where silence is intentional and safe.

## 5. Explainability Fields
Responses SHALL include:
- execution_outcome_category
- silence_as_success
- response_required
- response_generated
- response_message
- refusal_reason
- refusal_category
- room_authority_source
- person_policy_evaluated
- merged_room_authority_source

## 6. Silence-As-Success Policy
Silence is valid only when all are true:
- A requested action executed successfully.
- No refusal condition is present.
- No explicit response requirement is active.
Silence SHALL NOT mask refusal or policy-denied outcomes.

## 7. Direct Refusal Policy
Refusal behavior MUST be explicit and deterministic:
- refusal_reason and refusal_category MUST be emitted.
- response_required MUST be true.
- response_generated MUST be true.
- response_message MUST contain direct refusal language with no suggestion fallback path.

## 8. Deterministic Mapping Rules
- If refusal_reason is present: classify REFUSAL_SUCCESS.
- Else if generated speech/message exists: classify ANSWER_SUCCESS.
- Else if executed is true and response_required is false: classify SILENCE_SUCCESS.
- Else classify EXECUTE_SUCCESS.

## 9. Boundary Preservation
Outcome classification is projection metadata only. It does not transfer authority over:
- capability discovery
- person identity truth
- occupancy truth
- privacy or household memory governance
- experience restoration authority boundaries

## 10. Verification Requirements
Required verification evidence for #415:
- Services implementation with emitted taxonomy fields.
- Tests asserting outcome categories across success, answer, refusal, and silence paths.
- Portable harness evidence package under tmp/ec415_* artifacts.
- Cross-reference matrix linking requirements to docs, code, and tests.

## 11. Evidence Artifacts
- tmp/ec415_portable_harness.py
- tmp/ec415_portable_harness_results.json
- tmp/ec415_closure.py
- tmp/ec415_closure_stdout_latest.txt
- tmp/ec415_test_results.json
- tmp/ec415_scenarios.json
- tmp/ec415_coverage_matrix.json
- tmp/ec415_doc_cross_reference.json
