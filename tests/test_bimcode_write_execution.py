"""Offline transaction-state tests. No Revit model or provider used."""
import json
import unittest
from unittest.mock import Mock
from types import SimpleNamespace as N
import test_bimcode_write_runtime as fixtures
import bimcode_write_execution as w
import bimcode_write_runtime as preview_runtime


class Execution(unittest.TestCase):
    def setUp(self):
        f = self.f = fixtures.fixture()
        f.db.ElementId = fixtures.Identity
        self.preview = preview_runtime._preview(f.app, "rid", "M4A_Write_01", 0, f.db, f.guid)
        self.request = w.freeze(self.preview, (0, 0, 0), 10, 11)
        self.executor = w.Executor()
        self.tx = Mock()
        self.status = "Uninitialized"
        self.value = None
        self.has_value = False
        def start():
            self.status = "Started"
            return self.status
        def commit():
            self.status = "Committed"
            return self.status
        def rollback():
            self.status = "RolledBack"
            self.value = None
            return self.status
        def set_value(value):
            self.value = value
            self.has_value = True
            return True
        self.tx.Start.side_effect = start
        self.tx.Commit.side_effect = commit
        self.tx.RollBack.side_effect = rollback
        self.tx.GetStatus.side_effect = lambda: self.status
        f.parameter.AsString = lambda: self.value
        # HasValue changes are not needed until post-commit in this fixture.
        f.parameter.Set = Mock(side_effect=set_value)
        f.db.Transaction = Mock(return_value=self.tx)
        f.db.TransactionStatus = N(Started="Started", Committed="Committed", RolledBack="RolledBack",
                                  Pending="Pending", Uninitialized="Uninitialized")

    def execute(self, epochs=(0, 0, 0), now=12):
        f = self.f
        return self.executor.execute(self.request, f.app, epochs, now, f.db, f.guid)

    def rejected(self, reason):
        result = self.execute()
        self.assertEqual(result["reason_code"], reason)
        self.f.db.Transaction.assert_not_called()
        self.assertFalse(result["transaction_started"])
        self.assertFalse(result["model_modified"])

    def test_success(self):
        result = self.execute()
        self.assertEqual(result["reason_code"], "COMPLETE")
        self.assertTrue(result["verification_passed"])
        self.assertTrue(result["transaction_committed"])
        self.assertTrue(result["model_modified"])
        self.f.db.Transaction.assert_called_once_with(self.f.doc, w.TRANSACTION_NAME)
        self.f.parameter.Set.assert_called_once_with("M4A_Write_01")
        self.tx.Start.assert_called_once()
        self.tx.Commit.assert_called_once()
        self.tx.RollBack.assert_not_called()

    def test_stale_epoch_and_aba(self):
        for epochs in ((1, 0, 0), (0, 2, 0), (0, 0, 2)):
            self.executor = w.Executor()
            self.assertEqual(self.execute(epochs)["reason_code"], "STALE_CONTEXT")
        self.f.db.Transaction.assert_not_called()

    def test_expiry(self):
        self.assertEqual(self.execute(now=71)["reason_code"], "CONFIRMATION_EXPIRED")
        self.f.db.Transaction.assert_not_called()

    def test_stale_document(self):
        self.f.doc.GetHashCode = lambda: 999
        self.rejected("STALE_CONTEXT")

    def test_target_missing(self):
        self.f.doc.GetElement = lambda eid: None
        self.rejected("TARGET_MISSING")

    def test_target_changed(self):
        self.f.pipe.UniqueId = "other"
        self.rejected("TARGET_CHANGED")

    def test_parameter_missing(self):
        self.f.pipe.get_Parameter = lambda g: None
        self.rejected("PARAMETER_MISSING")

    def test_wrong_storage(self):
        self.f.parameter.StorageType = "Integer"
        self.rejected("STORAGE_TYPE_UNSUPPORTED")

    def test_read_only(self):
        self.f.parameter.IsReadOnly = True
        self.rejected("TARGET_NOT_WRITABLE")

    def test_before_changed(self):
        self.value = "Changed"
        self.rejected("PRECONDITION_CHANGED")

    def test_has_value_changed(self):
        self.f.parameter.HasValue = True
        self.rejected("PRECONDITION_CHANGED")

    def test_selection_changed(self):
        self.f.uidoc.Selection.GetElementIds = lambda: []
        self.rejected("STALE_CONTEXT")

    def test_invalid_value(self):
        self.preview["proposed_value"] = "bad/"
        self.request = w.freeze(self.preview, (0, 0, 0), 10, 11)
        self.rejected("INVALID_VALUE")

    def test_immutable_request(self):
        original = self.request.preview_json
        self.preview["current_value"] = "Changed"
        self.assertEqual(self.request.preview_json, original)
        with self.assertRaises(AttributeError):
            self.request.created = 999

    def test_replay(self):
        self.execute()
        self.assertEqual(self.execute()["reason_code"], "CONFIRMATION_INVALID")
        self.f.db.Transaction.assert_called_once()

    def test_busy(self):
        self.executor.retained = object()
        self.assertEqual(self.execute()["reason_code"], "EXECUTION_BUSY")
        self.f.db.Transaction.assert_not_called()

    def test_set_false(self):
        self.f.parameter.Set.side_effect = None
        self.f.parameter.Set.return_value = False
        self.assertEqual(self.execute()["reason_code"], "PARAMETER_SET_FAILED")
        self.tx.RollBack.assert_called_once()
        self.tx.Commit.assert_not_called()
        self.f.parameter.Set.assert_called_once()

    def test_set_exception(self):
        self.f.parameter.Set.side_effect = RuntimeError("set")
        self.assertEqual(self.execute()["reason_code"], "PARAMETER_SET_FAILED")
        self.tx.RollBack.assert_called_once()
        self.tx.Commit.assert_not_called()

    def test_commit_rolled_back(self):
        def commit():
            self.status = "RolledBack"
            return self.status
        self.tx.Commit.side_effect = commit
        result = self.execute()
        self.assertEqual(result["reason_code"], "TRANSACTION_COMMIT_FAILED")
        self.assertFalse(result["model_modified"])
        self.tx.Commit.assert_called_once()

    def test_pending_retained_and_resolution_no_second_write(self):
        def commit():
            self.status = "Pending"
            return self.status
        self.tx.Commit.side_effect = commit
        result = self.execute()
        self.assertEqual(result["reason_code"], "TRANSACTION_PENDING")
        self.assertIsNone(result["model_modified"])
        self.tx.Dispose.assert_not_called()
        self.tx.RollBack.assert_not_called()
        self.status = "Committed"
        result = self.executor.check_pending(self.f.db, self.f.guid)
        self.assertTrue(result["verification_passed"])
        self.f.parameter.Set.assert_called_once()
        self.f.db.Transaction.assert_called_once()
        self.tx.Commit.assert_called_once()

    def test_verification_mismatch(self):
        self.f.parameter.Set.side_effect = lambda v: True
        result = self.execute()
        self.assertEqual(result["reason_code"], "VERIFICATION_FAILED")
        self.assertTrue(result["model_modified"])
        self.assertTrue(result["transaction_committed"])
        self.tx.RollBack.assert_not_called()

    def test_start_exception(self):
        self.tx.Start.side_effect = RuntimeError("start")
        self.assertEqual(self.execute()["reason_code"], "TRANSACTION_START_FAILED")
        self.f.parameter.Set.assert_not_called()

    def test_commit_exception(self):
        self.tx.Commit.side_effect = RuntimeError("commit")
        self.assertEqual(self.execute()["reason_code"], "TRANSACTION_COMMIT_FAILED")
        self.tx.RollBack.assert_called_once()

    def test_unconfirmed_rollback(self):
        self.f.parameter.Set.side_effect = RuntimeError("set")
        self.tx.RollBack.side_effect = RuntimeError("rollback")
        self.assertEqual(self.execute()["reason_code"], "ROLLBACK_UNCONFIRMED")
        self.tx.Dispose.assert_not_called()
        self.assertIsNotNone(self.executor.retained)
