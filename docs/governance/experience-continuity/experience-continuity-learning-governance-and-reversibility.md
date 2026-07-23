# Experience Continuity Learning Governance and Reversibility

## 1. Purpose
This artifact defines governed learning policy and non-blocking learning write behavior for EC-B-03.

It establishes when learning is allowed, when learning is denied, how scope ownership is enforced, how asynchronous write disposition is applied, and how reversibility metadata is preserved.

## 2. Governance Sources
- [ADR: Experience Continuity Architecture](adr-experience-continuity-architecture.md)
- [Experience Continuity Scope Decisions](experience-continuity-scope-decisions.md)
- [Experience Continuity Requirements Backlog](experience-continuity-requirements-backlog.md)
- [Experience Continuity Epic and Issue Roadmap](experience-continuity-epic-and-issue-roadmap.md)
- [Experience Continuity Helper-Family Disposition Matrix](experience-continuity-helper-family-disposition-matrix.md)
- [Experience Continuity Preference Resolution Contract](experience-continuity-preference-resolution-contract.md)
- [Experience Continuity Identity Safety Context Matrix](experience-continuity-identity-safety-context-matrix.md)

## 3. Learning Eligibility Rules
Learning is allowed only when all of the following are true:
1. learning policy is enabled
2. ownership scope is supported
3. identity state is not blocked by fail-closed rules
4. confidence is not low for identity-sensitive learning
5. entity eligibility allows learning
6. preference eligibility allows learning
7. safety restrictions are clear
8. person-scope learning has explicit personalization policy permission

Eligibility output must include:
- learning_allowed
- ownership_scope
- write_path
- policy_decision
- reversibility_metadata

## 4. Learning Denial Rules
Learning is denied with deterministic reason codes for these conditions:
- guest identity
- unknown identity
- unavailable identity
- low-confidence identity
- policy-disabled learning
- unsupported ownership target
- ineligible entity target
- ineligible preference target
- unsafe learning context
- person-scope policy disallowed

Denied learning behavior:
- interaction continues
- write_path is none
- denial_reason is emitted
- explainability is preserved

## 5. Ownership Boundaries
Governed ownership scopes are:
- person
- room
- household

Boundary protections:
- person-scoped preference learning remains person-scoped
- room continuity learning remains room-scoped
- household default learning remains household-scoped
- room context is not promoted into person preference by default
- person preference is not written into room memory by default

## 6. Non-Blocking Write Strategy
Learning writes use an asynchronous non-blocking disposition.

Write path behavior:
- eligibility returns write_path=async for allowed learning
- write is enqueued without blocking the interaction response
- write completion is recorded via activity timeline event
- write failures are handled asynchronously and do not interrupt interaction flow

This design follows existing Concierge backend activity-lifecycle patterns and avoids introducing a complex queue framework.

## 7. Reversibility Metadata
Each allowed learning write produces rollback-supporting metadata:
- learning_source
- owner_scope
- timestamp
- reason
- policy_used
- rollback_supporting_metadata=true

This issue provides reversibility metadata only.

Rollback execution behavior is out of scope.

## 8. Explainability Requirements
Learning decision explainability must include:
- learning_allowed
- ownership_scope
- policy_result
- denial_reason (when denied)
- storage_target
- write_disposition

Explainability output must remain compatible with existing continuity diagnostics scaffolding and activity reference patterns.

## 9. Validation Scenarios
Required scenario coverage:
1. known identity learning allowed
2. guest learning denied
3. unknown learning denied
4. unavailable learning denied
5. low-confidence learning denied
6. policy-disabled learning denied
7. unsupported ownership scope denied
8. person preference learning scope
9. room continuity learning scope
10. household-default learning scope
11. successful async write enqueue
12. failed async write callback handling
13. reversibility metadata creation

## 10. Non-Goals
This issue does not implement:
- machine learning systems
- recommendation engines
- adaptive optimization
- follow-me music
- media orchestration
- lighting orchestration
- restoration behavior
- confidence-sensitive optimization
- cross-domain learning inference
- install-gate runtime execution logic
- production Home Assistant changes
