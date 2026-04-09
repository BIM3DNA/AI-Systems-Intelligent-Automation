# AI Systems & Intelligent Automation

This repository contains a pyRevit-delivered AI workbench with one Revit entry point and one window.

## Current Product Surfaces

- `Ollama Chat`: low-risk conversational help and prompt experimentation
- `ModelMind`: primary workflow for deterministic and semi-generative BIM task recipes
- `AI Agent`: advanced reviewed planning/execution surface with destructive tools disabled by default

## Key Implementation Artifacts

- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/script.py`
- `AI.extension/AI.tab/Dev.panel/AI_01.pushbutton/UI.xaml`
- `AI.extension/lib/prompt_catalog.json`
- `AI.extension/lib/approved_recipes.json`
- `AI.extension/lib/ai_prompt_registry.py`
- `AI.extension/lib/ai_local_store.py`
- `AI.extension/lib/ai_agent_session.py`
- `AI.extension/lib/ai_reviewed_code.py`
- `Openai_Server/chatgpt_service.py`
- `Model_Service/ModelService.py`

## Current Validation Position

The earlier migration baseline was runtime-validated in pyRevit at UI-launch level. Current live findings additionally confirm theme persistence, Ollama Chat, and deterministic ModelMind tasks. The reviewed-code hardening patch is implemented, but its new blocking/save-flow behavior still requires live post-patch validation in pyRevit/Revit.

## Current Product Framing

- `ModelMind` is the main BIM task surface
- `Ollama Chat` remains the low-risk conversation area
- `AI Agent` is currently a smaller deterministic reviewed-planner, not a broad autonomous agent

## Planner Provider Configuration

- local planning is always available through the deterministic action matcher
- optional cloud planning is available only when `OPENAI_API_KEY` is present in the environment
- cloud planning only normalizes user requests into the supported reviewed action set
- cloud output does not execute as raw code inside pyRevit

## 2026-04-09 Pass Position

Implemented in code:

- ModelMind bottom input/action layout polish
- AI Agent provider-backed planning path
- explicit local/cloud provider-state messaging

Still pending live Revit validation after this pass:

- ModelMind layout polish in runtime
- AI Agent local planner cases after the latest changes
- AI Agent OpenAI planner normalization with a valid key
- missing-key and request-failure runtime behavior
