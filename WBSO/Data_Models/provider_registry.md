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
| P-004 | External API provider adapters | external provider | future optional cloud-backed integrations | candidate | not required for this pass |
