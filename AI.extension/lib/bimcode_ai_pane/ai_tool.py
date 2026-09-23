"""One-turn coordinator. Execution entry point belongs ONLY to ExternalEvent.

Never receives a model-supplied action ID; never queues API objects.
"""
import json
from modelmind_headless import execute_headless_modelmind_readonly, project_value, resolve_headless_modelmind_specialty
from bimcode_ai_pane.tools import document_key
from bimcode_ai_pane import provider_bridge
from bimcode_ai_pane.ai_tool_registry import ACTIONS, LABELS, SPECIALTIES

NAME = "summarize_selected_pipes"
ACTION = ACTIONS[NAME]  # Summary compatibility; execution uses validated turn action.
FIELDS = ("action_id", "specialty", "classification", "reason_code", "summary",
          "selected_reference_count", "resolved_selected_count", "piping_checks",
          "hvac_checks", "electrical_checks", "generic_checks", "warnings", "warning_records", "warnings_total",
          "warning_display_truncated", "connector_rows_truncated", "next_guidance", "tables")


def compact(data, expected_action=ACTION):
    """Copy domain fields unchanged; omit whole transport entries with disclosure."""
    data = project_value(data)
    if (expected_action not in LABELS or data.get("action_id") != expected_action
            or data.get("specialty") != SPECIALTIES[expected_action]):
        raise ValueError("unexpected result")
    result = dict((key, data[key]) for key in FIELDS if key in data)
    omitted = {}
    for key in ("warnings", "warning_records", "piping_checks", "hvac_checks", "electrical_checks", "generic_checks"):
        if isinstance(result.get(key), list) and len(result[key]) > 30:
            omitted[key] = len(result[key]) - 30
            result[key] = result[key][:30]
    tables = []
    rows_left = 40
    source_tables = result.get("tables", [])
    omitted_tables = []
    for index, (title, headers, rows) in enumerate(source_tables):
        # Share the existing row budget so early distributions cannot hide all
        # connector/assignment detail. Values/order within each table stay exact.
        slots = max(1, min(12, len(source_tables)) - index)
        allowance = (rows_left + slots - 1) // slots if index < 12 else 0
        shown = rows[:allowance]
        if index < 12:
            tables.append([title, headers, shown])
            rows_left -= len(shown)
        omitted["table_rows"] = omitted.get("table_rows", 0) + len(rows) - len(shown)
        if len(rows) > len(shown) or index >= 12:
            omitted_tables.append(dict(index=index, title=title, rows=len(rows) - len(shown)))
    if omitted_tables:
        omitted["tables"] = omitted_tables
    if "tables" in result:
        result["tables"] = tables
    result["transport_omissions"] = omitted
    # Optional table details may be omitted, never core summary/warnings/checks.
    if len(json.dumps(result, ensure_ascii=True, allow_nan=False)) > 80000 and "tables" in result:
        result.pop("tables")
        omitted["tables_field"] = True
        omitted["table_rows"] = sum(len(rows) for title, headers, rows in source_tables)
        omitted["tables"] = [dict(index=i, title=t, rows=len(r))
                             for i, (t, h, r) in enumerate(source_tables)]
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
        self.turn["action"] = ACTIONS[valid["tool_call"]["name"]]
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
            action = turn["action"]
            specialty = SPECIALTIES[action]
            # Never filter or orchestrate a mixed selection. Empty selection and
            # supported + ordinary unsupported retain the closed builder report.
            specialties = scope.get("specialties") or []
            if (specialties and specialties != [specialty]) or (
                    not specialties and scope.get("unsupported_count", 0)):
                self.complete(provider_bridge.failure(rid, "AI_TOOL_NOT_ALLOWED"), None)
                return
            data = execute_headless_modelmind_readonly(action, uidoc.Document, uidoc)
            if not data.get("ok"):
                self.complete(provider_bridge.failure(rid, "MODELMIND_EXECUTION_FAILED"), None)
                return
            payload = compact(data, action)
        except Exception:
            self.complete(provider_bridge.failure(rid, "MODELMIND_EXECUTION_FAILED"), None)
            return
        self.complete(None, payload)
