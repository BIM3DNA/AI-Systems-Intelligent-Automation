"""M3B scalar continuation contract. One approved function, no command arguments."""
import json
import re

NAME = "summarize_selected_pipes"
MAX_REQUEST = 120000
MAX_RESULT = 80000
MESSAGES = {
    "AI_TOOL_NOT_ALLOWED": "Requested AI tool is not available.",
    "AI_TOOL_ARGUMENTS_INVALID": "The approved tool accepts no arguments.",
    "AI_TOOL_PROTOCOL_ERROR": "Invalid AI tool exchange.",
    "AI_TOOL_LOOP_LIMIT": "Only one tool call is allowed per request.",
    "MODELMIND_NOT_READY": "ModelMind is not ready for this request.",
    "MODELMIND_EXECUTION_FAILED": "ModelMind could not complete this request.",
    "STALE_CONTEXT": "The model context or selection changed. Please retry.",
}


class ToolError(ValueError):
    pass


def identifier(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,256}", value) is not None


def validate_call(call):
    if not isinstance(call, dict) or set(call) != {"call_id", "name", "arguments"}:
        raise ToolError("AI_TOOL_PROTOCOL_ERROR")
    if call["name"] != NAME:
        raise ToolError("AI_TOOL_NOT_ALLOWED")
    if type(call["arguments"]) is not dict or call["arguments"]:
        raise ToolError("AI_TOOL_ARGUMENTS_INVALID")
    if not identifier(call["call_id"]):
        raise ToolError("AI_TOOL_PROTOCOL_ERROR")


def validate_request(data):
    base = {"protocol_version", "request_id", "operation"}
    if data["operation"] == "agent_turn":
        if (set(data) != base | {"user_text"} or not isinstance(data.get("user_text"), str)
                or not data["user_text"].strip() or len(data["user_text"]) > 2000):
            raise ToolError("AI_TOOL_PROTOCOL_ERROR")
    else:
        expected = base | {"tool_call", "provider_state", "tool_result"}
        if set(data) != expected:
            raise ToolError("AI_TOOL_PROTOCOL_ERROR")
        validate_call(data["tool_call"])
        state = data["provider_state"]
        if (not isinstance(state, dict) or set(state) != {"response_id", "model"}
                or not identifier(state["response_id"]) or not isinstance(state["model"], str)
                or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", state["model"]) is None):
            raise ToolError("AI_TOOL_PROTOCOL_ERROR")
        result = data["tool_result"]
        if (not isinstance(result, dict) or result.get("action_id") != "PIPING-RO-001-A01"
                or result.get("specialty") != "PIPING"
                or len(json.dumps(result, ensure_ascii=True, allow_nan=False)) > MAX_RESULT):
            raise ToolError("AI_TOOL_PROTOCOL_ERROR")
    return data
