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

## 2026-04-10 Scope Refinement

The current aligned scope now also includes:

- honest provider diagnostics for the AI Agent planner surface
- safe distinction between key presence and real cloud request failure states
- clearer unsupported-request guidance for schedule/quantity prompts

Still outside implemented scope:

- reviewed deterministic schedule creation
- quantity schedule generation
- reviewed deterministic reporting of selected-duct total volume in cubic meters

That duct-volume action is now recorded as a candidate for near-term expansion only.

## 2026-04-10 Diagnostic Scope Addition

The current implemented scope now also includes:

- a developer-focused AI Agent diagnostic request:
  - `cloud planner self test`
- explicit reporting of whether the cloud planner runtime can:
  - see `OPENAI_API_KEY`
  - import `openai`
  - initialize a client
  - complete a provider probe request

This diagnostic path is for runtime transparency only. It does not change the reviewed deterministic execution boundary.

## 2026-04-10 OpenAI Planner Scope Note

The current implemented cloud scope is now:

- OpenAI Responses API for planning / intent normalization only
- deterministic reviewed local execution only

Still outside working runtime scope until dependency parity is fixed:

- successful live Revit OpenAI planner normalization

Current workspace blocker after dependency parity improvement:

- successful provider/network reachability for the Responses API path

## 2026-04-10 Shared Registry Scope Update

The current aligned product scope now also includes:

- one shared reviewed action registry for both ModelMind and AI Agent
- ModelMind as the visible source-of-truth reviewed action library
- AI Agent as planner/router over that same registry

Still outside proven live scope after this pass:

- live execution validation for the newly added MEP reviewed actions

## 2026-04-13 Expanded MEP Scope Note

The current aligned scope now also includes:

- expanded deterministic shared MEP actions for ducting, piping, electrical, and QA/BIM review
- a more robust deterministic duct-volume reporting path
- lightweight runtime guidance that keeps `phi3:mini` as the stable recommended Ollama model when heavier local models are unstable

Still outside proven live scope after this pass:

- live validation for the newly added pipe/electrical/QA actions
- live validation for the duct-volume fix

## 2026-04-14 Shared Catalog Visibility Scope Note

The current aligned scope now also includes:

- ModelMind as the visible governed reviewed-action catalog over the shared registry
- AI Agent as planner/router over the same shared reviewed actions without a second tree
- canonical reviewed actions separated from aliases/examples and from approved recipes
- a resizable AI Workbench shell with locally persisted size and position

Still outside proven live scope after this pass:

- live confirmation of the grouped ModelMind tree in pyRevit
- live confirmation of window resize/layout behavior in runtime
- live confirmation of approved-recipe domain grouping after save/reload

## 2026-04-14 AI Agent Queue State Scope Note

The current aligned scope now also includes:

- AI Agent bottom selector representing only the current reviewed plan steps
- supported reviewed actions shown separately as informational status rather than as an actionable queue selector
- explicit plan-step runtime state for enablement/execution/blocking visibility

Still outside proven live scope after this pass:

- live confirmation of corrected Agent queue control interaction
- live confirmation of Execute Plan gating/status behavior in runtime

## 2026-04-14 Action-Specific Undo Scope Note

The current aligned scope now also includes:

- session-level undo context only for actually reversible modifying reviewed actions
- one first supported reversible action:
  - `Create 3D view from current selection/context`

Still outside proven live scope after this pass:

- live confirmation of real create-3D-view undo in Revit
- live confirmation of honest undo failure handling in invalid/stale contexts

## 2026-04-15 Create-Sheet Undo Scope Note

The current aligned scope now also includes:

- real last-action undo for:
  - `Create 3D view from current selection/context`
  - `Create sheet`
- unified undo-context handling across AI Agent, ModelMind, and approved recipe execution

Still outside proven live scope after this pass:

- live confirmation of create-sheet undo in Revit
- live confirmation of approved-recipe create-sheet undo behavior

## 2026-04-15 QA/BIM Hardening Scope Note

The current aligned scope now also includes:

- hardened read-only QA/BIM summaries for:
  - selected elements by category
  - selected elements by type
  - missing key parameters from selection
  - active-view MEP health check

Still outside proven live scope after this pass:

- live confirmation of the improved QA/BIM summaries on real mixed-discipline selections and active views

## 2026-04-15 QA/BIM Scope/Alias Note

The current aligned scope now also includes:

- explicit active-document scope messaging for selected-element QA/BIM actions
- explicit active-view scope messaging for the QA/BIM health-check action
- improved metadata-only alias coverage for the existing QA/BIM reviewed actions

Still outside proven live scope after this pass:

- live confirmation of the new scope wording in multi-project runtime scenarios
- live confirmation of the new QA/BIM alias coverage during real planner use

## 2026-04-15 QA/BIM Category Grouping Note

The current aligned scope now also includes:

- a targeted fix for the existing reviewed action `report selected elements by category`
- hardened category-name resolution for valid Revit category objects

Still outside proven live scope after this pass:

- live confirmation that grouped category output now renders correctly on active-document selections

## 2026-04-15 QA/BIM Validation Metadata Alignment Note

The current aligned scope now also includes:

- explicit `live_validated` metadata for the four QA/BIM actions with confirmed runtime evidence
- compact active document / active view / selection-count context lines for the existing QA/BIM outputs
- canonical reviewed-action detail resolution for Recent Prompts in ModelMind

Still outside proven live scope after this pass:

- runtime confirmation of the promoted validation-state display and Recent Prompt detail behavior in the UI
