# Current Scope Alignment

## Date

2026-04-08

## Active Product Position

The current pyRevit-delivered AI window remains a single Revit entry point with three distinct surfaces:

- `Ollama Chat` for low-risk conversation and prompt experimentation
- `ModelMind` as the primary end-user workflow for deterministic and semi-generative BIM tasks
- `AI Agent` as the advanced reviewed planning/execution surface with destructive tools disabled by default

## What This Pass Aligned

- moved prompt/recipe inventory into a structured catalog under `AI.extension/lib/`
- introduced local approved-recipe persistence instead of ad hoc prompt-tree mutation
- clarified AI Agent button semantics around plan creation, reviewed execution, command disabling, and reset
- added local theme persistence for the window
- kept the single pyRevit entry point and current installer/runtime assumptions intact

## What Remains Outside Proven Scope

- live Revit validation of the refactored UI on Snowdon Towers Sample HVAC
- proof that the refactored window still launches correctly inside pyRevit after these edits
- proof that Ollama chat, ModelMind deterministic flows, and approved-recipe save/load all work at runtime in Revit

## Scope Guardrail

This pass is still a baseline-preserving refactor, not a production-grade agent runtime. The command layer remains deterministic-first and the AI Agent tab remains guarded, review-oriented, and intentionally limited.

## Reviewed-Code Alignment Update

ModelMind now treats reviewed code as a governed path rather than a generic execute-anything fallback.

- approval now depends on pyRevit compatibility validation
- unsupported Dynamo/DesignScript code is intentionally blocked
- approved recipes are only created from successful reviewed-code executions
- `create sheet` now has a pyRevit-safe reviewed template path

## 2026-04-09 Scope Clarification

The current product scope is now:

- `ModelMind` as the main user workflow
- `Ollama Chat` as the low-risk conversation surface
- `AI Agent` as a smaller deterministic reviewed-planner for a narrow supported BIM command set

This explicitly excludes any claim of broad autonomous agent capability in the current runtime.

## 2026-04-09 Provider Alignment Update

The current aligned runtime scope is:

- `ModelMind` remains the main user workflow with a wider input area and secondary reviewed-code presentation
- `AI Agent` now supports:
  - local deterministic planning
  - optional OpenAI-backed intent normalization
- cloud planning is only in scope for reviewed action selection/rejection
- cloud-generated freeform code execution is explicitly out of scope
- secrets are only in scope through environment loading via `OPENAI_API_KEY`

Still outside proven live scope for this pass:

- cloud planner behavior in live Revit
- missing-key and cloud-failure UI states in live Revit
- post-pass live verification of the ModelMind layout polish
