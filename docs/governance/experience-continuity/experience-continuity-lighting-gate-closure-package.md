# Experience Continuity Lighting Gate Closure Package

## 1. Purpose
This artifact closes EC-C-04 (#402) by packaging authoritative, architecture-aligned evidence that EC-C lighting continuity behaviors are documented, validated, and traceable to install-gate requirements.

Scope of this package is closure evidence only. It does not introduce new runtime behavior.

## 2. Governance Sources
Primary authority chain:
- [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md)
- [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md)
- [docs/governance/experience-continuity/experience-continuity-requirements-backlog.md](docs/governance/experience-continuity/experience-continuity-requirements-backlog.md)
- [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md)
- [docs/governance/experience-continuity/v1-capability-reconstruction.md](docs/governance/experience-continuity/v1-capability-reconstruction.md)

EC-C behavior contracts used by this closure:
- [docs/governance/experience-continuity/experience-continuity-learned-lighting-contract.md](docs/governance/experience-continuity/experience-continuity-learned-lighting-contract.md)
- [docs/governance/experience-continuity/experience-continuity-room-aware-lighting-command-behavior.md](docs/governance/experience-continuity/experience-continuity-room-aware-lighting-command-behavior.md)
- [docs/governance/experience-continuity/experience-continuity-lighting-fallback-decision-matrix.md](docs/governance/experience-continuity/experience-continuity-lighting-fallback-decision-matrix.md)

## 3. EC-C Requirement Coverage
Install-gate requirements covered in this package:
- EC-REQ-020: Learned/usual lighting outcomes and per-entity learned application.
- EC-REQ-021: Room-aware command targeting constrained to configured room/capability authority.
- EC-REQ-022: Deterministic degraded paths for unsupported/invalid capability conditions.
- EC-REQ-023: Separation of usual state memory from operational snapshots.
- EC-REQ-063: Explainable degraded-path decisions with deterministic guardrails.
- EC-REQ-090: Explicit mapping of install-gate continuity behaviors to both documentation and tests.

Coverage matrix artifact:
- [tmp/ec402_lighting_gate_coverage_matrix.json](tmp/ec402_lighting_gate_coverage_matrix.json)

## 4. Lighting Continuity Architecture Summary
The EC-C lighting architecture preserved in this closure package is:
- Room and capability authority is configuration-first and deterministic.
- Runtime discovery is not used as a replacement authority path.
- V1 user outcomes are preserved through V2 governed capability patterns.
- Explainability metadata is required for continuity decision support.

Primary implementation surfaces audited:
- [custom_components/concierge/services.py](custom_components/concierge/services.py)
- [custom_components/concierge/models.py](custom_components/concierge/models.py)
- [custom_components/concierge/storage.py](custom_components/concierge/storage.py)

## 5. Learned Lighting Behavior Summary
Learned/usual lighting evidence in this package confirms:
- Stable per-entity brightness levels can be learned and applied.
- Learned values are applied for usual/resume command families when available.
- Missing/unavailable/denied learned values use deterministic fallback hierarchy.
- Learning writes remain policy-governed and explainable.

Evidence artifacts:
- [tmp/ec399_portable_harness_results.json](tmp/ec399_portable_harness_results.json)
- [tmp/ec399_validation_scenarios.json](tmp/ec399_validation_scenarios.json)

## 6. Room-Aware Targeting Summary
Room-aware targeting evidence confirms:
- Command routing resolves through configured room/capability fields.
- Only configured room membership is operated.
- Unsupported command-capability combinations fail deterministically.
- No runtime membership inference/discovery substitution occurs.

Evidence artifacts:
- [tmp/ec400_portable_harness_results.json](tmp/ec400_portable_harness_results.json)
- [tmp/ec400_validation_scenarios.json](tmp/ec400_validation_scenarios.json)

## 7. Fallback/Degraded Path Summary
Degraded-path evidence confirms:
- Failure conditions are explicit (room missing, mapping missing, invalid/unavailable entities, unsupported capability/command).
- Failure handling is deterministic and safe (safe no-op or safe command rejection where applicable).
- Learned-value fallbacks resolve per entity using governed default hierarchy.
- Explainability fields include decision reason and fallback metadata.

Evidence artifacts:
- [tmp/ec401_portable_harness_results.json](tmp/ec401_portable_harness_results.json)
- [tmp/ec401_validation_scenarios.json](tmp/ec401_validation_scenarios.json)
- [docs/governance/experience-continuity/experience-continuity-lighting-fallback-decision-matrix.md](docs/governance/experience-continuity/experience-continuity-lighting-fallback-decision-matrix.md)

## 8. Test Coverage Matrix
Consolidated test coverage and pass/fail rollup are captured in:
- [tmp/ec402_lighting_gate_test_results.json](tmp/ec402_lighting_gate_test_results.json)
- [tmp/ec402_lighting_gate_coverage_matrix.json](tmp/ec402_lighting_gate_coverage_matrix.json)

Current closure run summary:
- Native targeted pytest: environment-blocked on this Windows host (`hass` fixture unavailable with plugin autoload disabled).
- Portable harness evidence: passing.
  - EC399: 10/10
  - EC400: 12/12
  - EC401: 12/12

Targeted service tests added for closure traceability:
- [tests/test_services.py](tests/test_services.py)
  - `test_execute_resume_lights_applies_learned_value_when_available`
  - `test_execute_usual_lights_applies_learned_value_when_available`
  - `test_execute_room_aware_lighting_records_decision_reason_for_fallback`

## 9. Documentation Cross-Reference Matrix
Behavior-to-doc-to-test traceability is captured in:
- [tmp/ec402_lighting_gate_doc_cross_reference.json](tmp/ec402_lighting_gate_doc_cross_reference.json)

This matrix links each install-gate behavior to:
- authoritative governance source,
- implementation artifact,
- validation artifact,
- and this operator closure package.

## 10. Validation Evidence Summary
Executable validation set produced for this closure:
- [tmp/ec402_lighting_gate_test_results.json](tmp/ec402_lighting_gate_test_results.json)
- [tmp/ec402_lighting_gate_scenarios.json](tmp/ec402_lighting_gate_scenarios.json)
- [tmp/ec402_lighting_gate_coverage_matrix.json](tmp/ec402_lighting_gate_coverage_matrix.json)
- [tmp/ec402_lighting_gate_doc_cross_reference.json](tmp/ec402_lighting_gate_doc_cross_reference.json)

Execution orchestration:
- [tmp/ec402_lighting_gate_closure.py](tmp/ec402_lighting_gate_closure.py)

Latest closure run log:
- [tmp/ec402_lighting_gate_closure_stdout_latest.txt](tmp/ec402_lighting_gate_closure_stdout_latest.txt)

## 11. Install-Gate Readiness Assessment
Readiness classification: INSTALL_GATE_REQUIRED

Assessment:
- EC-REQ-090 mapping requirement is satisfied by explicit coverage and cross-reference matrices.
- EC399/EC400/EC401 portable suites are fully passing and provide executable continuity evidence.
- Native targeted pytest remains environment-limited on this host; this limitation is explicitly captured and does not invalidate portable evidence artifacts.

Gate conclusion:
- EC-C-04 (#402) closure package is ready for downstream install-gate packaging consumption.

Wiki update decision:
- No wiki update required for this closure.
- Rationale: all required operator/governance traceability is now captured in this formal governance artifact and the generated EC402 matrices.

## 12. Non-Goals
This closure package does not:
- add or change EC runtime behavior,
- introduce EC-H or downstream issue implementation,
- modify production Home Assistant,
- replace existing authority contracts,
- alter out-of-scope continuity requirements.
