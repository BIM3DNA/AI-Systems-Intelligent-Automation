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
