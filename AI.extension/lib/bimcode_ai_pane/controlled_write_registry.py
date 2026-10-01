"""M4B-1 dormant metadata only; no dispatcher or production provider import."""
from copy import deepcopy
from bimcode_ai_pane import write_contracts
from bimcode_ai_pane.ai_tool_registry import TOOLS as READ_ONLY_TOOL_REGISTRY

CONTROLLED_WRITE_TOOL_REGISTRY = ({
    "tool_name": "set_selected_pipe_test_text",
    "action_id": write_contracts.M4A_ACTION_ID,
    "safety_class": "CONTROLLED_WRITE",
    "schema": {"type": "object", "properties": {"value": {
        "type": "string", "minLength": 1, "maxLength": 64,
        "pattern": "^[A-Za-z0-9][A-Za-z0-9 _-]{0,63}$"}},
        "required": ["value"], "additionalProperties": False},
    "description": (
        "Request native human-confirmed setting of only BIMCode_M4A_TestText on exactly "
        "one selected eligible rigid host Pipe. Excludes Mark, Comments, diameter, slope, "
        "system assignment, movement, rotation, Ducts, Electrical elements, multiple "
        "targets, batch editing and arbitrary parameters. No execution is available "
        "in this checkpoint; metadata is not consent or execution authority."),
    "enabled_predicate": "ControlledWritePermission",
    "document_eligibility_predicate": "document_eligibility",
    "argument_validator": "validate_arguments",
    "dispatcher_state": "NOT_IMPLEMENTED",
    "provider_exposure_allowed": False,
},)


def metadata():
    """Consumers receive copies, not writable references to the registry."""
    return deepcopy(CONTROLLED_WRITE_TOOL_REGISTRY)


def validate_arguments(arguments):
    if type(arguments) is not dict or set(arguments) != set(("value",)):
        return dict(valid=False, reason_code="INVALID_ARGUMENTS", value=None)
    return write_contracts.validate_value(arguments["value"])
