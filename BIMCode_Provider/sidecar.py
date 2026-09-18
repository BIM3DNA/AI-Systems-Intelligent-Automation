"""Fixed one-shot entry point. Never invoke this against real config in tests."""
import contextlib
import json
import logging
import os
from pathlib import Path
import sys

# -I removes script-directory discovery; explicitly trust only this fixed directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from provider_config import load_config
from protocol import parse, failure, success, MAX_REQUEST
from tool_protocol import ToolError, MAX_REQUEST as TOOL_MAX_REQUEST


def dispatch(raw, root, environ=None, sender=None):
    request_id = ""
    try:
        request = parse(raw)
        request_id = request["request_id"]
        config = load_config(root, environ)
        if config.state != "READY":
            code = {"MISSING_API_KEY": "CONFIG_MISSING_API_KEY",
                    "MISSING_MODEL": "CONFIG_MISSING_MODEL"}.get(config.state, "INVALID_CONFIG")
            return failure(request_id, code)
        # Readiness is local-only; also verify the pinned SDK is importable.
        # This is a one-shot child, not the Revit process. Ignore ambient SDK
        # customization (especially custom auth headers) without reading values.
        for name in list(os.environ):
            if name.startswith("OPENAI_") and name not in ("OPENAI_API_KEY", "OPENAI_MODEL"):
                del os.environ[name]
        import openai
        if openai.__version__ != "3.15.0":
            return failure(request_id, "INTERNAL_PROVIDER_ERROR")
        if request["operation"] == "readiness":
            return success(request_id, config.model, "READY")
        if sender is None:
            from provider import send
            sender = send
        return sender(config, request)
    except ToolError as exc:
        return failure(request_id, exc.args[0])
    except (ValueError, UnicodeError):
        return failure(request_id, "SIDECAR_PROTOCOL_ERROR")
    except Exception:
        return failure(request_id, "INTERNAL_PROVIDER_ERROR")


def main(stdin=None, stdout=None, root=None, environ=None, sender=None):
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    root = Path(__file__).resolve().parent.parent if root is None else root
    logging.disable(logging.CRITICAL)
    # Suppress SDK/library output and tracebacks; only the final envelope escapes.
    with open(os.devnull, "w", encoding="utf-8") as sink:
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            try:
                result = dispatch(stdin.read(TOOL_MAX_REQUEST + 1), root, environ, sender)
            except Exception:
                result = failure("", "INTERNAL_PROVIDER_ERROR")
    stdout.write(json.dumps(result, ensure_ascii=True, allow_nan=False))
    stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
