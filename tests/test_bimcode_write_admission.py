"""M4B admission and optional completion: fake host only, no Revit requests."""
import importlib.util
import pathlib
import sys
import unittest
from types import SimpleNamespace as N
from unittest.mock import Mock, patch
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "AI.extension/lib"))
from bimcode_ai_pane.write_access import OperationAdmission, OWNER_TYPES, admission_for, run_human_operation
from bimcode_ai_pane.write_completion import CompletionSink
from bimcode_ai_pane import write_projection as p
from test_bimcode_write_projection import result


def acquire(manager, kind="HUMAN_DEV_WRITE", rid="host1"):
    return manager.acquire(kind, rid, rid, "doc1", "session1", 1)


class Admission(unittest.TestCase):
    def test_all_owner_pairs_exclusive(self):
        for first in OWNER_TYPES:
            for second in OWNER_TYPES:
                manager = OperationAdmission()
                owner = acquire(manager, first)
                self.assertIsNotNone(owner)
                self.assertIsNone(acquire(manager, second))
                self.assertEqual(manager.active, owner)

    def test_matching_and_idempotent_release(self):
        manager = OperationAdmission(); owner = acquire(manager)
        self.assertFalse(manager.release(owner._replace(logical_request_id="other"), "BAD"))
        self.assertTrue(manager.release(owner, "DONE"))
        self.assertTrue(manager.release(owner, "DONE"))
        self.assertEqual(manager.last_released[1].release_reason, "DONE")
        other = acquire(manager, rid="host2")
        self.assertFalse(manager.release(owner, "LATE"))
        self.assertEqual(manager.active, other)

    def test_cleanup_and_safety_separate(self):
        for reason in ("DOCUMENT_CLOSE", "DOCUMENT_SWITCH", "PANE_DISPOSAL", "SHUTDOWN", "ABANDONED"):
            manager = OperationAdmission(); owner = acquire(manager)
            self.assertTrue(manager.cleanup(owner, reason, transaction_unresolved=True))
            self.assertIsNone(manager.active)
            self.assertTrue(manager.safety_locked)
            self.assertIsNone(acquire(manager))
            self.assertFalse(manager.resolve_safety(False))
            self.assertTrue(manager.resolve_safety(True))
            self.assertIsNotNone(acquire(manager))

    def test_stale_cleanup_no_stealing(self):
        manager = OperationAdmission(); owner = acquire(manager)
        self.assertFalse(manager.cleanup(owner._replace(token="old"), "STALE"))
        self.assertEqual(manager.active, owner)

    def test_legacy_busy_guards(self):
        session = N(write_busy=False, tools=N(pending=None), ai=N(turn=None))
        manager = admission_for(session)
        for obj, key in ((session, "write_busy"), (session.tools, "pending"), (session.ai, "turn")):
            setattr(obj, key, True)
            self.assertIsNone(acquire(manager))
            setattr(obj, key, False if key == "write_busy" else None)

    def test_human_guard_and_release_on_exception(self):
        session = N(document_identity="doc1")
        manager = admission_for(session); owner = acquire(manager, "CONTROLLED_WRITE_PROVIDER_TOOL")
        callback = Mock()
        with self.assertRaises(RuntimeError):
            run_human_operation(session, "PARAMETER_PROVISIONING", callback)
        callback.assert_not_called()
        manager.release(owner, "CLEANUP")
        with self.assertRaises(ValueError):
            run_human_operation(session, "HUMAN_DEV_PREVIEW", Mock(side_effect=ValueError()))
        self.assertIsNone(manager.active)


class Callbacks(unittest.TestCase):
    def test_every_host_outcome_once(self):
        cases = [("OK", "COMPLETE"), ("CANCELLED", "USER_CANCELLED"),
                 ("NOT_READY", "CONFIRMATION_EXPIRED"), ("PREVIEW_NOT_READY", "NO_CHANGE_REQUIRED"),
                 ("NOT_READY", "STALE_CONTEXT"), ("FAILED", "READ_FAILED"),
                 ("INDETERMINATE", "TRANSACTION_PENDING"), ("FAILED", "VERIFICATION_FAILED")]
        for kind, reason in cases:
            data = result(kind, reason)
            if kind == "PREVIEW_NOT_READY":
                data.update(current_value=None, current_has_value=False)
            if kind == "INDETERMINATE":
                data.update(transaction_started=True, transaction_status="Pending", model_modified=None)
            if reason == "VERIFICATION_FAILED":
                data.update(transaction_started=True, transaction_committed=True, transaction_status="Committed",
                            model_modified=True, verification_performed=True)
            callback = Mock(); sink = CompletionSink(acquire(OperationAdmission()), callback)
            self.assertTrue(sink.store(data))
            self.assertFalse(sink.store(data))
            self.assertTrue(sink.deliver("host1"))
            self.assertFalse(sink.deliver("host1"))
            callback.assert_called_once()
            self.assertEqual(p.project_receipt(sink.receipt.receipt)["classification"], data["classification"])

    def test_exception_isolated(self):
        sink = CompletionSink(acquire(OperationAdmission()), Mock(side_effect=ValueError("private")))
        sink.store(result()); sink.deliver("host1")
        self.assertEqual(sink.error, "CALLBACK_FAILED")
        self.assertTrue(p.project_receipt(sink.receipt.receipt)["transaction_committed"])

    def test_late_mismatched_delivery(self):
        callback = Mock(); sink = CompletionSink(acquire(OperationAdmission()), callback)
        sink.store(result())
        self.assertFalse(sink.deliver("other"))
        sink.cleanup()
        self.assertFalse(sink.deliver("host1"))
        callback.assert_not_called()
        self.assertIsNotNone(sink.receipt)

    def test_immutable_and_reentrant(self):
        data = result(); sink = CompletionSink(acquire(OperationAdmission()))
        def callback(receipt):
            self.assertFalse(sink.deliver("host1"))
            with self.assertRaises(AttributeError):
                receipt.receipt = None
            p.project_receipt(receipt.receipt)["warnings"].append("changed")
        sink.callback = callback
        sink.store(data); data["final_value"] = "changed"
        sink.deliver("host1")
        self.assertEqual(p.project_receipt(sink.receipt.receipt)["final_value"], "New")

    def test_wrong_host_result_rejected(self):
        sink = CompletionSink(acquire(OperationAdmission()))
        data = result(); data["request_id"] = "wrong"
        with self.assertRaises(ValueError):
            sink.store(data)

    def test_unknown_internal_error_is_preserved(self):
        data = result("INDETERMINATE", "INTERNAL_ERROR")
        data["model_modified"] = None
        sink = CompletionSink(acquire(OperationAdmission()))
        self.assertTrue(sink.store(data))
        projected = p.project_receipt(sink.receipt.receipt)
        self.assertIsNone(projected["model_modified"])
        self.assertEqual(projected["transaction_status"], "NOT_STARTED")


class Integration(unittest.TestCase):
    def setUp(self):
        system = patch.dict(sys.modules, {"System": N(Action=lambda f: f)})
        system.start()
        self.addCleanup(system.stop)
        spec = importlib.util.spec_from_file_location("fake_write_coordinator", ROOT / "AI.extension/lib/bimcode_ai_pane/write_coordinator.py")
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"pyrevit": N(DB=N(), UI=N(IExternalEventHandler=object), framework=N(Action=lambda f: f))}):
            spec.loader.exec_module(self.module)
        self.queue = []
        self.session = N(document_identity="doc1", tools=N(pending=None), ai=N(turn=None),
                         context_generation=1, selection_generation=1, panel=N(Dispatcher=N(BeginInvoke=self.queue.append)))
        self.coordinator = self.module.WriteCoordinator.__new__(self.module.WriteCoordinator)
        self.coordinator.__dict__.update(session=self.session, pending=None, output=None, epoch=0,
            executor=N(retained=None), resolving=False, running=False, delivering=False,
            admission=admission_for(self.session), owner=None, completion_sink=None)

    def test_dev_cancel_no_callback(self):
        with patch.object(self.module, "clock", return_value=1), patch.object(self.module, "capture_preview_context", return_value={}):
            self.coordinator.invoke(None, N(ask_for_string=lambda **kw: None), Mock())
        self.assertFalse(self.session.write_busy)
        self.assertIsNone(self.coordinator.admission.active)
        self.assertEqual(self.coordinator.completion_sink.receipt.owner_type, "HUMAN_DEV_WRITE")

    def test_deferred_callback_cleanup(self):
        callback = Mock()
        with patch.object(self.module, "clock", return_value=1), patch.object(self.module, "capture_preview_context", return_value={}):
            self.coordinator.invoke(None, N(ask_for_string=lambda **kw: None), Mock(), callback)
        callback.assert_not_called()
        self.assertEqual(len(self.queue), 1)
        self.coordinator.cleanup("DOCUMENT_CLOSE")
        self.queue[0]()
        callback.assert_not_called()
        self.assertIsNone(self.coordinator.admission.active)

    def test_provider_owner_blocks_dev(self):
        owner = acquire(self.coordinator.admission, "CONTROLLED_WRITE_PROVIDER_TOOL")
        forms = N(ask_for_string=Mock())
        with patch.object(self.module, "clock", return_value=1):
            self.coordinator.invoke(None, forms, Mock())
        forms.ask_for_string.assert_not_called()
        self.assertEqual(self.coordinator.admission.active, owner)

    def test_callback_reentry_cannot_write(self):
        forms = N(ask_for_string=Mock(return_value=None)); output = Mock()
        def callback(receipt):
            self.coordinator.invoke(None, forms, output)
        with patch.object(self.module, "clock", return_value=1), patch.object(self.module, "capture_preview_context", return_value={}):
            self.coordinator.invoke(None, forms, output, callback)
            self.queue[0]()
        self.assertEqual(forms.ask_for_string.call_count, 1)

    def test_execute_completion_keeps_host_result(self):
        self.coordinator.owner = acquire(self.coordinator.admission)
        callback = Mock()
        self.coordinator.completion_sink = CompletionSink(self.coordinator.owner, callback)
        self.coordinator.pending = N(preview_json='{}')
        data = result()
        self.coordinator.executor.execute = Mock(return_value=data)
        self.coordinator.output = Mock()
        self.module.framework.Guid = N(Parse=lambda value: value)
        with patch.object(self.module, "clock", return_value=1):
            self.coordinator.execute(None)
        self.assertEqual(len(self.queue), 1)
        self.queue[0]()
        callback.assert_called_once()
        self.assertEqual(p.project_receipt(callback.call_args[0][0].receipt)["final_value"], "New")

    def test_indeterminate_retains_lower_lock(self):
        self.coordinator.owner = acquire(self.coordinator.admission)
        self.coordinator.completion_sink = CompletionSink(self.coordinator.owner)
        self.coordinator.executor.retained = object()
        data = result("INDETERMINATE", "TRANSACTION_PENDING")
        data.update(transaction_status="Pending", model_modified=None)
        self.coordinator.complete(data)
        self.assertIsNone(self.coordinator.admission.active)
        self.assertTrue(self.coordinator.admission.safety_locked)
        self.coordinator.cleanup("PANE_DISPOSAL")
        self.assertTrue(self.coordinator.admission.safety_locked)
