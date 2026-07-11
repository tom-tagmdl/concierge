# Concierge Implementation Checklist

This checklist is the canonical build plan for Concierge implementation work.

Use it at the start of every development session.

## Session Start Ritual

1. Review open items in GitHub Project view: Now.
2. Pick one vertical slice that can reach done.
3. Confirm contract alignment with Homes That Behave Well.
4. Confirm Room Vocabulary ownership remains external.
5. Confirm Coordinator acts only as consumer.
6. Confirm implementation aligns with `docs/governance/room-vocabulary-consumption-architecture.md`.
7. Confirm vocabulary resolution remains deterministic.
8. Confirm ambiguity handling is documented.
9. Confirm ownership remains external.
10. Confirm implementation aligns with `docs/governance/runtime-vocabulary-resolution-architecture.md`.
11. Confirm room context remains governed input.
12. Confirm room-aware behavior is deterministic.
13. Confirm ambiguity handling remains explainable.
14. Confirm ownership remains external.
15. Confirm implementation aligns with `docs/governance/room-context-aware-vocabulary-consumption-architecture.md`.
16. Confirm merged-room vocabulary is not treated as a separate vocabulary system.
17. Confirm merged-room scope expansion behavior is documented.
18. Confirm merged-room ambiguity/conflict handling remains deterministic and explainable.
19. Confirm ownership remains external for merged-room definitions and membership.
20. Confirm implementation aligns with `docs/governance/merged-room-vocabulary-consumption-architecture.md`.
21. Confirm composite-room vocabulary is not treated as a separate vocabulary system.
22. Confirm hierarchy traversal behavior is deterministic and documented.
23. Confirm scope expansion behavior for composite and floor scopes is documented.
24. Confirm ambiguity handling for composite/hierarchy conflicts remains explainable.
25. Confirm ownership remains external for composite, zone, floor, and hierarchy definitions.
26. Confirm implementation aligns with `docs/governance/composite-room-vocabulary-consumption-architecture.md`.
27. Confirm validation categories are documented for affected vocabulary/scope paths.
28. Confirm duplicate, conflict, and orphan detection coverage is documented.
29. Confirm validation outcomes are classified as PASS/WARNING/ERROR/BLOCKED where applicable.
30. Confirm diagnostics and explainability participation for validation outcomes is documented.
31. Confirm ownership boundaries remain external while validating consumption.
32. Confirm implementation aligns with `docs/governance/vocabulary-validation-framework.md`.
33. Confirm explanation categories are documented for affected vocabulary/scope decisions.
34. Confirm machine-readable explanation structures are documented for affected decision paths.
35. Confirm human-readable explanation structures are documented for operator-facing scenarios.
36. Confirm validation outcomes are reflected in explainability when applicable.
37. Confirm diagnostics surfaces expose explanation references where required.
38. Confirm ownership boundaries remain external while explaining consumption decisions.
39. Confirm implementation aligns with `docs/governance/vocabulary-explainability-framework.md`.
40. Confirm vocabulary discovery remains room-aware and capability-aware.
41. Confirm guest-safe discovery filtering is documented.
42. Confirm discovery outputs do not expose internal identifiers or platform internals.
43. Confirm discovery filtering and visibility decisions are explainable.
44. Confirm diagnostics surfaces expose discovery filtering decisions.
45. Confirm ownership boundaries remain external while providing discovery outputs.
46. Confirm implementation aligns with `docs/governance/vocabulary-discovery-framework.md`.
47. Confirm diagnostics categories are documented for affected vocabulary/scope decisions.
48. Confirm lookup, alias, room-resolution, merged-room, and composite traces are documented.
49. Confirm conflict and validation trace paths are documented with severity outcomes.
50. Confirm diagnostics traces link to explainability and validation references.
51. Confirm troubleshooting workflow is documented for reported issues.
52. Confirm ownership boundaries remain external while exposing diagnostics outputs.
53. Confirm implementation aligns with `docs/governance/vocabulary-diagnostics-framework.md`.
54. Before beginning E5: review E4 readiness determination.
55. Before beginning E5: verify E5 authorization is documented.
56. Before beginning E5: verify no vocabulary ownership drift unresolved.
57. Confirm preserved Concierge V1 household-facing outcomes remain intact per `docs/governance/concierge-v1-outcome-preservation-baseline.md`.
58. If merged-room behavior may be affected, verify parity against `docs/governance/merged-room-outcome-preservation-contract.md`.
59. If composite-room, floor-scope, zone-scope, whole-house-scope, or hierarchy traversal behavior may be affected, verify parity against `docs/governance/composite-room-scope-outcome-preservation-contract.md`.
60. If execution hierarchy, room-level execution, merged-room execution, composite-room execution, floor-level execution, or whole-house execution behavior may be affected, verify parity against `docs/governance/execution-hierarchy-outcome-preservation-contract.md`.
61. If global context, home status, occupancy references, shared context, environmental context, platform state, signals, or household-summary behavior may be affected, verify parity against `docs/governance/global-context-outcome-preservation-contract.md`.
62. Confirm affected V1 household-facing outcomes are mapped in `docs/governance/v1-to-v2-capability-parity-matrix.md` before implementation.
63. Complete applicable checks from `docs/governance/v1-outcome-regression-checklist.md` before closing any implementation issue that affects preserved V1 household-facing outcomes.
64. Confirm E3a preservation readiness review has no blocking findings.
65. Implement backend + UI + tests for the same slice.
66. Move item to Done only after acceptance checks pass.

## Definition of Done

An item is done only when all are true:

- Behavior matches Homes That Behave Well contracts and patterns.
- Service schema and runtime validation are implemented.
- UI uses Home Assistant-native patterns.
- Tests cover success and failure paths.
- Diagnostics expose relevant state.
- User-visible docs are updated when behavior changes.

## Phase 1: Composite and Scope Foundation

- [ ] Add composite storage model fields for name, area_ids, primary_area, and metadata.
- [ ] Add floor configuration model for thermostat/HVAC and media defaults.
- [ ] Add deterministic effective scope resolver: room -> floor -> concierge.
- [ ] Add composite validation: same-floor membership only.
- [ ] Add stale membership/device cleanup on composite membership changes.

## Phase 2: Service Surface

- [ ] Implement concierge.update_floor_config.
- [ ] Implement concierge.get_floor_config.
- [ ] Expand concierge.update_composite_config to support rename and membership edits.
- [ ] Implement concierge.sync_composites for projection rebuild and validation.
- [ ] Add global policy endpoint semantics for quiet-hours and urgent bypass.

## Phase 3: Main Concierge UI

- [ ] Add three setup sections in main UI: concierge-wide, floor-wide, room cards.
- [ ] Add merge mode button on main screen.
- [ ] Add composite naming input in merge flow.
- [ ] Add room-card checkboxes for merge selection.
- [ ] Enforce same-floor-only merge selection with inline errors.
- [ ] Replace member room cards with composite tile after merge.
- [ ] Show member room names in composite tile summary.

## Phase 4: Composite Edit and Unmerge UX

- [ ] Add Edit action on composite tile.
- [ ] Add editable composite name in Edit panel.
- [ ] Add checklist of member rooms in Edit panel.
- [ ] Support partial unmerge: removed room tile returns; composite remains for remaining rooms.
- [ ] Support full dismantle: composite removed; all room tiles restored.
- [ ] Ensure removed-room devices are removed from composite selectors and snapshots.

## Phase 5: Composite Detail and Device Union

- [ ] Build composite selectors from union of devices in member rooms.
- [ ] Deduplicate entities deterministically.
- [ ] Mark unavailable entities clearly.
- [ ] Add category groups: lights, lamps(label), speakers, voice assistants, shades, TV, sensors.
- [ ] Gate AI/TTS/Asset Intelligence room options from global capability status.

## Phase 6: Voice and Execution Determinism

- [ ] Promote invocation area to composite context when member room voice endpoint is used.
- [ ] Ensure merged-room commands resolve identically from any member room.
- [ ] Keep execution hierarchy: scene -> group -> entity.
- [ ] Ensure one-call execution where possible for composite actions.

## Phase 7: Music Assistant and Climate Scope

- [ ] Keep Music Assistant enabled at concierge-wide capability scope.
- [ ] Add floor-wide Music Assistant defaults for routing/groups.
- [ ] Add room-level endpoint overrides for playback and TTS.
- [ ] Keep thermostat/HVAC defaults at floor scope.
- [ ] Allow room-level climate overrides for explicit exceptions.

## Phase 8: Test Coverage

- [ ] Add tests for same-floor merge validation and cross-floor rejection.
- [ ] Add tests for composite rename and membership edits.
- [ ] Add tests for partial unmerge and full dismantle projection behavior.
- [ ] Add tests for device union and removed-device cleanup.
- [ ] Add tests for invocation-context promotion to composite.
- [ ] Add tests for scope precedence: room > floor > concierge.

## Phase 9: Release Readiness

- [ ] Update service docs and strings for new capabilities.
- [ ] Update diagnostics for composite/floor/effective scope snapshots.
- [ ] Run tests, lint, and local validation.
- [ ] Bump manifest version before release tagging.
- [ ] Verify HACS and hassfest checks pass.

## Recommended Work Slice Order

1. Composite model + update_composite_config rename/membership edits.
2. Main UI merge flow with same-floor validation.
3. Composite edit/unmerge flow and projection updates.
4. Composite device union and selector refresh.
5. Floor config services and climate/music defaults.
6. Voice-context promotion and execution parity tests.
