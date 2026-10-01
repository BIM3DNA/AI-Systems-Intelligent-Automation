"""Pure M4B state-machine probes, no provider or Revit execution."""
import pathlib
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "AI.extension/lib"))
from bimcode_ai_pane import provider_write as m
from bimcode_ai_pane import write_projection as p
from test_bimcode_write_projection import result

PREFIX = ("PROVIDER_INITIAL_REQUEST", "PROVIDER_TOOL_SELECTED", "WRITE_ARGUMENTS_VALIDATED", "HOST_PREVIEW_BUILDING")
CONFIRM = ("PREVIEW_READY", "AWAITING_HUMAN_CONFIRMATION", "WRITE_REQUEST_QUEUED", "WRITE_EXECUTING")
TAIL = ("HOST_RESULT_READY", "PROVIDER_CONTINUATION_PENDING", "PROVIDER_FINAL_RESPONSE_READY")


class Machine(unittest.TestCase):
    def identity(self):
        return m.correlation("logical1", "host1", "session1", "doc1", "resp1", "call1", "New")

    def run_path(self, states, data):
        identity = self.identity()
        request = m.new_request(identity, 0)
        receipt = p.freeze_result(data)
        for index, state in enumerate(states):
            host = receipt if state in ("WRITE_SUCCEEDED", "WRITE_FAILED", "WRITE_INDETERMINATE", "HOST_RESULT_READY") else None
            step = m.transition(request, identity, state, index + 1, "TEST_EVIDENCE", host_result=host)
            self.assertTrue(step.accepted, (state, step.reason))
            request = step.request
        return request

    def test_exact_states(self):
        expected = ('IDLE PROVIDER_INITIAL_REQUEST PROVIDER_TOOL_SELECTED WRITE_ARGUMENTS_VALIDATED HOST_PREVIEW_BUILDING '
                    'PREVIEW_NOT_READY PREVIEW_READY AWAITING_HUMAN_CONFIRMATION USER_CANCELLED APPROVAL_EXPIRED '
                    'WRITE_REQUEST_QUEUED WRITE_EXECUTING WRITE_SUCCEEDED WRITE_FAILED WRITE_INDETERMINATE HOST_RESULT_READY '
                    'PROVIDER_CONTINUATION_PENDING PROVIDER_CONTINUATION_FAILED PROVIDER_FINAL_RESPONSE_READY COMPLETED CANCELLED EXPIRED').split()
        self.assertEqual(set(expected), set(m.STATES))
        self.assertEqual(len(m.STATES), 22)

    def test_success(self):
        req = self.run_path(PREFIX + CONFIRM + ("WRITE_SUCCEEDED",) + TAIL + ("COMPLETED",), result())
        self.assertEqual(req.state, "COMPLETED")
        self.assertTrue(p.project_receipt(req.host_result)["verification_passed"])

    def test_cancel(self):
        req = self.run_path(PREFIX + CONFIRM[:2] + ("USER_CANCELLED",) + TAIL + ("CANCELLED",), result("CANCELLED", "USER_CANCELLED"))
        self.assertEqual(req.state, "CANCELLED")

    def test_expiry(self):
        req = self.run_path(PREFIX + CONFIRM[:2] + ("APPROVAL_EXPIRED",) + TAIL + ("EXPIRED",), result("NOT_READY", "CONFIRMATION_EXPIRED"))
        self.assertEqual(req.state, "EXPIRED")

    def test_preview_not_ready(self):
        self.run_path(PREFIX + ("PREVIEW_NOT_READY",) + TAIL + ("COMPLETED",), result("PREVIEW_NOT_READY", "NO_CHANGE_REQUIRED"))

    def test_failed(self):
        self.run_path(PREFIX + CONFIRM + ("WRITE_FAILED",) + TAIL + ("COMPLETED",), result("FAILED", "READ_FAILED"))

    def test_indeterminate_cleanup_retains_lock(self):
        data = result("INDETERMINATE", "TRANSACTION_PENDING")
        data.update(transaction_started=True, transaction_status="Pending", model_modified=None)
        req = self.run_path(PREFIX + CONFIRM + ("WRITE_INDETERMINATE",) + TAIL + ("COMPLETED",), data)
        self.assertFalse(m.cleanup_intent(req, "completed")["owner_release_required"])

    def test_provider_failure_preserves_success(self):
        req = self.run_path(PREFIX + CONFIRM + ("WRITE_SUCCEEDED", "HOST_RESULT_READY", "PROVIDER_CONTINUATION_PENDING",
                                              "PROVIDER_CONTINUATION_FAILED", "COMPLETED"), result())
        self.assertEqual(req.provider_status.status, "FAILED")
        self.assertEqual(p.project_receipt(req.host_result)["classification"], "MEP_PARAMETER_WRITE_OK")

    def test_forbidden_edges_exhaustively(self):
        original = m.new_request(self.identity(), 0)
        for source in m.STATES:
            for target in m.STATES:
                if target not in m.TRANSITIONS[source]:
                    request = original._replace(state=source)
                    step = m.transition(request, request.correlation, target, 1, "TEST")
                    self.assertFalse(step.accepted, (source, target))
                    self.assertIs(step.request, request)

    def test_duplicate_terminal_and_second_selection(self):
        req = self.run_path(PREFIX + CONFIRM + ("WRITE_SUCCEEDED",) + TAIL + ("COMPLETED",), result())
        for state in ("COMPLETED", "IDLE", "PROVIDER_TOOL_SELECTED", "WRITE_EXECUTING", "WRITE_FAILED"):
            self.assertEqual(m.transition(req, req.correlation, state, 99, "TEST").reason, "REQUEST_TERMINAL")

    def test_correlation_mismatch(self):
        req = m.new_request(self.identity(), 0)
        for field in req.correlation._fields:
            wrong = req.correlation._replace(**{field: "wrong"})
            self.assertEqual(m.transition(req, wrong, "PROVIDER_INITIAL_REQUEST", 1, "TEST").reason, "CORRELATION_MISMATCH")

    def test_history_determinism(self):
        states = PREFIX + ("PREVIEW_NOT_READY",) + TAIL + ("COMPLETED",)
        self.assertEqual(self.run_path(states, result("NOT_READY")), self.run_path(states, result("NOT_READY")))

    def test_cleanup_lifecycle_intents(self):
        req = self.run_path(PREFIX + CONFIRM, result())
        for trigger in ("pane_disposal", "document_close", "shutdown", "provider_continuation_failure"):
            intent = m.cleanup_intent(req, trigger)
            self.assertFalse(intent["owner_release_required"])
            self.assertFalse(intent["continuation_allowed"])
            self.assertTrue(intent["callback_invalidation_required"])

    def test_invalid_timestamps(self):
        req = m.new_request(self.identity(), 1)
        for stamp in (-1, 0, float('nan'), float('inf'), True):
            self.assertFalse(m.transition(req, req.correlation, "PROVIDER_INITIAL_REQUEST", stamp, "TEST").accepted)

    def test_premature_success_evidence_rejected(self):
        req = self.run_path(PREFIX + ("PREVIEW_NOT_READY",), result("NOT_READY"))
        self.assertEqual(m.transition(req, req.correlation, "HOST_RESULT_READY", 99, "TEST",
                                     p.freeze_result(result())).reason, "UNEXPECTED_EXECUTION_EVIDENCE")

    def test_success_before_host_result_is_rejected(self):
        req = self.run_path(PREFIX + CONFIRM, result())
        self.assertEqual(m.transition(req, req.correlation, "WRITE_SUCCEEDED", 99, "TEST").reason,
                         "HOST_OUTCOME_MISMATCH")

    def test_host_result_correlation_and_immutability(self):
        req = self.run_path(PREFIX + CONFIRM + ("WRITE_SUCCEEDED",), result())
        data = result(); data["request_id"] = "other"
        self.assertEqual(m.transition(req, req.correlation, "HOST_RESULT_READY", 99, "TEST", p.freeze_result(data)).reason, "HOST_REQUEST_MISMATCH")
        data = result(); data["before_value"] = "changed"
        self.assertEqual(m.transition(req, req.correlation, "HOST_RESULT_READY", 99, "TEST", p.freeze_result(data)).reason, "HOST_RESULT_IMMUTABLE")
