"""M4A-DIAG-001: offline delayed dispatch and independent JSONL evidence.

No Revit/provider calls. Temporary logs live outside the repository.
"""
import ast
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace as N
import unittest
from unittest.mock import Mock, patch

import test_bimcode_write_coordinator as coordinator_fixture
import test_bimcode_write_execution as execution_fixture
from bimcode_ai_pane import write_diagnostic as d


def diagnostic_contract_ast(source):
    """Remove only the temporary observation seam; compare all remaining AST.

    Hoisted Raise/Set/release results are restored to the original expressions.
    All guards, timing constants, API operations, outputs and ownership remain.
    """
    class Strip(ast.NodeTransformer):
        def visit_ImportFrom(self, node):
            if any(alias.name == "write_diagnostic" for alias in node.names):
                return None
            return node

        def visit_Expr(self, node):
            if (isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute)
                    and isinstance(node.value.func.value, ast.Name) and node.value.func.value.id == "diag"):
                return None
            return self.generic_visit(node)

        def visit_Assign(self, node):
            target = node.targets[0]
            if ((isinstance(target, ast.Name) and target.id in ("trace", "command_trace", "diagnostic")) or
                    (isinstance(target, ast.Attribute) and target.attr == "diagnostic")):
                return None
            if isinstance(target, ast.Name) and target.id in ("raised", "set_result", "confirmation"):
                expected = {"raised": "self.event.Raise()", "set_result": 'parameter.Set(preview["proposed_value"])',
                            "confirmation": "confirm(preview)"}[target.id]
                if ast.dump(node.value) != ast.dump(ast.parse(expected, mode="eval").body):
                    raise AssertionError("Diagnostic hoist changed the underlying API call")
                return None
            if isinstance(target, ast.Name) and target.id in ("released", "delivered"):
                return ast.Expr(value=node.value)
            return self.generic_visit(node)

        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load) and node.id == "raised":
                return ast.parse("self.event.Raise()", mode="eval").body
            if isinstance(node.ctx, ast.Load) and node.id == "set_result":
                return ast.parse('parameter.Set(preview["proposed_value"])', mode="eval").body
            if isinstance(node.ctx, ast.Load) and node.id == "confirmation":
                return ast.parse("confirm(preview)", mode="eval").body
            return node

        def visit_Call(self, node):
            if isinstance(node.func, ast.Name) and node.func.id == "display":
                node.args = node.args[:2]
            return self.generic_visit(node)

        def visit_FunctionDef(self, node):
            node.decorator_list = [n for n in node.decorator_list if not (
                isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "diag")]
            if node.name == "display":
                node.args.args = node.args.args[:2]
                node.args.defaults = []
            return self.generic_visit(node)

        def visit_ExceptHandler(self, node):
            self.generic_visit(node)
            if isinstance(node.type, ast.Name) and node.type.id == "Exception":
                node.name = None
            return node

        def visit_If(self, node):
            self.generic_visit(node)
            return node if node.body else None

        def visit_Try(self, node):
            self.generic_visit(node)
            if not node.handlers and not node.finalbody:
                return node.body
            # display's diagnostic-only except logs then rethrows unchanged.
            if (len(node.handlers) == 1 and len(node.handlers[0].body) == 1 and
                    isinstance(node.handlers[0].body[0], ast.Raise) and not node.finalbody):
                return node.body
            return node
    return ast.dump(Strip().visit(ast.parse(source)), include_attributes=False)


class DiagnosticIntegration(unittest.TestCase):
    def setUp(self):
        self.c = coordinator_fixture.Coordination()
        self.c.setUp()
        self.addCleanup(self.c.tearDown)
        self.e = execution_fixture.Execution()
        self.e.setUp()
        self.c.f = self.e.f
        self.c.m.DB = self.e.f.db
        self.c.m.framework.Guid.Parse = lambda value: self.e.f.guid
        self.c.preview.clear()
        self.c.preview.update(self.e.preview)
        self.c.dialog.Show.return_value = "Confirm"
        self.temp = tempfile.TemporaryDirectory(prefix="m4a-diag-test-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "m4a_gate10c_diagnostic.jsonl"
        self.trace = d.Trace(str(self.path), time.monotonic)
        self.host = patch.object(d, "host_trace", return_value=self.trace)
        self.host.start()
        self.addCleanup(self.host.stop)
        self.ids = patch.object(self.c.m, "uuid4", return_value=N(hex="rid"))
        self.ids.start()
        self.addCleanup(self.ids.stop)

    def rows(self):
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines()]

    def markers(self):
        return [r["marker"] for r in self.rows()]

    def run_handler(self):
        self.c.owner.handler.Execute(self.e.f.app)

    def test_accepted_later_handler_commits_without_callback(self):
        self.c.invoke()
        self.e.tx.Commit.assert_not_called()
        self.assertNotIn("HANDLER_ENTERED", self.markers())
        self.run_handler()
        rows = self.rows()
        # Actual preserved order: ownership release precedes Dev output.
        expected = ["CONFIRM_ACCEPTED", "POST_CONFIRM_CONTEXT_VALID", "APPROVAL_REGISTERED",
                    "EXTERNAL_EVENT_RAISE_ATTEMPT", "EXTERNAL_EVENT_RAISE_RESULT",
                    "PUSHBUTTON_RETURN_AFTER_ACCEPTED", "HANDLER_ENTERED",
                    "PENDING_REQUEST_CONSUMED", "EXECUTOR_ENTERED",
                    "EXECUTION_REVALIDATION_STARTED", "REVALIDATION_RESULT",
                    "TRANSACTION_START_RESULT", "PARAMETER_SET_RESULT",
                    "TRANSACTION_COMMIT_RESULT", "POST_COMMIT_REREAD", "VERIFICATION_RESULT",
                    "EXECUTOR_RESULT_CREATED", "COMPLETION_CREATED", "COMPLETION_CALLBACK_STATE",
                    "COMPLETION_DELIVERED", "OWNER_RELEASED", "DEV_OUTPUT_ATTEMPT",
                    "DEV_OUTPUT_RESULT", "HANDLER_EXITED"]
        position = -1
        for marker in expected:
            position = self.markers().index(marker, position + 1)
        self.assertTrue(all(row["request_id"] == "rid" for row in rows[1:]))
        self.assertEqual(next(r["raise_result"] for r in rows if r["marker"] == "EXTERNAL_EVENT_RAISE_RESULT"), "Accepted")
        self.assertFalse(next(r["callback_present"] for r in rows if r["marker"] == "COMPLETION_CALLBACK_STATE"))
        self.assertTrue(self.c.owner.completion_sink.delivered)
        self.assertIsNone(self.c.owner.admission.active)
        self.e.tx.Commit.assert_called_once()
        self.e.f.parameter.Set.assert_called_once()
        self.assertEqual(self.e.value, "M4A_Write_01")
        self.assertEqual(self.c.output.print_html.call_count, 2)

    def test_nonaccepted_raise_has_exact_enum_and_no_handler(self):
        for status in ("Pending", "Denied"):
            with self.subTest(status=status):
                self.c.event.Raise.return_value = status
                self.c.invoke()
                row = [r for r in self.rows() if r["marker"] == "EXTERNAL_EVENT_RAISE_RESULT"][-1]
                self.assertEqual(row["raise_result"], status)
                self.assertNotIn("HANDLER_ENTERED", self.markers())
                self.assertIsNone(self.c.owner.pending)
                self.assertIn("EXTERNAL_EVENT_NOT_ACCEPTED", self.path.read_text())
        self.e.tx.Start.assert_not_called()

    def test_no_pending_handler_records_early_return(self):
        self.c.owner.diagnostic = self.trace
        self.run_handler()
        self.assertIn("HANDLER_PENDING_STATE", self.markers())
        self.assertIn("NO_PENDING_REQUEST", self.path.read_text())
        self.assertEqual(self.markers()[-1], "HANDLER_EXITED")
        self.assertNotIn("EXECUTOR_ENTERED", self.markers())

    def test_running_handler_records_early_return(self):
        self.c.owner.diagnostic = self.trace
        self.c.owner.running = True
        self.run_handler()
        self.assertIn("ALREADY_RUNNING", self.path.read_text())
        self.e.tx.Start.assert_not_called()

    def test_execution_time_stale_rejection(self):
        self.c.invoke()
        self.c.session.selection_generation += 1
        self.run_handler()
        row = next(r for r in self.rows() if r["marker"] == "REVALIDATION_RESULT")
        self.assertEqual(row["reason_code"], "STALE_CONTEXT")
        self.assertFalse(row["passed"])
        self.assertIn("COMPLETION_CREATED", self.markers())
        self.e.tx.Start.assert_not_called()

    def test_execution_time_expired_rejection(self):
        self.c.invoke()
        with patch.object(self.c.m, "clock", return_value=71):
            self.run_handler()
        row = next(r for r in self.rows() if r["marker"] == "REVALIDATION_RESULT")
        self.assertEqual(row["reason_code"], "CONFIRMATION_EXPIRED")
        self.e.tx.Start.assert_not_called()

    def test_before_value_revalidation_rejection(self):
        self.c.invoke()
        self.e.value = "Changed"
        self.run_handler()
        row = next(r for r in self.rows() if r["marker"] == "REVALIDATION_CHECK" and not r["passed"])
        self.assertEqual(row["check"], "before_value")
        self.assertIn("PRECONDITION_CHANGED", self.path.read_text())
        self.e.tx.Start.assert_not_called()

    def test_output_failure_does_not_erase_committed_receipt(self):
        self.c.invoke()
        self.c.output.print_html.side_effect = RuntimeError("output unavailable")
        # Preserve the existing second-emit exception behavior, not a runtime fix.
        with self.assertRaises(RuntimeError):
            self.run_handler()
        self.e.tx.Commit.assert_called_once()
        self.e.tx.RollBack.assert_not_called()
        self.assertEqual(self.e.value, "M4A_Write_01")
        rows = self.rows()
        result = next(r for r in rows if r["marker"] == "EXECUTOR_RESULT_CREATED")
        self.assertEqual(result["reason_code"], "COMPLETE")
        self.assertTrue(result["transaction_committed"])
        self.assertTrue(result["verification_passed"])
        self.assertTrue(self.c.owner.completion_sink.delivered)
        self.assertTrue(all(not r["success"] for r in rows if r["marker"] == "DEV_OUTPUT_RESULT" and r.get("classification") == "MEP_PARAMETER_WRITE_OK"))
        self.assertEqual(self.markers()[-1], "HANDLER_EXITED")

    def test_broken_diagnostic_sink_cannot_prevent_commit(self):
        self.trace.emit = Mock(side_effect=OSError("diagnostic unavailable"))
        self.c.invoke()
        self.run_handler()
        self.e.tx.Commit.assert_called_once()
        self.assertTrue(self.c.owner.completion_sink.delivered)
        self.assertEqual(self.c.output.print_html.call_count, 2)

    def test_cancel_does_not_manufacture_execution_markers(self):
        self.c.dialog.Show.return_value = "Cancel"
        self.c.invoke()
        self.assertIn("CONFIRM_REJECTED", self.markers())
        self.assertNotIn("CONFIRM_ACCEPTED", self.markers())
        self.assertNotIn("EXECUTOR_ENTERED", self.markers())

    def test_dialog_failure_does_not_claim_shown_or_accepted(self):
        self.c.dialog.Show.side_effect = RuntimeError("dialog")
        self.c.invoke()
        self.assertIn("CONFIRM_DIALOG_ATTEMPT", self.markers())
        self.assertNotIn("CONFIRM_DIALOG_SHOWN", self.markers())
        self.assertNotIn("CONFIRM_ACCEPTED", self.markers())
        self.e.tx.Start.assert_not_called()

    def test_set_exception_is_observed_without_retry(self):
        self.c.invoke()
        self.e.f.parameter.Set.side_effect = RuntimeError("sensitive arbitrary data")
        self.run_handler()
        self.assertIn("PARAMETER_SET_ATTEMPT", self.markers())
        self.assertNotIn("PARAMETER_SET_RESULT", self.markers())
        self.assertNotIn("sensitive arbitrary data", self.path.read_text())
        self.assertIn("PARAMETER_SET_FAILED", self.path.read_text())
        self.e.f.parameter.Set.assert_called_once()
        self.e.tx.RollBack.assert_called_once()

    def test_callback_invocation_does_not_enable_dev_sink(self):
        with patch.object(d, "host_trace") as create_trace:
            self.c.dialog.Show.return_value = "Cancel"
            self.c.owner.invoke(self.c.f.app, self.c.forms, self.c.output, Mock())
        create_trace.assert_not_called()
        self.assertIsNone(self.c.owner.diagnostic)
        self.assertFalse(self.path.exists())


class DiagnosticSink(unittest.TestCase):
    def test_append_utf8_allowlist_and_redacted_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.jsonl"
            trace = d.Trace(str(path), lambda: 1.5)
            d.bind(trace, "r1")
            d.record(trace, "TEST", {"provider_payload": "never-log", "current_value": "omit"}, reason_code="COMPLETE")
            d.exception(trace, "test", ValueError("never-log"))
            rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["request_id"], "r1")
            self.assertEqual(rows[0]["monotonic_seconds"], 1.5)
            self.assertTrue(rows[0]["timestamp_utc"].endswith("Z"))
            self.assertNotIn("never-log", path.read_text())
            self.assertNotIn("current_value", rows[0])

    def test_unwritable_sink_and_clock_failure_are_swallowed(self):
        with tempfile.TemporaryDirectory() as directory:
            trace = d.Trace(directory, lambda: 1)
            d.record(trace, "TEST")
            trace.monotonic = Mock(side_effect=RuntimeError("clock"))
            d.record(trace, "TEST")

    def test_executor_mutation_count_and_timer(self):
        path = Path(__file__).resolve().parents[1] / "AI.extension/lib/bimcode_write_execution.py"
        source = path.read_text()
        tree = ast.parse(source)
        calls = [n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
        self.assertEqual(calls.count("Transaction"), 1)
        self.assertEqual(calls.count("Set"), 1)
        self.assertIn("now - request.created > 60.0", source)

    def test_contract_comparison_detects_semantic_change(self):
        path = Path(__file__).resolve().parents[1] / "AI.extension/lib/bimcode_write_execution.py"
        source = path.read_text()
        self.assertNotEqual(diagnostic_contract_ast(source),
                            diagnostic_contract_ast(source.replace("> 60.0", "> 120.0")))
        with self.assertRaises(AssertionError):
            diagnostic_contract_ast(source.replace('parameter.Set(preview["proposed_value"])', 'parameter.Set("Other")'))


if __name__ == "__main__":
    unittest.main()
