# Issue #347 Memory Messaging Continuity Affinity Occupancy Restoration Separation Evidence

## Issue

- #347 - P3-R4-E10-04 Memory Messaging Continuity Affinity Occupancy Restoration Separation implementation
- Release: Release 4 - Messaging and Household Memory

## Mandatory Readiness Review (Pre-Implementation)

### 1. Authority review summary

PASS.

Authority order applied: ADR -> Contract -> Model -> Existing Implementation -> GitHub Issue.

No authority conflicts identified.

### 2. Contract review summary

PASS.

Reviewed contracts:

- `homes_that_behave_well/docs/contracts/household-memory-contract.md`
- `homes_that_behave_well/docs/contracts/household-coordination-contract.md`
- `homes_that_behave_well/docs/contracts/concierge-signal-contract.md`
- `homes_that_behave_well/docs/contracts/provenance-contract.md`

Contract alignment preserved:

- memory may consume messaging/continuity/affinity/occupancy/restoration context
- memory does not become authority for those domains
- source-of-truth remains external

### 3. Model review summary

PASS.

Reviewed models:

- `homes_that_behave_well/docs/models/household-memory-model.md`
- `homes_that_behave_well/docs/models/provenance-model.md`
- `homes_that_behave_well/docs/models/signal-model.md`
- `homes_that_behave_well/docs/models/event-model.md`
- `homes_that_behave_well/docs/models/household-coordination-snapshot-model.md`

Model alignment preserved:

- occupancy and restoration remain external
- memory references remain bounded consumption metadata
- no identity/occupancy/restoration behavioral authority transfer

### 4. Existing implementation review summary

PASS.

Reviewed existing implementation:

- #344 `household_memory_governance_boundary`
- #345 `household_memory_ownership_consumption_boundary`
- #346 `household_memory_identity_privacy_retention_separation_boundary`
- `custom_components/concierge/services.py`
- `custom_components/concierge/diagnostics.py`
- `tests/test_services.py`
- `tests/test_diagnostics.py`

Findings:

- Existing boundaries already provide deterministic response metadata and activity refs for push-person-message.
- Existing diagnostics pattern supports new boundary visibility slices from activity refs.
- Existing deny-path pattern supports deterministic non-authority visibility for policy-denied outcomes.

### 5. Scope validation

PASS.

Implemented only:

- messaging separation metadata
- continuity separation metadata
- affinity separation metadata
- occupancy separation metadata
- restoration separation metadata
- diagnostics separation visibility
- deterministic separation explainability metadata
- tests and durable evidence updates

Did not implement:

- message generation/delivery ownership changes
- continuity processing engines
- affinity scoring or ranking
- occupancy truth determination
- restoration execution workflows
- provenance expansion behaviors for #348

## Required Pre-Coding Review Answers

1. How does Household Memory relate to Messaging?
   - Household Memory may reference messaging context and provenance lineage but does not become message, delivery, or truth authority.
2. How does Household Memory relate to Continuity?
   - Household Memory may contribute bounded context references; continuity authority and reconstruction remain external.
3. How does Household Memory relate to Affinity?
   - Household Memory may reference affinity context; affinity scoring/ranking authority remains external.
4. How does Household Memory relate to Occupancy?
   - Household Memory may reference occupancy context; occupancy truth/determination authority remains external.
5. How does Household Memory relate to Restoration?
   - Household Memory may support restoration context; restoration behavior and outcomes remain external.
6. Which relationships are allowed?
   - Context reference and governed consumption relationships only.
7. Which relationships are prohibited?
   - Authority redefinition, truth ownership transfer, and behavior-engine takeover for the separated domains.
8. What authority claims are prohibited?
   - Messaging, continuity, affinity, occupancy, restoration, and source-of-truth authority claims.
9. What diagnostics are required?
   - Separation ref counts, latest separation statuses, latest boundary status/path, and non-authority claim flags.
10. What remains deferred to #348?
   - Memory provenance diagnostics/explainability depth expansion and related provenance-enhancement surfaces.

## Design Summaries

### Messaging separation design summary

- Memory may reference messaging context.
- Memory does not become messaging authority, delivery authority, or message truth authority.

### Continuity separation design summary

- Memory may contribute context references.
- Memory does not become continuity authority or continuity reconstruction behavior.

### Affinity separation design summary

- Memory may reference affinity context.
- Memory does not calculate affinity or own affinity authority.

### Occupancy separation design summary

- Memory may reference occupancy context.
- Memory does not determine occupancy and does not own occupancy truth.

### Restoration separation design summary

- Memory may support restoration context.
- Memory does not execute restoration and does not own restoration outcomes.

## Files Changed And Why

- `custom_components/concierge/services.py`
  - Added `_build_household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary(...)`.
  - Added response payload key `household_memory_messaging_continuity_affinity_occupancy_restoration_separation_boundary`.
  - Added success and deny activity refs for #347 separation traceability.

- `custom_components/concierge/diagnostics.py`
  - Added `_household_memory_messaging_continuity_affinity_occupancy_restoration_separation_visibility(state)`.
  - Added diagnostics payload key `household_memory_messaging_continuity_affinity_occupancy_restoration_separation_visibility`.

- `tests/test_services.py`
  - Added success-path assertions for #347 boundary payload.
  - Added deny-path assertions for #347 separation activity refs and non-authority claims.

- `tests/test_diagnostics.py`
  - Added diagnostics key allowlist coverage for #347.
  - Added #347 diagnostics visibility and non-authority assertions.

- `docs/governance/phase-3/issue-347-memory-messaging-continuity-affinity-occupancy-restoration-separation-evidence.md`
  - Durable #347 evidence artifact.

- `docs/governance/phase-3/release-4-implementation-tracker.md`
  - Added #347 execution evidence summary.

## Validation Evidence

### Static diagnostics validation

- Tool: `get_errors` on touched files
- Result: PASS (no diagnostics errors in touched files)

### Compile validation

- Command: `.venv\Scripts\python.exe -m py_compile custom_components\concierge\services.py custom_components\concierge\diagnostics.py tests\test_services.py tests\test_diagnostics.py`
- Result: PASS

- Command: `.venv\Scripts\python.exe -m compileall custom_components\concierge\services.py custom_components\concierge\diagnostics.py tests\test_services.py tests\test_diagnostics.py`
- Result: PASS

### Targeted pytest

- Command: `.venv\Scripts\python.exe -m pytest tests\test_services.py tests\test_diagnostics.py -q`
- Result: blocked by known local environment issue
- Blocker: `ModuleNotFoundError: No module named 'homeassistant.helpers'`

### Deployment validation

- Command: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\scripts\deploy-to-ha.ps1`
- Result: PASS (`robocopy` exit code `1`, successful sync)

### Hash parity validation

- `custom_components/concierge/services.py`
   - Local SHA256: `0AAEF4629FEF19E435CFEB0A43CAEE20281FF9E62C77607FB0129534DD0D72CF`
   - HA SHA256: `0AAEF4629FEF19E435CFEB0A43CAEE20281FF9E62C77607FB0129534DD0D72CF`
   - Match: `True`

- `custom_components/concierge/diagnostics.py`
   - Local SHA256: `60D3EBFC174A3B21FCD0FC3B395BE5952007FE4C208C92421D06060DBBF40CAA`
   - HA SHA256: `60D3EBFC174A3B21FCD0FC3B395BE5952007FE4C208C92421D06060DBBF40CAA`
   - Match: `True`

## Runtime Validation Package Status

- Pending user-side Home Assistant runtime package execution and diagnostics export capture.

## Deferred Scope Confirmation

- #348 memory provenance diagnostics and explainability expansion remains deferred.

## Closure Recommendation

Provisional PASS pending compile/deploy/hash/runtime validation evidence.

Compile/deploy/hash evidence is complete; runtime package execution remains pending.