# Legacy Migration Map

## Purpose

This file documents how legacy AI/pyRevit work is being carried into the current repository **AI Systems & Intelligent Automation**.

The objective is to preserve provenance while keeping the current repository clearly defined as the **2026 migration + refactor + active development stream**.

## Migration Rule

- Legacy repositories and older local code are treated as source lineage / technical baseline.
- Current 2026 work includes:
  - cleanup
  - renaming
  - refactor
  - structural simplification
  - validation
  - modularization
  - new implementation
- Historical work is not replayed or re-dated as if it happened in 2026.
- Only actual 2026 adaptation and current development work is logged as present WBSO activity.

## Legacy Source Lineage

Primary legacy references:

- earlier AI agent and ModelMind concepts
- earlier pyRevit extension work
- prior repository and local development streams associated with AI-assisted Revit automation
- legacy company-specific extension/tab/panel/button structures that formed the initial starting shell for the current cleanup

The development report describes this project direction as an AI Agent / ModelMind Codex System inside pyRevit, including an Ollama chatbox layer, model-context retrieval, deterministic commands, code generation, and safe execution against Revit. It also describes the AI Agent tab as a bridge to a local Codex/VS Code environment for controlled automation work. :contentReference[oaicite:2]{index=2}

## Migration Table

| Legacy Component / Area                | Legacy Role                                           | 2026 Action                                      | Current Status   | Notes                                                     |
| -------------------------------------- | ----------------------------------------------------- | ------------------------------------------------ | ---------------- | --------------------------------------------------------- |
| legacy pyRevit extension shell         | historical delivery vehicle for tools and experiments | kept as starting shell, then cleaned and renamed | active baseline  | used only as migration scaffold                           |
| external/company-specific metadata     | project identity in old extension state               | removed / rewritten                              | resolved         | active metadata now aligned to BIM3DNA / WBSO direction   |
| old toolbar / panel / button structure | mixed production + dev + company-specific items       | reduced and simplified                           | transitional     | only AI-relevant or still-reviewable items should remain  |
| DevButton-style experimental bundles   | temporary testing entry points                        | mostly deleted / reduced                         | reduced          | obsolete items intentionally removed from active baseline |
| AI-related pyRevit script entry point  | experimental entry into AI workflow                   | retained temporarily                             | active candidate | may later be renamed or modularized further               |
| `lib/` helper code                     | shared support layer                                  | selective keep                                   | pending review   | retain only if required by current scope                  |
| `hooks/`                               | extension support infrastructure                      | selective keep                                   | pending review   | preserve only if still useful                             |
| `Model_Service/`                       | service/model runtime experiments                     | carried forward for review                       | active candidate | needs further architecture classification                 |
| `Openai_Server/`                       | provider/API integration experiments                  | carried forward for review                       | active candidate | needs provider-boundary review                            |
| root utility/test scripts              | local experiments and checks                          | review individually                              | mixed            | keep only scope-relevant files                            |
| old requirements files                 | dependency snapshots                                  | consolidate later                                | transitional     | final dependency surface still to be cleaned              |

## What Was Changed in 2026

The following categories of work are treated as actual 2026 migration/refactor work:

- removing company-specific identity from active extension metadata
- cleaning pyRevit-visible naming
- reducing obsolete toolbar content
- retaining only project-relevant AI/service/provider candidates
- introducing repo-local WBSO structure
- documenting migration logic and architectural intent
- preparing the cleaned baseline for first validation and first stable push

## What Was Intentionally Removed

The following categories were intentionally targeted for removal from the active baseline where not in scope:

- obsolete company-specific bundles
- temporary dev buttons no longer needed in current architecture
- duplicate or unclear scripts without an active role
- external/company references in metadata, naming, and documentation

Detailed removal/cleanup decisions should also be reflected in:

- `issue_log.md`
- `pyrevit_extension_refactor.md`

## What Was Intentionally Kept

The following categories may remain temporarily if they still support current technical review:

- pyRevit extension skeleton needed for baseline loading
- AI-relevant entry point scripts
- service/provider candidate folders pending further architecture review
- helper/support code not yet proven removable

## Evidence Linkage

Related files:

- `WBSO/Technical_Notes/architecture_notes.md`
- `WBSO/Technical_Notes/issue_log.md`
- `WBSO/Technical_Notes/evidence_reference.md`
- `WBSO/Technical_Notes/pyrevit_extension_refactor.md`
- `WBSO/Testing_Validation/test_plan.md`

## Update Rule

Update this file only when:

- a legacy component is newly classified
- a retained module is moved into current architecture
- a component is definitively deleted
- a rename materially changes provenance mapping
- a migration decision becomes final enough to record
