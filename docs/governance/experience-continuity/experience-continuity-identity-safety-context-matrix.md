# Experience Continuity Identity Safety Context Matrix

## 1. Purpose
This artifact defines the governed identity-safety context for EC-B-02 fail-closed personalization behavior.

It establishes when personalization is allowed, when personalization is blocked, and how fallback remains deterministic and safe.

## 2. Governance Sources
- [ADR: Experience Continuity Architecture](adr-experience-continuity-architecture.md)
- [Experience Continuity Scope Decisions](experience-continuity-scope-decisions.md)
- [Experience Continuity Requirements Backlog](experience-continuity-requirements-backlog.md)
- [Experience Continuity Epic and Issue Roadmap](experience-continuity-epic-and-issue-roadmap.md)
- [V1-to-V2 Capability Parity Matrix](v1-to-v2-capability-parity-matrix.md)
- [V1 Capability Reconstruction](v1-capability-reconstruction.md)
- [Experience Continuity Preference Resolution Contract](experience-continuity-preference-resolution-contract.md)

## 3. Identity States
Identity-safety handling uses these explicit states:
- known
- guest
- unknown
- unavailable
- low_confidence

## 4. Personalization Eligibility Rules
Personalized preference application is allowed only when all are true:
1. identity state is known
2. identity context is available
3. confidence is above fail-closed threshold
4. policy explicitly allows personalization

If any condition is false, personalization must be blocked and fallback must continue.

## 5. Fail-Closed Policy
Fail-closed contexts are:
- guest
- unknown
- unavailable
- low_confidence
- policy-disallowed known identity

Fail-closed behavior requirements:
- no silent personalization
- deterministic policy reason code
- fallback tier selected from approved hierarchy
- explainability metadata preserved

## 6. Fallback Policy
When personalization is blocked, fallback proceeds in deterministic order:
1. room default
2. household default
3. system safe default

A safe default must always be provided.

Undefined or unsafe personalization outcomes are prohibited.

## 7. Confidence Requirements
Confidence is consumed from Voice Identity outputs.

Confidence behavior:
- high confidence may permit personalization for known identity when policy allows
- low confidence blocks personalization
- unavailable confidence data must not force unsafe personalization

Concierge consumes confidence outcomes and does not own confidence scoring.

## 8. Identity Safety Matrix
| Identity State | Personalization | Fallback Behavior |
|---|---|---|
| known | allowed only when confidence is above threshold and policy allows | if blocked by policy/confidence, use room -> household -> system safe |
| guest | blocked | use room -> household -> system safe |
| unknown | blocked | use room -> household -> system safe |
| unavailable | blocked | use room -> household -> system safe |
| low_confidence | blocked | use room -> household -> system safe |

## 9. Validation Scenarios
Required validation coverage:
1. known identity personalization allowed
2. guest identity blocked with fail-closed fallback
3. unknown identity blocked with fail-closed fallback
4. unavailable identity blocked with fail-closed fallback
5. low-confidence identity blocked with fail-closed fallback
6. policy-disallowed known identity blocked with fail-closed fallback
7. room-default-only environment
8. household-default-only environment
9. system-safe-only environment
10. missing personalization data
11. missing room default
12. missing household default
13. deterministic repeated-input behavior
14. explainability metadata includes policy reason, fallback reason, and selected source

## 10. Non-Goals
This issue does not implement:
- media playback
- media orchestration
- lighting orchestration
- restoration behavior
- Follow-Me Music
- Voice Identity scoring changes
- production Home Assistant changes
