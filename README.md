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

## Planner Provider Diagnostics

The AI Agent provider path now distinguishes:

- missing key
- key present
- auth failure
- network failure
- request failure
- provider ready
- local-only UI state

Safe diagnostics surfaced to the UI include:

- key present: yes/no
- provider reachable: yes/no
- last error category

The cloud planner also now exposes a developer-focused self-test request:

- `cloud planner self test`

It reports:

- env key visibility
- `openai` importability
- client initialization success
- provider probe request success
- runtime interpreter identity

## Shared Reviewed Action Registry

- ModelMind now acts as the visible source-of-truth reviewed action library
- AI Agent now plans and routes over that same reviewed action registry
- approved recipes remain a separate branch and are not a second planner action inventory

The cloud service path now uses the OpenAI Python client via the Responses API for:

- minimal provider probe
- supported-action normalization

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

## Still Unsupported In AI Agent

- reviewed deterministic schedule creation
- quantity schedule generation
- arbitrary non-reviewed cloud code execution

Broader schedule-generation requests remain unsupported unless they are implemented as reviewed deterministic actions.

## 2026-04-10 Shared Registry Position

The shared reviewed action registry now contains the initial HVAC, piping, electrical, QA/BIM, and low-risk write action set, and the AI Agent local planner normalizes against that same registry.

## 2026-04-13 Expanded MEP Position

Latest reported live-validated actions carried into the current pass:

- Ollama Chat with `phi3:mini`
- ModelMind:
  - `select all ducts`
  - `count ducts in active view`
  - `list ducts in active view`
  - `create sheet`
- AI Agent:
  - `select ducts`
  - `count selected ducts`
  - `count ducts in active view`
  - `list ducts in active view`
- reviewed create-sheet flow
- approved recipe save/load

This pass expands the shared reviewed MEP action set further for piping, electrical, QA/BIM, and low-risk write actions while keeping execution deterministic and reviewed.

Known limitation carried into this pass:

- heavier local models such as `gemma3:27b` may be unstable in runtime, while `phi3:mini` is the stable recommended model

## Current Workspace Cloud Planner Finding

The current workspace self-test through the actual service path reports:

- `env_key_present: yes`
- `openai_module_importable: yes`
- `client_init_ok: yes`
- `failure_category: network_failed`

That points to provider/network reachability as the next likely fix for cloud planning in the runtime used by the subprocess service.
