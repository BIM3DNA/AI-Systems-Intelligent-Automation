# BIMCode AI pane M3F - mixed-specialty Summary

## Current checkpoint - 2026-09-23

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

## Live validation matrix - all PENDING, not executed

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
