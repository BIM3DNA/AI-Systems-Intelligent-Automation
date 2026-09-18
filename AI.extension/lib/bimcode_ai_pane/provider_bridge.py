"""IronPython-compatible scalar process boundary. No Revit or network APIs."""
import json
import os.path
import uuid
import re

TIMEOUT_MS = 75000
MAX_OUTPUT = 100000
TEXT_TYPES = (str, type(u""))
ERRORS = {
    "AI_TOOL_NOT_ALLOWED": "Requested AI tool is not available.",
    "AI_TOOL_ARGUMENTS_INVALID": "The approved tool accepts no arguments.",
    "AI_TOOL_PROTOCOL_ERROR": "Invalid AI tool exchange.",
    "AI_TOOL_LOOP_LIMIT": "Only one tool call is allowed per request.",
    "MODELMIND_NOT_READY": "ModelMind is not ready for this request.",
    "MODELMIND_EXECUTION_FAILED": "ModelMind could not complete this request.",
    "STALE_CONTEXT": "The model context or selection changed. Please retry.",
    "PYTHON_RUNTIME_UNAVAILABLE": "Repo-local Python runtime is unavailable.",
    "SIDECAR_START_FAILED": "Provider process could not start.",
    "SIDECAR_TIMEOUT": "Provider process timed out.",
    "SIDECAR_PROTOCOL_ERROR": "Provider returned an invalid response.",
    "SIDECAR_NONZERO_EXIT": "Provider process exited unsuccessfully.",
    "SIDECAR_REQUEST_ID_MISMATCH": "Provider response did not match this request.",
    "CONFIG_MISSING_API_KEY": "Provider API key is not configured.",
    "CONFIG_MISSING_MODEL": "Provider model is not configured.",
    "INVALID_CONFIG": "Provider configuration is invalid.",
    "OPENAI_AUTH_ERROR": "OpenAI authentication or permission failed.",
    "OPENAI_RATE_LIMIT": "OpenAI rate limit reached. Try again later.",
    "OPENAI_QUOTA_OR_BILLING": "OpenAI quota or billing requires attention.",
    "OPENAI_TIMEOUT": "OpenAI request timed out.",
    "OPENAI_CONNECTION_ERROR": "OpenAI connection failed.",
    "OPENAI_API_ERROR": "OpenAI could not complete this request.",
    "OPENAI_EMPTY_RESPONSE": "OpenAI returned no assistant text.",
    "INTERNAL_PROVIDER_ERROR": "Provider is unavailable or failed internally.",
}


def failure(request_id, code):
    return dict(protocol_version=1, request_id=request_id, ok=False,
                provider="openai", model="", text=None,
                error=dict(code=code, message=ERRORS[code]))


def request(operation, text=""):
    result = dict(protocol_version=1, operation=operation, request_id=uuid.uuid4().hex)
    if operation in ("text_response", "agent_turn"):
        result["user_text"] = text
    return result


def paths():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    return (os.path.join(root, ".venv", "Scripts", "python.exe"),
            os.path.join(root, "BIMCode_Provider", "sidecar.py"), root)


def decode(raw, request_id, exit_code):
    if exit_code != 0:
        return failure(request_id, "SIDECAR_NONZERO_EXIT")
    try:
        if len(raw) > MAX_OUTPUT:
            raise ValueError()
        data = json.loads(raw)
        if isinstance(data, dict) and data.get("state") == "TOOL_REQUEST":
            return decode_tool(data, request_id)
        if isinstance(data, dict) and data.get("state") == "FINAL":
            data.pop("state")
        expected = set(("protocol_version", "request_id", "ok", "provider", "model", "text", "error"))
        if (not isinstance(data, dict) or set(data) != expected
                or type(data["protocol_version"]) is not int or data["protocol_version"] != 1
                or type(data["ok"]) is not bool or data["provider"] != "openai"):
            raise ValueError()
        if data["request_id"] != request_id:
            return failure(request_id, "SIDECAR_REQUEST_ID_MISMATCH")
        if not isinstance(data["model"], TEXT_TYPES) or len(data["model"]) > 128:
            raise ValueError()
        if data["ok"]:
            if (not isinstance(data["text"], TEXT_TYPES) or not data["text"].strip()
                    or len(data["text"]) > 12000 or data["error"] is not None):
                raise ValueError()
        else:
            error = data["error"]
            if not isinstance(error, dict) or error.get("code") not in ERRORS or data["text"] is not None:
                raise ValueError()
            # Never trust remote error messages or stderr; render local constants.
            data["error"] = dict(code=error["code"], message=ERRORS[error["code"]])
        return data
    except Exception:
        return failure(request_id, "SIDECAR_PROTOCOL_ERROR")


def valid_identifier(value):
    return isinstance(value, TEXT_TYPES) and re.match(r"\A[A-Za-z0-9_-]{1,256}\Z", value) is not None


def decode_tool(data, request_id):
    if data.get("request_id") != request_id:
        return failure(request_id, "SIDECAR_REQUEST_ID_MISMATCH")
    expected = set(("protocol_version", "request_id", "ok", "provider", "model", "text", "error",
                    "state", "tool_call", "provider_state"))
    if (set(data) != expected or data["state"] != "TOOL_REQUEST" or type(data["protocol_version"]) is not int
            or data["protocol_version"] != 1 or data["ok"] is not True
            or data["provider"] != "openai" or data["text"] is not None or data["error"] is not None):
        return failure(request_id, "AI_TOOL_PROTOCOL_ERROR")
    call = data["tool_call"]
    if not isinstance(call, dict) or set(call) != set(("call_id", "name", "arguments")):
        return failure(request_id, "AI_TOOL_PROTOCOL_ERROR")
    if call["name"] != "summarize_selected_pipes":
        return failure(request_id, "AI_TOOL_NOT_ALLOWED")
    if type(call["arguments"]) is not dict or call["arguments"]:
        return failure(request_id, "AI_TOOL_ARGUMENTS_INVALID")
    state = data["provider_state"]
    if (not valid_identifier(call["call_id"]) or not isinstance(state, dict)
            or set(state) != set(("response_id", "model"))
            or not valid_identifier(state["response_id"]) or not isinstance(data["model"], TEXT_TYPES)
            or re.match(r"\A[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z", data["model"]) is None
            or state["model"] != data["model"]):
        return failure(request_id, "AI_TOOL_PROTOCOL_ERROR")
    return data


def run(payload):
    """Only scalar work. Executed off the UI thread. Fixed executable/script."""
    from System.Diagnostics import Process
    from System.Text import UTF8Encoding
    request_id = payload["request_id"]
    executable, script, root = paths()
    if not os.path.isfile(executable):
        return failure(request_id, "PYTHON_RUNTIME_UNAVAILABLE")
    if not os.path.isfile(script):
        return failure(request_id, "SIDECAR_START_FAILED")
    process = Process()
    started = False
    try:
        info = process.StartInfo
        info.FileName = executable
        info.Arguments = '-I -B -X utf8 "{0}"'.format(script)
        info.WorkingDirectory = root
        info.UseShellExecute = False
        info.CreateNoWindow = True
        info.RedirectStandardInput = True
        info.RedirectStandardOutput = True
        info.RedirectStandardError = True
        info.StandardOutputEncoding = UTF8Encoding(False)
        info.StandardErrorEncoding = UTF8Encoding(False)
        started = process.Start()
        if not started:
            return failure(request_id, "SIDECAR_START_FAILED")
        # Drain both pipes concurrently to avoid stderr/stdout deadlocks.
        output = process.StandardOutput.ReadToEndAsync()
        errors = process.StandardError.ReadToEndAsync()
        writing = process.StandardInput.WriteLineAsync(json.dumps(payload, ensure_ascii=True))
        if not writing.Wait(5000):
            return failure(request_id, "SIDECAR_TIMEOUT")
        process.StandardInput.Close()
        if not process.WaitForExit(TIMEOUT_MS):
            return failure(request_id, "SIDECAR_TIMEOUT")
        if not output.Wait(1000) or not errors.Wait(1000):
            return failure(request_id, "SIDECAR_PROTOCOL_ERROR")
        return decode(output.Result, request_id, process.ExitCode)
    except Exception:
        return failure(request_id, "SIDECAR_START_FAILED")
    finally:
        if started:
            try:
                if not process.HasExited:
                    process.Kill()
                    process.WaitForExit(1000)
            except Exception:
                pass
        process.Dispose()


class SendState(object):
    """UI-thread-owned gate; independent of deterministic ModelMind state."""
    def __init__(self):
        self.ready = False
        self.active = None

    def enabled(self, text):
        return self.ready and self.active is None and bool(text.strip()) and len(text) <= 2000

    def begin(self, operation, text=""):
        if self.active is not None or (operation in ("text_response", "agent_turn") and not self.enabled(text)):
            return None
        self.active = request(operation, text)
        return self.active.copy()

    def finish(self, result):
        if self.active is None or result["request_id"] != self.active["request_id"]:
            return False
        if self.active["operation"] == "readiness":
            self.ready = result["ok"] and result["text"] == "READY"
        elif not result["ok"] and result["error"]["code"] in (
                "CONFIG_MISSING_API_KEY", "CONFIG_MISSING_MODEL", "INVALID_CONFIG",
                "PYTHON_RUNTIME_UNAVAILABLE"):
            self.ready = False
        self.active = None
        return True
