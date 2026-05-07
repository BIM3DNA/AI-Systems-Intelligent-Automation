# Model Registry

## Purpose

This file tracks the repo-local data/state models introduced for the current AI window architecture.

| Model ID | Asset | Type | Purpose | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| M-001 | `AI.extension/lib/prompt_catalog.json` | structured prompt catalog | backs the ModelMind available prompts tree with explicit metadata | active | deterministic and semi-generative recipe definitions |
| M-002 | `AI.extension/lib/approved_recipes.json` | reviewed recipe store | stores successful approved reviewed code as reusable local recipes | active | separate from the base prompt catalog |
| M-003 | local window settings file via `ai_local_store.py` | local UI state | persists dark/light theme selection locally | active | local filesystem path resolved at runtime |
| M-004 | agent session state via `ai_agent_session.py` | in-memory session model | holds current AI Agent goal, reviewed plan, toggle state, and execution status | active | session-scoped, not persistent across launches |
| M-005 | reviewed code preview state in `script.py` | UI state model | holds secondary reviewed-code visibility/content separate from the main result history | active | supports show/hide reviewed code UX |
| M-006 | planner provider state via `Model_Service/ModelService.py` + `chatgpt_service.py` | provider state model | reports local/cloud planner availability, key presence, provider reachability, and classified error state to the AI Agent UI | active | cloud path requires `OPENAI_API_KEY` from environment |
| M-007 | reviewed plan object via `ai_agent_session.py` | structured plan model | captures `matched_action`, `confidence`, `requires_modification`, `destructive`, `summary`, and `execution_ready` | active | execution remains constrained to supported deterministic/reviewed actions |
| M-008 | candidate reviewed deterministic action registry entry in `prompt_catalog.json` | catalog candidate model | records near-term but not yet enabled planner actions such as selected-duct total-volume reporting | candidate | not part of the active supported action set yet |

## 2026-05-06 AI-AGENT-002 Model Note

AI-AGENT-002 uses the existing cached Project Context and Project Onboarding data models to build a guided startup plan.

- no new persisted model store was introduced
- plan objects remain in-memory/session-scoped
- deterministic Project Context fallback can produce the guided plan without relying on a successful external provider request
- provider configuration was not changed

## 2026-05-07 MEP-RO-001 Selection Routing Note

The failed MEP-RO-001 validation shows that live Revit selection reports cannot rely on cached Project Context selection data alone.

- selection-report handlers must read `uidoc.Selection.GetElementIds()` at execution time
- deterministic BIM prompts that require live Revit state must not fall back to Ollama
- no new persisted model or provider configuration change is implied by this failure
