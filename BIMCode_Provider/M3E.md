# M3E - Full Electrical read-only AI tool surface

Implementation checkpoint: working tree above M3D closure
`4cae32f6ffdcbe161cea7e166417926a31752051` (2026-09-23).
IMPLEMENTED; STATIC VALIDATION PASSED; LIVE VALIDATION PENDING; NOT CLOSED.
No implementation commit allocated. No WBSO IDs or hours allocated.

## Fixed surface

Existing four Piping and four HVAC names/mappings remain unchanged. Exactly
twelve read-only AI tools, including these four additions:

| Tool | Action | Closed canonical prompt |
| --- | --- | --- |
| summarize_selected_electrical_elements | ELECTRICAL-RO-001-A01 | show selected electrical elements summary |
| inspect_selected_electrical_connectors | ELECTRICAL-RO-001-A02 | show selected electrical connectors |
| inspect_selected_electrical_circuit_assignment | ELECTRICAL-RO-001-A03 | check selected electrical circuit assignment |
| inspect_selected_electrical_qa_health | ELECTRICAL-RO-001-A04 | check selected electrical elements qa health |

Each strict function has an empty object schema: properties {}, required [],
additionalProperties false. No IDs, profiles, paths, commands or dispatch args.
DEVICE_PROFILE: Lighting Fixtures and Electrical Fixtures only.
EQUIPMENT_PROFILE: Electrical Equipment only. Conduit/fittings, cable tray/fittings,
wires, circuit-only selections, other device categories and links remain unsupported.

## Authority and execution

The unchanged closed runtime owns all eleven ELECTRICAL-QA checks, scope, roles,
relationships, applicability, counts, warnings and electrical quantities. No
open-connector or connector-count QA is added. LOAD/BASE_EQUIPMENT and
UPSTREAM_OR_LOAD_CIRCUIT/DOWNSTREAM_BRANCH_CIRCUIT remain data, not provider inference.
AVAILABLE/UNAVAILABLE/NOT_APPLICABLE/UNREADABLE are preserved distinctly.

The existing M2 ExternalEvent calls the existing headless executor. Request,
document, lifecycle and selection guards remain intact. Mixed supported specialties
fail closed; supported plus unsupported records remain owned by the closed builder.
One tool execution maximum per user request; no automatic tool chain or retry loop.
The sidecar remains Revit-API-free. Existing action provenance labels are reused.

Projection copies closed action-specific summary/tables/warnings/checks without
recalculation. Electrical checks join the existing 30-entry check/warning bound;
12 tables / 40 shared rows / 80,000-character transport budget remain unchanged.
All omitted entries are disclosed. Oversized core data fails closed.
Initial store=True; continuation uses previous_response_id and function_call_output
with call_id; final store=False, tools=[], tool_choice="none". No conversation DB.

## Static validation

Offline suite includes fixed mapping/schema, device/equipment scalar parity,
Electrical check truncation, oversized core, continuation, one-call limit,
cross-specialty/unsupported-only rejection and stale-context probes.
Existing Piping/HVAC suites retained. Native process/dispatcher and WPF probes,
IronPython compilation, sanitized AST/compile/tabnanny and diff checks performed.
Workbench, catalog and dependency manifests remain unchanged. Catalog count 237.
No authenticated OpenAI requests or live Revit tests performed.

## Live validation - all PENDING

Use a disposable model where needed. Keep the selection fixed and compare each
AI result to its closed canonical prompt above: exact classification/reason,
counts, warnings, IDs, role/relationship and applicability. Verify provenance,
maximum one execution and no model/view/selection mutation in every case.

| Case | Selection and prompt | Expected |
| --- | --- | --- |
| LIVE-M3E-01 | One Lighting Fixture or Electrical Fixture: Summarize the selected electrical element. | A01, DEVICE_PROFILE parity |
| LIVE-M3E-02 | Same supported element: Show me the connectors for the selected electrical element. | A02, applicability and read-state parity |
| LIVE-M3E-03 | Same: What circuit is the selected electrical element assigned to? | A03, circuit/panel/role parity |
| LIVE-M3E-04 | Same: Check the QA health of the selected electrical element. | A04, exact checks and issue counts |
| LIVE-M3E-05 | One Electrical Equipment: Summarize the selected electrical equipment. | A01, EQUIPMENT_PROFILE parity |
| LIVE-M3E-06 | What is the purpose of an electrical panelboard in a building? | General answer, no tool execution |
| LIVE-M3E-07 | Conduit: Summarize the selected electrical element. | Unsupported explanation/fail closed; no supported execution |
| LIVE-M3E-08 | Pipe + Electrical: Summarize the selected MEP elements. | One-specialty-at-a-time explanation, no chain |
| LIVE-M3E-09 | Duct + Electrical: Summarize the selected MEP elements. | One-specialty-at-a-time explanation, no chain |
| LIVE-M3E-10 | Pipe + Duct + Electrical: Summarize the selected MEP elements. | Safe mixed-scope explanation, no chain |

For case 07 an available closed-runtime unsupported category may substitute for
Conduit; record its exact category. Record actual document/view/IDs and results;
none of these cases is claimed passed by static tests.
