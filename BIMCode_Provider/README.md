# BIMCode M3A: text-only Python provider sidecar

Final audit: 2026-09-18; M3A_READY_FOR_CLOSURE_WITH_NONBLOCKING_GAPS.
Required live connectivity PASS (user-reported); source-control closure PENDING.
No authenticated request was made by implementation or this audit. Dependency
foundation: `4b1a9fee6d4a3cd736fb123a815743087561071f` (committed/pushed).
M1 and M2 remain source-control closed. No hours or evidence IDs allocated.

## Runtime and dependency ownership

The persistent pane runs in IronPython 2.7.12, which cannot host the modern SDK.
The authorized Python 3 child uses **only** `<repo>/.venv/Scripts/python.exe`;
missing runtime fails closed, with no PATH fallback or automatic installation.
Python 3.10.11 and official OpenAI SDK 3.15.0 are the tested development versions.
Install `requirements_sidecar.txt` independently. It pins the direct SDK, not
the entire transitive environment. `requirements_full.txt` is legacy material;
its PySimpleGUI availability and inflect conflict are outside M3A scope.
The development .venv is not a distribution strategy; packaging is deferred.

## Existing service reuse decision: C, deliberately not reused

`Openai_Server/chatgpt_service.py` imports json/os/sys and the SDK lazily. Its
provider-state path performs a real paid probe; it defaults a model, exposes raw
exception details in parts of its protocol, supplies temperature, and supports
Workbench action normalization. `Model_Service/ModelService.py` uses subprocess
with configurable/PATH runtime candidates and can propagate stderr. These
contracts do not satisfy M3A local-only readiness, fixed process paths, configured
model, secret isolation or error protocol. Extraction would change legacy callers.
Both files remain unchanged. The small SDK create/output_text pattern is retained,
but its policy/config/error wrappers are deliberately independent, not a second
planner or generic command facility.

## Configuration and protocol

Only the child reads configuration: process OPENAI_API_KEY / OPENAI_MODEL override
repo-root .env.local per key, including explicit empty values. Complete environment
configuration skips the file. UTF-8 KEY=VALUE, blank/comment lines, trimmed outer
whitespace and simple matching quotes are supported; unknown keys ignored,
duplicate supported file keys rejected. No interpolation or shell evaluation.
File capped at 64 KiB; malformed/unreadable configuration gives INVALID_CONFIG.
States: READY, MISSING_API_KEY, MISSING_MODEL, INVALID_CONFIG. Repr reports only state.
No fallback model. Key/model validation rejects control characters and key echoes.

One process, one stdin JSON request, one stdout JSON response, then exit. Protocol
version 1; request_id is a 32-character lowercase hexadecimal correlation token.
Operations: readiness (local configuration and SDK import only), text_response
(user_text, max 2000 characters). No extra fields, duplicate keys, credentials,
context, files, executable paths or tool descriptions accepted. Request max 20000
characters. Response fields: protocol_version, request_id, ok, provider, model,
text, error. Errors contain code and fixed message, not exceptions or SDK objects.
The IronPython adapter validates schema/ID/exit code and substitutes local error
messages. Raw stderr is drained but never rendered or logged.

Readiness runs once on pane initialization and on explicit Check AI config. It
does NOT authenticate or call OpenAI. Send is enabled only with local readiness,
nonempty input and no active provider operation. Configuration is reloaded for
every Send. A configuration failure disables Send until Check AI config succeeds;
transient/auth/provider failures release the gate and permit a deliberate retry.

## Network and concurrency boundary

The sole M3A network exception is provider.py -> official SDK Responses API at
fixed https://api.openai.com/v1. No configurable endpoint, redirects, environment
proxy, retries, tools, search, MCP, conversation persistence or background API mode.
SDK custom-header/admin/org/project configuration is not inherited. Library stdout,
stderr and logs are suppressed inside the child; known credential echoes in model
text are rejected. The fixed instruction says text-only, no Revit/model/tool access.
Responses uses configured model, max_output_tokens=2048, store=False,
background=False. SDK timeout 45 seconds; incomplete responses are failures.
Output text capped at 12000 characters with explicit truncation notice. Existing
16000-character / 400-block pane budget, themes and Find remain authoritative.

System.Diagnostics.Process uses a fixed executable/script, no shell, hidden window,
redirected pipes, isolated Python flags (-I -B -X utf8). Prompt only travels through
stdin. A background .NET thread runs scalar process work only; completion is queued
through WPF Dispatcher.BeginInvoke. No Revit objects/API access on that thread.
Input-write wait is 5 seconds; process wait 75 seconds, bounded stream-completion
waits; timed-out child is killed/disposed. There is no service, polling or timer.
Dispatcher shutdown drops completion because the UI session is ending.
M2 deterministic buttons and ExternalEvent remain separate/unchanged. Provider and
ModelMind results share the existing result viewer; whichever completes last is
displayed. AI text is always marked AI Response and cannot execute actions.

## Normalized failures

CONFIG_MISSING_API_KEY, CONFIG_MISSING_MODEL, INVALID_CONFIG,
PYTHON_RUNTIME_UNAVAILABLE, SIDECAR_START_FAILED (including missing script),
SIDECAR_TIMEOUT, SIDECAR_PROTOCOL_ERROR, SIDECAR_NONZERO_EXIT,
SIDECAR_REQUEST_ID_MISMATCH, OPENAI_AUTH_ERROR, OPENAI_RATE_LIMIT,
OPENAI_QUOTA_OR_BILLING, OPENAI_TIMEOUT, OPENAI_CONNECTION_ERROR,
OPENAI_API_ERROR, OPENAI_EMPTY_RESPONSE, INTERNAL_PROVIDER_ERROR.

## Offline validation

- 166 Python tests PASS: 119 unchanged M1/M2 + 47 M3A test methods (some table-driven).
- 10 native IronPython process/dispatcher probes PASS using a fake child only:
  success, stderr drain, malformed JSON, ID mismatch, nonzero exit, timeout,
  missing runtime, missing script, start failure, real worker -> WPF dispatcher.
- AST/py_compile/tabnanny: 24 Python files PASS. IronPython compile: three M3A
  Revit-side files PASS. Existing native WPF XAML/text/theme/Find probe PASS.
- 1475 Workbench function bodies source-identical to M1; catalog 237 unchanged.
- Lifecycle, tools/routing, headless seam, old service/launcher unchanged.
- Static mutation/host-neutral/network-boundary checks PASS; pip check PASS.
- Real .env.local was NOT read in this audit. Tests use fake config in temp dirs.

These are offline host-harness checks, not live Revit 2025.4 validation.

## Original user-run live procedure (completed; retained for reproduction)

Restart Revit/pyRevit to load the updated pane. Ensure the controlled .venv exists
with requirements_sidecar.txt installed and configure .env.local privately. Check
AI config must report local readiness without an API request. Enter:

`Reply with exactly: BIMCode AI OpenAI connection OK`

Click Send once. Confirm disabled Send during Thinking, responsive Revit, assistant
text under AI Response, configured model, restored Send, no secret output, no
ModelMind execution and no model/view/selection mutation. Exact wording alone is
not the sole success criterion. Confirm Find and theme rendering on this result.

Only after connectivity passes, send:
`What application are you running inside, and what can you do in this milestone?`
Expect Revit text-only conversation and no model inspection/modification or
ModelMind tools. Recheck the four deterministic buttons independently. Do not
intentionally invalidate real credentials or perform billing failure tests.

## Future host neutrality

Config/provider/protocol have no Revit, pyRevit, WPF or ModelMind imports. Future
AutoCAD/DrawingMind or ScanAI host adapters may reuse this boundary. The possible
ScanAI -> symbol detection -> DrawingMind/DWG coordinates -> deterministic transform
-> Revit placement-candidate path remains future design only; no AutoCAD code exists.

## Final closure-readiness assessment (2026-09-18)

User-supplied evidence, not tests newly performed by this audit:

| Case | Coverage / result | Observation |
| --- | --- | --- |
| LIVE-M3A-01 | COVERED / PASS | Local readiness: Text provider ready (authentication untested); no network claim or secret exposure. |
| LIVE-M3A-02 | COVERED / PASS | OpenAI / gpt-6-astra / COMPLETE; exact BIMCode AI OpenAI connection OK reply; Send recovered. |
| LIVE-M3A-03 | COVERED / PASS | Response identified Revit, text-only assistance, no active-model inspection/modification and no ModelMind tools. |
| LIVE-M3A-04 | COVERED / PASS | After AI, one Pipe Summary returned PIPING_SELECTION_SUMMARY_OK / COMPLETE / PIPING-RO-001-A01; no AI substitution. |

LIVE-02 establishes authentication, account/model access and transport at that
time, not permanent entitlement. The configured model is reported evidence, not
a hard-coded implementation choice. LIVE-04 reported one supported/processed Pipe,
23000.0 mm, Default type, Carbon Steel - Schedule 40, ASSIGNED to Hydronic Supply 5,
150.0 mm diameter, no warnings. No ModelMind execution on Send or mutation reported.

All offline validation totals above were rerun and passed at final audit. Runtime,
tests and manifests were not edited by the audit; documentation alone was updated.
Current runtime defects: NONE FOUND. M3B NOT STARTED. M1/M2 remain closed.
No required live blocker remains for this bounded connectivity milestone.
Auth/quota/rate-limit/timeout live injection is nonblocking: normalized SDK mocks,
fake-child process tests and native dispatcher tests cover failure/recovery;
do not invalidate real credentials or burn credit merely to reproduce them.
Optional evidence: live theme toggle, long response, more sequential prompts,
document switching during a request, pyRevit reload and already-open document tabs.

Limits retained: stream size is checked after ReadToEndAsync, not incrementally;
the child is fixed trusted code with bounded protocol output, not a sandbox for
arbitrary executables. Environment-sourced keys may be inherited by Revit from its
launcher, but the adapter never reads/transports them; file-sourced keys are loaded
only by the child. Credential-pattern/source review found no embedded credentials;
the actual secret was not read or equality-compared. No universal absence proof is
claimed. No post-live byte snapshot was supplied; the audit-start delta exactly
matches the reported pre-live scope, but totals alone cannot prove byte identity.

Evidence/Daily Log/KC IDs and hours: PENDING, none allocated. Implementation and
documentation remain unstaged/uncommitted/unpushed. Recommended reviewed combined
commit subject: feat(bimcode): add OpenAI sidecar connectivity. Approval required.

Reproduction commands (offline; never run the real sidecar against real config):

```powershell
.venv/Scripts/python.exe -B -m unittest discover -s tests -p 'test_*.py'
powershell -NoProfile -File tests/test_bimcode_provider_native.ps1
powershell -NoProfile -File tests/test_bimcode_result_find_wpf.ps1
.venv/Scripts/python.exe -B -m pip check
git diff --check
```
