"""TEMPORARY M4A-DIAG-001. Human Dev diagnostics; never a provider sink.

Remove this helper and its call sites after GATE-10C diagnosis. No Revit API,
stdout, environment dump, result payload, or arbitrary exception text is logged.
"""
import io
import json
import os
from datetime import datetime
from functools import wraps

FIELDS = frozenset((
    "request_id", "target_element_id", "parameter_guid", "selection_generation",
    "context_generation", "model_epoch", "approved_context_generation",
    "approved_selection_generation", "approved_model_epoch", "elapsed_seconds",
    "raise_result", "running", "pending_present", "resolving", "classification",
    "reason_code", "transaction_status", "transaction_started", "transaction_committed",
    "model_modified", "verification_performed", "verification_passed", "stage",
    "check", "passed", "callback_present", "delivered", "error", "released",
    "exception_type", "exception_message", "success", "set_result"))


class Trace(object):
    def __init__(self, path, monotonic):
        self.path = path
        self.monotonic = monotonic
        self.request_id = None

    def emit(self, marker, data=None, **fields):
        # Entire sink including field conversion/clock/open is best effort.
        try:
            row = dict(marker=marker, timestamp_utc=datetime.utcnow().isoformat() + "Z",
                       monotonic_seconds=self.monotonic(), request_id=self.request_id,
                       feature_id="MEP-PARAM-WR-001", action_id="MEP-PARAM-WR-001-A01",
                       owner="HUMAN_DEV_WRITE", diagnostic="M4A-DIAG-001")
            values = dict(data or {})
            values.update(fields)
            for key in FIELDS:
                if key in values:
                    value = values[key]
                    if value is None and key == "request_id":
                        continue
                    if value is None or isinstance(value, (bool, int, float)):
                        row[key] = value
                    elif isinstance(value, type(u"")) or isinstance(value, str):
                        row[key] = value[:160]
            with io.open(self.path, "a", encoding="utf-8") as stream:
                stream.write(u"{}\n".format(json.dumps(row, sort_keys=True, ensure_ascii=True)))
        except Exception:
            pass


def host_trace():
    """Only the human coordinator opts in. CPython/offline callers default off."""
    try:
        from System.IO import Path
        from System.Diagnostics import Stopwatch
        return Trace(os.path.join(str(Path.GetTempPath()), "m4a_gate10c_diagnostic.jsonl"),
                     lambda: float(Stopwatch.GetTimestamp()) / Stopwatch.Frequency)
    except Exception:
        return None


def record(trace, marker, data=None, **fields):
    try:
        if trace is not None:
            trace.emit(marker, data, **fields)
    except Exception:
        pass


def bind(trace, request_id):
    try:
        if trace is not None:
            trace.request_id = request_id
    except Exception:
        pass


def exception(trace, stage, error):
    # Exception text can contain arbitrary API/model/credential data. Intentionally
    # redact it completely rather than relying on a partial secret-pattern filter.
    try:
        record(trace, "EXCEPTION", stage=stage, exception_type=type(error).__name__,
               exception_message="[redacted; exception type and stage retained]")
    except Exception:
        pass


def raised(trace, value):
    try:
        record(trace, "EXTERNAL_EVENT_RAISE_RESULT", raise_result=str(value))
    except Exception:
        pass


def state(owner, marker, **fields):
    try:
        record(getattr(owner, "diagnostic", None), marker,
               running=owner.running, pending_present=owner.pending is not None,
               resolving=owner.resolving, **fields)
    except Exception:
        pass


def executor_result(function):
    """Observe every existing return without rewriting guards or result objects."""
    @wraps(function)
    def observed(self, request, uiapp, epochs, now, db, guid):
        trace = getattr(self, "diagnostic", None)
        record(trace, "EXECUTOR_ENTERED")
        try:
            record(trace, "EXECUTION_REVALIDATION_STARTED", elapsed_seconds=now - request.created,
                   context_generation=epochs[0], selection_generation=epochs[1], model_epoch=epochs[2],
                   approved_context_generation=request.epochs[0],
                   approved_selection_generation=request.epochs[1], approved_model_epoch=request.epochs[2])
        except Exception:
            pass
        try:
            result = function(self, request, uiapp, epochs, now, db, guid)
        except Exception as error:
            exception(trace, "executor", error)
            raise
        record(trace, "EXECUTOR_RESULT_CREATED", result)
        return result
    return observed
