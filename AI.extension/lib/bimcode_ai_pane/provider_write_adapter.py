"""003B-1 internal injected-transport adapter; production routing is unchanged.

Constructed in SessionWrites' persistent engine. Readiness and response methods
are trusted host callbacks, not public dictionary-based authorization endpoints.
No default transport, dispatch, confirmation, ownership transfer or continuation.
"""
import json
from collections import namedtuple
from threading import Lock
from bimcode_ai_pane import provider_bridge
from bimcode_ai_pane.write_continuation import _model
from bimcode_ai_pane.write_access import owner_document_key

Launch = namedtuple('Launch', 'ticket session model_generation turn_fields')
Outcome = namedtuple('Outcome', 'state binding')


class Adapter(object):
    def __init__(self, writes):
        self.writes = writes
        self.expected_model = None
        self.model_generation = 0
        self.outstanding = None
        self._lock = Lock()

    def _session(self):
        s = self.writes.session
        if (s.controlled_writes is not self.writes or
                self.writes.handoff.session is not s):
            raise ValueError('ADAPTER_SESSION_MISMATCH')
        return s

    def _invalidate(self):
        launch = self.outstanding
        self.outstanding = None
        if launch is not None and self.writes.handoff.ticket is launch.ticket:
            self.writes.handoff.ticket = None

    def _document_permission(self, session):
        gate = session.write_gate
        permission = gate.permission.view_model()
        if (session.document_identity is None or not permission['enabled'] or
                gate.document != permission['document_key'] or
                gate.document != owner_document_key(session)):
            raise ValueError('ADAPTER_DOCUMENT_PERMISSION_MISMATCH')

    def remember_readiness(self, active, response):
        """Before SendState.finish: retain only matched local readiness metadata.

        No credentials/configuration files are read. Re-observation invalidates
        an outstanding launch, even if the model changed away and back.
        """
        if not self._lock.acquire(False):
            raise ValueError('ADAPTER_BUSY')
        try:
            s = self._session()
            if (active is not s.panel._provider_state.active or type(active) is not dict or
                    active.get('operation') != 'readiness' or
                    not provider_bridge.valid_identifier(active.get('request_id'))):
                raise ValueError('READINESS_ORIGIN_REQUIRED')
            self._invalidate()
            self.expected_model = None
            self.model_generation += 1
            if (type(response) is not dict or set(response) != set((
                    'protocol_version', 'request_id', 'ok', 'provider', 'model', 'text', 'error'))):
                raise ValueError('EXPECTED_MODEL_UNAVAILABLE')
            parsed = provider_bridge.decode(json.dumps(response, allow_nan=False), active['request_id'], 0)
            if (not parsed['ok'] or parsed.get('text') != 'READY' or
                    parsed.get('state') is not None or not _model(parsed.get('model'))):
                raise ValueError('EXPECTED_MODEL_UNAVAILABLE')
            self.expected_model = parsed['model']
        finally:
            self._lock.release()

    def open(self, active):
        """Open before injected transport launch; never derive model from reply."""
        if not self._lock.acquire(False):
            raise ValueError('ADAPTER_BUSY')
        try:
            s = self._session()
            if self.outstanding is not None:
                raise ValueError('TRANSPORT_ALREADY_OUTSTANDING')
            if not _model(self.expected_model):
                raise ValueError('EXPECTED_MODEL_UNAVAILABLE')
            self._document_permission(s)
            ticket = self.writes.handoff.open_transport(active, self.expected_model)
            turn = ticket.turn
            self.outstanding = Launch(ticket, s, self.model_generation,
                (turn.get('request_id'), turn.get('key'), turn.get('generation'), turn.get('selection')))
            return self.outstanding
        finally:
            self._lock.release()

    def complete(self, launch, response):
        """Owner-thread callback, ending exclusively at binding-ready."""
        if not self._lock.acquire(False):
            raise ValueError('ADAPTER_BUSY')
        try:
            if type(launch) is not Launch or launch is not self.outstanding:
                raise ValueError('LAUNCH_ORIGIN_REQUIRED')
            self.outstanding = None  # Every matched attempt is single use.
            try:
                s = self._session()
                self._document_permission(s)
                ticket = launch.ticket
                turn = ticket.turn
                if (launch.session is not s or launch.model_generation != self.model_generation or
                        ticket.model != self.expected_model or
                        launch.turn_fields != (turn.get('request_id'), turn.get('key'),
                                               turn.get('generation'), turn.get('selection'))):
                    raise ValueError('STALE_LAUNCH_METADATA')
                if type(response) is not dict:
                    raise ValueError('INVALID_PROVIDER_EVIDENCE')
                binding = self.writes.handoff.bind_response(ticket, response)
                return Outcome('TRUSTED_PROVIDER_BINDING_READY', binding)
            finally:
                if self.writes.handoff.ticket is launch.ticket:
                    self.writes.handoff.ticket = None
        finally:
            self._lock.release()

    def launch(self, active, transport, complete):
        """Explicit internal injection only; callbacks must use owner thread.

        The transport receives a scalar copy, never the authoritative ticket.
        Production does not import/call this entry point.
        """
        if not callable(transport) or not callable(complete):
            raise ValueError('INJECTED_TRANSPORT_REQUIRED')
        launch = self.open(active)
        try:
            transport(dict(active), lambda response: complete(self.complete(launch, response)))
        except Exception:
            if self.outstanding is launch:
                self._invalidate()
            raise
        return launch
