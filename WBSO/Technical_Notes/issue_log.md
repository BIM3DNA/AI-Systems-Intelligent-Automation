# Issue Log

## Project

AI Systems & Intelligent Automation

## Logging Rule

This file tracks actual technical issues, cleanup decisions, unresolved architecture questions, and validation findings related to the 2026 migration + refactor stream.

---

## ISSUE-2026-04-08-001

**Title:** ModelMind prompt tree was backed by hardcoded UI state instead of a structured prompt registry  
**Status:** Resolved in code, runtime revalidation pending  
**Type:** Architecture / data model

### Description

The ModelMind prompt tree was populated directly from a hardcoded dictionary embedded in `script.py`. This made prompt inventory changes hard to audit and blurred the difference between prompt definitions, generated code, and reviewed assets.

### Action Taken

- introduced `AI.extension/lib/prompt_catalog.json`
- introduced `AI.extension/lib/ai_prompt_registry.py`
- moved prompt-tree rebuilding to structured catalog loading
- added a separate approved-recipe branch sourced from `approved_recipes.json`

### Remaining Work

- validate prompt-tree behavior inside pyRevit/Revit
- confirm tree filtering and approved-recipe refresh at runtime

---

## ISSUE-2026-04-08-002

**Title:** AI Agent tab lacked implemented safety semantics despite visible controls  
**Status:** Partially resolved  
**Type:** UX / safety architecture

### Description

The AI Agent tab already exposed controls for planning and command management, but the button semantics were not implemented in code. This created a mismatch between visible affordances and actual guarded behavior.

### Action Taken

- added local agent session helper
- defined plan-only behavior for `Run Agent`
- defined reviewed execution behavior for `Execute Plan`
- implemented session toggle/reset behavior
- kept destructive tools off by default
- kept undo disabled with visible explanation because robust rollback is not implemented

### Remaining Work

- validate real pyRevit/Revit behavior of plan generation and execution
- assess whether the current plan-matching heuristics need refinement after live use

---

## ISSUE-2026-04-08-003

**Title:** Theme preference was not persisted locally  
**Status:** Resolved in code, runtime revalidation pending  
**Type:** UX / local state

### Description

The AI window had no persisted theme preference. Each launch reverted to the same visual state and there was no explicit light/dark mode control.

### Action Taken

- added a local settings helper under `AI.extension/lib/`
- added a theme toggle in the window header
- persisted the selected theme locally

### Remaining Work

- confirm state persistence during real pyRevit relaunch

---

## ISSUE-2026-04-08-004

**Title:** This refactor pass is not yet runtime-validated in Snowdon Towers Sample HVAC  
**Status:** Open  
**Type:** Validation / runtime

### Description

The requested validation scenarios were implemented and/or mapped into the structured prompt catalog, but they were not executed in a live Revit session during this workspace-only pass.

### Impact

- baseline-preservation is strongly intended but not yet re-proven
- HVAC workflow claims remain unvalidated until executed in Revit
- Ollama chat runtime continuity after refactor remains unproven

### Required Next Validation

- confirm the AI tab still loads in pyRevit
- confirm the button still opens the UI
- confirm Ollama Chat still answers a simple prompt
- confirm ModelMind deterministic prompts run on Snowdon Towers Sample HVAC
- confirm AI Agent plan/execution behavior in a real session

---

## ISSUE-2026-04-08-005

**Title:** ModelMind reviewed-code approval path allowed Dynamo / DesignScript code to execute in pyRevit  
**Status:** Resolved in code, live post-fix revalidation pending  
**Type:** Runtime safety / reviewed-code validation

### Description

Generated reviewed code was allowed to reach execution even when it referenced unsupported Dynamo / DesignScript runtime modules and APIs.

### Impact

- unsafe or non-functional reviewed code could be executed
- pyRevit compatibility was not enforced before approval
- user trust in the reviewed-code path was weakened

### Action Taken

- added `ai_reviewed_code.py` validator
- blocked unsupported reviewed-code imports/modules/patterns before approval
- disabled approval when reviewed code is blocked
- surfaced blocked modules/patterns clearly in the ModelMind output pane
- revalidated reviewed code again immediately before execution

### Remaining Work

- run a live Revit check confirming DesignScript/Dynamo code is blocked before execution

---

## ISSUE-2026-04-08-006

**Title:** Approved recipes needed an explicit post-success save flow with required metadata  
**Status:** Resolved in code, live post-fix revalidation pending  
**Type:** UX / reviewed asset governance

### Description

Approved recipe persistence needed to remain restricted to successful reviewed-code executions and capture explicit metadata instead of relying on implicit prompt-tree state.

### Action Taken

- kept failed reviewed-code runs ineligible for approved recipe storage
- added explicit `Save as Approved Recipe` action after successful reviewed-code execution
- required metadata fields for save:
  - `id`
  - `title`
  - `category`
  - `role`
  - `risk_level`
  - `source_prompt`
  - `enabled`
- reloaded the ModelMind tree after save

### Remaining Work

- confirm the save dialog and immediate approved-branch refresh in live Revit

---

## ISSUE-2026-04-09-001

**Title:** Header layout and dark-mode readability still needed product polish after the baseline refactor  
**Status:** Resolved in code, live UI revalidation pending  
**Type:** UI / usability

### Description

The AI Workbench still had top-area layout pressure and several dark-mode readability issues, especially around dropdowns, tree text, labels, and disabled buttons.

### Action Taken

- moved theme/close controls fully to the top-right corner
- stabilized header/model/status layout with grid-based spacing
- added dark-mode resource styling for dropdowns and tree text
- improved disabled-button contrast for key gated actions
- kept light mode behavior intact unless necessary

### Remaining Work

- verify header alignment in live Revit
- verify dark-mode dropdown/tree/disabled-button readability in live Revit

---

## ISSUE-2026-04-09-002

**Title:** AI Agent scope was too broad for the current supported runtime  
**Status:** Resolved in code, live planner revalidation pending  
**Type:** Product scope / deterministic planning

### Description

The AI Agent surface still implied broader autonomous/runtime modes than the implementation actually supported.

### Action Taken

- narrowed AI Agent to a deterministic reviewed-planner
- removed placeholder runtime choices from the active UX
- improved supported-intent matching for duct-focused BIM planner requests
- added clearer guidance when a planner request is unsupported

### Remaining Work

- verify the new deterministic planner cases in live Revit:
  - count selected ducts
  - count all ducts in active view
  - list ducts in active view

---

## ISSUE-2026-04-09-003

**Title:** AI Agent lacked a real provider-backed planning path and clear missing-key behavior  
**Status:** Resolved in code, live provider revalidation pending  
**Type:** Provider integration / runtime configuration

### Description

The AI Agent surface had been narrowed conceptually, but it still lacked a real cloud-backed planning path for intent normalization and did not surface environment-based provider availability clearly.

### Action Taken

- reused `Openai_Server/chatgpt_service.py` for planner normalization
- added `Model_Service/ModelService.py` wrapper methods for provider-state checks and intent normalization
- limited cloud output to supported action selection or rejection
- kept all execution inside the deterministic/reviewed pyRevit path
- made missing `OPENAI_API_KEY` disable cloud mode with explicit UI guidance
- added provider-state handling for request failures without exposing keys

### Remaining Work

- verify missing-key UI behavior in live Revit
- verify cloud planner normalization in live Revit with a valid environment key
- verify cloud request failure handling/fallback in live Revit

---

## ISSUE-2026-04-09-004

**Title:** ModelMind input/actions still needed layout cleanup for real workbench use  
**Status:** Resolved in code, live UI revalidation pending  
**Type:** UI / product polish

### Description

ModelMind still used a cramped input/action layout that reduced the usable input width and gave reviewed actions too much visual competition with the prompt tree.

### Action Taken

- widened the ModelMind input field toward the right-side tree edge
- moved action buttons below the input
- kept prompt/recipe tree at the right
- kept reviewed code secondary through the existing collapsible reviewed-code section

### Remaining Work

- verify the new ModelMind input/button spacing in live Revit
- confirm the reviewed-code secondary presentation still feels clear during real use

---

## ISSUE-2026-04-10-001

**Title:** AI Agent provider diagnostics incorrectly mixed missing-key guidance with real cloud request failures  
**Status:** Resolved in code, live verification pending  
**Type:** Provider diagnostics / UI honesty

### Description

Current live findings showed that the AI Agent provider messaging could simultaneously report a cloud request failure and also instruct the user to set `OPENAI_API_KEY`, even when the key was already present in the Windows user environment.

### Action Taken

- added structured provider health states in the OpenAI service path
- distinguished key presence from provider reachability and request outcome
- limited the missing-key message to the actual `missing_key` state only
- exposed safe diagnostics for:
  - key present yes/no
  - provider reachable yes/no
  - last error category
- kept cloud/local planner behavior separate and explicit in the UI

### Remaining Work

- verify in live Revit that key-present no longer shows the missing-key message
- verify real cloud failures show the correct category
- verify local deterministic fallback still works when cloud planning fails

---

## ISSUE-2026-04-10-002

**Title:** Unsupported AI Agent requests needed clearer reviewed deterministic scope guidance  
**Status:** Resolved in code, live verification pending  
**Type:** Planner UX / supported-action guidance

### Description

Unsupported requests such as schedule-generation or quantity-schedule creation could return an overly terse `Unsupported request.` message even when a clearer reviewed deterministic limitation message and closest supported actions were available.

### Action Taken

- added clearer unsupported-request summaries for schedule/quantity and duct-volume-adjacent prompts
- explicitly states that schedule creation / quantity schedule generation is not yet implemented as a reviewed deterministic action
- suggests the closest currently supported deterministic requests
- recorded a near-term candidate action:
  - `report total volume of selected ducts in cubic meters`

### Remaining Work

- verify the clearer unsupported guidance in live Revit
- decide whether the candidate duct-volume action should be promoted into the active deterministic action set in a later pass

---

## ISSUE-2026-04-10-003

**Title:** Cloud planner needs runtime self-test visibility inside pyRevit/Revit  
**Status:** Resolved in code, live verification pending  
**Type:** Runtime diagnostics / dependency visibility

### Description

Live findings showed that `OPENAI_API_KEY` existed in Windows user environment variables, but the runtime-visible planner state still reported `key_present: no`. Earlier local verification also suggested the `openai` dependency was unavailable in the Python runtime used by the cloud planner service path.

### Action Taken

- added a provider self-test path through `chatgpt_service.py`
- exposed the self-test through the pyRevit-side service wrapper
- added an internal AI Agent request:
  - `cloud planner self test`
- made the self-test print structured safe diagnostics into the AI Agent output panel
- recorded the actual interpreter identity used by the service runtime

### Workspace Result Observed

Initial workspace result:

- environment key visible: yes
- `openai` module importable: no
- failure category: `missing_openai_module`

### Remaining Work

- confirm the same result inside live Revit
- fix dependency availability in the actual cloud-planner runtime used by pyRevit

---

## ISSUE-2026-04-10-004

**Title:** OpenAI cloud planner path needed to move to the OpenAI Responses API while preserving reviewed deterministic execution boundaries  
**Status:** Resolved in code, blocked in runtime by missing module  
**Type:** Provider implementation / runtime dependency

### Description

The cloud planner path needed to use the supported OpenAI Python client API for minimal planning requests while still rejecting unsupported actions and never executing raw cloud-generated code.

### Action Taken

- updated `chatgpt_service.py` to use the OpenAI Responses API
- updated the provider probe/self-test to use a minimal Responses API request
- preserved deterministic reviewed execution boundaries in the pyRevit layer

### Current Verified Result

- service path updated in code
- after installing and upgrading the OpenAI Python client in the actual service runtime, the current workspace failure category is now `network_failed`

### Remaining Work

- confirm live Revit shows the same post-fix state
- resolve provider/network reachability so the Responses API probe can succeed

---

## ISSUE-2026-04-10-005

**Title:** ModelMind and AI Agent were still using separate reviewed action inventories  
**Status:** Resolved in code, live verification pending  
**Type:** Architecture / planner-router design

### Description

ModelMind was already backed by the prompt catalog, but AI Agent still relied on a separate hardcoded subset and separate planner phrase mapping. That violated the requirement that one shared reviewed action registry should drive both surfaces.

### Action Taken

- removed the hardcoded AI Agent reviewed action subset in `ai_prompt_registry.py`
- made AI Agent read the same reviewed action entries used by ModelMind
- added registry metadata for planner aliases, handler names, scope, discipline, and confirmation requirements
- moved AI Agent local intent matching onto registry-provided aliases

### Remaining Work

- verify the expanded shared registry in live Revit
- verify AI Agent execution for the newly added MEP reviewed actions

---

## ISSUE-2026-04-10-006

**Title:** Initial MEP reviewed action set needed to be promoted into the shared registry and handler layer  
**Status:** Resolved in code, live verification pending  
**Type:** Reviewed action coverage / deterministic execution

### Description

The initial HVAC, piping, electrical, QA/BIM, and low-risk write action set needed to exist as first-class reviewed actions in the shared registry so both ModelMind and AI Agent could use them.

### Action Taken

- added shared reviewed registry entries for the initial MEP action set
- added deterministic handlers for the new selection/reporting/write actions in `script.py`
- preserved reviewed create-sheet handling and approved-recipe separation

### Remaining Work

- live Revit validation for the newly added reviewed MEP actions
- assess whether any additional alias tuning is needed after live use

---

## ISSUE-2026-04-13-001

**Title:** Reviewed duct-volume action returned `0.000 m³` and needed a more honest deterministic extraction path  
**Status:** Resolved in code, live verification pending  
**Type:** Deterministic handler robustness / sample-model data quality

### Description

Live testing showed that `report total selected duct volume in cubic meters` returned `0.000 m³`, which suggested either missing parameter data, wrong unit handling, or a need to derive volume from geometry-related dimensions instead of relying only on a direct parameter.

### Action Taken

- investigated the current implementation path
- kept direct `Volume` parameter reading as the first option
- added deterministic fallback derivation from:
  - diameter + length
  - width + height + length
  - cross-sectional area + length
- changed the result formatting so unresolved ducts are reported honestly instead of silently collapsing to a misleading zero-only result

### Remaining Work

- live Revit validation on Snowdon Towers Sample HVAC after the robustness fix
- determine whether the sample model exposes enough duct data for reliable derived volume on all tested ducts

---

## ISSUE-2026-04-13-002

**Title:** Shared reviewed MEP registry still lacked some first-class pipe/electrical/QA actions and natural-language aliases  
**Status:** Resolved in code, live verification pending  
**Type:** Shared registry expansion / deterministic workflow coverage

### Description

The shared reviewed registry needed more first-class pipe, electrical, and QA/BIM actions, plus better natural-language aliases, while preserving the single shared-registry architecture.

### Action Taken

- added reviewed actions for:
  - pipes in active view count/list
  - electrical fixtures in active view list
  - expanded pipe/electrical/QA/BIM reporting coverage
- improved alias coverage for:
  - duct length / selected duct volume / disconnected duct fittings / ducts without system
  - select pipes / count pipes in active view / list pipes in active view / pipes without system
  - electrical devices in active view / fixtures without circuit

### Remaining Work

- live Revit validation for the newly added reviewed MEP actions

---

## ISSUE-2026-04-13-003

**Title:** Heavier Ollama models can look like feature failures when the runtime itself is unstable  
**Status:** Mitigated in code, live observation continues  
**Type:** Runtime UX / provider stability messaging

### Description

Latest live findings indicate that `gemma3:27b` appears unstable/crashes in runtime, while `phi3:mini` remains stable. Without a small runtime note, users may conclude the feature surface is broken rather than the selected local model/runtime combination.

### Action Taken

- added a lightweight runtime note in the model info/status path
- kept `phi3:mini` as the stable recommended model in the UI messaging when a heavier model is selected or fails

### Remaining Work

- continue observing live runtime behavior for heavier local models
