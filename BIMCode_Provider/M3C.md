# M3C - full Piping read-only AI toolset

## 2026-09-21 final closure audit

M3C_READY_FOR_FINAL_CLOSURE_COMMIT. IMPLEMENTED / STATIC VALIDATION PASSED /
LIVE VALIDATION PASSED / IMPLEMENTATION CHECKPOINT COMMITTED AND PUSHED /
PROJECT-LOCAL WBSO CHECKPOINT COMMITTED AND PUSHED / SOURCE-CONTROL RECONCILIATION
VERIFIED / READY FOR FINAL CLOSURE COMMIT / NOT YET SOURCE-CONTROL CLOSED.
M1/M2/M3A/M3B remain source-control closed. No M3D or scope expansion.
This section supersedes the historical pending-live checkpoint and plan below.

Implementation `1364a0d691bb89db6169af205dd34a1757ce32bc`; WBSO checkpoint
`f346ebb39b69d87b454d8abf45a362e3dfa99c26`; reconciliation/current HEAD
`dafb63ecd1613fcf8c698a9b84df09245c476b0d`, parent the WBSO checkpoint.
Actual reconciliation subject: `project WBSO update...`. The proposed subject
`docs(wbso): reconcile M3C checkpoint source control` has no matching commit in
available history. Verified reconciliation scope: eight docs, +119/-0; main and
origin/live remote synchronized, 0/0, clean at audit start. Only documentation
changed since implementation; runtime/tests are identical in Git and clean locally.

Required live matrix supplied by the user in the 2026-09-21 audit request:

| Case | Observed result | Deterministic parity / boundary |
| --- | --- | --- |
| LIVE-M3C-01 | Pipe353871; inspect_selected_pipe_connectors -> A02; PIPING_CONNECTOR_REPORT_OK / COMPLETE | PASS; two raw/physical End Round connectors, diameter150mm, zero reciprocal connections, two unconnected, zero unreadable; no warnings/truncation/transport omissions |
| LIVE-M3C-02 | Same Pipe; inspect_selected_pipe_system_assignment -> A03; PIPING_SYSTEM_ASSIGNMENT_OK / COMPLETE | PASS; ASSIGNED, Hydronic Supply5, system353873, type132471, CONSISTENT, no contradictions/warnings |
| LIVE-M3C-03 | Same Pipe; inspect_selected_pipe_qa_health -> A04; PIPING_QA_HEALTH_YELLOW / COMPLETE | PASS; 12 Piping checks, three issues (one SEL-QA-011 + two PIPING-QA-008), zero partial checks, no warnings/read failures/transport omissions |
| LIVE-M3C-04 | Pipe slope question answered directly | PASS; no tool/provenance, ModelMind action, model inspection or mutation |
| LIVE-M3C-05 | Duct-only connector request declined with correct capability explanation | PASS; no Piping/HVAC tool, ModelMind execution or provenance |

All five PASS; A02/A03/A04 routing, factual parity and read-only behavior PASS;
A04 issue accounting PASS. Full facts, including connector origins/directions and
NOT_APPLICABLE checks, are in WBSO/Technical_Notes/evidence_reference.md.
Live evidence is user-reported; no new authenticated request or Revit test by this audit.
No package-introduced runtime defect found. Optional larger/ambiguous/Electrical-only
or forced race/error live variations remain unclaimed; they do not change the supplied
five-case required matrix or static boundary coverage.

Final static rerun PASS: 232 Python tests (208 retained +24 M3C), 30 native probes
(14 retained +16 M3C), 6 IronPython compiles, 27 AST/in-memory compile/tabnanny files,
native XAML/WPF/theme/Find, 1475 source-identical Workbench functions, catalog237,
mutation/network/allowlist/credential-pattern checks, pip check and diff check.
No count differences. Requirements/configuration, M2 execution and M3A foundation
remain unchanged. .env.local ignored/untracked and not read; no credential-pattern
hits in 110 tracked files and no Authorization-header logging in provider paths.

Exactly four strict empty-argument Piping tools remain. Static name/action mapping,
one execution per request, multiple/second/unknown/nonempty-call rejection, existing
ExternalEvent ownership and stale document/lifecycle/selection/request guards PASS.
Initial store=True; continuation previous_response_id + call_id + function_call_output,
store=False, tools=[], tool_choice=none preserved. No autonomous loop, HVAC/Electrical/
mutation tool or AutoCAD. No runtime/test/catalog/manifest edits during this audit.
Evidence/Daily Log/KC IDs and hours PENDING, no allocations. Final docs await review,
commit and push; proposed subject `docs(wbso): close M3C live validation`.

## 2026-09-19 WBSO source-control reconciliation

The implementation checkpoint `1364a0d691bb89db6169af205dd34a1757ce32bc`
and project-local WBSO checkpoint `f346ebb39b69d87b454d8abf45a362e3dfa99c26`
are both committed and pushed. The WBSO commit subject is
`docs(wbso): record M3C implementation checkpoint`; its parent is the implementation
checkpoint. Verified main/HEAD/origin/live remote alignment, 0/0 and clean before
this documentation-only reconciliation. They are checkpoint anchors, not closure.
M3C remains IMPLEMENTED / STATIC VALIDATION PASSED / LIVE VALIDATION PENDING /
NOT CLOSED. LIVE-M3C-01..05 remain NOT STARTED/PENDING. IDs and hours remain PENDING.
The next section is retained as the accurate pre-WBSO-commit checkpoint record.

## 2026-09-19 source-control and WBSO checkpoint reconciliation

Implementation/static checkpoint is committed and pushed as
1364a0d691bb89db6169af205dd34a1757ce32bc (parent M3B closure
4be024fe1ad21a7e314bf6778ce185474f6de055; subject Update): exactly 12 files,
605 insertions, 37 deletions. main HEAD/origin/main/live remote match, 0/0;
worktree was clean before this documentation-only update. The earlier baseline
and no-commit statements below describe the implementation task, not current Git.
This separate project-local WBSO documentation checkpoint awaits review/commit/push.

M3C IMPLEMENTED / STATIC VALIDATION PASSED / LIVE VALIDATION PENDING / NOT CLOSED.
No live test has started; no live A02/A03/A04 or deterministic-button parity PASS.
M1/M2/M3A/M3B remain source-control closed. M3D has not started.
2026-09-19 static rerun confirms the totals below: 232 Python tests, 30 native
probes, 6 IronPython compiles, 27 AST/compile/tabnanny checks, WPF/theme/Find,
1475 unchanged Workbench functions, catalog237, protected manifests/config,
boundary/allowlist/credential-pattern checks, pip check and diff check PASS.
No runtime/test changes, paid calls, secret reads, IDs/hours or staging/commit/push.
Required live plan below remains PENDING. Project-local evidence is recorded in
WBSO/Technical_Notes/evidence_reference.md and WBSO/Testing_Validation/test_plan.md.

## Historical implementation task checkpoint

2026-09-18 implementation checkpoint. IMPLEMENTED / STATIC PASS / LIVE PENDING.
M3C is not closed. No authenticated request or Revit live test was run by this task.
No staging, commit, push, Evidence/Daily Log/KC IDs or hours allocated.

## Verified baseline

M3B SOURCE-CONTROL CLOSED at 4be024fe1ad21a7e314bf6778ce185474f6de055,
parent 361b8e5cc24e4766afdc2f3d0d1208f6bbef2aa1, subject
`feat(bimcode): add first ModelMind AI tool bridge`.
Starting main HEAD = origin/main, ahead/behind 0/0, clean; no staged, modified
or non-ignored untracked paths. M1/M2/M3A remain source-control closed.
Earlier pre-commit M3B audit notes are historical, not a claim of open M3B closure.

## Fixed registry and schemas

| Function name | Literal action | Host provenance label | Description report phrase |
| --- | --- | --- | --- |
| summarize_selected_pipes | PIPING-RO-001-A01 | Selected Pipes Summary | summary |
| inspect_selected_pipe_connectors | PIPING-RO-001-A02 | Selected Pipe Connectors | connector report |
| inspect_selected_pipe_system_assignment | PIPING-RO-001-A03 | Selected Pipe System Assignment | system-assignment report |
| inspect_selected_pipe_qa_health | PIPING-RO-001-A04 | Selected Pipe QA Health | QA-health report |

Every definition has type `function`, strict `true`, the exact name above, and:

```json
{"type":"object","properties":{},"required":[],"additionalProperties":false}
```

Each description is exactly `Return the deterministic read-only {report phrase}
for currently selected supported rigid Revit pipes.` (one line).
The fixed sidecar protocol mapping is mirrored in the IronPython host registry;
tests require exact equality. Neither imports/exposes the generic ModelMind
catalog. No dynamic discovery, action-ID construction, script/path/URL/ElementId
arguments or arbitrary dispatch. Unknown names and nonempty/non-object arguments
fail closed at both boundaries. No HVAC, Electrical, mutation or AutoCAD tool.

## Execution and protocol

Initial Responses request declares all four tools, `tool_choice=auto`,
`parallel_tool_calls=False`. Model selection only, no keyword router. Direct
answers stay available; ambiguous intent should elicit clarification, not a sweep.
Instructions preserve deterministic classifications, counts, units, reason codes
and omissions; YELLOW/partial cannot be presented as GREEN/PASS. Final prose is
model-generated, so factual parity still requires the user-run live checks below.

The v1 envelope and fixed error taxonomy are unchanged. Name validation now uses
the four-name allowlist; continuation result action must equal that name's mapped
action. Existing request/model/call-ID checks remain. A host-only scalar action is
captured after validation and consumed by the existing coordinator. No queued API
objects or model-selected action IDs. Exactly one execution token per user prompt.
Multiple initial function calls or a tool request in the final continuation fail
with AI_TOOL_LOOP_LIMIT; follow-up uses tools=[], tool_choice=none. No recursion.

The lifecycle, panel state machine, ExternalEvent handler and headless facade are
unchanged. The coordinator calls execute_headless_modelmind_readonly(mapped_action,
document, uidocument) only from the existing ExternalEvent.Execute. Existing cached
document identity, lifecycle generation, selection generation and request identity
guards reject stale work. No API access from WPF callbacks, workers or sidecar.
Duct/Electrical-only supported selections are blocked. Empty, unsupported and
mixed selections containing Piping retain the closed builder's semantics; the host
does not silently filter the selection. Existing four deterministic buttons remain.

## Projection and bounded evidence

No builders, raw API record handling or domain calculations added. The existing
headless facade returns already-authored production summary/table/check content:

- A01: summary plus type/segment/assignment/diameter/slope/workset distributions
  and rigid-pipe records including level, geometry and assignment fields.
- A02: summary totals plus per-pipe connector summary and physical connector
  details (raw versus reciprocal state, unconnected/unreadable, dimensions/owners).
- A03: assignment/name/type/classification distributions and normalized system
  metadata records, consistency, sources and contradictions; unassigned/inconsistent
  IDs remain in the production summary.
- A04: deterministic summary issue/partial counts and exact piping/generic check
  dictionaries with applicability, issues/passed/skipped, affected IDs and omissions.

Transport uses a shared envelope but does not flatten/reinterpret these structures.
Classification, reason, selected/resolved counts, complete summary and production
guidance are copied; available warning/connector truncation metadata is retained.
No raw Element/Document/SDK objects leave the host. project_value still validates
exact scalars/containers before serialization.

Limits remain 80,000 serialized result characters, 120,000 request characters,
12 tables, 40 total table rows and 30 entries per warnings/warning_records/check
list. The production Piping QA lists fit the retained list cap; omitted entries
are still explicitly counted. Summary check/issue counts are not recalculated.
A02's multiple wide connector rows and A04's check dictionaries can exceed A01's
payload size depending on selection; bounds therefore remain enforced, not raised.

M3C divides the existing 40-row budget across remaining tables, avoiding an early
per-pipe summary/distribution consuming every connector/assignment-detail row.
Within each table headers, values and row order are preserved. transport_omissions
reports aggregate omitted table rows and per-table index/title/omitted-row counts.
If optional table content still exceeds the serialized bound, the entire tables
field is omitted with explicit counts. Core summary/warnings/check fields are no
longer dropped as a size fallback; oversized core evidence fails closed instead.
This changes transport coverage only, never production caps or semantic findings.
User-visible provenance always identifies actual action, classification and reason,
including continuation failure. Direct answers have no tool provenance. No raw JSON
is added to the main answer. Tooltip/footer now describe all four Piping reports.

## Storage, network and security

M3B storage behavior is inherited unchanged: initial tool-capable turn uses
store=True for response-ID continuation, even when it gives a direct answer;
final continuation uses store=False. No local conversation database, conversation
resource or multi-turn memory. Bounded selected-pipe facts are sent to OpenAI only
through the existing Python provider. No new network path or paid call by tests.
M3A config, canonical requirements_sidecar.txt and all manifests remain unchanged.
Fixed endpoint, isolated fixed child executable, no shell, no custom proxy/base URL,
bounded errors and sidecar-only credentials remain. .env.local is ignored/untracked;
no real secret contents inspected. No Revit model/view/selection/linked mutation.

## Static validation

- 232 Python tests: 208 retained baseline tests + 24 M3C tests, PASS. Two baseline
  assertions adapted only for the authorized plural tool list and relocated literal
  registry; no tests removed. New tests exercise four model-selected responses,
  exact schemas/maps, unknown/malformed requests, correlation and every stale guard,
  each action's parity/projection, Duct/Electrical rejection, simultaneous/second
  calls, result/action mismatch, bounds/omissions, sequential pane turns and labels.
- 30 native IronPython probes: original 10 process/dispatcher + 4 M3B + 16 M3C
  (four tools x envelope/execution/provenance/loop gate), PASS.
- Six native host-file compiles; native WPF/XAML/theme/Find PASS.
- AST/in-memory compile/tabnanny PASS; no generated bytecode required.
- All 1,475 existing Workbench function sources unchanged; runtime script,
  headless facade, M2 tools/lifecycle/panel, M3A config/manifests unchanged.
- Prompt catalog unchanged, 237 entries. Mutation/network boundary and diff checks PASS.

Commands: `.venv/Scripts/python.exe -B -m unittest discover -s tests -p 'test_*.py'`;
`powershell -NoProfile -ExecutionPolicy Bypass -File tests/test_bimcode_provider_native.ps1`;
same command for `tests/test_bimcode_result_find_wpf.ps1`; `git diff --check`.
Mocked selection tests do not prove actual model intent selection; no live PASS claimed.

## User-run live validation (PENDING)

Reload/restart the development extension in Revit as needed. Use a disposable
project and supported rigid Pipe. Keep document, view and selection unchanged
between the AI request and corresponding deterministic pane button comparison.
For every tool check label/action/classification/reason, authoritative facts and
units, warnings, omissions and no mutation. Record any prose/fact disagreement.

| Case | Prompt / setup | Expected and comparison |
| --- | --- | --- |
| LIVE-M3C-01 | Select Pipe; "Show me the connectors for the selected pipe." | A02 / Selected Pipe Connectors; complete fixture PIPING_CONNECTOR_REPORT_OK; compare Connectors button counts, raw/reciprocal state and records. Preserve PARTIAL if fixture warrants it. |
| LIVE-M3C-02 | Same Pipe; "What system is the selected pipe assigned to?" | A03 / Selected Pipe System Assignment; complete fixture PIPING_SYSTEM_ASSIGNMENT_OK; compare Assignment button state/name/type/consistency. |
| LIVE-M3C-03 | Pipe; "Check the QA health of the selected pipe." | A04 / Selected Pipe QA Health; compare QA Health button classification, issues, checks, partial count and warnings; never turn YELLOW/PARTIAL into healthy. |
| LIVE-M3C-04 | "What does pipe slope mean in Revit?" | Direct answer, no tool/provenance/execution. |
| LIVE-M3C-05 | Select only Duct; "Check the connectors for the selected duct." | Capability explanation; no Piping or HVAC execution. Host must reject any incompatible model-requested tool. |

Also regress Summary A01, Electrical-only refusal, an ambiguous "Check these selected
pipes" prompt (clarification or one justified tool, never a sweep), and a larger
Pipe selection with explicit omissions. Optional stale-context race must produce
controlled failure, not silent retargeting. No automated paid requests.
Next: review delta, run live cases and supply observations. Do not close M3C yet.
