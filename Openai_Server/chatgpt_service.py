import json
import os
import sys


DEFAULT_MODEL = "gpt-4o-mini"


class ProviderServiceError(Exception):
    def __init__(self, payload):
        Exception.__init__(self, payload.get("message", "Provider request failed."))
        self.payload = payload


def get_openai_api_key():
    return os.getenv("OPENAI_API_KEY")


def _build_state(state, message, key_present=False, provider_reachable=False, last_error_category="", detail=""):
    return {
        "available": state == "provider_ready",
        "state": state,
        "key_state": "key_present" if key_present else "missing_key",
        "key_present": bool(key_present),
        "provider_reachable": bool(provider_reachable),
        "last_error_category": last_error_category or state,
        "message": message,
        "detail": detail or "",
    }


def _runtime_info():
    return {
        "runtime_executable": sys.executable or "",
        "runtime_version": sys.version.splitlines()[0] if sys.version else "",
        "runtime_prefix": sys.prefix or "",
    }


def _classify_exception(exc):
    message = str(exc or exc.__class__.__name__)
    lowered = message.lower()
    status_code = getattr(exc, "status_code", None)
    code = getattr(exc, "code", None)
    exc_name = exc.__class__.__name__

    if status_code in (401, 403) or exc_name in ("AuthenticationError", "PermissionDeniedError"):
        return _build_state(
            "auth_failed",
            "OpenAI authentication failed.",
            key_present=True,
            provider_reachable=True,
            last_error_category="auth_failed",
            detail=message,
        )

    if status_code == 429 or exc_name == "RateLimitError" or "quota" in lowered or "billing" in lowered:
        return _build_state(
            "request_failed",
            "OpenAI quota or billing request failed.",
            key_present=True,
            provider_reachable=True,
            last_error_category="quota_failed",
            detail=message,
        )

    if status_code == 400 or exc_name == "BadRequestError" or code == "model_not_found" or "model" in lowered and "not found" in lowered:
        return _build_state(
            "request_failed",
            "OpenAI request/model configuration failed.",
            key_present=True,
            provider_reachable=True,
            last_error_category="bad_request",
            detail=message,
        )

    if (
        exc_name in ("APIConnectionError", "APITimeoutError", "TimeoutError")
        or "timed out" in lowered
        or "timeout" in lowered
        or "connection" in lowered
        or "dns" in lowered
        or "name resolution" in lowered
        or "temporary failure" in lowered
        or "connection reset" in lowered
    ):
        return _build_state(
            "network_failed",
            "OpenAI network or timeout failure.",
            key_present=True,
            provider_reachable=False,
            last_error_category="network_failed",
            detail=message,
        )

    return _build_state(
        "request_failed",
        "OpenAI request failed.",
        key_present=True,
        provider_reachable=False,
        last_error_category="unknown_exception",
        detail=message,
    )


def _safe_message(text):
    message = str(text or "")
    api_key = get_openai_api_key()
    if api_key:
        message = message.replace(api_key, "[redacted]")
    return message


def _import_openai_class():
    try:
        from openai import OpenAI

        return {"ok": True, "OpenAI": OpenAI}
    except Exception as exc:
        return {
            "ok": False,
            "state": _build_state(
                "missing_openai_module",
                "OpenAI Python module is not available in this runtime.",
                key_present=bool(get_openai_api_key()),
                provider_reachable=False,
                last_error_category="missing_openai_module",
                detail=_safe_message(exc),
            ),
        }


def get_openai_client():
    api_key = get_openai_api_key()
    if not api_key:
        raise ProviderServiceError(
            _build_state(
                "missing_key",
                "OpenAI missing key.",
                key_present=False,
                provider_reachable=False,
                last_error_category="missing_key",
            )
        )

    import_result = _import_openai_class()
    if not import_result.get("ok"):
        raise ProviderServiceError(import_result.get("state"))

    try:
        return import_result.get("OpenAI")(api_key=api_key, timeout=10.0)
    except Exception as exc:
        raise ProviderServiceError(
            _build_state(
                "client_init_failed",
                "OpenAI client initialization failed.",
                key_present=True,
                provider_reachable=False,
                last_error_category="client_init_failed",
                detail=_safe_message(exc),
            )
        )


def run_provider_self_test(model_name=DEFAULT_MODEL):
    api_key = get_openai_api_key()
    result = {
        "env_key_present": bool(api_key),
        "openai_module_importable": False,
        "client_init_ok": False,
        "test_request_ok": False,
        "failure_category": "",
        "failure_message_safe": "",
    }
    result.update(_runtime_info())

    if not api_key:
        result["failure_category"] = "missing_key"
        result["failure_message_safe"] = "OPENAI_API_KEY is not visible in this runtime."
        return result

    import_result = _import_openai_class()
    if not import_result.get("ok"):
        state = import_result.get("state") or {}
        result["failure_category"] = state.get("state", "missing_openai_module")
        result["failure_message_safe"] = _safe_message(state.get("detail") or state.get("message"))
        return result

    result["openai_module_importable"] = True

    try:
        client = import_result.get("OpenAI")(api_key=api_key, timeout=10.0)
        result["client_init_ok"] = True
    except Exception as exc:
        result["failure_category"] = "client_init_failed"
        result["failure_message_safe"] = _safe_message(exc)
        return result

    try:
        response = client.responses.create(
            model=model_name,
            input="Reply with OK only.",
            max_output_tokens=5,
            temperature=0,
        )
        text = getattr(response, "output_text", "") or ""
        if "OK" not in text.upper():
            result["failure_category"] = "request_failed"
            result["failure_message_safe"] = _safe_message(
                text or "Unexpected provider self-test response."
            )
            return result
        result["test_request_ok"] = True
        result["failure_category"] = "provider_ready"
        result["failure_message_safe"] = "OpenAI provider self-test succeeded."
        return result
    except Exception as exc:
        state = _classify_exception(exc)
        result["failure_category"] = state.get("state", "request_failed")
        result["failure_message_safe"] = _safe_message(state.get("detail") or state.get("message"))
        return result


def probe_provider(model_name=DEFAULT_MODEL):
    client = get_openai_client()
    try:
        response = client.responses.create(
            model=model_name,
            input="Reply with OK only.",
            max_output_tokens=5,
            temperature=0,
        )
        text = getattr(response, "output_text", "") or ""
        if "OK" not in text.upper():
            raise ProviderServiceError(
                _build_state(
                    "request_failed",
                    "OpenAI provider probe returned an unexpected response.",
                    key_present=True,
                    provider_reachable=True,
                    last_error_category="bad_response",
                    detail=_safe_message(text),
                )
            )
        return _build_state(
            "provider_ready",
            "OpenAI ready.",
            key_present=True,
            provider_reachable=True,
            last_error_category="",
        )
    except Exception as exc:
        raise ProviderServiceError(_classify_exception(exc))


def get_provider_state():
    self_test = run_provider_self_test(model_name=DEFAULT_MODEL)
    failure_category = self_test.get("failure_category", "")
    provider_reachable = failure_category in ("provider_ready", "auth_failed", "request_failed")
    if failure_category == "provider_ready":
        state = _build_state(
            "provider_ready",
            "OpenAI ready.",
            key_present=True,
            provider_reachable=True,
            last_error_category="",
        )
    elif failure_category == "missing_key":
        state = _build_state(
            "missing_key",
            "OpenAI missing key.",
            key_present=False,
            provider_reachable=False,
            last_error_category="missing_key",
            detail=self_test.get("failure_message_safe", ""),
        )
    elif failure_category == "missing_openai_module":
        state = _build_state(
            "missing_openai_module",
            "OpenAI Python module is not available in this runtime.",
            key_present=True,
            provider_reachable=False,
            last_error_category="missing_openai_module",
            detail=self_test.get("failure_message_safe", ""),
        )
    elif failure_category == "client_init_failed":
        state = _build_state(
            "client_init_failed",
            "OpenAI client initialization failed.",
            key_present=True,
            provider_reachable=False,
            last_error_category="client_init_failed",
            detail=self_test.get("failure_message_safe", ""),
        )
    else:
        state = _build_state(
            failure_category or "request_failed",
            "OpenAI request failed." if failure_category not in ("auth_failed", "network_failed") else (
                "OpenAI authentication failed." if failure_category == "auth_failed" else "OpenAI network or timeout failure."
            ),
            key_present=bool(self_test.get("env_key_present")),
            provider_reachable=provider_reachable,
            last_error_category=failure_category or "request_failed",
            detail=self_test.get("failure_message_safe", ""),
        )
    state.update(_runtime_info())
    return state


def ask_openai(question, model=DEFAULT_MODEL, max_tokens=300, temperature=0.2):
    client = get_openai_client()
    try:
        response = client.responses.create(
            model=model,
            input=question,
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        return (getattr(response, "output_text", "") or "").strip()
    except Exception as exc:
        raise ProviderServiceError(_classify_exception(exc))


def normalize_intent_to_supported_action(user_request, supported_actions, model_name=DEFAULT_MODEL):
    supported_actions = supported_actions or []
    prompt = """You are a strict BIM planning normalizer.
Choose exactly one supported action from the list or reject the request.
Do not invent new tools, schedules, reports, or actions beyond the supported list.
Prefer the closest exact supported action when the user phrasing is informal.
Return machine-readable JSON only with this schema:
{{
  "matched_action": "<action id or empty string>",
  "confidence": 0.0,
  "summary": "<brief explanation>",
  "execution_ready": true,
  "rejected": false
}}
If unsupported or ambiguous, return:
{{
  "matched_action": "",
  "confidence": 0.0,
  "summary": "<why unsupported or ambiguous>",
  "execution_ready": false,
  "rejected": true
}}
Supported actions:
{actions}
User request:
{request}
""".format(
        actions=json.dumps(supported_actions, indent=2),
        request=user_request,
    )
    raw = ask_openai(prompt, model=model_name, max_tokens=250, temperature=0.0)
    try:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            raw = raw[start : end + 1]
        data = json.loads(raw)
    except Exception:
        raise ProviderServiceError(
            _build_state(
                "request_failed",
                "OpenAI returned non-JSON planner output.",
                key_present=True,
                provider_reachable=True,
                last_error_category="bad_response",
                detail="Cloud planner returned non-JSON output.",
            )
        )

    return {
        "matched_action": data.get("matched_action", "") or "",
        "confidence": float(data.get("confidence", 0.0) or 0.0),
        "summary": data.get("summary", "") or "",
        "execution_ready": bool(data.get("execution_ready", False)),
        "rejected": bool(data.get("rejected", False)),
    }


def _read_stdin_payload():
    raw = sys.stdin.read()
    if not raw:
        return {}
    return json.loads(raw)


def _write_json(data):
    sys.stdout.write(json.dumps(data))


def main():
    if len(sys.argv) < 2:
        _write_json({"ok": False, "error": "No command provided."})
        return 1

    command = sys.argv[1]
    try:
        if command == "--provider-state":
            _write_json({"ok": True, "result": get_provider_state()})
            return 0

        if command == "--provider-self-test":
            _write_json({"ok": True, "result": run_provider_self_test()})
            return 0

        if command == "--normalize-intent":
            payload = _read_stdin_payload()
            result = normalize_intent_to_supported_action(
                payload.get("user_request", ""),
                payload.get("supported_actions", []),
                payload.get("model_name", DEFAULT_MODEL),
            )
            _write_json({"ok": True, "result": result})
            return 0

        if command == "--ask":
            payload = _read_stdin_payload()
            result = ask_openai(
                payload.get("question", ""),
                model=payload.get("model", DEFAULT_MODEL),
                max_tokens=int(payload.get("max_tokens", 300)),
                temperature=float(payload.get("temperature", 0.2)),
            )
            _write_json({"ok": True, "result": result})
            return 0

        _write_json({"ok": False, "error": "Unknown command: {0}".format(command)})
        return 1
    except ProviderServiceError as exc:
        payload = dict(exc.payload)
        payload["ok"] = False
        payload["error"] = payload.get("message", "Provider request failed.")
        _write_json(payload)
        return 1
    except Exception as exc:
        payload = _build_state(
            "request_failed",
            "OpenAI request failed.",
            key_present=bool(get_openai_api_key()),
            provider_reachable=False,
            last_error_category="unknown_exception",
            detail=_safe_message(exc),
        )
        payload["ok"] = False
        payload["error"] = payload["message"]
        _write_json(payload)
        return 1


if __name__ == "__main__":
    sys.exit(main())
