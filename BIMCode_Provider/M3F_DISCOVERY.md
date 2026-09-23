# M3F-DISC-001 - Multi-specialty orchestration discovery

2026-09-23. DISCOVERY COMPLETE / IMPLEMENTATION NOT STARTED.
Ready for implementation design, not authorization to implement.
No runtime/test/tool/catalog/provider-registry changes, authenticated requests or
Revit live tests. No Evidence/Daily Log/KC IDs, hours or commits allocated.

## 1. Verified baseline

Branch main; HEAD and origin/main c281b0c85d9254072db390843b8c107713a606b1,
subject `docs(wbso): close M3E live validation`, parent
f7fde73ca95b5b316f410ff5fee75aa2b3349b8a. Ahead/behind 0/0. Starting
status --short empty; worktree clean; staged/modified/untracked files none.
This is the Git-verified M3E closure, notwithstanding preserved pre-commit audit
wording in historical documentation. Implementation anchor:
ee2b8346dddce8e7532ab7c0adc244947eeaf719.

## 2. Current source inventory

Host registry: AI.extension/lib/bimcode_ai_pane/ai_tool_registry.py, TOOLS/ACTIONS.
Sidecar mappings: BIMCode_Provider/tool_protocol.py, ACTIONS.
Provider schema declarations: BIMCode_Provider/provider.py, TOOLS.
Exactly twelve current tools, strict empty-object arguments:

| Tool | Fixed action |
| --- | --- |
| summarize_selected_pipes | PIPING-RO-001-A01 |
| inspect_selected_pipe_connectors | PIPING-RO-001-A02 |
| inspect_selected_pipe_system_assignment | PIPING-RO-001-A03 |
| inspect_selected_pipe_qa_health | PIPING-RO-001-A04 |
| summarize_selected_ducts | HVAC-RO-001-A01 |
| inspect_selected_duct_connectors | HVAC-RO-001-A02 |
| inspect_selected_duct_system_assignment | HVAC-RO-001-A03 |
| inspect_selected_duct_qa_health | HVAC-RO-001-A04 |
| summarize_selected_electrical_elements | ELECTRICAL-RO-001-A01 |
| inspect_selected_electrical_connectors | ELECTRICAL-RO-001-A02 |
| inspect_selected_electrical_circuit_assignment | ELECTRICAL-RO-001-A03 |
| inspect_selected_electrical_qa_health | ELECTRICAL-RO-001-A04 |

No composite tool currently exists. No mutation, generic command, AutoCAD or ScanAI
tool, arbitrary model-selected action ID or autonomous tool loop is allowed.

### Selection routing (AI path versus deterministic pane buttons)

AI Coordinator.execute_approved in ai_tool.py calls
modelmind_headless.resolve_headless_modelmind_specialty(document, uidocument).
Input is live Document/UIDocument in a valid Revit callback, not scalar IDs from AI.
The resolver acquires a nonblocking process-local lock, scopes isolated backend
doc/uidoc globals, iterates Selection.GetElementIds and resolves Document.GetElement.
Closed predicates, in order: _piping_ro_001_scope_kind == SUPPORTED_PIPE;
_hvac_ro_001_scope_kind == SUPPORTED_DUCT; _electrical_ro_001_scope_kind profile
DEVICE_PROFILE or EQUIPMENT_PROFILE. Other resolved elements increment unsupported.
Success shape: {ok: true, specialties: sorted unique strings, selected_count: int,
unsupported_count: int}. It does NOT return per-specialty counts/IDs or a snapshot.
Failures: {ok: false, action_id: null, error_code: EXECUTION_BUSY,
INVALID_DOCUMENT_CONTEXT or SELECTION_UNREADABLE}. Unresolved IDs and read exceptions
fail the entire resolver; they are not silently counted as ordinary unsupported.

| Selection | Resolver output specialties | Current AI behavior |
| --- | --- | --- |
| Pipe only | [PIPING] | Matching fixed Piping tool permitted |
| Duct only | [HVAC] | Matching fixed HVAC tool permitted |
| Electrical fixtures/equipment | [ELECTRICAL] | Matching Electrical tool permitted |
| Pipe + Duct | [HVAC, PIPING] | AI_TOOL_NOT_ALLOWED |
| Pipe + Electrical | [ELECTRICAL, PIPING] | AI_TOOL_NOT_ALLOWED |
| Duct + Electrical | [ELECTRICAL, HVAC] | AI_TOOL_NOT_ALLOWED |
| All three | [ELECTRICAL, HVAC, PIPING] | AI_TOOL_NOT_ALLOWED |
| Unsupported only | [], unsupported_count > 0 | AI_TOOL_NOT_ALLOWED |
| Supported + unsupported | Supported specialty set plus unsupported count | One specialty: builder receives entire selection; multiple: rejected |
| Empty | [], selected_count=0, unsupported_count=0 | Matching requested builder runs, preserving closed NOT_READY result |
| Unresolved | ok=false / SELECTION_UNREADABLE | MODELMIND_NOT_READY; no builder |

Distinct path: tools.py ModelMindToolBridge.execute serves deterministic M2 pane
buttons, not AI Coordinator. It returns NOT_READY/NO_ELEMENTS_SELECTED for empty;
NOT_READY/NO_SUPPORTED_SELECTED_ELEMENTS for unsupported-only;
MIXED_SPECIALTY_REVIEW/MIXED_SUPPORTED_SPECIALTIES for multiple specialties; and
NOT_READY/SUPPORTED_AND_UNSUPPORTED_SELECTION for one supported plus unsupported.
Do not conflate those strings with the resolver shape or change this button policy
as a side effect of a future AI composite implementation.

### Current execution guards

- provider.py tool_response rejects more than one function_call, or any function
  call during operation tool_result, with AI_TOOL_LOOP_LIMIT; rejects unknown names,
  invalid arguments, async/namespaced/non-direct calls. send sets
  parallel_tool_calls=False; final continuation tools=[] / tool_choice=none.
- tool_protocol.validate_call checks exact fields, literal allowlist, empty dict,
  bounded call_id. validate_request correlates fixed action and specialty, bounded
  result and provider response/model state. It is not a persistent execution ledger.
- provider_bridge.decode_tool validates the host envelope. ai_tool.Coordinator.begin
  stores request_id, document_identity, context_generation, selection_generation,
  used=False and disallows another active turn/pane request. queue checks request
  identity, consumes used before raising the event; another call gets LOOP_LIMIT.
- execute_approved consumes pending before work; compares document_key and both
  generations. document_key in tools.py uses hash/title/path supplemented by lifecycle
  generation (not persistent cross-session identity). No-document fails closed.
- lifecycle.py ModelMindReadOnlyHandler.Execute invokes the coordinator in the
  existing M2 event; PaneSession.raise_ai_event uses that event. Lifecycle and native
  selection events update generations. A lock does not make background API use safe.
- Initial provider turn store=True; continuation previous_response_id plus call_id
  and function_call_output; final store=False, tools=[], tool_choice=none.
  No local conversation database. Preserve all of these controls.

## 3. Problem and architecture options

For one Pipe, one Duct and one Electrical Equipment, a mixed Summary must retain
three distinct deterministic reports, but yield one bounded, auditable answer.
The provider must not choose sub-action lists, filter Revit data or interpret QA.

| Option | Safety/authority/auditability | Complexity and tradeoffs |
| --- | --- | --- |
| A: named deterministic composite action | One provider call; explicit stable composite and child provenance | Good reusable domain contract, but unnecessary catalog/Workbench surface expansion if treated as a new public command; snapshot seam still required |
| B: one AI tool, fixed host fan-out | One request/event; host chooses only present specialties and A01s | Preferred integration; small bounded handler, reuses builders; needs snapshot and composite transport/provenance |
| C: provider multi-tool calls | Host can validate names but provider controls decomposition/order/coverage | Weakens one-call guard, more partial/stale cases and payloads; reject for first scope |
| D: sequential continuation loop | Provider gains adaptive repeated execution authority | Extra round trips, drift/retry/termination complexity; conflicts with second-call guard; reject |
| E: deterministic host planner | Same as B when it is a literal three-entry plan | Useful internal name, not a general planning engine; dynamic planning adds no value for Summary |

Recommendation: B with a tiny E-style fixed planner and A-style composite action
identity. These are layers, not three competing execution architectures.
One provider call, one host request, one existing ExternalEvent; deterministic
order PIPING, HVAC, ELECTRICAL; zero or one invocation per present specialty, max3.
No transactions or model mutation in any option's allowed scope. No nested event,
parallel API call, retry or provider-selected plan. Domain code is reused, not copied.
Compared with C/D, host owns coverage, order, bounds, error policy and provenance.
Extensibility requires a reviewed fixed mapping change, never discovery of actions.

Important policy change: one *specialty builder* execution is no longer true for
the new composite. Preserve one top-level execution token; explicitly permit up to
three fixed internal A01 evaluations for that token only. Do not mislabel fan-out
as a single underlying action. Existing twelve tool behaviors remain unchanged.

## 4. Proposed first scope and minimal execution seam

M3F-A01: Summary only. Proposed feature MEP-MULTI-RO-001, action
MEP-MULTI-RO-001-A01, tool summarize_selected_mep_elements, strict empty schema.
Proposed total thirteen AI tools. No mixed Connectors, Assignment or QA; no new
categories, linked traversal, catalog routes, workflows, export eligibility or
evidence advancement. An internal action identity need not add a catalog entry.
Single-specialty prompts may continue using their existing tool. If the composite
is chosen for one specialty, wrap its unchanged A01 facts with explicit provenance.

Current execute_headless_modelmind_readonly cannot be reused unchanged to satisfy
the snapshot requirement. Each of _piping_ro_001_build_data (script.py:38292),
_hvac_ro_001_build_data (40256), _electrical_ro_001_build_data (42780 onward) calls
_mep_ro_001_selection_snapshot (36477), which reads the full current UI selection,
sorts IDs, resolves them, and constructs generic records for every resolved item.
Calling each builder on the full mixed selection introduces foreign-specialty
unsupported records, misleading partial scope and repeated work. Never temporarily
call SetElementIds to supply a subset; never spoof UIDocument/Selection objects.

Minimal proposed refactor for design review:

1. Keep existing builder signatures as wrappers with their existing snapshot call.
   Extract each remaining body mechanically into a private build-from-snapshot
   core. Existing wrapper paths, outputs and semantics must remain identical.
2. Composite headless entry captures IDs once inside the existing event, checks
   bounds, resolves/classifies once with closed predicates and builds one generic
   snapshot. Partition records and selected_ids/selected_id_texts consistently into
   disjoint specialty snapshots. No raw API object may leave the callback.
3. Each core receives its explicit subset snapshot, with no further selection read.
   Counts are subset-relative, labeled accordingly; global counts live on composite.
   Audit transitive calls before implementation to ensure no remaining selection
   rereads or mutations; do not treat discovery inspection as that regression proof.
4. Hold _EXECUTION_LOCK once for the whole composite and _document_context once;
   invoke the private cores, not the public locking executor from inside the lock.
   Public nested/concurrent calls still return EXECUTION_BUSY. Do not change to a
   reentrant lock just to permit recursion. Alternative sequential public calls
   release/reacquire the lock and still lack snapshot isolation: not recommended.
5. Serialize/copy each child's existing presentation fields before leaving context;
   restore isolated module doc/uidoc in finally, release lock and discard raw records.

The backend cache is initialized once; object.__new__ bypasses UI initialization.
Its document globals change temporarily, not the model or interactive Workbench.
Current exception paths return RESULT_PROJECTION_FAILED / HEADLESS_EXECUTION_FAILED
without exporting traces. Keep sanitized per-child error codes. Current report IDs
are timestamp-based, not unique request identities: retain child report IDs but add
host request_id + child ordinal for correlation; never infer identity from time.
No new logging of prompts, credentials or raw documents. Domain side-effect-free
reuse must be protected with closure tests, not assumed from the method name.

## 5. Proposed deterministic rules and failure precedence

These are proposed, not current runtime classifications. Four top-level states:

| Classification | Condition / primary reason |
| --- | --- |
| MEP_MULTI_SELECTION_NOT_READY | No valid document, empty, unsupported-only, unresolvable snapshot, or selection admission cap; reasons NO_VALID_DOCUMENT_CONTEXT / NO_ELEMENTS_SELECTED / NO_SUPPORTED_SELECTED_ELEMENTS / SELECTION_UNREADABLE / SELECTION_LIMIT_EXCEEDED |
| MEP_MULTI_SELECTION_FAILED | Stale context, composite infrastructure failure or no usable child result; STALE_CONTEXT / COMPOSITE_EXECUTION_FAILED / NO_USABLE_SPECIALTY_RESULT |
| MEP_MULTI_SELECTION_SUMMARY_PARTIAL | At least one usable child plus any failed/not-ready/partial child, unsupported items or processing omissions; deterministic reason priority below |
| MEP_MULTI_SELECTION_SUMMARY_OK | All present children completed usable non-partial A01s, no unsupported scope or processing omissions; COMPLETE |

No separate UNSUPPORTED class: unsupported-only is NOT_READY with explicit reason.
ok means envelope/execution infrastructure completed, not model health: true for
OK/PARTIAL/NOT_READY domain envelopes, false for FAILED infrastructure/stale results.
Usable child = executor completed and classification is neither FAILED nor NOT_READY;
PARTIAL child can be usable. Preserve original child classification and reason always.
Precedence: stale/context-integrity failure overrides all and suppresses child facts;
admission NOT_READY prevents all execution; no usable children => FAILED; otherwise
PARTIAL reasons ordered SUBACTION_FAILED, SUBACTION_NOT_READY, SUBACTION_PARTIAL,
PROCESSING_CAP_REACHED, UNSUPPORTED_ELEMENTS_PRESENT. Store all reasons separately.

Pipe/Duct/Electrical-only uses just that A01; any of the four mixed combinations
uses exactly the present A01s. Electrical device+equipment is one specialty.
Supported+unsupported: recommend PARTIAL with separate category/count/ID scope,
not foreign items injected into every child. Fail-closed alternative is simpler but
loses safe supported results and diverges from existing AI single-specialty tolerance.
Unresolved references: recommend fail closed before execution for first scope, in
line with current resolver; do not silently drop IDs. Partial unresolved support
can be reviewed later. Distinguish null resolution from an unreadable property on a
resolved supported element: the latter remains authoritative child partial data.

Piping/HVAC success + Electrical failure: retain successful children, Electrical
failure entry, PARTIAL/SUBACTION_FAILED, no retry or second provider call.
Processing cap => explicit omitted records and PARTIAL; child domain caps unchanged.
Display/projection omissions alone do NOT change domain classification or imply
failed evaluation. Separate transport_truncated from partial and processing omissions.
If mandatory core cannot fit, fail that child with RESULT_PROJECTION_FAILED; if no
usable children remain fail composite, never return a blank healthy summary.

Before snapshot and before/after each child, validate document identity, lifecycle,
selection generation and request identity; validate again before publishing results.
No yields, modal calls, message pumping or async API use inside the event. Ordinary UI
selection changes should not interleave synchronous work, but do not rely on that
as the only guard. Recheck selected ID set at end for integrity (not a new evaluation
snapshot). On detected drift discard the whole composite, no partial stale answer.
Document/model edits not represented by existing generations remain a design risk:
same callback/no pumping constrains exposure, but is not a transaction snapshot.

## 6. Proposed scalar result contract and provenance

All fields are built-in JSON-safe scalars/lists/maps; no Element/Document/ElementId
objects, provider instructions or exception traces. A host-only request record owns
identity/generation tokens; do not transmit paths or document identity keys.

Top level: schema_version=1, ok, action_id=MEP-MULTI-RO-001-A01,
feature_id=MEP-MULTI-RO-001, request_id, report_id, timestamp, document_title,
active_view_name, active_view_type, classification, reason_code, reasons[],
selected_reference_count, resolved_selected_count, supported_specialty_count,
supported_count, unsupported_count, unresolved_count, partial, warnings[],
warnings_total, transport_truncated, transport_omissions, specialties, unsupported_scope.

specialties has exactly PIPING/HVAC/ELECTRICAL keys, each with present(bool),
selected_count, supported_count, processed_count, processing_omitted_count,
action_id (null if absent), execution_state (NOT_PRESENT/COMPLETED/FAILED/NOT_READY),
classification, reason_code, error_code, child_report_id, child_ordinal,
bounded_projection, transport_omissions, warnings[], warnings_total.
Absent specialties are not failures; no invented zero-issue/healthy status.
Counts come from host partition or existing builder outputs; where a closed result
does not expose a metric, use null with availability reason, not parsed prose or
inferred zero. Design must choose any additive typed metadata seam explicitly.

unsupported_scope: categories[{category_id, category_name, count}],
unresolved_references[{id, reason}], unsupported_ids[], reason_code,
omitted_category_count, omitted_id_count. Stable category IDs distinguish duplicate
names. Snapshot identity: selected = resolved + unresolved; resolved = supported +
unsupported; supported = sum specialty selected counts. No double counting devices
and equipment as separate specialties. For unreadable initial enumeration counts
are null, not asserted complete. Never sum unlike specialty quantities or QA counts.

Provider receives the bounded composite with child facts/classifications/warnings,
unsupported coverage and omissions; cannot recompute QA, assignment, connectivity,
cross-specialty relations or merge conflicting semantics. Existing compact() and
tool_protocol SPECIALTIES assumptions need an explicit composite branch, not a
generic action/specialty bypass. Composite output must match the fixed tool identity.

UI label: Selected MEP Elements Summary; show composite action/classification/reason
AND executed sub-action IDs with child classifications. Show failed/skipped children
and transport omissions visibly, not only in hidden metadata. Reuse provider_ui.py
and panel.py provenance flow; do not let provider prose replace host-generated badges.
Keep the existing 16,000-character / bounded-block presentation and Find behavior.

## 7. Bounds and performance

Current production: Piping200, HVAC200, Electrical200 supported processing caps;
element-row limits200 each; connector rows400 each; per-element connectors8/8/20,
Electrical systems20. Selection snapshot generic-record work precedes specialty
processing caps: 200 is NOT a bound on selected-ID enumeration or generic reads.
Current headless project_value: 100,000 nodes, depth16, total text2,000,000 chars,
per string8192, finite floats and <=64-bit integers. Current AI compact: 30 entries
per check/warning list, twelve tables, forty shared rows, serialized result80,000
chars. Sidecar request120,000 chars. These are character, not token budgets.
Three max child AI payloads approach240,000 chars plus envelope: not acceptable
under the existing80,000 result limit. No measured composite timing/token estimate
exists; sequential latency roughly sums child work, but no millisecond promise.

Conservative design recommendations (not runtime changes):

- Admit at most600 selected IDs before generic record building; over limit fail
  NOT_READY rather than claim exhaustive scope. Existing per-specialty200 caps stay.
- Max3 child attempts, deterministic order; total result serialized <=80,000 chars.
  Budget <=20,000 per child and <=20,000 composite overhead, verified after escaping.
  Up to12 tables/40 rows PER composite, fairly allocated among present specialties,
  not three independent40-row budgets. Preserve core summaries and reason metadata;
  remove whole optional rows first with exact omissions; do not truncate scalar facts.
- Max30 warnings per child, max30 composite warnings; preserve totals and omitted
  counts. Bound unsupported category/ID lists to30 each with exact remainder counts.
- Advisory2-second checkpoint between child calls: do not start another after budget
  exhausted; mark it FAILED/TIME_BUDGET_EXCEEDED and return partial if usable results
  exist. This cannot interrupt an in-flight API read and is not a hard UI deadline.
  Validate whether this budget is practical before implementation acceptance.
- Report snapshot/partition/each-child/composition elapsed time and respective
  processed counts; no single misleading denominator. No timers/polling added.

## 8. Future implementation tests and live plan (NOT EXECUTED)

Static tests must preserve the existing261-test baseline and add:

- Exact existing12 mappings unchanged plus only fixed composite A01 =>13; empty
  schemas, reject action/specialty/ID lists and all existing protocol failures.
- All single/mixed combinations, both Electrical profiles, supported+unsupported,
  unsupported-only, empty, unresolved, invalid document, cap boundaries599/600/601.
- One provider call/event/request token, max3 distinct A01s; no retry, nested event,
  public-lock recursion, background API, UI selection mutation or provider plan.
- One selection evaluation snapshot; partition count conservation, stable order,
  no cross-specialty contamination; wrapper/core equivalence for all12 old actions.
- Guard changes before execution/between children/before publication, switch away
  and back, same-document reactivation, request mismatch, lock contention and cleanup.
- Each child failure permutation, all fail, partial/unreadable/capped, absent child,
  bounded transport, Unicode escaping, zero remaining row budget, oversized core,
  warning retention/counts, display-only truncation without false domain PARTIAL.
- No stale facts published; globals/lock restored after exceptions; no logging or
  raw object transport. Child report-ID collision cannot confuse request correlation.
- Existing Piping/HVAC/Electrical suites, provider continuation, native host/WPF/
  theme/Find, Workbench AST/source equivalence except reviewed snapshot extraction,
  catalog237, manifests, mutation/network/credential boundary regressions.

| Future case | Required evidence | State |
| --- | --- | --- |
| LIVE-M3F-01 | Pipe-only composite and existing A01 parity | PENDING |
| LIVE-M3F-02 | Duct-only composite and existing A01 parity | PENDING |
| LIVE-M3F-03 | Electrical DEVICE_PROFILE A01 parity | PENDING |
| LIVE-M3F-04 | Electrical EQUIPMENT_PROFILE A01 parity | PENDING |
| LIVE-M3F-05 | Pipe+Duct summary, two child provenances | PENDING |
| LIVE-M3F-06 | Pipe+Electrical summary | PENDING |
| LIVE-M3F-07 | Duct+Electrical summary | PENDING |
| LIVE-M3F-08 | All three summary, three exact child results | PENDING |
| LIVE-M3F-09 | Supported+unsupported => explicit partial scope | PENDING |
| LIVE-M3F-10 | Unsupported-only => NOT_READY, no child | PENDING |
| LIVE-M3F-11 | General MEP question => no tool | PENDING |
| LIVE-M3F-12 | Mutation request => no mutation; no mutation tool | PENDING |

Use 'Summarize the selected MEP elements' for summary cases. Compare each child
against direct A01 on that specialty subset as manual fixture setup, then restore
the mixed selection; the runtime must never change selection. Record doc/view/IDs,
exact counts, classification/reason, omission and latency evidence, event/attempt
counts, provenance, unchanged selection/model/view. Add empty-selection live case
and practical large-selection/transport tests; unresolved/stale/forced-failure
coverage may be synthetic rather than corrupting a model or paying for error tests.

## 9. R&D uncertainties and next design gate

Technical uncertainties: exact wrapper/core equivalence; completeness and stability
of one partitioned snapshot across heterogeneous reads; partial-result policy that
does not imply success for absent/failed specialties; fair bounded transport without
losing decisive evidence; UI latency at admitted bounds; auditable child provenance
under one provider execution token. Investigate with deterministic fixtures, source
closure tests, fault injection and later measured live runs. These are technical
questions, not fabricated WBSO eligibility claims, results, IDs or hours.

Likely future files: modelmind_headless.py and its contract; script.py only for
reviewed snapshot/core extraction; new host composite module; ai_tool.py,
ai_tool_registry.py, provider_bridge.py/provider_ui.py/panel.py as required by the
fixed envelope/provenance; provider.py/tool_protocol.py; targeted tests/docs.
lifecycle.py event architecture should stay unchanged. Catalog, manifests, existing
QA/domain functions, Dashboard/Issue Index, workflows/export, Context Suggestions
and Visual Preview must remain unchanged. No new provider-registry entry today.

Implementation design must finalize explicit snapshot signatures, typed count
availability, lock ownership, composite envelope validation and budget tests before
coding. Discovery is complete; those are bounded design tasks, not permission to
implement or proof of live performance.
