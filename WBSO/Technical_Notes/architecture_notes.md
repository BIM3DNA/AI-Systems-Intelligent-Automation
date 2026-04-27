# Architecture Notes

## Project

AI Systems & Intelligent Automation

## Current Phase

2026 migration baseline + guarded product-architecture refactor

## Purpose

This file records the current architecture after restructuring the single pyRevit AI window around clearer product roles and safer local state.

## 2026-04-21 Stable-Baseline Catalog Usability Update

- added a dedicated ModelMind catalog filter surface in the right-hand catalog pane
- kept filtering read-only and separate from the main ModelMind prompt input
- kept grouping intact while exposing lightweight expand/collapse controls and match-status text
- improved Selected Action Details readability using existing reviewed metadata only
- left reviewed execution, window lifecycle, ExternalEvent behavior, timeout handling, and undo architecture unchanged

## 2026-04-21 Stable-Baseline Reviewed Schedule Update

- added deterministic reviewed schedule-creation handlers for MEP category schedules grouped by level/reference-level
- kept schedule generation inside the existing reviewed deterministic action model rather than introducing freeform code generation
- added template-first schedule duplication when an explicit or heuristically matched schedule template exists, with native schedule definition fallback
- kept execution architecture unchanged: no window-lifecycle, dispatch, timeout, create-sheet, create-3d-view, rename-active-view, or undo-architecture changes were made

## 2026-04-21 Schedule Promotion And Template Separation Update

- promoted only the schedule actions backed by real runtime evidence to `live_validated`
- moved generic native schedule actions into a dedicated `Schedules` catalog branch with subgroups for Pipes, Ducts, Electrical, and Bundles
- added separate template-only ACO schedule actions under `Schedules / Template-Based`
- kept generic native schedule actions separate from project-specific template-backed actions so template heuristics do not contaminate the native schedule family

## Current Product Architecture

### 1. Single pyRevit Entry Point

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- still acts as the pyRevit button entry point
- still owns the WPF window launch
- now delegates prompt catalog, approved recipe storage, theme persistence, and agent session semantics to support modules under `AI.extension/lib/`

### 2. Window Role Separation

- `Ollama Chat`: low-risk conversational help and prompt experimentation
- `ModelMind`: primary task surface for deterministic and semi-generative BIM work
- `AI Agent`: advanced plan/review/execute surface with modifying commands guarded and destructive tools off by default

### 3. Structured Prompt Layer

Structured prompt metadata now lives in:

- `AI.extension/lib/prompt_catalog.json`

Each prompt entry carries:

- `id`
- `title`
- `category`
- `role`
- `risk_level`
- `mode`
- `prompt_text`
- `enabled`

The ModelMind tree is now rebuilt from this structured source rather than from hardcoded class state.

### 4. Approved Recipe Layer

Reviewed generated code can now be persisted as an approved local recipe in:

- `AI.extension/lib/approved_recipes.json`

This separates:

- catalog prompts
- approved reviewed recipes
- transient generated code waiting for approval

### 5. Local UI State Layer

Theme choice is now stored locally through a local settings helper and persisted outside the transient session.

### 6. Agent Session Layer

The AI Agent tab now has explicit session semantics:

- `Run Agent` creates or refreshes a plan only
- `Execute Plan` runs the reviewed plan
- `Disable/Enable` toggles selected reviewed commands for the session
- `Reset Commands` clears plan/session command state
- `Undo Last Action` remains disabled because robust rollback/journaling is not implemented

## Architectural Consequence of This Pass

The window is still a single-shell pyRevit experience, but responsibilities are clearer:

- UI composition stays in the button script and XAML
- prompt and recipe state moved into reusable support assets
- agent orchestration remains lightweight, local, and safety-oriented

## What Was Actually Verified Locally

- `prompt_catalog.json` parses successfully
- `approved_recipes.json` parses successfully
- `UI.xaml` is well-formed XML
- the code was statically reviewed for IronPython-compatible syntax patterns in the edited areas

## What Was Not Yet Verified

- live pyRevit loading after this refactor
- live Revit execution of the new HVAC validation commands
- live Ollama response behavior after UI changes
- approved recipe persistence during a real pyRevit/Revit session

## 2026-04-08 Reviewed-Code Hardening Update

The ModelMind reviewed-code path is now hardened around a pyRevit compatibility gate.

### Added runtime guardrails

- reviewed code is validated before approval is enabled
- reviewed code is validated again immediately before execution
- unsupported Dynamo/DesignScript/runtime references are blocked before execution
- failed reviewed-code runs remain ineligible for approved-recipe storage
- approved-recipe save is now an explicit post-success action with required metadata

### New support component

- `AI.extension/lib/ai_reviewed_code.py`

This module detects unsupported reviewed-code patterns such as:

- `Autodesk.DesignScript`
- `DesignScript`
- `RevitServices`
- `RevitNodes`
- `ProtoGeometry`
- `from Revit import ...`
- Dynamo document/transaction context APIs

### Live findings recorded for this pass

The following are reported as live runtime findings for the current baseline before/through this pass:

- theme persistence works across relaunch
- Ollama Chat works in live runtime
- ModelMind deterministic tasks work
- failed reviewed-code runs are not added to approved recipes

### Still pending live validation after hardening

- confirm invalid DesignScript/Dynamo reviewed code is blocked before execution in live Revit
- confirm valid reviewed code executes and can then be saved as an approved recipe
- confirm the saved approved recipe appears immediately in the approved branch after reload

## 2026-04-09 UI and Deterministic Planner Polish Update

### Confirmed live baseline facts carried into this pass

- pyRevit AI tab loads
- button opens AI Workbench
- Ollama Chat works in live runtime
- theme persistence works across relaunch
- ModelMind deterministic `select all ducts` works in Snowdon Towers Sample HVAC
- reviewed create-sheet template validates as pyRevit-compatible
- reviewed create-sheet execution succeeds in live runtime
- approved recipe save dialog works
- approved recipe is stored and reloaded into the ModelMind tree

### Code/UI changes added in this pass

- top header/layout stabilized with title/subtitle left and controls pushed to the far right
- dark-mode readability improved for dropdowns, tree text, labels, and disabled actions
- reviewed-code output moved into a secondary show/hide panel instead of always dumping raw code into the main history
- AI Agent narrowed to a deterministic reviewed-planner with a small supported command set
- added deterministic planner support for:
  - `select all ducts`
  - `count selected ducts`
  - `count all ducts in active view`
  - `list ducts in active view`
  - `find unconnected fittings`
  - `report elements without system assignment`

### Still pending live validation after this polish pass

- AI Agent handling of the new deterministic duct-count/list cases
- top-right header alignment verification in live Revit
- dark-mode dropdown readability verification in live Revit
- dark-mode tree readability verification in live Revit
- disabled-button readability verification in live Revit

## 2026-04-09 Provider-Backed Reviewed Planner Update

### Purpose of this pass

- finish the ModelMind layout polish
- wire AI Agent to a real provider-backed planning path
- keep execution deterministic and reviewed inside pyRevit

### Architecture changes added

- ModelMind input now spans most of the available width and its action buttons now sit below the input area
- reviewed code remains secondary through the existing show/hide reviewed-code panel
- AI Agent now supports two planning modes:
  - local deterministic planner
  - OpenAI-backed intent normalization planner
- the cloud planner only normalizes requests into the existing supported deterministic/reviewed action set
- cloud output does not execute as raw code
- reviewed execution still goes through the local command registry or the reviewed `create sheet` template path

### Provider security boundary

- `OPENAI_API_KEY` is read from environment only
- no API key is stored in repo-local files, logs, JSON artifacts, UI text, or WBSO evidence
- if the key is missing, cloud planning is unavailable and the UI falls back to local planning guidance
- if the cloud request fails, the UI reports the failure precisely and local planning remains available

### Current validation position for this pass

Locally verified:

- helper/service modules compile under CPython
- `UI.xaml` is well-formed XML after the latest layout/provider edits
- prompt and approved-recipe JSON assets still parse

Not yet live-validated after this pass:

- ModelMind layout polish in live Revit
- AI Agent local planner handling of the supported deterministic cases after this provider wiring
- AI Agent cloud planning normalization with a valid environment key
- missing-key UI state in live Revit
- cloud request failure handling in live Revit

## 2026-04-10 Provider Diagnostics Refinement

### Problem addressed in this pass

Current live findings reported that:

- `OPENAI_API_KEY` exists in Windows user environment variables
- AI Agent still showed both:
  - `Cloud unavailable: request failed`
  - `Set OPENAI_API_KEY in the environment to enable cloud planning.`
- that combined messaging was incorrect when the key was already present

### Architectural changes added

- added a structured provider health state model across the OpenAI service layer, the subprocess bridge, and the pyRevit UI
- provider diagnostics now distinguish:
  - `missing_key`
  - `key_present` via explicit key-state diagnostics
  - `auth_failed`
  - `request_failed`
  - `network_failed`
  - `provider_ready`
  - `local_only`
- the provider layer now reports:
  - key present: yes/no
  - provider reachable: yes/no
  - last error category
- missing-key guidance is now only shown when the actual state is `missing_key`

### Planner UX consequence

- the AI Agent provider line is now intended to report the actual planner condition instead of collapsing cloud failures into a generic missing-key-like state
- when cloud planning fails, the agent falls back to local deterministic planning where possible
- unsupported planner requests now return clearer reviewed deterministic scope guidance instead of only `Unsupported request.`

### Near-term candidate action recorded

- `report total volume of selected ducts in cubic meters`

This candidate is recorded for near-term expansion only. It is not yet implemented as an active reviewed deterministic action.

### Validation position for this pass

Implemented and locally checked:

- updated provider/service modules compile
- updated prompt catalog parses

Not yet live-validated after the fix:

- key-present state no longer showing the missing-key message in live Revit
- cloud failure showing the correct error category in live Revit
- local planner fallback after cloud failure in live Revit
- improved unsupported schedule/quantity guidance in live Revit

## 2026-04-10 Cloud Planner Self-Test Update

### What was added

- a cloud planner self-test path was added through the same OpenAI subprocess service route used by AI Agent planning
- the self-test reports, without exposing secrets:
  - `env_key_present`
  - `openai_module_importable`
  - `client_init_ok`
  - `test_request_ok`
  - `failure_category`
  - `failure_message_safe`
  - runtime interpreter identity

### Exact workspace result observed

From the current workspace self-test:

- `env_key_present: yes`
- `openai_module_importable: no`
- `client_init_ok: no`
- `test_request_ok: no`
- `failure_category: missing_openai_module`
- `runtime_executable: C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python313\\python.exe`

### Architectural consequence

The current evidence points to a runtime dependency visibility issue in the Python interpreter used by the cloud planner service path, not to a missing `OPENAI_API_KEY` in that same interpreter.

## 2026-04-10 Responses API Planner Update

### Service-path change

- the OpenAI cloud planner path now uses the OpenAI Python client through the Responses API
- the provider probe/self-test now also uses a minimal Responses API request instead of a model-retrieve probe
- cloud output remains restricted to reviewed supported-action normalization only

### Verified current result

After installing and upgrading the OpenAI Python client in the actual service runtime:

- `env_key_present: yes`
- `openai_module_importable: yes`
- `client_init_ok: yes`
- `test_request_ok: no`
- `failure_category: network_failed`

This means the Responses API path is now wired and dependency-visible in the actual service interpreter. The current blocker has narrowed to provider network/API reachability.

## 2026-04-10 Shared Reviewed Action Registry Update

### Architecture change

- ModelMind and AI Agent now read from one shared reviewed action registry
- ModelMind remains the visible action/recipe library
- AI Agent now acts as planner/router over that same reviewed action registry
- approved recipes remain a distinct ModelMind branch and are not the planner source-of-truth action inventory

### Shared registry metadata now used

- `id`
- `title`
- `category`
- `discipline`
- `role`
- `risk_level`
- `scope_type`
- `planner_aliases`
- `deterministic_handler`
- `requires_confirmation`
- `enabled`

### Current implementation result

- shared reviewed actions loaded from registry: `23`
- AI Agent local planner now matches from registry aliases instead of a separate hardcoded action list

### Validation position

Locally verified:

- shared reviewed actions load from the registry
- AI Agent planner normalizes example prompts against that same registry

Not yet live-validated in Revit after this pass:

- shared ModelMind tree rendering for the expanded MEP set
- AI Agent execution for the newly added MEP reviewed actions
- approved recipe save/load continuity after the registry refactor

## 2026-04-13 Expanded Reviewed MEP Action Pass

### Confirmed live baseline facts carried into this pass

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

### Known live issues carried into this pass

- `gemma3:27b` appears unstable/crashes in runtime, while `phi3:mini` is stable
- `report total selected duct volume in cubic meters` returned `0.000 m³` and required investigation
- cloud/OpenAI planning remains non-blocking and is not the focus of this pass

### Code changes added in this pass

- expanded the shared reviewed registry to cover additional piping, electrical, QA/BIM, and low-risk write actions
- added missing pipe active-view reviewed actions
- added electrical active-view listing action
- improved local alias coverage for practical BIM phrasing
- added a lightweight model/runtime note that keeps `phi3:mini` as the stable recommended fallback when heavier local models behave unstably
- hardened the duct-volume action so it:
  - uses direct volume when available
  - derives volume from section dimensions and length when possible
  - returns an honest unresolved-data note when volume cannot be determined reliably

### Current local verification for this pass

- shared reviewed actions loaded from registry: `26`
- AI Agent local planner matched shared aliases for:
  - `duct length`
  - `total selected duct volume`
  - `pipes without system`
  - `count pipes in active view`
  - `electrical devices in active view`
  - `create a 3d view from this selection`

### Still pending live validation after this pass

- duct-volume action behavior on Snowdon Towers Sample HVAC after the robustness fix
- new pipe active-view actions in ModelMind and AI Agent
- new electrical and QA/BIM reviewed actions in live Revit
- 3D-view creation action in live Revit

## 2026-04-14 Shared Catalog Visibility and Resize Pass

This pass focused on usability and governance, not on adding a second AI Agent catalog surface.

### Architectural changes

- kept one shared reviewed registry only
- changed ModelMind tree rendering so it now shows the shared reviewed action catalog by governed top-level domains:
  - HVAC
  - Piping
  - Electrical
  - QA / BIM
  - Views / Sheets
- kept aliases and example prompts as metadata on canonical reviewed actions instead of creating duplicate tree leaves
- kept Approved Recipes in a distinct branch and grouped them by domain where possible
- kept AI Agent as a planner/router over the same shared reviewed actions without adding a second catalog tree

### UI/runtime architecture changes

- made the AI Workbench window structurally resizable with persisted width, height, and position
- refit ModelMind to use a resizable split layout with:
  - expanding output/history area
  - expanding reviewed catalog tree
  - action-details panel for canonical prompt, aliases/examples, role, risk, and validation state
  - wrapped bottom action buttons under the input field to avoid overlap on smaller sizes
- added a lightweight Recent Prompts branch stored locally for convenience only; it is not part of the canonical reviewed catalog

### Local verification for this pass

- shared reviewed actions exposed in the governed ModelMind tree shape:
  - HVAC
  - Piping
  - Electrical
  - QA / BIM
  - Views / Sheets
  - Recent Prompts
  - Approved Recipes
- shared reviewed actions available from registry: `26`
- AI Agent supported-action view also reflects the same `26` shared reviewed actions
- `UI.xaml` is well-formed after the resize/layout refactor

### Still pending live validation after this pass

- live Revit confirmation that the new resizable layout behaves correctly when the window is stretched and reduced
- live Revit confirmation that the governed ModelMind tree renders correctly with grouped reviewed actions and approved-recipe domains
- live Revit confirmation that AI Agent supported-action summaries remain correct in the runtime UI after this refactor

## 2026-04-14 AI Agent Plan-Step Control Pass

This pass did not expand the reviewed action set. It focused only on AI Agent queue usability and control-state logic.

### Root cause

- the bottom AI Agent selector had been overloaded with two meanings:
  - current reviewed plan steps
  - shared supported reviewed actions
- the adjacent buttons (`Disable/Enable`, `Reset Commands`, `Execute Plan`) only operate on current plan steps, not on the whole supported-action catalog
- when no plan existed, the selector still showed supported actions, which made the control look actionable while the buttons correctly remained disabled

### Architectural behavior after this pass

- the bottom selector now represents only the current reviewed plan steps
- supported reviewed actions remain visible separately as informational text only
- AI Agent still uses the shared reviewed registry and still does not introduce a second catalog tree
- Approved Recipes remain ModelMind-centered and were not added as a new Agent queue source in this pass

### Stateful plan-step fields

Each queued plan step now carries explicit runtime state:

- `id`
- `title`
- `role` (`read_only` or `modifying`)
- `risk`
- `enabled`
- `executed`
- `blocked_reason`
- `undo_available`

### Local verification for this pass

- a local deterministic plan for `count selected ducts` now produces a plan step with the explicit queue-state fields above
- toggling that step off changes the session state so `has_enabled_steps` becomes false
- `UI.xaml` remains well-formed after the Agent control relabel/state additions

### Still pending live validation after this pass

- live confirmation that the selected plan step now activates the adjacent buttons as intended
- live confirmation that `Execute Plan` availability messaging matches destructive-tools gating correctly

## 2026-04-14 Action-Specific Undo Pass

This pass does not add generic undo. It adds real reversible undo only for the already validated modifying action `Create 3D view from current selection/context`.

### Undo model added

- session-level undo context is now stored only for the last successfully executed modifying reviewed action
- undo context is structured and currently records:
  - `action_id`
  - `action_title`
  - `role`
  - `document_identity`
  - `created_element_ids`
  - `created_view_id`
  - `created_view_name`
  - `timestamp_utc`
  - `session_marker`
  - `undo_available`

### First truly undoable action

- `Create 3D view from current selection/context`

Forward execution now records the created 3D view identifier after a successful transaction commit. Undo deletes that recorded view in a new transaction if:

- the undo context still exists
- the action is the supported reversible create-3D-view action
- the document identity still matches
- the created view still exists

### Session behavior

- read-only actions do not create undo context
- blocked modifying actions do not create undo context
- `Reset Commands` clears the current undo context to avoid stale reversible state from surviving a session reset
- undo context is cleared after a successful undo

### Local verification for this pass

- blocked modifying action with destructive tools off: no undo context created
- successful modifying action with destructive tools on: undo context created
- `reset()` clears undo context
- successful read-only execution does not create undo context

### Still pending live validation after this pass

- live confirmation that create-3D-view undo deletes the created view in Revit
- live confirmation of honest failure cases when the created view is already gone or document context changes

## 2026-04-15 Create-Sheet Undo Extension Pass

This pass extends the existing reviewed-action undo framework from `Create 3D view from current selection/context` to `Create sheet`.

### Undo-context extension

- `run_code_in_revit` now infers and returns structured undo context when a reviewed create-sheet execution succeeds
- create-sheet undo context now records:
  - `action_id`
  - `action_title`
  - `role`
  - `document_identity`
  - `created_sheet_id`
  - `created_sheet_number`
  - `created_sheet_name`
  - `timestamp_utc`
  - `session_marker`
  - `undo_available`

### Shared modifying behavior

The same last-action undo context is now populated consistently when create sheet succeeds through:

- AI Agent reviewed plan execution
- ModelMind reviewed execution
- approved recipe execution

The framework still keeps only one current-session undo context and does not introduce a history stack.

### First truly undoable modifying actions after this pass

- `Create 3D view from current selection/context`
- `Create sheet`

### Session behavior preserved

- read-only actions remain non-undoable
- destructive-tools gating remains unchanged for forward modifying execution
- `Reset Commands` still clears undo context as the safe session behavior

### Local verification for this pass

- successful create-sheet execution path creates undo context structurally
- create-sheet undo context clears on reset
- create-3D-view undo path still creates undo context structurally
- read-only execution still creates no undo context
- approved-recipe/create-sheet path is wired through the same undo-context application helper

### Still pending live validation after this pass

- actual delete-on-undo behavior for the created sheet in Revit
- honest runtime failure handling for missing/dependent/deleted sheets
- approved-recipe create-sheet undo behavior in the live runtime

## 2026-04-15 QA/BIM Hardening Pass

This pass did not change the catalog architecture or reviewed action inventory. It hardened the existing QA/BIM read-only actions for runtime trustworthiness and better BIM-coordination output.

### Actions hardened

- `report selected elements by category`
- `report selected elements by type`
- `report missing key parameters from selected elements`
- `health check of active view for supported MEP categories`

### Output improvements

- total selected/inspected counts
- grouped breakdowns
- sample element ids
- explicit truncation (`showing first 20`)
- explicit no-selection / nothing-missing notes

### Parameter-inspection changes

The reviewed baseline now prefers a smaller production-oriented check set:

- `Mark`
- `Comments`
- `Family and Type`
- `System assignment` where actually applicable
- `Electrical circuit/system` where actually applicable

Irrelevant categories are skipped instead of being counted as missing for nonsensical parameters.

### Health-check changes

The active-view health check now summarizes:

- ducts count
- duct fittings count
- pipes count
- pipe fittings count
- electrical fixtures count
- electrical equipment count
- elements without system assignment where supported
- unconnected fitting findings where supported
- missing electrical circuit/system info where supported

### Local verification for this pass

- QA/BIM handler blocks were updated without syntax regressions
- `UI.xaml` remains well-formed
- registry/catalog architecture remains unchanged; the hardened actions stay under the shared QA / BIM branch

### Still pending live validation after this pass

- runtime usefulness and correctness of the hardened QA/BIM summaries on real project selections/views
- parameter applicability behavior across mixed-discipline live selections

## 2026-04-15 QA/BIM Scope Messaging and Alias Pass

This pass did not add QA/BIM actions. It clarified scope and improved natural-language normalization for the existing QA/BIM reviewed actions.

### Scope clarification

- selected-element QA/BIM actions now explicitly state:
  - `Selection scope: active document only`
- empty-selection responses now explicitly state:
  - no selected elements found in the active Revit document
  - selections in other open Revit projects are not included
- active-view QA/BIM actions now explicitly state:
  - `View scope: active view in active document`

### Alias improvements

The shared reviewed catalog now includes additional metadata aliases/examples for:

- selected elements by category
- selected elements by type
- missing key parameters from selection
- health check of active view for supported MEP categories

These remain metadata only and do not create duplicate ModelMind tree nodes.

### Local verification for this pass

- new QA/BIM alias prompts normalize to the intended reviewed actions through the shared planner/catalog path
- scope messaging lines are present in the reviewed handler output
- the shared catalog metadata now correctly advertises:
  - `selection` scope for selected-element QA/BIM actions
  - `active_view` scope for the health check action

### Still pending live validation after this pass

- live confirmation that the new scope wording reduces confusion when users have selections in other open Revit projects
- live confirmation that the added QA/BIM aliases are sufficient for common natural-language prompts

## 2026-04-15 QA/BIM Category Grouping Defect Fix

This pass did not add reviewed actions or change scope rules. It fixes one output defect in the existing QA/BIM action `report selected elements by category`.

### Root cause

- the category report grouped by `_category_name(elem)`
- `_category_name(elem)` depended on `get_elem_name(category)`
- `get_elem_name()` attempted `elem.Document.GetElement(elem.GetTypeId())` before checking whether the object was a real Revit `Element`
- Revit `Category` objects do not support that path reliably, so the helper fell into its blanket exception handler and returned the literal string `(err)`
- that `(err)` string then appeared as the rendered category bucket, e.g. `(err): 5 | sample ids: ...`

### Fix

- hardened `get_elem_name()` so it:
  - returns `Name` first when present
  - only attempts `Document/GetTypeId` when those members actually exist
  - falls back safely without emitting `(err)` for valid category objects
- hardened the category report so actual grouping exceptions now return an honest message instead of rendering a fake category bucket
- missing categories now render as:
  - `<No Category>`

### Still pending live validation after this pass

- live confirmation that category breakdowns now render as real Revit category names on non-empty active selections

## 2026-04-15 QA/BIM Validation Metadata Promotion and Context UX Pass

This pass did not add reviewed actions or change planner architecture. It aligned the shared reviewed catalog with confirmed runtime evidence and improved small selection-context cues for the existing QA/BIM actions.

### Metadata promotion

The following reviewed QA/BIM actions are now explicitly marked `live_validated` in the shared reviewed catalog:

- `report selected elements by category`
- `report selected elements by type`
- `report missing key parameters from selected elements`
- `health check of active view for supported MEP categories`

Other reviewed actions keep their previous validation state unless they already had equivalent live evidence.

### UX hardening

- selection-based QA/BIM outputs now include compact context lines for:
  - active document
  - active view
  - current selection count
- the active-view health-check output now includes the active document line as well
- Recent Prompts now resolve back to canonical reviewed-action metadata for the Selected Action panel

### Still pending live validation after this pass

- runtime confirmation of the promoted validation-state display in the Selected Action panel
- runtime confirmation of the compact context lines and canonical recent-prompt details behavior

## 2026-04-16 Reviewed Production-Assistant Expansion Pass

This pass expands the validated reviewed MEP/QA baseline into a broader reviewed production-assistant surface while preserving the shared-catalog architecture:

- ModelMind remains the canonical reviewed catalog and approved-recipe surface
- AI Agent remains the planner/router/executor over the same shared reviewed actions and presets
- no separate AI Agent catalog tree was added

### Structural additions completed

- discipline QA presets implemented as canonical reviewed multi-step presets:
  - HVAC QA preset
  - Piping QA preset
  - Electrical QA preset
  - Coordination / BIM QA preset
- new native deterministic reviewed actions added for:
  - split selected pipes
  - duplicate reporting and duplicate removal
  - categories list + id
  - select/count/list all elements of category
  - room/space checks
  - rename active view
  - align selected tags
  - total length for selected linear MEP elements
  - total length in active view for supported linear MEP categories

### Governance notes

- all new items default to `structural_only`
- destructive-tools gating remains in place for new modifying actions
- no fake undo was added for actions without a safe reversible model
- real undo was added only where practical for the new modifying set:
  - rename active view

### Deliberately deferred items

- quick dimension selected elements
- add couplings to selected pipes / by interval
- batch rename selected views

These were left out because a safe first-pass deterministic implementation was not yet defensible within this pass.

### External-tool reuse check

- local repository search did not expose reusable native source for the requested split/duplicate/room-space/tag-alignment helpers
- native deterministic reviewed equivalents were implemented instead of brittle button-click bridges

### Still pending live validation after this pass

- all new presets and actions added in this pass remain pending live Revit validation

## 2026-04-19 Preset Hardening and Scope-Governance Pass

This pass does not expand broad feature scope. It hardens preset semantics, selection safety, category disambiguation, and shared undo consistency.

### Preset governance changes

- preset execution now snapshots the current selection before execution
- each preset step can declare explicit scope behavior:
  - `use_current_selection`
  - `use_generated_selection`
  - `use_active_view`
  - `restore_previous_selection_after_step`
- preset-local generated working selections are now used where selected-element actions would otherwise depend on accidental UI state
- the original selection is restored after preset execution

### Presets hardened in this pass

- HVAC QA preset
- Piping QA preset
- Electrical QA preset
- Coordination / BIM QA preset

### Additional governance changes

- category resolution now prefers physical model categories over annotation/tag categories
- exact category syntax is supported for the generic category helper actions:
  - `category:walls`
  - `category:\"Pipe Fittings\"`
  - `categories:doors,windows`
- ModelMind now exposes the same honest Undo Last Action surface as AI Agent
- duplicate actions remain `structural_only`; output now explicitly says `Exact duplicate rule`

### Still pending live validation after this pass

- all hardened preset/runtime behaviors added in this pass

## 2026-04-20 Stability-Fenced Catalog Routing Hardening

This pass intentionally avoids all window lifecycle, dispatcher, ExternalEvent, timeout, and reviewed modify execution boundaries.

### Safe scope only

- normalize reviewed prompt matching in the shared catalog loader
- expand metadata-only aliases/examples for already validated QA presets and generic category helpers
- keep the stable reviewed execution architecture unchanged

### What changed

- added normalized prompt matching for:
  - repeated whitespace
  - comma spacing in multi-category prompts
  - exact `category:` / `categories:` syntax formatting
- expanded metadata-only aliases/examples for:
  - HVAC QA preset
  - Piping QA preset
  - Electrical QA preset
  - Coordination / BIM QA preset
  - generic select/count/list category helpers

### Explicitly unchanged

- Workbench launch/bootstrap flow
- modal/modeless behavior
- ExternalEvent lifecycle/state management
- create sheet / create 3D view / rename active view execution paths
- shared undo architecture

## 2026-04-20 Stable-Baseline UI Polish

This pass is styling/text only on the restored stable baseline.

### Safe scope only

- improve button-state readability in dark mode
- clarify close-button wording/tooltips
- preserve the current layout and execution behavior

### What changed

- added a shared disabled-button style in `UI.xaml`
- disabled buttons now use:
  - muted gray-blue text
  - subdued dark background
  - subdued border
- added small shared button padding for clearer text spacing
- clarified the close-button tooltip so it does not imply special continuity behavior

### Explicitly unchanged

- `script.py`
- window lifecycle
- modal/modeless behavior
- ExternalEvent / reviewed request dispatch
- create sheet / create 3D view / rename active view execution
- shared undo behavior

## 2026-04-20 Stable-Baseline ModelMind Catalog Usability

This pass remains UI/catalog-only and does not touch reviewed execution behavior.

### Safe scope only

- clarify how the existing ModelMind catalog filter already works
- improve Selected Action panel readability
- preserve Recent Prompts semantics

### What changed

- updated the main ModelMind input tooltip to state that it already filters the catalog by titles, aliases, and examples while typing
- updated the catalog hint text to explain the existing filter behavior and the Recent Prompts to canonical metadata relationship
- renamed the details group to `Selected Action Details`
- clarified the details meta placeholder text
- increased the details body height slightly for better readability

### Explicitly unchanged

- no dedicated new search control was added because that would require script wiring
- no favorites/pinning branch was added because that would require new UI/state plumbing beyond this safe pass
- all execution/lifecycle/dispatcher behavior remains unchanged

## 2026-04-22 BUNGE Template Recipe Hardening

- replaced heuristic ACO template-source ranking with explicit reviewed BUNGE/ACO recipe mappings for the known project schedule family
- template source selection now blocks floor-specific, sheet, AI-generated, and previously generated ACO output schedules from acting as canonical masters
- generic native schedule actions were left unchanged; only template-backed source selection and exact level retarget validation were tightened

## 2026-04-24 ACO/Bunge Product-Family Schedule Recipes

- added separate structural reviewed ACO pipe product-family template actions for 1.4301 single socket, 1.4404 single socket, and 1.4404 double socket sources
- generic all-ACO pipe template actions remain blocked when no neutral all-pipe master exists
- pipe-fitting level retargeting now uses stricter level-name resolution and normalized Level-field matching before creating schedules

## 2026-04-27 Read-Only Project Context Scanner

- added a deterministic read-only Revit project context scanner with bootstrap and standard scan depths
- scanner output is cached in the AI Workbench session for Ollama Chat grounding, AI Agent reviewed-plan suggestions, and Codex task brief generation
- no model transactions, reviewed execution lifecycle changes, ExternalEvent changes, or free-form AI Agent execution paths were added

## 2026-04-27 Project Context UX and Deterministic Q&A Hardening

- expanded the cached Project Context tree so names/status for views, sheets, links, imports, schedules, warnings, issues, and suggested reviewed actions are visible without sending prompts to Ollama
- added deterministic fast-path answers for common structured project-context questions such as schedules, CAD/imports, links, warnings, categories, and first checks
- kept the scanner and context Q&A read-only; no transactions, lifecycle changes, reviewed dispatch changes, or schedule/template creation behavior changes were introduced

## 2026-04-27 Project Context Cache Consistency Fix

- centralized Project Context cache reads through a latest-context helper so the tree, deterministic chat answers, quick actions, AI Agent plan, and Codex brief use the same newest scan snapshot
- standard project scans replace bootstrap context for downstream schedule/warning summaries
- Revit link display now prefers human-readable link names/status/path text instead of raw API object representations
