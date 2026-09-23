# M3D - full HVAC read-only AI tool surface

## 2026-09-23 - M3D final closure audit

Package: BIMCODE-REVIT-AI-PANE-001 / M3D - Full HVAC Read-Only AI Tool Surface.

- IMPLEMENTED
- STATIC VALIDATION PASSED
- LIVE VALIDATION PASSED
- IMPLEMENTATION CHECKPOINT COMMITTED / PUSHED
- PROJECT-LOCAL WBSO CHECKPOINT COMMITTED / PUSHED
- PARTIAL LIVE-VALIDATION CHECKPOINT COMMITTED / PUSHED
- READY FOR FINAL CLOSURE COMMIT
- NOT YET SOURCE-CONTROL CLOSED

M3D_READY_FOR_FINAL_CLOSURE_COMMIT. All seven required live cases PASS, supplied
by the user; no authenticated OpenAI request or live Revit test repeated here.
No package-introduced runtime defect identified. Earlier pending/partial/pre-commit
sections below are historical and superseded. Final documentation is not committed
or pushed; no final source-control closure is claimed.

Git-verified anchors:
- Implementation: `433a3c36540e4ae1637ce2740e2447331ae11b54`,
  `feat(bimcode): add read-only HVAC AI tools`.
- WBSO: `c70a21b070d611f18019ba331b10eeccbb414dff`,
  `docs(wbso): record M3D implementation checkpoint`.
- Partial-live / audit-start HEAD: `aa812925c9d1e5e00bd7be74495212e52763a677`,
  `docs(wbso): record M3D partial live validation`, parent the WBSO SHA above.

At audit start: main HEAD = origin/main = live remote at partial-live SHA; 0/0,
clean, status --short empty, no staged/modified/untracked paths. No runtime/test
changes since implementation. This audit changes documentation only.

| Case | Supplied live evidence | Result |
| --- | --- | --- |
| LIVE-M3D-01 | Duct353895, Project2/{3D}; A01 HVAC_SELECTION_SUMMARY_OK / COMPLETE; Summary parity, explicit bounded omissions | PASS |
| LIVE-M3D-02 | Same Duct; A02 HVAC_CONNECTOR_REPORT_OK / COMPLETE; raw/physical/End2, non-End0, unconnected2, abnormal-End0; exact parity | PASS |
| LIVE-M3D-03 | A03 HVAC_SYSTEM_ASSIGNMENT_OK / COMPLETE; ASSIGNED, Mechanical Supply Air1, Supply Air, type132467, system353896, CONSISTENT | PASS |
| LIVE-M3D-04 | A04 HVAC_QA_HEALTH_YELLOW / COMPLETE; 12 HVAC + 12 generic checks; issues3, partial0; SEL-QA-011=1, HVAC-QA-008=2, HVAC-QA-009=0 | PASS |
| LIVE-M3D-05 | Supply-air purpose question answered directly; no provenance/tool, action, ModelMind execution or model inspection | PASS |
| LIVE-M3D-06 | Electrical Fixture connector request declined with capability explanation; no Piping/HVAC/Electrical action or ModelMind execution | PASS |
| LIVE-M3D-07 | Pipe+Duct request prompted single-specialty clarification; no provenance, Piping/HVAC/ModelMind execution or dual-tool chain | PASS |

Exactly eight fixed strict empty-object tools remain: four Piping + four HVAC.
No caller action ID, Electrical/mutation tool, generic command execution, autonomous
multi-tool loop, AutoCAD or ScanAI. Maximum one execution; unknown/malformed/nonempty/
multiple/second calls fail closed. Existing M2 ExternalEvent and
execute_headless_modelmind_readonly remain the execution boundary; Python3 sidecar
is Revit-API-free. Document/lifecycle/selection/request guards remain active.
Initial store=True; previous_response_id/call_id/function_call_output; final
store=False, tools=[], tool_choice=none. No local conversation database.

No HVAC recomputation: geometry, shape/dimensions/area/volume, slope/vertical state,
assignment, topology/type/flow, insulation/lining, QA classifications/counts/warnings
remain deterministic ModelMind outputs. Projection only bounds transport with
explicit omissions. HVAC-QA-009 remains abnormal physical End count; valid Curve/tap
connectors do not cause false abnormal-End issues. No independent Curve/tap live
retest is claimed. Initial pre-restart AI_TOOL_NOT_ALLOWED resolved on full Revit
restart: stale loaded registry/runtime reload condition, not a confirmed M3D defect.

Final rerun 2026-09-23: 251 Python tests PASS; 46 native probes PASS
(10 process/dispatcher + 4 M3B + 32 eight-tool); six IronPython host compiles PASS;
30 AST/in-memory compile/tabnanny files PASS; native XAML/WPF/theme/Find PASS.
1475 existing Workbench functions source-identical; catalog237 unchanged.
Mutation/network-boundary/exact eight-tool allowlist scans PASS. Credential-pattern
scan: 109 tracked text files, zero findings; previous 107 excluded the then-untracked
M3D document/test file. Pattern scan is not an exhaustive secret proof. No provider
Authorization-header logging; .env.local ignored/untracked and not read. No secret
copied to documentation. pip check and git diff --check PASS.
Evidence ID / Daily Log ID / KC ID / hours: PENDING; none allocated.
Proposed subject: `docs(wbso): close M3D live validation`. No staging/commit/push.

## 2026-09-21 - M3D partial live-validation checkpoint

BIMCODE-REVIT-AI-PANE-001 / M3D - Full HVAC Read-Only AI Tool Surface.

- IMPLEMENTED
- STATIC VALIDATION PASSED
- IMPLEMENTATION CHECKPOINT COMMITTED / PUSHED
- PROJECT-LOCAL WBSO CHECKPOINT COMMITTED / PUSHED
- LIVE VALIDATION IN PROGRESS
- LIVE-M3D-01 PASS
- LIVE-M3D-02 PASS
- LIVE-M3D-03 THROUGH LIVE-M3D-07 PENDING
- NOT CLOSED

User-reported partial live evidence, recorded 2026-09-21; no additional Revit or
authenticated OpenAI tests run by this documentation task. This section supersedes
earlier pending-all/pre-commit statuses, which remain historical below.
Implementation: `433a3c36540e4ae1637ce2740e2447331ae11b54`, subject
`feat(bimcode): add read-only HVAC AI tools`.
Project-local WBSO checkpoint: `c70a21b070d611f18019ba331b10eeccbb414dff`,
subject `docs(wbso): record M3D implementation checkpoint`, parent the implementation.
Before this edit: main HEAD = origin/main = live remote = WBSO checkpoint,
0/0, status --short empty, clean. This new partial-live documentation is not yet
committed/pushed and does not establish final validation or closure readiness.

Project2 / {3D}, one rigid non-placeholder OVAL Duct 353895. A01 Summary and
A02 Connectors passed routing, deterministic parity and read-only behavior using
OpenAI / gpt-6-astra, status COMPLETE. A01 classification HVAC_SELECTION_SUMMARY_OK;
A02 HVAC_CONNECTOR_REPORT_OK; both reason COMPLETE. A01 explicitly disclosed six
omitted selection-scope rows and zero omitted duct records. A02 had two physical
End connectors, zero non-End connectors, zero abnormal-End-count ducts, no warnings,
unreadability, truncation or transport omissions.

Initial A01 AI attempt returned FAILED / AI_TOOL_NOT_ALLOWED / "Requested AI tool
is not available." Revit was still using the previous loaded runtime. Full Revit
restart followed by the same request succeeded. Record as RUNTIME RELOAD / STALE
LOADED REGISTRY CONDITION: persistent Revit/pyRevit had not loaded the new HVAC
registry, per supplied observations; not a confirmed M3D implementation defect.
No runtime correction was made. This straight-duct case is consistent with
HVAC-QA-009 but does NOT independently retest Curve/tap topology.

| Case | Prompt / fixture | Expected / disposition |
| --- | --- | --- |
| LIVE-M3D-01 | Summarize the selected duct. | PASS: A01 Summary parity after full restart |
| LIVE-M3D-02 | Show me the connectors for the selected duct. | PASS: A02 Connectors parity |
| LIVE-M3D-03 | What system is the selected duct assigned to? | NOT STARTED / PENDING: inspect_selected_duct_system_assignment -> HVAC-RO-001-A03; direct parity |
| LIVE-M3D-04 | Check the QA health of the selected duct. | NOT STARTED / PENDING: inspect_selected_duct_qa_health -> HVAC-RO-001-A04; deterministic QA parity |
| LIVE-M3D-05 | What is the purpose of a supply air duct system? | NOT STARTED / PENDING: direct answer, no ModelMind execution |
| LIVE-M3D-06 | Electrical selection: Check the connectors for the selected electrical element. | NOT STARTED / PENDING: no Piping/HVAC/Electrical execution, safe explanation |
| LIVE-M3D-07 | Pipe+Duct: Summarize the selected MEP elements. | NOT STARTED / PENDING: no automatic chain, at most one execution, safe mixed-specialty refusal |

Remaining cases must not be inferred from A01/A02. Keep selection fixed for direct
comparisons; record tool/action, classification/reason, counts, warnings/omissions
and read-only behavior. No further tests performed by this documentation task.

Eight fixed read-only tools remain: four PIPING-RO-001 and four HVAC-RO-001
A01-A04 (complete mappings in provider_registry.md and BIMCode_Provider/M3D.md).
Strict empty-object schemas, maximum one execution, existing M2 ExternalEvent,
execute_headless_modelmind_readonly and stale document/lifecycle/selection/request
guards remain unchanged. Sidecar is Revit-API-free; bounded projections preserve
ModelMind authority. No model mutation, Electrical AI tools, generic action dispatch,
autonomous multi-tool loop, AutoCAD or ScanAI. Evidence ID / Daily Log ID / KC ID /
hours: PENDING; none allocated. No runtime/tests/catalog/manifests changed.

Implementation checkpoint: 2026-09-21. IMPLEMENTED / STATIC VALIDATION PASSED /
IMPLEMENTATION CHECKPOINT COMMITTED / PUSHED / LIVE VALIDATION PENDING / NOT CLOSED.
Verified Git implementation: `433a3c36540e4ae1637ce2740e2447331ae11b54`, parent
`b8e9bed04ce1e1e93c93ac251725e308df352b88`, subject
`feat(bimcode): add read-only HVAC AI tools`; 13 files, +445/-32.
Before this documentation update: main HEAD = origin/main = live remote at that
implementation SHA; ahead/behind 0/0, status --short empty, worktree clean.
This separate project-local WBSO documentation checkpoint awaits review/commit/push.
No authenticated API request or live Revit test performed by this documentation task.
Baseline: main / HEAD / origin/main `b8e9bed04ce1e1e93c93ac251725e308df352b88`,
M3C closure (`docs(wbso): close M3C live validation`), clean and 0/0 before work.

## Fixed surface

Exactly eight tools, four retained Piping tools plus these four HVAC tools:

| Tool | Fixed action | Verified closed canonical prompt |
| --- | --- | --- |
| summarize_selected_ducts | HVAC-RO-001-A01 | show selected ducts summary |
| inspect_selected_duct_connectors | HVAC-RO-001-A02 | show selected duct connectors |
| inspect_selected_duct_system_assignment | HVAC-RO-001-A03 | check selected ducts system assignment |
| inspect_selected_duct_qa_health | HVAC-RO-001-A04 | check selected ducts qa health |

Retained unchanged mappings: summarize_selected_pipes -> PIPING-RO-001-A01;
inspect_selected_pipe_connectors -> A02; inspect_selected_pipe_system_assignment
-> A03; inspect_selected_pipe_qa_health -> A04 (all PIPING-RO-001).
Host labels: Selected Ducts Summary, Selected Duct Connectors, Selected Duct
System Assignment, Selected Duct QA Health. Classification/reason provenance
continues to come from the deterministic result, not model-generated text.

Every schema is strict with parameters
`{"type":"object","properties":{},"required":[],"additionalProperties":false}`.
No caller-provided action ID, element/document ID, specialty, path, code or URL.
Schema contract checked against [official OpenAI function-calling documentation](https://developers.openai.com/api/docs/guides/function-calling).

## Execution and boundaries

Reuse the existing host coordinator, static allowlists, M2 ExternalEvent and
execute_headless_modelmind_readonly. No second execution architecture or generic
dispatch. The existing closed HVAC A01-A04 builders remain authoritative.
Exactly one execution per user request; unknown/malformed/nonempty/multiple/
second/recursive requests fail closed. Stale document, lifecycle, selection and
request guards remain. The provider remains Revit-API-free.

Host verifies the selected specialty matches the fixed action. Pipe+Duct,
Pipe+Electrical, Duct+Electrical and other multi-specialty selections fail closed
with a single-supported-specialty explanation; no filtering or orchestration.
Electrical-only and unsupported-only selections do not execute either specialty.
Empty selection retains the deterministic NOT_READY report. Supported elements
plus ordinary unsupported elements retain the existing closed-builder partial
scope reporting, without filtering the builder's selection.
Natural-language tool choice remains model-driven; instructions prohibit using
Piping/HVAC tools for electrical requests. No keyword router is introduced.
Live refusal and intent selection are pending, not proven by mocked responses.

## Projection and deterministic authority

The existing 80,000-character transport limit, 12-table / 40-total-row budget
and 30-entry list caps remain. Preserve production summary/tables unchanged;
add hvac_checks to the existing field allowlist and disclosed list cap.
A01 retains identity, duct shape/dimensions, length, slope/vertical interpretation,
elevations/level, system and insulation/lining where provided by production.
A02 retains raw/physical counts, End/Curve types, geometry, reciprocal connections,
owner IDs, unreadability and truncation. A03 retains assignment/system metadata,
consistency and contradictions. A04 retains hvac_checks and generic_checks,
issue/partial counts, affected IDs, warnings, classification and reason.
Optional detail omissions are explicit in transport_omissions. Oversized core
evidence fails closed. No domain recomputation or raw API objects are introduced.
HVAC-QA-009 remains physical End connector count: Curve/tap connectors do not
become abnormal End connectors. Production code is untouched.

Continuation remains initial store=True; follow-up previous_response_id + call_id
+ function_call_output, store=False, tools=[], tool_choice=none. No local
conversation database, extra persistence, endpoint or dependency change.
No Electrical/mutation tools, autonomous loop, AutoCAD or ScanAI implementation.

## Static validation

- 251 Python tests PASS: 232 retained tests (scope assertions updated for the
  authorized eight-tool/mixed-selection contract) plus 19 M3D tests.
- 46 native probes PASS: 10 process/dispatcher + 4 M3B + 32 eight-tool probes.
- Six IronPython host-file compiles PASS; native XAML/WPF/theme/Find PASS.
- 30 Python files AST / in-memory compile / tabnanny PASS, including Workbench
  sanitized only for CLR `.None` syntax during Python 3 parsing.
- All 1,475 existing Workbench functions source-identical; entire Workbench,
  closed HVAC/Piping handlers, M2 headless/lifecycle/tools and manifests unchanged.
- Catalog 237 unchanged; exact eight-tool allowlists; mutation/network/Revit
  boundary scans PASS. Existing sidecar SDK version-only import is permitted;
  an initial overly broad import scan was corrected, with no runtime change.
- Credential-pattern scan: 107 tracked text files, zero findings; no provider
  print/header logging. This is a pattern check, not an exhaustive secret proof.
- .env.local ignored/untracked; contents not read. pip check and diff check PASS.

Project-local WBSO checkpoint now records the preceding implementation audit totals;
this documentation task does not rerun static/live tests or claim live PASS.
Evidence ID, Daily Log ID, KC ID and hours: PENDING; none allocated.

## Required user-run live matrix (all NOT STARTED / PENDING)

Use a supported rigid non-placeholder Duct; keep selection fixed while comparing
each AI result with its canonical deterministic action above. For each case record
tool/action, classification/reason, key counts/fields, omissions, factual parity,
and no model/view/selection mutation. Check UI recovery and maximum one execution.

| Case | Prompt / fixture | Expected |
| --- | --- | --- |
| LIVE-M3D-01 | Summarize the selected duct. | summarize_selected_ducts / A01; direct Summary parity |
| LIVE-M3D-02 | Show me the connectors for the selected duct. | inspect_selected_duct_connectors / A02; direct Connectors parity, End/Curve distinction |
| LIVE-M3D-03 | What system is the selected duct assigned to? | inspect_selected_duct_system_assignment / A03; direct Assignment parity |
| LIVE-M3D-04 | Check the QA health of the selected duct. | inspect_selected_duct_qa_health / A04; direct QA parity, exact HVAC/SEL checks and counts; use tap/Curve fixture if available |
| LIVE-M3D-05 | What is the purpose of a supply air duct system? | Direct answer, no ModelMind tool or provenance |
| LIVE-M3D-06 | Select supported electrical element. Check the connectors for the selected electrical element. | No Piping/HVAC/Electrical execution; safe capability explanation |
| LIVE-M3D-07 | Select Pipe+Duct. Summarize the selected MEP elements. | No automatic multi-specialty chain; single-specialty explanation / fail closed, zero execution |

Do not claim closure until required live evidence is reviewed separately.
