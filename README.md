# AI Systems & Intelligent Automation

This repository contains a pyRevit-delivered AI workbench with one Revit entry point and one window.

## Current Product Surfaces

- `Ollama Chat`: low-risk conversational help and prompt experimentation
- `ModelMind`: primary workflow for deterministic and semi-generative BIM task recipes
- `AI Agent`: advanced reviewed planning/execution surface with destructive tools disabled by default

## Key Implementation Artifacts

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`
- `AI.extension/lib/prompt_catalog.json`
- `AI.extension/lib/approved_recipes.json`
- `AI.extension/lib/ai_prompt_registry.py`
- `AI.extension/lib/ai_local_store.py`
- `AI.extension/lib/ai_agent_session.py`
- `AI.extension/lib/ai_reviewed_code.py`
- `Openai_Server/chatgpt_service.py`
- `Model_Service/ModelService.py`

## Current Validation Position

The earlier migration baseline was runtime-validated in pyRevit at UI-launch level. Current live findings additionally confirm theme persistence, Ollama Chat, and deterministic ModelMind tasks. The reviewed-code hardening patch is implemented, but its new blocking/save-flow behavior still requires live post-patch validation in pyRevit/Revit.

## Current Product Framing

- `ModelMind` is the main BIM task surface
- `Ollama Chat` remains the low-risk conversation area
- `AI Agent` is currently a smaller deterministic reviewed-planner, not a broad autonomous agent

## Stable-Baseline Catalog Usability

The current stable baseline now includes a dedicated ModelMind catalog filter in the right-hand catalog pane. That filter is read-only: it narrows reviewed catalog browsing by title, aliases, examples, and grouping metadata without changing the main prompt input or triggering execution.

## Stable-Baseline Reviewed Schedule Generation

The stable baseline now also includes deterministic reviewed schedule-generation actions for supported MEP categories. These actions stay inside the shared reviewed catalog, support detailed vs summary schedule modes, and prefer duplicating an existing schedule template when a matching source schedule is available before falling back to a native deterministic schedule definition.

The promoted generic schedule family is now grouped under a dedicated `Schedules` catalog branch. Separate ACO template-only schedule actions also exist under `Schedules / Template-Based`; they do not silently fall back into the generic native schedule family when no matching project template is found.

## Planner Provider Configuration

- local planning is always available through the deterministic action matcher
- optional cloud planning is available only when `OPENAI_API_KEY` is present in the environment
- cloud planning only normalizes user requests into the supported reviewed action set
- cloud output does not execute as raw code inside pyRevit

## Planner Provider Diagnostics

The AI Agent provider path now distinguishes:

- missing key
- key present
- auth failure
- network failure
- request failure
- provider ready
- local-only UI state

Safe diagnostics surfaced to the UI include:

- key present: yes/no
- provider reachable: yes/no
- last error category

The cloud planner also now exposes a developer-focused self-test request:

- `cloud planner self test`

It reports:

- env key visibility
- `openai` importability
- client initialization success
- provider probe request success
- runtime interpreter identity

## Shared Reviewed Action Registry

- ModelMind now acts as the visible source-of-truth reviewed action library
- AI Agent now plans and routes over that same reviewed action registry
- approved recipes remain a separate branch and are not a second planner action inventory

The cloud service path now uses the OpenAI Python client via the Responses API for:

- minimal provider probe
- supported-action normalization

## 2026-04-09 Pass Position

Implemented in code:

- ModelMind bottom input/action layout polish
- AI Agent provider-backed planning path
- explicit local/cloud provider-state messaging

Still pending live Revit validation after this pass:

- ModelMind layout polish in runtime
- AI Agent local planner cases after the latest changes
- AI Agent OpenAI planner normalization with a valid key
- missing-key and request-failure runtime behavior

## Still Unsupported In AI Agent

- reviewed deterministic schedule creation
- quantity schedule generation
- arbitrary non-reviewed cloud code execution

Broader schedule-generation requests remain unsupported unless they are implemented as reviewed deterministic actions.

## 2026-04-10 Shared Registry Position

The shared reviewed action registry now contains the initial HVAC, piping, electrical, QA/BIM, and low-risk write action set, and the AI Agent local planner normalizes against that same registry.

## 2026-04-13 Expanded MEP Position

Latest reported live-validated actions carried into the current pass:

- Ollama Chat with `phi3:mini`
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
- reviewed create-sheet flow
- approved recipe save/load

This pass expands the shared reviewed MEP action set further for piping, electrical, QA/BIM, and low-risk write actions while keeping execution deterministic and reviewed.

Known limitation carried into this pass:

- heavier local models such as `gemma3:27b` may be unstable in runtime, while `phi3:mini` is the stable recommended model

## 2026-04-14 Shared Catalog Visibility and Resize Pass

This pass keeps the same shared reviewed-registry architecture but makes it more usable:

- ModelMind now renders the shared reviewed catalog as the visible governed task library
- AI Agent remains a planner/router over the same reviewed actions and does not gain a second catalog tree
- aliases/examples remain metadata on canonical actions instead of becoming duplicate tree nodes
- Approved Recipes stay separate from the canonical reviewed catalog
- the Workbench shell is now structurally resizable and stores its size/position locally

What was verified locally in this pass:

- shared reviewed actions available from registry: `26`
- ModelMind tree sections build as:
  - `HVAC`
  - `Piping`
  - `Electrical`
  - `QA / BIM`
  - `Views / Sheets`
  - `Recent Prompts`
  - `Approved Recipes`
- AI Agent supported-action UI now reflects the same `26` shared reviewed actions
- `UI.xaml` is well-formed after the resize/layout refactor

What still needs live confirmation in Revit:

- grouped ModelMind tree rendering
- window resize/restore behavior
- approved-recipe domain grouping in the updated tree
- matched-action visibility and supported-action display in AI Agent after planning

## 2026-04-14 AI Agent Queue State Pass

This pass does not expand the reviewed action catalog. It fixes AI Agent queue usability only.

- the bottom Agent selector now represents only the current reviewed plan steps
- supported reviewed actions remain visible separately as informational text
- plan steps now carry explicit runtime state such as `enabled`, `executed`, `blocked_reason`, and `undo_available`
- button enablement now follows actual plan/session state rather than generic selector population

What was verified locally in this pass:

- a `count selected ducts` plan produces a queued step with the explicit state fields above
- disabling the only queued step makes the session non-runnable
- `UI.xaml` remains well-formed after the Agent control changes

What still needs live confirmation:

- revised queue-selector interaction in pyRevit
- corrected button enable/disable transitions in runtime
- Execute Plan gating/status messaging when modifying steps are present and destructive tools remain off

## 2026-04-14 Action-Specific Undo Pass

This pass adds real undo only for a truly reversible reviewed action:

- `Create 3D view from current selection/context`

What changed:

- successful modifying execution can now store structured undo context
- Undo Last Action is enabled only when that reversible context exists
- `Reset Commands` clears undo context to avoid stale reversible state
- read-only actions remain non-undoable

What was verified locally in this pass:

- blocked modifying execution does not create undo context
- successful modifying execution does create undo context
- reset clears undo context
- read-only execution does not create undo context

What still needs live confirmation:

- actual deletion of the created 3D view on undo in Revit
- honest undo failure messaging for stale/missing contexts

## 2026-04-15 Create-Sheet Undo Extension

This pass extends the existing real reviewed-action undo framework to:

- `Create sheet`

What changed:

- successful create-sheet execution can now populate last-action undo context
- the same last-action undo model is now used across:
  - AI Agent reviewed execution
  - ModelMind reviewed execution
  - approved recipe execution
- create-3D-view undo remains in place
- read-only actions remain non-undoable

What was verified locally in this pass:

- successful create-sheet execution can create undo context structurally
- reset clears that undo context
- create-3D-view undo context still works structurally
- read-only execution still creates no undo context

What still needs live confirmation:

- actual sheet deletion on undo in Revit
- honest failure messaging when the created sheet is gone or cannot be deleted safely
- approved-recipe create-sheet undo behavior in live runtime

## 2026-04-15 QA/BIM Hardening Pass

This pass does not change the catalog architecture or reviewed action inventory. It tightens the usefulness and trustworthiness of the existing QA / BIM read-only actions.

What changed:

- `report selected elements by category` now returns total count, grouped counts, sample ids, and truncation
- `report selected elements by type` now returns total count, grouped counts, sample ids, and truncation
- `report missing key parameters from selected elements` now checks a smaller reviewed baseline:
  - `Mark`
  - `Comments`
  - `Family and Type`
  - `System assignment` where applicable
  - `Electrical circuit/system` where applicable
- `health check of active view for supported MEP categories` now includes clearer counts and read-only summary findings for missing system assignment, unconnected fittings, and electrical assignment gaps

What was verified locally in this pass:

- no syntax/tokenization regressions in the updated script
- `UI.xaml` remains well-formed
- the hardened QA/BIM output paths are present in code

What still needs live confirmation:

- usefulness/correctness of the hardened QA/BIM summaries on real selections and active views
- parameter applicability behavior across mixed-discipline runtime selections

## 2026-04-15 QA/BIM Scope and Alias Pass

This pass does not add QA/BIM actions. It clarifies scope and improves natural-language matching for the existing reviewed QA/BIM actions.

What changed:

- selected-element QA/BIM outputs now explicitly state:
  - `Selection scope: active document only`
- empty-selection QA/BIM outputs now explicitly state that selections in other open Revit projects are not included
- the active-view health check now explicitly states:
  - `View scope: active view in active document`
- shared-catalog aliases/examples were expanded for the existing QA/BIM actions so the planner can better normalize natural phrasing

What was verified locally in this pass:

- the new QA/BIM alias prompts normalize through the shared planner/catalog path
- scope-message text is present in the QA/BIM handler output
- the QA/BIM catalog metadata correctly distinguishes `selection` and `active_view` scope

What still needs live confirmation:

- the new scope wording in multi-project runtime scenarios
- the new QA/BIM alias coverage during real planner use

## 2026-04-15 QA/BIM Category Grouping Fix

What changed:

- fixed the existing reviewed action `report selected elements by category` so valid selections should render real category groups instead of the fallback `(err)` bucket
- preserved the active-document selection scope messaging and total selection count line
- hardened the shared naming helper so Revit `Category` objects are named safely

What was verified locally in this pass:

- the category-report code path now groups by category names without relying on the broken `(err)` fallback
- `script.py` still passes local sanity checks

What still needs live confirmation:

- grouped category output on non-empty active-document selections in Revit

## 2026-04-15 QA/BIM Validation Metadata Promotion and Context UX

What changed:

- promoted the four QA/BIM reviewed actions with confirmed runtime evidence to `live_validated`
- added compact active document / active view / current selection count lines to selection-based QA/BIM outputs
- made Recent Prompts resolve through canonical reviewed-action metadata for the Selected Action panel

What was verified locally in this pass:

- the four targeted QA/BIM reviewed actions now resolve as `live_validated` from the shared registry
- `script.py` still passes local sanity checks
- Recent Prompt details now resolve through canonical action lookup before the Selected Action panel is built

What still needs live confirmation:

- Selected Action panel display of the promoted validation states
- compact context-line presentation in pyRevit/Revit
- Recent Prompt canonical-details behavior in the live ModelMind UI

## 2026-04-16 Reviewed Production-Assistant Expansion

What changed:

- added canonical reviewed QA presets to the shared reviewed catalog
- added new native deterministic reviewed helpers for split pipes, duplicates, categories, room/space checks, selected view/tag utilities, and broader linear-MEP quantities
- preserved ModelMind as the canonical catalog and AI Agent as the planner/router over the same reviewed actions

What was verified locally in this pass:

- `script.py` passed `tabnanny`
- support modules compiled successfully where applicable
- `prompt_catalog.json` parsed successfully
- shared reviewed registry grouping looked structurally correct
- planner alias matching worked for the newly added presets/actions in local checks

What still needs live confirmation:

- all new presets and actions added in this pass
- rename-active-view undo behavior in live runtime

## 2026-04-19 Preset Hardening and Scope Governance

What changed:

- hardened preset execution with explicit scope behavior and selection snapshot/restore
- fixed HVAC and Piping preset selected-step semantics
- broadened Electrical QA preset inspected categories
- hardened Coordination / BIM QA preset so selection-only steps are skipped explicitly when there is no current selection
- added ModelMind access to the shared Undo Last Action surface
- expanded split-pipe aliases/examples and improved category disambiguation

What was verified locally in this pass:

- `script.py` passed `tabnanny`
- support modules compiled successfully where applicable
- `prompt_catalog.json` parsed successfully
- `UI.xaml` remained well-formed
- planner alias matching worked for the hardened presets and expanded split-pipe variants

What still needs live confirmation:

- hardened HVAC QA preset
- hardened Piping QA preset
- redesigned Electrical QA preset
- hardened Coordination / BIM QA preset
- category disambiguation on walls / doors / pipe fittings
- ModelMind shared undo
- expanded split-pipe prompt variants

## 2026-04-20 Stability-Fenced Catalog Routing Hardening

What changed:

- normalized reviewed prompt matching in the shared catalog loader so harmless whitespace/comma/category-syntax variations resolve more consistently
- expanded metadata-only aliases/examples for validated QA presets and generic category helper actions

What was verified locally in this pass:

- `ai_prompt_registry.py` compiled successfully
- `prompt_catalog.json` parsed successfully
- local routing checks confirmed the new preset/category prompt variants resolve through the shared reviewed registry

What was intentionally left unchanged:

- window lifecycle architecture
- reviewed Revit execution dispatch
- create sheet / create 3D view / rename active view execution paths
- shared undo architecture

## 2026-04-20 Stable-Baseline UI Polish

What changed:

- added shared disabled-button styling in `UI.xaml`
- clarified the close-button tooltip so it does not imply special continuity behavior

What was verified locally in this pass:

- `UI.xaml` parsed successfully
- local inspection confirmed disabled-button brushes and trigger styling are present

What was intentionally left unchanged:

- `script.py`
- all execution architecture
- all lifecycle / dispatcher behavior
- create sheet / create 3D view / rename active view paths

## 2026-04-20 Stable-Baseline ModelMind Catalog Usability

What changed:

- clarified in `UI.xaml` that the main ModelMind input already filters the catalog while typing
- clarified the catalog hint text and Recent Prompt explanation
- improved the Selected Action details group/header wording and body height

What was verified locally in this pass:

- `UI.xaml` parsed successfully
- local inspection confirmed the revised tooltip/hint/detail text is present

What was intentionally left unchanged:

- `script.py`
- all execution architecture
- all lifecycle / dispatcher behavior
- no separate search control was added
- no favorites/pinning state was added

## Current Workspace Cloud Planner Finding

The current workspace self-test through the actual service path reports:

- `env_key_present: yes`
- `openai_module_importable: yes`
- `client_init_ok: yes`
- `failure_category: network_failed`

That points to provider/network reachability as the next likely fix for cloud planning in the runtime used by the subprocess service.

## 2026-04-22 Stability-Fenced Schedule Template Update

- generic native schedule actions remain the validated path and were not changed in behavior
- ACO/BUNGE template-backed actions now use explicit reviewed source-template recipes with hard exclusions for floor-specific, sheet, AI-generated, and previously generated ACO output schedules
- template actions remain structural_only and template-only; if no safe canonical master exists or level retargeting cannot be applied safely, the action blocks honestly instead of creating a misleading schedule

## 2026-04-24 ACO/Bunge Product-Family Schedule Update

- added structural reviewed template-only actions for ACO 1.4301 single socket, 1.4404 single socket, and 1.4404 double socket pipe schedule/summary variants
- generic all-ACO pipe schedule/summary prompts continue to block without a neutral master template
- only the live-confirmed ACO pipe-fitting summary action is promoted; product-family actions and pipe-fitting level retargeting remain pending live validation

## 2026-04-27 Project Context Scanner Update

- added a read-only Project Context Scanner with bootstrap and standard scan depths for document metadata, active view, levels, links, imports/CAD, categories, schedules, selection, warnings, and detected issue flags
- Ollama Chat can answer project questions from the latest cached context, and AI Agent can propose reviewed catalog actions without executing them
- added a copyable Codex Task Brief generator; it does not edit files, call external Codex, or enable generated code execution

## 2026-04-27 Project Context UX/Q&A Update

- Project Context now exposes richer cached context details in the tree, including sampled view/sheet/link/import/schedule names and status flags
- common structured context questions are answered deterministically from cached Revit API context instead of waiting on Ollama
- the context panel keeps the read-only scanner boundary and does not change reviewed execution, ExternalEvent lifecycle, undo, or schedule creation behavior

## 2026-04-27 Project Context Consistency Fix

- Project Context consumers now read through the same latest cached scan snapshot, so Scan Project, the tree, deterministic chat answers, AI Agent planning, and Codex briefs stay aligned
- standard scans supersede bootstrap scans for schedule and warning summaries
- Revit link display now uses readable link names/status/path text where available instead of raw Revit API object strings
