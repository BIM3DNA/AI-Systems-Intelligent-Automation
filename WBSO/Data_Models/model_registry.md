# Model Registry

## Purpose

This file tracks the repo-local data/state models introduced for the current AI window architecture.

| Model ID | Asset | Type | Purpose | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| M-001 | `AI.extension/lib/prompt_catalog.json` | structured prompt catalog | backs the ModelMind available prompts tree with explicit metadata | active | deterministic and semi-generative recipe definitions |
| M-002 | `AI.extension/lib/approved_recipes.json` | reviewed recipe store | stores successful approved reviewed code as reusable local recipes | active | separate from the base prompt catalog |
| M-003 | local window settings file via `ai_local_store.py` | local UI state | persists dark/light theme selection locally | active | local filesystem path resolved at runtime |
| M-004 | agent session state via `ai_agent_session.py` | in-memory session model | holds current AI Agent goal, reviewed plan, toggle state, and execution status | active | session-scoped, not persistent across launches |
