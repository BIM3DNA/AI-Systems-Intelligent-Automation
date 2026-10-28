"""Dispatcher-owned context leases; calls the existing read-only coordinator.

No Revit calls here. Runtime subscribes to DocumentChanged; the existing pane
already tracks activation/selection. Only coordinator execution reads the model.
"""
from bimcode_mcp import protocol as p
from bimcode_ai_pane.write_access import admission_blocked, admission_for


class Controller(object):
    def __init__(self, session, clock=None):
        self.session = session
        self.clock = clock or p.monotonic
        self.epoch = 0
        self.closed = False
        self.contexts = {}

    def model_changed(self, sender=None, args=None):
        self.epoch += 1
        self.contexts.clear()

    def stop(self):
        self.closed = True
        self.contexts.clear()

    def stamp(self):
        session = self.session
        return (session.document_identity, session.context_generation,
                session.selection_generation, self.epoch)

    def handle(self, request, ticket):
        """UI dispatcher only; tickets contain scalar JSON and cancellation."""
        rid = request["request_id"]
        fail = lambda code: ticket.complete(p.result(rid, error=code))
        if self.closed or getattr(self.session, "disposed", False):
            fail("BRIDGE_STOPPED")
            return
        if not ticket.alive():
            return
        session = self.session
        if session.document_identity is None:
            fail("NO_ACTIVE_DOCUMENT")
            return
        if (admission_blocked(session) or admission_for(session).busy()
                or getattr(session, "write_busy", False)
                or session.tools.pending is not None or session.ai.turn is not None):
            fail("REVIT_BUSY")
            return
        now = self.clock()
        self.contexts = dict((k, v) for k, v in self.contexts.items() if now < v[1])
        if request["operation"] == "context":
            if len(self.contexts) >= 8:
                fail("CONTEXT_LIMIT")
                return
            token = p.secret()
            self.contexts[token] = (self.stamp(), now + p.CONTEXT_SECONDS)
            ticket.complete(p.result(rid, dict(context_token=token,
                document_title=session.document_identity[1],
                expires_in_seconds=p.CONTEXT_SECONDS, single_use=True,
                selection_generation=session.selection_generation)))
            return
        if request["operation"] != "inspect" or request.get("tool") not in p.TOOLS:
            fail("INVALID_REQUEST")
            return
        lease = self.contexts.pop(request.get("context_token"), None)
        if lease is None or lease[0] != self.stamp() or now >= lease[1]:
            fail("STALE_CONTEXT")
            return

        def guard():
            return (not self.closed and not getattr(session, "disposed", False)
                    and ticket.alive() and self.clock() < lease[1]
                    and self.stamp() == lease[0])

        if not session.ai.begin(rid):
            fail("REVIT_BUSY")
            return
        owned_turn = session.ai.turn

        def complete(error, data):
            try:
                if not guard():
                    fail("STALE_CONTEXT")
                elif error is not None:
                    fail(error["error"]["code"])
                else:
                    ticket.complete(p.result(rid, data))
            finally:
                # Never release another provider/adapter's turn.
                if session.ai.turn is owned_turn:
                    session.ai.clear()

        try:
            session.ai.queue_readonly(rid, request["tool"], complete, guard)
        except Exception:
            complete({"error": {"code": "MODELMIND_EXECUTION_FAILED"}}, None)
