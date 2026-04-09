# Provider Registry

## Project

AI Systems & Intelligent Automation

## Purpose

This file tracks provider categories and provider-boundary decisions for the repository.

| Provider ID | Provider Name | Type | Current Role | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| P-001 | Ollama | local runtime provider | low-risk chat and local code-generation support | active baseline | current runtime assumption retained |
| P-002 | Deterministic command layer | non-LLM execution mode | trusted direct execution of known Revit commands | active baseline | preserves safer baseline execution |
| P-003 | Approved recipe store | local reviewed execution asset | reviewed generated code saved for repeatable reuse | active | governance layer rather than inference provider |
| P-004 | OpenAI planner adapter | external provider | AI Agent cloud intent normalization for supported reviewed actions | active optional | unavailable when `OPENAI_API_KEY` is missing |

## 2026-04-09 Product Position

The active AI Agent surface currently rides on `P-002` and should be described as a deterministic reviewed-planner, not as a broad provider-orchestrating autonomous agent.

## 2026-04-09 Provider Integration Update

The current AI Agent planner path can now use:

- `P-002` for local deterministic intent matching
- `P-004` for optional OpenAI-backed intent normalization

Provider boundary rules:

- `P-004` only normalizes or rejects against the supported action list
- `P-004` does not execute code
- execution remains bound to `P-002` and the reviewed local recipe path
- missing-key and request-failure states are surfaced explicitly in the UI
