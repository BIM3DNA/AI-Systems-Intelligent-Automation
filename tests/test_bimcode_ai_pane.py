"""Offline M1 lifecycle probes; no Revit process, network, or file writes.

Run only this file: python -B tests/test_bimcode_ai_pane.py
Host API stubs verify scheduling/ownership, not live Revit integration.
"""

import ast
import importlib
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "AI.extension" / "lib"))
from bimcode_ai_pane.context import empty_context, read_context


class Event:
    def __init__(self):
        self.handlers = []

    def __iadd__(self, value):
        self.handlers.append(value)
        return self

    def __isub__(self, value):
        self.handlers.remove(value)
        return self


class DelegateFactory:
    def __getitem__(self, unused):
        return lambda callback: callback


class ContextTests(unittest.TestCase):
    def test_no_document(self):
        self.assertEqual(read_context(types.SimpleNamespace(ActiveUIDocument=None)), empty_context())

    def test_context_is_scalar_and_selection_is_only_counted(self):
        selection = Mock()
        selection.GetElementIds.return_value = types.SimpleNamespace(Count=4)
        view = types.SimpleNamespace(IsValidObject=True, Name="Level 1", ViewType="FloorPlan")
        doc = types.SimpleNamespace(IsValidObject=True, Title="Test model")
        uidoc = types.SimpleNamespace(Document=doc, ActiveView=view, Selection=selection)
        result = read_context(types.SimpleNamespace(ActiveUIDocument=uidoc))
        self.assertEqual(result, dict(document="Test model", view="Level 1",
                                     view_type="FloorPlan", selection_count=4, status="Ready"))
        self.assertEqual(selection.mock_calls, [unittest.mock.call.GetElementIds()])
        selection.GetElementIds.side_effect = RuntimeError("busy")
        self.assertIsNone(read_context(types.SimpleNamespace(ActiveUIDocument=uidoc))["selection_count"])
        doc.IsValidObject = False
        self.assertEqual(read_context(types.SimpleNamespace(ActiveUIDocument=uidoc)), empty_context())


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.storage = {}
        self.registered = False
        self.external = Mock()
        self.external.Raise.return_value = "Accepted"
        ui = types.SimpleNamespace(
            IDockablePaneProvider=type("Provider", (), {}),
            IExternalEventHandler=type("Handler", (), {}),
            DockablePaneId=lambda value: value,
            DockablePane=types.SimpleNamespace(PaneIsRegistered=lambda unused: self.registered),
            DockablePaneState=types.SimpleNamespace,
            DockPosition=types.SimpleNamespace(Right="Right"),
            ExternalEvent=types.SimpleNamespace(Create=lambda handler: self.external),
            ExternalEventRequest=types.SimpleNamespace(Accepted="Accepted", Pending="Pending"),
            Events=types.SimpleNamespace(ViewActivatedEventArgs=object, SelectionChangedEventArgs=object),
        )
        app = types.SimpleNamespace(DocumentOpened=Event(), DocumentCreated=Event(), DocumentClosed=Event())
        self.uiapp = types.SimpleNamespace(
            Application=app, ViewActivated=Event(), SelectionChanged=Event(), ActiveUIDocument=None,
            RegisterDockablePane=Mock(side_effect=self.register),
            GetDockablePane=Mock(return_value=Mock()),
        )
        pyrevit = types.ModuleType("pyrevit")
        pyrevit.UI = ui
        pyrevit.DB = types.SimpleNamespace(Events=types.SimpleNamespace(
            DocumentOpenedEventArgs=object, DocumentCreatedEventArgs=object, DocumentClosedEventArgs=object))
        pyrevit.framework = types.SimpleNamespace(
            Guid=types.SimpleNamespace(Parse=lambda value: value), EventHandler=DelegateFactory())
        pyrevit.forms = types.SimpleNamespace(WPFPanel=object, open_dockable_panel=Mock())
        coreutils = types.ModuleType("pyrevit.coreutils")
        coreutils.envvars = types.SimpleNamespace(
            get_pyrevit_env_var=self.storage.get,
            set_pyrevit_env_var=lambda key, value: self.storage.update({key: value}))
        presentation = types.ModuleType("bimcode_ai_pane.panel")
        presentation.BIMCodeAIPanel = Mock(side_effect=lambda: Mock())
        self.modules = patch.dict(sys.modules, {
            "pyrevit": pyrevit, "pyrevit.coreutils": coreutils,
            "bimcode_ai_pane.panel": presentation})
        self.modules.start()
        sys.modules.pop("bimcode_ai_pane.lifecycle", None)
        self.module = importlib.import_module("bimcode_ai_pane.lifecycle")

    def tearDown(self):
        sys.modules.pop("bimcode_ai_pane.lifecycle", None)
        self.modules.stop()

    def register(self, panel_id, title, provider):
        self.assertEqual(title, "BIMCode AI")
        data = types.SimpleNamespace()
        provider.SetupDockablePane(data)
        self.assertEqual(data.InitialState.DockPosition, "Right")
        self.assertTrue(data.VisibleByDefault)
        self.registered = True

    def test_repeat_start_does_not_register_or_subscribe_twice(self):
        first = self.module.start(self.uiapp)
        self.assertIs(first, self.module.start(self.uiapp))
        self.uiapp.RegisterDockablePane.assert_called_once()
        self.assertEqual(len(self.uiapp.ViewActivated.handlers), 1)
        first.subscribe()
        self.assertEqual(len(first._subscriptions), 5)
        self.assertEqual(len(self.uiapp.SelectionChanged.handlers), 1)
        self.module.show(self.uiapp)
        self.uiapp.RegisterDockablePane.assert_called_once()
        self.assertEqual(len(self.uiapp.SelectionChanged.handlers), 1)

    def test_selection_callback_updates_only_count_without_refresh(self):
        session = self.module.start(self.uiapp)
        session.panel.reset_mock()
        callback = self.uiapp.SelectionChanged.handlers[0]
        # No active document is needed: event args own the selection snapshot.
        for count in (0, 1, 3, 0):
            args = Mock()
            args.GetSelectedElements.return_value = types.SimpleNamespace(Count=count)
            callback(None, args)
            args.GetSelectedElements.assert_called_once_with()
        self.assertEqual(session.panel.mock_calls, [
            unittest.mock.call.render_selection_count(n) for n in (0, 1, 3, 0)])
        self.external.Raise.assert_not_called()

    def test_unreadable_selection_does_not_claim_zero(self):
        session = self.module.start(self.uiapp)
        args = Mock()
        args.GetSelectedElements.side_effect = RuntimeError("document switching")
        session.on_selection_changed(None, args)
        session.panel.render_selection_count.assert_called_once_with(None)
        self.external.Raise.assert_not_called()

    def test_missing_or_unavailable_panel_does_not_escape_callback(self):
        session = self.module.start(self.uiapp)
        args = Mock()
        args.GetSelectedElements.return_value = types.SimpleNamespace(Count=0)
        session.panel.render_selection_count.side_effect = RuntimeError("host closing")
        session.on_selection_changed(None, args)
        session.panel = None
        session.on_selection_changed(None, args)
        self.external.Raise.assert_not_called()

    def test_unsupported_runtime_retains_manual_refresh(self):
        del self.uiapp.SelectionChanged
        session = self.module.start(self.uiapp)
        self.assertEqual(len(session._subscriptions), 4)
        session.request_refresh()
        self.external.Raise.assert_called_once()

    def test_button_queues_then_execute_reads_context(self):
        session = self.module.start(self.uiapp)
        session.panel.render.reset_mock()
        session.request_refresh()
        self.external.Raise.assert_called_once()
        session.panel.render.assert_not_called()
        session.handler.Execute(self.uiapp)
        session.panel.render.assert_called_once_with(empty_context())

    def test_close_clears_snapshot_and_schedules_refresh(self):
        session = self.module.start(self.uiapp)
        session.on_document_closed(None, None)
        session.panel.render.assert_called_with(empty_context())
        self.external.Raise.assert_called_once()

    def test_show_retries_on_activation_when_host_not_ready(self):
        self.uiapp.ActiveUIDocument = types.SimpleNamespace(
            Document=types.SimpleNamespace(IsValidObject=True))
        self.uiapp.GetDockablePane.side_effect = RuntimeError("not ready")
        session = self.module.start(self.uiapp)
        self.assertTrue(session.show_pending)
        self.uiapp.GetDockablePane.side_effect = None
        session.on_view_activated(None, None)
        self.assertFalse(session.show_pending)

    def test_close_to_no_document_then_reopen_shows_existing_pane(self):
        session = self.module.start(self.uiapp)
        self.uiapp.GetDockablePane.assert_not_called()
        self.assertTrue(session.show_pending)
        project = types.SimpleNamespace(Document=types.SimpleNamespace(IsValidObject=True))
        self.uiapp.ActiveUIDocument = project
        session.on_view_activated(None, None)
        pane = self.uiapp.GetDockablePane.return_value
        pane.Show.assert_called_once()
        self.assertFalse(session.show_pending)

        self.uiapp.ActiveUIDocument = None
        session.on_document_closed(None, None)
        session.handler.Execute(self.uiapp)
        self.assertTrue(session.show_pending)
        pane.Show.assert_called_once()  # No Show against the no-document host.
        session.on_document_changed(None, None)
        session.handler.Execute(self.uiapp)  # Open event can precede activation.
        pane.Show.assert_called_once()
        self.uiapp.ActiveUIDocument = project
        session.on_view_activated(None, None)
        self.assertEqual(pane.Show.call_count, 2)
        self.uiapp.GetDockablePane.assert_called_with("aa6b23d4-f8e3-4b2f-9ad7-de9e05bfb5e4")
        session.on_view_activated(None, None)
        session.handler.Execute(self.uiapp)
        self.assertEqual(pane.Show.call_count, 2)  # Ordinary views do not reopen it.
        self.uiapp.RegisterDockablePane.assert_called_once()
        session.subscribe()
        self.assertEqual(len(session._subscriptions), 5)
        self.assertEqual(len(self.uiapp.ViewActivated.handlers), 1)
        self.assertEqual(len(self.uiapp.SelectionChanged.handlers), 1)

    def test_open_event_restores_visibility_via_existing_refresh_event(self):
        session = self.module.start(self.uiapp)
        session.show_pending = False
        self.uiapp.ActiveUIDocument = types.SimpleNamespace(
            Document=types.SimpleNamespace(IsValidObject=False))
        session.on_document_changed(None, None)
        session.handler.Execute(self.uiapp)
        self.uiapp.GetDockablePane.assert_not_called()
        self.assertTrue(session.show_pending)
        self.uiapp.ActiveUIDocument.Document.IsValidObject = True
        session.handler.Execute(self.uiapp)
        self.uiapp.GetDockablePane.return_value.Show.assert_called_once()
        self.assertFalse(session.show_pending)
        self.uiapp.RegisterDockablePane.assert_called_once()

    def test_registration_failure_removes_delegates(self):
        self.uiapp.RegisterDockablePane.side_effect = RuntimeError("registration failed")
        with self.assertRaises(RuntimeError):
            self.module.start(self.uiapp)
        self.assertEqual(self.uiapp.ViewActivated.handlers, [])
        self.assertEqual(self.uiapp.Application.DocumentClosed.handlers, [])
        self.assertEqual(self.uiapp.SelectionChanged.handlers, [])
        self.assertEqual(self.storage, {})
        self.external.Dispose.assert_called_once()

    def test_show_never_registers(self):
        with self.assertRaises(RuntimeError):
            self.module.show(self.uiapp)
        self.uiapp.RegisterDockablePane.assert_not_called()


class BoundaryTests(unittest.TestCase):
    def test_new_runtime_has_no_execution_or_mutation_imports(self):
        package = ROOT / "AI.extension" / "lib" / "bimcode_ai_pane"
        forbidden = {"Transaction", "TransactionGroup", "SetElementIds", "PickObject",
                     "PickObjects", "FilteredElementCollector", "OpenAndActivateDocument",
                     "requests", "openai", "urllib", "socket", "threading", "subprocess",
                     "Idling", "Timer", "DispatcherTimer"}
        for path in package.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
            names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
            imports = {n.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.alias)}
            self.assertFalse((names | imports) & forbidden, str(path))


if __name__ == "__main__":
    unittest.main(verbosity=2)
