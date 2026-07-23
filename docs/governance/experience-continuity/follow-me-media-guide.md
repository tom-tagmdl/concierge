# Follow-Me Media Guide

Issue: #419
Classification: POST_INSTALL_ENHANCEMENT
Requirement Coverage: EC-REQ-044

## 1. Purpose
Define true cross-room Follow-Me Media behavior as a post-install enhancement that preserves install-gate certified room-aware and merged-room behaviors.

## 2. Governance Sources
- docs/governance/experience-continuity/experience-continuity-scope-decisions.md
- docs/governance/experience-continuity/experience-continuity-requirements-backlog.md
- docs/governance/experience-continuity/v1-to-v2-capability-parity-matrix.md
- docs/governance/experience-continuity/experience-continuity-epic-and-issue-roadmap.md
- docs/governance/experience-continuity/install-gate-evidence-binder.md
- docs/governance/experience-continuity/final-readiness-checklist.md
- docs/governance/experience-continuity/readiness-review-runbook.md
- docs/governance/experience-continuity/example-closure-decision-record.md
- docs/governance/experience-continuity/room-runtime-authority-contract.md
- docs/governance/experience-continuity/calm-behavior-policy-guide.md

## 3. Follow-Me Architecture
Follow-Me flow:
1. Resolve identity continuity authority from runtime context.
2. Resolve room transition source, source room, and destination room.
3. Resolve source room media context from room-scoped continuity state.
4. Evaluate eligibility and refusal conditions in deterministic order.
5. Apply room-audio authority in destination room.
6. Execute provider handoff to destination room speakers when allowed.
7. Persist destination room media context for future continuation.
8. Emit explainability fields for auditability.

## 4. Identity Requirements
Follow-Me requires known identity with acceptable confidence.

Fail-closed conditions:
- unresolved identity
- low or ambiguous confidence
- conflicting identity sources

On fail-closed conditions, Follow-Me emits governed refusal and does not hand off media.

## 5. Room Transition Rules
Transition requirements:
- source room must be known
- destination room must be known
- source and destination must differ
- transition ambiguity blocks handoff

Room authority remains configuration-authored.

## 6. Cooldown Rules
Manual-stop cooldown remains authoritative.

When cooldown is active, Follow-Me handoff is denied with explicit refusal reason.

## 7. Manual Stop Rules
Manual stop remains authoritative.

When manual stop is marked in source context, Follow-Me does not restart media automatically.

## 8. Merged-Room Interactions
Follow-Me does not replace merged-room execution semantics.

Merged-room interactions remain governed by install-gate certified behavior.

Explicit boundary:
- room-aware playback != merged-room playback != follow-me playback

## 9. Non-Regression Requirements
Follow-Me implementation must preserve:
- merged-room grouped playback behavior
- merged-room TTS behavior
- merged-room duck behavior
- merged-room restore behavior
- refusal and calm outcome taxonomy behavior

## 10. Validation Scenarios
Core scenarios:
- room A to room B handoff with known identity
- room B to room C handoff with known identity
- destination unavailable
- unresolved identity
- low confidence identity
- competing identities
- manual stop blocked
- cooldown blocked
- merged-room coexistence preserved
- person-scoped preference continuity preserved

## 11. Limitations
- Follow-Me is POST_INSTALL_ENHANCEMENT and was intentionally excluded from install-gate certification.
- No predictive playback behavior is implemented.
- No BLE roadmap behavior is implemented.
- No multi-user arbitration redesign is implemented beyond deterministic guardrail refusals.
