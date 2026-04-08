# Provider Strategy

## Project

AI Systems & Intelligent Automation

## Purpose

This file records the current provider/model strategy for the AI Systems & Intelligent Automation repository.

## Current Product-to-Provider Mapping

### Ollama Chat

- role: low-risk conversational help and prompt experimentation
- preferred provider mode: local Ollama runtime
- execution expectation: no direct model modification from chat itself

### ModelMind

- role: primary user-facing task surface
- preferred provider mode: deterministic command layer first, local code generation second
- execution expectation: deterministic recipes are preferred; generated code still requires review/approval

### AI Agent

- role: advanced reviewed plan/execution surface
- preferred provider mode: reviewed deterministic plan generation in the current pass
- execution expectation: modifying commands remain guarded and destructive tools are off by default

## Current Provider Categories

| Provider ID | Provider Name | Type | Current Role | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| P-001 | Ollama | local runtime provider | local chat and local code-generation assistance | active baseline | retained for current baseline |
| P-002 | Local deterministic command layer | non-LLM execution mode | trusted deterministic ModelMind and agent execution paths | active baseline | used to preserve safer runtime behavior |
| P-003 | Local approved-recipe store | local reviewed asset mode | reviewed generated code saved for repeatable local reuse | new active component | not a model provider but part of execution governance |
| P-004 | External API providers | external API provider | future optional adapters | candidate | still optional and modular |

## Rules Still in Force

1. Provider-specific logic should not dominate the pyRevit button script.
2. Deterministic execution should remain available without requiring an external provider.
3. Generated code should remain reviewable before execution.
4. Modifying execution in AI Agent should remain explicitly guarded.

## Current Validation Limit

The provider/runtime split has been implemented structurally in code, but live post-refactor provider behavior has not yet been revalidated in Revit.
