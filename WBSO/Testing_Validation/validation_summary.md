# Validation Summary

## 2026-05-06 AI-AGENT-002 Guided Project Startup Plan

Status: runtime validated as plan-only.

### Environment

- Revit project: `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`
- Active view: `TEST [FloorPlan]`

### Validated paths

- AI Workbench opened normally.
- Bootstrap/startup behavior showed no long freeze.
- Scan Project completed.
- Ask Agent for Plan returned `[GUIDED PROJECT STARTUP PLAN]`.
- Deterministic prompts returned the same guided plan:
  - `guided project startup plan`
  - `project startup plan`
  - `what should the agent do first`
  - `agent project plan`
- Create Codex Brief included guided Agent startup plan metadata.
- No pyRevit console error was observed.
- No model mutation was observed.
- Agent remained plan-only.

### Observed project context

- Levels: 16
- Ambiguous level aliases: 14
- Views: 89
- Sheets: 6
- Revit links: 8 loaded, 0 unavailable
- Link coordinate health: OK
- BIM Basis / Levels & Grids: PARTIAL
- Level findings: 201
- Grid findings: 28
- CAD/imports: 46
- Schedules sampled: 20
- Populated schedules: 20
- Warnings: 10
- Selected elements: 0

### Agent plan phases

- Phase 1: Project onboarding checklist; BIM Basis / Levels & Grids review; CAD/import review; Review Revit warnings summary
- Phase 2: Active-view health check
- Phase 3: Create pipe schedule by level; Create pipe fitting schedule by level; ACO pipe fitting summary from template
- Blocked: Level-targeted automation because ambiguous level aliases exist

### Remaining unvalidated

- Execute Plan for the guided startup plan
- BIM Basis / Levels & Grids interpretation refinement for IFC-heavy projects
- Dedicated warning review action
- BIM3DNA toolbar-copy sync

## 2026-05-07 MEP-RO-001 Selection Reports Validation Attempt

Status: failed runtime validation.

### Feature

MEP-RO-001 ModelMind Read-Only BIM/QA Selection Action Pack.

### Environments tested

- `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`, active view `TEST [FloorPlan]`
- Snowdon Towers Sample HVAC
- Electrical sample/project

### Prompts tested

- `report selected elements by category`
- `report selected elements by type`
- `count selected elements`
- `health check selected elements`
- `report missing parameters from selection`

### Expected deterministic headers

- `[SELECTED ELEMENTS BY CATEGORY]`
- `[SELECTED ELEMENTS BY TYPE]`
- `[COUNT SELECTED ELEMENTS]`
- `[SELECTION HEALTH CHECK]`
- `[MISSING PARAMETERS FROM SELECTION]`

### Actual output

The prompts returned generic Ollama responses instead of Revit-specific deterministic reports, including Python/list counting guidance, HTML/browser/JavaScript-style health-check prose, generic parameter/form explanation, and generic category/type report text.

### Result

Failed. The Revit selection-report handlers were not live validated because the typed prompts fell through to Ollama before deterministic routing executed.

### Required next fix

- add deterministic routing for all MEP-RO-001 selection-report prompts before Ollama fallback
- read current live Revit selection at execution time through `uidoc.Selection.GetElementIds()`
- preserve standardized no-selection wording
- keep handlers read-only

### Safety

No model mutation was observed during this failed validation attempt.

## 2026-05-07 MEP-RO-001 Routing/Live Selection Hotfix - Passed Validation

Status: runtime validated after hotfix.

### Feature

MEP-RO-001 ModelMind Read-Only BIM/QA Selection Action Pack.

### Environments tested

- `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`, active view `TEST [FloorPlan]`
- Snowdon Towers Sample HVAC, active view `3D HVAC Layout`
- Snowdon Towers Sample Electrical, active view `3D - Just Electrical`

### Prompts tested

- `report selected elements by category`
- `report selected elements by type`
- `count selected elements`
- `health check selected elements`
- `report missing parameters from selection`

### Expected headers

- `[SELECTED ELEMENTS BY CATEGORY]`
- `[SELECTED ELEMENTS BY TYPE]`
- `[COUNT SELECTED ELEMENTS]`
- `[SELECTION HEALTH CHECK]`
- `[MISSING PARAMETERS FROM SELECTION]`

### Actual deterministic Revit-specific outputs

- no-selection tests returned deterministic headers and the standardized no-selection message
- BUNGE selected piping validation reported 21 selected elements: 12 Pipes and 9 Pipe Fittings, with sample levels Ground Floor 20 and First Floor 1
- Snowdon HVAC validation reported 111 selected elements: 42 Duct Fittings, 41 Ducts, 27 Air Terminals, and 1 Mechanical Equipment, with sample levels L5, L4, L3, and R1
- Snowdon Electrical validation reported 1300 selected elements, including Electrical Fixtures, Lighting Fixtures, Conduits, Conduit Fittings, Electrical Equipment, and Electrical Analytical Loads, with 66 type groups detected
- no generic Ollama fallback was observed for the five tested prompts after hotfix

### Prior failed validation

Resolved. The earlier failure is preserved in this file and was caused by typed prompts falling through to Ollama before deterministic routing.

### Safety

- no model mutation observed
- no pyRevit console error observed
- no long freeze observed

### Remaining refinements

- optional discipline-specific parameter sets
- active-view reports
- BIM3DNA toolbar sync

## 2026-05-07 - MEP-RO-002 and MEP-RO-003 Runtime Validation

### Status

- MEP-RO-002: runtime validated
- MEP-RO-003: runtime validated

### Summary

Read-only deterministic reporting was validated across piping, HVAC, and electrical contexts.

### MEP-RO-002

- active-view reports route deterministically before Ollama
- live active view is read at execution time
- active document only
- category/type/level/sample ElementId summaries validated
- missing-parameter reporting validated
- capped large-view handling validated

### MEP-RO-003

- system assignment reports route deterministically before Ollama
- live selection and live active-view scopes validated
- active document only
- no connector traversal
- no geometry extraction
- assigned/readable, missing/empty, unavailable/not applicable, and unknown/error summaries validated

### Safety

- no model mutation observed
- no generic Ollama fallback observed
- no pyRevit traceback observed in provided runtime outputs

## 2026-05-07 - MEP-RO-004 Discipline-Specific QA Rules Runtime Validation

### Status

MEP-RO-004: runtime validated after duplicate-rule aggregation hotfix.

### Summary

MEP-RO-004 adds deterministic read-only discipline-specific QA reports for selected elements and active-view MEP elements. It extends the validated MEP read-only stack with rule-based checks for piping, HVAC, and electrical contexts.

### Validation coverage

- BUNGE no-selection selected discipline QA returned the correct deterministic no-selection message.
- BUNGE selected piping QA returned piping rule summaries, failed checks by rule/category/type/level, unavailable/not applicable highlights, and deduplicated sample ElementIds.
- BUNGE active-view piping QA returned active-view piping rule summaries and confirmed visible Revit links are not scanned for internal QA.
- Snowdon HVAC active-view discipline QA handled a capped 2000-element inspection from a 2627-element active view.
- Snowdon Electrical active-view discipline QA generated electrical QA summaries with conduit/circuit applicability handled as unavailable/not applicable where appropriate.
- Snowdon selected electrical discipline QA generated selected electrical QA summaries.

### Hotfix trace

Initial runtime validation found duplicate failed-check reporting because `COMMON-001 Mark present` and `COMMON-002 Comments present` overlapped with discipline-specific PIP/HVAC/ELEC Mark and Comments rules. The hotfix suppresses duplicate common identity-rule failures where discipline-specific equivalents apply, deduplicates grouped sample ElementIds, and adds the report note that counts represent rule evaluations while sample ElementIds are deduplicated.

### Safety

- no generic Ollama fallback observed for known MEP-RO-004 prompt families
- no pyRevit traceback observed in provided runtime outputs
- no model mutation indicated
- no connector traversal, geometry extraction, linked-document scan, parameter write, tag creation, schedule/view/sheet creation, system assignment change, or electrical circuit edit is part of the validated behavior

## 2026-05-14 - MEP-RO-005 Exportable QA Evidence Snapshot Runtime Validation

### Status

MEP-RO-005: runtime validated.

### Summary

MEP-RO-005 adds a deterministic read-only export layer that saves the latest accepted AI Workbench diagnostic/QA report to a timestamped evidence folder. It extends the validated MEP read-only stack with filesystem evidence snapshots for WBSO, demo, and QA review workflows.

### Validation coverage

- Empty-state export guard returned `[QA REPORT EXPORT]` and `No exportable deterministic report is available yet. Run a read-only report first.`
- BUNGE active-view piping QA report exported successfully to `C:/Users/User/Desktop/Results/AI_Workbench/QA_Exports/20260514_163439`.
- Exported `report.md`, `report.txt`, `metadata.json`, and `artifact_manifest.txt` were created and inspected.
- `metadata.json` was valid JSON and contained `deterministic_route: true`, `read_only: true`, `model_modified: false`, `linked_documents_scanned: false`, `connector_traversal_used: false`, and `geometry_extraction_used: false`.
- Alternate aliases `save current QA report` and `create QA evidence snapshot` exported successfully.
- Snowdon HVAC capped QA report export preserved capped-report content in `report.md`.
- Snowdon selected electrical QA report export validated selected-scope metadata.
- Generic Ollama response rejection returned `[QA REPORT EXPORT]` and refused to export the non-deterministic output as QA evidence.

### Safety

- no generic Ollama fallback observed for export prompts
- no pyRevit traceback observed in provided runtime outputs
- no model mutation indicated
- no linked-document scan, connector traversal, geometry extraction, or Revit parameter write is part of the validated export behavior

## 2026-05-17 - MEP-RO-006 QA Export Index / Snapshot Registry Runtime Validation

### Status

MEP-RO-006: runtime validated.

### Summary

MEP-RO-006 extends MEP-RO-005 by maintaining a persistent local index for successful QA evidence exports.

### Validation coverage

- Empty index behavior returned deterministic no-index messages for `show QA export index` and `show latest QA export`.
- BUNGE active-view piping QA export updated `qa_export_index.jsonl`, `qa_export_index.csv`, and `latest_export.json`.
- Index file integrity was inspected for latest JSON, JSONL, and CSV governance fields.
- `list QA evidence snapshots`, `QA export index summary`, and `show latest QA export` returned deterministic index reports.
- Snowdon HVAC second indexed export updated latest export metadata and increased total indexed exports to 2.
- Generic Ollama response was rejected by export and did not create a new index entry.

### Safety

- index read/write is filesystem-only
- no Ollama fallback for index prompts
- no pyRevit traceback indicated
- no Revit model mutation indicated

## 2026-05-17 - MEP-ACT-001 Reviewed Action Proposal Framework Runtime Validation

### Status

MEP-ACT-001: runtime validated.

### Summary

MEP-ACT-001 introduces deterministic proposal-only reviewed-action preflights between the read-only QA/export stack and future reviewed write actions.

### Validation coverage

- No-selection split proposal returned not-ready proposal with no selected elements.
- BUNGE selected pipes/fittings preflight classified 34 selected elements into 9 eligible pipes, 14 skipped pipe fittings, 6 near-vertical pipes, and 5 too-short pipes.
- Non-pipe selection proposal classified 11 selected CAD/DWG/link-like elements as skipped non-pipe categories and returned not ready.
- Future action placeholders for tagging selected MEP elements and filling missing marks returned proposal-only/future-action-not-implemented outputs.
- Unknown reviewed action proposal returned deterministic suggestions for supported proposal prompts.
- `[REVIEWED ACTION PROPOSAL]` was exported by MEP-RO-005 and indexed by MEP-RO-006.
- Generic Ollama response after proposal was rejected as deterministic export evidence and did not replace latest export metadata.

### Safety

- proposal-only
- read-only
- no transaction opened
- no Revit model mutation indicated
- no connector traversal, geometry extraction, linked-document scan, parameter write, tag/schedule/view/sheet creation, system/circuit edit, or pipe splitting execution indicated

## 2026-05-18 - MEP-WR-001 Split Selected Pipes Dry Run Runtime Validation

### Status

MEP-WR-001: runtime validated.

### Summary

MEP-WR-001 adds deterministic dry-run-only candidate reporting for future selected pipe splitting. It reads live selected elements, classifies eligible and skipped elements, generates non-executable midpoint candidates for eligible straight pipes, and exports/indexes the report through MEP-RO-005/006.

### Validation coverage

- No-selection dry-run returned `[SPLIT SELECTED PIPES DRY RUN]`, Not ready, and no-mutation safety wording.
- BUNGE mixed pipes/fittings dry-run classified 21 selected elements into 3 eligible pipes, 3 candidate split points, 8 pipe fittings, 6 near-vertical pipes, and 4 too-short pipes.
- Candidate rows included pipe id, level, system, diameter/size, slope, original length, candidate point, and estimated segment A/B lengths.
- Non-pipe selection dry-run skipped 9 CAD/DWG/link-like elements and returned Not ready.
- Alias routes `calculate pipe split candidates` and `selected pipe split dry run` returned deterministic dry-run reports without Ollama fallback.
- Export/index validation passed with source header `[SPLIT SELECTED PIPES DRY RUN]` and selected-elements scope.
- Generic Ollama response was rejected as deterministic export evidence and did not replace the latest deterministic dry-run export.

### Safety

- dry-run only
- read-only
- no transaction opened
- no pipe was split
- no connector traversal, geometry extraction, linked-document scan, parameter write, or Revit model mutation indicated

## 2026-05-18 - MEP-ACT-002 Reviewed Proposal / Dry-Run Confirmation Guard Runtime Validation

### Status

MEP-ACT-002: runtime validated after report-scope metadata hotfix.

### Summary

MEP-ACT-002 adds a deterministic confirmation/readiness guard between reviewed proposals, split dry-runs, and future reviewed apply features. It detects latest proposal/dry-run session state, blocks confirm/apply/execute commands, and exports/indexes guard reports as deterministic evidence.

### Validation coverage

- No-source guard returned source type none, Not ready, `execution_available: false`, and `execution_performed: false`.
- Reviewed proposal state detection found the MEP-ACT-001 `[REVIEWED ACTION PROPOSAL]` state and returned status-only output.
- Confirm latest proposal was blocked because MEP-WR-002 reviewed apply is not implemented.
- Split dry-run state detection found the MEP-WR-001 `[SPLIT SELECTED PIPES DRY RUN]` state with 3 eligible pipes and 3 candidates, then blocked confirmation.
- `apply reviewed action` and `execute latest proposal` were blocked with no action applied.
- Status aliases `reviewed action status` and `can I apply latest action` returned deterministic status-only guard reports.
- Export/index validation passed with source header `[REVIEWED ACTION CONFIRMATION GUARD]`.
- Report-scope hotfix validated that confirmation guard exports store `session-local reviewed action state / active document only`.
- Generic Ollama response was rejected as deterministic export evidence and did not replace the latest deterministic guard export.

### Safety

- confirmation guard only
- read-only
- no transaction opened
- no action applied
- no pipe was split
- no connector traversal, geometry extraction, linked-document scan, parameter write, or Revit model mutation indicated

## 2026-05-19 - MEP-WR-002 Split Selected Pipes Rollback Test Runtime Validation

### Status

MEP-WR-002: runtime validated.

### Summary

MEP-WR-002 validates selected pipe split dry-run candidates against Revit's pipe split API inside a rollback-only transaction group. It requires prior MEP-WR-001 dry-run state and `ROLLBACK-TEST-OK` before any transaction opens.

### Validation coverage

- No-source rollback-test prompt returned source unavailable, Not ready, `Transaction opened: false`, `BreakCurve called: false`, and no model mutation.
- Valid dry-run source with missing token returned Confirmation required and did not open a transaction.
- Initial tokenized command `run split rollback test ROLLBACK-TEST-OK` fell through to generic Ollama; route hotfix was applied and validated.
- Tokenized rollback-test prompt processed 5 of 7 dry-run candidates under the safety cap.
- `PlumbingUtils.BreakCurve` returned temporary new pipe ids for 5 candidates inside the rollback transaction group.
- `TransactionGroup` rolled back successfully.
- Original pipe ids still resolved 5/5 after rollback.
- Temporary returned pipe ids no longer resolved 5/5 after rollback.
- Original lengths restored within tolerance 5/5.
- Export/index validation passed with source header `[SPLIT SELECTED PIPES ROLLBACK TEST]` and scope `latest split dry-run candidates / active document only`.

### Safety

- rollback test only
- no persistent model mutation
- no connector traversal
- no geometry extraction
- no linked-document scan
- no parameter write
- no tag/schedule/view/sheet/system/circuit edit

## 2026-06-05 - COORD-WR-005 Link Reset Workflow Status Dashboard

### Status

Runtime validated and export/index validated.

### Summary

COORD-WR-005 was validated in `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`, view `{3D - e.avdovicQREF7} [ThreeD]`, using link `2972572 | 3D-01B-AR-01.ifc : 48`.

The dashboard aggregates shared COORD-WR-001 audit, COORD-WR-002 rollback, COORD-WR-003 applied, COORD-WR-004 verified, and latest QA export state. Shared audit and verification persistence corrected the initial loss of status after selection was cleared.

### Critical Result

- final audit: `OK`
- 8 links near zero
- 0 offset links
- rollback: `Passed`
- apply: `Applied`
- verification: `Verified`
- selected RevitLinkInstance count: 0
- workflow status: `Ready / clean`
- transaction/model/selection/linked-document modification: false

Final export:
`C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260605_163936`

Commit:
`7e02f91 Add link reset workflow status dashboard`

## 2026-06-04 - COORD-WR-004 Link Origin Reset Post-Apply Verification Runtime Validation

### Status

COORD-WR-004: runtime validated and export/index validated.

### Summary

COORD-WR-004 was validated in `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`, active view `{3D - e.avdovicQREF7} [ThreeD]`. It verifies the latest COORD-WR-003 applied Revit link origin reset without opening a transaction or modifying model data.

### Main finding

COORD-WR-004 correctly verified link `2972572` after COORD-WR-003 reset it to zero origin. Both selected-link verification and no-selection latest-state verification returned `Verified`.

### Validation coverage

- COORD-WR-002 rollback `COORD-WR-002-20260604_151647` passed for link `2972572`.
- COORD-WR-003 readiness `COORD-WR-003-20260604_151952` passed as readiness-only; `Reviewed apply result: Not ready` means persistent apply was not requested.
- COORD-WR-003 apply `COORD-WR-003-20260604_152029` committed one transaction, called `MoveElement`, reset the link to `(0.000000, 0.000000, 0.000000)`, and stored `latest_link_origin_reset_apply_state`.
- COORD-WR-004 latest apply verification `COORD-WR-004-20260604_152052` returned `Verified`.
- COORD-WR-004 selected-link verification `COORD-WR-004-20260604_152647` returned `Verified`.
- COORD-WR-004 no-selection latest-state verification `COORD-WR-004-20260604_152936` returned `Verified`.
- `[LINK ORIGIN RESET POST-APPLY VERIFICATION]` exported and indexed at `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260604_153013`.
- Final `[LINK TRANSFORM AUDIT REPORT]` exported and indexed at `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260604_153603`.

### Safety

- COORD-WR-004 is read-only.
- Transaction opened: false.
- TransactionGroup opened: false.
- MoveElement called: false.
- Model modified: false.
- UI selection modified: false.
- Linked document modified: false.
- Stored element id use is verification-only.
- No apply-by-stored-id behavior was introduced.

## 2026-06-03 - COORD-WR-001 to COORD-WR-003 Link Transform Audit and Reviewed Reset Runtime Validation

### Status

COORD-WR-001, COORD-WR-002, and COORD-WR-003: runtime validated.

### Summary

The coordination workflow was runtime validated in `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`, active view `{3D - e.avdovicQREF7} [ThreeD]`. The selected test link was `2972572`, `3D-01B-AR-01.ifc : 48`, with original offset `(0.000000, -6.233596, 0.000000) ft`, approximately `(0, -1900, 0) mm`.

### Main finding

The workflow safely detected a non-zero link origin, rollback-tested a selected link origin reset, preserved the latest passed rollback source across prompt routes, and persistently reset exactly one reviewed selected link to project origin after explicit token confirmation.

### Critical safety validation

- COORD-WR-001 audit opened no transaction and modified no model data.
- COORD-WR-002 rollback test `COORD-WR-002-20260603_144729` opened a `TransactionGroup`, called `MoveElement`, verified temporary zero origin, rolled back, and left persistent model changes false.
- Latest passed rollback source was stored and read back through `AI_WORKBENCH_COORD_SHARED_STATE`.
- COORD-WR-003 readiness `COORD-WR-003-20260603_145224` passed without transaction or `MoveElement`.
- COORD-WR-003 apply `COORD-WR-003-20260603_145444` accepted `PERSISTENT-LINK-RESET-OK`, committed one transaction, and reset link `2972572` to `(0.000000, 0.000000, 0.000000)`.
- Post-apply audit `COORD-WR-001-20260603_145614` reported 8 loaded links, 8 near zero origin, 0 offset links, and audit result `OK`.
- QA export/index validation passed at `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260603_150023`.

### Safety

- no batch/all-link reset
- no apply by stored element id alone
- no linked document mutation
- no reload/unload
- no pin/unpin
- no parameter writes
- no rotation/transform API beyond guarded `MoveElement`
- no UI selection modification

## 2026-05-19 - MEP-WR-003 Split Selected Pipe Single-Candidate Persistent Reviewed Apply Core Runtime Validation

### Status

MEP-WR-003: core runtime validated.

### Summary

MEP-WR-003 validates the first persistent reviewed apply path. It applies exactly one candidate that was generated by MEP-WR-001, validated by MEP-WR-002, explicitly selected by the user, and explicitly confirmed with `PERSISTENT-SPLIT-OK`.

### Validation coverage

- Source-not-ready behavior blocked apply without transaction or model mutation.
- Readiness listing showed 5 eligible rollback-tested candidates and blocked candidates 6 and 7 as not rollback-tested due cap.
- Missing candidate selection returned Candidate selection required.
- Missing persistent token returned Confirmation required.
- Capped/untested candidate 6 was blocked with no transaction.
- Candidate 1 persistent apply passed for original pipe `3003513`.
- Returned new pipe id was `3130288`.
- Transaction opened, `BreakCurve` called, and `TransactionGroup` assimilated.
- Persistent model changes were reported true only after explicit candidate selection and token confirmation.
- Original and new segment lengths were each `4.657 ft (1419 mm)`.
- Combined segment length was `9.314 ft (2839 mm)` with `0 mm` delta.
- Generic `apply reviewed action` and `execute latest proposal` remained blocked by MEP-ACT-002.
- Export/index validation passed with source header `[SPLIT SELECTED PIPE REVIEWED APPLY]` and scope `single split candidate / active document only`.
- Generic Ollama response was rejected as deterministic export evidence.

### Follow-up limitation

Post-apply model-state verification via repeated `dry run split selected pipes` was inconclusive due empty selection; the active Revit selection was empty. The persistent apply report itself confirmed the split result, returned new pipe id, segment lengths, zero length delta, and persistent model change status.

### Safety

- exactly one persistent split applied
- no batch apply
- no connector traversal
- no geometry extraction
- no linked-document scan
- no parameter write
- no tag/schedule/view/sheet/system/circuit edit

## 2026-05-25 - MEP-WR-005 Split Apply Source Consumption / Staleness Guard Runtime Validation

### Status

MEP-WR-005: runtime validated.

### Summary

MEP-WR-005 was runtime validated in `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`, active view `TEST [FloorPlan]`. It adds a session-local consumed-source guard so a MEP-WR-001 dry-run / MEP-WR-002 rollback-test pair cannot be reused for additional persistent MEP-WR-003 applies after one successful model mutation.

### Main finding

A successful MEP-WR-003 persistent split marks the source dry-run/rollback pair consumed. A second persistent apply attempt from the same source is blocked before transaction and before `BreakCurve`.

### Critical safety validation

- stale candidate 2 apply blocked
- `Transaction opened: false`
- `BreakCurve called: false`
- `Transaction group assimilated: false`
- `Persistent model changes: false`

### Validation coverage

- Initial source-state route returned `[SPLIT APPLY SOURCE STATE]` with no source and apply allowed false.
- Fresh dry-run produced 7 candidate split points from 31 selected elements.
- Rollback-test processed 5 of 7 candidates, rolled back successfully, and passed.
- Source-state report showed current source fresh true and persistent apply allowed true before apply.
- Candidate 1 persistent apply split pipe `3003513` and returned new pipe `3130274`.
- Source-state report after apply showed consumed true, consumed by MEP-WR-003, applied candidate 1, original pipe `3003513`, returned new pipe `3130274`, current source fresh false, and persistent apply allowed false.
- `apply split candidate 2 PERSISTENT-SPLIT-OK` was blocked from stale source before transaction.
- MEP-WR-004 verification resolved original pipe `3003513` and returned new pipe `3130274`, verified lengths, and did not clear consumed source.
- Refreshed dry-run and rollback-test after the consumed timestamp restored source freshness and persistent-apply eligibility.
- Generic `apply reviewed action` remained blocked by MEP-ACT-002.
- `[SPLIT APPLY SOURCE STATE]` export/index validation passed with export folder `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260525_171457`.

### Safety

- WR-005 adds no new write API
- no new transaction
- no new `BreakCurve`
- no connector traversal
- no geometry extraction
- no linked-document scan
- no parameter write
- no tag/schedule/view/sheet/system/circuit edit
