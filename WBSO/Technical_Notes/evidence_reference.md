# Evidence Reference

## Purpose

This file maps technical work in the repository to concrete WBSO evidence artifacts, validation notes, and repository-local documentation.

## Evidence ID Format

`EV-YYYY-MM-DD-###`

---

## EV-2026-04-08-001 - AI window architecture refactor with structured prompts and guarded agent semantics

### Summary

Refactored the single pyRevit AI window into clearer product roles while preserving the single entry-point structure. Introduced a structured ModelMind prompt catalog, approved-recipe storage, local theme persistence, and explicit AI Agent session semantics.

### Why It Changed

This pass was needed to:

- clarify product responsibilities across Ollama Chat, ModelMind, and AI Agent
- remove hardcoded prompt-tree state from the UI controller
- introduce a safer approved-recipe concept for reviewed generated code
- make AI Agent controls behaviorally explicit and safety-oriented
- improve UX clarity without splitting the window or changing installer assumptions

### Code / Repo Areas Affected

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`
- `AI.extension/lib/ai_prompt_registry.py`
- `AI.extension/lib/ai_local_store.py`
- `AI.extension/lib/ai_agent_session.py`
- `AI.extension/lib/prompt_catalog.json`
- `AI.extension/lib/approved_recipes.json`

### WBSO Files Updated

---

## EV-2026-04-21-001 - Stable-baseline ModelMind catalog usability polish

### Summary

Added a dedicated read-only catalog filter surface, compact catalog status text, low-risk expand/collapse controls, and clearer Selected Action Details framing for the stable ModelMind catalog.

### Why It Changed

This pass was needed to:

- separate catalog browsing from the main ModelMind prompt input
- make the larger reviewed catalog easier to search without triggering execution
- improve operator understanding of canonical metadata, aliases, examples, and validation state
- preserve the restored stable execution baseline

### Code / Repo Areas Affected

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`
- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`

### Validation Position

- local XML/tabnanny verification only in this pass
- no reviewed execution architecture changes
- no new live pyRevit/Revit confirmation claimed

---

## EV-2026-04-21-002 - Stable-baseline reviewed schedule generation

### Summary

Added deterministic reviewed schedule-generation actions for supported MEP categories, with level/reference-level grouping, detailed vs summary schedule modes, and template-first duplication where available.

### Why It Changed

This pass was needed to:

- extend governed Workbench coverage into schedule creation without introducing freeform generic code generation
- support practical MEP quantity workflows by category rather than one unrestricted universal schedule
- keep schedule generation on the stable reviewed deterministic baseline

### Code / Repo Areas Affected

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/lib/prompt_catalog.json`

### Validation Position

- local tabnanny/json/alias-resolution verification completed
- no execution architecture changes
- no live pyRevit/Revit schedule-creation confirmation claimed in this pass

---

## EV-2026-04-21-003 - Schedule promotion and template-backed catalog separation

### Summary

Promoted only the validated generic schedule family to `live_validated`, reorganized schedules into a dedicated `Schedules` catalog branch, and added separate template-only ACO actions that do not fall back silently into the native schedule family.

### Why It Changed

This pass was needed to:

- keep runtime-validated generic schedule actions distinct from still-unproven template heuristics
- place schedules in a clearer ModelMind tree structure
- support project-specific template-backed schedule creation without contaminating the shared native schedule family

### Code / Repo Areas Affected

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/lib/prompt_catalog.json`
- `AI.extension/lib/ai_prompt_registry.py`

### Validation Position

- local tabnanny/json/registry-resolution verification completed
- generic promoted schedule actions now resolve as `live_validated`
- ACO template actions remain `structural_only`
- no new live Revit confirmation claimed in this pass

- `WBSO/Technical_Notes/architecture_notes.md`
- `WBSO/Technical_Notes/issue_log.md`
- `WBSO/Technical_Notes/evidence_reference.md`
- `WBSO/Technical_Notes/pyrevit_extension_refactor.md`
- `WBSO/Technical_Notes/provider_strategy.md`
- `WBSO/Technical_Notes/current_scope_alignment.md`
- `WBSO/Testing_Validation/test_plan.md`
- `WBSO/Testing_Validation/experiment_log.csv`
- `WBSO/Testing_Validation/runs/2026-04-03_migration_baseline/validation_summary.md`
- `WBSO/Data_Models/model_registry.md`
- `WBSO/Data_Models/provider_registry.md`
- `WBSO/Data_Models/prompt_asset_manifest.csv`
- `README.md`

### What Was Actually Verified

- `prompt_catalog.json` parses successfully
- `approved_recipes.json` parses successfully
- `UI.xaml` is well-formed XML

### What Was Not Yet Verified

- pyRevit runtime loading after this refactor
- Revit UI launch after this refactor
- Ollama chat runtime response after this refactor
- Snowdon Towers Sample HVAC execution of the requested validation workflows

### Where to Find the Validation Notes

- `WBSO/Testing_Validation/test_plan.md`
- `WBSO/Testing_Validation/runs/2026-04-03_migration_baseline/validation_summary.md`
- `WBSO/Testing_Validation/experiment_log.csv`

### Open Follow-up

- perform live pyRevit/Revit validation on Snowdon Towers Sample HVAC
- confirm baseline preservation in the refactored UI
- refine agent planning heuristics after live use

---

## EV-2026-04-08-002 - Reviewed-code validator and approved-recipe hardening

### Summary

Hardened the ModelMind reviewed-code path so only pyRevit-compatible reviewed code can be approved/executed, and only successful reviewed runs can be saved as approved recipes.

### Why It Changed

Current live findings showed that:

- theme persistence already works across relaunch
- Ollama Chat already works in live runtime
- ModelMind deterministic tasks already work
- invalid reviewed code referencing DesignScript / Dynamo runtime modules had still been allowed to execute
- failed reviewed-code runs were correctly not being added to approved recipes and that rule needed to remain in force

### Code / Repo Areas Affected

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`
- `AI.extension/lib/ai_reviewed_code.py`
- `AI.extension/lib/ai_prompt_registry.py`
- `AI.extension/lib/prompt_catalog.json`

### What Was Added

- reviewed-code validation gate before approval
- reviewed-code validation gate immediately before execution
- explicit reviewed-code state label: `draft / validated / blocked / executed / saved`
- explicit `Save as Approved Recipe` action after success
- required approved-recipe metadata capture
- pyRevit-safe reviewed-code template for `create sheet`

### Live Findings Recorded

Live runtime findings reported for this pass:

- theme persistence works across relaunch
- Ollama Chat works in live runtime
- ModelMind deterministic tasks work

### Intentionally Blocked by Design

The validator now blocks reviewed code containing unsupported pyRevit runtime references such as:

- `Autodesk.DesignScript`
- `DesignScript`
- `RevitServices`
- `RevitNodes`
- `ProtoGeometry`
- `from Revit import ...`
- Dynamo-specific context APIs

### Still Not Yet Live-Validated After the Patch

- blocking behavior for invalid reviewed code in live Revit
- successful reviewed-code save flow in live Revit
- immediate approved-branch refresh after save in live Revit

---

## EV-2026-04-09-001 - UI polish and deterministic reviewed-planner narrowing

### Summary

Polished the AI Workbench header/layout and dark-mode readability, streamlined ModelMind reviewed-code presentation, and narrowed AI Agent into a smaller deterministic reviewed-planner for supported BIM workflows.

### Why It Changed

This pass was needed because the live runtime baseline was working, but the product surface still had:

- header/layout crowding risk
- dark-mode readability issues for dropdowns, tree text, and disabled actions
- overly verbose reviewed-code output in ModelMind
- an AI Agent surface that implied broader autonomy than the current supported runtime

### Live runtime facts already confirmed for this pass

- pyRevit AI tab loads
- button opens AI Workbench
- Ollama Chat works
- theme persistence works across relaunch
- ModelMind `select all ducts` works in Snowdon Towers Sample HVAC
- reviewed create-sheet flow works
- approved recipe save/load works

### What changed in code

- top-right header/button alignment
- dark-mode dropdown/tree/disabled-control styling
- show/hide reviewed-code panel for ModelMind
- clearer approved-recipes branch presentation
- direct approved-recipe execution from the tree
- deterministic reviewed-planner support for additional duct-focused requests

### What still requires live validation

- AI Agent deterministic planner handling for the new duct-focused cases
- top-right header alignment confirmation in live Revit
- dark-mode dropdown/tree readability confirmation in live Revit
- disabled-button readability confirmation in live Revit

---

## EV-2026-04-09-002 - Provider-backed reviewed planner integration

### Summary

Integrated a real provider-backed AI Agent planning path using the existing OpenAI service route while keeping execution deterministic and reviewed inside pyRevit.

### Why It Changed

This pass was needed because:

- ModelMind still needed layout polish
- AI Agent needed a real planning provider path
- cloud planning needed to respect environment-based secret loading
- execution still had to remain inside the reviewed deterministic action set

### Code / Repo Areas Affected

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`
- `AI.extension/lib/ai_agent_session.py`
- `AI.extension/lib/ai_prompt_registry.py`
- `AI.extension/lib/prompt_catalog.json`
- `Openai_Server/chatgpt_service.py`
- `Model_Service/ModelService.py`

### What Changed

- widened the ModelMind input and moved its actions below the input
- added planner provider state/availability UI
- added local vs OpenAI planner selection
- loaded `OPENAI_API_KEY` from environment only
- added provider-state checks for:
  - local only
  - cloud available
  - cloud unavailable: missing key
  - cloud unavailable: request failed
- constrained cloud planning to machine-readable supported-action normalization
- kept execution routed through the deterministic command registry or reviewed `create sheet` template

### What Was Actually Verified Locally

- `Openai_Server/chatgpt_service.py` compiles
- `Model_Service/ModelService.py` compiles
- AI support modules compile
- `UI.xaml` is well-formed XML
- prompt/approved-recipe JSON files parse

### Live Findings Carried Forward

Previously live-validated findings still in force:

- pyRevit AI tab loads
- button opens AI Workbench
- Ollama Chat works
- theme persistence works
- ModelMind `select all ducts` works
- reviewed create-sheet flow works
- approved recipe save/load works

### What Was Not Yet Verified Live In This Pass

- ModelMind layout polish in live Revit
- AI Agent local planner handling after this pass
- AI Agent OpenAI planner normalization with a valid key
- missing-key UI behavior in live Revit
- request-failure handling/fallback in live Revit

---

## EV-2026-04-10-001 - Provider diagnostics refinement and honest planner-state reporting

### Summary

Refined the AI Agent provider diagnostics so the UI can distinguish key presence from real cloud request failures and report planner state more honestly.

### Why It Changed

Current live findings reported that:

- `OPENAI_API_KEY` exists in Windows user environment variables
- the AI Agent UI still showed both a request-failed message and a missing-key setup message
- that combined messaging was incorrect

### Code / Repo Areas Affected

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `Openai_Server/chatgpt_service.py`
- `Model_Service/ModelService.py`
- `AI.extension/lib/ai_agent_session.py`
- `AI.extension/lib/ai_prompt_registry.py`
- `AI.extension/lib/prompt_catalog.json`

### What Changed

- added structured provider health reporting from the OpenAI service layer
- distinguished:
  - `missing_key`
  - `auth_failed`
  - `request_failed`
  - `network_failed`
  - `provider_ready`
  - `local_only`
- surfaced safe diagnostics for key presence, provider reachability, and last error category
- removed the broad missing-key notice from non-missing-key failures
- improved unsupported planner guidance for schedule/quantity requests
- recorded a candidate near-term action for selected-duct volume reporting without claiming it is implemented

### What Was Actually Verified Locally

- updated provider/service modules compile
- updated prompt catalog parses

### Live Findings Recorded For This Pass

- key exists in Windows user environment variables
- the pre-fix live UI messaging was incorrect because it mixed missing-key and request-failed guidance
- unsupported schedule-generation request rejection remains acceptable for now because schedule generation is outside the current reviewed deterministic action set

### What Still Needs Live Verification

- key-present state no longer shows the missing-key guidance
- cloud failure shows the correct classified state in the UI
- local deterministic fallback still works when cloud planning fails
- improved unsupported schedule/quantity guidance is shown in live Revit

---

## EV-2026-04-10-002 - Cloud planner self-test and runtime-identity diagnostics

### Summary

Added a cloud planner self-test path so the actual Python runtime used by the AI Agent cloud planner can report environment visibility, dependency availability, and request readiness safely inside the Revit UI.

### Why It Changed

This pass was needed because:

- `OPENAI_API_KEY` exists in Windows user environment variables
- AI Agent still showed `key_present: no` in live runtime
- local verification suggested the `openai` module might be missing in the runtime used by the subprocess service path

### Code / Repo Areas Affected

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `Openai_Server/chatgpt_service.py`
- `Model_Service/ModelService.py`
- `AI.extension/lib/ai_agent_session.py`

### What Was Added

- provider self-test command in `chatgpt_service.py`
- service wrapper method in `ModelService.py`
- internal AI Agent request:
  - `cloud planner self test`
- safe runtime-identity reporting:
  - runtime executable
  - runtime version
  - subprocess command used

### What Was Actually Verified In This Workspace Pass

Workspace self-test result through the service path:

- `env_key_present: yes`
- `openai_module_importable: no`
- `client_init_ok: no`
- `test_request_ok: no`
- `failure_category: missing_openai_module`
- runtime executable reported as `C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python313\\python.exe`

### What Still Needs Live Verification

- whether live Revit sees the same environment key visibility result
- whether live Revit reports the same missing-module result
- whether local deterministic planning still remains validated after the self-test additions

---

## EV-2026-04-10-003 - OpenAI Responses API planner wiring

### Summary

Updated the OpenAI-backed cloud planner path to use the OpenAI Python client through the Responses API while keeping cloud use limited to planning / intent normalization / supported-action mapping.

### What Changed

- `chatgpt_service.py` now uses the Responses API for:
  - minimal provider probe
  - planner normalization requests
- no raw cloud-generated code is executed
- reviewed deterministic execution boundaries remain intact in the pyRevit layer

### What Was Actually Verified

- updated provider/service modules compile
- the Responses API service path now reports:
  - `env_key_present: yes`
  - `openai_module_importable: yes`
  - `client_init_ok: yes`
  - `failure_category: network_failed`

### Current Runtime Conclusion

The OpenAI planner is not yet confirmed working in live Revit. The current verified blocker is no longer dependency visibility; it is provider/network reachability from the Python runtime used by the cloud planner subprocess.

---

## EV-2026-04-10-004 - Shared reviewed action registry for ModelMind and AI Agent

### Summary

Refactored ModelMind and AI Agent to share one reviewed action registry so the visible task library and the planner/router operate over the same reviewed action definitions.

### Code / Repo Areas Affected

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/lib/ai_prompt_registry.py`
- `AI.extension/lib/ai_agent_session.py`
- `AI.extension/lib/prompt_catalog.json`

### What Changed

- AI Agent no longer depends on a separate hardcoded action inventory
- registry metadata now includes reviewed action planner aliases and deterministic handler names
- AI Agent local planning now matches against registry aliases
- both ModelMind and AI Agent now consume the same reviewed action definitions

### New reviewed MEP action coverage added

- HVAC / Ducting:
  - select all ducts
  - count selected ducts
  - count ducts in active view
  - list ducts in active view
  - report total selected duct length
  - report total selected duct volume in cubic meters
  - find unconnected duct fittings
  - report ducts without system assignment
- Piping:
  - select all pipes
  - count selected pipes
  - report total selected pipe length
  - find unconnected pipe fittings
  - report pipes without system assignment
- Electrical:
  - select all electrical fixtures in active view
  - count selected fixtures/devices
  - report devices without circuit/system info
  - list fixtures by type in active view
- QA / BIM:
  - report selected elements by category
  - report selected elements by type
  - health check for active view selection
  - report missing parameters from selection
- Low-risk write actions:
  - create sheet
  - create 3D view from selection/context

### What Was Actually Verified Locally

- shared reviewed actions loaded from registry: `23`
- AI Agent local planner normalized example prompts through the shared registry for:
  - `select ducts`
  - `count selected ducts`
  - `volume of selected ducts`
  - `find disconnected duct fittings`
  - `create a sheet`

### What Still Needs Live Verification

- ModelMind rendering of the shared reviewed action set
- AI Agent execution of the new MEP reviewed actions in live Revit
- approved recipe save/load continuity after the registry refactor

---

## EV-2026-04-13-001 - Expanded reviewed MEP registry over the shared action architecture

### Summary

Expanded the shared reviewed action registry around the already validated local deterministic workflow while preserving the architecture:

- `ModelMind` = source-of-truth reviewed action library
- `AI Agent` = planner/router over the same reviewed actions

### Live findings carried into this pass

Reported as already live-validated before this code pass:

- Ollama Chat works with `phi3:mini`
- ModelMind:
  - `select all ducts`
  - `count ducts in active view`
  - `list ducts in active view`
  - `create sheet`
- AI Agent:
  - `select ducts`
  - `count selected ducts`
  - `count ducts in active view`
  - `list ducts in active view`
- reviewed create-sheet flow remains working
- approved recipe save/load remains working

### What changed in code

- added reviewed deterministic actions for additional piping, electrical, QA/BIM, and low-risk write workflows
- expanded alias coverage for practical BIM phrasing
- added pipe active-view count/list actions
- added electrical active-view fixture listing action

### What was actually verified locally

- shared reviewed actions loaded from registry: `26`
- AI Agent local planner normalized shared-registry aliases for:
  - `duct length`
  - `total selected duct volume`
  - `pipes without system`
  - `count pipes in active view`
  - `electrical devices in active view`
  - `create a 3d view from this selection`

### Duct-volume investigation outcome

- the old implementation depended only on a direct `Volume` parameter
- the new implementation now:
  - uses direct volume if available
  - derives volume from section dimensions + length when possible
  - reports unresolved ducts honestly if the sample/model data is insufficient

### What still needs live verification

- duct-volume action after the robustness fix
- the newly added pipe/electrical/QA actions
- `create 3D view` in live Revit

---

## EV-2026-04-14-001 - Shared catalog visibility and resizable Workbench shell

### Scope

- make ModelMind visibly reflect the full shared reviewed action registry
- keep aliases/examples as metadata rather than duplicate nodes
- keep Approved Recipes outside the canonical catalog
- keep AI Agent as planner/router only, not as a second catalog tree
- make the Workbench shell resizable with persisted window geometry

### Files changed

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`
- `AI.extension/lib/ai_prompt_registry.py`
- `AI.extension/lib/ai_agent_session.py`

### What was actually verified locally

- shared reviewed actions available from registry: `26`
- ModelMind tree sections now build as:
  - `HVAC`
  - `Piping`
  - `Electrical`
  - `QA / BIM`
  - `Views / Sheets`
  - `Recent Prompts`
  - `Approved Recipes`
- AI Agent supported-action view now reflects the same `26` shared reviewed actions instead of a stale hardcoded subset
- `UI.xaml` parses successfully after the resizable split-layout refactor

### What remains unvalidated in live Revit

- grouped ModelMind tree rendering in the actual pyRevit window
- resize behavior, splitter usability, and persisted window position/size in runtime
- approved-recipe branch grouping by domain after save/reload in runtime

---

## EV-2026-04-14-002 - AI Agent plan-step state and control clarification

### Scope

- clarify that the bottom AI Agent selector is only for current reviewed plan steps
- keep supported reviewed actions informational rather than interactive in that control
- fix button enable/disable behavior to follow actual plan-step state

### Files changed

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`
- `AI.extension/lib/ai_agent_session.py`

### What was actually verified locally

- a local plan for `count selected ducts` creates a step with:
  - `id`
  - `title`
  - `role`
  - `risk`
  - `enabled`
  - `executed`
  - `blocked_reason`
  - `undo_available`
- disabling that single step changes session state so `has_enabled_steps` becomes false
- `UI.xaml` parses successfully after the Agent control relabel/state additions

### What remains unvalidated in live Revit

- selected-plan-step interaction in the actual Agent UI
- corrected button enable/disable behavior during live session use
- Execute Plan availability messaging when only modifying steps are enabled and destructive tools remain off

---

## EV-2026-04-14-003 - Action-specific undo for create-3D-view

### Scope

- add real reversible undo context only for a truly reversible reviewed modifying action
- do not add generic/global undo
- keep Approved Recipes and the broader reviewed catalog behavior unchanged

### Files changed

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`
- `AI.extension/lib/ai_agent_session.py`

### What was actually verified locally

- blocked modifying execution with destructive tools off does not create undo context
- successful modifying execution with destructive tools on creates undo context
- `reset()` clears undo context
- successful read-only execution does not create undo context
- `UI.xaml` parses successfully after adding the undo-status text

### What remains unvalidated in live Revit

- real delete-on-undo behavior for the created 3D view
- honest runtime failure reporting if the created view is already gone
- live confirmation that `Undo Last Action` enables only when the create-3D-view undo context exists

---

## EV-2026-04-15-001 - Create-sheet undo extension

### Scope

- extend the real reviewed-action undo framework from create-3D-view to create sheet
- keep one last-action undo context only
- keep read-only actions non-undoable

### Files changed

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`
- `AI.extension/lib/ai_agent_session.py`

### What was actually verified locally

- successful create-sheet execution can create undo context structurally
- `reset()` clears create-sheet undo context
- create-3D-view undo-context behavior still works structurally
- read-only execution still creates no undo context
- approved-recipe and reviewed execution paths are wired through the shared undo-context application helper

### What remains unvalidated in live Revit

- actual delete-on-undo behavior for created sheets
- honest runtime failure reporting when a created sheet is gone or not deletable
- approved-recipe create-sheet undo behavior in the live session

---

## EV-2026-04-15-002 - QA/BIM reviewed-action hardening

### Scope

- improve runtime trustworthiness of the existing QA/BIM read-only reviewed actions
- keep the shared registry/catalog architecture unchanged
- avoid cloud work and avoid undo-framework expansion outside direct bug fixes

### Files changed

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`

### What was actually verified locally

- the four QA/BIM handlers were refactored without syntax regressions
- grouped/sample-id output paths are present for category/type reports
- the parameter-check path now includes explicit nothing-missing handling
- the active-view health-check path now includes unconnected-fitting and missing-system summary lines

### What remains unvalidated in live Revit

- usefulness/correctness of the hardened QA/BIM outputs on real selections and active views
- parameter applicability behavior across mixed-discipline runtime selections

---

## EV-2026-04-15-003 - QA/BIM scope messaging and alias hardening

### Scope

- clarify active-document / active-view scope for the existing QA/BIM reviewed actions
- improve natural-language alias coverage without changing canonical actions or catalog structure

### Files changed

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/lib/prompt_catalog.json`

### What was actually verified locally

- the following prompts now normalize to the intended reviewed actions:
  - `show selected elements by category`
  - `group selected elements by type`
  - `check missing key parameters in selection`
  - `health check this active view`
  - `inspect active view for MEP issues`
- scope messaging lines are present in the QA/BIM handler output
- QA/BIM catalog metadata now correctly distinguishes `selection` vs `active_view` scope

### What remains unvalidated in live Revit

- runtime usefulness of the new scope wording when users have selections in other open Revit projects
- live confirmation that the added aliases cover the intended prompt phrasing well enough

---

## EV-2026-04-15-004 - QA/BIM category grouping defect fix

### Scope

- fix the existing reviewed action `report selected elements by category` so it renders real category groups instead of the fallback `(err)` label
- preserve active-document scope messaging and the existing shared reviewed catalog architecture

### Files changed

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`

### What was actually verified locally

- `script.py` passes local indentation/tokenization sanity checks
- the category-grouping path now uses hardened naming logic for Revit `Category` objects
- the action still preserves:
  - `Selection scope: active document only`
  - `Total selected elements: <n>`
- actual grouping failures now return:
  - `Unable to group selected elements by category.`

### What remains unvalidated in live Revit

- runtime confirmation that grouped category output now renders real Revit category names such as `Ducts` and `Duct Fittings`

---

## EV-2026-04-15-005 - QA/BIM validation metadata promotion and context UX

### Scope

- promote only the QA/BIM reviewed actions with explicit runtime evidence to `live_validated`
- improve low-noise context awareness in QA/BIM output
- keep Recent Prompts as convenience history while resolving their details through canonical reviewed metadata

### Files changed

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/lib/ai_prompt_registry.py`
- `AI.extension/lib/prompt_catalog.json`

### What was actually verified locally

- the following actions now resolve as `live_validated` through the shared reviewed registry:
  - `report-selected-elements-by-category`
  - `report-selected-elements-by-type`
  - `report-missing-parameters-from-selection`
  - `health-check-active-view-selection`
- `script.py` still passes local tokenization/indentation sanity checks
- Recent Prompt details now resolve through canonical action lookup before the Selected Action panel is built

### What remains unvalidated in live Revit

- runtime confirmation of the promoted validation-state display in the Selected Action panel
- runtime confirmation of the compact context lines and recent-prompt canonical-details behavior

---

## EV-2026-04-16-001 - Reviewed production-assistant expansion pass

### Scope

- expand the shared reviewed registry with discipline QA presets and additional deterministic production-assistant actions
- preserve the one-catalog ModelMind/AI Agent architecture
- add only native deterministic reviewed implementations where safe and available

### Files changed

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/lib/ai_prompt_registry.py`
- `AI.extension/lib/ai_agent_session.py`
- `AI.extension/lib/prompt_catalog.json`

### What was actually verified locally

- `script.py` passed local `tabnanny` indentation/tokenization sanity
- `ai_prompt_registry.py` and `ai_agent_session.py` compiled successfully
- `prompt_catalog.json` parsed successfully
- shared reviewed registry now exposes the new top-level groupings:
  - `QA Presets`
  - `Selection / Categories`
  - `Coordination / Spaces`
  - `Cleanup / Repair`
  - `Views / Sheets / Tags`
  - `Quantities`
- planner normalization matched the newly added presets/actions for:
  - `run hvac qa preset`
  - `run piping qa preset`
  - `run electrical qa preset`
  - `run bim qa preset`
  - `split selected pipes every 1.5 m`
  - `report duplicates`
  - `remove duplicates`
  - `count all walls`
  - `list all pipe fittings`
  - `room to space check`
  - `rename active view`
  - `align selected tags`

### What remains unvalidated in live Revit

- all new presets and actions added in this pass

---

## EV-2026-04-19-001 - Preset hardening and scope-governance pass

### Scope

- harden preset-step scope semantics
- improve category resolution governance
- add ModelMind access to the shared reviewed undo surface
- keep duplicate actions structural only until proven in runtime

### Files changed

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/lib/ai_prompt_registry.py`
- `AI.extension/lib/ai_agent_session.py`
- `AI.extension/lib/prompt_catalog.json`
- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`

### What was actually verified locally

- `script.py` passed local `tabnanny`
- `ai_prompt_registry.py` and `ai_agent_session.py` compiled successfully
- `prompt_catalog.json` parsed successfully
- `UI.xaml` remained well-formed
- planner normalization matched the expanded split-pipe aliases
- planner normalization still matched the four hardened presets
- hidden preset-support electrical actions remained available for preset execution without becoming top-level planner targets

### What remains unvalidated in live Revit

- hardened HVAC QA preset
- hardened Piping QA preset
- redesigned Electrical QA preset
- hardened Coordination / BIM QA preset
- category disambiguation on walls / doors / pipe fittings
- ModelMind shared undo
- expanded split-pipe prompt variants

---

## EV-2026-04-20-002 - Stability-fenced catalog routing hardening

### Scope

- improve safe deterministic reviewed prompt routing without touching lifecycle or execution plumbing
- expand aliases/examples for already validated presets and category helpers only

### Files changed

- `AI.extension/lib/ai_prompt_registry.py`
- `AI.extension/lib/prompt_catalog.json`

### What was actually verified locally

- `ai_prompt_registry.py` compiled successfully
- `prompt_catalog.json` parsed successfully
- local routing checks confirmed:
  - `run the hvac qa preset`
  - `run piping preset`
  - `electrical coordination preset`
  - `run the bim qa preset`
  - `select categories:doors, windows`
  - `count categories:doors, windows`
  - `list category:"Pipe Fittings"`
  resolve through the shared reviewed registry

### What remains unvalidated in live Revit

- runtime confirmation that the new alias/example variants are actually used successfully through the stable fenced Workbench

---

## EV-2026-04-20-003 - Stable-baseline UI polish

### Scope

- improve dark-mode button-state readability only
- clarify close-button wording only
- do not touch execution or lifecycle architecture

### Files changed

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`

### What was actually verified locally

- `UI.xaml` remained well-formed XML
- local inspection confirmed:
  - shared disabled-button brushes are present
  - shared disabled-button trigger style is present
  - close-button tooltip text is clarified

### What remains unvalidated in live Revit

- whether enabled vs disabled buttons are now clearly distinguishable in dark mode

---

## EV-2026-04-20-004 - Stable-baseline ModelMind catalog usability

### Scope

- improve ModelMind catalog discoverability and details-panel readability only
- do not touch execution or lifecycle architecture

### Files changed

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`

### What was actually verified locally

- `UI.xaml` remained well-formed XML
- local inspection confirmed:
  - the main ModelMind input now explains the existing live filter behavior
  - the catalog hint text now explains filtering and Recent Prompt resolution more clearly
  - the details group/header text was updated for readability

### What remains unvalidated in live Revit

- whether the improved hints/details make the growing ModelMind catalog easier to browse in runtime

### 2026-04-22 template-recipe hardening evidence

- local verification covered explicit shared-catalog routing for ACO/BUNGE template actions after moving source selection to exact reviewed recipe definitions
- static inspection confirmed canonical-master exclusions for floor-specific, sheet, AI-generated, and previously generated ACO output schedules

### 2026-04-24 schedule-template evidence

- live evidence provided by user confirms generic native schedules remain valid, generic all-ACO pipe template actions block honestly, and ACO pipe-fitting summary from canonical master produced a populated summary with Grand total 141
- local verification added routing coverage for the new structural product-family ACO pipe actions and exact coded level prompts

### 2026-04-27 project-context scanner evidence

- local verification covered script tabnanny, registry/session compile, prompt_catalog parsing, UI.xaml parsing, and shared-catalog routing for scanner/planner/brief prompts
- no live Revit validation was executed for scanner collector completeness in this pass

### 2026-04-27 project-context UX/Q&A evidence

- user-provided live validation confirms bootstrap and standard scans succeed in Snowdon Towers Sample HVAC and return expected project counts
- this pass adds deterministic context-answer routing to avoid Ollama timeouts for known structured questions
- local verification covers static syntax/XML/JSON checks only; live validation of the new quick actions and dark-theme tree styling remains pending

## EV-2026-05-06-001 - AI-AGENT-002 Guided Project Startup Plan

### Feature

AI-AGENT-002 Guided Project Startup Plan

### What changed

- Agent plan now produces structured project-startup phases.
- Deterministic prompts route to the guided plan.
- Codex Brief includes guided Agent plan metadata.

### Why

To convert Project Context diagnostics into a safer user-facing plan before automation.

### Files changed in the implementation pass

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/lib/prompt_catalog.json`
- `AI.extension/lib/ai_prompt_registry.py`

### Validation

- live Revit validation on BUNGE project
- document: `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`
- active view: `TEST [FloorPlan]`

### Artifacts

- runtime text output from Scan Project
- runtime text output from Ask Agent for Plan
- runtime text output from guided plan prompts
- runtime text output from Create Codex Brief
- screenshot artifacts not yet added

### Status

- runtime validated as plan-only
- Execute Plan not validated

## EV-2026-05-07-001 - MEP-RO-001 ModelMind Read-Only BIM/QA Selection Action Pack

### Feature

MEP-RO-001 ModelMind Read-Only BIM/QA Selection Action Pack

### What changed in the implementation pass

- existing selection-report pack was hardened
- aliases were expanded
- no model-modifying actions were added

### Validation performed

- Scan Project succeeded before selection-report tests.
- No-selection test attempted.
- Selected pipes/fittings test attempted.
- Selected ducts/fittings test attempted.
- Selected electrical elements test attempted.

### Validation result

Failed.

### Reason

Typed selection-report prompts fell through to Ollama and returned generic non-Revit answers instead of deterministic Revit selection reports.

### Artifacts

- runtime text output from failed prompts
- no validated Revit selection-report output yet
- screenshot artifacts not yet added

### Status

- structural/hardened
- routing failed
- not live validated

## EV-2026-05-07-002 - MEP-RO-001 Routing/Live Selection Hotfix

### Feature

MEP-RO-001 Routing/Live Selection Hotfix

### What changed

- Fixed deterministic routing for selection-report prompts.
- Confirmed live selection reading through the existing `_selected_elements(doc, uidoc)` path.
- Validated read-only Revit-specific output across piping, HVAC, and electrical selections.

### Hotfix files changed

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`

### Files intentionally not changed in the implementation pass

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`
- `AI.extension/lib/prompt_catalog.json`
- `AI.extension/lib/ai_prompt_registry.py`
- `AI.extension/lib/ai_agent_session.py`
- BIM3DNA toolbar copy
- WBSO files during the implementation pass

### Validation

- no selection passed
- BUNGE pipes/fittings passed
- Snowdon HVAC selected elements passed
- Snowdon Electrical selected elements passed
- no generic Ollama fallback observed for the five tested prompts after hotfix
- no model mutation observed

### Artifacts

- runtime text output from Scan Project
- runtime text output from no-selection prompts
- runtime text output from selected piping prompts
- runtime text output from selected HVAC prompts
- runtime text output from selected electrical prompts
- screenshot artifacts not yet added

### Status

Runtime validated after hotfix.

## EV-AI-051 through EV-AI-055 - MEP-RO-002 Active View Read-Only MEP Report Pack

### Feature

MEP-RO-002 - Active View Read-Only MEP Report Pack

### Evidence IDs

- EV-AI-051: active-view report deterministic routing validation
- EV-AI-052: BUNGE active-view piping report validation
- EV-AI-053: Snowdon HVAC active-view report validation
- EV-AI-054: Snowdon Electrical active-view report validation
- EV-AI-055: active-view missing-parameter report validation

### Validation Summary

- deterministic routes before Ollama
- live active view read at execution time
- active document only
- no linked-document scan
- no model mutation
- no pyRevit console error observed
- no generic Ollama fallback observed
- category/type/level/sample ElementId summaries validated
- missing-parameter reporting validated
- capped large-view handling validated

### Artifacts Path

`WBSO/Testing_Validation/runs/2026-05-07_mep-ro-002-active-view-reports-validated/`

### Status

Runtime validated.

## EV-AI-117 through EV-AI-124 - MEP-WR-005 Split Apply Source Consumption / Staleness Guard

### Feature

MEP-WR-005 - Split Apply Source Consumption / Staleness Guard

### Evidence IDs

- EV-AI-117: MEP-WR-005 initial split apply source-state route validation. Prompt `show split apply source state` returned `[SPLIT APPLY SOURCE STATE]` with dry-run, rollback, and persistent apply unavailable; consumed false; persistent apply currently allowed false.
- EV-AI-118: MEP-WR-005 fresh dry-run and rollback source allowed persistent apply. `dry run split selected pipes` produced 7 candidates and `run split rollback test ROLLBACK-TEST-OK` passed for 5 temporary splits; source state showed persistent apply allowed true.
- EV-AI-119: MEP-WR-005 source consumed after successful MEP-WR-003 apply. `apply split candidate 1 PERSISTENT-SPLIT-OK` applied pipe `3003513`, returned new pipe `3130274`, and source state showed consumed true.
- EV-AI-120: MEP-WR-005 second stale persistent apply blocked before transaction. `apply split candidate 2 PERSISTENT-SPLIT-OK` returned Blocked with transaction opened false, BreakCurve called false, and persistent model changes false.
- EV-AI-121: MEP-WR-004 verification did not clear consumed source. `verify latest split apply` verified pipe `3003513` and new pipe `3130274`; follow-up source-state report still showed consumed true and apply allowed false.
- EV-AI-122: MEP-WR-005 refreshed dry-run and rollback source restored eligibility. New dry-run and rollback-test after the consumed timestamp showed current source fresh true and persistent apply currently allowed true.
- EV-AI-123: MEP-WR-005 generic apply / verification route regression validation. `apply reviewed action` remained MEP-ACT-002 blocked; `verify latest split apply` remained MEP-WR-004.
- EV-AI-124: MEP-WR-005 source-state export/index validation. `show split apply source state` exported through MEP-RO-005 and indexed through MEP-RO-006 with source header `[SPLIT APPLY SOURCE STATE]`.

### Validation Summary

- deterministic source-state routes before Ollama
- consumed-source marker added after successful MEP-WR-003 persistent apply
- stale second apply blocked before transaction
- MEP-WR-004 verification does not clear consumed state
- new rollback-test after consumed timestamp restores eligibility
- source-state report export/index works
- generic LLM output remains non-exportable as deterministic evidence

### Artifacts Path

`WBSO/Testing_Validation/runs/2026-05-25_mep-wr-005-split-apply-source-consumption-guard-validated/`

### Export Artifact

`C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260525_171457`

### Related Commit

`<paste commit hash for "Add split apply source consumption guard">`

### Status

Runtime validated.

## MEP-WR-006 - Split Result Visual Review / Select Elements Helper

### Status

Runtime validated.

### Date

2026-05-26

### Evidence

- EV-AI-125: No-source safety path returned Not ready without selection change or model mutation.
- EV-AI-126: Explicit old ID selection handled missing returned pipe id `3130274` with partial selection only.
- EV-AI-127: Missing returned pipe id `999999999` handled with partial selection only.
- EV-AI-128: ShowElements route operated on the resolving subset and did not mutate model data.
- EV-AI-129: Latest WR-004 verified split result selected original pipe `3003513` and returned pipe `3130262`.
- EV-AI-130: Explicit fresh IDs `3003513` and `3130262` selected both elements successfully.
- EV-AI-131: `show latest split result in model` selected and showed both elements successfully.
- EV-AI-132: `[SPLIT RESULT VISUAL REVIEW]` report exported and indexed at `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260526_180331`.

### Validation Folder

`WBSO/Testing_Validation/runs/2026-05-26_mep-wr-006-split-result-visual-review-validated/`

### Technical Conclusion

MEP-WR-006 provides deterministic UI-only visual review of split results. It resolves latest verified split state or explicit IDs, updates Revit UI selection, optionally calls ShowElements, and performs no model mutation.

## MEP-WR-007 - Split Workflow Session State Dashboard / Reset Helper

Status:
Runtime validated

Date:
2026-05-28

Evidence:

- EV-AI-133: Empty dashboard showed no active split workflow source state and recommended dry-run as next action.
- EV-AI-134: Full workflow state was built through dry-run, rollback-test, persistent apply, verification, visual review, and consumed-source state.
- EV-AI-135: Populated dashboard reported WR-001 through WR-006 state, consumed source marker, selected result IDs, and correct next action.
- EV-AI-136: Reset without `CLEAR-SPLIT-STATE-OK` token was blocked and cleared no state.
- EV-AI-137: Reset preview reported what would be cleared without clearing session state or model data.
- EV-AI-138: Tokenized reset cleared dry-run, rollback-test, reviewed apply, verification, consumed-source, and visual review session states.
- EV-AI-139: Post-reset probes confirmed workflow source state was cleared and apply was blocked before transaction.
- EV-AI-140: `[SPLIT WORKFLOW SESSION STATE]` report exported and indexed at `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260528_112016`.
- EV-AI-141: Explicit post-reset verification of pipe `3087152` and returned pipe `3130262` proved the persistent Revit split remained in the model.
- EV-AI-142: Post-reset `[SPLIT APPLY VERIFICATION REPORT]` exported and indexed at `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260528_112534`.

Validation folder:
`WBSO/Testing_Validation/runs/2026-05-28_mep-wr-007-split-workflow-session-state-reset-validated/`

Technical conclusion:
MEP-WR-007 provides deterministic session-state visibility and explicit tokenized reset for the reviewed split workflow. It clears AI Workbench in-memory/session-local split workflow state only. It does not modify or undo Revit model data.

## MEP-WR-008 - Split Workflow Actionability Classifier / Dashboard Refinement

Status:
Runtime validated

Date:
2026-05-29

Evidence:

- EV-AI-143: WR-008 implementation and static validation. Added deterministic `[SPLIT WORKFLOW ACTIONABILITY STATE]` classifier routes, prompt catalog entry, export header, and passed static validation.
- EV-AI-144: Empty/fresh actionability state validation. `show split workflow actionability` reported no actionable source and recommended `run dry run split selected pipes`.
- EV-AI-145: Dry-run plus rollback-tested actionable source validation. Pipe `3087996` dry-run and rollback-test passed; WR-008 reported actionable dry-run, actionable rollback-tested source, and persistent apply allowed.
- EV-AI-146: Post-apply consumed/stale source classification. After applying pipe `3087996` and returning new pipe `3130282`, WR-008 reported consumed/stale source and persistent apply allowed false.
- EV-AI-147: Verification plus visual review actionability classification. WR-004 verified original pipe `3087996` and returned pipe `3130282`; WR-006 selected both; WR-008 reported actionable verification and visual review target.
- EV-AI-148: WR-007 reset before post-reset diagnostic test. `clear split workflow state CLEAR-SPLIT-STATE-OK` cleared dry-run, rollback-test, reviewed apply, verification, consumed-source, and visual review session state.
- EV-AI-149: Post-reset Not ready diagnostic report generation. Verification, visual review, and apply probes produced Not ready reports without restoring actionable workflow state.
- EV-AI-150: Critical diagnostic/not-ready actionability classification. WR-008 reported only diagnostic/not-ready reports available, no actionable source, and recommended `run dry run split selected pipes`.
- EV-AI-151: QA export registration defect found. Initial `export latest QA report` after WR-008 returned no exportable deterministic report because WR-008 did not populate `latest_deterministic_report`.
- EV-AI-152: QA export registration patch and final export/index validation. `[SPLIT WORKFLOW ACTIONABILITY STATE]` exported and indexed at `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260529_164849`.

Validation folder:
`WBSO/Testing_Validation/runs/2026-05-29_mep-wr-008-split-workflow-actionability-classifier-validated/`

Technical conclusion:
MEP-WR-008 provides deterministic actionability classification for the reviewed split workflow. It separates diagnostic/latest report availability from actionable source availability and is read-only/session-state classification only.

## MEP-WR-009 - Split Apply Preflight Source Revalidation / External Edit Staleness Guard

Status:
Runtime validated and export/index validated

Date:
2026-06-01

Evidence:

- EV-AI-153: WR-009 implementation and static validation. Added deterministic `[SPLIT APPLY PREFLIGHT REVALIDATION]` route/header, integrated preflight into WR-003 before transaction, and passed static/governance validation.
- EV-AI-154: No-source / Not ready preflight validation. `check split apply preflight` after session reset returned Not ready, missing dry-run/rollback source, transaction opened false, BreakCurve called false, and model modified false.
- EV-AI-155: Fresh dry-run plus rollback source preflight passed. Pipe `3087152` with passed rollback-test revalidated current line geometry, source length, candidate projection, segment lengths, and rollback-test success.
- EV-AI-156: WR-003 apply route used WR-009 before transaction. `apply split candidate 1 PERSISTENT-SPLIT-OK` included preflight Passed and opened transaction/called BreakCurve only after preflight passed.
- EV-AI-157: Consumed/stale source blocked after persistent apply. Preflight blocked pipe `3087152` source after apply due consumed source, length mismatch, candidate point no longer inside bounded curve, and segment length failure.
- EV-AI-158: WR-009 QA export/index validation. `[SPLIT APPLY PREFLIGHT REVALIDATION]` exported and indexed at `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260601_104232`.
- EV-AI-159: External edit setup: valid source before pinning. Pipe `3060449` passed dry-run, rollback-test, and preflight before the manual pinning/external edit.
- EV-AI-160: External edit after rollback invalidated source and blocked apply safely. After pinning/source invalidation, WR-009 reported Not ready and WR-003 apply stayed blocked before transaction and BreakCurve.

Validation folder:
`WBSO/Testing_Validation/runs/2026-06-01_mep-wr-009-split-apply-preflight-revalidation-guard-validated/`

Technical conclusion:
MEP-WR-009 validates pre-apply source revalidation for the reviewed split workflow. Fresh sources pass, consumed or stale sources block, missing sources block, external edit/source invalidation blocks safely, and the persistent apply path only proceeds after preflight passes.

## EV-AI-103 through EV-AI-108 - MEP-WR-002 Split Selected Pipes Rollback Test

### Feature

MEP-WR-002 - Split Selected Pipes Rollback Test

### Evidence IDs

- EV-AI-103: MEP-WR-002 no-source rollback-test guard validation
- EV-AI-104: MEP-WR-002 dry-run source available but rollback token missing validation
- EV-AI-105: MEP-WR-002 tokenized route failure and hotfix validation
- EV-AI-106: MEP-WR-002 rollback transaction / BreakCurve probe validation
- EV-AI-107: MEP-WR-002 rollback verification validation
- EV-AI-108: MEP-WR-002 rollback-test export/index validation

### Validation Summary

- deterministic rollback-test routing before Ollama
- explicit `ROLLBACK-TEST-OK` token required before transaction
- initial tokenized route failure preserved as negative validation evidence
- tokenized route hotfix validated
- `PlumbingUtils.BreakCurve` called inside rollback transaction group
- transaction group rolled back
- original pipe ids restored and temporary pipe ids removed
- no persistent model mutation
- rollback-test report exported and indexed

### Artifacts Path

`WBSO/Testing_Validation/runs/2026-05-19_mep-wr-002-split-selected-pipes-rollback-test-validated/`

### Status

Runtime validated.

## EV-AI-109 through EV-AI-116 - MEP-WR-003 Split Selected Pipe Single-Candidate Persistent Reviewed Apply

### Feature

MEP-WR-003 - Split Selected Pipe Single-Candidate Persistent Reviewed Apply

### Evidence IDs

- EV-AI-109: MEP-WR-003 source-not-ready and guard behavior validation
- EV-AI-110: MEP-WR-003 valid source readiness listing validation
- EV-AI-111: MEP-WR-003 missing candidate selection validation
- EV-AI-112: MEP-WR-003 missing persistent token validation
- EV-AI-113: MEP-WR-003 capped untested candidate blocked validation
- EV-AI-114: MEP-WR-003 single-candidate persistent apply validation
- EV-AI-115: MEP-WR-003 reviewed apply export/index validation
- EV-AI-116: MEP-WR-003 post-apply generic guard and Ollama rejection validation

### Validation Summary

- deterministic reviewed-apply routing before Ollama
- explicit candidate selection required
- explicit `PERSISTENT-SPLIT-OK` token required
- only rollback-tested candidates accepted
- capped untested candidate blocked
- exactly one persistent split applied
- original pipe `3003513` split with returned new pipe id `3130288`
- combined length matched original length with `0 mm` delta
- no batch apply
- generic apply/execute prompts remained blocked by MEP-ACT-002
- post-apply repeated dry-run verification inconclusive because active selection was empty
- reviewed apply report exported and indexed

### Artifacts Path

`WBSO/Testing_Validation/runs/2026-05-19_mep-wr-003-single-candidate-pipe-split-reviewed-apply-validated/`

### Status

Core runtime validated.

## EV-AI-089 through EV-AI-094 - MEP-WR-001 Split Selected Pipes Dry Run

### Feature

MEP-WR-001 - Split Selected Pipes Dry Run

### Evidence IDs

- EV-AI-089: MEP-WR-001 no-selection split dry-run validation
- EV-AI-090: BUNGE mixed pipes/fittings split dry-run candidate validation
- EV-AI-091: non-pipe selection split dry-run rejection validation
- EV-AI-092: split dry-run deterministic alias route validation
- EV-AI-093: split dry-run export/index validation
- EV-AI-094: generic Ollama rejection after split dry-run validation

### Validation Summary

- deterministic dry-run routes before Ollama
- live selected elements read at execution time
- selected-elements-only / active-document-only scope validated
- midpoint candidate generation validated for eligible straight pipes
- fittings, near-vertical pipes, too-short pipes, and non-pipe selections skipped correctly
- `[SPLIT SELECTED PIPES DRY RUN]` exported and indexed through MEP-RO-005/006
- generic Ollama response rejected as deterministic export evidence
- no transaction, pipe split, connector traversal, geometry extraction, linked-document scan, parameter write, or model mutation observed

### Artifacts Path

`WBSO/Testing_Validation/runs/2026-05-18_mep-wr-001-split-selected-pipes-dry-run-validated/`

### Status

Runtime validated.

## EV-AI-095 through EV-AI-102 - MEP-ACT-002 Reviewed Proposal / Dry-Run Confirmation Guard

### Feature

MEP-ACT-002 - Reviewed Proposal / Dry-Run Confirmation Guard

### Evidence IDs

- EV-AI-095: MEP-ACT-002 no-source confirmation guard validation
- EV-AI-096: reviewed proposal state detection validation
- EV-AI-097: confirm latest proposal blocked validation
- EV-AI-098: split dry-run state detection and confirm latest dry-run blocked validation
- EV-AI-099: apply/execute reviewed action blocked validation
- EV-AI-100: confirmation guard status alias validation
- EV-AI-101: confirmation guard export/index validation and report_scope hotfix validation
- EV-AI-102: generic Ollama rejection after confirmation guard validation

### Validation Summary

- deterministic confirmation/status routes before Ollama
- no-source state handled safely
- MEP-ACT-001 reviewed proposal state detected
- MEP-WR-001 split dry-run state detected
- confirm/apply/execute prompts blocked with `execution_available: false` and `execution_performed: false`
- `[REVIEWED ACTION CONFIRMATION GUARD]` exported and indexed through MEP-RO-005/006
- report-scope metadata hotfix validated for `session-local reviewed action state / active document only`
- generic Ollama response rejected as deterministic export evidence
- no transaction, action apply, pipe split, connector traversal, geometry extraction, linked-document scan, parameter write, or model mutation observed

### Artifacts Path

`WBSO/Testing_Validation/runs/2026-05-18_mep-act-002-reviewed-confirmation-guard-validated/`

### Status

Runtime validated after report-scope metadata hotfix.

## EV-AI-076 through EV-AI-081 - MEP-RO-006 QA Export Index / Snapshot Registry Pack

### Feature

MEP-RO-006 - QA Export Index / Snapshot Registry Pack

### Evidence IDs

- EV-AI-076: MEP-RO-006 empty-index deterministic handling validation
- EV-AI-077: BUNGE indexed QA export validation
- EV-AI-078: QA export index file integrity validation
- EV-AI-079: QA export index list/latest route validation
- EV-AI-080: Snowdon HVAC second indexed export validation
- EV-AI-081: generic Ollama rejection with no new index entry validation

### Validation Summary

- deterministic index routes before Ollama
- empty-index messages validated
- BUNGE and Snowdon HVAC indexed exports validated
- `qa_export_index.jsonl`, `qa_export_index.csv`, and `latest_export.json` inspected
- total indexed export count incremented from 1 to 2
- generic Ollama response did not create a new index entry
- no model mutation observed

### Artifacts Path

`WBSO/Testing_Validation/runs/2026-05-17_mep-ro-006-qa-export-index-registry-validated/`

### Status

Runtime validated.

## EV-AI-082 through EV-AI-088 - MEP-ACT-001 Reviewed Action Proposal Framework

### Feature

MEP-ACT-001 - Reviewed Action Proposal Framework

### Evidence IDs

- EV-AI-082: MEP-ACT-001 no-selection split proposal validation
- EV-AI-083: BUNGE selected pipes/fittings split proposal preflight validation
- EV-AI-084: non-pipe selection split proposal rejection/preflight validation
- EV-AI-085: future reviewed action proposal validation
- EV-AI-086: unknown reviewed action proposal validation
- EV-AI-087: reviewed action proposal export/index validation
- EV-AI-088: generic Ollama rejection after reviewed proposal validation

### Validation Summary

- deterministic proposal routes before Ollama
- live selection preflight validated
- selected pipes/fittings split proposal classified eligible and skipped elements
- non-pipe selection returned not-ready proposal
- future action placeholders remained proposal-only
- unknown reviewed action proposal returned supported prompt suggestions
- `[REVIEWED ACTION PROPOSAL]` exported through MEP-RO-005 and indexed through MEP-RO-006
- generic Ollama response rejected as deterministic export evidence
- no transaction or model mutation observed

### Artifacts Path

`WBSO/Testing_Validation/runs/2026-05-17_mep-act-001-reviewed-action-proposal-framework-validated/`

### Status

Runtime validated.

## EV-AI-062 through EV-AI-068 - MEP-RO-004 Discipline-Specific Missing Parameter / QA Rules Pack

### Feature

MEP-RO-004 - Discipline-Specific Missing Parameter / QA Rules Pack

### Evidence IDs

- EV-AI-062: MEP-RO-004 deterministic discipline-QA routing validation
- EV-AI-063: MEP-RO-004 duplicate-rule aggregation hotfix validation
- EV-AI-064: BUNGE selected piping QA validation
- EV-AI-065: BUNGE active-view piping QA validation
- EV-AI-066: Snowdon HVAC active-view discipline QA validation
- EV-AI-067: Snowdon Electrical active-view discipline QA validation
- EV-AI-068: Snowdon selected electrical discipline QA validation

### Validation Summary

- deterministic routing before Ollama
- live selected elements read at execution time
- live active-view elements read at execution time
- active document only
- no linked-document scan
- no connector traversal
- no geometry extraction
- no model mutation or parameter writes
- selected and active-view discipline QA reports validated
- duplicate common Mark/Comments rule aggregation hotfix validated
- grouped sample ElementIds deduplicated after hotfix
- capped large-view handling validated

### Artifacts Path

`WBSO/Testing_Validation/runs/2026-05-07_mep-ro-004-discipline-qa-rules-validated/`

### Status

Runtime validated after duplicate-rule aggregation hotfix.

## EV-AI-069 through EV-AI-075 - MEP-RO-005 Exportable QA Report / Evidence Snapshot Pack

### Feature

MEP-RO-005 - Exportable QA Report / Evidence Snapshot Pack

### Evidence IDs

- EV-AI-069: MEP-RO-005 deterministic export routing and empty-state guard validation
- EV-AI-070: BUNGE active-view piping QA evidence export validation
- EV-AI-071: exported file integrity validation for `report.md`, `report.txt`, `metadata.json`, and `artifact_manifest.txt`
- EV-AI-072: alternate export alias validation
- EV-AI-073: Snowdon HVAC capped QA report export validation
- EV-AI-074: Snowdon selected electrical QA report export validation
- EV-AI-075: generic Ollama response rejection validation

### Validation Summary

- deterministic export routing before Ollama
- session-local latest deterministic report state validated
- empty-state guard validated
- timestamped Desktop Results export folder validated
- `report.md`, `report.txt`, `metadata.json`, and `artifact_manifest.txt` generated and inspected
- metadata flags validated for read-only/no-mutation/no-linked-scan/no-connector/no-geometry behavior
- alternate aliases validated
- capped HVAC QA report export validated
- selected electrical QA report export validated
- generic Ollama responses rejected as deterministic QA evidence

### Artifacts Path

`WBSO/Testing_Validation/runs/2026-05-14_mep-ro-005-exportable-qa-evidence-snapshots-validated/`

### Status

Runtime validated.

## EV-AI-056 through EV-AI-061 - MEP-RO-003 MEP System Assignment / Classification QA Pack

### Feature

MEP-RO-003 - MEP System Assignment / Classification Read-Only QA Pack

### Evidence IDs

- EV-AI-056: MEP-RO-003 deterministic system-report routing validation
- EV-AI-057: BUNGE selected piping system assignment validation
- EV-AI-058: BUNGE active-view piping system assignment validation
- EV-AI-059: Snowdon HVAC active-view system assignment validation
- EV-AI-060: Snowdon Electrical active-view system/circuit validation
- EV-AI-061: Snowdon selected electrical system/circuit validation

### Validation Summary

- deterministic routes before Ollama
- live selected elements read at execution time
- live active-view elements read at execution time
- active document only
- no linked-document scan
- no connector traversal
- no geometry extraction
- no model mutation
- no pyRevit console error observed
- no generic Ollama fallback observed
- system assignment summaries validated
- missing/empty/unavailable classifications validated
- capped large-view handling validated

### Artifacts Path

`WBSO/Testing_Validation/runs/2026-05-07_mep-ro-003-system-assignment-qa-validated/`

### Status

Runtime validated.

## EV-AI-161 through EV-AI-167 - COORD-WR-001 to COORD-WR-003 Link Transform Audit and Reviewed Reset

### Feature

COORD-WR-001 - Link Transform Audit / Coordinate Drift Report
COORD-WR-002 - Link Origin Reset Rollback Test
COORD-WR-003 - Single Selected Link Reviewed Origin Reset Apply

### Evidence IDs

- EV-AI-161: COORD-WR-001 link transform audit report validation. `[LINK TRANSFORM AUDIT REPORT]` audited active-document `RevitLinkInstance` transforms read-only and later confirmed 8 loaded links near zero origin.
- EV-AI-162: COORD-WR-002 rollback reset validation. Rollback Test ID `COORD-WR-002-20260603_144729` temporarily moved link `2972572` to zero origin, verified it, rolled back the `TransactionGroup`, and restored original origin with persistent model changes false.
- EV-AI-163: COORD-WR-002 latest-passed rollback source persistence validation. The passed rollback source was stored and read back through `pyrevit script envvar AI_WORKBENCH_COORD_SHARED_STATE` using key `latest_passed_link_origin_reset_rollback_state`.
- EV-AI-164: COORD-WR-003 readiness validation. Apply ID `COORD-WR-003-20260603_145224` confirmed latest passed source, selected link match, origin/basis match, non-zero origin, and delta match without transaction or model mutation.
- EV-AI-165: COORD-WR-003 persistent reviewed apply validation. Apply ID `COORD-WR-003-20260603_145444` accepted `PERSISTENT-LINK-RESET-OK`, opened one transaction, called `MoveElement`, committed, and reset link `2972572` to zero origin.
- EV-AI-166: COORD-WR-001 post-apply audit validation. Audit ID `COORD-WR-001-20260603_145614` reported 8 loaded links, 8 near zero origin, 0 offset links, 0 future reset candidates, and link `2972572` classified `OK_ZERO_ORIGIN`.
- EV-AI-167: COORD workflow QA export/index validation. `[LINK TRANSFORM AUDIT REPORT]` exported to `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260603_150023` with `report.md`, `report.txt`, `metadata.json`, `artifact_manifest.txt`, and updated export indexes.

### Validation Summary

- deterministic coordination routes validated for audit, rollback proof, and reviewed apply
- rollback apply path requires `ROLLBACK-LINK-RESET-OK`
- persistent apply path requires `PERSISTENT-LINK-RESET-OK`
- latest passed rollback source remains available across prompt routes and is not overwritten by invalid/Not Ready reports
- exactly one selected `RevitLinkInstance` was persistently reset
- no batch/all-link reset, linked document mutation, reload/unload, pin/unpin, parameter write, rotation, or UI selection modification
- QA export/index integration validated for `[LINK TRANSFORM AUDIT REPORT]`

### Artifacts Path

`WBSO/Testing_Validation/runs/2026-06-03_coord-wr-001-to-003-link-transform-audit-and-reset-validated/`

### Commit Reference

- `38ab72c8f0fd0da897b50963947104744807b5f2`
- `Add reviewed link origin reset apply`
- changed implementation files: `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`, `AI.extension/lib/prompt_catalog.json`

### Status

Runtime validated.

## EV-AI-173 through EV-AI-180 - COORD-WR-004 Link Origin Reset Post-Apply Verification Helper

### Feature

COORD-WR-004 - Link Origin Reset Post-Apply Verification Helper

### Evidence IDs

- EV-AI-173: COORD-WR-004 implementation and latest apply state persistence fix. COORD-WR-003 stores `latest_link_origin_reset_apply_state` only after a real `Applied` result; COORD-WR-004 reads it for read-only verification only.
- EV-AI-174: COORD-WR-002 rollback validation for current offset link. Rollback Test ID `COORD-WR-002-20260604_151647` passed for link `2972572`, original offset `(0, -2000, 0)` mm, with TransactionGroup rolled back and persistent model changes false.
- EV-AI-175: COORD-WR-003 reviewed persistent apply validation. Apply ID `COORD-WR-003-20260604_152029` reset link `2972572` to zero origin, committed one transaction, and stored valid latest apply state.
- EV-AI-176: COORD-WR-004 selected-link verification. Verification ID `COORD-WR-004-20260604_152647` verified selected link `2972572` matched the latest applied link and remained at zero origin.
- EV-AI-177: COORD-WR-004 no-selection latest-state verification. Verification ID `COORD-WR-004-20260604_152936` verified link `2972572` from latest apply state with no selected `RevitLinkInstance`.
- EV-AI-178: COORD-WR-004 QA export/index validation. `[LINK ORIGIN RESET POST-APPLY VERIFICATION]` exported to `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260604_153013`.
- EV-AI-179: Final COORD-WR-001 full audit and QA export. Audit ID `COORD-WR-001-20260604_153245` reported 8 loaded links, all near zero origin, and exported to `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260604_153603`.
- EV-AI-180: Commit evidence for COORD-WR-004. Latest commit `fefa253 Add link reset post-apply verification` records the implementation in `script.py` and `prompt_catalog.json`.

### Validation Summary

- read-only post-apply verification report validated
- selected-link verification validated
- no-selection latest-state verification validated
- `latest_link_origin_reset_apply_state` persistence validated after `Applied`
- stored element id use remains verification-only
- no apply-by-stored-id behavior introduced
- QA export/index validated for `[LINK ORIGIN RESET POST-APPLY VERIFICATION]`
- final full link transform audit validated all 8 links near zero origin

### Artifacts Path

`WBSO/Testing_Validation/runs/2026-06-04_coord-wr-004-link-origin-reset-post-apply-verification-validated/`

### Daily Log

`DL-2026-06-04-08`

### Week

`2026-W11`

### Status

Runtime validated and export/index validated.

## EV-AI-181 through EV-AI-188 - COORD-WR-005 Link Reset Workflow Status Dashboard

### Feature

COORD-WR-005 - Link Reset Workflow Status Dashboard

### Evidence IDs

- EV-AI-181: Dashboard implementation. Deterministic routes, shared-state aggregation, readiness classification, `[LINK RESET WORKFLOW STATUS]`, and QA export support were implemented.
- EV-AI-182: Shared verification-state correction. COORD-WR-004 now preserves the latest valid verification under `latest_link_origin_reset_post_apply_verification_state` after selection is cleared.
- EV-AI-183: Audit-state persistence. COORD-WR-001 stores `latest_link_transform_audit_state`, allowing COORD-WR-005 to report audit status without running a new audit.
- EV-AI-184: Full workflow validation. Link `2972572` passed initial audit, rollback test `COORD-WR-002-20260605_145813`, readiness, persistent apply `COORD-WR-003-20260605_150040`, and verification `COORD-WR-004-20260605_163104`.
- EV-AI-185: Selected dashboard validation. COORD-WR-005 reported the valid verification state and `Ready / clean`.
- EV-AI-186: No-selection dashboard validation. After clearing selection, the persisted verification remained available and workflow status remained `Ready / clean`.
- EV-AI-187: Final dashboard QA export. `[LINK RESET WORKFLOW STATUS]` exported to `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260605_163936`.
- EV-AI-188: Commit evidence. Commit `7e02f91 Add link reset workflow status dashboard` on `main`.

### Validation Folder

`WBSO/Testing_Validation/runs/2026-06-05_coord-wr-005-link-reset-workflow-status-dashboard-validated/`

### Daily Log

`DL-2026-06-05-08`

### Week

`2026-W11`

### Technical Conclusion

COORD-WR-005 provides selection-independent read-only workflow status reporting from serializable coordination state. Final runtime status was `Ready / clean`, and the dashboard introduced no model mutation behavior.

## EV-AI-189 through EV-AI-196 - COORD-WR-006 Link Reset Workflow History / Run Register

### Feature

COORD-WR-006 - Link Reset Workflow History / Run Register

### Evidence IDs

- EV-AI-189: Implementation and workflow history feature. Added local JSONL/CSV storage, latest-ten reporting, deterministic prompt routes, `[LINK RESET WORKFLOW HISTORY]`, and QA export support.
- EV-AI-190: Local history storage. Added `C:\Users\User\Desktop\Results\AI_Workbench\Workflow_History\link_reset_workflow_history.jsonl` and `link_reset_workflow_history.csv` for meaningful coordination checkpoints.
- EV-AI-191: Cross-session fallback seeding. Added full QA export index scanning for the newest `[LINK RESET WORKFLOW STATUS]` export and defensive `report.txt`/`report.md` parsing.
- EV-AI-192: Fallback recovery validation. With shared status `Not ready`, recovered `Ready / clean` checkpoint `COORD-WR-005-20260605_163912` from `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260605_163936`.
- EV-AI-193: Duplicate prevention validation. A second run against the same fallback export skipped append and preserved record count 1.
- EV-AI-194: Recovered record completeness. The row contained audit `COORD-WR-001-20260605_163837`, rollback `COORD-WR-002-20260605_145813`, apply `COORD-WR-003-20260605_150040`, verification `COORD-WR-004-20260605_163104`, link `2972572`, origins, source export, and workflow status.
- EV-AI-195: Final history QA export. `[LINK RESET WORKFLOW HISTORY]` exported to `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260608_094652`.
- EV-AI-196: Commit evidence. Commit `073eb567325b2155813a97be5533781c2e815d1f Add link reset workflow history register` on `main`.

### Validation Folder

`WBSO/Testing_Validation/runs/2026-06-08_coord-wr-006-link-reset-workflow-history-validated/`

### Daily Log

`DL-2026-06-08-08`

### Week

`2026-W11`

### Technical Conclusion

COORD-WR-006 persists meaningful workflow evidence across Revit/pyRevit session boundaries while remaining filesystem-only with respect to writes. It modifies no Revit model or linked-document data.

## EV-AI-197 through EV-AI-215 - COORD-WR-007 to COORD-WR-015 Coordination Link Evidence and Inventory

### Feature Batch

COORD-WR-007 through COORD-WR-015 provide current-state reconciliation, multi-record reconciliation, readiness advice, evidence bundling, evidence integrity checks, Revit link inventory health, local inventory snapshots, snapshot status, and a consolidated master handover dashboard.

### Evidence IDs

- EV-AI-197: COORD-WR-007 implementation of latest-history current-state reconciliation.
- EV-AI-198: COORD-WR-007 runtime/export. Report `COORD-WR-007-20260611_100416` returned `MATCHES_CURRENT_MODEL`; export `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260611_100512`.
- EV-AI-199: COORD-WR-008 implementation of the multi-record reconciliation dashboard.
- EV-AI-200: COORD-WR-008 runtime/export. Report `COORD-WR-008-20260611_105414` returned `DASHBOARD_ALL_MATCH`; export `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260611_105440`.
- EV-AI-201: COORD-WR-009 implementation and patch adding WR-008 QA-export fallback detection.
- EV-AI-202: COORD-WR-009 runtime/export. Report `COORD-WR-009-20260611_112047` returned `READY_NO_ACTION_CLEAN`; export `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260611_112113`.
- EV-AI-203: COORD-WR-010 implementation of the consolidated workflow evidence bundle.
- EV-AI-204: COORD-WR-010 runtime/export. Report `COORD-WR-010-20260611_113417` returned `BUNDLE_CLEAN_WITH_PARTIAL_SOURCE_LINKS`; export `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260611_113447`.
- EV-AI-205: COORD-WR-011 implementation of the evidence bundle integrity check.
- EV-AI-206: COORD-WR-011 runtime/export. Report `COORD-WR-011-20260611_122146` returned `INTEGRITY_CLEAN_WITH_HISTORY_SOURCE`; export `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260611_122158`.
- EV-AI-207: COORD-WR-012 implementation of the Revit link inventory/external-reference health audit.
- EV-AI-208: COORD-WR-012 runtime/export. Report `COORD-WR-012-20260611_123248` returned `LINK_INVENTORY_HEALTH_OK` for 8 loaded/readable links; export `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260611_123305`.
- EV-AI-209: COORD-WR-013 implementation of the link inventory snapshot register and change detection.
- EV-AI-210: COORD-WR-013 runtime/export. Baseline `COORD-WR-013-20260611_124442` was created, then `COORD-WR-013-20260611_124459` skipped an unchanged duplicate; export `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260611_124510`.
- EV-AI-211: COORD-WR-014 implementation of the snapshot status and drift dashboard.
- EV-AI-212: COORD-WR-014 runtime/export. Report `COORD-WR-014-20260611_141902` returned `SNAPSHOT_STATUS_UNCHANGED_CLEAN`; export `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260611_141936`.
- EV-AI-213: COORD-WR-015 implementation of the coordination link master status dashboard.
- EV-AI-214: COORD-WR-015 runtime/export. Report `COORD-WR-015-20260611_143248` returned `COORD_LINK_MASTER_CLEAN_WITH_HISTORY_SOURCE`; export `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260611_143318`.
- EV-AI-215: Commit evidence. Commit `3a1ab8d4b71c63cb08209e24dfafee939da98033 Add coordination link master status dashboard` on `main`.

### Validation Folder

`WBSO/Testing_Validation/runs/2026-06-11_coord-wr-007-to-015-coordination-link-evidence-inventory-validated/`

### Daily Log

`DL-2026-06-11-09`

### Week

`2026-W12`

### Technical Conclusion

The batch established a durable read-only evidence chain across session boundaries. The final master result was `COORD_LINK_MASTER_CLEAN_WITH_HISTORY_SOURCE`. No Revit model, linked-document, parameter, transform, or UI selection mutation was performed; only COORD-WR-013 wrote local snapshot JSONL/CSV evidence.

## EV-AI-216 through EV-AI-226 - COORD-WR-016 to COORD-WR-020 Coordination Link Final Handover

### Feature Batch

COORD-WR-016 through COORD-WR-020 provide master evidence integrity validation, durable final handover history, read-only register status, register integrity validation, and a consolidated final coordination closeout.

### Evidence IDs

- EV-AI-216: COORD-WR-016 implementation of the coordination link master evidence integrity check.
- EV-AI-217: COORD-WR-016 runtime/export. Report `COORD-WR-016-20260612_142827` returned `COORD_LINK_MASTER_INTEGRITY_CLEAN_WITH_HISTORY_SOURCE`; export `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260612_142857`.
- EV-AI-218: COORD-WR-017 implementation of the local coordination handover JSONL/CSV register and duplicate prevention.
- EV-AI-219: COORD-WR-017 runtime/export. Report `COORD-WR-017-20260612_144543` appended one clean record; report `COORD-WR-017-20260612_144553` skipped the duplicate; export `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260612_144607`.
- EV-AI-220: COORD-WR-018 implementation of the read-only handover register status dashboard.
- EV-AI-221: COORD-WR-018 runtime/export. Report `COORD-WR-018-20260612_162429` returned `COORD_HANDOVER_STATUS_DUPLICATE_CONFIRMED`; export `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260612_162448`.
- EV-AI-222: COORD-WR-019 implementation of the handover register JSONL/CSV and referenced evidence integrity check.
- EV-AI-223: COORD-WR-019 runtime/export. Report `COORD-WR-019-20260612_165421` returned `COORD_HANDOVER_REGISTER_INTEGRITY_CLEAN_WITH_DUPLICATE_STATUS`; export `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260612_165433`.
- EV-AI-224: COORD-WR-020 implementation of the final coordination handover summary.
- EV-AI-225: COORD-WR-020 runtime/export. Report `COORD-WR-020-20260612_171325` returned `COORD_HANDOVER_FINAL_READY_WITH_HISTORY_SOURCE`; export `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260612_171342`.
- EV-AI-226: Commit evidence. Commit `713382d1ec97b453a2f48870172e08796f7f5aa1 Add coordination handover final evidence workflow` on `main`.

### Validation Folder

`WBSO/Testing_Validation/runs/2026-06-12_coord-wr-016-to-020-coordination-link-final-handover-validated/`

### Daily Log

`DL-2026-06-12-10`

### Week

`2026-W12`

### Technical Conclusion

The batch completed the coordination final-handover evidence chain. The final result was `COORD_HANDOVER_FINAL_READY_WITH_HISTORY_SOURCE`. No Revit model, linked-document, parameter, transform, or UI selection mutation occurred; WR-017 wrote only the local Coordination_Handover_History JSONL/CSV register.

## EV-AI-227 through EV-AI-238 - MEP-RO-v1 MEP Read-Only Action Set v1

### Feature

MEP-RO-v1 - MEP Read-Only Action Set v1

### Evidence IDs

- EV-AI-227: Implementation evidence. Added deterministic `[MEP READ ONLY V1 REPORT]` routes and report generation for BIM QA, HVAC/ducting, piping, and electrical active-view/selection checks in `script.py` and `prompt_catalog.json`.
- EV-AI-228: BIM QA empty-selection runtime evidence. Reports `MEP-RO-v1-20260617_155121`, `155207`, `155224`, and `155242` returned `MEP_RO_REPORT_EMPTY_SELECTION`.
- EV-AI-229: Selected piping runtime evidence. Twelve selected pipes validated count, length, selected category/type grouping, and missing-parameter reporting across reports `MEP-RO-v1-20260617_160954`, `161012`, `161033`, `161053`, and `161128`.
- EV-AI-230: Mixed selection runtime evidence. Report `MEP-RO-v1-20260617_161553` validated a 36-element mixed selection health check with model, annotation, and reference-like element counts.
- EV-AI-231: Piping active-view runtime evidence. Pipe fitting connector health and pipe system assignment checks passed in `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7 / TEST [FloorPlan]`; exports `20260617_162700` and `20260617_162913`.
- EV-AI-232: HVAC active-view runtime evidence. Snowdon Towers HVAC / L3 validated duct count, duct list, duct fitting connector health, and duct system assignment; export `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260617_164426`.
- EV-AI-233: HVAC selected-element runtime evidence. Selected 122 ducts validated count, length, and volume-read reporting; volume-read correctly returned partial/skipped where Revit volume values were unavailable; export `20260617_163920`.
- EV-AI-234: Electrical runtime evidence. Snowdon Towers Electrical / `3D - PV Systems - Stripped [ThreeD]` validated fixture/device type listing and missing circuit/system info reports.
- EV-AI-235: Guardrail runtime evidence. `select all ducts` returned `MEP_RO_SELECTION_ACTION_BLOCKED`, preserved UI selection, and exported via `[MEP READ ONLY V1 REPORT]` at `20260617_155754`.
- EV-AI-236: Defect/fix evidence. Fixed `list ducts in active view` crash from missing `_level_name_for_element` and improved type-name fallback; after fix report `MEP-RO-v1-20260617_164406` returned OK.
- EV-AI-237: Classification/fix evidence. Corrected list-output classification so normal 100-row truncation remains `MEP_RO_REPORT_OK` with display metadata.
- EV-AI-238: Commit evidence placeholder. Commit: `<insert latest commit hash from git log -1 --oneline>`; message: `<insert actual commit message used>`.

### Validation Folder

`WBSO/Testing_Validation/runs/2026-06-17_mep-ro-v1-read-only-action-set-validated/`

### Daily Log

`DL-2026-06-17-11`

### Week

`2026-W13`

### Technical Conclusion

MEP-RO-v1 provides deterministic, QA-exportable MEP read-only reporting across BIM QA, piping, HVAC/ducting, and electrical workflows. It reads active-view and selected-element context only, blocks selection-changing routes for future MEP-SEL-v1, and performs no Revit model, linked-document, parameter, transaction, or UI selection mutation.

## EV-AI-239 through EV-AI-247 - MEP-SEL-v1 MEP Selection-Only Action Set v1

### Feature

MEP-SEL-v1 - MEP Selection-Only Action Set v1

### Evidence IDs

- EV-AI-239: Implementation evidence. Added deterministic `[MEP SELECTION V1 REPORT]` routes for active-view MEP UI selection-only workflows in `script.py` and `prompt_catalog.json`.
- EV-AI-240: Piping selection runtime evidence. Report `MEP-SEL-v1-20260618_123008` selected 18 active-view pipes in `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7 / TEST [FloorPlan]`; result `MEP_SEL_SELECTION_OK`, UI selection modified true, model modified false.
- EV-AI-241: Piping connector selection defect/fix evidence. Initial `select unconnected pipe fittings` returned 84 false skipped/unreadable fittings; after connector-inspection patch report `MEP-SEL-v1-20260618_155601` checked 97 fittings, found 0 candidates, 0 skipped, and preserved selection.
- EV-AI-242: HVAC selection runtime evidence. Reports `MEP-SEL-v1-20260618_123859` and `MEP-SEL-v1-20260618_123926` validated selection of 307 ducts and zero-candidate behavior for ducts without system assignment in Snowdon Towers Sample HVAC / L3.
- EV-AI-243: HVAC connector selection runtime evidence. Report `MEP-SEL-v1-20260618_155850` checked 285 duct fittings, found 0 unconnected candidates, 0 skipped/unreadable elements, and exported at `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260618_155922`.
- EV-AI-244: Electrical selection runtime evidence. Report `MEP-SEL-v1-20260618_124449` selected 499 active-view electrical fixtures/devices in Snowdon Towers Sample Electrical / `3D - PV Systems - Stripped [ThreeD]`.
- EV-AI-245: Electrical QA-derived selection runtime evidence. Report `MEP-SEL-v1-20260618_124648` selected 29 devices without circuit/system info; export `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260618_124834`.
- EV-AI-246: QA export evidence. Confirmed `[MEP SELECTION V1 REPORT]` exports preserve source prompt/header/document/view metadata at `20260618_124834` and `20260618_155922`.
- EV-AI-247: Commit evidence placeholder. Commit: `<insert latest commit hash from git log -1 --oneline>`; message: `Add MEP selection-only v1 actions`.

### Validation Folder

`WBSO/Testing_Validation/runs/2026-06-18_mep-sel-v1-selection-only-action-set-validated/`

### Daily Log

`DL-2026-06-18-12`

### Week

`2026-W13`

### Technical Conclusion

MEP-SEL-v1 provides deterministic, QA-exportable Revit UI selection-only workflows for active-view MEP QA. It may modify UI selection when candidates exist, but never modifies Revit model data, linked documents, parameters, systems, connectors, views, sheets, or tags. Zero-candidate reports preserve existing selection.

## EV-AI-248 through EV-AI-258 - MEP QA Workbench Evidence Pipeline

### Feature Batch

MEP QA Workbench Evidence Pipeline - exports, bundles, dashboards, named-view drilldown, and project issue indexing

### Date

2026-06-19 / 2026-W13

### Evidence IDs

- EV-AI-248: Implementation batch evidence. Added MEP-RO-EXPORT-v1, MEP-QA-BUNDLE-v1, MEP-QA-DASHBOARD-v1, MEP-QA-VIEWSCAN-v1, MEP-QA-VIEWDETAIL-v1, MEP-QA-VIEWEXPORT-v1, and MEP-QA-ISSUEINDEX-v1 as a layered MEP QA evidence pipeline.
- EV-AI-249: Structured export evidence. MEP-RO-EXPORT-v1 exported active-view pipe, duct, electrical device, and circuit/system issue rows with structured CSV/JSON schemas.
- EV-AI-250: Active-view bundle evidence. MEP-QA-BUNDLE-v1 generated active-view QA evidence bundles for piping, HVAC, and electrical contexts.
- EV-AI-251: Active-view dashboard evidence. MEP-QA-DASHBOARD-v1 classified BUNGE piping and Snowdon HVAC as GREEN and Snowdon Electrical as YELLOW.
- EV-AI-252: Multi-view scan evidence. MEP-QA-VIEWSCAN-v1 scanned eligible floor plan views and produced project/view matrix results without active-view switching.
- EV-AI-253: Named-view detail evidence. MEP-QA-VIEWDETAIL-v1 produced focused named-view drilldowns for First Floor, TEST, L3, and Model Linking - Parking.
- EV-AI-254: Named-view issue export evidence. MEP-QA-VIEWEXPORT-v1 exported named-view issue rows, including 6 First Floor pipe fitting issues and 125 Model Linking - Parking electrical issues.
- EV-AI-255: Project issue index evidence. MEP-QA-ISSUEINDEX-v1 produced navigable issue queues: 8 BUNGE rows, EMPTY Snowdon HVAC, and 29 Snowdon Electrical rows.
- EV-AI-256: QA export registration evidence. Validated report headers `[MEP EXPORT V1 REPORT]`, `[MEP QA BUNDLE V1 REPORT]`, `[MEP QA DASHBOARD V1 REPORT]`, `[MEP QA VIEWSCAN V1 REPORT]`, `[MEP QA VIEWDETAIL V1 REPORT]`, `[MEP QA VIEWEXPORT V1 REPORT]`, and `[MEP QA ISSUE INDEX V1 REPORT]`.
- EV-AI-257: Safety/governance evidence. Read-only tools opened no transactions, modified no model data, changed no UI selection, and did not switch active views; file writes were limited to explicit export/bundle commands outside the repository.
- EV-AI-258: Commit evidence. Commits: `263796e` Add MEP structured QA export v1; `c2d9aeb` Add MEP active view QA bundle v1; `not found in local git log` Add MEP active view QA dashboard v1; `c74aa9b` Add MEP multi-view QA scan v1; `bdf7a26` Add MEP named view QA detail v1; `1073deb` Add MEP named view QA export v1; `3c3eb18` Add MEP project issue index v1.

## EV-AI-259 through EV-AI-268 - AI Workbench Console Layer and MEP Issue Index Export

Status: Runtime validated

Date: 2026-06-24 / 2026-06-25

Week: `2026-W14`

Validation folder: `WBSO/Testing_Validation/runs/2026-06-25_ai-workbench-console-layer-and-issue-index-export-validated/`

- EV-AI-259: MEP-QA-ISSUEINDEX-EXPORT-v1 implementation and BUNGE runtime validation. `export mep project issue index` returned `[MEP QA ISSUE INDEX EXPORT V1 REPORT]`, `MEP_QA_ISSUEINDEX_EXPORT_OK`, 15 eligible views scanned, 24 issue candidates, 8 issue-index rows exported, and model/UI selection modified false.
- EV-AI-260: Snowdon HVAC empty issue-index export validation. The export returned `MEP_QA_ISSUEINDEX_EXPORT_EMPTY`, scanned 11 views, counted 1105 MEP inventory items, found 0 issue candidates, and generated empty CSV/JSON evidence for traceability.
- EV-AI-261: Snowdon Electrical issue-index export validation. The export returned `MEP_QA_ISSUEINDEX_EXPORT_OK`, scanned 30 views, counted 3196 MEP inventory items, found 350 issue candidates, and exported 29 issue-index rows.
- EV-AI-262: QA export/index validation for `[MEP QA ISSUE INDEX EXPORT V1 REPORT]`. `export latest QA report` preserved source prompt `export mep project issue index`, source header, source document, active view, and model-modified false.
- EV-AI-263: AI-WORKBENCH-CONSOLE-v1 deterministic command autocomplete validation. The console became the default user-facing interface, `export mep` surfaced deterministic MEP suggestions, and Tab accepted a high-confidence suggestion.
- EV-AI-264: Unsupported prompt blocking validation. Prompt `banana cut all pipes with dragon` was blocked, did not resolve to `select all pipes`, did not run, and did not modify model data or UI selection.
- EV-AI-265: AI-WORKBENCH-SINGLE-CONSOLE-v1 result routing validation. Deterministic command output now appears inside the Console tab while Ollama Chat remains available separately.
- EV-AI-266: Console result summary and UX validation. The summary parser extracted report header, feature ID/name, result classification, export folder, total issue candidates, skipped/unreadable count, and warnings; Copy result and Open export folder controls were added.
- EV-AI-267: Revit context panel and selection-gate validation. The context panel no longer fails on invalid `OST_ElectricalDevices`; `select all pipes` resolves as selection-only, displays the confirmation card, and enables Run after confirmation.
- EV-AI-268: Remaining selection dispatch bottleneck evidence. Confirmed selection-only execution currently returns `[MEP READ ONLY V1 REPORT]` with `MEP_RO_SELECTION_ACTION_BLOCKED`, so the UI gate is validated but backend dispatch to MEP-SEL-v1 remains future work. Commit evidence: `51a907e` issue-index export, `95e052a` console v1, `f1dd511` console UX, `546b843` single-tab routing, `134106d` selection gate; result-summary parser exact commit message was not found and is documented as included in later console integration.

Technical conclusion: the batch adds a deterministic ModelMind console layer for command discovery, safety preview, one-tab deterministic result output, and issue-index export evidence. It preserves no-model-modification governance. Selection-only execution from the console remains a documented integration bottleneck rather than a completed selection mutation path.

### Validation Folder

`WBSO/Testing_Validation/runs/2026-06-19_mep-qa-workbench-evidence-pipeline-validated/`

### Technical Conclusion

The MEP QA Workbench batch converts active-view MEP diagnostics into a layered evidence pipeline covering structured exports, active-view bundles, dashboards, multi-view scans, named-view drilldowns, named-view issue exports, and project-level issue indexing while preserving strict Revit model-safety boundaries.
## EV-AI-289 through EV-AI-307 - AI Workbench Guided Console Workflow

Status: Runtime validated

Date range: 2026-06-25 to 2026-06-29

Week: `2026-W14`

Daily log references:

- DL-2026-06-25-02 - Selection dispatch fix and runtime validation
- DL-2026-06-26-01 - Console history and history file validation
- DL-2026-06-29-01 - History viewer, context suggestions, recipe planner, navigator, guided start, guided coach, and layout polish validation

Validation folder: `WBSO/Testing_Validation/runs/2026-06-29_ai-workbench-guided-console-workflow-validated/`

- EV-AI-289: AI-WORKBENCH-SELECTION-DISPATCH-v1 implementation evidence. Confirmed selection-only console prompts normalize to existing MEP-SEL-v1 aliases before dispatch while the MEP-RO guard remains preserved for unconfirmed or unsafe paths.
- EV-AI-290: Selection dispatch runtime validation. Prompt `select all pipes` with confirmation checked returned `[MEP SELECTION V1 REPORT]`, feature `MEP-SEL-v1`, classification `MEP_SEL_SELECTION_OK`, selected 18 pipes, UI selection modified true, model modified false, transaction opened false.
- EV-AI-291: Selection dispatch negative/regression validation. `select unconnected pipe fittings` returned a clean MEP-SEL empty result with 0 candidates and no MEP-RO guard; unsupported prompt `banana cut all pipes with dragon` remained blocked; report/export regressions passed.
- EV-AI-292: AI-WORKBENCH-CONSOLE-HISTORY-v1 implementation evidence. Executed console commands now write local command history under `C:\Users\User\Desktop\Results\AI_Workbench\Console_History`.
- EV-AI-293: Console history runtime validation. `console_history.jsonl`, `console_history.csv`, `latest_console_result.txt`, `latest_console_result.json`, and `latest_console_result.md` were generated; unsupported no-match prompt was not logged.
- EV-AI-294: AI-WORKBENCH-CONSOLE-HISTORY-VIEWER-v1 implementation evidence. Added history viewer, latest result viewer, and session summary export routes and controls.
- EV-AI-295: History viewer/session summary runtime validation. `[AI WORKBENCH CONSOLE HISTORY VIEWER REPORT]`, `[AI WORKBENCH LATEST CONSOLE RESULT REPORT]`, and `[AI WORKBENCH CONSOLE SESSION SUMMARY EXPORT REPORT]` were validated with no malformed history lines and model/UI safety preserved.
- EV-AI-296: AI-WORKBENCH-CONTEXT-SUGGESTIONS-v1 implementation evidence. Added context-aware next-action recommendations from active context, latest result, recent history, and prompt catalog availability.
- EV-AI-297: Context suggestions runtime validation. Prompt `suggest next ai workbench actions` returned `[AI WORKBENCH CONTEXT SUGGESTIONS REPORT]`, classification `AI_WORKBENCH_CONTEXT_SUGGESTIONS_OK`, detected Piping context, 97 fittings, 18 pipes, and eight suggestions without automatic execution.
- EV-AI-298: AI-WORKBENCH-RECIPE-PLANNER-v1 implementation evidence. Added deterministic QA evidence workflow recipe planning.
- EV-AI-299: Recipe planner runtime validation. Prompt `create mep qa evidence recipe` returned four baseline steps, two optional piping review steps, execute automatically false for every step, model modified false, and UI selection modified false.
- EV-AI-300: AI-WORKBENCH-RECIPE-NAVIGATOR-v1 implementation evidence. Added safe prompt-loading controls for Load next, Load recipe step, Load QA start, Clear loaded, and navigator status.
- EV-AI-301: Recipe navigator runtime validation. Navigator buttons loaded prompts only, did not execute commands, preserved selection confirmation requirements, and kept unsupported prompts blocked.
- EV-AI-302: AI-WORKBENCH-GUIDED-START-v1 implementation evidence. Added beginner-facing Start Here guided workflow panel and deterministic help report.
- EV-AI-303: Guided Start runtime validation. Start, Next, Plan, Evidence, Review, and Help buttons loaded prompts only; `[AI WORKBENCH GUIDED START HELP REPORT]` was returned; model/UI safety preserved.
- EV-AI-304: AI-WORKBENCH-GUIDED-COACH-v1 implementation evidence. Added Guided Coach panel for result interpretation and next recommended prompt.
- EV-AI-305: Guided Coach runtime validation. Dashboard GREEN recommended issue-index export, issue-index export OK recommended latest QA export, QA export complete recommended session summary export, and Load recommended next loaded prompt only.
- EV-AI-306: AI-WORKBENCH-CONSOLE-LAYOUT-POLISH-v1 implementation evidence. Added compact/collapsible Guided Start and Guided Coach panels, grouped controls, hidden mini labels, and result summary minimum height.
- EV-AI-307: Layout polish runtime validation. Collapsible panels restored correctly, Result/History/Guidance/Maintenance controls remained functional, result summary readability improved, dashboard/export/QA export regressions passed, selection confirmation remained required, banana prompt remained blocked, and no model modification or active-view switching occurred.

Commit evidence: `not found in local git log` selection dispatch; `b38f488` console history; `7d07e07` history viewer; `b14867a` context suggestions; `ec771d7` recipe planner; `70f56ac` recipe navigator; `9a98076` guided start; `c366708` guided coach; `f037b07` layout polish.

Technical conclusion: the guided console workflow batch converts ModelMind from a deterministic command surface into a guided workflow environment for command traceability, recommendations, recipe planning, prompt-loading navigation, guided onboarding, result coaching, and compact layout. It preserves no-model-modification governance; UI selection mutation remains isolated to confirmed MEP-SEL-v1 routes.

## EV-AI-308 through EV-AI-319 - AI Workbench Console UX Runtime Batch

Status: Runtime validated

Date: 2026-07-06

Week: `2026-W15`

Validation folder: `WBSO/Testing_Validation/runs/2026-07-06_ai-workbench-console-ux-runtime-batch-validated/`

- EV-AI-308: AI-WORKBENCH-SELECTION-CONFIRM-COMPACT-v1 implementation and runtime validation. Commit `a7333d1`; compact selection confirmation displayed for `select all pipes`, Run stayed disabled until confirmation, and confirmed execution routed to MEP-SEL-v1.
- EV-AI-309: Compact selection runtime result. `[MEP SELECTION V1 REPORT]`, `MEP_SEL_SELECTION_OK`, candidate count 18, selected count 18, UI selection modified true, model modified false, transaction opened false.
- EV-AI-310: Compact selection negative/regression validation. `select unconnected pipe fittings` returned `MEP_SEL_EMPTY_ACTIVE_VIEW_RESULT`; dashboard did not require selection confirmation; banana prompt remained blocked.
- EV-AI-311: AI-WORKBENCH-CONSOLE-SHELL-SIMPLIFY-v1 runtime validation. Commit `30505cb`; Console tab is primary, legacy tabs hidden behind Show Advanced Tabs, and utility controls collapsed behind Show Controls without breaking existing commands.
- EV-AI-312: AI-WORKBENCH-ALIAS-ROUTE-HARDENING-v1 runtime validation. Commit `ee64658`; `show latest result` and `show latest console result` route to `[AI WORKBENCH LATEST CONSOLE RESULT REPORT]` and no longer route to split visual review. Historical bad row from 2026-06-30 15:37:38 is retained as defect evidence.
- EV-AI-313: AI-WORKBENCH-SAFE-CATALOG-VIEW-v1 runtime validation. Commit `75e1c38`; Safe Catalog hides legacy/model-write/reviewed-action commands by default, Advanced Commands reveals them only for development review, and reviewed/model-write Run remains guarded/disabled.
- EV-AI-314: Safe Catalog regression validation. MEP-SEL-v1 routes, dashboard, history, context suggestions, recipe planner, latest-result aliases, and banana prompt blocking all remained valid.
- EV-AI-315: AI-WORKBENCH-VISUAL-v1 runtime validation. Commit `a44e4bc`; `[AI WORKBENCH VISUAL PREVIEW REPORT]` returned `AI_WORKBENCH_VISUAL_PREVIEW_OK`, Piping context, 97 pipe fittings, 18 pipes, and four cards: View Context, Latest Result, Issues / Candidates, Safe Next Action.
- EV-AI-316: Visual Preview refresh and safety validation. Dashboard, selection, suggestions, and recipe planner results refreshed Visual Preview; model modified false, UI selection modified false, external files written false for the visual status report.
- EV-AI-317: AI-WORKBENCH-VISUAL-ACTION-CARDS-v1 runtime validation. Commit `7faea67`; Visual Action Cards load prompts only, do not execute commands, do not write history on load, and preserve selection confirmation for selection-only prompts.
- EV-AI-318: Visual Action Cards export workflow validation. Manual `export mep project issue index` returned `[MEP QA ISSUE INDEX EXPORT V1 REPORT]`, `MEP_QA_ISSUEINDEX_EXPORT_OK`, generated 11 files, found 24 issue candidates, and wrote to `C:\Users\User\Desktop\Results\AI_Workbench\MEP_Issue_Index_Exports\20260706_153525_export_mep_project_issue_index`.
- EV-AI-319: Batch safety/governance evidence. No Revit model mutation, transaction, TransactionGroup, parameter write, active-view switch, linked-document mutation, or automatic command execution was introduced; selection-only commands still require explicit confirmation; MEP-SEL-v1 dispatch and MEP-RO guard are preserved.

Known pending follow-up: AI-WORKBENCH-NEXT-STEP-ENGINE-v1 is pending runtime validation and is not recorded here as completed, implemented, pushed, or validated.

Technical conclusion: the Console UX runtime batch improves safety clarity and operator workflow through compact selection confirmation, simplified shell controls, hardened alias resolution, safe catalog filtering, read-only Visual Preview cards, and load-only Visual Action Cards while preserving deterministic routing and Revit model-safety boundaries.

## EV-AI-320 through EV-AI-323 - AI Workbench Next-Step Workflow Anchor Batch

Status: Runtime validated

Date: 2026-07-08

Week: `2026-W16`

Daily log references:

- DL-2026-07-08-01 - AI-WORKBENCH-NEXT-STEP-ENGINE-v1
- DL-2026-07-08-02 - AI-WORKBENCH-WORKFLOW-ANCHOR-v1

Validation folder: `WBSO/Testing_Validation/runs/2026-07-08_ai-workbench-next-step-workflow-anchor-validated/`

- EV-AI-320: AI-WORKBENCH-NEXT-STEP-ENGINE-v1 implementation evidence. Commit `046ba44`; added one deterministic next-step resolver used by Guided Coach, Visual Preview, Utility Load Next, and Recipe Navigator Load Next.
- EV-AI-321: AI-WORKBENCH-NEXT-STEP-ENGINE-v1 runtime validation. `show ai workbench next step status` returned `[AI WORKBENCH NEXT STEP REPORT]`, feature `AI-WORKBENCH-NEXT-STEP-ENGINE-v1`, classification `AI_WORKBENCH_NEXT_STEP_OK`, Piping context, auto-run false, and no model/UI/active-view/external writes from the status route.
- EV-AI-322: AI-WORKBENCH-WORKFLOW-ANCHOR-v1 implementation evidence. Commit `157e995`; added workflow-relevant latest-result anchoring so meta/status/viewer commands do not overwrite the workflow state used by Load Next.
- EV-AI-323: AI-WORKBENCH-WORKFLOW-ANCHOR-v1 runtime validation and discovered QA export anchor defect. Dashboard, issue-index export, Next Step status, latest-result viewer, and recipe planner anchor scenarios passed; `export latest QA report` was found to still use raw latest meta output instead of the workflow anchor and is recorded as pending `AI-WORKBENCH-QA-EXPORT-ANCHOR-v1` follow-up, not completed.

Runtime context: `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`, `TEST [FloorPlan]`, Piping, 97 pipe fittings, 18 pipes.

Technical conclusion: the batch unifies next-step guidance across AI Workbench surfaces and adds workflow anchoring for latest-result precision. It preserves load-only guidance, explicit manual Run boundaries, MEP-SEL confirmation, MEP-RO guards, Safe Catalog filtering, and no Revit model mutation.

## EV-AI-324 through EV-AI-328 - AI Workbench QA Export Anchor

Status: Implemented, statically validated, live Revit validated, committed, and pushed

Date: 2026-07-10

Week: `2026-W16`

Daily log: `DL-2026-07-10-01` (hours require manual entry)

Validation folder: `WBSO/Testing_Validation/runs/2026-07-10_ai-workbench-qa-export-anchor-validated/`

- EV-AI-324: AI-WORKBENCH-QA-EXPORT-ANCHOR-v1 implementation and static validation. Commit `378f5c3` (`Use workflow anchor for QA report export`); implementation in `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`; prompt catalog unchanged; requested static and governance checks passed.
- EV-AI-325: Successful workflow-source QA export runtime validation. The issue-index -> latest-result viewer -> Load Next -> QA export chain completed at `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260710_162242`, generated the four existing snapshot files, and updated all three QA indexes. The successful run reported `Export source mode: raw latest`; workflow-anchor fallback is implemented but was not directly selected in this run.
- EV-AI-326: QA export completion to Console session-summary handoff. `QA_REPORT_EXPORT_COMPLETE` enabled handoff; manual session-summary export wrote five files at `C:\Users\User\Desktop\Results\AI_Workbench\Console_History\Session_Summaries\20260710_162730_console_session_summary`, with 90 history entries read, 20 included, and 0 malformed.
- EV-AI-327: `QA_REPORT_EXPORT_NOT_READY` and failed-handoff prevention. The not-ready path returned before QA folder/file creation, reported all safety flags false, and the Next Step Engine blocked session-summary handoff while recommending `export latest QA report` retry.
- EV-AI-328: Regression, safety, and Console status evidence. Dashboard/Visual Preview/latest-result/Safe Catalog/unsupported-prompt checks passed; no model mutation occurred. `show ai workbench next step satus` was a test-input typo and is not recorded as a software defect.

Evidence paths:

- `C:\Users\User\Desktop\Results\AI_Workbench\MEP_Issue_Index_Exports\20260710_161832_export_mep_project_issue_index`
- `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260710_162242`
- `C:\Users\User\Desktop\Results\AI_Workbench\Console_History\Session_Summaries\20260710_162730_console_session_summary`
- `C:\Users\User\Desktop\Results\AI_Workbench\MEP_Issue_Index_Exports\20260710_163746_export_mep_project_issue_index`

Technical conclusion: AI-WORKBENCH-QA-EXPORT-ANCHOR-v1 closes the downstream export-source gap and establishes the safe evidence chain Dashboard -> Issue Index -> QA Export -> Console Session Summary. Failed QA exports do not advance. `AI-WORKBENCH-EVIDENCE-RUNBOOK-v1` remains pending.
