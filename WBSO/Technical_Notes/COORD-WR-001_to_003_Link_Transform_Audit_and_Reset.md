# COORD-WR-001 to COORD-WR-003 - Link Transform Audit and Reviewed Reset

Date:
2026-06-03

Project:
AI Workbench / BIM3DNA Revit Coordination Automation

R&D theme:
Deterministic Revit coordination automation for safe `RevitLinkInstance` transform auditing and reviewed correction.

## Technical Problem

The project needed a deterministic Revit automation workflow to detect Revit link coordinate drift, test whether a selected link could be safely reset to project origin, and then perform a reviewed persistent reset only when all safety and source-revalidation conditions were satisfied.

## Technical Uncertainty

- How to safely inspect `RevitLinkInstance` transforms without modifying model state.
- How to verify that a link can be translated back to origin without committing the change.
- How to gate a persistent `MoveElement` apply behind a previous rollback test.
- How to prevent stale or invalid rollback state from being reused.
- How to persist the latest passed rollback source across AI Workbench prompt routes.
- How to ensure the persistent apply affects only one selected `RevitLinkInstance` and never performs batch/all-link operations.

## Implemented Workflow

### COORD-WR-001 - Link Transform Audit / Coordinate Drift Report

- Header: `[LINK TRANSFORM AUDIT REPORT]`
- Read-only audit of `RevitLinkInstance` transforms.
- Reports origin, approximate millimetre offset, rotation, basis vectors, mirrored state, loaded/readable state, pinned/grouped state, and classification.
- Classifies links as `OK_ZERO_ORIGIN`, `OFFSET_FROM_ZERO`, `REVIEW_REQUIRED`, and related deterministic statuses.
- Opens no transaction.
- Performs no model changes.

### COORD-WR-002 - Link Origin Reset Rollback Test

- Header: `[LINK ORIGIN RESET ROLLBACK TEST]`
- Confirmation token: `ROLLBACK-LINK-RESET-OK`
- Requires exactly one selected `RevitLinkInstance`.
- Uses `TransactionGroup`, inner `Transaction`, and `ElementTransformUtils.MoveElement`.
- Temporarily moves the selected link origin to zero.
- Verifies the temporary zero origin.
- Rolls back the `TransactionGroup`.
- Verifies the final origin matches the original origin.
- Stores the latest passed rollback source only after a `Passed` result with valid source data.

### COORD-WR-003 - Single Selected Link Reviewed Origin Reset Apply

- Header: `[LINK ORIGIN RESET REVIEWED APPLY]`
- Confirmation token: `PERSISTENT-LINK-RESET-OK`
- Requires latest passed COORD-WR-002 rollback source.
- Requires selected link id/name to match the rollback-tested link.
- Requires current origin and transform basis to match the rollback-tested source within tolerance.
- Requires current origin not already zero.
- Uses a single `DB.Transaction` and `ElementTransformUtils.MoveElement`.
- Performs one selected-link persistent origin reset to zero.
- Verifies final origin near zero and basis preserved.
- Does not modify linked documents, reload/unload, pin/unpin, rotate, write parameters, or modify UI selection.

## R&D Issue and Resolution

Initial COORD-WR-003 implementation could not reliably access the COORD-WR-002 rollback source after later prompt routes. A later Not Ready rollback report could overwrite or hide the latest valid passed rollback source, which blocked the reviewed apply.

The resolution was shared session state backed by pyRevit script environment storage:

- `get_coord_shared_state()`
- `set_latest_passed_link_origin_reset_rollback_state()`
- `get_latest_passed_link_origin_reset_rollback_state()`

Shared state key:
`latest_passed_link_origin_reset_rollback_state`

Shared state source:
`pyrevit script envvar AI_WORKBENCH_COORD_SHARED_STATE`

State storage rules:

- Write `latest_passed_link_origin_reset_rollback_state` only when COORD-WR-002 result is `Passed`.
- Do not overwrite this key on Not ready, Already at zero, Failed, no selection, missing token, multiple selection, or unreadable source.
- Store only serializable values: strings, booleans, integers/floats, and `[x, y, z]` lists.
- Do not store raw Revit API objects.

## Runtime Validation Context

Test model:
`BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`

Active view:
`{3D - e.avdovicQREF7} [ThreeD]`

Selected test link:

- Element id: `2972572`
- Name: `3D-01B-AR-01.ifc : 48`
- Original offset before apply: `(0.000000, -6.233596, 0.000000) ft`
- Approximate offset before apply: `(0, -1900, 0) mm`

## Validation Evidence

### COORD-WR-002 Rollback Test

- Rollback Test ID: `COORD-WR-002-20260603_144729`
- Rollback test result: `Passed`
- TransactionGroup opened: true
- Transaction opened: true
- `MoveElement` called: true
- Temporary origin: `(0.000000, 0.000000, 0.000000)`
- Temporary verification passed: true
- TransactionGroup rolled back: true
- TransactionGroup assimilated: false
- Final origin matched original: true
- Persistent model changes: false
- Latest passed rollback source stored: true
- Latest passed rollback source read-back succeeded: true
- Shared state object/source: `pyrevit script envvar AI_WORKBENCH_COORD_SHARED_STATE`

### COORD-WR-003 Readiness

- Apply ID: `COORD-WR-003-20260603_145224`
- Latest passed COORD-WR-002 source exists: true
- Latest passed rollback result: `Passed`
- Selected link matches rollback-tested link: true
- Current origin matches rollback source: true
- Current basis matches rollback source: true
- Current origin already zero: false
- Delta matches rollback-tested delta: true
- Pre-apply result: `Passed`
- Transaction opened: false
- `MoveElement` called: false
- Persistent model changes: false

### COORD-WR-003 Persistent Apply

- Apply ID: `COORD-WR-003-20260603_145444`
- Confirmation token accepted: true
- Pre-apply result: `Passed`
- Transaction opened: true
- `MoveElement` called: true
- Transaction committed: true
- Transaction rolled back: false
- Persistent model changes: true
- Link transform modified persistently: true
- Final origin: `(0.000000, 0.000000, 0.000000)`
- Final origin approximate mm: `(0, 0, 0)`
- Final origin near zero: true
- Final basis matches pre-apply basis: true
- Final linked document readable: true
- Post-apply verification passed: true
- Reviewed apply result: `Applied`

### Post-Apply Audit

- Audit ID: `COORD-WR-001-20260603_145614`
- Total Revit link instances found: 8
- Loaded link instances: 8
- Links near zero origin: 8
- Links offset from zero: 0
- Links rotated/non-orthogonal: 0
- Links pinned: 0
- Future reset candidates: 0
- Links requiring manual review: 0
- Audit result: `OK`
- Recommended next action: no coordinate action required
- Link `2972572` final origin: `(0.000000, 0.000000, 0.000000)`
- Link `2972572` classification: `OK_ZERO_ORIGIN`

### QA Export Evidence

- Export folder: `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260603_150023`
- Source prompt: `audit link transforms`
- Source header: `[LINK TRANSFORM AUDIT REPORT]`
- Scope: `active document Revit link transform audit / read-only`
- Generated files: `report.md`, `report.txt`, `metadata.json`, `artifact_manifest.txt`
- Index files updated: `latest_export.json`, `qa_export_index.jsonl`, `qa_export_index.csv`

## Safety and Governance

- COORD-WR-001 is read-only and opens no transaction.
- COORD-WR-002 uses `TransactionGroup` rollback only and does not persist model changes.
- COORD-WR-003 performs a persistent move only after exactly one selected `RevitLinkInstance`, passed rollback source, matching selected link id/name, matching source origin and basis, accepted confirmation token, and non-zero current origin.
- No batch/all-link reset.
- No apply by stored element id alone.
- No UI selection modification.
- No linked document mutation.
- No reload/unload.
- No pin/unpin.
- No parameter writes.
- No `RotateElement`, `TransformElement`, or `Location.Move`.
- `MoveElement` remains guarded in rollback/apply paths only.

## Commit Reference

- Commit: `38ab72c8f0fd0da897b50963947104744807b5f2`
- Commit message: `Add reviewed link origin reset apply`
- Commit timestamp: `2026-06-03 15:01:47 +0200`
- Primary changed implementation files:
  - `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
  - `AI.extension/lib/prompt_catalog.json`

## Status

COORD-WR-001, COORD-WR-002, and COORD-WR-003 are runtime validated as a deterministic coordination workflow chain.
