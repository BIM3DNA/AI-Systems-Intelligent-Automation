# pyRevit Extension Refactor Notes

## Project

AI Systems & Intelligent Automation

## Scope of This Note

This file records the current refactor of the single pyRevit AI window while preserving the validated single-entry baseline.

## Objective of This Pass

The objective was to improve product architecture clarity and safety without changing:

- the single pyRevit button entry point
- the single WPF window delivery model
- the installer/runtime assumption that the extension still launches from the current structure

## Refactor Actions Performed on 2026-04-08

### 1. Window Responsibility Clarification

- clarified window roles in labels/tooltips and code comments
- positioned `ModelMind` as the primary workflow
- kept `Ollama Chat` as low-risk conversation
- kept `AI Agent` advanced and guarded

### 2. Structured ModelMind Prompt Registry

- added `AI.extension/lib/prompt_catalog.json`
- replaced hardcoded ModelMind prompt-tree state with structured prompt metadata loading
- preserved the existing command inventory categories

### 3. Approved Recipe Flow

- added `AI.extension/lib/approved_recipes.json`
- added helper logic to save successful reviewed generated code as approved local recipes
- surfaced approved recipes in a distinct ModelMind branch

### 4. Agent Safety Semantics

- implemented plan-only behavior for `Run Agent`
- implemented reviewed execution for `Execute Plan`
- implemented session command enable/disable and reset
- left undo disabled because robust rollback/journaling is not implemented
- left destructive tools off by default with visible warnings

### 5. Local UX State

- added dark/light mode toggle
- persisted theme choice locally through a local settings helper

## Validation Position

This refactor was completed as a workspace/code pass. It has not yet been runtime-validated in pyRevit/Revit after the edits.

### Locally Checked

- JSON assets parse
- XAML is well-formed XML

### Not Yet Checked

- pyRevit tab load after refactor
- button launch after refactor
- Ollama chat response after refactor
- ModelMind deterministic execution after refactor
- Snowdon Towers HVAC scenarios in live Revit

## 2026-04-08 Reviewed-Code Hardening Pass

### Refactor Actions

- added a reviewed-code validator module for pyRevit compatibility checks
- prevented approval of reviewed code containing unsupported Dynamo / DesignScript references
- added explicit reviewed-code state messaging in the ModelMind UI
- changed approved-recipe persistence from immediate prompt to explicit post-success save action
- added a pyRevit-safe `create sheet` reviewed-code template using `DB.ViewSheet.Create(...)`

### Runtime Position After This Pass

Live findings already reported:

- theme persistence works
- Ollama Chat works
- deterministic ModelMind tasks work

Still pending live validation:

- invalid reviewed code is blocked before execution
- valid reviewed code executes and can then be saved
- saved approved recipe appears immediately in the approved branch

## 2026-04-09 Product Polish Pass

### Refactor direction

- keep one AI Workbench window
- keep ModelMind as primary task surface
- reduce AI Agent to a smaller deterministic reviewed-planner
- improve dark-mode usability without destabilizing the validated baseline

### Runtime facts already confirmed entering this pass

- AI tab loads
- button opens the workbench
- Ollama Chat works
- theme persistence works
- deterministic `select all ducts` works
- reviewed create-sheet flow works
- approved recipe save/load works

### Remaining runtime follow-up after this pass

- validate planner handling for the new duct count/list cases
- validate header alignment and dark-mode readability fixes in live Revit

## 2026-04-09 Provider-Backed Planner Pass

### Refactor direction

- keep ModelMind as the primary task surface with a cleaner bottom input/action layout
- keep AI Agent narrow and reviewed
- add optional provider-backed planning without introducing raw cloud execution inside pyRevit

### Refactor actions

- widened the ModelMind input field and moved action buttons below it
- reused `Openai_Server/chatgpt_service.py` for planner normalization
- added `Model_Service/ModelService.py` provider-state and normalize-intent wrapper methods
- added AI Agent provider UI states for local, available cloud, missing-key cloud, and request-failed cloud
- constrained AI Agent plan output to a reviewed plan object:
  - `matched_action`
  - `confidence`
  - `requires_modification`
  - `destructive`
  - `summary`
  - `execution_ready`

### Security boundary

- `OPENAI_API_KEY` is now read from environment only
- no code path in this pass stores or displays the key
- cloud planning only selects or rejects supported actions
- deterministic/reviewed execution remains local to the pyRevit runtime

### Runtime position after this pass

Locally checked:

- updated XAML parses
- updated service/helper modules compile

Still pending live validation:

- ModelMind layout polish
- AI Agent local/cloud planner runtime behavior
- missing-key and request-failure UI handling inside live Revit
