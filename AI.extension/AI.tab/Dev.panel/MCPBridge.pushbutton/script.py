"""Human opt-in only. The existing persistent PaneSession owns the bridge."""
from pyrevit import forms
from pyrevit.coreutils import envvars
from bimcode_ai_pane import SESSION_KEY

session = envvars.get_pyrevit_env_var(SESSION_KEY)
if session is None:
    forms.alert("Restart Revit with AI.extension enabled to register the Workbench.",
                title="BIMCode MCP")
else:
    try:
        path = session.toggle_mcp_bridge()
        message = ("Read-only bridge started. Codex can now connect locally.\n\n"
                   "Connection file (keep private):\n" + path +
                   "\n\nClick MCP Bridge again to stop it.") if path else "MCP bridge stopped."
        forms.alert(message, title="BIMCode MCP")
    except Exception:
        forms.alert("MCP bridge could not start or stop cleanly. Restart Revit and "
                    "check BIMCode_MCP/README.md prerequisites. No model change was requested.",
                    title="BIMCode MCP")
