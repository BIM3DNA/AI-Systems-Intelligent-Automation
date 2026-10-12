"""003B-2A persistent-session reservation/transfer only, no Revit execution.

All entry points run on the session owner thread. Admission's nonblocking lock
also excludes concurrent/reentrant acquire/release/transfer operations. No
provider route calls these methods. Returns scalar status, not authority objects.
"""
from collections import namedtuple
from uuid import uuid4
from bimcode_ai_pane.write_access import Owner, owner_document_key, document_eligibility
from bimcode_ai_pane.controlled_write_registry import validate_arguments
from bimcode_ai_pane.write_clock import Clock

Reservation = namedtuple('Reservation', 'evidence owner')


class Transfer(object):
    def __init__(self, writes):
        self.writes = writes
        self.reservation = None
        self.transferred = None
        self.adopted = False
        self._invalidated = False
        self._candidate = None

    def _manager(self):
        return self.writes.session.write_gate.admission

    @property
    def invalidated(self):
        with self._manager()._state_lock:
            return self._invalidated

    @invalidated.setter
    def invalidated(self, value):
        with self._manager()._state_lock:
            self._invalidated = value

    def _validate(self, evidence, new_request=False):
        try:
            return self._check(evidence, new_request)
        except (ValueError, AttributeError, TypeError):
            if self.reservation is not None and not new_request:
                self.invalidated = True  # A stale reservation never revives.
            raise ValueError('TRANSFER_CONTEXT_INVALID')

    def _check(self, evidence, new_request=False):
        s, w = self.writes.session, self.writes
        if ((self.invalidated and not new_request) or s.controlled_writes is not w or w.transfer is not self or
                evidence is None or evidence is not w.adapter.accepted):
            raise ValueError('TRANSFER_ORIGIN_REQUIRED')
        launch, binding = evidence
        ticket = launch.ticket
        gate = s.write_gate
        turn = s.ai.turn
        if (binding is not w.handoff.binding or binding.origin != 'VALIDATED_PROVIDER' or
                launch.session is not s or w.handoff.session is not s or
                ticket.active is not s.panel._provider_state.active or
                ticket.active.get('request_id') != ticket.transport_id or
                ticket.active.get('operation') != 'agent_turn' or turn is not ticket.turn or
                type(turn) is not dict or turn.get('used') is not True or
                launch.turn_fields != (turn.get('request_id'), turn.get('key'),
                                       turn.get('generation'), turn.get('selection')) or
                ticket.generation != w.handoff._epochs() or binding.epochs != ticket.generation or
                launch.model_generation != w.adapter.model_generation or
                ticket.model != w.adapter.expected_model or binding.model != ticket.model or
                ticket.document != owner_document_key(s) or
                binding.identity.document_id != ticket.document or binding.identity.session_id != str(id(s)) or
                binding.permission_generation != gate.permission.generation or
                ticket.permission_generation != gate.permission.generation or
                getattr(s, 'disposed', False) or gate.closed or
                not gate.permission.view_model()['enabled'] or
                gate.document != ticket.document or gate.permission.view_model()['document_key'] != ticket.document or
                not document_eligibility(gate.facts)['eligible'] or
                binding.identity.tool_name != 'set_selected_pipe_test_text' or
                not validate_arguments(dict(value=binding.identity.value))['valid'] or
                w.handoff.pending is not None or self._manager().safety_locked or
                gate.lifecycle is not None):
            raise ValueError('TRANSFER_CONTEXT_INVALID')
        return binding

    def owns_turn(self, reservation, turn):
        if reservation is not self.reservation or type(reservation) is not Reservation:
            return False
        try:
            self._validate(reservation.evidence)
            return turn is reservation.evidence[0].ticket.turn
        except (ValueError, AttributeError, TypeError):
            return False

    def reserve(self):
        manager = self._manager()
        if not manager._lock.acquire(False):
            raise ValueError('ADMISSION_BUSY')
        try:
            evidence = self.writes.adapter.accepted
            fresh = (self.reservation is not None and self.invalidated and
                     evidence is not self.reservation.evidence)
            if (self.reservation is not None and not fresh) or manager.active is not None:
                raise ValueError('RESERVATION_ALREADY_OWNED')
            binding = self._validate(evidence, new_request=fresh)
            i = binding.identity
            owner = Owner(uuid4().hex, 'PROVIDER_TURN', i.logical_request_id, i.host_request_id,
                          i.document_id, i.session_id, Clock().sample().monotonic, None, 'ACQUIRED', None)
            reservation = Reservation(evidence, owner)
            prior = (self.reservation, self.transferred, self.adopted, self.invalidated)
            self.reservation = reservation
            self.transferred, self.adopted, self.invalidated = None, False, False
            try:
                if manager.busy is None or manager.busy(reservation):
                    raise ValueError('ADMISSION_BUSY')
                self._validate(evidence)
            except Exception:
                self.reservation, self.transferred, self.adopted, self.invalidated = prior
                raise
            with manager._state_lock:
                if self.invalidated or not manager.publish_owner(None, owner):
                    raise ValueError('TRANSFER_CONTEXT_INVALID')
            return dict(state='PROVIDER_TURN_RESERVED')
        finally:
            manager._lock.release()

    def transfer(self):
        manager = self._manager()
        if not manager._lock.acquire(False):
            raise ValueError('ADMISSION_BUSY')
        try:
            r = self.reservation
            if r is None or self.transferred is not None or manager.active is not r.owner:
                raise ValueError('TRANSFER_OWNER_MISMATCH')
            self._validate(r.evidence)
            if manager.busy is None or manager.busy(r):
                raise ValueError('ADMISSION_BUSY')
            replacement = r.owner._replace(token=uuid4().hex, owner_type='CONTROLLED_WRITE_PROVIDER_TOOL')
            # Recheck after construction; no external calls in publication below.
            self._validate(r.evidence)
            if manager.active is not r.owner:
                raise ValueError('TRANSFER_OWNER_MISMATCH')
            with manager._state_lock:
                if self.invalidated or not manager.publish_owner(r.owner, replacement):
                    raise ValueError('TRANSFER_CONTEXT_INVALID')
                self.transferred = replacement  # Consumes reservation once.
            # 003A already marked this exact turn used. Do not clear ai.turn.
            return dict(state='CONTROLLED_WRITE_OWNER_TRANSFERRED')
        finally:
            manager._lock.release()

    def adopt(self):
        """Construct dispatcher in this engine; expose scalar outcome only."""
        from bimcode_ai_pane.provider_write_dispatch import Dispatcher
        if self.reservation is None:
            raise ValueError('TRANSFER_REQUIRED')
        d = Dispatcher(self.writes.session, self.reservation.evidence[1].identity)
        if self._candidate is not None:
            raise ValueError('ADOPTION_BUSY')
        self._candidate = d
        try:
            return d.adopt_transferred()
        finally:
            self._candidate = None

    def _adopt(self, dispatcher):
        manager = self._manager()
        if not manager._lock.acquire(False):
            raise ValueError('ADMISSION_BUSY')
        try:
            from bimcode_ai_pane.provider_write_dispatch import Dispatcher
            r = self.reservation
            if (r is None or self.transferred is None or self.adopted or
                    manager.active is not self.transferred or type(dispatcher) is not Dispatcher or
                    dispatcher is not self._candidate or
                    dispatcher.session is not self.writes.session or dispatcher.used or
                    dispatcher.owner is not None or dispatcher.request is not None or
                    dispatcher.identity is not r.evidence[1].identity):
                raise ValueError('TRANSFER_ADOPTION_REJECTED')
            binding = self._validate(r.evidence)
            if manager.busy is None or manager.busy(r):
                raise ValueError('ADMISSION_BUSY')
            with manager._state_lock:
                if (self.invalidated or manager.safety_locked or
                        manager._pending_cleanup is not None or manager.active is not self.transferred):
                    raise ValueError('TRANSFER_ADOPTION_REJECTED')
                dispatcher.owner = self.transferred
                dispatcher.epochs = binding.epochs
                dispatcher.permission_generation = binding.permission_generation
                dispatcher.used = True  # No preview/dispatch entry is enabled in 2A.
                self.writes.dispatcher = dispatcher
                self.adopted = True
            return dict(state='TRANSFERRED_OWNER_ADOPTED')
        finally:
            manager._lock.release()

    def invalidate(self, reason):
        # Reentrant cleanup must invalidate first, so transfer's final check fails.
        manager = self._manager()
        with manager._state_lock:
            if self.reservation is None:
                return False
            self.invalidated = True
            r = self.reservation
            owner = self.transferred or (r.owner if r is not None else None)
        # Release state lock BEFORE attempting operation lock. Future executing
        # lifecycles own their cleanup; this sealed 2A owner cannot execute.
        if self.writes.session.write_gate.lifecycle is not None:
            return False
        return manager.cleanup(owner, reason)
