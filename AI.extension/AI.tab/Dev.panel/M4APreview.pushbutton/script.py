"""Human-invoked read-only M4A preview harness; no execution authorization."""
import json
from uuid import uuid4
from xml.sax.saxutils import escape

from bimcode_write_runtime import build_preview, capture_preview_context


def _main():
    from pyrevit import HOST_APP, forms, script
    uiapp = HOST_APP.uiapp
    context = capture_preview_context(uiapp)
    value = forms.ask_for_string(
        default="M4A_Test_01", title="M4A Preview - read-only",
        prompt="Proposed test text (preview only; no value will be written):")
    if value is None:
        return
    # Request identity only, not a parameter GUID or a confirmation token.
    # No pane generation exists for this synchronous, human-invoked command.
    result = build_preview(uiapp, uuid4().hex, value,
                           selection_generation=None, context=context)
    output = script.get_output()
    output.print_html("<h3>M4A read-only preview</h3>"
                      "<p>No confirmation or execution has occurred. "
                      "confirmation_required describes a future requirement only.</p>")
    # Preserve every returned field, including null/empty distinctions and reasons.
    # Escape model text before insertion into the pyRevit HTML output window.
    output.print_html("<pre>" + escape(json.dumps(result, indent=2, sort_keys=True,
                                                 ensure_ascii=True)) + "</pre>")
    return result


def main():
    from pyrevit.coreutils import envvars
    from bimcode_ai_pane import SESSION_KEY
    from bimcode_ai_pane.write_access import run_human_operation
    return run_human_operation(envvars.get_pyrevit_env_var(SESSION_KEY), "HUMAN_DEV_PREVIEW", _main)


if __name__ == "__main__":
    main()
