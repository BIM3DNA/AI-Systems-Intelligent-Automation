# Evidence Reference

## Purpose

This file maps technical work in the repository to concrete WBSO evidence artifacts, validation notes, and repository-local documentation.

## Evidence ID Format

`EV-YYYY-MM-DD-###`

---

## EV-2026-04-03-001 — 2026 migration baseline setup

### Summary

Established the first 2026 repository-local migration baseline for **AI Systems & Intelligent Automation**. The project was re-scoped away from legacy company-facing extension identity and prepared as the current BIM3DNA / WBSO-aligned development stream.

### Why It Changed

This baseline was needed to:

- clean active extension metadata
- remove external/company-specific references
- simplify the working extension structure
- preserve legacy provenance without falsifying chronology
- introduce project-local WBSO technical evidence files before ongoing development continues

### Code / Repo Areas Affected

- extension metadata and visible project identity
- active pyRevit extension structure
- retained AI-relevant folders/modules
- repository-local WBSO structure

### WBSO Files Created / Updated

- `WBSO/Technical_Notes/architecture_notes.md`
- `WBSO/Technical_Notes/issue_log.md`
- `WBSO/Technical_Notes/evidence_reference.md`
- `WBSO/Technical_Notes/legacy_migration_map.md`
- `WBSO/Technical_Notes/pyrevit_extension_refactor.md`
- `WBSO/Technical_Notes/provider_strategy.md`
- `WBSO/Technical_Notes/current_scope_alignment.md`
- `WBSO/Testing_Validation/test_plan.md`
- `WBSO/Testing_Validation/experiment_log.csv`
- `WBSO/Testing_Validation/validation_summary_template.md`
- `WBSO/Testing_Validation/runs/2026-04-03_migration_baseline/validation_summary.md`
- `WBSO/Testing_Validation/runs/2026-04-03_migration_baseline/artifacts_manifest.txt`
- `WBSO/Data_Models/model_registry.md`
- `WBSO/Data_Models/provider_registry.md`
- `WBSO/Data_Models/prompt_asset_manifest.csv`

### Validation Status

At this evidence point, the repository baseline and evidence structure were established. Runtime pyRevit validation is planned as the next step and has not yet been recorded as completed in this entry.

### Artifacts / Where to Find Them

- Repo-local evidence root: `WBSO/`
- Migration notes: `WBSO/Technical_Notes/legacy_migration_map.md`
- Refactor notes: `WBSO/Technical_Notes/pyrevit_extension_refactor.md`
- Validation planning: `WBSO/Testing_Validation/test_plan.md`
- Baseline validation folder: `WBSO/Testing_Validation/runs/2026-04-03_migration_baseline/`

### Related Commit

Add the first baseline commit hash here after commit/push.

### Open Follow-up

- validate pyRevit loading after cleanup
- classify retained service/provider folders
- continue modular cleanup of remaining scripts/components

---

## EV-2026-04-03-002 — Project overview and scope alignment baseline

### Summary

Created the first WBSO-aligned project overview narrative for the 2026 AI Systems & Intelligent Automation repository phase and added current scope alignment notes inside the repository.

### Why It Changed

This step was needed to align:

- the repository’s current cleanup/migration phase
- the approved AI Agent / ModelMind direction
- the repo-local WBSO structure
- the future central WBSO administration update flow

### Evidence Sources

- `Project_Overview.docx` in central administration
- `WBSO/Technical_Notes/current_scope_alignment.md`
- `WBSO/Technical_Notes/architecture_notes.md`
- `WBSO/Technical_Notes/legacy_migration_map.md`

### Open Follow-up

Sync central WBSO administration files after the first baseline commit is pushed.

## EV-2026-04-03-003 — First pyRevit runtime validation of cleaned AI baseline

### Summary

Validated that the cleaned AI Systems & Intelligent Automation extension can be discovered and loaded by pyRevit after correcting the custom extension directory and rearranging the working folder structure. Also confirmed that clicking the active AI button opens the chat/UI window without immediate runtime errors.

### Why It Changed

The initial migration baseline established the cleaned repository structure and repo-local WBSO evidence layer, but actual runtime behavior still needed to be proven. This step was required to confirm that the cleaned pyRevit delivery surface is operational and not only structurally correct on disk.

### What Changed

- rearranged repository files/folders to match pyRevit extension discovery expectations
- added the correct custom extension directory in pyRevit settings
- refreshed pyRevit and revalidated extension loading
- clicked the active AI button to validate initial UI launch behavior
- updated repo-local WBSO evidence files with actual runtime results

### What Was Proven

- pyRevit discovers the cleaned extension
- the **AI** tab is visible in Revit
- the active button/script is visible in the AI tab
- clicking the button opens the chat/UI window
- no immediate runtime errors occur during initial UI launch

### What Was Not Yet Proven

- correctness of downstream provider/service logic
- correctness of AI request/response handling
- correctness of generated code or command execution against Revit
- full end-to-end AI Agent behavior

### Artifacts / Evidence

- screenshot of pyRevit settings showing the correct custom extension path
- screenshot of the AI tab visible in Revit
- screenshot/evidence of the button/UI launch state
- screenshots of repo structure after rearrangement
- updated validation summary
- updated experiment log row
- updated issue log entries

### Where to Find Them

- `WBSO/Testing_Validation/runs/2026-04-03_migration_baseline/`
- `WBSO/Testing_Validation/experiment_log.csv`
- `WBSO/Technical_Notes/issue_log.md`
- `WBSO/Technical_Notes/pyrevit_extension_refactor.md`

### Alignment with Report Scope

This validation aligns with the report’s AI Agent / ModelMind direction, which describes a dedicated AI tab inside pyRevit connected to local Codex/VS Code runtime, local models, and controlled execution workflows.

### Open Follow-up

- validate actual chat/provider behavior beyond UI launch
- classify retained provider/service folders more strictly
- decide in a later pass whether repo structure should be further normalized
