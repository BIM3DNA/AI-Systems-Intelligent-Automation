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
