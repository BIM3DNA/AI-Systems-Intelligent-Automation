"""M4B-0 pure permission/view model. Not wired to pane or provider execution.

Facts must eventually be captured by a host API adapter; unknown facts fail closed.
No API, environment, persistence, target selection, or execution dependencies.
"""
from bimcode_ai_pane.write_contracts import string_types
from collections import namedtuple
from uuid import uuid4
import time
import hashlib
from threading import Lock, RLock
from functools import wraps


def _serialized(failure):
    def decorate(method):
        @wraps(method)
        def call(self, *args, **kwargs):
            if not self._lock.acquire(False):
                return failure
            try:
                return method(self, *args, **kwargs)
            finally:
                self._lock.release()
        return call
    return decorate

OWNER_TYPES = ("PROVIDER_TURN", "READ_ONLY_PROVIDER_TOOL", "CONTROLLED_WRITE_PROVIDER_TOOL",
               "HUMAN_DEV_WRITE", "HUMAN_DEV_PREVIEW", "PARAMETER_PROVISIONING",
               "DETERMINISTIC_READ_ONLY_TOOL")
Owner = namedtuple("Owner", "token owner_type logical_request_id host_request_id document_id session_id acquired_at lease state release_reason")
SafetyResolution = namedtuple('SafetyResolution', 'generation source owner records')


class OperationAdmission(object):
    """Host-created identities only; no timeout stealing or transaction authority."""
    def __init__(self, busy=None):
        # Lock order: operation _lock -> short _state_lock. Intent publishers
        # take ONLY _state_lock, release it, then try _lock nonblocking.
        # No callback/API/transport may run while holding _state_lock.
        self._state_lock = RLock()
        self._active = None
        self._last_released = None
        self._safety_locked = False
        self._safety_generation = 0
        self._safety_records = []
        self._safety_overflow = False
        self._resolution_ticket = None
        self._pending_cleanup = None
        self._predecessor = None
        self.busy = busy
        self._lock = Lock()

    @property
    def active(self):
        with self._state_lock:
            return self._active

    @property
    def last_released(self):
        with self._state_lock:
            return self._last_released

    @property
    def safety_locked(self):
        with self._state_lock:
            return self._safety_locked

    @safety_locked.setter
    def safety_locked(self, value):
        # Legacy trusted callers may only ADD evidence. False cannot erase it.
        self.retain_safety(value)

    def retain_safety(self, unresolved=True, source=None, owner=None, event=None):
        """Trusted host evidence only. Unknown sources are never auto-resolved.

        At most 16 records; overflow retains an intervention-only lock. Callers
        supply stable event keys for retries, not a fresh key per cleanup pass.
        """
        with self._state_lock:
            if unresolved:
                self._publish_safety(source, owner, event)

    def _publish_safety(self, source, owner, event):
        # State lock held. No external calls. None denotes a NEW unknown event.
        if event is not None and any(s is source and o is owner and e == event
                                     for s, o, e in self._safety_records):
            return
        self._safety_generation += 1
        self._resolution_ticket = None
        self._safety_locked = True
        if len(self._safety_records) < 16:
            self._safety_records.append((source, owner, event))
        else:
            self._safety_overflow = True

    def resolution_ticket(self, source, owner):
        """Host-only capability: exact executor and retained request owner.

        Capture BEFORE querying that executor. Never encode/accept this object
        across the provider or Dev JSON boundary. A generation number is NOT
        resolution authority. Uncorrelated/overflow evidence needs intervention.
        """
        with self._state_lock:
            if source is None or type(owner) is not Owner or self._safety_overflow:
                return None
            records = tuple(r for r in self._safety_records if r[0] is source and r[1] is owner)
            if not records:
                return None
            ticket = SafetyResolution(self._safety_generation, source, owner, records)
            self._resolution_ticket = ticket
            return ticket

    def inspect_safety(self):
        with self._state_lock:
            pending = self._pending_cleanup
            owner = self._active
            return dict(retained_safety_lock=self._safety_locked,
                safety_evidence_generation=self._safety_generation,
                safety_evidence_count=len(self._safety_records),
                safety_evidence_overflow=self._safety_overflow,
                owner_present=owner is not None,
                owner_identity=dict(token=owner.token, owner_type=owner.owner_type,
                    logical_request_id=owner.logical_request_id, host_request_id=owner.host_request_id,
                    document_id=owner.document_id, session_id=owner.session_id) if owner else None,
                owner_state='HELD' if owner else 'QUIESCENT',
                pending_cleanup=pending is not None,
                cleanup_reason=pending[1] if pending else None,
                pending_cleanup_execution_active=pending[2] if pending else False,
                requires_intervention=self._safety_locked or pending is not None)

    def publish_owner(self, expected, replacement):
        """Called under _lock; final safety check and owner publication atomic."""
        with self._state_lock:
            if (self._active is not expected or self._safety_locked or
                    self._pending_cleanup is not None):
                return False
            self._active = replacement
            self._predecessor = expected
            return True

    @_serialized(None)
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
        owner = Owner(uuid4().hex, owner_type, logical_request_id, host_request_id,
                            document_id, session_id, acquired_at, lease, "ACQUIRED", None)
        return owner if self.publish_owner(None, owner) else None

    @_serialized(False)
    def release(self, owner, reason):
        return self._release(owner, reason)

    def _release(self, owner, reason):
        with self._state_lock:
            if self._pending_cleanup is not None:
                return False
            if self._active is None:
                return self.last_released is not None and owner == self.last_released[0]
            if owner != self._active:
                return False
            self._last_released = (owner, owner._replace(state="RELEASED", release_reason=reason))
            self._active = None
            return True

    def cleanup(self, owner, reason, execution_active=False, transaction_unresolved=False,
                evidence_source=None):
        # Publish BEFORE attempting the contended operation lock. Same-owner
        # duplicate intent can strengthen, never weaken, retained evidence.
        with self._state_lock:
            # Host-reported uncertainty is session safety evidence, even if
            # ownership transferred just before publication of this intent.
            if execution_active or transaction_unresolved:
                self._publish_safety(evidence_source, owner,
                    ('cleanup', bool(execution_active), bool(transaction_unresolved)))
            if owner is not None and owner is self._predecessor:
                owner = self._active
            if owner is None or owner != self._active:
                return False
            prior = self._pending_cleanup
            active = execution_active or (prior is not None and prior[2])
            self._pending_cleanup = (owner, reason, active)
        return self.reconcile_cleanup(owner, executor_quiescent=not active)

    @_serialized(False)
    def reconcile_cleanup(self, owner, executor_quiescent=False):
        """Trusted host fact only; does NOT resolve retained safety evidence."""
        with self._state_lock:
            pending = self._pending_cleanup
            if (pending is None or pending[0] != owner or self._active != owner or
                    executor_quiescent is not True):
                return False
            self._last_released = (owner, owner._replace(state="RELEASED", release_reason=pending[1]))
            self._active = None
            self._pending_cleanup = None
            return True

    @_serialized(False)
    def resolve_safety(self, executor_quiescent, ticket=None):
        # Only the trusted host may attest explicit executor status inspection.
        with self._state_lock:
            if (executor_quiescent is True and self._active is None and
                    self._pending_cleanup is None and type(ticket) is SafetyResolution and
                    ticket is self._resolution_ticket and ticket.generation == self._safety_generation and
                    not self._safety_overflow):
                self._safety_records = [r for r in self._safety_records
                    if not (r[0] is ticket.source and r[1] is ticket.owner)]
                self._safety_locked = bool(self._safety_records)
                self._resolution_ticket = None
                return True
            return False


def _continuation_pending(session):
    writes = getattr(session, 'controlled_writes', None)
    handoff = getattr(writes, 'handoff', None)
    if handoff is None:
        return False
    handoff.check()  # Deterministic admission boundary, no timer or API work.
    return handoff.pending is not None


def _busy(session, reservation=None):
    turn = getattr(getattr(session, 'ai', None), 'turn', None)
    owned_turn = False
    if reservation is not None:
        transfer = getattr(getattr(session, 'controlled_writes', None), 'transfer', None)
        # Only the retained, validated reservation can account for its own turn.
        owned_turn = transfer is not None and transfer.owns_turn(reservation, turn)
    return bool(_continuation_pending(session) or getattr(session, 'write_busy', False) or
                getattr(getattr(session, 'tools', None), 'pending', None) is not None or
                (turn is not None and not owned_turn))


def admission_for(session):
    manager = getattr(session, "write_admission", None)
    if manager is None:
        manager = OperationAdmission(lambda reservation=None: _busy(session, reservation))
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
