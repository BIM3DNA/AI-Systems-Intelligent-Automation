"""Host-only M4A executor. Called exclusively by the write ExternalEvent.

Preview module remains transaction-free. This module has no provider imports.
"""
import json
from collections import namedtuple
from datetime import datetime

from bimcode_ai_pane import write_contracts as c
from bimcode_write_runtime import capture_preview_context, resolve_target, resolve_parameter, PreviewBlocked

TRANSACTION_NAME = "BIMCode M4A Set Test Text"
Request = namedtuple("Request", "preview_json epochs created confirmed")


def freeze(preview, epochs, created, confirmed):
    if preview["classification"] != c.PREVIEW_OK or preview["reason_code"] != "COMPLETE":
        raise ValueError("Preview is not executable")
    return Request(json.dumps(preview, sort_keys=True, ensure_ascii=True), tuple(epochs), created, confirmed)


def result_for(preview, kind, reason):
    return dict(feature_id=c.M4A_FEATURE_ID, action_id=c.M4A_ACTION_ID,
                request_id=preview.get("request_id"), classification="MEP_PARAMETER_WRITE_" + kind,
                reason_code=reason, document_identity=preview.get("document_identity"),
                target_element_id=preview.get("target_element_id"),
                target_unique_id=preview.get("target_unique_id"), parameter_guid=c.M4A_TEST_PARAMETER_GUID,
                parameter_display_name=c.M4A_TEST_PARAMETER_NAME,
                before_value=preview.get("current_value"), before_has_value=preview.get("current_has_value"),
                proposed_value=preview.get("proposed_value"), final_value=None,
                confirmation_result="NOT_CONFIRMED", transaction_started=False,
                transaction_status="NOT_STARTED", transaction_committed=False, model_modified=False,
                verification_performed=False, verification_passed=False, warnings=[],
                timestamp=datetime.utcnow().isoformat() + "Z")


def _mark(result, kind, reason):
    result.update(classification="MEP_PARAMETER_WRITE_" + kind, reason_code=reason)
    return result


class Executor(object):
    """Own at most one transaction, including unresolved failure processing."""
    def __init__(self):
        self.retained = None
        self.used = set()

    def revalidate(self, uiapp, preview, db, guid):
        context = capture_preview_context(uiapp)
        if context.get("reason"):
            raise PreviewBlocked("STALE_CONTEXT")
        if context["metadata"]["document_identity"] != preview["document_identity"]:
            raise PreviewBlocked("STALE_CONTEXT")
        doc = context["doc"]
        element = doc.GetElement(db.ElementId(preview["target_element_id"]))
        if element is None or not element.IsValidObject:
            raise PreviewBlocked("TARGET_MISSING")
        if element.UniqueId != preview["target_unique_id"]:
            raise PreviewBlocked("TARGET_CHANGED")
        if (context["metadata"] != preview["selection_snapshot"] or
                context["fingerprint"] != preview["selection_fingerprint"]):
            raise PreviewBlocked("STALE_CONTEXT")
        doc, uidoc, selected = resolve_target(uiapp, db, context)
        if selected.UniqueId != element.UniqueId:
            raise PreviewBlocked("TARGET_CHANGED")
        type_id = selected.GetTypeId()
        if (int(type_id.Value) != preview["pipe_type"]["element_id"] or
                doc.GetElement(type_id).UniqueId != preview["pipe_type"]["unique_id"]):
            raise PreviewBlocked("PRECONDITION_CHANGED")
        if preview["parameter_guid"] != c.M4A_TEST_PARAMETER_GUID:
            raise PreviewBlocked("PARAMETER_IDENTITY_MISMATCH")
        parameter = resolve_parameter(doc, selected, db, guid)
        if (parameter.AsString() != preview["current_value"] or
                bool(parameter.HasValue) != preview["current_has_value"]):
            raise PreviewBlocked("PRECONDITION_CHANGED")
        return doc, selected, parameter

    def verify(self, doc, preview, result, db, guid):
        result.update(transaction_committed=True, model_modified=True,
                      verification_performed=True, transaction_status="Committed")
        try:
            element = doc.GetElement(db.ElementId(preview["target_element_id"]))
            if element is None or element.UniqueId != preview["target_unique_id"]:
                raise ValueError("Target identity changed")
            parameter = resolve_parameter(doc, element, db, guid)
            result["final_value"] = parameter.AsString()
            if result["final_value"] != preview["proposed_value"]:
                raise ValueError("Verification mismatch")
            result["verification_passed"] = True
            return _mark(result, "OK", "COMPLETE")
        except Exception:
            result["warnings"].append("Transaction committed; inspect the model or use manual Undo. No compensation attempted.")
            return _mark(result, "FAILED", "VERIFICATION_FAILED")

    def execute(self, request, uiapp, epochs, now, db, guid):
        preview = json.loads(request.preview_json)
        result = result_for(preview, "NOT_READY", "STALE_CONTEXT")
        result["confirmation_result"] = "CONFIRMED"
        if self.retained is not None:
            return _mark(result, "NOT_READY", "EXECUTION_BUSY")
        if preview["request_id"] in self.used:
            return _mark(result, "NOT_READY", "CONFIRMATION_INVALID")
        if len(self.used) >= 1000:
            return _mark(result, "NOT_READY", "EXECUTION_BUSY")
        self.used.add(preview["request_id"])
        if tuple(epochs) != request.epochs:
            return result
        if now < request.confirmed or now - request.created > 60.0:
            return _mark(result, "NOT_READY", "CONFIRMATION_EXPIRED")
        if not c.validate_value(preview.get("proposed_value"))["valid"]:
            return _mark(result, "NOT_READY", "INVALID_VALUE")
        try:
            doc, element, parameter = self.revalidate(uiapp, preview, db, guid)
        except PreviewBlocked as error:
            return _mark(result, "NOT_READY", error.reason)
        except Exception:
            return _mark(result, "FAILED", "READ_FAILED")
        tx = None
        phase = "TRANSACTION_START_FAILED"
        try:
            tx = db.Transaction(doc, TRANSACTION_NAME)
            self.retained = (tx, doc, preview, result)
            start = tx.Start()
            result["transaction_status"] = str(start)
            if start != db.TransactionStatus.Started:
                return self.settle(db, guid, phase)
            result["transaction_started"] = True
            options = tx.GetFailureHandlingOptions()
            options.SetForcedModalHandling(True)
            tx.SetFailureHandlingOptions(options)
            phase = "PARAMETER_SET_FAILED"
            if not parameter.Set(preview["proposed_value"]):
                return self.settle(db, guid, phase)
            phase = "TRANSACTION_COMMIT_FAILED"
            status = tx.Commit()
            result["transaction_status"] = str(status)
            if status == db.TransactionStatus.Committed and tx.GetStatus() == status:
                result = self.verify(doc, preview, result, db, guid)
                tx.Dispose()
                self.retained = None
                return result
            return self.settle(db, guid, phase)
        except Exception:
            if tx is None:
                return _mark(result, "FAILED", phase)
            return self.settle(db, guid, phase)

    def settle(self, db, guid, reason):
        """No retry. Roll back only Started; retain Pending/unknown ownership."""
        tx, doc, preview, result = self.retained
        try:
            status = tx.GetStatus()
            result["transaction_status"] = str(status)
            if status == db.TransactionStatus.Started:
                result["transaction_started"] = True
                status = tx.RollBack()
                result["transaction_status"] = str(status)
                if status != db.TransactionStatus.RolledBack or tx.GetStatus() != status:
                    result["model_modified"] = None
                    return _mark(result, "INDETERMINATE", "ROLLBACK_UNCONFIRMED")
            if status == db.TransactionStatus.Pending:
                result["model_modified"] = None
                return _mark(result, "INDETERMINATE", "TRANSACTION_PENDING")
            if status == db.TransactionStatus.Committed:
                # Exception/contradictory return is not evidence of rollback or success.
                result.update(transaction_committed=True, model_modified=True)
                _mark(result, "FAILED", reason)
            elif status in (db.TransactionStatus.RolledBack, db.TransactionStatus.Uninitialized):
                result["model_modified"] = False
                _mark(result, "FAILED", reason)
            else:
                result["model_modified"] = None
                return _mark(result, "INDETERMINATE", "TRANSACTION_STATUS_UNKNOWN")
            tx.Dispose()
            self.retained = None
            return result
        except Exception:
            result["model_modified"] = None
            return _mark(result, "INDETERMINATE", "ROLLBACK_UNCONFIRMED")

    def check_pending(self, db, guid):
        """Explicit human status check only; never Start, Set, Commit or rollback."""
        tx, doc, preview, result = self.retained
        try:
            status = tx.GetStatus()
            result["transaction_status"] = str(status)
            if status == db.TransactionStatus.Committed:
                result = self.verify(doc, preview, result, db, guid)
            elif status == db.TransactionStatus.RolledBack:
                result["model_modified"] = False
                _mark(result, "FAILED", "TRANSACTION_COMMIT_FAILED")
            else:
                return _mark(result, "INDETERMINATE", "TRANSACTION_PENDING")
            tx.Dispose()
            self.retained = None
            return result
        except Exception:
            return _mark(result, "INDETERMINATE", "TRANSACTION_STATUS_UNKNOWN")
