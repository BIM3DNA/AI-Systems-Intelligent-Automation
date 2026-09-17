"""Session registration and Revit callback ownership for the M1 pane.

Startup owns registration. Commands only show an already registered pane.
The session holder roots the provider, panel, delegates, and read-only event
across command-engine lifetimes and extension reloads.
"""

from pyrevit import DB, UI, framework, forms
from pyrevit.coreutils import envvars

from bimcode_ai_pane import PANEL_ID, PANEL_TITLE, SESSION_KEY
from bimcode_ai_pane.context import empty_context, read_context
from bimcode_ai_pane.panel import BIMCodeAIPanel
from bimcode_ai_pane.tools import ModelMindToolBridge, document_key, result_for


def pane_id():
    return UI.DockablePaneId(framework.Guid.Parse(PANEL_ID))


class RightDockProvider(UI.IDockablePaneProvider):
    def __init__(self, panel):
        self.panel = panel

    def SetupDockablePane(self, data):
        # Installed pyRevit's public registration helper does not set InitialState.
        data.FrameworkElement = self.panel
        state = UI.DockablePaneState()
        state.DockPosition = UI.DockPosition.Right
        data.InitialState = state
        data.VisibleByDefault = True


class ContextRefreshHandler(UI.IExternalEventHandler):
    def __init__(self, session):
        self.session = session

    def Execute(self, uiapp):
        self.session.refresh(uiapp)
        self.session.try_initial_show(uiapp)

    def GetName(self):
        return "BIMCode AI read-only context refresh"


class ModelMindReadOnlyHandler(UI.IExternalEventHandler):
    def __init__(self, session):
        self.session = session

    def Execute(self, uiapp):
        session = self.session
        request = session.tools.pending
        if request is None:
            return
        try:
            result = session.tools.execute(request, uiapp, session.context_generation)
        except Exception:
            result = result_for(request, "FAILED", "TOOL_EXECUTION_FAILED")
        finally:
            # No API objects or exception trace are retained by the request.
            session.tools.clear()
        session.finish_tool(result)

    def GetName(self):
        return "BIMCode AI ModelMind read-only tools"


class PaneSession(object):
    def __init__(self, uiapp):
        self.uiapp = uiapp
        self.panel = BIMCodeAIPanel()
        self.provider = RightDockProvider(self.panel)
        self.handler = ContextRefreshHandler(self)
        self.refresh_event = UI.ExternalEvent.Create(self.handler)
        self.tools = ModelMindToolBridge()
        self.context_generation = 0
        self.document_identity = None
        self.tool_handler = ModelMindReadOnlyHandler(self)
        self.tool_event = None
        try:
            self.tool_event = UI.ExternalEvent.Create(self.tool_handler)
            self.panel.bind_refresh(self.request_refresh)
            self.panel.bind_tools(self.request_tool)
        except Exception:
            self.refresh_event.Dispose()
            if self.tool_event is not None:
                self.tool_event.Dispose()
            raise
        self.show_pending = True
        self._subscriptions = []

    def subscribe(self):
        if self._subscriptions:
            return
        # Store exact delegate instances for rollback and to avoid collection.
        specs = (
            (self.uiapp, "ViewActivated", UI.Events.ViewActivatedEventArgs,
             self.on_view_activated),
            (self.uiapp.Application, "DocumentOpened", DB.Events.DocumentOpenedEventArgs,
             self.on_document_changed),
            (self.uiapp.Application, "DocumentCreated", DB.Events.DocumentCreatedEventArgs,
             self.on_document_changed),
            (self.uiapp.Application, "DocumentClosed", DB.Events.DocumentClosedEventArgs,
             self.on_document_closed),
        )
        if (hasattr(self.uiapp, "SelectionChanged")
                and hasattr(UI.Events, "SelectionChangedEventArgs")):
            specs += ((self.uiapp, "SelectionChanged", UI.Events.SelectionChangedEventArgs,
                       self.on_selection_changed),)
        if (hasattr(self.uiapp, "ThemeChanged")
                and hasattr(UI.Events, "ThemeChangedEventArgs")):
            specs += ((self.uiapp, "ThemeChanged", UI.Events.ThemeChangedEventArgs,
                       self.on_theme_changed),)
        for source, name, event_type, callback in specs:
            # Theme subscriptions use this same retained/rollback-safe list.
            delegate = framework.EventHandler[event_type](callback)
            getattr(source, name).__iadd__(delegate)
            self._subscriptions.append((source, name, delegate))

    def dispose_unregistered(self):
        for source, name, delegate in reversed(self._subscriptions):
            getattr(source, name).__isub__(delegate)
        self._subscriptions = []
        self.panel.bind_refresh(None)
        self.panel.bind_tools(None)
        self.tools.clear()
        self.tool_event.Dispose()
        self.refresh_event.Dispose()

    def refresh(self, uiapp):
        # Called only from startup / a command / a supported Revit API event.
        self.document_identity = document_key(uiapp)
        self.panel.render(read_context(uiapp))

    def request_tool(self, tool_name):
        # WPF callback: cached scalar identity only. No Revit reads here.
        request = self.tools.begin(tool_name, self.document_identity, self.context_generation)
        if request is None:
            return
        try:
            self.panel.set_tools_busy(True)
            response = self.tool_event.Raise()
            if response not in (UI.ExternalEventRequest.Accepted, UI.ExternalEventRequest.Pending):
                self.finish_tool(result_for(request, "FAILED", "EXTERNAL_EVENT_NOT_ACCEPTED"))
        except Exception:
            self.finish_tool(result_for(request, "FAILED", "EXTERNAL_EVENT_UNAVAILABLE"))

    def finish_tool(self, result):
        self.tools.clear()
        try:
            self.panel.render_tool_result(result)
        except Exception:
            pass  # A disposed pane must not escape into Revit event dispatch.
        finally:
            try:
                self.panel.set_tools_busy(False)
            except Exception:
                pass

    def invalidate_tool_context(self):
        # Even switch-away-and-back / same-model reopen invalidates queued work.
        self.context_generation += 1
        self.document_identity = None

    def request_refresh(self):
        # WPF callback: Raise schedules the read; it does not read Revit objects.
        try:
            result = self.refresh_event.Raise()
            if result in (UI.ExternalEventRequest.Accepted, UI.ExternalEventRequest.Pending):
                self.panel.set_status("Refresh queued; waiting for Revit")
            else:
                self.panel.set_status("Refresh unavailable; try again when Revit is ready")
        except Exception:
            self.panel.set_status("Refresh unavailable; try again when Revit is ready")

    def try_initial_show(self, uiapp):
        if self.show_pending:
            try:
                # Keep the request pending through Revit's no-document state.
                uidoc = uiapp.ActiveUIDocument
                if uidoc is None:
                    return
                doc = uidoc.Document
                if doc is None or not doc.IsValidObject:
                    return
                uiapp.GetDockablePane(pane_id()).Show()
                self.show_pending = False
            except Exception:
                # Revit can register a pane before its visual host exists.
                # Retry on activation/refresh; no Idling polling or timer.
                pass

    def on_view_activated(self, sender, args):
        self.invalidate_tool_context()
        self.refresh(self.uiapp)
        self.try_initial_show(self.uiapp)

    def on_selection_changed(self, sender, args):
        # Native Revit UI event: read only the event snapshot's count. No
        # UIDocument traversal, retained ElementIds, or ExternalEvent request.
        try:
            count = args.GetSelectedElements().Count
        except Exception:
            count = None
        try:
            if self.panel is not None:
                self.panel.render_selection_count(count)
        except Exception:
            # A closing/unavailable WPF host must never escape into Revit's
            # event dispatch. The existing explicit refresh remains recovery.
            pass

    def on_theme_changed(self, sender, args):
        # Presentation only: no context refresh, request invalidation or tools.
        try:
            self.panel.apply_current_theme()
        except Exception:
            pass

    def on_document_changed(self, sender, args):
        # DocumentOpened/Created may precede activation of that document.
        self.invalidate_tool_context()
        self.show_pending = True
        self.request_refresh()

    def on_document_closed(self, sender, args):
        # Do not dereference the closed document or display its cached context.
        # Revit can hide the visual host when the final project closes. Re-arm
        # Show for the next valid active document without registering again.
        self.invalidate_tool_context()
        self.show_pending = True
        self.panel.render(empty_context())
        self.request_refresh()


def start(uiapp):
    """Run from extension startup (valid API context), once per host session."""
    if not hasattr(forms, "WPFPanel") or not hasattr(UI.DockablePane, "PaneIsRegistered"):
        raise RuntimeError("BIMCode AI requires pyRevit WPFPanel and Revit dockable panes")
    existing = envvars.get_pyrevit_env_var(SESSION_KEY)
    if UI.DockablePane.PaneIsRegistered(pane_id()):
        if existing is None:
            raise RuntimeError("BIMCode AI pane registered without its session; restart Revit")
        existing.refresh(uiapp)
        existing.show_pending = True
        existing.try_initial_show(uiapp)
        return existing
    if existing is not None:
        raise RuntimeError("BIMCode AI session/registration mismatch; restart Revit")

    session = PaneSession(uiapp)
    try:
        session.subscribe()
        uiapp.RegisterDockablePane(pane_id(), PANEL_TITLE, session.provider)
    except Exception:
        session.dispose_unregistered()
        raise
    envvars.set_pyrevit_env_var(SESSION_KEY, session)
    session.refresh(uiapp)
    session.try_initial_show(uiapp)
    return session


def show(uiapp):
    """Show only; never register from a command or prompt."""
    if not UI.DockablePane.PaneIsRegistered(pane_id()):
        raise RuntimeError("BIMCode AI is not registered. Restart Revit with AI.extension enabled.")
    forms.open_dockable_panel(PANEL_ID)
    session = envvars.get_pyrevit_env_var(SESSION_KEY)
    if session is not None:
        session.show_pending = False
        session.refresh(uiapp)
