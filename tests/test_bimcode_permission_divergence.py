"""002C permission/finalization regressions, retaining the six 002B probes.

Fake host execution only. No Revit, provider request, or production correction.
"""
import ast
import json
from pathlib import Path
from types import SimpleNamespace as N
import unittest
from unittest.mock import Mock, patch
import test_bimcode_provider_write_host_bridge as host_tests
import test_bimcode_ai_pane as pane_tests
from bimcode_ai_pane.provider_write_session import SessionWrites


def method(path, class_name, method_name):
    """Run the exact pure callback body without importing its WPF/API host."""
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method_name)
    namespace = {}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace[method_name]


ROOT = Path(__file__).resolve().parents[1] / 'AI.extension/lib/bimcode_ai_pane'


class PermissionDivergence(unittest.TestCase):
    setUp = host_tests.HostBridge.setUp
    confirm = host_tests.HostBridge.confirm
    run_host = host_tests.HostBridge.run_host
    host = host_tests.HostBridge.host

    def api(self):
        api = SessionWrites(self.session)
        api.dispatcher = self.d
        return api

    def test_success_finalizes_without_disabling_before_any_undo(self):
        self.assertIs(self.d.lifecycle.permission, self.gate.permission)
        self.assertIs(self.d.admission, self.gate.admission)
        self.confirm()
        self.assertTrue(self.gate.permission.view_model()['enabled'])
        observed = []
        original = self.gate.permission.disable
        def disable():
            observed.append((self.d.request.state, self.host()['reason_code'],
                             self.d.sink.receipt is not None))
            original()
        with patch.object(self.gate.permission, 'disable', side_effect=disable):
            self.run_host()
        self.assertEqual(observed, [])
        self.assertEqual(self.d.lifecycle.result.reason, 'REQUEST_FINALIZED')
        self.assertFalse(self.d.lifecycle.result.permission_reset)
        self.assertTrue(self.host()['transaction_committed'])
        self.assertTrue(self.host()['verification_passed'])
        self.assertTrue(self.gate.permission.view_model()['enabled'])
        self.assertIsNone(self.d.admission.active)
        self.assertIsNone(self.bridge.pending)
        self.assertIsNone(self.gate.lifecycle)
        self.assertTrue(self.d.sink.closed)
        self.assertTrue(self.d.leases.closed)
        self.assertEqual(self.d.leases.queue.state, 'EXECUTION_STARTED')
        self.assertEqual(json.loads(self.api().inspect())['state'], 'HOST_RESULT_READY')

    def test_owner_release_and_receipt_storage_alone_do_not_disable(self):
        from test_bimcode_write_projection import result
        data = result()
        data['request_id'] = self.identity.host_request_id
        self.d.sink.store(data)
        self.assertTrue(self.gate.permission.view_model()['enabled'])
        self.d.sink.cleanup()
        self.assertTrue(self.gate.permission.view_model()['enabled'])
        self.assertTrue(self.d.admission.release(self.d.owner, 'HOST_RESULT_READY'))
        self.assertTrue(self.gate.permission.view_model()['enabled'])

    def test_pane_refreshes_from_authority_and_stale_text_cannot_authorize(self):
        fields = {}
        render = method(ROOT / 'panel.py', 'BIMCodeAIPanel', 'render_write_gate')
        panel = N(FindName=lambda name: fields.setdefault(name, N()))
        self.session.panel = panel
        panel.render_write_gate = Mock(side_effect=lambda model: render(panel, model))
        refresh = method(ROOT / 'lifecycle.py', 'PaneSession', 'render_write_gate')
        self.session.render_write_gate = lambda: refresh(self.session)
        self.session.render_write_gate()
        self.confirm()
        self.run_host()
        self.assertEqual(fields['WritePermissionText'].Text,
                         'CONTROLLED WRITES: ENABLED FOR THIS SESSION')
        self.assertEqual(panel.render_write_gate.call_count, 3)
        status = json.loads(self.api().inspect())
        self.assertTrue(status['permission_enabled'])
        self.assertFalse(status['busy'])
        self.assertTrue(self.d._permission(self.identity.document_id))
        # Artificially stale display never grants permission: only authority does.
        self.gate.permission.disable()
        self.assertFalse(self.d._permission(self.identity.document_id))
        with patch('bimcode_ai_pane.provider_write_session.get_bridge') as bridge:
            self.assertEqual(json.loads(self.api().begin('Another'))['reason'], 'PERMISSION_DISABLED')
            bridge.assert_not_called()
        self.session.render_write_gate()
        self.assertEqual(fields['WritePermissionText'].Text, 'CONTROLLED WRITES: DISABLED')

    def test_document_changed_callback_only_increments_epoch(self):
        callback = method(ROOT / 'write_coordinator.py', 'WriteCoordinator', 'on_model_changed')
        coordinator = self.session.m4a_write
        generation = self.gate.permission.generation
        for operation in ('TransactionCommitted', 'TransactionUndone', 'TransactionRedone'):
            before = coordinator.epoch
            callback(coordinator, None, N(Operation=operation))
            self.assertEqual(coordinator.epoch, before + 1)
            self.assertTrue(self.gate.permission.view_model()['enabled'])
            self.assertEqual(self.gate.permission.generation, generation)

    def test_selection_callback_does_not_disable_permission(self):
        callback = method(ROOT / 'lifecycle.py', 'PaneSession', 'on_selection_changed')
        self.session.panel = N(render_selection_count=Mock())
        before = self.session.selection_generation
        callback(self.session, None, N(GetSelectedElements=lambda: N(Count=0)))
        self.assertEqual(self.session.selection_generation, before + 1)
        self.assertTrue(self.gate.permission.view_model()['enabled'])

    def test_explicit_disable_and_document_switch_revoke_and_render(self):
        # Actual PaneSession callbacks, with the existing fake-host fixture.
        fixture = pane_tests.LifecycleTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        session = fixture.module.start(fixture.uiapp)
        for action in (session.disable_writes,
                       lambda: session.on_document_changed(None, None),
                       lambda: session.on_document_closed(None, None),
                       session.on_pane_unloaded,
                       lambda: session.on_shutdown(None, None)):
            session.write_gate.observe(self.gate.document, self.gate.facts)
            session.write_gate.permission.enable_from_human(self.gate.document, self.gate.facts, True)
            action()
            self.assertFalse(session.write_gate.permission.view_model()['enabled'])
            self.assertFalse(session.panel.render_write_gate.call_args[0][0]['controlled_write_permission_enabled'])

    def test_fresh_request_after_success_without_reenable_and_old_receipt_immutable(self):
        from bimcode_ai_pane.provider_write_dispatch import Dispatcher
        self.confirm()
        self.run_host()
        receipt = self.d.request.host_result
        self.session.uiapp = self.f.app
        api = self.api()
        native_dispatch = lambda d, app, call, response: d._dispatch(app, call, response, self.f.db, self.f.guid)
        with patch('bimcode_ai_pane.provider_write_session.get_bridge', return_value=self.bridge), \
                patch.object(Dispatcher, 'dispatch', native_dispatch):
            fresh = json.loads(api.begin('Next_Value'))
        self.assertTrue(fresh['accepted'])
        self.assertEqual(fresh['state'], 'AWAITING_HUMAN_CONFIRMATION')
        self.assertNotEqual(fresh['host_request_id'], self.identity.host_request_id)
        self.assertIs(self.d.request.host_result, receipt)
        self.run_host()  # old event has no pending ticket
        self.f.parameter.Set.assert_called_once()
        self.assertIs(self.d.request.host_result, receipt)

    def test_cancel_preserves_permission_without_transaction(self):
        self.show.return_value = False
        self.confirm()
        self.assertEqual(self.d.request.state, 'CANCELLED')
        self.assertEqual(self.host()['reason_code'], 'USER_CANCELLED')
        self.assertTrue(self.gate.permission.view_model()['enabled'])
        self.assertIsNone(self.d.admission.active)
        self.f.parameter.Set.assert_not_called()

    def test_preview_expiry_preserves_session_permission_not_approval(self):
        self.now += 121
        self.confirm()
        self.assertEqual(self.host()['reason_code'], 'PREVIEW_LEASE_EXPIRED')
        self.assertTrue(self.gate.permission.view_model()['enabled'])
        self.assertTrue(self.d.leases.closed)
        self.confirm()
        self.run_host()
        self.f.parameter.Set.assert_not_called()

    def test_queue_expiry_preserves_session_permission_not_approval(self):
        self.confirm()
        self.now += 31
        self.run_host()
        self.assertEqual(self.host()['reason_code'], 'EXECUTION_QUEUE_LEASE_EXPIRED')
        self.assertTrue(self.gate.permission.view_model()['enabled'])
        self.assertIsNone(self.d.admission.active)
        self.f.parameter.Set.assert_not_called()

    def test_invalid_document_eligibility_revokes_permission(self):
        self.confirm()
        self.f.doc.IsReadOnly = True
        self.run_host()
        self.assertEqual(self.host()['reason_code'], 'READ_ONLY_DOCUMENT')
        self.assertFalse(self.gate.permission.view_model()['enabled'])
        self.f.parameter.Set.assert_not_called()
