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

## What Was Not Executed During This Workspace Pass

- live pyRevit loading
- live Revit button launch
- live Ollama response validation
- live Snowdon Towers Sample HVAC scenario execution
- live post-hardening reviewed-code blocking/approved-recipe save flow checks

## Acceptance Condition for Next Runtime Pass

The refactor should only be considered runtime-proven after the scenario set above is executed and documented in Revit/pyRevit.
