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
