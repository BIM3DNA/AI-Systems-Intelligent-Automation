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
