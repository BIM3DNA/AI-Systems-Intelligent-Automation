"""Offline authoritative host evidence and UI contracts; no runtime calls."""
import json
import pathlib
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "AI.extension/lib"))
from bimcode_ai_pane import write_projection as p
from bimcode_ai_pane import write_contracts as c


def result(kind="OK", reason="COMPLETE"):
    success = kind == "OK"
    return dict(feature_id=c.M4A_FEATURE_ID, action_id=c.M4A_ACTION_ID, request_id="host1",
                classification="MEP_PARAMETER_WRITE_" + kind, reason_code=reason,
                target_category=c.M4A_CATEGORY, target_element_id=123, target_unique_id="unique1",
                parameter_display_name=c.M4A_TEST_PARAMETER_NAME, parameter_guid=c.M4A_TEST_PARAMETER_GUID,
                before_has_value=False, before_value=None, proposed_value="New", final_value="New" if success else None,
                confirmation_result="CONFIRMED" if success else "NOT_CONFIRMED", transaction_started=success,
                transaction_committed=success, transaction_status="Committed" if success else "NOT_STARTED",
                model_modified=success, verification_performed=success, verification_passed=success,
                warnings=[], timestamp="2026-10-01T12:00:00Z")


class Projections(unittest.TestCase):
    def test_required_fields_and_serialization(self):
        data = result()
        receipt = p.freeze_result(data)
        self.assertEqual(receipt, p.freeze_result(dict(reversed(list(data.items())))))
        output = p.project_receipt(receipt)
        self.assertTrue(set(p.FIELDS).issubset(output))
        self.assertEqual(json.loads(json.dumps(output)), output)
        self.assertLessEqual(len(receipt.json), p.MAX_OUTPUT)

    def test_immutable_and_dropped_unknown_data(self):
        data = result()
        data.update(instructions=object(), exception=ValueError("secret"), nested={"x": object()})
        receipt = p.freeze_result(data)
        data["classification"] = "fake"
        output = p.project_receipt(receipt)
        output["warnings"].append("edited")
        self.assertEqual(p.project_receipt(receipt)["warnings"], [])
        self.assertNotIn("instructions", output)
        with self.assertRaises(AttributeError):
            receipt.json = "changed"

    def test_warning_budget(self):
        data = result()
        data["warnings"] = [ValueError("raw"), "Traceback (most recent call last):", "bad\nstack"] + ["x" * 1000] * 40
        projected = p.project_receipt(p.freeze_result(data))
        self.assertEqual(len(projected["warnings"]), 30)
        self.assertEqual(projected["warning_omitted_count"], 13)
        self.assertEqual(projected["warning_truncated_count"], 30)
        self.assertTrue(all(len(w) == 256 for w in projected["warnings"]))

    def test_unicode_null_and_budget(self):
        data = result()
        data["before_value"] = "\u03bb" * 256
        data["warnings"] = ["\u03bb" * 256] * 30
        encoded = p.freeze_result(data).json
        self.assertTrue(encoded.isascii())
        self.assertLessEqual(len(encoded), p.MAX_OUTPUT)
        self.assertEqual(p.project_receipt(p.Receipt(encoded))["before_value"], data["before_value"])

    def test_invalid_shape_core_objects_and_limits(self):
        for field, value in (("before_value", "x" * 257), ("final_value", object()),
                             ("warnings", None), ("classification", "UNKNOWN"),
                             ("target_element_id", True), ("transaction_started", 1),
                             ("before_value", "\ud800")):
            data = result(); data[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                p.freeze_result(data)
        with self.assertRaises(ValueError):
            p.freeze_result({})

    def test_nonexecution_cases(self):
        for kind, reason in (("NOT_READY", "NO_CHANGE_REQUIRED"), ("CANCELLED", "USER_CANCELLED"),
                             ("NOT_READY", "CONFIRMATION_EXPIRED"), ("NOT_READY", "STALE_CONTEXT"),
                             ("NOT_READY", "PRECONDITION_CHANGED"), ("PREVIEW_NOT_READY", "NO_VALID_DOCUMENT")):
            data = p.project_receipt(p.freeze_result(result(kind, reason)))
            self.assertFalse(data["model_modified"])
            self.assertFalse(data["transaction_started"])
            self.assertEqual(data["reason_code"], reason)

    def test_failed_and_indeterminate(self):
        for kind in ("FAILED", "INDETERMINATE"):
            data = result(kind, "TRANSACTION_PENDING")
            if kind == "INDETERMINATE":
                data.update(model_modified=None, transaction_status="Pending", transaction_started=True)
            receipt = p.freeze_result(data)
            view = p.provenance(receipt, p.explanation("COMPLETE", message="It succeeded"))
            self.assertNotEqual(view["status"], "COMPLETE")
            self.assertEqual(view["host_status"]["classification"], data["classification"])

    def test_verification_failure_does_not_rollback(self):
        data = result(); data.update(classification="MEP_PARAMETER_WRITE_FAILED", reason_code="VERIFICATION_FAILED",
                                     verification_passed=False, final_value="Wrong")
        view = p.provenance(p.freeze_result(data))
        self.assertEqual(view["verification"], "FAIL")
        self.assertEqual(view["transaction"], "Committed")
        self.assertTrue(view["model_modified"])
        self.assertNotEqual(view["status"], "COMPLETE")

    def test_explanation_independent(self):
        receipt = p.freeze_result(result())
        for status in p.EXPLANATION_STATES:
            view = p.provenance(receipt, p.explanation(status))
            self.assertEqual(view["status"], "COMPLETE")
            self.assertEqual(view["provider_status"]["status"], status)
            self.assertEqual(view["host_status"], p.project_receipt(receipt))

    def test_preview_adapter_and_before_confirmation(self):
        data = result("PREVIEW_OK")
        data.update(current_value=None, current_has_value=False)
        receipt = p.from_preview(data)
        view = p.provenance(receipt, phase="AWAITING_HUMAN_CONFIRMATION")
        self.assertEqual(view["confirmation"], "REQUIRED")
        self.assertFalse(view["model_modified"])
        self.assertNotEqual(view["status"], "COMPLETE")

    def test_contradictions_rejected(self):
        for change in (dict(transaction_committed=False), dict(verification_passed=False),
                       dict(final_value="different"), dict(model_modified=False)):
            data = result(); data.update(change)
            with self.assertRaises(ValueError):
                p.freeze_result(data)

    def test_host_adapter_category_unknown(self):
        data = result(); del data["target_category"]
        self.assertIsNone(p.project_receipt(p.from_host_result(data))["target_category"])
