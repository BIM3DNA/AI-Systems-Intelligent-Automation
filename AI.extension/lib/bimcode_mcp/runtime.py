"""Opt-in Revit host wiring. Loaded only by the local MCP Bridge button."""
import json
import os
import uuid

from bimcode_mcp.host import Controller
from bimcode_mcp.transport import Listener


def _private_directory():
    """Create the credential directory with a current-user-only Windows DACL."""
    import clr
    clr.AddReference("System.IO.FileSystem.AccessControl")
    from System.IO import DirectoryInfo, FileSystemAclExtensions
    from System.Security.AccessControl import (
        DirectorySecurity, FileSystemAccessRule, FileSystemRights,
        InheritanceFlags, PropagationFlags, AccessControlType,
    )
    from System.Security.Principal import WindowsIdentity
    local = os.environ.get("LOCALAPPDATA")
    if not local or not os.path.isabs(local):
        raise RuntimeError("MCP_LOCAL_APPDATA_UNAVAILABLE")
    parent = os.path.join(local, "BIMCode", "MCP")
    if not os.path.isdir(parent):
        os.makedirs(parent)
    path = os.path.join(parent, "session-" + uuid.uuid4().hex)
    identity = WindowsIdentity.GetCurrent()
    try:
        sid = identity.User
        security = DirectorySecurity()
        security.SetAccessRuleProtection(True, False)
        security.SetOwner(sid)
        security.AddAccessRule(FileSystemAccessRule(
            sid, FileSystemRights.FullControl,
            InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
            getattr(PropagationFlags, "None"), AccessControlType.Allow))
        info = DirectoryInfo(path)
        if info.Exists:
            raise RuntimeError("MCP_DIRECTORY_ALREADY_EXISTS")
        FileSystemAclExtensions.Create(info, security)
        actual = FileSystemAclExtensions.GetAccessControl(info)
        if not actual.AreAccessRulesProtected:
            raise RuntimeError("MCP_PRIVATE_DIRECTORY_FAILED")
    finally:
        identity.Dispose()
    return path


class Runtime(object):
    def __init__(self, session):
        self.session = session
        self.controller = Controller(session)
        self.listener = None
        self.directory = None
        self.connection_file = None
        self.delegate = None

    def start(self):
        from pyrevit import DB, framework
        from System import Action
        required = {"SelectionChanged", "ViewActivated", "DocumentOpened",
                    "DocumentCreated", "DocumentClosed", "ApplicationClosing"}
        if not required.issubset(set(item[1] for item in self.session._subscriptions)):
            raise RuntimeError("MCP_LIFECYCLE_EVENTS_UNAVAILABLE")
        try:
            self.directory = _private_directory()
            self.delegate = framework.EventHandler[DB.Events.DocumentChangedEventArgs](
                self.controller.model_changed)
            self.session.uiapp.Application.DocumentChanged += self.delegate
            dispatcher = self.session.panel.Dispatcher

            def dispatch(request, ticket):
                # Workers only post scalar requests. Host reads run in Execute.
                dispatcher.BeginInvoke(Action(lambda: self.controller.handle(request, ticket)))

            self.listener = Listener(dispatch)
            self.connection_file = os.path.join(self.directory, "connection.json")
            descriptor = dict(version=1, host="127.0.0.1", port=self.listener.port,
                              token=self.listener.token, revit_pid=os.getpid())
            with open(self.connection_file, "w") as target:
                json.dump(descriptor, target)
            self.listener.start()
            return self.connection_file
        except Exception:
            self.stop()
            raise

    def stop(self):
        # UI/API owner only. No worker join: never block Revit's dispatcher.
        self.controller.stop()
        if self.listener is not None:
            self.listener.stop()
        if self.delegate is not None:
            try:
                self.session.uiapp.Application.DocumentChanged -= self.delegate
            finally:
                self.delegate = None
        if self.connection_file and os.path.isfile(self.connection_file):
            os.remove(self.connection_file)
        if self.directory and os.path.isdir(self.directory):
            os.rmdir(self.directory)
