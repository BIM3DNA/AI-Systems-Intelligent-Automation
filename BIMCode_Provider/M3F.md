# BIMCode AI pane M3F - mixed-specialty Summary

## 2026-09-24 - M3F final documentation checkpoint (current)

BIMCODE-REVIT-AI-PANE-001 / M3F - Mixed-Specialty Read-Only Summary.

- DISCOVERY COMPLETE
- IMPLEMENTATION COMPLETE
- STATIC VALIDATION PASSED
- IMPLEMENTATION CHECKPOINT COMMITTED / PUSHED
- PROJECT-LOCAL WBSO CHECKPOINT COMMITTED / PUSHED
- STATUS RECONCILIATION COMMITTED / PUSHED
- LIVE VALIDATION 12/12 PASS
- FINAL STATIC / REGRESSION AUDIT PASSED
- READY FOR SOURCE-CONTROL CLOSURE
- FINAL DOCUMENTATION UPDATED
- FINAL CLOSURE COMMIT / PUSH PENDING
- NOT YET SOURCE-CONTROL CLOSED

Authoritative current status supersedes earlier pending-live/pre-commit wording.
Earlier dated checkpoints below are historical, not current closure claims.
Discovery: ae06fc6e5fc4cede99279b9921d2826f94a5fc75.
Implementation / project-local WBSO: 8b43f006c1b1bb7c5a013c89d261e96801911d9e.
Status reconciliation: 3cb9a4724d58b1d643ecddecb6e52c178fadc644,
subject: docs(wbso): reconcile M3F implementation checkpoint status.
Before this edit: main HEAD = origin/main = reconciliation SHA, ahead/behind 0/0;
parent = implementation/WBSO SHA. No staged or non-ignored untracked files.
This final documentation is not committed/pushed; no final closure commit exists.

Feature MEP-MULTI-RO-001; action MEP-MULTI-RO-001-A01; AI tool
summarize_selected_mep_elements. Read-only mixed-selection SUMMARY ONLY.
Current AI surface: 13 READ-ONLY TOOLS (Piping 4 / HVAC 4 / Electrical 4 / MEP 1).
One provider-selected tool, one host orchestration request, one existing Revit
ExternalEvent, one captured evaluation selection/context snapshot, deterministic
host partition, snapshot-fed specialty A01 cores, one composite deterministic
result, bounded provider projection, then final natural-language response.
The final selection integrity reread is not another evaluation snapshot.
No UI-selection mutation, recursive execute_headless_modelmind_readonly call,
nested ExternalEvent, provider-selected specialty list or child action IDs,
autonomous provider multi-tool loop, model writes, generic Revit command tool,
ElementId tool arguments or generated-code execution. Sidecar has no Revit API.
Provider network scope unchanged; .env.local ignored/untracked and not read.
No Authorization-header logging found. No secret contents copied to records.

Final audit evidence (recorded here, not rerun by this documentation task):
288 Python tests PASS; 66 native probes PASS; 7 IronPython host files PASS;
33 sanitized AST/in-memory compile/tabnanny files PASS; native XAML/WPF/theme/Find
PASS; catalog 237 unchanged; mutation/network-boundary/AI-allowlist protections
PASS; credential-pattern scan 115 tracked text files, 0 findings (not exhaustive
secret proof); dependency check: no broken requirements; git diff --check PASS.
Workbench discovery baseline: 1475 original functions, 1478 current; 1472 original
functions source-identical, 3 reviewed wrappers and 3 new snapshot-fed cores.
Extracted cores preserve original implementation remainders; reconstructed
baseline equivalence PASS. Closed PIPING-RO-001/HVAC-RO-001/ELECTRICAL-RO-001
semantics and single-specialty A01 contracts preserved. HVAC-QA-009 still uses
physical End count and permits valid Curve/tap connectors. Electrical QA has
neither open-connector nor connector-count checks. No introduced defect found.

LIVE-M3F-01 through LIVE-M3F-12 are PASS, based on user-supplied Revit evidence;
Codex did not independently rerun live cases or authenticated OpenAI requests.
Exact matrix, actual prompts and classification/reason contract are recorded in
BIMCode_Provider/M3F.md and WBSO/Technical_Notes/evidence_reference.md, in their
current final documentation sections. Transport/display truncation is distinct
from semantic PARTIAL: successful 01-08 remain SUMMARY_OK / COMPLETE despite
explicit lower-priority display omissions; actual unsupported scope caused 09.

Nonblocking coverage, not defects: unresolved-reference, child-failure PARTIAL,
child-NOT_READY PARTIAL, processing/admission-cap exceedance, larger mixed-selection
performance and advisory time-budget paths were not deliberately reproduced live.
Relevant fail-closed behavior has offline/static coverage. Provider projection
can omit lower-priority display details; no unobserved live PASS is claimed.

Nonblocking Git observation: AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py
is reported modified by status, but its content diff is empty. Filtered working-tree
and HEAD objects both equal 98c548c522874f736063446d2c048b9d325afc98.
Status/index/line-ending anomaly with no identified content difference, not a
runtime modification or M3F defect. Worktree must not be called clean.
File left untouched; source-control housekeeping may be reviewed next session.

M3F Evidence ID: PENDING. Daily Log ID: PENDING. Knowledge Capture ID: PENDING.
Project-local hours: PENDING. No identifiers/hours allocated or central IDs reused.
Central WBSO remains separately managed outside this repository.
Next: audit this documentation delta, authorize final documentation commit/push,
verify HEAD/origin alignment and closure, then mark M3F SOURCE-CONTROL CLOSED.
Next R&D milestone after closure: M4 controlled low-risk write research.
No M4 implementation, runtime/test/dependency/catalog/secret change, staging,
commit or push is performed by this documentation-only task.

### Final live evidence and classification contract

All rows below are user-supplied live Revit evidence, not new Codex test runs.
Cases 01-10 use summarize_selected_mep_elements -> MEP-MULTI-RO-001-A01.
In 01-08 the composite is MEP_MULTI_SELECTION_SUMMARY_OK / COMPLETE.
Single-specialty children report PIPING_SELECTION_SUMMARY_OK,
HVAC_SELECTION_SUMMARY_OK or ELECTRICAL_SELECTION_SUMMARY_OK / COMPLETE.

| Case | Observed evidence | Result |
| --- | --- | --- |
| LIVE-M3F-01 | Pipe only; PIPING-RO-001-A01; supported 1, unsupported 0, unresolved 0, no warnings | PASS |
| LIVE-M3F-02 | Rigid non-placeholder Duct only; HVAC-RO-001-A01; supported 1, unsupported 0, unresolved 0, no warnings | PASS |
| LIVE-M3F-03 | Electrical Fixture 356066, Duplex Receptacle / Standard; DEVICE_PROFILE, SUPPORTED_ELECTRICAL_FIXTURE, DEVICE_UNASSIGNED_REVIEW; ELECTRICAL-RO-001-A01 | PASS |
| LIVE-M3F-04 | Equipment 354806, P109; EQUIPMENT_PROFILE, SUPPORTED_ELECTRICAL_EQUIPMENT, EQUIPMENT_DISTRIBUTION_EMPTY_REVIEW; systems 0, LOAD 0, BASE_EQUIPMENT 0; ELECTRICAL-RO-001-A01 | PASS |
| LIVE-M3F-05 | Pipe + Duct; only PIPING-RO-001-A01 and HVAC-RO-001-A01; both COMPLETE | PASS |
| LIVE-M3F-06 | Pipe + Electrical; only PIPING-RO-001-A01 and ELECTRICAL-RO-001-A01; both COMPLETE | PASS |
| LIVE-M3F-07 | Duct + Electrical; only HVAC-RO-001-A01 and ELECTRICAL-RO-001-A01; both COMPLETE | PASS |
| LIVE-M3F-08 | All three specialties; all three A01 children COMPLETE; supported 3, unsupported 0, unresolved 0, warnings 0 | PASS |
| LIVE-M3F-09 | Pipe 353871 + Conduit 358784; MEP_MULTI_SELECTION_SUMMARY_PARTIAL / UNSUPPORTED_ELEMENTS_PRESENT; Piping A01 SUMMARY_OK / COMPLETE retained; Conduit UNSUPPORTED_CATEGORY, unresolved 0; no Electrical reinterpretation, retry or second provider tool | PASS |
| LIVE-M3F-10 | Conduit 358784 only; MEP_MULTI_SELECTION_NOT_READY / NO_SUPPORTED_SELECTED_ELEMENTS; no sub-actions, no child or Electrical reinterpretation | PASS |
| LIVE-M3F-11 | Actual prompt: What is the difference between a pipe, a duct, and an electrical conduit in Revit? Normal provider response; no tool, ModelMind action, host execution or model interaction | PASS |
| LIVE-M3F-12 | Actual prompt: Move the selected pipe 500 mm upward. Provider explained read-only tools; no tool/action/write, ExternalEvent mutation request, DB.Transaction or model modification | PASS |

Successful 01-08 sometimes omitted selection-scope, workset/distribution,
insulation/lining, individual detailed element rows or empty Electrical
panel/circuit tables. All supported child evaluations completed, no semantic
unsupported/unresolved scope existed, and omission metadata remained explicit.
These are display omissions, not semantic PARTIAL. Case 09 demonstrates actual
semantic PARTIAL while retaining the supported child's semantic result.

Exactly four composite classifications:
- MEP_MULTI_SELECTION_SUMMARY_OK
- MEP_MULTI_SELECTION_SUMMARY_PARTIAL
- MEP_MULTI_SELECTION_NOT_READY
- MEP_MULTI_SELECTION_FAILED

Implemented composite reason codes:
COMPLETE; NO_ELEMENTS_SELECTED; NO_SUPPORTED_SELECTED_ELEMENTS;
NO_VALID_DOCUMENT_CONTEXT; SELECTION_UNREADABLE; SELECTION_LIMIT_EXCEEDED;
EXECUTION_BUSY; STALE_CONTEXT; RESULT_PROJECTION_FAILED;
COMPOSITE_EXECUTION_FAILED; NO_USABLE_SPECIALTY_RESULT; SUBACTION_FAILED;
SUBACTION_NOT_READY; SUBACTION_PARTIAL; UNSUPPORTED_ELEMENTS_PRESENT.
Additional child/scope diagnostics: TIME_BUDGET_EXCEEDED;
HEADLESS_EXECUTION_FAILED; UNRESOLVED_REFERENCE; UNSUPPORTED_CATEGORY.

## Historical M3F implementation checkpoint reconciliation - 2026-09-24

BIMCODE-REVIT-AI-PANE-001 / M3F - Mixed-Specialty Summary.

- DISCOVERY COMPLETE
- IMPLEMENTATION COMPLETE
- STATIC VALIDATION PASSED
- IMPLEMENTATION CHECKPOINT COMMITTED / PUSHED
- PROJECT-LOCAL WBSO CHECKPOINT COMMITTED / PUSHED
- LIVE VALIDATION PENDING
- NOT CLOSED

Implementation and project-local WBSO share the verified checkpoint
`8b43f006c1b1bb7c5a013c89d261e96801911d9e`, subject `project WBSO update...`.
At reconciliation start: main HEAD = origin/main = that SHA; ahead/behind 0/0.
This is an implementation checkpoint, not M3F final/source-control closure.
LIVE-M3F-01 through LIVE-M3F-12 remain NOT STARTED / PENDING; no live PASS claimed.

Technical state unchanged: summarize_selected_mep_elements -> MEP-MULTI-RO-001-A01,
mixed-specialty SUMMARY ONLY; 13 read-only tools (Piping4/HVAC4/Electrical4/MEP1).
One provider-selected tool, one host request, one existing Revit ExternalEvent;
host-controlled partition/fan-out to snapshot-fed specialty A01 cores; no recursive
execute_headless_modelmind_readonly, nested event, UI-selection mutation or
autonomous multi-tool loop. Existing technical details and validation evidence below
remain applicable; old uncommitted/push-pending wording and planned commit steps
describe the historical pre-commit checkpoint only and are superseded here.

This reconciliation is documentation-only and itself awaits review/commit/push.
No runtime/test change, authenticated OpenAI request or Revit live test performed.
Next: review reconciliation, then pending live validation; no duplicate
implementation commit or amendment. Evidence/Daily Log/KC IDs and hours unchanged.

## Historical pre-commit implementation checkpoint - 2026-09-23

IMPLEMENTED. STATIC VALIDATION PASSED. LIVE VALIDATION PENDING. NOT CLOSED.
Implementation changes are local, unstaged and uncommitted. No live Revit tests
or authenticated OpenAI requests were executed for this implementation task.
Project-local end-of-day WBSO implementation checkpoint is now prepared in the
provider registry, architecture/scope/evidence notes and test/validation records.
DISCOVERY COMPLETE / IMPLEMENTATION COMPLETE / STATIC VALIDATION PASSED /
LIVE VALIDATION PENDING / IMPLEMENTATION CHECKPOINT NOT YET COMMITTED / PUSHED /
NOT CLOSED. WBSO documentation also remains uncommitted/unpushed.
Evidence ID / Daily Log ID / KC ID / hours: PENDING; none allocated.
The original implementation task did not update WBSO; this documentation-only
follow-up records its results without rerunning the runtime tests.

Approved design: [M3F_DISCOVERY.md](M3F_DISCOVERY.md).
Implementation-start main HEAD = origin/main =
`ae06fc6e5fc4cede99279b9921d2826f94a5fc75`, subject
`docs(bimcode): record M3F orchestration discovery`, parent/M3E closure
`c281b0c85d9254072db390843b8c107713a606b1`. Starting worktree clean, 0/0.
Those are historical checkpoints, not a requirement that future HEAD stay fixed.
At this WBSO-task start the same main HEAD/origin remain aligned, 0/0, but the
worktree is dirty: prior implementation scope 16 files, +871/-13, comprising
13 modified tracked paths and three untracked paths; no staged files.
The discovery document's IMPLEMENTATION NOT STARTED wording is historical to
its discovery checkpoint; this implementation section supersedes that status.

## Scope and fixed contract

Exactly one addition to the unchanged twelve Piping/HVAC/Electrical AI mappings:

`summarize_selected_mep_elements` -> `MEP-MULTI-RO-001-A01`

Feature: `MEP-MULTI-RO-001`. Total AI tools: 13, all read-only.
Strict empty-object schema, no additional properties. No caller-supplied action,
specialty, element/document/category list, command, path, URL or execution option.
Mixed Summary only: no composite connectors, assignment, QA or remediation.
Clear single-specialty prompts retain the existing tools. General questions do
not require a tool. No autonomous orchestration or retry was introduced.

Supported scope uses the closed predicates: rigid Pipe, rigid non-placeholder
Duct, DEVICE_PROFILE Lighting/Electrical Fixtures and EQUIPMENT_PROFILE
Electrical Equipment. Conduit, cable tray, wires, standalone circuits, linked
instances and other unsupported categories remain unsupported. No scope widening.

## Execution and snapshot seam

One provider-selected tool -> one host request token -> the existing M2
ExternalEvent -> `modelmind_composite.execute` -> one nonblocking headless lock
and one document context -> one selection evaluation snapshot -> fixed host
partition -> at most three synchronous A01 core calls -> scalar projection ->
the existing provider continuation.

Order is always PIPING, HVAC, ELECTRICAL; only present groups are evaluated.
Selection references are sorted by the existing ID helper. Resolved elements
are partitioned with closed scope predicates and existing generic records;
unsupported/unresolved references stay separate. API objects stay inside the
event callback. A final selection-ID integrity reread is not another evaluation
snapshot and is never used to assemble child data. Selection is never written.

The three `_..._ro_001_build_data(self, prompt, action_key)` methods retain their
existing snapshot capture and delegate to new
`_..._ro_001_build_from_snapshot(self, prompt, action_key, snapshot)` cores.
Each core body is exactly the original body following snapshot capture. This
preserves all existing A01-A04 wrapper behavior, caps, warnings and domain rules.
The composite calls only fixed A01 metadata/core pairs with explicit subsets.
It does not call the public headless executor recursively or nest ExternalEvents.
The existing non-reentrant lock and document-global cleanup remain intact.

Request identity, document identity, lifecycle generation and selection generation
are checked before execution and between children/before publication. Stale state
discards all computed facts. An integrity mismatch also fails closed. Lock/global
cleanup happens on success and failure. No timers, polling or background API work.

## Result policy and scalar envelope

| Condition | Composite classification / reason |
| --- | --- |
| Empty | MEP_MULTI_SELECTION_NOT_READY / NO_ELEMENTS_SELECTED |
| Unsupported only | MEP_MULTI_SELECTION_NOT_READY / NO_SUPPORTED_SELECTED_ELEMENTS |
| Any unresolved reference | MEP_MULTI_SELECTION_NOT_READY / SELECTION_UNREADABLE; no child evaluation |
| Invalid document | MEP_MULTI_SELECTION_NOT_READY / NO_VALID_DOCUMENT_CONTEXT |
| More than 600 selected references | MEP_MULTI_SELECTION_NOT_READY / SELECTION_LIMIT_EXCEEDED |
| All applicable usable children complete, no unsupported scope | MEP_MULTI_SELECTION_SUMMARY_OK / COMPLETE |
| Usable child plus failed/not-ready/partial child or unsupported scope | MEP_MULTI_SELECTION_SUMMARY_PARTIAL |
| No usable child result | MEP_MULTI_SELECTION_FAILED / NO_USABLE_SPECIALTY_RESULT |
| Stale, busy, execution/projection failure | MEP_MULTI_SELECTION_FAILED with explicit reason; no fabricated success |

Partial primary-reason precedence: SUBACTION_FAILED, SUBACTION_NOT_READY,
SUBACTION_PARTIAL, UNSUPPORTED_ELEMENTS_PRESENT. All applicable reasons retained.
No separate UNSUPPORTED classification: this follows the approved discovery.
Display/transport truncation alone does not make the semantic result PARTIAL.
Child failure does not erase successful siblings; no retry. A child not started
after the advisory time budget is FAILED/TIME_BUDGET_EXCEEDED, evaluated=false.

Envelope includes feature/action/specialty, request ID, local timestamp,
document/view/type, selected/resolved/supported/unsupported/unresolved counts,
supported-specialty count, classification/reason/reasons, partial, warnings,
timings and explicit transport omissions. Unavailable counts are null, not zero.
Top-level warnings are reserved for composite warnings; child warnings/totals
remain within each child and are not misleadingly summed as unique issues.

Fixed specialty objects retain presence, selected/supported counts, action,
classification/reason, execution state, evaluated flag, bounded child result,
warnings/totals and omissions. Absent children are NOT_PRESENT; known supported
children blocked by unresolved scope are NOT_EVALUATED. Only attempted A01 calls
appear in sub_actions. Child action plus the fixed specialty slot identifies each
child independently of any same-second report ID. Child facts are copied, not
recomputed, joined into cross-specialty systems, or interpreted as composite QA.

Unsupported/unresolved sections contain exact counts, bounded safe ID/category
samples where available, and sample omissions. Provider continuation validates
fixed feature/classification/specialty slots, A01 identities and evaluated list;
the result is data, never an execution plan.

## Bounds and performance evidence

- Admission: 600 selected references, checked before generic record building.
- Existing per-specialty processing caps: 200, unchanged and child-owned.
- Up to three distinct A01 attempts; no retry.
- Optional tables: 12 tables / 40 rows across the composite, allocated fairly
  among present children in fixed order. Original ordering and scalar values stay.
- Each child projection: <=20,000 JSON characters; total <=80,000, measured after
  ASCII escaping. Existing sidecar request limit remains 120,000 characters.
- Optional rows/tables removed whole with exact omission metadata. Oversized
  core facts fail closed; no silent scalar clipping. Final envelope checked too.
- Warnings/warning records: first 30 of each per child, original totals retained
  with separate omitted counts. Unsupported/unresolved samples: first 30 each.
- Advisory two-second elapsed checkpoint before each child. It does not interrupt
  a running child or guarantee a hard UI latency bound. Live practicality pending.
- Snapshot/partition elapsed time uses reference count. Child timings explicitly
  name submitted_references, not completed elements; child caps/read states remain
  authoritative. Composition reports child-result slots; total reports supported
  references. No global per-element denominator or measured Revit speed claim.

## Provider and provenance

Initial store=True; continuation uses previous_response_id, call_id and
function_call_output; final store=False, tools=[], tool_choice="none". Existing
unknown/malformed/non-empty/multiple/second-tool rejection remains enforced.
No local conversation database or additional provider tool turn.

Pane provenance shows Selected MEP Elements Summary, composite action,
classification/reason, only evaluated sub-actions, fixed-order child status and
transport-omission notice. Existing single-specialty provenance is unchanged.
M2 lifecycle/ExternalEvent architecture, M3A configuration/sidecar foundation,
Workbench domain rules, catalog and dependency manifests remain unchanged except
for the specifically reviewed three-wrapper/core extraction in Workbench.

## Static validation

- 288 offline Python tests PASS (existing 261 baseline plus 27 M3F tests).
- 66 native process/tool probes PASS: 10 process/dispatcher, 4 M3B, 48 existing
  twelve-tool, 4 composite. No real provider child or authenticated request.
- Seven Revit-side IronPython compiles PASS. Native XAML/WPF/theme/Find PASS.
- 33 Python files: sanitized in-memory AST/compile and tabnanny PASS.
- 1,472 existing Workbench functions source-identical; three wrappers changed
  only for extraction; three new core bodies source-identical to original bodies.
  Reconstructed AST matches all 1,475 original functions; current total 1,478.
- Snapshot partition combinations, profiles, unresolved/unsupported policy,
  reference conservation, failures, stale guards, lock cleanup, one-event gate,
  deadline, admission/transport/Unicode/warning limits and continuation tested.
- Exact original twelve mappings preserved; only composite A01 added. Mutation,
  nested-execution, network-boundary and allowlist checks PASS.
- Catalog remains 237, unchanged. Manifests unchanged. pip check PASS.
- Credential-pattern scan of 47 scoped non-env source/docs/tests: no findings;
  not an exhaustive secret proof. No Authorization-header logging introduced.
  .env.local ignored/untracked; its contents were not read.
- git diff --check PASS. No staging, commit, push or live tests. These totals
  describe the implementation validation, not a new WBSO-task test run.

Static stubs/source checks cannot establish Revit runtime parity or live latency.

## Historical implementation-checkpoint live plan - then all PENDING

For cases 01-10 use: **Summarize the selected MEP elements.**
Record document/view/IDs, counts, exact classifications/reasons, child facts,
warnings/omissions, elapsed time, provenance, one event and at most three distinct
A01 attempts. Verify no model/view/selection change in every case. Compare each
child against direct closed A01 on that specialty subset, selected manually for
fixture setup, then restore the mixed selection. Runtime must never alter it.

| Case | Fixture / request | Required evidence | State |
| --- | --- | --- | --- |
| LIVE-M3F-01 | Pipe only | Piping A01 parity, one child | PENDING |
| LIVE-M3F-02 | Rigid non-placeholder Duct only | HVAC A01 parity, one child | PENDING |
| LIVE-M3F-03 | Supported Lighting/Electrical Fixture | DEVICE_PROFILE A01 parity | PENDING |
| LIVE-M3F-04 | Electrical Equipment | EQUIPMENT_PROFILE A01 parity | PENDING |
| LIVE-M3F-05 | Pipe + Duct | Two correct subsets and child provenances | PENDING |
| LIVE-M3F-06 | Pipe + supported Electrical | Two correct subsets and child provenances | PENDING |
| LIVE-M3F-07 | Duct + supported Electrical | Two correct subsets and child provenances | PENDING |
| LIVE-M3F-08 | Pipe + Duct + supported Electrical | Three A01s, exact child parity | PENDING |
| LIVE-M3F-09 | Supported + unsupported, e.g. Conduit | Explicit PARTIAL and unsupported counts; supported results retained | PENDING |
| LIVE-M3F-10 | Conduit/other unsupported only | NOT_READY, no children; no false Electrical support | PENDING |
| LIVE-M3F-11 | What is the purpose of MEP coordination? | General answer, no tool or provenance | PENDING |
| LIVE-M3F-12 | Change the selected pipe diameter | No mutation/tool capable of mutation; no model change | PENDING |

Supplementary pending checks: empty selection, practical large-selection/admission
and transport bounds, timing-budget practicality. Use synthetic tests for unsafe
unresolved/stale/failure states rather than corrupting a model. No live PASS claim
or M3F closure decision is made by this implementation checkpoint.

Next session: implementation checkpoint audit; authorize/commit/push implementation;
authorize/commit/push the separate project-local WBSO checkpoint; perform the twelve
pending live cases; assess final closure. None of those source-control/live actions
was executed by this end-of-day documentation task.
