"""M3F fixed Summary composition. API callback only; no scheduling or mutation."""
import json
import time
import modelmind_headless as backend

ACTION = "MEP-MULTI-RO-001-A01"
PLAN = (
    ("PIPING", "PIPING_RO_001_ACTION_METADATA", "_piping_ro_001_build_from_snapshot"),
    ("HVAC", "HVAC_RO_001_ACTION_METADATA", "_hvac_ro_001_build_from_snapshot"),
    ("ELECTRICAL", "ELECTRICAL_RO_001_ACTION_METADATA", "_electrical_ro_001_build_from_snapshot"),
)


def size(value):
    return len(json.dumps(value, ensure_ascii=True, allow_nan=False))


def envelope(request_id):
    return dict(ok=True, feature_id="MEP-MULTI-RO-001", action_id=ACTION,
                specialty="MEP", request_id=request_id, timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                document_title=None, active_view_name=None, active_view_type=None,
                classification="MEP_MULTI_SELECTION_NOT_READY", reason_code="NO_ELEMENTS_SELECTED",
                selected_reference_count=None, resolved_selected_count=None,
                supported_reference_count=None, supported_specialty_count=0,
                unsupported_reference_count=None, unresolved_reference_count=None,
                partial=False, warnings=[], warnings_total=0, sub_actions=[],
                transport_truncated=False, transport_omissions={}, reasons=[], timings=[],
                unsupported_scope=dict(count=0, samples=[], omitted_count=0),
                unresolved_scope=dict(count=0, samples=[], omitted_count=0),
                specialties=dict((s, dict(specialty=s, present=False, selected_count=0,
                    supported_count=0, action_id=None, classification=None, reason_code=None,
                    execution_state="NOT_PRESENT", evaluated=False, warnings=[],
                    warnings_total=0, result=None, transport_omissions={})) for s, _, __ in PLAN))


def stop(result, reason, failed=False):
    result.update(ok=not failed, classification="MEP_MULTI_SELECTION_FAILED" if failed
                  else "MEP_MULTI_SELECTION_NOT_READY", reason_code=reason, reasons=[reason])
    return result


def bounded_child(data, rows_limit, tables_limit):
    result = backend.project_value(dict((k, data[k]) for k in backend._RESULT_FIELDS if k in data))
    omissions = {}
    for key in ("warnings", "warning_records"):
        values = result.get(key, [])
        if len(values) > 30:
            omissions[key] = len(values) - 30
            result[key] = values[:30]
    tables = result.get("tables", [])
    shown = []
    omitted = []
    left = rows_limit
    for index, (title, headers, rows) in enumerate(tables):
        slots = max(1, min(tables_limit, len(tables)) - index)
        allowance = (left + slots - 1) // slots if index < tables_limit else 0
        selected = rows[:allowance]
        if index < tables_limit:
            shown.append([title, headers, selected]); left -= len(selected)
        if len(rows) != len(selected) or index >= tables_limit:
            omitted.append(dict(index=index, title=title, rows=len(rows)-len(selected)))
    result["tables"] = shown
    omissions["tables"] = omitted
    result["transport_omissions"] = omissions
    if size(result) > 20000:
        result.pop("tables")
        omissions["tables_field"] = True
        omissions["tables"] = [dict(index=i, title=t, rows=len(r)) for i, (t, h, r) in enumerate(tables)]
    if size(result) > 20000:
        raise backend.ProjectionError("Composite child core exceeds limit")
    return result


def execute(document, uidocument, request_id, guard):
    try:
        result = backend.project_value(_execute(document, uidocument, request_id, guard))
        result["transport_omissions"] = dict(
            unsupported_samples=result["unsupported_scope"]["omitted_count"],
            unresolved_samples=result["unresolved_scope"]["omitted_count"])
        result["transport_truncated"] = any(result["transport_omissions"].values()) or any(
            any(c["transport_omissions"].values()) for c in result["specialties"].values())
        if not guard():
            return stop(envelope(request_id), "STALE_CONTEXT", True)
        if size(result) > 80000:
            raise backend.ProjectionError("Composite exceeds limit")
        return result
    except Exception:
        return stop(envelope(request_id), "RESULT_PROJECTION_FAILED", True)


def _execute(document, uidocument, request_id, guard):
    """One lock/context and one evaluation snapshot; guard supplied by host only."""
    result = envelope(request_id)
    if not backend._EXECUTION_LOCK.acquire(False):
        return stop(result, "EXECUTION_BUSY", True)
    started = time.time()
    try:
        if not guard():
            return stop(envelope(request_id), "STALE_CONTEXT", True)
        if (document is None or uidocument is None or not document.IsValidObject
                or not uidocument.Document.Equals(document)):
            return stop(result, "NO_VALID_DOCUMENT_CONTEXT")
        module = backend._load_backend()
        with backend._document_context(module, document, uidocument):
            worker = object.__new__(module.OllamaAIChat)
            result["document_title"] = module._document_title(document)
            result["active_view_name"] = module._active_view_title(document, uidocument)
            result["active_view_type"] = worker._mep_ro_v1_active_view_type()
            try:
                ids = list(uidocument.Selection.GetElementIds())
                ids.sort(key=lambda x: worker._mep_ro_001_id_value(x))
            except Exception:
                return stop(result, "SELECTION_UNREADABLE")
            result["selected_reference_count"] = len(ids)
            if len(ids) > 600:
                return stop(result, "SELECTION_LIMIT_EXCEEDED")
            groups = dict((s, []) for s, _, __ in PLAN)
            unsupported, unresolved = [], []
            for ident in ids:
                try:
                    element = document.GetElement(ident)
                except Exception:
                    element = None
                if element is None:
                    unresolved.append(dict(id=worker._mep_ro_001_id_text(ident), reason="UNRESOLVED_REFERENCE"))
                    continue
                if worker._piping_ro_001_scope_kind(element) == "SUPPORTED_PIPE":
                    specialty = "PIPING"
                elif worker._hvac_ro_001_scope_kind(element) == "SUPPORTED_DUCT":
                    specialty = "HVAC"
                elif worker._electrical_ro_001_scope_kind(element)[1] in ("DEVICE_PROFILE", "EQUIPMENT_PROFILE"):
                    specialty = "ELECTRICAL"
                else:
                    specialty = None
                record = worker._mep_ro_001_element_record(element)
                if specialty:
                    groups[specialty].append((ident, record))
                else:
                    unsupported.append(dict(id=record.get("element_id"), category_id=record.get("category_id"),
                                            category=record.get("category_name"), reason="UNSUPPORTED_CATEGORY"))
            result.update(resolved_selected_count=len(ids)-len(unresolved),
                          supported_reference_count=sum(len(v) for v in groups.values()),
                          unsupported_reference_count=len(unsupported), unresolved_reference_count=len(unresolved),
                          supported_specialty_count=sum(bool(v) for v in groups.values()))
            for specialty, _, __ in PLAN:
                if groups[specialty]:
                    result["specialties"][specialty].update(present=True,
                        selected_count=len(groups[specialty]), supported_count=len(groups[specialty]),
                        action_id=specialty + "-RO-001-A01", execution_state="NOT_EVALUATED")
            for key, values in (("unsupported_scope", unsupported), ("unresolved_scope", unresolved)):
                result[key] = dict(count=len(values), samples=values[:30], omitted_count=max(0, len(values)-30))
            result["timings"].append(dict(phase="snapshot_partition", processed=len(ids), elapsed_ms=(time.time()-started)*1000))
            if not guard():
                return stop(envelope(request_id), "STALE_CONTEXT", True)
            if unresolved:
                return stop(result, "SELECTION_UNREADABLE")
            if not ids:
                return stop(result, "NO_ELEMENTS_SELECTED")
            present = result["supported_specialty_count"]
            if not present:
                return stop(result, "NO_SUPPORTED_SELECTED_ELEMENTS")
            reasons, usable = [], 0
            rows_left, tables_left, remaining = 40, 12, present
            for specialty, metadata_name, method in PLAN:
                subset = groups[specialty]
                if not subset:
                    continue
                if not guard():
                    return stop(envelope(request_id), "STALE_CONTEXT", True)
                child = result["specialties"][specialty]
                action = specialty + "-RO-001-A01"
                child.update(execution_state="FAILED", reason_code="TIME_BUDGET_EXCEEDED")
                row_budget = rows_left // remaining
                table_budget = tables_left // remaining
                rows_left -= row_budget; tables_left -= table_budget; remaining -= 1
                tick = time.time()
                if tick-started <= 2.0:
                    child["evaluated"] = True
                    result["sub_actions"].append(action)
                    try:
                        metadata = getattr(module, metadata_name)
                        key, prompt = next((k, v[1]) for k, v in metadata.items() if v[0] == action)
                        snapshot = dict(selected_ids=[i for i, r in subset],
                            selected_id_texts=[worker._mep_ro_001_id_text(i) for i, r in subset],
                            records=[r for i, r in subset], unavailable=[], selection_read_error=None)
                        data = getattr(worker, method)(prompt, key, snapshot)
                        child["classification"] = data["classification"]
                        child["reason_code"] = data["reason_code"]
                        child["result"] = bounded_child(data, row_budget, table_budget)
                        child["transport_omissions"] = child["result"]["transport_omissions"]
                        child["warnings"] = child["result"].get("warning_records", child["result"].get("warnings", []))
                        child["warnings_total"] = data.get("warnings_total", len(data.get("warning_records", data.get("warnings", []))))
                        cls = child["classification"]
                        if cls.endswith("_FAILED"):
                            reasons.append("SUBACTION_FAILED")
                        elif cls.endswith("_NOT_READY"):
                            child["execution_state"] = "NOT_READY"; reasons.append("SUBACTION_NOT_READY")
                        else:
                            child["execution_state"] = "COMPLETED"; usable += 1
                            if cls.endswith("_PARTIAL"):
                                reasons.append("SUBACTION_PARTIAL")
                    except backend.ProjectionError:
                        child.update(result=None, error_code="RESULT_PROJECTION_FAILED")
                        reasons.append("SUBACTION_FAILED")
                    except Exception:
                        child.update(result=None, error_code="HEADLESS_EXECUTION_FAILED")
                        reasons.append("SUBACTION_FAILED")
                else:
                    reasons.append("SUBACTION_FAILED")
                # Submitted references are not a claim of completed processing:
                # closed child caps/read failures remain authoritative.
                result["timings"].append(dict(phase=specialty, submitted_references=len(subset) if child["evaluated"] else 0,
                                               elapsed_ms=(time.time()-tick)*1000))
                if not guard():
                    return stop(envelope(request_id), "STALE_CONTEXT", True)
            # Integrity reread only, never used as another evaluation snapshot.
            if (not guard() or set(worker._mep_ro_001_id_text(i) for i in ids) !=
                    set(worker._mep_ro_001_id_text(i) for i in uidocument.Selection.GetElementIds())):
                return stop(envelope(request_id), "STALE_CONTEXT", True)
            composition_started = time.time()
            if not usable:
                return stop(result, "NO_USABLE_SPECIALTY_RESULT", True)
            if unsupported:
                reasons.append("UNSUPPORTED_ELEMENTS_PRESENT")
            priority = ("SUBACTION_FAILED", "SUBACTION_NOT_READY", "SUBACTION_PARTIAL", "UNSUPPORTED_ELEMENTS_PRESENT")
            result["reasons"] = [r for r in priority if r in reasons]
            result.update(partial=bool(reasons), reason_code=result["reasons"][0] if reasons else "COMPLETE",
                          classification="MEP_MULTI_SELECTION_SUMMARY_PARTIAL" if reasons else "MEP_MULTI_SELECTION_SUMMARY_OK")
            result["timings"].append(dict(phase="composition", child_results=present,
                                           elapsed_ms=(time.time()-composition_started)*1000))
            result["timings"].append(dict(phase="total", supported_references=result["supported_reference_count"],
                                           elapsed_ms=(time.time()-started)*1000))
            result = backend.project_value(result)
            if size(result) > 80000:
                return stop(envelope(request_id), "RESULT_PROJECTION_FAILED", True)
            return result
    except Exception:
        return stop(envelope(request_id), "COMPOSITE_EXECUTION_FAILED", True)
    finally:
        backend._EXECUTION_LOCK.release()
