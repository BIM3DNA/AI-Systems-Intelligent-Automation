# Codex Handoff

## Current Branch
main

## Last Stable Commit
7cec120

## Current Focus
Runtime validation and export tooling for ModelMind reviewed actions.

The immediate priority is to support safer validation of ModelMind actions without changing the stable Revit execution architecture.

## Last Tested In Revit
- create ACO 1.4301 single socket pipe schedule from template: passed
- create ACO pipe fitting summary from template: passed
- ACO 1.4404 product-family templates: pending / empty-source issue

## Current ACO / Bunge Schedule State
- Generic native schedule actions by level/reference level are working and should stay `live_validated`.
- Generic ACO pipe schedule from template blocks correctly because there is no neutral all-ACO pipe master template.
- Generic ACO pipe summary from template blocks correctly because there is no neutral all-ACO pipe summary-compatible master template.
- ACO pipe fitting summary from template works from canonical `ACO pipe fittings` and is the only ACO/template action currently promoted based on live evidence.
- Product-family ACO pipe actions are template-only and should remain conservative.
- Product-family ACO source templates are now checked for visible body rows before duplication; empty sources block instead of creating empty schedules.

## Protected Areas
Do not touch unless explicitly requested:

- window lifecycle
- modal/modeless behavior
- `__persistentengine__`
- ExternalEvent / reviewed dispatch
- request timeout / dispatcher lifecycle
- create sheet execution path
- create 3D view execution path
- rename active view execution path
- shared undo plumbing

## Working Constraints
- Keep ACO/Bunge template actions template-only.
- Do not add native fallback for ACO template actions.
- Do not promote newly changed ACO/template actions without explicit live runtime evidence.
- Preserve the shared reviewed registry architecture across ModelMind and AI Agent.
- Keep generic native schedule actions separate from ACO/Bunge template-backed actions.

## Next Recommended Task
Build runtime validation/export tooling for ModelMind actions.

Suggested direction:
- add a read-only/export-focused validation report for reviewed ModelMind actions
- capture action id, title, handler, validation state, prompt aliases, and runtime result status
- avoid changing reviewed execution dispatch or Revit lifecycle behavior
- keep output suitable for WBSO/evidence updates and live Revit validation logs

## Local Notes
- `PROJECT_STATE.md` mirrors the current operational state.
- Root `TASKS.md` and `DEV_CONTEXT.md` were referenced by the IDE but were not present on disk during this update.
