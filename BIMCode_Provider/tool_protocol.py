"""M3F scalar continuation contract. Thirteen fixed functions, one call per turn."""
import json
import re

NAME = "summarize_selected_pipes"
ACTIONS = {
    "summarize_selected_pipes": "PIPING-RO-001-A01",
    "inspect_selected_pipe_connectors": "PIPING-RO-001-A02",
    "inspect_selected_pipe_system_assignment": "PIPING-RO-001-A03",
    "inspect_selected_pipe_qa_health": "PIPING-RO-001-A04",
    "summarize_selected_ducts": "HVAC-RO-001-A01",
    "inspect_selected_duct_connectors": "HVAC-RO-001-A02",
    "inspect_selected_duct_system_assignment": "HVAC-RO-001-A03",
    "inspect_selected_duct_qa_health": "HVAC-RO-001-A04",
    "summarize_selected_electrical_elements": "ELECTRICAL-RO-001-A01",
    "inspect_selected_electrical_connectors": "ELECTRICAL-RO-001-A02",
    "inspect_selected_electrical_circuit_assignment": "ELECTRICAL-RO-001-A03",
    "inspect_selected_electrical_qa_health": "ELECTRICAL-RO-001-A04",
    "summarize_selected_mep_elements": "MEP-MULTI-RO-001-A01",
}
SPECIALTIES = dict((action, action.split("-", 1)[0]) for action in ACTIONS.values())
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
    if not isinstance(call["name"], str) or call["name"] not in ACTIONS:
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
        if (not isinstance(result, dict) or result.get("action_id") != ACTIONS[data["tool_call"]["name"]]
                or result.get("specialty") != SPECIALTIES[ACTIONS[data["tool_call"]["name"]]]
                or len(json.dumps(result, ensure_ascii=True, allow_nan=False)) > MAX_RESULT):
            raise ToolError("AI_TOOL_PROTOCOL_ERROR")
        if data["tool_call"]["name"] == "summarize_selected_mep_elements":
            validate_composite(result)
    return data


def validate_composite(result):
    """Fixed host-result contract, never a provider-controlled execution plan."""
    order = ("PIPING", "HVAC", "ELECTRICAL")
    children = result.get("specialties")
    if (result.get("feature_id") != "MEP-MULTI-RO-001" or not isinstance(children, dict)
            or set(children) != set(order)
            or result.get("classification") not in (
                "MEP_MULTI_SELECTION_NOT_READY", "MEP_MULTI_SELECTION_FAILED",
                "MEP_MULTI_SELECTION_SUMMARY_OK", "MEP_MULTI_SELECTION_SUMMARY_PARTIAL")):
        raise ToolError("AI_TOOL_PROTOCOL_ERROR")
    evaluated = []
    for specialty in order:
        child = children[specialty]
        action = specialty + "-RO-001-A01"
        if (not isinstance(child, dict) or child.get("specialty") != specialty
                or child.get("action_id") not in (None, action)
                or type(child.get("evaluated")) is not bool):
            raise ToolError("AI_TOOL_PROTOCOL_ERROR")
        if child["evaluated"]:
            if child.get("action_id") != action:
                raise ToolError("AI_TOOL_PROTOCOL_ERROR")
            evaluated.append(action)
    if result.get("sub_actions") != evaluated:
        raise ToolError("AI_TOOL_PROTOCOL_ERROR")
