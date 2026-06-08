# COORD-WR-006 - Link Reset Workflow History / Run Register

## Status

Runtime validated and export/index validated on 2026-06-08.

## Project Context

- Company: Intra.actions B.V.
- Project: WBSO - AI Systems & Intelligent Automation
- Repository: BIM3DNA / AI-Systems-Intelligent-Automation
- Branch: `main`
- Commit: `073eb567325b2155813a97be5533781c2e815d1f Add link reset workflow history register`
- Daily log: `DL-2026-06-08-08`
- Week: `2026-W11`
- Model: `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`
- View: `TEST [FloorPlan]`

## Purpose

COORD-WR-006 adds a local workflow history/run register for the reviewed Revit link reset workflow. It persists meaningful COORD-WR-005 checkpoints outside transient pyRevit session state and can recover a prior checkpoint from QA export history.

Report header:
`[LINK RESET WORKFLOW HISTORY]`

Export scope:
`Revit link reset workflow history / local read-only register`

## Storage

- Folder: `C:\Users\User\Desktop\Results\AI_Workbench\Workflow_History`
- JSONL: `link_reset_workflow_history.jsonl`
- CSV: `link_reset_workflow_history.csv`

Records contain flattened, JSON-safe values only. Raw `DB.XYZ`, `Transform`, `ElementId`, `RevitLinkInstance`, `Document`, and `View` objects are not stored.

## Source Priority

1. Latest meaningful shared COORD-WR-005 state.
2. Newest indexed QA export with header `[LINK RESET WORKFLOW STATUS]`.
3. No checkpoint.

Fallback scans the complete QA export JSONL/CSV index rather than relying on `latest_export.json`, which may point to a later history export. It prefers `report.txt` and falls back to `report.md`.

Meaningful statuses:

- `Ready / clean`
- `Review required`
- `Apply completed; verification missing`
- `Rollback passed; apply pending`
- `Audit only / reset not started`
- `Not ready` only when useful workflow state exists

## Technical Bottlenecks

1. Live pyRevit shared state can disappear after a session reset.
2. The original history implementation still depended on live COORD-WR-005 state.
3. `latest_export.json` cannot reliably identify the latest workflow-status export.
4. Exported report parsing must tolerate missing or unavailable fields.
5. Repeated recovery of the same export must not create duplicate rows.
6. Local persistence must not broaden the Revit model-write boundary.

## Initial Negative Evidence

Prompt:
`coord reset status`

Status:
`COORD-WR-005-20260608_091433`

Observed:

- audit state unavailable
- rollback state unavailable
- apply state unavailable
- verification state unavailable
- workflow status `Not ready`
- transaction opened false
- model modified false

Initial history prompt:
`show link reset workflow history`

History report:
`COORD-WR-006-20260608_091455`

Observed:

- append attempted false
- record count 0
- warning that latest COORD-WR-005 status was not meaningful

This negative result exposed the cross-session persistence gap and is retained as validation evidence.

## Fallback Recovery

Recovered source export:
`C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260605_163936`

Recovered checkpoint:

- status id: `COORD-WR-005-20260605_163912`
- workflow status: `Ready / clean`
- audit: `COORD-WR-001-20260605_163837 | OK`
- rollback: `COORD-WR-002-20260605_145813 | Passed`
- apply: `COORD-WR-003-20260605_150040 | Applied`
- verification: `COORD-WR-004-20260605_163104 | Verified`
- target link: `2972572 | 3D-01B-AR-01.ifc : 48`
- initial origin: approximately `(0, -2300, 0)` mm
- final origin: `(0, 0, 0)` mm

## Runtime Validation

### First Fallback Append

- history report: `COORD-WR-006-20260608_094522`
- primary shared state meaningful: false
- QA fallback attempted: true
- QA fallback source found: true
- QA fallback parsed: true
- checkpoint source: `qa_export_fallback`
- append attempted: true
- append succeeded: true
- duplicate skipped: false
- record count: 1

### Duplicate Prevention

- history report: `COORD-WR-006-20260608_094609`
- append attempted: true
- append succeeded: false
- duplicate skipped: true
- record count: 1

Duplicate prevention uses `status_id`, or source export folder when status id is unavailable.

## Export Validation

- Final export: `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260608_094652`
- Source prompt: `show link reset workflow history`
- Source header: `[LINK RESET WORKFLOW HISTORY]`
- Scope: `Revit link reset workflow history / local read-only register`
- Generated: `report.md`, `report.txt`, `metadata.json`, `artifact_manifest.txt`
- Updated: `qa_export_index.jsonl`, `qa_export_index.csv`, `latest_export.json`

## Safety

COORD-WR-006 reads QA export files and writes local Workflow_History JSONL/CSV files only. It opens no `DB.Transaction` or `DB.TransactionGroup`, calls no movement API, runs no workflow action automatically, changes no parameters or UI selection, and modifies no Revit model or linked-document data.

## Evidence

EV-AI-189 through EV-AI-196.

## Daily Log Row

`DL-2026-06-08-08 | 08-06-26 | Intra.actions B.V. | WBSO - AI Systems & Intelligent Automation | 8 | Implemented, debugged, and live-validated COORD-WR-006 Link Reset Workflow History / Run Register. Work included local JSONL/CSV workflow history storage, meaningful checkpoint filtering, duplicate prevention, cross-session QA export fallback seeding, parser validation, fallback recovery of the prior Ready / clean COORD-WR-005 checkpoint, final history QA export, and read-only governance validation. | EV-AI-189; EV-AI-190; EV-AI-191; EV-AI-192; EV-AI-193; EV-AI-194; EV-AI-195; EV-AI-196 | 2026-W11 | Validated on BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7 in TEST [FloorPlan]. Shared state was Not ready after session reset, so COORD-WR-006 recovered the clean checkpoint COORD-WR-005-20260605_163912 from QA export 20260605_163936. Final history report COORD-WR-006-20260608_094522 appended one record with Ready / clean status; duplicate test COORD-WR-006-20260608_094609 skipped duplicate append; final QA export: 20260608_094652.`
