# BIMCODE-REVIT-AI-PANE-001 M3B implementation checkpoint

2026-09-18 final audit: M3B_READY_FOR_CLOSURE_WITH_NONBLOCKING_GAPS.
STATIC PASS; required LIVE matrix COVERED / PASS (user-reported).
Not closed, staged, committed or pushed. No authenticated request made by this task.
M1/M2/M3A remain closed. Clean starting main HEAD/origin:
361b8e5cc24e4766afdc2f3d0d1208f6bbef2aa1 (M3A closure), ahead/behind 0/0,
subject feat(bimcode): add OpenAI sidecar connectivity.
No hours, Evidence, Daily Log, KC or prompt-asset IDs allocated.

## One approved capability

The only AI tool is summarize_selected_pipes, internally mapped to the literal
PIPING-RO-001-A01. No model/user action-ID argument, expression, path, document
identity or element-ID argument exists. The Responses tool schema is:

```json
{
  "type": "function",
  "name": "summarize_selected_pipes",
  "description": "Return the deterministic read-only ModelMind summary for currently selected supported rigid Revit pipes.",
  "strict": true,
  "parameters": {
    "type": "object",
    "properties": {},
    "required": [],
    "additionalProperties": false
  }
}
```

Model decides whether to call it (tool_choice auto, parallel_tool_calls false).
General text questions can return directly. Prompt instructs the model not to
use Piping for duct/electrical requests or invent unavailable capabilities.
No HVAC/Electrical/connectors/assignment/QA/export/mutation tool is exposed.
Natural-language routing is model-selected, not a deterministic intent guarantee;
the host independently restricts execution to this one read-only action.

## Verified Responses continuation and storage change

Installed official SDK 3.15.0 was inspected: FunctionToolParam;
ResponseFunctionToolCall (type, name, arguments JSON string, call_id);
FunctionCallOutput (type function_call_output, call_id, output string);
ResponseCreateParams (previous_response_id, tools, tool_choice, store).
Official guide: https://developers.openai.com/api/docs/guides/function-calling

Initial agent_turn uses store=True for official response-ID continuation.
This is an explicit change from M3A store=False: OpenAI retains the initial
response under its applicable storage policy (installed SDK documents at least
30 days, subject to data-retention exceptions). Even a direct answer in agent_turn
uses this setting, since tool use is not known until the response arrives.
There is no conversation resource or local response persistence. The input tooltip
discloses initial-turn storage and transfer of bounded selected-pipe data to OpenAI.
The host keeps only response_id and configured model, plus call_id/name/empty args,
in memory for this turn. No raw SDK response or hidden reasoning is transported.

Follow-up tool_result sends previous_response_id with one function_call_output,
JSON-encoded deterministic data, repeated fixed instructions, tools=[],
tool_choice=none, store=False and background=False. A changed configured model
between legs is rejected. No retries automatically execute the action again.
Any function call on the second response (or multiple calls on the first) fails
AI_TOOL_LOOP_LIMIT. Unknown output/tool types and nonempty arguments fail closed.
SDK/request transport failure ends the turn; the user may deliberately retry.
The SDK stays outside IronPython in fixed repo .venv/Scripts/python.exe.
requirements_sidecar.txt / Python 3.10.11 / openai 3.15.0 remain unchanged.

## Process protocol

Existing readiness and text_response contracts remain supported, including
M3A store=False text execution. The bound pane now sends agent_turn.
Version 1 gains exact-key agent_turn and tool_result operations; no generic dispatch.
Intermediate success adds state=TOOL_REQUEST, validated tool_call and provider_state.
Direct/follow-up success uses state=FINAL. Failures retain ok=False and fixed error
code/message (the existing backward-compatible FAILED representation).
Host correlation, schema/name/argument/identifier checks apply before queueing.
Request ID remains one turn's correlation token; only the active phase can advance.

Input: 2000 user characters; agent/continuation envelope <=120000 serialized
characters; tool_result <=80000 ASCII-JSON characters; IDs <=256 characters;
configured model <=128 characters. Existing M3A text request limit remains 20000.
Provider text <=12000 characters; host response envelope <=100000 characters;
existing 16000-character / 400-block presentation remains unchanged.
As in M3A, host stream size is checked after collection, not incremental streaming.
There is one fixed trusted child per API leg, no daemon, arbitrary executable or shell.
API key remains child-owned and is never added to protocol/arguments/logs.
Only provider.py accesses the fixed OpenAI endpoint; no other network path added.

## Revit execution and stale safety

The coordinator captures cached scalar document identity, lifecycle generation,
selection-event generation and turn ID at Send. No API objects are queued.
Only ModelMindReadOnlyHandler.Execute invokes Coordinator.execute_approved.
It reuses the already registered M2 ExternalEvent; no new event or subscriptions.
WPF/provider callbacks only queue. Background workers only exchange scalar JSON.
Immediately before execution, document identity and both generations are checked.
Switch-away/back, reopen, view transitions and selection changes (even same count)
invalidate the request. Target: existing Revit 2025.4 SelectionChanged support.
STALE_CONTEXT is rendered deterministically without a tool call or second API leg.

One coordinator turn and one execution token; pending consumed before executing.
M2 busy state prevents beginning AI; AI busy state temporarily disables M2 buttons.
After completion/failure, normal M2 button behavior resumes unchanged. No polling,
timers or background Revit reads. Existing M1 registration/show/refresh remains.

The existing closed scope resolver is a guard against silently executing Piping
on HVAC/Electrical-only selections. It never routes AI to those specialties.
Empty, unsupported-only, supported-plus-unsupported and mixed selections with
Piping go unchanged to the closed Piping builder, which owns their semantics.
No elements are filtered and no Piping/QA/domain rule is recreated.
The facade call is exactly execute_headless_modelmind_readonly(ACTION, doc, uidoc).
Its structured result is authoritative; prose is explanatory, not a QA decision.
Pure supported-Pipe results match direct M2 execution; M2's generic mixed-selection
routing rejection remains unchanged and is intentionally not copied into A01.

## Deterministic transport projection

Reuse project_value to reject raw/CLR objects and non-finite values. Retain:
action_id, specialty, classification, reason_code, summary,
selected_reference_count, resolved_selected_count, piping_checks, generic_checks,
warnings, warning_records, warnings_total, warning_display_truncated and tables.
Omit document/view names, timestamps, canonical prompts, report metadata and
next_guidance. No scalar facts are rewritten or recalculated.

Checks/warning lists: first 30 per field. Tables: at most 12 with 40 total rows,
whole cells/headers retained. Explicit transport_omissions records omitted rows
and entries. If still over 80000 serialized characters, omit optional whole fields
in order: tables, warning_records, warnings, piping_checks, generic_checks.
Summary and core identity/classification/reason fields are never clipped; if
they alone exceed the bound, fail instead of inventing a partial fact.
Prompt requires disclosure of omissions and treats tool content as data, not
instructions. Model narrative accuracy remains a live-validation requirement.

Final pane provenance is constructed from host data, never model text:
Selected Pipes Summary, PIPING-RO-001-A01, exact classification and reason.
No raw tool JSON displayed by default. Find/theme/renderer are reused.
Provenance remains visible if the second API call fails after a successful read.
No provenance on direct text answers. Send stays gated across both API legs.

## Errors and validation

New fixed codes: AI_TOOL_NOT_ALLOWED, AI_TOOL_ARGUMENTS_INVALID,
AI_TOOL_PROTOCOL_ERROR, AI_TOOL_LOOP_LIMIT, MODELMIND_NOT_READY,
MODELMIND_EXECUTION_FAILED, STALE_CONTEXT. M3A error mappings remain.
Host execution failures use design B: render safe deterministic failure directly,
without another API request. Production NOT_READY/PARTIAL classifications in a
successfully built result are retained and may be explained by the provider.

Offline validation: 208 Python tests PASS (166 prior + 42 M3B); original 10 native
process/dispatcher probes plus 4 native M3B probes PASS. AST/py_compile/tabnanny:
27 files PASS; native IronPython compile: 5 host files PASS. Native XAML/WPF,
theme/Find, pip check, mutation/network/secret-pattern/allowlist and diff checks PASS.
1475 existing Workbench function bodies source-identical. Catalog 237 unchanged.
M2 tools.py and headless facade byte-equivalent to baseline after line-ending
normalization. Existing 166 Python tests were not edited. Real .env.local not read.
No live authenticated request made; mocks/fake child only.

## Original user-run live procedure (completed; retained for reproduction)

Restart Revit/pyRevit with the updated code; confirm local readiness.

1. Select one supported rigid Pipe. Send: Summarize the selected pipe.
   Expect Thinking -> Reading selected pipes -> Thinking -> final AI response;
   exactly one PIPING-RO-001-A01, PIPING_SELECTION_SUMMARY_OK and host provenance.
   Compare counts, units, type/system/diameter/length against direct Summary for
   the same unchanged selection. Send restores; no model/view/selection mutation.
2. After PASS, ask: What is the purpose of a hydronic supply system?
   Expect direct text, no ModelMind execution and no tool provenance.
3. After PASS, select a Duct and ask: Summarize the selected duct.
   Expected normal response: only selected-pipe summary is connected; no action.
   If the model erroneously calls Piping, host rejects it without executing a
   builder; record this as a routing observation, not a passed normal-text case.

Supplemental boundary checks: change selection/document while first API request
is pending; expect STALE_CONTEXT if a tool is requested, with no execution. Check
empty/multiple/mixed selections against closed A01 behavior; normal deterministic
Summary/Connectors/Assignment/QA Health after completion; Find/theme; provider
failure recovery. Do not deliberately invalidate real credentials or burn quota.
Future tool expansion requires a separate reviewed package after closure.
No AutoCAD/DrawingMind implementation, autonomy, mutation or catalog route added.

## Final closure audit and supplied live evidence (2026-09-18)

All three required cases are COVERED / PASS, based on the user's live observations,
not newly executed Revit/API requests during this audit.

- LIVE-M3B-01: one supported rigid Pipe; configured gpt-6-astra returned COMPLETE,
  host provenance Selected Pipes Summary / PIPING-RO-001-A01 /
  PIPING_SELECTION_SUMMARY_OK / COMPLETE. Reported facts matched the user's
  prior deterministic A01 result for the same selection.
- LIVE-M3B-02: hydronic supply explanation was a direct OpenAI response, with no
  action ID, tool provenance or ModelMind execution. Tool use is not forced.
- LIVE-M3B-03: selected-Duct request produced a capability explanation, not a tool
  call, in both Project2 and Snowdon Towers Sample HVAC. No HVAC action, pipe-tool
  misuse, ModelMind execution or provenance was observed.

LIVE-01 parity evidence:

| Field | Supplied observed value / assessment |
| --- | --- |
| Count / ID | One supported Pipe, 353871; no skipped, unsupported or unresolved references |
| Type / segment | Default / Carbon Steel - Schedule 40 |
| System | Hydronic Supply 5 / ASSIGNED |
| Diameter | 150.0 mm |
| Length | 23000.0 mm / 75.459 ft; conversion independently checks at displayed precision |
| Slope | 0 |
| Start / end elevation | 2276.6 mm / 2276.6 mm |
| Reference level | Level 1 |
| Insulation / workset | 0.0 mm / Workset1 [0] |
| Pinned / grouped / assembly | No / No / No |
| Reads / omissions / warnings | No partial reads, omitted rows or warnings |
| Classification / reason | PIPING_SELECTION_SUMMARY_OK / COMPLETE |

The source's closed A01 record table supplies these domain fields; the AI bridge
does not calculate their values. Count/processing facts remain in the unchanged
summary/table content; there is no newly invented processed-count calculation.
Narrative wording need not match direct UI formatting. No saved raw live payload
was supplied for independent byte comparison; model values above are user-reported.

Final offline rerun confirmed all totals above: 208 Python tests, 14 native probes,
27 Python static checks and 5 IronPython compiles PASS; WPF/theme/Find, pip check,
allowlist, mutation/network, credential-pattern and whitespace checks PASS.
All 1475 Workbench functions source-identical, catalog237 unchanged. M2 tools.py,
headless facade, M3A config loader and dependency manifests unchanged. Lifecycle
has the previously reviewed coordinator/selection-generation additions; it is
not byte-identical to M3A, but existing registration/show/refresh behavior and
M2 execution/routing/stale handling regressions pass. No new runtime edit here.

Current defects: NONE FOUND. No additional live test is required for this bounded
one-tool closure. Forced stale races and invalid/multiple/second-tool coercion are
sufficiently covered by mocks/native checks. Paid auth/quota/timeout injection is
nonblocking; do not burn credit or revoke keys. Optional gaps: additional sequential
tool turns, long explanation, document switching during a round-trip, reload,
theme changes and already-open multi-document tabs. These are not claimed PASS.

Source-control closure remains PENDING. Audit-start delta matched the reported
16 files / 1047 insertions / 15 deletions. No post-live file snapshot was supplied,
so matching totals alone do not establish post-live byte identity. This audit
changes documentation only, with runtime/tests verified unchanged during the audit.
Recommend one reviewed implementation+tests+docs commit:
feat(bimcode): add first ModelMind AI tool bridge. No staging/commit/push performed.
IDs/hours remain PENDING, none allocated. M3C NOT STARTED. Additional Piping tools,
then HVAC/Electrical, are possible future packages only after M3B closure; none
are exposed/pre-wired through AI now. AutoCAD/DrawingMind remains future-only.
