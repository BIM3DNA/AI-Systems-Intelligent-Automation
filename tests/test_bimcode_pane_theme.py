"""Presentation-only probes; python -B tests/test_bimcode_pane_theme.py."""
import ast
import importlib
import sys
import types
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

import test_bimcode_ai_pane as m1
from bimcode_ai_pane import theme, tools


class PresentationTests(unittest.TestCase):
    def setUp(self):
        self.path = m1.ROOT / 'AI.extension/lib/bimcode_ai_pane/BIMCodeAIPane.xaml'
        self.root = ET.parse(self.path).getroot()
        self.named = {n.get('{http://schemas.microsoft.com/winfx/2006/xaml}Name'): n
                      for n in self.root.iter() if n.get('{http://schemas.microsoft.com/winfx/2006/xaml}Name')}

    def test_no_redundant_heading(self):
        self.assertFalse(any(n.get('Text') == 'BIMCode AI' for n in self.root.iter()))

    def test_context_wraps_and_preserves_all_fields(self):
        self.assertTrue(self.named['ContextBar'].tag.endswith('WrapPanel'))
        for name in ('DocumentText', 'ViewText', 'ViewTypeText', 'SelectionText', 'RefreshButton'):
            self.assertIn(self.named[name], list(self.named['ContextBar']))
        self.assertEqual(self.named['SelectionText'].get('Text'), 'Sel: 0')

    def test_short_context_with_full_value_tooltips(self):
        for name in ('DocumentText', 'ViewText', 'ViewTypeText'):
            self.assertEqual(self.named[name].get('TextTrimming'), 'CharacterEllipsis')
        self.assertEqual(self.named['RefreshButton'].get('ToolTip'), 'Refresh Revit context')

    def test_buttons_result_and_disabled_send_retained(self):
        for name in ('SummaryButton', 'ConnectorsButton', 'AssignmentButton', 'QAHealthButton'):
            self.assertIn(name, self.named)
        self.assertTrue(any(n.get('Content') == 'Send' and n.get('IsEnabled') == 'False' for n in self.root.iter()))
        self.assertTrue(self.named['ToolResultText'].tag.endswith('FlowDocumentScrollViewer'))
        self.assertEqual(tools.MAX_TEXT, 16000)

    def test_palette_keys_match_xaml_resources(self):
        keys = {n.get('{http://schemas.microsoft.com/winfx/2006/xaml}Key') for n in self.root.iter()}
        self.assertTrue(set(theme.PALETTES['dark']).issubset(keys))
        self.assertEqual(set(theme.PALETTES['dark']), set(theme.PALETTES['light']))

    def test_light_palette(self):
        resources = {}
        theme.apply_resources(resources, 'light', lambda value: value)
        self.assertEqual(resources, theme.PALETTES['light'])
        self.assertEqual(resources['SurfaceBrush'], '#ffffff')

    def test_dark_palette(self):
        resources = {}
        theme.apply_resources(resources, 'dark', lambda value: value)
        self.assertEqual(resources, theme.PALETTES['dark'])
        self.assertEqual(resources['PaneBackgroundBrush'], '#0f172a')

    def test_reads_revit_theme_without_setting_it(self):
        for value, expected in ((1, 'dark'), (2, 'light')):
            module = types.ModuleType('pyrevit')
            manager = types.SimpleNamespace(CurrentTheme=value)
            module.UI = types.SimpleNamespace(UIThemeManager=manager, UITheme=types.SimpleNamespace(Dark=1))
            with patch.dict(sys.modules, {'pyrevit': module}):
                self.assertEqual(theme.current_theme(), expected)
                self.assertEqual(manager.CurrentTheme, value)

    def test_unavailable_api_falls_back_without_polling(self):
        with patch.dict(sys.modules, {'pyrevit': types.ModuleType('pyrevit')}):
            self.assertEqual(theme.current_theme(), 'light')

    def test_theme_module_no_network_model_or_workbench_dependency(self):
        tree = ast.parse((m1.ROOT / 'AI.extension/lib/bimcode_ai_pane/theme.py').read_text())
        names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        names |= {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        self.assertFalse(names & {'Document', 'Transaction', 'Set', 'requests', 'openai', 'socket', 'OllamaAIChat', 'Idling', 'Timer'})
        self.assertFalse(any(isinstance(n, ast.Attribute) and n.attr == 'CurrentTheme' and isinstance(n.ctx, ast.Store) for n in ast.walk(tree)))

    def test_panel_tooltips_and_selection_updates(self):
        class Control:
            def __init__(self):
                self.Click = m1.Event()
                self.TextChanged = m1.Event()

        class WPF:
            def __init__(self):
                self.controls, self.Resources = {}, {}

            def FindName(self, name):
                return self.controls.setdefault(name, Control())

        module = types.ModuleType('pyrevit')
        module.forms = types.SimpleNamespace(WPFPanel=WPF)
        with patch.dict(sys.modules, {'pyrevit': module}):
            sys.modules.pop('bimcode_ai_pane.panel', None)
            panel_module = importlib.import_module('bimcode_ai_pane.panel')
            with patch.object(panel_module, 'apply_resources') as apply:
                panel = panel_module.BIMCodeAIPanel()
                panel.render(dict(document='Long full document', view='Long full view',
                                  view_type='ThreeD', selection_count=2, status='Ready'))
                self.assertEqual(panel.FindName('DocumentText').ToolTip, 'Long full document')
                self.assertEqual(panel.FindName('ViewText').ToolTip, 'Long full view')
                self.assertEqual(panel.FindName('SelectionText').Text, 'Sel: 2')
                panel.render_selection_count(None)
                self.assertEqual(panel.FindName('SelectionText').Text, 'Sel: unavailable')
                self.assertEqual(apply.call_count, 2)
        sys.modules.pop('bimcode_ai_pane.panel', None)


class ThemeLifecycleTests(unittest.TestCase):
    setUp = m1.LifecycleTests.setUp
    tearDown = m1.LifecycleTests.tearDown
    register = m1.LifecycleTests.register

    def enable_theme(self):
        self.uiapp.ThemeChanged = m1.Event()
        self.module.UI.Events.ThemeChangedEventArgs = object

    def test_retained_event_once_without_context_or_tool_changes(self):
        self.enable_theme()
        session = self.module.start(self.uiapp)
        self.module.start(self.uiapp)
        session.subscribe()
        self.assertEqual(len(self.uiapp.ThemeChanged.handlers), 1)
        self.assertEqual(len(session._subscriptions), 6)
        generation = session.context_generation
        session.panel.reset_mock()
        session.on_theme_changed(None, None)
        session.panel.apply_current_theme.assert_called_once()
        session.panel.render.assert_not_called()
        self.external.Raise.assert_not_called()
        self.tool_external.Raise.assert_not_called()
        self.assertEqual(session.context_generation, generation)

    def test_theme_subscription_rolled_back_on_registration_failure(self):
        self.enable_theme()
        self.uiapp.RegisterDockablePane.side_effect = RuntimeError()
        with self.assertRaises(RuntimeError):
            self.module.start(self.uiapp)
        self.assertEqual(self.uiapp.ThemeChanged.handlers, [])

    def test_missing_theme_event_keeps_existing_subscriptions(self):
        session = self.module.start(self.uiapp)
        self.assertEqual(len(session._subscriptions), 5)

    def test_unavailable_panel_does_not_escape_theme_event(self):
        self.enable_theme()
        session = self.module.start(self.uiapp)
        session.panel = None
        session.on_theme_changed(None, None)


if __name__ == '__main__':
    unittest.main(verbosity=2)
