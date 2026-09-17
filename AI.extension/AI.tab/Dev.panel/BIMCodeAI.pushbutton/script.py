"""Show the BIMCode AI pane registered by extension startup."""

from pyrevit import HOST_APP, forms

try:
    from bimcode_ai_pane.lifecycle import show
    show(HOST_APP.uiapp)
except Exception as error:
    forms.alert(str(error), title="BIMCode AI")
