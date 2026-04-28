# Test Plan

## Project

AI Systems & Intelligent Automation

## Milestone

2026-04-08 AI window architecture refactor

## Purpose

This test plan defines the next validation checkpoint after refactoring the single pyRevit AI window into clearer product roles with structured prompts and guarded local state.

## Primary Runtime Risks to Revalidate

1. the AI tab still loads in pyRevit
2. the active button still opens the refactored UI
3. Ollama Chat still answers a simple prompt
4. ModelMind deterministic prompts still execute correctly
5. the AI Agent plan/review/execute surface behaves according to the new semantics
6. theme toggle persists across relaunch

## Required Validation Model

Snowdon Towers Sample HVAC

## Planned Scenario Set

### 1. HVAC modeller

- run `list ducts in active view`
- run `find unconnected fittings`
- run `report elements without system assignment`

### 2. BIM manager

- run `health check`
- run representative counts/totals/report prompts
- confirm structured prompt-tree navigation and filtering

## 2026-04-21 Stable-Baseline Catalog Usability Checks

1. confirm the dedicated ModelMind catalog filter narrows the tree without modifying the main prompt input
2. confirm clear/reset restores the full grouped catalog
3. confirm Expand All / Collapse All only affect catalog browsing state
4. confirm Selected Action Details remain readable for canonical entries, approved recipes, and Recent Prompts
5. confirm no regression to validated create-sheet, create-3d-view, rename-active-view, preset, or category-helper execution paths

## 2026-04-21 Stable-Baseline Reviewed Schedule Checks

1. create pipe schedule by level in detailed mode
2. create duct fitting schedule by level in summary mode
3. create conduit schedule by reference level
4. create electrical fixture/equipment schedule by level and confirm whether separate fixture/equipment schedules are created as designed
5. create schedule bundle by level and confirm supported categories are created deterministically
6. confirm template-first duplication works when an explicit source schedule exists
7. confirm native fallback is honest when no schedule template is found
8. confirm no regression to validated create-sheet, create-3d-view, rename-active-view, preset, or category-helper execution paths

## 2026-04-21 Schedule Promotion And Template Checks

1. confirm generic validated schedule actions appear under `Schedules` with the expected Pipes / Ducts / Electrical / Bundles grouping
2. confirm `create pipe schedule by level`, `create duct fitting summary by level`, `create schedule bundle by reference level`, and `create electrical fixture/equipment schedule by level` resolve as `live_validated`
3. confirm ACO template actions appear under `Schedules / Template-Based`
4. confirm template-only actions fail honestly when no matching source schedule exists
5. confirm template actions do not silently fall back to the generic native schedule family

### 3. General chat

- send a simple Ollama Chat prompt and confirm response

### 4. Safety and UX

- confirm `Allow destructive tools` is off by default
- confirm `Run Agent` creates a plan only
- confirm `Execute Plan` only runs reviewed enabled commands
- confirm `Undo Last Action` is visibly disabled with explanation
- confirm theme toggling persists after relaunch

## What Was Actually Executed During This Workspace Pass

- parsed `prompt_catalog.json`
- parsed `approved_recipes.json`
- validated that `UI.xaml` is well-formed XML
- performed static code review of the refactored controller and helper modules

## Live Findings Already Available for This Pass

- theme persistence works across relaunch
- Ollama Chat works in live runtime
- ModelMind deterministic tasks work
- failed reviewed-code runs are not added to approved recipes

## New Post-Hardening Runtime Targets

1. deterministic ModelMind task still works
2. invalid generated code with DesignScript references is blocked before execution
3. valid pyRevit-compatible reviewed code can execute
4. successful reviewed run can be saved as approved recipe
5. approved recipe appears in the ModelMind approved branch after reload

## 2026-04-09 Runtime Targets for This Polish Pass

1. Ollama Chat still works
2. ModelMind `select all ducts` still works
3. reviewed create-sheet flow still works
4. approved recipe save/load still works
5. AI Agent successfully handles:
   - count selected ducts
   - count all ducts in active view
   - list ducts in active view
6. top-right header alignment is fixed
7. dark-mode dropdown text is readable
8. dark-mode tree text is readable
9. disabled buttons remain readable

## 2026-04-09 Runtime Targets for This Provider-Integration Pass

1. ModelMind layout is improved:
   - input wider
   - action buttons below input
2. Ollama Chat still works
3. AI Agent local planning still handles supported deterministic cases
4. AI Agent cloud planning can normalize at least:
   - count selected ducts
   - count all ducts in active view
   - list ducts in active view
   - create sheet
5. Execute Plan only works for supported reviewed actions
6. missing `OPENAI_API_KEY` state is handled gracefully
7. cloud provider failure falls back cleanly or shows a precise error

## 2026-04-10 Runtime Targets for This Provider-Diagnostics Pass

1. key-present state no longer shows missing-key guidance
2. cloud request failure shows the correct classified failure category
3. local deterministic planner still works when cloud planning fails
4. unsupported schedule-generation request shows clear reviewed deterministic guidance
5. supported deterministic requests still work

## 2026-04-10 Runtime Targets for This Cloud Self-Test Pass

1. determine whether `OPENAI_API_KEY` is visible to the runtime actually used by the cloud planner
2. determine whether `openai` is importable in that runtime
3. determine whether client initialization succeeds in that runtime
4. determine whether a provider probe request succeeds in that runtime
5. confirm local deterministic planner still works

## 2026-04-10 Runtime Targets for This Responses API Pass

1. confirm the cloud planner service can import `openai` in the runtime it actually uses
2. confirm a minimal Responses API probe succeeds
3. confirm AI Agent can normalize:
   - select ducts
   - count selected ducts
   - create sheet
4. keep unsupported broader schedule-generation requests rejected unless actually implemented

## 2026-04-10 Runtime Targets for This Shared Registry Pass

1. ModelMind shows the shared reviewed actions correctly
2. AI Agent can execute:
   - select all ducts
   - count selected ducts
   - count ducts in active view
   - report total selected duct volume in cubic meters
   - find unconnected duct fittings
   - create sheet
3. approved recipes still save and reload correctly

## 2026-04-13 Runtime Targets for This Expanded MEP Pass

ModelMind

1. report total selected duct length
2. report total selected duct volume in cubic meters
3. find unconnected duct fittings
4. report ducts without system assignment
5. select all pipes
6. count pipes in active view
7. list pipes in active view

AI Agent

8. natural-language mapping for:
   - `duct length`
   - `volume of selected ducts`
   - `find disconnected duct fittings`
   - `pipes without system`
   - `create a 3d view from this selection`
9. reviewed plan generation remains bounded and execution remains deterministic

## Additional Checks Executed In This Provider-Integration Pass

- compiled `AI.extension/lib/ai_local_store.py`
- compiled `AI.extension/lib/ai_prompt_registry.py`
- compiled `AI.extension/lib/ai_agent_session.py`
- compiled `AI.extension/lib/ai_reviewed_code.py`
- compiled `Model_Service/ModelService.py`
- compiled `Openai_Server/chatgpt_service.py`
- reparsed `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`

## Additional Checks Executed In This Provider-Diagnostics Pass

- compiled `AI.extension/lib/ai_prompt_registry.py`
- compiled `AI.extension/lib/ai_agent_session.py`
- compiled `Model_Service/ModelService.py`
- compiled `Openai_Server/chatgpt_service.py`
- reparsed `AI.extension/lib/prompt_catalog.json`

## Additional Checks Executed In This Cloud Self-Test Pass

- compiled `Openai_Server/chatgpt_service.py`
- compiled `Model_Service/ModelService.py`
- compiled `AI.extension/lib/ai_agent_session.py`
- executed `--provider-state` through the service path
- executed `--provider-self-test` through the service path

Workspace self-test result:

- `env_key_present: yes`
- `openai_module_importable: yes`
- `client_init_ok: yes`
- `test_request_ok: no`
- `failure_category: network_failed`

## Additional Checks Executed In This Responses API Pass

- switched provider probe to the OpenAI Responses API
- switched planner normalization requests to the OpenAI Responses API
- re-ran provider-state and provider-self-test through the service path

Current workspace result after the Responses API switch:

- `failure_category: network_failed`

## Additional Checks Executed In This Shared Registry Pass

- compiled `AI.extension/lib/ai_prompt_registry.py`
- compiled `AI.extension/lib/ai_agent_session.py`
- reparsed `AI.extension/lib/prompt_catalog.json`
- loaded shared reviewed actions from the registry
- verified AI Agent local planning against shared aliases for:
  - `select ducts`
  - `count selected ducts`
  - `volume of selected ducts`
  - `find disconnected duct fittings`
  - `create a sheet`

Shared reviewed actions loaded locally:

- `23`

## Additional Checks Executed In This Expanded MEP Pass

- compiled `AI.extension/lib/ai_prompt_registry.py`
- compiled `AI.extension/lib/ai_agent_session.py`
- reparsed `AI.extension/lib/prompt_catalog.json`
- verified shared reviewed actions loaded from registry: `26`
- verified AI Agent local shared-registry planning for:
  - `duct length`
  - `total selected duct volume`
  - `pipes without system`
  - `count pipes in active view`
  - `electrical devices in active view`
  - `create a 3d view from this selection`

## Live Findings Already Reported Before This Pass

- Ollama Chat works with `phi3:mini`
- ModelMind works for:
  - `select all ducts`
  - `count ducts in active view`
  - `list ducts in active view`
  - `create sheet`
- AI Agent works for:
  - `select ducts`
  - `count selected ducts`
  - `count ducts in active view`
  - `list ducts in active view`
- reviewed create-sheet flow remains working
- approved recipe save/load remains working
- `gemma3:27b` appears unstable/crashes in runtime while `phi3:mini` is stable
- `report total selected duct volume in cubic meters` returned `0.000 m³` before the fix in this pass

## Additional Live Checks Not Executed In This Provider-Integration Pass

- live ModelMind layout verification in Revit
- live AI Agent local planner verification after provider wiring
- live AI Agent OpenAI planner normalization with a valid key
- live missing-key handling verification
- live cloud request failure verification

## Additional Live Checks Not Executed In This Provider-Diagnostics Pass

- live verification that key-present no longer shows the missing-key message
- live verification of provider category reporting for auth/network/request failures
- live verification of local fallback after a cloud failure
- live verification of the clearer unsupported schedule/quantity guidance

## Additional Live Checks Not Executed In This Cloud Self-Test Pass

- live Revit confirmation of the runtime-visible `OPENAI_API_KEY` state
- live Revit confirmation of `openai` importability in the actual cloud-planner runtime
- live Revit confirmation of the exact self-test failure category

## Additional Live Checks Not Executed In This Responses API Pass

- live Revit confirmation that the Responses API path works after dependency parity is fixed
- live Revit confirmation of AI Agent cloud normalization for the supported cases

## Additional Live Checks Not Executed In This Shared Registry Pass

- live Revit validation of the shared ModelMind tree
- live Revit execution validation for the expanded MEP reviewed action set
- live Revit validation of approved recipe continuity after the registry refactor

## Additional Live Checks Not Executed In This Expanded MEP Pass

- duct-volume action validation after the robustness fix
- new pipe active-view actions
- new electrical and QA/BIM reviewed actions
- `create 3D view` in live Revit

## Acceptance Condition for Next Runtime Pass

The refactor should only be considered runtime-proven after the scenario set above is executed and documented in Revit/pyRevit.

## 2026-04-14 Runtime Targets for Shared Catalog Visibility and Resize Pass

### ModelMind

- confirm the tree now shows the governed shared reviewed catalog under:
  - HVAC
  - Piping
  - Electrical
  - QA / BIM
  - Views / Sheets
- confirm aliases/examples appear only in the action details area, not as duplicate tree nodes
- confirm Approved Recipes remain separate and group by domain where possible
- confirm Recent Prompts appears only as a convenience branch and does not pollute the canonical catalog

### AI Agent

- confirm AI Agent still has no second catalog tree
- confirm the supported-actions summary/list reflects the current shared reviewed actions instead of an outdated subset
- confirm the currently matched reviewed action is visible when a plan is generated

### Window shell

- confirm the window can be resized in pyRevit/Revit
- confirm width, height, and screen position are restored on reopen
- confirm the ModelMind splitter, output pane, prompt tree, and button area remain stable without overlap or clipping

### What was actually executed in this workspace pass

- local tree-shape verification for the shared reviewed catalog
- local registry count verification: `26` reviewed actions
- local AI Agent supported-action count verification: `26`
- local XML parse of `UI.xaml`

### Live checks not executed in this pass

- live Revit confirmation of grouped ModelMind tree rendering
- live Revit confirmation of window resize/restore behavior
- live Revit confirmation of approved-recipe domain grouping in the new tree structure

## 2026-04-14 Runtime Targets for AI Agent Queue State Pass

### AI Agent

- confirm the bottom selector now shows only current reviewed plan steps
- confirm supported reviewed actions remain visible separately as informational text
- confirm selecting a current plan step enables `Disable/Enable`
- confirm `Reset Commands` enables only when a current plan exists
- confirm `Execute Plan` enables only when the current plan has at least one runnable enabled step
- confirm modifying-only plans stay blocked when destructive tools remain off
- confirm `Undo Last Action` remains disabled unless a real reversible context exists

### What was actually executed in this workspace pass

- local session-state check for a `count selected ducts` plan
- local verification that queued step state fields are present
- local verification that disabling the only step makes `has_enabled_steps` false
- local XML parse of `UI.xaml`

### Live checks not executed in this pass

- live pyRevit confirmation of the revised queue selector behavior
- live confirmation of button enable/disable transitions during real Agent use

## 2026-04-14 Runtime Targets for Action-Specific Undo Pass

### AI Agent undo

- run `Create 3D view from current selection/context`
- confirm Undo Last Action becomes enabled only after that modifying action completes successfully
- trigger Undo Last Action and confirm:
  - the created 3D view is deleted
  - the Agent reports:
    - `UNDONE: Create 3D view from current selection/context`
    - `Deleted created 3D view: <name>`
- confirm Undo Last Action disables again after successful use

### Honest failure cases

- attempt undo with no undo context and confirm honest failure text
- attempt undo after the created view is manually deleted and confirm honest failure text
- confirm read-only actions never enable Undo Last Action

### What was actually executed in this workspace pass

- local session-state checks for blocked modifying, successful modifying, reset-cleared, and read-only execution paths
- local XML parse of `UI.xaml`

### Live checks not executed in this pass

- real Revit create-3D-view undo
- real runtime invalid-context failure checks

## 2026-04-15 Runtime Targets for Create-Sheet Undo Extension

### Undoable modifying actions

- run `Create sheet` through:
  - AI Agent plan execution
  - ModelMind reviewed execution
  - approved recipe execution
- confirm each successful create-sheet path enables Undo Last Action
- trigger Undo Last Action and confirm:
  - the created sheet is deleted
  - the Agent reports:
    - `UNDONE: Create sheet`
    - `Deleted created sheet: <sheet number> (<sheet name>)`

### Honest failure cases

- attempt sheet undo when the created sheet was manually deleted
- attempt sheet undo when the document/context has changed
- confirm honest failure messaging rather than silent success

### What was actually executed in this workspace pass

- local session-state checks for create-sheet undo-context creation
- local confirmation that reset clears undo context
- local confirmation that create-3D-view undo-context behavior still works

### Live checks not executed in this pass

- actual Revit sheet deletion by undo
- approved-recipe create-sheet undo in live runtime

## 2026-04-15 Runtime Targets for QA/BIM Hardening

### QA / BIM actions

- run `report selected elements by category` on a mixed selection and confirm:
  - total selected count
  - grouped breakdown
  - sample ids
  - truncation behavior when many groups exist
- run `report selected elements by type` and confirm the same structure
- run `report missing key parameters from selected elements` and confirm:
  - only meaningful/applicable checks are included
  - explicit nothing-missing or no-selection notes appear when appropriate
- run `health check of active view for supported MEP categories` and confirm:
  - per-category counts
  - unconnected fitting findings where supported
  - missing system/electrical assignment findings where supported

### What was actually executed in this workspace pass

- local syntax/tokenization check on the updated script
- local XML parse of `UI.xaml`
- local inspection of the hardened QA/BIM output paths in code

### Live checks not executed in this pass

- all runtime confirmation for the hardened QA/BIM summaries

## 2026-04-15 Runtime Targets for QA/BIM Scope/Alias Hardening

### Scope messaging

- run selected-element QA/BIM actions with no active selection and confirm output explicitly says:
  - no selected elements found in the active Revit document
  - selections in other open Revit projects are not included
- run the active-view health check and confirm output explicitly says:
  - `View scope: active view in active document`

### Planner alias coverage

- confirm the planner normalizes:
  - `show selected elements by category`
  - `group selected elements by type`
  - `check missing key parameters in selection`
  - `health check this active view`
  - `inspect active view for MEP issues`

### What was actually executed in this workspace pass

- local alias-normalization checks through the shared catalog/planner path
- local verification of scope-message text in the QA/BIM handlers
- local JSON parse of `prompt_catalog.json`

### Live checks not executed in this pass

- all live confirmation for the new scope wording and QA/BIM alias behavior

## 2026-04-15 Runtime Targets for QA/BIM Category Grouping Defect Fix

### Reviewed action under test

- `report selected elements by category`

### Runtime checks to execute

- select a known mixed set of elements in the active Revit document
- run `report selected elements by category`
- confirm output includes:
  - `Selection scope: active document only`
  - `Total selected elements: <n>`
  - real category groups such as `Ducts: <count>` and `Duct Fittings: <count>` when applicable
- confirm valid selections no longer render:
  - `(err): <count> | sample ids: ...`

### What was actually executed in this workspace pass

- local code inspection of the category report and shared naming helper
- local sanity verification after hardening `get_elem_name()`

### Live checks not executed in this pass

- all live confirmation for corrected grouped category output

## 2026-04-15 Runtime Targets for QA/BIM Validation-State Promotion and Context UX

### Metadata checks

- confirm the Selected Action panel shows `Validation: live_validated` for:
  - report selected elements by category
  - report selected elements by type
  - report missing key parameters from selected elements
  - health check of active view for supported MEP categories

### Recent Prompt consistency checks

- select one of the live-validated QA/BIM actions through Recent Prompts
- confirm the Selected Action panel resolves to canonical reviewed-action metadata instead of appearing empty or history-only

### Context-UX checks

- confirm selection-based QA/BIM outputs now include:
  - active document
  - active view
  - current selection count
- confirm the active-view health check now includes the active document line

### What was actually executed in this workspace pass

- local JSON and shared-registry verification of promoted validation states
- local code verification of canonical Recent Prompt detail resolution
- local tokenization/indentation sanity check of `script.py`

### Live checks not executed in this pass

- all live confirmation for validation-state promotion and context-UX presentation

## 2026-04-16 Runtime Targets for Reviewed Production-Assistant Expansion

### QA presets

- run:
  - HVAC QA preset
  - Piping QA preset
  - Electrical QA preset
  - Coordination / BIM QA preset
- confirm each preset executes its reviewed steps without crashing when selection-based steps have no active-document selection

### New reviewed actions

- validate in live Revit:
  - split selected pipes
  - report duplicates
  - remove duplicates
  - categories list + id
  - select/count/list all elements of category
  - report rooms without matching spaces
  - report spaces without matching rooms
  - report room/space mismatches
  - rename active view
  - align selected tags
  - total length of selected linear MEP elements
  - total length in active view for supported linear MEP categories

### Undo checks

- confirm rename active view creates a real reversible undo context
- confirm Undo Last Action restores the prior active-view name

### What was actually executed in this workspace pass

- local syntax/tokenization/JSON/XAML sanity checks
- shared-registry grouping sanity checks
- planner alias matching checks for new presets/actions

### Live checks not executed in this pass

- all live confirmation for the new presets/actions added in this pass

## 2026-04-19 Runtime Targets for Preset Hardening and Scope Governance

### Presets

- run and validate:
  - HVAC QA preset
  - Piping QA preset
  - Electrical QA preset
  - Coordination / BIM QA preset
- confirm one preset step does not contaminate downstream selected-element inputs unless explicitly intended

### Category helpers

- validate category disambiguation for:
  - walls
  - doors
  - pipe fittings
- validate exact syntax:
  - `category:walls`
  - `category:\"Pipe Fittings\"`
  - `categories:doors,windows`

### Undo

- validate ModelMind shared undo on a real reversible reviewed action

### Split-pipe aliases

- validate:
  - `split selected pipes 1.5 m each`
  - `split selected pipes at 1.5 m`
  - `split selected pipes into 1500 mm segments`
  - `split selected pipes to max 1500 mm`
  - `split selected pipes every 1500 mm`

### What was actually executed in this workspace pass

- local syntax/tokenization/JSON/XAML sanity checks
- planner alias checks for hardened presets and expanded split-pipe variants

### Live checks not executed in this pass

- all live validation targets listed above

## 2026-04-27 Project Context UX/Q&A Validation Targets

### Local/static checks

- run `python -m tabnanny AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- compile `AI.extension/lib/ai_prompt_registry.py`
- compile `AI.extension/lib/ai_agent_session.py`
- parse `AI.extension/lib/prompt_catalog.json`
- parse `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`
- inspect that no project-context scanner or context-answer code adds Revit transactions

### Live Revit checks pending

- Workbench opens without freeze and bootstrap context loads
- Project Context panel can be resized and remains readable in dark theme
- tree shows link names/status, schedule names/status, category counts, warning groups, and detected issues
- deterministic prompts `what schedules exist`, `what CAD imports are in this model`, and `what are the main BIM issues` answer without Ollama timeout
- Ask Agent for Plan remains plan-only and Create Codex Brief remains copy-only

## 2026-04-27 Project Context Consistency Validation Targets

- run Scan Project after bootstrap context loads
- confirm scan summary, Project Context tree, `what schedules exist`, AI Agent observed context, and Codex brief report matching schedule sampled/populated/empty/unknown counts
- confirm warning count matches across scan summary, tree, `show warnings`, AI Agent observed context, and Codex brief
- confirm `what should I test first in this project` returns BIM/project first checks rather than generic software testing guidance
- confirm Revit links display human-readable link names/status and no raw `Autodesk.Revit.DB.FilePath object at ...` text
- confirm no model mutation occurs

## 2026-04-28 Project Context Chat Readability Validation Targets

- run `what schedules exist` and confirm the chat answer shows schedule summary counts first, then capped grouped details
- run `what CAD imports are in this model`, `what are the main BIM issues`, `what should I test first in this project`, `summarize current project`, and `what links are loaded`
- confirm chat turns are visually separated with plain-text separators
- confirm Project Context tree still contains full schedule/context detail
- confirm no model mutation occurs

## 2026-04-28 Linked Model Coordinate Health Validation Targets

- run Scan Project and expand Project Context > Links / Coordinate Health
- confirm link names/status/path text are readable and no raw `Autodesk.Revit.DB.FilePath object at ...` values appear
- confirm transform origin, rotation Z, Z-offset, identity/non-identity, duplicate link, and unloaded/unavailable flags are visible
- run `check linked model coordinates`, `are the links aligned`, `check Revit link transforms`, `what linked models are loaded`, `are any links unloaded`, and `coordinate health check`
- confirm deterministic answers, no Ollama timeout, no model mutation, and AI Agent remains plan-only

### Added local checks for 2026-04-22

- verify generic native schedule actions still resolve unchanged through the shared reviewed catalog
- verify ACO/BUNGE template actions resolve through explicit reviewed template recipes
- verify floor-specific and sheet schedules are excluded as canonical master sources
- verify level-targeted template actions block before creation when safe level retargeting cannot be established

### Added local checks for 2026-04-24

- verify product-family ACO pipe schedule and summary prompts resolve to separate structural reviewed actions
- verify exact coded level prompts such as 02_Ground Floor route to the intended template actions
- verify ACO pipe-fitting summary remains the only promoted ACO/template action based on current runtime evidence
- verify generic native schedule actions continue resolving as live_validated entries

### Added local checks for 2026-04-27

- verify `scan current project`, `summarize current project`, `ask AI Agent for a plan`, and `create Codex task brief` resolve through the shared reviewed catalog
- verify scanner code adds no new Transaction usage
- verify no reviewed execution lifecycle, ExternalEvent, create-sheet, create-3d-view, rename-view, or undo paths were modified
- live runtime validation remains required for collector accuracy and UI behavior

## 2026-04-20 Runtime Targets for Stable-Baseline UI Polish

### Dark mode

- validate that disabled buttons are clearly visually unavailable
- validate that enabled buttons remain readable and distinct from disabled controls
- check especially:
  - Show reviewed code
  - Approve & Run Code
  - Save as Approved Recipe
  - Undo Last Action
  - AI Agent control-strip buttons

### Header wording

- validate that close wording/tooltips are clear and do not imply special continuity behavior

### What was actually executed in this workspace pass

- local `UI.xaml` well-formedness validation
- local inspection of disabled-button resource/style definitions

### Live checks not executed in this pass

- all live validation targets listed above

## 2026-04-20 Runtime Targets for Stable-Baseline ModelMind Catalog Usability

### Catalog usability

- validate that users understand the existing catalog filtering behavior from the revised input tooltip/hint text
- validate that the Selected Action details panel is easier to read for larger reviewed catalog entries
- validate that Recent Prompts still read as shortcuts resolving back to canonical metadata

### What was actually executed in this workspace pass

- local `UI.xaml` well-formedness validation
- local inspection of the revised catalog hint/detail text

### Live checks not executed in this pass

- all live validation targets listed above

## 2026-04-20 Runtime Targets for Stability-Fenced Catalog Routing

### QA presets

- validate prompt variants:
  - `run the hvac qa preset`
  - `run piping preset`
  - `electrical coordination preset`
  - `run the bim qa preset`

### Category helpers

- validate deterministic reviewed routing for:
  - `select categories:doors, windows`
  - `count categories:doors, windows`
  - `list category:"Pipe Fittings"`

### What was actually executed in this workspace pass

- local compile/JSON sanity checks
- local shared-registry routing checks for the new alias/example variants

### Live checks not executed in this pass

- all live validation targets listed above
