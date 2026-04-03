# Provider Strategy

## Project

AI Systems & Intelligent Automation

## Purpose

This file records the current provider/model strategy for the AI Systems & Intelligent Automation repository.

The project direction described in the development report is not a generic cloud chatbot architecture. It is a BIM-oriented AI Agent / ModelMind system inside pyRevit, with local reasoning, safe execution, and a Codex/VS Code layer for code generation, validation, and controlled interaction with the Revit model.

## Strategy Principle

The provider layer must support the AI Agent architecture without becoming the architecture itself.

The provider/model stack exists to support:

- prompt interpretation
- code generation assistance
- model-context reasoning
- deterministic + generative workflows
- controlled Revit automation execution

It must not:

- bypass safety checks
- become tightly coupled to pyRevit UI code
- hardcode one vendor/model into the full architecture
- make current development dependent on a single provider

## Current Provider Categories

### 1. Local LLM Runtime

Primary intended category:

- Ollama-hosted local models

The development report explicitly identifies an **Ollama Chatbox** powered by locally hosted LLMs such as phi3, phi3:mini, gemma, and llama3, intended for BIM/code discussion, quick help, and prompt experimentation.

### 2. Codex / VS Code Thinking-and-Execution Layer

A separate but related category is the local Codex / VS Code layer used for:

- code generation
- static analysis
- transaction sandbox concepts
- rollback-oriented guarded execution
- secure script preparation before interaction with live Revit state

The report describes this as a secure local layer behind the AI Agent tab, enabling contextual code generation, static analysis, and rollback from natural-language instructions.

### 3. External / API-based Providers

This category may include:

- OpenAI-based provider experiments
- server/API-backed provider adapters
- future external services when needed

These should remain optional and modular. They are not the baseline identity of the project.

## Baseline Provider Policy

### Preferred default

For current project identity and WBSO alignment:

- local-first
- privacy-aware
- modular
- replaceable

### Practical rule

The provider layer should support at least these conceptual modes:

- `local_chat`
- `local_codegen`
- `external_api`
- `disabled / deterministic only`

## Architectural Rules

1. Provider-specific logic must be isolated from pyRevit UI entry points.
2. Provider-specific configuration must not be hardcoded inside button scripts.
3. All provider/model usage should remain traceable in repo-local WBSO notes.
4. External provider integration must remain optional.
5. The system should preserve a path toward:
   - deterministic commands
   - generative experiments
   - controlled execution against live Revit context

## Current Intent for This Repo

At the current baseline, the project should retain a provider strategy that supports:

- local model experimentation
- future provider abstraction
- safe migration from legacy scripts toward modular architecture
- later classification of `Model_Service/` and `Openai_Server/`

## Open Questions

- Should local chat and codegen remain in the same provider boundary or separate ones?
- Should OpenAI/API integration be a thin adapter or a standalone service layer?
- Which retained legacy components already imply provider assumptions?
- How should approval/rejection feedback later influence provider selection or prompt tuning?

## Immediate Next Step

During the next technical pass:

- classify retained provider/service folders
- decide whether current provider code is:
  - keep
  - rename
  - split
  - remove
- update `provider_registry.md` accordingly
