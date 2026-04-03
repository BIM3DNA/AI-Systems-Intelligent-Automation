# Provider Registry

## Project

AI Systems & Intelligent Automation

## Purpose

This file tracks provider categories and provider-boundary decisions for the repository.

The development report makes clear that the AI Agent architecture combines:

- local AI interaction
- pyRevit integration
- VS Code / Codex runtime support
- safe execution concepts
- deterministic and generative workflows.

This registry exists so provider choices remain visible and do not become hidden assumptions in the codebase.

---

## Provider Registry

| Provider ID | Provider Name                        | Type                          | Current Role                                                     | Status             | Notes                                                        |
| ----------- | ------------------------------------ | ----------------------------- | ---------------------------------------------------------------- | ------------------ | ------------------------------------------------------------ |
| P-001       | Ollama                               | local runtime provider        | local LLM hosting for AI Agent / chatbox / experimentation       | candidate baseline | explicitly aligned with report direction                     |
| P-002       | Local Codex / VS Code runtime        | local execution/codegen layer | code generation, static analysis, guarded execution preparation  | active concept     | architecture layer rather than ordinary API provider         |
| P-003       | OpenAI API                           | external API provider         | optional external model/provider experiments                     | candidate          | should remain modular and optional                           |
| P-004       | Internal deterministic command layer | non-LLM provider mode         | known automation commands without generative provider dependency | active concept     | important for safe hybrid architecture                       |
| P-005       | Disabled / no-provider mode          | operational mode              | structural baseline without active AI provider dependency        | valid fallback     | useful for testing pyRevit extension loading and UI behavior |

---

## Current Baseline Position

The preferred project direction is:

- local-first
- modular
- provider-agnostic where possible
- safe and reviewable in Revit-facing workflows

## Risks

- provider logic becoming mixed into pyRevit UI scripts
- service folders retaining legacy assumptions
- unclear split between local codegen/runtime and chat/inference provider roles
- external provider dependence growing before local baseline is stabilized

## Next Action

In the next architecture pass:

- classify retained `Model_Service/` and `Openai_Server/`
- decide whether they are:
  - providers
  - services
  - orchestration layers
  - temporary legacy holdovers
