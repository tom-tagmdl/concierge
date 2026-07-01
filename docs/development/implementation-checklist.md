# Concierge Implementation Checklist

This checklist is the canonical build plan for Concierge implementation work.

Use it at the start of every development session.

## Session Start Ritual

1. Review open items in GitHub Project view: Now.
2. Pick one vertical slice that can reach done.
3. Confirm contract alignment with Homes That Behave Well.
4. Implement backend + UI + tests for the same slice.
5. Move item to Done only after acceptance checks pass.

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
