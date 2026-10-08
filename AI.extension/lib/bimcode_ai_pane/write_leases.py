"""Provider-only 120/30 leases; no dispatch, dialog, executor or transaction.

M4A CONFIRMATION_EXPIRED retains its legacy 60-second meaning. The two provider
expiry reasons map to NOT_READY/nonexecution, not transaction failure. This task's
distinct-reason requirement supersedes design section 9's proposed common reason.
No M4A caller uses these contracts.
"""
import json
from collections import namedtuple
from bimcode_ai_pane import write_contracts as c
from bimcode_ai_pane import provider_write as machine
from bimcode_ai_pane import write_projection as projection
from bimcode_ai_pane.write_access import Owner
from bimcode_ai_pane.write_clock import Clock, deadline

PREVIEW_SECONDS, EXECUTION_QUEUE_SECONDS = 120, 30
STATES = ("NOT_STARTED", "ACTIVE", "EXPIRED", "INVALIDATED", "CONSUMED", "EXECUTION_STARTED")
REASONS = ("PREVIEW_LEASE_EXPIRED", "PREVIEW_LEASE_INVALIDATED", "EXECUTION_QUEUE_LEASE_EXPIRED",
           "EXECUTION_QUEUE_LEASE_INVALIDATED", "LEASE_CORRELATION_FAILED", "LEASE_ALREADY_CONSUMED",
           "LEASE_NOT_ACTIVE", "CLOCK_STATE_INVALID")
INVALIDATIONS = ("DOCUMENT_SWITCH", "DOCUMENT_CLOSE", "PANE_DISPOSAL", "SHUTDOWN", "OWNER_MISMATCH",
                 "SELECTION_CHANGED", "DOCUMENT_IDENTITY_CHANGED", "SESSION_IDENTITY_CHANGED", "TARGET_CHANGED",
                 "PARAMETER_CHANGED", "BEFORE_VALUE_CHANGED", "EPOCH_CHANGED", "USER_CANCEL", "ABANDONED",
                 "CONTINUATION_TERMINAL", "REQUEST_FINALIZED")
Binding = namedtuple("Binding", "logical_request_id host_request_id owner document_id session_id selection_fingerprint "
                     "target_element_id target_unique_id parameter_guid before_has_value before_value proposed_value model_epoch write_epoch")
Lease = namedtuple("Lease", "kind state binding created_at expires_at created_utc checked_at checked_utc "
                   "queue_raised_at handler_started_at consumed reason invalidation")
Outcome = namedtuple("Outcome", "accepted reason preview queue")


def binding(identity, owner, selection_fingerprint, target_element_id, target_unique_id,
            before_has_value, before_value, model_epoch, write_epoch, parameter_guid=c.M4A_TEST_PARAMETER_GUID):
    machine.new_request(identity, 0)
    if (type(owner) is not Owner or owner.state != "ACQUIRED" or owner.owner_type != "CONTROLLED_WRITE_PROVIDER_TOOL" or
            (owner.logical_request_id, owner.host_request_id, owner.document_id, owner.session_id) !=
            (identity.logical_request_id, identity.host_request_id, identity.document_id, identity.session_id) or
            not machine._identifier(owner.token) or not machine._identifier(selection_fingerprint) or
            not machine._identifier(target_unique_id) or type(target_element_id) not in projection.integer_types or
            not 0 < target_element_id < 2 ** 63 or parameter_guid != c.M4A_TEST_PARAMETER_GUID or
            type(before_has_value) is not bool or
            any(type(v) not in projection.integer_types or v < 0 for v in (model_epoch, write_epoch)) or
            not c.validate_value(identity.value)["valid"]):
        raise ValueError("LEASE_CORRELATION_FAILED")
    projection._text(before_value)
    return Binding(identity.logical_request_id, identity.host_request_id, owner, identity.document_id,
                   identity.session_id, selection_fingerprint, target_element_id, target_unique_id,
                   parameter_guid, before_has_value, before_value, identity.value, model_epoch, write_epoch)


def _empty(kind):
    return Lease(kind, "NOT_STARTED", None, None, None, None, None, None, None, None, False, "LEASE_NOT_ACTIVE", None)


class Leases(object):
    """Single-use pair on the logical-owner thread, using a host-owned clock.

    Future host adapter calls create_preview at deterministic preview completion,
    confirm immediately after native Confirm, handler_started at matching handler
    admission. No caller-supplied timestamp. These methods never execute API work.
    """
    def __init__(self, clock):
        if not isinstance(clock, Clock):
            raise ValueError("CLOCK_STATE_INVALID")
        self.clock = clock
        self.preview, self.queue = _empty("PREVIEW"), _empty("EXECUTION_QUEUE")
        self.closed = False

    def _out(self, accepted, reason):
        return Outcome(accepted, reason, self.preview, self.queue)

    def _stamp(self):
        try:
            return self.clock.sample()
        except ValueError:
            self.invalidate("ABANDONED")
            raise ValueError("CLOCK_STATE_INVALID")

    def create_preview(self, context):
        if self.closed or self.preview.state != "NOT_STARTED":
            return self._out(False, "LEASE_ALREADY_CONSUMED")
        if type(context) is not Binding:
            return self._out(False, "LEASE_CORRELATION_FAILED")
        try:
            identity = machine.correlation(context.logical_request_id, context.host_request_id,
                             context.session_id, context.document_id, value=context.proposed_value)
            checked = binding(identity, context.owner, context.selection_fingerprint, context.target_element_id,
                              context.target_unique_id, context.before_has_value, context.before_value,
                              context.model_epoch, context.write_epoch, context.parameter_guid)
            if checked != context:
                raise ValueError()
            stamp = self._stamp()
            expires = deadline(stamp.monotonic, PREVIEW_SECONDS)
        except ValueError as exc:
            return self._out(False, "CLOCK_STATE_INVALID" if str(exc) == "CLOCK_STATE_INVALID" else "LEASE_CORRELATION_FAILED")
        self.preview = Lease("PREVIEW", "ACTIVE", context, stamp.monotonic, expires, stamp.utc,
                             stamp.monotonic, stamp.utc, None, None, False, "COMPLETE", None)
        return self._out(True, "COMPLETE")

    def _check(self, kind, context, stamp):
        name = "preview" if kind == "PREVIEW" else "queue"
        lease = getattr(self, name)
        if lease.state == "NOT_STARTED":
            return "LEASE_NOT_ACTIVE"
        if lease.binding != context:
            self.invalidate("OWNER_MISMATCH" if lease.binding is None or type(context) is not Binding or
                            lease.binding.owner != context.owner else self._changed(lease.binding, context))
            return "LEASE_CORRELATION_FAILED"
        if lease.consumed:
            return "LEASE_ALREADY_CONSUMED"
        if lease.state != "ACTIVE":
            return lease.reason if lease.state in ("EXPIRED", "INVALIDATED") else "LEASE_NOT_ACTIVE"
        expired = stamp.monotonic >= lease.expires_at
        lease = lease._replace(checked_at=stamp.monotonic, checked_utc=stamp.utc,
                              state="EXPIRED" if expired else "ACTIVE",
                              reason=kind + "_LEASE_EXPIRED" if expired else "COMPLETE")
        setattr(self, name, lease)
        return lease.reason

    @staticmethod
    def _changed(before, after):
        fields = (("document_id", "DOCUMENT_IDENTITY_CHANGED"), ("session_id", "SESSION_IDENTITY_CHANGED"),
                  ("selection_fingerprint", "SELECTION_CHANGED"), ("target_element_id", "TARGET_CHANGED"),
                  ("target_unique_id", "TARGET_CHANGED"), ("parameter_guid", "PARAMETER_CHANGED"),
                  ("before_has_value", "BEFORE_VALUE_CHANGED"), ("before_value", "BEFORE_VALUE_CHANGED"),
                  ("model_epoch", "EPOCH_CHANGED"), ("write_epoch", "EPOCH_CHANGED"))
        return next((reason for key, reason in fields if getattr(before, key) != getattr(after, key)), "ABANDONED")

    def check(self, kind, context):
        if kind not in ("PREVIEW", "EXECUTION_QUEUE"):
            return self._out(False, "LEASE_NOT_ACTIVE")
        try:
            stamp = self._stamp()
        except ValueError:
            return self._out(False, "CLOCK_STATE_INVALID")
        reason = self._check(kind, context, stamp)
        return self._out(reason == "COMPLETE", reason)

    def confirm(self, context, human_confirmed=False):
        if human_confirmed is not True:
            return self.invalidate("USER_CANCEL")
        try:
            stamp = self._stamp()
            expires = deadline(stamp.monotonic, EXECUTION_QUEUE_SECONDS)
        except ValueError:
            return self._out(False, "CLOCK_STATE_INVALID")
        reason = self._check("PREVIEW", context, stamp)
        if reason != "COMPLETE":
            return self._out(False, reason)
        self.preview = self.preview._replace(state="CONSUMED", consumed=True)
        self.queue = Lease("EXECUTION_QUEUE", "ACTIVE", context, stamp.monotonic, expires, stamp.utc,
                           stamp.monotonic, stamp.utc, None, None, False, "COMPLETE", None)
        return self._out(True, "COMPLETE")

    def queue_raised(self, context):
        outcome = self.check("EXECUTION_QUEUE", context)
        if outcome.accepted and self.queue.queue_raised_at is None:
            self.queue = self.queue._replace(queue_raised_at=self.queue.checked_at)
            return self._out(True, "COMPLETE")
        return self._out(False, outcome.reason if not outcome.accepted else "LEASE_ALREADY_CONSUMED")

    def handler_started(self, context):
        outcome = self.check("EXECUTION_QUEUE", context)
        if not outcome.accepted:
            return outcome
        self.queue = self.queue._replace(state="EXECUTION_STARTED", consumed=True, handler_started_at=self.queue.checked_at)
        return self._out(True, "COMPLETE")

    def invalidate(self, trigger):
        if trigger not in INVALIDATIONS:
            raise ValueError("INVALID_CLEANUP_REASON")
        for name in ("preview", "queue"):
            lease = getattr(self, name)
            if lease.state in ("NOT_STARTED", "ACTIVE"):
                setattr(self, name, lease._replace(state="INVALIDATED", reason=lease.kind + "_LEASE_INVALIDATED", invalidation=trigger))
        self.closed = True
        return self._out(False, "EXECUTION_QUEUE_LEASE_INVALIDATED" if self.queue.binding else "PREVIEW_LEASE_INVALIDATED")

    def provenance(self):
        def scalar(lease):
            data = lease._asdict()
            if lease.binding is not None:
                data["binding"] = lease.binding._asdict()
                data["binding"]["owner"] = lease.binding.owner._asdict()
            return data
        return json.dumps(dict(preview=scalar(self.preview), queue=scalar(self.queue)),
                          sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"))


def expired_request(request, leases):
    """Pure nonexecution receipt + existing 22-state expiry path. Never dispatch."""
    kind = "EXECUTION_QUEUE" if request.state == "WRITE_REQUEST_QUEUED" else "PREVIEW"
    lease = leases.queue if kind == "EXECUTION_QUEUE" else leases.preview
    if leases.closed or request.state not in ("PREVIEW_READY", "AWAITING_HUMAN_CONFIRMATION", "WRITE_REQUEST_QUEUED") or lease.state != "EXPIRED":
        raise ValueError("LEASE_NOT_ACTIVE")
    b, identity = lease.binding, request.correlation
    if (b.logical_request_id, b.host_request_id, b.document_id, b.session_id, b.proposed_value, b.owner.owner_type) != (
            identity.logical_request_id, identity.host_request_id, identity.document_id, identity.session_id, identity.value, request.owner):
        raise ValueError("LEASE_CORRELATION_FAILED")
    data = dict(feature_id=c.M4A_FEATURE_ID, action_id=c.M4A_ACTION_ID, request_id=b.host_request_id,
                classification="MEP_PARAMETER_WRITE_NOT_READY", reason_code=lease.reason, target_category=c.M4A_CATEGORY,
                target_element_id=b.target_element_id, target_unique_id=b.target_unique_id,
                parameter_display_name=c.M4A_TEST_PARAMETER_NAME, parameter_guid=b.parameter_guid,
                before_has_value=b.before_has_value, before_value=b.before_value, proposed_value=b.proposed_value,
                final_value=None, confirmation_result="CONFIRMED" if kind == "EXECUTION_QUEUE" else "NOT_CONFIRMED",
                transaction_started=False, transaction_committed=False, transaction_status="NOT_STARTED", model_modified=False,
                verification_performed=False, verification_passed=False, warnings=[], timestamp=lease.checked_utc)
    receipt = projection.freeze_result(data)
    first = machine.transition(request, identity, "APPROVAL_EXPIRED", lease.checked_at, lease.reason)
    if not first.accepted:
        raise ValueError(first.reason)
    final = machine.transition(first.request, identity, "HOST_RESULT_READY", lease.checked_at, lease.reason, host_result=receipt)
    if not final.accepted:
        raise ValueError(final.reason)
    leases.invalidate("ABANDONED")
    return final.request
