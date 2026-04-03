# Architecture Notes

## Project

AI Systems & Intelligent Automation

## Current Phase

2026 migration baseline + refactor + active development stream

## Purpose

This file records the current technical architecture of the repository at the present stage of development. The repository is treated as the 2026 migration and refactor stream for ongoing AI systems and intelligent automation work in BIM / pyRevit / Revit API workflows.

## Architectural Intent

The project is intended to evolve into a modular AI-enabled automation framework centered on a pyRevit-based AI Agent that can support:

- deterministic commands for known Revit automation operations
- generative AI-assisted script creation
- local or controlled provider/model integration
- traceable execution against live Revit context
- future approval-driven or self-improving workflows

The broader R&D direction is consistent with the development report, which describes a local AI Agent / ModelMind / Codex-style system integrated into pyRevit, with dynamic model-context retrieval, code synthesis, static analysis, and controlled execution against the active Revit document. It also positions the AI Agent as part of a safe, auditable BIM copilot architecture rather than a general chatbot. :contentReference[oaicite:1]{index=1}

## Current Baseline Architecture

At the time of this baseline commit, the repository is organized around the following main layers:

### 1. pyRevit Extension Layer

This layer represents the visible in-Revit entry point. It includes:

- extension metadata
- tab / panel / pushbutton structure
- icon + bundle configuration
- the initial script entry point used to invoke AI-related workflows from pyRevit

This layer is currently being simplified from a legacy company-specific toolbar structure into a neutral AI Systems & Intelligent Automation baseline.

### 2. Shared Support Layer

This includes:

- `lib/`
- `hooks/`
- any reusable helper code or extension support files retained from the legacy baseline

This layer should remain minimal and only contain reusable logic needed by the current architecture.

### 3. Service / Provider Layer

Current candidate folders include:

- `Model_Service/`
- `Openai_Server/`

These represent service/provider integration directions that may support:

- local model runtime orchestration
- provider abstraction
- external or local AI request handling
- code generation or validation workflows

At this baseline phase, these components are treated as candidate retained modules pending further modular cleanup and scoping.

### 4. Root Utility / Experiment Layer

The repository still contains some standalone utility or experiment scripts. These are not yet treated as final architecture components. Each one must be reviewed and classified as one of:

- keep and integrate
- archive conceptually in migration notes
- delete from active baseline
- refactor into a clearer module boundary

### 5. Repo-Local WBSO Evidence Layer

The repository now contains:

- `WBSO/Technical_Notes/`
- `WBSO/Testing_Validation/`
- `WBSO/Data_Models/`

This layer exists to keep technical evidence close to the code and to support disciplined logging of:

- migration/refactor work
- validation activities
- architectural changes
- retained/deleted legacy components
- future provider/model/config changes

## Current Boundary Rules

The architecture should follow these rules going forward:

- pyRevit UI entry points should remain thin
- reusable business logic should not remain buried inside button scripts if it can be isolated
- provider-specific behavior should be separated from UI behavior
- legacy company-specific naming and assumptions should not remain in active components
- repo-local WBSO evidence should be updated after each meaningful development pass
- historical source lineage should be preserved via migration mapping, not by re-dating past work

## Current In-Scope Work

The following work is currently in scope:

- cleaning and renaming extension metadata
- simplifying the extension structure
- reducing obsolete toolbar/panel/button items
- preserving only AI-relevant components
- mapping legacy components to their new status
- validating the cleaned baseline in pyRevit
- preparing the codebase for further Codex-assisted modular development

## Deferred / Later-Phase Work

The following are intentionally deferred:

- final provider abstraction design
- production-grade agent orchestration
- formal static-analysis / sandbox execution layer
- advanced approval/rejection learning loop
- robust command registry and action safety framework
- deeper service decomposition until the baseline extension is stable

## Current Risks

- legacy code entanglement may hide dependencies not yet visible in the cleaned structure
- some retained scripts may still depend on removed metadata or folder assumptions
- pyRevit loading behavior must be revalidated after renaming/refactor
- service/provider candidates may overlap in responsibility and require consolidation
- root-level utility scripts may create architectural ambiguity if left unmanaged

## Next Architectural Milestones

1. push the first stable migration baseline
2. validate pyRevit loading of the cleaned extension
3. classify retained scripts/modules more strictly
4. isolate provider/service responsibilities
5. define the next functional AI Agent baseline
6. continue aligned WBSO evidence capture after each pass
