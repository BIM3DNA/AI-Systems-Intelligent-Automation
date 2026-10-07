"""Trusted native UI only. No provider flag, callback or consent argument."""
import json
from bimcode_ai_pane import write_contracts as c


def show(preview, identity):
    from Autodesk.Revit import UI
    dialog = UI.TaskDialog("BIMCode M4B Controlled Write")
    dialog.TitleAutoPrefix = False
    dialog.MainInstruction = "Change exactly one parameter in one transaction?"
    dialog.MainContent = (
        "Document: {0}\nTarget: Pipe {1}\nParameter: {2}\nGUID: {3}\n"
        "Before: {4}\nProposed: {5}\nLogical request: {6}\nHost request: {7}\n"
        "Provider response: {8}\nCall: {9}").format(
            preview["document_identity"]["title"], preview["target_element_id"],
            c.M4A_TEST_PARAMETER_NAME, c.M4A_TEST_PARAMETER_GUID,
            json.dumps(preview["current_value"], ensure_ascii=True),
            json.dumps(preview["proposed_value"], ensure_ascii=True),
            identity.logical_request_id, identity.host_request_id,
            identity.previous_response_id, identity.call_id)
    dialog.AddCommandLink(UI.TaskDialogCommandLinkId.CommandLink1,
                          "Confirm this one parameter write")
    dialog.CommonButtons = UI.TaskDialogCommonButtons.Cancel
    dialog.DefaultButton = UI.TaskDialogResult.Cancel
    dialog.AllowCancellation = True
    return dialog.Show() == UI.TaskDialogResult.CommandLink1
