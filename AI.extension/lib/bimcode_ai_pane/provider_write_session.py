"""Session-engine authority boundary. Caller engines exchange strings only.

Not registered with the provider. begin/confirm require a trusted human host
callback in valid Revit API context. inspect reads retained scalar state only.
"""
import json
from uuid import uuid4
from bimcode_ai_pane.provider_write_dispatch import Dispatcher
from bimcode_ai_pane.provider_write_host_bridge import get_bridge
from bimcode_ai_pane.provider_write import correlation
from bimcode_ai_pane.write_access import admission_for, owner_document_key
from bimcode_ai_pane.write_contracts import validate_value, string_types


def encoded(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=True, allow_nan=False)


class SessionWrites(object):
    """Constructed only by PaneSession in the persistent startup engine.

    Host generates all identities. Dev callers cannot inject coordination
    instances, correlation fields, a consent boolean, a target or an action.
    This is a trusted host entry, not a Python sandbox or a provider endpoint.
    """
    def __init__(self, session):
        self.session = session
        self.dispatcher = None

    def begin(self, value):
        checked = validate_value(value)
        if not checked["valid"]:
            return encoded(dict(accepted=False, reason=checked["reason_code"]))
        s = self.session
        gate = s.write_gate
        if getattr(s, "disposed", False) or gate.closed or not gate.permission.view_model()["enabled"]:
            return encoded(dict(accepted=False, reason="PERMISSION_DISABLED"))
        admission = admission_for(s)
        if (admission.active is not None or admission.safety_locked or
                (admission.busy is not None and admission.busy())):
            return encoded(dict(accepted=False, reason="EXECUTION_BUSY"))
        # Called in this method's engine, NOT the invoking Dev engine.
        bridge = get_bridge(s)
        if bridge.pending is not None or bridge.running or bridge.confirming or bridge.executor.retained is not None:
            return encoded(dict(accepted=False, reason="EXECUTION_BUSY"))
        identity = correlation(uuid4().hex, uuid4().hex, str(id(s)), owner_document_key(s),
            "host-test-response-" + uuid4().hex, "host-test-call-" + uuid4().hex, value)
        d = Dispatcher(s, identity, implementation_ready=True)
        self.dispatcher = d
        outcome = d.dispatch(s.uiapp, dict(name=identity.tool_name, call_id=identity.call_id,
                            arguments=dict(value=value)), identity.previous_response_id)
        return encoded(dict(accepted=outcome.accepted, reason=outcome.reason,
                            host_request_id=identity.host_request_id, state=d.request.state if d.request else None))

    def confirm(self, host_request_id):
        d = self.dispatcher
        if (not isinstance(host_request_id, string_types) or d is None or
                host_request_id != d.identity.host_request_id):
            return encoded(dict(accepted=False, reason="CORRELATION_MISMATCH"))
        # No caller-provided approval. The retained bridge opens native UI.
        bridge = get_bridge(self.session)
        result = bridge.request_confirmation(self.session.uiapp, d, d.identity)
        if isinstance(result, string_types):
            return encoded(dict(accepted=False, reason=result))
        return self.inspect()

    def inspect(self):
        gate = self.session.write_gate
        admission = gate.admission
        availability = dict(permission_enabled=not getattr(self.session, "disposed", False) and
            not gate.closed and gate.permission.view_model()["enabled"],
            busy=bool(admission.active is not None or admission.safety_locked or
                      (admission.busy is not None and admission.busy())))
        d = self.dispatcher
        if d is None:
            return encoded(dict(availability, reason="NO_RETAINED_HARNESS_REQUEST"))
        request = d.request
        return encoded(dict(availability, correlation=d.identity._asdict(),
            state=request.state if request else None, history=request.history if request else (),
            host_result=json.loads(request.host_result.json) if request and request.host_result else None,
            preview=json.loads(d.preview_json) if d.preview_json else None,
            leases=json.loads(d.leases.provenance())))
