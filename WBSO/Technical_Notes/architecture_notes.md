# Architecture Notes

## Project

AI Systems & Intelligent Automation

## Current Phase

2026 migration baseline + guarded product-architecture refactor

## Purpose

This file records the current architecture after restructuring the single pyRevit AI window around clearer product roles and safer local state.

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
