# -*- coding: utf-8 -*-
import json
import os
import subprocess
import sys


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OPENAI_SERVICE_PATH = os.path.join(ROOT_DIR, "Openai_Server", "chatgpt_service.py")


def _candidate_python_commands():
    candidates = []

    if os.environ.get("PYTHON_EXECUTABLE"):
        candidates.append([os.environ.get("PYTHON_EXECUTABLE")])

    executable = sys.executable or ""
    executable_name = os.path.basename(executable).lower()
    if (
        executable
        and "ipy" not in executable_name
        and "ironpython" not in executable_name
    ):
        candidates.append([executable])

    candidates.append(["py", "-3"])
    candidates.append(["python"])
    return candidates


def _run_service(command, payload=None, timeout_seconds=20):
    payload = payload or {}
    errors = []
    for python_cmd in _candidate_python_commands():
        try:
            process = subprocess.Popen(
                python_cmd + [OPENAI_SERVICE_PATH, command],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            out, err = process.communicate(
                input=json.dumps(payload).encode("utf-8"), timeout=timeout_seconds
            )
            if process.returncode != 0:
                try:
                    data = json.loads(out.decode("utf-8"))
                    if isinstance(data, dict):
                        if data.get("error"):
                            data["ok"] = False
                            data["python_cmd"] = python_cmd
                            return data
                        errors.append("Service request failed.")
                        continue
                except Exception:
                    pass
                errors.append(err.decode("utf-8") or "Service request failed.")
                continue

            data = json.loads(out.decode("utf-8"))
            if not data.get("ok"):
                errors.append(data.get("error", "Service returned an error."))
                continue
            return {"ok": True, "result": data.get("result"), "python_cmd": python_cmd}
        except OSError as exc:
            errors.append(str(exc))
        except Exception as exc:
            errors.append(str(exc))

    return {
        "ok": False,
        "error": "; ".join([msg for msg in errors if msg])
        or "Python service unavailable.",
    }


def get_openai_provider_state():
    state = _run_service("--provider-state", {})
    if not state.get("ok"):
        return {
            "available": False,
            "state": state.get("state", "request_failed"),
            "key_state": state.get("key_state", "missing_key"),
            "key_present": bool(state.get("key_present", False)),
            "provider_reachable": bool(state.get("provider_reachable", False)),
            "last_error_category": state.get("last_error_category", "request_failed"),
            "message": state.get("message", "OpenAI request failed."),
            "detail": state.get("detail", state.get("error", "Unknown error")),
            "runtime_command": " ".join(state.get("python_cmd", []) or []),
        }
    result = state.get("result") or {}
    result["detail"] = result.get("detail", "")
    result["runtime_command"] = " ".join(state.get("python_cmd", []) or [])
    return result


def get_openai_provider_self_test():
    state = _run_service("--provider-self-test", {})
    if not state.get("ok"):
        return {
            "ok": False,
            "env_key_present": False,
            "openai_module_importable": False,
            "client_init_ok": False,
            "test_request_ok": False,
            "failure_category": state.get("state", "request_failed"),
            "failure_message_safe": state.get(
                "detail", state.get("error", "Unknown error")
            ),
            "runtime_command": " ".join(state.get("python_cmd", []) or []),
        }
    result = state.get("result") or {}
    result["ok"] = True
    result["runtime_command"] = " ".join(state.get("python_cmd", []) or [])
    return result


def normalize_intent_to_supported_action(
    user_request, supported_actions, model_name="gpt-4o-mini"
):
    payload = {
        "user_request": user_request,
        "supported_actions": supported_actions,
        "model_name": model_name,
    }
    return _run_service("--normalize-intent", payload)
