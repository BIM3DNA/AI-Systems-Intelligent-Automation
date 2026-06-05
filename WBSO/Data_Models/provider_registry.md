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

## 2026-05-07 MEP-RO-001 Hotfix Provider Boundary Note

After the MEP-RO-001 routing/live-selection hotfix, the known selection-report prompts no longer fall through to generic Ollama fallback.

- deterministic Revit API handlers produced the validated selected-element reports
- Ollama did not produce the selected-element reports
- no provider configuration was changed
- provider boundary remains: deterministic BIM commands handle live Revit selection state; conversational providers remain fallback only for non-deterministic questions

## 2026-05-07 MEP-RO-002 / MEP-RO-003 Provider Boundary Note

Ollama/OpenAI fallback is intentionally bypassed for known MEP-RO-002 and MEP-RO-003 prompts.

- runtime validation confirmed deterministic routing for known active-view and system-assignment prompts
- deterministic Revit API handlers produced the validated reports
- provider failure should not affect these deterministic report paths
- no provider configuration was changed

## 2026-05-07 MEP-RO-004 Provider Boundary Note

Ollama/OpenAI fallback is intentionally bypassed for known MEP-RO-004 discipline-QA prompts.

- runtime validation confirmed deterministic routing for selected and active-view discipline QA reports
- deterministic Revit API handlers produced the validated QA outputs
- provider failure should not affect known MEP-RO-004 report paths
- no provider configuration was changed

## 2026-05-14 MEP-RO-005 Provider Boundary Note

Ollama/OpenAI fallback is intentionally bypassed for MEP-RO-005 export prompts.

- runtime validation confirmed deterministic routing for export prompts
- generic Ollama responses are rejected as deterministic QA evidence
- export behavior depends on session-local deterministic report state, not provider output
- no provider configuration was changed

## 2026-05-17 MEP-RO-006 Provider Boundary Note

MEP-RO-006 index prompts route deterministically before Ollama/OpenAI fallback.

- Ollama/OpenAI are not used for index reading or index writing
- index outputs are based on local filesystem metadata only
- generic Ollama responses remain non-exportable as deterministic QA evidence
- no provider configuration was changed

## 2026-05-17 MEP-ACT-001 Provider Boundary Note

MEP-ACT-001 proposal prompts route deterministically before Ollama/OpenAI fallback.

- Ollama/OpenAI are not used for reviewed action proposal preflight
- supported proposal prompts read live Revit context locally and safely
- generic Ollama responses remain non-exportable as deterministic QA evidence
- no provider configuration was changed

## 2026-05-18 MEP-WR-001 Provider Boundary Note

MEP-WR-001 split dry-run prompts route deterministically before Ollama/OpenAI fallback.

- Ollama/OpenAI are not used for split candidate dry-runs
- candidate reports are generated from live selected elements in the active document
- generic Ollama responses remain non-exportable as deterministic QA evidence
- no provider configuration was changed

## 2026-05-18 MEP-ACT-002 Provider Boundary Note

MEP-ACT-002 confirmation/status prompts route deterministically before Ollama/OpenAI fallback.

- Ollama/OpenAI are not used for confirmation guard decisions
- apply/execute prompts are blocked locally and deterministically
- generic Ollama responses remain non-exportable as deterministic QA evidence
- no provider configuration was changed

## 2026-05-19 MEP-WR-002 Provider Boundary Note

MEP-WR-002 rollback-test prompts route deterministically before Ollama/OpenAI fallback.

- LLM providers are not used to decide rollback-test eligibility or transaction execution
- tokenized rollback-test prompts are routed after stripping/detecting `ROLLBACK-TEST-OK`
- generic LLM output remains rejected by export as deterministic evidence
- no provider configuration was changed

## 2026-05-19 MEP-WR-003 Provider Boundary Note

MEP-WR-003 reviewed-apply prompts route deterministically before Ollama/OpenAI fallback.

- LLM providers are not used to choose candidates, decide eligibility, or execute persistent apply
- persistent apply requires explicit candidate selection and `PERSISTENT-SPLIT-OK`
- generic `apply reviewed action` and `execute latest proposal` remain blocked by deterministic MEP-ACT-002 guard logic
- generic LLM output remains rejected by export as deterministic evidence
- no provider configuration was changed

## 2026-05-25 MEP-WR-005 Provider Boundary Note

MEP-WR-005 source-consumption prompts route deterministically before Ollama/OpenAI fallback.

- LLM providers are not used to decide source freshness, consumed-source state, or persistent-apply eligibility
- status prompts such as `show split apply source state` and `split apply staleness status` are provider-independent
- MEP-WR-003 apply routes consult MEP-WR-005 session state before any transaction path
- generic LLM output remains rejected by export as deterministic evidence
- no provider configuration was changed

## 2026-06-03 COORD-WR-001 to COORD-WR-003 Provider Boundary Note

COORD-WR-001, COORD-WR-002, and COORD-WR-003 prompts route deterministically before Ollama/OpenAI fallback.

- LLM providers are not used to audit link transforms, decide rollback eligibility, store passed rollback source, or execute reviewed origin reset.
- COORD-WR-002 requires explicit `ROLLBACK-LINK-RESET-OK` before rollback transaction logic.
- COORD-WR-003 requires explicit `PERSISTENT-LINK-RESET-OK` before persistent apply logic.
- Generic LLM output remains rejected by export as deterministic evidence.
- No provider configuration was changed.

## 2026-06-05 COORD-WR-005 Provider Boundary Note

COORD-WR-005 prompts route deterministically before Ollama/OpenAI fallback.

- LLM providers are not used to aggregate coordination state or classify workflow readiness.
- The dashboard reads serializable shared/session state and the deterministic QA export index.
- COORD-WR-005 does not invoke audit, rollback, apply, or verification behavior.
- Generic LLM output remains rejected as deterministic QA evidence.
- No provider configuration was changed.

## 2026-06-04 COORD-WR-004 Provider Boundary Note

COORD-WR-004 prompts route deterministically before Ollama/OpenAI fallback.

- LLM providers are not used to choose verification targets, interpret link transforms, or decide verification result.
- COORD-WR-004 reads the stored latest applied state and/or current selected link deterministically.
- Stored element id use is read-only verification only.
- Generic LLM output remains rejected by export as deterministic evidence.
- No provider configuration was changed.
