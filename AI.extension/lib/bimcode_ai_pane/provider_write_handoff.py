"""003A internal admission only. Production response routing is NOT connected.

The trusted response adapter opens a ticket against the actual retained host
turn BEFORE receiving a response. Dictionaries alone cannot create provenance.
All methods belong to the persistent session engine/UI owner thread. No worker.
"""
from collections import namedtuple
from uuid import uuid4
from threading import Lock
from copy import deepcopy
from bimcode_ai_pane import provider_write as machine
from bimcode_ai_pane import write_projection as projection
from bimcode_ai_pane import write_continuation as continuation
from bimcode_ai_pane.controlled_write_registry import validate_arguments
from bimcode_ai_pane.provider_bridge import valid_identifier
from bimcode_ai_pane.write_access import owner_document_key
from bimcode_ai_pane.write_clock import deadline

HOLD_SECONDS = 120
LEDGER_LIMIT = 1000
Binding = namedtuple('Binding', 'transport_id turn_generation identity epochs model permission_generation origin')
Ticket = namedtuple('Ticket', 'transport_id active turn generation document model permission_generation')


class Handoff(object):
    def __init__(self, session):
        self.session = session
        self.ticket = None
        self.binding = None
        self.seen = set()
        self._binding_lock = Lock()
        self.pending = None
        self.last = None
        self.failure = None

    def _epochs(self):
        s = self.session
        return (s.context_generation, s.selection_generation, s.m4a_write.epoch,
                s.write_gate.cleanup_generation)

    def open_transport(self, active, model):
        """Trusted internal adapter only; never called by production in 003A."""
        self.check()
        s = self.session
        turn = s.ai.turn
        if (self.pending is not None or self.ticket is not None or self.binding is not None or
                active is not s.panel._provider_state.active or type(active) is not dict or
                active.get('operation') != 'agent_turn' or turn is None or turn.get('used') or
                active.get('request_id') != turn.get('request_id') or
                not valid_identifier(active.get('request_id')) or
                turn.get('key') != s.document_identity or turn.get('generation') != s.context_generation or
                turn.get('selection') != s.selection_generation or not continuation._model(model) or
                getattr(s, 'disposed', False) or s.write_gate.closed or
                not s.write_gate.permission.view_model()['enabled']):
            raise ValueError('PROVIDER_ORIGIN_NOT_READY')
        self.ticket = Ticket(active['request_id'], active, turn, self._epochs(), owner_document_key(s),
                             model, s.write_gate.permission.generation)
        return self.ticket

    def bind_response(self, ticket, response):
        # No nested coordinator/sink locks. Nonblocking also rejects reentry.
        if not self._binding_lock.acquire(False):
            raise ValueError('PROVIDER_BINDING_BUSY')
        try:
            return self._bind_response(ticket, response)
        finally:
            self._binding_lock.release()

    def _bind_response(self, ticket, response):
        """Validate recorded-shape response against the retained transport ticket.

        This is a trusted callback seam, not a public string/dict provenance API.
        It must not be wired until provider write exposure is separately approved.
        """
        s = self.session
        if type(ticket) is not Ticket or ticket is not self.ticket:
            raise ValueError('PROVIDER_ORIGIN_REQUIRED')
        self.ticket = None  # Consume failed attempts too.
        active = s.panel._provider_state.active
        if (s.ai.turn is not ticket.turn or ticket.turn.get('used') or
                ticket.generation != self._epochs() or ticket.document != owner_document_key(s) or
                ticket.permission_generation != s.write_gate.permission.generation or
                getattr(s, 'disposed', False) or s.write_gate.closed or
                not s.write_gate.permission.view_model()['enabled'] or active is not ticket.active or
                active.get('request_id') != ticket.transport_id or active.get('operation') != 'agent_turn'):
            raise ValueError('STALE_PROVIDER_TURN')
        fields = set(('protocol_version','request_id','ok','provider','model','text','error',
                      'state','tool_call','provider_state'))
        if (type(response) is not dict or set(response) != fields or
                type(response['protocol_version']) is not int or response['protocol_version'] != 1 or
                response['request_id'] != ticket.transport_id or response['ok'] is not True or
                response['provider'] != 'openai' or response['state'] != 'TOOL_REQUEST' or
                response['text'] is not None or response['error'] is not None or response['model'] != ticket.model):
            raise ValueError('INVALID_PROVIDER_EVIDENCE')
        call, state = response['tool_call'], response['provider_state']
        if (type(call) is not dict or set(call) != set(('name','call_id','arguments')) or
                call['name'] != 'set_selected_pipe_test_text' or not valid_identifier(call['call_id']) or
                type(state) is not dict or set(state) != set(('response_id','model')) or
                not valid_identifier(state['response_id']) or state['model'] != ticket.model or
                call['call_id'].startswith('host-test-') or state['response_id'].startswith('host-test-')):
            raise ValueError('INVALID_PROVIDER_EVIDENCE')
        value = validate_arguments(call['arguments'])
        if not value['valid']:
            raise ValueError(value['reason_code'])
        key = (state['response_id'], call['call_id'])
        if len(self.seen) >= LEDGER_LIMIT or any(r == key[0] or c == key[1] for r, c in self.seen):
            raise ValueError('PROVIDER_REPLAY_OR_CAPACITY')
        identity = machine.correlation(uuid4().hex, uuid4().hex, str(id(s)), ticket.document,
                                       key[0], key[1], value['value'])
        binding = Binding(ticket.transport_id, ticket.generation[0], identity,
                               ticket.generation, ticket.model, ticket.permission_generation, 'VALIDATED_PROVIDER')
        # All prerequisite validation/construction precedes the one reservation.
        self.seen.add(key)
        ticket.turn['used'] = True
        self.binding = binding
        return self.binding

    def admit(self, dispatcher):
        """Called after receipt storage and HOST_RESULT_READY, before cleanup."""
        if self.binding is None:
            return False  # Human host-test requests are deliberately ineligible.
        d, b, s = dispatcher, self.binding, self.session
        if s.controlled_writes.dispatcher is not d:
            return False  # Late old completion cannot consume a newer binding.
        try:
            self.check()
            if (self.pending is not None or s.controlled_writes.dispatcher is not d or
                    d.session is not s or d.identity != b.identity or d.request.correlation != b.identity or
                    b.identity.session_id != str(id(s)) or b.identity.document_id != owner_document_key(s) or
                    b.permission_generation != s.write_gate.permission.generation or b.origin != 'VALIDATED_PROVIDER' or
                    b.epochs != d.epochs or b.permission_generation != d.permission_generation or
                    b.epochs[:2] != self._epochs()[:2] or b.epochs[3] != self._epochs()[3] or
                    s.write_gate.closed or getattr(s, 'disposed', False) or
                    not s.write_gate.permission.view_model()['enabled'] or
                    d.request.state != 'HOST_RESULT_READY' or d.sink is None or
                    d.sink.receipt is None or d.sink.receipt.receipt != d.request.host_result):
                raise ValueError('HANDOFF_CORRELATION_MISMATCH')
            host = projection.project_receipt(d.request.host_result)
            if host['classification'].startswith('MEP_PARAMETER_WRITE_PREVIEW_'):
                raise ValueError('HOST_RESULT_NOT_TERMINAL')
            if host['proposed_value'] != b.identity.value:
                raise ValueError('HANDOFF_CORRELATION_MISMATCH')
            if not d.sink.deliver(b.identity.logical_request_id):
                raise ValueError('COMPLETION_ALREADY_DELIVERED')
            coord = continuation.Coordinator()
            now = d.clock.sample().monotonic
            snap = coord.begin(d.request, d.sink, d.admission, b.model, now)
            d.request = coord.request
            s.write_gate.request = d.request
            # Retain BEFORE resource finalization; no worker is scheduled.
            self.pending = (d, coord, snap, deadline(now, HOLD_SECONDS))
            d.lifecycle.finalize_admitted(d.request, coord)
            s.write_gate.lifecycle, s.write_gate.request = None, None
            self.binding = None
            self.failure = None
            return True
        except Exception:
            self.failure = 'CONTINUATION_ADMISSION_FAILED'
            self.binding = None
            if self.pending is not None:
                d.admission.retain_safety(True, self, d.owner, 'ADMISSION_FINALIZATION_FAILED')
                self.invalidate('ADMISSION_FINALIZATION_FAILED')
            return False

    def invalidate(self, reason):
        self.ticket = None
        self.binding = None
        if self.pending is None:
            return
        d, coord, snap, expires = self.pending
        # Clock failure cannot erase evidence or extend the hold.
        try:
            stamp = d.clock.sample().monotonic
        except ValueError:
            stamp = d.request.timestamp
        target = d.request.terminal_intent or 'COMPLETED'
        status = projection.explanation('UNAVAILABLE', error_classification=reason)
        step = machine.transition(d.request, d.identity, target, stamp, reason, provider_status=status)
        if not step.accepted:
            d.admission.retain_safety(True, self, d.owner, 'CONTINUATION_TRANSITION_FAILED')
            raise ValueError(step.reason)
        coord.close('document_close' if reason in ('DOCUMENT_CLOSE','DOCUMENT_SWITCH') else 'cancelled')
        coord.request = d.request = step.request
        self.last = dict(state=d.request.state, reason=reason, host_result=snap.host_result.json,
                         provider_status=status._asdict())
        self.pending = None

    def check(self):
        if self.pending is not None:
            d, coord, snap, expires = self.pending
            s = self.session
            if (getattr(s, 'disposed', False) or s.write_gate.closed or
                    owner_document_key(s) != d.identity.document_id or
                    s.write_gate.permission.generation != d.permission_generation or
                    not s.write_gate.permission.view_model()['enabled']):
                self.invalidate('CONTINUATION_CONTEXT_INVALIDATED')
                return
            try:
                expired = d.clock.sample().monotonic >= expires
            except ValueError:
                self.invalidate('CONTINUATION_CLOCK_INVALID')
                return
            if expired:
                self.invalidate('CONTINUATION_HOLD_EXPIRED')

    def inspect(self):
        # Pure retained snapshot. Expiry belongs to operational check() calls.
        if self.pending is None:
            return dict(pending=False, last=deepcopy(self.last), failure=self.failure)
        d, coord, snap, expires = self.pending
        return dict(pending=True, state=d.request.state, expires_at=expires,
                    correlation=d.identity._asdict(), host_result=snap.host_result.json,
                    provider_network_enabled=False)
