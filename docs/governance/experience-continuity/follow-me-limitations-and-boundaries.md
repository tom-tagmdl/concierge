# Follow-Me Limitations And Boundaries

Issue: #419
Classification: POST_INSTALL_ENHANCEMENT
Requirement Coverage: EC-REQ-044

## 1. Purpose
Define explicit implementation boundaries for Follow-Me Media so post-install enhancement delivery does not alter install-gate classification or authority boundaries.

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
Follow-Me evaluates policy and guardrails before any handoff and emits explainability for each decision.

Follow-Me does not bypass room capability authority.

## 4. Identity Requirements
Identity authority must be sufficient and non-conflicting.

Blocked states:
- unknown
- low confidence
- ambiguous or conflicting attributions

## 5. Room Transition Rules
Room transition must be explicit and explainable.

Blocked states:
- missing source room
- missing destination room
- no room change
- ambiguous transition

## 6. Cooldown Rules
Cooldown status remains enforced from source room continuity context.

Follow-Me cannot hand off during active cooldown windows.

## 7. Manual Stop Rules
Manual stop remains a hard guardrail for automatic handoff.

Follow-Me does not auto-restart media after manual stop markers.

## 8. Merged-Room Interactions
Follow-Me and merged-room are separate concepts.

Follow-Me cannot override merged-room scope decisions in this issue.

## 9. Non-Regression Requirements
No regression allowed for install-gate validated behaviors from EC403 through EC411 and EC412 through EC418.

## 10. Validation Scenarios
Validation matrices in tmp/ec419_* cover:
- transition eligibility
- identity gating
- cooldown/manual-stop guardrails
- merged-room coexistence
- preference continuity
- install-gate baseline preservation

## 11. Limitations
- Classification remains POST_INSTALL_ENHANCEMENT.
- This issue does not re-open install-gate readiness artifacts.
- This issue does not modify production Home Assistant.
