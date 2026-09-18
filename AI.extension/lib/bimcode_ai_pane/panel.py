"""WPF presentation only; no Revit API reads in control callbacks."""

import os.path

from pyrevit import forms

from bimcode_ai_pane import PANEL_ID, PANEL_TITLE
from bimcode_ai_pane.context import empty_context
from bimcode_ai_pane.result_presentation import build_presentation
from bimcode_ai_pane.rich_result import make_document
from bimcode_ai_pane.result_find import ResultFind
from bimcode_ai_pane.theme import current_theme, apply_resources
from bimcode_ai_pane import provider_bridge, provider_ui

TOOL_BUTTONS = (
    ("SummaryButton", "selection.summary"),
    ("ConnectorsButton", "selection.connectors"),
    ("AssignmentButton", "selection.system_assignment"),
    ("QAHealthButton", "selection.qa_health"),
)


class BIMCodeAIPanel(forms.WPFPanel):
    panel_id = PANEL_ID
    panel_title = PANEL_TITLE
    panel_source = os.path.join(os.path.dirname(__file__), "BIMCodeAIPane.xaml")

    def __init__(self):
        forms.WPFPanel.__init__(self)
        self._request_refresh = None
        self._request_tool = None
        self._tools_busy = False
        self._presentation = {"blocks": []}
        self._finder = ResultFind()
        self.FindName("FindInput").TextChanged += self._on_find
        self.FindName("FindPrevious").Click += self._on_find_previous
        self.FindName("FindNext").Click += self._on_find_next
        self.FindName("FindClear").Click += self._on_find_clear
        self.FindName("RefreshButton").Click += self._on_refresh
        for name, tool in TOOL_BUTTONS:
            control = self.FindName(name)
            control.Tag = tool
            control.Click += self._on_tool
        self.render(empty_context())
        self._provider_state = provider_bridge.SendState()
        self.FindName("MessageInput").Text = ""
        self.FindName("SendButton").Click += self._on_send
        self.FindName("ProviderCheckButton").Click += self._on_provider_check
        self.FindName("MessageInput").TextChanged += self._on_provider_text
        self._on_provider_check(None, None)

    def _update_provider_controls(self):
        self.FindName("SendButton").IsEnabled = self._provider_state.enabled(
            self.FindName("MessageInput").Text)
        self.FindName("ProviderCheckButton").IsEnabled = self._provider_state.active is None

    def _on_provider_text(self, sender, args):
        self._update_provider_controls()

    def _on_provider_check(self, sender, args):
        self._start_provider("readiness")

    def _on_send(self, sender, args):
        self._start_provider("text_response", self.FindName("MessageInput").Text)

    def _start_provider(self, operation, text=""):
        payload = self._provider_state.begin(operation, text)
        if payload is None:
            return
        self._update_provider_controls()
        self.FindName("ProviderStatus").Text = ("Thinking..." if operation == "text_response"
                                               else "Checking local provider configuration...")
        try:
            provider_ui.launch(payload, self.Dispatcher, self._provider_complete)
        except Exception:
            self._provider_complete(provider_bridge.failure(payload["request_id"], "SIDECAR_START_FAILED"))

    def _provider_complete(self, result):
        operation = self._provider_state.active["operation"] if self._provider_state.active else None
        if not self._provider_state.finish(result):
            return
        try:
            self.FindName("ProviderStatus").Text = (
                "Text provider ready (authentication untested)." if operation == "readiness" and result["ok"]
                else "Text request complete." if result["ok"] else result["error"]["message"])
            if operation == "text_response":
                self._presentation = provider_ui.presentation(result)
                self.FindName("FindInput").Text = ""
                self._finder.search(self._presentation, "")
                self._render_find()
        finally:
            self._update_provider_controls()

    def apply_current_theme(self):
        try:
            apply_resources(self.Resources, current_theme())
        except Exception:
            # Preserve the XAML light fallback if the visual host is unavailable.
            pass

    def bind_refresh(self, callback):
        self._request_refresh = callback

    def _on_refresh(self, sender, args):
        if self._request_refresh is not None:
            self._request_refresh()

    def bind_tools(self, callback):
        self._request_tool = callback

    def _on_tool(self, sender, args):
        if self._request_tool is not None and not self._tools_busy:
            self._request_tool(sender.Tag)

    def set_tools_busy(self, busy):
        self._tools_busy = busy
        for name, unused in TOOL_BUTTONS:
            self.FindName(name).IsEnabled = not busy
        self.set_status("Running..." if busy else "Ready")

    def render_tool_result(self, result):
        self._presentation = build_presentation(result)
        self.FindName("FindInput").Text = ""
        self._finder.search(self._presentation, "")
        self._render_find()

    def _on_find(self, sender, args):
        self._finder.search(self._presentation, self.FindName("FindInput").Text)
        self._render_find()

    def _on_find_previous(self, sender, args):
        self._finder.move(-1)
        self._render_find()

    def _on_find_next(self, sender, args):
        self._finder.move(1)
        self._render_find()

    def _on_find_clear(self, sender, args):
        self.FindName("FindInput").Text = ""
        self._on_find(sender, args)

    def _render_find(self):
        self.FindName("FindCount").Text = self._finder.caption()
        for name in ("FindPrevious", "FindNext"):
            self.FindName(name).IsEnabled = bool(self._finder.matches)
        if not self._presentation["blocks"]:
            return
        viewer = self.FindName("ToolResultText")
        # Rebuild only the bounded UI document: avoids accumulating formatting
        # edits across searches, and never invokes the tool/context callbacks.
        viewer.Document = (make_document(self._presentation, self._finder)
                           if self._finder.matches else make_document(self._presentation))
        if self._finder.matches:
            viewer.UpdateLayout()
            viewer.Document.Tag.BringIntoView()

    def set_status(self, message):
        self.FindName("StatusText").Text = "Running..." if self._tools_busy else message

    def render(self, snapshot):
        self.apply_current_theme()
        self.FindName("DocumentText").Text = snapshot["document"]
        self.FindName("DocumentText").ToolTip = snapshot["document"]
        self.FindName("ViewText").Text = snapshot["view"]
        self.FindName("ViewText").ToolTip = snapshot["view"]
        self.FindName("ViewTypeText").Text = snapshot["view_type"]
        self.FindName("ViewTypeText").ToolTip = snapshot["view_type"]
        self.render_selection_count(snapshot["selection_count"])
        self.set_status(snapshot["status"])

    def render_selection_count(self, count):
        # SelectionChanged runs on Revit's UI thread, as do view callbacks.
        # Hidden panes retain their controls; no visibility/Loaded gate needed.
        control = self.FindName("SelectionText")
        if control is not None:
            control.Text = (
                "Sel: unavailable" if count is None else "Sel: {0}".format(count)
            )
