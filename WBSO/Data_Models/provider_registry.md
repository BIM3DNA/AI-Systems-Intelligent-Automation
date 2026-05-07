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

## 2026-04-10 Diagnostics Refinement

The provider-state path now carries safe diagnostic distinctions for:

- key present vs missing key
- provider reachable vs not reachable
- auth failure
- network failure
- request failure
- provider ready

The UI-local `local_only` state remains a presentation state used when the local planner is active or when cloud mode is unavailable.

## 2026-04-10 Self-Test Extension

The provider path now also exposes a developer-focused self-test surface that reports:

- environment key visibility
- module importability
- client initialization success
- provider probe request success
- runtime interpreter identity

Current workspace self-test classification:

- `network_failed`

## 2026-04-10 Responses API Note

The OpenAI planner adapter now targets the OpenAI Responses API for provider probing and supported-action normalization.

## 2026-05-06 AI-AGENT-002 Provider Boundary Note

AI-AGENT-002 Guided Project Startup Plan can run through deterministic local Project Context logic even when an external OpenAI request fails or is unavailable.

- no provider configuration was changed
- no provider/model runtime behavior beyond deterministic local fallback was validated
- Execute Plan remains governed by reviewed/catalog approval and was not tested in this validation session

## 2026-05-07 MEP-RO-001 Provider Boundary Note

The MEP-RO-001 validation failure demonstrates that deterministic BIM prompts requiring live Revit selection state must be intercepted before Ollama fallback.

- the observed generic responses came from fallback chat behavior, not validated Revit selection-report execution
- no provider configuration was changed
- no model/provider behavior beyond the observed fallback was validated
