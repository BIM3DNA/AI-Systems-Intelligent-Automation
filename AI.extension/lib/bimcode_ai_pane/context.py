"""Read a small context snapshot, only inside a Revit API callback.

Never retain Documents, Views, UIDocuments, selections, or ElementIds in the UI.
"""


def empty_context():
    return {
        "document": "No document",
        "view": "Unavailable",
        "view_type": "Unavailable",
        "selection_count": 0,
        "status": "Ready",
    }


def read_context(uiapp):
    snapshot = empty_context()
    try:
        uidoc = uiapp.ActiveUIDocument
        if uidoc is None:
            return snapshot
        doc = uidoc.Document
        if doc is None or not doc.IsValidObject:
            return snapshot
    except Exception:
        snapshot["status"] = "Context unavailable; refresh when Revit is ready"
        return snapshot

    try:
        snapshot["document"] = doc.Title or "Untitled document"
    except Exception:
        snapshot["document"] = "Unavailable"
        snapshot["status"] = "Some context is unavailable"
    try:
        view = uidoc.ActiveView
        if view is not None and view.IsValidObject:
            snapshot["view"] = view.Name or "Unnamed view"
            snapshot["view_type"] = str(view.ViewType)
    except Exception:
        snapshot["status"] = "Some context is unavailable"
    try:
        snapshot["selection_count"] = uidoc.Selection.GetElementIds().Count
    except Exception:
        # Unknown is not a claim that the user's selection is empty.
        snapshot["selection_count"] = None
        snapshot["status"] = "Selection unavailable; refresh when Revit is ready"
    return snapshot
