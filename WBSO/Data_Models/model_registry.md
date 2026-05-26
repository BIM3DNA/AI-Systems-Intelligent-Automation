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

## 2026-05-07 MEP-RO-001 Hotfix Validation Note

MEP-RO-001 now avoids generic Ollama fallback for known selection-report prompts after the routing/live-selection hotfix.

- deterministic Revit API handlers produced the validated selected-element reports
- handlers read the current live selection through `uidoc.Selection.GetElementIds()` and resolve elements with `doc.GetElement(id)`
- no new persisted model store was introduced
- no provider configuration was changed

## 2026-05-07 MEP-RO-002 / MEP-RO-003 Model Note

MEP-RO-002 and MEP-RO-003 are deterministic Revit API diagnostics, not model-provider features.

- known prompts do not depend on LLM output
- active-view reports read current active-view elements at execution time
- system assignment reports read current selection or active-view elements at execution time
- routing is deterministic before Ollama fallback
- no new persisted model store was introduced
- no provider configuration was changed

## 2026-05-07 MEP-RO-004 Model Note

MEP-RO-004 is not an LLM model-provider feature. It is a deterministic Revit API rule-evaluation layer routed before Ollama/OpenAI fallback for known discipline-QA prompts.

- selection-scope QA reads current selected elements at execution time
- active-view QA reads current active-view elements at execution time
- rule results are computed locally from safe readable Revit parameters/properties
- grouped sample ElementIds are deduplicated after the duplicate-rule aggregation hotfix
- no new persisted model store was introduced
- no provider configuration was changed

## 2026-05-14 MEP-RO-005 Model Note

MEP-RO-005 is not an LLM model-provider feature. It is a deterministic evidence-export layer for the latest accepted AI Workbench report.

- export prompts do not call Ollama/OpenAI
- generic Ollama outputs are not exported as deterministic QA evidence
- latest deterministic report state is session-local
- exported metadata records document/view context, source prompt, source header, report scope, and safety flags
- generated files are filesystem evidence artifacts only
- no persisted Revit model store was introduced
- no provider configuration was changed

## 2026-05-17 MEP-RO-006 Model Note

MEP-RO-006 is not an LLM model-provider feature. It is a deterministic filesystem index layer for exported QA evidence snapshots.

- index files are local filesystem artifacts
- index prompts do not call Ollama/OpenAI
- index entries record export metadata and safety/governance fields
- generic Ollama output remains rejected as deterministic export evidence
- no persisted Revit model store was introduced
- no provider configuration was changed

## 2026-05-17 MEP-ACT-001 Model Note

MEP-ACT-001 is not an LLM model-provider feature. It is a deterministic reviewed-action proposal/preflight layer.

- supported proposal prompts bypass Ollama/OpenAI
- proposal state is session-local
- split-selected-pipes preflight reads live selection only
- future action placeholders remain proposal-only
- no execution state, transaction, or write-action model was introduced
- generic Ollama output remains rejected as deterministic export evidence
- no provider configuration was changed

## 2026-05-18 MEP-WR-001 Model Note

MEP-WR-001 is not an LLM model-provider feature. It is a deterministic Revit selection dry-run and candidate reporting layer.

- supported prompts bypass Ollama/OpenAI
- dry-run state is session-local and exportable through deterministic report state
- midpoint split candidates are non-executable evidence only
- no transaction, pipe split, connector traversal, geometry extraction, linked-document scan, parameter write, or model mutation was introduced

## 2026-05-18 MEP-ACT-002 Model Note

MEP-ACT-002 is not an LLM model-provider feature. It is a deterministic confirmation guard layer.

- supported confirmation/status prompts bypass Ollama/OpenAI
- guard state is session-local and exportable through deterministic report state
- confirmation/apply/execute prompts are blocked until a future reviewed apply feature exists
- generic Ollama output remains rejected as deterministic export evidence
- no provider configuration was changed

## 2026-05-19 MEP-WR-002 Model Note

MEP-WR-002 is not an LLM model-provider feature. It is deterministic Revit API rollback-test logic for split dry-run candidates.

- supported rollback-test prompts bypass Ollama/OpenAI
- `ROLLBACK-TEST-OK` gates transaction opening
- `PlumbingUtils.BreakCurve` is used only inside a rollback transaction group
- rollback-test state is session-local and exportable through deterministic report state
- no persistent model store was introduced
- generic Ollama output remains rejected as deterministic export evidence

## 2026-05-19 MEP-WR-003 Model Note

MEP-WR-003 is not an LLM model-provider feature. It is deterministic reviewed apply logic for one rollback-tested split candidate.

- supported reviewed-apply prompts bypass Ollama/OpenAI
- candidate eligibility is decided from MEP-WR-001 and MEP-WR-002 session state, not provider output
- `PERSISTENT-SPLIT-OK` gates persistent transaction execution
- exactly one candidate can be applied per command
- generic Ollama output remains rejected as deterministic export evidence
- no provider configuration was changed

## 2026-05-25 MEP-WR-005 Model Note

MEP-WR-005 is not an LLM model-provider feature. It is a session-local governance state layer for split apply source consumption and staleness.

- state object: `latest_split_apply_consumed_source_state`
- records `consumed_by_feature_id`, consumed timestamp, dry-run source timestamp, rollback-test source timestamp, applied candidate number, applied original pipe id, returned new pipe id, consumed true/false, and persistent-apply eligibility
- marks a MEP-WR-001 dry-run / MEP-WR-002 rollback-test source as consumed only after successful MEP-WR-003 persistent apply
- blocks second persistent apply attempts from the consumed source before transaction
- requires a new successful rollback-test after the consumed timestamp before persistent apply is eligible again
- exposes `[SPLIT APPLY SOURCE STATE]` as a deterministic source-state report
- runtime validated in BUNGE on 2026-05-25

## 2026-05-26 MEP-WR-006 Model Note

Feature ID: MEP-WR-006
Feature: Split Result Visual Review / Select Elements Helper
Status: Runtime validated
Evidence: EV-AI-125 to EV-AI-132

MEP-WR-006 is a deterministic UI-only visual review helper for verified split results. It selects/highlights original and returned pipe elements from latest WR-004 / WR-003 state or explicit IDs.

- primary export: `C:\Users\User\Desktop\Results\AI_Workbench\QA_Exports\20260526_180331`
- validated original pipe id: `3003513`
- validated returned new pipe id: `3130262`
- no transaction
- no BreakCurve
- no model mutation
- UI selection only
