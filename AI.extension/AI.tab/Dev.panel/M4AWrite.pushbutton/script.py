"""Human-only entry to M4A; never called from a provider or read-only tool."""
from pyrevit import HOST_APP, forms, script
from pyrevit.coreutils import envvars
from bimcode_ai_pane import SESSION_KEY
from bimcode_ai_pane.write_coordinator import get_coordinator

session = envvars.get_pyrevit_env_var(SESSION_KEY)
if session is None:
    print("M4A write unavailable: restart Revit with the BIMCode pane registered.")
else:
    get_coordinator(session).invoke(HOST_APP.uiapp, forms, script.get_output())
