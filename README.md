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

## Current Workspace Cloud Planner Finding

The current workspace self-test through the actual service path reports:

- `env_key_present: yes`
- `openai_module_importable: yes`
- `client_init_ok: yes`
- `failure_category: network_failed`

That points to provider/network reachability as the next likely fix for cloud planning in the runtime used by the subprocess service.
