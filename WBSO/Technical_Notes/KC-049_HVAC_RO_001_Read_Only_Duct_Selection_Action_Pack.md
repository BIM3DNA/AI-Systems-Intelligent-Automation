# KC-049 Knowledge Capture - HVAC-RO-001 Read-Only Duct Selection Action Pack

## Feature Package

- Feature ID: HVAC-RO-001
- Name: ModelMind Read-Only Duct Selection Action Pack
- Status: Implemented and statically validated; Revit runtime validation required.
- Date: 30-07-26 (`2026-07-30`)
- Week: `2026-W18`
- Branch: `main`
- Baseline: `4af43b526292d0cc3a24d5c36c63de232cdedc9b`
- Evidence: EV-AI-354 and EV-AI-355
- Daily log: `DL-2026-07-30-02`
- Hours: blank; manual entry required
- Source-control status: runtime implementation is uncommitted and unpushed; no implementation commit exists

## Problem Statement

ModelMind required deterministic, bounded, read-only inspection of rigid ducts already selected in the active Revit document. Existing generic MEP-RO-001 reports did not expose duct shape, dimensions, cross-sectional area, volume provenance, slope applicability, HVAC system consistency, insulation/lining, or reciprocal physical connector evidence. Existing legacy duct commands cover active-view counts, lists, totals, system reports, QA, selection, and export, but do not provide the approved selection-specific HVAC action pack.

The package must preserve the selected elements as input only. It must not open a picker, change UI selection, mutate connectors, assign systems, resize ducts, alter slope, change views, modify linked documents, advance evidence workflow state, or create external evidence.

## Repository Baseline and Scope

Before implementation, local `main` and `origin/main` both resolved to `4af43b526292d0cc3a24d5c36c63de232cdedc9b`, with no ahead/behind divergence and a clean worktree.

Runtime implementation changes are limited to:

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/lib/prompt_catalog.json`

Git reported two files changed, 2338 insertions, and 270 deletions. The deletion count is attributed to similarity matching around adjacent PIPING-RO-001 and HVAC-RO-001 blocks. Codex independently verified that existing PIPING runtime methods remained byte-for-byte unchanged.

This WBSO update does not modify the runtime implementation.

## Relationship to MEP-RO-001 and PIPING-RO-001

HVAC-RO-001 reuses MEP-RO-001 architecture for:

- current active-document selection snapshot;
- selected ElementId resolution;
- unresolved-reference preservation;
- identity, type, workset, pinned, group, assembly, and design-option reads;
- guarded parameter access;
- generic QA;
- deterministic Markdown tables;
- report registration;
- safety and workflow-isolation metadata.

It adapts PIPING-RO-001 patterns for:

- explicit supported/unsupported scope;
- normalized specialty records;
- bounded connector details;
- reciprocal physical connection confirmation;
- normalized system assignment;
- QA aggregation and classification precedence;
- caps and deterministic sorting;
- Context Suggestions gating and safe-card projection;
- Workflow Anchor and strict QA-source exclusion.

Legacy MEP, piping, selection, workflow, and export behavior is not reassigned.

## Route Ownership

Action IDs and canonical prompts:

1. `HVAC-RO-001-A01` - `show selected ducts summary`
2. `HVAC-RO-001-A02` - `show selected duct connectors`
3. `HVAC-RO-001-A03` - `check selected ducts system assignment`
4. `HVAC-RO-001-A04` - `check selected ducts qa health`

Summary aliases:

- `summarize selected ducts`
- `report selected ducts summary`
- `inspect selected ducts`

Connector aliases:

- `inspect selected duct connectors`
- `report selected duct connectors`
- `check selected duct connections`

System aliases:

- `show selected ducts system assignment`
- `report selected duct system assignment`
- `inspect selected duct systems`

QA aliases:

- `run selected ducts health check`
- `inspect selected ducts qa`
- `report selected duct issues`

All sixteen routes are deterministic, report-only, manually executed, confirmation-free, and `auto_run false`.

Existing routes remain with their previous handlers, including selected/active-view duct counts, lists, length/volume totals, unconnected fittings, missing-system reports, legacy system and QA reports, selection-only commands, and active-view duct export.

## Supported and Unsupported Scope

Supported elements must satisfy all of:

- `isinstance(element, DB.Mechanical.Duct)`;
- category `OST_DuctCurves`;
- active-document resolution;
- current UI selection membership;
- guarded `IsPlaceholder == false`.

Implemented classifications:

- `SUPPORTED_DUCT`
- `UNSUPPORTED_DUCT_PLACEHOLDER`
- `UNSUPPORTED_FLEX_DUCT`
- `UNSUPPORTED_DUCT_FITTING`
- `UNSUPPORTED_DUCT_ACCESSORY`
- `UNSUPPORTED_DUCT_INSULATION`
- `UNSUPPORTED_DUCT_LINING`
- `UNSUPPORTED_FABRICATION_PART`
- `UNSUPPORTED_LINK_INSTANCE`
- `UNSUPPORTED_NON_DUCT`
- `UNRESOLVED_REFERENCE`

Unsupported and unresolved references remain visible. Expected runtime behavior is NOT_READY for empty/no-supported scope and PARTIAL when supported ducts coexist with unsupported or unresolved references. These outcomes remain pending live Revit confirmation.

## Normalized Duct Record

Identity and restrictions:

- ElementId and UniqueId;
- category;
- family/type identity, duct type, and type ID;
- workset;
- pinned state;
- group and assembly membership;
- design option;
- placeholder state.

Geometry:

- curve state and curve type;
- length in internal feet, millimetres, and metres;
- start/end elevation and elevation delta;
- horizontal run;
- direction;
- reference level;
- slope state, source, ratio, percent, per mille, and angle.

Shape and dimensions:

- shape state and normalized shape;
- diameter, width, height, major dimension, and minor dimension;
- cross-sectional area in internal square feet and square metres;
- area source.

Volume:

- direct Revit volume;
- calculated section-area-times-length volume;
- selected display volume and source;
- discrepancy state, ratio, and percentage.

System:

- assignment state;
- MEP system ID, name, type, and classification;
- built-in and fallback metadata;
- authoritative sources;
- consistency and contradictions.

Connectors:

- connector-manager state;
- raw, physical, reciprocal-connected, unconnected, and unreadable counts;
- connector type/domain/shape/origin/direction/flow direction;
- dimensions;
- raw `IsConnected`;
- reciprocal physical state;
- connected active-document owner IDs/categories/classes.

Insulation and lining:

- state;
- related element IDs;
- thickness where readable.

Unavailable optional values remain explicit. The implementation does not fabricate dimension, area, volume, insulation, or lining zeroes.

## Shape and Dimension Model

Normalized shapes are:

- `ROUND`
- `RECTANGULAR`
- `OVAL`
- `OTHER`
- `INCONSISTENT`
- `UNAVAILABLE`
- `UNREADABLE`

Primary shape evidence is consensus across eligible physical HVAC end connectors. Guarded built-ins `RBS_CURVE_DIAMETER_PARAM`, `RBS_CURVE_WIDTH_PARAM`, and `RBS_CURVE_HEIGHT_PARAM` provide fallback or cross-check evidence.

Round ducts require a positive finite diameter and use circular area. Width and height are not fabricated.

Rectangular ducts require positive finite width and height and use width multiplied by height. Diameter is not fabricated.

Oval ducts require reliable full major/minor dimensions and use ellipse area with source `CALCULATED_ELLIPSE`.

Other or unavailable shapes retain readable evidence without a fabricated standard formula. Contradictory physical shape evidence remains `INCONSISTENT`.

## Length, Area, and Volume

Length prefers stable Revit built-in metadata and falls back to `LocationCurve.Length`. Values remain in internal feet and are displayed in millimetres and metres. The near-zero threshold is 1 mm.

Cross-sectional area is calculated only from valid shape-specific dimensions. Its source is explicit.

Volume priority is:

1. stable direct Revit volume when readable;
2. calculated section area multiplied by length;
3. unavailable.

When direct and calculated values both exist, both are retained. Contradiction requires both the declared absolute internal-unit tolerance and the two-percent relative tolerance to be exceeded. Optional direct-volume absence alone is not a design defect.

## Slope and Verticality

The package does not copy pipe-slope assumptions. It attempts guarded duct slope built-ins and independently calculates endpoint elevation delta, horizontal run, and geometric ratio where meaningful.

States are `AVAILABLE`, `NOT_APPLICABLE`, `UNAVAILABLE`, and `UNREADABLE`.

Vertical or near-vertical ducts use a 1 mm horizontal-run tolerance and report conventional slope as `NOT_APPLICABLE`. Endpoint elevations remain visible.

Straight nonvertical ducts report authored slope when available; otherwise a geometric ratio may be shown with source `CALCULATED`. Curved ducts retain curve metadata without a fabricated global slope.

## System Assignment

States are:

- `ASSIGNED`
- `UNASSIGNED_REVIEW`
- `UNAVAILABLE`
- `UNREADABLE`
- `INCONSISTENT`

Authority order is:

1. `Duct.MEPSystem`;
2. built-in system name/type/classification;
3. existing fallback metadata as supplementary evidence;
4. connector system information as supplementary diagnostic evidence only.

Different legitimate systems across selected ducts are distribution data. Only contradictory authoritative metadata on the same duct is inconsistent.

## Connectors and Reciprocity

Inspection is limited to connectors owned by each selected supported duct and one immediate `AllRefs` hop.

Eligible selected connectors require HVAC domain and a positive physical type. Reference owners must resolve in the active document, differ from the selected owner, and expose an eligible physical HVAC reference connector. Logical/system/reference/analytical connectors, self owners, linked owners, unresolved owners, unsupported domains, and nonphysical connector types are excluded.

A connection is authoritative only when:

- `connector.IsConnectedTo(reference)` is true; and
- `reference.IsConnectedTo(connector)` is true.

Raw `IsConnected` is diagnostic only. No `ConnectTo`, `DisconnectFrom`, graph mutation, or model traversal beyond one hop is used.

## Stable HVAC QA

- `HVAC-QA-001` Unsupported selected element
- `HVAC-QA-002` Missing duct type
- `HVAC-QA-003` Invalid or inconsistent duct shape
- `HVAC-QA-004` Missing system assignment
- `HVAC-QA-005` Missing or nonpositive required dimensions
- `HVAC-QA-006` Missing or near-zero length
- `HVAC-QA-007` Section or volume evidence inconsistent
- `HVAC-QA-008` Unconnected physical connector
- `HVAC-QA-009` Abnormal physical connector count
- `HVAC-QA-010` Connector read failure
- `HVAC-QA-011` Inconsistent system metadata
- `HVAC-QA-012` Unreadable required HVAC parameter

`HVAC-QA-007` treats optional volume absence as not applicable. It reports impossible section or contradictory direct/calculated volume as an issue and guarded required-read failure as partial.

Approved generic checks reused without duplication:

- `SEL-QA-001` through `SEL-QA-008`
- `SEL-QA-011`
- `SEL-QA-013`
- `SEL-QA-015`
- `SEL-QA-016`

## Result Classifications

- `HVAC_SELECTION_SUMMARY_OK`
- `HVAC_CONNECTOR_REPORT_OK`
- `HVAC_SYSTEM_ASSIGNMENT_OK`
- `HVAC_QA_HEALTH_GREEN`
- `HVAC_QA_HEALTH_YELLOW`
- `HVAC_QA_HEALTH_PARTIAL`
- `HVAC_SELECTION_REPORT_PARTIAL`
- `HVAC_SELECTION_REPORT_NOT_READY`
- `HVAC_SELECTION_REPORT_FAILED`

Static validation found no existing classification collision. Runtime classification behavior remains unvalidated.

## Caps and Deterministic Sorting

Caps:

- supported ducts processed: 200;
- displayed duct rows: 200;
- connector-detail rows: 400;
- displayed connectors per duct: 8;
- connected owner IDs per connector: 20;
- affected IDs per QA check: 50;
- warnings: 50;
- normalized value: 160 characters.

Display truncation alone is not PARTIAL. Skipping supported ducts because the processing cap is exceeded is PARTIAL.

Sorting uses numeric duct ElementId, connector origin/type/domain/sequence, numeric connected owner ID, stable HVAC-QA ID, normalized system fields, and count-descending distributions.

## Context Suggestions and Safe Cards

Supported-duct gating requires at least one supported rigid non-placeholder duct.

Capacity policy:

- normal: 6;
- pipe only: 10;
- duct only: 10;
- pipe plus duct: 14;
- pipe plus duct plus unsupported: 14.

Formula: `min(14, 6 + 4 x eligible supported specialty count)`.

Ordering:

1. evidence/export priority;
2. four generic MEP-RO-001 actions;
3. four PIPING-RO-001 actions when eligible;
4. four HVAC-RO-001 actions when eligible;
5. optional/history actions when capacity remains.

Context Suggestions and safe prompt cards share the same capacity. Rendering does not execute commands.

## Workflow and Safety Isolation

Every HVAC report declares:

- `model_modified false`
- `ui_selection_modified false`
- `active_view_changed false`
- `external_files_written false`
- `transaction_started false`
- `transaction_group_started false`
- `linked_document_modified false`
- `selection_picker_opened false`
- `auto_run false`

Workflow metadata:

- `evidence_runbook_advanced false`
- `evidence_cycle_manifest_updated false`
- `workflow_anchor_eligible false`
- `qa_export_source_eligible false`
- `evidence_cycle_stage false`

All nine HVAC classifications are excluded from Workflow Anchor selection. The strict QA-source allowlist was not broadened. Visual Preview uses the existing snake-case-compatible safety parser.

## Static Validation

Codex reported successful:

- baseline and branch alignment verification;
- tabnanny;
- compatible supporting-module compilation;
- sanitized full AST parse;
- prompt catalog JSON parse;
- catalog count 231;
- four HVAC catalog entries and sixteen unique routes;
- legacy duct-route preservation;
- byte-for-byte preservation of PIPING runtime methods;
- result-classification, HVAC-QA, generic-QA, scope, cap, sorting, shape, dimension, system, and connector assertions;
- Context Suggestions cases for empty, Wall-only, fitting-only, duct-only, duct-plus-Wall, pipe-only, and pipe-plus-duct;
- safe-card capacity;
- report-only/manual/auto-run-false metadata;
- Workflow Anchor and strict QA-source exclusion;
- Visual Preview safety-field presence;
- diff-scoped governance scan;
- `git diff --check`.

Governance found no new transaction, TransactionGroup, model mutation, parameter write, connector mutation, selection picker/change, active-view assignment, linked-document mutation, automatic execution, or external file write.

## Runtime Test Plan

First stage:

1. empty selection;
2. Wall-only selection;
3. Duct Fitting-only selection;
4. one rigid non-placeholder duct;
5. rigid duct plus Wall.

Extended stage:

- round, rectangular, oval-if-present, connected, one-open-end, two-open-end, assigned, unassigned-if-available, vertical, sloped-if-present, curved, insulated, lined, and multiple-system ducts;
- Pipe plus Duct suggestion capacity;
- more than 200 ducts if practical;
- placeholder, FlexDuct, fabrication, unreadable connector, inconsistent system, volume-discrepancy, and unsupported-slope paths where available.

Revit runtime validation has not yet been performed for HVAC-RO-001.

## Known Limitations

1. Direct duct volume built-in availability varies by Revit version and duct type.
2. Duct slope built-in availability requires runtime confirmation.
3. Curved ducts do not receive a fabricated global slope.
4. Oval area requires reliable full major/minor dimensions.
5. Insulation and lining metadata are optional and API-dependent.
6. Placeholder classification requires an actual placeholder duct.
7. Reciprocal HVAC connector behavior requires live validation.
8. Context Suggestions gating and fourteen-item mixed-specialty capacity lack runtime proof.
9. The nine result classifications lack runtime proof.
10. `HVAC-QA-001` through `HVAC-QA-012` lack runtime proof.

## Conclusion

HVAC-RO-001 is implemented and statically validated. Revit runtime validation, source-control commit, and remote closure remain pending.

## Initial Live Validation Milestone

Runtime validation on 30-07-26 used Snowdon Towers Sample HVAC / `Cover [ThreeD]` and a BUNGE model for negative scope. Empty selection, Wall-only, Pipe Fitting, true Duct Fitting, supported round rigid duct, connector, assigned-system, QA, Context Suggestions, Visual Preview, and workflow-isolation paths passed.

Representative duct `1466955` normalized as ROUND, 203.2 mm diameter, 4,776.7 mm length, `0.032429 m2` section area, `0.154897 m3` host volume within tolerance, zero slope, L5 reference level, assigned Mechanical Return Air 29 system, and no insulation/lining. Duct-only Context Suggestions expanded to ten while retaining evidence precedence and all four generic actions.

### Connector Topology Finding and Decision

The duct exposed five legitimate physical HVAC connectors: two End and three Curve, all reciprocally connected. The initial HVAC-QA-009 assumption of exactly two total physical connectors was invalid for tap/branch topology and produced a false positive.

The stable QA ID was retained and renamed `Abnormal physical end connector count`. The corrected rule expects exactly two readable physical End connectors. Additional accepted Curve connectors remain valid records, contribute to total physical counts, and remain independently checked by HVAC-QA-008. Unreadable manager or connector-type evidence produces partial status. Connector reports now expose End, non-End, and unreadable-type counts.

Post-correction duct `1466955` passed HVAC-QA-009 and all five connectors passed HVAC-QA-008. Overall QA remained YELLOW solely because `SEL-QA-011` found a blank Mark, which is valid model QA rather than an implementation defect. Issue count decreased from two to one and partial count remained zero.

### Current Limitations

Subsequent runtime coverage passed for rectangular, oval, vertical oval, one-open, two-open, assigned Supply Air, mixed pipe-plus-duct capacity fourteen, insulation host/element, and lining host/element paths. `UNASSIGNED_REVIEW` was not practically reproducible because Revit assigned isolated ducts to standalone Supply/Return/Exhaust systems; this is not a defect. Unreadable connector-manager/type paths, processing/display caps, and human-readable system type remain limitations. Non-zero/curved slope, abnormal End topology beyond open states, FlexDuct, placeholder, fabrication, accessory, pipe-plus-duct-plus-unsupported, inconsistent-system, area/volume contradiction, invalid-dimension, and near-zero-length paths were not encountered.

## Current Milestone Conclusion

HVAC-RO-001 has broad live validation across supported shapes, vertical geometry, connector states, assigned systems, mixed-specialty suggestions, insulation/lining, safety metadata, and workflow isolation. The HVAC-QA-009 correction remained stable and no new code defect was found. Final static and Git scope audit passed. Runtime implementation is ready for commit; source-control commit and push remain pending.
