# KC-047 Commit Note - MEP-RO-001 Read-Only BIM/QA Selection Action Pack

## Feature Package

- Feature ID: MEP-RO-001
- Name: ModelMind Read-Only BIM/QA Selection Action Pack
- Status: Implemented, live Revit validated, committed, pushed, and source-control closed
- Date: 2026-07-22
- Week: `2026-W18`
- Branch: `main`
- Evidence: EV-AI-343 through EV-AI-347
- Daily log: `DL-2026-07-22-01`; hours require manual entry

## Problem Statement

ModelMind required a deterministic way to inspect elements already selected by the user without invoking a picker, changing the Revit UI selection, mutating the model, or contaminating the evidence workflow. Existing reports did not provide one shared selection record for category/type summaries, stable identifiers, parameter availability, and generic QA health.

## Architectural Approach

MEP-RO-001 adds a shared read-only active-document selection collector. It reads current selection IDs, resolves each element defensively, preserves unavailable references, and builds reusable records. Four report projections consume that record. Routes dispatch deterministically before generic provider fallback and remain report-only/manual-run.

Deterministic sorting is applied to categories, family/types, identifiers, parameters, and affected IDs. Parameter identity is derived from available built-in ID, shared GUID, and project/family metadata. Reads are guarded and represented through present/missing/readable/unreadable coverage, storage type, read-only state, value variation, and normalized distinct values.

## Four Actions

1. `show selected elements summary` returns `MEP_SELECTION_SUMMARY_OK` with counts, category percentages, family/type grouping, deterministic ordering, and truncation metadata.
2. `show selected element identifiers` returns `MEP_SELECTION_IDENTIFIERS_OK` with ElementId, UniqueId, category, family/type, type ID, name, workset, design option, owner view, pinned, group, assembly, and active-document source classification.
3. `check selected element parameter availability` returns `MEP_SELECTION_PARAMETER_AVAILABILITY_OK` with parameter identity class, built-in ID/shared GUID, storage, coverage, readability, read-only state, value variation, and distinct normalized values.
4. `check selected elements qa health` returns GREEN, YELLOW, or PARTIAL through stable checks `SEL-QA-001` through `SEL-QA-016`.

Twenty canonical and alias routes are uniquely owned.

## Stable QA Mapping

- `SEL-QA-001` unavailable reference; `002` missing category; `003` missing type; `004` missing expected family/type.
- `SEL-QA-005` pinned; `006` grouped; `007` assembly member; `008` design option; `009` view-specific; `010` owner-view mismatch.
- `SEL-QA-011` blank Mark; `012` blank Type Mark; `013` duplicate nonblank Mark; `014` duplicate nonblank Type Mark.
- `SEL-QA-015` missing workset resolution; `016` unreadable parameter access.

## Output and No-Selection Controls

Limits are 200 identifier rows, 100 parameter rows, 50 affected IDs, 160 normalized-value characters, and 50 distinct values. No-selection returns `MEP_SELECTION_REPORT_NOT_READY` with `NO_ELEMENTS_SELECTED`; it does not open a picker or alter state.

## Workflow Isolation

All MEP-RO-001 classifications and the feature fallback are excluded from Workflow Anchor. The report header/classifications are not accepted by strict QA-source resolution. Context Suggestions can expose the actions only when selection exists, after the evidence-cycle dashboard. Visual Preview can show the raw latest MEP-RO-001 result while separately preserving the authoritative workflow anchor. Runbook and manifest state do not advance.

## Runtime Validation

Validation used `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`, `TEST [FloorPlan]` and `{3D - e.avdovicQREF7} [ThreeD]`, Piping.

- All four empty-selection paths returned Not ready without side effects.
- Pipe `3061679` validated summary, identifiers, workset/pinned data, and 181 parameter identities with 100 displayed and 81 omitted.
- Mixed Pipe/Fitting/Wall IDs `3063653`, `3063990`, `3130355` validated deterministic grouping and 268 parameter identities with 100 displayed and 168 omitted.
- Blank/duplicate Mark, blank Type Mark, duplicate Type Mark detector, pinned, group, large-selection, and affected-ID caps were validated.
- A 149-element selection displayed all identifiers; affected-ID samples capped at 50 with 99 omitted.

The different-type wall test was invalid: `RO001-DUP-TYPE` was entered into instance Mark, so `SEL-QA-013` fired while Type Mark remained blank and `SEL-QA-014` was not applicable. This is not an implementation defect and is not claimed as a successful different-type duplicate Type Mark test.

## Static and Governance Validation

Tabnanny, supporting-module compilation, prompt JSON parse (223 entries), 20-route uniqueness, representative legacy routes, deterministic helper assertions, `SEL-QA-001` through `016`, limits 200/100/50/160, dispatch precedence, workflow/QA exclusions, and `git diff --check` passed.

No new transaction, TransactionGroup, model mutation, parameter write, UI selection change, active-view switch, linked-document mutation, automatic dispatch, evidence-manifest write, or external export generation was introduced.

## Commit and Push Closure

- Commit: `9ad951cb7febc95506bfc023b360de59471e3e6a`
- Message: `Add read-only BIM QA selection reports`
- Files: `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`; `AI.extension/lib/prompt_catalog.json`
- Push: `main -> origin/main`
- Final alignment: ahead/behind `0/0`; source worktree clean

The initial OpenSSL certificate validation failure was a development-environment Git transport issue. A command-local Windows schannel retry succeeded; Git configuration was unchanged.

## Known Limitations

1. Revit Edit Group remains a restricted/modal editing context.
2. Assembly-member path was not practically live validated.
3. The 200-row identifier boundary was not crossed live.
4. Unavailable-reference paths were not encountered live.
5. Unreadable-parameter exception paths were not encountered live.
6. Parameter identity remains best-effort where Revit exposes no stable definition metadata.
7. Visual Preview remains textual and does not render a 3D viewport.
8. Different-type duplicate Type Mark test was invalid due to value entry in instance Mark instead of type-level Type Mark.

None blocks package closure.

## Daily Log / Hours

- Daily log ID: `DL-2026-07-22-01`
- Date: 22-07-2026
- Work recorded: implementation architecture; deterministic routing; shared collector; parameter and QA models; static/governance checks; live Revit validation; workflow isolation; source-control closure; project-local WBSO documentation.
- Hours: manual entry required; no supplied or project-local numeric value was found.

## Final Classification

IMPLEMENTED / LIVE REVIT VALIDATED / COMMITTED / PUSHED / SOURCE-CONTROL CLOSED.
