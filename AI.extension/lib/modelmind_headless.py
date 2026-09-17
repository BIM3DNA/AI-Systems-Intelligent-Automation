"""M2A: private, serialized reuse of closed selection builders.

PRECONDITION: call execute_headless_modelmind_readonly ONLY from a supported
Revit API callback/command (M2B must use ExternalEvent.Execute). A valid document
is not proof of API context. This module does not schedule work or make arbitrary
WPF/background calls safe. No pane integration is supplied in M2A.

The private module is compiled once, not imported as an interactive Workbench.
Its explicit bootstrap flag never enters the interactive module or environment.
No WPF object is allocated: headless OllamaAIChat has object as its base, and
object.__new__ bypasses __init__. The audited builder closure uses NO instance
fields, only methods. No fields are injected. Tests enforce this invariant.
"""

import math
import os
import threading
import types
from contextlib import contextmanager


_MODULE = None
_EXECUTION_LOCK = threading.Lock()
_SPECS = (
    ("PIPING", "PIPING_RO_001_ACTION_METADATA", "_piping_ro_001_build_data"),
    ("HVAC", "HVAC_RO_001_ACTION_METADATA", "_hvac_ro_001_build_data"),
    ("ELECTRICAL", "ELECTRICAL_RO_001_ACTION_METADATA", "_electrical_ro_001_build_data"),
)
SUPPORTED_ACTIONS = tuple(
    "{0}-RO-001-A{1:02d}".format(specialty, number)
    for specialty, _, __ in _SPECS for number in range(1, 5)
)
# Only presentation data already constructed by production; never raw records.
_RESULT_FIELDS = (
    "feature_id", "feature_name", "action_id", "canonical_prompt", "report_id",
    "timestamp", "document_title", "active_view_name", "active_view_type",
    "classification", "reason_code", "selected_reference_count",
    "resolved_selected_count", "summary", "tables", "piping_checks",
    "hvac_checks", "electrical_checks", "generic_checks", "warnings",
    "warning_records", "warnings_total", "warning_display_truncated",
    "connector_rows_truncated", "next_guidance",
)
try:
    _TEXT_TYPES = (str, unicode)
    _INTEGER_TYPES = (int, long)
except NameError:
    _TEXT_TYPES = (str,)
    _INTEGER_TYPES = (int,)


class ProjectionError(ValueError):
    pass


def project_value(value):
    """Copy only exact built-in scalars/containers; never stringify an object.

    Tuples become lists (production tables use tuples). No sorting, truncation,
    findings or classification changes. Transport bounds fail explicitly rather
    than silently modifying a domain result. Element IDs in production tables
    are already scalar; raw ElementId/CLR collections are deliberately rejected.
    """
    budget = [100000, 2000000]

    def copy(item, depth):
        budget[0] -= 1
        if budget[0] < 0 or depth > 16:
            raise ProjectionError("Result exceeds transport structural limit")
        kind = type(item)
        if item is None or kind is bool or kind in _INTEGER_TYPES:
            if kind in _INTEGER_TYPES and item.bit_length() > 64:
                raise ProjectionError("Integer exceeds transport limit")
            return item
        if kind is float:
            if math.isnan(item) or math.isinf(item):
                raise ProjectionError("Non-finite result number")
            return item
        if kind in _TEXT_TYPES:
            budget[1] -= len(item)
            if len(item) > 8192 or budget[1] < 0:
                raise ProjectionError("Result exceeds transport text limit")
            return item
        if kind in (list, tuple):
            if len(item) > budget[0]:
                raise ProjectionError("Result exceeds transport structural limit")
            return [copy(child, depth + 1) for child in item]
        if kind is dict:
            if len(item) * 2 > budget[0]:
                raise ProjectionError("Result exceeds transport structural limit")
            result = {}
            for key, child in item.items():
                if type(key) not in _TEXT_TYPES:
                    raise ProjectionError("Non-string result key")
                result[copy(key, depth + 1)] = copy(child, depth + 1)
            return result
        raise ProjectionError("Non-serialization-safe result value")

    return copy(value, 0)


def _load_backend():
    """Called under the execution lock. No sys.modules/sys.path/env flag writes."""
    global _MODULE
    if _MODULE is None:
        path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "AI.tab", "Dev.panel",
            "AI_01.pushbutton", "script.py"))
        module = types.ModuleType("_modelmind_headless_backend")
        module.__file__ = path
        module._MODELMIND_HEADLESS_BOOTSTRAP = True
        with open(path, "rb") as source:
            code = compile(source.read(), path, "exec")
        # Execute the trusted local module, never a prompt or user-provided code.
        exec(code, module.__dict__)
        if module.OllamaAIChat.__bases__ != (object,):
            raise RuntimeError("Headless backend must not construct a CLR/WPF base")
        _MODULE = module
    return _MODULE


@contextmanager
def _document_context(module, document, uidocument):
    previous = module.doc, module.uidoc
    module.doc, module.uidoc = document, uidocument
    try:
        yield
    finally:
        module.doc, module.uidoc = previous


def _failure(action_id, code):
    # Infrastructure error, NOT a replacement ModelMind/domain classification.
    return {"ok": False, "action_id": action_id, "error_code": code}


def resolve_headless_modelmind_specialty(document, uidocument):
    """M2B routing only, in API context. Reuse closed canonical predicates.

    No semantic evaluation, filtering of the eventual builder selection, or raw
    object output. Uses the same serialized/scoped bootstrap as M2A execution.
    """
    if not _EXECUTION_LOCK.acquire(False):
        return _failure(None, "EXECUTION_BUSY")
    try:
        if (document is None or uidocument is None or not document.IsValidObject
                or not uidocument.Document.Equals(document)):
            return _failure(None, "INVALID_DOCUMENT_CONTEXT")
        module = _load_backend()
        with _document_context(module, document, uidocument):
            worker = object.__new__(module.OllamaAIChat)
            specialties = set()
            unsupported = 0
            selected = 0
            for element_id in uidocument.Selection.GetElementIds():
                selected += 1
                element = document.GetElement(element_id)
                if element is None:
                    return _failure(None, "SELECTION_UNREADABLE")
                if worker._piping_ro_001_scope_kind(element) == "SUPPORTED_PIPE":
                    specialties.add("PIPING")
                elif worker._hvac_ro_001_scope_kind(element) == "SUPPORTED_DUCT":
                    specialties.add("HVAC")
                else:
                    _, profile = worker._electrical_ro_001_scope_kind(element)
                    if profile in ("DEVICE_PROFILE", "EQUIPMENT_PROFILE"):
                        specialties.add("ELECTRICAL")
                    else:
                        unsupported += 1
            return {"ok": True, "specialties": sorted(specialties),
                    "selected_count": selected, "unsupported_count": unsupported}
    except Exception:
        return _failure(None, "SELECTION_UNREADABLE")
    finally:
        _EXECUTION_LOCK.release()


def execute_headless_modelmind_readonly(action_id, document, uidocument):
    """Execute one of the 12 existing action IDs in the caller's Revit context.

    ok means builder + projection completed, NOT a healthy/ready model. Preserve
    production classification/reason_code, including NOT_READY and QA YELLOW.
    Nested/concurrent calls fail immediately. Serialization does not make Revit
    API access thread-safe. The caller must satisfy the API-context precondition.
    Only the isolated module's globals are bound; no interactive runtime changes.
    """
    if type(action_id) not in _TEXT_TYPES or action_id not in SUPPORTED_ACTIONS:
        return _failure(None, "UNSUPPORTED_ACTION")
    if not _EXECUTION_LOCK.acquire(False):
        return _failure(action_id, "EXECUTION_BUSY")
    try:
        if (document is None or uidocument is None or not document.IsValidObject
                or not uidocument.Document.Equals(document)):
            return _failure(action_id, "INVALID_DOCUMENT_CONTEXT")
        module = _load_backend()
        for specialty, metadata_name, builder_name in _SPECS:
            metadata = getattr(module, metadata_name)
            for action_key, (known_id, prompt) in metadata.items():
                if known_id != action_id:
                    continue
                with _document_context(module, document, uidocument):
                    worker = object.__new__(module.OllamaAIChat)
                    data = getattr(worker, builder_name)(prompt, action_key)
                    result = project_value(dict(
                        (key, data[key]) for key in _RESULT_FIELDS if key in data))
                result["ok"] = True
                result["specialty"] = specialty
                return result
        return _failure(action_id, "ACTION_METADATA_MISMATCH")
    except ProjectionError:
        return _failure(action_id, "RESULT_PROJECTION_FAILED")
    except Exception:
        # Never retain/re-export exception objects, traces, raw data or documents.
        return _failure(action_id, "HEADLESS_EXECUTION_FAILED")
    finally:
        _EXECUTION_LOCK.release()
