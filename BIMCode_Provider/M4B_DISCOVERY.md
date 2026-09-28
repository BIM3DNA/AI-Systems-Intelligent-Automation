# M4B-DISC-001 - Provider-facing controlled write discovery

Date: 2026-09-28. Package: BIMCODE-REVIT-AI-PANE-001.
Status: DISCOVERY COMPLETE; READY FOR IMPLEMENTATION DESIGN ONLY.
No provider write registration, runtime/test change, live execution or WBSO update.
All M4B behavior below is proposed unless explicitly described as current source.
No new live PASS, Evidence/Daily Log/KC identifier or hours allocated.

## 1. Verified closed baseline

Discovery-start branch: main. HEAD = origin/main =
84bb732df8c391a909f17c33d28ed25f47a1bd41.
Subject: docs(wbso): mark M4A host-only write closed.
Parent: d4561fc3670b2dd13d70de5a3c5ec6d9eb784a5e.
Ahead/behind: 0/0. Worktree clean; status --short, staged, modified and
non-ignored untracked lists empty before creating this document.

Git history, not inferred subjects, establishes these checkpoints:

| Checkpoint | Full SHA |
| --- | --- |
| Discovery | 4db623b120b7fa19ce9a80bfa32fc682e089225c |
| Implementation design | dc14eaea00e92f75837ef98abbf012c007d3ab47 |
| Preview foundation | 83a87ee5c58782dffb86a5add8936273c4bff647 |
| Preview harness / invocation selection snapshot | 74d14b80931d4f218a2adb04b2889de65dc268d6 |
| Host-write implementation | 60b1818ef00bac7a058c751f24e2d4afaf857666 |
| Final validation documentation | d4561fc3670b2dd13d70de5a3c5ec6d9eb784a5e |
| Host-only closure reconciliation | 84bb732df8c391a909f17c33d28ed25f47a1bd41 |

EOD documentation remains 1f592632c8c14bf79f32e35002bbf43200347a4a.
M4A host-only layer is SOURCE-CONTROL CLOSED, with recorded nonblocking gaps.
Provider-facing writes remain NOT IMPLEMENTED / NOT STARTED / NOT CLOSED.
13 read-only provider tools; catalog 237. This document does not reopen M4A.

## 2. Current provider architecture: source inventory

Paths in this inventory are relative to repository root. Line references describe
the baseline above; function names are the durable navigation anchors.

| Boundary | Exact current source / symbol |
| --- | --- |
| Pane Send | AI.extension/lib/bimcode_ai_pane/panel.py:66 `_on_send`, :73 `_start_provider` |
| Scalar request identity / admission | provider_bridge.py:45 `request`, :175 `SendState`; `begin` creates UUID, keeps active request |
| Worker / WPF return | provider_ui.py `launch`: System.Threading.Thread runs scalar bridge; Dispatcher.BeginInvoke delivers completion |
| Serialization / process | provider_bridge.py:123 `run`: JSON stdin, fixed .venv/Scripts/python.exe, `-I -B -X utf8`, fixed BIMCode_Provider/sidecar.py, no shell |
| Sidecar entry | BIMCode_Provider/sidecar.py `main`, `dispatch`; protocol.py `parse`; fixed one-shot child |
| Provider schema | BIMCode_Provider/provider.py `TOOLS`, `TOOL_INSTRUCTION` |
| Python 3 mapping / validation | BIMCode_Provider/tool_protocol.py `ACTIONS`, `validate_call`, `validate_request`, `validate_composite` |
| Host mapping | AI.extension/lib/bimcode_ai_pane/ai_tool_registry.py `TOOLS`, `ACTIONS`, `LABELS`, `SPECIALTIES` |
| Initial Responses call | BIMCode_Provider/provider.py:124 `send` |
| Call extraction | provider.py:73 `tool_response` |
| Host response validation | provider_bridge.py:58 `decode`, :97 `decode_tool` |
| Pane tool dispatch | panel.py:92 `_provider_complete`; ai_tool.py:64 `Coordinator`, :86 `queue` |
| Read-only ExternalEvent | lifecycle.py:47 `ModelMindReadOnlyHandler.Execute`; :172 `PaneSession.raise_ai_event` |
| Deterministic execution | ai_tool.py:119 `execute_approved`; modelmind_headless.execute_headless_modelmind_readonly; composite branch modelmind_composite.execute |
| Projection | ai_tool.py:19 `compact` with project_value; composite has its own bounded payload |
| Host completion | ai_tool.py:108 `complete`; panel.py:129 `_ai_tool_complete` |
| Continuation | panel.py `_ai_tool_complete` builds operation=tool_result; provider.send submits function_call_output |
| Provenance | panel.py `_ai_provenance`; provider_ui.py `presentation`; result_presentation._Budget and existing rich renderer |

The three provider layers are distinct: model tool selection, Python 3 protocol
validation, and independent IronPython host authorization. Tool arguments never
select action IDs. Existing read-only tools all require exactly an empty object.
Mappings: four Piping names -> PIPING-RO-001-A01..A04; four Duct names ->
HVAC-RO-001-A01..A04; four Electrical names -> ELECTRICAL-RO-001-A01..A04;
summarize_selected_mep_elements -> MEP-MULTI-RO-001-A01. Exact names remain in
ai_tool_registry.TOOLS, mirrored in tool_protocol.ACTIONS.

Verified sequence:

1. SendState.begin and Coordinator.begin capture request ID, cached document key,
   context generation and selection generation; deterministic buttons become busy.
2. A worker starts a one-shot sidecar; protocol.parse rejects duplicate envelope
   keys, invalid request IDs, excess size and unexpected fields.
3. provider.send agent_turn uses store=True, background=False,
   parallel_tool_calls=False, tools=TOOLS, tool_choice=auto.
4. tool_response returns either final text or one bounded TOOL_REQUEST envelope.
   Sidecar/process exits before Revit tool work. It does not wait for Revit.
5. Dispatcher returns to pane; Coordinator.queue consumes the turn's used flag,
   fixes the action from its own allowlist, and raises the existing read-only event.
6. Execute rechecks document/lifecycle/selection, then calls deterministic code.
   No worker invokes Revit. Complete calls the pane's callback.
7. _ai_tool_complete creates tool_result with original response_id, call_id and
   request_id. A NEW one-shot sidecar performs the continuation HTTP request.
8. provider.send uses previous_response_id and one function_call_output containing
   JSON deterministic data; store=False, tools=[], tool_choice=none. Tool calls in
   this response are rejected. The pane renders host-sourced provenance plus text.

This is one logical user request, normally TWO HTTP requests, not one long HTTP
request. Current SDK timeout is 45 seconds, max_retries=0; process wait is 75 seconds
per sidecar run. Human confirmation time is outside those HTTP/process intervals.
There is no current host-tool completion timeout or persistence/recovery journal.

## 3. Current one-tool controls and reuse limits

| Control | Enforcement / proposed disposition |
| --- | --- |
| One provider call | provider.tool_response rejects len(calls)!=1 and any call during tool_result; keep |
| No parallel/recursive loop | parallel_tool_calls=False plus host used flag and pane _ai_waiting; keep all, not just prompt guidance |
| Unknown tool | tool_response, tool_protocol.validate_call, provider_bridge.decode_tool and host ACTIONS; add separate fixed write allowlist only |
| Malformed output | unexpected output item kinds, async_/namespace/non-direct caller, non-completed call status rejected; keep |
| Arguments | Python 3 and host demand dict=={} today; write needs a separate exact {value:string} validator, never relax read-only validation |
| Argument JSON | provider.tool_response currently json.loads(raw), raw length <=100; duplicate argument keys can collapse here. Write path must reject duplicates at initial parse, not only outer protocol.parse |
| Identity | protocol.parse validates 32 lowercase hex request ID; decode checks matching request_id, bounded call_id/response_id/model; Coordinator.queue matches active turn; preserve and bind call ID/value locally |
| Stale context | Coordinator.begin/execute_approved; lifecycle invalidates on view/open/create/close, increments selection generation; add write model epoch and exact snapshot/preconditions |
| Busy | SendState.active, Coordinator.turn, session.tools.pending and write_busy; use owner-aware admission, not unconditional bypass |
| Continuation | validate_request action/specialty checks and model equality; write needs its own typed result schema, not read-only compact/specialty coercion |

The 100-character raw argument limit is not a canonical value limit: JSON escaping
can exceed it for a valid 64-character scalar. Propose a separate bounded write
argument envelope (1024 characters), decoded exact-key/type/full-value validation;
leave the read-only cap unchanged. Reject NaN, duplicate keys, null/array/bool values.

## 4. Closed host-only write: exact inventory and contracts

Entry: AI.extension/AI.tab/Dev.panel/M4AWrite.pushbutton/script.py calls
write_coordinator.get_coordinator(session).invoke(HOST_APP.uiapp, forms, output).
It is not called by the provider. `get_coordinator` requires retained SelectionChanged,
ViewActivated, DocumentClosed/Opened/Created subscriptions; creates one session
WriteCoordinator/event and DocumentChanged subscription, or reuses it.

| Stage | Exact current implementation |
| --- | --- |
| Value validation | bimcode_ai_pane/write_contracts.py:22 validate_value; string, anchored \A...\Z, strip equality; no coercion/normalization |
| Snapshot | bimcode_write_runtime.py:28 capture_preview_context; active document/view and sorted IDs, deterministic SHA-256 |
| Target | :51 resolve_target; fixed host rigid Pipe, explicit supplied snapshot |
| Binding / GUID | :82 verify_binding; :93 resolve_parameter; SharedParameterElement.Lookup and get_Parameter(guid), no name lookup fallback |
| Preview | :112 _preview, :160 build_preview; invalid scalar stops before target resolution; no-change is NOT_READY |
| Human interaction | write_coordinator.py:80 invoke, :21 confirm; preview printed, native Cancel-default TaskDialog with target/GUID/before/after/request |
| Epochs | WriteCoordinator.epochs; context_generation, selection_generation, all-document DocumentChanged epoch (including Undo/Redo) |
| Approval | bimcode_write_execution.py:16 freeze; immutable namedtuple Request(preview_json, epochs, created, confirmed) |
| Queue / admission | WriteCoordinator.pending/running/resolving, session.write_busy; active AI turn rejected today |
| Event | WriteHandler.Execute -> WriteCoordinator.execute consumes pending before API work |
| Executor | bimcode_write_execution.Executor.execute/revalidate; used-ID replay set capped at 1000; retained transaction ownership |
| Mutation | executor :121 DB.Transaction; :132 Parameter.Set; one Commit; fixed transaction name |
| Verification | Executor.verify GUID reread and exact proposed equality; no false success on mismatch |
| Failure / Pending | Executor.settle; check_pending on explicit repeated HUMAN Dev command; no second Start/Set/Commit |
| Presentation | write_coordinator.display -> escaped JSON in Dev output; no current pane completion callback |

Fixed feature MEP-PARAM-WR-001; action MEP-PARAM-WR-001-A01;
BIMCode_M4A_TestText; GUID 2f3c955d-45ee-4258-bc61-08acd40a2912;
INSTANCE String/Text; OST_PipeCurves; transaction `BIMCode M4A Set Test Text`.
Exactly one non-placeholder, unpinned host Pipe, no group/assembly/design option;
non-family/non-workshared/writable/non-modifiable document. Parameter must be shared,
fixed GUID and expected name, Pipes-only instance binding, String and Text, writable.
Current before value must be null or <=256 characters without Unicode control
categories. Proposed value is 1..64 ASCII-contract characters and not unchanged.

Actual order: human invocation -> stamp/epochs/snapshot -> value dialog -> validate/
preview -> print preview -> stale/age check -> native confirmation -> recheck ->
freeze -> event Raise -> execution revalidation -> one transaction/Set/Commit ->
exact reread. Snapshot API objects do not enter provider serialization or queued
approval; approval contains scalar JSON only. Executor may retain API objects only
while it owns unresolved transaction state, accessed solely in valid API callbacks.

Preview classifications: MEP_PARAMETER_WRITE_PREVIEW_OK / NOT_READY / FAILED.
Execution classifications: MEP_PARAMETER_WRITE_OK / CANCELLED / NOT_READY /
FAILED / INDETERMINATE. Exact prefixes apply to each suffix.
Reasons include COMPLETE, INVALID_VALUE, NO_CHANGE_REQUIRED, NO_ELEMENTS_SELECTED,
MULTIPLE_ELEMENTS_SELECTED, UNSUPPORTED_TARGET, UNSUPPORTED_DOCUMENT, NO_VALID_DOCUMENT,
PARAMETER_MISSING, PARAMETER_IDENTITY_MISMATCH, INVALID_BINDING, STORAGE_TYPE_UNSUPPORTED,
DATA_TYPE_UNSUPPORTED, TARGET_NOT_WRITABLE, CURRENT_VALUE_UNSAFE, READ_FAILED,
USER_CANCELLED, STALE_CONTEXT, CONFIRMATION_EXPIRED, CONFIRMATION_INVALID,
CONFIRMATION_FAILED, EXECUTION_BUSY, EXTERNAL_EVENT_NOT_ACCEPTED, TARGET_MISSING,
TARGET_CHANGED, PRECONDITION_CHANGED, TRANSACTION_START_FAILED, PARAMETER_SET_FAILED,
TRANSACTION_COMMIT_FAILED, TRANSACTION_PENDING, TRANSACTION_STATUS_UNKNOWN,
ROLLBACK_UNCONFIRMED, VERIFICATION_FAILED and INTERNAL_ERROR.

Current `result_for` starts confirmation_result=NOT_CONFIRMED; executor changes it
to CONFIRMED. Cancel is represented by classification/reason, not a literal CANCELLED
confirmation field. Do not silently reinterpret these fields in provider projection.
Post-confirm/pre-executor rejections also need a separate host-owned confirmation
observation if the UI is to report consent accurately; this is an integration design
gap, not authority to rewrite closed results. Similarly target_category exists in
preview but not result_for: carry it from the bound preview, not model inference.

## 5. Problem and options

Provider may propose only set_selected_pipe_test_text({value:...}). It cannot select
IDs, GUID, parameter, action, transaction options, consent, retries or success.

| Option | Assessment |
| --- | --- |
| A: one logical request through preview/TaskDialog/write/result | RECOMMENDED with asynchronous host coordinator. Best reuse of existing two-HTTP-turn exchange, native consent and one final result. Cannot block UI waiting for event. Requires owner-aware admission and completion sink. |
| B: preview response then later host button | Strong separation, but approval across turns needs immutable host state, expiry/replay rules and result-to-conversation linkage. Execution need not call AI again, but explaining it later needs a separate explicit turn; more UI/persistence complexity. Defer. |
| C: immediate TaskDialog and async pane completion | Useful scheduling mechanics for A, not a second semantic result. If preview is sent as function_call_output before execution, later success cannot replace it safely. Keep provider continuation pending until one terminal host disposition. |
| D: plan then manual Dev command | Safe interim fallback, no mutation tool; duplicated input and not genuine integration. Existing M4A remains available. |
| E: provider confirms/executes | REJECT. Natural-language intent is not confirmation of an exact deterministic preview; model cannot issue human consent. |

## 6. Recommended coordinator and API-context sequence

Choose A with C-style asynchronous completion, ONE logical request and ONE tool total.
No read+write pair or child tool chain. Existing infrastructure supports callbacks,
but is NOT safe for writes unchanged: invoke rejects session.ai.turn; output is Dev
only; arguments/result validators are read-only; UI labels success by provider.ok.

Proposed phases:

IDLE -> PROVIDER_PENDING -> HOST_PREVIEW_QUEUED -> PREVIEW_READY -> AWAITING_HUMAN
-> WRITE_QUEUED -> EXECUTING -> HOST_RESULT -> FINAL_EXPLANATION -> DONE.
Rejected/cancelled/expired paths go to HOST_RESULT without write queuing.
INDETERMINATE returns one honest host result but retains write ownership separately.

1. Pane accepts one request; captures cached lifecycle/selection/document counters
   and already-installed model epoch plus enablement generation. Reserve owner ID.
2. After one validated call, consume one-tool token even if rejected. Strictly bind
   request_id/call_id/value and fixed action in host memory. Reject mismatched owner.
3. Dedicated provider-write PREPARATION ExternalEvent reads context/builds preview
   and displays native TaskDialog in valid API context. Do not put write behavior in
   ModelMindReadOnlyHandler or invoke Revit from Dispatcher/network thread.
4. Before showing dialog render a bounded host preview card; do not wait for layout
   completion to authorize anything. TaskDialog itself contains authoritative values.
   If live WPF painting requires another dispatcher turn, use explicit PREVIEW_READY
   callback then schedule confirmation API phase with a fresh stale check, not DoEvents.
5. On explicit Confirm, recheck preview and epochs, freeze approval, enqueue exactly
   one existing dedicated write ExternalEvent. Return from preparation callback;
   no synchronous Wait/Join, nested event Execute call, or recursive read-only bridge.
6. Shared write owner calls existing executor. Completion sink returns scalar result
   to pane; Dispatcher schedules presentation/network only after API work unwinds.
7. Retain deterministic result first, then launch one tools-disabled continuation.
   No further tool use, even after failure, cancel or expiry.

Two API scheduling phases (preparation and the one mutation event) are not two
provider tools or two writes. Register event/coordinator and model epoch once in a
valid startup/enablement API context, before provider latency starts; not lazily from
WPF. Share session.m4a_write/executor with Dev path, never create a second executor
that bypasses retained Pending locks. Existing Dev invoke semantics remain default.
Owner-aware adapter admits only the same reserved AI turn, while rejecting every
other AI/Dev/M2 request. Any extraction requires protected M4A regression tests.

Pane-local ai_tool.complete/_ai_tool_complete callback pattern is reusable; write
coordinator has no callback today and needs one. No polling, Idling subscription,
timer or background Revit API access required. Event Raise Accepted means scheduled,
not executed. Pending/denied Raise must not trigger repeated mutation submissions.

UI may keep request pending without blocking the dispatcher. Revit modal TaskDialog
naturally requires user response; final provider continuation begins only afterward.
No current arbitrary UI timeout should clear an accepted write and allow replacement.
Provide explicit host cancel-before-execution that invalidates queued owner/token;
late event must consume inertly. After execution starts, cancellation must not claim
rollback. On close/disposal, invalidate unexecuted requests; committed result remains
true even if pane delivery fails. No replay on restart/reopen; lose consent on restart.

Pending/unknown transaction: deliver INDETERMINATE with nullable model_modified and
exact flags, retain global mutation lock. Human-only status query in API context may
settle status without new write; no automatic polling or second provider output for
the same call. Later human status evidence can be displayed locally, not rewritten
as earlier success. Host result must survive provider timeout in session memory;
durable crash recovery is explicitly not claimed by initial scope.

## 7. Fixed schema and action identity

Tool name: set_selected_pipe_test_text. Function wrapper type=function, strict=true.
Parameters (only argument):

```json
{
  "type": "object",
  "properties": {
    "value": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9 _-]{0,63}$"
    }
  },
  "required": ["value"],
  "additionalProperties": false
}
```

Use fixed mapping to MEP-PARAM-WR-001-A01, feature MEP-PARAM-WR-001. Preserve same
domain identity across preview/confirmation/execution; add host-owned origin=AI_PANE,
safety_class=CONTROLLED_WRITE and phase metadata outside closed result. Distinct
orchestration package M4B does not require another domain action/catalog route.
A second action ID would complicate parity without a new semantic action. No caller
action argument and no addition to the read-only headless action allowlist.

Schema validation alone is insufficient. Validate exact keys/types and duplicate
keys in sidecar AND host; use full \A...\Z/strip/length/control validation, not loose
JSON-schema `$` semantics. Repeat host target/GUID/binding/writability/no-change and
stale checks. Human consent and transaction verification remain independent gates.
Unsupported schema/model configuration must fail closed, never silently downgrade
strictness. Actual configured model/schema acceptance remains future validation;
no credential/model config was read during discovery.

## 8. Confirmation and expiry

Only human clicking native Confirm for this exact preview grants consent. Request
text, provider text, earlier consent, confirmation=true, reused token or changed
value cannot authorize execution. TaskDialog remains Cancel-default and host-owned;
preview card is explanatory, not an approval control. No token reaches provider.

Record monotonic timestamps: request_received, tool_selected, preview_created,
preview_shown, dialog_opened, human_confirmed, event_queued, event_executed.
Record UTC timestamps for audit display only; use monotonic time for validity.

Propose separately configurable-in-code fixed bounds, NOT tool parameters:
- Request-to-preview admission: 120 seconds; stale counters independently reject.
- Preview/context lease: 120 seconds from preview creation, checked after dialog;
  never silently refresh target/value. Expired preview requires a NEW human request.
- Confirmed approval queue lease: 30 seconds from explicit Confirm, checked inside
  executor before any transaction; no retry on expiration.
These are proposed initial bounds, not measured performance claims.

Current executor uses now-request.created >60 and rejects now<confirmed; invoke
starts created BEFORE proposed-value input. Merely changing pane timestamps is not
enough. Implementation design must explicitly add versioned expiry policy/fields at
freeze/execute, preserve legacy Dev default or separately authorize its change,
and test both. Never spoof created=confirmed while mislabelling original creation.
No renewal/reconfirmation loop inside one request. WRITE-07A two expiry PASS cases
remain historical M4A evidence, not proof of WRITE-07 model-change/change-back.

## 9. Deterministic projection and failure semantics

Use a dedicated bounded write projector, not ai_tool.compact (read-only field set
and specialty rules). Core fields cannot be truncated; overflow fails transport,
never removes mutation/verification evidence. Proposed <=80000-character envelope
reuses transport ceiling; include explicit warning omissions if ever needed.

Preserve feature_id, action_id, request_id, classification, reason_code,
target_category, target_element_id (host-selected result only), parameter_display_name,
parameter_guid, before_value and before_has_value, proposed_value, final_value,
confirmation_result, transaction_started, transaction_committed, transaction_status,
model_modified (including null), verification_performed, verification_passed, warnings.
Use null for unknown values; never confuse null with empty string/unset. Supplement
host-owned phase, origin, confirmation_observed and timestamp fields separately.
For preview rejection, map current_value to before_value by an explicit documented
projection while preserving original preview classification; do not invent WRITE_OK.
No need to transmit document path, UniqueId, snapshot/epochs or approval token.

| Host outcome | Provider/pane meaning |
| --- | --- |
| Cancel | WRITE_CANCELLED / USER_CANCELLED; no transaction. Report no change only when flags establish it. |
| Preview not ready | Preserve PREVIEW_NOT_READY and exact reason; no TaskDialog/event execution. |
| Expired | WRITE_NOT_READY / CONFIRMATION_EXPIRED; no retry, fresh human request required. |
| Stale | WRITE_NOT_READY / STALE_CONTEXT or exact precondition reason; no automatic rebuilding/retry. |
| Failed | Preserve exact transaction/rollback facts, including committed=true on verification failure. Never claim universal rollback. |
| Indeterminate | State uncertainty explicitly; lock retained. No successful final value inferred. |
| Success | WRITE_OK / COMPLETE only with committed=true and verification_passed=true; exact before/final values. |

## 10. Continuation and presentation

Keep current store=True initial -> previous_response_id/call_id/function_call_output
-> store=False/tools=[]/tool_choice=none final. Send host cancellation/rejection as
deterministic data, not a bridge error that bypasses explanation. Protocol errors
before a valid call remain local failures. Exactly one function output per call.
Do not use OpenAI async function calls, programmatic tools, background mode or agents
to solve local scheduling. Current tool_response intentionally rejects such callers.

45-second SDK / 75-second process bounds still apply to each HTTP phase, not human
wait. Expired/deleted response IDs or continuation timeout yield explanation failure;
show saved host result and never rerun mutation. No indefinite HTTP retention promise.
M4B must distinguish provider explanation success from write success: current
provider_ui.presentation uses result.ok -> COMPLETE, which is insufficient for writes.

Before consent, display Tool requested: Set Selected Pipe Test Text; fixed action;
CONTROLLED WRITE; Confirmation REQUIRED; No model change yet; exact before/proposed.
Afterward show host classification/reason, consent observation, transaction status,
verification, before/final independently of provider text. FAILED/INDETERMINATE and
unverified commit never receive green write COMPLETE. Render values as text, not
HTML/commands. Preserve existing theme, Find, character/block bounds and read-only UI.

## 11. Registry, enablement and document scope

Separate READ_ONLY_TOOL_REGISTRY and CONTROLLED_WRITE_TOOL_REGISTRY with different
schemas, dispatchers, safety labels, enablement and admission rules. Preserve all
13 existing entries/descriptions/contracts. Union has 14 only when write test mode
and the host document gate are enabled. Never advertise disabled writes to provider.

Recommend host-local pyRevit user configuration section `bimcode_ai_pane`, explicit
boolean `controlled_write_test_mode`, default false. Missing/malformed/non-bool values
fail closed. This is a proposal, not an existing setting. Pair it with an explicit
human session-only opt-in for the active disposable project via host UI; no persisted
document permit. Reset per-document opt-in on close/reopen/switch and session restart.
Visible `Controlled writes enabled (test project)` indicator; disable revokes unqueued
approval and invalidates queued authority before execution, never hides committed facts.

API key/model readiness is not permission. Do not use .env.local or an environment
variable for write permission. Sidecar receives only host-generated capability for
schema advertisement in a strictly validated envelope; provider arguments cannot set
it. Host rechecks its own live permit/enablement generation at preview and execution.
A forged sidecar capability is never sufficient. No config file is edited here.

Runtime can prove non-workshared/non-family/writable/non-modifiable host document,
one eligible rigid Pipe, no links/groups/assemblies/design options/pinned/placeholder,
and provisioned exact GUID. It cannot prove that a document is disposable. Require
explicit human test-model attestation, bind permit to session document identity and
show title in confirmation; do not infer safety from filename. Fail closed when
required lifecycle/model epoch subscriptions are unavailable. No automatic provisioning.

## 12. Routing, disambiguation and injection boundaries

Proposed description: Propose ONE controlled write of BIMCode_M4A_TestText on ONE
selected eligible rigid host Pipe. Supply only the exact user-requested scalar value.
Host preview and separate explicit human confirmation are mandatory; this call does
not itself grant consent. Not for other parameters, categories, geometry or batches.

Positive intents: `Set the selected pipe test text to M4A_AI_01.`,
`Change the selected pipe test text to Demo_01.`,
`Write Review_Ready to the selected pipe test field.`
Ambiguous value/target/field: ask clarification, no tool. Never invent a value.
Negative intents: move 500 mm, diameter, system assignment, Mark, Comments, Duct,
multiple Pipes, script execution, fix model. General shared-parameter questions use
no tool. Pipe summary/QA/connectors/system and mixed MEP summary retain their exact
read-only tools. No preliminary read tool before a write; one tool TOTAL.

Strict schema constrains structure, NOT semantic intent or prompt injection. An LLM
can select the wrong allowed tool; static tests cannot guarantee natural-language
routing. Native explicit consent and fixed executor remain safety barriers. In
implementation design, consider a separate human write-mode affordance; do not claim
regex keyword filtering perfectly proves user intent. Tests must include erroneous
provider selection for read-only/general prompts and require no unconfirmed write.

Threats and controls:
- Hidden action/ElementId/GUID/parameter/confirm/options fields: reject extra keys
  in both protocols; dispatcher identity is literal host mapping.
- Numeric-looking ID inside value: valid literal text can be accepted, never parsed
  as a target. Likewise code-like alphanumeric text is inert; no eval/exec/parser.
- Code punctuation/control/Unicode payloads: scalar validation rejects; escape display.
- Ignore-confirmation prompts or model output posing as consent: never enter confirm
  branch without native click and matching unexpired host state.
- Tool-output instruction requesting another write: data only, tools disabled and
  host token consumed. No provider retry even on error.
- Arrays/multiple values/batch IDs: schema/type/key checks; target count exactly one.
- Forged/replayed call/late completion: request/call/owner/generation binding and
  single-use executor; consume on rejected attempt, no new action behind same turn.
- Model/selection ABA during provider wait or dialog: epoch/generation and immutable
  snapshot; no silent recapture that targets a new Pipe.
- Provider explanation claims success incorrectly: host result remains primary;
  model text cannot change badges/transaction state or trigger any API call.

## 13. Static validation plan (future; not executed)

A. Registry parity: source-identical 13 entries; disabled 13, enabled eligible 14;
malformed/missing config, revoked permit and unsupported document hide/reject write.
B. Schema: one valid value, bounds/full match/trailing newline/whitespace; duplicate
JSON keys, extra identity/confirmation fields, null/arrays/non-string rejected;
escaped valid values bounded correctly. Host and sidecar parity.
C. Routing fixtures: exact tool-name/action/safety mapping; positive/negative prompt
instruction fixtures, mocked wrong-tool output; live/eval testing still needed for LLM.
D. Consent: no preview -> no dialog; no click -> no approval; cancel; confirmation
error; changed preview; separate leases; clock reversal; selection/document/model ABA.
E. One-tool: multiple calls, read+write, two writes, late duplicate, second continuation
call, recursive coordinator entry, wrong request/call ID, owner collision, no retry.
F. Projection: all classification families and null flags, unset vs empty, committed
verification failure, Pending/rollback unknown, cancellation, warning/size bounds;
provider timeout after commit never loses host result or triggers retry.
G. Regression: all current read-only suites, M3F, M4A preview/provisioning/Dev write,
fixed GUID/transaction/Set counts, callback thread boundary, source/AST protected
functions, catalog237, config/dependency isolation, native WPF/theme/Find, IronPython,
syntax/tabnanny/whitespace and bounded credential-pattern scan excluding secrets.
H. Lifecycle: register once, no duplicate subscriptions, initialized epoch before Send,
modal/dispatcher shutdown, pending ownership retained, human status check no mutation,
accepted event executes late after cancel/expiry and cannot write.

Existing baseline suites: tests/test_bimcode_write_contracts.py, write_runtime.py,
write_execution.py, write_coordinator.py, write_preview_harness.py (each with
test_bimcode_ prefix), test_bimcode_write_native.ps1, test_bimcode_provider.py,
test_bimcode_ai_tool.py and specialty AI tool suites. Proposed new tests:
tests/test_bimcode_provider_write.py, test_bimcode_provider_write_coordinator.py,
test_bimcode_provider_write_native.ps1. Counts are not claimed before implementation.

## 14. Future live matrix - all PENDING, do not execute in discovery

| Case | Required observation |
| --- | --- |
| LIVE-M4B-01 | Default disabled: 13 tools, mutation prompt cannot execute |
| LIVE-M4B-02 | Explicit host enablement/attestation in disposable project; indicator, 14-tool eligible configuration |
| LIVE-M4B-03 | Natural-language fixed write -> correct tool/value, deterministic preview/native dialog; no transaction before consent |
| LIVE-M4B-04 | Cancel -> CANCELLED/USER_CANCELLED, no transaction; provider parity |
| LIVE-M4B-05 | Confirm -> one transaction/Set, exact GUID reread; WRITE_OK only when verified |
| LIVE-M4B-06 | One native Undo restores previous value; no compensating transaction |
| LIVE-M4B-07 | Same value -> NO_CHANGE_REQUIRED, no dialog/write |
| LIVE-M4B-08 | Empty selection -> fail closed |
| LIVE-M4B-09 | Multiple selection -> fail closed |
| LIVE-M4B-10 | Duct -> unsupported, no write |
| LIVE-M4B-11 | Invalid scalar -> reject unchanged, no normalization/write |
| LIVE-M4B-12 | Unsupported mutation prompts -> no write tool execution |
| LIVE-M4B-13 | General question -> no tool |
| LIVE-M4B-14 | Pipe read-only summary parity |
| LIVE-M4B-15 | M3F mixed-summary parity, no mutation |
| LIVE-M4B-16 | Controlled injected second provider call -> loop rejection, no second execution; offline evidence if live injection impractical |
| LIVE-M4B-17 | Expiry -> no transaction; exercise preview and confirmed queue leases separately |
| LIVE-M4B-18 | Provider displayed facts match direct host result for same before/value fixture |

Supplemental required safety exercises: selection/model/document change and change-
back during wait; revoked enablement; provider continuation failure after successful
write; pane close before event; duplicate click. Pending/rollback/verification fault
injection offline if not safe live; mark unobserved coverage explicitly, never PASS.
Use provisioned disposable non-workshared model; record exact IDs/values/flags/times,
native transaction/Undo evidence and deterministic result independently of prose.

## 15. R&D uncertainty, non-goals and implementation prerequisites

Uncertainty: connect one provider-selected intent to a deterministic host pipeline
without making model output authority for consent, target, transaction or success.
Investigate ownership across two event phases and two HTTP calls, separate expiry
leases, immutable correlation, UI loss after mutation, Pending ownership, bounded
provenance and incorrect tool selection. Options/rejections above are design evidence,
not validated implementation. Planned evidence: static state-machine probes, protocol
adversarial cases, native event/UI probes, timed live matrix and direct-host parity.
Evidence/Daily Log/KC IDs and hours remain PENDING; WBSO files untouched.

Likely future files (proposal, not changes in this task):
- BIMCode_Provider/provider.py, tool_protocol.py, protocol.py: gated schemas,
  instructions, exact write arguments and typed continuation validation.
- AI.extension/lib/bimcode_ai_pane/provider_bridge.py, ai_tool.py: independent
  validators, one-token safety-class dispatch, owner/request binding.
- New bimcode_ai_pane/provider_write.py: pure state/permit/projection coordination.
- bimcode_ai_pane/write_coordinator.py: owner-aware scalar entry and result sink,
  shared event/executor/lock; preserve existing Dev invocation.
- bimcode_write_execution.py: narrowly reviewed versioned timing contract only if
  required; no new mutation locations or weakened preconditions.
- bimcode_ai_pane/lifecycle.py: API-context creation and permit/model epoch lifetime;
  preserve read-only handler execution behavior.
- panel.py, provider_ui.py, BIMCodeAIPane.xaml: enablement/preview and authoritative
  write provenance distinct from provider text status.
- Proposed tests listed above; existing M4A tests extended, never removed to hide
  regression. ai_tool_registry.py should keep 13 entries unchanged; separate write
  registry/module rather than adding mutation to read-only ACTIONS.

Keep Workbench script.py, modelmind_headless/composite, closed specialty evaluators,
prompt_catalog.json, dependencies, .env.local, existing provider credential loader,
M4ASetup/Preview commands and WBSO unchanged unless later explicitly authorized.

Before implementation: approve detailed state/ownership diagram and exact callback
contract; decide registration lifetime and config UX; approve explicit versioned
expiry change; define cancel/late callback/retained transaction terminal states;
freeze typed projection; protect all 13 tools; validate supported model/schema with
authorized future testing; then implement behind default-off gate. Discovery-ready
is not implementation authorization or live validation approval.

Non-goals: arbitrary parameters/IDs/commands/code; batch/multiple targets; geometry,
move/rotate/rehost/delete/create; connectors/systems/circuits; tags/views/sheets;
autonomous remediation; read+write or multi-write plans; AutoCAD. No sidecar Revit API,
background Revit access, provider confirmation or provider-accessible generic dispatcher.

## 16. External references and verification boundary

Official OpenAI documentation reviewed for schema/continuation design, not to infer
repository behavior: [Function calling](https://developers.openai.com/api/docs/guides/function-calling)
documents strict objects, function output correlation, no-tools and parallel-call
controls. [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
documents model-dependent schema support, including fine-tuned string-keyword
limitations. Fail closed if the configured model rejects the exact schema; no
authenticated model/schema test was performed. These sources do not grant mutation
authority or prove routing accuracy.

[Autodesk ExternalEvent.Raise](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/13bf4411-c400-dcd2-458c-7f09357d9ecb.htm)
describes queued execution when Revit is ready, not synchronous completion. Local
code establishes the existing event pattern; new two-phase scheduling must still be
validated on the project's actual Revit version. No Revit run was performed here.

Discovery deliverable: only BIMCode_Provider/M4B_DISCOVERY.md. No PROJECT_STATE or
WBSO update, runtime/test/config change, secret read, staging, commit or push.
