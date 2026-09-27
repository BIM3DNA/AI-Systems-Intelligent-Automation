# M4A implementation design - parameter provisioning and write contract

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
