# Concierge GitHub Project Setup

This guide creates a reusable GitHub Project for Concierge implementation tracking.

## Recommended Project Name

Concierge Implementation

## Recommended Views

1. Now
- Filter: Status = In Progress OR Status = Ready
- Sort: Priority desc, Size asc

2. Next
- Filter: Status = Ready
- Sort: Priority desc

3. Backlog
- Filter: Status = Backlog
- Group by: Epic

4. Done
- Filter: Status = Done
- Sort: Updated desc

## Recommended Custom Fields

1. Status (single select)
- Backlog
- Ready
- In Progress
- Blocked
- In Review
- Done

2. Priority (single select)
- P0
- P1
- P2
- P3

3. Epic (single select)
- Composite Foundation
- Service Surface
- Main UI
- Composite Edit UX
- Device Union
- Voice Determinism
- Music and Climate Scope
- Test Coverage
- Release Readiness

4. Scope (single select)
- Concierge
- Floor
- Room
- Composite

5. Size (single select)
- XS
- S
- M
- L

6. Contract Reference (text)
- Store the source contract/pattern doc path

## Labels to Create

- concierge
- ui
- backend
- contracts
- tests
- composite
- scope
- floor
- voice
- music-assistant
- climate

## How to Seed the Project

1. Import the seed CSV file in this folder:
- github-project-seed.csv

Optional milestone-based import:

- github-project-seed-waves.csv
- see github-project-waves.md for wave execution guidance

If full CSV import fails:

- import github-project-seed-minimal.csv first
- then follow github-project-import-fallback.md

2. Map fields during import:
- Title -> Title
- Body -> Body
- Status -> Status
- Priority -> Priority
- Epic -> Epic
- Scope -> Scope
- Size -> Size
- Labels -> Labels

3. Add contract links to each item where missing.

## Session Workflow

1. Start in Now view.
2. Move one item to In Progress.
3. Complete code + tests + docs.
4. Move to In Review.
5. Move to Done after validation.

## Guardrails

- Do not close items without tests unless explicitly deferred.
- Keep one active item per person to preserve focus.
- Keep implementation aligned to Homes That Behave Well contracts first, then UI polish.
