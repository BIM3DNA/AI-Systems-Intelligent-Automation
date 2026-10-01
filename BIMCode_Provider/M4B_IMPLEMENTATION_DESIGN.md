# M4B implementation design: asynchronous controlled provider write

Date: 2026-10-01. Status: DESIGN READY; NOT IMPLEMENTED; LIVE VALIDATION PENDING.
Package: BIMCODE-REVIT-AI-PANE-001 / M4B.
This document is a design artifact, not authorization to implement, register a tool,
execute a write, run authenticated tests, or close M4B.

## 1. Verified baseline and discovery reconciliation

The pre-edit worktree was clean, with no staged, modified, or untracked files.
Branch `main`; HEAD, `origin/main`, and live remote `refs/heads/main` were all
`3782c179a2b30fba2948b1bb825542b12470126d`; ahead/behind `0/0`.
Parent: `84bb732df8c391a909f17c33d28ed25f47a1bd41`.
Subject: `Updated project WBSO...`.
Author/committer: `Emin-A <eminavdovic@gmail.com>`.
Author and commit date: `2026-09-28 21:50:54 +0200`.

Discovery and the project-local WBSO checkpoint were committed TOGETHER in this
one commit. Identification is from the changed paths/content, not its subject.

| Committed path | Insertions | Deletions |
| --- | ---: | ---: |
| BIMCode_Provider/M4B_DISCOVERY.md | 556 | 0 |
| PROJECT_STATE.md | 66 | 0 |
| WBSO/Data_Models/provider_registry.md | 60 | 0 |
| WBSO/Technical_Notes/architecture_notes.md | 109 | 0 |
| WBSO/Technical_Notes/current_scope_alignment.md | 66 | 0 |
| WBSO/Technical_Notes/evidence_reference.md | 76 | 0 |
| WBSO/Testing_Validation/test_plan.md | 80 | 0 |
| WBSO/Testing_Validation/validation_summary.md | 63 | 0 |
| TOTAL: 8 files | 1076 | 0 |

The parent is the closed M4A host-only layer (`docs(wbso): mark M4A host-only
write closed`). No runtime implementation was added by this checkpoint.
The tracked discovery records the fixed tool/action/schema, human confirmation,
Option A asynchronous host coordination, sidecar exit before host completion,
owner-aware admission, completion callback, deterministic projection, authoritative
host result, default-off permission, 13/14 tool split, lease redesign, and all
LIVE-M4B-01 through LIVE-M4B-18 as pending.

Reconciliations, without changing discovery or WBSO:

- Their pre-commit statements describing discovery as untracked/uncommitted and
  design as blocked are stale relative to the verified Git checkpoint above.
- Discovery's possible local configuration gate is narrowed here to memory-only
  human permission. No configuration/environment variable grants write consent.
- Shared admission requires thin future guards for human Preview/Setup entry
  points, not changes to their parameter or preview semantics.
- The closed M4A Dev request retains its legacy lease. Provider requests receive
  an explicit versioned lease contract; timestamps must not be spoofed to reuse it.

## 2. Current source inventory and retained boundaries

Paths below are relative to the repository. `pane/` in this document abbreviates
`AI.extension/lib/bimcode_ai_pane/`; `lib/` abbreviates `AI.extension/lib/`.

| Responsibility | Existing source / symbol |
| --- | --- |
| Pane send/request lifecycle | pane/panel.py: `_on_send`, `_start_provider`, `_provider_complete`, `_ai_tool_complete` |
| Scalar request and Send lock | pane/provider_bridge.py: request construction, `SendState.begin/finish`, `decode`, `decode_tool`, `run` |
| Background process/UI completion | pane/provider_ui.py: `launch`, presentation helpers; worker then Dispatcher callback |
| AI ownership and one-call guard | pane/ai_tool.py: `Coordinator.begin`, `queue`, `complete`, `execute_approved`; `turn`, `used`, `pending` |
| Host fixed read-only registry | pane/ai_tool_registry.py: `ACTIONS`, `LABELS`, `SPECIALTIES` (13 entries) |
| Provider schema and initial/final API | BIMCode_Provider/provider.py: `TOOLS`, `TOOL_INSTRUCTION`, `client_for`, `send`, `tool_response` |
| Scalar protocol and tool validation | BIMCode_Provider/protocol.py: bounded request parsing; tool_protocol.py: `validate_call`, `validate_request`, fixed `ACTIONS` |
| One-shot sidecar | BIMCode_Provider/sidecar.py: `main`/dispatch, stdin JSON -> scalar stdout JSON |
| Read-only host dispatch | pane/lifecycle.py: `PaneSession`, `ModelMindReadOnlyHandler`, `raise_ai_event`, `request_tool` |
| Read-only result projection | pane/ai_tool.py: `compact`; bounded allowlist, not raw Revit objects |
| M4A value contract | pane/write_contracts.py: `validate_value`, fixed feature/action/name/GUID |
| Snapshot/fingerprint | lib/bimcode_write_runtime.py: `capture_preview_context`; sorted selection and canonical JSON fingerprint |
| Target/GUID/binding | same: `resolve_target`, `verify_binding`, `resolve_parameter` |
| Deterministic preview | same: `_preview`, `build_preview` |
| Native consent/approval | pane/write_coordinator.py: `confirm`, `WriteCoordinator.invoke`, `epochs`; execution module `freeze` |
| Dedicated write event/completion | same: `WriteHandler.Execute`, `WriteCoordinator.execute`, `get_coordinator` |
| Epochs | pane/lifecycle.py: context/selection generations; WriteCoordinator DocumentChanged epoch |
| Transaction and verification | lib/bimcode_write_execution.py: `Executor.execute`, `revalidate`, `settle`, `verify`, `check_pending`, `result_for` |

Current provider initial call uses `store=True`. Continuation uses the original
`previous_response_id`, original `call_id`, and `function_call_output`;
`store=False`, `tools=[]`, `tool_choice="none"`. Keep these semantics. Current
multiple-call and second-call rejection, unknown-tool checks, strict arguments,
request correlation and bounded output validation must remain on both sides.

Current M4A contract: feature `MEP-PARAM-WR-001`, action
`MEP-PARAM-WR-001-A01`, parameter `BIMCode_M4A_TestText`, constant
`M4A_TEST_PARAMETER_GUID = 2f3c955d-45ee-4258-bc61-08acd40a2912`, exactly one
eligible rigid host-document Pipe, transaction `BIMCode M4A Set Test Text`.
Only the existing host executor calls `Parameter.Set`. It validates identity,
selection, epochs, type, binding, storage, prior value and HasValue immediately
before mutation; checks commit status and rereads the exact GUID afterward.
Pending/unknown transaction outcomes retain a safety lock. Verification failure
after commit is not rollback, and must retain `model_modified=True`.

## 3. Architecture decision

Use Option A: pane-owned logical request, short-lived initial sidecar, host-only
preview/TaskDialog/dedicated write ExternalEvent, immutable completion receipt,
then a NEW sidecar for one explanation continuation. Never wait for a human in
the sidecar, hold a transaction during a dialog/network call, or call Revit from
a worker. No polling, timers, background Revit API, generated code or retries.

Sequence:

1. Reserve a logical provider turn; prepare document eligibility/snapshot in a
   valid host API event. Build the tool surface from host permission evidence.
2. Start initial sidecar; provider returns zero or exactly one function call.
   Sidecar exits before host confirmation. Zero calls complete as ordinary text.
3. Validate the single call and consume the one-tool budget BEFORE dispatch.
   Promote the existing owner token to controlled write without release/reacquire.
4. Retain original response ID, call ID, logical ID, host request ID, tool name,
   validated value, permission generation, document/selection/context epochs.
5. Host preparation event rechecks snapshot and permission, builds preview, renders
   a non-authorizing preview card, then opens native TaskDialog in API context.
6. Cancel/not-ready/expiry yields a deterministic non-mutation result. Confirm
   freezes the approval and queues the existing dedicated write event.
7. Write handler consumes the request once, revalidates and calls the host executor.
8. Store scalar host receipt, then dispatch completion to the pane. Render host
   truth before sending a continuation. No API objects cross the boundary.
9. New sidecar sends one function_call_output. Render explanation separately.
   Release request owner at terminal state, except retained transaction safety lock.

Failure before tool selection produces a provider error, no fabricated host write.
Failure after selection but before execution produces a truthful blocked/cancelled
receipt. Failure during execution uses the executor's actual transaction outcome.
Failure during explanation never changes that receipt or retries the mutation.

## 4. State machine and lifecycle rules

Owners: `P` = reserved PROVIDER_TURN; `W` = CONTROLLED_WRITE_PROVIDER_TOOL;
`T` = retained transaction safety lock, independent of request ownership;
`-` = no request owner. Each table row is nonterminal unless marked terminal.
All transitions not listed are forbidden, including any provider-supplied transition.
Read-only selection branches to the unchanged read-only coordinator, not write states.

| State | Owner | Valid entry | Valid exit | Cleanup/lifecycle class |
| --- | --- | --- | --- | --- |
| IDLE | - | fresh coordinator / released terminal | PROVIDER_INITIAL_REQUEST | terminal, L0 |
| PROVIDER_INITIAL_REQUEST | P | IDLE, successful admission | PROVIDER_TOOL_SELECTED, PROVIDER_FINAL_RESPONSE_READY, CANCELLED, EXPIRED | L1 |
| PROVIDER_TOOL_SELECTED | P | validated single initial call | WRITE_ARGUMENTS_VALIDATED, HOST_RESULT_READY, CANCELLED | L1; invalid call cannot execute |
| WRITE_ARGUMENTS_VALIDATED | W | valid schema + atomic owner promotion | HOST_PREVIEW_BUILDING, HOST_RESULT_READY, CANCELLED, EXPIRED | L1 |
| HOST_PREVIEW_BUILDING | W | host preparation handler | PREVIEW_NOT_READY, PREVIEW_READY, HOST_RESULT_READY | L1 |
| PREVIEW_NOT_READY | W | blocked preview | HOST_RESULT_READY | L3; no approval |
| PREVIEW_READY | W | deterministic OK preview | AWAITING_HUMAN_CONFIRMATION, APPROVAL_EXPIRED, CANCELLED | L1 |
| AWAITING_HUMAN_CONFIRMATION | W | displayed preview/native dialog | USER_CANCELLED, APPROVAL_EXPIRED, WRITE_REQUEST_QUEUED, HOST_RESULT_READY | L1; stale recheck after dialog |
| USER_CANCELLED | W | native Cancel | HOST_RESULT_READY | L3; mark cancellation terminal intent |
| APPROVAL_EXPIRED | W | expired preview/queue lease | HOST_RESULT_READY | L3; mark expiry terminal intent |
| WRITE_REQUEST_QUEUED | W | valid native Confirm + frozen request | WRITE_EXECUTING, APPROVAL_EXPIRED, HOST_RESULT_READY, CANCELLED | L1; single-use token |
| WRITE_EXECUTING | W | consumed matching event request | WRITE_SUCCEEDED, WRITE_FAILED, WRITE_INDETERMINATE | L2 |
| WRITE_SUCCEEDED | W | committed + reread verified | HOST_RESULT_READY | L3 |
| WRITE_FAILED | W | definitive executor failure, including committed verification failure | HOST_RESULT_READY | L3; preserve commit flags |
| WRITE_INDETERMINATE | W+T | pending/unknown executor outcome | HOST_RESULT_READY | L3 + retained T |
| HOST_RESULT_READY | W (or P for rejected call) | immutable receipt from listed result paths | PROVIDER_CONTINUATION_PENDING, COMPLETED, CANCELLED, EXPIRED | L3; publish truth first |
| PROVIDER_CONTINUATION_PENDING | W/P, optionally T | receipt published + valid original call | PROVIDER_CONTINUATION_FAILED, PROVIDER_FINAL_RESPONSE_READY, COMPLETED, CANCELLED, EXPIRED | L3 |
| PROVIDER_CONTINUATION_FAILED | W/P, optionally T | error/timeout/malformed final | COMPLETED, CANCELLED, EXPIRED | L3; host unchanged |
| PROVIDER_FINAL_RESPONSE_READY | W/P, optionally T | validated final text/no tool | COMPLETED, CANCELLED, EXPIRED | L3 |
| COMPLETED | - (possibly T) | final/error/no-continuation decision | IDLE only when admission safe | terminal L0; not synonymous with write success |
| CANCELLED | - (possibly T) | preexecution cancellation or cancelled terminal intent | IDLE only when safe | terminal L0 |
| EXPIRED | - (possibly T) | expired preexecution request/terminal intent | IDLE only when safe | terminal L0 |

Lifecycle classes apply to EVERY state in the table:

- L0: clear transient callbacks/approval and release matching request owner once;
  retain bounded scalar receipt, tombstone and any T lock. Duplicate events are
  ignored. Late callbacks cannot revive the request or overwrite newer requests.
- L1: document switch/close, pane disposal/explicit cancel, permission revocation,
  or shutdown invalidates generation and unconsumed approval. No transaction may
  start. Queue handlers see invalid token and return non-mutation receipt. If no
  execution has begun, terminate CANCELLED/EXPIRED; suppress unavailable continuation.
  Native dialog must recheck invalidation after it returns. Hiding the pane also
  cancels unexecuted provider-write intent via UI visibility notification; it does
  not unregister the pane or its once-per-session lifecycle subscriptions.
- L2: cancellation/close cannot assert rollback or clear ownership while executing.
  Finish/settle in valid host context; preserve receipt even if UI disposed. During
  shutdown no new API work is scheduled; unresolved outcome remains indeterminate.
  Never release T merely because a document/pane/process disappeared.
- L3: document/pane loss suppresses explanation/UI delivery as needed, not transaction
  truth. Store receipt first, release request owner after terminal processing, retain
  T if unresolved. An explicit host status inspection may resolve T without another
  Set/commit/retry. Receipt revision is separate from the already-consumed tool call;
  it does not initiate a second provider continuation.
- All classes: duplicate event/callback with identical correlation/payload is a no-op;
  contradictory duplicate is a protocol diagnostic, first accepted receipt retained.
  Wrong-generation callback cannot drive current state. If it contains an actual
  execution receipt, retain it in the old request slot rather than discarding truth.

No asynchronous cancellation implies success or no mutation. No generic timeout can
release an executing/retained transaction. Completion only means logical request ended.

## 5. Owner-aware admission

Proposed pure `OperationAdmission` in pane/write_access.py owns one immutable token
`(session_nonce, logical_request_id, owner_generation, owner_type)` and a separate
retained-T flag. Owner types: PROVIDER_TURN, READ_ONLY_PROVIDER_TOOL,
CONTROLLED_WRITE_PROVIDER_TOOL, HUMAN_DEV_WRITE, HUMAN_DEV_PREVIEW,
PARAMETER_PROVISIONING, and DETERMINISTIC_READ_ONLY_TOOL (M2).

All are mutually exclusive while active. Existing read-only pending/turn/busy gates
remain checks, not replaced by a permissive flag. Acquire once before starting work;
duplicate acquisition rejects. A valid provider selection atomically specializes P
to W or READ_ONLY_PROVIDER_TOOL using the SAME request/generation, never dropping
the lock. Host coordinator accepts that matching W token despite the matching AI
turn, but still rejects every unrelated AI/human owner. No blanket removal of
`session.ai.turn` protection.

Release is compare-and-release on the same token at terminal cleanup, once. Cancel,
expiry and failure before execution consume/invalidate approval. Stale owners may
be cleared only with proof no pending/running/retained executor exists; otherwise
fail closed and require explicit host status inspection. Read-only requests while
write/dialog/continuation is pending return busy, never run alongside a write.
Setup and Preview get thin admission/finally-release guards; their domain logic is
unchanged. No elapsed-time lock stealing. A full session restart resets pure state,
not a claim about the fate of a previously indeterminate model transaction.

## 6. Permission and eligibility

Memory only: `PaneSession.controlled_write_permission` contains enabled=false,
session nonce, document key, permission generation and human disposable-model
attestation. Restart initializes disabled. No config file, environment variable,
API key or model response enables it.

Pane control: `Enable controlled writes for this session` plus `Disable controlled
writes`. Enable raises a host preparation event, validates document/binding and
asks the human to attest use of a disposable test project. This is permission to
offer a tool, NOT approval for a write. Indicator exactly:
`CONTROLLED WRITES: DISABLED` or `CONTROLLED WRITES: ENABLED FOR THIS SESSION`.
Show disabled reason separately; disable remains available while a turn is active.

Registry eligibility: active host project, not family/linked/workshared/read-only
or currently modifiable, expected shared GUID/Text/instance/Pipe binding provisioned.
Recheck in valid host API context before each initial request; no WPF Revit reads.
Selection cardinality is NOT tool-list eligibility: enabled eligible document gets
14 even with zero/multiple/unsupported selection; deterministic preview rejects it.
Otherwise exactly the original 13, with write schema omitted entirely.

Document switch/close resets permission and increments generation. Reopening requires
new enable action. Same-document view/selection changes invalidate pending snapshots,
not silently renew approval. DocumentChanged invalidates write epochs; recheck
parameter eligibility before offer and execution. Missing binding means no write tool;
removal after offer means preview/execution blocked, not automatic provisioning.
Use existing `resolve_target`/`resolve_parameter` reason codes, including their
workshared-document rejection, not invented substitute runtime codes.

Execution additionally requires exactly one host rigid non-placeholder Pipe, no
group/assembly/design option/pinned target, expected type/identity, writable String
parameter, unchanged before value/HasValue and matching invocation snapshot/epochs.

## 7. Registry and fixed schema

Keep original thirteen mappings source-compatible. READ_ONLY_TOOL_REGISTRY is the
existing registry; CONTROLLED_WRITE_TOOL_REGISTRY is a separate single-entry
registry. Compose a new list per request without mutating global TOOLS.

| Entry field | Fixed design |
| --- | --- |
| Name | set_selected_pipe_test_text |
| Action | MEP-PARAM-WR-001-A01 |
| Safety | CONTROLLED_WRITE |
| Enable predicate | matching memory permission/session/document generation |
| Document predicate | section 6; selection deferred to host preview |
| Validator | exact object/value validation plus existing M4A validate_value |
| Dispatcher | provider-write coordinator -> host preparation -> M4A write event |
| Projection | write_projection.project_receipt, explicit scalar allowlist |
| Provenance label | Set Selected Pipe Test Text |

Responses function wrapper uses `type: function`, this name, `strict: true`, and
the following exact `parameters`:

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

Exact proposed tool description:

> Request a human-confirmed change of ONLY BIMCode_M4A_TestText on exactly one
> currently selected eligible rigid Pipe in the active host test project. Supply
> only the requested literal value. The host previews, validates, asks a native
> confirmation dialog and alone decides whether to write. This call does not grant
> consent or guarantee success. Do not use for Mark, Comments, other parameters,
> geometry, systems, Ducts, batches, scripts, repair, summaries or QA. Never infer
> confirmation from conversation. At most one tool total per request; do not chain
> a read and a write. If disabled or the requested operation differs, explain that
> it is unsupported rather than substituting this test-field write.

Both sidecar and host reject duplicate JSON keys, nonobject/array input, any key
except `value`, nonstring, empty, overlength, whitespace/control/newline/tab and
non-full matches. Host uses existing `\A...\Z` validation, not `$` accepting a
trailing newline. No normalization or trimming into validity. Explicit forbidden
fields include confirmation, confirmed, ElementId, element_ids, parameter,
parameter_name, parameter_guid, action_id, document_id, transaction and options.
Paths/URLs/scripts with syntax fail grammar. Alphanumeric words such as `delete`
cannot reliably be recognized as commands; they are inert text, NEVER interpreted
or executed. No-change/selection/document/parameter checks are host-only predicates.

Positive routing: `Set the selected pipe test text to M4A_AI_01.`, `Change the
selected pipe test text to Demo_01.`, `Write Review_Ready to the selected pipe test
field.` Negative routing: Set Mark/Comments, change diameter, move pipe, assign
system, modify Duct/multiple Pipes/all elements, run script/fix model. Summarize,
connectors, QA remain their read-only tools; shared-parameter questions use no tool.
Model routing is probabilistic, not proof of authorization. Host contract and human
dialog are the enforcement boundary even if the model chooses the wrong tool.

## 8. Protocol, callback and continuation

Introduce a bounded optional host-generated field `tool_surface` on agent_turn and
tool_result requests: `READ_ONLY` (default if absent) or `CONTROLLED_WRITE_TEST`.
Keep protocol_version=1 and old read-only shape accepted; any other extension rejects.
Only the pane's host-validated permission snapshot can choose the second value.
It is schema-selection metadata, not host execution authority. Bind it to the
logical turn and reject response/continuation surface mismatch.

Example continuation envelope (IDs illustrative; result is the section 10 object):

```json
{
  "protocol_version": 1,
  "request_id": "0123456789abcdef0123456789abcdef",
  "operation": "tool_result",
  "tool_surface": "CONTROLLED_WRITE_TEST",
  "tool_call": {"call_id": "call_original", "name": "set_selected_pipe_test_text", "arguments": {"value": "M4A_AI_01"}},
  "provider_state": {"response_id": "resp_original", "model": "configured-model"},
  "tool_result": {"action_id": "MEP-PARAM-WR-001-A01", "classification": "MEP_PARAMETER_WRITE_OK", "reason_code": "COMPLETE"}
}
```

The example's tool_result is abbreviated for legibility; actual request MUST contain
the complete mandatory projection in section 10, not this abbreviated object.
Existing envelope field `provider_state.response_id` becomes API argument
`previous_response_id`. The controlled-write validator uses its own fixed receipt
contract rather than the read-only `specialty` predicate. Retain
the original logical request ID across the two process invocations and correlate
worker completion separately by phase. No provider-supplied action/target is accepted.

Proposed `WriteCompletionReceipt` is immutable JSON plus correlation tuple
`(session_nonce, logical_request_id, host_request_id, owner_generation, call_id)`.
`ProviderWriteCoordinator.accept_host_result(receipt)` is the UI-side sink.
Write handler records receipt into session storage in Revit API context BEFORE
posting Dispatcher delivery; callback exceptions cannot lose it. Deferred UI callback
has no Revit access. Preserve first accepted payload hash; exact duplicate ignored,
conflicting duplicate logged as protocol failure without mutation or overwrite.

Disposed pane/document/expired request: retain actual transaction receipt, suppress
stale UI/continuation. Wrong request never changes current UI. Cancellation before
execution invalidates queued token; after execution begins it cannot discard truth.
There is no callback timeout that proves no mutation. A missing callback marks UI
status unavailable, retains admission if execution may exist, and exposes explicit
host status inspection (no retry/Set). Bounded one active receipt plus last completed
receipt and capped scalar tombstones; no document/API objects retained in receipts.

A new sidecar receives complete validated projection. It sends original response ID
and call ID with JSON function_call_output. Initial store=True; final store=False,
tools=[], tool_choice=none, parallel_tool_calls=False. Even if API returns a call in
final output, reject it at sidecar AND pane. Consume one-tool guard before any dispatch;
read+write, write+read, two writes, malformed multi-call, retries and second tools all
fail closed. Explanatory text cannot dispatch anything.

Keep current bounds: 2,000 user characters; 80,000 serialized tool-result characters;
120,000 request characters; 100,000 response characters; 12,000 final-text characters.
Use ensure_ascii serialization to make transport budgeting predictable. Preserve
required receipt fields; overflow blocks explanation, never truncates transaction
truth into a misleading result. SDK timeout 45 seconds, process timeout 75 seconds,
max_retries=0. No automatic retry. Continue only once with original call/model state.
Use current scalar response envelope and request matching; no SDK/API objects.
API error, timeout, malformed final and cancellation affect explanation only.

Official contract reference: [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling).
This supports strict schemas and function_call_output continuation; application
authorization, leases and transaction truth remain host responsibilities. No
authenticated request was used to prepare this design.

## 9. Confirmation and clocks

Only existing native `confirm` TaskDialog can approve. Cancel is default. Pane
preview is informational; no pane button executes/bypasses native confirmation.
Dialog includes document/view/target, fixed parameter/GUID, before/after and request
identity. Conversation wording, schema arguments and prior approval never count.

Record monotonic timestamps: tool_selected_at, arguments_validated_at,
preview_created_at, preview_displayed_at, dialog_opened_at, confirmed_at,
event_raised_at, handler_started_at, transaction_started_at. UTC display timestamps
are diagnostic only. Use a host monotonic clock available in IronPython (Stopwatch),
injectable in tests; never provider wall-clock time.

Preview lease: 120 seconds from completed deterministic preview creation. Recheck
before opening and after returning from dialog. Confirm must occur within it.
Successful confirmation replaces preview lease with 30-second execution-queue lease
from confirmed_at; check before Raise, at handler entry and immediately before
transaction.Start. Full stale-context checks still apply. Neither lease renews;
human resubmission is a new request, not automatic retry. Negative/invalid elapsed
time fails closed. Lease bounds do not authorize aborting an already started transaction.

| Condition | Result / reason | Phase diagnostic |
| --- | --- | --- |
| Preview/dialog lease expired | MEP_PARAMETER_WRITE_NOT_READY / CONFIRMATION_EXPIRED | PREVIEW_LEASE |
| Queue/confirmation lease expired | MEP_PARAMETER_WRITE_NOT_READY / CONFIRMATION_EXPIRED | EXECUTION_QUEUE_LEASE |
| Context/selection/DocumentChanged changed | MEP_PARAMETER_WRITE_NOT_READY / STALE_CONTEXT | actual stage |
| Invalid/revoked owner before execution | MEP_PARAMETER_WRITE_NOT_READY / CONFIRMATION_INVALID | OWNER_INVALID |

Precedence: invalid correlation/replay/owner first, stale context second, lease
third, then existing target/parameter/value revalidation. No new expiry reason code
is necessary. Use versioned immutable `ProviderRequestV2` and `freeze_provider`/
lease validator in the host executor boundary. Preserve legacy Request/freeze and
60-second Dev behavior; do not alter created time to trick existing validation.
Common mutation/settlement/verification implementation remains single-sourced.

## 10. Projection and independent status

`HOST_WRITE_STATUS` is the host classification/reason, NEVER provider ok/text.
`PROVIDER_EXPLANATION_STATUS` is PENDING, COMPLETE, FAILED or UNAVAILABLE.
UI overall success is allowed only on host OK/COMPLETE with committed=true and
verification_passed=true. Logical COMPLETED or explanation COMPLETE is not write OK.

Mandatory projection: feature_id, action_id, request_id (host ID), classification,
reason_code, target_category, target_element_id, parameter_display_name,
parameter_guid, before_value, proposed_value, final_value, confirmation_result,
transaction_started, transaction_committed, transaction_status, model_modified,
verification_performed, verification_passed, warnings. Include logical request ID,
host phase and before_has_value as bounded metadata; omit raw API objects and paths.
Unknown fields are not forwarded. Missing values remain null, not empty-success.
Category derives from validated host target; otherwise null. Fixed identifiers are
host constants. Preserve up to 30 bounded warnings with an explicit omitted count;
do not omit the warning that commit occurred but verification failed.

| Outcome | Projection treatment |
| --- | --- |
| PREVIEW_NOT_READY | preserve original PREVIEW_NOT_READY classification/reason in preview evidence; nonexecuted host receipt NOT_READY, same reason |
| NO_CHANGE_REQUIRED | NOT_READY / NO_CHANGE_REQUIRED; no confirmation/transaction/mutation |
| USER_CANCELLED | CANCELLED / USER_CANCELLED; native cancellation, transaction not started |
| CONFIRMATION_EXPIRED | NOT_READY / CONFIRMATION_EXPIRED, phase identifies lease |
| STALE_CONTEXT | NOT_READY / STALE_CONTEXT; no queued approval reuse |
| WRITE_OK | OK / COMPLETE; committed true, final reread, verified true |
| WRITE_FAILED | preserve executor failure reason and actual transaction flags; never infer rollback |
| WRITE_INDETERMINATE | INDETERMINATE, actual status, model_modified null if unknown, retained T |
| VERIFICATION_FAILED | FAILED / VERIFICATION_FAILED; committed/model_modified true, verification failed; manual inspection/Undo warning |

Write classification prefixes above are `MEP_PARAMETER_WRITE_`; preview uses
`MEP_PARAMETER_WRITE_PREVIEW_`. Failed preview reads retain preview failure evidence
and yield nonexecuted FAILED receipt, not a fabricated transaction failure.

Before consent show Tool requested: Set Selected Pipe Test Text; Safety: CONTROLLED
WRITE; action; Pipe ID; fixed parameter; before/after; Confirmation: REQUIRED;
Model modified: NO. After cancel show CANCELLED and NO. After success show OK,
Committed, Verification PASS, before/final. After verification failure show committed
but verification FAILED, not a green success. Render provider explanation in a separate
section with its own status. Host success + explanation failure must still show all
committed/verified facts. Preserve current theme, bounded renderer and local Find.

## 11. Proposed implementation file plan (no files below changed by this design)

Every new runtime module requires a pure/fake-host test before integration. `pane/`
and `lib/` expand as defined in section 2.

| Path | Kind | Responsibility, dependency and reason |
| --- | --- | --- |
| pane/write_access.py | new | pure permission/admission tokens; shared by pane and human commands; no API/background consent |
| pane/provider_write.py | new | state reducer/correlation/continuation handoff; uses access/projection, separates orchestration from executor |
| pane/provider_write_events.py | new | once-registered preparation event for eligibility/snapshot/preview/dialog; uses runtime/coordinator only in API context |
| pane/write_projection.py | new | bounded immutable receipt projection; no provider SDK/Revit dependency |
| pane/controlled_write_registry.py | new | fixed mapping/metadata and host argument check; depends on write_contracts |
| BIMCode_Provider/write_tool_protocol.py | new | one strict schema, validator, provider-side mapping; isolated from read-only mappings |
| BIMCode_Provider/tool_protocol.py | modify | surface-aware call/request validator delegates write branch; readonly contract unchanged |
| BIMCode_Provider/protocol.py | modify | optional tool_surface allowlist/bounds; rejects unknown envelope fields |
| BIMCode_Provider/provider.py | modify | compose 13/14 schemas/instructions per request; keep one-call/final-no-tool guards |
| pane/provider_bridge.py | modify | scalar surface/call validation and phase correlation, no Revit API |
| pane/ai_tool.py | modify | reserve/promote owner and dispatch fixed write branch; readonly execute/compact semantics unchanged |
| pane/panel.py | modify | permission UI, logical write flow and independent status rendering |
| pane/provider_ui.py | modify | independent host/explanation presentation; existing worker remains API-free |
| pane/BIMCodeAIPane.xaml | modify | enable/disable control, indicator, host provenance section |
| pane/lifecycle.py | modify | session state, preparation-event creation, once-only subscriptions, invalidation/cleanup |
| pane/write_coordinator.py | modify | matching owner admission, preview/dialog continuation and immutable callback; retain Dev path |
| lib/bimcode_write_execution.py | modify | explicit versioned provider lease interface; reuse existing transaction/verification, preserve legacy request |
| AI.extension/AI.tab/Dev.panel/M4APreview.pushbutton/script.py | modify | thin shared admission guard only |
| AI.extension/AI.tab/Dev.panel/M4ASetup.pushbutton/script.py | modify | thin shared admission guard only |
| tests/test_bimcode_provider_write.py | new | state machine, correlation, callback, continuation and fake host |
| tests/test_bimcode_write_access.py | new | permission/owner/lifecycle admission |
| tests/test_bimcode_write_projection.py | new | complete bounded truthful receipts and UI status |
| tests/test_bimcode_write_tool_protocol.py | new | 13/14 schemas, arguments, forbidden fields, continuation |
| tests/test_bimcode_write_runtime.py | modify | provider lifecycle boundary regressions; existing preview tests retained |
| tests/test_bimcode_write_native.ps1 | modify | native contract/bridge probes and IronPython compatibility |

Existing relevant provider/pane test files discovered at implementation time may
need narrowly scoped integration assertions; inventory before edits and approve any
additional path. No broad rewrite justified. No new dependency/config/secret file.
Must remain unchanged: AI_01.pushbutton/script.py Workbench/domain functions,
prompt_catalog.json (237), read-only ai_tool_registry.py mappings, write_contracts.py
fixed identities/value semantics, bimcode_write_runtime.py target/preview semantics,
sidecar process foundation/config, requirements manifests, .env.local, AGENTS.md,
WBSO, closed specialty handlers, dashboard/issue index/export/workflow semantics.
No changes to bundles or human provisioning parameter contract are needed.

## 12. Implementation order and checkpoints

These are proposed future commits, not authorization to stage/commit now.

| Stage | Deliverable / gate |
| --- | --- |
| M4B-0 | memory-only permission and tests, default disabled |
| M4B-1 | registry partition without enabling write schema |
| M4B-2 | strict one-value validation, hostile input probes |
| M4B-3 | deterministic projection/provenance contracts |
| Checkpoint A | commit pure contracts only after static PASS; no exposed tool |
| M4B-4 | reducer and exhaustive legal/illegal transition tests |
| M4B-5 | owner admission across provider/human/M2, retained-T guard |
| M4B-6 | host receipt callback and duplicate/late lifecycle handling |
| M4B-7 | new-sidecar continuation and independent status |
| M4B-8 | versioned leases and host-only regression proof |
| Checkpoint B | commit disabled integration after native/fake-host PASS |
| M4B-9 | feature-gated 14th schema/UI wiring; keep default off |
| M4B-10 | full static/regression/security audit, reviewed diff |
| Checkpoint C | implementation checkpoint; LIVE VALIDATION PENDING, NOT CLOSED |
| M4B-11 | separately authorized authenticated/Revit matrix |
| Checkpoint D | closure documentation only after evidence reviewed; never presume PASS |

## 13. Static validation plan

- Registry: exactly original 13 disabled/ineligible, exactly14 enabled eligible;
  no selection-dependent omission; no electrical/HVAC write schema; unchanged read maps.
- Arguments: valid boundary lengths; extra/duplicate keys; every forbidden field;
  arrays/null/bool/batches; whitespace/newline/tab/control; overlength, paths, URLs,
  punctuation, literal code-like text never executes; no normalization.
- Routing fixtures: exact positive/negative prompts from section 7; test instruction
  and mapping deterministically. Actual model decision needs live evidence, not a
  mocked assertion that routing is guaranteed.
- Approval: no confirmation argument or inferred consent, default Cancel, changed
  preview rejected, snapshot captured before network, API-only host preparation.
- Budget: two calls, read+write/write+read, two writes, second final call, retries,
  model text/final text injection never dispatch; used guard consumed on first call.
- Projection: preview/nochange/cancel/expiry/stale/success/failure/indeterminate/
  committed-verification-failure, nulls, budgets, warning priority, no secret/API object.
- State: every edge and forbidden edge; duplicate event/acquire/callback; conflicting
  duplicate; late wrongrequest; pane hide/dispose; document close/switch; shutdown;
  no timeout releases retained T; explicit status inspection does not mutate.
- Clock: 120/30 boundaries and negative clock, long dialog, delayed event, stale ABA
  through DocumentChanged, unchanged legacy Dev 60-second tests.
- Continuation: exact original IDs, one new process, tools empty/none, timeout/errors/
  malformed output, host success preserved after provider failure/cancel, no retry.
- UI: disabled default/reset, local enable only, independent status, themes/Find/bounds,
  provenance rendered before explanation, no false COMPLETE.
- Regressions: M3 13-tool dispatch, M2 ExternalEvent/headless, all existing Workbench
  protected functions source comparison, M4A Preview and native host-write tests,
  transaction settle/verify/pending/replay cases, catalog237 and unchanged manifests.
- Tooling: Python tests with bytecode/cache writes disabled where practical; native
  assertions/bridge probes, IronPython compile, sanitized AST, py_compile to temporary
  workspace, tabnanny, diff-check, dependency check and redacted credential-pattern
  scan without reading .env.local. Report actual counts at implementation, not here.

## 14. LIVE-M4B matrix (ALL PENDING; do not execute in this task)

Common setup S: disposable eligible host project, provisioned fixed GUID, one eligible
Pipe, known before value distinct from M4A_AI_01. E=enabled for that document; D=disabled.
All cases inspect provenance/action/target and actual parameter independently after
execution. No automatic read tool chained to write. Explanation may fail independently;
unless testing failure, expect a truthful summary, never a second action.
Abbreviations: NR=MEP_PARAMETER_WRITE_NOT_READY; OK=MEP_PARAMETER_WRITE_OK/COMPLETE;
CXL=MEP_PARAMETER_WRITE_CANCELLED/USER_CANCELLED; PNR=preview NOT_READY; NT=no
transaction/no modification. Provider refusal/no-call is NOT a fabricated host NR.

| Case | Setup / permission / exact prompt or human action | Expected tool / preview / TaskDialog | Host / transaction / model | Explanation / provenance |
| --- | --- | --- | --- | --- |
| LIVE-M4B-01 | S,D; `Set the selected pipe test text to M4A_AI_01.` | write absent, no call; no preview/dialog | no host write; NT | disabled/unsupported, indicator DISABLED |
| LIVE-M4B-02 | S,D -> local Enable; then `What is a shared parameter?` | local enable attestation only; 14 schemas; question no tool/write dialog | no host write; NT | general answer; ENABLED FOR THIS SESSION |
| LIVE-M4B-03 | S,E; `Set the selected pipe test text to M4A_AI_01.`; inspect preview then Cancel | one write, correct before/after/target; native dialog | CXL; NT | cancelled; preview provenance + NO mutation |
| LIVE-M4B-04 | S,E; `Change the selected pipe test text to Demo_01.`; native Cancel | one write, Demo_01 preview, Cancel default | CXL; NT | explicit cancellation, not COMPLETE write |
| LIVE-M4B-05 | S,E; `Set the selected pipe test text to M4A_AI_01.`; Confirm | one write, OK preview, native Confirm | OK, one committed transaction, exact final text verified | committed/verified provenance; explanation separate |
| LIVE-M4B-06 | after05; no prompt; native Revit Undo | no provider call/preview/dialog | native Undo restores before; no new AI transaction | prior receipt historical, not rewritten; document epoch advances |
| LIVE-M4B-07 | S,E; current value M4A_AI_01; same write prompt | one write; PNR NO_CHANGE_REQUIRED; no dialog | NR/NO_CHANGE_REQUIRED; NT | no change needed, not write success |
| LIVE-M4B-08 | eligible doc,E, empty selection; same write prompt | one write; PNR selection count; no dialog | NR existing empty-selection reason; NT | selection prerequisite + truthful provenance |
| LIVE-M4B-09 | eligible doc,E, two Pipes; same write prompt | one write; PNR count; no dialog | NR existing multi-selection reason; NT | one target required, no batch |
| LIVE-M4B-10 | eligible doc,E, only Duct selected; `Set the selected pipe test text to M4A_AI_01.` | if write selected, PNR unsupported target; no dialog; refusal also safe | NR existing unsupported-target reason if dispatched; otherwise no host; NT | no Duct mutation; record which branch observed |
| LIVE-M4B-11 | S,E; `Set the selected pipe test text to bad/value.` | expected refusal/no tool; any invalid call rejected before preview/dialog | no execution; NT | invalid value; never sanitize to different requested value |
| LIVE-M4B-12 | S,E; `Set Mark to X.` | no write; no preview/dialog | no host write; NT | unsupported parameter; no test-field substitution |
| LIVE-M4B-13 | S,E; `What is a shared parameter?` | no tool/preview/dialog | no host write; NT | general answer, no mutation provenance |
| LIVE-M4B-14 | S,E; `Summarize the selected pipe.` | existing summarize_selected_pipes only; no write dialog | unchanged read-only result; NT | read-only action provenance |
| LIVE-M4B-15 | mixed supported selection,E; `Summarize the selected MEP elements.` | existing mixed-summary tool only; no write dialog | unchanged composite read-only result; NT | existing composite child provenance |
| LIVE-M4B-16 | S,E; `Summarize the selected pipe and set its test text to M4A_AI_01.` | no chain; request clarification or at most one call; injected double-call separately rejected | zero or one human-confirmed write only; never two tools | explain one-tool limit; no implied authorization |
| LIVE-M4B-17 | S,E; same write prompt; hold native dialog >120s then Confirm | one write, shown preview then expiry; no executable approval | NR/CONFIRMATION_EXPIRED, PREVIEW_LEASE; NT | expired, request new submission; no retry |
| LIVE-M4B-18 | S,E; same write prompt Confirm; compare separate human Dev write after manual Undo/restoration | same fixed host contract; separate requests/approvals; no AI chain | equivalent classified/verified outcomes; each successful run one TX | host before/final/flags match; provider explanation cannot override |

Cases10/11 distinguish safe provider refusal from actually exercising host rejection;
do not mark an unexecuted host branch live-PASS. Inject malformed/duplicate calls in
offline probes, not production provider bypass. Case16 cannot force a probabilistic
provider to return two calls; rejection needs deterministic offline evidence as well.
Case17's 30-second queued-event branch needs a controlled test-host delayed event
fixture, not production timers or sleeping inside an active transaction; if unavailable,
record static-only evidence, not invented live PASS. Additional lifecycle subcases:
disable/restart/doc switch reset, pane hide/close, provider error after committed write,
stale selection/model ABA, retained Pending outcome and duplicate callback. Run only
when separately authorized and feasible; record limitations explicitly.

## 15. Technical uncertainty, alternatives and non-goals

Uncertainty: how can a short-lived provider function-call response connect to a
long-running human-confirmed Revit ExternalEvent mutation while retaining one-tool
execution, explicit consent, deterministic host authority, stale-context protection
and explanation that cannot override transaction truth?

Recommended: asynchronous host ownership + frozen approval + authoritative receipt +
new explanation process. Alternatives rejected: sidecar waiting for human (lifetime/
timeouts/ownership coupling); synchronous WPF host execution (invalid API context);
reuse read-only event for writes (boundary confusion); release/reacquire owner (race);
provider confirmation or retries (consent/replay violation); persistent silent enable
(scope drift); fake fresh timestamps (lease bypass); provider text as success (false
transaction truth). Validate using pure reducer tests, native fake-host probes and
separately authorized live evidence. No WBSO IDs, prompt IDs or hours allocated here.

Non-goals: arbitrary parameters including Mark/Comments, multiple Pipes/batches,
geometry/system/circuit changes, tags/views/sheets, generated code/generic commands,
autonomous remediation, second write tool, read+write plans, provider confirmation,
AutoCAD, automatic compensation/Undo, model auto-run or broader mutation privileges.

## 16. Deliverable and readiness

This task creates only `BIMCode_Provider/M4B_IMPLEMENTATION_DESIGN.md`.
Design readiness does not mean implemented/static-runtime-validated/live-validated.
Runtime, tests, WBSO, catalog, configuration, dependencies and secrets are unchanged.
Nothing staged, committed or pushed. M4B_IMPLEMENTATION_DESIGN_READY.
