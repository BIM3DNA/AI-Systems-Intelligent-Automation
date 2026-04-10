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

## Acceptance Condition for Next Runtime Pass

The refactor should only be considered runtime-proven after the scenario set above is executed and documented in Revit/pyRevit.
