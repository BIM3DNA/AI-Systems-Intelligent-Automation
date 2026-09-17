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


class PaneSession(object):
    def __init__(self, uiapp):
        self.uiapp = uiapp
        self.panel = BIMCodeAIPanel()
        self.provider = RightDockProvider(self.panel)
        self.handler = ContextRefreshHandler(self)
        self.refresh_event = UI.ExternalEvent.Create(self.handler)
        self.panel.bind_refresh(self.request_refresh)
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
        for source, name, event_type, callback in specs:
            delegate = framework.EventHandler[event_type](callback)
            getattr(source, name).__iadd__(delegate)
            self._subscriptions.append((source, name, delegate))

    def dispose_unregistered(self):
        for source, name, delegate in reversed(self._subscriptions):
            getattr(source, name).__isub__(delegate)
        self._subscriptions = []
        self.panel.bind_refresh(None)
        self.refresh_event.Dispose()

    def refresh(self, uiapp):
        # Called only from startup / a command / a supported Revit API event.
        self.panel.render(read_context(uiapp))

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

    def on_document_changed(self, sender, args):
        # DocumentOpened/Created may precede activation of that document.
        self.show_pending = True
        self.request_refresh()

    def on_document_closed(self, sender, args):
        # Do not dereference the closed document or display its cached context.
        # Revit can hide the visual host when the final project closes. Re-arm
        # Show for the next valid active document without registering again.
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
