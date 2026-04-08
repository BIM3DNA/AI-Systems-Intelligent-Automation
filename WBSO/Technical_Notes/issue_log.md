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
