# KC-040 - AI Workbench Guided Console Workflow

## Batch

AI Workbench Guided Console Workflow - selection dispatch, history, suggestions, recipes, guided onboarding, coaching, and layout polish

## Date Range

2026-06-25 to 2026-06-29

## Workstream

AI Workbench / ModelMind / Revit MEP QA automation

## Evidence Range

EV-AI-289 through EV-AI-307

## Daily Log References

- DL-2026-06-25-02 - Selection dispatch fix and runtime validation
- DL-2026-06-26-01 - Console history and history file validation
- DL-2026-06-29-01 - History viewer, context suggestions, recipe planner, navigator, guided start, guided coach, and layout polish validation

## Features

- AI-WORKBENCH-SELECTION-DISPATCH-v1
- AI-WORKBENCH-CONSOLE-HISTORY-v1
- AI-WORKBENCH-CONSOLE-HISTORY-VIEWER-v1
- AI-WORKBENCH-CONTEXT-SUGGESTIONS-v1
- AI-WORKBENCH-RECIPE-PLANNER-v1
- AI-WORKBENCH-RECIPE-NAVIGATOR-v1
- AI-WORKBENCH-GUIDED-START-v1
- AI-WORKBENCH-GUIDED-COACH-v1
- AI-WORKBENCH-CONSOLE-LAYOUT-POLISH-v1

## Technical Summary

The AI Workbench Console was extended from a deterministic command execution interface into a guided ModelMind workflow environment. The batch fixed confirmed selection-only dispatch, added local command history, added history viewing and session summary export, added context-aware recommendations, added deterministic QA evidence recipes, added safe prompt-loading navigation, added a beginner-facing Guided Start workflow, added post-result Guided Coach recommendations, and polished the layout so guidance remains visible without making the result summary unusable.

## Runtime Context

- Model: `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`
- Active view: `TEST [FloorPlan]`
- Discipline: Piping
- Pipe fittings: 97
- Pipes: 18
- Initial selection: 0
- Project issue-index scan: 15 eligible views, 15 scanned, 0 skipped, 14 with MEP inventory, 8 with issue candidates, 538 total MEP inventory, 24 issue candidates, 8 issue-index rows exported.

## Main Runtime Results

- `select all pipes` routed to MEP-SEL-v1 after explicit confirmation and selected 18 pipes.
- Console command history generated local JSONL/CSV/latest-result files under `Console_History`.
- History viewer and session summary reports were visible inside the Console.
- Context suggestions detected Piping context and generated eight next-action suggestions without execution.
- Recipe planner produced four baseline QA evidence steps and two optional piping review steps, all non-executing.
- Recipe navigator loaded prompts only and preserved explicit Run as the execution boundary.
- Guided Start loaded beginner workflow prompts only.
- Guided Coach interpreted results and loaded recommended next prompts only.
- Layout polish added collapsible guided panels, grouped controls, and a 220 minimum result summary height.

## Safety and Governance

- No `DB.Transaction` or `DB.TransactionGroup` added.
- No Revit model mutation APIs added.
- No parameter writes added.
- No active-view switching added.
- No linked-document mutation added.
- No automatic command execution from guided, navigator, or coach buttons.
- Selection mutation remains isolated to existing MEP-SEL-v1 and requires explicit confirmation.
- Unsupported prompt `banana cut all pipes with dragon` remains blocked.
- Exports write only to approved AI_Workbench result folders.

## Known Follow-Up

`AI-WORKBENCH-SELECTION-CONFIRM-COMPACT-v1` remains future work. The selection-only confirmation card should remain explicit for safety, but a compact one-line confirmation strip, session-level remembered confirmation, small persistent badge, or context-only confirmation display should be investigated.

## 2026-07-06 Addendum - Console UX Runtime Batch

### Evidence Range

EV-AI-308 through EV-AI-319

### Features

- AI-WORKBENCH-SELECTION-CONFIRM-COMPACT-v1
- AI-WORKBENCH-CONSOLE-SHELL-SIMPLIFY-v1
- AI-WORKBENCH-ALIAS-ROUTE-HARDENING-v1
- AI-WORKBENCH-SAFE-CATALOG-VIEW-v1
- AI-WORKBENCH-VISUAL-v1
- AI-WORKBENCH-VISUAL-ACTION-CARDS-v1

### Runtime Context

- Model: `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`
- Active view: `TEST [FloorPlan]`
- Discipline: Piping
- Pipe fittings: 97
- Pipes: 18

### Runtime Results

- Compact selection confirmation validated: `select all pipes` selected 18 pipes only after explicit confirmation and kept model modified false.
- Console shell simplification validated: Console is the default visible tab, legacy tabs are hidden by default, and utility controls are collapsed by default.
- Alias route hardening validated: `show latest result` and `show latest console result` route to the Console latest-result viewer, not split visual review.
- Safe Catalog validated: legacy/model-write/reviewed-action commands are hidden by default and remain guarded when Advanced Commands is enabled.
- Visual Preview validated: `[AI WORKBENCH VISUAL PREVIEW REPORT]` shows View Context, Latest Result, Issues / Candidates, and Safe Next Action cards.
- Visual Action Cards validated: Load buttons populate safe prompts only, do not auto-run, do not write history on load, and preserve selection confirmation.

### Commit References

- `a7333d1` - Compact AI Workbench selection confirmation
- `30505cb` - Simplify AI Workbench console shell
- `ee64658` - Harden AI Workbench alias routing
- `75e1c38` - Filter AI Workbench command catalog for safe mode
- `a44e4bc` - Add AI Workbench visual preview panel
- `7faea67` - Add load-only visual action cards

### Safety

No Revit model mutation, `DB.Transaction`, `DB.TransactionGroup`, parameter write, active-view switch, linked-document mutation, or automatic command execution was introduced. Selection-only commands still require explicit confirmation. Visual Action Cards load prompts only and do not write Console history or exports on load.

### Pending Follow-Up

AI-WORKBENCH-NEXT-STEP-ENGINE-v1 is pending runtime validation and is not documented as completed, implemented, pushed, or validated in this evidence batch.

## 2026-07-08 Addendum - Next-Step Workflow Anchor Batch

### Evidence Range

EV-AI-320 through EV-AI-323

### Features

- AI-WORKBENCH-NEXT-STEP-ENGINE-v1
- AI-WORKBENCH-WORKFLOW-ANCHOR-v1

### Runtime Context

- Model: `BUNGE_BvdK_R24_3D_Loading Building_e.avdovicQREF7`
- Active view: `TEST [FloorPlan]`
- Discipline: Piping
- Pipe fittings: 97
- Pipes: 18

### Runtime Results

- Next Step Engine validated: `[AI WORKBENCH NEXT STEP REPORT]` returned `AI_WORKBENCH_NEXT_STEP_OK`, identified Guided Coach, Visual Preview, Utility Load Next, and Recipe Navigator Load Next as shared resolver surfaces, and kept auto-run false.
- Dashboard GREEN mapped to `export mep project issue index`.
- Issue-index export OK mapped to `export latest QA report`.
- QA report export complete mapped to `export ai workbench console session summary`.
- Selection OK mapped to `show active view mep qa dashboard`.
- Context suggestions OK mapped to `create mep qa evidence recipe`.
- Recipe planner OK mapped to `show active view mep qa dashboard`.
- Workflow Anchor validated: Visual Preview status, Next Step status, latest-result viewer, and history-style meta commands are skipped for next-step state, while raw latest result remains visible for inspection.
- Dashboard and recipe planner anchors survived Visual Preview status; issue-index export anchor survived latest-result viewer.

### Commit References

- `046ba44` - Unify AI Workbench next step recommendations
- `157e995` - Anchor next step recommendations to workflow results

### Safety

No Revit model mutation, `DB.Transaction`, `DB.TransactionGroup`, parameter write, active-view switch, linked-document mutation, direct selection API, or automatic command execution was introduced. Load Next remains load-only. Exports occur only after manual Run.

### Known Follow-Up

AI-WORKBENCH-QA-EXPORT-ANCHOR-v1 is pending only. During workflow anchor validation, `export latest QA report` still used raw latest meta/viewer output after `show latest result`, so QA export failed with `[QA REPORT EXPORT] Latest output is not a deterministic AI Workbench QA report. Run a read-only deterministic report first.` This is a workflow-source integration defect, not a model-safety defect.

## 2026-07-10 Addendum - QA Export Anchor Completed

AI-WORKBENCH-QA-EXPORT-ANCHOR-v1 is now implemented and runtime validated in commit `378f5c3`. It closes the downstream source-selection gap after the Next Step Engine and Workflow Anchor, preserves the existing QA snapshot/index structure, adds explicit not-ready behavior, and prevents false session-summary handoff.

The successful runtime export reported `Export source mode: raw latest`; workflow-anchor fallback is implemented but was not directly selected in that run. Evidence: EV-AI-324 through EV-AI-328. `AI-WORKBENCH-EVIDENCE-RUNBOOK-v1` remains pending.

## Commit References

- `not found in local git log` - Route confirmed AI Workbench selection commands to MEP-SEL v1
- `b38f488` - Add AI Workbench console command history
- `7d07e07` - Add AI Workbench console history viewer
- `b14867a` - Add AI Workbench context suggestions
- `ec771d7` - Add AI Workbench recipe planner
- `70f56ac` - Add AI Worbench recipe navigator
- `9a98076` - Add AI Workbench guided start
- `c366708` - Add AI Workbench guided coach
- `f037b07` - Polish AI Workbench console layout

## Conclusion

KC-040 records the runtime-validated guided console workflow batch after KC-039. The batch improves user discoverability, traceability, workflow planning, guided onboarding, and result interpretation while preserving strict deterministic routing and Revit safety boundaries.
