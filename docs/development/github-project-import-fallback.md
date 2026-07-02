# GitHub Project Import Fallback Guide

Use this if GitHub rejects the full CSV import.

## Why Import Fails

Common causes:

- You are in a classic project instead of Project (v2).
- CSV contains columns GitHub cannot auto-map in your project.
- Custom fields are not created before import.
- CSV parser rejects complex quoted columns.

## Fastest Fix: Minimal CSV First

1. Open your Project (v2) in Table view.
2. Use Import CSV.
3. Import:
- github-project-seed-minimal.csv

This file contains only:

- Title
- Body

After import succeeds, set Status/Priority/Epic/Scope using multi-select edits in table view.

## Then Add Metadata in Bulk

1. Filter titles for one wave/epic keyword (for example: composite).
2. Multi-select rows.
3. Set fields in one action:
- Status = Backlog
- Epic = Composite Foundation
- Scope = Composite
- Priority = P0 or P1

Repeat by epic.

## If CSV Import UI Is Missing

You are likely not in Project (v2) table import flow.

Check:

- Project type is Project (v2)
- View is Table
- Use Add items or view menu import option

## No-Import Workaround: Copy/Paste Rows

1. Open github-project-seed-minimal.csv.
2. Copy title/body rows in chunks.
3. Paste directly into table cells in the first two columns.

GitHub will create draft items from pasted rows.

## Optional CLI Workaround (if needed)

If you want, we can use GitHub CLI to create issues from CSV and add those issues to the project.

This is slower but reliable when project CSV import is blocked by account policy.
