"""Offline M3A tests. Real local config is never loaded."""
import contextlib
import ast
import importlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "BIMCode_Provider"))
sys.path.insert(0, str(ROOT / "AI.extension/lib"))
import provider_config as config
import protocol
import provider
import sidecar
from bimcode_ai_pane import provider_bridge as bridge
from bimcode_ai_pane import provider_ui

FAKE = "fake-test-key-not-a-credential"
RID = "a" * 32


def req(operation="text_response", **extra):
    value = dict(protocol_version=1, request_id=RID, operation=operation)
    if operation == "text_response":
        value["user_text"] = "hello"
    value.update(extra)
    return value


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def load(self, text="", env=None):
        (self.root / ".env.local").write_text(text, encoding="utf-8")
        return config.load_config(self.root, {} if env is None else env)

    def test_fallback(self):
        self.assertEqual(self.load("OPENAI_API_KEY=" + FAKE + "\nOPENAI_MODEL=test-model").state, "READY")

    def test_env_precedence(self):
        c = self.load("OPENAI_API_KEY=other\nOPENAI_MODEL=file-model", {"OPENAI_API_KEY": FAKE})
        self.assertEqual(c.api_key, FAKE)
        self.assertEqual(c.model, "file-model")

    def test_complete_environment_skips_file(self):
        with patch.object(Path, "read_text", side_effect=AssertionError()):
            c = config.load_config(self.root, dict(OPENAI_API_KEY=FAKE, OPENAI_MODEL="test-model"))
        self.assertEqual(c.state, "READY")

    def test_comments_blanks_unknown_quotes(self):
        c = self.load("# comment\n\nUNKNOWN=anything\n OPENAI_API_KEY = '" + FAKE + "'\nOPENAI_MODEL=\"test-model\"")
        self.assertEqual(c.state, "READY")

    def test_missing_key(self):
        self.assertEqual(self.load().state, "MISSING_API_KEY")

    def test_missing_model(self):
        self.assertEqual(self.load("OPENAI_API_KEY=" + FAKE).state, "MISSING_MODEL")

    def test_empty_env_does_not_fallback(self):
        self.assertEqual(self.load("OPENAI_API_KEY=" + FAKE, {"OPENAI_API_KEY": ""}).state, "MISSING_API_KEY")

    def test_duplicate(self):
        self.assertEqual(self.load("OPENAI_MODEL=a\nOPENAI_MODEL=b").state, "INVALID_CONFIG")

    def test_bad_quote(self):
        self.assertEqual(self.load("OPENAI_MODEL='abc").state, "INVALID_CONFIG")

    def test_invalid_model(self):
        self.assertEqual(self.load(env=dict(OPENAI_API_KEY=FAKE, OPENAI_MODEL="https://other")).state, "INVALID_CONFIG")

    def test_repr(self):
        self.assertNotIn(FAKE, repr(config.Config("READY", FAKE, "test-model")))

    def test_model_cannot_echo_key(self):
        self.assertEqual(self.load(env=dict(OPENAI_API_KEY=FAKE, OPENAI_MODEL=FAKE)).state, "INVALID_CONFIG")


class ProtocolTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(protocol.parse(json.dumps(req())), req())

    def test_readiness(self):
        self.assertEqual(protocol.parse(json.dumps(req("readiness")))["operation"], "readiness")

    def test_invalid_json(self):
        with self.assertRaises(ValueError):
            protocol.parse("{")

    def test_invalid_requests(self):
        for data in (req(protocol_version=2), req(protocol_version=True), req("tools"),
                     req(user_text=""), req(user_text="a" * 2001), req(api_key=FAKE),
                     req(request_id="bad")):
            with self.subTest(data=data), self.assertRaises(ValueError):
                protocol.parse(json.dumps(data))

    def test_duplicate_json_key(self):
        with self.assertRaises(ValueError):
            protocol.parse('{"request_id":"a","request_id":"b"}')

    def test_invalid_input_never_reads_config(self):
        with patch.object(sidecar, "load_config", side_effect=AssertionError()):
            self.assertEqual(sidecar.dispatch("{", ROOT)["error"]["code"], "SIDECAR_PROTOCOL_ERROR")

    def test_stdout_protocol_and_secret_suppression(self):
        def send(c, r):
            print(FAKE)
            print(FAKE, file=sys.stderr)
            return protocol.success(r["request_id"], c.model, "answer")
        stream, err = io.StringIO(), io.StringIO()
        with tempfile.TemporaryDirectory() as root, contextlib.redirect_stderr(err):
            sidecar.main(io.StringIO(json.dumps(req())), stream, root,
                         dict(OPENAI_API_KEY=FAKE, OPENAI_MODEL="test-model"), send)
        data = json.loads(stream.getvalue())
        self.assertEqual(data["request_id"], RID)
        self.assertEqual(data["text"], "answer")
        self.assertNotIn(FAKE, stream.getvalue() + err.getvalue())

    def test_readiness_never_sends(self):
        with tempfile.TemporaryDirectory() as root:
            result = sidecar.dispatch(json.dumps(req("readiness")), root,
                                      dict(OPENAI_API_KEY=FAKE, OPENAI_MODEL="test-model"),
                                      Mock(side_effect=AssertionError()))
        self.assertEqual(result["text"], "READY")

    def test_config_failure(self):
        with tempfile.TemporaryDirectory() as root:
            result = sidecar.dispatch(json.dumps(req()), root, {})
        self.assertEqual(result["error"]["code"], "CONFIG_MISSING_API_KEY")


class ProviderTests(unittest.TestCase):
    def run_send(self, text="answer", error=None, status="completed"):
        factory = Mock()
        client = factory.return_value.__enter__ = Mock(return_value=Mock())
        factory.return_value.__exit__ = Mock(return_value=False)
        call = client.return_value.responses.create
        call.return_value = types.SimpleNamespace(output_text=text, status=status)
        call.side_effect = error
        result = provider.send(config.Config("READY", FAKE, "configured-model"), req(), factory)
        return result, call

    def test_success_and_boundary(self):
        result, call = self.run_send()
        self.assertEqual(result["text"], "answer")
        self.assertEqual(call.call_count, 1)
        args = call.call_args.kwargs
        self.assertEqual(args["model"], "configured-model")
        self.assertFalse(args["store"])
        self.assertFalse(args["background"])
        self.assertFalse(set(args) & {"tools", "previous_response_id", "conversation", "temperature"})

    def test_empty(self):
        self.assertEqual(self.run_send("")[0]["error"]["code"], "OPENAI_EMPTY_RESPONSE")

    def test_incomplete(self):
        self.assertEqual(self.run_send(status="incomplete")[0]["error"]["code"], "OPENAI_API_ERROR")

    def test_bound(self):
        self.assertLessEqual(len(self.run_send("a" * 20000)[0]["text"]), 12000)

    def test_secret_echo(self):
        result, unused = self.run_send(FAKE)
        self.assertFalse(result["ok"])
        self.assertNotIn(FAKE, json.dumps(result))

    def test_internal_exception_safe(self):
        result, unused = self.run_send(error=RuntimeError(FAKE))
        self.assertEqual(result["error"]["code"], "INTERNAL_PROVIDER_ERROR")
        self.assertNotIn(FAKE, json.dumps(result))

    def test_sdk_errors(self):
        import openai
        import httpx2
        request = httpx2.Request("POST", "https://api.openai.com/v1/responses")
        response = httpx2.Response(429, request=request)
        cases = [
            (openai.AuthenticationError(FAKE, response=response, body={}), "OPENAI_AUTH_ERROR"),
            (openai.RateLimitError(FAKE, response=response, body={}), "OPENAI_RATE_LIMIT"),
            (openai.RateLimitError(FAKE, response=response, body={"code": "insufficient_quota"}), "OPENAI_QUOTA_OR_BILLING"),
            (openai.APITimeoutError(request), "OPENAI_TIMEOUT"),
            (openai.APIConnectionError(request=request), "OPENAI_CONNECTION_ERROR"),
            (openai.APIStatusError(FAKE, response=response, body={}), "OPENAI_API_ERROR"),
        ]
        for error, code in cases:
            with self.subTest(code=code):
                result, unused = self.run_send(error=error)
                self.assertEqual(result["error"]["code"], code)
                self.assertNotIn(FAKE, json.dumps(result))

    def test_fixed_client_configuration(self):
        with patch.object(provider, "OpenAI") as client, patch.object(provider.httpx2, "Client") as http:
            provider.client_for(config.Config("READY", FAKE, "model"))
        self.assertEqual(client.call_args.kwargs["base_url"], "https://api.openai.com/v1")
        self.assertEqual(client.call_args.kwargs["max_retries"], 0)
        self.assertFalse(http.call_args.kwargs["trust_env"])
        self.assertFalse(http.call_args.kwargs["follow_redirects"])


class BridgeTests(unittest.TestCase):
    def test_fixed_paths(self):
        executable, script, root = bridge.paths()
        self.assertEqual(Path(root), ROOT)
        self.assertEqual(Path(executable), ROOT / ".venv/Scripts/python.exe")
        self.assertEqual(Path(script), ROOT / "BIMCode_Provider/sidecar.py")

    def test_valid(self):
        data = protocol.success(RID, "model", "answer")
        self.assertEqual(bridge.decode(json.dumps(data), RID, 0), data)

    def test_malformed(self):
        self.assertEqual(bridge.decode("{", RID, 0)["error"]["code"], "SIDECAR_PROTOCOL_ERROR")

    def test_nonzero(self):
        self.assertEqual(bridge.decode(FAKE, RID, 1)["error"]["code"], "SIDECAR_NONZERO_EXIT")

    def test_id_mismatch(self):
        self.assertEqual(bridge.decode(json.dumps(protocol.success("b" * 32, "m", "a")), RID, 0)["error"]["code"], "SIDECAR_REQUEST_ID_MISMATCH")

    def test_remote_error_text_not_rendered(self):
        data = protocol.failure(RID, "OPENAI_API_ERROR")
        data["error"]["message"] = FAKE
        self.assertNotIn(FAKE, json.dumps(bridge.decode(json.dumps(data), RID, 0)))

    def test_bad_schema(self):
        for raw in ("[]", "null", "{}", "x" * 100001):
            self.assertEqual(bridge.decode(raw, RID, 0)["error"]["code"], "SIDECAR_PROTOCOL_ERROR")

    def test_gate_readiness_empty_duplicate_restore(self):
        gate = bridge.SendState()
        self.assertFalse(gate.enabled("hello"))
        first = gate.begin("readiness")
        self.assertIsNone(gate.begin("readiness"))
        gate.finish(protocol.success(first["request_id"], "model", "READY"))
        self.assertFalse(gate.enabled(" "))
        self.assertTrue(gate.enabled("hello"))
        send = gate.begin("text_response", "hello")
        self.assertFalse(gate.enabled("hello"))
        self.assertIsNone(gate.begin("text_response", "hello"))
        self.assertFalse(gate.finish(protocol.success("wrong", "m", "a")))
        gate.finish(protocol.failure(send["request_id"], "OPENAI_TIMEOUT"))
        self.assertTrue(gate.enabled("hello"))
        send = gate.begin("text_response", "hello")
        gate.finish(protocol.success(send["request_id"], "model", "answer"))
        self.assertTrue(gate.enabled("hello"))

    def test_config_failure_disables(self):
        gate = bridge.SendState()
        gate.ready = True
        send = gate.begin("text_response", "hello")
        gate.finish(protocol.failure(send["request_id"], "INVALID_CONFIG"))
        self.assertFalse(gate.enabled("hello"))

    def test_presentation_find_bound(self):
        from bimcode_ai_pane.result_find import ResultFind
        model = provider_ui.presentation(protocol.success(RID, "model", "Hello" * 2400))
        self.assertLessEqual(model["character_count"], 16000)
        finder = ResultFind()
        finder.search(model, "hello")
        self.assertEqual(len(finder.matches), 2400)

    def test_failure_presentation(self):
        model = provider_ui.presentation(protocol.failure(RID, "OPENAI_AUTH_ERROR"))
        self.assertIn("FAILED", str(model))


class PaneTests(unittest.TestCase):
    def setUp(self):
        class Event:
            def __iadd__(self, handler):
                return self
        class Control:
            def __init__(self):
                self.Text, self.IsEnabled = "", True
                self.Click, self.TextChanged = Event(), Event()
        class WPF:
            def __init__(self):
                self.controls, self.Resources, self.Dispatcher = {}, {}, object()
            def FindName(self, name):
                return self.controls.setdefault(name, Control())
        host = types.ModuleType("pyrevit")
        host.forms = types.SimpleNamespace(WPFPanel=WPF)
        self.host_patch = patch.dict(sys.modules, {"pyrevit": host})
        self.host_patch.start()
        self.addCleanup(self.host_patch.stop)
        sys.modules.pop("bimcode_ai_pane.panel", None)
        self.module = importlib.import_module("bimcode_ai_pane.panel")
        self.addCleanup(lambda: sys.modules.pop("bimcode_ai_pane.panel", None))
        self.launch_patch = patch.object(provider_ui, "launch")
        self.launch = self.launch_patch.start()
        self.addCleanup(self.launch_patch.stop)
        self.panel = self.module.BIMCodeAIPanel()
        self.panel._render_find = Mock()

    def ready(self):
        payload = self.launch.call_args.args[0]
        self.panel._provider_complete(protocol.success(payload["request_id"], "model", "READY"))
        self.panel.FindName("MessageInput").Text = "hello"
        self.panel._on_provider_text(None, None)

    def test_initial_readiness_only(self):
        self.assertEqual(self.launch.call_args.args[0]["operation"], "readiness")
        self.assertFalse(self.panel.FindName("SendButton").IsEnabled)

    def test_send_success_and_m2_isolation(self):
        self.ready()
        tool, refresh = Mock(), Mock()
        self.panel.bind_tools(tool)
        self.panel.bind_refresh(refresh)
        self.assertTrue(self.panel.FindName("SendButton").IsEnabled)
        self.panel._on_send(None, None)
        self.panel._on_send(None, None)
        self.assertEqual(self.launch.call_count, 2)  # readiness + one Send
        self.assertFalse(self.panel.FindName("SendButton").IsEnabled)
        payload = self.launch.call_args.args[0]
        self.panel._provider_complete(protocol.success(payload["request_id"], "model", "answer"))
        self.assertTrue(self.panel.FindName("SendButton").IsEnabled)
        self.assertIn("AI Response", str(self.panel._presentation))
        tool.assert_not_called()
        refresh.assert_not_called()

    def test_send_failure_restores(self):
        self.ready()
        self.panel._on_send(None, None)
        payload = self.launch.call_args.args[0]
        self.panel._provider_complete(protocol.failure(payload["request_id"], "OPENAI_AUTH_ERROR"))
        self.assertTrue(self.panel.FindName("SendButton").IsEnabled)
        self.assertIn("OPENAI_AUTH_ERROR", str(self.panel._presentation))

    def test_start_failure_restores(self):
        self.ready()
        self.launch.side_effect = RuntimeError(FAKE)
        self.panel._on_send(None, None)
        self.assertTrue(self.panel.FindName("SendButton").IsEnabled)
        self.assertNotIn(FAKE, str(self.panel._presentation))

    def test_missing_config_disables(self):
        payload = self.launch.call_args.args[0]
        self.panel._provider_complete(protocol.failure(payload["request_id"], "CONFIG_MISSING_MODEL"))
        self.assertFalse(self.panel.FindName("SendButton").IsEnabled)
        self.assertTrue(self.panel.FindName("ProviderCheckButton").IsEnabled)


class BoundaryTests(unittest.TestCase):
    def test_provider_host_neutral_and_network_owner(self):
        for path in (ROOT / "BIMCode_Provider").glob("*.py"):
            tree = ast.parse(path.read_text())
            names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
            names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
            imports = {n.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.alias)}
            self.assertFalse((names | imports) & {"Autodesk", "pyrevit", "Document", "UIApplication",
                             "Transaction", "TransactionGroup", "SetElementIds", "subprocess",
                             "socket", "requests", "urllib", "eval", "exec"})
            if path.name != "provider.py":
                self.assertNotIn("responses.create", path.read_text())

    def test_process_and_ui_boundary(self):
        source = (ROOT / "AI.extension/lib/bimcode_ai_pane/provider_bridge.py").read_text()
        self.assertIn("info.UseShellExecute = False", source)
        self.assertIn("info.CreateNoWindow = True", source)
        self.assertNotIn("OPENAI_API_KEY", source)
        for forbidden in ("cmd.exe", "powershell", "Transaction", "UIDocument", "UIApplication"):
            self.assertNotIn(forbidden, source)
        ui = (ROOT / "AI.extension/lib/bimcode_ai_pane/provider_ui.py").read_text()
        self.assertIn("dispatcher.BeginInvoke", ui)
        self.assertNotIn("ExternalEvent", ui)


if __name__ == "__main__":
    unittest.main()
