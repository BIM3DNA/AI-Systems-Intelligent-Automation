"""Pure M4B logical request reducer. No events, processes, API calls or dispatch.

Timestamps and host IDs are supplied by a future trusted host adapter, not tools.
Returned intents describe future cleanup; they do not acquire/release runtime locks.
"""
import math
from collections import namedtuple
from bimcode_ai_pane import write_contracts as c
from bimcode_ai_pane.write_projection import Receipt, explanation, project_receipt

TRANSITIONS = {
    "IDLE": ("PROVIDER_INITIAL_REQUEST",),
    "PROVIDER_INITIAL_REQUEST": ("PROVIDER_TOOL_SELECTED", "PROVIDER_FINAL_RESPONSE_READY", "CANCELLED", "EXPIRED"),
    "PROVIDER_TOOL_SELECTED": ("WRITE_ARGUMENTS_VALIDATED", "HOST_RESULT_READY", "CANCELLED"),
    "WRITE_ARGUMENTS_VALIDATED": ("HOST_PREVIEW_BUILDING", "HOST_RESULT_READY", "CANCELLED", "EXPIRED"),
    "HOST_PREVIEW_BUILDING": ("PREVIEW_NOT_READY", "PREVIEW_READY", "HOST_RESULT_READY"),
    "PREVIEW_NOT_READY": ("HOST_RESULT_READY",),
    "PREVIEW_READY": ("AWAITING_HUMAN_CONFIRMATION", "APPROVAL_EXPIRED", "CANCELLED"),
    "AWAITING_HUMAN_CONFIRMATION": ("USER_CANCELLED", "APPROVAL_EXPIRED", "WRITE_REQUEST_QUEUED", "HOST_RESULT_READY"),
    "USER_CANCELLED": ("HOST_RESULT_READY",),
    "APPROVAL_EXPIRED": ("HOST_RESULT_READY",),
    "WRITE_REQUEST_QUEUED": ("WRITE_EXECUTING", "APPROVAL_EXPIRED", "HOST_RESULT_READY", "CANCELLED"),
    "WRITE_EXECUTING": ("WRITE_SUCCEEDED", "WRITE_FAILED", "WRITE_INDETERMINATE"),
    "WRITE_SUCCEEDED": ("HOST_RESULT_READY",),
    "WRITE_FAILED": ("HOST_RESULT_READY",),
    "WRITE_INDETERMINATE": ("HOST_RESULT_READY",),
    "HOST_RESULT_READY": ("PROVIDER_CONTINUATION_PENDING", "COMPLETED", "CANCELLED", "EXPIRED"),
    "PROVIDER_CONTINUATION_PENDING": ("PROVIDER_CONTINUATION_FAILED", "PROVIDER_FINAL_RESPONSE_READY", "COMPLETED", "CANCELLED", "EXPIRED"),
    "PROVIDER_CONTINUATION_FAILED": ("COMPLETED", "CANCELLED", "EXPIRED"),
    "PROVIDER_FINAL_RESPONSE_READY": ("COMPLETED", "CANCELLED", "EXPIRED"),
    "COMPLETED": (), "CANCELLED": (), "EXPIRED": ()}
STATES = tuple(TRANSITIONS)
TERMINAL_STATES = ("COMPLETED", "CANCELLED", "EXPIRED")
Correlation = namedtuple("Correlation", "logical_request_id host_request_id session_id document_id previous_response_id call_id tool_name value")
Request = namedtuple("Request", "correlation state owner timestamp history host_result provider_status terminal_intent retained_safety_lock")
TransitionResult = namedtuple("TransitionResult", "accepted reason request")


def _identifier(value):
    return (isinstance(value, c.string_types) and 0 < len(value) <= 256 and
            all(ch.isalnum() or ch in "_-:." for ch in value))


def correlation(logical_request_id, host_request_id, session_id, document_id,
                previous_response_id=None, call_id=None, value=None):
    """Host-only construction seam; no dict of provider-selected host identities."""
    if not all(_identifier(v) for v in (logical_request_id, host_request_id, session_id, document_id)):
        raise ValueError("INVALID_HOST_CORRELATION")
    if any(v is not None and not _identifier(v) for v in (previous_response_id, call_id)):
        raise ValueError("INVALID_PROVIDER_CORRELATION")
    if value is not None and not c.validate_value(value)["valid"]:
        raise ValueError("INVALID_VALUE")
    return Correlation(logical_request_id, host_request_id, session_id, document_id,
                       previous_response_id, call_id, "set_selected_pipe_test_text", value)


def _time(value):
    return type(value) in (int, float) and value >= 0 and not math.isnan(value) and not math.isinf(value)


def new_request(identity, timestamp):
    if type(identity) is not Correlation or identity != correlation(
            identity.logical_request_id, identity.host_request_id, identity.session_id,
            identity.document_id, identity.previous_response_id, identity.call_id, identity.value):
        raise ValueError("INVALID_CORRELATION")
    if not _time(timestamp):
        raise ValueError("INVALID_TIMESTAMP")
    return Request(identity, "IDLE", "NONE", timestamp, (), None, explanation(), None, False)


def transition(request, identity, target, timestamp, reason, host_result=None, provider_status=None):
    """Invalid transitions return original immutable request, never coerce state."""
    def reject(code):
        return TransitionResult(False, code, request)
    if type(request) is not Request or type(identity) is not Correlation or identity != request.correlation:
        return reject("CORRELATION_MISMATCH")
    if request.state in TERMINAL_STATES:
        return reject("REQUEST_TERMINAL")
    if target not in TRANSITIONS.get(request.state, ()):
        return reject("INVALID_TRANSITION")
    if not _time(timestamp) or timestamp < request.timestamp or not _identifier(reason):
        return reject("INVALID_TRANSITION_EVIDENCE")
    if target == "WRITE_ARGUMENTS_VALIDATED" and not c.validate_value(identity.value)["valid"]:
        return reject("INVALID_VALUE")
    receipt = request.host_result
    if host_result is not None:
        if target not in ("WRITE_SUCCEEDED", "WRITE_FAILED", "WRITE_INDETERMINATE", "HOST_RESULT_READY"):
            return reject("UNEXPECTED_HOST_RESULT")
        try:
            data = project_receipt(host_result)
        except (ValueError, TypeError, KeyError):
            return reject("INVALID_HOST_RESULT")
        if data["request_id"] != identity.host_request_id:
            return reject("HOST_REQUEST_MISMATCH")
        if receipt is not None and receipt != host_result:
            return reject("HOST_RESULT_IMMUTABLE")
        receipt = host_result
    required = {"WRITE_SUCCEEDED": "MEP_PARAMETER_WRITE_OK", "WRITE_FAILED": "MEP_PARAMETER_WRITE_FAILED",
                "WRITE_INDETERMINATE": "MEP_PARAMETER_WRITE_INDETERMINATE"}
    if target in required and (receipt is None or project_receipt(receipt)["classification"] != required[target]):
        return reject("HOST_OUTCOME_MISMATCH")
    if target in ("HOST_RESULT_READY", "PROVIDER_CONTINUATION_PENDING") and receipt is None:
        return reject("HOST_RESULT_REQUIRED")
    if target == "HOST_RESULT_READY" and request.state not in ("WRITE_SUCCEEDED", "WRITE_FAILED", "WRITE_INDETERMINATE"):
        data = project_receipt(receipt)
        if (data["transaction_started"] or data["transaction_committed"] or
                data["model_modified"] is not False or data["verification_performed"] or
                data["classification"] == "MEP_PARAMETER_WRITE_OK"):
            return reject("UNEXPECTED_EXECUTION_EVIDENCE")
        if request.state == "USER_CANCELLED" and data["classification"] != "MEP_PARAMETER_WRITE_CANCELLED":
            return reject("HOST_OUTCOME_MISMATCH")
        if request.state == "APPROVAL_EXPIRED" and data["reason_code"] not in (
                "CONFIRMATION_EXPIRED", "PREVIEW_LEASE_EXPIRED", "EXECUTION_QUEUE_LEASE_EXPIRED"):
            return reject("HOST_OUTCOME_MISMATCH")
    if target == "PROVIDER_CONTINUATION_PENDING" and not (identity.previous_response_id and identity.call_id):
        return reject("PROVIDER_CORRELATION_REQUIRED")
    intent = request.terminal_intent
    if target == "USER_CANCELLED":
        intent = "CANCELLED"
    if target == "APPROVAL_EXPIRED":
        intent = "EXPIRED"
    if target in TERMINAL_STATES and intent is not None and target != intent:
        return reject("TERMINAL_INTENT_MISMATCH")
    status = provider_status or request.provider_status
    try:
        status = explanation(*status)
    except (ValueError, TypeError):
        return reject("INVALID_PROVIDER_STATUS")
    expected_status = {"PROVIDER_CONTINUATION_PENDING": "PENDING", "PROVIDER_CONTINUATION_FAILED": "FAILED",
                       "PROVIDER_FINAL_RESPONSE_READY": "COMPLETE"}.get(target)
    if expected_status:
        if provider_status is not None and status.status != expected_status:
            return reject("PROVIDER_STATUS_MISMATCH")
        status = status._replace(status=expected_status)
    owner = request.owner
    if target in TERMINAL_STATES:
        owner = "NONE"
    elif target in ("PROVIDER_INITIAL_REQUEST", "PROVIDER_TOOL_SELECTED"):
        owner = "PROVIDER_TURN"
    elif target == "WRITE_ARGUMENTS_VALIDATED":
        owner = "CONTROLLED_WRITE_PROVIDER_TOOL"
    retained = request.retained_safety_lock or target == "WRITE_INDETERMINATE"
    updated = request._replace(state=target, owner=owner, timestamp=timestamp,
        history=request.history + ((request.state, target, reason, timestamp),),
        host_result=receipt, provider_status=status, terminal_intent=intent,
        retained_safety_lock=retained)
    return TransitionResult(True, "COMPLETE", updated)


def cleanup_intent(request, trigger):
    """Report cleanup only. Never cancel an executing transaction or resolve it."""
    if trigger not in ("completed", "cancelled", "expired", "provider_continuation_failure",
                       "pane_disposal", "document_close", "shutdown"):
        raise ValueError("INVALID_CLEANUP_TRIGGER")
    retained = request.retained_safety_lock or request.state == "WRITE_EXECUTING"
    terminal = request.state in TERMINAL_STATES
    return dict(trigger=trigger, owner_release_required=not retained,
                callback_invalidation_required=True, retained_host_result=request.host_result,
                retained_provider_status=request.provider_status, state_terminal=terminal,
                finalization_required=not terminal, continuation_allowed=False,
                retained_safety_lock=retained)
