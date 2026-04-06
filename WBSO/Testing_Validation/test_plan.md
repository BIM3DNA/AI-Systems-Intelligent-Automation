# Test Plan

## Project

AI Systems & Intelligent Automation

## Milestone

2026-04-03 migration baseline

## Purpose

This test plan defines the first validation checkpoint for the cleaned 2026 baseline of the repository.

## Goal

To verify that the cleaned and renamed pyRevit extension baseline remains technically usable after migration/refactor work and that the repository is ready for ongoing development under disciplined WBSO evidence capture.

## What Is Being Tested

1. extension metadata integrity
2. pyRevit recognition of the cleaned extension
3. visible tab/panel/button loading behavior
4. entry script launch behavior
5. controlled failure behavior if downstream AI/provider logic is still incomplete
6. basic alignment between repository structure and current project scope

## Why This Test Matters

The repository has been materially changed through:

- metadata cleanup
- naming cleanup
- structural reduction
- removal of obsolete items
- introduction of repo-local evidence files

Without validation, the migration baseline remains only structurally clean, not technically proven.

## Success Criteria

The baseline is considered valid if:

- pyRevit recognizes the extension
- the cleaned extension loads without structural errors
- the intended visible entry point appears correctly
- launching the entry point succeeds or fails in a clearly explainable way
- no external/company-facing naming remains in the active pyRevit-visible baseline
- evidence of the validation is saved in the repo-local WBSO structure

## Failure Criteria

The baseline is not yet valid if:

- pyRevit does not recognize the extension
- bundle metadata/path errors prevent loading
- the entry point is missing
- renaming caused unresolved script/icon/bundle references
- the cleaned baseline still exposes unwanted legacy identity
- the result cannot be documented clearly

## Validation Artifacts to Capture

- screenshot of extension structure in repo
- screenshot of pyRevit-visible result
- screenshot of any startup/load behavior
- screenshot of any runtime error if encountered
- short written validation summary
- artifact manifest of files/screenshots captured

## Planned Evidence Location

- `WBSO/Testing_Validation/runs/2026-04-03_migration_baseline/`
- `WBSO/Technical_Notes/evidence_reference.md`
- `WBSO/Testing_Validation/experiment_log.csv`

## Immediate Next Test After Baseline

After the first baseline push:

- validate pyRevit loading
- record output
- update validation summary
- update experiment log
- update evidence reference

## Execution Result — 2026-04-03 Runtime Validation

### Outcome

Pass

### What Was Confirmed

- pyRevit recognized the cleaned extension after correct path configuration
- the AI tab became visible
- the active button/script became visible in the tab
- clicking the button opened the chat/UI window
- no immediate runtime errors were observed during launch

### What Still Requires Testing

- actual provider/service behavior
- deeper chat workflow correctness
- AI-assisted code generation / execution flow
- controlled Revit interaction beyond initial UI launch
