"""M4B-DISPATCH-001 internal, single-use host preview admission ONLY.

Not imported by pane/provider routing. A future trusted host API callback owns
construction and calls dispatch/check_preview; never call on a provider worker.
Identity and readiness are host-owned, not provider arguments. Requires the
existing M4A model-epoch observer. No confirmation, execution, or continuation
entry point exists here. Production registry/gate availability remains unchanged.
"""
import json
from collections import namedtuple
from bimcode_ai_pane import provider_write as machine
from bimcode_ai_pane import write_contracts as contract
from bimcode_ai_pane import write_projection as projection
from bimcode_ai_pane.controlled_write_registry import validate_arguments
from bimcode_ai_pane.write_access import admission_for, owner_document_key, document_eligibility
from bimcode_ai_pane.write_clock import Clock
from bimcode_ai_pane.write_completion import CompletionSink
from bimcode_ai_pane.write_leases import Leases, binding, expired_request
from bimcode_ai_pane.write_lifecycle import Lifecycle
from bimcode_ai_pane.session_write_gate import read_document
from bimcode_write_runtime import _preview, capture_preview_context
from bimcode_write_execution import result_for

Outcome = namedtuple("Outcome", "accepted reason request preview_json lease")


class Dispatcher(object):
    """One logical request; scalar snapshots only, shared session admission.

    A host must retain this object until completion/cleanup. No timeout polling.
    Recheck explicitly at a future UI boundary; these leases are NOT approval.
    The per-session replay ledger is bounded and never evicted to permit replay.
    """
    def __init__(self, session, identity, clock=None, implementation_ready=False):
        machine.new_request(identity, 0)  # Strict immutable correlation validation.
        self.session, self.identity = session, identity
        self.clock = clock if clock is not None else Clock()
        self.ready = implementation_ready is True
        self.admission = admission_for(session)
        self.request = None
        self.owner = None
        self.preview_json = None
        self.leases = Leases(self.clock)
        self.context_binding = None
        self.lifecycle = None
        self.sink = None
        self.used = False
        self.epochs = None
        self.permission_generation = None

    def _out(self, accepted, reason):
        return Outcome(accepted, reason, self.request, self.preview_json, self.leases.preview)

    def _move(self, state, reason, receipt=None):
        try:
            stamp = self.clock.sample().monotonic
        except ValueError:
            if reason != "INTERNAL_DISPATCH_ERROR":
                raise
            stamp = self.request.timestamp  # Failure only; never extends a lease.
        result = machine.transition(self.request, self.identity, state,
            stamp, reason, host_result=receipt)
        if not result.accepted:
            raise ValueError(result.reason)
        self.request = result.request
        if self.lifecycle is not None and self.session.write_gate.lifecycle is self.lifecycle:
            self.session.write_gate.request = self.request

    def _epochs(self):
        values = (self.session.context_generation, self.session.selection_generation,
                  self.session.m4a_write.epoch, self.session.write_gate.cleanup_generation)
        if any(type(v) not in projection.integer_types or v < 0 for v in values):
            raise ValueError("HOST_CONTEXT_UNAVAILABLE")
        return values

    def _permission(self, document):
        gate = self.session.write_gate
        state = gate.permission.view_model()
        return (not gate.closed and state["enabled"] is True and
                gate.document == document == state["document_key"] == self.identity.document_id)

    def _finish(self, reason, preview=None, failed=False):
        """Nonexecution result in existing reducer/projection contracts."""
        if self.request is not None and self.request.state not in machine.TERMINAL_STATES:
            if self.request.host_result is None:
                if preview is None:
                    data = json.loads(self.preview_json) if self.preview_json else dict(
                        request_id=self.identity.host_request_id, proposed_value=self.identity.value)
                    receipt = projection.from_host_result(result_for(data, "FAILED" if failed else "NOT_READY", reason))
                else:
                    receipt = projection.from_preview(preview)
                self._move("HOST_RESULT_READY", reason, receipt)
            self._move("EXPIRED" if self.request.terminal_intent == "EXPIRED" else "COMPLETED", reason)
        self.leases.invalidate("REQUEST_FINALIZED")
        if self.lifecycle is not None:
            gate = self.session.write_gate
            if gate.lifecycle is self.lifecycle:
                if gate.permission.generation == self.lifecycle.permission_generation:
                    self.lifecycle.finalize(self.request)
                else:
                    # Permission was independently revoked. Never disable a newer
                    # permission or release anyone else's owner during late cleanup.
                    self.sink.cleanup()
                    self.admission.release(self.owner, reason)
                gate.lifecycle, gate.request = None, None
        elif self.owner is not None:
            self.admission.release(self.owner, reason)
        try:
            self.session.render_write_gate()
        except Exception:
            pass  # Host receipt/admission safety must survive pane disposal.
        return self._out(False, reason)

    def dispatch(self, uiapp, call, previous_response_id):
        """Valid Revit API context only; no API access during construction."""
        from Autodesk.Revit import DB
        from System import Guid
        return self._dispatch(uiapp, call, previous_response_id, DB,
                              Guid(contract.M4A_TEST_PARAMETER_GUID))

    def _dispatch(self, uiapp, call, previous_response_id, db, guid):
        # Dependency injection is host/test-only, not a provider payload seam.
        if self.used:
            return self._out(False, "REQUEST_TERMINAL" if self.request is not None and
                self.request.state in machine.TERMINAL_STATES else "AI_TOOL_LOOP_LIMIT")
        self.used = True  # Consume even rejected/failed attempts.
        try:
            self.request = machine.new_request(self.identity, self.clock.sample().monotonic)
            self._move("PROVIDER_INITIAL_REQUEST", "COMPLETE")
            self._move("PROVIDER_TOOL_SELECTED", "COMPLETE")
            if not self.ready:
                return self._finish("IMPLEMENTATION_UNAVAILABLE")
            if (type(call) is not dict or set(call) != set(("name", "call_id", "arguments")) or
                    call["name"] != self.identity.tool_name):
                return self._finish("AI_TOOL_NOT_ALLOWED")
            if (not self.identity.previous_response_id or not self.identity.call_id or
                    previous_response_id != self.identity.previous_response_id or
                    call["call_id"] != self.identity.call_id or
                    self.identity.session_id != str(id(self.session)) or
                    self.identity.document_id != owner_document_key(self.session)):
                return self._finish("CORRELATION_MISMATCH")
            ledger = getattr(self.session, "_internal_write_dispatch_seen", None)
            if ledger is None:
                ledger = set()
                self.session._internal_write_dispatch_seen = ledger
            keys = (('logical', self.identity.logical_request_id), ('host', self.identity.host_request_id),
                    ('call', self.identity.previous_response_id, self.identity.call_id),
                    ('response', self.identity.previous_response_id))
            if any(key in ledger for key in keys):
                return self._finish("REQUEST_TERMINAL")
            if len(ledger) >= 4000:
                return self._finish("EXECUTION_BUSY")
            ledger.update(keys)  # Also consume rejected validated correlations.
            checked = validate_arguments(call["arguments"])
            if not checked["valid"]:
                return self._finish(checked["reason_code"])
            if checked["value"] != self.identity.value:
                return self._finish("CORRELATION_MISMATCH")
            gate = self.session.write_gate
            if gate.admission is not self.admission:
                return self._finish("CORRELATION_MISMATCH")
            if not self._permission(self.identity.document_id):
                return self._finish("PERMISSION_DISABLED")
            if self.admission.safety_locked:
                return self._finish("UNRESOLVED_MUTATION_SAFETY")
            if self.admission.active is not None or gate.lifecycle is not None:
                return self._finish("EXECUTION_BUSY")
            try:
                self.epochs = self._epochs()
            except (AttributeError, ValueError):
                return self._finish("HOST_CONTEXT_UNAVAILABLE")
            self.permission_generation = gate.permission.generation
            document, facts = read_document(uiapp, db, guid)
            eligible = document_eligibility(facts)
            if not eligible["eligible"]:
                gate.observe(document, facts)
                return self._finish(eligible["reason_code"])
            if document != self.identity.document_id:
                gate.observe(document, facts)
                return self._finish("CORRELATION_MISMATCH")
            self.owner = self.admission.acquire("CONTROLLED_WRITE_PROVIDER_TOOL",
                self.identity.logical_request_id, self.identity.host_request_id, document,
                self.identity.session_id, self.clock.sample().monotonic)
            if self.owner is None:
                return self._finish("EXECUTION_BUSY")
            self._move("WRITE_ARGUMENTS_VALIDATED", "COMPLETE")
            self._move("HOST_PREVIEW_BUILDING", "COMPLETE")
            context = capture_preview_context(uiapp)
            preview = _preview(uiapp, self.identity.host_request_id, self.identity.value,
                               self.epochs[1], db, guid, context)
            if (preview.get("request_id") != self.identity.host_request_id or
                    preview.get("proposed_value") != self.identity.value or
                    preview.get("feature_id") != contract.M4A_FEATURE_ID or
                    preview.get("action_id") != contract.M4A_ACTION_ID or
                    preview.get("parameter_guid") != contract.M4A_TEST_PARAMETER_GUID):
                return self._finish("CORRELATION_MISMATCH")
            projection.from_preview(preview)  # Validate scalar shape/nonmutation flags.
            self.preview_json = json.dumps(preview, sort_keys=True, ensure_ascii=True, allow_nan=False)
            if preview["classification"] != contract.PREVIEW_OK or preview["reason_code"] != "COMPLETE":
                self._move("PREVIEW_NOT_READY", preview["reason_code"])
                return self._finish(preview["reason_code"], preview)
            if (self._epochs() != self.epochs or not self._permission(document) or
                    gate.permission.generation != self.permission_generation or self.admission.active != self.owner):
                return self._finish("STALE_CONTEXT")
            if (preview["selection_snapshot"] != context["metadata"] or
                    preview["selection_fingerprint"] != context["fingerprint"] or
                    preview["document_identity"] != context["metadata"]["document_identity"] or
                    preview["view_identity"] != context["metadata"]["view_identity"] or
                    [preview["target_element_id"]] != context["metadata"]["selected_element_ids"]):
                self.preview_json = None
                return self._finish("CORRELATION_MISMATCH")
            self.context_binding = binding(self.identity, self.owner, preview["selection_fingerprint"],
                preview["target_element_id"], preview["target_unique_id"], preview["current_has_value"],
                preview["current_value"], self.epochs[2], self.epochs[3], preview["parameter_guid"])
            lease = self.leases.create_preview(self.context_binding)
            if not lease.accepted:
                return self._finish(lease.reason)
            self._move("PREVIEW_READY", "COMPLETE")
            self._move("AWAITING_HUMAN_CONFIRMATION", "COMPLETE")
            self.sink = CompletionSink(self.owner)
            self.lifecycle = Lifecycle(self.owner, self.admission, gate.permission, self.leases, self.sink)
            gate.lifecycle, gate.request = self.lifecycle, self.request
            return self._out(True, "COMPLETE")
        except Exception:
            return self._error()

    def _error(self):
        # Explicit bounded failure, never log API/provider exceptions. Cleanup
        # does not clear any independent mutation safety lock or stored receipt.
        try:
            return self._finish("INTERNAL_DISPATCH_ERROR", failed=True)
        except Exception:
            self.leases.invalidate("ABANDONED")
            if self.owner is not None:
                self.admission.release(self.owner, "INTERNAL_DISPATCH_ERROR")
            if self.sink is not None:
                self.sink.cleanup()
            return self._out(False, "INTERNAL_DISPATCH_ERROR")

    def check_preview(self, uiapp, identity):
        """API-context recheck only; NEVER confirms, queues, or executes a write."""
        from Autodesk.Revit import DB
        from System import Guid
        return self._check_preview(uiapp, identity, DB, Guid(contract.M4A_TEST_PARAMETER_GUID))

    def _check_preview(self, uiapp, identity, db, guid):
        if identity != self.identity:
            return self._out(False, "CORRELATION_MISMATCH")
        if self.request is None or self.request.state != "AWAITING_HUMAN_CONFIRMATION":
            return self._out(False, "REQUEST_TERMINAL")
        try:
            gate = self.session.write_gate
            if self.admission.safety_locked:
                return self._finish("UNRESOLVED_MUTATION_SAFETY")
            if (gate.lifecycle is not self.lifecycle or self.admission.active != self.owner or
                    not self._permission(self.identity.document_id) or
                    gate.permission.generation != self.permission_generation):
                return self._finish("PREVIEW_LEASE_INVALIDATED")
            checked = self.leases.check("PREVIEW", self.context_binding)
            if not checked.accepted:
                if checked.reason == "PREVIEW_LEASE_EXPIRED":
                    self.request = expired_request(self.request, self.leases)
                return self._finish(checked.reason)
            document, facts = read_document(uiapp, db, guid)
            if document != self.identity.document_id or not document_eligibility(facts)["eligible"]:
                gate.observe(document, facts)
                return self._finish("PREVIEW_LEASE_INVALIDATED")
            if self._epochs() != self.epochs:
                return self._finish("PREVIEW_LEASE_INVALIDATED")
            preview = _preview(uiapp, self.identity.host_request_id, self.identity.value,
                               self.epochs[1], db, guid)
            before = json.loads(self.preview_json)
            keys = ('document_identity', 'view_identity', 'selection_snapshot', 'selection_fingerprint',
                    'target_element_id', 'target_unique_id', 'pipe_type', 'parameter_guid',
                    'current_value', 'current_has_value', 'proposed_value', 'binding_kind', 'storage_type', 'writable')
            if (preview["classification"] != contract.PREVIEW_OK or
                    any(preview.get(key) != before.get(key) for key in keys)):
                return self._finish("PREVIEW_LEASE_INVALIDATED")
            return self._out(True, "COMPLETE")
        except Exception:
            return self._error()
