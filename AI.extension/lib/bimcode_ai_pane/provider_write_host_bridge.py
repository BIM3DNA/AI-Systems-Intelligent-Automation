"""DISPATCH-002 host-only bridge. No provider registration or continuation.

Create/confirm from a trusted Revit API callback, never a worker or tool payload.
One bridge retained per pane session; the dedicated event executes later.
"""
import json
from collections import namedtuple
from bimcode_ai_pane import provider_write_confirmation as confirmation
from bimcode_ai_pane import write_contracts as c
from bimcode_ai_pane import provider_write as machine
from bimcode_ai_pane.write_access import owner_document_key, document_eligibility
from bimcode_ai_pane.session_write_gate import read_document
from bimcode_write_execution import Executor, result_for

Pending = namedtuple("Pending", "identity owner preview_json binding epochs permission_generation")


class Bridge(object):
    """No injected production consent or executor. Tests patch native UI only."""
    def __init__(self, session):
        self.session = session
        self.dispatcher = None
        self.pending = None
        self.executor = Executor()
        self.running = False
        self.confirming = False
        self.event = None
        self.handler = None

    def _api(self):
        from Autodesk.Revit import DB
        from System import Guid
        return DB, Guid(c.M4A_TEST_PARAMETER_GUID)

    def _result_move(self, target, reason, receipt=None):
        """Terminal evidence may survive a failed clock; never renew approval."""
        d = self.dispatcher
        try:
            stamp = d.clock.sample().monotonic
        except ValueError:
            stamp = d.request.timestamp
        moved = machine.transition(d.request, d.identity, target, stamp, reason, host_result=receipt)
        if not moved.accepted:
            raise ValueError(moved.reason)
        d.request = moved.request
        if self.session.write_gate.lifecycle is d.lifecycle:
            self.session.write_gate.request = d.request

    def _finish(self, result):
        d = self.dispatcher
        if d.request.host_result is not None:
            return d.request
        d.sink.store(result)
        receipt = d.sink.receipt.receipt
        reason = result["reason_code"]
        if d.request.state == "WRITE_EXECUTING":
            target = {"MEP_PARAMETER_WRITE_OK": "WRITE_SUCCEEDED",
                      "MEP_PARAMETER_WRITE_FAILED": "WRITE_FAILED",
                      "MEP_PARAMETER_WRITE_INDETERMINATE": "WRITE_INDETERMINATE"}[result["classification"]]
            self._result_move(target, reason, receipt)
        self._result_move("HOST_RESULT_READY", reason, receipt)
        self.pending = None
        # Receipt first, then cleanup. Never clear independent safety evidence.
        unresolved = self.executor.retained is not None or result["model_modified"] is None
        if unresolved:
            d.admission.safety_locked = True
        gate = self.session.write_gate
        if gate.lifecycle is d.lifecycle and gate.permission.generation == d.lifecycle.permission_generation:
            # A superseding owner is never released or overwritten by late work.
            if d.admission.active not in (None, d.owner):
                d.leases.invalidate("ABANDONED")
                d.sink.cleanup()
                return d.request
            d.lifecycle.finalize(d.request, transaction_unresolved=unresolved)
            gate.lifecycle, gate.request = None, None
        else:
            d.leases.invalidate("ABANDONED")
            d.sink.cleanup()
            d.admission.release(d.owner, "HOST_RESULT_READY")
        # No callback delivery or continuation in DISPATCH-002.
        return d.request

    def _render_gate(self):
        # Both callers are host/UI callbacks (native confirmation or Execute).
        # A disappearing pane must not alter the authoritative host receipt.
        try:
            self.session.render_write_gate()
        except Exception:
            pass

    def _reject(self, reason, kind="NOT_READY", confirmed=False):
        d = self.dispatcher
        result = result_for(json.loads(d.preview_json), kind, reason)
        if confirmed:
            result["confirmation_result"] = "CONFIRMED"
        if reason in ("PREVIEW_LEASE_EXPIRED", "EXECUTION_QUEUE_LEASE_EXPIRED"):
            self._result_move("APPROVAL_EXPIRED", reason)
        return self._finish(result)

    def _valid(self, uiapp, ticket, db, guid):
        d, gate = self.dispatcher, self.session.write_gate
        if (ticket.identity != d.identity or d.request.correlation != ticket.identity or
                ticket.owner != d.owner or ticket.binding != d.context_binding or
                ticket.preview_json != d.preview_json or
                ticket.identity.session_id != str(id(self.session)) or
                owner_document_key(self.session) != ticket.identity.document_id):
            return "CORRELATION_MISMATCH"
        if d.admission.safety_locked:
            return "UNRESOLVED_MUTATION_SAFETY"
        if d.admission.active != ticket.owner:
            return "EXECUTION_BUSY"
        if (gate.lifecycle is not d.lifecycle or not d._permission(ticket.identity.document_id) or
                gate.permission.generation != ticket.permission_generation or d._epochs() != ticket.epochs):
            return "STALE_CONTEXT"
        document, facts = read_document(uiapp, db, guid)
        eligible = document_eligibility(facts)
        if document != ticket.identity.document_id:
            gate.observe(document, facts)
            return "STALE_CONTEXT"
        if not eligible["eligible"]:
            gate.observe(document, facts)
            return eligible["reason_code"]
        return None

    def request_confirmation(self, uiapp, dispatcher, identity):
        """Trusted pane/host API callback; native dialog is sole consent source."""
        if self.running or self.confirming or self.pending is not None or self.executor.retained is not None:
            return "EXECUTION_BUSY"
        if (dispatcher.session is not self.session or identity != dispatcher.identity or
                dispatcher.request is None or dispatcher.request.state != "AWAITING_HUMAN_CONFIRMATION"):
            return "CORRELATION_MISMATCH"
        self.dispatcher = dispatcher
        d = dispatcher
        ticket = Pending(identity, d.owner, d.preview_json, d.context_binding,
                         d.epochs, d.permission_generation)
        self.confirming = True
        try:
            db, guid = self._api()
            checked = d.leases.check("PREVIEW", ticket.binding)
            if not checked.accepted:
                return self._reject(checked.reason)
            reason = self._valid(uiapp, ticket, db, guid)
            if reason:
                return self._reject(reason)
            # No silent preview replacement: check exact original preconditions.
            self.executor.revalidate(uiapp, json.loads(ticket.preview_json), db, guid)
            if not confirmation.show(json.loads(ticket.preview_json), identity):
                d._move("USER_CANCELLED", "USER_CANCELLED")
                result = self._reject("USER_CANCELLED", "CANCELLED")
                d._move("CANCELLED", "USER_CANCELLED")
                return d.request
            # Consume at the native Confirm return, not after another API pass.
            checked = d.leases.confirm(ticket.binding, human_confirmed=True)
            if not checked.accepted:
                return self._reject(checked.reason)
            reason = self._valid(uiapp, ticket, db, guid)
            if reason:
                return self._reject(reason, confirmed=True)
            d._move("WRITE_REQUEST_QUEUED", "COMPLETE")
            checked = d.leases.queue_raised(ticket.binding)
            if not checked.accepted:
                return self._reject(checked.reason, confirmed=True)
            self.pending = ticket
            from Autodesk.Revit import UI
            try:
                accepted = self.event.Raise() == UI.ExternalEventRequest.Accepted
            except Exception:
                accepted = False
            if not accepted:
                self.pending = None
                return self._reject("EXTERNAL_EVENT_NOT_ACCEPTED", "FAILED", True)
            return d.request
        except Exception as error:
            self.pending = None
            return self._reject(getattr(error, "reason", "CONFIRMATION_FAILED"), "FAILED")
        finally:
            self.confirming = False
            self._render_gate()

    def execute(self, uiapp):
        if self.running or self.pending is None:
            return None
        ticket, self.pending = self.pending, None  # Consume before any callback/API.
        d = self.dispatcher
        self.running = True
        try:
            if d.request.state != "WRITE_REQUEST_QUEUED":
                return None
            checked = d.leases.handler_started(ticket.binding)
            if not checked.accepted:
                return self._reject(checked.reason, confirmed=True)
            db, guid = self._api()
            reason = self._valid(uiapp, ticket, db, guid)
            if reason:
                return self._reject(reason, confirmed=True)
            def admitted():
                # Last scalar guard, after executor host reads and before Start.
                reason = self._valid(uiapp, ticket, db, guid)
                if reason:
                    from bimcode_write_runtime import PreviewBlocked
                    raise PreviewBlocked(reason)
                d._move("WRITE_EXECUTING", "COMPLETE")
            result = self.executor.execute_provider(json.loads(ticket.preview_json), uiapp, db, guid, admitted)
            return self._finish(result)
        except Exception as error:
            result = result_for(json.loads(ticket.preview_json), "FAILED", getattr(error, "reason", "INTERNAL_ERROR"))
            result["confirmation_result"] = "CONFIRMED"
            if d.request.state == "WRITE_EXECUTING":
                result.update(classification="MEP_PARAMETER_WRITE_INDETERMINATE", model_modified=None,
                              transaction_status="Unknown")
                d.admission.safety_locked = True
            return self._finish(result)
        finally:
            self.running = False
            self._render_gate()


def get_bridge(session):
    """Create once in valid API context, retain handler/event with pane session."""
    current = getattr(session, "provider_write_bridge", None)
    if current is None:
        from Autodesk.Revit import UI
        # Reuse existing model observer, not its HUMAN_DEV_WRITE owner or event.
        from bimcode_ai_pane.write_coordinator import get_coordinator
        get_coordinator(session)
        current = Bridge(session)
        class Handler(UI.IExternalEventHandler):
            def GetName(self):
                return "BIMCode M4B native-confirmed provider contract write"
            def Execute(self, uiapp):
                current.execute(uiapp)
        current.handler = Handler()
        current.event = UI.ExternalEvent.Create(current.handler)
        session.provider_write_bridge = current
    return current
