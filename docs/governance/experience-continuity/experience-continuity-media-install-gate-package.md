# Experience Continuity Media Install Gate Closure Package

## 1. Purpose
This package closes the EC-E media install-gate evidence set for #411.

It consolidates the already-passing EC-E issue evidence for room-level music playback, room-level continue/resume media, room-level last-media context, and manual-stop suppression/cooldown, then anchors those behaviors to the room runtime authority model and the supporting EC-D audio continuity gate.

This artifact is closure evidence only. It does not add runtime behavior, and it does not implement Follow-Me Media.

## 2. Governance Sources
- [docs/governance/experience-continuity/adr-experience-continuity-architecture.md](adr-experience-continuity-architecture.md)
- [docs/governance/experience-continuity/experience-continuity-scope-decisions.md](experience-continuity-scope-decisions.md)
- [docs/governance/experience-continuity/experience-continuity-outcome-preservation-review.md](experience-continuity-outcome-preservation-review.md)
- [docs/governance/experience-continuity/experience-continuity-epic-and-issue-roadmap.md](experience-continuity-epic-and-issue-roadmap.md)
- [docs/governance/experience-continuity/experience-continuity-requirements-backlog.md](experience-continuity-requirements-backlog.md)
- [docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md](v1-to-v2-capability-parity-matrix.md)
- [docs/governance/experience-continuity/v1-capability-reconstruction.md](v1-capability-reconstruction.md)
- [docs/governance/experience-continuity/experience-continuity-media-provider-precedence-contract.md](experience-continuity-media-provider-precedence-contract.md)
- [docs/governance/experience-continuity/experience-continuity-room-media-continuation-contract.md](experience-continuity-room-media-continuation-contract.md)
- [docs/governance/experience-continuity/experience-continuity-room-media-memory-contract.md](experience-continuity-room-media-memory-contract.md)
- [docs/governance/experience-continuity/experience-continuity-manual-stop-suppression-contract.md](experience-continuity-manual-stop-suppression-contract.md)
- [docs/governance/experience-continuity/experience-continuity-audio-gate-closure-package.md](experience-continuity-audio-gate-closure-package.md)
- [tmp/ec_issue_updates/412.md](../../../tmp/ec_issue_updates/412.md)

## 3. EC-E Requirement Coverage
Install-gate requirements represented in this package:
- EC-REQ-040: room-level music playback resolution with Music Assistant preferred when configured.
- EC-REQ-041: room-level continue/resume media, including room-scoped continuation hierarchy, merged-room source-room selection, and no Follow-Me behavior.
- EC-REQ-042: room-level last-media context capture and persistence.
- EC-REQ-043: manual-stop suppression and cooldown guardrail.
- EC-REQ-050: room runtime authority model from Room Configuration.
- EC-REQ-090: every install-gate continuity behavior maps to both documentation and validation evidence.

Supporting EC-D audio continuity requirements included in the closure package:
- EC-REQ-030: bounded duck/restore lifecycle.
- EC-REQ-031: speech continuity remains separate from media continuation.
- EC-REQ-032: room-scoped music/duck/TTS audio memory with configured speaker authority.
- EC-REQ-033: deterministic degraded-path fallback or refusal.
- EC-REQ-063: explainable degraded-path guardrails.

## 4. Architecture Summary
The EC-E media stack preserved in this closure package is:
- Room Configuration remains authoritative for room ownership, room membership, and configured output targets.
- Music Assistant is the preferred provider when configured, but it never becomes the source of room authority.
- Room-scoped media memory is stored in Experience Continuity usual-state records only.
- Manual-stop suppression is a hard guardrail and is evaluated before governed continuation proceeds.
- Merged-room playback expands output scope without creating merged-room persistent media memory.
- EC-D audio continuity remains the supporting bounded lifecycle for duck/restore and grouped speaker output.

Primary implementation surfaces audited:
- [custom_components/concierge/services.py](../../../custom_components/concierge/services.py)
- [custom_components/concierge/models.py](../../../custom_components/concierge/models.py)
- [custom_components/concierge/storage.py](../../../custom_components/concierge/storage.py)
- [custom_components/concierge/coordinator.py](../../../custom_components/concierge/coordinator.py)

## 5. Consolidated Evidence Summary
Primary EC-E suites:
- #407 EC-E-01 room-level music playback resolution: 20/20 portable scenarios passed.
- #408 EC-E-02 room-level continue/resume media: 20/20 portable scenarios passed.
- #409 EC-E-03 room-level last-media context: 16/16 portable scenarios passed.
- #410 EC-E-04 manual-stop suppression and cooldown: 16/16 portable scenarios passed.

Supporting EC-D suites:
- #403 room audio memory: 15/15 portable scenarios passed.
- #404 speech / duck / restore: 6/6 portable scenarios passed.
- #405 audio fallback / no-speaker behavior: 16/16 portable scenarios passed.

The native pytest path remains environment-blocked on this Windows host, and that limitation is already captured in the source issue artifacts. The portable harness evidence is the practical validation path for this workspace.

## 6. Package Validation Artifacts
Executable validation and traceability artifacts produced for this closure package:
- [tmp/ec411_test_results.json](../../../tmp/ec411_test_results.json)
- [tmp/ec411_scenarios.json](../../../tmp/ec411_scenarios.json)
- [tmp/ec411_coverage_matrix.json](../../../tmp/ec411_coverage_matrix.json)
- [tmp/ec411_doc_cross_reference.json](../../../tmp/ec411_doc_cross_reference.json)
- [tmp/ec411_traceability_matrix.json](../../../tmp/ec411_traceability_matrix.json)

Execution orchestration:
- [tmp/ec411_closure.py](../../../tmp/ec411_closure.py)

Latest closure run log:
- [tmp/ec411_closure_stdout_latest.txt](../../../tmp/ec411_closure_stdout_latest.txt)

## 7. Install-Gate Readiness Assessment
Readiness classification: READY_FOR_INSTALL_GATE_CLOSURE

Assessment:
- The EC-E issue chain is complete and explicit across #407 through #410.
- The room runtime authority model in #412 is grounded and preserved.
- The supporting EC-D audio gate closure is already passing and remains bound to the same architecture.
- The package adds no new runtime behavior and does not introduce Follow-Me Media.

Wiki update decision:
- No wiki update required.
- The governance closure package is the canonical operator/architecture artifact for this install-gate package.

## 8. Non-Goals
This closure package does not:
- implement new media functionality,
- implement Follow-Me Media,
- create new persistent merged-room media memory,
- change production Home Assistant,
- widen room authority beyond Room Configuration,
- proceed to downstream EC-H issues.