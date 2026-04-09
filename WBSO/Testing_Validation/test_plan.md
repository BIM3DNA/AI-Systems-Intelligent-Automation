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

## Additional Checks Executed In This Provider-Integration Pass

- compiled `AI.extension/lib/ai_local_store.py`
- compiled `AI.extension/lib/ai_prompt_registry.py`
- compiled `AI.extension/lib/ai_agent_session.py`
- compiled `AI.extension/lib/ai_reviewed_code.py`
- compiled `Model_Service/ModelService.py`
- compiled `Openai_Server/chatgpt_service.py`
- reparsed `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`

## Additional Live Checks Not Executed In This Provider-Integration Pass

- live ModelMind layout verification in Revit
- live AI Agent local planner verification after provider wiring
- live AI Agent OpenAI planner normalization with a valid key
- live missing-key handling verification
- live cloud request failure verification

## Acceptance Condition for Next Runtime Pass

The refactor should only be considered runtime-proven after the scenario set above is executed and documented in Revit/pyRevit.
