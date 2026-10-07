"""TEMPORARY M4B-HOST-LIVE-001 acceptance harness. Never a provider tool."""
import json
from xml.sax.saxutils import escape
from bimcode_ai_pane.write_contracts import validate_value
from bimcode_write_runtime import capture_preview_context, resolve_target, PreviewBlocked

INSPECT = "Inspect retained result (read-only)"
NEW = "New internal M4B test request"


def display(output, data):
    output.print_html("<pre>" + escape(json.dumps(data, indent=2, sort_keys=True,
                                                ensure_ascii=True)) + "</pre>")
    return data


def inspect(session, output):
    """Scalar inspection only, including after document close/permission reset."""
    return display(output, json.loads(session.inspect_controlled_write_request()))


def new_request(session, uiapp, forms, output, db):
    status = json.loads(session.inspect_controlled_write_request())
    if not status["permission_enabled"]:
        return display(output, dict(reason="PERMISSION_DISABLED"))
    if status["busy"]:
        return display(output, dict(reason="EXECUTION_BUSY"))
    context = capture_preview_context(uiapp)
    try:
        # Reuse the authoritative rigid host-Pipe/document selection resolver.
        resolve_target(uiapp, db, context)
    except PreviewBlocked as error:
        return display(output, dict(reason=error.reason))
    value = forms.ask_for_string(default="M4B_HOST_WRITE_01", title="TEMPORARY M4B Host Test",
        prompt="One fixed test parameter only. Native confirmation follows; input is not consent.")
    if value is None:
        return display(output, dict(reason="INPUT_CANCELLED"))
    checked = validate_value(value)
    if not checked["valid"]:
        return display(output, dict(reason=checked["reason_code"]))
    current = capture_preview_context(uiapp)
    if current.get("reason") or current.get("fingerprint") != context.get("fingerprint"):
        return display(output, dict(reason="STALE_CONTEXT"))
    outcome = json.loads(session.begin_controlled_write_request(value))
    if outcome["accepted"]:
        session.confirm_controlled_write_request(outcome["host_request_id"])
    else:
        display(output, outcome)
    # Do not wait: the accepted ExternalEvent runs AFTER this command returns.
    return inspect(session, output)


def main():
    from pyrevit import HOST_APP, DB, forms, script
    from pyrevit.coreutils import envvars
    from bimcode_ai_pane import SESSION_KEY
    output = script.get_output()
    session = envvars.get_pyrevit_env_var(SESSION_KEY)
    if session is None:
        return display(output, dict(reason="PANE_SESSION_UNAVAILABLE"))
    mode = forms.CommandSwitchWindow.show([INSPECT, NEW], message="TEMPORARY M4B host acceptance")
    if mode == INSPECT:
        return inspect(session, output)
    if mode == NEW:
        try:
            return new_request(session, HOST_APP.uiapp, forms, output, DB)
        except Exception:
            # Never retry, confirm or execute on an error. Retained receipt wins.
            display(output, dict(reason="HARNESS_ERROR", instruction="Inspect retained result; do not retry blindly."))
            return inspect(session, output)


if __name__ == "__main__":
    main()
