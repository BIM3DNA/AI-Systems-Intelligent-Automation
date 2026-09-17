"""M2B offline tests; run separately with python -B (no Revit/network)."""
import ast
import importlib
import pathlib
import sys
import types
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch

import test_bimcode_ai_pane as m1
import test_modelmind_headless as m2a
from bimcode_ai_pane import tools


def host(number=1):
    doc, uidoc = m2a.context()
    doc.GetHashCode = lambda: number
    doc.PathName = ''
    uidoc.Selection.GetElementIds = lambda: types.SimpleNamespace(Count=0)
    return types.SimpleNamespace(ActiveUIDocument=uidoc)


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.uiapp = host()
        self.bridge = tools.ModelMindToolBridge()

    def run_route(self, specialties, count=1, unsupported=0, tool='selection.summary', data=None):
        request = self.bridge.begin(tool, tools.document_key(self.uiapp), 3)
        scope = dict(ok=True, specialties=specialties, selected_count=count, unsupported_count=unsupported)
        payload = data or dict(ok=True, classification='PIPING_SELECTION_SUMMARY_OK', reason_code='COMPLETE')
        with patch.object(tools, 'resolve_headless_modelmind_specialty', return_value=scope), patch.object(
                tools, 'execute_headless_modelmind_readonly', return_value=payload) as execute:
            result = self.bridge.execute(request, self.uiapp, 3)
            self.called = execute.call_args
        self.bridge.clear()
        return result

    def test_empty_selection(self):
        result = self.run_route([], 0)
        self.assertEqual(result['status'], 'NOT_READY')
        self.assertEqual(result['reason_code'], 'NO_ELEMENTS_SELECTED')
        self.assertIsNone(self.called)

    def test_piping_summary(self):
        self.run_route(['PIPING'])
        self.assertEqual(self.called.args[0], 'PIPING-RO-001-A01')

    def test_hvac_summary(self):
        self.run_route(['HVAC'])
        self.assertEqual(self.called.args[0], 'HVAC-RO-001-A01')

    def test_electrical_summary(self):
        self.run_route(['ELECTRICAL'])
        self.assertEqual(self.called.args[0], 'ELECTRICAL-RO-001-A01')

    def test_all_twelve_tool_mappings(self):
        for specialty in ('PIPING', 'HVAC', 'ELECTRICAL'):
            for tool, (_, suffix) in tools.TOOLS.items():
                self.run_route([specialty], tool=tool)
                self.assertEqual(self.called.args[0], specialty + '-RO-001-' + suffix)

    def test_unsupported_only(self):
        self.assertEqual(self.run_route([], unsupported=1)['status'], 'NOT_READY')
        self.assertIsNone(self.called)

    def test_mixed_specialties(self):
        self.assertEqual(self.run_route(['PIPING', 'HVAC'], 2)['status'], 'MIXED_SPECIALTY_REVIEW')
        self.assertIsNone(self.called)

    def test_supported_plus_unsupported_does_not_filter(self):
        result = self.run_route(['PIPING'], 2, 1)
        self.assertEqual(result['reason_code'], 'SUPPORTED_AND_UNSUPPORTED_SELECTION')
        self.assertIsNone(self.called)

    def test_changed_document_rejected_before_routing(self):
        request = self.bridge.begin('selection.summary', tools.document_key(self.uiapp), 3)
        with patch.object(tools, 'resolve_headless_modelmind_specialty') as resolve:
            self.assertEqual(self.bridge.execute(request, host(2), 3)['status'], 'STALE_CONTEXT')
            resolve.assert_not_called()

    def test_same_document_reopen_or_view_transition_rejected(self):
        request = self.bridge.begin('selection.summary', tools.document_key(self.uiapp), 3)
        self.assertEqual(self.bridge.execute(request, self.uiapp, 4)['status'], 'STALE_CONTEXT')

    def test_no_document(self):
        request = self.bridge.begin('selection.summary', None, 3)
        self.assertEqual(self.bridge.execute(request, host_none(), 3)['status'], 'NOT_READY')

    def test_single_request_and_scalar_snapshot(self):
        first = self.bridge.begin('selection.summary', tools.document_key(self.uiapp), 3)
        self.assertIsNone(self.bridge.begin('selection.qa_health', None, 3))
        self.assertIs(self.bridge.pending, first)
        tools.project_value(first)
        self.assertIsNone(first['action_id'])
        self.bridge.clear()
        self.assertEqual(self.bridge.begin('selection.qa_health', None, 4)['request_id'], 2)

    def test_classification_and_ui_status(self):
        for suffix, status in [('OK', 'OK'), ('NOT_READY', 'NOT_READY'), ('PARTIAL', 'PARTIAL'), ('FAILED', 'FAILED'), ('YELLOW', 'OK')]:
            production = 'PIPING_QA_HEALTH_' + suffix
            result = self.run_route(['PIPING'], data=dict(ok=True, classification=production))
            self.assertEqual(result['classification'], production)
            self.assertEqual(result['data']['classification'], production)
            self.assertEqual(result['status'], status)

    def test_busy_and_facade_failure(self):
        for error, status in [('EXECUTION_BUSY', 'BUSY'), ('RESULT_PROJECTION_FAILED', 'FAILED')]:
            self.assertEqual(self.run_route(['PIPING'], data=dict(ok=False, error_code=error))['status'], status)

    def test_warnings_and_bounded_tables(self):
        result = self.run_route(['PIPING'], data=dict(ok=True, classification='PRODUCTION_UNCHANGED',
            summary=['summary'], warning_records=[{'code': 'CODE', 'message': 'original warning'}],
            tables=[('Rows', ['Id'], [['x' * 600] for _ in range(100)])]))
        text = tools.render_result(result)
        self.assertIn('original warning', text)
        self.assertIn('PRODUCTION_UNCHANGED', text)
        self.assertLessEqual(len(text), tools.MAX_TEXT)
        self.assertIn('truncated', text)

    def test_raw_object_never_stringified(self):
        class Raw:
            def __str__(self):
                raise AssertionError('Raw repr reached renderer')
        self.assertIn('Invalid presentation payload', tools.render_result({'data': Raw()}))


def host_none():
    return types.SimpleNamespace(ActiveUIDocument=None)


class SessionTests(unittest.TestCase):
    setUp = m1.LifecycleTests.setUp
    tearDown = m1.LifecycleTests.tearDown
    register = m1.LifecycleTests.register

    def test_button_only_queues_and_disables(self):
        session = self.module.start(self.uiapp)
        session.panel.reset_mock()
        with patch.object(session.tools, 'execute') as execute:
            session.request_tool('selection.summary')
            session.request_tool('selection.qa_health')
            execute.assert_not_called()
        session.panel.set_tools_busy.assert_called_once_with(True)
        self.tool_external.Raise.assert_called_once()
        self.external.Raise.assert_not_called()

    def test_wpf_request_does_not_read_uiapplication(self):
        session = self.module.start(self.uiapp)

        class ForbiddenAPI:
            @property
            def ActiveUIDocument(self):
                raise AssertionError('API read from WPF callback')

        session.uiapp = ForbiddenAPI()
        session.request_tool('selection.summary')
        self.tool_external.Raise.assert_called_once()
        self.assertIsNotNone(session.tools.pending)

    def test_execute_success_restores_controls(self):
        session = self.module.start(self.uiapp)
        session.request_tool('selection.summary')
        with patch.object(session.tools, 'execute', return_value={'status': 'NOT_READY'}) as execute:
            session.tool_handler.Execute(self.uiapp)
            execute.assert_called_once()
        session.panel.render_tool_result.assert_called_once_with({'status': 'NOT_READY'})
        session.panel.set_tools_busy.assert_called_with(False)
        self.assertIsNone(session.tools.pending)

    def test_execute_failure_restores_controls(self):
        session = self.module.start(self.uiapp)
        session.request_tool('selection.summary')
        with patch.object(session.tools, 'execute', side_effect=RuntimeError('private')):
            session.tool_handler.Execute(self.uiapp)
        result = session.panel.render_tool_result.call_args.args[0]
        self.assertEqual(result['status'], 'FAILED')
        session.panel.set_tools_busy.assert_called_with(False)
        self.assertIsNone(session.tools.pending)

    def test_raise_denial_and_exception_restore_controls(self):
        session = self.module.start(self.uiapp)
        for failure in ('Denied', RuntimeError('unavailable')):
            self.tool_external.Raise.side_effect = failure if isinstance(failure, Exception) else None
            self.tool_external.Raise.return_value = failure
            session.request_tool('selection.summary')
            self.assertIsNone(session.tools.pending)
            session.panel.set_tools_busy.assert_called_with(False)

    def test_transition_invalidates_queued_request(self):
        session = self.module.start(self.uiapp)
        session.request_tool('selection.summary')
        session.on_document_closed(None, None)
        session.tool_handler.Execute(self.uiapp)
        self.assertEqual(session.panel.render_tool_result.call_args.args[0]['status'], 'STALE_CONTEXT')

    def test_repeated_start_reuses_both_handlers(self):
        session = self.module.start(self.uiapp)
        self.assertIs(session, self.module.start(self.uiapp))
        self.assertEqual(len(session._subscriptions), 5)
        self.uiapp.RegisterDockablePane.assert_called_once()

    def test_disposed_renderer_does_not_leave_pending_request(self):
        session = self.module.start(self.uiapp)
        session.panel.render_tool_result.side_effect = RuntimeError()
        session.request_tool('selection.summary')
        session.tool_handler.Execute(self.uiapp)
        self.assertIsNone(session.tools.pending)
        session.panel.set_tools_busy.assert_called_with(False)

    def test_registration_failure_disposes_both_events(self):
        self.uiapp.RegisterDockablePane.side_effect = RuntimeError()
        with self.assertRaises(RuntimeError):
            self.module.start(self.uiapp)
        self.external.Dispose.assert_called_once()
        self.tool_external.Dispose.assert_called_once()


class PanelTests(unittest.TestCase):
    def test_controls_busy_state_and_result_projection(self):
        class Control:
            def __init__(self):
                self.Click = m1.Event()
                self.TextChanged = m1.Event()
                self.UpdateLayout = Mock()
                self.Text = ''
                self.IsEnabled = True

        class WPF:
            def __init__(self):
                self.controls = {}

            def FindName(self, name):
                return self.controls.setdefault(name, Control())

        host_module = types.ModuleType('pyrevit')
        host_module.forms = types.SimpleNamespace(WPFPanel=WPF)
        with patch.dict(sys.modules, {'pyrevit': host_module}):
            sys.modules.pop('bimcode_ai_pane.panel', None)
            panel_module = importlib.import_module('bimcode_ai_pane.panel')
            panel = panel_module.BIMCodeAIPanel()
            callback = Mock()
            panel.bind_tools(callback)
            panel._on_tool(panel.FindName('SummaryButton'), None)
            callback.assert_called_once_with('selection.summary')
            panel.set_tools_busy(True)
            panel.set_status('Ready')
            self.assertEqual(panel.FindName('StatusText').Text, 'Running...')
            for name, unused in panel_module.TOOL_BUTTONS:
                self.assertFalse(panel.FindName(name).IsEnabled)
            panel._on_tool(panel.FindName('SummaryButton'), None)
            callback.assert_called_once()
            with patch.object(panel_module, 'make_document', side_effect=lambda model: model):
                panel.render_tool_result(dict(tool_name='selection.summary', status='FAILED', reason_code='test'))
            self.assertIn('FAILED', str(panel.FindName('ToolResultText').Document))
            refresh = Mock()
            panel.bind_refresh(refresh)
            with patch.object(panel_module, 'make_document', return_value=Mock()) as render:
                panel.FindName('FindInput').Text = 'failed'
                panel._on_find(None, None)
                self.assertTrue(panel.FindName('FindNext').IsEnabled)
                self.assertEqual(panel.FindName('FindCount').Text, '1/1')
                panel._on_find_next(None, None)
                panel._on_find_previous(None, None)
                render.return_value.Tag.BringIntoView.assert_called()
                panel._on_find_clear(None, None)
                self.assertEqual(panel.FindName('FindCount').Text, '0/0')
                self.assertFalse(panel.FindName('FindNext').IsEnabled)
                panel.FindName('FindInput').Text = 'not found'
                panel._on_find(None, None)
                self.assertEqual(panel.FindName('FindCount').Text, '0/0')
                panel.render_tool_result(dict(status='OK'))
                self.assertEqual(panel.FindName('FindInput').Text, '')
            callback.assert_called_once()
            refresh.assert_not_called()
            panel.set_tools_busy(False)
            for name, unused in panel_module.TOOL_BUTTONS:
                self.assertTrue(panel.FindName(name).IsEnabled)
            self.assertEqual(panel.FindName('StatusText').Text, 'Ready')
        sys.modules.pop('bimcode_ai_pane.panel', None)

    def test_xaml_readonly_result_and_send_disabled(self):
        tree = ET.parse(m1.ROOT / 'AI.extension/lib/bimcode_ai_pane/BIMCodeAIPane.xaml')
        nodes = list(tree.iter())
        self.assertEqual(len([n for n in nodes if n.get('Content') == 'Send' and n.get('IsEnabled') == 'False']), 1)
        self.assertEqual(len([n for n in nodes if n.get('{http://schemas.microsoft.com/winfx/2006/xaml}Name') == 'ToolResultText' and n.tag.endswith('FlowDocumentScrollViewer')]), 1)

    def test_only_external_event_calls_execution(self):
        path = m1.ROOT / 'AI.extension/lib/bimcode_ai_pane/lifecycle.py'
        tree = ast.parse(path.read_text())
        owner = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for call in ast.walk(node):
                    if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == 'execute':
                        owner.append(node.name)
        self.assertEqual(owner, ['Execute'])


class ResolverTests(unittest.TestCase):
    setUp = m2a.BootstrapTests.setUp
    tearDown = m2a.BootstrapTests.tearDown

    def test_empty_real_resolver(self):
        result = m2a.seam.resolve_headless_modelmind_specialty(*m2a.context())
        self.assertEqual(result, dict(ok=True, specialties=[], selected_count=0, unsupported_count=0))

    def test_resolver_exception_restores_globals(self):
        module = m2a.seam._load_backend()
        document, uidocument = m2a.context()
        uidocument.Selection.GetElementIds = Mock(side_effect=RuntimeError('private'))
        result = m2a.seam.resolve_headless_modelmind_specialty(document, uidocument)
        self.assertEqual(result['error_code'], 'SELECTION_UNREADABLE')
        self.assertIsNone(module.doc)
        self.assertIsNone(module.uidoc)
        self.assertTrue(m2a.seam.resolve_headless_modelmind_specialty(*m2a.context())['ok'])

    def test_resolver_obeys_execution_lock(self):
        m2a.seam._EXECUTION_LOCK.acquire()
        try:
            result = m2a.seam.resolve_headless_modelmind_specialty(object(), object())
            self.assertEqual(result['error_code'], 'EXECUTION_BUSY')
            self.assertIsNone(m2a.seam._MODULE)
        finally:
            m2a.seam._EXECUTION_LOCK.release()

    def test_unresolved_reference_is_not_silently_dropped(self):
        doc, uidoc = m2a.context()
        uidoc.Selection.GetElementIds = lambda: [123]
        doc.GetElement = lambda unused: None
        self.assertEqual(m2a.seam.resolve_headless_modelmind_specialty(doc, uidoc)['error_code'], 'SELECTION_UNREADABLE')
        self.assertIsNone(m2a.seam._MODULE.doc)

    def test_wrong_document_rejected(self):
        doc, uidoc = m2a.context()
        self.assertEqual(m2a.seam.resolve_headless_modelmind_specialty(m2a.Doc(), uidoc)['error_code'], 'INVALID_DOCUMENT_CONTEXT')
        self.assertIsNone(m2a.seam._MODULE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
