"""Local authenticated IPC client. Does not import Revit or call model APIs."""
import os
from pathlib import Path
import socket

from bimcode_mcp import protocol as p


class BridgeError(RuntimeError):
    pass


class BridgeClient:
    def __init__(self, connection=None):
        self.connection = Path(connection) if connection else None

    def _descriptor(self):
        path = self.connection
        if path is None:
            local = os.environ.get("LOCALAPPDATA")
            if not local:
                raise BridgeError("Start MCP Bridge in Revit on this Windows machine.")
            paths = list((Path(local) / "BIMCode" / "MCP").glob("session-*/connection.json"))
            if len(paths) != 1:
                raise BridgeError("Start one Revit MCP Bridge, or use --connection with its file path. "
                                  "Remove stale session folders only after their Revit process has exited.")
            path = paths[0]
        try:
            with path.open("rb") as source:
                raw = source.read(p.MAX_REQUEST + 1)
            if len(raw) > p.MAX_REQUEST:
                raise ValueError()
            value = p.loads(raw.decode("utf-8"))
            if (not isinstance(value, dict)
                    or set(value) != {"version", "host", "port", "token", "revit_pid"}
                    or type(value["version"]) is not int or value["version"] != p.VERSION
                    or value["host"] != "127.0.0.1"
                    or type(value["port"]) is not int or not 1 <= value["port"] <= 65535
                    or type(value["revit_pid"]) is not int or value["revit_pid"] < 1
                    or not p.is_token(value["token"])):
                raise ValueError()
            return value
        except Exception:
            raise BridgeError("Local bridge connection file is missing or invalid.") from None

    def call(self, operation, tool=None, context_token=None):
        descriptor = self._descriptor()
        request = dict(version=p.VERSION, token=descriptor["token"],
                       request_id=p.secret(), operation=operation)
        if operation == "inspect":
            request.update(tool=tool, context_token=context_token)
        try:
            p.validate_request(request, descriptor["token"])
            with socket.create_connection(("127.0.0.1", descriptor["port"]), timeout=2) as connection:
                connection.sendall(p.encode(request, p.MAX_REQUEST))
                response = p.receive(connection, p.MAX_RESPONSE, p.monotonic() + 25.0)
        except Exception:
            raise BridgeError("Local Revit bridge unavailable or request invalid. "
                              "Check that Revit and MCP Bridge are running.") from None
        if (not isinstance(response, dict)
                or set(response) != {"version", "request_id", "ok", "data", "error_code"}
                or type(response["version"]) is not int or response["version"] != p.VERSION
                or response["request_id"] != request["request_id"]
                or type(response["ok"]) is not bool):
            raise BridgeError("Local bridge returned an invalid response.")
        if not response["ok"]:
            code = response.get("error_code")
            allowed = {"BRIDGE_STOPPED", "NO_ACTIVE_DOCUMENT", "REVIT_BUSY", "CONTEXT_LIMIT",
                       "STALE_CONTEXT", "INVALID_REQUEST", "REVIT_TIMEOUT", "RESULT_TOO_LARGE",
                       "MODELMIND_NOT_READY", "MODELMIND_EXECUTION_FAILED", "AI_TOOL_NOT_ALLOWED",
                       "AI_TOOL_PROTOCOL_ERROR", "AI_TOOL_LOOP_LIMIT"}
            if code not in allowed or response["data"] is not None:
                raise BridgeError("Local bridge returned an invalid error.")
            raise BridgeError(code + ": obtain fresh Revit context before retrying; no automatic retry.")
        if response["error_code"] is not None or not isinstance(response["data"], dict):
            raise BridgeError("Local bridge returned an invalid result.")
        return response["data"]
