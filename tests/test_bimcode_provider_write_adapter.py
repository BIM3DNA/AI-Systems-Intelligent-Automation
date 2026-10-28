"""Offline recorded-shape adapter evidence, never authenticated provider proof."""
import ast
import copy
import json
import pathlib
import subprocess
import unittest
from unittest.mock import patch
import test_bimcode_provider_write_handoff as fixtures
from bimcode_ai_pane import provider_bridge
from bimcode_ai_pane import provider_write_adapter as adapter

ROOT = pathlib.Path(__file__).resolve().parents[1]


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.HandoffTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.s, self.h = self.f.s, self.f.h
        self.a = self.s.controlled_writes.adapter
        self.h.ticket = None
        self.active = self.f.active
        self.response = copy.deepcopy(self.f.response)
        self.readiness()

    def readiness(self, model='fixture-model'):
        active = dict(request_id='readiness', operation='readiness')
        self.s.panel._provider_state.active = active
        self.a.remember_readiness(active, dict(protocol_version=1, request_id='readiness',
            ok=True, provider='openai', model=model, text='READY', error=None))
        self.s.panel._provider_state.active = self.active

    def bind(self):
        return self.a.complete(self.a.open(self.active), self.response)

    def rejected(self, change):
        launch = self.a.open(self.active)
        change()
        with self.assertRaises((ValueError, TypeError)):
            self.a.complete(launch, self.response)
        self.assertIsNone(self.h.binding)
        self.assertEqual(self.h.seen, set())
        self.assertIsNone(self.h.ticket)

    def test_injected_transport(self):
        results = []
        def transport(payload, callback):
            self.assertIsNotNone(self.a.outstanding)
            self.assertIsNot(payload, self.active)
            self.assertEqual(payload['request_id'], 'transport')
            callback(self.response)
        self.a.launch(self.active, transport, results.append)
        self.assertEqual(results[0].state, 'TRUSTED_PROVIDER_BINDING_READY')
        self.assertIs(results[0].binding, self.h.binding)
        self.assertEqual(results[0].binding.model, 'fixture-model')

    def test_missing_expected_model(self):
        self.a.expected_model = None
        with self.assertRaises(ValueError): self.a.open(self.active)

    def test_invalid_expected_model(self):
        with self.assertRaises(ValueError): self.readiness('bad model')
        self.assertIsNone(self.a.expected_model)

    def test_unmatched_readiness(self):
        with self.assertRaises(ValueError): self.a.remember_readiness({}, {})

    def test_readiness_failure(self):
        active = dict(request_id='ready', operation='readiness')
        self.s.panel._provider_state.active = active
        with self.assertRaises(ValueError):
            self.a.remember_readiness(active, provider_bridge.failure('ready', 'CONFIG_MISSING_MODEL'))
        self.assertIsNone(self.a.expected_model)

    def test_forged_ticket(self):
        launch = self.a.open(self.active)
        for forged in (launch._asdict(), adapter.Launch(*launch), None):
            with self.assertRaises(ValueError): self.a.complete(forged, self.response)
        self.assertIs(self.a.outstanding, launch)
        self.assertEqual(self.a.complete(launch, self.response).state, 'TRUSTED_PROVIDER_BINDING_READY')

    def test_arbitrary_dictionary(self):
        with self.assertRaises(ValueError): self.a.complete({}, self.response)
        self.assertIsNone(self.h.binding)

    def test_missing_transport(self):
        self.rejected(lambda: setattr(self.s.panel._provider_state, 'active', None))

    def test_wrong_request(self):
        self.rejected(lambda: self.response.update(request_id='wrong'))

    def test_wrong_session(self):
        self.rejected(lambda: setattr(self.s, 'controlled_writes', object()))

    def test_foreign_session_ticket(self):
        other = adapter.Adapter(self.s.controlled_writes)
        launch = self.a.open(self.active)
        with self.assertRaises(ValueError): other.complete(launch, self.response)
        self.assertIsNone(self.h.binding)

    def test_wrong_document(self):
        self.rejected(lambda: setattr(self.s, 'document_identity', ('other',)))

    def test_permission_document_mismatch(self):
        self.rejected(lambda: setattr(self.s.write_gate, 'document', 'other'))

    def test_protocol_version(self):
        self.rejected(lambda: self.response.update(protocol_version=True))

    def test_unsuccessful_response(self):
        self.rejected(lambda: self.response.update(ok=False))

    def test_wrong_provider_state_model(self):
        self.rejected(lambda: self.response['provider_state'].update(model='other'))

    def test_wrong_turn_identity(self):
        self.rejected(lambda: setattr(self.s.ai, 'turn', dict(self.s.ai.turn)))

    def test_changed_turn_generation(self):
        self.rejected(lambda: self.s.ai.turn.update(generation=99))

    def test_changed_turn_key(self):
        self.rejected(lambda: self.s.ai.turn.update(key=('other',)))

    def test_context_generation(self):
        self.rejected(lambda: setattr(self.s, 'context_generation', 99))

    def test_selection_generation(self):
        self.rejected(lambda: setattr(self.s, 'selection_generation', 99))

    def test_permission_generation(self):
        self.rejected(lambda: self.s.write_gate.permission.disable())

    def test_wrong_model(self):
        self.rejected(lambda: self.response.update(model='other'))

    def test_configuration_refresh_invalidates(self):
        launch = self.a.open(self.active)
        self.readiness('other')
        self.readiness('fixture-model')
        with self.assertRaises(ValueError): self.a.complete(launch, self.response)
        self.assertEqual(self.h.seen, set())

    def test_missing_response_id(self):
        self.rejected(lambda: self.response['provider_state'].pop('response_id'))

    def test_missing_call_id(self):
        self.rejected(lambda: self.response['tool_call'].pop('call_id'))

    def test_multiple_calls(self):
        self.rejected(lambda: self.response.update(tool_calls=[self.response['tool_call']] * 2))

    def test_unsupported_output(self):
        self.rejected(lambda: self.response.update(output=[dict(type='computer_call')]))

    def test_unknown_tool(self):
        self.rejected(lambda: self.response['tool_call'].update(name='arbitrary'))

    def test_invalid_arguments(self):
        self.rejected(lambda: self.response['tool_call'].update(arguments=dict(value=' ')))

    def test_injected_target(self):
        self.rejected(lambda: self.response['tool_call']['arguments'].update(element_id=353871))

    def test_injected_parameter(self):
        self.rejected(lambda: self.response['tool_call']['arguments'].update(parameter='Mark'))

    def test_synthetic_provenance(self):
        self.rejected(lambda: self.response['provider_state'].update(response_id='host-test-response-1'))

    def test_duplicate_response(self):
        self.h.seen.add(('response', 'other'))
        with self.assertRaises(ValueError): self.bind()
        self.assertEqual(self.h.seen, {('response', 'other')})

    def test_duplicate_call(self):
        self.h.seen.add(('other', 'call'))
        with self.assertRaises(ValueError): self.bind()
        self.assertEqual(self.h.seen, {('other', 'call')})

    def test_capacity(self):
        self.h.seen = set(('r'+str(i), 'c'+str(i)) for i in range(1000))
        with self.assertRaises(ValueError): self.bind()
        self.assertEqual(len(self.h.seen), 1000)

    def test_replay_after_terminal_completion(self):
        # Actual 003A fixture completes once, then expires its pending hold.
        self.f.ticket = self.h.open_transport(self.active, 'fixture-model')
        self.f.finish()
        self.f.f.now += 120
        self.h.check()
        self.s.ai.turn = dict(request_id='transport', key=self.s.document_identity,
                              generation=0, selection=0, used=False)
        self.response['provider_state']['response_id'] = 'later_response'
        with self.assertRaises(ValueError): self.bind()
        self.assertEqual(self.h.seen, {('response', 'call')})

    def test_lifecycle_invalidation(self):
        for reason in ('DOCUMENT_SWITCH', 'DOCUMENT_CLOSE', 'PANE_DISPOSAL', 'ABANDONED'):
            with self.subTest(reason=reason):
                case = AdapterTests(); case.setUp()
                try:
                    case.rejected(lambda: case.s.write_gate.cleanup(reason))
                finally: case.doCleanups()

    def test_disposed_session(self):
        self.rejected(lambda: setattr(self.s, 'disposed', True))

    def test_duplicate_callback(self):
        launch = self.a.open(self.active)
        self.a.complete(launch, self.response)
        binding = self.h.binding
        with self.assertRaises(ValueError): self.a.complete(launch, self.response)
        self.assertIs(self.h.binding, binding)
        self.assertEqual(len(self.h.seen), 1)

    def test_competing_transport(self):
        launch = self.a.open(self.active)
        with self.assertRaises(ValueError): self.a.open(self.active)
        self.assertIs(self.a.outstanding, launch)

    def test_replaced_transport(self):
        self.rejected(lambda: setattr(self.s.panel._provider_state, 'active', dict(self.active)))

    def test_invalid_consumes_ticket_not_capacity(self):
        launch = self.a.open(self.active)
        with self.assertRaises(ValueError): self.a.complete(launch, {})
        with self.assertRaises(ValueError): self.a.complete(launch, self.response)
        self.assertEqual(self.h.seen, set())
        self.assertEqual(self.bind().state, 'TRUSTED_PROVIDER_BINDING_READY')

    def test_transport_exception(self):
        def failed(payload, callback): raise RuntimeError('offline')
        with self.assertRaises(RuntimeError): self.a.launch(self.active, failed, lambda result: None)
        self.assertIsNone(self.a.outstanding)
        self.assertIsNone(self.h.ticket)
        self.assertEqual(self.h.seen, set())

    def test_no_downstream_execution(self):
        from bimcode_ai_pane.provider_write_dispatch import Dispatcher
        from bimcode_ai_pane.provider_write_host_bridge import Bridge
        from bimcode_ai_pane.write_continuation import Coordinator
        from bimcode_ai_pane.write_access import OperationAdmission
        with patch.object(Dispatcher, 'dispatch', side_effect=AssertionError('dispatch')), \
                patch.object(Bridge, 'request_confirmation', side_effect=AssertionError('confirm')), \
                patch.object(OperationAdmission, 'acquire', side_effect=AssertionError('owner')), \
                patch.object(Coordinator, 'begin', side_effect=AssertionError('continuation')):
            self.bind()
        self.assertIsNone(self.h.pending)
        self.f.f.no_mutation()

    def test_production_unchanged(self):
        paths = ['BIMCode_Provider/provider.py', 'BIMCode_Provider/tool_protocol.py']
        paths += ['AI.extension/lib/bimcode_ai_pane/'+name for name in (
            'provider_bridge.py', 'provider_ui.py', 'panel.py', 'ai_tool.py',
            'ai_tool_registry.py', 'controlled_write_registry.py', 'provider_write_handoff.py')]
        for name in paths:
            if name.endswith('/ai_tool.py'):
                from readonly_source_contract import assert_readonly_core_unchanged
                assert_readonly_core_unchanged(self, ROOT)
                continue
            before = subprocess.check_output(['git', 'show', 'HEAD:'+name]).decode('utf-8-sig')
            if (name.endswith('/provider_write_handoff.py')
                    and 'd.admission.safety_locked = True' in before):
                # FIX-001: only synchronized monotonic safety publication.
                # A pre-fix HEAD needs normalization; a committed fix compares
                # byte-for-byte without applying the transformation twice.
                self.assertEqual(before.count('d.admission.safety_locked = True'), 2)
                before = before.replace('d.admission.safety_locked = True',
                    "d.admission.retain_safety(True, self, d.owner, 'ADMISSION_FINALIZATION_FAILED')", 1)
                before = before.replace('d.admission.safety_locked = True',
                    "d.admission.retain_safety(True, self, d.owner, 'CONTINUATION_TRANSITION_FAILED')", 1)
                before = before.replace('from threading import Lock', 'from threading import Lock\nfrom copy import deepcopy')
                before = before.replace('    def inspect(self):\n        self.check()',
                    '    def inspect(self):\n        # Pure retained snapshot. Expiry belongs to operational check() calls.')
                before = before.replace('last=self.last, failure=self.failure',
                                        'last=deepcopy(self.last), failure=self.failure')
            self.assertEqual(before.replace('\r\n', '\n'),
                             (ROOT/name).read_text(encoding='utf-8-sig'))
        self.assertFalse(provider_bridge.decode_tool(self.response, 'transport')['ok'])
        from bimcode_ai_pane.ai_tool_registry import TOOLS
        self.assertEqual(len(TOOLS), 13)

    def test_internal_only_import_boundary(self):
        source = (ROOT/'AI.extension/lib/bimcode_ai_pane/provider_write_adapter.py').read_text()
        tree = ast.parse(source)
        names = [n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)]
        for forbidden in ('dispatch', 'request_confirmation', 'Raise', 'Transaction', 'Set',
                          'run_worker'):
            self.assertNotIn(forbidden, names)
