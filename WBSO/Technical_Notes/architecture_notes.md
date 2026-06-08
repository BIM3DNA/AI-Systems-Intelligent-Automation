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

## 2026-04-28 Project Context Chat Readability

- improved Ollama Chat transcript readability using plain-text separators rather than changing control architecture
- made deterministic context answers count-first and sectioned for schedules, CAD/imports, links, issues, first checks, and project summary output
- preserved read-only scanner behavior and did not touch reviewed execution, lifecycle, undo, or model mutation paths

## 2026-04-28 Linked Model Coordinate Health

- extended the read-only Project Context scanner with linked-model coordinate health metadata for host project position and RevitLinkInstance transform summaries
- added conservative flags for unloaded links, non-identity transforms, Z offsets, rotation, duplicate link instances, and unknown coordinate state
- added deterministic context-answer routing and a structural reviewed catalog action without changing reviewed execution, lifecycle, undo, or link/model mutation behavior

## 2026-05-06 AI-AGENT-002 Guided Project Startup Plan

AI-AGENT-002 adds a guided project-startup planning layer on top of cached Project Context and Project Onboarding data.

### Architectural role

- consumes the latest cached Project Context snapshot
- consumes the deterministic Project Onboarding Checklist
- formats a plan for the AI Agent and deterministic chat prompts
- keeps the Agent plan-only
- does not execute actions automatically
- preserves reviewed/catalog governance for any later Execute Plan action

### Plan structure

- Required read-only diagnostics
- Optional project health checks
- Reviewed automation candidates
- Blocked / not recommended actions

### Governance boundary

- no model mutation is introduced
- no free-form code execution is introduced
- Execute Plan remains governed by the existing reviewed/catalog approval flow
- this feature converts observed context into safer planning order; it is not an autonomous execution path

## 2026-05-07 MEP-RO-001 Read-Only BIM/QA Selection Action Pack

MEP-RO-001 is intended to provide cross-discipline read-only selection reporting through ModelMind and deterministic AI Workbench routing.

### Intended reports

- report selected elements by category
- report selected elements by type
- count selected elements
- health check selected elements
- report missing parameters from selection

### Required architecture

- selection-report prompts must route deterministically before Ollama fallback
- handlers must read the current live Revit selection at execution time using `uidoc.Selection.GetElementIds()`
- cached Project Context selection data is insufficient because users may select elements after `Scan Project`
- handlers must remain read-only and must not create, delete, modify, or parameter-write model data

### Current status

- structural/hardened implementation exists in the runtime branch
- live runtime validation on 2026-05-07 failed before Revit selection reports executed
- failure cause: typed prompts fell through to Ollama and returned generic non-Revit prose
- next work should be a deterministic routing and live-selection hotfix, not new feature expansion

## 2026-05-07 MEP-RO-001 Routing/Live Selection Hotfix

MEP-RO-001 selection reports are now documented as deterministic read-only BIM/QA tools after the routing/live-selection hotfix validation.

### Hotfix architecture

- known selection-report prompts route before Ollama fallback
- selection handlers read the current live Revit selection at execution time through `uidoc.Selection.GetElementIds()`
- `doc.GetElement(id)` is used to resolve selected elements safely
- reports remain read-only and do not create, delete, parameter-write, or otherwise modify model data

### Report content

- category counts
- type/family-type counts
- level and reference-level samples where available
- sample ElementIds
- selection health warnings such as mixed categories or missing level/reference-level data
- missing parameter summaries
- safety notes stating that no model data is modified

### Traceability

The earlier 2026-05-07 validation failure remains part of the evidence trail. The correct narrative is:

1. the structural selection action pack existed and was hardened
2. initial runtime validation failed because typed prompts fell through to Ollama
3. a narrow `script.py` hotfix added deterministic routing and confirmed live selection handling
4. runtime retest passed across no-selection, piping, HVAC, and electrical selections

Status: runtime validated after hotfix.

## 2026-05-07 MEP-RO-002 and MEP-RO-003 Read-Only MEP QA Layers

MEP-RO-001 established runtime-validated selected-element BIM/QA reporting from the current live Revit selection. MEP-RO-002 and MEP-RO-003 extend the same deterministic read-only pattern to active-view MEP reporting and system assignment/classification diagnostics.

### MEP-RO-002 architectural role

- adds deterministic active-view read-only MEP reports
- reads the live active view at execution time
- reports active-view MEP category/type/level/sample ElementId summaries
- supports no-selection workflows by inspecting visible MEP content in the active document
- caps large active-view inspections for readability/performance

### MEP-RO-003 architectural role

- adds deterministic system assignment/classification QA for selected elements and active-view MEP elements
- reads live selection for selection scope
- reads live active-view elements for active-view scope
- classifies readable/assigned, missing/empty, unavailable/not applicable, and unknown/error system states
- uses safe parameter/property reads only
- does not use connector traversal or geometry extraction

### Governance boundary

- known MEP-RO-002 and MEP-RO-003 prompts route deterministically before Ollama fallback
- active document only
- no linked-document scan
- no model mutation
- no parameter writes
- no tags, schedules, views, sheets, systems, circuits, or connectors are created or edited
- capped inspection prevents heavy model scans

## 2026-05-07 MEP-RO-004 Discipline-Specific Read-Only QA Rules

MEP-RO-004 builds on the validated read-only MEP stack:

- MEP-RO-001 selected-element reports
- MEP-RO-002 active-view MEP reports
- MEP-RO-003 system assignment, classification, and circuit reports
- MEP-RO-004 discipline-specific QA rule reports

### Architectural role

- introduces a small deterministic rule evaluator for MEP QA checks
- evaluates selected elements and active-view elements using live Revit state at execution time
- uses active-document data only
- does not scan linked documents
- does not use connector traversal
- does not use geometry extraction
- does not mutate model data or write parameters
- returns pass, fail, unavailable/not applicable, and error classifications
- caps large active-view inspections for readability and performance

### Rule coverage

- common MEP identity checks: Mark, Comments, Family and Type, Level/reference level, system assignment where applicable, and category readability
- piping checks: system assignment, level, size/diameter, Mark, Comments, pipe slope where applicable, and pipe length where applicable
- HVAC checks: system assignment, level, size, flow where applicable, Mark, Comments, and Family and Type
- electrical checks: circuit/system, panel, circuit number, level, Mark, Comments, Family and Type, and conduit/cable tray size where applicable

### Hotfix trace

Initial runtime validation showed that common identity rules and discipline-specific identity rules could duplicate the same logical Mark/Comments failures. The hotfix suppresses duplicate COMMON-001 and COMMON-002 failures where discipline-specific Mark/Comments rules exist for the same element, and deduplicates grouped sample ElementIds. The reporting note now clarifies that counts represent rule evaluations while sample ElementIds are deduplicated.

Status: runtime validated after duplicate-rule aggregation hotfix.

## 2026-05-14 MEP-RO-005 Exportable QA Evidence Snapshots

MEP-RO-005 builds on the validated read-only MEP QA stack:

- MEP-RO-001 selected-element reports
- MEP-RO-002 active-view MEP reports
- MEP-RO-003 system assignment, classification, and circuit reports
- MEP-RO-004 discipline-specific QA rule reports
- MEP-RO-005 exportable QA evidence snapshots

### Architectural role

- adds a deterministic read-only export layer for the latest accepted AI Workbench diagnostic/QA report
- keeps a session-local latest deterministic report state
- routes export prompts deterministically before Ollama fallback
- exports only accepted deterministic report headers
- rejects generic Ollama outputs as deterministic QA evidence
- writes timestamped evidence snapshots under the Desktop Results path, with a Temp fallback
- generates `report.md`, `report.txt`, `metadata.json`, and `artifact_manifest.txt`

### Metadata and safety model

`metadata.json` records:

- `deterministic_route: true`
- `read_only: true`
- `model_modified: false`
- `linked_documents_scanned: false`
- `connector_traversal_used: false`
- `geometry_extraction_used: false`
- source prompt, source report header, document title, active view, export folder, and generated files

The export action is filesystem-only. It does not mutate the Revit model, write parameters, scan linked-document internals, traverse connectors, or extract geometry.

Status: runtime validated.

## 2026-05-18 MEP-WR-001 Split Selected Pipes Dry Run

MEP-WR-001 adds a deterministic read-only dry-run layer after MEP-ACT-001 and before any future reviewed apply feature.

### Architectural role

- routes known split dry-run prompts deterministically before Ollama fallback
- reads current live selected elements only in the active document
- calculates non-executable midpoint candidate data for eligible straight pipes
- reports candidate split point, estimated segment A/B lengths, pipe type, level, system, diameter/size, and slope
- classifies skipped elements into pipe fittings, pipe accessories, non-pipes, pinned pipes, grouped pipes, design-option pipes, unreadable curves, unbounded curves, unsupported curve types, too-short pipes, near-vertical pipes, unreadable endpoints, and calculation errors
- records warnings for missing/unreadable level, system, diameter/size, and slope
- exposes `[SPLIT SELECTED PIPES DRY RUN]` as an exportable deterministic header for MEP-RO-005/006

MEP-WR-001 does not call `PlumbingUtils.BreakCurve`, open transactions, split pipes, move fittings, modify systems, traverse connectors, extract geometry, scan linked documents, write parameters, or mutate the Revit model.

Status: runtime validated.

## 2026-05-18 MEP-ACT-002 Reviewed Proposal / Dry-Run Confirmation Guard

MEP-ACT-002 adds a deterministic confirmation/readiness guard after reviewed proposals and dry-runs, and before any future reviewed apply action.

### Architectural role

- routes known confirmation/status prompts deterministically before Ollama fallback
- inspects session-local source state from MEP-WR-001 split dry-runs, MEP-ACT-001 reviewed proposals, or accepted deterministic report headers
- detects `[SPLIT SELECTED PIPES DRY RUN]` and `[REVIEWED ACTION PROPOSAL]`
- blocks confirm/apply/execute prompts because MEP-WR-002 reviewed apply is not implemented
- reports `execution_available: false` and `execution_performed: false`
- exposes `[REVIEWED ACTION CONFIRMATION GUARD]` as an exportable deterministic header for MEP-RO-005/006
- includes a report-scope hotfix so confirmation guard exports store `session-local reviewed action state / active document only`

MEP-ACT-002 is confirmation-governance only. It opens no transaction and performs no pipe split, action apply, parameter write, connector traversal, geometry extraction, linked-document scan, or Revit model mutation.

Status: runtime validated after report-scope metadata hotfix.

## 2026-05-19 MEP-WR-002 Split Selected Pipes Rollback Test

MEP-WR-002 validates whether split candidates from MEP-WR-001 can be passed to Revit's pipe split API inside a rollback-only transaction group.

### Architectural role

- routes known rollback-test prompts deterministically before Ollama fallback
- requires latest `[SPLIT SELECTED PIPES DRY RUN]` state from MEP-WR-001
- requires explicit `ROLLBACK-TEST-OK` before opening a transaction
- validates candidate pipe ids, pipe category, bounded `LocationCurve`, candidate point, minimum segment length, pinned/group/design-option state, and near-vertical status before probing
- opens `TransactionGroup` and inner `Transaction` only for rollback-test execution
- calls `PlumbingUtils.BreakCurve` only inside the rollback-test transaction group
- commits the inner transaction only to inspect temporary results
- always rolls back the `TransactionGroup`
- caps rollback-test processing to 5 candidates
- verifies original pipe ids still resolve, temporary new pipe ids no longer resolve, and original lengths are restored within tolerance
- exposes `[SPLIT SELECTED PIPES ROLLBACK TEST]` as an exportable deterministic header for MEP-RO-005/006

The initial tokenized command `run split rollback test ROLLBACK-TEST-OK` fell through to generic Ollama because the route matcher used exact tokenless route text. The hotfix detects `ROLLBACK-TEST-OK` separately and strips the token from route matching, preserving the token as an execution gate.

MEP-WR-002 is rollback-test-only. It does not assimilate the transaction group, leave persistent pipe splits, traverse connectors, extract geometry, scan linked documents, write parameters, or create tags, schedules, views, sheets, systems, circuits, families, or types.

Status: runtime validated.

## 2026-05-19 MEP-WR-003 Split Selected Pipe Single-Candidate Persistent Reviewed Apply

MEP-WR-003 is the first persistent reviewed apply feature. It applies exactly one explicitly selected pipe split candidate that was generated by MEP-WR-001 and successfully validated by MEP-WR-002.

### Architectural role

- routes known reviewed-apply prompts deterministically before Ollama fallback
- requires latest MEP-WR-001 dry-run state
- requires latest MEP-WR-002 rollback-test state with result `Passed` or `Passed with warnings`
- requires explicit candidate selection by candidate number or pipe id
- requires explicit `PERSISTENT-SPLIT-OK` token before opening a transaction
- blocks capped/untested candidates
- hard-limits execution to one candidate per command
- rejects batch/all-candidate apply requests
- validates target pipe still exists in the active document and remains eligible
- opens `TransactionGroup` and inner `Transaction`
- calls `PlumbingUtils.BreakCurve` for the single selected candidate
- inspects returned new pipe id and segment lengths
- commits the inner transaction and calls `TransactionGroup.Assimilate()` only after validation passes
- exposes `[SPLIT SELECTED PIPE REVIEWED APPLY]` as an exportable deterministic header for MEP-RO-005/006

Runtime validation applied candidate 1 for original pipe `3003513`, returning new pipe id `3130288`. The original and new segments were each `4.657 ft (1419 mm)`, the combined length was `9.314 ft (2839 mm)`, and length delta was `0 mm`. The report confirmed `Transaction opened: true`, `BreakCurve called: true`, `Transaction group assimilated: true`, and `Persistent model changes: true`.

The post-apply repeated dry-run verification was inconclusive due empty selection; the active Revit selection was empty. This limitation is tracked for future improvement; the persistent apply report itself confirmed the returned new pipe id and before/after length checks.

MEP-WR-003 does not implement batch apply, apply-all, connector traversal, geometry extraction, linked-document scan, parameter writes, tag/schedule/view/sheet creation, system/circuit edits, or family/type creation. Generic `apply reviewed action` and `execute latest proposal` prompts remain blocked by MEP-ACT-002.

Status: core runtime validated.

## 2026-05-25 MEP-WR-005 Split Apply Source Consumption / Staleness Guard

MEP-WR-005 adds a session-local source-consumption guard after the first persistent pipe split apply. The problem it addresses is that a MEP-WR-001 dry-run and MEP-WR-002 rollback-test source were created before the model was changed by MEP-WR-003; after a persistent split, those old candidates may no longer represent the current Revit model.

### Architectural role

- stores `latest_split_apply_consumed_source_state`
- marks the dry-run / rollback-test source consumed only after successful MEP-WR-003 persistent apply
- records consumed timestamp, source timestamps, applied candidate number, applied original pipe id, and returned new pipe id
- blocks any second persistent apply from the consumed source before transaction and before `BreakCurve`
- requires a new successful MEP-WR-002 rollback-test after the consumed timestamp to restore eligibility
- exposes `[SPLIT APPLY SOURCE STATE]` as an exportable deterministic status report
- keeps MEP-WR-004 verification read-only and explicitly does not clear consumed state

Runtime validation used BUNGE `TEST [FloorPlan]`. MEP-WR-001 generated seven candidates, MEP-WR-002 rollback-tested five, MEP-WR-003 applied candidate 1 on pipe `3003513`, and MEP-WR-004 verified returned new pipe `3130274`. MEP-WR-005 then reported the source consumed and blocked `apply split candidate 2 PERSISTENT-SPLIT-OK` with `Transaction opened: false`, `BreakCurve called: false`, and `Persistent model changes: false`.

A refreshed dry-run and rollback-test after the apply produced a newer rollback timestamp and restored persistent-apply eligibility. This validates the governance boundary needed before any future batch apply or connector-aware apply research.

MEP-WR-005 adds no new write API, transaction, connector traversal, geometry extraction, linked-document scan, parameter write, tag/schedule/view/sheet creation, system/circuit edit, or family/type creation.

Status: runtime validated.

## 2026-06-03 COORD-WR-001 to COORD-WR-003 Link Transform Audit and Reviewed Reset

COORD-WR-001 through COORD-WR-003 introduce a deterministic coordination automation chain for Revit link transform review and single-link reviewed origin reset.

### Architectural role

- COORD-WR-001 emits `[LINK TRANSFORM AUDIT REPORT]` as a read-only active-document `RevitLinkInstance` transform audit.
- COORD-WR-002 emits `[LINK ORIGIN RESET ROLLBACK TEST]` and requires `ROLLBACK-LINK-RESET-OK` before opening a rollback-only `TransactionGroup`.
- COORD-WR-002 uses `ElementTransformUtils.MoveElement` only inside rollback test scope, verifies temporary zero origin, rolls back, and verifies final origin restored.
- COORD-WR-003 emits `[LINK ORIGIN RESET REVIEWED APPLY]` and requires `PERSISTENT-LINK-RESET-OK`.
- COORD-WR-003 requires the latest passed COORD-WR-002 source, selected link id/name match, current origin/basis match, and current origin not already zero before persistent apply.
- Shared coordination state is stored through pyRevit script envvar `AI_WORKBENCH_COORD_SHARED_STATE` under `latest_passed_link_origin_reset_rollback_state`.
- The passed rollback source is written only on `Passed` rollback-test results and is not overwritten by Not Ready, Already at zero, Failed, missing-token, no-selection, multiple-selection, or unreadable-source reports.

### Runtime validation

Runtime validation reset selected link `2972572`, `3D-01B-AR-01.ifc : 48`, from `(0.000000, -6.233596, 0.000000) ft` to `(0.000000, 0.000000, 0.000000) ft`. COORD-WR-002 rollback validation passed, COORD-WR-003 readiness passed without transaction, COORD-WR-003 persistent apply committed one transaction, and post-apply COORD-WR-001 audit reported 8 loaded links near zero origin with audit result `OK`.

### Safety boundary

The chain supports a controlled progression from read-only audit to rollback proof to single selected reviewed apply. It does not implement batch/all-link reset, apply by stored element id alone, linked document mutation, reload/unload, pin/unpin, parameter writes, rotation, UI selection modification, or linked-document scanning.

Status: runtime validated.

## 2026-06-04 COORD-WR-004 Link Origin Reset Post-Apply Verification

COORD-WR-004 adds the read-only verification layer after COORD-WR-003 persistent reviewed apply. It verifies that the latest applied `RevitLinkInstance` remains at zero origin and that current transform basis/origin still match the stored applied final state.

### Architectural role

- emits `[LINK ORIGIN RESET POST-APPLY VERIFICATION]`
- reads `latest_link_origin_reset_apply_state`
- verifies latest applied target by stored element id in read-only mode
- supports selected-link verification when exactly one `RevitLinkInstance` is selected
- reports whether selected link and latest applied link match
- stores no write target for apply-by-stored-id behavior
- exports through the deterministic QA export/index path

### State boundary

COORD-WR-003 now stores `latest_link_origin_reset_apply_state` only after a real `Applied` result. Readiness-only reports such as `Reviewed apply result: Not ready` do not overwrite the latest valid applied state. COORD-WR-004 treats stored element id use as verification-only.

### Runtime validation

Runtime validation used link `2972572`, `3D-01B-AR-01.ifc : 48`. COORD-WR-003 apply `COORD-WR-003-20260604_152029` reset the link from approximately `(0, -2000, 0)` mm to `(0, 0, 0)` mm and stored the latest apply state. COORD-WR-004 verified the latest applied target, selected-link mode, and no-selection latest-state mode.

### Safety boundary

COORD-WR-004 opens no `Transaction`, opens no `TransactionGroup`, calls no `MoveElement`, performs no linked-document mutation, reload/unload, pin/unpin, parameter write, UI selection modification, or model mutation.

Status: runtime validated and export/index validated.

## 2026-06-05 COORD-WR-005 Link Reset Workflow Status Dashboard

COORD-WR-005 adds a read-only coordination workflow checkpoint over COORD-WR-001 through COORD-WR-004. It emits `[LINK RESET WORKFLOW STATUS]`, reads persisted audit/rollback/apply/verification state, reads the latest QA export index, and deterministically classifies workflow readiness.

The primary architecture issue was state continuity across independent prompt routes. COORD-WR-004 verification initially disappeared from the dashboard after selection was cleared, and COORD-WR-001 audit state was not available outside the immediate audit route. Compact serializable snapshots were added under `latest_link_origin_reset_post_apply_verification_state` and `latest_link_transform_audit_state`.

The shared state source is `pyrevit script envvar AI_WORKBENCH_COORD_SHARED_STATE`. Invalid or unresolved verification runs do not replace the previous valid `Verified` state. This allows a no-selection dashboard to remain `Ready / clean` when the active document, applied link id, and verification state still match.

Runtime validation completed the full chain for link `2972572`, from approximately `(0, -2300, 0)` mm to zero origin. Final audit `COORD-WR-001-20260605_163837` reported 8 near-zero links and no offsets or review candidates. Dashboard `COORD-WR-005-20260605_163912` remained `Ready / clean` with zero selected links.

COORD-WR-005 adds no transaction, TransactionGroup, movement API, correction, linked-document mutation, selection modification, reload/unload, pin/unpin, batch reset, or apply-by-stored-id behavior.

## 2026-06-08 COORD-WR-006 Link Reset Workflow History / Run Register

COORD-WR-006 extends COORD-WR-005 with a filesystem-backed workflow checkpoint register. Meaningful dashboard checkpoints are flattened into JSON-safe records and stored in `link_reset_workflow_history.jsonl` and `link_reset_workflow_history.csv` under `Desktop\Results\AI_Workbench\Workflow_History`.

### Source architecture

1. Prefer meaningful `latest_link_reset_workflow_status_state`.
2. If shared state is unavailable, empty, or not meaningful, scan the complete QA export JSONL/CSV indexes.
3. Select the newest export with source header `[LINK RESET WORKFLOW STATUS]`.
4. Parse `report.txt`, with `report.md` fallback.
5. Append only meaningful workflow statuses and prevent duplicates by `status_id` or source export folder.

The full index scan is necessary because `latest_export.json` can point to a newer history report rather than the latest workflow-status report.

### Runtime result

After pyRevit shared state reset, COORD-WR-005 status `COORD-WR-005-20260608_091433` was `Not ready`. COORD-WR-006 initially appended nothing. The fallback then recovered clean checkpoint `COORD-WR-005-20260605_163912` from export `20260605_163936`, appended one record, and skipped the same record on a second run.

### Safety boundary

COORD-WR-006 reads QA export files and writes local history JSONL/CSV only. It opens no transaction or TransactionGroup, calls no movement API, runs no audit/rollback/apply/verification action, changes no selection, and modifies no Revit or linked-document data.

## 2026-05-17 MEP-RO-006 QA Export Index / Snapshot Registry

MEP-RO-006 builds on MEP-RO-005 by registering every successful QA evidence export in a persistent local filesystem index.

### Architectural role

- successful exports update `qa_export_index.jsonl`, `qa_export_index.csv`, and `latest_export.json`
- primary index location is `%USERPROFILE%/Desktop/Results/AI_Workbench/QA_Exports/_index/`
- fallback index location is `%TEMP%/AI_Workbench/QA_Exports/_index/`
- deterministic list/latest index routes run before Ollama fallback
- index read prompts do not scan the Revit model or linked documents
- generic Ollama responses remain rejected by the export path and do not create index entries
- index metadata records `read_only: true`, `model_modified: false`, `linked_documents_scanned: false`, `connector_traversal_used: false`, and `geometry_extraction_used: false`

The registry is filesystem/index-only. It does not mutate the Revit model, write parameters, open transactions, traverse connectors, extract geometry, or inspect linked-document internals.

Status: runtime validated.

## 2026-05-17 MEP-ACT-001 Reviewed Action Proposal Framework

MEP-ACT-001 introduces a deterministic proposal-only layer between the validated read-only QA/export stack and future reviewed write actions.

### Architectural role

- routes known action-oriented prompts deterministically before Ollama fallback
- classifies the requested action into a supported proposal key
- reads live Revit context safely, currently focused on current selection for split-selected-pipes preflight
- stores session-local reviewed action proposal state
- outputs `[REVIEWED ACTION PROPOSAL]` with explicit proposal-only/no-execution safety wording
- accepts `[REVIEWED ACTION PROPOSAL]` as a deterministic export header, so proposals can be exported by MEP-RO-005 and indexed by MEP-RO-006

### Proposal coverage

- `split_selected_pipes` includes live-selection preflight for eligible pipes, skipped pipe fittings/accessories/non-pipes, near-vertical pipes, too-short pipes, unreadable location curves, pinned pipes, grouped pipes, design-option pipes, unsupported curve types, and readability warnings
- `tag_selected_mep_elements`, `fill_missing_marks`, `export_latest_qa_report`, `create_qa_snapshot`, and `create_schedule_from_report` are recognized future reviewed actions with proposal-only placeholders
- `unknown_reviewed_action` returns supported proposal prompts without using Ollama

MEP-ACT-001 does not execute confirmation/apply behavior. It opens no transaction and performs no pipe splitting, tagging, scheduling, parameter writing, system/circuit editing, connector traversal, geometry extraction, or model mutation.

Status: runtime validated.
