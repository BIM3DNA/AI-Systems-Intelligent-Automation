"""WPF presentation only; no Revit API reads in control callbacks."""

import os.path

from pyrevit import forms

from bimcode_ai_pane import PANEL_ID, PANEL_TITLE
from bimcode_ai_pane.context import empty_context


class BIMCodeAIPanel(forms.WPFPanel):
    panel_id = PANEL_ID
    panel_title = PANEL_TITLE
    panel_source = os.path.join(os.path.dirname(__file__), "BIMCodeAIPane.xaml")

    def __init__(self):
        forms.WPFPanel.__init__(self)
        self._request_refresh = None
        self.FindName("RefreshButton").Click += self._on_refresh
        self.render(empty_context())

    def bind_refresh(self, callback):
        self._request_refresh = callback

    def _on_refresh(self, sender, args):
        if self._request_refresh is not None:
            self._request_refresh()

    def set_status(self, message):
        self.FindName("StatusText").Text = message

    def render(self, snapshot):
        self.FindName("DocumentText").Text = snapshot["document"]
        self.FindName("ViewText").Text = snapshot["view"]
        self.FindName("ViewTypeText").Text = snapshot["view_type"]
        self.render_selection_count(snapshot["selection_count"])
        self.set_status(snapshot["status"])

    def render_selection_count(self, count):
        # SelectionChanged runs on Revit's UI thread, as do view callbacks.
        # Hidden panes retain their controls; no visibility/Loaded gate needed.
        control = self.FindName("SelectionText")
        if control is not None:
            control.Text = (
                "Unavailable" if count is None else
                "{0} {1}".format(count, "element" if count == 1 else "elements")
            )
