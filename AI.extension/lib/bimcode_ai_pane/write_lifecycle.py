"""Callable provider-write cleanup foundation, deliberately NOT event-wired.

No executor/API cancellation, no retry, no receipt revision. Continuation close
suppresses future/late delivery; an already-running scalar sidecar drains under
its existing timeout. Executing owners remain held; quiescent indeterminate
requests may release orchestration ownership but NEVER their safety lock.
"""
from collections import namedtuple
from bimcode_ai_pane import provider_write as machine
from bimcode_ai_pane import write_projection as projection

Cleanup = namedtuple("Cleanup", "reason owner_released owner_held permission_reset callback_invalidated "
                     "continuation_cancelled host_result retained_safety_lock request")
TRIGGERS = {"DOCUMENT_SWITCH": "document_close", "DOCUMENT_CLOSE": "document_close",
            "PANE_DISPOSAL": "pane_disposal", "SHUTDOWN": "shutdown",
            "ABANDONED": "cancelled", "CONTINUATION_TERMINAL": "completed"}


class Lifecycle(object):
    """One instance per host-owned request. Call only on the logical-owner thread.

    All methods take the latest immutable reducer request. Optional executing /
    unresolved flags are trusted executor facts, never provider data. Defaults
    cannot override retained state or EXECUTION_STARTED without a host receipt.
    Repeated identical cleanup is inert; later authoritative completion can settle
    the same held owner. It never resolves a retained safety lock automatically.
    """
    def __init__(self, owner, admission, permission, leases, sink, continuation=None):
        if admission.active != owner or sink.owner != owner:
            raise ValueError("LEASE_CORRELATION_FAILED")
        self.owner, self.admission, self.permission = owner, admission, permission
        self.leases, self.sink, self.continuation = leases, sink, continuation
        self.permission_generation = permission.generation
        self.result, self._evidence = None, None
        self.receipt = None

    def cleanup(self, reason, request, execution_active=False, transaction_unresolved=False):
        if reason not in TRIGGERS or type(execution_active) is not bool or type(transaction_unresolved) is not bool:
            raise ValueError("INVALID_CLEANUP_REASON")
        identity = request.correlation
        owner = self.owner
        if (identity.logical_request_id, identity.host_request_id, identity.document_id, identity.session_id) != (
                owner.logical_request_id, owner.host_request_id, owner.document_id, owner.session_id):
            raise ValueError("LEASE_CORRELATION_FAILED")
        if reason == "CONTINUATION_TERMINAL" and request.state not in machine.TERMINAL_STATES:
            raise ValueError("REQUEST_NOT_TERMINAL")
        for lease in (self.leases.preview, self.leases.queue):
            if lease.binding is not None and lease.binding.owner != owner:
                raise ValueError("LEASE_CORRELATION_FAILED")
        completion = self.sink.receipt
        receipt = request.host_result or (completion.receipt if completion is not None else None)
        if completion is not None and (completion.logical_request_id, completion.host_request_id,
                completion.document_id, completion.session_id, completion.owner_type) != (
                owner.logical_request_id, owner.host_request_id, owner.document_id, owner.session_id, owner.owner_type):
            raise ValueError("LEASE_CORRELATION_FAILED")
        if (completion is not None and receipt != completion.receipt) or (self.receipt is not None and receipt != self.receipt):
            raise ValueError("HOST_RESULT_IMMUTABLE")
        host = projection.project_receipt(receipt) if receipt is not None else None
        if host is not None and host["request_id"] != owner.host_request_id:
            raise ValueError("LEASE_CORRELATION_FAILED")
        evidence = (reason, request, receipt, execution_active, transaction_unresolved)
        if evidence == self._evidence:
            return self.result
        # A late old cleanup cannot disable/release a newer request or permission.
        if self.admission.active not in (None, owner):
            raise ValueError("LEASE_CORRELATION_FAILED")
        if self.admission.active is None and (self.admission.last_released is None or self.admission.last_released[0] != owner):
            raise ValueError("LEASE_CORRELATION_FAILED")
        if self.permission.generation != self.permission_generation:
            raise ValueError("LEASE_CORRELATION_FAILED")
        if self.continuation is not None and self.continuation.request is not None:
            if self.continuation.request.correlation != identity or (
                    self.continuation.request.host_result is not None and self.continuation.request.host_result != receipt):
                raise ValueError("LEASE_CORRELATION_FAILED")
        active = execution_active or request.state == "WRITE_EXECUTING" or (
            self.leases.queue.state == "EXECUTION_STARTED" and host is None)
        unresolved = (transaction_unresolved or request.retained_safety_lock or
                      (host is not None and (host["classification"] == "MEP_PARAMETER_WRITE_INDETERMINATE" or
                       host["model_modified"] is None or host["transaction_status"] in ("Started", "Pending", "Unknown"))))
        self.receipt = receipt
        self.permission.disable()  # Conservative reset, no silent auto-enable/revalidation.
        self.permission_generation = self.permission.generation
        self.leases.invalidate(reason)
        self.sink.cleanup()  # Immutable stored completion is retained.
        if self.continuation is not None:
            self.continuation.close(TRIGGERS[reason])
        if active or unresolved:
            self.admission.safety_locked = True
        released = False
        if not active:
            released = self.admission.release(owner, reason)
        self.result = Cleanup(reason, released, active, True, True, self.continuation is not None,
                              receipt, self.admission.safety_locked, request)
        self._evidence = evidence
        return self.result

    def document_switch(self, request, **facts):
        return self.cleanup("DOCUMENT_SWITCH", request, **facts)

    def document_close(self, request, **facts):
        return self.cleanup("DOCUMENT_CLOSE", request, **facts)

    def pane_disposal(self, request, **facts):
        return self.cleanup("PANE_DISPOSAL", request, **facts)

    def shutdown(self, request, **facts):
        return self.cleanup("SHUTDOWN", request, **facts)

    def abandon(self, request, **facts):
        return self.cleanup("ABANDONED", request, **facts)

    def continuation_terminal(self, request, **facts):
        return self.cleanup("CONTINUATION_TERMINAL", request, **facts)
