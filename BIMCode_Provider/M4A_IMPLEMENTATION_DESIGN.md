# M4A implementation design - parameter provisioning and write contract

## 2026-09-28 - Validated host-only implementation (current)

M4A HOST-ONLY WRITE LAYER READY FOR SOURCE-CONTROL CLOSURE.
Host-only live validation PASSED WITH DOCUMENTED NONBLOCKING COVERAGE GAPS;
final static/regression audit PASSED. This final documentation is prepared for
review, not yet committed/pushed; host-only source-control closure is not yet claimed.
Provider write tool / OpenAI write integration NOT IMPLEMENTED.
PROVIDER-FACING WRITE PHASE NOT STARTED / NOT CLOSED.
No natural-language provider request can invoke M4A Write. Provider surface remains
13 READ-ONLY TOOLS (4 Piping / 4 HVAC / 4 Electrical / 1 mixed summary); catalog237.
Evidence ID / Daily Log ID / Knowledge Capture ID / project-local hours: PENDING.
No central WBSO identifiers reused. No runtime/test/provider/configuration/secret
changes or live/API tests performed by this documentation task.

Design COMPLETE / COMMITTED / PUSHED at dc14eaea00e92f75837ef98abbf012c007d3ab47.
Host implementation60b1818ef00bac7a058c751f24e2d4afaf857666 and EOD documentation
1f592632c8c14bf79f32e35002bbf43200347a4a are committed/pushed.
Full checkpoint chain/subjects: PROJECT_STATE.md.

Validated flow: human Dev command -> current context snapshot -> scalar validation
-> read-only preview -> native Cancel-default TaskDialog -> explicit confirmation
-> immutable single-use approval -> dedicated write ExternalEvent -> full final
precondition checks -> one transaction/Set/Commit -> GUID reread/exact verification.
No provider, retry, batch, second write, compensation or TransactionGroup.
Fixed contract remains MEP-PARAM-WR-001 / MEP-PARAM-WR-001-A01,
BIMCode_M4A_TestText / 2f3c955d-45ee-4258-bc61-08acd40a2912, INSTANCE String/Text,
OST_PipeCurves, one eligible rigid host Pipe. Transaction: BIMCode M4A Set Test Text.

Timing clarification: the implemented60-second lifetime begins before the proposed-
value dialog, not at Confirm. Two WRITE-07A CONFIRMATION_EXPIRED observations PASS
with no transaction/mutation. This usability limitation is retained for later
provider-facing hardening; it is not live proof of model-change/change-back rejection.
WRITE-07 model-change path retains offline coverage, no deliberate live reproduction.
Provisioning, preview, cancel, confirmed write, exact reread, native Undo, same-value,
empty/multiple/Duct/invalid guards and read-only regressions passed; M3F repeat
passed after an initial unchanged-source time-budget observation.

Final audit evidence from the preceding audit (not rerun in this documentation task):
362 Python tests PASS, including74 M4A-specific;17 native contract assertions;
66 native bridge probes;14 IronPython compiles;7 AST/py_compile/tabnanny files;
native XAML/WPF/theme/Find, whitespace, dependency, mutation-location and registry
checks PASS. Catalog237 unchanged. Credential-pattern scan reviewed126 tracked text
files: two existing identifier false positives; no newly introduced leak identified.
M3F composite/two-second budget/deadline/order/headless/Workbench source unchanged.
HVAC-QA-009 retains physical End rule and valid Curve/tap connectors; Electrical
QA still excludes open-connector and connector-count rules.

Nonblocking limits: WRITE-07 model-change/change-back not deliberately reproduced
live (static/offline coverage retained); Pending, explicit rollback/failure and
post-commit verification-failure injection not deliberately reproduced live.
Workshared documents, broader targets/categories/parameters remain outside scope.
The first WRITE-13 attempt hit TIME_BUDGET_EXCEEDED, then immediate repeat passed;
retain as INTERMITTENT / ADVISORY TIME-BUDGET OBSERVATION, not a demonstrated
persistent M4A-induced regression. Approval lifetime starts before the value dialog,
not at explicit Confirm: a known usability/timing limitation for later hardening.
WRITE-07A expiry PASS is separate from WRITE-07 model-change coverage.

Next: audit/authorize final host-only documentation checkpoint, verify closure,
then separately design provider integration. Original design/EOD text below is
historical; current authority is this section and PROJECT_STATE.md.

## Current implementation checkpoint - 2026-09-27

Design COMPLETE / COMMITTED / PUSHED at dc14eaea00e92f75837ef98abbf012c007d3ab47.
Discovery, preview foundation and harness are committed/pushed; see
[PROJECT_STATE.md](../PROJECT_STATE.md) for exact anchors.
Host-only write implementation COMMITTED / PUSHED at
60b1818ef00bac7a058c751f24e2d4afaf857666, parent
74d14b80931d4f218a2adb04b2889de65dc268d6. Despite subject project WBSO update...,
this is the nine-file runtime/test implementation (+749/-2), not final closure.

Implemented refinement authorized after this design: Dev command builds preview
and obtains native confirmation BEFORE queuing a dedicated write ExternalEvent.
The event consumes the immutable request and revalidates before mutation.
Executor is isolated in AI.extension/lib/bimcode_write_execution.py, leaving
bimcode_write_runtime.py preview transaction-free. Coordinator lives in
bimcode_ai_pane/write_coordinator.py; M4AWrite is the sole human entry.
Existing pane lifecycle/selection counters are reused; one retained DocumentChanged
subscription increments a write-only epoch conservatively for all documents.
This also invalidates commit/Undo/Redo/change-back; callback never writes/schedules.
Single-use approval expires after60 seconds and binds exact snapshot, fingerprint,
target/UniqueId/GUID/before/HasValue/proposed value/context and confirmation time.
Pending/unknown transaction ownership is retained; another human invocation only
checks status, never retries Set/Commit. Read/provider admission is blocked while
write work is pending. Provider integration remains absent;13 read-only tools.

Fixed identity remains BIMCode_M4A_TestText /
2f3c955d-45ee-4258-bc61-08acd40a2912, instance Text / OST_PipeCurves, one eligible
host rigid Pipe. Action MEP-PARAM-WR-001-A01; feature MEP-PARAM-WR-001.
Provisioning PASS; preview01-06 PASS; host WRITE-01..05 PASS (user supplied).
WRITE-06..13 PENDING; host live validation PARTIAL; M4A NOT SOURCE-CONTROL CLOSED.
Static checkpoint:362 tests (74 M4A),17 native assertions,66 bridge probes,
14 IronPython compiles,7 syntax files PASS; recorded, not rerun here.
Evidence/Daily Log/KC IDs/hours PENDING. Next: complete host-only validation.

The original design below remains historical. Its original in-event confirmation
ordering and proposed file list are superseded by the implemented refinement above;
it does not imply that provider execution or final package closure exists.

Date: 2026-09-27. Design/preparation only; no runtime implementation.
Baseline: main HEAD = origin/main = 4db623b120b7fa19ce9a80bfa32fc682e089225c,
parent 1d9c3a9a7525011d20f6753bcd663ffdc950ce7a. Starting worktree clean.
Discovery: M4A_DISCOVERY.md, committed/pushed. M3F remains closed; the production
surface remains 13 read-only tools. This document refines discovery prerequisites;
it does not authorize provisioning, model writes or provider-tool registration.

## 1. Frozen parameter identity and provisioning decision

Parameter display name: BIMCode_M4A_TestText.
Fixed shared GUID: **2f3c955d-45ee-4258-bc61-08acd40a2912**.
Exactly one GUID was generated for this design using System.Guid.NewGuid.
Do not regenerate it during implementation, installation, provisioning or execution.
This is a parameter identity, not a WBSO identifier.

Future authoritative runtime constant: `M4A_TEST_PARAMETER_GUID` in
`AI.extension/lib/bimcode_ai_pane/write_contracts.py`, stored as canonical text.
The provisioning utility imports that same constant; it must not define a second
literal. Convert to System.Guid only in Revit-side code. The provider needs no GUID.
This design is authoritative until that reviewed module exists. Tests may assert
this frozen value; no settings/environment/provider override or name fallback.

| Alternative | Decision |
| --- | --- |
| A. Manually create and bind | Simple UI, but creating a new definition generates a GUID rather than accepting this frozen one. Manual binding of an already prepared exact-GUID definition is possible, but requires that definition to be prepared first. |
| B. Separate deterministic provisioning utility | Recommended: explicitly create/verify exact GUID, Text data type and instance/category binding; reproducible and independently auditable. Never reachable from AI. |
| C. Existing shared parameter | No equally isolated exact-GUID fixture is established. Do not repurpose production data or a same-name/different-GUID parameter. |

This is an explicit refinement of discovery's manual-provisioning preference to
solve the now-fixed GUID requirement. Do not substitute Mark/Comments.

Future provisioning procedure (human-triggered, separate authorization):
1. Open a disposable, non-workshared project, not a production/central/family model.
   Draw one rigid Pipe outside groups, assemblies and design options.
2. Run a standalone pyRevit-context setup utility, not an AI tool or startup hook.
   Confirm document identity and exact parameter specification before setup.
3. Inspect existing SharedParameterElement/binding by GUID. If exactly correct,
   report ALREADY_PROVISIONED without changes. If same name has another GUID,
   type/storage/category binding differs, or duplicate/conflicting definitions exist,
   stop; do not delete, ReInsert, broaden categories or silently repair.
4. For a missing definition, use ExternalDefinitionCreationOptions with explicitly
   assigned GUID and SpecTypeId.String.Text. Use a dedicated user-approved shared
   parameter file, never the office master. Restore Application.SharedParametersFilename
   in a finally path. Do not overwrite an existing unknown file. File creation and
   binding are provisioning-only effects, never part of the AI operation.
5. Bind as InstanceBinding to a CategorySet containing only OST_PipeCurves, under
   a suitable visible UI group such as Data. One separate setup transaction must
   validate its terminal result; this is not the later one-parameter write action.
6. Read back SharedParameterElement.GuidValue, definition data type, instance binding,
   exact category set and selected Pipe parameter storage/IsReadOnly. Record fixture
   readiness; initial value may be unset. Do not initialize values automatically.
7. Save the disposable fixture manually. Verify unrelated categories lack the binding.

No utility, shared parameter file or Revit binding is created by this design task.
Installed Revit 2025.4 signatures must pass the native compile/readiness gate before
the future utility is used. A category binding cannot exclude placeholders or group
members by itself; runtime eligibility must independently reject them.

## 2. Scope and deterministic parameter resolution

Exactly one selected host-document Autodesk.Revit.DB.Plumbing.Pipe, category
OST_PipeCurves, IsPlaceholder=false. No picker/filtering of a larger selection.
Reject ElementType, linked elements/instances, FlexPipe/fabrication/fittings,
group/assembly members, design-option targets and pinned targets. Reject family,
workshared, read-only or already-modifiable documents and unknown editability.
No type-parameter, system, geometry or circuit changes; no implicit borrowing.

Resolve in the dedicated API callback, then again after confirmation:
- Check active document/session identity, eligibility, exact selected set and target
  ElementId plus UniqueId. Never resolve a caller-supplied ID.
- Resolve SharedParameterElement by the constant GUID and verify its definition's
  Text data type. Verify Document.ParameterBindings entry is InstanceBinding with
  exactly OST_PipeCurves; binding identity comes from the definition, not its name.
- Resolve target get_Parameter(Guid); require non-null, IsShared, matching GUID,
  owner equal to the selected instance, StorageType.String and IsReadOnly=false.
- Read HasValue and AsString. Store raw null separately from empty string. Display
  null as '(unset)' and empty as '(empty)'; a display marker is not a stored value.
  A convenience current_text may map null to empty, but confirmation/precondition
  comparisons retain `(HasValue, raw_value)` so null/empty transitions are detected.
- New values are nonempty; normalization is identity. Post-write equality compares
  exact AsString to the normalized requested string, not localized AsValueString.

Expected unsafe conditions return PREVIEW_NOT_READY; API exceptions/unreadable
safety evidence return PREVIEW_FAILED, never a fabricated empty value.

| Condition | Reason code |
| --- | --- |
| Parameter or shared definition missing | PARAMETER_MISSING |
| GUID/owner/shared identity mismatch | PARAMETER_IDENTITY_MISMATCH |
| Wrong storage | STORAGE_TYPE_UNSUPPORTED |
| Non-Text data type | DATA_TYPE_UNSUPPORTED |
| Parameter IsReadOnly | TARGET_NOT_WRITABLE |
| Type/broadened/missing binding | INVALID_BINDING |
| Invalid document context | NO_VALID_DOCUMENT |
| Workshared/family/read-only/transaction context | UNSUPPORTED_DOCUMENT |
| Target category/profile/group/option/pinned exclusion | UNSUPPORTED_TARGET |
| Zero or multiple selected IDs | SELECTION_COUNT_INVALID |
| Read/binding API exception | READ_FAILED |
| Proposed value equals current raw string | NO_CHANGE_REQUIRED |

## 3. Fixed provider contract

Feature: MEP-PARAM-WR-001. Action: MEP-PARAM-WR-001-A01.
Tool: `set_selected_pipe_test_text` (proposal only, not execution authorization).
Exact parameters schema:

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

No other arguments. Host performs full-string validation (not merely a regex match
ending at a pre-newline `$`), length 1-64, ASCII allowlist, leading/trailing-space
rejection, no controls/newline/tab, no whitespace-only/empty value. No trimming,
case folding or Unicode normalization; normalized value equals accepted input.
Reject overlength rather than truncate. The provider schema is advisory defense;
host validation remains authoritative. Current values are bounded to 256 visible
characters and rendered literally; unreadable/control/bidi/oversized values block
preview rather than conceal authorization data. No interpolation or code evaluation.

Normal mode exposes only the original 13 read-only tools. Explicit per-turn host
write-mode opt-in exposes only this proposal tool. Host rejects cross-mode calls.
One provider tool maximum even on cancel/failure; continuation has no tools and
cannot cause a second proposal or mutation. Provider text never confirms success.

## 4. Two-phase state machine and classifications

The two phases are logical, within one dedicated ExternalEvent invocation:
QUEUED -> PREVIEWING -> AWAITING_CONFIRMATION -> REVALIDATING -> CONSUMED ->
EXECUTING -> terminal result. No provider path can enter EXECUTING directly.
Pure state objects must enforce transitions, not trust caller-supplied state names.

Phase 1 classifications:
- MEP_PARAMETER_WRITE_PREVIEW_OK / COMPLETE
- MEP_PARAMETER_WRITE_PREVIEW_NOT_READY / reason from section 2 or INVALID_VALUE
- MEP_PARAMETER_WRITE_PREVIEW_FAILED / READ_FAILED or INTERNAL_ERROR

Only PREVIEW_OK may show confirmation. No transaction in any preview path.
Host-only preview test mode can stop there, without adding a provider argument.

Phase 2 uses classification + reason, consistent with M3F's separation of outcome
and cause; do not create redundant classification variants for every guard:

| Classification | Reason examples / meaning |
| --- | --- |
| MEP_PARAMETER_WRITE_OK | COMPLETE; committed and exact reread verified |
| MEP_PARAMETER_WRITE_CANCELLED | CANCELLED; no affirmative user confirmation |
| MEP_PARAMETER_WRITE_NOT_READY | STALE_CONTEXT, CONFIRMATION_EXPIRED, CONFIRMATION_INVALID, PRECONDITION_CHANGED, TARGET_NOT_WRITABLE; no transaction |
| MEP_PARAMETER_WRITE_FAILED | TRANSACTION_FAILED, SET_FAILED, VERIFICATION_FAILED, READ_FAILED, INTERNAL_ERROR; transaction provenance distinguishes effects |
| MEP_PARAMETER_WRITE_INDETERMINATE | TRANSACTION_PENDING, ROLLBACK_UNCONFIRMED; terminal outcome not established |

Thus WRITE_STALE_CONTEXT and WRITE_PRECONDITION_CHANGED requested conceptually are
NOT_READY with exact reasons, not ambiguous success/failure text. All names here
are planned constants, not existing registered tools or catalog codes.

## 5. Confirmation binding and TaskDialog

Immutable host-only record binds request_id, preview_id, session/open-document
identity, lifecycle generation, model-change generation, selection generation,
view identity, target ElementId/UniqueId, fixed GUID, binding/storage/type proof,
HasValue/raw before value, proposed and normalized value, expiry and one-use nonce.
No persistent token, no provider token, no live Element/Parameter in queued payload.
Revalidate every field after affirmative confirmation; mismatches invalidate the
entire record. Use a 60-second monotonic lifetime, checked after dialog returns;
no timer/polling. Consume before transaction start even if execution later fails.
Cancellation, dialog failure, stale/expired state and repeated request IDs cannot
be replayed. Cancellation is not permission to retry within the same provider turn.

Native TaskDialog inside the API callback shows document, exact target ID/category,
Pipe type (family not applicable where appropriate), parameter display name/GUID,
exact before/after values and scope. Use a Confirm command link plus native Cancel,
Cancel as DefaultButton; map ONLY the Confirm command-link result to affirmation.
Close, Escape where supported, Cancel and any unexpected result mean cancellation.
Do not use Yes as a default, markup links, hidden text, clipped values or provider
rendered confirmation. No transaction is open while the dialog is visible.
Native dialog construction/default/close behavior is a required installed-version
probe before enabling writes, not a live claim made by this document.

## 6. Minimal reliable model-change invalidation

Inspected lifecycle.py:100 `PaneSession.subscribe` already retains exact delegates
for ViewActivated, DocumentOpened/Created/Closed, SelectionChanged and ThemeChanged.
Its `on_document_changed` (:237) handles opening/creation, not DB DocumentChanged.
Add ONE Application.DocumentChanged subscription through the same retained-delegate
and duplicate-subscription/disposal mechanism. No new global service or IUpdater.

Use one write-only epoch for the active open-document session. Increment for every
DocumentChanged of that document (commit/Undo/Redo), not just target IDs: changes
to binding/definitions/type or change-and-back matter too. Inactive documents need
no dictionary of parameter histories; existing lifecycle switches invalidate the
write session. If document identification in callback fails, invalidate conservatively.
Callback only updates scalar epoch/invalidation; never writes or schedules execution.
This read-only event covers committed changes, Undo and Redo [R2]. Rereading value
alone cannot detect ABA; element filtering adds complexity without sufficient benefit.
Uncommitted changes within the same external transaction are excluded by refusing
already-modifiable document context; unavailable event subscription disables writes.

Own transaction's expected change notification must not cancel a consumed operation:
state EXECUTING/VERIFYING is distinct from a pending approval. Still increment epoch
for future requests. No change to original read-only generation behavior.

## 7. Dedicated ExternalEvent boundary

Keep ModelMindReadOnlyHandler, its registry and backend execution lock read-only.
Register one ControlledParameterWriteHandler and ExternalEvent per PaneSession;
separate write queue/contract/lock. A session admission gate prevents simultaneous
read/provider/write requests and modal reentrancy. Failed Raise consumes/clears its
request; Pending Raise status is not permission to enqueue another request.
The dedicated callback builds preview, confirms, revalidates and executes at most
once. No nested event, recursive headless call or Workbench dynamic dispatcher.
Provider worker/sidecar may carry only scalar proposal and result, never Revit API.

## 8. Transaction, Pending and verification contract

Prose design only; no transaction code is introduced.
Final validation -> require Started from one normal named transaction -> one
Parameter.Set(normalized value) -> require true/no exception -> Commit once ->
inspect returned and final status -> reacquire parameter -> exact AsString reread.
No TransactionGroup, subtransaction, compensating transaction or retry.
Set false/throw requires rollback if still Started; check rollback terminal status.
Start/commit exceptions are not proof of either modification or rollback.

Recommend explicit forced-modal failure handling, default Revit failure UI, no
warning suppression/preprocessor/automatic resolution. Require terminal Committed
for success; RolledBack is TRANSACTION_FAILED. Pending is INDETERMINATE, never
success or proof of no change. Preserve transaction ownership and block admission;
do not attempt rollback/disposal while failure processing is pending [R3].
For an unexpected Pending, a user-invoked host 'Check pending result' request may
raise the same dedicated event in resolution-only mode: inspect status and reread
after terminal completion, with no Start/Set/Commit/retry. This is not a second write
request or provider tool. No polling/timer is required. The handler must refuse new
writes while unresolved. This explicitly supplies the recovery callback left open
in discovery. Native harness must verify ownership/disposal and completion before
shipping; if unsupported, keep writes disabled rather than claiming readiness.

If committed reread fails/mismatches: FAILED / VERIFICATION_FAILED with
transaction_committed=true, rollback=false, model_modified=true or unknown as
supported by evidence. Never claim rollback after commit. Show deterministic local
result and manual Undo/inspection guidance; no automated correction.
Success requires exact equality with normalized value and committed terminal status.
Before-value null/empty/HasValue details are retained for the manual Undo test.
Cancellation/preview/precondition failure: transaction_started=false,
transaction_committed=false, model_modified=false, execution_state=NOT_EXECUTED.

## 9. Exact future implementation files

New files (not created now):
- AI.extension/lib/bimcode_ai_pane/write_contracts.py: sole GUID constant, fixed
  write registry/action identity, pure scalar validation and immutable state contracts.
- AI.extension/lib/bimcode_write_runtime.py: GUID resolver, preview builder,
  one-transaction executor, reread and terminal-status handling in API context.
- AI.extension/lib/bimcode_ai_pane/write_coordinator.py: approval state machine,
  TaskDialog, dedicated handler, admission and resolution-only pending callback.
- BIMCode_Provider/write_contracts.py: fixed tool schema/scalar provider validation;
  NO GUID copy and no Revit imports; cross-runtime value/schema parity tests.
- tools/revit/provision_m4a_test_parameter.py: separately invoked provisioning
  utility; imports host constant, never imported by pane/provider/startup.
- tests/test_bimcode_write_contracts.py
- tests/test_bimcode_write_runtime.py
- tests/test_bimcode_write_coordinator.py
- tests/test_bimcode_write_native.ps1

Modified only when later authorized:
- AI.extension/lib/bimcode_ai_pane/lifecycle.py: dedicated event/epoch/admission.
- AI.extension/lib/bimcode_ai_pane/panel.py and BIMCodeAIPane.xaml: explicit write
  opt-in, host-local test path/result and pending resolution control.
- AI.extension/lib/bimcode_ai_pane/provider_bridge.py: separate write protocol variant.
- BIMCode_Provider/tool_protocol.py: fixed write-call/result validation.
- BIMCode_Provider/provider.py: mode-filtered schema and one-tool continuation.

No separate write_registry.py needed for one mapping; keep registry in host contracts.
No edits to the large Workbench script, 13 read-only mappings, headless/composite
runtime, prompt catalog, requirements, config, closed QA handlers or WBSO planned
for the runtime implementation. Existing tests may need additive mode assertions,
but never weaken read-only no-write/exact-mapping protections to accommodate writes.

## 10. Coding order, validation gates and preserved boundaries

1. M4A-0: review this design; implement separately authorized provisioning utility;
   provision/verify disposable fixed-GUID fixture, record native version evidence.
2. M4A-1: pure contracts, exact mapping/value/schema/reason enums; exhaustive tests.
3. M4A-2: read-only deterministic preview; missing/wrong binding/storage/editability,
   null/empty, no-op, bounds and no-transaction probes.
4. M4A-3: confirmation binding/cancel/replay/expiry; lifecycle/selection/model epoch,
   ABA, duplicate subscription/disposal tests.
5. M4A-4: dedicated event/queue/gate and native TaskDialog probes; existing read events
   unchanged; local host preview only, provider integration absent.
6. M4A-5: one transaction + verification, false/throw/Pending/RolledBack/rollback
   failure/mismatch probes; authorized local disposable-model write and Undo tests.
7. M4A-6: provider integration ONLY after deterministic host write path is proven
   locally; never use the AI provider as the transaction/confirmation test harness.
8. M4A-7: full offline/native/static regression, exact 13 read tools and catalog237;
   no-write-in-read-path, one-tool mode isolation, no generated code/network expansion.
9. M4A-8: separately authorized live matrix M4A-01..17 from discovery, plus fixed-GUID
   provisioning idempotency/conflict tests and pending resolution recovery in harness.

All future live cases remain PENDING. No model fixture, provider tool or transaction
has been created now. IDs/hours unchanged. Existing source and WBSO remain untouched.

## 11. References and readiness qualification

This design resolves identities and architecture; READY means ready for reviewed
implementation, not live provisioning complete or runtime safety already validated.
Revit 2025.4 native API/TaskDialog/failure-handling probes remain explicit build gates.

- [R1 Autodesk ExternalDefinitionCreationOptions](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/1cd9e425-23a3-04f8-c130-4d4a799abd13.htm): explicit GUID property; otherwise a random GUID is used. Use fixed identity in the separate provisioning utility.
- [R2 Autodesk Transactions in Events](https://help.autodesk.com/cloudhelp/2014/ENU/Revit/files/GUID-CF185732-A702-452C-90D2-F290A1456DBF.htm): DocumentChanged is read-only and follows commit/Undo/Redo.
- [R3 Autodesk Transaction.Commit](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/32714010-7138-f64f-8fde-a310354448e3.htm): inspect terminal status; pending failure processing forbids new transactions.

M4A_IMPLEMENTATION_DESIGN_READY
