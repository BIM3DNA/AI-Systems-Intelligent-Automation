"""Immutable scalar completion and at-most-once sink; no Revit/provider imports."""
from collections import namedtuple
from bimcode_ai_pane import write_projection as projection

Completion = namedtuple("Completion", "logical_request_id host_request_id owner_type document_id session_id receipt")


def completion(owner, result):
    # Early cancellation has no preview ID. Correlation comes from the host owner,
    # never provider text. The original host result is not edited.
    data = dict(result)
    if data.get("request_id") not in (None, owner.host_request_id):
        raise ValueError("HOST_REQUEST_MISMATCH")
    data["request_id"] = owner.host_request_id
    if data.get("classification", "").startswith("MEP_PARAMETER_WRITE_PREVIEW_"):
        receipt = projection.from_preview(data)
    else:
        receipt = projection.from_host_result(data)
    return Completion(owner.logical_request_id, owner.host_request_id, owner.owner_type,
                      owner.document_id, owner.session_id, receipt)


class CompletionSink(object):
    """Trusted host-local callback; receives scalars, not Revit objects or executor.

    This is not a Python sandbox. Coordinator dispatches delivery after API work.
    Failure diagnostics intentionally omit exception text and traceback.
    """
    def __init__(self, owner, callback=None):
        if callback is not None and not callable(callback):
            raise ValueError("INVALID_CALLBACK")
        self.owner = owner
        self.callback = callback
        self.receipt = None
        self.closed = False
        self.delivered = False
        self.error = None

    def store(self, result):
        if self.receipt is not None:
            return False
        self.receipt = completion(self.owner, result)
        return True

    def deliver(self, logical_request_id):
        if logical_request_id != self.owner.logical_request_id:
            return False
        if self.closed or self.delivered or self.receipt is None:
            return False
        self.delivered = True  # Consume before user code, including reentrancy.
        try:
            if self.callback is not None:
                self.callback(self.receipt)
        except Exception:
            self.error = "CALLBACK_FAILED"
        finally:
            self.callback = None
        return True

    def cleanup(self):
        self.closed = True
        self.callback = None
