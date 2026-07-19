# Release 4 Implementation Tracker

- Tracker Issue: #290
- Generated: 2026-07-11

## Included Issues

- #339 - P3-R4-E9-01 Messaging governance boundary implementation
- #340 - P3-R4-E9-02 Messaging provenance implementation
- #341 - P3-R4-E9-03 Notification and delivery boundary implementation
- #342 - P3-R4-E9-04 Recipient, consent, privacy, and visibility boundary implementation
- #343 - P3-R4-E9-05 Messaging diagnostics and explainability implementation
- #344 - P3-R4-E10-01 Household memory governance boundary implementation
- #345 - P3-R4-E10-02 Memory ownership and consumption boundary implementation
- #346 - P3-R4-E10-03 Memory identity/privacy/retention separation implementation
- #347 - P3-R4-E10-04 Memory messaging/continuity/affinity/occupancy/restoration separation implementation
- #348 - P3-R4-E10-05 Memory provenance, diagnostics, and explainability implementation
- #349 - P3-R4-VAL-01 Release 4 governed implementation validation

## Authority Source Hardening

A Phase 3 authority-source hardening pass was performed across the canonical Phase 3 backlog.

Implementation issues were reviewed against canonical HTBW ADRs, contracts, and models in the homes_that_behave_well repository.

Supporting source references from voice_identity and asset_intelligence were added where relevant.

No missing authority sources were invented.

No implementation code was changed.

No roadmap scope was expanded.

## Execution Evidence

- #339 - Messaging governance boundary implementation evidence: `docs/governance/phase-3/issue-339-messaging-governance-boundary-evidence.md`
- #340 - Messaging provenance implementation evidence: `docs/governance/phase-3/issue-340-messaging-provenance-evidence.md`
	- Local deployment executed via `scripts/deploy-to-ha.ps1` on 2026-07-19 with `robocopy` exit code `1` (successful sync)
	- Runtime file SHA256 parity verified for `custom_components/concierge/services.py` and `custom_components/concierge/diagnostics.py`
	- Home Assistant runtime validation completed with PASS outcomes for web UI, explicit voice/speaker entity routes, iPad explicit mobile route, iPad person fallback route, and non-authority assertions
	- Symbolic room voice/speaker negative cases observed as expected configuration-dependent guardrail behavior
	- Closure recommendation: PASS
- #341 - Notification and delivery boundary implementation evidence: `docs/governance/phase-3/issue-341-notification-delivery-boundary-evidence.md`
	- Delivery boundary metadata and execution tracking added to `concierge.push_person_message` response and activity refs
	- Delivery boundary diagnostics visibility added in `notification_delivery_boundary_visibility`
	- Local deployment executed via `scripts/deploy-to-ha.ps1` on 2026-07-19 with `robocopy` exit code `1` (successful sync)
	- Runtime file SHA256 parity verified for `custom_components/concierge/services.py` and `custom_components/concierge/diagnostics.py`
	- Closure recommendation: PASS candidate pending Tom runtime validation package execution
- #342 - Recipient, consent, privacy, and visibility boundary implementation evidence: `docs/governance/phase-3/issue-342-recipient-consent-privacy-visibility-boundary-evidence.md`
	- Recipient-consent-privacy-visibility boundary metadata and deterministic eligibility enforcement added to `concierge.push_person_message`
	- Boundary diagnostics visibility added in `recipient_consent_privacy_visibility_boundary_visibility`
	- Local deployment executed via `scripts/deploy-to-ha.ps1` on 2026-07-19 with `robocopy` exit code `1` (successful sync)
	- Runtime file SHA256 parity verified for `custom_components/concierge/services.py` and `custom_components/concierge/diagnostics.py`
	- Runtime package execution completed for recipient/consent allow+deny paths and response-level non-authority assertions
	- Privacy boundary reason-code runtime confirmation achieved via explicit entity retest (`privacy_boundary_channel_restricted`)
	- Visibility-specific reason-code runtime confirmation achieved via isolation retest (`visibility_boundary_channel_restricted`) with `privacy_mode: standard` and `visibility_mode: restricted`
	- Diagnostics export assertions for #342 visibility payload remain supplemental
	- Closure recommendation: PASS candidate pending supplemental runtime evidence capture
- #343 - Messaging diagnostics and explainability implementation evidence: `docs/governance/phase-3/issue-343-messaging-diagnostics-and-explainability-evidence.md`
	- Added `messaging_diagnostics_explainability` response surface for deterministic messaging decision explainability
	- Added `messaging_diagnostics_explainability` activity refs to support success/deny traceability without authority transfer
	- Added diagnostics visibility surface `messaging_diagnostics_explainability_visibility`
	- Local deployment executed via `scripts/deploy-to-ha.ps1` on 2026-07-19 with `robocopy` exit code `1` (successful sync)
	- Runtime file SHA256 parity verified for `custom_components/concierge/services.py` and `custom_components/concierge/diagnostics.py`
	- Runtime validation confirms success explainability, operational failure distinguishability, recipient/consent/privacy/visibility deny explainability, boundary/provenance response visibility, and non-authority assertions
	- Closure recommendation: PASS candidate pending diagnostics export evidence (Test 10)
- #344 - Household memory governance boundary implementation evidence: `docs/governance/phase-3/issue-344-household-memory-governance-boundary-evidence.md`
	- Added `household_memory_governance_boundary` response surface for bounded non-authoritative household memory governance metadata
	- Added `household_memory_governance_boundary` activity refs for traceable boundary visibility
	- Added diagnostics visibility surface `household_memory_governance_boundary_visibility`
	- Local deployment executed via `scripts/deploy-to-ha.ps1` on 2026-07-19 with `robocopy` exit code `1` (successful sync)
	- Runtime file SHA256 parity verified for `custom_components/concierge/services.py` and `custom_components/concierge/diagnostics.py`
	- Home Assistant restart confirmed healthy (no restart log errors)
	- Runtime package Tests 1-9 executed with PASS outcomes, including boundary visibility, non-authority assertions, and messaging/provenance regression checks
	- Runtime diagnostics export Test 10 verified with `household_memory_boundary_ref_count=18`, `latest_boundary_status=active`, and all diagnostics non-rights authority claims `false`
	- Closure recommendation: PASS
- #345 - Memory ownership and consumption boundary implementation evidence: `docs/governance/phase-3/issue-345-memory-ownership-and-consumption-boundary-evidence.md`
	- Added `household_memory_ownership_consumption_boundary` response surface for deterministic ownership and consumption boundary metadata
	- Added `household_memory_ownership_consumption_boundary` activity refs for success/deny boundary traceability
	- Added diagnostics visibility surface `household_memory_ownership_consumption_boundary_visibility`
	- Added ownership and consumption non-authority assertions tied to existing governed decision inputs
	- Local compile validation passed (`py_compile` and `compileall`)
	- Targeted pytest hit known local environment blocker (`ModuleNotFoundError: No module named 'homeassistant.helpers'`)
	- Local deployment executed via `scripts/deploy-to-ha.ps1` on 2026-07-19 with `robocopy` exit code `1` (successful sync)
	- Runtime file SHA256 parity verified for `custom_components/concierge/services.py` and `custom_components/concierge/diagnostics.py`
	- Home Assistant restart confirmed healthy (no restart log errors)
	- Runtime package Tests 1-9 executed with PASS outcomes for ownership visibility, consumption visibility, boundary assertions, explainability, and non-authority assertions
	- Runtime diagnostics export Test 10 verified with `ownership_boundary_ref_count=20`, `latest_boundary_status=active`, `consumption_permitted_count=20`, `consumption_denied_count=0`, and all diagnostics non-rights authority claims `false`
	- Closure recommendation: PASS
- #346 - Memory identity/privacy/retention separation implementation evidence: `docs/governance/phase-3/issue-346-memory-identity-privacy-retention-separation-evidence.md`
	- Added `household_memory_identity_privacy_retention_separation_boundary` response surface for deterministic identity/privacy/retention separation metadata
	- Added `household_memory_identity_privacy_retention_separation_boundary` activity refs for success/deny separation traceability
	- Added diagnostics visibility surface `household_memory_identity_privacy_retention_separation_visibility`
	- Added separation non-authority assertions preserving external identity/privacy/retention/source-of-truth authorities
	- Local compile validation passed (`py_compile` and `compileall`)
	- Targeted pytest hit known local environment blocker (`ModuleNotFoundError: No module named 'homeassistant.helpers'`)
	- Local deployment executed via `scripts/deploy-to-ha.ps1` on 2026-07-19 with `robocopy` exit code `1` (successful sync)
	- Runtime file SHA256 parity verified for `custom_components/concierge/services.py` and `custom_components/concierge/diagnostics.py`
	- Closure recommendation: Provisional PASS pending runtime package execution and diagnostics export confirmation
