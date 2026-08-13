# PROJECT STATE

Last updated: 2026-08-13

Repository:
C:\00_WORKS\DEVELOPMENT\AI

Branch:
main

# 1. LAST VERIFIED RUNTIME / PACKAGE CLOSURE BASELINE

Last verified runtime/package closure commit:

6d0f5f37178df8508148c39276b89f2bf558565c

At the package-closure checkpoint:

- branch: main
- HEAD: 6d0f5f37178df8508148c39276b89f2bf558565c
- origin/main: 6d0f5f37178df8508148c39276b89f2bf558565c
- ahead / behind: 0 / 0
- worktree: clean

This commit is the verified source-control closure baseline for
ELECTRICAL-RO-001 and the preceding closed ModelMind packages.

It is not necessarily the repository's current HEAD after later documentation
or feature commits.

Always verify the live Git state at the start of every development session.

Do not treat older Codex conversation history as authoritative.

The authoritative project state is:

1. Git repository and Git history
2. this PROJECT_STATE.md
3. AGENTS.md
4. project-local WBSO records
5. verified runtime test evidence

# 2. CURRENT MODELMIND PACKAGE STATUS

## PIPING-RO-001

Feature:
ModelMind Read-Only Piping Selection Action Pack

Status:

SOURCE-CONTROL CLOSED

Initial implementation commit:

27b159998f1caa5637897a90712c4048cae10e91

Targeted correction commit:

b3867636c0f5f7991da45a88362aacaab05a76f8

Canonical actions:

- show selected pipes summary
- show selected pipe connectors
- check selected pipes system assignment
- check selected pipes qa health

Important final correction:

Context Suggestions capacity and Visual Preview snake_case safety parsing were
corrected.

Remaining limitations are non-blocking and must not be treated as regressions
unless failing behavior is actually reproduced.

## HVAC-RO-001

Feature:
ModelMind Read-Only Duct Selection Action Pack

Status:

SOURCE-CONTROL CLOSED

Runtime commit:

94aedee58db199e0635847688789a622963dd8a2

Project-local WBSO closure commit:

374779d4bce1201483cc1ce3438d84e4aaaeeba4

Canonical actions:

- show selected ducts summary
- show selected duct connectors
- check selected ducts system assignment
- check selected ducts qa health

Important final correction:

HVAC-QA-009 evaluates physical End connector count rather than total physical
connector count.

Curve connectors used by valid taps/branches must not create false topology
defects.

## ELECTRICAL-DISC-001

Feature:
ModelMind Read-Only Electrical Selection Discovery

Status:

SOURCE-CONTROL CLOSED

Closure commit:

2428f1a523fbebcff533369e0fb373d043d80f73

Purpose:

Discovery-only electrical API investigation used to determine safe production
semantics.

Canonical discovery route:

inspect selected electrical api data

Aliases:

- inspect selected electrical elements
- discover selected electrical data
- show selected electrical discovery report

Important established semantics:

- AVAILABLE
- UNAVAILABLE
- NOT_APPLICABLE
- UNREADABLE

Roles:

- LOAD
- BASE_EQUIPMENT

Relationships:

- UPSTREAM_OR_LOAD_CIRCUIT
- DOWNSTREAM_BRANCH_CIRCUIT

Initial production conclusions:

Supported:

- OST_LightingFixtures
- OST_ElectricalFixtures

Conditional / equipment profile:

- OST_ElectricalEquipment

Unsupported for initial production package:

- OST_Conduit

## ELECTRICAL-RO-001

Feature:
ModelMind Read-Only Electrical Selection Action Pack

Status:

SOURCE-CONTROL CLOSED

Implementation + initial project-local WBSO commit:

90a5e9e1e279de2d49ee0bf2c4c30cfce00a68d1

Final project-local WBSO closure commit:

6d0f5f37178df8508148c39276b89f2bf558565c

Canonical actions:

- show selected electrical elements summary
- show selected electrical connectors
- check selected electrical circuit assignment
- check selected electrical elements qa health

Prompt catalog:

236 entries

ELECTRICAL-RO production routes:

- 4 canonical entries
- 12 aliases
- 16 unique routes

# 3. ELECTRICAL-RO-001 PRODUCTION ARCHITECTURE

## DEVICE_PROFILE

Supported categories:

- OST_LightingFixtures
- OST_ElectricalFixtures

Typical semantics:

- selected element behaves as a load
- zero systems can become DEVICE_UNASSIGNED_REVIEW
- one coherent system becomes DEVICE_ASSIGNED
- multiple systems become DEVICE_MULTI_SYSTEM_REVIEW

## EQUIPMENT_PROFILE

Supported category:

- OST_ElectricalEquipment

Equipment may legitimately:

- expose zero systems
- expose one system
- expose multiple systems
- act as LOAD on an upstream feeder
- act as BASE_EQUIPMENT for downstream circuits
- expose physical connectors
- expose Logical connectors
- expose Surface interfaces
- expose MasterSurface interfaces

# 4. ELECTRICAL-RO-001 ASSIGNMENT STATES

Device states:

- DEVICE_ASSIGNED
- DEVICE_MULTI_SYSTEM_REVIEW
- DEVICE_UNASSIGNED_REVIEW
- UNAVAILABLE
- UNREADABLE
- INCONSISTENT

Equipment states:

- EQUIPMENT_DISTRIBUTION_ASSIGNED
- EQUIPMENT_DISTRIBUTION_EMPTY_REVIEW
- EQUIPMENT_DISTRIBUTION_PARTIAL
- UNAVAILABLE
- UNREADABLE
- INCONSISTENT

# 5. ELECTRICAL CONNECTOR APPLICABILITY

Classes:

- PHYSICAL_ELECTRICAL
- LOGICAL_REFERENCE
- SURFACE_INTERFACE
- MASTER_SURFACE_INTERFACE
- CONDUIT_INTERFACE
- OTHER

Important rule:

Do not force physical geometry/connectivity semantics onto Logical, Surface or
MasterSurface connectors.

NOT_APPLICABLE is valid and must not automatically become UNREADABLE or PARTIAL.

The initial ELECTRICAL-RO package deliberately excludes:

- open-connector QA
- connector-count QA

# 6. ELECTRICAL QA MODEL

Stable checks:

- ELECTRICAL-QA-001 Unsupported selected element
- ELECTRICAL-QA-002 Required electrical API unreadable
- ELECTRICAL-QA-003 Missing device circuit assignment
- ELECTRICAL-QA-004 Assigned device panel missing
- ELECTRICAL-QA-005 Assigned device circuit number missing
- ELECTRICAL-QA-006 Equipment role distribution unreadable
- ELECTRICAL-QA-007 Role and circuit relationship inconsistent
- ELECTRICAL-QA-008 Invalid system voltage
- ELECTRICAL-QA-009 Invalid system load
- ELECTRICAL-QA-010 Invalid power factor
- ELECTRICAL-QA-011 Connector read failure

Reused generic checks:

- SEL-QA-001
- SEL-QA-002
- SEL-QA-003
- SEL-QA-004
- SEL-QA-005
- SEL-QA-006
- SEL-QA-007
- SEL-QA-008
- SEL-QA-015
- SEL-QA-016

Do not add new deterministic electrical QA rules without runtime evidence.

# 7. FINAL ELECTRICAL-RO LIVE VALIDATION

Primary model:

Snowdon Towers Sample Electrical

Validated:

- empty selection A01-A04
- unsupported Conduit A01-A04
- Lighting Fixture A01-A04
- Electrical Fixture A01-A04
- zero-system transformer A01-A04
- multi-system panelboard P108 A01-A04
- supplemental panelboard P105 A03
- DEVICE_UNASSIGNED_REVIEW
- ELECTRICAL-QA-003 YELLOW path
- Lighting Fixture + Electrical Fixture mixed selection
- Device + Electrical Equipment mixed selection
- supported Lighting Fixture + unsupported Conduit
- unsupported Lighting Device
- unsupported Conduit Fitting
- Context Suggestions 6 / 10 / 14 / 18
- Visual Preview mixed-specialty capacities
- workflow isolation
- read-only governance
- final static regression
- final Git audit

P108 panelboard:

- 8 ElectricalSystems
- LOAD count 1
- BASE_EQUIPMENT count 7
- A01 passed
- A02 passed
- A03 passed
- A04 GREEN
- deterministic issues 0
- partial checks 0

DEVICE_UNASSIGNED_REVIEW:

Lighting Fixture 1763856

- ElectricalSystems readable
- system count 0
- DEVICE_UNASSIGNED_REVIEW
- A04 YELLOW
- exactly ELECTRICAL-QA-003
- no cascading false positives

# 8. CONTEXT SUGGESTIONS

Formula:

min(18, 6 + 4 × eligible specialty count)

Validated capacities:

- no supported specialty / unsupported-only: 6
- one supported specialty: 10
- two supported specialties: 14
- three supported specialties: 18

Validated combinations include:

- pipe
- duct
- electrical
- pipe + duct
- pipe + electrical
- duct + electrical
- pipe + duct + electrical

Visual Preview follows the same safe capacities.

No automatic execution.

# 9. FINAL RUNTIME HASHES

Current ELECTRICAL-RO closure runtime:

script.py:

3FFBF3D1E6DB36F90CD6431A0E6B078B3C26280A71A84C2531984E6A15F4BA0B

prompt_catalog.json working-tree SHA-256 (Windows CRLF):

0879A32807D4893A3B325D3495BBA0CFB12380AC127F0B30F569E07CAF707953

prompt_catalog.json Git blob SHA-256 (repository LF content; identical at
90a5e9e1e279de2d49ee0bf2c4c30cfce00a68d1,
6d0f5f37178df8508148c39276b89f2bf558565c, and current HEAD):

1794C036AAFA1F5B39EC99582738B1DF87FFF064F1C3E67FB09A6101E7124A6B

Historical note:

The previously documented value
5CA5F995492B20B9FD443BD4E34BB2E0108F2181FA3A292192F15EF6E9C26829
could not be reproduced from repository history or common alternate byte
representations and is treated as an incorrectly recorded documentation value,
not as evidence of a runtime/catalog-content difference.

# 10. READ-ONLY GOVERNANCE

For PIPING-RO, HVAC-RO and ELECTRICAL-RO report actions:

Expected safety behavior:

- model_modified false
- ui_selection_modified false
- active_view_changed false
- external_files_written false
- transaction_started false
- transaction_group_started false
- linked_document_modified false
- selection_picker_opened false
- auto_run false

Expected workflow behavior:

- evidence_runbook_advanced false
- evidence_cycle_manifest_updated false
- workflow_anchor_eligible false
- qa_export_source_eligible false
- evidence_cycle_stage false

Do not accidentally turn these read-only actions into workflow anchors, QA-export
sources or mutation commands.

# 11. PROTECTED EXISTING AREAS

Do not casually modify:

- window lifecycle
- ExternalEvent / reviewed dispatch
- modal/modeless behavior
- create sheet paths
- create 3D view paths
- rename view paths
- existing PIPING-RO handlers
- existing HVAC-RO handlers
- existing ELECTRICAL-DISC handlers
- existing ELECTRICAL-RO handlers
- generic MEP-RO behavior
- exact route ownership
- Context Suggestions capacity logic
- workflow-anchor allowlists
- QA-export-source allowlists

Changes to these require explicit task scope and regression validation.

# 12. LEGACY / HISTORICAL STATE

Older PROJECT_STATE notes recorded:

- create ACO 1.4301 single socket pipe schedule from template: passed
- create ACO pipe fitting summary from template: passed
- 1.4404 templates: pending / empty-source issue

These notes predate the current ModelMind PIPING/HVAC/ELECTRICAL closure cycle.

They are preserved as historical context only.

Do not assume they represent the current development priority.

# 13. REMAINING NON-BLOCKING ELECTRICAL COVERAGE

Not fully reproduced or validated:

- DEVICE_MULTI_SYSTEM_REVIEW
- Data Devices
- Communication Devices
- Fire Alarm Devices
- Security Devices
- Wire-only selection
- Electrical Circuit-only selection
- Cable Tray
- Cable Tray Fitting
- linked-instance selection
- genuine ConnectorManager failure
- genuine connector-enumeration failure
- genuine ElectricalSystems failure
- processing-cap exceedance
- connector-per-element cap exceedance
- system-per-element cap exceedance
- phase API gaps
- pole API gaps
- system-classification API gaps
- balancing API gaps
- demand-factor semantics

These are not known defects.

Do not change production behavior merely to address an unobserved theoretical
case.

Reproduce first.

# 14. WBSO STATE

Current WBSO week:

2026-W19

Project-local ELECTRICAL-RO records:

- EV-AI-358
- EV-AI-359
- DL-2026-08-08-01
- DL-2026-08-12-01
- KC-051

Central final closure records:

- EV-AI-364 through EV-AI-370
- DL-2026-08-12-08
- KC-052 central commit note

Central WBSO files are outside the Git repository.

Do not stage or commit central WBSO files into this repository.

# 15. NEXT DEVELOPMENT STATE

There is currently no open ELECTRICAL-RO-001 closure task.

PIPING-RO-001:
CLOSED

HVAC-RO-001:
CLOSED

ELECTRICAL-DISC-001:
CLOSED

ELECTRICAL-RO-001:
CLOSED

New development must begin as a new bounded feature/package from the current
clean main branch after verifying live Git state.

The last verified runtime/package closure baseline is:

6d0f5f37178df8508148c39276b89f2bf558565c

Later documentation-only commits, including durable project handoff files, may
exist above this closure commit and do not reopen ELECTRICAL-RO-001.

Before implementing the next feature:

1. verify Git status;
2. confirm branch main;
3. confirm HEAD/origin alignment;
4. inspect existing architecture;
5. define a new feature/package ID;
6. define supported and unsupported scope;
7. identify regression-sensitive handlers;
8. define validation before implementation;
9. do not modify closed packages without explicit need;
10. do not commit or push without explicit user approval.
