# M2A headless ModelMind execution seam

Baseline: `d25c545e0e4f92d14492f52f04d109bd32f15beb`. M1 remains closed.
M2 is not yet live. This module has no pane integration or automatic execution.

## Caller contract

`execute_headless_modelmind_readonly(action_id, document, uidocument)` is an
internal synchronous backend. Call ONLY inside a supported Revit API command or
callback. M2B must invoke it from `IExternalEventHandler.Execute`; a WPF callback
must only queue a request. Document validity checks do not establish API context.
No thread scheduling, timer, Idling subscription or background API access exists.

Allowed IDs are precisely PIPING-RO-001-A01..A04, HVAC-RO-001-A01..A04 and
ELECTRICAL-RO-001-A01..A04. They resolve against the existing production metadata,
not copied prompts or domain logic: summary, connectors, assignment, QA health.
The execution seam does not resolve mixed specialties; M2B adds conservative
routing using the scalar scope helper documented below.
No Dashboard, Issue Index, export, evidence or mutation entry points are exposed.

## Bootstrap and construction

The facade compiles the trusted local Workbench source once in a private module
with `_MODELMIND_HEADLESS_BOOTSTRAP=True`. It does not register that module in
sys.modules, modify sys.path, set environment flags or import the interactive
Workbench. The cached module begins with doc/uidoc=None.

The narrow guards skip provider imports, CLR/UI imports, agent/settings/catalog
imports, logger initialization, document capture and forms.alert replacement.
Normal execution defaults to false and retains its original startup behavior.
No window, catalog, settings store, agent or provider is constructed headlessly.
The module's private name does not execute the guarded main() entry point.

In headless mode ONLY, the two UI class declarations inherit object instead of
their CLR UI bases. `object.__new__(OllamaAIChat)` is consequently a pure Python
allocation, NOT an unsafe uninitialized CLR Window. __init__ is never called.
Injected instance fields: NONE. The three builders' transitive closure comprises
102 methods plus 17 global helpers. Tests reject any required non-method self
field or dependency on suppressed imports. All existing function bodies remain
unchanged; the public Console handlers/formatters are not called.

## Context and concurrency

One nonblocking lock covers import, validation, evaluation and projection. Nested
or overlapping requests return EXECUTION_BUSY; this does NOT make Revit APIs
thread-safe. Valid document/UIDocument identity is checked before loading.
The private module's prior doc/uidoc are saved, replaced for one call and restored
in finally, including builder/projection failure. No document or worker instance
is cached. Interactive module globals are never rebound.

## Result contract

`ok=True` means execution/projection completed, not that QA is green. Original
classification, reason_code, summaries, table ordering, QA checks and warning
fields are preserved verbatim. `specialty` identifies the explicitly requested
pack. Raw scope/element/connector/system records are omitted, not recomputed.
Tables already carry scalar element IDs. Raw ElementId objects are rejected.

Exact built-in None/bool/int/long/finite-float/str/unicode/list/dict values are
copied recursively; production tuples become lists. Unknown objects are never
stringified. Transport bounds: 100,000 nodes, depth 16, 2,000,000 total string
characters, 8,192 characters per string, 64-bit integer magnitude. These are
serialization limits, not modified production processing/display caps. Exceeding
a bound fails explicitly with RESULT_PROJECTION_FAILED, never silent truncation
or a changed domain classification. Output contains no exception/traceback.

Infrastructure failures return `ok=False`, action_id and error_code only:
UNSUPPORTED_ACTION, EXECUTION_BUSY, INVALID_DOCUMENT_CONTEXT,
ACTION_METADATA_MISMATCH, RESULT_PROJECTION_FAILED or HEADLESS_EXECUTION_FAILED.
These are facade errors, not new ModelMind classifications. M2B must present them
as execution errors rather than model/QA findings.

## Validation and remaining live work

Run `python -B tests/test_modelmind_headless.py` and
`python -B tests/test_bimcode_ai_pane.py`. Tests exercise real builder code using
host fakes (empty/supported/unsupported), context cleanup, overlap rejection,
projection, import isolation, dependency closure, catalog and normal-mode AST
equivalence. Fake host evidence is not live Revit evidence.

Before claiming runtime parity, perform a normal Workbench launch/provider-status
and specialty-command regression in Revit, then headless-vs-Console comparison
from the future M2B ExternalEvent path for supported Pipe, Duct and Electrical
device/equipment selections. Verify document switching, error recovery and no
global alert/UI changes. No pane tools or live test execution belong to M2A.

## M2B consumer / routing addition

`resolve_headless_modelmind_specialty(document, uidocument)` reuses the existing
Piping/HVAC scope-kind methods and Electrical scope/profile method under the same
lock and scoped context. It returns only selected count, unsupported count and
supported specialty names; failures are controlled scalar errors. No M2A
execution/projection function or closed semantic body was changed for M2B.

`bimcode_ai_pane/tools.py` maps selection.summary/connectors/system_assignment/
qa_health to the chosen specialty's A01/A02/A03/A04. Empty/unsupported-only and
supported-plus-unsupported selections return NOT_READY without builder execution.
Multiple supported specialties return MIXED_SPECIALTY_REVIEW. Mixed electrical
device/equipment selections remain one specialty, using existing closed behavior.
Unreadable/unresolved references fail closed. No selected element is discarded.

WPF clicks queue scalar request_id/tool_name/action_id (initially None), cached
document identity and lifecycle generation. Only the dedicated ModelMind
ExternalEvent.Execute resolves the selection and invokes the established M2A
execute facade. Selection is intentionally read at execution, not captured at
click time. Document identity uses runtime hash/title/path plus generation;
every activation/open/create/close increments generation. View-only transitions
also reject pending requests conservatively; switch-away-and-back cannot retarget
them. No Document/UIDocument/element is retained in pending work. Refresh remains
separate; no additional lifecycle subscriptions exist.

All four controls disable for pending/running work and restore after completion,
failure or Raise rejection. M2A's execution lock remains authoritative. Production
classifications are retained (QA YELLOW is completed/OK transport, not green QA).
Rendering revalidates scalar projection and displays at most 16,000 characters,
30 summary lines, 20 warnings, 12 tables and 40 total table rows, with omission
notices. These are pane presentation limits only; production caps/results remain
unchanged. Send stays disabled. No live validation is claimed.
