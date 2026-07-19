# Issue #346 Memory Identity Privacy and Retention Separation Evidence

## Issue

- #346 - P3-R4-E10-03 Memory Identity Privacy and Retention Separation implementation
- Release: Release 4 - Messaging and Household Memory

## Mandatory Readiness Review (Pre-Implementation)

### 1. Authority review summary

PASS.

Authority order applied: ADR -> Contract -> Model -> Existing Implementation -> GitHub Issue.

No authority conflicts identified.

### 2. Ownership review summary

PASS.

Validated ownership boundaries:

- HTBW remains architecture/governance/contract/model authority.
- Concierge remains bounded runtime orchestrator and diagnostics visibility producer.
- Voice Identity authority remains external.
- Privacy authority remains external to household memory metadata.
- Retention authority remains external to household memory metadata.

### 3. Existing implementation review summary

PASS.

Reviewed implementation surfaces:

- `custom_components/concierge/services.py`
- `custom_components/concierge/diagnostics.py`
- `tests/test_services.py`
- `tests/test_diagnostics.py`
- `docs/governance/phase-3/issue-327-privacy-household-memory-boundary-evidence.md`
- `docs/governance/phase-3/issue-344-household-memory-governance-boundary-evidence.md`
- `docs/governance/phase-3/issue-345-memory-ownership-and-consumption-boundary-evidence.md`

Findings:

- #344 and #345 already established bounded household memory governance and ownership/consumption metadata + activity refs + diagnostics visibility.
- Existing `push_person_message` flow already exposes deterministic decision fields suitable for separation explainability.
- Existing deny-path activity refs pattern supports deterministic visibility for separation outcomes.

### 4. Planned file modification list

- `custom_components/concierge/services.py`
- `custom_components/concierge/diagnostics.py`
- `tests/test_services.py`
- `tests/test_diagnostics.py`
- `docs/governance/phase-3/issue-346-memory-identity-privacy-retention-separation-evidence.md`
- `docs/governance/phase-3/release-4-implementation-tracker.md`

### 5. Scope validation

PASS.

Implemented only:

- identity/privacy/retention separation boundary metadata
- deterministic separation explainability metadata tied to existing governed decision inputs
- activity external refs for success/deny separation visibility
- diagnostics visibility for separation boundary references
- tests and durable evidence updates

Did not implement:

- #347 cross-domain separation behavior
- #348 provenance/diagnostics expansion behavior
- non-native permissions frameworks or custom HTML UI patterns
- new retention execution engines or policy adjudicators

### 6. Conflict assessment

PASS.

No blocking authority conflict identified.

### 7. Readiness determination

PASS.

## Required Pre-Coding Review Answers

1. What identity behavior is in scope for #346?
   - Identity separation metadata and non-authority assertions only.
2. What identity behavior is out of scope for #346?
   - Identity authority adjudication, identity source replacement, or identity resolution engines.
3. What privacy behavior is in scope for #346?
   - Privacy separation metadata and references to existing governed privacy boundary outputs.
4. What privacy behavior is out of scope for #346?
   - Privacy policy authority decisions or privacy source-of-truth replacement.
5. What retention behavior is in scope for #346?
   - Retention separation metadata and non-authority assertions only.
6. What retention behavior is out of scope for #346?
   - Retention policy execution, deletion, archival, scheduler, or expiration engines.
7. What authority relationships must hold?
   - Identity, privacy, retention, and source-of-truth authorities remain external and unredefined.
8. What diagnostics should expose separation?
   - Ref counts, latest boundary path/status, latest separation flags, latest separation decision metadata.
9. What diagnostics non-rights must be explicit?
   - Claims for identity/privacy/retention/source-of-truth authority all remain false.
10. What behavior remains deferred after #346?
   - #347 memory messaging/continuity/affinity/occupancy/restoration separation and #348 provenance-depth expansion.

## Implementation Summary

Added response boundary surface:

- `household_memory_identity_privacy_retention_separation_boundary`

Added activity ref surface:

- `household_memory_identity_privacy_retention_separation_boundary`

Boundary includes deterministic:

- identity separation metadata
- privacy separation metadata
- retention separation metadata
- separation explainability based on existing delivery governance decisions
- authority relationship protections and non-authority assertions

## Diagnostics Summary

Added diagnostics visibility surface:

- `household_memory_identity_privacy_retention_separation_visibility`

Diagnostics exposes:

- authority visibility markers for external identity/privacy/retention/source-of-truth authorities
- separation boundary ref counts and latest ref fields
- separation boundary assertions
- diagnostics non-rights authority-claim flags

No private household memory content is exposed by this diagnostics addition.

## Files Changed And Why

- `custom_components/concierge/services.py`
  - Added `_build_household_memory_identity_privacy_retention_separation_boundary(...)`.
  - Added response payload key `household_memory_identity_privacy_retention_separation_boundary`.
  - Added success and deny activity refs for deterministic separation traceability.

- `custom_components/concierge/diagnostics.py`
  - Added `_household_memory_identity_privacy_retention_separation_visibility(state)`.
  - Added diagnostics payload key `household_memory_identity_privacy_retention_separation_visibility`.

- `tests/test_services.py`
  - Added success-path assertions for #346 boundary payload.
  - Added deny-path assertions for #346 separation activity ref and non-authority claims.

- `tests/test_diagnostics.py`
  - Added diagnostics allowlist key coverage for #346 visibility payload.
  - Added assertions for separation visibility, boundary assertions, and diagnostics non-rights claims.

## Validation Evidence

### Static diagnostics validation

- Tool: `get_errors` on touched files
- Result: PASS (no diagnostics errors in touched files)

### Compile validation

- Command: `.venv\Scripts\python.exe -m py_compile custom_components\concierge\services.py custom_components\concierge\diagnostics.py tests\test_services.py tests\test_diagnostics.py`
- Result: PASS

- Command: `.venv\Scripts\python.exe -m compileall custom_components\concierge\services.py custom_components\concierge\diagnostics.py tests\test_services.py tests\test_diagnostics.py`
- Result: PASS

### Pytest validation

- Command: `.venv\Scripts\python.exe -m pytest tests\test_services.py tests\test_diagnostics.py -q`
- Result: blocked by known local environment issue
- Blocker: `ModuleNotFoundError: No module named 'homeassistant.helpers'`

### Deployment validation

- Command: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\scripts\deploy-to-ha.ps1`
- Result: PASS (`robocopy` exit code `1`, successful sync)

### Hash parity validation

- `custom_components/concierge/services.py`
  - Local SHA256: `74798BEC8F23A59344FCF7BE37CBDA3CE2E966ADACFEEAD01D0FF9531A0DCC06`
  - HA SHA256: `74798BEC8F23A59344FCF7BE37CBDA3CE2E966ADACFEEAD01D0FF9531A0DCC06`
  - Match: `True`

- `custom_components/concierge/diagnostics.py`
  - Local SHA256: `EC73EFC4616E32492A2091DC3A10831F76B0C0C8116A3A6D879AB94304B1FCA3`
  - HA SHA256: `EC73EFC4616E32492A2091DC3A10831F76B0C0C8116A3A6D879AB94304B1FCA3`
  - Match: `True`

## Runtime Package Status

- Home Assistant runtime package execution for #346 response and diagnostics payloads is pending user-side execution.
- This document currently contains implementation, compile, deployment, and parity evidence.

## Closure Recommendation

Provisional PASS pending runtime package execution and diagnostics export confirmation.