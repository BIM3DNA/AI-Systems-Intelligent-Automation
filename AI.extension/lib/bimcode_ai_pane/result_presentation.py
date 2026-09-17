"""Scalar domain result -> bounded presentation blocks. No domain evaluation.

Promotions select existing summary lines/distribution cells; they never sum,
infer missing zeros, merge states, or inspect Revit objects. Details retain all
available fields in source order (dictionary fields use stable key order) until
the explicit display limit. The input and M2A projection are never modified.
"""

from modelmind_headless import project_value
from bimcode_ai_pane.tools import TOOLS, MAX_TEXT

NOTICE = "Additional details omitted by pane display limit."
WARNING_NOTICE = "Additional warnings omitted by pane display limit."
MAX_BLOCKS = 400
TEXT_TYPES = (str, type(u""))


def _text(value):
    if value is None:
        return "none"
    if isinstance(value, TEXT_TYPES):
        return value
    if isinstance(value, (list, dict)):
        return "[structured value; see Details]"
    return str(value)


def _leaves(value, label=""):
    if isinstance(value, dict):
        if not value:
            yield label, "{}"
        for key in sorted(value):
            for item in _leaves(value[key], label + "." + key if label else key):
                yield item
    elif isinstance(value, list):
        if not value:
            yield label, "[]"
        for index, child in enumerate(value):
            for item in _leaves(child, "{0}[{1}]".format(label, index + 1)):
                yield item
    else:
        yield label, _text(value)


class _Budget(object):
    def __init__(self):
        self.remaining = MAX_TEXT - len(NOTICE) - len(WARNING_NOTICE) - 4
        self.count = 0
        self.truncated = False

    def add(self, group, kind, text, label="", tone="PrimaryTextBrush"):
        # Two characters account for the WPF paragraph terminator. All labels,
        # bullet markers and headings are counted, not just domain cell text.
        text, label = _text(text), _text(label)
        if kind == "bullet":
            label = u"\u2022 " + label
        cost = len(text) + len(label) + 2
        if self.count >= MAX_BLOCKS - 2 or self.remaining <= 2:
            self.truncated = True
            return False
        if cost > self.remaining:
            self.truncated = True
            joined = (label + text)[:self.remaining - 2]
            label, text = "", joined
            cost = len(text) + 2
        group.append(dict(kind=kind, text=text, label=label, tone=tone))
        self.remaining -= cost
        self.count += 1
        return not self.truncated


def _facts(data, extra):
    prefixes = ("Total selected references:", "Supported rigid", "Supported electrical elements:",
                "Supported pipes processed:", "Supported ducts processed:",
                "Supported elements processed:", "Unsupported or unresolved selected references:") + extra
    return [line for line in (data.get("summary") or [])
            if isinstance(line, TEXT_TYPES) and line.startswith(prefixes)]


def _summary(data):
    return _facts(data, ("Total readable",)), (
        "Pipe type distribution", "Duct type distribution", "Shape distribution",
        "System assignment distribution", "Profile distribution")


def _connectors(data):
    return _facts(data, ("Total raw connector count:", "Physical piping connector count:",
        "Physical HVAC connector count:", "Physical End connector count:",
        "Reciprocally connected physical connector count:",
        "Unconnected physical connector count:", "Unreadable connector count:",
        "Connectors analyzed:")), ("Connector applicability distribution",)


def _assignment(data):
    return _facts(data, ()), ("System assignment state distribution",
        "Profile-specific assignment distribution", "System name distribution",
        "System classification distribution")


def _qa(data):
    return _facts(data, ("Deterministic issue count:", "Partial check count:",
        "Generic parameter-read error elements:", "Stable piping checks evaluated:",
        "Stable HVAC checks evaluated:", "Stable electrical checks evaluated:")), ()


ADAPTERS = {"selection.summary": _summary, "selection.connectors": _connectors,
            "selection.system_assignment": _assignment, "selection.qa_health": _qa}


def _status_tone(status, classification):
    if status == "FAILED" or classification.endswith("_FAILED"):
        return "ErrorBrush"
    if status in ("PARTIAL", "MIXED_SPECIALTY_REVIEW", "BUSY") or classification.endswith(("_PARTIAL", "_YELLOW")):
        return "WarningBrush"
    if status == "OK":
        return "SuccessBrush"
    return "SecondaryTextBrush"


def build_presentation(result):
    """Returns only presentation blocks; no new domain classification namespace."""
    try:
        source = project_value(result)
    except Exception:
        source = {"status": "FAILED", "reason_code": "Invalid presentation payload"}
    if not isinstance(source, dict):
        source = {"status": "NOT_READY", "reason_code": "Unsupported presentation payload", "value": source}
    raw_data = source.get("data")
    data = raw_data if isinstance(raw_data, dict) else {}
    budget = _Budget()
    header, warnings, facts, sections, details = [], [], [], [], []
    add = budget.add
    tool = source.get("tool_name")
    title = TOOLS.get(tool, ("ModelMind", None))[0] if isinstance(tool, TEXT_TYPES) else "ModelMind"
    status = _text(source.get("status", "NOT_READY"))
    classification = _text(source.get("classification") or data.get("classification") or "")
    reason = _text(source.get("reason_code") or data.get("reason_code") or "")
    add(header, "title", title)
    if source.get("specialty"):
        add(header, "metadata", _text(source["specialty"]) + (u" \u00b7 " + reason if reason else ""), tone="AccentBrush")
    add(header, "status", status.replace("_", " "), tone=_status_tone(status, classification))
    if classification:
        add(header, "technical", classification, tone="SecondaryTextBrush")
    if reason:
        add(header, "technical", reason, "Reason: ", "SecondaryTextBrush")
    if reason == "NO_ELEMENTS_SELECTED":
        add(header, "text", "No elements selected.")

    # Reserve warnings BEFORE optional promotions/details, but render them after
    # the high-value sections. Never silently swallow warning overflow.
    warning_groups = [(key, data.get(key)) for key in ("warnings", "warning_records") if data.get(key)]
    warning_overflow = False
    if warning_groups:
        add(warnings, "heading", "Warnings", tone="WarningBrush")
        for key, values in warning_groups:
            for label, text in _leaves(values):
                if not add(warnings, "bullet", text, label + ": " if label else "", "WarningBrush"):
                    warning_overflow = True
                    break
        if data.get("warning_display_truncated"):
            add(warnings, "note", "Additional warnings omitted by production display limit.", tone="WarningBrush")
            warning_overflow = warning_overflow or budget.truncated
    else:
        add(warnings, "heading", "Warnings")
        add(warnings, "text", "None reported" if not data.get("warning_display_truncated") else "Additional warnings omitted by production display limit.")

    summary, promoted = ADAPTERS.get(tool, _summary)(data) if isinstance(tool, TEXT_TYPES) else ([], ())
    if summary:
        add(facts, "heading", "Summary")
        for line in summary:
            label, separator, value = line.partition(":")
            if not add(facts, "fact", value.strip(), label + ": " if separator else ""):
                break
    tables = data.get("tables") or []
    for table in tables:
        if not isinstance(table, list) or len(table) != 3:
            continue
        title, headers, rows = table
        if title not in promoted or not isinstance(headers, list) or not isinstance(rows, list):
            continue
        add(sections, "heading", "Systems" if title == "System name distribution" else title)
        for row in rows:
            if not isinstance(row, list):
                continue
            # Existing distribution Count cell only; never count detail rows or
            # infer absent states as zero. Original table retained below.
            if "Count" in headers and row and len(row) > headers.index("Count"):
                if not add(sections, "fact", _text(row[headers.index("Count")]), _text(row[0]) + ": "):
                    break

    if data and reason != "NO_ELEMENTS_SELECTED":
        add(details, "heading", "Details")
        for label, text in _leaves(data.get("summary", []), "Summary"):
            if not add(details, "text", text, label + ": "):
                break
        for table in tables:
            if budget.remaining <= 2 or budget.count >= MAX_BLOCKS - 2:
                budget.truncated = True
                break
            if not isinstance(table, list) or len(table) != 3:
                for label, text in _leaves(table, "Table"):
                    if not add(details, "technical", text, label + ": "):
                        break
                continue
            title, headers, rows = table
            add(details, "subheading", _text(title))
            if not rows:
                add(details, "technical", ", ".join(_text(name) for name in headers), "Columns: ")
                add(details, "note", "No rows.", tone="SecondaryTextBrush")
            for index, row in enumerate(rows):
                if not isinstance(row, list) or not isinstance(headers, list):
                    for label, text in _leaves(row, "Row"):
                        if not add(details, "technical", text, label + ": "):
                            break
                    continue
                if len(headers) <= 3 and len(row) == len(headers) and all(not isinstance(v, (list, dict)) for v in row):
                    compact = u"  |  ".join(_text(name) + ": " + _text(value) for name, value in zip(headers, row))
                    if not add(details, "text", compact):
                        break
                    continue
                identifier = next((i for i, name in enumerate(headers) if name in ("Pipe id", "Duct id", "Element id")), None)
                row_title = "Record {0}".format(index + 1)
                if identifier is not None and identifier < len(row):
                    row_title = headers[identifier].replace(" id", "") + " " + _text(row[identifier])
                if not add(details, "record", row_title):
                    break
                for column, value in enumerate(row):
                    label = _text(headers[column]) if column < len(headers) else "Column {0}".format(column + 1)
                    for nested_label, text in _leaves(value, label):
                        if not add(details, "technical", text, nested_label + ": "):
                            break
                # Do not conceal headers for missing cells in unexpected payloads.
                for name in headers[len(row):]:
                    add(details, "technical", "[cell unavailable]", _text(name) + ": ")
        for key in sorted(data):
            if key in ("summary", "tables", "warnings", "warning_records"):
                continue
            for label, text in _leaves(data[key], key):
                if not add(details, "technical", text, label + ": "):
                    break
    for key in sorted(source):
        if key in ("data", "classification", "reason_code", "specialty", "status", "tool_name"):
            continue
        for label, text in _leaves(source[key], key):
            if not add(details, "technical", text, label + ": "):
                break
    if raw_data is not None and not isinstance(raw_data, dict):
        for label, text in _leaves(raw_data, "Data"):
            if not add(details, "technical", text, label + ": "):
                break
    if warning_overflow:
        warnings.append(dict(kind="note", text=WARNING_NOTICE, label="", tone="WarningBrush"))
    blocks = header + facts + sections + warnings + details
    if budget.truncated:
        blocks.append(dict(kind="note", text=NOTICE, label="", tone="WarningBrush"))
    return {"blocks": blocks, "truncated": budget.truncated,
            "character_count": sum(len(b["text"]) + len(b["label"]) + 2 for b in blocks)}
