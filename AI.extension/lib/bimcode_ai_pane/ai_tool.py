"""One-turn coordinator. Execution entry point belongs ONLY to ExternalEvent.

Never receives a model-supplied action ID; never queues API objects.
"""
import json
from modelmind_headless import execute_headless_modelmind_readonly, project_value, resolve_headless_modelmind_specialty
from bimcode_ai_pane.tools import document_key
from bimcode_ai_pane import provider_bridge

NAME = "summarize_selected_pipes"
ACTION = "PIPING-RO-001-A01"
FIELDS = ("action_id", "specialty", "classification", "reason_code", "summary",
          "selected_reference_count", "resolved_selected_count", "piping_checks",
          "generic_checks", "warnings", "warning_records", "warnings_total",
          "warning_display_truncated", "tables")


def compact(data):
    """Copy domain fields unchanged; omit whole transport entries with disclosure."""
    data = project_value(data)
    if data.get("action_id") != ACTION or data.get("specialty") != "PIPING":
        raise ValueError("unexpected result")
    result = dict((key, data[key]) for key in FIELDS if key in data)
    omitted = {}
    for key in ("warnings", "warning_records", "piping_checks", "generic_checks"):
        if isinstance(result.get(key), list) and len(result[key]) > 30:
            omitted[key] = len(result[key]) - 30
            result[key] = result[key][:30]
    tables = []
    rows_left = 40
    for title, headers, rows in result.get("tables", []):
        shown = rows[:rows_left] if len(tables) < 12 else []
        if shown:
            tables.append([title, headers, shown])
            rows_left -= len(shown)
        omitted["table_rows"] = omitted.get("table_rows", 0) + len(rows) - len(shown)
    if "tables" in result:
        result["tables"] = tables
    result["transport_omissions"] = omitted
    # Never clip a fact mid-value. Drop optional whole fields, then fail closed.
    for key in ("tables", "warning_records", "warnings", "piping_checks", "generic_checks"):
        if len(json.dumps(result, ensure_ascii=True, allow_nan=False)) <= 80000:
            break
        if key in result:
            result.pop(key)
            omitted[key + "_field"] = True
    if len(json.dumps(result, ensure_ascii=True, allow_nan=False)) > 80000:
        raise ValueError("transport limit")
    return result


class Coordinator(object):
    def __init__(self, session):
        self.session = session
        self.turn = None
        self.pending = False
        self.callback = None

    def begin(self, request_id):
        if self.turn is not None or self.session.tools.pending is not None:
            return False
        self.turn = dict(request_id=request_id, key=self.session.document_identity,
                         generation=self.session.context_generation,
                         selection=self.session.selection_generation, used=False)
        return True

    def clear(self):
        self.turn = None
        self.pending = False
        self.callback = None

    def queue(self, response, callback):
        rid = response.get("request_id")
        valid = provider_bridge.decode_tool(response, rid)
        if not valid["ok"]:
            callback(valid, None)
            return
        if self.turn is None or self.turn["request_id"] != rid:
            callback(provider_bridge.failure(rid, "AI_TOOL_PROTOCOL_ERROR"), None)
            return
        if self.turn["used"]:
            callback(provider_bridge.failure(rid, "AI_TOOL_LOOP_LIMIT"), None)
            return
        self.turn["used"] = True
        self.callback = callback
        self.pending = True
        try:
            if not self.session.raise_ai_event():
                self.complete(provider_bridge.failure(rid, "MODELMIND_NOT_READY"), None)
        except Exception:
            self.complete(provider_bridge.failure(rid, "MODELMIND_NOT_READY"), None)

    def complete(self, error, data):
        callback = self.callback
        self.pending = False
        self.callback = None
        if callback is not None:
            try:
                callback(error, data)
            except Exception:
                # A disposed WPF host must never escape into Revit dispatch.
                self.clear()

    def execute_approved(self, uiapp):
        # Called solely inside ModelMindReadOnlyHandler.Execute, never a worker.
        if not self.pending or self.turn is None:
            return
        self.pending = False  # consume before execution, even on exception
        turn = self.turn
        rid = turn["request_id"]
        try:
            session = self.session
            if (turn["key"] != document_key(uiapp)
                    or turn["generation"] != session.context_generation
                    or turn["selection"] != session.selection_generation):
                self.complete(provider_bridge.failure(rid, "STALE_CONTEXT"), None)
                return
            if turn["key"] is None:
                self.complete(provider_bridge.failure(rid, "MODELMIND_NOT_READY"), None)
                return
            uidoc = uiapp.ActiveUIDocument
            scope = resolve_headless_modelmind_specialty(uidoc.Document, uidoc)
            if not scope.get("ok"):
                self.complete(provider_bridge.failure(rid, "MODELMIND_NOT_READY"), None)
                return
            # Do not silently reinterpret a selected Duct/Electrical request as
            # Piping. Other empty/unsupported/mixed cases still belong to A01.
            if scope.get("specialties") and "PIPING" not in scope["specialties"]:
                self.complete(provider_bridge.failure(rid, "AI_TOOL_NOT_ALLOWED"), None)
                return
            data = execute_headless_modelmind_readonly(ACTION, uidoc.Document, uidoc)
            if not data.get("ok"):
                self.complete(provider_bridge.failure(rid, "MODELMIND_EXECUTION_FAILED"), None)
                return
            payload = compact(data)
        except Exception:
            self.complete(provider_bridge.failure(rid, "MODELMIND_EXECUTION_FAILED"), None)
            return
        self.complete(None, payload)
