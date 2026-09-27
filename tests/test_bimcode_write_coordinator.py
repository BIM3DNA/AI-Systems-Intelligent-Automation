"""Host-only confirmation/event admission tests using fake APIs."""
import importlib
import sys
from types import SimpleNamespace as N
import unittest
from unittest.mock import Mock, patch
import test_bimcode_write_runtime as fixtures
import test_bimcode_ai_pane as pane_tests
import bimcode_write_runtime as runtime


class Coordination(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.fixture()
        self.f.app.Application = N(DocumentChanged=pane_tests.Event())
        self.session = N(uiapp=self.f.app, context_generation=0, selection_generation=0,
                         tools=N(pending=None), ai=N(turn=None),
                         _subscriptions=[(None, n, None) for n in
                                         ("SelectionChanged", "ViewActivated", "DocumentClosed",
                                          "DocumentOpened", "DocumentCreated")])
        self.event = Mock()
        self.event.Raise.return_value = "Accepted"
        self.dialog = Mock()
        self.dialog.Show.return_value = "Cancel"
        self.ui = N(IExternalEventHandler=object, ExternalEvent=N(Create=Mock(return_value=self.event)),
                    ExternalEventRequest=N(Accepted="Accepted"), TaskDialog=Mock(return_value=self.dialog),
                    TaskDialogCommandLinkId=N(CommandLink1="Confirm"),
                    TaskDialogResult=N(Cancel="Cancel", CommandLink1="Confirm"),
                    TaskDialogCommonButtons=N(Cancel="Cancel"))
        db = N(Events=N(DocumentChangedEventArgs=object))
        framework = N(EventHandler=pane_tests.DelegateFactory(), Guid=N(Parse=lambda s:s))
        self.modules = patch.dict(sys.modules, {"pyrevit":N(DB=db, UI=self.ui, framework=framework)})
        self.modules.start()
        sys.modules.pop("bimcode_ai_pane.write_coordinator", None)
        self.m = importlib.import_module("bimcode_ai_pane.write_coordinator")
        self.owner = self.m.get_coordinator(self.session)
        self.preview = runtime._preview(self.f.app, "test-rid", "M4A_Write_01", 0, self.f.db, self.f.guid)
        self.forms = Mock()
        self.forms.ask_for_string.return_value = "M4A_Write_01"
        self.output = Mock()
        self.clock = patch.object(self.m, "clock", return_value=10)
        self.clock.start()
        self.builder = patch.object(self.m, "build_preview", return_value=self.preview)
        self.builder.start()

    def tearDown(self):
        self.builder.stop()
        self.clock.stop()
        sys.modules.pop("bimcode_ai_pane.write_coordinator", None)
        self.modules.stop()

    def invoke(self):
        self.owner.invoke(self.f.app, self.forms, self.output)

    def test_duplicate_registration_and_subscription(self):
        self.assertIs(self.m.get_coordinator(self.session), self.owner)
        self.ui.ExternalEvent.Create.assert_called_once()
        self.assertEqual(len(self.f.app.Application.DocumentChanged.handlers), 1)

    def test_missing_required_epochs_fails_closed(self):
        self.session._subscriptions = []
        with self.assertRaises(RuntimeError):
            self.m.get_coordinator(self.session)

    def test_cancel_input(self):
        self.forms.ask_for_string.return_value = None
        self.invoke()
        self.dialog.Show.assert_not_called()
        self.event.Raise.assert_not_called()
        self.assertFalse(self.session.write_busy)

    def test_cancel_confirmation(self):
        self.invoke()
        self.event.Raise.assert_not_called()
        self.assertIsNone(self.owner.pending)
        self.assertEqual(self.dialog.DefaultButton, "Cancel")
        self.assertTrue(self.dialog.AllowCancellation)
        self.assertFalse(self.session.write_busy)

    def test_close_unexpected_is_cancel(self):
        self.dialog.Show.return_value = "Close"
        self.invoke()
        self.event.Raise.assert_not_called()

    def test_invalid_preview_no_dialog(self):
        self.preview.update(classification="MEP_PARAMETER_WRITE_PREVIEW_NOT_READY", reason_code="INVALID_VALUE")
        self.invoke()
        self.dialog.Show.assert_not_called()
        self.event.Raise.assert_not_called()

    def test_confirm_enqueue_then_consume_once(self):
        self.dialog.Show.return_value = "Confirm"
        self.invoke()
        self.assertIsNotNone(self.owner.pending)
        self.assertTrue(self.session.write_busy)
        self.event.Raise.assert_called_once()
        self.owner.executor = Mock(retained=None)
        self.owner.executor.execute.return_value = {"test":"result"}
        self.owner.handler.Execute(self.f.app)
        self.owner.handler.Execute(self.f.app)
        self.owner.executor.execute.assert_called_once()
        self.assertFalse(self.session.write_busy)

    def test_busy_no_second_dialog_or_raise(self):
        self.dialog.Show.return_value = "Confirm"
        self.invoke()
        self.invoke()
        self.dialog.Show.assert_called_once()
        self.event.Raise.assert_called_once()

    def test_read_provider_busy(self):
        self.session.ai.turn = {}
        self.invoke()
        self.forms.ask_for_string.assert_not_called()
        self.event.Raise.assert_not_called()

    def test_model_epoch_invalidates_after_preview(self):
        def change_then_confirm():
            self.owner.on_model_changed(None, None)
            self.owner.on_model_changed(None, None)
            return "Confirm"
        self.dialog.Show.side_effect = change_then_confirm
        self.invoke()
        self.assertEqual(self.owner.epoch, 2)
        self.event.Raise.assert_not_called()

    def test_raise_failure_consumes_request(self):
        self.dialog.Show.return_value = "Confirm"
        self.event.Raise.return_value = "Pending"
        self.invoke()
        self.assertIsNone(self.owner.pending)
        self.assertFalse(self.session.write_busy)

    def test_pending_query_only(self):
        self.owner.executor = Mock(retained=object())
        self.owner.executor.check_pending.return_value = {"state":"pending"}
        self.invoke()
        self.forms.ask_for_string.assert_not_called()
        self.owner.handler.Execute(self.f.app)
        self.owner.executor.check_pending.assert_called_once()
        self.owner.executor.execute.assert_not_called()

    def test_readonly_admission_guard(self):
        from bimcode_ai_pane.ai_tool import Coordinator
        self.session.write_busy = True
        coordinator = Coordinator(self.session)
        self.assertFalse(coordinator.begin("provider-request"))
