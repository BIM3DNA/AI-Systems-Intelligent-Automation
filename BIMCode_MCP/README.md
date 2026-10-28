# BIMCode read-only MCP adapter

Package: **BIMCODE-MCP-RO-001**, local pilot, live Revit acceptance pending.

Use Codex, Claude Code or a compatible VS Code assistant to inspect the current
Revit selection through the existing ModelMind tools. The adapter makes no model
API calls and needs no OpenAI API key or Claude-specific code. The chosen AI
client handles its own model/subscription and receives the returned model facts.

This belongs in the existing AI repository. Keep the root `AGENTS.md` and
`PROJECT_STATE.md`; a second repository or duplicate state files are unnecessary.
`AGENTS.md` governs engineering, `PROJECT_STATE.md` records implementation and
validation, and this README explains installation. MCP client configuration is
separate from all three.

## Scope and architecture

| MCP tool | Existing host capability |
| --- | --- |
| `get_revit_context` | Cached document title plus a new single-use context token |
| `summarize_selected_pipes` | `PIPING-RO-001-A01` |
| `inspect_selected_pipe_connectors` | `PIPING-RO-001-A02` |
| `summarize_selected_mep_elements` | `MEP-MULTI-RO-001-A01` |

A client starts `server.py` over MCP **stdio**. The server connects to an
explicitly enabled, authenticated **loopback TCP** bridge inside Revit. A worker
posts scalar requests to the pane's UI dispatcher. The existing read-only
coordinator schedules the existing `ExternalEvent`; only its `Execute` callback
reads Revit and runs the closed ModelMind builders/composite.

No new Revit event executor, domain rules, generated-code execution, generic
command, arbitrary element IDs, write tools, provider continuation or catalog
routes. Existing M4A/M4B write research remains separate. The active provider's
13-tool registry is unchanged. MCP exposes only the three inspections above.

Context tokens expire in 30 seconds, are single-use and bind document identity,
activation generation, selection generation and a bridge-owned model-change
epoch. Switch-away/back, selection changes, model edits, timeout and stop reject
queued inspections. One host inspection is active at a time; pane/provider work,
write ownership, pending continuations and retained safety locks block admission.
The existing coordinator owns and clears each turn. Classification, reason codes,
units, partial states and transport omission markers are retained unchanged.

## Windows setup

Prerequisites: the repository's supported Revit 2025.4 / pyRevit environment and
CPython 3.10+ on **the same Windows machine**. The server was tested here with
CPython 3.12; the pinned SDK declares Python >=3.10. Native IronPython/.NET/Revit
acceptance still needs the manual tests below. SDK v1.30 is pinned to retain the
existing Python 3.10 baseline; upgrading to SDK v2 is a separate migration.

From the existing repository in PowerShell:

```powershell
py -3 -m venv BIMCode_MCP\.venv
.\BIMCode_MCP\.venv\Scripts\python.exe -m pip install -r BIMCode_MCP\requirements.txt
.\BIMCode_MCP\.venv\Scripts\python.exe -I -B BIMCode_MCP\server.py --help
```

The dedicated environment keeps MCP dependencies separate from the existing
OpenAI sidecar. No secrets or `.env` files need to be copied.

1. Restart Revit fully after deploying these source files, so the persistent pane
   loads the new code. A pyRevit reload alone is not acceptance evidence.
2. Open a test project and select a rigid pipe.
3. Click **AI > Dev > MCP Bridge**. The command starts the bridge and shows the
   private connection-file path. Click it again to stop; shutdown also stops it.
4. Configure a client using one of the examples below. The server starts even if
   Revit is absent, but inspection calls return an error until the bridge runs.

The bridge creates a random session directory under
`%LOCALAPPDATA%\BIMCode\MCP` with a current-user-only Windows DACL, then writes
`connection.json` with a random port and 256-bit secret. Failure to establish the
private directory prevents startup. Do not paste or commit this file. Only local
127.0.0.1 connections are accepted; this is not an internet or HTTP MCP endpoint.
No firewall opening or port forwarding is needed.

With one session descriptor, discovery is automatic on each call. With multiple
Revit instances, pass `--connection` followed by the path shown by the selected
Revit instance. A crash may leave stale session directories: stop/close the owning
Revit process before removing its stale directory. Do not guess between sessions.
The bridge does not persist inspection reports or log secrets/model payloads.
Same-user processes and local administrators remain inside the machine's trust
boundary. Bounded facts returned to an AI client may be sent to its model provider.

## Connect Codex

Use local Windows Codex (CLI, supported desktop or IDE extension). This does not
connect a remote/cloud Codex container to Revit automatically.

Assuming the documented checkout path `C:\00_WORKS\DEVELOPMENT\AI`:

```powershell
codex mcp add bimcode-revit -- C:\00_WORKS\DEVELOPMENT\AI\BIMCode_MCP\.venv\Scripts\python.exe -I -B C:\00_WORKS\DEVELOPMENT\AI\BIMCode_MCP\server.py
codex mcp list
```

Alternatively merge [examples/codex.config.toml](examples/codex.config.toml) into
your user Codex configuration, updating the checkout path. Do not overwrite other
server entries. The TOML example explicitly forwards `LOCALAPPDATA`; if discovery
is unavailable in a particular launcher, use `--connection` with the private file
path instead. In Codex, `/mcp` displays connections; it does not create the server.

## Connect VS Code or Claude Code

VS Code's selected agent and the Codex extension have distinct configurations.
Configuring VS Code's Copilot harness does not configure Codex automatically.

For compatible Copilot/Claude configurations, merge
[examples/portable.mcp.json](examples/portable.mcp.json) into the workspace-root
`.mcp.json`, changing the absolute paths. For VS Code's legacy/local format use
[examples/vscode.mcp.json](examples/vscode.mcp.json) in `.vscode/mcp.json`; that
format uses `servers`, while the portable format uses `mcpServers`.
Use only the configuration for the client you are actually running. Nothing in
this repository enables a client automatically.

Claude Code can also register the same command:

```powershell
claude mcp add --transport stdio bimcode-revit -- C:\00_WORKS\DEVELOPMENT\AI\BIMCode_MCP\.venv\Scripts\python.exe -I -B C:\00_WORKS\DEVELOPMENT\AI\BIMCode_MCP\server.py
```

A separate Claude subscription is optional; it is not an MCP prerequisite.

## First acceptance prompt

> Use BIMCode's get_revit_context and tell me the document title. Then use the
> returned token to summarize the selected pipes. Report the deterministic
> classification, reason, counts, units and any omissions. Make no model changes.

Obtain a fresh token before every inspection. If Revit is busy, finish/cancel the
active command and explicitly retry from `get_revit_context`. The adapter expires
host work after 20 seconds and never retries an inspection automatically. A tool
that returned successfully may still report a domain `NOT_READY` or `PARTIAL`;
that is not equivalent to a healthy model.

## Validation and remaining acceptance

Offline tests use real MCP initialization, tool discovery, schema validation,
stdio subprocesses and authenticated sockets with a simulated Revit dispatcher
and mocked domain builder. They do not prove Windows ACL creation, IronPython
runtime behavior, actual Revit API scheduling or live client integration.

```powershell
.\BIMCode_MCP\.venv\Scripts\python.exe -m pip install pytest -r requirements_sidecar.txt
.\BIMCode_MCP\.venv\Scripts\python.exe -m pytest -q tests
```

The provider dependency above is for the existing offline regression suite only;
the MCP server itself does not import or call OpenAI. Source-comparison tests need
Git history (`git fetch --unshallow` for a shallow checkout).

Manual acceptance, all pending until run on Windows/Revit:

1. Start/stop twice; verify one listener, cleanup, restart and current-user-only
   access to the private descriptor. Confirm no automatic listener on startup.
2. Discover exactly four MCP tools. Run pipe summary and connector inspection;
   compare unchanged selection results against Workbench, including counts/units.
3. Run mixed MEP summary and compare child states/omissions with Workbench.
4. Test empty selection and unsupported-only selection; preserve existing refusals
   and not-ready results. No filtering, selection mutation or fabricated success.
5. Get a token, change selection/document/view or edit the model, then inspect:
   expect `STALE_CONTEXT`. Repeat with expiry and token reuse.
6. Hold Revit in a modal command so inspection times out; release the command and
   confirm that the expired request does not inspect or return a late result.
7. Exercise existing pane tools/provider work and write gates while MCP is queued:
   no concurrent ownership or bypass. Recheck normal pane operation after failure.
8. Stop/close Revit with work queued; old tokens/connection must fail. Repeat with
   the chosen Codex client. Claude/VS Code acceptance is separate if used.

Current run evidence is in `PROJECT_STATE.md`. No live PASS, source-control closure,
WBSO hours or evidence IDs are inferred from offline tests.

References: [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp),
[official Python SDK v1](https://py.sdk.modelcontextprotocol.io/v1/),
[VS Code MCP](https://code.visualstudio.com/docs/agent-customization/mcp-servers),
[Claude Code MCP](https://code.claude.com/docs/en/mcp).
