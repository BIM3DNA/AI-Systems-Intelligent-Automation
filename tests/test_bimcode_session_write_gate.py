"""M4B-8A fake-host UI/lifecycle probes; no Revit process or network."""
import ast
import os
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'AI.extension/lib'))
from bimcode_ai_pane.session_write_gate import SessionWriteGate, read_document
from bimcode_ai_pane.write_access import OperationAdmission, document_eligibility
from bimcode_ai_pane.controlled_write_registry import metadata
import test_bimcode_ai_pane as pane_tests
import test_bimcode_provider as provider_tests
from test_bimcode_write_runtime import fixture as document_fixture
from test_bimcode_write_lifecycle import fixture as cleanup_fixture, finish_host
from test_bimcode_write_projection import result


def facts():
    return dict(valid_document=True, active_uidocument=True, family_document=False,
                host_document=True, linked_document=False, workshared=False,
                read_only=False, modifiable=False, fixed_parameter_available=True,
                fixed_parameter_binding_valid=True)


def eligible_gate():
    gate = SessionWriteGate(OperationAdmission())
    gate.observe('doc1', facts())
    return gate


def enable(gate):
    gate.queue_enable()
    ticket, gate.enable_pending = gate.enable_pending, None
    return gate.enable(ticket, True)


def attached_gate(executing=False):
    lifecycle, request, coordinator, clock = cleanup_fixture(executing)
    gate = SessionWriteGate(lifecycle.admission)
    gate.permission = lifecycle.permission
    gate.document, gate.facts = 'doc1', facts()
    gate.lifecycle, gate.request = lifecycle, request
    return gate, lifecycle, coordinator


class GateTests(unittest.TestCase):
    def test_default_disabled_and_diagnostics(self):
        view = SessionWriteGate(OperationAdmission()).view_model()
        self.assertEqual(view['status'], 'CONTROLLED WRITES: DISABLED')
        self.assertEqual(view['controlled_write_permission_scope'], 'NONE')
        self.assertEqual(view['eligibility_text'], 'Eligible: NO (NO_VALID_DOCUMENT)')
        self.assertEqual(view['dispatch_status'], 'PROVIDER WRITE DISPATCH: NOT YET AVAILABLE')
        for key in ('controlled_write_permission_enabled', 'controlled_write_provider_exposed',
                    'controlled_write_dispatch_available', 'preview_lease_active', 'execution_queue_lease_active'):
            self.assertIs(view[key], False)
        self.assertEqual(view['current_owner'], 'NONE')

    def test_enabled_status_and_registry_still_13(self):
        gate = eligible_gate()
        self.assertTrue(enable(gate))
        view = gate.view_model()
        self.assertEqual(view['status'], 'CONTROLLED WRITES: ENABLED FOR THIS SESSION')
        self.assertEqual(view['eligibility_text'], 'Eligible: YES (COMPLETE)')
        self.assertEqual(view['controlled_write_permission_scope'], 'CURRENT_DOCUMENT / SESSION_ONLY')
        self.assertEqual(view['active_provider_tool_count'], 13)
        self.assertEqual(view['controlled_write_metadata_count'], 1)
        self.assertFalse(view['controlled_write_provider_exposed'])
        self.assertEqual(metadata()[0]['dispatcher_state'], 'NOT_IMPLEMENTED')

    def test_cancel(self):
        gate = eligible_gate()
        gate.queue_enable()
        self.assertFalse(gate.enable(gate.enable_pending, False))
        self.assertFalse(gate.permission.view_model()['enabled'])
        self.assertEqual(gate.note, 'ENABLE_CANCELLED')

    def test_no_environment_or_api_key_enablement(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'fake-not-a-key', 'CONTROLLED_WRITES_ENABLED': '1'}):
            self.assertFalse(eligible_gate().view_model()['controlled_write_permission_enabled'])

    def test_next_session_disabled(self):
        self.assertTrue(enable(eligible_gate()))
        self.assertFalse(eligible_gate().view_model()['controlled_write_permission_enabled'])

    def test_disable_idempotent(self):
        gate = eligible_gate(); enable(gate)
        gate.cleanup('ABANDONED')
        state = gate.view_model()
        gate.cleanup('ABANDONED')
        self.assertEqual(gate.view_model(), state)
        self.assertFalse(state['controlled_write_permission_enabled'])

    def test_same_document_view_refresh_does_not_revoke(self):
        gate = eligible_gate(); enable(gate)
        gate.observe('doc1', facts())
        self.assertTrue(gate.permission.view_model()['enabled'])

    def test_switch_and_switch_back_never_restore(self):
        gate = eligible_gate(); enable(gate)
        gate.observe('doc2', facts()); gate.observe('doc1', facts())
        self.assertFalse(gate.permission.view_model()['enabled'])

    def test_lost_binding_revokes(self):
        gate = eligible_gate(); enable(gate)
        gate.observe('doc1', dict(facts(), fixed_parameter_available=False))
        self.assertFalse(gate.permission.view_model()['enabled'])
        self.assertIn('FIXED_PARAMETER_MISSING', gate.view_model()['eligibility_text'])

    def test_lifecycle_cleanup_all_resources(self):
        for reason in ('DOCUMENT_SWITCH', 'DOCUMENT_CLOSE', 'PANE_DISPOSAL', 'SHUTDOWN', 'ABANDONED'):
            gate, lifecycle, coordinator = attached_gate()
            gate.cleanup(reason)
            self.assertFalse(gate.permission.view_model()['enabled'], reason)
            self.assertEqual(lifecycle.leases.preview.state, 'INVALIDATED')
            self.assertTrue(lifecycle.sink.closed)
            self.assertIsNone(lifecycle.sink.callback)
            self.assertTrue(coordinator.closed)
            self.assertIsNone(gate.admission.active)
            self.assertIsNotNone(gate.last_cleanup)
            snapshot = gate.view_model()
            gate.cleanup(reason)
            self.assertEqual(gate.view_model(), snapshot)

    def test_execution_queue_invalidated(self):
        gate, lifecycle, _ = attached_gate()
        lifecycle.leases.confirm(lifecycle.leases.preview.binding, True)
        self.assertTrue(gate.view_model()['execution_queue_lease_active'])
        gate.cleanup('DOCUMENT_CLOSE')
        self.assertEqual(lifecycle.leases.queue.state, 'INVALIDATED')

    def test_executing_owner_retained(self):
        gate, lifecycle, _ = attached_gate(True)
        gate.cleanup('SHUTDOWN')
        self.assertEqual(gate.admission.active, lifecycle.owner)
        self.assertTrue(gate.admission.safety_locked)
        self.assertIsNone(gate.last_cleanup.host_result)

    def test_indeterminate_receipt_retained(self):
        gate, lifecycle, _ = attached_gate(True)
        data = result('INDETERMINATE', 'TRANSACTION_PENDING')
        data.update(transaction_started=True, transaction_status='Pending', model_modified=None)
        gate.request = finish_host(lifecycle, gate.request, data)
        receipt = gate.request.host_result
        gate.cleanup('PANE_DISPOSAL')
        self.assertEqual(gate.last_cleanup.host_result, receipt)
        self.assertTrue(gate.admission.safety_locked)
        self.assertIsNone(gate.admission.active)
        self.assertFalse(enable(gate))

    def test_cleanup_corruption_fails_closed_without_owner_release(self):
        gate, lifecycle, coordinator = attached_gate()
        gate.request = None
        gate.cleanup('DOCUMENT_CLOSE')
        self.assertTrue(gate.admission.safety_locked)
        self.assertEqual(gate.admission.active, lifecycle.owner)
        self.assertFalse(gate.permission.view_model()['enabled'])
        self.assertTrue(lifecycle.sink.closed)
        self.assertTrue(coordinator.closed)

    def test_disable_during_confirmation_rejects_old_ticket(self):
        gate = eligible_gate()
        gate.queue_enable()
        ticket, gate.enable_pending = gate.enable_pending, None
        gate.confirmation_active = True
        gate.cleanup('ABANDONED')
        self.assertFalse(gate.enable(ticket, True))

    def test_busy_and_safety_do_not_enable(self):
        for safety in (False, True):
            gate = eligible_gate()
            gate.admission.safety_locked = safety
            gate.admission.busy = lambda: not safety
            self.assertFalse(enable(gate))

    def test_source_boundary_no_io_execution_or_environment(self):
        source = (ROOT / 'AI.extension/lib/bimcode_ai_pane/session_write_gate.py').read_text()
        tree = ast.parse(source)
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        self.assertFalse(names & {'open', 'environ', 'getenv', 'Set', 'Transaction', 'execute',
                                  'run_worker', 'launch', 'GetElementIds', 'Selection', 'Raise'})


class EligibilityTests(unittest.TestCase):
    def setUp(self):
        self.f = document_fixture()
        self.f.doc.IsLinked = False
        self.f.doc.PathName = 'disposable'
        self.f.uidoc.Selection.GetElementIds = Mock(side_effect=AssertionError('No selection reads'))

    def check(self):
        return read_document(self.f.app, self.f.db, self.f.guid)

    def test_valid_no_selection_read(self):
        identity, actual = self.check()
        self.assertTrue(identity)
        self.assertEqual(document_eligibility(actual)['reason_code'], 'COMPLETE')
        self.f.uidoc.Selection.GetElementIds.assert_not_called()

    def test_document_reasons(self):
        for prop, reason in (('IsFamilyDocument', 'FAMILY_DOCUMENT'), ('IsLinked', 'LINKED_DOCUMENT'),
                             ('IsWorkshared', 'WORKSHARED_DOCUMENT'), ('IsReadOnly', 'READ_ONLY_DOCUMENT'),
                             ('IsModifiable', 'DOCUMENT_MODIFIABLE')):
            setattr(self.f.doc, prop, True)
            self.assertEqual(document_eligibility(self.check()[1])['reason_code'], reason)
            setattr(self.f.doc, prop, False)

    def test_no_document(self):
        self.f.app.ActiveUIDocument = None
        self.assertEqual(document_eligibility(self.check()[1])['reason_code'], 'NO_VALID_DOCUMENT')

    def test_missing_property_unknown(self):
        del self.f.doc.IsReadOnly
        self.assertEqual(document_eligibility(self.check()[1])['reason_code'], 'DOCUMENT_FACTS_UNREADABLE')

    def test_missing_identity_unknown(self):
        del self.f.doc.PathName
        self.assertEqual(document_eligibility(self.check()[1])['reason_code'], 'DOCUMENT_FACTS_UNREADABLE')

    def test_missing_parameter(self):
        self.f.db.SharedParameterElement.Lookup = lambda *a: None
        self.assertEqual(document_eligibility(self.check()[1])['reason_code'], 'FIXED_PARAMETER_MISSING')

    def test_binding_wrong_category(self):
        self.f.binding.Categories = []
        self.assertEqual(document_eligibility(self.check()[1])['reason_code'], 'FIXED_PARAMETER_BINDING_INVALID')

    def test_binding_wrong_type(self):
        self.f.doc.ParameterBindings.get_Item = lambda d: object()
        self.assertEqual(document_eligibility(self.check()[1])['reason_code'], 'FIXED_PARAMETER_BINDING_INVALID')

    def test_wrong_name(self):
        self.f.shared.Name = 'other'
        self.assertEqual(document_eligibility(self.check()[1])['reason_code'], 'FIXED_PARAMETER_BINDING_INVALID')

    def test_binding_unreadable(self):
        self.f.doc.ParameterBindings.get_Item = Mock(side_effect=RuntimeError('unreadable'))
        self.assertEqual(document_eligibility(self.check()[1])['reason_code'], 'DOCUMENT_FACTS_UNREADABLE')


class EventTests(unittest.TestCase):
    register = pane_tests.LifecycleTests.register

    def setUp(self):
        pane_tests.LifecycleTests.setUp(self)
        self.addCleanup(lambda: pane_tests.LifecycleTests.tearDown(self))
        for name in ('ApplicationClosing', 'DockableFrameVisibilityChanged'):
            setattr(self.uiapp, name, pane_tests.Event())
            setattr(self.module.UI.Events, name + 'EventArgs', object)
        self.reader = patch.object(self.module, 'read_document', return_value=('doc1', facts()))
        self.read = self.reader.start()
        self.addCleanup(self.reader.stop)
        self.session = self.module.start(self.uiapp)
        self.dialog = Mock()
        self.dialog.Show.return_value = 'Cancel'
        self.module.UI.TaskDialog = Mock(return_value=self.dialog)
        self.module.UI.TaskDialogCommonButtons = types.SimpleNamespace(Ok=1, Cancel=2)
        self.module.UI.TaskDialogResult = types.SimpleNamespace(Ok='Ok', Cancel='Cancel')

    def request(self, answer='Ok'):
        self.dialog.Show.return_value = answer
        self.session.request_write_enable()
        self.session.handler.Execute(self.uiapp)

    def test_local_click_only_queues_native_cancel_default(self):
        self.read.reset_mock()
        self.session.request_write_enable()
        self.read.assert_not_called()
        self.dialog.Show.assert_not_called()
        self.session.handler.Execute(self.uiapp)
        self.assertEqual(self.dialog.DefaultButton, 'Cancel')
        self.assertEqual(self.dialog.CommonButtons, 3)
        self.assertFalse(self.session.write_gate.permission.view_model()['enabled'])

    def test_explicit_enable_disable_no_provider_event(self):
        self.request()
        self.assertTrue(self.session.write_gate.permission.view_model()['enabled'])
        self.tool_external.Raise.assert_not_called()
        self.session.disable_writes()
        self.assertFalse(self.session.write_gate.permission.view_model()['enabled'])

    def test_switch_via_view_event(self):
        self.request()
        self.session.on_view_activated(None, None)
        self.assertTrue(self.session.write_gate.permission.view_model()['enabled'])
        self.read.return_value = ('doc2', facts())
        self.session.on_view_activated(None, None)
        self.assertFalse(self.session.write_gate.permission.view_model()['enabled'])
        self.assertTrue(self.session.write_gate.view_model()['controlled_write_document_eligible'])

    def test_document_close_immediately_disabled_no_document(self):
        self.request()
        self.session.on_document_closed(None, None)
        model = self.session.write_gate.view_model()
        self.assertFalse(model['controlled_write_permission_enabled'])
        self.assertEqual(model['controlled_write_eligibility_reason'], 'NO_VALID_DOCUMENT')

    def test_hide_and_dispose_cleanup(self):
        self.request()
        self.session.on_pane_visibility(None, types.SimpleNamespace(
            PaneId=types.SimpleNamespace(Equals=lambda other: True), DockableFrameShown=False))
        self.assertFalse(self.session.write_gate.permission.view_model()['enabled'])
        self.assertEqual(len(self.uiapp.ViewActivated.handlers), 1)
        self.session.dispose_unregistered()
        self.session.dispose_unregistered()
        self.assertTrue(self.session.write_gate.closed)
        self.external.Dispose.assert_called_once()

    def test_shutdown_event_cleanup_and_no_new_api_event(self):
        self.request()
        self.external.Raise.reset_mock()
        self.uiapp.ApplicationClosing.handlers[0](None, None)
        self.assertFalse(self.session.write_gate.permission.view_model()['enabled'])
        self.assertTrue(self.session.disposed)
        self.external.Raise.assert_not_called()
        self.assertEqual(self.uiapp.ApplicationClosing.handlers, [])
        self.session.handler.Execute(self.uiapp)  # Stale queued enable stays dead.

    def test_duplicate_subscriptions_guard(self):
        self.session.subscribe()
        self.module.start(self.uiapp)
        for name in ('ApplicationClosing', 'DockableFrameVisibilityChanged', 'SelectionChanged'):
            self.assertEqual(len(getattr(self.uiapp, name).handlers), 1)

    def test_wired_events_clean_actual_foundation_slot(self):
        for callback in (self.session.disable_writes, self.session.on_pane_unloaded,
                         lambda: self.session.on_document_closed(None, None),
                         lambda: self.session.on_document_changed(None, None)):
            gate, lifecycle, coordinator = attached_gate()
            self.session.write_gate = gate
            callback()
            self.assertTrue(lifecycle.sink.closed)
            self.assertTrue(coordinator.closed)
            self.assertEqual(lifecycle.leases.preview.state, 'INVALIDATED')
            self.assertIsNone(gate.admission.active)

    def test_document_change_during_dialog(self):
        self.dialog.Show.side_effect = lambda: (self.read.configure_mock(return_value=('doc2', facts())) or 'Ok')
        self.request()
        self.assertFalse(self.session.write_gate.permission.view_model()['enabled'])

    def test_disable_during_dialog(self):
        self.dialog.Show.side_effect = lambda: (self.session.disable_writes() or 'Ok')
        self.request()
        self.assertFalse(self.session.write_gate.permission.view_model()['enabled'])

    def test_ineligible_no_dialog_exact_reason(self):
        self.read.return_value = ('doc1', dict(facts(), workshared=True))
        self.request()
        self.dialog.Show.assert_not_called()
        self.assertEqual(self.session.write_gate.note, 'WORKSHARED_DOCUMENT')

    def test_missing_lifecycle_subscription_blocks_enable(self):
        self.session._subscriptions = [s for s in self.session._subscriptions if s[1] != 'ApplicationClosing']
        self.request()
        self.dialog.Show.assert_not_called()
        self.assertEqual(self.session.write_gate.note, 'LIFECYCLE_EVENTS_UNAVAILABLE')

    def test_event_failure_no_pending_enable(self):
        self.external.Raise.side_effect = RuntimeError('unavailable')
        self.session.request_write_enable()
        self.assertIsNone(self.session.write_gate.enable_pending)
        self.assertEqual(self.session.write_gate.note, 'ENABLE_EVENT_UNAVAILABLE')


class PanelTests(unittest.TestCase):
    def setUp(self):
        provider_tests.PaneTests.setUp(self)

    def test_controls_render_only_bound_state(self):
        gate = eligible_gate()
        self.panel.render_write_gate(gate.view_model())
        self.assertEqual(self.panel.FindName('WritePermissionText').Text, 'CONTROLLED WRITES: DISABLED')
        enable(gate)
        self.panel.render_write_gate(gate.view_model())
        self.assertEqual(self.panel.FindName('WritePermissionText').Text, 'CONTROLLED WRITES: ENABLED FOR THIS SESSION')
        self.assertEqual(self.panel.FindName('WriteDispatchText').Text, 'PROVIDER WRITE DISPATCH: NOT YET AVAILABLE')
        self.assertFalse(self.panel.FindName('EnableWritesButton').IsEnabled)
        self.assertIn('active_provider_tool_count: 13', self.panel.FindName('WriteGateArea').ToolTip)

    def test_controls_only_call_local_bound_callbacks(self):
        callbacks = [Mock(), Mock(), Mock()]
        self.panel.bind_write_gate(*callbacks)
        calls_before = self.launch.call_count
        self.panel._on_enable_writes(None, None)
        self.panel._on_disable_writes(None, None)
        self.panel._on_unloaded(None, None)
        for callback in callbacks:
            callback.assert_called_once_with()
        self.assertEqual(self.launch.call_count, calls_before)


if __name__ == '__main__':
    unittest.main()
