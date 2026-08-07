# KC-051 - ELECTRICAL-RO-001 Read-Only Electrical Selection Action Pack

Date: 2026-08-08

Status: implementation and static validation complete; live Revit validation in progress; uncommitted and unpushed; not source-control closed.

Evidence: EV-AI-358. Daily Log: DL-2026-08-08-01. No numeric hours are recorded.

## Why Discovery Preceded Production

Electrical family instances do not expose one uniform connector/system model. ELECTRICAL-DISC-001 established which APIs were authoritative, optional, non-applicable, or unreadable before production QA was defined. This prevented device assumptions from being imposed on distribution equipment and prevented optional Revit API absence from becoming false defects.

## Two Production Profiles

`DEVICE_PROFILE` covers Lighting Fixtures and Electrical Fixtures. A readable assigned load circuit is the common relationship, with the selected element acting as `LOAD` on an `UPSTREAM_OR_LOAD_CIRCUIT`.

`EQUIPMENT_PROFILE` covers Electrical Equipment. Equipment can have no systems, an upstream feeder, downstream branch circuits, or both. A panel can therefore be `LOAD` on its feeder while simultaneously acting as `BASE_EQUIPMENT` for downstream circuits. Multiple systems or branches are not inherently inconsistent.

## Connector Applicability

Only physical End/Curve/Physical connectors in `DomainElectrical` are treated as `PHYSICAL_ELECTRICAL`. Logical connectors represent circuit references and must not be used as physical connectivity evidence. Surface and MasterSurface connectors describe interfaces. `DomainCableTrayConduit` interfaces often have no meaningful device voltage, load, origin, or direction value, so those fields are `NOT_APPLICABLE`, not unreadable.

The four-state model is essential: `AVAILABLE` means meaningful data was read; `UNAVAILABLE` means the API/value was absent; `NOT_APPLICABLE` means the value has no valid semantics for that connector/record; `UNREADABLE` means an expected read failed. Only the last state, required-read failures, unresolved scope, or hard caps should drive completeness PARTIAL.

## Assignment and QA Semantics

Readable zero-system equipment uses `EQUIPMENT_DISTRIBUTION_EMPTY_REVIEW`. It is an assignment/review state, not automatically a model defect. Circuit labels are display values, not unique relationship identities: the same visible number can occur on distinct upstream and downstream records with different system IDs, panels, and roles.

The initial QA model deliberately excludes connector-count and open-connector defects because devices and equipment can validly expose differing physical/interface topologies. Phase, balancing, demand-factor, pole-validity, active-power availability, Room/Space, Mark, and Type Mark rules also remain excluded until evidence supports stable semantics.

## Routing and Context Suggestions

Four exact production routes and twelve aliases now resolve after ELECTRICAL-DISC exact ownership and before generic MEP/fuzzy fallback. This fixes production-like prompt misrouting without changing global fuzzy dispatch.

Electrical becomes a third Context Suggestions specialty only when at least one supported Lighting Fixture, Electrical Fixture, or Electrical Equipment element is selected. Capacity is `min(18, 6 + 4 x eligible specialty count)`. Unsupported Conduit alone retains normal capacity and does not expose production electrical actions.

## Current Live Evidence

Passed cases include empty and Conduit-only A01-A04, assigned Lighting Fixture A01-A04, assigned Electrical Fixture A01-A04, zero-system transformer A01-A04, panelboard A01/A02, electrical-only suggestion capacity ten, and read-only/workflow isolation flags.

The panelboard evidence confirms simultaneous upstream LOAD and downstream BASE_EQUIPMENT roles, eight systems, and End/Logical/Surface/MasterSurface connector applicability without false inconsistency or PARTIAL.

## Pending Validation Matrix

Pending: panelboard A03/A04; mixed Lighting/Electrical Fixtures; device plus equipment; supported plus Conduit; unassigned and multi-system devices if reproducible; genuine unreadable reads; processing, connector, and system caps; pipe-plus-electrical, duct-plus-electrical, and all-three suggestion capacities; unsupported device categories; Wire, Electrical Circuit, Cable Tray/Fitting, Conduit Fitting, and link selections; phase/pole/classification/balancing gaps; demand-factor semantics.

## Governance and Closure State

ELECTRICAL-RO-001 reads the existing active-document selection only. It opens no transaction or picker, writes no parameter/connector/circuit/panel/system/model data, does not alter UI selection or active view, writes no external evidence, does not auto-run, and remains Workflow Anchor, strict QA-source, and Evidence Runbook/Cycle ineligible.

The implementation remains uncommitted and unpushed. This knowledge capture records an interim live-validation checkpoint, not final source-control closure.
