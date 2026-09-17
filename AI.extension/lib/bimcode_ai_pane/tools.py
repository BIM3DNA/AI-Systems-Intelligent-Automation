"""Framework-neutral M2B requests, routing policy and bounded presentation.

execute() requires Revit API context; begin()/render_result() perform no API reads.
No Document, UIDocument or element is retained in this module or request records.
"""

from modelmind_headless import (
    execute_headless_modelmind_readonly, resolve_headless_modelmind_specialty,
    project_value,
)

TOOLS = {
    "selection.summary": ("Selection Summary", "A01"),
    "selection.connectors": ("Connectors", "A02"),
    "selection.system_assignment": ("System Assignment", "A03"),
    "selection.qa_health": ("QA Health", "A04"),
}
MAX_TEXT = 16000


def document_key(uiapp):
    """API callback only. Runtime identity supplemented by lifecycle generation.

    Generation invalidates requests across every activation/open/create/close,
    including switch-away-and-back and reopening the same model. Hash is never
    the sole stale-context guard. Failure to read identity fails closed.
    """
    try:
        uidoc = uiapp.ActiveUIDocument
        if uidoc is None or not uidoc.Document.IsValidObject:
            return None
        doc = uidoc.Document
        return (int(doc.GetHashCode()), doc.Title, doc.PathName)
    except Exception:
        return None


def result_for(request, status, reason, specialty=None):
    return {"request_id": request["request_id"], "tool_name": request["tool_name"],
            "action_id": request["action_id"], "status": status,
            "specialty": specialty, "reason_code": reason}


class ModelMindToolBridge(object):
    def __init__(self):
        self.pending = None
        self._sequence = 0

    def begin(self, tool_name, key, generation):
        if self.pending is not None or tool_name not in TOOLS:
            return None
        self._sequence += 1
        self.pending = {"request_id": self._sequence, "tool_name": tool_name,
                        "action_id": None, "document_key": key,
                        "generation": generation}
        return self.pending

    def clear(self):
        self.pending = None

    def execute(self, request, uiapp, generation):
        # Only the dedicated ExternalEvent handler calls this method.
        if (request["generation"] != generation
                or request["document_key"] != document_key(uiapp)):
            return result_for(request, "STALE_CONTEXT", "DOCUMENT_OR_VIEW_TRANSITION")
        if request["document_key"] is None:
            return result_for(request, "NOT_READY", "NO_VALID_DOCUMENT_CONTEXT")
        uidoc = uiapp.ActiveUIDocument
        doc = uidoc.Document
        scope = resolve_headless_modelmind_specialty(doc, uidoc)
        if not scope.get("ok"):
            code = scope.get("error_code", "ROUTING_FAILED")
            return result_for(request, "BUSY" if code == "EXECUTION_BUSY" else "FAILED", code)
        specialties = scope["specialties"]
        if not scope["selected_count"]:
            return result_for(request, "NOT_READY", "NO_ELEMENTS_SELECTED")
        if not specialties:
            return result_for(request, "NOT_READY", "NO_SUPPORTED_SELECTED_ELEMENTS")
        if len(specialties) != 1:
            return result_for(request, "MIXED_SPECIALTY_REVIEW", "MIXED_SUPPORTED_SPECIALTIES", "mixed")
        specialty = specialties[0]
        if scope["unsupported_count"]:
            return result_for(request, "NOT_READY", "SUPPORTED_AND_UNSUPPORTED_SELECTION", specialty)
        request["action_id"] = "{0}-RO-001-{1}".format(specialty, TOOLS[request["tool_name"]][1])
        data = execute_headless_modelmind_readonly(request["action_id"], doc, uidoc)
        if not data.get("ok"):
            code = data.get("error_code", "EXECUTION_FAILED")
            return result_for(request, "BUSY" if code == "EXECUTION_BUSY" else "FAILED", code, specialty)
        classification = data.get("classification", "")
        status = "OK"
        if classification.endswith("_NOT_READY"):
            status = "NOT_READY"
        elif classification.endswith("_FAILED"):
            status = "FAILED"
        elif classification.endswith("_PARTIAL"):
            status = "PARTIAL"
        result = result_for(request, status, data.get("reason_code"), specialty)
        result["classification"] = classification
        result["data"] = data
        return project_value(result)


def render_result(result):
    """Only serialization-safe input. Bounded text, never dict/object reprs."""
    try:
        result = project_value(result)
        data = result.get("data") or {}
        text_types = (str, type(u""))

        def scalar(value):
            if isinstance(value, text_types):
                return value[:600]
            if isinstance(value, (list, dict)):
                return "[structured field omitted]"
            # project_value already rejected every non-scalar object. Includes
            # IronPython long IDs/counts without traversing raw CLR properties.
            return "" if value is None else str(value)

        label = TOOLS.get(result.get("tool_name"), ("ModelMind", None))[0]
        lines = ["Tool: " + label, "Status: " + scalar(result.get("status")),
                 "Specialty: " + scalar(result.get("specialty") or "none"),
                 "Classification: " + scalar(result.get("classification") or "not available"),
                 "Reason: " + scalar(result.get("reason_code")), "", "Summary"]
        summaries = data.get("summary") or []
        lines.extend(scalar(item) for item in summaries[:30])
        if len(summaries) > 30:
            lines.append("[Additional summary lines omitted from pane]")
        lines.extend(["", "Warnings"])
        warnings = data.get("warnings") or data.get("warning_records") or []
        for item in warnings[:20]:
            if isinstance(item, dict):
                lines.append(" | ".join(scalar(item[key]) for key in sorted(item)))
            else:
                lines.append(scalar(item))
        if not warnings:
            lines.append("None reported" if data else "Not evaluated")
        if len(warnings) > 20 or data.get("warning_display_truncated"):
            lines.append("[Additional warnings omitted from pane/production display]")
        rows_left = 40
        for title, headers, rows in (data.get("tables") or [])[:12]:
            if not rows_left:
                lines.append("[Additional table rows omitted from pane]")
                break
            lines.extend(["", scalar(title), " | ".join(scalar(v) for v in headers[:16])])
            shown = rows[:rows_left]
            for row in shown:
                lines.append(" | ".join(scalar(v) for v in row[:16]))
            rows_left -= len(shown)
            if len(rows) > len(shown):
                lines.append("[Additional table rows omitted from pane]")
        if len(data.get("tables") or []) > 12:
            lines.append("[Additional tables omitted from pane]")
        text = "\n".join(lines)
        if len(text) > MAX_TEXT:
            marker = "\n[Pane text truncated; production result unchanged]"
            text = text[:MAX_TEXT - len(marker)] + marker
        return text
    except Exception:
        return "Status: FAILED\nReason: Invalid presentation payload"
