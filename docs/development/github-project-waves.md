# Concierge Project Waves

Use this with github-project-seed-waves.csv to execute Concierge in milestone order.

## How to Use

1. Create a custom field in GitHub Project named Milestone.
2. Add values: Wave 1, Wave 2, Wave 3.
3. Import github-project-seed-waves.csv and map Milestone.
4. Create a board view grouped by Milestone and then by Status.

## Wave Goals

### Wave 1: Foundation and Contract Safety

Goal:

- stabilize composite model, services, and validation
- enforce same-floor constraints
- support rename/unmerge semantics at backend level

Exit criteria:

- composite lifecycle services work end-to-end
- stale device references are cleaned up
- tests pass for merge constraints and unmerge/dismantle

### Wave 2: UI and Composite Experience

Goal:

- ship merge and edit flows in main Concierge UI
- replace member tiles with composite tile and show members
- provide composite selectors built from member-room union

Exit criteria:

- merge flow validates same-floor in UI
- partial and full unmerge behave exactly as contracts define
- selectors update correctly when membership changes

### Wave 3: Voice, Scope, and Release Hardening

Goal:

- enforce composite voice determinism from any member room
- add floor-scoped climate and Music Assistant defaults
- complete diagnostics and release validation

Exit criteria:

- invocation parity proven in tests
- floor defaults and room overrides resolve deterministically
- release checklist passes (tests, hassfest, HACS)

## Recommended Session Cadence

1. Start each session in the Project Now view filtered to current Milestone.
2. Keep only one item In Progress per developer.
3. Prefer vertical completion: backend + UI + tests for one behavior.
4. Move item to Done only with green tests and documented behavior.
