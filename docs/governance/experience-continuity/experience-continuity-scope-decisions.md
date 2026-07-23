# Experience Continuity Scope Decisions Before Requirements Backlog

## Status
Accepted for backlog preparation

## Source Artifacts
- [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md)
- [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md)
- [docs/governance/experience-continuity/v1-capability-reconstruction.md](docs/governance/experience-continuity/v1-capability-reconstruction.md)
- [custom_components/concierge/services.yaml](custom_components/concierge/services.yaml)
- [custom_components/concierge/services.py](custom_components/concierge/services.py)
- [custom_components/concierge/coordinator.py](custom_components/concierge/coordinator.py)
- [tests/test_services.py](tests/test_services.py)
- [tests/test_foundation.py](tests/test_foundation.py)
- [homes_that_behave_well/docs/contracts/room-awareness-contract.md](../homes_that_behave_well/docs/contracts/room-awareness-contract.md)
- [homes_that_behave_well/docs/contracts/person-identity-contract.md](../homes_that_behave_well/docs/contracts/person-identity-contract.md)
- [homes_that_behave_well/docs/contracts/occupancy-and-presence-contract.md](../homes_that_behave_well/docs/contracts/occupancy-and-presence-contract.md)
- [voice_identity/custom_components/voice_identity/services.py](../voice_identity/custom_components/voice_identity/services.py)
- [asset_intelligence/custom_components/asset_intelligence/advisory.py](../asset_intelligence/custom_components/asset_intelligence/advisory.py)

## Scope Decisions
1. Bedtime, Good Morning, and Goodnight remain out of Concierge V2 Experience Continuity parity scope.
2. Primary Bedroom Alarm automations are out of scope for Concierge V2 Experience Continuity parity and do not block initial Concierge V2 install readiness.
3. True follow-me or cross-room media is post-install enhancement scope, not an initial install-gate requirement.
4. Initial implementation does not require one-to-one preservation of V1 helper schemas; helper-backed state families use explicit disposition policy.
5. Initial Experience Continuity install gate remains strict for room-aware continuity behaviors and safety behaviors.

## In-Scope For Initial Concierge V2 Experience Continuity Gate
- learned or usual lighting behavior
- room-aware lighting command behavior
- room-aware play jazz or play genre behavior
- room-aware continue or resume behavior
- Sonos speech output with duck and restore behavior
- room capability discovery
- monitoring follow-up answers
- capability-not-available graceful refusal
- guest, unknown, and low-confidence safe defaults
- silence-is-success behavior
- person-aware preference readiness where identity confidence is available
- tests and documentation for all install-gate behaviors

## Out-of-Scope For Initial Concierge V2 Experience Continuity Gate
- Bedtime routine replacement
- Good Morning routine replacement
- Goodnight routine replacement
- Primary Bedroom Alarm replacement
- true cross-room follow-me media as an install-gate blocker
- exact V1 helper schema preservation

## Post-Install Enhancements
- true cross-room follow-me media behavior
- additional media transition policies beyond initial room-aware gate
- additional mode-specific continuity tuning once install gate passes

## Helper-Backed State Disposition Policy
Each V1 helper-backed state family must be assigned one disposition:
- migrate if deterministic and safe
- seed V2 state from V1 helper data if readable
- re-learn under V2 governance
- replace with room default
- replace with person plus room default
- retire as V1-only implementation detail

Backlog generation must not assume V1 helper schema is the V2 storage model.

## Impact On V1-to-V2 Parity Matrix
- Primary Bedroom Alarm scope classification is resolved to OUT_OF_SCOPE for initial Concierge V2 Experience Continuity parity.
- Follow-me or cross-room media is resolved to POST_INSTALL_ENHANCEMENT and is not part of the initial install gate.
- The initial install-readiness classification remains NOT_READY because required in-scope gate behaviors remain GAP, PARTIAL, or REDESIGN in the parity matrix.

## Impact On ADR Open Questions
This artifact resolves previously open scope questions related to:
- Primary Bedroom Alarm parity inclusion
- follow-me or cross-room media install-gate requirement
- Bedtime, Good Morning, Goodnight parity inclusion
- helper migration expectations for initial implementation

The ADR should reference this artifact for scope authority prior to requirements backlog generation.

## Impact On Requirements Backlog Generation
Backlog generation after this scope cleanup must:
- avoid creating install-gate requirements for out-of-scope routine domains and alarm replacement
- include strict room-aware continuity requirements for lighting, audio, media, monitoring, guardrails, and identity-safe defaults
- include helper-family disposition requirements instead of schema-locking requirements
- keep Concierge V2 install-readiness as NOT_READY until in-scope gate behaviors are covered

## Remaining Open Questions, If Any
1. Is Sonos-as-room-voice mandatory for initial install gate or allowed configurable override in the same gate phase?
2. What minimum evidence threshold will be accepted for silence-is-success verification across domains?
3. Which specific helper families should prefer seed-from-V1 versus re-learn-first when both are feasible?
4. What exact test suite structure is required to declare each install-gate behavior complete?
