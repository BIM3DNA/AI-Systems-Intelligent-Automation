# Evidence Reference

## Purpose

This file maps technical work in the repository to concrete WBSO evidence artifacts, validation notes, and repository-local documentation.

## Evidence ID Format

`EV-YYYY-MM-DD-###`

---

## EV-2026-04-08-001 - AI window architecture refactor with structured prompts and guarded agent semantics

### Summary

Refactored the single pyRevit AI window into clearer product roles while preserving the single entry-point structure. Introduced a structured ModelMind prompt catalog, approved-recipe storage, local theme persistence, and explicit AI Agent session semantics.

### Why It Changed

This pass was needed to:

- clarify product responsibilities across Ollama Chat, ModelMind, and AI Agent
- remove hardcoded prompt-tree state from the UI controller
- introduce a safer approved-recipe concept for reviewed generated code
- make AI Agent controls behaviorally explicit and safety-oriented
- improve UX clarity without splitting the window or changing installer assumptions

### Code / Repo Areas Affected

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`
- `AI.extension/lib/ai_prompt_registry.py`
- `AI.extension/lib/ai_local_store.py`
- `AI.extension/lib/ai_agent_session.py`
- `AI.extension/lib/prompt_catalog.json`
- `AI.extension/lib/approved_recipes.json`

### WBSO Files Updated

- `WBSO/Technical_Notes/architecture_notes.md`
- `WBSO/Technical_Notes/issue_log.md`
- `WBSO/Technical_Notes/evidence_reference.md`
- `WBSO/Technical_Notes/pyrevit_extension_refactor.md`
- `WBSO/Technical_Notes/provider_strategy.md`
- `WBSO/Technical_Notes/current_scope_alignment.md`
- `WBSO/Testing_Validation/test_plan.md`
- `WBSO/Testing_Validation/experiment_log.csv`
- `WBSO/Testing_Validation/runs/2026-04-03_migration_baseline/validation_summary.md`
- `WBSO/Data_Models/model_registry.md`
- `WBSO/Data_Models/provider_registry.md`
- `WBSO/Data_Models/prompt_asset_manifest.csv`
- `README.md`

### What Was Actually Verified

- `prompt_catalog.json` parses successfully
- `approved_recipes.json` parses successfully
- `UI.xaml` is well-formed XML

### What Was Not Yet Verified

- pyRevit runtime loading after this refactor
- Revit UI launch after this refactor
- Ollama chat runtime response after this refactor
- Snowdon Towers Sample HVAC execution of the requested validation workflows

### Where to Find the Validation Notes

- `WBSO/Testing_Validation/test_plan.md`
- `WBSO/Testing_Validation/runs/2026-04-03_migration_baseline/validation_summary.md`
- `WBSO/Testing_Validation/experiment_log.csv`

### Open Follow-up

- perform live pyRevit/Revit validation on Snowdon Towers Sample HVAC
- confirm baseline preservation in the refactored UI
- refine agent planning heuristics after live use

---

## EV-2026-04-08-002 - Reviewed-code validator and approved-recipe hardening

### Summary

Hardened the ModelMind reviewed-code path so only pyRevit-compatible reviewed code can be approved/executed, and only successful reviewed runs can be saved as approved recipes.

### Why It Changed

Current live findings showed that:

- theme persistence already works across relaunch
- Ollama Chat already works in live runtime
- ModelMind deterministic tasks already work
- invalid reviewed code referencing DesignScript / Dynamo runtime modules had still been allowed to execute
- failed reviewed-code runs were correctly not being added to approved recipes and that rule needed to remain in force

### Code / Repo Areas Affected

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`
- `AI.extension/lib/ai_reviewed_code.py`
- `AI.extension/lib/ai_prompt_registry.py`
- `AI.extension/lib/prompt_catalog.json`

### What Was Added

- reviewed-code validation gate before approval
- reviewed-code validation gate immediately before execution
- explicit reviewed-code state label: `draft / validated / blocked / executed / saved`
- explicit `Save as Approved Recipe` action after success
- required approved-recipe metadata capture
- pyRevit-safe reviewed-code template for `create sheet`

### Live Findings Recorded

Live runtime findings reported for this pass:

- theme persistence works across relaunch
- Ollama Chat works in live runtime
- ModelMind deterministic tasks work

### Intentionally Blocked by Design

The validator now blocks reviewed code containing unsupported pyRevit runtime references such as:

- `Autodesk.DesignScript`
- `DesignScript`
- `RevitServices`
- `RevitNodes`
- `ProtoGeometry`
- `from Revit import ...`
- Dynamo-specific context APIs

### Still Not Yet Live-Validated After the Patch

- blocking behavior for invalid reviewed code in live Revit
- successful reviewed-code save flow in live Revit
- immediate approved-branch refresh after save in live Revit
