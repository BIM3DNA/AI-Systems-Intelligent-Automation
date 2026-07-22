# Model Registry

## Purpose

This file tracks the repo-local data/state models introduced for the current AI window architecture.

| Model ID | Asset | Type | Purpose | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| M-001 | `AI.extension/lib/prompt_catalog.json` | structured prompt catalog | backs the ModelMind available prompts tree with explicit metadata | active | deterministic and semi-generative recipe definitions |
| M-002 | `AI.extension/lib/approved_recipes.json` | reviewed recipe store | stores successful approved reviewed code as reusable local recipes | active | separate from the base prompt catalog |
| M-003 | local window settings file via `ai_local_store.py` | local UI state | persists dark/light theme selection locally | active | local filesystem path resolved at runtime |
| M-004 | agent session state via `ai_agent_session.py` | in-memory session model | holds current AI Agent goal, reviewed plan, toggle state, and execution status | active | session-scoped, not persistent across launches |
| M-005 | reviewed code preview state in `script.py` | UI state model | holds secondary reviewed-code visibility/content separate from the main result history | active | supports show/hide reviewed code UX |
| M-006 | planner provider state via `Model_Service/ModelService.py` + `chatgpt_service.py` | provider state model | reports local/cloud planner availability, key presence, provider reachability, and classified error state to the AI Agent UI | active | cloud path requires `OPENAI_API_KEY` from environment |
| M-007 | reviewed plan object via `ai_agent_session.py` | structured plan model | captures `matched_action`, `confidence`, `requires_modification`, `destructive`, `summary`, and `execution_ready` | active | execution remains constrained to supported deterministic/reviewed actions |
| M-008 | candidate reviewed deterministic action registry entry in `prompt_catalog.json` | catalog candidate model | records near-term but not yet enabled planner actions such as selected-duct total-volume reporting | candidate | not part of the active supported action set yet |

## 2026-05-06 AI-AGENT-002 Model Note

AI-AGENT-002 uses the existing cached Project Context and Project Onboarding data models to build a guided startup plan.

- no new persisted model store was introduced
- plan objects remain in-memory/session-scoped
- deterministic Project Context fallback can produce the guided plan without relying on a successful external provider request
- provider configuration was not changed

## 2026-05-07 MEP-RO-001 Selection Routing Note

The failed MEP-RO-001 validation shows that live Revit selection reports cannot rely on cached Project Context selection data alone.

- selection-report handlers must read `uidoc.Selection.GetElementIds()` at execution time
- deterministic BIM prompts that require live Revit state must not fall back to Ollama
- no new persisted model or provider configuration change is implied by this failure

## 2026-05-07 MEP-RO-001 Hotfix Validation Note

MEP-RO-001 now avoids generic Ollama fallback for known selection-report prompts after the routing/live-selection hotfix.

- deterministic Revit API handlers produced the validated selected-element reports
- handlers read the current live selection through `uidoc.Selection.GetElementIds()` and resolve elements with `doc.GetElement(id)`
- no new persisted model store was introduced
- no provider configuration was changed

## 2026-05-07 MEP-RO-002 / MEP-RO-003 Model Note

MEP-RO-002 and MEP-RO-003 are deterministic Revit API diagnostics, not model-provider features.

- known prompts do not depend on LLM output
- active-view reports read current active-view elements at execution time
- system assignment reports read current selection or active-view elements at execution time
- routing is deterministic before Ollama fallback
- no new persisted model store was introduced
- no provider configuration was changed

## 2026-05-07 MEP-RO-004 Model Note

MEP-RO-004 is not an LLM model-provider feature. It is a deterministic Revit API rule-evaluation layer routed before Ollama/OpenAI fallback for known discipline-QA prompts.

- selection-scope QA reads current selected elements at execution time
- active-view QA reads current active-view elements at execution time
- rule results are computed locally from safe readable Revit parameters/properties
- grouped sample ElementIds are deduplicated after the duplicate-rule aggregation hotfix
- no new persisted model store was introduced
- no provider configuration was changed

## 2026-05-14 MEP-RO-005 Model Note

MEP-RO-005 is not an LLM model-provider feature. It is a deterministic evidence-export layer for the latest accepted AI Workbench report.

- export prompts do not call Ollama/OpenAI
- generic Ollama outputs are not exported as deterministic QA evidence
- latest deterministic report state is session-local
- exported metadata records document/view context, source prompt, source header, report scope, and safety flags
- generated files are filesystem evidence artifacts only
- no persisted Revit model store was introduced
- no provider configuration was changed

## 2026-05-17 MEP-RO-006 Model Note

MEP-RO-006 is not an LLM model-provider feature. It is a deterministic filesystem index layer for exported QA evidence snapshots.

- index files are local filesystem artifacts
- index prompts do not call Ollama/OpenAI
- index entries record export metadata and safety/governance fields
- generic Ollama output remains rejected as deterministic export evidence
- no persisted Revit model store was introduced
- no provider configuration was changed

## 2026-05-17 MEP-ACT-001 Model Note

MEP-ACT-001 is not an LLM model-provider feature. It is a deterministic reviewed-action proposal/preflight layer.

- supported proposal prompts bypass Ollama/OpenAI
- proposal state is session-local
- split-selected-pipes preflight reads live selection only
- future action placeholders remain proposal-only
- no execution state, transaction, or write-action model was introduced
- generic Ollama output remains rejected as deterministic export evidence
- no provider configuration was changed

## 2026-05-18 MEP-WR-001 Model Note

MEP-WR-001 is not an LLM model-provider feature. It is a deterministic Revit selection dry-run and candidate reporting layer.

- supported prompts bypass Ollama/OpenAI
- dry-run state is session-local and exportable through deterministic report state
- midpoint split candidates are non-executable evidence only
- no transaction, pipe split, connector traversal, geometry extraction, linked-document scan, parameter write, or model mutation was introduced

## 2026-05-18 MEP-ACT-002 Model Note

MEP-ACT-002 is not an LLM model-provider feature. It is a deterministic confirmation guard layer.

- supported confirmation/status prompts bypass Ollama/OpenAI
- guard state is session-local and exportable through deterministic report state
- confirmation/apply/execute prompts are blocked until a future reviewed apply feature exists
- generic Ollama output remains rejected as deterministic export evidence
- no provider configuration was changed

## 2026-05-19 MEP-WR-002 Model Note

MEP-WR-002 is not an LLM model-provider feature. It is deterministic Revit API rollback-test logic for split dry-run candidates.

- supported rollback-test prompts bypass Ollama/OpenAI
- `ROLLBACK-TEST-OK` gates transaction opening
- `PlumbingUtils.BreakCurve` is used only inside a rollback transaction group
- rollback-test state is session-local and exportable through deterministic report state
- no persistent model store was introduced
- generic Ollama output remains rejected as deterministic export evidence

## 2026-05-19 MEP-WR-003 Model Note

MEP-WR-003 is not an LLM model-provider feature. It is deterministic reviewed apply logic for one rollback-tested split candidate.

- supported reviewed-apply prompts bypass Ollama/OpenAI
- candidate eligibility is decided from MEP-WR-001 and MEP-WR-002 session state, not provider output
- `PERSISTENT-SPLIT-OK` gates persistent transaction execution
- exactly one candidate can be applied per command
- generic Ollama output remains rejected as deterministic export evidence
- no provider configuration was changed

## 2026-05-25 MEP-WR-005 Model Note

MEP-WR-005 is not an LLM model-provider feature. It is a session-local governance state layer for split apply source consumption and staleness.

- state object: `latest_split_apply_consumed_source_state`
- records `consumed_by_feature_id`, consumed timestamp, dry-run source timestamp, rollback-test source timestamp, applied candidate number, applied original pipe id, returned new pipe id, consumed true/false, and persistent-apply eligibility
- marks a MEP-WR-001 dry-run / MEP-WR-002 rollback-test source as consumed only after successful MEP-WR-003 persistent apply
- blocks second persistent apply attempts from the consumed source before transaction
- requires a new successful rollback-test after the consumed timestamp before persistent apply is eligible again
- exposes `[SPLIT APPLY SOURCE STATE]` as a deterministic source-state report
- runtime validated in BUNGE on 2026-05-25

## 2026-05-26 MEP-WR-006 Model Note

Feature ID: MEP-WR-006
Feature: Split Result Visual Review / Select Elements Helper
Status: Runtime validated
Evidence: EV-AI-125 to EV-AI-132

MEP-WR-006 is a deterministic UI-only visual review helper for verified split results. It selects/highlights original and returned pipe elements from latest WR-004 / WR-003 state or explicit IDs.

- primary export: `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260526_180331`
- validated original pipe id: `3003513`
- validated returned new pipe id: `3130262`
- no transaction
- no BreakCurve
- no model mutation
- UI selection only

## 2026-05-28 MEP-WR-007 Model Note

Feature ID: MEP-WR-007
Feature: Split Workflow Session State Dashboard / Reset Helper
Status: Runtime validated
Evidence: EV-AI-133 to EV-AI-142

MEP-WR-007 is a deterministic session-state governance helper for the reviewed pipe split workflow. It displays and clears AI Workbench session-local split workflow state after explicit token confirmation.

- dashboard header: `[SPLIT WORKFLOW SESSION STATE]`
- reset header: `[SPLIT WORKFLOW SESSION RESET]`
- reset token: `CLEAR-SPLIT-STATE-OK`
- primary exports: `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260528_112016` and `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260528_112534`
- clears dry-run, rollback-test, reviewed apply, verification, consumed-source, and visual review session state only
- explicit post-reset verification proved original pipe `3087152` and returned pipe `3130262` remained in the Revit model
- no transaction
- no BreakCurve
- no model mutation
- existing persistent Revit split is not undone

## 2026-05-29 MEP-WR-008 Model Note

Feature ID: MEP-WR-008
Feature: Split Workflow Actionability Classifier / Dashboard Refinement
Status: Runtime validated
Evidence: EV-AI-143 to EV-AI-152

MEP-WR-008 is a deterministic session-state actionability classifier for the reviewed pipe split workflow. It distinguishes raw/latest report availability from actionable workflow source availability.

- report header: `[SPLIT WORKFLOW ACTIONABILITY STATE]`
- primary export: `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260529_164849`
- validated source prompt: `show split workflow actionability`
- validated source header: `[SPLIT WORKFLOW ACTIONABILITY STATE]`
- validated scope: `session-local reviewed split workflow actionability / active document only`
- distinguishes Not ready diagnostic reports from ready workflow source state
- classifies consumed/stale sources separately from fresh rollback-tested source state
- final export registration patch populates `latest_deterministic_report` for QA export
- no transaction
- no BreakCurve
- no session-state clearing
- no UI selection modification

## 2026-06-05 COORD-WR-005 Model Note

Feature ID: COORD-WR-005

Feature: Link Reset Workflow Status Dashboard

Status: Runtime validated and export/index validated

Evidence: EV-AI-181 to EV-AI-188

COORD-WR-005 is deterministic read-only workflow-state aggregation and classification logic. It reads compact serializable coordination state and the QA export index without rerunning audit, rollback, apply, or verification actions.

- report header: `[LINK RESET WORKFLOW STATUS]`
- shared state source: `pyrevit script envvar AI_WORKBENCH_COORD_SHARED_STATE`
- state keys: `latest_link_transform_audit_state`, `latest_passed_link_origin_reset_rollback_state`, `latest_link_origin_reset_apply_state`, `latest_link_origin_reset_post_apply_verification_state`, `latest_link_reset_workflow_status_state`
- validated link: `2972572 | 3D-01B-AR-01.ifc : 48`
- selected and no-selection dashboard status: `Ready / clean`
- final export: `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260605_163936`
- commit: `7e02f91 Add link reset workflow status dashboard`
- no raw Revit API objects stored in shared audit/verification snapshots
- no transaction, movement API, model mutation, linked-document mutation, or UI selection modification
- no model mutation

## 2026-06-01 MEP-WR-009 Model Note

Feature ID: MEP-WR-009
Feature: Split Apply Preflight Source Revalidation / External Edit Staleness Guard
Status: Runtime validated and export/index validated
Evidence: EV-AI-153 to EV-AI-160

MEP-WR-009 is deterministic preflight revalidation for the reviewed pipe split workflow. It runs before MEP-WR-003 persistent apply opens a transaction or calls BreakCurve.

- report header: `[SPLIT APPLY PREFLIGHT REVALIDATION]`
- primary export: `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260601_104232`
- validated source prompt: `check split apply preflight`
- validated source header: `[SPLIT APPLY PREFLIGHT REVALIDATION]`
- validated scope: `single split candidate preflight revalidation / active document only`
- validates dry-run/rollback source availability, selected candidate identity, consumed/stale state, current pipe resolution, pipe category, LocationCurve, line geometry, current length, candidate point projection, bounded-curve placement, and segment length rules
- WR-003 persistent apply now includes WR-009 preflight and proceeds only after preflight passes
- consumed/stale source blocks before transaction and BreakCurve
- external edit/source invalidation blocks safely before transaction and BreakCurve
- diagnostic route is read-only
- no connector traversal
- no geometry extraction beyond current pipe LocationCurve/Line reads required for revalidation
- no linked-document scan
- no session-state clearing
- no UI selection modification
- no model mutation in diagnostic route

## 2026-06-03 COORD-WR-001 to COORD-WR-003 Model Note

Feature IDs: COORD-WR-001, COORD-WR-002, COORD-WR-003

Feature:
Link Transform Audit / Rollback-Tested Reviewed Origin Reset

Status:
Runtime validated

Evidence:
EV-AI-161 to EV-AI-167

COORD-WR-001 is deterministic read-only `RevitLinkInstance` transform audit logic. COORD-WR-002 is deterministic rollback-test logic for a selected link origin reset. COORD-WR-003 is deterministic reviewed apply logic for a single selected link origin reset.

- audit header: `[LINK TRANSFORM AUDIT REPORT]`
- rollback header: `[LINK ORIGIN RESET ROLLBACK TEST]`
- reviewed apply header: `[LINK ORIGIN RESET REVIEWED APPLY]`
- rollback token: `ROLLBACK-LINK-RESET-OK`
- persistent apply token: `PERSISTENT-LINK-RESET-OK`
- shared state object: `latest_passed_link_origin_reset_rollback_state`
- shared state source: `pyrevit script envvar AI_WORKBENCH_COORD_SHARED_STATE`
- validated link id: `2972572`
- validated final origin: `(0.000000, 0.000000, 0.000000)`
- primary export: `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260603_150023`
- no batch/all-link reset
- no linked document mutation
- no reload/unload
- no pin/unpin
- no parameter writes
- no UI selection modification

## 2026-06-04 COORD-WR-004 Model Note

Feature ID: COORD-WR-004

Feature:
Link Origin Reset Post-Apply Verification Helper

Status:
Runtime validated and export/index validated

Evidence:
EV-AI-173 to EV-AI-180

COORD-WR-004 is deterministic read-only verification logic for the reviewed link origin reset workflow. It verifies the latest COORD-WR-003 applied state or exactly one selected `RevitLinkInstance` without opening a transaction or changing model data.

- report header: `[LINK ORIGIN RESET POST-APPLY VERIFICATION]`
- source state key: `latest_link_origin_reset_apply_state`
- shared state source: `pyrevit script envvar AI_WORKBENCH_COORD_SHARED_STATE`
- validated link id: `2972572`
- selected-link verification: `COORD-WR-004-20260604_152647`
- no-selection latest-state verification: `COORD-WR-004-20260604_152936`
- primary verification export: `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260604_153013`
- final audit export: `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260604_153603`
- stored element id use is verification-only
- no apply-by-stored-id behavior
- no transaction
- no TransactionGroup
- no MoveElement
- no model mutation
- no UI selection modification

## 2026-06-08 COORD-WR-006 Model Note

Feature ID: COORD-WR-006

Feature:
Link Reset Workflow History / Run Register

Status:
Runtime validated and export/index validated

Evidence:
EV-AI-189 to EV-AI-196

Commit:
`073eb567325b2155813a97be5533781c2e815d1f Add link reset workflow history register`

COORD-WR-006 is deterministic local-history logic for the reviewed Revit link reset workflow. It persists meaningful COORD-WR-005 checkpoints outside transient pyRevit shared state.

- report header: `[LINK RESET WORKFLOW HISTORY]`
- local folder: `C:\Users\User\Desktop\Results\AI_Workbench\Workflow_History`
- files: `link_reset_workflow_history.jsonl`, `link_reset_workflow_history.csv`
- source priority: meaningful shared COORD-WR-005 state, newest indexed `[LINK RESET WORKFLOW STATUS]` export, none
- recovered checkpoint: `COORD-WR-005-20260605_163912`
- recovered source export: `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260605_163936`
- duplicate prevention: `status_id`, or source export folder when status id is unavailable
- final history export: `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260608_094652`
- no raw Revit API objects stored
- no transaction, TransactionGroup, movement API, linked-document mutation, or UI selection modification

## 2026-06-11 COORD-WR-007 to COORD-WR-015 Model Note

Feature IDs: COORD-WR-007 through COORD-WR-015
Status: Runtime validated
Evidence: EV-AI-197 through EV-AI-215

The batch uses deterministic state dictionaries and local evidence files rather than LLM model output:

- WR-007/008: history reconciliation state
- WR-009: readiness advisor state with WR-008 QA-export fallback
- WR-010/011: evidence bundle and integrity state
- WR-012: current Revit link inventory health state
- WR-013: normalized snapshot record/signature in JSONL and latest CSV
- WR-014: snapshot baseline/drift status state
- WR-015: consolidated master status state

Final master report `COORD-WR-015-20260611_143248` returned `COORD_LINK_MASTER_CLEAN_WITH_HISTORY_SOURCE`. Commit: `3a1ab8d4b71c63cb08209e24dfafee939da98033 Add coordination link master status dashboard`.

## 2026-06-12 COORD-WR-016 to COORD-WR-020 Model Note

Feature IDs: COORD-WR-016 through COORD-WR-020
Status: Runtime validated
Evidence: EV-AI-216 through EV-AI-226
Commit: `713382d1ec97b453a2f48870172e08796f7f5aa1 Add coordination handover final evidence workflow`

The batch completes the deterministic coordination final-handover evidence model:

- WR-016: master evidence integrity state for export folders, indexes, history, and snapshots
- WR-017: normalized local handover register record/signature in JSONL and latest CSV
- WR-018: read-only handover register status and duplicate state
- WR-019: JSONL/CSV and referenced export integrity state
- WR-020: consolidated final handover closeout state

The final report `COORD-WR-020-20260612_171325` returned `COORD_HANDOVER_FINAL_READY_WITH_HISTORY_SOURCE`. WR-017 is the only feature in this batch that writes local evidence files; no feature modifies Revit model data.

## 2026-06-17 MEP-RO-v1 Model Note

Feature ID: MEP-RO-v1
Status: Runtime validated
Evidence: EV-AI-227 through EV-AI-238
Commit: `<insert latest commit hash from git log -1 --oneline>`

MEP-RO-v1 is deterministic read-only reporting logic for AI Workbench / ModelMind MEP QA. It does not use an LLM provider to decide report content, actionability, or export eligibility.

- report header: `[MEP READ ONLY V1 REPORT]`
- source files: `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`, `AI.extension/lib/prompt_catalog.json`
- scope: active-view and selected-element MEP QA reporting
- domains: BIM QA, HVAC/ducting, piping, electrical
- guarded boundary: selection-changing routes are blocked and reserved for MEP-SEL-v1
- QA export: latest deterministic report registration preserves original prompt, active document, and active view
- no transaction, TransactionGroup, parameter write, model mutation, linked-document mutation, reload/unload, pin/unpin, sheet/view/tag creation, or UI selection modification

## 2026-06-18 MEP-SEL-v1 Model Note

Feature ID: MEP-SEL-v1
Status: Runtime validated
Evidence: EV-AI-239 through EV-AI-247
Commit: `<insert actual commit hash from git log -1 --oneline>`

MEP-SEL-v1 is deterministic Revit UI selection-only logic for AI Workbench / ModelMind MEP QA. It is intentionally separate from MEP-RO-v1 because it may modify the Revit UI selection, but it must not modify Revit model data.

- report header: `[MEP SELECTION V1 REPORT]`
- source files: `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`, `AI.extension/lib/prompt_catalog.json`
- scope: reviewed Revit UI selection-only actions for active-view MEP QA
- domains: piping, HVAC/ducting, electrical fixtures/devices
- action areas: select active-view pipes/ducts/electrical devices; select unconnected pipe/duct fittings; select ducts without system assignment; select devices without circuit/system info
- QA export: latest deterministic report registration preserves original prompt, active document, and active view
- UI selection mutation: `UIDocument.Selection.SetElementIds` is allowed only inside MEP-SEL-v1 handlers and only when candidate count is greater than zero
- zero-candidate behavior: existing Revit UI selection is not cleared
- no transaction, TransactionGroup, parameter write, model mutation, linked-document mutation, reload/unload, pin/unpin, sheet/view/tag creation, delete, copy, mirror, connect/disconnect, join/unjoin, or alignment/model-modification action

## 2026-06-19 MEP QA Workbench Evidence Pipeline

Feature type: deterministic MEP QA evidence/reporting model.

Validated state/model concepts:

- active-view export rows for pipes, ducts, electrical devices, and issue candidates
- active-view bundle metadata, table counts, and generated evidence files
- active-view dashboard status classifications
- multi-view floor plan scan rows and view status classifications
- named-view detail target view resolution and issue groups
- named-view issue export file/index metadata
- project-level issue index rows with suggested follow-up commands

The pipeline is provider-independent and uses deterministic Revit API reads, local filesystem writes for explicit export/bundle commands, and latest deterministic QA report registration. Named-view and multi-view models rely on view-id collection and do not change active view or UI selection.

## 2026-06-24/25 AI Workbench Console Layer Model Note

Feature IDs:

- MEP-QA-ISSUEINDEX-EXPORT-v1
- AI-WORKBENCH-CONSOLE-v1
- AI-WORKBENCH-CONSOLE-UX-v1
- AI-WORKBENCH-SINGLE-CONSOLE-v1
- AI-WORKBENCH-SINGLE-CONSOLE-FIX-v1
- AI-WORKBENCH-SELECTION-GATE-FIX-v1

Status: Runtime validated

Evidence: EV-AI-259 through EV-AI-268

The batch adds deterministic console state and UI-facing command metadata on top of the existing prompt catalog and QA report state:

- prompt-catalog aliases and local suggestion ranking for autocomplete
- command confidence gating for unsupported prompt blocking
- prompt preview and safety preview metadata
- active Revit context summary using safe document/view/selection/category reads
- single Console-tab result routing for deterministic command output
- parsed result summary state for header, feature ID/name, result classification, export folder, issue counts, skipped/unreadable counts, and warnings
- selection-only confirmation state before enabling Run
- project issue-index export metadata for `MEP_Issue_Index_Exports`

The model is provider-independent for deterministic command routing. It does not use Ollama/OpenAI to decide whether known console commands may execute. Confirmed selection-only execution still returns the MEP-RO guard and is not yet a completed MEP-SEL-v1 dispatch path.

Commit evidence:

- `51a907e` - Add MEP project issue index export v1
- `95e052a` - Add unified AI Workbench console v1
- `f1dd511` - Improve AI Workbench console UX v1
- `546b843` - Route AI Workbench console results to single tab v1
- `134106d` - Fix AI Workbench selection confirmation gate v1
- `commit included in later console integration commit` - Fix AI Workbench console result summary parser v1
## 2026-06-25/29 AI Workbench Guided Console Workflow Model Note

Feature IDs:

- AI-WORKBENCH-SELECTION-DISPATCH-v1
- AI-WORKBENCH-CONSOLE-HISTORY-v1
- AI-WORKBENCH-CONSOLE-HISTORY-VIEWER-v1
- AI-WORKBENCH-CONTEXT-SUGGESTIONS-v1
- AI-WORKBENCH-RECIPE-PLANNER-v1
- AI-WORKBENCH-RECIPE-NAVIGATOR-v1
- AI-WORKBENCH-GUIDED-START-v1
- AI-WORKBENCH-GUIDED-COACH-v1
- AI-WORKBENCH-CONSOLE-LAYOUT-POLISH-v1

Status: Runtime validated

Evidence: EV-AI-289 through EV-AI-307

The batch adds guided workflow state and local evidence metadata on top of the existing deterministic Console:

- confirmed selection-only dispatch normalization to MEP-SEL-v1 aliases
- local command history files for executed Console commands
- latest result and session summary report/export state
- context suggestion state derived from active context, latest result, history, and prompt catalog entries
- recipe planner state for non-executing baseline and optional workflow steps
- recipe navigator state for loaded prompts and prompt-loading actions
- Guided Start prompt-loading state
- Guided Coach interpretation and recommended next-prompt state
- layout visibility state for collapsible Guided Start and Guided Coach panels

The model remains provider-independent for deterministic command routing and guidance. Ollama/OpenAI are not used to decide whether known guided console controls execute; guided controls do not execute commands at all.

Commit evidence:

- `not found in local git log` - Route confirmed AI Workbench selection commands to MEP-SEL v1
- `b38f488` - Add AI Workbench console command history
- `7d07e07` - Add AI Workbench console history viewer
- `b14867a` - Add AI Workbench context suggestions
- `ec771d7` - Add AI Workbench recipe planner
- `70f56ac` - Add AI Worbench recipe navigator
- `9a98076` - Add AI Workbench guided start
- `c366708` - Add AI Workbench guided coach
- `f037b07` - Polish AI Workbench console layout

## AI-WORKBENCH-QA-EXPORT-ANCHOR-v1

Status: Runtime validated

Commit: `378f5c3` - Use workflow anchor for QA report export

Implementation path: `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`

State/model relationship:

- consumes raw latest Console result metadata;
- consumes AI-WORKBENCH-WORKFLOW-ANCHOR-v1 metadata and retained workflow report text;
- preserves AI-WORKBENCH-NEXT-STEP-ENGINE-v1 load-only recommendation semantics;
- records export source mode and raw/anchor provenance in QA export metadata;
- treats `QA_REPORT_EXPORT_NOT_READY` as non-success;
- allows session-summary handoff only after `QA_REPORT_EXPORT_COMPLETE`.

Prompt catalog: unchanged.

Completed package: `AI-WORKBENCH-EVIDENCE-RUNBOOK-v1`, fully runtime-validated, committed, and pushed.

## AI-WORKBENCH-EVIDENCE-RUNBOOK-v1

Status: Implemented, fully runtime-validated, committed, and pushed. The Context Suggestions workflow-guidance inconsistency is closed.

Initial commit: `4f6eaf3` - Add AI Workbench evidence runbook.

Final package commit: `73c7f7916d54f79fccdf0ceda33f0cf6e47eca8d` - Complete AI Workbench evidence runbook workflow alignment.

Final correction status: evidence gate, active-cycle isolation, summary guards, strict source eligibility, terminal-cycle diagnostics, dark-theme corrections, and Context Suggestions alignment are committed and pushed to `origin/main`.

State/model relationship:

- consumes Console history, raw latest result, workflow anchor, and prompt catalog safety metadata;
- derives a four-stage evidence cycle and active boundary timestamp/history index;
- records active entries considered and historical entries ignored;
- exposes retry, handoff, terminal, restart, previous-cycle-complete, and new-dashboard-boundary-required state;
- caches only explicitly eligible QA source reports for active-cycle fallback;
- currently allowlists `MEP_QA_ISSUEINDEX_EXPORT_OK` as QA evidence source;
- blocks premature summaries with `AI_WORKBENCH_CONSOLE_SESSION_SUMMARY_NOT_READY`;
- blocks duplicate terminal-cycle summaries with `AI_WORKBENCH_CONSOLE_SESSION_SUMMARY_CYCLE_COMPLETE`;
- writes no files from runbook/status/load-only controls;
- makes Context Suggestions consume the active runbook stage and shared Next Step Engine while suppressing ineligible QA/session-summary workflow actions.

Provider relationship: provider-independent deterministic state resolution. No Ollama/OpenAI call determines stage, source eligibility, handoff, or terminal-cycle state.

Closure: Context Suggestions now consumes the runbook/evidence gate, recommends issue-index export after dashboard completion, respects strict QA-source eligibility, and restarts at a new dashboard after terminal cycle completion. Evidence: EV-AI-335 through EV-AI-337.

## AI-WORKBENCH-EVIDENCE-CYCLE-MANIFEST-v1

Status: Implemented, fully runtime-validated, committed, pushed, and source-control closed.

Commit: `4797b5e2b7f1be3aac63bccb24f809c8fbe7476b` - Complete AI Workbench evidence cycle manifest.

State/model relationship:

- creates deterministic cycle IDs from document, view, dashboard report ID, boundary timestamp, and boundary history index;
- persists `cycle_manifest.json` under `Desktop\Results\AI_Workbench\Evidence_Cycles\<cycle_id>`;
- records Stage 1-4 provenance and propagates cycle metadata through Stage 2-4 exports;
- tracks artifact occurrences, revisions, superseded artifacts, latest successful selections, completeness, provenance, and cross-stage cycle matching;
- preserves historical artifacts and supports legacy Console history without cycle IDs;
- exposes terminal and restart-required state plus read-only/load-only manifest guidance.

Validated cycle: `EVCYCLE-20260720-120400-fb9e254b78`; four stages complete; provenance valid; cross-stage match true; two duplicate stage artifacts; terminal and restart required. Evidence: EV-AI-338 through EV-AI-342.

## MEP-RO-001 - ModelMind Read-Only BIM/QA Selection Action Pack

Status: Implemented, live Revit validated, committed, pushed, and source-control closed.

Commit: `9ad951cb7febc95506bfc023b360de59471e3e6a` - Add read-only BIM QA selection reports.

The package adds four deterministic report models over the user's existing active-document selection: category/type summary, stable identifiers, parameter availability, and generic QA health. A shared safe collector resolves selected IDs without opening a picker and preserves unavailable references. Sorting is deterministic; output is bounded at 200 identifier rows, 100 parameter rows, 50 affected IDs, and 160 normalized-value characters.

QA state uses stable checks `SEL-QA-001` through `SEL-QA-016`. No-selection returns `MEP_SELECTION_REPORT_NOT_READY` with `NO_ELEMENTS_SELECTED`. All result classifications are excluded from workflow-anchor and strict QA-source eligibility. No transaction, model/UI-selection/view/link mutation, automatic dispatch, evidence-manifest write, or external export is introduced. Evidence: EV-AI-343 through EV-AI-347.
