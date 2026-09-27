"""M4A read-only preview. Call only in a valid Revit API context.

No pane/provider integration, confirmation token, transaction or value setter.
Returned scalar data is descriptive, never authorization for a future write.
"""
from datetime import datetime
import hashlib
import json
import unicodedata
from bimcode_ai_pane import write_contracts as contract


class PreviewBlocked(Exception):
    def __init__(self, reason):
        self.reason = reason
        Exception.__init__(self, reason)


def _require(condition, reason):
    if not condition:
        raise PreviewBlocked(reason)


def _id(value):
    return int(value.Value)


def capture_preview_context(uiapp):
    """Host-only invocation snapshot; API references never leave this callback."""
    try:
        uidoc = uiapp.ActiveUIDocument
        _require(uidoc is not None, "NO_VALID_DOCUMENT")
        doc = uidoc.Document
        _require(doc is not None and doc.IsValidObject, "NO_VALID_DOCUMENT")
        ids = tuple(uidoc.Selection.GetElementIds())
        view = uidoc.ActiveView
        _require(view is not None and view.IsValidObject, "NO_VALID_DOCUMENT")
        metadata = dict(document_identity=dict(session_hash=doc.GetHashCode(), title=doc.Title),
                        view_identity=dict(element_id=_id(view.Id), unique_id=view.UniqueId),
                        selected_element_ids=sorted(_id(eid) for eid in ids))
        fingerprint = hashlib.sha256(json.dumps(metadata, sort_keys=True,
                                                separators=(",", ":")).encode("utf-8")).hexdigest()
        return dict(uidoc=uidoc, doc=doc, ids=ids, metadata=metadata,
                    fingerprint=fingerprint, reason=None)
    except PreviewBlocked as error:
        return dict(reason=error.reason, failed=False)
    except Exception:
        return dict(reason="READ_FAILED", failed=True)


def resolve_target(uiapp, db, context=None):
    """Resolve only the explicit host snapshot; never reread or substitute IDs."""
    if context is None:
        context = capture_preview_context(uiapp)
    if context["reason"]:
        if context.get("failed"):
            raise RuntimeError("Selection capture failed")
        raise PreviewBlocked(context["reason"])
    uidoc, doc, ids = context["uidoc"], context["doc"], context["ids"]
    # Context may span the modal value dialog, but never another active document.
    current = uiapp.ActiveUIDocument
    _require(current is not None and current.Document.Equals(doc), "STALE_CONTEXT")
    _require(doc is not None and doc.IsValidObject, "NO_VALID_DOCUMENT")
    _require(not (doc.IsFamilyDocument or doc.IsWorkshared or doc.IsReadOnly or
                  doc.IsModifiable), "UNSUPPORTED_DOCUMENT")
    _require(len(ids) != 0, "NO_ELEMENTS_SELECTED")
    _require(len(ids) == 1, "MULTIPLE_ELEMENTS_SELECTED")
    element = doc.GetElement(ids[0])
    _require(element is not None and element.IsValidObject, "UNSUPPORTED_TARGET")
    _require(isinstance(element, db.Plumbing.Pipe) and
             not isinstance(element, db.ElementType), "UNSUPPORTED_TARGET")
    _require(element.Document.Equals(doc) and
             element.Category is not None and
             _id(element.Category.Id) == int(db.BuiltInCategory.OST_PipeCurves),
             "UNSUPPORTED_TARGET")
    _require(not element.IsPlaceholder and not element.Pinned and
             _id(element.GroupId) == -1 and _id(element.AssemblyInstanceId) == -1 and
             element.DesignOption is None, "UNSUPPORTED_TARGET")
    return doc, uidoc, element


def verify_binding(doc, shared, db):
    definition = shared.GetDefinition()
    _require(definition.GetDataType().Equals(db.SpecTypeId.String.Text),
             "DATA_TYPE_UNSUPPORTED")
    binding = doc.ParameterBindings.get_Item(definition)
    _require(isinstance(binding, db.InstanceBinding), "INVALID_BINDING")
    categories = sorted(_id(cat.Id) for cat in binding.Categories)
    _require(categories == [int(db.BuiltInCategory.OST_PipeCurves)], "INVALID_BINDING")
    return definition


def resolve_parameter(doc, element, db, guid):
    shared = db.SharedParameterElement.Lookup(doc, guid)
    _require(shared is not None, "PARAMETER_MISSING")
    _require(shared.GuidValue.Equals(guid) and shared.Name == contract.M4A_TEST_PARAMETER_NAME,
             "PARAMETER_IDENTITY_MISMATCH")
    verify_binding(doc, shared, db)
    parameter = element.get_Parameter(guid)
    _require(parameter is not None, "PARAMETER_MISSING")
    _require(parameter.IsShared and parameter.GUID.Equals(guid) and
             parameter.Element.Document.Equals(doc) and
             parameter.Element.UniqueId == element.UniqueId,
             "PARAMETER_IDENTITY_MISMATCH")
    _require(parameter.StorageType == db.StorageType.String, "STORAGE_TYPE_UNSUPPORTED")
    _require(parameter.Definition.GetDataType().Equals(db.SpecTypeId.String.Text),
             "DATA_TYPE_UNSUPPORTED")
    _require(not parameter.IsReadOnly, "TARGET_NOT_WRITABLE")
    return parameter


def _preview(uiapp, request_id, value, selection_generation, db, guid, context=None):
    result = dict(feature_id=contract.M4A_FEATURE_ID, action_id=contract.M4A_ACTION_ID,
                  request_id=request_id, document_identity=None, view_identity=None,
                  selection_generation=selection_generation, target_element_id=None,
                  selection_snapshot=None, selection_fingerprint=None,
                  target_unique_id=None, target_category=contract.M4A_CATEGORY,
                  pipe_type=None, parameter_guid=contract.M4A_TEST_PARAMETER_GUID,
                  parameter_display_name=contract.M4A_TEST_PARAMETER_NAME,
                  storage_type=None, current_value=None, current_has_value=None,
                  proposed_value=None, writable=False, binding_kind=None, warnings=[],
                  confirmation_required=True, transaction_started=False,
                  model_modified=False, timestamp=datetime.utcnow().isoformat() + "Z",
                  classification=contract.PREVIEW_NOT_READY, reason_code="INVALID_VALUE")
    if not contract.validate_value(value)["valid"]:
        return result
    result["proposed_value"] = value
    try:
        if context is None:
            context = capture_preview_context(uiapp)
        result.update(selection_snapshot=context.get("metadata"),
                      selection_fingerprint=context.get("fingerprint"))
        doc, uidoc, element = resolve_target(uiapp, db, context)
        view = uidoc.ActiveView
        _require(view is not None and view.IsValidObject, "NO_VALID_DOCUMENT")
        result.update(document_identity=dict(session_hash=doc.GetHashCode(), title=doc.Title),
                      view_identity=dict(element_id=_id(view.Id), unique_id=view.UniqueId),
                      target_element_id=_id(element.Id), target_unique_id=element.UniqueId,
                      pipe_type=dict(element_id=_id(element.GetTypeId()),
                                     unique_id=doc.GetElement(element.GetTypeId()).UniqueId))
        parameter = resolve_parameter(doc, element, db, guid)
        raw = parameter.AsString()
        _require(raw is None or (isinstance(raw, contract.string_types) and
                 len(raw) <= 256 and all(unicodedata.category(c)[0] != "C" for c in raw)),
                 "CURRENT_VALUE_UNSAFE")
        result.update(storage_type="String", current_value=raw,
                      current_has_value=bool(parameter.HasValue), writable=True,
                      binding_kind="INSTANCE",
                      current_display="(unset)" if raw is None else (raw or "(empty)"))
        _require(raw != value, "NO_CHANGE_REQUIRED")
        result.update(classification=contract.PREVIEW_OK, reason_code="COMPLETE")
    except PreviewBlocked as error:
        result["reason_code"] = error.reason
    except Exception:
        # Never fabricate missing/empty evidence or expose raw API exception text.
        result.update(classification=contract.PREVIEW_FAILED, reason_code="READ_FAILED")
    return result


def build_preview(uiapp, request_id, value, selection_generation=None, context=None):
    """Host-only synchronous API-context entry; no queue or provider dispatch."""
    from Autodesk.Revit import DB
    from System import Guid
    return _preview(uiapp, request_id, value, selection_generation, DB,
                    Guid(contract.M4A_TEST_PARAMETER_GUID), context=context)
