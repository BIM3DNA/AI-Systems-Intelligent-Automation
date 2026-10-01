"""One-shot host-result explanation seam; not wired to pane or write dispatch.

begin/finish/close belong to the future logical-owner thread. run_worker is scalar
work only and must run off the UI thread. No callback invokes Revit or another
completion sink. Instances are single-use, including after failure or disposal.
"""
import json
import re
import threading
import uuid
from collections import namedtuple
from bimcode_ai_pane import provider_write as machine
from bimcode_ai_pane import write_projection as projection
from bimcode_ai_pane import provider_bridge as bridge
from bimcode_ai_pane.write_completion import CompletionSink

Input = namedtuple("Input", "logical_request_id previous_response_id call_id tool_name function_call_output "
                   "host_result host_classification host_reason provider_status created_at model transport_id")
Final = namedtuple("Final", "logical_request_id host_result provider_status response_id text reason "
                   "started_at completed_at timed_out tools_disabled second_tool_requested cleanup")
ERROR_MAP = {
    "SIDECAR_TIMEOUT": "CONTINUATION_TIMEOUT", "OPENAI_TIMEOUT": "CONTINUATION_TIMEOUT",
    "SIDECAR_START_FAILED": "SIDECAR_START_FAILED", "SIDECAR_NONZERO_EXIT": "SIDECAR_EXIT_FAILED",
    "SIDECAR_REQUEST_ID_MISMATCH": "RESPONSE_CORRELATION_FAILED",
    "AI_TOOL_LOOP_LIMIT": "SECOND_TOOL_REQUESTED", "CONTINUATION_OUTPUT_TOO_LARGE": "OUTPUT_TOO_LARGE",
    "SIDECAR_PROTOCOL_ERROR": "MALFORMED_CONTINUATION_RESPONSE",
    "OPENAI_EMPTY_RESPONSE": "MALFORMED_CONTINUATION_RESPONSE",
}
REASONS = frozenset(tuple(ERROR_MAP.values()) + ("PROVIDER_UNAVAILABLE", "INTERNAL_CONTINUATION_ERROR"))
_handoff_lock = threading.Lock()


def _model(value):
    return isinstance(value, bridge.TEXT_TYPES) and re.match(r"\A[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z", value)


def prepare(request, sink, admission, model, timestamp):
    """Accept delivered host-local completion, never provider-selected host IDs."""
    if (type(request) is not machine.Request or request.state != "HOST_RESULT_READY" or
            request.provider_status.status != "NOT_STARTED" or
            any(edge[1] == "PROVIDER_CONTINUATION_PENDING" for edge in request.history)):
        raise ValueError("HOST_RESULT_NOT_READY")
    if (type(sink) is not CompletionSink or not sink.delivered or sink.closed or
            sink.receipt is None or admission.active != sink.owner):
        raise ValueError("COMPLETION_NOT_DELIVERED_OR_OWNER_LOST")
    identity, owner, completed = request.correlation, sink.owner, sink.receipt
    if (completed.logical_request_id != identity.logical_request_id or
            completed.host_request_id != identity.host_request_id or
            completed.session_id != identity.session_id or completed.document_id != identity.document_id or
            completed.owner_type != owner.owner_type or request.owner != owner.owner_type or
            (owner.logical_request_id, owner.host_request_id, owner.session_id, owner.document_id) !=
            (identity.logical_request_id, identity.host_request_id, identity.session_id, identity.document_id) or
            completed.receipt != request.host_result):
        raise ValueError("RESPONSE_CORRELATION_FAILED")
    # Revalidate caller-built namedtuples, timestamps and canonical projection.
    machine.new_request(identity, timestamp)
    if timestamp < request.timestamp or not _model(model):
        raise ValueError("INVALID_CONTINUATION_INPUT")
    if not bridge.valid_identifier(identity.previous_response_id) or not bridge.valid_identifier(identity.call_id):
        raise ValueError("PROVIDER_CORRELATION_REQUIRED")
    data = projection.project_receipt(request.host_result)
    if data["request_id"] != identity.host_request_id or data["classification"] == "MEP_PARAMETER_WRITE_PREVIEW_OK":
        raise ValueError("HOST_RESULT_NOT_TERMINAL")
    return Input(identity.logical_request_id, identity.previous_response_id, identity.call_id,
                 identity.tool_name, request.host_result.json, request.host_result, data["classification"],
                 data["reason_code"], request.provider_status, timestamp, model, uuid.uuid4().hex)


def payload(snapshot):
    """Fresh bounded wire copy, with no host identity accepted from provider data."""
    if type(snapshot) is not Input:
        raise ValueError("INVALID_CONTINUATION_INPUT")
    data = projection.project_receipt(snapshot.host_result)
    if (snapshot.function_call_output != snapshot.host_result.json or
            snapshot.host_classification != data["classification"] or snapshot.host_reason != data["reason_code"] or
            snapshot.tool_name != "set_selected_pipe_test_text" or not _model(snapshot.model) or
            not machine._identifier(snapshot.logical_request_id) or
            not bridge.valid_identifier(snapshot.previous_response_id) or not bridge.valid_identifier(snapshot.call_id) or
            re.match(r"\A[a-f0-9]{32}\Z", snapshot.transport_id) is None):
        raise ValueError("INVALID_CONTINUATION_INPUT")
    result = dict(protocol_version=1, request_id=snapshot.transport_id, operation="write_explanation",
                  previous_response_id=snapshot.previous_response_id, call_id=snapshot.call_id,
                  tool_name=snapshot.tool_name, function_call_output=snapshot.function_call_output, model=snapshot.model)
    if len(json.dumps(result, ensure_ascii=True, allow_nan=False)) > 120000:
        raise ValueError("OUTPUT_TOO_LARGE")
    return result


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_KEY")
        result[key] = value
    return result


def decode_final(raw, request_id, exit_code):
    """Sanitize process stdout. Remote error messages/stderr are never retained."""
    if exit_code != 0:
        return dict(reason="SIDECAR_EXIT_FAILED")
    if not isinstance(raw, bridge.TEXT_TYPES):
        return dict(reason="MALFORMED_CONTINUATION_RESPONSE")
    if len(raw) > bridge.MAX_OUTPUT:
        return dict(reason="OUTPUT_TOO_LARGE")
    try:
        data = json.loads(raw, object_pairs_hook=_unique)
        if type(data) is not dict:
            raise ValueError()
        if data.get("request_id") != request_id:
            return dict(reason="RESPONSE_CORRELATION_FAILED")
        if data.get("state") == "TOOL_REQUEST" or "tool_call" in data or "tool_calls" in data:
            return dict(reason="SECOND_TOOL_REQUESTED")
        base = set(("protocol_version", "request_id", "ok", "provider", "model", "text", "error"))
        if (type(data.get("protocol_version")) is not int or data["protocol_version"] != 1 or
                data.get("provider") != "openai" or type(data.get("ok")) is not bool):
            raise ValueError()
        if not data["ok"]:
            if set(data) != base or data["text"] is not None or type(data["error"]) is not dict:
                raise ValueError()
            code = data["error"].get("code")
            if not isinstance(code, bridge.TEXT_TYPES):
                raise ValueError()
            return dict(reason=ERROR_MAP.get(code, "PROVIDER_UNAVAILABLE"))
        if set(data) != base | set(("state", "response_id", "previous_response_id", "call_id")):
            raise ValueError()
        if (data["state"] != "WRITE_FINAL" or data["error"] is not None or not _model(data["model"]) or
                not all(bridge.valid_identifier(data[k]) for k in ("response_id", "previous_response_id", "call_id")) or
                not isinstance(data["text"], bridge.TEXT_TYPES) or not data["text"].strip()):
            raise ValueError()
        if len(data["text"]) > 12000:
            return dict(reason="OUTPUT_TOO_LARGE")
        return data
    except Exception:
        return dict(reason="MALFORMED_CONTINUATION_RESPONSE")


class Coordinator(object):
    """Single logical request / single process attempt; no retries or write actions.

    Future caller owns scheduling and actual admission release. This seam reports
    cleanup intent, never clears an unresolved host transaction's safety lock.
    """
    def __init__(self):
        self.snapshot = None
        self.request = None
        self.result = None
        self.closed = False
        self._worker_started = False
        self._lock = threading.Lock()

    def begin(self, request, sink, admission, model, timestamp):
        with self._lock, _handoff_lock:
            if self.snapshot is not None or self.closed:
                raise ValueError("CONTINUATION_ALREADY_ATTEMPTED")
            if getattr(sink, "continuation_claimed", False):
                raise ValueError("CONTINUATION_ALREADY_ATTEMPTED")
            snapshot = prepare(request, sink, admission, model, timestamp)
            payload(snapshot)
            step = machine.transition(request, request.correlation, "PROVIDER_CONTINUATION_PENDING",
                                      timestamp, "CONTINUATION_STARTED")
            if not step.accepted:
                raise ValueError(step.reason)
            sink.continuation_claimed = True
            self.snapshot, self.request = snapshot, step.request
            return snapshot

    def run_worker(self, snapshot, runner=None):
        with self._lock:
            if snapshot != self.snapshot or self.closed or self._worker_started or snapshot is None:
                raise ValueError("CONTINUATION_ALREADY_ATTEMPTED_OR_STALE")
            self._worker_started = True
        try:
            return (runner or bridge.run)(payload(snapshot), decoder=decode_final)
        except Exception:
            return dict(reason="INTERNAL_CONTINUATION_ERROR")

    def finish(self, snapshot, response, timestamp):
        with self._lock:
            if (self.closed or self.result is not None or snapshot != self.snapshot or
                    snapshot is None or not self._worker_started):
                raise ValueError("LATE_OR_MISMATCHED_CONTINUATION")
            # Decode again: even injected runners must pass the same strict boundary.
            if type(response) is dict and set(response) == set(("reason",)) and response["reason"] in REASONS:
                parsed = response
            else:
                try:
                    parsed = decode_final(json.dumps(response, ensure_ascii=True, allow_nan=False), snapshot.transport_id, 0)
                except Exception:
                    parsed = dict(reason="MALFORMED_CONTINUATION_RESPONSE")
            reason = parsed.get("reason")
            if not reason and (parsed["previous_response_id"] != snapshot.previous_response_id or
                               parsed["call_id"] != snapshot.call_id or parsed["model"] != snapshot.model or
                               parsed["response_id"] == snapshot.previous_response_id):
                reason = "RESPONSE_CORRELATION_FAILED"
            status = projection.explanation("FAILED" if reason else "COMPLETE",
                       None if reason else parsed["response_id"], reason, None, str(timestamp))
            target = "PROVIDER_CONTINUATION_FAILED" if reason else "PROVIDER_FINAL_RESPONSE_READY"
            step = machine.transition(self.request, self.request.correlation, target, timestamp,
                                      reason or "COMPLETE", provider_status=status)
            if not step.accepted:
                raise ValueError(step.reason)
            terminal = machine.transition(step.request, step.request.correlation,
                         step.request.terminal_intent or "COMPLETED", timestamp, reason or "COMPLETE")
            if not terminal.accepted:
                raise ValueError(terminal.reason)
            self.request = terminal.request
            cleanup = machine.cleanup_intent(self.request, "provider_continuation_failure" if reason else "completed")
            self.result = Final(snapshot.logical_request_id, snapshot.host_result, status,
                          status.response_id, None if reason else parsed["text"], reason or "COMPLETE",
                          snapshot.created_at, timestamp, reason == "CONTINUATION_TIMEOUT", True,
                          reason == "SECOND_TOOL_REQUESTED", tuple(sorted(cleanup.items())))
            self.closed = True
            return self.result

    def close(self, trigger="pane_disposal"):
        with self._lock:
            intent = machine.cleanup_intent(self.request, trigger) if self.request is not None else None
            self.closed = True
            return intent
