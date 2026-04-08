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
