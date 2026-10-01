"""Pure M4B receipt/provenance contracts. No provider or Revit integration."""
import json
from collections import namedtuple
from bimcode_ai_pane import write_contracts as c

MAX_STRING = 256
MAX_WARNINGS = 30
MAX_WARNING_LENGTH = 256
MAX_OUTPUT = 80000  # ASCII JSON characters (also UTF-8 bytes).
Receipt = namedtuple("Receipt", "json")
Explanation = namedtuple("Explanation", "status response_id error_classification message timestamp")
EXPLANATION_STATES = ("NOT_STARTED", "PENDING", "COMPLETE", "FAILED", "UNAVAILABLE")
CLASSIFICATIONS = tuple("MEP_PARAMETER_WRITE_" + kind for kind in
                        ("NOT_READY", "CANCELLED", "OK", "FAILED", "INDETERMINATE",
                         "PREVIEW_NOT_READY", "PREVIEW_FAILED", "PREVIEW_OK"))
TEXT_FIELDS = ("feature_id", "action_id", "request_id", "classification", "reason_code",
               "target_category", "target_unique_id", "parameter_display_name", "parameter_guid",
               "before_value", "proposed_value", "final_value", "confirmation_result",
               "transaction_status", "timestamp")
FLAGS = ("transaction_started", "transaction_committed", "model_modified",
         "verification_performed", "verification_passed", "before_has_value")
FIELDS = TEXT_FIELDS + FLAGS + ("target_element_id", "warnings")
try:
    integer_types = (int, long)
except NameError:
    integer_types = (int,)


def _text(value, nullable=True):
    if value is None and nullable:
        return value
    if (not isinstance(value, c.string_types) or len(value) > MAX_STRING or
            any(ord(ch) < 32 or 0xD800 <= ord(ch) <= 0xDFFF for ch in value)):
        raise ValueError("INVALID_RESULT_TEXT")
    return value


def explanation(status="NOT_STARTED", response_id=None, error_classification=None,
                message=None, timestamp=None):
    if status not in EXPLANATION_STATES:
        raise ValueError("INVALID_EXPLANATION_STATUS")
    return Explanation(status, *[_text(v) for v in
                       (response_id, error_classification, message, timestamp)])


def _serialize(data):
    encoded = json.dumps(data, sort_keys=True, ensure_ascii=True, allow_nan=False,
                         separators=(",", ":"))
    if len(encoded) > MAX_OUTPUT:
        raise ValueError("RESULT_BUDGET_EXCEEDED")
    return encoded


def freeze_result(result):
    """Whitelist and validate authoritative host evidence, never repair its truth.

    Core strings are rejected rather than truncated. Only warnings may be omitted.
    Unknown keys (including instructions/exception/stack payloads) are never read.
    Warning text is untrusted data, never an instruction to an execution path.
    """
    if type(result) is not dict or any(k not in result for k in FIELDS):
        raise ValueError("INVALID_RESULT_SHAPE")
    data = dict((key, _text(result[key])) for key in TEXT_FIELDS)
    for key in ("request_id", "reason_code", "timestamp"):
        if not data[key]:
            raise ValueError("MISSING_PROVENANCE")
    if (data["feature_id"] != c.M4A_FEATURE_ID or data["action_id"] != c.M4A_ACTION_ID or
            data["parameter_guid"] != c.M4A_TEST_PARAMETER_GUID or
            data["parameter_display_name"] != c.M4A_TEST_PARAMETER_NAME or
            data["target_category"] not in (None, c.M4A_CATEGORY)):
        raise ValueError("RESULT_IDENTITY_MISMATCH")
    if data["classification"] not in CLASSIFICATIONS:
        raise ValueError("UNKNOWN_CLASSIFICATION")
    for key in FLAGS:
        value = result[key]
        if type(value) is not bool and not (value is None and key in ("model_modified", "before_has_value")):
            raise ValueError("INVALID_RESULT_FLAG")
        data[key] = value
    target = result["target_element_id"]
    if target is not None and (type(target) not in integer_types or not 0 < target < 2 ** 63):
        raise ValueError("INVALID_TARGET_ID")
    data["target_element_id"] = target
    if data["confirmation_result"] not in ("NOT_CONFIRMED", "CONFIRMED", "REQUIRED"):
        raise ValueError("INVALID_CONFIRMATION")
    if data["transaction_status"] not in ("NOT_STARTED", "Started", "Committed", "RolledBack",
                                           "Pending", "Unknown", "Uninitialized", "Error"):
        raise ValueError("INVALID_TRANSACTION_STATUS")
    committed = data["transaction_committed"]
    if committed and (data["transaction_status"] != "Committed" or data["model_modified"] is not True):
        raise ValueError("CONTRADICTORY_COMMIT")
    if data["transaction_status"] == "Committed" and not committed:
        raise ValueError("CONTRADICTORY_COMMIT")
    if data["verification_passed"] and not (committed and data["verification_performed"]):
        raise ValueError("CONTRADICTORY_VERIFICATION")
    if (data["transaction_status"] in ("RolledBack", "NOT_STARTED", "Uninitialized") and data["model_modified"] is not False
            and not (data["classification"] == "MEP_PARAMETER_WRITE_INDETERMINATE" and data["model_modified"] is None)):
        raise ValueError("CONTRADICTORY_TRANSACTION")
    if data["reason_code"] == "VERIFICATION_FAILED" and not (
            committed and data["verification_performed"] and not data["verification_passed"] and
            data["classification"] == "MEP_PARAMETER_WRITE_FAILED"):
        raise ValueError("CONTRADICTORY_VERIFICATION_FAILURE")
    if data["classification"] == "MEP_PARAMETER_WRITE_OK":
        if not (data["reason_code"] == "COMPLETE" and committed and data["transaction_started"] and
                data["verification_passed"] and data["confirmation_result"] == "CONFIRMED" and
                data["final_value"] == data["proposed_value"] and c.validate_value(data["proposed_value"])["valid"]):
            raise ValueError("UNPROVEN_SUCCESS")
    if data["classification"] in (c.PREVIEW_OK, c.PREVIEW_NOT_READY, c.PREVIEW_FAILED,
                                    "MEP_PARAMETER_WRITE_NOT_READY", "MEP_PARAMETER_WRITE_CANCELLED"):
        if any(data[k] for k in ("transaction_started", "transaction_committed", "verification_performed",
                                "verification_passed")) or data["model_modified"] is not False or data["transaction_status"] != "NOT_STARTED":
            raise ValueError("CONTRADICTORY_NONEXECUTION")
    if data["classification"] == "MEP_PARAMETER_WRITE_CANCELLED" and data["confirmation_result"] != "NOT_CONFIRMED":
        raise ValueError("CONTRADICTORY_CANCELLATION")
    if type(result["warnings"]) not in (list, tuple):
        raise ValueError("INVALID_WARNINGS")
    warnings, omitted, truncated = [], 0, 0
    for warning in result["warnings"]:
        if (len(warnings) >= MAX_WARNINGS or not isinstance(warning, c.string_types) or
                "Traceback (" in warning or " at Autodesk." in warning or
                any(ord(ch) < 32 or 0xD800 <= ord(ch) <= 0xDFFF for ch in warning)):
            omitted += 1
            continue
        if len(warning) > MAX_WARNING_LENGTH:
            truncated += 1
        warnings.append(warning[:MAX_WARNING_LENGTH])
    data.update(warnings=warnings, warning_omitted_count=omitted, warning_truncated_count=truncated)
    return Receipt(_serialize(data))


def project_receipt(receipt):
    """Fresh scalar copy; caller edits cannot mutate the immutable receipt."""
    if type(receipt) is not Receipt or not isinstance(receipt.json, c.string_types) or len(receipt.json) > MAX_OUTPUT:
        raise ValueError("INVALID_RECEIPT")
    data = json.loads(receipt.json)
    # Revalidate even a manually constructed namedtuple. Preserve original omission counts.
    checked = json.loads(freeze_result(data).json)
    for key in ("warning_omitted_count", "warning_truncated_count"):
        value = data.get(key)
        if type(value) not in integer_types or value < 0:
            raise ValueError("INVALID_OMISSION_COUNT")
        checked[key] = value
    if _serialize(checked) != receipt.json:
        raise ValueError("NONCANONICAL_RECEIPT")
    return checked


def from_host_result(result):
    """Pure adapter for closed M4A result_for output; absent category stays unknown."""
    if type(result) is not dict:
        raise ValueError("INVALID_RESULT_SHAPE")
    data = dict(result)
    data.setdefault("target_category", None)
    return freeze_result(data)


def from_preview(preview):
    """Explicit nonexecution adapter. Never upgrades preview to write success."""
    if type(preview) is not dict or preview.get("classification") not in (c.PREVIEW_OK, c.PREVIEW_NOT_READY, c.PREVIEW_FAILED):
        raise ValueError("INVALID_PREVIEW")
    if preview.get("transaction_started") is not False or preview.get("model_modified") is not False:
        raise ValueError("INVALID_PREVIEW_FLAGS")
    data = dict(preview)
    data.update(before_value=preview.get("current_value"), before_has_value=preview.get("current_has_value"),
                final_value=None, confirmation_result="REQUIRED" if preview["classification"] == c.PREVIEW_OK else "NOT_CONFIRMED",
                transaction_started=False, transaction_committed=False, transaction_status="NOT_STARTED",
                model_modified=False, verification_performed=False, verification_passed=False)
    return freeze_result(data)


def provenance(receipt, provider_status=None, phase="HOST_RESULT_READY"):
    host = project_receipt(receipt)
    provider_status = provider_status or explanation()
    if type(provider_status) is not Explanation:
        raise ValueError("INVALID_EXPLANATION")
    explanation(*provider_status)  # Validate even caller-built namedtuple.
    success = (host["classification"] == "MEP_PARAMETER_WRITE_OK" and
               phase in ("WRITE_SUCCEEDED", "HOST_RESULT_READY", "PROVIDER_CONTINUATION_PENDING",
                         "PROVIDER_CONTINUATION_FAILED", "PROVIDER_FINAL_RESPONSE_READY", "COMPLETED"))
    before = phase in ("PREVIEW_READY", "AWAITING_HUMAN_CONFIRMATION")
    if before and host["classification"] != c.PREVIEW_OK:
        raise ValueError("INVALID_PREVIEW_PROVENANCE")
    return dict(tool_requested="Set Selected Pipe Test Text", safety_class="CONTROLLED_WRITE",
                safety_label="CONTROLLED WRITE", action_id=host["action_id"],
                target=host["target_element_id"], parameter=host["parameter_display_name"],
                before_value=host["before_value"], proposed_value=host["proposed_value"], final_value=host["final_value"],
                confirmation="REQUIRED" if before else host["confirmation_result"],
                transaction=host["transaction_status"], model_modified=host["model_modified"],
                verification=("PASS" if host["verification_passed"] else
                              "FAIL" if host["verification_performed"] else "NOT_PERFORMED"),
                status="AWAITING_HUMAN_CONFIRMATION" if before else "COMPLETE" if success else host["classification"],
                host_authoritative=True, host_status=host, provider_status=provider_status._asdict())
