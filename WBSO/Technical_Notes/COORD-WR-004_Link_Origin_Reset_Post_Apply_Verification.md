# COORD-WR-004 - Link Origin Reset Post-Apply Verification Helper

Date:
2026-06-04

Week:
2026-W11

Daily log reference:
DL-2026-06-04-08

Project:
AI Workbench / BIM3DNA Revit Coordination Automation

Commit:
`fefa253 Add link reset post-apply verification`

## Status

Runtime validated and export/index validated.

## Feature Chain Context

- COORD-WR-001 - Link Transform Audit / Coordinate Drift Report
- COORD-WR-002 - Link Origin Reset Rollback Test
- COORD-WR-003 - Single Selected Link Reviewed Origin Reset Apply
- COORD-WR-004 - Link Origin Reset Post-Apply Verification Helper

## Purpose

COORD-WR-004 provides a read-only post-apply verification report after COORD-WR-003 persistent reviewed link origin reset. It verifies whether the latest applied `RevitLinkInstance` is still at zero origin, whether the current transform matches the stored applied final state, and whether selected/no-selection verification modes behave safely.

Validated report header:
`[LINK ORIGIN RESET POST-APPLY VERIFICATION]`

Validated prompt routes:

- `verify latest link origin reset apply`
- `verify selected link reset result`
- `check latest link reset result`
- `export latest QA report`
- `show latest QA export`
- `audit link transforms`

## Technical Uncertainty

The coordination workflow needed a deterministic way to verify persistent link-origin reset results after COORD-WR-003 without opening a transaction or using any correction API. A key uncertainty was how to preserve and consume the latest applied state safely: COORD-WR-003 should store `latest_link_origin_reset_apply_state` only after a real `Applied` result, while COORD-WR-004 should use that stored element id for read-only verification only.

## Implementation Boundary

- COORD-WR-003 performs the persistent apply.
- COORD-WR-004 does not apply, move, reset, or correct links.
- COORD-WR-004 reads `latest_link_origin_reset_apply_state` for verification only.
- Stored element id use is verification-only and does not introduce apply-by-stored-id behavior.
- COORD-WR-003 now stores `latest_link_origin_reset_apply_state` only after a valid `Applied` result.
- The shared state source is `pyrevit script envvar AI_WORKBENCH_COORD_SHARED_STATE`.

## Runtime Validation Context

Validation model:
`BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`

Validation view:
`{3D - e.avdovicQREF7} [ThreeD]`

Target link:
`2972572`, `3D-01B-AR-01.ifc : 48`

## Runtime Validation Summary

### COORD-WR-002 Rollback Validation

- Rollback Test ID: `COORD-WR-002-20260604_151647`
- Selected link id: `2972572`
- Selected link name: `3D-01B-AR-01.ifc : 48`
- Original origin: `(0.000000, -6.561680, 0.000000)` internal feet
- Original approximate offset: `(0, -2000, 0)` mm
- Temporary origin: `(0.000000, 0.000000, 0.000000)`
- Temporary verification passed: true
- TransactionGroup rolled back: true
- TransactionGroup assimilated: false
- Persistent model changes: false
- Rollback test result: `Passed`
- Latest passed rollback source stored: true

### COORD-WR-003 Readiness Validation

- Apply ID: `COORD-WR-003-20260604_151952`
- Selected `RevitLinkInstance` count: 1
- Selected link matches rollback-tested link: true
- Current origin matches rollback source: true
- Current basis matches rollback source: true
- Current origin already zero: false
- Delta matches rollback-tested delta: true
- Pre-apply result: `Passed`
- Transaction opened: false
- MoveElement called: false
- Model modified: false

The readiness report says `Reviewed apply result: Not ready` because persistent apply was not requested. This is readiness-only behavior, not a failed validation.

### COORD-WR-003 Persistent Apply Validation

- Apply ID: `COORD-WR-003-20260604_152029`
- Confirmation token accepted: true
- Pre-apply result: `Passed`
- Transaction opened: true
- MoveElement called: true
- Transaction committed: true
- Persistent model changes: true
- Link transform modified persistently: true
- Linked document modified: false
- UI selection modified: false
- Final origin: `(0.000000, 0.000000, 0.000000)`
- Final approximate mm: `(0, 0, 0)`
- Final basis matches pre-apply basis: true
- Final rotation about Z: `0.0`
- Final mirrored flag: false
- Post-apply verification passed: true
- Reviewed apply result: `Applied`
- Latest apply state stored: true
- Latest apply state key: `latest_link_origin_reset_apply_state`
- Shared state source: `pyrevit script envvar AI_WORKBENCH_COORD_SHARED_STATE`

### COORD-WR-004 Latest Apply Verification

- Verification ID: `COORD-WR-004-20260604_152052`
- Latest COORD-WR-003 state exists: true
- Latest COORD-WR-003 raw state exists: true
- Latest COORD-WR-003 state valid Applied source: true
- Latest apply result: `Applied`
- Verification target source: latest apply
- Target link id: `2972572`
- Link resolves: true
- Current origin near zero: true
- Current basis orthonormal/safe: true
- Current basis matches latest apply final basis: true
- Current origin matches latest apply final origin: true
- Verification result: `Verified`
- Transaction opened: false
- Model modified: false
- Linked document modified: false
- UI selection modified: false

### COORD-WR-004 Selected-Link Verification

- Verification ID: `COORD-WR-004-20260604_152647`
- Selected element count: 1
- Selected `RevitLinkInstance` count: 1
- Selected link id: `2972572`
- Selected link matches latest applied link: true
- Current origin: `(0.000000, 0.000000, 0.000000)`
- Current approximate mm: `(0, 0, 0)`
- Current origin near zero: true
- Current basis matches latest apply final basis: true
- Current origin matches latest apply final origin: true
- Verification result: `Verified`
- Transaction opened: false
- Model modified: false

### COORD-WR-004 No-Selection Latest-State Verification

- Verification ID: `COORD-WR-004-20260604_152936`
- Selected `RevitLinkInstance` count: 0
- Latest COORD-WR-003 state exists: true
- Latest COORD-WR-003 state valid Applied source: true
- Verification target source: latest apply
- Target link id: `2972572`
- Target link resolves: true
- Current origin near zero: true
- Current basis matches latest apply final basis: true
- Current origin matches latest apply final origin: true
- Verification result: `Verified`
- Transaction opened: false
- Model modified: false

## QA Export / Index Validation

COORD-WR-004 export:

- Export folder: `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260604_153013`
- Source prompt: `check latest link reset result`
- Source header: `[LINK ORIGIN RESET POST-APPLY VERIFICATION]`
- Scope: `selected/latest Revit link origin reset post-apply verification / read-only`
- Generated files: `report.md`, `report.txt`, `metadata.json`, `artifact_manifest.txt`
- Indexes updated: `qa_export_index.jsonl`, `qa_export_index.csv`, `latest_export.json`

Final COORD-WR-001 audit export:

- Audit ID: `COORD-WR-001-20260604_153245`
- Export folder: `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260604_153603`
- Source prompt: `audit link transforms`
- Source header: `[LINK TRANSFORM AUDIT REPORT]`
- Scope: `active document Revit link transform audit / read-only`
- Total Revit link instances found: 8
- Loaded link instances: 8
- Unloaded / unresolved link instances: 0
- Selected Revit link instances: 0
- Links near zero origin: 8
- Links offset from zero: 0
- Links rotated/non-orthogonal: 0
- Links pinned: 0
- Future reset candidates: 0
- Links requiring manual review: 0
- Audit result: `OK`
- Recommended next action: no coordinate action required
- Transaction opened: false
- Model modified: false

## Safety Classification

COORD-WR-004 is strictly read-only. It opens no `Transaction`, opens no `TransactionGroup`, does not call `MoveElement`, does not modify model data, does not modify UI selection, does not mutate linked documents, does not reload/unload links, and does not pin/unpin links. It verifies the latest applied link state only.

## Evidence

EV-AI-173 through EV-AI-180.
