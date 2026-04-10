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
| P-004 | OpenAI planner adapter | external API provider | AI Agent cloud intent normalization for supported reviewed actions only | active optional path | requires `OPENAI_API_KEY` from environment |

## Rules Still in Force

1. Provider-specific logic should not dominate the pyRevit button script.
2. Deterministic execution should remain available without requiring an external provider.
3. Generated code should remain reviewable before execution.
4. Modifying execution in AI Agent should remain explicitly guarded.

## Current Validation Limit

The provider/runtime split has been implemented structurally in code, but live post-integration provider behavior has not yet been revalidated in Revit.

## 2026-04-09 Planner Position

For the current runtime, the AI Agent surface should be treated as:

- deterministic
- reviewed
- narrow in scope
- guidance-first when unsupported

It should not be presented as a broad autonomous agent until richer planner/runtime coverage genuinely exists.

## 2026-04-09 Provider Integration Update

The current planner stack is now:

- local planner path: deterministic local intent matcher for the supported BIM action set
- cloud planner path: OpenAI-backed request normalization through `Openai_Server/chatgpt_service.py` and `Model_Service/ModelService.py`

Rules added in this pass:

1. `OPENAI_API_KEY` is loaded from environment only.
2. Cloud planning must be disabled when the key is missing.
3. Cloud planning may only select or reject from the supported action list.
4. Cloud output must never execute directly as raw code.
5. Execution remains inside the pyRevit-reviewed deterministic command/recipe path.

Current live position:

- provider integration implemented in code
- missing-key and request-failure states surfaced in UI
- live Revit verification for cloud planning still pending

## 2026-04-10 Provider Diagnostics Update

The provider boundary now distinguishes:

- key presence
- provider reachability
- provider-ready vs failed request states

Safe diagnostic fields now expected across the provider path:

- `key_present`
- `provider_reachable`
- `last_error_category`
- `state`

Current failure classes surfaced for UI use:

- `missing_key`
- `missing_openai_module`
- `client_init_failed`
- `auth_failed`
- `network_failed`
- `request_failed`
- `provider_ready`

UI rule tightened in this pass:

- `Set OPENAI_API_KEY...` guidance must appear only for `missing_key`

Still pending live validation:

- key-present but request-failed reporting in live Revit
- accurate category display for cloud failures in live Revit

## 2026-04-10 Self-Test Position

The cloud planner service path now exposes a self-test that reports the actual runtime used for provider requests.

Current workspace self-test result after runtime dependency fix:

- key visible in runtime: yes
- `openai` importable in runtime: yes
- client initialization in runtime: yes
- classified failure: `network_failed`

This indicates the next likely fix is provider/network reachability from the Python interpreter used by the cloud planner subprocess.

## 2026-04-10 Responses API Position

The OpenAI planner service path now uses the OpenAI Python client via the Responses API for both:

- minimal provider probe
- intent normalization requests

Current blocker remains unchanged after that wiring update:

- the runtime used by the subprocess cannot yet complete a provider request due to `network_failed`
