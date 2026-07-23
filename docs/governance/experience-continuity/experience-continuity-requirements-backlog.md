# Experience Continuity Requirements Backlog

## Status
Draft for architecture-governed backlog planning

## Purpose
Define architecture-governed requirements for Concierge V2 Experience Continuity based on established authority artifacts, without creating implementation code, issues, or new ADRs.

## Governing Sources
- [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md)
- [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md)
- [docs/governance/experience-continuity/v1-capability-reconstruction.md](docs/governance/experience-continuity/v1-capability-reconstruction.md)
- [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md)

## Scope Baseline
In scope for initial production install gate is defined by [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md).

Out-of-scope and post-install enhancement boundaries in this backlog follow that artifact exactly.

## Backlog Rules
- Requirements are outcome-governed and architecture-governed.
- Requirements must not assume one-for-one V1 automation-to-service translation.
- Requirements must preserve ownership boundaries from governing contracts and models.
- Requirements in this document do not prescribe implementation internals.

## Requirement Format
Each requirement includes:
- Requirement ID
- Gate Tier
- Requirement Statement
- Evidence Trace
- Verification Intent

Gate Tier values:
- INSTALL_GATE_REQUIRED
- INSTALL_GATE_SUPPORTING
- POST_INSTALL_ENHANCEMENT

## A. Governance And Traceability Requirements
### EC-REQ-001
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Concierge V2 Experience Continuity shall be evaluated by outcome parity, not by object or name parity.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md), [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md)
- Verification Intent: Parity validation artifacts demonstrate user-outcome checks for each in-scope capability.

### EC-REQ-002
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Experience Continuity requirements shall preserve ownership boundaries across Concierge, Foundation and HTBW, Voice Identity, and Asset Intelligence.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md)
- Verification Intent: Requirements and validation show no transfer of room truth, identity attribution, or asset stewardship ownership.

### EC-REQ-003
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Concierge V2 install-readiness shall remain NOT_READY until all initial install-gate requirements are verified or explicitly scoped out by governance decision.
- Evidence Trace: [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md), [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md)
- Verification Intent: Final readiness report references requirement-level pass status for all install-gate requirements.

## B. Continuity State Model Requirements
### EC-REQ-010
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Experience Continuity shall define explicit continuity state categories for learned usual state, operational snapshot state, and fallback default state.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md)
- Verification Intent: State model documentation and diagnostics expose category distinction.

### EC-REQ-011
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Experience Continuity shall represent capture and restore behavior distinctly for operational restore and preference restore.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md)
- Verification Intent: Test scenarios validate operational restore does not automatically imply preference restore.

### EC-REQ-012
- Gate Tier: INSTALL_GATE_SUPPORTING
- Requirement Statement: Experience Continuity state shall include explicit continuity scope references sufficient to distinguish entity, room, person, household, and mode contexts.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md), [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md)
- Verification Intent: Traceability outputs show continuity scope used for each continuity decision.

## C. Lighting Continuity Requirements
### EC-REQ-020
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Concierge V2 shall provide learned or usual lighting behavior for in-scope room-aware continuity outcomes.
- Evidence Trace: [docs/governance/experience-continuity/v1-capability-reconstruction.md](docs/governance/experience-continuity/v1-capability-reconstruction.md), [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md)
- Verification Intent: Validation demonstrates usual lighting outcomes in resolved room contexts.

### EC-REQ-021
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Concierge V2 shall support room-aware lighting command continuity with deterministic fallback behavior when preferred context is unavailable.
- Evidence Trace: [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md), [docs/governance/experience-continuity/v1-capability-reconstruction.md](docs/governance/experience-continuity/v1-capability-reconstruction.md)
- Verification Intent: Tests cover known room, unknown room, and no-device fallback.

### EC-REQ-022
- Gate Tier: INSTALL_GATE_SUPPORTING
- Requirement Statement: Lighting continuity shall distinguish brightness restore, color-temperature restore, and color restore where supported, with safe defaults where unsupported.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md)
- Verification Intent: Requirement validation matrix covers supported and unsupported light capabilities.

### EC-REQ-023
- Gate Tier: INSTALL_GATE_SUPPORTING
- Requirement Statement: Lighting continuity shall preserve separation between learned usual restore and immediate operational snapshot restore.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md)
- Verification Intent: Scenario tests show both restore modes produce distinct expected outcomes.

## D. Audio Continuity Requirements
### EC-REQ-030
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Concierge V2 shall provide Sonos speech output with explicit duck and restore behavior for in-scope room continuity interactions.
- Evidence Trace: [docs/governance/experience-continuity/v1-capability-reconstruction.md](docs/governance/experience-continuity/v1-capability-reconstruction.md), [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md)
- Verification Intent: Tests verify duck begins and restore completes under normal and degraded paths.

### EC-REQ-031
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Audio continuity shall separate speech output continuity from media continuation continuity.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md)
- Verification Intent: Validation confirms speech continuity operations do not imply media auto-resume unless policy allows.

### EC-REQ-032
- Gate Tier: INSTALL_GATE_SUPPORTING
- Requirement Statement: Audio continuity shall model chat volume, duck volume, and music volume as separate policy concerns.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md), [docs/governance/experience-continuity/v1-capability-reconstruction.md](docs/governance/experience-continuity/v1-capability-reconstruction.md)
- Verification Intent: Coverage matrix validates each volume concern independently.

### EC-REQ-033
- Gate Tier: INSTALL_GATE_SUPPORTING
- Requirement Statement: Audio continuity shall provide deterministic fallback behavior when preferred room speaker is unavailable.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md), [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md)
- Verification Intent: Tests cover no-Sonos and degraded speaker availability paths.

## E. Media Continuity Requirements
### EC-REQ-040
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Concierge V2 shall provide room-aware play jazz and play genre behavior in resolved room context.
- Evidence Trace: [docs/governance/experience-continuity/v1-capability-reconstruction.md](docs/governance/experience-continuity/v1-capability-reconstruction.md), [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md)
- Verification Intent: Acceptance tests verify resolved-room genre playback outcomes.

### EC-REQ-041
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Concierge V2 shall provide room-aware continue or resume media behavior.
- Evidence Trace: [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md), [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md)
- Verification Intent: Tests validate continue behavior in current room context.

### EC-REQ-042
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Concierge V2 shall capture last-media context sufficient for room-aware continuation decisions.
- Evidence Trace: [docs/governance/experience-continuity/v1-capability-reconstruction.md](docs/governance/experience-continuity/v1-capability-reconstruction.md), [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md)
- Verification Intent: Validation demonstrates durable last-media references used by continuation outcomes.

### EC-REQ-043
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Media continuity shall enforce manual-stop respect and cooldown behavior to prevent unwanted auto-start.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md), [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md)
- Verification Intent: Tests verify cooldown and no-auto-start behavior after explicit user stop.

### EC-REQ-044
- Gate Tier: POST_INSTALL_ENHANCEMENT
- Requirement Statement: True cross-room follow-me media behavior may be introduced as post-install enhancement after initial install gate completion.
- Evidence Trace: [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md)
- Verification Intent: Deferred scope marker remains separate from initial gate pass criteria.

## F. Monitoring And Follow-Up Requirements
### EC-REQ-050
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Concierge V2 shall provide room capability discovery behavior for user queries about room abilities.
- Evidence Trace: [docs/governance/experience-continuity/v1-capability-reconstruction.md](docs/governance/experience-continuity/v1-capability-reconstruction.md), [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md)
- Verification Intent: Acceptance tests validate room capability query outcomes.

### EC-REQ-051
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Concierge V2 shall answer in-scope room monitoring follow-up questions for temperature, humidity, light, air quality, and noise when data is available.
- Evidence Trace: [docs/governance/experience-continuity/v1-capability-reconstruction.md](docs/governance/experience-continuity/v1-capability-reconstruction.md), [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md)
- Verification Intent: Scenario tests validate follow-up responses by signal type and data availability.

### EC-REQ-052
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Monitoring follow-up behavior shall provide graceful capability-not-available refusal when requested capability cannot be served.
- Evidence Trace: [docs/governance/experience-continuity/v1-capability-reconstruction.md](docs/governance/experience-continuity/v1-capability-reconstruction.md), [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md)
- Verification Intent: Negative-path tests validate refusal outcome and calm messaging posture.

## G. Guardrails And Calm Behavior Requirements
### EC-REQ-060
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Concierge V2 shall enforce guest, unknown, and low-confidence safe defaults for continuity behavior.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md), [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md)
- Verification Intent: Tests verify safe-default outcomes for each confidence and guest posture.

### EC-REQ-061
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Identity-personalized continuity behavior shall fail closed when identity confidence is unknown, low, unavailable, or not permitted.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md), [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md)
- Verification Intent: Validation demonstrates room or household default fallback under fail-closed conditions.

### EC-REQ-062
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Silence-is-success behavior shall be verified as a continuity policy outcome for relevant interaction classes.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md), [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md)
- Verification Intent: Policy validation defines and checks where no proactive chatter is expected.

### EC-REQ-063
- Gate Tier: INSTALL_GATE_SUPPORTING
- Requirement Statement: Guardrails shall include deterministic degraded-path behavior for missing devices, disabled integrations, unavailable Voice Identity, unavailable speakers, and no-room context.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md)
- Verification Intent: Degraded-path matrix validates continuity fallback decisions and explainability.

## H. Person-Aware Preference Requirements
### EC-REQ-070
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Concierge V2 shall support person-aware preference readiness where identity confidence is available and policy allows.
- Evidence Trace: [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md), [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md)
- Verification Intent: Validation demonstrates person-aware preference resolution readiness separate from fail-closed paths.

### EC-REQ-071
- Gate Tier: INSTALL_GATE_SUPPORTING
- Requirement Statement: Preference resolution shall apply explicit hierarchy: command intent, guardrail, known person, person plus room, room default, household default, system safe default.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md)
- Verification Intent: Decision trace validation confirms precedence order across scenarios.

### EC-REQ-072
- Gate Tier: INSTALL_GATE_SUPPORTING
- Requirement Statement: Person-aware preference behavior shall not override explicit safety and policy constraints.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md)
- Verification Intent: Policy tests confirm guardrails take precedence.

## I. Learning And Helper-State Disposition Requirements
### EC-REQ-080
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Learning behavior shall be governed, non-blocking, explainable, and reversible.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md)
- Verification Intent: Validation confirms interaction latency and behavior outcomes do not depend on synchronous learning completion.

### EC-REQ-081
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Personalized learning commits shall be disallowed for guest, unknown, and low-confidence identity contexts unless explicit policy authorizes otherwise.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md), [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md)
- Verification Intent: Tests verify suppression of personalized learning under restricted contexts.

### EC-REQ-082
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Each V1 helper-backed state family shall be assigned one governed disposition: migrate, seed, re-learn, replace with room default, replace with person plus room default, or retire.
- Evidence Trace: [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md), [docs/governance/experience-continuity/v1-capability-reconstruction.md](docs/governance/experience-continuity/v1-capability-reconstruction.md)
- Verification Intent: Migration planning artifact enumerates every helper state family and assigned disposition.

### EC-REQ-083
- Gate Tier: INSTALL_GATE_SUPPORTING
- Requirement Statement: Initial implementation requirements shall not mandate preservation of V1 helper schema shape.
- Evidence Trace: [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md)
- Verification Intent: Requirements review confirms schema-independence posture.

## J. Documentation And Validation Requirements
### EC-REQ-090
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Every install-gate continuity behavior shall have explicit architecture-aligned documentation and test coverage.
- Evidence Trace: [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md), [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md)
- Verification Intent: Gate checklist maps each behavior to at least one documentation artifact and one validation artifact.

### EC-REQ-091
- Gate Tier: INSTALL_GATE_REQUIRED
- Requirement Statement: Install gate reporting shall include explicit pass or fail outcomes for all in-scope gate behaviors and explicit notation of out-of-scope items.
- Evidence Trace: [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md)
- Verification Intent: Final readiness artifact contains a complete gate matrix.

### EC-REQ-092
- Gate Tier: INSTALL_GATE_SUPPORTING
- Requirement Statement: Diagnostics and explainability outputs shall provide sufficient continuity decision traceability for supportability without violating ownership boundaries.
- Evidence Trace: [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](docs/governance/experience-continuity/adr-experience-continuity-architecture.md), [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md)
- Verification Intent: Diagnostics validation confirms decision trace visibility and ownership safety.

## Explicit Out-Of-Scope Requirements For Initial Install Gate
The following shall not be used as initial install-gate blockers:
- Bedtime replacement behavior.
- Good Morning replacement behavior.
- Goodnight replacement behavior.
- Primary Bedroom Alarm replacement behavior.
- true cross-room follow-me media behavior.
- one-to-one V1 helper schema preservation.

Source: [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](docs/governance/experience-continuity/experience-continuity-scope-decisions.md)

## Backlog Readiness Note
This requirements backlog remains architecture-governed and intentionally does not define:
- implementation code
- issue decomposition
- release assignment
- repository task tracking IDs

Those activities are downstream of this artifact.
