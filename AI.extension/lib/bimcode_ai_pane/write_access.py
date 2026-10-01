"""M4B-0 pure permission/view model. Not wired to pane or provider execution.

Facts must eventually be captured by a host API adapter; unknown facts fail closed.
No API, environment, persistence, target selection, or execution dependencies.
"""
from bimcode_ai_pane.write_contracts import string_types
from collections import namedtuple
from uuid import uuid4
import time
import hashlib

OWNER_TYPES = ("PROVIDER_TURN", "READ_ONLY_PROVIDER_TOOL", "CONTROLLED_WRITE_PROVIDER_TOOL",
               "HUMAN_DEV_WRITE", "HUMAN_DEV_PREVIEW", "PARAMETER_PROVISIONING",
               "DETERMINISTIC_READ_ONLY_TOOL")
Owner = namedtuple("Owner", "token owner_type logical_request_id host_request_id document_id session_id acquired_at lease state release_reason")


class OperationAdmission(object):
    """Host-created identities only; no timeout stealing or transaction authority."""
    def __init__(self, busy=None):
        self.active = None
        self.last_released = None
        self.safety_locked = False
        self.busy = busy

    def acquire(self, owner_type, logical_request_id, host_request_id, document_id,
                session_id, acquired_at, lease=None):
        if owner_type not in OWNER_TYPES:
            raise ValueError("INVALID_OWNER_TYPE")
        if self.active is not None or self.safety_locked or (self.busy is not None and self.busy()):
            return None
        if not all(isinstance(v, string_types) and 0 < len(v) <= 256 for v in
                   (logical_request_id, host_request_id, document_id, session_id)):
            raise ValueError("INVALID_OWNER_IDENTITY")
        if (type(acquired_at) not in (int, float) or not 0 <= acquired_at <= 1e15 or
                (lease is not None and (type(lease) not in (int, float) or not 0 <= lease <= 1e15))):
            raise ValueError("INVALID_OWNER_TIME")
        self.active = Owner(uuid4().hex, owner_type, logical_request_id, host_request_id,
                            document_id, session_id, acquired_at, lease, "ACQUIRED", None)
        return self.active

    def release(self, owner, reason):
        if self.active is None:
            return self.last_released is not None and owner == self.last_released[0]
        if owner != self.active:
            return False
        self.last_released = (owner, owner._replace(state="RELEASED", release_reason=reason))
        self.active = None
        return True

    def cleanup(self, owner, reason, execution_active=False, transaction_unresolved=False):
        if owner != self.active:
            return False
        if execution_active or transaction_unresolved:
            self.safety_locked = True
        return self.release(owner, reason)

    def resolve_safety(self, executor_quiescent):
        # Only the trusted host may attest explicit executor status inspection.
        if executor_quiescent is True and self.active is None:
            self.safety_locked = False
            return True
        return False


def admission_for(session):
    manager = getattr(session, "write_admission", None)
    if manager is None:
        manager = OperationAdmission(lambda: bool(getattr(session, "write_busy", False) or
            getattr(getattr(session, "tools", None), "pending", None) is not None or
            getattr(getattr(session, "ai", None), "turn", None) is not None))
        session.write_admission = manager
    return manager


def admission_blocked(session):
    manager = getattr(session, "write_admission", None)
    return manager is not None and (manager.active is not None or manager.safety_locked)


def owner_document_key(session):
    # Bounded opaque identity from the existing cached scalar document tuple.
    return hashlib.sha256(repr(getattr(session, "document_identity", None)).encode("utf-8")).hexdigest()


def run_human_operation(session, owner_type, operation):
    """Thin synchronous Dev-command guard; no added target/parameter semantics."""
    if session is None:
        return operation()
    manager = admission_for(session)
    request_id = uuid4().hex
    owner = manager.acquire(owner_type, request_id, request_id,
                            owner_document_key(session), str(id(session)), time.time())
    if owner is None:
        raise RuntimeError("M4A operation busy")
    try:
        return operation()
    finally:
        manager.release(owner, "HUMAN_COMMAND_FINISHED")


def document_eligibility(facts):
    """Evaluate explicit scalar host facts, never infer missing evidence as safe."""
    if type(facts) is not dict:
        return dict(eligible=False, reason_code="NO_VALID_DOCUMENT")
    checks = (
        ("valid_document", True, "NO_VALID_DOCUMENT"),
        ("active_uidocument", True, "NO_ACTIVE_UIDOCUMENT"),
        ("family_document", False, "FAMILY_DOCUMENT"),
        ("host_document", True, "NON_HOST_CONTEXT"),
        ("linked_document", False, "LINKED_DOCUMENT"),
        ("workshared", False, "WORKSHARED_DOCUMENT"),
        ("read_only", False, "READ_ONLY_DOCUMENT"),
        ("modifiable", False, "DOCUMENT_MODIFIABLE"),
        ("fixed_parameter_available", True, "FIXED_PARAMETER_MISSING"),
        ("fixed_parameter_binding_valid", True, "FIXED_PARAMETER_BINDING_INVALID"))
    for key, expected, reason in checks:
        if key not in facts or type(facts[key]) is not bool:
            return dict(eligible=False, reason_code="DOCUMENT_FACTS_UNREADABLE", field=key)
        if facts[key] is not expected:
            return dict(eligible=False, reason_code=reason)
    return dict(eligible=True, reason_code="COMPLETE")


class ControlledWritePermission(object):
    """Pure host-local state contract, not an authorization/security token.

    Caller must be a future explicit human UI control, never provider arguments.
    No visible control or event subscriptions are introduced in M4B-0/1.
    """
    def __init__(self):
        self._enabled = False
        self._document_key = None
        self.generation = 0

    def disable(self):
        self._enabled = False
        self._document_key = None
        self.generation += 1

    def enable_from_human(self, document_key, facts, human_confirmed=False):
        self.disable()
        eligibility = document_eligibility(facts)
        if (human_confirmed is not True or
                not isinstance(document_key, string_types) or not document_key):
            return False
        if not eligibility["eligible"]:
            return False
        self._document_key = document_key
        self._enabled = True
        return True

    def document_changed(self, document_key):
        if document_key != self._document_key:
            self.disable()

    def document_closed(self):
        self.disable()

    def pane_disposed(self):
        self.disable()

    def shutdown(self):
        self.disable()

    def view_model(self):
        return dict(enabled=self._enabled, document_key=self._document_key,
                    generation=self.generation,
                    status=("CONTROLLED WRITES: ENABLED FOR THIS SESSION" if self._enabled
                            else "CONTROLLED WRITES: DISABLED"),
                    dispatch_status="PROVIDER WRITE DISPATCH: NOT YET AVAILABLE",
                    provider_exposure_allowed=False)
