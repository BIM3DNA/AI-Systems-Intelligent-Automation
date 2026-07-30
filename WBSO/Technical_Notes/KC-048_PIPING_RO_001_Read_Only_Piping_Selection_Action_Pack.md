# KC-048 Knowledge Capture - PIPING-RO-001 Read-Only Piping Selection Action Pack

## Feature Package

- Feature ID: PIPING-RO-001
- Name: ModelMind Read-Only Piping Selection Action Pack
- Status: Implemented, live validated, targeted UI integration defects resolved, and committed locally; remote closure pending
- Date: 30-07-26 (`2026-07-30`)
- Week: `2026-W18`
- Branch: `main`
- Evidence: EV-AI-348 through EV-AI-353
- Daily logs: `DL-2026-07-24-01`; `DL-2026-07-30-01`; hours require manual entry
- Source-control status: correction commit `b3867636c0f5f7991da45a88362aacaab05a76f8` exists locally and has not been pushed

## Problem Statement

ModelMind needed deterministic, bounded, read-only inspection of rigid pipes already selected in the active Revit document. Existing generic selection reports did not expose piping-specific segment, system, slope, elevation, or reciprocal connector state. Existing broad piping reports also could not prove physical reciprocal connector relationships or distinguish supported rigid pipes from fittings, FlexPipe, fabrication parts, and unrelated selected elements.

## Read-Only Architecture

PIPING-RO-001 builds on the MEP-RO-001 selection snapshot and generic identity/QA helpers. It reads the current active-document selection without opening a picker, resolves each selected reference defensively, processes supported rigid pipes in deterministic ElementId order, and produces four report projections. It does not call active-view dashboard collectors or use the legacy Boolean connector count as authoritative evidence.

The implementation modifies only:

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/lib/prompt_catalog.json`

Implementation scope metadata reported by Codex was approximately 2001 insertions and one deletion across two files. This is scope metadata, not a quality result. The targeted correction commit changes only the primary AI Workbench script.

## Supported and Unsupported Scope

Supported elements must satisfy both `isinstance(element, DB.Plumbing.Pipe)` and category `OST_PipeCurves`.

Unsupported selection states are reported explicitly:

- `UNSUPPORTED_NON_PIPE`
- `UNSUPPORTED_PIPE_FITTING`
- `UNSUPPORTED_FLEX_PIPE`
- `UNSUPPORTED_FABRICATION_PART`
- `UNRESOLVED_REFERENCE`

Mixed supported/unsupported selections are processed but become PARTIAL. A selection with no supported rigid pipe returns `PIPING_SELECTION_REPORT_NOT_READY` / `NO_SUPPORTED_RIGID_PIPES`.

## Actions and Classifications

1. `show selected pipes summary` - `PIPING-RO-001-A01`
2. `show selected pipe connectors` - `PIPING-RO-001-A02`
3. `check selected pipes system assignment` - `PIPING-RO-001-A03`
4. `check selected pipes qa health` - `PIPING-RO-001-A04`

Result classifications are `PIPING_SELECTION_SUMMARY_OK`, `PIPING_CONNECTOR_REPORT_OK`, `PIPING_SYSTEM_ASSIGNMENT_OK`, `PIPING_QA_HEALTH_GREEN`, `PIPING_QA_HEALTH_YELLOW`, `PIPING_QA_HEALTH_PARTIAL`, `PIPING_SELECTION_REPORT_PARTIAL`, `PIPING_SELECTION_REPORT_NOT_READY`, and `PIPING_SELECTION_REPORT_FAILED`.

Sixteen canonical/alias lookups are uniquely owned. Existing aliases `check selected pipe systems` and `selected piping qa report` remain assigned to legacy handlers.

## Pipe Record Model

Each supported pipe record includes guarded identity, type, segment, workset, pinned/group/assembly/design-option state, system assignment, diameter, length, slope, endpoint elevations, reference level, optional insulation thickness, connector totals, reciprocal connection totals, connected owner IDs, and explicit unreadable/partial states.

Pipe segment resolution prefers stable Revit built-in/API metadata. It reports `AVAILABLE`, `NOT_SUPPORTED`, `UNAVAILABLE`, or `UNREADABLE`; API failure is partial rather than a false missing-segment defect.

## System Assignment Model

Resolution priority is:

1. `Pipe.MEPSystem`;
2. built-in system ID/name/type/classification parameters;
3. the existing coarse fallback as supplementary metadata.

Normalized states are `ASSIGNED`, `UNASSIGNED_REVIEW`, `UNAVAILABLE`, `UNREADABLE`, and `INCONSISTENT`. Contradiction is evaluated per pipe, not across the selection. Runtime validation with pipes on `M531 7` and `Domestic Cold Water 1` confirmed that multiple legitimate systems remain a distribution and do not trigger inconsistency.

## Slope Model

The signed built-in slope ratio is preserved and displayed as ratio, percent, per mille, and `degrees(atan(abs(ratio)))`. Endpoint elevations are read independently. Straight nonvertical pipes are applicable; vertical or near-vertical pipes use a 1 mm horizontal-run tolerance and report `NOT_APPLICABLE`. The implementation never derives a replacement slope or modifies the model.

## Reciprocal Connector Rules

Connector inspection is limited to connectors owned by the selected pipe and one immediate `AllRefs` hop. Eligible connectors require piping domain and a positive physical connector type. Logical/reference/system-only connectors, self-owner references, unresolved owners, and non-active-document owners are excluded.

A physical connection is counted only when both `connector.IsConnectedTo(reference)` and `reference.IsConnectedTo(connector)` return true. Raw `IsConnected` is diagnostic only. Connection, disconnection, graph traversal, model mutation, selection change, and active-view change are forbidden.

Live evidence confirmed two reciprocal connections for pipe `3060449`, and one reciprocal plus one open connector for pipe `3060110`.

## Stable QA Checks

- `PIPING-QA-001` Unsupported selected element
- `PIPING-QA-002` Missing pipe type
- `PIPING-QA-003` Missing pipe segment
- `PIPING-QA-004` Missing system assignment
- `PIPING-QA-005` Missing or zero diameter
- `PIPING-QA-006` Missing or near-zero length
- `PIPING-QA-007` Slope data unavailable
- `PIPING-QA-008` Unconnected physical connector
- `PIPING-QA-009` Abnormal physical connector count
- `PIPING-QA-010` Connector read failure
- `PIPING-QA-011` Inconsistent system metadata
- `PIPING-QA-012` Unreadable required piping parameter

Generic checks reused from MEP-RO-001 are `SEL-QA-001` through `SEL-QA-008`, `SEL-QA-011`, `SEL-QA-013`, `SEL-QA-015`, and `SEL-QA-016`.

## Caps and Sorting

Caps are 200 processed pipes, 200 pipe rows, 400 connector-detail rows, 8 displayed connectors per pipe, 20 connected-owner IDs per connector, 50 affected IDs per check, 50 warnings, and 160 normalized characters. Display truncation alone is not PARTIAL; skipped supported pipes are.

Sorting uses numeric pipe ElementId, connector origin/type/domain/sequence, numeric owner IDs, stable QA IDs, normalized system fields, and count-descending distributions.

## Live Validation

Validation used `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`, views `TEST [FloorPlan]` and `{3D - e.avdovicQREF7} [ThreeD]`, discipline Piping.

- All four no-selection actions returned NOT_READY / `NO_ELEMENTS_SELECTED`.
- Pipe `3060449` returned summary, connector, and system OK; all piping checks passed; generic blank Mark produced QA YELLOW.
- Pipe `3060449` plus Wall `3130302` produced summary/QA PARTIAL, with `PIPING-QA-001` identifying the wall.
- Fitting `3060245` alone returned NOT_READY / `NO_SUPPORTED_RIGID_PIPES`.
- Pipe `3060110` plus fitting `3060245` produced PARTIAL; the vertical pipe had slope not applicable and one reciprocal plus one open connector.
- Standard pipe `3130534` retained a valid assigned system while both connectors were open.
- Pipes `3060449` and `3130534` validated two legitimate systems with no `PIPING-QA-011` inconsistency.

## Workflow Isolation

Every tested report showed model, UI selection, active view, external files, transaction, TransactionGroup, linked document, picker, and auto-run flags false. Evidence Runbook advancement, Evidence Cycle Manifest update, Workflow Anchor eligibility, QA-source eligibility, and evidence-cycle stage were false. Visual Preview retained `MEP-QA-DASHBOARD-v1` as authoritative Workflow Anchor.

## Context Suggestions and Visual Preview Correction

The root cause was inconsistent fixed suggestion limits across Context Suggestions and safe prompt-card projection. The six-command limit was consumed by the highest-priority evidence/export item, four generic MEP-RO-001 actions, and the first piping action.

The correction keeps the normal-context capacity at six and raises capacity to ten only when at least one supported rigid pipe is selected. Both Context Suggestions and safe prompt-card projection use the same dynamic capacity. Evidence/export precedence and the four generic MEP-RO-001 actions remain ahead of all four PIPING-RO-001 actions. No-selection, Wall-only, and fitting-only contexts retain the normal behavior and expose no piping suggestions.

Visual Preview parsing now recognizes the PIPING-RO-001 snake-case safety fields `model_modified`, `ui_selection_modified`, and `external_files_written`. New reports display explicit false values. Historical Console records that already contain unknown values are retained and are not rewritten.

Live correction validation on pipe `3003513` confirmed all four piping suggestions, all four generic selection suggestions, the higher-priority evidence/export suggestion, and the optional history suggestion in deterministic order. Pipe+Wall retained the same piping availability. Direct execution returned summary OK, connectors OK, system assignment OK, and QA YELLOW. Visual Preview showed model modification, UI selection modification, and external file writing as false.

## Final Correction and Source Control

Commit `b3867636c0f5f7991da45a88362aacaab05a76f8` (`Fix PIPING-RO-001 context suggestion exposure`) contains only `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`. It applies the context-aware suggestion capacity and the targeted Visual Preview safety-field aliases. The commit is local on `main`; remote closure remains pending because it has not been pushed.

The commit parent is `27b159998f1caa5637897a90712c4048cae10e91`. Its diff is one file changed, 13 insertions, and 6 deletions. The worktree was clean immediately after the correction commit, and `main` was ahead of `origin/main` by one commit and behind by zero before this WBSO-only update. The correction commit excludes the prompt catalog, WBSO files, generated evidence, Console history, ZIP files, and package files.

## Limitations

The following paths were not practically live validated: `UNASSIGNED_REVIEW`, FlexPipe-only, fabrication-part-only, connector-manager failure, inconsistent authoritative system metadata, missing/unreadable segment, missing/zero diameter, sub-1-mm length, more than 200 supported pipes, connector-detail cap, and connected-owner cap. System type currently displays as ElementId rather than resolved type name. Historical Visual Preview records are not retroactively rewritten.

## Conclusion

PIPING-RO-001 is implemented, substantially live validated, targeted Context Suggestions and Visual Preview integration defects resolved, and committed locally in b386763. Remote source-control closure remains pending until the commit is pushed.
