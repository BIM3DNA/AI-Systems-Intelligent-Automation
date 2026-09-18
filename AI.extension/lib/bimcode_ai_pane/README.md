# BIMCODE-REVIT-AI-PANE-001 / Milestone 1

Implemented UI shell and live read-only context. Static validation is separate
from live Revit acceptance. Verdict: M1_READY_FOR_CLOSURE_WITH_NONBLOCKING_GAPS.
Runtime defects: NONE REMAINING. M1 source-control status: UNCOMMITTED / UNPUSHED;
closure PENDING REVIEW / COMMIT / PUSH. M2 has not started.
Baseline: `45bf742fd45ca83ce4d65319116113541d299a52` on clean synchronized main.

## Installed target and registration

Validated target: Revit 2025.4, pyRevit `5.3.1.25308+1659` at
`C:\Users\Korisnik\AppData\Roaming\pyRevit-Master`. Its loader runs extension
`startup.py` in a persistent IronPython engine and includes extension `lib`.
Existing AI.extension has one unrelated import-command hook and no prior startup
script or dockable pane. That hook and the Workbench script are unchanged.

Stable panel UUID: `aa6b23d4-f8e3-4b2f-9ad7-de9e05bfb5e4`.

The panel subclasses `forms.WPFPanel`. The installed public
`forms.register_dockable_panel` sets the content and default visibility but
does not assign InitialState. A small public Revit `IDockablePaneProvider`
therefore sets `DockablePaneState.DockPosition = DockPosition.Right` and
`VisibleByDefault = True`, then startup uses `UIApplication.RegisterDockablePane`.
No pyRevit patch, private-provider override, or C# add-in is needed.

`PaneIsRegistered` guards registration even before the pane's visual host is
created (the installed `forms.is_registered_dockable_panel` uses PaneExists).
A namespaced pyRevit session environment value retains one session/provider/
panel, exact event delegates, and read-only ExternalEvent. Repeated startup
reuses it. Session/registration mismatch reports a restart requirement; it does
not register a second pane. Session objects hold no Document/View/ElementId.

Startup attempts Show only with a valid active document; otherwise Show remains
pending. DocumentOpened/DocumentCreated/DocumentClosed reset show_pending.
ViewActivated or queued read-only refresh obtains the existing pane by stable
UUID and calls Show; success clears pending. No reconstruction or registration
occurs on these paths. This fixes LIVE-PANE-06: the flag previously stayed false
after the first Show and the pane stayed hidden after closing/reopening projects.
No timers or Idling polling are used. The new AI > Dev > BIMCode AI
button uses `forms.open_dockable_panel` and never registers. A successful initial
Show is not repeated on every view change, so closing the pane is respected.
Revit may restore a user's saved position after the first registration; Right
is the initial position, not a forced override of the user's saved layout.

## Context and API boundaries

ViewActivated refreshes the active document/view snapshot in Revit's callback.
DocumentOpened/DocumentCreated queue refresh because activation may follow those
events. DocumentClosed clears the displayed snapshot immediately and queues a
fresh read without dereferencing the closed document. No-document defaults are
No document / Unavailable / 0 elements. A failed selection read is displayed as
Unavailable rather than a false zero.

Selection updates automatically through UIApplication.SelectionChanged on the
installed Revit 2025.4 target. The handler reads only
SelectionChangedEventArgs.GetSelectedElements().Count and directly updates the
Selection text on Revit's UI thread. It retains no event args or ElementIds and
does not queue an ExternalEvent, reread document/view context, or change status.
Unavailable reads display Unavailable; absent controls or a closing host are
tolerated. Hidden panes still receive the update without being shown.

The strongly retained delegate uses the existing subscription list and rollback
cleanup. Registration is capability-guarded; unsupported runtimes retain manual
refresh. Repeated subscribe/start/show does not add another selection handler.
Restart Revit once to load this refinement: reloading pyRevit intentionally keeps
the original session/panel alive and does not replace an older implementation.

Refresh context remains the explicit recovery path. A WPF click only raises a
minimal read-only ExternalEvent; Execute
reads ActiveUIDocument, Title, ActiveView Name/ViewType, and selected-ID Count on
the Revit API thread. It has no mutation dispatch or arbitrary execution path.
UI rendering receives scalar values only. No background API access, whole-model
enumeration, QA invocation, selection change, view change, transaction, export,
workflow advancement, or evidence write is introduced.

Send is disabled; AI connection is not configured. Input is transient WPF text
only. No network client, credential handling, persistence, or OpenAI call exists.
ChatGPT/Codex subscription billing and OpenAI API billing are separate; no API
credential or billing setup is needed for M1.

## Validation

Run `python -B tests/test_bimcode_ai_pane.py` from the repository root for offline
context/lifecycle probes. These stubs do not prove Revit event binding or docking.
Parse all new Python and XAML, load the Page through Windows WPF XamlReader,
check prohibited API/import boundaries, check catalog count 237, and compare
existing tracked runtime content to baseline. Do not run unrelated network tests.

2026-09-17 final static results: 15 offline tests PASS; seven Python files pass
AST, py_compile (temporary outputs removed), and tabnanny; XML parsing and Windows WPF
XamlReader Page loading PASS; catalog remains 237; all existing tracked runtime
and hook content unchanged. The Workbench LF SHA-256 remains
`B9B619A369CA14C8854A335987E47E96075761D6A93A26D1AC872E1407CA753B`.
No Revit live test was executed by the implementation task.

Authoritative user-reported live evidence:

| Case | Result | Evidence |
| --- | --- | --- |
| LIVE-PANE-01 | PASS | Registered and appeared |
| LIVE-PANE-02 | PASS | Right docking, resizing and normal interaction stable |
| LIVE-PANE-03 | PASS | Project opening updated Document / Active View |
| LIVE-PANE-04 | PASS | View activation updated Active View / View Type |
| LIVE-PANE-05 | PASS | Explicit Refresh updated selection count |
| LIVE-PANE-05B | PASS | Automatic 0 -> 1 -> multiple -> 0 without Refresh |
| LIVE-PANE-06 | INITIAL FAIL / FIXED | show_pending was not reset after first Show |
| LIVE-PANE-06B | PASS AFTER FIX | Repeated close-all/reopen and another project restored pane and context; no manual ribbon click or duplicate pane |
| LIVE-PANE-07 | PASS | Input visible; Send disabled; AI connection is not enabled in Milestone 1 |

LIVE-PANE-08 was not supplied and is not claimed. Source inspection and static
probes establish the no-mutation/no-network boundary; do not invent a live result.

Nonblocking gaps: exact visible no-document wording/status; deliberate user hide
then view switch; Revit saved docking position; live pyRevit reload; additional
already-open project tab switching; workshared and family document context.
Linked-model inspection and the M2-M8 integrations below are outside M1.

Pre-closure-documentation audit delta: 11 files, +763/-1 (runtime/UI/configuration
8 files +356; tests 1 file +268; docs 2 files +139/-1). That is a historical audit
snapshot; subsequent closure documentation enlarges the final proposed scope.
Existing Workbench runtime and prompt catalog remain unchanged. Catalog Git/LF
SHA-256: `55A58E3B6E1A67D833B91B5DFC5BAC883955B0352BB8BFA862AC3C32917FDB94`;
Git object: `aa0bf1fc19ba2c5ceb7afe24c3a0749f80288b57`.
Project-local Evidence / Daily Log / KC IDs and hours: PENDING; the local sequence
is not unambiguous. No new KC note or prompt asset is allocated.

## Deferred milestones

- M2: pane to ModelMind read-only tool bridge (selection, connectors, assignment,
  QA health, active-view context). Revit reads must retain a valid API boundary.
- M3: OpenAI Responses API with structured tool/function calls, externalized
  model configuration (proposed target `gpt-6-astra`, to verify then), credentials,
  and billing setup. No provider implementation in M1.
- M4: planner to ModelMind read-only tools.
- M5: first deterministic mutation tool, potentially Connect Pipes, with plan,
  confirmation, execute, observe, and post-action QA. Requires a separately
  designed safe Revit execution boundary; M1's refresh event is not that dispatcher.
- M6: planner to deterministic command library to ModelMind verification loop.
- M7: vision / AI Image Scanner integration.
- M8: family generator integration.

Streaming, WebSocket, async tools, autonomous loops, conversation persistence,
tool registries, approval flows, mutation dispatcher, and audit integration are
deferred. No existing ModelMind semantics or catalog metadata are changed.
# M3A current checkpoint (2026-09-18)

M1/M2 remain closed. M3A adds a separate text-only Python 3 provider process;
the prior disabled-Send/no-network descriptions above describe M1/M2 history.
Local-only configuration readiness gates Send; provider work never uses the M2
ExternalEvent. Lifecycle, deterministic tools, themes, bounded renderer and Find
are preserved. User-reported LIVE-M3A-01..04 are COVERED / PASS. Final audit verdict:
M3A_READY_FOR_CLOSURE_WITH_NONBLOCKING_GAPS. Source-control closure is PENDING;
implementation/documentation remain unstaged, uncommitted and unpushed. M3B not started.
See `BIMCode_Provider/README.md` at repository root for the authoritative M3A
configuration/protocol/security contract, validation evidence and live procedure.
