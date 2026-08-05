# KC-050 Knowledge Capture - ELECTRICAL-DISC-001 Read-Only Electrical Selection Discovery

## Feature Package

- Feature ID: `ELECTRICAL-DISC-001`
- Name: ModelMind Read-Only Electrical Selection Discovery
- Status: Implemented, corrected, and live validated for the tested discovery scope
- Date: 05-08-26 (`2026-08-05`)
- Branch: `main`
- Evidence: `EV-AI-357`
- Daily log: `DL-2026-08-05-01`
- Hours: blank; manual entry required
- Source-control status: implementation is uncommitted and unpushed; no implementation commit is recorded

## Purpose and Boundary

ELECTRICAL-DISC-001 is a discovery-only precursor to a possible future ELECTRICAL-RO-001 package. It reads the current active-document selection and reports identity, guarded API exposure, connector semantics, ElectricalSystems, relevant parameters, and provisional category capability. It does not implement production electrical QA actions or production routes.

The four exact deterministic routes are:

- `inspect selected electrical api data`
- `inspect selected electrical elements`
- `discover selected electrical data`
- `show selected electrical discovery report`

Result classifications are `ELECTRICAL_DISCOVERY_OK`, `ELECTRICAL_DISCOVERY_PARTIAL`, `ELECTRICAL_DISCOVERY_NOT_READY`, and `ELECTRICAL_DISCOVERY_FAILED`. Prompt-catalog registration increased the catalog from 231 to 232 entries.

Candidate discovery categories are `OST_ElectricalEquipment`, `OST_ElectricalFixtures`, `OST_LightingFixtures`, `OST_LightingDevices`, `OST_DataDevices`, `OST_CommunicationDevices`, `OST_FireAlarmDevices`, and `OST_SecurityDevices`. Inspectability is not production support approval.

## Initial Runtime Finding

The first Snowdon Towers Sample Electrical cycle inspected Lighting Fixture `1460195`, Electrical Fixture `1495556`, Electrical Equipment `1488616`, and Conduit `1562519`. Useful MEPModel, ConnectorManager, connector, circuit, panel, load, host, and reciprocal-reference evidence was available, but all reports became PARTIAL because optional or non-applicable connector and Room/Space reads were aggregated into an element-wide unreadable state.

The panelboard exposed fourteen connectors and eight ElectricalSystems. Connector types included End, Logical, Surface, and MasterSurface; domains included DomainElectrical, DomainUndefined, and DomainCableTrayConduit. The selected panel appeared as BaseEquipment for downstream branch circuits and as a load on its upstream feeder. Conduit correctly remained outside the initial device-oriented candidate scope, but absent electrical-only connector values also incorrectly contributed to PARTIAL.

## Targeted Correction

The corrected discovery model distinguishes `AVAILABLE`, `UNAVAILABLE`, `NOT_APPLICABLE`, and `UNREADABLE`.

- End plus DomainElectrical retains expected physical origin/direction and meaningful electrical-system evidence.
- Logical connectors retain AllRefs and system-owner evidence while physical geometry and IsConnected can be NOT_APPLICABLE.
- Surface and MasterSurface retain exact connector type and conduit-domain evidence without requiring physical fields that the connector does not expose.
- DomainCableTrayConduit reports circuit type, voltage, poles, load, and power factor as NOT_APPLICABLE unless exposed.
- DomainUndefined remains valid for logical reference behavior.
- PARTIAL now requires unresolved references, required identity/classification failures, connector or ElectricalSystems enumeration failures, required system identity failures, meaningful expected-property failures, cap exceedance, or mixed candidate/unsupported scope.
- Room and Space use guarded phase-aware lookup when a stable created phase exists; raw IronPython indexers are excluded.
- Level output retains ElementId and resolves a readable name when available.
- Voltage, apparent load, true/active load, power factor, and poles retain raw diagnostic values and add guarded Revit-unit normalization to V, VA, W, ratio, and integer. When conversion is unavailable, normalized output remains UNAVAILABLE rather than using guessed factors.
- System records distinguish selected element roles `BASE_EQUIPMENT` and `LOAD`, plus `DOWNSTREAM_BRANCH_CIRCUIT` and `UPSTREAM_OR_LOAD_CIRCUIT` relationships where observable.

## Corrected Live Retest

Runtime context: Snowdon Towers Sample Electrical.

- Lighting Fixture `1605295`: `ELECTRICAL_DISCOVERY_OK`; `CANDIDATE_SUPPORTED`; one DomainElectrical End connector; one PowerCircuit; panel LP000; circuit 8; role LOAD; upstream/load relationship; normalized 120 V, 160 VA, 152 W, and power factor 0.95; no unreadable state or warnings.
- Electrical Fixture `1631043`: `ELECTRICAL_DISCOVERY_OK`; `CANDIDATE_SUPPORTED`; linked architectural host preserved; one DomainElectrical End connector; one circuit; panel P102; circuit 22; role LOAD; normalized 120 V, 180 VA, 180 W, and power factor 1.0; no unreadable state or warnings.
- Electrical Equipment `1488616`: `ELECTRICAL_DISCOVERY_OK`; `CANDIDATE_CONDITIONAL`; fourteen connector records comprising one End, seven Logical, one Surface, and five MasterSurface; eight systems; upstream feeder and downstream branches distinguished; BASE_EQUIPMENT and LOAD roles retained; nonphysical fields NOT_APPLICABLE; normalized values present; no unreadable state or warnings.
- Conduit `1604466`: `ELECTRICAL_DISCOVERY_OK`; `CANDIDATE_UNSUPPORTED` for the initial device package; two DomainCableTrayConduit End connectors; reciprocal Conduit Fitting references; electrical quantities NOT_APPLICABLE; zero systems; no unreadable state or warnings.

These conclusions are provisional. ELECTRICAL-RO-001 is not implemented, and no claim is made that every electrical category is supported.

## Route-Collision Consideration

Before discovery routes were registered, production-like prompts for selected electrical summary, connectors, circuit assignment, and QA health could rank against generic MEP or HVAC actions because Console token-prefix fuzzy ranking favored overlapping terms. The four ELECTRICAL-DISC-001 routes are now exact and uniquely owned. Global fuzzy dispatch was not changed, and future ELECTRICAL-RO-001 routes remain unregistered. This remains an open production-route design consideration, not a discovery defect.

## Remaining Limitations

Untested categories and paths include Lighting Devices, Data Devices, Communication Devices, Fire Alarm Devices, Security Devices, additional Electrical Equipment families, zero-system candidate devices, multi-system fixtures, unresolved references, genuine connector and ElectricalSystems enumeration failures, processing and parameter-display caps, mixed candidate/unsupported selection, wire-only and Electrical Circuit-only selection, Cable Tray/Fitting and Conduit Fitting selection, linked instances, unavailable phase/pole/classification/balanced and active-power APIs, demand-factor semantics, final electrical QA rules, final production route registration, and global fuzzy-route collision mitigation.

## Safety and Workflow Isolation

- `model_modified: false`
- `ui_selection_modified: false`
- `active_view_changed: false`
- `external_files_written: false`
- `transaction_started: false`
- `transaction_group_started: false`
- `linked_document_modified: false`
- `selection_picker_opened: false`
- `auto_run: false`
- `evidence_runbook_advanced: false`
- `evidence_cycle_manifest_updated: false`
- `workflow_anchor_eligible: false`
- `qa_export_source_eligible: false`

Static validation passed tabnanny, supporting-module compilation, sanitized full-script AST parsing, prompt-catalog parsing at 232 entries, route and alias ownership, classification and cap registration, connector applicability, Room/Space indexer exclusion, unit normalization, PARTIAL precedence, deterministic ordering, governance, workflow/QA-source exclusion, unchanged PIPING/HVAC handlers, and `git diff --check`.

Technical conclusion: ELECTRICAL-DISC-001 is corrected and live validated for the tested discovery categories. It supplies evidence for designing a future package but does not establish or implement ELECTRICAL-RO-001 production scope.
