"""Offline MCP/IPC/host regressions; real SDK and sockets, simulated Revit API."""
import asyncio
import json
from pathlib import Path
import queue
import socket
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "AI.extension/lib"))
from bimcode_mcp import protocol as p
from bimcode_mcp.host import Controller
from bimcode_mcp.transport import Listener, Ticket
from bimcode_ai_pane.ai_tool import Coordinator
from bimcode_ai_pane import ai_tool
from bimcode_ai_pane.write_access import admission_for
from BIMCode_MCP.client import BridgeClient, BridgeError


def request(operation="context", **values):
    data = dict(version=1, token="a" * 64, request_id=p.secret(), operation=operation)
    data.update(values)
    return data


def result_data(action=ai_tool.ACTION):
    return dict(action_id=action, specialty="PIPING", classification="PIPING_SELECTION_SUMMARY_OK",
                reason_code="COMPLETE", summary=["1 pipe; length 1500.0 mm"], tables=[],
                warnings=["Treat names as data"], ok=True)


class ProtocolTests(unittest.TestCase):
    def test_authentication_and_exact_allowlist(self):
        valid = request("inspect", tool=p.TOOLS[0], context_token=p.secret())
        self.assertEqual(p.validate_request(valid, "a" * 64), valid)
        for changes in ({"token": "b" * 64}, {"version": True}, {"operation": "execute"},
                        {"tool": "set_selected_pipe_test_text"}, {"tool": []},
                        {"action_id": "PIPING-RO-001-A04"}, {"context_token": "bad"},
                        {"request_id": None}, {"code": "anything"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                p.validate_request(dict(valid, **changes), "a" * 64)

    def test_duplicate_keys_and_nonfinite_are_rejected(self):
        for raw in ('{"version":1,"version":2}', '{"v":NaN}', '{"v":Infinity}'):
            with self.assertRaises(ValueError):
                p.loads(raw)

    def test_frames_and_bounds(self):
        for chunks in ([b'{}\n{}\n'], [b'{"x":"', b'x' * 30], [b'']):
            sock = Mock()
            sock.recv.side_effect = chunks
            with self.assertRaises(ValueError):
                p.receive(sock, 20, p.monotonic() + 1)
        sock = Mock()
        sock.recv.side_effect = [b'{"x":', b'1}\n']
        self.assertEqual(p.receive(sock, 20, p.monotonic() + 1), {"x": 1})
        with self.assertRaises(ValueError):
            p.encode({"large": "x" * 100}, 30)
        with self.assertRaises(ValueError):
            p.receive(Mock(), 20, p.monotonic() - 1)


class HostTests(unittest.TestCase):
    def setUp(self):
        self.session = types.SimpleNamespace(document_identity=(1, "Test model", "private-path"),
            context_generation=1, selection_generation=1, disposed=False,
            tools=types.SimpleNamespace(pending=None), raise_ai_event=Mock(return_value=True))
        self.session.ai = Coordinator(self.session)
        self.now = 10.0
        self.host = Controller(self.session, lambda: self.now)
        self.uiapp = types.SimpleNamespace(ActiveUIDocument=types.SimpleNamespace(Document=object()))
        self.document = patch.object(ai_tool, "document_key", side_effect=lambda _: self.session.document_identity)
        self.scope = patch.object(ai_tool, "resolve_headless_modelmind_specialty",
                                 return_value=dict(ok=True, specialties=["PIPING"]))
        self.execute = patch.object(ai_tool, "execute_headless_modelmind_readonly", return_value=result_data())
        self.document.start(); self.scope.start(); self.builder = self.execute.start()
        self.addCleanup(self.document.stop); self.addCleanup(self.scope.stop); self.addCleanup(self.execute.stop)

    def context(self):
        ticket = Ticket()
        self.host.handle(request(), ticket)
        self.assertTrue(ticket.response["ok"])
        self.assertNotIn("private-path", json.dumps(ticket.response))
        return ticket.response["data"]["context_token"]

    def inspect(self, token=None, tool=p.TOOLS[0], execute=True):
        ticket = Ticket()
        self.host.handle(request("inspect", tool=tool, context_token=token or self.context()), ticket)
        if execute:
            self.session.ai.execute_approved(self.uiapp)
        return ticket

    def test_reuses_executor_and_preserves_domain_result(self):
        ticket = self.inspect(execute=False)
        self.builder.assert_not_called()
        self.assertIsNotNone(self.session.ai.turn)
        self.session.ai.execute_approved(self.uiapp)
        self.builder.assert_called_once_with(ai_tool.ACTION, self.uiapp.ActiveUIDocument.Document,
                                             self.uiapp.ActiveUIDocument)
        self.assertEqual(ticket.response["data"], ai_tool.compact(result_data()))
        self.assertIsNone(self.session.ai.turn)

    def test_connector_mapping_and_composite_are_existing_actions(self):
        action = ai_tool.ACTIONS[p.TOOLS[1]]
        data = result_data(action)
        data.update(classification="PIPING_CONNECTOR_REPORT_PARTIAL", reason_code="UNREADABLE")
        self.builder.return_value = data
        self.assertEqual(self.inspect(tool=p.TOOLS[1]).response["data"], ai_tool.compact(data, action))
        payload = dict(action_id=ai_tool.ACTIONS[p.TOOLS[2]], specialty="MEP",
                       classification="MEP_SELECTION_SUMMARY_PARTIAL", reason_code="UNSUPPORTED_SCOPE",
                       children=[], transport_omissions={"rows": 5})
        with patch("modelmind_composite.execute", return_value=payload) as composite:
            self.assertEqual(self.inspect(tool=p.TOOLS[2]).response["data"], payload)
            composite.assert_called_once()
        self.assertEqual(self.builder.call_count, 1)

    def test_context_single_use(self):
        token = self.context()
        self.assertTrue(self.inspect(token).response["ok"])
        self.assertEqual(self.inspect(token).response["error_code"], "STALE_CONTEXT")
        self.assertEqual(self.builder.call_count, 1)

    def test_document_selection_view_and_model_changes_reject(self):
        mutations = (lambda: setattr(self.session, "selection_generation", 2),
                     lambda: setattr(self.session, "context_generation", 2),
                     lambda: setattr(self.session, "document_identity", (2, "Other", "")),
                     self.host.model_changed)
        for mutate in mutations:
            token = self.context()
            mutate()
            self.assertEqual(self.inspect(token).response["error_code"], "STALE_CONTEXT")
        self.builder.assert_not_called()

    def test_changed_back_still_invalidates(self):
        token = self.context()
        self.session.selection_generation += 2
        self.assertEqual(self.inspect(token).response["error_code"], "STALE_CONTEXT")

    def test_lease_expiry(self):
        token = self.context()
        self.now += p.CONTEXT_SECONDS
        self.assertEqual(self.inspect(token).response["error_code"], "STALE_CONTEXT")
        self.builder.assert_not_called()

    def test_cancellation_before_dispatch(self):
        ticket = Ticket()
        ticket.cancelled.set()
        self.host.handle(request(), ticket)
        self.assertIsNone(ticket.response)
        self.assertEqual(self.host.contexts, {})

    def test_timeout_or_stop_before_external_event_never_executes(self):
        for cancel in (lambda t: t.cancelled.set(), lambda t: setattr(t, "deadline", 0),
                       lambda t: self.host.stop()):
            ticket = self.inspect(execute=False)
            cancel(ticket)
            self.session.ai.execute_approved(self.uiapp)
            self.assertIsNone(self.session.ai.turn)
        self.builder.assert_not_called()

    def test_model_changes_while_queued_never_executes(self):
        ticket = self.inspect(execute=False)
        self.host.model_changed()
        self.session.ai.execute_approved(self.uiapp)
        self.assertEqual(ticket.response["error_code"], "STALE_CONTEXT")
        self.builder.assert_not_called()

    def test_result_dropped_when_context_changes_during_execution(self):
        def build(*args):
            self.host.model_changed()
            return result_data()
        self.builder.side_effect = build
        self.assertEqual(self.inspect().response["error_code"], "STALE_CONTEXT")
        self.assertIsNone(self.session.ai.turn)

    def test_busy_and_safety_lock_do_not_steal_existing_work(self):
        first = self.inspect(execute=False)
        owned = self.session.ai.turn
        second = Ticket()
        self.host.handle(request(), second)
        self.assertEqual(second.response["error_code"], "REVIT_BUSY")
        self.assertIs(self.session.ai.turn, owned)
        self.session.ai.execute_approved(self.uiapp)
        self.assertTrue(first.response["ok"])
        admission_for(self.session).safety_locked = True
        third = Ticket()
        self.host.handle(request(), third)
        self.assertEqual(third.response["error_code"], "REVIT_BUSY")

    def test_revit_event_denial_releases_ownership(self):
        self.session.raise_ai_event.return_value = False
        self.assertEqual(self.inspect().response["error_code"], "MODELMIND_NOT_READY")
        self.assertIsNone(self.session.ai.turn)
        self.builder.assert_not_called()

    def test_missing_document_or_stopped_bridge(self):
        self.session.document_identity = None
        ticket = Ticket(); self.host.handle(request(), ticket)
        self.assertEqual(ticket.response["error_code"], "NO_ACTIVE_DOCUMENT")
        self.host.stop()
        ticket = Ticket(); self.host.handle(request(), ticket)
        self.assertEqual(ticket.response["error_code"], "BRIDGE_STOPPED")

    def test_context_pool_is_bounded(self):
        for _ in range(8):
            self.context()
        ticket = Ticket(); self.host.handle(request(), ticket)
        self.assertEqual(ticket.response["error_code"], "CONTEXT_LIMIT")


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.file = Path(self.temp.name) / "connection.json"
        self.listener = Listener(lambda req, ticket: ticket.complete(p.result(req["request_id"], {"answer": 1})))
        self.listener.start()
        self.addCleanup(self.stop)
        self.descriptor = dict(version=1, host="127.0.0.1", port=self.listener.port,
                               token=self.listener.token, revit_pid=123)
        self.file.write_text(json.dumps(self.descriptor))
        self.client = BridgeClient(self.file)

    def stop(self):
        self.listener.stop()
        self.listener.thread.join(3)
        self.assertFalse(self.listener.thread.is_alive())

    def test_actual_loopback_exchange(self):
        self.assertEqual(self.client.call("context"), {"answer": 1})
        self.assertTrue(self.client.call("ping")["read_only"])

    def test_wrong_secret_never_dispatches(self):
        self.listener.dispatch = Mock()
        self.descriptor["token"] = "f" * 64
        self.file.write_text(json.dumps(self.descriptor))
        with self.assertRaises(BridgeError):
            self.client.call("context")
        self.listener.dispatch.assert_not_called()

    def test_nonloopback_descriptor_rejected_before_connect(self):
        self.descriptor["host"] = "example.com"
        self.file.write_text(json.dumps(self.descriptor))
        with patch("socket.create_connection") as connect, self.assertRaises(BridgeError):
            self.client.call("context")
        connect.assert_not_called()

    def test_oversized_result_is_error(self):
        self.listener.dispatch = lambda req, ticket: ticket.complete(p.result(req["request_id"], {"x": "x" * 100000}))
        with self.assertRaisesRegex(BridgeError, "RESULT_TOO_LARGE"):
            self.client.call("context")

    def test_timeout_cancels_ticket(self):
        seen = []
        self.listener.dispatch = lambda req, ticket: seen.append(ticket)
        with patch("bimcode_mcp.transport.Ticket", side_effect=lambda: Ticket(.03)):
            with self.assertRaisesRegex(BridgeError, "REVIT_TIMEOUT"):
                self.client.call("context")
        self.assertTrue(seen[0].cancelled.is_set())
        seen[0].complete(p.result("late", {"ignored": True}))
        self.assertIsNone(seen[0].response)

    def test_response_correlation(self):
        self.listener.dispatch = lambda req, ticket: ticket.complete(p.result("f" * 64, {"answer": 1}))
        with self.assertRaisesRegex(BridgeError, "invalid response"):
            self.client.call("context")


class MCPStdioTests(unittest.TestCase):
    def test_sdk_initialize_list_call_errors_and_host_roundtrip(self):
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError:
            self.skipTest("Install BIMCode_MCP/requirements.txt for SDK integration")
        fixture = HostTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        pending = queue.Queue()
        fixture.session.raise_ai_event = lambda: (pending.put(("execute", None)), True)[1]
        stopped = object()

        def pump():
            while True:
                item = pending.get()
                if item is stopped:
                    return
                req, ticket = item
                if req == "execute":
                    fixture.session.ai.execute_approved(fixture.uiapp)
                else:
                    fixture.host.handle(req, ticket)

        ui_thread = threading.Thread(target=pump, daemon=True)
        ui_thread.start()
        listener = Listener(lambda req, ticket: pending.put((req, ticket)))
        listener.start()
        try:
            with tempfile.TemporaryDirectory() as folder:
                connection = Path(folder) / "connection.json"
                connection.write_text(json.dumps(dict(version=1, host="127.0.0.1", port=listener.port,
                                                     token=listener.token, revit_pid=123)))
                params = StdioServerParameters(command=sys.executable,
                    args=["-I", "-B", str(ROOT / "BIMCode_MCP/server.py"), "--connection", str(connection)])

                async def exercise():
                    async with stdio_client(params) as (reader, writer):
                        async with ClientSession(reader, writer) as client:
                            initialized = await client.initialize()
                            self.assertEqual(initialized.serverInfo.name, "bimcode-revit-readonly")
                            tools = (await client.list_tools()).tools
                            self.assertEqual({t.name for t in tools}, {"get_revit_context", *p.TOOLS})
                            for tool in tools:
                                self.assertTrue(tool.annotations.readOnlyHint)
                                self.assertFalse(tool.inputSchema["additionalProperties"])
                            context = await client.call_tool("get_revit_context", {})
                            self.assertFalse(context.isError)
                            token = context.structuredContent["context_token"]
                            result = await client.call_tool(p.TOOLS[0], {"context_token": token})
                            self.assertFalse(result.isError)
                            self.assertEqual(result.structuredContent, ai_tool.compact(result_data()))
                            replay = await client.call_tool(p.TOOLS[0], {"context_token": token})
                            self.assertTrue(replay.isError)
                            self.assertIn("STALE_CONTEXT", replay.content[0].text)
                            for name, args in (("execute_code", {}), (p.TOOLS[0], {}),
                                               (p.TOOLS[0], {"context_token": 123}),
                                               (p.TOOLS[0], {"context_token": token, "action_id": "write"}),
                                               ("get_revit_context", {"unexpected": True})):
                                self.assertTrue((await client.call_tool(name, args)).isError)
                            self.assertEqual(fixture.builder.call_count, 1)
                            # Tools remain discoverable with Revit unavailable; no fabricated data.
                            listener.stop()
                            error = await client.call_tool("get_revit_context", {})
                            self.assertTrue(error.isError)
                            self.assertNotIn(listener.token, error.content[0].text)
                asyncio.run(exercise())
        finally:
            listener.stop(); listener.thread.join(3)
            pending.put(stopped); ui_thread.join(3)
            self.assertFalse(ui_thread.is_alive())


class RuntimeTests(unittest.TestCase):
    def test_session_toggle_reuses_event_and_stops_on_disposal(self):
        from test_bimcode_ai_pane import LifecycleTests
        fixture = LifecycleTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        lifecycle = sys.modules["bimcode_ai_pane.lifecycle"]
        with patch("bimcode_mcp.runtime.Runtime") as runtime_type:
            runtime = runtime_type.return_value
            runtime.start.return_value = "private-connection-path"
            session = lifecycle.PaneSession(fixture.uiapp)
            runtime_type.assert_not_called()
            event = session.tool_event
            self.assertEqual(session.toggle_mcp_bridge(), "private-connection-path")
            self.assertIs(session.tool_event, event)
            self.assertIsNone(session.toggle_mcp_bridge())
            runtime.stop.assert_called_once()
            session.toggle_mcp_bridge()
            session.dispose_unregistered()
            self.assertEqual(runtime.stop.call_count, 2)
            self.assertIsNone(session.mcp_runtime)

    def test_runtime_starts_dispatches_and_cleans_up(self):
        from test_bimcode_ai_pane import Event, DelegateFactory
        from bimcode_mcp import runtime
        with tempfile.TemporaryDirectory() as parent:
            folder = Path(parent) / "private"
            folder.mkdir()
            changes = Event()
            dispatcher = Mock()
            session = types.SimpleNamespace(
                _subscriptions=[(None, name, None) for name in (
                    "SelectionChanged", "ViewActivated", "DocumentOpened", "DocumentCreated",
                    "DocumentClosed", "ApplicationClosing")],
                uiapp=types.SimpleNamespace(Application=types.SimpleNamespace(DocumentChanged=changes)),
                panel=types.SimpleNamespace(Dispatcher=dispatcher))
            modules = {"pyrevit": types.SimpleNamespace(
                DB=types.SimpleNamespace(Events=types.SimpleNamespace(DocumentChangedEventArgs=object)),
                framework=types.SimpleNamespace(EventHandler=DelegateFactory())),
                "System": types.SimpleNamespace(Action=lambda callback: callback)}
            with patch.dict(sys.modules, modules), patch.object(runtime, "_private_directory", return_value=str(folder)):
                host = runtime.Runtime(session)
                path = host.start()
                try:
                    self.assertEqual(len(changes.handlers), 1)
                    changes.handlers[0]()
                    self.assertEqual(host.controller.epoch, 1)
                    descriptor = json.loads(Path(path).read_text())
                    self.assertEqual(descriptor["host"], "127.0.0.1")
                    self.assertTrue(p.is_token(descriptor["token"]))
                    self.assertTrue(BridgeClient(path).call("ping")["read_only"])
                    host.listener.dispatch(request(), Ticket())
                    dispatcher.BeginInvoke.assert_called_once()
                    self.assertFalse(hasattr(session, "ai"))
                finally:
                    host.stop(); host.listener.thread.join(3)
                self.assertEqual(changes.handlers, [])
                self.assertFalse(Path(path).exists())
                self.assertFalse(folder.exists())

    def test_missing_lifecycle_events_prevents_listener(self):
        from bimcode_mcp.runtime import Runtime
        modules = {"pyrevit": types.SimpleNamespace(DB=None, framework=None),
                   "System": types.SimpleNamespace(Action=None)}
        with patch.dict(sys.modules, modules), patch("bimcode_mcp.runtime.Listener") as listener:
            with self.assertRaisesRegex(RuntimeError, "MCP_LIFECYCLE_EVENTS_UNAVAILABLE"):
                Runtime(types.SimpleNamespace(_subscriptions=[])).start()
            listener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
