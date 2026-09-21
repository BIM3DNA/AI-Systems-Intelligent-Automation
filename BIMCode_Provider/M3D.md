# M3D - full HVAC read-only AI tool surface

Implementation checkpoint: 2026-09-21, working tree only. IMPLEMENTED / STATIC
VALIDATION PASSED / LIVE VALIDATION PENDING / NOT CLOSED. No staging, commit,
push, authenticated API request or live Revit test performed by this task.
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

No WBSO update, IDs, prompt-asset IDs or hours allocated. No live PASS claimed.

## Required user-run live matrix (all PENDING)

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
