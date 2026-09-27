# M4A controlled parameter write - discovery only

## Current checkpoint - 2026-09-27

Discovery is COMPLETE / COMMITTED / PUSHED at
4db623b120b7fa19ce9a80bfa32fc682e089225c. Design, preview foundation and preview
harness are also committed/pushed; exact Git anchors and authoritative status:
[PROJECT_STATE.md](../PROJECT_STATE.md).
Host-only write implementation is now committed/pushed at
60b1818ef00bac7a058c751f24e2d4afaf857666 (nine runtime/test files, +749/-2).
Provisioning and preview matrix PASS; user-reported WRITE-01..05 PASS including
confirmed write, exact reread and manual Undo. WRITE-06..13 remain PENDING.
M4A host-write live validation PARTIAL / IN PROGRESS; NOT SOURCE-CONTROL CLOSED.
Provider write tool / OpenAI write integration NOT IMPLEMENTED;13 read-only tools.
Evidence/Daily Log/KC IDs and hours PENDING. No runtime/live tests performed by
this documentation update. Continue host-only validation; no broader mutation.

The original discovery below is preserved as a historical design checkpoint;
its no-implementation statements describe that time, not the current milestone.

Date: 2026-09-27. Package: BIMCODE-REVIT-AI-PANE-001 / M4A.
Verdict: M4A_DISCOVERY_READY_FOR_IMPLEMENTATION_DESIGN.
This is a design recommendation, not implementation or live validation approval.

## 1. Baseline and scope

Verified main HEAD/origin/main: 1d9c3a9a7525011d20f6753bcd663ffdc950ce7a;
parent f284e03123a946579dd14b95ea4ee4050dc6796b; ahead/behind 0/0; clean
before discovery. M3F is SOURCE-CONTROL CLOSED. Its 12/12 user-supplied live
passes and recorded final audit (288 Python tests, 66 native probes, 7 IronPython
compiles, 33 AST/compile/tabnanny files) are prior evidence, not rerun here.
Current production surface remains 13 read-only tools (4/4/4/1), catalog 237.
Only this document is created. No runtime/tests/WBSO/config changes, no writes,
Revit tests, authenticated provider calls, identifiers or hours are allocated.

## 2. Existing infrastructure: reusable versus unsafe seams

Locations below refer to the baseline above; script means
AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py.

| Location / symbol | Finding and disposition |
| --- | --- |
| script:4760 `_run_link_origin_reset_reviewed_apply` | Explicit transaction, geometry reread, rollback branch. Reuse design lessons only: it moves links, accepts prompt tokens, and marks committed after calling Commit without checking returned status. Not a safe M4A executor. |
| script:4560 `_collect_link_origin_reset_apply_data`; :5052 `_collect_link_origin_reset_post_apply_verification_data` | Preflight and independent verification concepts are useful; link-domain state is not reusable parameter approval. |
| script:3354-3406 latest rollback/apply/verification state accessors | Session-local evidence storage, not an immutable, single-use authorization capability bound to a parameter/value. |
| script:4106 `_run_link_origin_reset_rollback_test`; :25016 pipe split rollback group; :51027 reviewed split group | TransactionGroup/rollback experiments exist. Do not reuse: geometry scope, multiple operations and temporary mutation exceed M4A. Preview must not mutate even temporarily. |
| script:13820/13855 link confirmation tokens; :13624 persistent split token | Text tokens can be supplied in a prompt. They are not proof of a human approving an exact host preview. |
| script:52182 `answer_reviewed_action_confirmation_guard_question` | MEP-ACT-002 is a report/guard which explicitly blocks apply, not a general write approval service. |
| script:16923 `_console_confirmed_selection_dispatch_prompt`; :17111 confirmation checkbox handler | Selection confirmation concept only; not current-value-bound parameter confirmation. |
| script:15125 `execute_reviewed_action_handler` | Broad deterministic dispatcher; do not expose it or its handler names to M4A provider input. |
| script:55724 `run_reviewed_preset` | Iterates steps and can replace/restore UI selection. Unsuitable for one-element, no-selection-mutation writes. |
| script:55810 `run_approved_recipe`; :15667 `run_code_in_revit`; lib/ai_reviewed_code.py | Stored/generated-code validation and execution are explicitly excluded, even if called approved. |
| lib/ai_agent_session.py:4 `AgentSession`, :314 `execute`; script:55875 `_get_execute_plan_status`, :56166 `on_agent_execute` | Catalog/role gates and plan execution; broad multi-step/destructive enablement is not exact preview confirmation. Do not reuse Execute Plan. |
| script:12273-12369 undo helpers | Compensating transactions for prior actions, not ordinary Revit Undo. Do not add compensating M4A writes. |
| lib/Samples/Parameters.py:34 `get_param_value`, :89-91 Set samples | Demonstrates StorageType, built-in Comments/Mark and Set. Sample performs multiple writes and has no binding/verification guards; never import or execute it. |
| script:36612 `_mep_ro_001_parameter_identity`, :36663 `_mep_ro_001_read_parameter`, :37262 `_piping_ro_001_builtin_parameter` | Read-side identity/value patterns. Leave closed handlers unchanged; implement a small fixed-GUID write resolver separately. |
| script:36766 `_mep_ro_001_lookup_parameter_state` | Name lookup is useful for reporting, not authorization. No arbitrary LookupParameter string in write resolution. |

No reusable exact-preview, single-use human confirmation store was found in the
inspected pane/Workbench paths. This is a scoped finding, not a claim that every
legacy command is safe or has been audited. Existing modal Workbench, WinForms
messages and recipe metadata dialogs are not a write authorization boundary.

## 3. Current pane execution map

All pane paths are under AI.extension/lib/bimcode_ai_pane/ unless noted.

- panel.py:66 `_on_send`, :73 `_start_provider`: provider request and
  Coordinator.begin with active request_id; :92 `_provider_complete` checks
  identity and routes the single tool; :129 `_ai_tool_complete` builds continuation.
- provider_bridge.py: request protocol and request-state ownership; provider_ui.py:7
  `launch` waits for sidecar on a worker and dispatches completion onto UI.
  This worker must never resolve Revit elements or write.
- ai_tool.py:71 `Coordinator.begin`: captures document key, context_generation,
  selection_generation and used=false. :84 `queue` consumes one-tool admission,
  fixed name-to-action lookup, then raises the existing event. :117
  `execute_approved` means protocol-approved read execution, NOT human consent.
- tools.py:21 `document_key`: runtime document hash/title/path supplemented by
  lifecycle generation; hash/path alone are insufficient for future writes.
- lifecycle.py:73 `PaneSession`: scalar generations and queue; :47
  `ModelMindReadOnlyHandler.Execute` consumes pending work; :170 `raise_ai_event`
  uses the already registered tool_event. :176 invalidates context; :209 view
  activation and :214 selection changes; :237/:243 open/create/close lifecycle.
  `on_document_changed` is an open/create callback, NOT DB DocumentChanged.
  Current subscriptions (:100) do not track arbitrary model edits or Undo.
- lib/modelmind_headless.py:23 `_EXECUTION_LOCK`, :122 `_document_context`, :177
  `execute_headless_modelmind_readonly`; :55 `project_value` is scalar-safe copying.
  lib/modelmind_composite.py owns fixed A01 fan-out with the same backend lock.
- BIMCode_Provider/tool_protocol.py:43 `validate_call`, :54 `validate_request`;
  provider.py:73 `tool_response`, :124 `send`: validated one-tool request and
  tools-disabled continuation. Provider input is not host authority.

## 4. Recommended event and transaction architecture

Do NOT extend ModelMindReadOnlyHandler with a transaction branch. A tagged union
could technically be guarded, but compromises a useful no-write invariant.
Recommend one separately registered ControlledParameterWriteHandler/ExternalEvent
per pane session, registered alongside (not replacing) the existing events.
This intentionally differs from the conceptual reuse of the read-only event.
Reuse lifecycle infrastructure, not its read-only execution handler.

Use separate write registry, request contract, single-use state and nonblocking
write execution lock. Add one session admission gate shared with pane read tools
and provider turns so read/write queues cannot overlap or reenter during a modal
dialog. Existing read-only backend lock remains unchanged; do not hold it for a
write or acquire nested locks. Revit API thread serialization is not by itself
protection against stale queued work or modal reentrancy.

One provider tool -> one write-intent queue -> one dedicated event invocation:
preflight/read -> deterministic preview -> native confirmation -> revalidate ->
at most one normal transaction -> post-commit reread -> result. No transaction
exists while the preview/confirmation is shown. A preview-only host test command
may stop after preview, but is not another provider tool or schema argument.
No second event is raised by confirmation and no background API work is added.

## 5. Parameter candidates and preferred choice

| Candidate | Advantages | Risks / disposition |
| --- | --- | --- |
| Mark, ALL_MODEL_MARK | Common instance string; built-in identity | Tags/schedules/numbering and duplicate-mark warnings; not lowest risk. Availability/writability must be checked. Reject for first experiment. |
| Comments, ALL_MODEL_INSTANCE_COMMENTS | Common instance string; no intended geometry/system role | May already hold project information, feed schedules/export, or be driven by project automation. Not universally safe. Second-choice future scope, not automatic fallback. |
| Dedicated shared instance Text parameter `BIMCode_M4A_TestText` | Isolated value, stable GUID, easy before/after test | Must be manually provisioned in disposable fixture; verify instance binding and no dependent schedules/tags/updaters. Preferred. |
| Ordinary named project text parameter | Can isolate test data | Name is ambiguous; parameter ID is document-local. Inferior to fixed shared GUID. |

Choose exactly one: `BIMCode_M4A_TestText`, a dedicated shared instance Text
parameter bound only to Pipes in a disposable non-workshared project. No universal
safe parameter is established. No fallback to Comments/Mark and no runtime binding
creation. Fixture provisioning is a separate human setup operation. The actual
shared GUID must be recorded and frozen during implementation design; none is
invented or allocated here. Missing/unapproved GUID blocks execution.

For every candidate, worksharing ownership, design options, groups and links can
invalidate assumptions. IsReadOnly=false alone is insufficient. Family-instance
parameters may be formula/type driven, and Equipment/device profiles add family
variability. Dedicated text has no intended system/geometry effect, but external
updaters can react to any model change: restrict validation to a controlled model,
do not promise absence of all third-party side effects in arbitrary projects.

## 6. Initial target and editability scope

Exactly one selected host-document rigid non-placeholder Pipe, OST_PipeCurves,
actual Plumbing.Pipe instance; no FlexPipe/fabrication/fitting/link/reference
proxy, ElementType or family-document context. Verify IsPlaceholder explicitly;
do not import the entire Workbench merely for the predicate. Duct is similar but
adds another validation branch; Electrical fixtures/equipment add family/profile
variability. Choose narrow option B, not all specialties.

Reject workshared documents entirely (including borrowed/owned elements and
read-only worksets): no implicit checkout, borrowing, synchronization or ownership
changes. Reject read-only documents, already-modifiable transaction context,
groups, assemblies, design-option members, pinned elements and linked models.
Unknown editability or failed property reads fail closed. Only standalone,
non-workshared project/main-model instances are initially supported. Other states
are future scope, not defects. No picker or UI selection update.

## 7. Stable parameter identity

Resolve only the host-fixed shared GUID with get_Parameter(Guid). Verify IsShared,
matching GUID, instance Parameter.Element, shared definition/binding, Pipes category,
InstanceBinding, StorageType.String and Text data type. No type fallback.
BuiltInParameter is appropriate for a future fixed built-in; ForgeTypeId validates
data type and is not interchangeable with a shared definition GUID. Definition.Name
is display metadata only; LookupParameter is not an authorization lookup. Autodesk
documents duplicate-name ambiguity and localization risks [S1].

## 8. Provider tool and value contract (proposed, not registered)

Name: `set_selected_pipe_test_text`.
Proposed feature/action: MEP-PARAM-WR-001 / MEP-PARAM-WR-001-A01.
This follows repository specialty/WR/action naming, but allocates no WBSO ID.
One strict function schema, with only the scalar value:

```json
{
  "type": "function",
  "name": "set_selected_pipe_test_text",
  "description": "Propose one test-text change on one selected rigid Pipe; host preview and explicit human confirmation required.",
  "strict": true,
  "parameters": {
    "type": "object",
    "properties": {"value": {"type": "string", "minLength": 1, "maxLength": 64, "pattern": "^[A-Za-z0-9][A-Za-z0-9 _-]{0,63}$"}},
    "required": ["value"],
    "additionalProperties": false
  }
}
```

Host repeats all validation; schema support is not a safety boundary. For this
test-only parameter, deliberately accept ASCII letters/digits/space/_/- only,
1-64 characters, no trailing space, no empty/whitespace-only string; reject rather
than silently trim. Normalization is identity. Unicode/non-ASCII, line breaks,
controls, tabs, formula prefixes, URL/path punctuation, brackets/quotes and code
syntax are rejected. No escape/interpolation/template evaluation. This is not a
general international text-editing policy. A harmless plain word resembling an API
name is still just data, never a callable command; lexical filters cannot identify
all semantic code. No code/script/URL/path/command fields exist or are interpreted.
Reject embedded control/bidi characters in existing values rather than hiding them
in preview. Bound the before-value to 256 display characters; do not silently truncate
authorization data. Existing unreadable/oversized values block the first experiment.

Provider only interprets intent, selects this fixed proposal tool, and supplies
value. Host owns target/parameter/value validation, preview, consent, transaction,
rollback and success. No IDs, action names, parameter names, documents, scripts,
paths, commands, specialty lists or arrays accepted. Maintain one-tool maximum
for the whole request, including cancelled/failed proposals, then no-tools continuation.

## 9. Deterministic preview and naming

Proposed classifications (not existing production values):
MEP_PARAMETER_WRITE_PREVIEW_OK, MEP_PARAMETER_WRITE_PREVIEW_NOT_READY,
MEP_PARAMETER_WRITE_PREVIEW_FAILED. Reasons separate readiness from exceptions:
COMPLETE, NO_VALID_DOCUMENT, INVALID_VALUE, SELECTION_COUNT_INVALID,
UNSUPPORTED_TARGET, UNSUPPORTED_DOCUMENT, PARAMETER_MISSING, PARAMETER_IDENTITY_MISMATCH,
STORAGE_TYPE_UNSUPPORTED, TARGET_NOT_WRITABLE, NO_CHANGE_REQUIRED, READ_FAILED.

Scalar immutable preview fields: feature_id, action_id, request_id, preview_id,
session nonce/document key plus document generation, document display title,
view ID/UniqueId, lifecycle/selection/model-change generations, target ID AND
UniqueId, category ID/name, family/type (family may be not-applicable for Pipe),
parameter GUID/element ID/display name/data-type ID, StorageType, HasValue and raw
current value (null distinct from empty), proposed/normalized values, IsReadOnly,
instance binding proof, editability/worksharing flags, warnings, created/expiry
time, confirmation_required=true, transaction_started=false, model_modified=false.
Any unavailable safety field blocks readiness; no provider-composed preview text.
Equal before/after is NOT_READY / NO_CHANGE_REQUIRED, no Set and no undo entry.

## 10. Confirmation and stale protection

Prefer native Revit TaskDialog inside the dedicated API callback, with explicit
Apply test text / Cancel and Cancel default; closed dialog/Escape/nonaffirmative
result cancels. Display exact document, element, GUID/name, before and after values,
single-operation scope and ordinary Undo guidance. Escape markup/link processing;
no clipped before/after. WPF modeless confirmation is more flexible but introduces
another queue gap and larger lifecycle/UX surface. It is not the first choice.

Create host-only immutable approval record bound to every preview identity/value,
request, view, generations and parameter binding; random session-local nonce,
single-use, nonpersistent, 60-second monotonic expiry. Never send token to provider.
No prompt text, checkbox from an earlier operation or provider response can approve.
After affirmative result, revalidate and atomically consume capability before any
transaction; failures/cancel/exception/expiry consume or discard it. Double clicks,
callback replay, new prompt, close/reload and repeated request IDs cannot replay.

Reuse lifecycle and selection generations but ADD a write-only model-change epoch
from DB DocumentChanged (including Undo/Redo), invalidating pending previews on any
host-document change. Do not change read-only generation semantics. Event callback
only invalidates state, never writes. Direct reread of target UniqueId, selected ID
set, parameter binding, HasValue/raw before value, writability and active view is
mandatory after confirmation. Epoch catches value change-and-back (ABA), which
value comparison alone misses. Treat unavailable change tracking as write-disabled.
Document identity must include session-local open-instance identity, not merely
title/path/hash. Never retain Element/Parameter objects in queued scalar records.
Own successful commit increments model epoch; do not misreport that expected change
as stale authorization after the operation is consumed.

## 11. Write sequence and failure/rollback model

Design only; no DB.Transaction code is supplied or created by this discovery.

1. Admit exactly one proposal; capture/revalidate context in the API callback.
2. Resolve one target and fixed parameter, validate scalar input and build preview.
3. Obtain explicit native confirmation with no open transaction.
4. Re-resolve all identities/generations and compare exact before state; consume token.
5. Start one named normal transaction; require Started. No TransactionGroup/subtransaction.
6. Set exactly once with the validated string. False or exception is failure, not success.
7. Optional in-transaction reread detects mismatch early; rollback on mismatch.
8. Commit once; inspect returned status and final transaction status, not just exceptions.
9. Only after Committed, reacquire target/parameter and reread exact value.
10. Report deterministic result; never retry or open a compensating transaction.

Normal rollback suffices while this single transaction is still Started. Rollback
return/final status must also be checked; never claim restoration if rollback failed
or is pending. Set false means not a confirmed change [S4]; preflight no-op rejection
avoids treating an unchanged value as a successful write. Commit may return RolledBack
or Pending [S2]. Pending is NOT success or proof of no change. Recommend explicit
forced modal failure handling for the first experiment, ordinary Revit error UI,
no warning suppression, no failure preprocessor or automatic resolution [S3].
If Pending is nevertheless observed, retain transaction ownership, block further
requests, report indeterminate TRANSACTION_PENDING, and require terminal resolution
in a later valid API callback before releasing the gate. Never rollback a pending
failure process blindly or dispose it as if committed. Implementation design must
test this defensive lifecycle; no polling/background API or additional transaction.
No preprocessor is justified by current evidence; revisit only for a reproduced
failure requiring it. Transaction.Start/Commit exceptions are distinct provenance.

## 12. Verification, result and Undo

Proposed final classifications: MEP_PARAMETER_WRITE_OK,
MEP_PARAMETER_WRITE_CANCELLED, MEP_PARAMETER_WRITE_NOT_READY,
MEP_PARAMETER_WRITE_FAILED, MEP_PARAMETER_WRITE_INDETERMINATE.
Reasons include COMPLETE, CANCELLED, STALE_CONTEXT, TARGET_NOT_WRITABLE,
PRECONDITION_CHANGED, TRANSACTION_FAILED, TRANSACTION_PENDING, SET_FAILED,
VERIFICATION_FAILED. These are recommendations, not registered codes.

Success requires committed terminal status AND successful post-commit reread AND
exact ordinal equality with normalized value. Provider prose cannot determine success.
If post-commit verification fails, report transaction_committed=true and
VERIFICATION_FAILED; model_modified may be true/unknown. Do not claim rollback or
open a second transaction. Offer manual inspection/ordinary Undo, not automatic repair.
If no transaction was started, explicitly report NOT_EXECUTED and model_modified=false.

A committed normal transaction supplies a named Revit Undo item [S2]. Later live
validation must confirm one item, exact previous value/HasValue behavior after Undo,
optional Redo, and no item on preview/cancel/preflight rejection. Do not reuse the
Workbench compensating undo helpers; no live reversibility claim is made here.

## 13. Provenance and security

In-memory/pane result only; no file audit artifact, logs of secrets or WBSO writes.
Capture timestamp, request/preview IDs, feature/action, document/view/target identity,
parameter identity, before/proposed/normalized/final values, confirmation outcome,
transaction started/committed/rollback statuses, verification result, warnings,
classification/reason and whether modification is confirmed/false/unknown.
Keep exact local provenance even if provider prose is shortened. Send only minimal
bounded scalar result to tools-disabled continuation; no confirmation capabilities.

Model text, current parameter values and returned provider prose are untrusted data.
No eval/exec, generated code, arbitrary dispatcher, command deserialization or API
names used as operations. Render as plain text. Input allowlists are not substitutes
for host confirmation. Add explicit host write-mode opt-in, default off, per turn:
normal/general/read-only turns expose only the existing 13 tools and host rejects
write calls regardless of provider intent. In write mode expose only the one fixed
proposal tool; no combined read/write chain. Provider semantic routing alone cannot
guarantee a natural-language request is safe. Preview remains the authorization gate.
No second mutation from continuation; used token remains consumed on all outcomes.

## 14. Proposed implementation file boundaries

New (future):
- BIMCode_Provider/write_contracts.py: pure strict scalar schema/value checks and
  one literal tool declaration, no Revit API, network or duplicate general registry.
- AI.extension/lib/bimcode_ai_pane/write_contracts.py: IronPython-compatible fixed
  GUID/action mapping, immutable preview/approval state and host validation.
- AI.extension/lib/bimcode_ai_pane/write_coordinator.py: write queue, single-use
  token/admission, native dialog and dedicated handler; no Workbench imports.
- AI.extension/lib/bimcode_write_runtime.py: fixed-target API read/write/verify
  boundary only; no provider calls or generic executor.
- tests/test_bimcode_write_contracts.py and tests/test_bimcode_write_runtime.py;
  native host/confirmation probes in a dedicated write test script.

Narrow future integration changes: lifecycle.py (dedicated event/change epoch),
panel.py and BIMCodeAIPane.xaml (explicit write-mode opt-in and deterministic output),
provider_bridge.py and BIMCode_Provider/tool_protocol.py (separate write variant),
BIMCode_Provider/provider.py (mode-filtered fixed schema, unchanged client/network).
Cross-runtime contract parity tests are mandatory; do not import Python-3 SDK modules
into IronPython. No need for both write_registry.py and write_contracts.py at one tool.
Leave script.py, ai_tool_registry.py's 13 mappings, tools.py read execution,
modelmind_headless.py, modelmind_composite.py, specialty handlers, prompt catalog,
requirements, configuration and existing QA/workflow/export logic unchanged.

## 15. Static test plan (future, not executed)

- Exact schema/one literal mapping; reject extra keys, arrays, IDs, names, code,
  invalid bounds/characters and unknown GUID; parity of provider/host contracts.
- One element/category/profile; linked/type/group/design-option/workshared/pinned
  and unreadable states fail closed; correct String/Text/instance identity.
- Preview exact values and flags; null/empty distinction; no clipping/no-op handling;
  no transaction on preview, invalid input, missing parameter or cancellation.
- Confirmation binding of every field; cancel/close/Escape; expiry, replay,
  reused request, double callback, reload, lifecycle, selection/view and ABA changes.
- Set false/throw, start failure, commit RolledBack/Pending/throw, rollback failure;
  terminal status handling and gate retention; pre/postcommit mismatch and reread error.
- Exactly one Set/transaction/event request; no loops/retry/compensation; locks cleaned
  only after terminal states; no queued API objects or off-thread API reads.
- Write-mode admission: general/read-only turns cannot invoke write; no-tools final
  continuation and malicious result/prompt injection cannot authorize or chain writes.
- Preserve all 13 mappings, M3F partition semantics, closed specialty source bodies,
  catalog237, dependencies and read-only no-transaction static boundaries. Run full
  existing suites plus native IronPython/WPF/dialog and AST/tabnanny/diff checks.

## 16. Future live matrix (all NOT RUN / PENDING)

Use a disposable standalone project, one ungrouped rigid Pipe and the manually
provisioned fixed-GUID test parameter. Record before/after/Undo, IDs, versions,
classification, transaction flags and screenshots. Never manufacture corruption.

| Case | Required result |
| --- | --- |
| M4A-01 | Valid preview; exact values/identity; zero transaction before approval |
| M4A-02 | Explicit Apply; exactly one successful write/transaction |
| M4A-03 | Independent post-write reread matches normalized value |
| M4A-04 | Revit Undo restores prior state; one entry; optional Redo |
| M4A-05 | Cancel; no transaction/change/Undo entry |
| M4A-06 | Escape and close dialog; no transaction/change |
| M4A-07 | Empty selection rejected |
| M4A-08 | Multiple selection rejected, none filtered for execution |
| M4A-09 | Duct/Electrical/other unsupported category rejected |
| M4A-10 | Missing/wrong GUID/read-only/wrong-type parameter rejected |
| M4A-11 | Stale lifecycle/selection/view after preview rejects confirmation |
| M4A-12 | Before value changed after preview rejects; include change-back epoch probe |
| M4A-13 | General question, normal read mode: no write tool/execution |
| M4A-14 | Move/system/geometry request: no permitted write execution |
| M4A-15 | Existing M3F mixed summary parity and no transaction |
| M4A-16 | Workshared/group/design-option exclusions where safe fixtures exist |
| M4A-17 | Invalid value, same-value no-op, expiry and double-confirm/replay |

Native modal confirmation prevents ordinary user edits while visible. Cases 11/12
need controlled test seams or queued-state/native harness coverage, not unsupported
background model modification; record static-only disposition if not safely live
reproducible. Failure injection/rollback/Pending tests belong in stubs/native harness
unless a safe real fixture exists. Do not claim all paths are live-reproducible.

## 17. R&D uncertainty, decisions and implementation-design gates

Question: can provider-originated intent become one explicitly confirmed, stale-safe,
transaction-bounded parameter mutation with deterministic post-write verification,
without broadening existing read-only authority?
Alternatives investigated: extending read event versus dedicated handler; text tokens,
modeless WPF approval versus native modal confirmation; Mark/Comments versus isolated
shared text; generic dispatcher versus isolated fixed runtime; group/compensating
rollback versus one normal transaction. Selected design is dedicated, fixed and modal.
Main failure modes: wrong identity, stale/replayed approval, API read-only failures,
model change/ABA, Set/commit/rollback ambiguity, postcommit mismatch, provider injection,
unintended shared/type effect and modal reentrancy. Proposed evidence: contract/state
probes, source regression, native callback tests and the future live matrix above.

Before implementation authorization: provision and freeze the fixture GUID; review
the dedicated-event decision; confirm native Cancel/expiry UX and pending-transaction
terminal handling on installed Revit 2025.4; approve the value alphabet and opt-in mode.
These are bounded implementation-design decisions, not discovery runtime defects.
No WBSO Evidence/Daily Log/KC IDs or hours allocated.

Non-goals: arbitrary parameters/API, movement/rotation/rehosting, connector edits,
system/circuit assignment, fitting repair, deletion/creation, family/view/sheet bulk
creation, generated Python/C#, batch/chained remediation or AutoCAD. No M4A write
exists as a result of this document.

## 18. API research references and version qualification

Repository targets Revit 2025.4. Official references below establish API concepts;
2026 reference signatures/options must be checked against installed 2025 assemblies
in implementation design. No live API availability or fixture claim is made here.

- [S1 Autodesk LookupParameter](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/4400b9f8-3787-0947-5113-2522ff5e5de2.htm): name ambiguity; built-in/GUID alternatives.
- [S2 Autodesk Transaction.Commit](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/32714010-7138-f64f-8fde-a310354448e3.htm): returned statuses, Pending and named Undo item.
- [S3 Autodesk FailureHandlingOptions](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/c03bb2e5-f679-bf24-4e87-08b3c3a08385.htm): modal handling, rollback options and preprocessors.
- [S4 Autodesk Parameter class](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/333ff41b-e6a7-d959-60bf-c3bfae495581.htm): typed parameter access and fixed GUID/built-in identity. Set return behavior must additionally be checked against the installed overload documentation before implementation.
- [S5 Autodesk Binding](https://help.autodesk.com/cloudhelp/2015/ENU/Revit-API/files/GUID-C02B4263-E916-4705-A9B8-1715A526081E.htm): instance versus type binding; one definition cannot be both.

M4A_DISCOVERY_READY_FOR_IMPLEMENTATION_DESIGN
