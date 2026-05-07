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

---

## ISSUE-2026-04-21-001

**Title:** ModelMind catalog browsing depended on the main prompt box instead of a dedicated filter surface  
**Status:** Resolved in code, live runtime confirmation pending  
**Type:** UI usability / operator clarity

### Description

On the restored stable baseline, the growing ModelMind catalog remained browsable, but filtering still piggybacked on the main prompt input. That mixed prompt authoring with catalog exploration and made the catalog harder to understand as a separate read-only surface.

### Action Taken

- added a dedicated catalog filter box in the ModelMind catalog pane
- added read-only match-status text plus clear/reset behavior
- added low-risk expand/collapse controls for the catalog tree
- improved Selected Action Details readability without touching reviewed execution paths

### Remaining Work

- confirm the dedicated filter feels clearer in live pyRevit/Revit
- confirm Recent Prompts and canonical metadata resolution remain intuitive under filtered browsing

---

## ISSUE-2026-04-21-002

**Title:** Stable baseline lacked reviewed deterministic schedule-generation for governed MEP quantity workflows  
**Status:** Resolved in code, live runtime confirmation pending  
**Type:** Workflow coverage / governed automation

### Description

The stable Workbench baseline had deterministic reviewed actions for counts, lists, reports, sheets, and views, but not for governed schedule generation. Users needed category-specific schedule creation by level/reference level without opening the door to freeform code approval or broad execution changes.

### Action Taken

- added deterministic reviewed schedule actions for pipe, pipe fitting, duct, duct fitting, conduit, and electrical fixture/equipment schedules by level
- added a reviewed schedule-bundle action for supported categories
- implemented detailed vs summary schedule modes, with grand-total intent where supported
- added template-first duplication with native schedule fallback
- kept unrestricted shared code-approval flow unchanged

### Remaining Work

- live-validate schedule creation in Revit across supported categories
- confirm field availability and grouping behavior in real project templates
- decide later whether prefab-code filtering should be expanded beyond the low-risk exact-value support added here

---

## ISSUE-2026-04-21-003

**Title:** Generic native schedules and project-specific template-backed schedules needed explicit separation in the reviewed catalog  
**Status:** Resolved in code, live runtime confirmation pending  
**Type:** Governance / catalog structure

### Description

After the first reviewed schedule pass, generic native schedules and future template-backed project-specific schedules were still too close conceptually. The stable baseline needed explicit separation so validated native schedule actions could be promoted without implying that template matching, prefab filtering, or project-specific ACO/Bunge behavior had the same runtime proof.

### Action Taken

- promoted only the validated generic schedule actions to `live_validated`
- moved schedule entries into a dedicated `Schedules` category in the shared reviewed catalog
- added separate template-only ACO schedule actions under `Schedules / Template-Based`
- kept template actions honest: they fail clearly when no matching template is found and do not silently fall back to the generic native schedule family

### Remaining Work

- live-validate the new template-backed ACO actions
- decide whether explicit Bunge-branded template actions should be added separately once matching examples are proven at runtime
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

---

## ISSUE-2026-04-14-001

**Title:** ModelMind tree governance and visibility were still too flat for the shared reviewed registry  
**Status:** Structurally addressed, live runtime confirmation pending  
**Type:** Information architecture / UX governance

### Description

The shared reviewed registry existed, but ModelMind still rendered a flatter legacy-style tree. That weakened the intended product architecture because users could not clearly see the full reviewed catalog by domain/group, while AI Agent was already planning over the same underlying reviewed actions.

### Action Taken

- changed ModelMind tree rendering to show the shared reviewed catalog by:
  - HVAC
  - Piping
  - Electrical
  - QA / BIM
  - Views / Sheets
- kept aliases/examples in action details instead of creating duplicate nodes
- kept Approved Recipes separate and grouped by domain
- added a lightweight Recent Prompts branch outside the governed catalog

### Remaining Work

- confirm the grouped tree rendering in live Revit
- confirm that approved recipes still appear in the intended domain branch after save/reload in runtime

---

## ISSUE-2026-04-14-002

**Title:** AI Workbench layout was not resilient enough for resize and long catalog/output sessions  
**Status:** Structurally addressed, live runtime confirmation pending  
**Type:** WPF layout / local state persistence

### Description

The window shell was still fixed-size and more auto-content-driven than it should have been. That made the catalog/output split less usable and made it harder to verify that controls would remain readable without overlap when the window size changes.

### Action Taken

- enabled resizable window behavior with minimum width/height
- persisted window width, height, left, and top locally
- refit ModelMind to a splitter-based layout with stable bottom action area
- added selection-details panel and kept the reviewed-code panel visually secondary

### Remaining Work

- confirm live resize behavior in Revit/pyRevit
- confirm there is no clipping or overlap at smaller practical window sizes

---

## ISSUE-2026-04-14-003

**Title:** AI Agent plan-step selector was ambiguous and made adjacent controls appear broken  
**Status:** Structurally addressed, live runtime confirmation pending  
**Type:** State management / queue UX

### Description

Latest live findings showed that AI Agent supported actions executed successfully, but selecting items in the bottom dropdown did not activate the adjacent controls consistently. The underlying issue was that the dropdown mixed two concepts:

- the current reviewed plan steps
- the full supported reviewed-action catalog

Only current plan steps are actionable for toggle/reset/execute state, so using the same control for catalog display made the disabled buttons look incorrect.

### Action Taken

- restricted the bottom selector to current reviewed plan steps only
- kept supported actions in separate informational text
- added explicit per-step state fields (`enabled`, `executed`, `blocked_reason`, `undo_available`, etc.)
- tied control enablement to actual plan/session state instead of to generic selector population

### Remaining Work

- confirm live runtime interaction with the revised selector and buttons
- confirm that the step-state text is sufficiently clear in the pyRevit UI

---

## ISSUE-2026-04-14-004

**Title:** Undo Last Action had no real reversible implementation behind it  
**Status:** Structurally addressed for create-3D-view only, live runtime confirmation pending  
**Type:** Safe rollback / action-specific undo

### Description

The AI Agent `Undo Last Action` control existed as a placeholder, but no real reversible action context was being stored. That meant the control could not honestly support undo even for modifying actions that are actually reversible.

### Action Taken

- added session-level structured undo context
- limited real undo to the actually reversible reviewed action:
  - `Create 3D view from current selection/context`
- implemented undo by deleting the created 3D view in a fresh transaction when the stored context is still valid
- kept read-only actions and generic/global rollback out of scope

### Remaining Work

- live Revit confirmation that the created view is deleted correctly by Undo Last Action
- live confirmation of failure messaging when the created view no longer exists or the context is invalid

---

## ISSUE-2026-04-15-001

**Title:** Create sheet had no real reversible undo even though the action was already working  
**Status:** Structurally addressed, live runtime confirmation pending  
**Type:** Safe rollback / action-specific undo

### Description

The reviewed create-sheet action was already working through AI Agent, ModelMind, and approved recipes, but only create-3D-view had real undo support. That left the undo framework inconsistent across modifying reviewed actions.

### Action Taken

- extended the structured session undo context model to create sheet
- implemented `Undo Last Action` support for create sheet by deleting the created sheet in a fresh transaction when the context is still valid
- unified undo-context application across:
  - AI Agent execution
  - ModelMind reviewed execution
  - approved recipe execution

### Remaining Work

- live Revit confirmation that created sheets are deleted correctly by undo
- live confirmation of honest failure handling when the created sheet no longer exists or cannot be deleted safely

---

## ISSUE-2026-04-15-002

**Title:** Existing QA/BIM reviewed actions were too thin for trustworthy coordination output  
**Status:** Structurally addressed, live runtime confirmation pending  
**Type:** Read-only QA/BIM output quality

### Description

The QA/BIM reviewed actions existed in the shared registry, but their runtime output was still too minimal for reliable coordination use. The biggest weaknesses were:

- no clear total/grouped breakdowns
- blanket missing-parameter counts for irrelevant fields/categories
- weak active-view health summary for MEP inspection

### Action Taken

- hardened the four existing QA/BIM handlers in place
- added grouped counts, sample ids, explicit no-selection/nothing-missing notes, and truncation behavior
- narrowed parameter inspection to a smaller meaningful baseline and skipped irrelevant categories
- improved the active-view health check with system/unconnected/electrical summary findings

### Remaining Work

- live Revit confirmation that the new QA/BIM summaries are useful and trustworthy on real mixed-discipline views and selections

---

## ISSUE-2026-04-15-003

**Title:** QA/BIM planner prompts and scope assumptions were not explicit enough for multi-project runtime use  
**Status:** Structurally addressed, live runtime confirmation pending  
**Type:** Planner usability / scope messaging

### Description

Live findings showed that selected-element QA actions can correctly operate only on the active Revit document selection, but users may have manual selections in other open Revit projects and still expect them to count. At the same time, several natural-language QA prompts were not matching the intended reviewed actions.

### Action Taken

- added explicit active-document/active-view scope text to the QA/BIM outputs
- improved shared-catalog aliases/examples for the existing QA/BIM reviewed actions
- preserved canonical reviewed actions and kept aliases as metadata only

### Remaining Work

- confirm in live runtime that the new scope messaging prevents confusion
- confirm in live runtime that the new QA/BIM aliases cover common planner phrasing sufficiently

---

## ISSUE-2026-04-15-004

**Title:** QA/BIM selected-elements-by-category rendered `(err)` instead of real category groups  
**Status:** Structurally fixed, live runtime confirmation pending  
**Type:** Reviewed output defect / helper robustness

### Description

Live findings showed that `report selected elements by category` reported the correct total selected count but rendered grouped lines as `(err): <count> | sample ids: ...` instead of real Revit category names.

### Root Cause

- `get_elem_name()` assumed the object being named was a full Revit element and attempted `Document.GetElement(GetTypeId())`
- category grouping passes Revit `Category` objects through that helper
- for category objects, that assumption failed and the helper returned the literal fallback `(err)`

### Action Taken

- hardened `get_elem_name()` to read `Name` first and only use type lookup when the object actually supports it
- hardened the category report so valid selections group by real category name and actual grouping exceptions return an honest message
- standardized the missing-category label to `<No Category>`

### Remaining Work

- confirm in live runtime that non-empty active selections now render real grouped category names

---

## ISSUE-2026-04-15-005

**Title:** QA/BIM validation metadata and recent-prompt action details lagged behind confirmed runtime behavior  
**Status:** Structurally addressed, live runtime confirmation pending  
**Type:** Metadata consistency / UX hardening

### Description

Four QA/BIM reviewed actions now have explicit live runtime evidence, but the shared catalog still treated them as structural only. In addition, Recent Prompts could leave the Selected Action panel showing the history entry instead of the canonical reviewed-action metadata.

### Action Taken

- promoted the four confirmed QA/BIM reviewed actions to `live_validated`
- preserved prior validation states for actions without equivalent live evidence
- added compact active document / active view / current selection count lines to selection-based QA/BIM outputs
- resolved Recent Prompt details back through the canonical reviewed catalog before rendering the Selected Action panel

### Remaining Work

- confirm in live runtime that the Selected Action panel now shows the promoted validation state for the targeted QA/BIM actions
- confirm the compact context lines are useful without adding noise

---

## ISSUE-2026-04-16-001

**Title:** Broader reviewed production-assistant coverage was missing for presets, category helpers, duplicates, room/space checks, and common repetitive BIM utilities  
**Status:** Structurally addressed, live runtime confirmation pending  
**Type:** Reviewed action coverage / deterministic workflow expansion

### Description

The validated AI Workbench baseline was useful for reviewed MEP and QA/BIM inspection, but it still lacked a governed reviewed surface for higher-value production-assistant workflows such as discipline QA presets, pipe splitting, duplicate review/removal, category-driven helpers, room/space checks, and a small set of safe view/tag/quantity helpers.

### Action Taken

- added canonical reviewed QA presets to the shared reviewed registry
- added native deterministic reviewed actions for the requested high-value helpers where a safe implementation was feasible
- preserved destructive-tools gating and the shared ModelMind/AI Agent architecture
- added reversible undo only for the new modifying action where a real safe rollback path was practical:
  - rename active view

### Remaining Work

- live Revit validation for every new preset/action added in this pass
- future decision on whether quick dimension, batch view rename, and add couplings can be implemented safely enough for the reviewed architecture

---

## ISSUE-2026-04-19-001

**Title:** Reviewed presets were not explicitly governing selection scope, allowing selection-state contamination between steps  
**Status:** Structurally addressed, live runtime confirmation pending  
**Type:** Preset semantics / scope governance

### Description

The newly added QA presets executed reviewed steps sequentially but did not explicitly control selection handoff. As a result, selection-changing steps such as unconnected-fitting detection could contaminate later selected-element steps.

### Action Taken

- added preset-level selection snapshot/restore behavior
- added per-step scope behavior metadata
- refactored HVAC and Piping presets to use explicit generated working selections for selected-only quantity/parameter steps
- refactored Coordination / BIM QA preset into an explicit hybrid behavior that skips selection-only steps when no current selection exists
- broadened Electrical QA preset coverage and made the inspected categories explicit in runtime output
- added a shared Undo Last Action button to ModelMind using the same reviewed session undo context

### Remaining Work

- live runtime validation of the hardened preset semantics
- live runtime validation of ModelMind shared undo

---

## ISSUE-2026-04-20-002

**Title:** Stable reviewed routing remained overly sensitive to harmless prompt formatting differences for validated presets and generic category helpers  
**Status:** Structurally addressed, live runtime confirmation pending  
**Type:** Deterministic routing / reviewed metadata hardening

### Description

The restored stable baseline preserved execution safety, but some validated presets and generic category helper actions still relied on sparse examples and exact spacing-sensitive prompt matching.

### Action Taken

- normalized prompt matching for whitespace, comma spacing, and category-syntax formatting in `ai_prompt_registry.py`
- expanded metadata-only aliases/examples in `prompt_catalog.json` for validated QA presets and generic category helper forms
- intentionally avoided any changes to reviewed execution, lifecycle, dispatcher state, timeout logic, or modifying action paths

### Remaining Work

- live confirmation that the new prompt variants are useful in the stable fenced build

---

## ISSUE-2026-04-20-003

**Title:** Stable-baseline dark mode still made disabled Workbench buttons too visually similar to enabled controls  
**Status:** Structurally addressed, live runtime confirmation pending  
**Type:** UI readability / state clarity

### Description

On the stable baseline, dark-mode button states were still too close visually. Unavailable controls did not read as clearly unavailable at a glance.

### Action Taken

- added a shared disabled-button style in `UI.xaml`
- tuned disabled foreground/background/border values to be visibly muted without making enabled controls dim
- clarified the close-button tooltip so the stable baseline does not imply background continuity behavior

### Remaining Work

- live confirmation that dark-mode button states are clearly distinguishable in runtime

---

## ISSUE-2026-04-20-004

**Title:** ModelMind catalog filtering existed in the stable baseline but was not clearly discoverable as a catalog usability feature  
**Status:** Structurally addressed, live runtime confirmation pending  
**Type:** UI/catalog usability

### Description

The stable baseline already supported read-only catalog filtering through the main ModelMind input, but the UI did not explain that clearly. The Selected Action panel also remained a bit terse for a growing reviewed catalog.

### Action Taken

- clarified in `UI.xaml` that the main ModelMind input already filters the catalog by canonical titles, aliases, and examples
- improved the PromptTree hint text to explain Recent Prompt behavior more explicitly
- renamed the details group and improved details placeholder wording/space
- intentionally did not add a separate search box or favorites branch because that would require additional script/state wiring outside the safe scope

### Remaining Work

- live confirmation that the improved hints/details materially improve catalog usability

### 2026-04-22

- tightened BUNGE/ACO template actions to stop heuristic self-duplication and block narrow floor/sheet/generated schedules from being reused as canonical sources
- generic all-ACO pipe template actions now block honestly when no neutral master template exists instead of silently using a narrow product-family schedule

### 2026-04-24

- added product-family reviewed template actions instead of allowing the generic ACO pipe template action to pick a narrow source
- kept pipe-fitting level retargeting under investigation; exact coded level prompts are routed and guarded, but live Revit proof is still pending

### 2026-04-27

- added read-only project scan support for document/view/levels/links/imports/categories/schedules/selection/warnings context
- runtime validation is still pending for scanner completeness and Ollama grounding behavior

### 2026-04-27 Context UX/Q&A follow-up

- live Revit validation showed bootstrap and standard scans succeed, but simple structured context questions could time out when routed through Ollama
- deterministic context-answer routing was added for schedules, CAD/imports, links, categories, warnings, detected issues, levels/views/sheets, and first-check prompts
- Project Context panel readability/detail was expanded; live validation remains pending for the new deterministic answer buttons and dark-theme tree styling

### 2026-04-27 Context cache consistency follow-up

- live Revit validation showed schedule and warning counts could diverge between Scan Project, tree, deterministic chat answers, AI Agent plan, and Codex brief
- cache access was centralized so standard Scan Project becomes the authoritative latest context for all Project Context consumers
- first-check/test-first phrasing now routes to deterministic BIM context guidance, and Revit link path/name output avoids raw API object representations

### 2026-04-28 Chat transcript readability follow-up

- live runtime validation showed deterministic context answers work, but long schedule/chat outputs were too dense for demo use
- chat transcript turns now use plain-text separators, and deterministic answers use bracketed sections with count-first summaries
- schedule details are capped in chat while the Project Context tree remains the full-detail surface

### 2026-04-28 Linked model coordinate health follow-up

- added a read-only scanner section and deterministic answer path for linked model coordinate/transform health
- link coordinate findings are conservative review flags only; the Workbench does not claim coordinate correctness or mutate link/project coordinate state
- live Revit validation remains pending for linked model names, status labels, transform origin/rotation display, and absence of raw API object path strings

### 2026-05-06 AI-AGENT-002 Guided Project Startup Plan

Resolved:

- Agent plan ordering previously mixed diagnostics and schedule/template actions too early.
- Warning review previously appeared as `Scan current project`; the guided plan now has explicit `Review Revit warnings summary`.
- Level-targeted automation is now blocked/cautioned when ambiguous level aliases exist.

Runtime validation:

- validated in Revit on `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`
- active view: `TEST [FloorPlan]`
- Ask Agent for Plan returned `[GUIDED PROJECT STARTUP PLAN]`
- deterministic guided-plan prompts returned the same plan format
- Create Codex Brief included guided Agent startup plan metadata
- no model mutation was observed
- Agent remained plan-only

Open:

- Execute Plan remains unvalidated.
- BIM Basis / Levels & Grids interpretation still needs refinement to reduce false positives in IFC-heavy projects.
- Dedicated warning review action still needs implementation.
- Sync to BIM3DNA toolbar copy remains pending as a separate task.

---

## ISSUE-2026-05-07-001

**Title:** MEP-RO-001 selection-report prompts fall through to Ollama  
**Status:** Open / runtime validation failed  
**Type:** deterministic routing failure

### Symptoms

- `report selected elements by category` returned generic non-Revit prose.
- `report selected elements by type` returned generic non-Revit prose.
- `count selected elements` returned a Python/list counting explanation.
- `health check selected elements` returned an HTML/browser/JavaScript-style answer.
- `report missing parameters from selection` returned a generic parameter/form explanation.

### Validation Environments

- `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`, active view `TEST [FloorPlan]`, with no selection and with selected pipes/pipe fittings.
- Snowdon Towers Sample HVAC, with selected ducts/duct fittings.
- Electrical sample/project, with selected Electrical Fixtures, Electrical Equipment, Lighting Fixtures, and Data/Communication Devices where available.

### Root Cause Hypothesis

Deterministic routing did not intercept the MEP-RO-001 selection-report prompts before Ollama fallback, or the catalog aliases are not connected to the chat routing path used by typed prompts.

### Required Fix

- Add deterministic routing aliases for all MEP-RO-001 prompts before Ollama fallback.
- Ensure selection handlers read current live selection using `uidoc.Selection.GetElementIds()` at action time.
- Return the standardized no-selection wording when no elements are selected.
- Keep all handlers read-only.

### Resolved Issues

None for this validation pass.
