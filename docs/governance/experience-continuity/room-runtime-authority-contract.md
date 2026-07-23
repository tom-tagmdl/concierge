# Room Runtime Authority Contract

## Purpose
Preserve the V1 room-ability outcome: Concierge can accurately answer what the current room can do.

## Source Evidence
- docs/governance/experience-continuity/adr-experience-continuity-architecture.md
- docs/governance/experience-continuity/experience-continuity-scope-decisions.md
- docs/governance/experience-continuity/experience-continuity-outcome-preservation-review.md
- docs/governance/experience-continuity/experience-continuity-epic-and-issue-roadmap.md
- docs/governance/experience-continuity/experience-continuity-requirements-backlog.md
- docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md
- docs/governance/experience-continuity/v1-capability-reconstruction.md

## Requirement Coverage
EC-REQ-050

## Scope
Implement room capability awareness by consuming Room Configuration authored room definitions, configured vocabulary, and configured capability-device selections at runtime.

## Non-Goals
- Do not recreate V1 runtime entity discovery.
- Do not infer room capabilities by scanning all Home Assistant entities at runtime.
- Do not bypass the configured room definition.
- Do not treat labels or raw entity membership as primary runtime authority when room configuration exists.

## Architecture / Design Guidance
Preserve the V1 user outcome while replacing the V1 runtime discovery mechanism with the V2 configuration-authored mechanism. Room Configuration is authoritative for Concierge runtime capability awareness.

## Dependencies
- Parent epic: #389
- Issue dependencies: EC-A-02

## Implementation Areas To Inspect
- custom_components/concierge/services.py
- custom_components/concierge/coordinator.py
- custom_components/concierge/storage.py
- docs/governance/capability-discovery-foundation.md
- docs/governance/experience-continuity/experience-continuity-epic-and-issue-roadmap.md

## Acceptance Criteria
- Room ability queries return accurate room-aware capability guidance.
- Capability answers are traceable to configured room definition and capability mappings.
- Runtime answer path does not require broad dynamic discovery scans.
- Outcome remains calm and bounded to the current room context.

## Tests Required
- Query tests proving capability answers map to configured room capability selections.
- Negative tests proving non-configured capabilities return policy-aligned refusal or unavailability response.

## Documentation Required
- Room capability awareness contract documentation reflecting configuration-authored runtime authority.

## Install Gate Impact
INSTALL_GATE_REQUIRED

## Validation Evidence Required
- Test traces mapping room queries to configured room capability definitions.

## Labels / Classification
- INSTALL_GATE_REQUIRED
- PRESERVE OUTCOME / V2 CONFIGURATION-AUTHORED MECHANISM

## Execution Order Notes
Preserve existing order; this remains a dependency for room-aware lighting and media command issues.